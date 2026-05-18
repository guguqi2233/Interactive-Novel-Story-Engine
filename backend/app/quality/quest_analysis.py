from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.world_state import QuestTriggerType, QuestVisibility
from app.engine.content.world_loader import QuestDef
from app.quality import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class QuestCompletionCoverage(BaseModel):
    completed_quest_ids: list[str] = Field(default_factory=list)
    visited_stage_ids: dict[str, list[str]] = Field(default_factory=dict)
    completed_objective_ids: dict[str, list[str]] = Field(default_factory=dict)


class QuestCompletionAnalysisRequest(BaseModel):
    coverage: QuestCompletionCoverage | None = None


class QuestIssueRef(BaseModel):
    quest_id: str
    stage_id: str | None = None
    objective_id: str | None = None
    ref_id: str | None = None
    severity: QualityIssueSeverity = QualityIssueSeverity.WARNING
    code: str


class QuestCompletionAnalysis(BaseModel):
    world_id: str
    total_quests: int = 0
    active_quests: int = 0
    hidden_quests: int = 0
    stages: dict[str, int] = Field(default_factory=dict)
    terminal_stages: dict[str, list[str]] = Field(default_factory=dict)
    unreachable_stages: list[QuestIssueRef] = Field(default_factory=list)
    missing_next_stage_refs: list[QuestIssueRef] = Field(default_factory=list)
    missing_trigger_refs: list[QuestIssueRef] = Field(default_factory=list)
    objectives_without_completion_path: list[QuestIssueRef] = Field(default_factory=list)
    circular_paths: list[QuestIssueRef] = Field(default_factory=list)
    hidden_quest_visibility_risks: list[QuestIssueRef] = Field(default_factory=list)
    required_availability_issues: list[QuestIssueRef] = Field(default_factory=list)
    scenario_covered_completed_quests: list[str] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


def analyze_quest_completion(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    coverage: QuestCompletionCoverage | None = None,
) -> QuestCompletionAnalysis:
    world_path = Path(worlds_root) / world_id
    raw_quests = _read_yaml_list(world_path / "quests.yaml", "quests")
    quests: list[QuestDef] = []
    parse_issues: list[QuestIssueRef] = []
    for index, raw_quest in enumerate(raw_quests):
        try:
            quests.append(QuestDef.model_validate(raw_quest))
        except ValidationError:
            parse_issues.append(
                QuestIssueRef(
                    quest_id=str(raw_quest.get("id", f"quest_index_{index}")) if isinstance(raw_quest, dict) else f"quest_index_{index}",
                    severity=QualityIssueSeverity.ERROR,
                    code="quest_schema_invalid",
                )
            )
    refs = _available_refs(world_path)
    analysis = _analyze_quests(world_id, quests, refs, coverage or QuestCompletionCoverage())
    analysis.missing_trigger_refs.extend(parse_issues)
    analysis.quality_report = quest_analysis_to_quality_report(analysis)
    return analysis


