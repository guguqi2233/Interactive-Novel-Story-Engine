from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.content.world_branching import WorldDiff
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.scenarios.regression import (
    ScenarioRegressionCase,
    ScenarioRegressionRun,
    run_scenario_regression_suite,
)


class BranchRegressionSelection(BaseModel):
    scenario_id: str
    reason: str
    matched_tags: list[str] = Field(default_factory=list)


class BranchRegressionRequest(BaseModel):
    base_branch: str = "base"
    target_branch: str = "target"
    diff: WorldDiff | None = None
    scenario_cases: list[ScenarioRegressionCase] = Field(default_factory=list)


class BranchRegressionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    world_id: str
    base_branch: str
    target_branch: str
    selected: list[BranchRegressionSelection] = Field(default_factory=list)
    skipped_case_ids: list[str] = Field(default_factory=list)
    regression_run: ScenarioRegressionRun | None = None
    passed: bool = True
    failure_count: int = 0
    safe_summary: dict[str, int | str | bool] = Field(default_factory=dict)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


def run_branch_diff_regression(
    *,
    world_id: str,
    diff: WorldDiff,
    scenario_cases: list[ScenarioRegressionCase],
    base_branch: str = "base",
    target_branch: str = "target",
    worlds_root: str = "worlds",
) -> BranchRegressionReport:
    selections = select_regression_cases(diff, scenario_cases)
    selected_ids = {selection.scenario_id for selection in selections}
    selected_cases = [case for case in scenario_cases if case.id in selected_ids]
    regression_run = run_scenario_regression_suite(selected_cases, worlds_root=worlds_root) if selected_cases else None
    failure_count = regression_run.failed if regression_run else 0
    report = BranchRegressionReport(
        world_id=world_id,
        base_branch=base_branch,
        target_branch=target_branch,
        selected=selections,
        skipped_case_ids=[case.id for case in scenario_cases if case.id not in selected_ids],
        regression_run=regression_run,
        passed=failure_count == 0,
        failure_count=failure_count,
        safe_summary={
            "selected_cases": len(selected_cases),
            "skipped_cases": len(scenario_cases) - len(selected_cases),
            "diff_added": len(diff.added_entities),
            "diff_removed": len(diff.removed_entities),
            "diff_changed": len(diff.changed_entities),
            "visibility_risks": len(diff.visibility_risks),
            "passed": failure_count == 0,
        },
        quality_report=WorldQualityReport(world_id=world_id),
    )
    report.quality_report = _to_quality_report(report)
    return report


def select_regression_cases(
    diff: WorldDiff,
    scenario_cases: list[ScenarioRegressionCase],
) -> list[BranchRegressionSelection]:
    required_tags = _required_tags_for_diff(diff)
    selections: list[BranchRegressionSelection] = []
    for case in scenario_cases:
        case_tags = {tag.lower() for tag in case.tags}
        matched = sorted(required_tags & case_tags)
        if matched:
            selections.append(
                BranchRegressionSelection(
                    scenario_id=case.id,
                    reason=_selection_reason(matched),
                    matched_tags=matched,
                )
            )
    return selections


def _required_tags_for_diff(diff: WorldDiff) -> set[str]:
    tags: set[str] = set()
    for entity in [*diff.added_entities, *diff.removed_entities, *diff.changed_entities]:
        file_name = entity.file.lower()
        entity_type = entity.entity_type.lower()
        if file_name == "quests.yaml" or entity_type == "quest":
            tags.update({"quest", "quest_path"})
        if file_name == "locations.yaml" or entity_type == "location":
            tags.update({"navigation", "exploration", "map"})
        if file_name == "items.yaml" or entity_type == "item":
            tags.update({"trade", "economy", "item"})
        if file_name == "npcs.yaml" or entity_type == "npc":
            tags.update({"dialogue", "schedule", "planning", "npc"})
        if file_name == "facts.yaml" or entity_type == "fact":
            tags.update({"visibility", "hidden-boundary", "leak"})
        if file_name == "rumors.yaml" or entity_type == "rumor":
            tags.update({"rumor", "social", "visibility"})
        if file_name == "factions.yaml" or entity_type == "faction":
            tags.update({"faction", "social"})
    if diff.visibility_risks:
        tags.update({"visibility", "hidden-boundary", "leak"})
    if diff.migration_impacts or diff.removed_entities:
        tags.update({"migration", "save-load"})
    return tags


def _selection_reason(tags: list[str]) -> str:
    if any(tag in tags for tag in ["quest", "quest_path"]):
        return "changed quest content"
    if any(tag in tags for tag in ["navigation", "exploration", "map"]):
        return "changed map or location content"
    if any(tag in tags for tag in ["trade", "economy", "item"]):
        return "changed item or economy content"
    if any(tag in tags for tag in ["dialogue", "schedule", "planning", "npc"]):
        return "changed NPC content"
    if any(tag in tags for tag in ["visibility", "hidden-boundary", "leak"]):
        return "changed hidden or visibility-sensitive content"
    return "matched changed content tags"


def _to_quality_report(report: BranchRegressionReport) -> WorldQualityReport:
    issues = [
        QualityIssue(
            id=f"branch_regression:failure:{result.case_id}",
            severity=QualityIssueSeverity.ERROR,
            category="branch_diff_regression",
            entity_id=result.case_id,
            message="Selected branch regression scenario failed.",
            safe_details={"failure_count": len(result.failure_reasons)},
        )
        for result in (report.regression_run.case_results if report.regression_run else [])
        if not result.passed
    ]
    if not report.selected:
        issues.append(
            QualityIssue(
                id="branch_regression:no_selected_cases",
                severity=QualityIssueSeverity.WARNING,
                category="branch_diff_regression",
                message="No scenario regression cases matched this branch diff.",
            )
        )
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["branch_diff_regression"],
        metrics=[
            QualityMetric(
                name="branch_regression_selected_cases",
                value=len(report.selected),
                category="branch_diff_regression",
                status=QualityMetricStatus.OK if report.selected else QualityMetricStatus.WARNING,
            ),
            QualityMetric(
                name="branch_regression_failures",
                value=report.failure_count,
                category="branch_diff_regression",
                threshold=0,
                status=QualityMetricStatus.ERROR if report.failure_count else QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary=report.safe_summary,
        recommended_actions=["Review failed branch regression scenarios before merging branch content."] if issues else [],
    ).normal_copy()
