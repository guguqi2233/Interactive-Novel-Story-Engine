from typing import Any

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.world_state import FactVisibility, QuestVisibility
from app.engine.content.world_loader import MapVisibility, WorldLoader
from app.playtesting.runner import PlaytestReport
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.scenarios.regression import ScenarioRegressionRun


class ContentCoverageRequest(BaseModel):
    events: list[Event] = Field(default_factory=list)
    playtest_reports: list[PlaytestReport] = Field(default_factory=list)
    scenario_reports: list[ScenarioRegressionRun] = Field(default_factory=list)


class ContentCoverageSummary(BaseModel):
    total: int = 0
    covered: int = 0
    uncovered: int = 0
    coverage_percent: float = 0.0
    covered_ids: list[str] = Field(default_factory=list)
    uncovered_ids: list[str] = Field(default_factory=list)
    safe_summary: str = ""


class ContentCoverageReport(BaseModel):
    world_id: str
    locations: ContentCoverageSummary
    npcs: ContentCoverageSummary
    items: ContentCoverageSummary
    quests: ContentCoverageSummary
    facts: ContentCoverageSummary
    factions: ContentCoverageSummary
    rumors: ContentCoverageSummary
    crimes: ContentCoverageSummary
    combat_encounters: ContentCoverageSummary
    shops_trade: ContentCoverageSummary
    hidden_entities_redacted: dict[str, int] = Field(default_factory=dict)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


class _ObservedCoverage(BaseModel):
    locations: set[str] = Field(default_factory=set)
    npcs_seen: set[str] = Field(default_factory=set)
    npcs_talked: set[str] = Field(default_factory=set)
    items: set[str] = Field(default_factory=set)
    quests: set[str] = Field(default_factory=set)
    quest_stages: set[str] = Field(default_factory=set)
    facts: set[str] = Field(default_factory=set)
    factions: set[str] = Field(default_factory=set)
    rumors: set[str] = Field(default_factory=set)
    crimes: set[str] = Field(default_factory=set)
    combat_encounters: set[str] = Field(default_factory=set)
    shops_trade: set[str] = Field(default_factory=set)


def analyze_content_coverage(
    world_id: str,
    *,
    worlds_root: str = "worlds",
    events: list[Event] | None = None,
    playtest_reports: list[PlaytestReport] | None = None,
    scenario_reports: list[ScenarioRegressionRun] | None = None,
) -> ContentCoverageReport:
    pack = WorldLoader(worlds_root).load(world_id)
    observed = _collect_observed(
        events or [],
        playtest_reports or [],
        scenario_reports or [],
        start_location_id=pack.manifest.start_location_id,
    )

    visible_locations, hidden_locations = _visible_location_ids(pack)
    visible_npcs, hidden_npcs = _visible_npc_ids(pack)
    visible_items, hidden_items = _visible_item_ids(pack)
    visible_quests, hidden_quests = _visible_quest_stage_ids(pack)
    visible_facts, hidden_facts = _visible_fact_ids(pack)
    visible_factions, hidden_factions = _visible_faction_ids(pack)
    visible_rumors, hidden_rumors = _visible_rumor_ids(pack)
    visible_shops, hidden_shops = _visible_shop_ids(pack)

    report = ContentCoverageReport(
        world_id=world_id,
        locations=_summary(visible_locations, observed.locations, "locations"),
        npcs=_summary(visible_npcs, observed.npcs_seen | observed.npcs_talked, "NPCs"),
        items=_summary(visible_items, observed.items, "items"),
        quests=_summary(visible_quests, observed.quests | observed.quest_stages, "quest stages"),
        facts=_summary(visible_facts, observed.facts, "facts"),
        factions=_summary(visible_factions, observed.factions, "factions"),
        rumors=_summary(visible_rumors, observed.rumors, "rumors"),
        crimes=_summary(_configured_or_observed_ids(observed.crimes), observed.crimes, "crime paths"),
        combat_encounters=_summary(
            _configured_or_observed_ids(observed.combat_encounters),
            observed.combat_encounters,
            "combat paths",
        ),
        shops_trade=_summary(visible_shops, observed.shops_trade, "shop/trade paths"),
        hidden_entities_redacted={
            "locations": len(hidden_locations),
            "npcs": len(hidden_npcs),
            "items": len(hidden_items),
            "quests": len(hidden_quests),
            "facts": len(hidden_facts),
            "factions": len(hidden_factions),
            "rumors": len(hidden_rumors),
            "shops_trade": len(hidden_shops),
        },
        quality_report=WorldQualityReport(world_id=world_id),
    )
    report.quality_report = _to_quality_report(report)
    return report


