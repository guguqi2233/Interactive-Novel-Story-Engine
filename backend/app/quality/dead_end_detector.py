from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.world_state import FactVisibility, QuestTriggerType
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class DeadEndCoverage(BaseModel):
    visited_locations: list[str] = Field(default_factory=list)
    acquired_items: list[str] = Field(default_factory=list)
    talked_npcs: list[str] = Field(default_factory=list)
    discovered_facts: list[str] = Field(default_factory=list)


class DeadEndAnalysisRequest(BaseModel):
    coverage: DeadEndCoverage | None = None


class DeadEndIssueRef(BaseModel):
    code: str
    severity: QualityIssueSeverity = QualityIssueSeverity.WARNING
    entity_type: str
    entity_id: str
    quest_id: str | None = None
    objective_id: str | None = None
    ref_id: str | None = None
    file: str | None = None
    path: str | None = None


class DeadEndAnalysis(BaseModel):
    world_id: str
    map_dead_ends: list[DeadEndIssueRef] = Field(default_factory=list)
    required_item_unreachable: list[DeadEndIssueRef] = Field(default_factory=list)
    required_npc_unreachable: list[DeadEndIssueRef] = Field(default_factory=list)
    required_fact_undiscoverable: list[DeadEndIssueRef] = Field(default_factory=list)
    quest_objective_missing_trigger: list[DeadEndIssueRef] = Field(default_factory=list)
    locked_door_without_key_path: list[DeadEndIssueRef] = Field(default_factory=list)
    merchant_item_unavailable: list[DeadEndIssueRef] = Field(default_factory=list)
    npc_blocking_quest_without_fallback: list[DeadEndIssueRef] = Field(default_factory=list)
    hidden_clue_never_discoverable: list[DeadEndIssueRef] = Field(default_factory=list)
    schedule_conflicts: list[DeadEndIssueRef] = Field(default_factory=list)
    playtest_coverage_gaps: list[DeadEndIssueRef] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


def analyze_dead_ends(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    coverage: DeadEndCoverage | None = None,
) -> DeadEndAnalysis:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)

    content = _WorldContent.load(world_path)
    analysis = DeadEndAnalysis(
        world_id=world_id,
        quality_report=WorldQualityReport(world_id=world_id),
    )
    reachable_locations = _reachable_locations(content.start_location_id, content.locations)
    quest_required_refs = _quest_required_refs(content.quests)

    _detect_map_dead_ends(analysis, content, reachable_locations, quest_required_refs["location"])
    _detect_required_items(analysis, content, reachable_locations, quest_required_refs["item"])
    _detect_required_npcs(analysis, content, reachable_locations, quest_required_refs["npc"])
    _detect_required_facts(analysis, content, quest_required_refs["fact"])
    _detect_objective_trigger_gaps(analysis, content)
    _detect_locked_location_access(analysis, content, reachable_locations, quest_required_refs["location"])
    _detect_merchant_inventory(analysis, content, reachable_locations, quest_required_refs["item"])
    _detect_npc_life_blockers(analysis, content, quest_required_refs["npc"])
    _detect_schedule_conflicts(analysis, content, reachable_locations, quest_required_refs["npc"])
    _detect_playtest_coverage_gaps(analysis, quest_required_refs, coverage or DeadEndCoverage())

    analysis.quality_report = dead_end_analysis_to_quality_report(analysis)
    return analysis


