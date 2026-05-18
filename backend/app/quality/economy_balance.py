from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.world_state import QuestTriggerType
from app.playtesting.runner import PlaytestReport
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class EconomyBalanceAnalysisRequest(BaseModel):
    playtest_reports: list[PlaytestReport] = Field(default_factory=list)


class EconomyBalanceReport(BaseModel):
    world_id: str
    total_items: int = 0
    tradeable_items: int = 0
    merchant_count: int = 0
    shop_inventory_count: int = 0
    negative_price_issues: list[QualityIssue] = Field(default_factory=list)
    zero_price_tradeable_issues: list[QualityIssue] = Field(default_factory=list)
    arbitrage_risks: list[QualityIssue] = Field(default_factory=list)
    non_tradeable_shop_items: list[QualityIssue] = Field(default_factory=list)
    hidden_shop_items: list[QualityIssue] = Field(default_factory=list)
    quest_reward_outliers: list[QualityIssue] = Field(default_factory=list)
    required_item_affordability_issues: list[QualityIssue] = Field(default_factory=list)
    missing_shop_items: list[QualityIssue] = Field(default_factory=list)
    stolen_item_trade_risks: list[QualityIssue] = Field(default_factory=list)
    price_modifier_issues: list[QualityIssue] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        for field_name in _ISSUE_FIELDS:
            payload[field_name] = [
                issue.normal_copy().model_dump(mode="json", exclude_none=True)
                for issue in getattr(self, field_name)
            ]
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


class _EconomyContent(BaseModel):
    world_path: Path
    items: list[dict[str, Any]] = Field(default_factory=list)
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_EconomyContent":
        return cls(
            world_path=world_path,
            items=_read_yaml_list(world_path / "items.yaml", "items"),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            quests=_read_yaml_list(world_path / "quests.yaml", "quests"),
        )

    @property
    def item_by_id(self) -> dict[str, dict[str, Any]]:
        return {str(item.get("id")): item for item in self.items if item.get("id")}


_ISSUE_FIELDS = [
    "negative_price_issues",
    "zero_price_tradeable_issues",
    "arbitrage_risks",
    "non_tradeable_shop_items",
    "hidden_shop_items",
    "quest_reward_outliers",
    "required_item_affordability_issues",
    "missing_shop_items",
    "stolen_item_trade_risks",
    "price_modifier_issues",
]

STARTING_CURRENCY_ESTIMATE = 20
QUEST_REWARD_OUTLIER_THRESHOLD = 1000
PRICE_MODIFIER_EXTREME_THRESHOLD = 3.0


def analyze_economy_balance(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    playtest_reports: list[PlaytestReport] | None = None,
) -> EconomyBalanceReport:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)
    content = _EconomyContent.load(world_path)
    item_by_id = content.item_by_id
    merchants = [npc for npc in content.npcs if bool(npc.get("merchant"))]
    report = EconomyBalanceReport(
        world_id=world_id,
        total_items=len(item_by_id),
        tradeable_items=sum(1 for item in content.items if _is_tradeable(item)),
        merchant_count=len(merchants),
        shop_inventory_count=sum(len(_string_list(merchant.get("shop_inventory"))) for merchant in merchants),
        quality_report=WorldQualityReport(world_id=world_id),
    )

    _detect_item_price_issues(report, content.items)
    _detect_merchant_modifier_issues(report, merchants)
    _detect_shop_inventory_issues(report, merchants, item_by_id)
    _detect_quest_reward_outliers(report, content.quests)
    _detect_required_item_affordability(report, content.quests, merchants, item_by_id)
    _detect_stolen_item_risks(report, content.items)
    _observe_playtest_economy_path(report, playtest_reports or [])

    report.quality_report = economy_balance_report_to_quality_report(report)
    return report


