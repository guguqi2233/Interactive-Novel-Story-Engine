from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.event_log import Event, EventLog
from app.playtesting.runner import PlaytestReport, PlaytestScenarioReport
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class NPCBehaviorCoverageRequest(BaseModel):
    events: list[Event] = Field(default_factory=list)
    playtest_reports: list[PlaytestReport] = Field(default_factory=list)
    scenario_reports: list[PlaytestScenarioReport] = Field(default_factory=list)


class NPCBehaviorCoverageReport(BaseModel):
    world_id: str
    total_npcs: int = 0
    hidden_npcs: int = 0
    npcs_seen_by_player: int = 0
    npcs_talked_to: int = 0
    npcs_with_goals: int = 0
    goals_total: int = 0
    goals_activated: int = 0
    goals_completed: int = 0
    goals_failed: int = 0
    goals_blocked: int = 0
    planning_actions_executed: dict[str, int] = Field(default_factory=dict)
    schedule_moves_executed: int = 0
    reactions_triggered: int = 0
    rumor_spread_actions: int = 0
    crime_reports: int = 0
    combat_participation: int = 0
    unused_goal_warnings: list[QualityIssue] = Field(default_factory=list)
    unreachable_npc_warnings: list[QualityIssue] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["unused_goal_warnings"] = [
            issue.normal_copy().model_dump(mode="json", exclude_none=True)
            for issue in self.unused_goal_warnings
        ]
        payload["unreachable_npc_warnings"] = [
            issue.normal_copy().model_dump(mode="json", exclude_none=True)
            for issue in self.unreachable_npc_warnings
        ]
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


class _NPCContent(BaseModel):
    world_path: Path
    start_location_id: str
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_NPCContent":
        manifest = _read_yaml_file(world_path / "manifest.yaml")
        return cls(
            world_path=world_path,
            start_location_id=str(manifest.get("start_location_id", "")),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            locations=_read_yaml_list(world_path / "locations.yaml", "locations"),
        )


class _ObservedNPCBehavior(BaseModel):
    seen_npcs: set[str] = Field(default_factory=set)
    talked_npcs: set[str] = Field(default_factory=set)
    activated_goals: set[tuple[str, str]] = Field(default_factory=set)
    completed_goals: set[tuple[str, str]] = Field(default_factory=set)
    failed_goals: set[tuple[str, str]] = Field(default_factory=set)
    blocked_goals: set[tuple[str, str]] = Field(default_factory=set)
    planning_actions: dict[str, int] = Field(default_factory=dict)
    planning_goal_ids: set[tuple[str, str]] = Field(default_factory=set)
    schedule_moves: int = 0
    reactions: int = 0
    rumor_spreads: int = 0
    crime_reports: int = 0
    combat_participation: int = 0


def analyze_npc_behavior_coverage(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    event_log: EventLog | None = None,
    events: list[Event] | None = None,
    playtest_reports: list[PlaytestReport] | None = None,
    scenario_reports: list[PlaytestScenarioReport] | None = None,
) -> NPCBehaviorCoverageReport:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)

    content = _NPCContent.load(world_path)
    all_events = list(events or [])
    if event_log is not None:
        all_events.extend(event_log.list_events())

    observed = _observe_events(all_events)
    _observe_playtest_reports(observed, playtest_reports or [], scenario_reports or [])
    npc_ids = {str(npc.get("id")) for npc in content.npcs if npc.get("id")}
    reachable_locations = _reachable_locations(content.start_location_id, content.locations)
    npcs_with_goals = [npc for npc in content.npcs if _goal_ids(npc)]
    hidden_npcs = {str(npc.get("id")) for npc in content.npcs if _is_hidden_npc(npc)}
    unused_goal_warnings = _unused_goal_warnings(content.npcs, observed)
    unreachable_npc_warnings = _unreachable_npc_warnings(content.npcs, reachable_locations)

    report = NPCBehaviorCoverageReport(
        world_id=world_id,
        total_npcs=len(npc_ids),
        hidden_npcs=len(hidden_npcs),
        npcs_seen_by_player=len(observed.seen_npcs & npc_ids),
        npcs_talked_to=len(observed.talked_npcs & npc_ids),
        npcs_with_goals=len(npcs_with_goals),
        goals_total=sum(len(_goal_ids(npc)) for npc in content.npcs),
        goals_activated=len(observed.activated_goals),
        goals_completed=len(observed.completed_goals),
        goals_failed=len(observed.failed_goals),
        goals_blocked=len(observed.blocked_goals),
        planning_actions_executed=dict(sorted(observed.planning_actions.items())),
        schedule_moves_executed=observed.schedule_moves,
        reactions_triggered=observed.reactions,
        rumor_spread_actions=observed.rumor_spreads,
        crime_reports=observed.crime_reports,
        combat_participation=observed.combat_participation,
        unused_goal_warnings=unused_goal_warnings,
        unreachable_npc_warnings=unreachable_npc_warnings,
        quality_report=WorldQualityReport(world_id=world_id),
    )
    report.quality_report = _quality_report_from_npc_coverage(report)
    return report