def dead_end_analysis_to_quality_report(analysis: DeadEndAnalysis) -> WorldQualityReport:
    buckets: list[tuple[list[DeadEndIssueRef], str]] = [
        (analysis.map_dead_ends, "dead_end_map"),
        (analysis.required_item_unreachable, "dead_end_required_item"),
        (analysis.required_npc_unreachable, "dead_end_required_npc"),
        (analysis.required_fact_undiscoverable, "dead_end_required_fact"),
        (analysis.quest_objective_missing_trigger, "dead_end_quest_objective"),
        (analysis.locked_door_without_key_path, "dead_end_locked_access"),
        (analysis.merchant_item_unavailable, "dead_end_merchant_item"),
        (analysis.npc_blocking_quest_without_fallback, "dead_end_npc_blocker"),
        (analysis.hidden_clue_never_discoverable, "dead_end_hidden_clue"),
        (analysis.schedule_conflicts, "dead_end_schedule"),
        (analysis.playtest_coverage_gaps, "dead_end_playtest_coverage"),
    ]
    issues = [
        _quality_issue_from_ref(ref, category)
        for bucket, category in buckets
        for ref in bucket
    ]
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
        world_id=analysis.world_id,
        categories=["dead_end_detection"],
        metrics=[
            QualityMetric(
                name="dead_end_issues",
                value=len(issues),
                category="dead_end_detection",
                threshold=0,
                status=status,
            ),
            QualityMetric(
                name="dead_end_blockers",
                value=blocker_count,
                category="dead_end_detection",
                threshold=0,
                status=QualityMetricStatus.BLOCKER if blocker_count else QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="dead_end_warnings",
                value=warning_count,
                category="dead_end_detection",
                status=QualityMetricStatus.WARNING if warning_count else QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary={
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(blocker_count, error_count, warning_count),
    )


class _WorldContent(BaseModel):
    world_path: Path
    start_location_id: str
    locations: list[dict[str, Any]] = Field(default_factory=list)
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_WorldContent":
        manifest = _read_yaml_file(world_path / "manifest.yaml")
        return cls(
            world_path=world_path,
            start_location_id=str(manifest.get("start_location_id", "")),
            locations=_read_yaml_list(world_path / "locations.yaml", "locations"),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            items=_read_yaml_list(world_path / "items.yaml", "items"),
            quests=_read_yaml_list(world_path / "quests.yaml", "quests"),
            facts=_read_yaml_list(world_path / "facts.yaml", "facts"),
        )

    @property
    def location_by_id(self) -> dict[str, dict[str, Any]]:
        return _by_id(self.locations)

    @property
    def npc_by_id(self) -> dict[str, dict[str, Any]]:
        return _by_id(self.npcs)

    @property
    def item_by_id(self) -> dict[str, dict[str, Any]]:
        return _by_id(self.items)

    @property
    def fact_by_id(self) -> dict[str, dict[str, Any]]:
        return _by_id(self.facts)


def _detect_map_dead_ends(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_locations: set[str],
) -> None:
    for location in sorted(content.locations, key=lambda item: str(item.get("id", ""))):
        location_id = str(location.get("id", ""))
        exits = _exits(location)
        if location_id not in reachable_locations:
            analysis.map_dead_ends.append(
                _ref(
                    code="location_unreachable_from_start",
                    severity=QualityIssueSeverity.ERROR if location_id in required_locations else QualityIssueSeverity.WARNING,
                    entity_type="location",
                    entity_id=location_id,
                    file="locations.yaml",
                    path=f"locations.{location_id}",
                )
            )
        elif not exits and location_id != content.start_location_id:
            analysis.map_dead_ends.append(
                _ref(
                    code="map_dead_end",
                    severity=QualityIssueSeverity.WARNING,
                    entity_type="location",
                    entity_id=location_id,
                    file="locations.yaml",
                    path=f"locations.{location_id}",
                )
            )


def _detect_required_items(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_items: set[str],
) -> None:
    item_by_id = content.item_by_id
    for item_id in sorted(required_items):
        item = item_by_id.get(item_id)
        if item is None:
            analysis.required_item_unreachable.append(
                _ref(
                    code="required_item_missing",
                    severity=QualityIssueSeverity.BLOCKER,
                    entity_type="item",
                    entity_id=item_id,
                    ref_id=item_id,
                    file="quests.yaml",
                )
            )
            continue
        if not _item_reachable(item, content, reachable_locations):
            analysis.required_item_unreachable.append(
                _ref(
                    code="required_item_unreachable",
                    severity=QualityIssueSeverity.ERROR,
                    entity_type="item",
                    entity_id=item_id,
                    ref_id=item_id,
                    file="items.yaml",
                    path=f"items.{item_id}",
                )
            )
        if _is_hidden(item) and not _is_discoverable_item(item):
            analysis.required_item_unreachable.append(
                _ref(
                    code="required_item_hidden_without_discovery",
                    severity=QualityIssueSeverity.WARNING,
                    entity_type="item",
                    entity_id=item_id,
                    ref_id=item_id,
                    file="items.yaml",
                    path=f"items.{item_id}",
                )
            )


def _detect_required_npcs(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_npcs: set[str],
) -> None:
    npc_by_id = content.npc_by_id
    for npc_id in sorted(required_npcs):
        npc = npc_by_id.get(npc_id)
        if npc is None:
            analysis.required_npc_unreachable.append(
                _ref(
                    code="required_npc_missing",
                    severity=QualityIssueSeverity.BLOCKER,
                    entity_type="npc",
                    entity_id=npc_id,
                    ref_id=npc_id,
                    file="quests.yaml",
                )
            )
            continue
        location_id = str(npc.get("location_id", ""))
        schedule_locations = {
            str(entry.get("location_id"))
            for entry in npc.get("schedule", [])
            if isinstance(entry, dict) and entry.get("location_id")
        }
        possible_locations = {location_id} | schedule_locations
        if possible_locations and possible_locations.isdisjoint(reachable_locations):
            analysis.required_npc_unreachable.append(
                _ref(
                    code="required_npc_unreachable",
                    severity=QualityIssueSeverity.ERROR,
                    entity_type="npc",
                    entity_id=npc_id,
                    ref_id=npc_id,
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}",
                )
            )
        if bool(npc.get("hidden")) and "player" not in _string_list(npc.get("discovered_by")):
            analysis.required_npc_unreachable.append(
                _ref(
                    code="required_npc_hidden_without_discovery",
                    severity=QualityIssueSeverity.WARNING,
                    entity_type="npc",
                    entity_id=npc_id,
                    ref_id=npc_id,
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}",
                )
            )