def economy_balance_report_to_quality_report(report: EconomyBalanceReport) -> WorldQualityReport:
    issues = [issue for field_name in _ISSUE_FIELDS for issue in getattr(report, field_name)]
    blocker_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.BLOCKER)
    error_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.WARNING)
    status = QualityMetricStatus.OK
    if blocker_count:
        status = QualityMetricStatus.BLOCKER
    elif error_count:
        status = QualityMetricStatus.ERROR
    elif warning_count:
        status = QualityMetricStatus.WARNING
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["economy_balance"],
        metrics=[
            QualityMetric(name="total_items", value=report.total_items, category="economy_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="tradeable_items", value=report.tradeable_items, category="economy_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="merchant_count", value=report.merchant_count, category="economy_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="shop_inventory_count", value=report.shop_inventory_count, category="economy_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="economy_balance_issues", value=len(issues), category="economy_balance", threshold=0, status=status),
            QualityMetric(name="economy_balance_blockers", value=blocker_count, category="economy_balance", threshold=0, status=QualityMetricStatus.BLOCKER if blocker_count else QualityMetricStatus.OK),
        ],
        issues=issues,
        summary={
            "total_items": report.total_items,
            "tradeable_items": report.tradeable_items,
            "merchant_count": report.merchant_count,
            "shop_inventory_count": report.shop_inventory_count,
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(blocker_count, error_count, warning_count),
    )


def _detect_item_price_issues(report: EconomyBalanceReport, items: list[dict[str, Any]]) -> None:
    for item in sorted(items, key=lambda value: str(value.get("id", ""))):
        item_id = str(item.get("id", ""))
        price = _number(item.get("base_price"), default=0)
        if price < 0:
            report.negative_price_issues.append(
                _item_issue(
                    item=item,
                    code="negative_price",
                    severity=QualityIssueSeverity.BLOCKER,
                    message="Item has a negative base_price.",
                    safe_details={"base_price": price},
                    path=f"items.{item_id}.base_price",
                )
            )
        if price == 0 and _is_tradeable(item):
            report.zero_price_tradeable_issues.append(
                _item_issue(
                    item=item,
                    code="zero_price_tradeable_item",
                    severity=QualityIssueSeverity.WARNING,
                    message="Tradeable item has zero base_price.",
                    safe_details={"base_price": price},
                    path=f"items.{item_id}.base_price",
                )
            )


def _detect_merchant_modifier_issues(report: EconomyBalanceReport, merchants: list[dict[str, Any]]) -> None:
    for merchant in sorted(merchants, key=lambda value: str(value.get("id", ""))):
        merchant_id = str(merchant.get("id", ""))
        buy_modifier = _number(merchant.get("buy_price_modifier"), default=1.0)
        sell_modifier = _number(merchant.get("sell_price_modifier"), default=0.5)
        if sell_modifier > buy_modifier:
            report.arbitrage_risks.append(
                _merchant_issue(
                    merchant=merchant,
                    code="sell_price_exceeds_buy_price",
                    severity=QualityIssueSeverity.ERROR,
                    message="Merchant sell price modifier is higher than buy price modifier and may allow arbitrage.",
                    safe_details={"buy_price_modifier": buy_modifier, "sell_price_modifier": sell_modifier},
                    path=f"npcs.{merchant_id}.sell_price_modifier",
                )
            )
        for field_name, value in (("buy_price_modifier", buy_modifier), ("sell_price_modifier", sell_modifier)):
            if value < 0:
                severity = QualityIssueSeverity.BLOCKER
            elif value > PRICE_MODIFIER_EXTREME_THRESHOLD:
                severity = QualityIssueSeverity.WARNING
            else:
                continue
            report.price_modifier_issues.append(
                _merchant_issue(
                    merchant=merchant,
                    code=f"price_modifier_extreme_{field_name}",
                    severity=severity,
                    message="Merchant price modifier is outside the expected sanity range.",
                    safe_details={field_name: value},
                    path=f"npcs.{merchant_id}.{field_name}",
                )
            )