def _observe_events(events: list[Event]) -> _ObservedNPCBehavior:
    observed = _ObservedNPCBehavior()
    for event in sorted(events, key=lambda item: (item.turn, item.event_id)):
        _observe_event_header(observed, event)
        for delta in event.state_deltas:
            metadata = delta.metadata
            source = str(metadata.get("source", ""))
            npc_id = _metadata_npc_id(metadata) or _npc_id_from_path(delta.path)
            if npc_id and event.visible_to_player:
                observed.seen_npcs.add(npc_id)
            if source == "npc_goal":
                _observe_goal_delta(observed, metadata)
            if source == "npc_planning":
                _observe_planning_delta(observed, metadata)
            if source == "npc_schedule":
                observed.schedule_moves += 1
                if npc_id:
                    observed.seen_npcs.add(npc_id)
            if source == "npc_reaction":
                observed.reactions += 1
                reaction = str(metadata.get("reaction", ""))
                if reaction == "spread_rumor":
                    observed.rumor_spreads += 1
            if source == "combat":
                observed.combat_participation += 1
            if source == "npc_planning" and str(metadata.get("plan_type")) == "report_crime":
                observed.crime_reports += 1
    return observed


def _observe_event_header(observed: _ObservedNPCBehavior, event: Event) -> None:
    if event.visible_to_player and event.target_id:
        observed.seen_npcs.add(event.target_id)
    if event.action_type in {"talk", "talk_to_npc", "npc_talked"} and event.target_id:
        observed.talked_npcs.add(event.target_id)
    if event.action_type == "npc_planning" and not event.state_deltas:
        plan_type = event.result
        if plan_type:
            observed.planning_actions[plan_type] = observed.planning_actions.get(plan_type, 0) + 1
        if plan_type == "spread_rumor":
            observed.rumor_spreads += 1
        if plan_type == "report_crime":
            observed.crime_reports += 1
    if event.action_type in {"attack", "combat"}:
        observed.combat_participation += 1


def _observe_playtest_reports(
    observed: _ObservedNPCBehavior,
    playtest_reports: list[PlaytestReport],
    scenario_reports: list[PlaytestScenarioReport],
) -> None:
    for report in playtest_reports:
        for action in report.actions_taken:
            if action.action_type in {"talk", "talk_to_npc", "npc_talked"} and action.result:
                observed.planning_actions["player_talk_attempt"] = observed.planning_actions.get("player_talk_attempt", 0) + 1
            if action.action_type in {"attack", "combat"}:
                observed.combat_participation += 1
    for scenario_report in scenario_reports:
        _observe_playtest_reports(observed, [scenario_report.playtest_report], [])


def _observe_goal_delta(observed: _ObservedNPCBehavior, metadata: dict[str, Any]) -> None:
    npc_id = _metadata_npc_id(metadata)
    goal_id = str(metadata.get("goal_id", ""))
    status = str(metadata.get("status", ""))
    if not npc_id or not goal_id:
        return
    key = (npc_id, goal_id)
    if status == "active":
        observed.activated_goals.add(key)
    elif status == "completed":
        observed.completed_goals.add(key)
    elif status == "failed":
        observed.failed_goals.add(key)
    elif status == "blocked":
        observed.blocked_goals.add(key)


def _observe_planning_delta(observed: _ObservedNPCBehavior, metadata: dict[str, Any]) -> None:
    plan_type = str(metadata.get("plan_type", ""))
    if plan_type:
        observed.planning_actions[plan_type] = observed.planning_actions.get(plan_type, 0) + 1
    npc_id = _metadata_npc_id(metadata)
    goal_id = str(metadata.get("goal_id", ""))
    if npc_id and goal_id:
        observed.planning_goal_ids.add((npc_id, goal_id))
    if plan_type == "spread_rumor":
        observed.rumor_spreads += 1
    if plan_type == "report_crime":
        observed.crime_reports += 1


def _unused_goal_warnings(npcs: list[dict[str, Any]], observed: _ObservedNPCBehavior) -> list[QualityIssue]:
    covered_goals = (
        observed.activated_goals
        | observed.completed_goals
        | observed.failed_goals
        | observed.blocked_goals
        | observed.planning_goal_ids
    )
    warnings: list[QualityIssue] = []
    for npc in sorted(npcs, key=lambda item: str(item.get("id", ""))):
        npc_id = str(npc.get("id", ""))
        for goal_id in _goal_ids(npc):
            if (npc_id, goal_id) in covered_goals:
                continue
            warnings.append(
                _npc_issue(
                    npc=npc,
                    code="npc_goal_never_covered",
                    category="npc_behavior_coverage",
                    severity=QualityIssueSeverity.WARNING,
                    message="An NPC goal exists in content but was not covered by supplied events or playtests.",
                    safe_details={"goal_id": goal_id},
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}.goals.{goal_id}",
                )
            )
    return warnings