def _detect_required_facts(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    required_facts: set[str],
) -> None:
    fact_by_id = content.fact_by_id
    for fact_id in sorted(required_facts):
        fact = fact_by_id.get(fact_id)
        if fact is None:
            analysis.required_fact_undiscoverable.append(
                _ref(
                    code="required_fact_missing",
                    severity=QualityIssueSeverity.BLOCKER,
                    entity_type="fact",
                    entity_id=fact_id,
                    ref_id=fact_id,
                    file="quests.yaml",
                )
            )
            continue
        visibility = str(fact.get("visibility", ""))
        known_by = _string_list(fact.get("known_by"))
        if visibility == FactVisibility.HIDDEN and "player" not in known_by and not _fact_has_discovery_path(fact):
            ref = _ref(
                code="required_fact_hidden_without_discovery",
                severity=QualityIssueSeverity.ERROR,
                entity_type="fact",
                entity_id=fact_id,
                ref_id=fact_id,
                file="facts.yaml",
                path=f"facts.{fact_id}",
            )
            analysis.required_fact_undiscoverable.append(ref)
            analysis.hidden_clue_never_discoverable.append(
                ref.model_copy(update={"code": "hidden_clue_never_discoverable"})
            )


def _detect_objective_trigger_gaps(analysis: DeadEndAnalysis, content: _WorldContent) -> None:
    for quest in sorted(content.quests, key=lambda item: str(item.get("id", ""))):
        quest_id = str(quest.get("id", ""))
        objective_ids = {
            str(objective)
            for stage in quest.get("stages", [])
            if isinstance(stage, dict)
            for objective in stage.get("objectives", [])
        }
        completed_objective_ids = {
            str(trigger.get("objective_id"))
            for trigger in quest.get("triggers", [])
            if isinstance(trigger, dict) and trigger.get("objective_id")
        }
        for objective_id in sorted(objective_ids - completed_objective_ids):
            analysis.quest_objective_missing_trigger.append(
                _ref(
                    code="quest_objective_missing_trigger",
                    severity=QualityIssueSeverity.WARNING,
                    entity_type="quest_objective",
                    entity_id=objective_id,
                    quest_id=quest_id,
                    objective_id=objective_id,
                    file="quests.yaml",
                    path=f"quests.{quest_id}.objectives.{objective_id}",
                )
            )


def _detect_locked_location_access(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_locations: set[str],
) -> None:
    for location_id in sorted(required_locations):
        location = content.location_by_id.get(location_id)
        if location is None:
            continue
        visual = location.get("visual") if isinstance(location.get("visual"), dict) else {}
        visibility = str(visual.get("visibility", "public"))
        tags = set(_string_list(visual.get("tags"))) | set(_string_list(location.get("tags")))
        looks_locked = visibility in {"hidden", "discoverable"} or "locked" in tags or "requires_key" in tags
        if not looks_locked:
            continue
        if not _has_access_item_for_location(content, location_id, reachable_locations):
            analysis.locked_door_without_key_path.append(
                _ref(
                    code="locked_location_without_access_path",
                    severity=QualityIssueSeverity.ERROR,
                    entity_type="location",
                    entity_id=location_id,
                    ref_id=location_id,
                    file="locations.yaml",
                    path=f"locations.{location_id}",
                )
            )