def _detect_shop_inventory_issues(
    report: EconomyBalanceReport,
    merchants: list[dict[str, Any]],
    item_by_id: dict[str, dict[str, Any]],
) -> None:
    for merchant in sorted(merchants, key=lambda value: str(value.get("id", ""))):
        merchant_id = str(merchant.get("id", ""))
        for item_id in sorted(_string_list(merchant.get("shop_inventory"))):
            item = item_by_id.get(item_id)
            if item is None:
                report.missing_shop_items.append(
                    _merchant_issue(
                        merchant=merchant,
                        code="merchant_inventory_missing_item",
                        severity=QualityIssueSeverity.ERROR,
                        message="Merchant inventory references an undefined item.",
                        safe_details={"item_id": item_id},
                        path=f"npcs.{merchant_id}.shop_inventory",
                    )
                )
                continue
            if not _is_tradeable(item):
                report.non_tradeable_shop_items.append(
                    _item_issue(
                        item=item,
                        code="non_tradeable_item_in_shop",
                        severity=QualityIssueSeverity.ERROR,
                        message="Merchant shop inventory contains a non-tradeable item.",
                        safe_details={"merchant_id": merchant_id},
                        path=f"npcs.{merchant_id}.shop_inventory",
                    )
                )
            if _is_hidden_item(item):
                report.hidden_shop_items.append(
                    _item_issue(
                        item=item,
                        code="hidden_item_visible_in_shop",
                        severity=QualityIssueSeverity.ERROR,
                        message="Merchant shop inventory contains a hidden item that should not be visible in player shop UI.",
                        safe_details={"merchant_id": merchant_id},
                        path=f"npcs.{merchant_id}.shop_inventory",
                    )
                )


def _detect_quest_reward_outliers(report: EconomyBalanceReport, quests: list[dict[str, Any]]) -> None:
    for quest in sorted(quests, key=lambda value: str(value.get("id", ""))):
        quest_id = str(quest.get("id", ""))
        for index, reward in enumerate(quest.get("rewards", [])):
            amount = _reward_currency_amount(reward)
            if amount is None:
                continue
            if amount <= 0 or amount > QUEST_REWARD_OUTLIER_THRESHOLD:
                report.quest_reward_outliers.append(
                    QualityIssue(
                        id=f"economy_balance:quest_reward:{quest_id}:{index}",
                        severity=QualityIssueSeverity.WARNING,
                        category="economy_balance",
                        file="quests.yaml",
                        path=f"quests.{quest_id}.rewards[{index}]",
                        entity_id=quest_id,
                        message="Quest currency reward is outside the expected sanity range.",
                        safe_details={"amount": amount},
                    )
                )


def _detect_required_item_affordability(
    report: EconomyBalanceReport,
    quests: list[dict[str, Any]],
    merchants: list[dict[str, Any]],
    item_by_id: dict[str, dict[str, Any]],
) -> None:
    rewards_total = sum(amount or 0 for quest in quests for amount in (_reward_currency_amount(reward) for reward in quest.get("rewards", [])))
    estimated_income = STARTING_CURRENCY_ESTIMATE + rewards_total
    merchant_by_item = _merchant_by_item(merchants)
    for quest in quests:
        for trigger in quest.get("triggers", []):
            if not isinstance(trigger, dict) or trigger.get("type") != QuestTriggerType.ITEM_ACQUIRED:
                continue
            item_id = str(trigger.get("id", ""))
            item = item_by_id.get(item_id)
            if item is None or item_id not in merchant_by_item:
                continue
            merchant = merchant_by_item[item_id]
            price = round(_number(item.get("base_price"), default=0) * _number(merchant.get("buy_price_modifier"), default=1.0))
            if price > estimated_income:
                report.required_item_affordability_issues.append(
                    _item_issue(
                        item=item,
                        code="required_item_too_expensive_without_income_path",
                        severity=QualityIssueSeverity.WARNING,
                        message="Quest-required shop item may cost more than known starting currency plus rewards.",
                        safe_details={"estimated_price": price, "estimated_income": estimated_income},
                        path=f"items.{item_id}.base_price",
                    )
                )


