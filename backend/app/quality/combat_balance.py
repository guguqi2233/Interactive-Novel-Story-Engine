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


class CombatBalanceAnalysisRequest(BaseModel):
    playtest_reports: list[PlaytestReport] = Field(default_factory=list)


class CombatBalanceReport(BaseModel):
    world_id: str
    combatant_npcs: int = 0
    combat_path_playtests: int = 0
    combat_actions_observed: int = 0
    enemy_stat_outliers: list[QualityIssue] = Field(default_factory=list)
    unavoidable_lethal_encounters: list[QualityIssue] = Field(default_factory=list)
    flee_impossible_encounters: list[QualityIssue] = Field(default_factory=list)
    non_lethal_path_issues: list[QualityIssue] = Field(default_factory=list)
    quest_critical_death_issues: list[QualityIssue] = Field(default_factory=list)
    combat_reward_issues: list[QualityIssue] = Field(default_factory=list)
    public_combat_consequence_issues: list[QualityIssue] = Field(default_factory=list)
    hidden_witness_leak_risks: list[QualityIssue] = Field(default_factory=list)
    status_effect_resolution_issues: list[QualityIssue] = Field(default_factory=list)
    dead_required_npc_issues: list[QualityIssue] = Field(default_factory=list)
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


class _CombatContent(BaseModel):
    world_path: Path
    start_location_id: str
    locations: list[dict[str, Any]] = Field(default_factory=list)
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)
    rumors: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_CombatContent":
        manifest = _read_yaml_file(world_path / "manifest.yaml")
        return cls(
            world_path=world_path,
            start_location_id=str(manifest.get("start_location_id", "")),
            locations=_read_yaml_list(world_path / "locations.yaml", "locations"),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            items=_read_yaml_list(world_path / "items.yaml", "items"),
            quests=_read_yaml_list(world_path / "quests.yaml", "quests"),
            facts=_read_yaml_list(world_path / "facts.yaml", "facts"),
            rumors=_read_yaml_list(world_path / "rumors.yaml", "rumors"),
        )


_ISSUE_FIELDS = [
    "enemy_stat_outliers",
    "unavoidable_lethal_encounters",
    "flee_impossible_encounters",
    "non_lethal_path_issues",
    "quest_critical_death_issues",
    "combat_reward_issues",
    "public_combat_consequence_issues",
    "hidden_witness_leak_risks",
    "status_effect_resolution_issues",
    "dead_required_npc_issues",
]

HP_OUTLIER_THRESHOLD = 30
ATTACK_OUTLIER_THRESHOLD = 8
DEFENSE_OUTLIER_THRESHOLD = 6
SUPPORTED_RESOLVING_STATUS_TAGS = {"resolves_status", "rest_if_injured", "status_resolves"}
COMBAT_TAGS = {"enemy", "hostile", "combat", "guard", "bandit", "boss", "public_combat"}
LETHAL_TAGS = {"lethal", "deadly", "kill_on_failure"}
NON_LETHAL_TERMS = {"non_lethal", "non-lethal", "subdue", "capture", "spare"}


def analyze_combat_balance(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    playtest_reports: list[PlaytestReport] | None = None,
) -> CombatBalanceReport:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)

    content = _CombatContent.load(world_path)
    combat_npcs = [npc for npc in content.npcs if _is_combat_npc(npc)]
    location_by_id = {
        str(location.get("id")): location
        for location in content.locations
        if location.get("id")
    }
    npc_by_id = {
        str(npc.get("id")): npc
        for npc in content.npcs
        if npc.get("id")
    }
    report = CombatBalanceReport(
        world_id=world_id,
        combatant_npcs=len(combat_npcs),
        quality_report=WorldQualityReport(world_id=world_id),
    )

    _detect_combat_npc_risks(report, content, combat_npcs, location_by_id)
    _detect_quest_combat_risks(report, content.quests, npc_by_id)
    _observe_playtest_combat_path(report, playtest_reports or [])

    report.quality_report = combat_balance_report_to_quality_report(report)
    return report


def combat_balance_report_to_quality_report(report: CombatBalanceReport) -> WorldQualityReport:
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
        categories=["combat_balance"],
        metrics=[
            QualityMetric(name="combatant_npcs", value=report.combatant_npcs, category="combat_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="combat_path_playtests", value=report.combat_path_playtests, category="combat_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="combat_actions_observed", value=report.combat_actions_observed, category="combat_balance", status=QualityMetricStatus.OK),
            QualityMetric(name="combat_balance_issues", value=len(issues), category="combat_balance", threshold=0, status=status),
            QualityMetric(name="combat_balance_errors", value=error_count, category="combat_balance", threshold=0, status=QualityMetricStatus.ERROR if error_count else QualityMetricStatus.OK),
            QualityMetric(name="combat_balance_warnings", value=warning_count, category="combat_balance", threshold=0, status=QualityMetricStatus.WARNING if warning_count else QualityMetricStatus.OK),
        ],
        issues=issues,
        summary={
            "combatant_npcs": report.combatant_npcs,
            "combat_path_playtests": report.combat_path_playtests,
            "combat_actions_observed": report.combat_actions_observed,
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(blocker_count, error_count, warning_count),
    )


