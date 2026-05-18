from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.world_state import QuestTriggerType
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class ScheduleConflictAnalysisRequest(BaseModel):
    include_debug_details: bool = False


class ScheduleConflictReport(BaseModel):
    world_id: str
    total_npcs: int = 0
    scheduled_npcs: int = 0
    invalid_schedule_locations: list[QualityIssue] = Field(default_factory=list)
    unreachable_schedule_locations: list[QualityIssue] = Field(default_factory=list)
    overlapping_time_blocks: list[QualityIssue] = Field(default_factory=list)
    missing_default_schedules: list[QualityIssue] = Field(default_factory=list)
    quest_required_npc_unavailable: list[QualityIssue] = Field(default_factory=list)
    merchant_unavailable_trade_objectives: list[QualityIssue] = Field(default_factory=list)
    npc_goal_location_mismatches: list[QualityIssue] = Field(default_factory=list)
    inactive_state_schedule_conflicts: list[QualityIssue] = Field(default_factory=list)
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


class _ScheduleContent(BaseModel):
    world_path: Path
    start_location_id: str
    locations: list[dict[str, Any]] = Field(default_factory=list)
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_ScheduleContent":
        manifest = _read_yaml_file(world_path / "manifest.yaml")
        return cls(
            world_path=world_path,
            start_location_id=str(manifest.get("start_location_id", "")),
            locations=_read_yaml_list(world_path / "locations.yaml", "locations"),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            items=_read_yaml_list(world_path / "items.yaml", "items"),
            quests=_read_yaml_list(world_path / "quests.yaml", "quests"),
        )


_ISSUE_FIELDS = [
    "invalid_schedule_locations",
    "unreachable_schedule_locations",
    "overlapping_time_blocks",
    "missing_default_schedules",
    "quest_required_npc_unavailable",
    "merchant_unavailable_trade_objectives",
    "npc_goal_location_mismatches",
    "inactive_state_schedule_conflicts",
]


def analyze_schedule_conflicts(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
) -> ScheduleConflictReport:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)
    content = _ScheduleContent.load(world_path)
    location_ids = {str(location.get("id")) for location in content.locations if location.get("id")}
    reachable_locations = _reachable_locations(content.start_location_id, content.locations)
    quest_required_npcs = _quest_required_npcs(content.quests)
    required_shop_items = _quest_required_items(content.quests)
    merchants_by_item = _merchants_by_item(content.npcs)

    report = ScheduleConflictReport(
        world_id=world_id,
        total_npcs=len([npc for npc in content.npcs if npc.get("id")]),
        scheduled_npcs=len([npc for npc in content.npcs if _schedule(npc)]),
        quality_report=WorldQualityReport(world_id=world_id),
    )

    for npc in sorted(content.npcs, key=lambda item: str(item.get("id", ""))):
        _detect_missing_default_schedule(report, npc, quest_required_npcs, required_shop_items, merchants_by_item)
        _detect_invalid_and_unreachable_locations(report, npc, location_ids, reachable_locations)
        _detect_overlapping_time_blocks(report, npc)
        _detect_required_npc_availability(report, npc, quest_required_npcs, reachable_locations)
        _detect_goal_location_mismatch(report, npc)
        _detect_inactive_state_with_schedule(report, npc)

    _detect_merchant_trade_availability(report, content.npcs, required_shop_items, merchants_by_item, reachable_locations)
    report.quality_report = schedule_conflict_report_to_quality_report(report)
    return report


def schedule_conflict_report_to_quality_report(report: ScheduleConflictReport) -> WorldQualityReport:
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
        categories=["schedule_conflict"],
        metrics=[
            QualityMetric(name="total_npcs", value=report.total_npcs, category="schedule_conflict", status=QualityMetricStatus.OK),
            QualityMetric(name="scheduled_npcs", value=report.scheduled_npcs, category="schedule_conflict", status=QualityMetricStatus.OK),
            QualityMetric(name="schedule_conflict_issues", value=len(issues), category="schedule_conflict", threshold=0, status=status),
            QualityMetric(name="schedule_conflict_errors", value=error_count, category="schedule_conflict", threshold=0, status=QualityMetricStatus.ERROR if error_count else QualityMetricStatus.OK),
            QualityMetric(name="schedule_conflict_warnings", value=warning_count, category="schedule_conflict", threshold=0, status=QualityMetricStatus.WARNING if warning_count else QualityMetricStatus.OK),
        ],
        issues=issues,
        summary={
            "total_npcs": report.total_npcs,
            "scheduled_npcs": report.scheduled_npcs,
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(blocker_count, error_count, warning_count),
    )