def _collect_observed(
    events: list[Event],
    playtest_reports: list[PlaytestReport],
    scenario_reports: list[ScenarioRegressionRun],
    *,
    start_location_id: str,
) -> _ObservedCoverage:
    observed = _ObservedCoverage(locations={start_location_id})
    for event in sorted(events, key=lambda item: (item.turn, item.event_id)):
        _observe_event(observed, event)
    for report in playtest_reports:
        observed.locations.add(report.final_state_summary.location_id)
        for action in report.actions_taken:
            _observe_action(observed, action.action_type, action.result, action.input_text)
    for scenario in scenario_reports:
        for result in scenario.case_results:
            for fact_id in result.actual_summary.get("known_facts", []):
                observed.facts.add(str(fact_id))
            for item_id in result.actual_summary.get("inventory", []):
                observed.items.add(str(item_id))
            for quest_id, stage in result.actual_summary.get("quest_states", {}).items():
                observed.quests.add(str(quest_id))
                observed.quest_stages.add(f"{quest_id}:{stage}")
    return observed


def _observe_event(observed: _ObservedCoverage, event: Event) -> None:
    if event.target_id:
        if event.action_type in {"talk", "talk_to_npc", "npc_talked"}:
            observed.npcs_talked.add(event.target_id)
        elif event.action_type in {"buy", "sell", "trade"}:
            observed.shops_trade.add(event.target_id)
        else:
            observed.npcs_seen.add(event.target_id)
    _observe_action(observed, event.action_type, event.result, event.input_text or "")
    for delta in event.state_deltas:
        path = delta.path
        value = str(delta.value or "")
        for prefix, bucket in [
            ("player.location_id", observed.locations),
            ("objects.", observed.items),
            ("quests.", observed.quests),
            ("facts.", observed.facts),
            ("factions.", observed.factions),
            ("rumors.", observed.rumors),
            ("crimes.", observed.crimes),
            ("combats.", observed.combat_encounters),
        ]:
            if path.startswith(prefix):
                entity_id = _entity_id_from_delta_path(path, prefix)
                if entity_id:
                    bucket.add(entity_id)
        if path == "player.location_id" and value:
            observed.locations.add(value)
        if path.startswith("quests.") and ".current_stage" in path:
            parts = path.split(".")
            if len(parts) >= 3:
                observed.quest_stages.add(f"{parts[1]}:{value}")


def _observe_action(observed: _ObservedCoverage, action_type: str, result: str, input_text: str) -> None:
    normalized = f"{action_type} {result} {input_text}".lower()
    if action_type == "move":
        for token in normalized.replace(",", " ").split():
            observed.locations.add(token)
    if action_type in {"talk", "talk_to_npc"}:
        observed.npcs_talked.add(_last_token(normalized))
    if action_type in {"use_item", "search"}:
        observed.items.add(_last_token(normalized))
    if action_type in {"buy", "sell"}:
        observed.shops_trade.add("trade")
    if action_type in {"attack", "defend", "flee"}:
        observed.combat_encounters.add("combat")
    if "rumor" in normalized:
        observed.rumors.add("rumor")
    if "crime" in normalized or "theft" in normalized:
        observed.crimes.add("crime")


def _visible_location_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible: set[str] = set()
    hidden: set[str] = set()
    for location in pack.locations:
        if location.visual and location.visual.visibility == MapVisibility.HIDDEN:
            hidden.add(location.id)
        else:
            visible.add(location.id)
    return visible, hidden


def _visible_npc_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {npc.id for npc in pack.npcs if not npc.hidden and npc.visible}
    hidden = {npc.id for npc in pack.npcs if npc.hidden or not npc.visible}
    return visible, hidden


def _visible_item_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {item.id for item in pack.items if not item.hidden and item.visible}
    hidden = {item.id for item in pack.items if item.hidden or not item.visible}
    return visible, hidden