def _detect_combat_npc_risks(
    report: CombatBalanceReport,
    content: _CombatContent,
    combat_npcs: list[dict[str, Any]],
    location_by_id: dict[str, dict[str, Any]],
) -> None:
    consequence_markers = _combat_consequence_markers(content)
    for npc in sorted(combat_npcs, key=lambda item: str(item.get("id", ""))):
        npc_id = str(npc.get("id", ""))
        location_id = str(npc.get("location_id", ""))
        location = location_by_id.get(location_id, {})
        hp = _number(npc.get("max_hp", npc.get("hp")), default=10)
        attack = _number(npc.get("attack"), default=2)
        defense = _number(npc.get("defense"), default=1)
        tags = set(_string_list(npc.get("tags")))

        if hp > HP_OUTLIER_THRESHOLD or attack > ATTACK_OUTLIER_THRESHOLD or defense > DEFENSE_OUTLIER_THRESHOLD:
            report.enemy_stat_outliers.append(
                _npc_issue(
                    npc=npc,
                    code="enemy_stat_outlier",
                    severity=QualityIssueSeverity.WARNING,
                    message="Combat NPC stats are outside the lightweight combat sanity range.",
                    safe_details={"hp": hp, "attack": attack, "defense": defense},
                    path=f"npcs.{npc_id}",
                )
            )

        no_exits = not _exits(location)
        if no_exits and (tags & LETHAL_TAGS or attack >= ATTACK_OUTLIER_THRESHOLD):
            report.unavoidable_lethal_encounters.append(
                _npc_issue(
                    npc=npc,
                    code="unavoidable_lethal_encounter",
                    severity=QualityIssueSeverity.ERROR,
                    message="Lethal or high-damage combat appears in a location with no flee exit.",
                    safe_details={"location_id": location_id, "attack": attack},
                    path=f"npcs.{npc_id}.location_id",
                )
            )

        if no_exits and "flee_warning" not in tags and "no_flee_warning" not in tags:
            report.flee_impossible_encounters.append(
                _npc_issue(
                    npc=npc,
                    code="flee_impossible_without_warning",
                    severity=QualityIssueSeverity.WARNING,
                    message="Combat location has no exits but the encounter has no content-level flee warning tag.",
                    safe_details={"location_id": location_id},
                    path=f"npcs.{npc_id}.tags",
                )
            )

        if "public_combat" in tags and not consequence_markers:
            report.public_combat_consequence_issues.append(
                _npc_issue(
                    npc=npc,
                    code="public_combat_consequence_missing",
                    severity=QualityIssueSeverity.WARNING,
                    message="Public combat encounter has no obvious crime, rumor, or consequence marker.",
                    safe_details={},
                    path=f"npcs.{npc_id}.tags",
                )
            )

        if _status_effects(npc) and not tags.intersection(SUPPORTED_RESOLVING_STATUS_TAGS):
            report.status_effect_resolution_issues.append(
                _npc_issue(
                    npc=npc,
                    code="status_effect_never_resolves",
                    severity=QualityIssueSeverity.WARNING,
                    message="NPC starts with a combat status effect but no content-level resolution tag.",
                    safe_details={"status_effects": sorted(_status_effects(npc))},
                    path=f"npcs.{npc_id}.status_effects",
                )
            )

        _detect_hidden_witness_risks(report, npc, content.npcs)