def _detect_invalid_and_unreachable_locations(
    report: ScheduleConflictReport,
    npc: dict[str, Any],
    location_ids: set[str],
    reachable_locations: set[str],
) -> None:
    npc_id = str(npc.get("id", ""))
    for index, entry in enumerate(_schedule(npc)):
        location_id = str(entry.get("location_id", ""))
        if location_id not in location_ids:
            report.invalid_schedule_locations.append(
                _npc_issue(
                    npc=npc,
                    code="schedule_location_missing",
                    severity=QualityIssueSeverity.ERROR,
                    message="NPC schedule references a missing location id.",
                    safe_details={"location_id": location_id, "schedule_index": index},
                    path=f"npcs.{npc_id}.schedule[{index}].location_id",
                )
            )
        elif location_id not in reachable_locations:
            report.unreachable_schedule_locations.append(
                _npc_issue(
                    npc=npc,
                    code="schedule_location_unreachable",
                    severity=QualityIssueSeverity.WARNING,
                    message="NPC schedule uses a location that is not reachable from the start location.",
                    safe_details={"location_id": location_id, "schedule_index": index},
                    path=f"npcs.{npc_id}.schedule[{index}].location_id",
                )
            )


def _detect_overlapping_time_blocks(report: ScheduleConflictReport, npc: dict[str, Any]) -> None:
    npc_id = str(npc.get("id", ""))
    seen: dict[str, set[tuple[str, str]]] = {}
    for entry in _schedule(npc):
        time_of_day = str(entry.get("time_of_day", ""))
        signature = (str(entry.get("location_id", "")), str(entry.get("activity", "")))
        seen.setdefault(time_of_day, set()).add(signature)
    for time_of_day, signatures in sorted(seen.items()):
        if time_of_day and len(signatures) > 1:
            report.overlapping_time_blocks.append(
                _npc_issue(
                    npc=npc,
                    code="schedule_overlapping_time_block",
                    severity=QualityIssueSeverity.WARNING,
                    message="NPC has multiple schedule entries for the same time block.",
                    safe_details={"time_of_day": time_of_day},
                    path=f"npcs.{npc_id}.schedule.{time_of_day}",
                )
            )


def _detect_missing_default_schedule(
    report: ScheduleConflictReport,
    npc: dict[str, Any],
    quest_required_npcs: set[str],
    required_shop_items: set[str],
    merchants_by_item: dict[str, set[str]],
) -> None:
    npc_id = str(npc.get("id", ""))
    schedule = _schedule(npc)
    if schedule:
        return
    is_merchant_for_required_item = any(npc_id in merchants_by_item.get(item_id, set()) for item_id in required_shop_items)
    if npc_id in quest_required_npcs or bool(npc.get("merchant")) or _goal_location_targets(npc) or is_merchant_for_required_item:
        report.missing_default_schedules.append(
            _npc_issue(
                npc=npc,
                code="npc_missing_default_schedule",
                severity=QualityIssueSeverity.WARNING,
                message="Important NPC has no schedule entries; availability may be underspecified.",
                safe_details={"merchant": bool(npc.get("merchant")), "quest_required": npc_id in quest_required_npcs},
                path=f"npcs.{npc_id}.schedule",
            )
        )


def _detect_required_npc_availability(
    report: ScheduleConflictReport,
    npc: dict[str, Any],
    quest_required_npcs: set[str],
    reachable_locations: set[str],
) -> None:
    npc_id = str(npc.get("id", ""))
    if npc_id not in quest_required_npcs:
        return
    possible_locations = _npc_possible_locations(npc)
    if possible_locations and possible_locations.isdisjoint(reachable_locations):
        report.quest_required_npc_unavailable.append(
            _npc_issue(
                npc=npc,
                code="quest_required_npc_unavailable",
                severity=QualityIssueSeverity.ERROR,
                message="Quest-required NPC is never scheduled or placed in a reachable location.",
                safe_details={},
                path=f"npcs.{npc_id}.schedule",
            )
        )


def _detect_merchant_trade_availability(
    report: ScheduleConflictReport,
    npcs: list[dict[str, Any]],
    required_shop_items: set[str],
    merchants_by_item: dict[str, set[str]],
    reachable_locations: set[str],
) -> None:
    npc_by_id = {str(npc.get("id")): npc for npc in npcs if npc.get("id")}
    for item_id in sorted(required_shop_items):
        for npc_id in sorted(merchants_by_item.get(item_id, set())):
            npc = npc_by_id.get(npc_id)
            if npc is None:
                continue
            if _npc_possible_locations(npc).isdisjoint(reachable_locations):
                report.merchant_unavailable_trade_objectives.append(
                    _npc_issue(
                        npc=npc,
                        code="merchant_unavailable_for_trade_objective",
                        severity=QualityIssueSeverity.ERROR,
                        message="Quest-required shop item belongs to a merchant who is never reachable.",
                        safe_details={"item_id": item_id},
                        path=f"npcs.{npc_id}.shop_inventory",
                    )
                )