def quest_analysis_to_quality_report(analysis: QuestCompletionAnalysis) -> WorldQualityReport:
    issues: list[QualityIssue] = []
    for bucket, category in (
        (analysis.missing_next_stage_refs, "quest_missing_next_stage"),
        (analysis.missing_trigger_refs, "quest_missing_trigger_ref"),
        (analysis.objectives_without_completion_path, "quest_objective_completion_path"),
        (analysis.unreachable_stages, "quest_unreachable_stage"),
        (analysis.circular_paths, "quest_circular_path"),
        (analysis.hidden_quest_visibility_risks, "quest_visibility"),
        (analysis.required_availability_issues, "quest_required_availability"),
    ):
        for item in bucket:
            issues.append(_quality_issue_from_ref(item, category))

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
        categories=["quest_completion"],
        metrics=[
            QualityMetric(name="total_quests", value=analysis.total_quests, category="quest_completion", status=QualityMetricStatus.OK),
            QualityMetric(name="hidden_quests", value=analysis.hidden_quests, category="quest_completion", status=QualityMetricStatus.OK),
            QualityMetric(name="quest_completion_issues", value=len(issues), category="quest_completion", threshold=0, status=status),
            QualityMetric(
                name="scenario_covered_completed_quests",
                value=len(analysis.scenario_covered_completed_quests),
                category="quest_completion",
                status=QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary={
            "total_quests": analysis.total_quests,
            "hidden_quests": analysis.hidden_quests,
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
            "scenario_covered_completed_quests": sorted(analysis.scenario_covered_completed_quests),
        },
        recommended_actions=_recommended_actions(blocker_count, error_count, warning_count),
    )


def _analyze_quests(
    world_id: str,
    quests: list[QuestDef],
    refs: dict[str, set[str]],
    coverage: QuestCompletionCoverage,
) -> QuestCompletionAnalysis:
    analysis = QuestCompletionAnalysis(
        world_id=world_id,
        total_quests=len(quests),
        active_quests=sum(1 for quest in quests if quest.visibility == QuestVisibility.PUBLIC),
        hidden_quests=sum(1 for quest in quests if quest.visibility == QuestVisibility.HIDDEN),
        quality_report=WorldQualityReport(world_id=world_id),
    )
    completed_coverage = set(coverage.completed_quest_ids)

    for quest in quests:
        stage_ids = {stage.id for stage in quest.stages}
        analysis.stages[quest.id] = len(stage_ids)
        adjacency: dict[str, set[str]] = defaultdict(set)
        terminal: list[str] = []
        objective_ids = {objective for stage in quest.stages for objective in stage.objectives}
        completed_by_trigger = {trigger.objective_id for trigger in quest.triggers if trigger.objective_id}

        for stage in quest.stages:
            targets = [*stage.next_stages, *stage.failure_stages, *stage.alternate_stages]
            if not targets:
                terminal.append(stage.id)
            for target in targets:
                if target not in stage_ids:
                    analysis.missing_next_stage_refs.append(
                        QuestIssueRef(
                            quest_id=quest.id,
                            stage_id=stage.id,
                            ref_id=target,
                            severity=QualityIssueSeverity.ERROR,
                            code="missing_next_stage_ref",
                        )
                    )
                else:
                    adjacency[stage.id].add(target)
        analysis.terminal_stages[quest.id] = sorted(terminal)

        reachable = _reachable(quest.initial_stage, adjacency) if quest.initial_stage in stage_ids else set()
        for stage_id in sorted(stage_ids - reachable):
            analysis.unreachable_stages.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    stage_id=stage_id,
                    severity=QualityIssueSeverity.WARNING,
                    code="unreachable_stage",
                )
            )
        if _has_cycle(stage_ids, adjacency):
            analysis.circular_paths.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    severity=QualityIssueSeverity.WARNING,
                    code="circular_path",
                )
            )
        for objective_id in sorted(objective_ids - completed_by_trigger):
            analysis.objectives_without_completion_path.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    objective_id=objective_id,
                    severity=QualityIssueSeverity.WARNING,
                    code="objective_without_completion_path",
                )
            )
        analysis.missing_trigger_refs.extend(_missing_trigger_refs(quest, refs, objective_ids, stage_ids))
        if quest.visibility == QuestVisibility.HIDDEN:
            analysis.hidden_quest_visibility_risks.extend(_hidden_quest_visibility_risks(quest, refs))
        if quest.id in completed_coverage:
            analysis.scenario_covered_completed_quests.append(quest.id)

    analysis.scenario_covered_completed_quests = sorted(set(analysis.scenario_covered_completed_quests))
    return analysis


def _missing_trigger_refs(
    quest: QuestDef,
    refs: dict[str, set[str]],
    objective_ids: set[str],
    stage_ids: set[str],
) -> list[QuestIssueRef]:
    issues: list[QuestIssueRef] = []
    for trigger in quest.triggers:
        ref_kind = _trigger_ref_kind(trigger.type)
        if trigger.id not in refs.get(ref_kind, set()):
            issues.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    ref_id=trigger.id,
                    severity=QualityIssueSeverity.ERROR,
                    code=f"missing_trigger_{ref_kind}",
                )
            )
        if trigger.objective_id and trigger.objective_id not in objective_ids:
            issues.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    objective_id=trigger.objective_id,
                    severity=QualityIssueSeverity.ERROR,
                    code="missing_trigger_objective",
                )
            )
        if trigger.next_stage and trigger.next_stage not in stage_ids:
            issues.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    stage_id=trigger.next_stage,
                    severity=QualityIssueSeverity.ERROR,
                    code="missing_trigger_next_stage",
                )
            )
    return issues