def _detect_quest_combat_risks(
    report: CombatBalanceReport,
    quests: list[dict[str, Any]],
    npc_by_id: dict[str, dict[str, Any]],
) -> None:
    for quest in sorted(quests, key=lambda item: str(item.get("id", ""))):
        quest_id = str(quest.get("id", ""))
        quest_text = _quest_search_text(quest)
        combat_related = _contains_any(quest_text, {"combat", "fight", "attack", "defeat", "subdue", "capture"})
        non_lethal_related = _contains_any(quest_text, NON_LETHAL_TERMS)

        if combat_related and not quest.get("rewards"):
            report.combat_reward_issues.append(
                QualityIssue(
                    id=f"combat_balance:{quest_id}:combat_reward_missing",
                    severity=QualityIssueSeverity.WARNING,
                    category="combat_balance",
                    file="quests.yaml",
                    path=f"quests.{quest_id}.rewards",
                    entity_id=quest_id,
                    message="Combat-related quest has no configured reward.",
                    safe_details={"code": "combat_reward_missing"},
                )
            )

        if non_lethal_related and not _quest_has_non_lethal_path(quest):
            report.non_lethal_path_issues.append(
                QualityIssue(
                    id=f"combat_balance:{quest_id}:non_lethal_path_missing",
                    severity=QualityIssueSeverity.WARNING,
                    category="combat_balance",
                    file="quests.yaml",
                    path=f"quests.{quest_id}",
                    entity_id=quest_id,
                    message="Quest appears to require a non-lethal outcome but has no explicit non-lethal path marker.",
                    safe_details={"code": "non_lethal_path_missing"},
                )
            )

        for trigger in _quest_triggers(quest):
            if trigger.get("type") != QuestTriggerType.NPC_TALKED:
                continue
            npc_id = str(trigger.get("id", ""))
            npc = npc_by_id.get(npc_id)
            if npc is None:
                continue
            if _is_dead_npc(npc):
                report.dead_required_npc_issues.append(
                    _quest_npc_issue(
                        quest_id=quest_id,
                        npc=npc,
                        code="dead_npc_required_by_quest",
                        severity=QualityIssueSeverity.ERROR,
                        message="Quest requires talking to an NPC who starts dead or incapacitated.",
                        path=f"quests.{quest_id}.triggers",
                    )
                )
            if (_is_combat_npc(npc) or "quest_critical" in set(_string_list(npc.get("tags")))) and not _has_fallback_for_trigger(quest, trigger):
                report.quest_critical_death_issues.append(
                    _quest_npc_issue(
                        quest_id=quest_id,
                        npc=npc,
                        code="quest_critical_npc_death_without_fallback",
                        severity=QualityIssueSeverity.ERROR,
                        message="Quest-critical combat-capable NPC can block the quest if killed and no fallback trigger is configured.",
                        path=f"quests.{quest_id}.triggers",
                    )
                )


def _detect_hidden_witness_risks(
    report: CombatBalanceReport,
    combat_npc: dict[str, Any],
    npcs: list[dict[str, Any]],
) -> None:
    combat_location = str(combat_npc.get("location_id", ""))
    combat_id = str(combat_npc.get("id", ""))
    for witness in sorted(npcs, key=lambda item: str(item.get("id", ""))):
        if witness is combat_npc:
            continue
        if str(witness.get("location_id", "")) != combat_location or not _is_hidden_npc(witness):
            continue
        tags = set(_string_list(witness.get("tags")))
        if "hidden_witness_safe" in tags:
            continue
        report.hidden_witness_leak_risks.append(
            _npc_issue(
                npc=witness,
                code="hidden_witness_leak_risk",
                severity=QualityIssueSeverity.WARNING,
                message="Hidden NPC shares a combat location; verify witness data stays debug-only/player-safe.",
                safe_details={"combat_npc": combat_id if not _is_hidden_npc(combat_npc) else "hidden_combatant"},
                path=f"npcs.{str(witness.get('id', ''))}.location_id",
            )
        )


def _observe_playtest_combat_path(
    report: CombatBalanceReport,
    playtest_reports: list[PlaytestReport],
) -> None:
    report.combat_path_playtests = sum(
        1
        for playtest_report in playtest_reports
        if playtest_report.strategy == "combat_path" or any("combat" in action.action_type for action in playtest_report.actions_taken)
    )
    report.combat_actions_observed = sum(
        1
        for playtest_report in playtest_reports
        for action in playtest_report.actions_taken
        if action.action_type in {"attack", "defend", "flee"}
    )


def _combat_consequence_markers(content: _CombatContent) -> bool:
    values: list[str] = []
    for fact in content.facts:
        values.extend(_string_list(fact.get("tags")))
        values.append(str(fact.get("id", "")))
    for rumor in content.rumors:
        values.extend(_string_list(rumor.get("tags")))
        values.append(str(rumor.get("id", "")))
        values.append(str(rumor.get("fact_id", "")))
    text = " ".join(values).lower()
    return any(marker in text for marker in ("combat", "assault", "crime", "witness", "public_combat"))