def _visible_quest_stage_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible: set[str] = set()
    hidden: set[str] = set()
    for quest in pack.quests:
        target = visible if quest.visibility == QuestVisibility.PUBLIC else hidden
        target.add(quest.id)
        for stage in quest.stages:
            target.add(f"{quest.id}:{stage.id}")
    return visible, hidden


def _visible_fact_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {fact.id for fact in pack.facts if fact.visibility == FactVisibility.PUBLIC}
    hidden = {fact.id for fact in pack.facts if fact.visibility != FactVisibility.PUBLIC}
    return visible, hidden


def _visible_faction_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {faction.id for faction in pack.factions if faction.known_by_player}
    hidden = {faction.id for faction in pack.factions if not faction.known_by_player}
    return visible, hidden


def _visible_rumor_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {rumor.id for rumor in pack.rumors if rumor.known_by_player}
    hidden = {rumor.id for rumor in pack.rumors if not rumor.known_by_player}
    return visible, hidden


def _visible_shop_ids(pack: Any) -> tuple[set[str], set[str]]:
    visible = {npc.id for npc in pack.npcs if npc.merchant and not npc.hidden and npc.visible}
    hidden = {npc.id for npc in pack.npcs if npc.merchant and (npc.hidden or not npc.visible)}
    return visible, hidden


def _summary(configured: set[str], observed: set[str], label: str) -> ContentCoverageSummary:
    covered_ids = sorted(configured & observed)
    uncovered_ids = sorted(configured - observed)
    total = len(configured)
    covered = len(covered_ids)
    percent = round((covered / total) * 100, 2) if total else 100.0
    return ContentCoverageSummary(
        total=total,
        covered=covered,
        uncovered=len(uncovered_ids),
        coverage_percent=percent,
        covered_ids=covered_ids,
        uncovered_ids=uncovered_ids,
        safe_summary=f"{covered}/{total} {label} covered",
    )


def _configured_or_observed_ids(observed: set[str]) -> set[str]:
    return set(observed) if observed else set()


def _to_quality_report(report: ContentCoverageReport) -> WorldQualityReport:
    summaries = [
        report.locations,
        report.npcs,
        report.items,
        report.quests,
        report.facts,
        report.factions,
        report.rumors,
        report.crimes,
        report.combat_encounters,
        report.shops_trade,
    ]
    metrics = [
        QualityMetric(
            name=f"content_coverage_{name}",
            value=summary.coverage_percent,
            unit="percent",
            category="content_coverage",
            threshold=50,
            status=QualityMetricStatus.WARNING if summary.total and summary.coverage_percent < 50 else QualityMetricStatus.OK,
        )
        for name, summary in [
            ("locations", report.locations),
            ("npcs", report.npcs),
            ("items", report.items),
            ("quests", report.quests),
            ("facts", report.facts),
            ("factions", report.factions),
            ("rumors", report.rumors),
            ("crimes", report.crimes),
            ("combat", report.combat_encounters),
            ("shops_trade", report.shops_trade),
        ]
    ]
    issues = [
        QualityIssue(
            id=f"content_coverage:low:{index}",
            severity=QualityIssueSeverity.WARNING,
            category="content_coverage",
            message=f"Low coverage: {summary.safe_summary}.",
            safe_details={"coverage_percent": summary.coverage_percent},
        )
        for index, summary in enumerate(summaries)
        if summary.total and summary.coverage_percent < 50
    ]
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["content_coverage"],
        metrics=metrics,
        issues=issues,
        summary={
            "average_coverage_percent": round(sum(item.coverage_percent for item in summaries) / len(summaries), 2),
            "hidden_entities_redacted": report.hidden_entities_redacted,
        },
        recommended_actions=["Run scenario regression or playtests to cover uncovered content."] if issues else [],
    ).normal_copy()


def _entity_id_from_delta_path(path: str, prefix: str) -> str:
    if prefix.endswith("."):
        remainder = path[len(prefix):]
        return remainder.split(".", 1)[0]
    return ""


def _last_token(value: str) -> str:
    tokens = [token for token in value.replace(",", " ").split() if token]
    return tokens[-1] if tokens else ""