def _detect_goal_location_mismatch(report: ScheduleConflictReport, npc: dict[str, Any]) -> None:
    npc_id = str(npc.get("id", ""))
    schedule_locations = {str(entry.get("location_id", "")) for entry in _schedule(npc) if entry.get("location_id")}
    if not schedule_locations:
        schedule_locations = {str(npc.get("location_id", ""))}
    for goal_id, target_location in _goal_location_targets(npc).items():
        if target_location not in schedule_locations:
            report.npc_goal_location_mismatches.append(
                _npc_issue(
                    npc=npc,
                    code="npc_goal_location_not_scheduled",
                    severity=QualityIssueSeverity.WARNING,
                    message="NPC goal wants a location the schedule never reaches.",
                    safe_details={"goal_id": goal_id, "location_id": target_location},
                    path=f"npcs.{npc_id}.goals.{goal_id}.desired_state",
                )
            )


def _detect_inactive_state_with_schedule(report: ScheduleConflictReport, npc: dict[str, Any]) -> None:
    npc_id = str(npc.get("id", ""))
    if not _schedule(npc):
        return
    condition = str(npc.get("condition", "")).lower()
    if npc.get("alive") is False or condition in {"dead", "incapacitated"}:
        report.inactive_state_schedule_conflicts.append(
            _npc_issue(
                npc=npc,
                code="inactive_npc_has_active_schedule",
                severity=QualityIssueSeverity.WARNING,
                message="NPC is initially dead or incapacitated but still has an active schedule.",
                safe_details={"condition": condition or "dead"},
                path=f"npcs.{npc_id}.schedule",
            )
        )


def _quest_required_npcs(quests: list[dict[str, Any]]) -> set[str]:
    return {
        str(trigger.get("id"))
        for quest in quests
        for trigger in quest.get("triggers", [])
        if isinstance(trigger, dict)
        and trigger.get("type") == QuestTriggerType.NPC_TALKED
        and trigger.get("id")
    }


def _quest_required_items(quests: list[dict[str, Any]]) -> set[str]:
    return {
        str(trigger.get("id"))
        for quest in quests
        for trigger in quest.get("triggers", [])
        if isinstance(trigger, dict)
        and trigger.get("type") == QuestTriggerType.ITEM_ACQUIRED
        and trigger.get("id")
    }


def _merchants_by_item(npcs: list[dict[str, Any]]) -> dict[str, set[str]]:
    merchants: dict[str, set[str]] = {}
    for npc in npcs:
        npc_id = str(npc.get("id", ""))
        if not npc_id or not bool(npc.get("merchant")):
            continue
        for item_id in _string_list(npc.get("shop_inventory")):
            merchants.setdefault(item_id, set()).add(npc_id)
    return merchants


def _goal_location_targets(npc: dict[str, Any]) -> dict[str, str]:
    targets: dict[str, str] = {}
    for goal in npc.get("goals", []):
        if not isinstance(goal, dict):
            continue
        goal_id = str(goal.get("id", ""))
        desired = goal.get("desired_state")
        if not isinstance(desired, dict) or not goal_id:
            continue
        target = desired.get("location_id") or desired.get("location")
        if isinstance(target, str) and target:
            targets[goal_id] = target
    return targets


def _npc_possible_locations(npc: dict[str, Any]) -> set[str]:
    locations = {str(npc.get("location_id", ""))}
    for entry in _schedule(npc):
        if entry.get("location_id"):
            locations.add(str(entry.get("location_id")))
    return {location_id for location_id in locations if location_id}


def _schedule(npc: dict[str, Any]) -> list[dict[str, Any]]:
    schedule = npc.get("schedule", [])
    return [entry for entry in schedule if isinstance(entry, dict)] if isinstance(schedule, list) else []


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
        id=f"schedule_conflict:{'hidden' if hidden else npc_id}:{code}:{safe_details.get('time_of_day', safe_details.get('location_id', 'npc'))}",
        severity=severity,
        category="schedule_conflict",
        file="npcs.yaml",
        path="npcs.yaml" if hidden else path,
        entity_id=None if hidden else npc_id,
        message=message,
        safe_details={"code": code, **safe_details},
        hidden_details_debug_only={"npc_id": npc_id, "path": path} if hidden else None,
    )


def _is_hidden_npc(npc: dict[str, Any]) -> bool:
    return bool(npc.get("hidden")) and "player" not in _string_list(npc.get("discovered_by"))


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
        actions.append("Fix schedule references and required NPC availability before relying on regression playtests.")
    if warnings:
        actions.append("Review overlapping schedules, missing default schedules, and goal/schedule mismatches.")
    return actions