def _unreachable_npc_warnings(npcs: list[dict[str, Any]], reachable_locations: set[str]) -> list[QualityIssue]:
    warnings: list[QualityIssue] = []
    for npc in sorted(npcs, key=lambda item: str(item.get("id", ""))):
        npc_id = str(npc.get("id", ""))
        possible_locations = {str(npc.get("location_id", ""))}
        for entry in npc.get("schedule", []):
            if isinstance(entry, dict) and entry.get("location_id"):
                possible_locations.add(str(entry.get("location_id")))
        if possible_locations and possible_locations.isdisjoint(reachable_locations):
            warnings.append(
                _npc_issue(
                    npc=npc,
                    code="npc_never_reachable",
                    category="npc_behavior_coverage",
                    severity=QualityIssueSeverity.WARNING,
                    message="An NPC is never placed in a statically reachable location.",
                    safe_details={},
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}",
                )
            )
    return warnings


def _quality_report_from_npc_coverage(report: NPCBehaviorCoverageReport) -> WorldQualityReport:
    issues = [*report.unused_goal_warnings, *report.unreachable_npc_warnings]
    warning_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.WARNING)
    status = QualityMetricStatus.WARNING if warning_count else QualityMetricStatus.OK
    metrics = [
        QualityMetric(name="total_npcs", value=report.total_npcs, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="npcs_seen_by_player", value=report.npcs_seen_by_player, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="npcs_talked_to", value=report.npcs_talked_to, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="npcs_with_goals", value=report.npcs_with_goals, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="goals_total", value=report.goals_total, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="goals_activated", value=report.goals_activated, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="goals_completed", value=report.goals_completed, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="goals_failed", value=report.goals_failed, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="goals_blocked", value=report.goals_blocked, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="schedule_moves_executed", value=report.schedule_moves_executed, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="reactions_triggered", value=report.reactions_triggered, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="rumor_spread_actions", value=report.rumor_spread_actions, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="crime_reports", value=report.crime_reports, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="combat_participation", value=report.combat_participation, category="npc_behavior", status=QualityMetricStatus.OK),
        QualityMetric(name="npc_behavior_warnings", value=warning_count, category="npc_behavior", threshold=0, status=status),
    ]
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["npc_behavior"],
        metrics=metrics,
        issues=issues,
        summary={
            "total_npcs": report.total_npcs,
            "hidden_npcs": report.hidden_npcs,
            "npcs_seen_by_player": report.npcs_seen_by_player,
            "npcs_talked_to": report.npcs_talked_to,
            "goals_total": report.goals_total,
            "goals_activated": report.goals_activated,
            "planning_actions_executed": report.planning_actions_executed,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(warning_count),
    )


def _npc_issue(
    *,
    npc: dict[str, Any],
    code: str,
    category: str,
    severity: QualityIssueSeverity,
    message: str,
    safe_details: dict[str, Any],
    file: str,
    path: str,
) -> QualityIssue:
    npc_id = str(npc.get("id", ""))
    hidden = _is_hidden_npc(npc)
    details = {"code": code, **safe_details}
    return QualityIssue(
        id=f"{category}:{'hidden' if hidden else npc_id}:{code}:{safe_details.get('goal_id', 'npc')}",
        severity=severity,
        category=category,
        file=file,
        path=path if not hidden else file,
        entity_id=None if hidden else npc_id,
        message=message,
        safe_details=details,
        hidden_details_debug_only={"npc_id": npc_id, "path": path} if hidden else None,
    )


def _goal_ids(npc: dict[str, Any]) -> list[str]:
    goal_ids: list[str] = []
    for goal in npc.get("goals", []):
        if isinstance(goal, dict) and goal.get("id"):
            goal_ids.append(str(goal.get("id")))
        elif isinstance(goal, str):
            goal_ids.append(goal)
    return sorted(set(goal_ids))


def _reachable_locations(start_location_id: str, locations: list[dict[str, Any]]) -> set[str]:
    adjacency = {str(location.get("id", "")): set(_exits(location).values()) for location in locations}
    seen: set[str] = set()
    queue = [start_location_id] if start_location_id else []
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        queue.extend(sorted(adjacency.get(current, set()) - seen))
    return seen


def _exits(location: dict[str, Any]) -> dict[str, str]:
    exits = location.get("exits", {})
    if not isinstance(exits, dict):
        return {}
    return {str(direction): str(target) for direction, target in exits.items() if target}


def _metadata_npc_id(metadata: dict[str, Any]) -> str | None:
    npc_id = metadata.get("npc_id")
    return str(npc_id) if npc_id else None


def _npc_id_from_path(path: str) -> str | None:
    parts = path.split(".")
    if len(parts) >= 2 and parts[0] == "npcs":
        return parts[1]
    return None


def _is_hidden_npc(npc: dict[str, Any]) -> bool:
    return bool(npc.get("hidden")) and "player" not in _string_list(npc.get("discovered_by"))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _read_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
    data = _read_yaml_file(path)
    values = data.get(key, []) if isinstance(data, dict) else []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _recommended_actions(warnings: int) -> list[str]:
    if not warnings:
        return []
    return [
        "Add scenario regression or playtest coverage for unused NPC goals and unreachable NPCs.",
        "Review hidden NPC findings in debug-only reports without exposing hidden NPC details to normal reports.",
    ]