def _detect_merchant_inventory(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_items: set[str],
) -> None:
    item_ids = set(content.item_by_id)
    for npc in sorted(content.npcs, key=lambda item: str(item.get("id", ""))):
        npc_id = str(npc.get("id", ""))
        inventory = _string_list(npc.get("shop_inventory"))
        if inventory and not bool(npc.get("merchant")):
            analysis.merchant_item_unavailable.append(
                _ref(
                    code="shop_inventory_on_non_merchant",
                    severity=QualityIssueSeverity.WARNING,
                    entity_type="npc",
                    entity_id=npc_id,
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}.shop_inventory",
                )
            )
        for item_id in sorted(inventory):
            if item_id not in item_ids:
                analysis.merchant_item_unavailable.append(
                    _ref(
                        code="merchant_item_missing",
                        severity=QualityIssueSeverity.ERROR,
                        entity_type="item",
                        entity_id=item_id,
                        ref_id=item_id,
                        file="npcs.yaml",
                        path=f"npcs.{npc_id}.shop_inventory",
                    )
                )
        if not set(inventory).intersection(required_items):
            continue
        possible_locations = {str(npc.get("location_id", ""))}
        for entry in npc.get("schedule", []):
            if isinstance(entry, dict) and entry.get("location_id"):
                possible_locations.add(str(entry.get("location_id")))
        if possible_locations.isdisjoint(reachable_locations):
            analysis.merchant_item_unavailable.append(
                _ref(
                    code="merchant_unreachable_for_required_item",
                    severity=QualityIssueSeverity.ERROR,
                    entity_type="npc",
                    entity_id=npc_id,
                    file="npcs.yaml",
                    path=f"npcs.{npc_id}",
                )
            )


def _detect_npc_life_blockers(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    required_npcs: set[str],
) -> None:
    npc_by_id = content.npc_by_id
    for npc_id in sorted(required_npcs):
        npc = npc_by_id.get(npc_id)
        if npc is None:
            continue
        condition = str(npc.get("condition", "")).lower()
        alive = npc.get("alive", True)
        if alive is False or condition in {"dead", "incapacitated"}:
            if not _npc_has_quest_fallback(content, npc_id):
                analysis.npc_blocking_quest_without_fallback.append(
                    _ref(
                        code="npc_unavailable_without_fallback",
                        severity=QualityIssueSeverity.BLOCKER,
                        entity_type="npc",
                        entity_id=npc_id,
                        ref_id=npc_id,
                        file="npcs.yaml",
                        path=f"npcs.{npc_id}",
                    )
                )


def _detect_schedule_conflicts(
    analysis: DeadEndAnalysis,
    content: _WorldContent,
    reachable_locations: set[str],
    required_npcs: set[str],
) -> None:
    for npc in sorted(content.npcs, key=lambda item: str(item.get("id", ""))):
        npc_id = str(npc.get("id", ""))
        schedule = [entry for entry in npc.get("schedule", []) if isinstance(entry, dict)]
        by_time: dict[str, set[str]] = defaultdict(set)
        for entry in schedule:
            by_time[str(entry.get("time_of_day", ""))].add(str(entry.get("location_id", "")))
        for time_of_day, locations in sorted(by_time.items()):
            if len(locations) > 1:
                analysis.schedule_conflicts.append(
                    _ref(
                        code="npc_schedule_conflicting_locations",
                        severity=QualityIssueSeverity.WARNING,
                        entity_type="npc",
                        entity_id=npc_id,
                        file="npcs.yaml",
                        path=f"npcs.{npc_id}.schedule.{time_of_day}",
                    )
                )
        if npc_id in required_npcs:
            possible_locations = {str(npc.get("location_id", ""))} | {
                str(entry.get("location_id", ""))
                for entry in schedule
                if entry.get("location_id")
            }
            if possible_locations and possible_locations.isdisjoint(reachable_locations):
                analysis.schedule_conflicts.append(
                    _ref(
                        code="required_npc_schedule_never_reachable",
                        severity=QualityIssueSeverity.ERROR,
                        entity_type="npc",
                        entity_id=npc_id,
                        file="npcs.yaml",
                        path=f"npcs.{npc_id}.schedule",
                    )
                )