def _quest_has_non_lethal_path(quest: dict[str, Any]) -> bool:
    if bool(quest.get("non_lethal_path")):
        return True
    tags = {tag.lower() for tag in _string_list(quest.get("tags"))}
    if tags.intersection(NON_LETHAL_TERMS | {"non_lethal_available", "capture_available"}):
        return True
    for trigger in _quest_triggers(quest):
        action = str(trigger.get("action", "")).lower()
        if action in {"non_lethal_attack", "subdue", "capture"}:
            return True
        if bool(trigger.get("non_lethal")):
            return True
    for reward in quest.get("rewards", []):
        if isinstance(reward, dict) and bool(reward.get("non_lethal")):
            return True
    return False


def _has_fallback_for_trigger(quest: dict[str, Any], trigger: dict[str, Any]) -> bool:
    objective_id = trigger.get("objective_id")
    next_stage = trigger.get("next_stage")
    for other in _quest_triggers(quest):
        if other is trigger:
            continue
        if other.get("type") == trigger.get("type") and other.get("id") == trigger.get("id"):
            continue
        if objective_id and other.get("objective_id") == objective_id:
            return True
        if next_stage and other.get("next_stage") == next_stage:
            return True
    return False


def _quest_npc_issue(
    *,
    quest_id: str,
    npc: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    path: str,
) -> QualityIssue:
    npc_id = str(npc.get("id", ""))
    hidden = _is_hidden_npc(npc)
    return QualityIssue(
        id=f"combat_balance:{quest_id}:{'hidden_npc' if hidden else npc_id}:{code}",
        severity=severity,
        category="combat_balance",
        file="quests.yaml",
        path="quests.yaml" if hidden else path,
        entity_id=quest_id,
        message=message,
        safe_details={"code": code},
        hidden_details_debug_only={"npc_id": npc_id, "path": path} if hidden else None,
    )


def _npc_issue(
    *,
    npc: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    safe_details: dict[str, Any],
    path: str,
) -> QualityIssue:
    npc_id = str(npc.get("id", ""))
    hidden = _is_hidden_npc(npc)
    return QualityIssue(
        id=f"combat_balance:{'hidden_npc' if hidden else npc_id}:{code}",
        severity=severity,
        category="combat_balance",
        file="npcs.yaml",
        path="npcs.yaml" if hidden else path,
        entity_id=None if hidden else npc_id,
        message=message,
        safe_details={"code": code, **safe_details},
        hidden_details_debug_only={"npc_id": npc_id, "path": path} if hidden else None,
    )


def _is_combat_npc(npc: dict[str, Any]) -> bool:
    tags = set(_string_list(npc.get("tags")))
    return bool(
        tags.intersection(COMBAT_TAGS | LETHAL_TAGS)
        or _string_list(npc.get("hostile_to"))
        or npc.get("attack") is not None
        or npc.get("defense") is not None
        or npc.get("hp") is not None
        or npc.get("max_hp") is not None
        or npc.get("combat_stance") is not None
        or _status_effects(npc)
    )


def _is_hidden_npc(npc: dict[str, Any]) -> bool:
    return bool(npc.get("hidden")) and "player" not in _string_list(npc.get("discovered_by"))


def _is_dead_npc(npc: dict[str, Any]) -> bool:
    condition = str(npc.get("condition", "")).lower()
    return npc.get("alive") is False or condition in {"dead", "incapacitated"}


def _status_effects(npc: dict[str, Any]) -> set[str]:
    return set(_string_list(npc.get("status_effects")))


def _quest_search_text(quest: dict[str, Any]) -> str:
    parts = [
        str(quest.get("id", "")),
        str(quest.get("title", "")),
        str(quest.get("description", "")),
        " ".join(_string_list(quest.get("tags"))),
    ]
    for stage in quest.get("stages", []):
        if isinstance(stage, dict):
            parts.extend(
                [
                    str(stage.get("id", "")),
                    str(stage.get("title", "")),
                    str(stage.get("description", "")),
                    " ".join(_string_list(stage.get("objectives"))),
                    " ".join(_string_list(stage.get("next_stages"))),
                ]
            )
    for trigger in _quest_triggers(quest):
        parts.append(str(trigger))
    return " ".join(parts).lower()


def _quest_triggers(quest: dict[str, Any]) -> list[dict[str, Any]]:
    triggers = quest.get("triggers", [])
    return [trigger for trigger in triggers if isinstance(trigger, dict)] if isinstance(triggers, list) else []


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _exits(location: dict[str, Any]) -> dict[str, str]:
    exits = location.get("exits", {})
    if not isinstance(exits, dict):
        return {}
    return {str(direction): str(target) for direction, target in exits.items() if target}


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
    if blockers or errors:
        actions.append("Review lethal encounters, quest-critical NPC death paths, and required fallback triggers.")
    if warnings:
        actions.append("Review combat rewards, flee warnings, public combat consequences, and status effect resolution.")
    return actions