def _hidden_quest_visibility_risks(quest: QuestDef, refs: dict[str, set[str]]) -> list[QuestIssueRef]:
    risks: list[QuestIssueRef] = []
    for trigger in quest.triggers:
        if trigger.type == QuestTriggerType.FACT_DISCOVERED and trigger.id in refs.get("public_facts", set()):
            risks.append(
                QuestIssueRef(
                    quest_id=quest.id,
                    ref_id=trigger.id,
                    severity=QualityIssueSeverity.WARNING,
                    code="hidden_quest_public_fact_trigger",
                )
            )
    return risks


def _available_refs(world_path: Path) -> dict[str, set[str]]:
    facts = _read_yaml_list(world_path / "facts.yaml", "facts")
    return {
        "fact": _ids(facts),
        "public_facts": {str(item.get("id")) for item in facts if isinstance(item, dict) and item.get("visibility") == "public"},
        "item": _ids(_read_yaml_list(world_path / "items.yaml", "items")),
        "npc": _ids(_read_yaml_list(world_path / "npcs.yaml", "npcs")),
        "location": _ids(_read_yaml_list(world_path / "locations.yaml", "locations")),
        "faction": _ids(_read_yaml_list(world_path / "factions.yaml", "factions")),
    }


def _trigger_ref_kind(trigger_type: QuestTriggerType) -> str:
    if trigger_type == QuestTriggerType.FACT_DISCOVERED:
        return "fact"
    if trigger_type == QuestTriggerType.ITEM_ACQUIRED:
        return "item"
    if trigger_type == QuestTriggerType.NPC_TALKED:
        return "npc"
    if trigger_type == QuestTriggerType.LOCATION_VISITED:
        return "location"
    if trigger_type == QuestTriggerType.FACTION_REPUTATION:
        return "faction"
    return "unknown"


def _read_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    values = data.get(key, []) if isinstance(data, dict) else []
    return values if isinstance(values, list) else []


def _ids(values: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("id")) for item in values if isinstance(item, dict) and item.get("id")}


def _reachable(initial_stage: str, adjacency: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque([initial_stage])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(sorted(adjacency.get(current, set()) - seen))
    return seen


def _has_cycle(stage_ids: set[str], adjacency: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str) -> bool:
        if stage_id in visiting:
            return True
        if stage_id in visited:
            return False
        visiting.add(stage_id)
        for target in adjacency.get(stage_id, set()):
            if visit(target):
                return True
        visiting.remove(stage_id)
        visited.add(stage_id)
        return False

    return any(visit(stage_id) for stage_id in sorted(stage_ids))


def _quality_issue_from_ref(ref: QuestIssueRef, category: str) -> QualityIssue:
    return QualityIssue(
        id=f"{category}:{ref.quest_id}:{ref.stage_id or ref.objective_id or ref.ref_id or 'quest'}:{ref.code}",
        severity=ref.severity,
        category=category,
        file="quests.yaml",
        path=f"quests.{ref.quest_id}",
        entity_id=ref.quest_id,
        message=_safe_issue_message(ref),
        safe_details={
            "quest_id": ref.quest_id,
            "stage_id": ref.stage_id,
            "objective_id": ref.objective_id,
            "ref_id": ref.ref_id,
            "code": ref.code,
        },
    )


def _safe_issue_message(ref: QuestIssueRef) -> str:
    if ref.code == "missing_next_stage_ref":
        return f"Quest {ref.quest_id} references a missing stage id."
    if ref.code.startswith("missing_trigger"):
        return f"Quest {ref.quest_id} has a trigger with a missing reference."
    if ref.code == "objective_without_completion_path":
        return f"Quest {ref.quest_id} has an objective without a completion trigger."
    if ref.code == "unreachable_stage":
        return f"Quest {ref.quest_id} has an unreachable stage."
    if ref.code == "circular_path":
        return f"Quest {ref.quest_id} has a circular stage path."
    if ref.code == "hidden_quest_public_fact_trigger":
        return f"Hidden quest {ref.quest_id} is triggered by a public fact."
    return f"Quest {ref.quest_id} has a quest analysis issue."


def _recommended_actions(blockers: int, errors: int, warnings: int) -> list[str]:
    actions: list[str] = []
    if blockers or errors:
        actions.append("Fix quest reference errors before relying on completion analysis.")
    if warnings:
        actions.append("Review warnings for unreachable stages, circular paths, and objective completion gaps.")
    return actions