def _detect_playtest_coverage_gaps(
    analysis: DeadEndAnalysis,
    required_refs: dict[str, set[str]],
    coverage: DeadEndCoverage,
) -> None:
    observed = {
        "location": set(coverage.visited_locations),
        "item": set(coverage.acquired_items),
        "npc": set(coverage.talked_npcs),
        "fact": set(coverage.discovered_facts),
    }
    for ref_type, refs in sorted(required_refs.items()):
        for ref_id in sorted(refs - observed.get(ref_type, set())):
            analysis.playtest_coverage_gaps.append(
                _ref(
                    code=f"playtest_missing_required_{ref_type}",
                    severity=QualityIssueSeverity.INFO,
                    entity_type=ref_type,
                    entity_id=ref_id,
                    ref_id=ref_id,
                )
            )


def _quest_required_refs(quests: list[dict[str, Any]]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {
        "fact": set(),
        "item": set(),
        "npc": set(),
        "location": set(),
    }
    for quest in quests:
        for trigger in quest.get("triggers", []):
            if not isinstance(trigger, dict) or "id" not in trigger:
                continue
            trigger_type = str(trigger.get("type", ""))
            ref_id = str(trigger.get("id"))
            if trigger_type == QuestTriggerType.FACT_DISCOVERED:
                refs["fact"].add(ref_id)
            elif trigger_type == QuestTriggerType.ITEM_ACQUIRED:
                refs["item"].add(ref_id)
            elif trigger_type == QuestTriggerType.NPC_TALKED:
                refs["npc"].add(ref_id)
            elif trigger_type == QuestTriggerType.LOCATION_VISITED:
                refs["location"].add(ref_id)
    return refs


def _reachable_locations(start_location_id: str, locations: list[dict[str, Any]]) -> set[str]:
    adjacency = {str(location.get("id", "")): set(_exits(location).values()) for location in locations}
    seen: set[str] = set()
    queue: deque[str] = deque([start_location_id] if start_location_id else [])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(sorted(adjacency.get(current, set()) - seen))
    return seen


def _item_reachable(item: dict[str, Any], content: _WorldContent, reachable_locations: set[str]) -> bool:
    location_id = item.get("location_id")
    if isinstance(location_id, str) and location_id in reachable_locations:
        return True
    owner_id = item.get("owner_id")
    if owner_id == "player":
        return True
    if isinstance(owner_id, str):
        owner = content.npc_by_id.get(owner_id)
        if owner and str(owner.get("location_id", "")) in reachable_locations:
            return True
    container_id = item.get("container_id")
    if isinstance(container_id, str):
        container = content.item_by_id.get(container_id)
        if container and _item_reachable(container, content, reachable_locations):
            return True
    return False


def _has_access_item_for_location(content: _WorldContent, location_id: str, reachable_locations: set[str]) -> bool:
    generic_access_tags = {"key", "lockpick"}
    explicit_tags = {f"opens:{location_id}", f"unlocks:{location_id}", f"access:{location_id}"}
    for item in content.items:
        tags = set(_string_list(item.get("tags")))
        if not tags.intersection(generic_access_tags | explicit_tags):
            continue
        if _item_reachable(item, content, reachable_locations) and not (_is_hidden(item) and not _is_discoverable_item(item)):
            return True
    return False


def _npc_has_quest_fallback(content: _WorldContent, npc_id: str) -> bool:
    for quest in content.quests:
        npc_objectives = {
            str(trigger.get("objective_id"))
            for trigger in quest.get("triggers", [])
            if isinstance(trigger, dict)
            and trigger.get("type") == QuestTriggerType.NPC_TALKED
            and trigger.get("id") == npc_id
            and trigger.get("objective_id")
        }
        if not npc_objectives:
            continue
        fallback_objectives = {
            str(trigger.get("objective_id"))
            for trigger in quest.get("triggers", [])
            if isinstance(trigger, dict)
            and trigger.get("type") != QuestTriggerType.NPC_TALKED
            and trigger.get("objective_id")
        }
        if npc_objectives.intersection(fallback_objectives):
            return True
    return False


def _exits(location: dict[str, Any]) -> dict[str, str]:
    exits = location.get("exits", {})
    if not isinstance(exits, dict):
        return {}
    return {str(direction): str(target) for direction, target in exits.items() if target}


def _by_id(values: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in values if isinstance(item, dict) and item.get("id")}


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


def _is_hidden(value: dict[str, Any]) -> bool:
    return bool(value.get("hidden")) or str(value.get("visibility", "")) == "hidden"


def _is_discoverable_item(item: dict[str, Any]) -> bool:
    return bool(item.get("discoverable")) or bool(_string_list(item.get("discovered_by")))


def _fact_has_discovery_path(fact: dict[str, Any]) -> bool:
    tags = _string_list(fact.get("tags"))
    return any(
        tag == "searchable"
        or tag.startswith("location:")
        or tag.startswith("object:")
        or tag.startswith("npc:")
        for tag in tags
    )


def _ref(
    *,
    code: str,
    severity: QualityIssueSeverity,
    entity_type: str,
    entity_id: str,
    quest_id: str | None = None,
    objective_id: str | None = None,
    ref_id: str | None = None,
    file: str | None = None,
    path: str | None = None,
) -> DeadEndIssueRef:
    return DeadEndIssueRef(
        code=code,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        quest_id=quest_id,
        objective_id=objective_id,
        ref_id=ref_id,
        file=file,
        path=path,
    )


def _quality_issue_from_ref(ref: DeadEndIssueRef, category: str) -> QualityIssue:
    return QualityIssue(
        id=f"{category}:{ref.entity_type}:{ref.entity_id}:{ref.code}",
        severity=ref.severity,
        category=category,
        file=ref.file,
        path=ref.path,
        entity_id=ref.entity_id,
        message=_safe_issue_message(ref),
        safe_details={
            "code": ref.code,
            "entity_type": ref.entity_type,
            "entity_id": ref.entity_id,
            "quest_id": ref.quest_id,
            "objective_id": ref.objective_id,
            "ref_id": ref.ref_id,
        },
    )


def _safe_issue_message(ref: DeadEndIssueRef) -> str:
    messages = {
        "location_unreachable_from_start": "A location is not reachable from the configured start location.",
        "map_dead_end": "A reachable location has no exits and may be an intentional dead end.",
        "required_item_missing": "A quest requires an item id that is not defined.",
        "required_item_unreachable": "A quest-required item is not reachable by static placement rules.",
        "required_item_hidden_without_discovery": "A quest-required item is hidden without a clear discovery path.",
        "required_npc_missing": "A quest requires an NPC id that is not defined.",
        "required_npc_unreachable": "A quest-required NPC is never located in a reachable location.",
        "required_npc_hidden_without_discovery": "A quest-required NPC is hidden without a clear discovery path.",
        "required_fact_missing": "A quest requires a fact id that is not defined.",
        "required_fact_hidden_without_discovery": "A quest-required fact is hidden without a player discovery path.",
        "hidden_clue_never_discoverable": "A hidden clue appears to have no player discovery path.",
        "quest_objective_missing_trigger": "A quest objective has no trigger that can complete it.",
        "locked_location_without_access_path": "A quest-required locked or hidden location has no reachable key or lockpick path.",
        "merchant_item_missing": "A merchant inventory references an undefined item.",
        "shop_inventory_on_non_merchant": "An NPC has shop inventory but is not marked as a merchant.",
        "merchant_unreachable_for_required_item": "A required shop item belongs to a merchant the player cannot reach.",
        "npc_unavailable_without_fallback": "A quest-required NPC is dead or incapacitated without a fallback trigger.",
        "npc_schedule_conflicting_locations": "An NPC schedule has conflicting locations for the same time of day.",
        "required_npc_schedule_never_reachable": "A quest-required NPC schedule never places them in a reachable location.",
    }
    return messages.get(ref.code, "A possible dead-end or unreachable objective issue was detected.")


def _recommended_actions(blockers: int, errors: int, warnings: int) -> list[str]:
    actions: list[str] = []
    if blockers:
        actions.append("Fix blocker dead-end issues before accepting the world pack for regression playtests.")
    if errors:
        actions.append("Review unreachable required references, locked access paths, and missing content ids.")
    if warnings:
        actions.append("Review warnings for intentional hard paths, dead-end map nodes, and schedule conflicts.")
    return actions