def _detect_stolen_item_risks(report: EconomyBalanceReport, items: list[dict[str, Any]]) -> None:
    for item in sorted(items, key=lambda value: str(value.get("id", ""))):
        tags = set(_string_list(item.get("tags")))
        if "stolen" not in tags or not _is_tradeable(item):
            continue
        if "trade_risk" not in tags and "refuse_stolen" not in tags:
            item_id = str(item.get("id", ""))
            report.stolen_item_trade_risks.append(
                _item_issue(
                    item=item,
                    code="stolen_item_trade_risk_not_configured",
                    severity=QualityIssueSeverity.INFO,
                    message="Stolen tradeable item relies on default stolen-item refusal without content-level risk tags.",
                    safe_details={},
                    path=f"items.{item_id}.tags",
                )
            )


def _observe_playtest_economy_path(report: EconomyBalanceReport, playtest_reports: list[PlaytestReport]) -> None:
    trade_actions = sum(
        1
        for playtest_report in playtest_reports
        for action in playtest_report.actions_taken
        if action.action_type in {"buy", "sell"}
    )
    if trade_actions:
        report.quality_report.summary["playtest_trade_actions"] = trade_actions


def _merchant_by_item(merchants: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for merchant in merchants:
        for item_id in _string_list(merchant.get("shop_inventory")):
            mapping.setdefault(item_id, merchant)
    return mapping


def _reward_currency_amount(reward: Any) -> int | None:
    if not isinstance(reward, dict):
        return None
    reward_type = str(reward.get("type") or reward.get("reward_type") or "")
    if reward_type not in {"currency", "money", "coins", "gold"}:
        return None
    amount = reward.get("amount", reward.get("value"))
    return int(amount) if isinstance(amount, int | float) else None


def _item_issue(
    *,
    item: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    safe_details: dict[str, Any],
    path: str,
) -> QualityIssue:
    item_id = str(item.get("id", ""))
    hidden = _is_hidden_item(item)
    return QualityIssue(
        id=f"economy_balance:{'hidden' if hidden else item_id}:{code}",
        severity=severity,
        category="economy_balance",
        file="items.yaml",
        path="items.yaml" if hidden else path,
        entity_id=None if hidden else item_id,
        message=message,
        safe_details={"code": code, **safe_details},
        hidden_details_debug_only={"item_id": item_id, "path": path} if hidden else None,
    )


def _merchant_issue(
    *,
    merchant: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    safe_details: dict[str, Any],
    path: str,
) -> QualityIssue:
    merchant_id = str(merchant.get("id", ""))
    hidden = bool(merchant.get("hidden")) and "player" not in _string_list(merchant.get("discovered_by"))
    return QualityIssue(
        id=f"economy_balance:{'hidden_merchant' if hidden else merchant_id}:{code}:{safe_details.get('item_id', 'merchant')}",
        severity=severity,
        category="economy_balance",
        file="npcs.yaml",
        path="npcs.yaml" if hidden else path,
        entity_id=None if hidden else merchant_id,
        message=message,
        safe_details={"code": code, **safe_details},
        hidden_details_debug_only={"merchant_id": merchant_id, "path": path} if hidden else None,
    )


def _is_tradeable(item: dict[str, Any]) -> bool:
    return bool(item.get("tradeable", True))


def _is_hidden_item(item: dict[str, Any]) -> bool:
    return bool(item.get("hidden")) and "player" not in _string_list(item.get("discovered_by"))


def _number(value: Any, *, default: float) -> float:
    return float(value) if isinstance(value, int | float) else default


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _read_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
    data = _read_yaml_file(path)
    values = data.get(key, []) if isinstance(data, dict) else []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _recommended_actions(blockers: int, errors: int, warnings: int) -> list[str]:
    actions: list[str] = []
    if blockers:
        actions.append("Fix negative prices before using the content pack for trade tests.")
    if errors:
        actions.append("Review merchant inventory, hidden shop items, and arbitrage risks.")
    if warnings:
        actions.append("Review zero-price tradeables, reward outliers, and affordability warnings.")
    return actions
