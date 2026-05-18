from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.quality.benchmarks import BenchmarkReport
from app.quality.reports import (
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class WorldHealthDimension(StrEnum):
    STRUCTURE = "structure"
    REACHABILITY = "reachability"
    SECRECY = "secrecy"
    CONTINUITY = "continuity"
    BALANCE = "balance"
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    MIGRATION_SAFETY = "migration_safety"


class WorldHealthCategoryScore(BaseModel):
    dimension: WorldHealthDimension
    score: int = Field(ge=0, le=100)
    status: QualityMetricStatus
    explanation: str
    blocker_count: int = 0
    error_count: int = 0
    warning_count: int = 0


class WorldHealthScore(BaseModel):
    health_id: str = Field(default_factory=lambda: str(uuid4()))
    world_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    overall_score: int = Field(ge=0, le=100)
    category_scores: list[WorldHealthCategoryScore]
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    source_report_ids: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


def build_world_health_score(
    world_id: str,
    reports: list[WorldQualityReport],
    *,
    benchmark_reports: list[BenchmarkReport] | None = None,
) -> WorldHealthScore:
    normal_reports = [report.normal_copy() for report in reports]
    benchmark_reports = benchmark_reports or []
    source_report_ids = [report.run_id for report in normal_reports]
    source_report_ids.extend(report.benchmark_id for report in benchmark_reports)

    category_scores = [
        _score_dimension(dimension, normal_reports, benchmark_reports)
        for dimension in WorldHealthDimension
    ]
    overall_score = _overall_score(category_scores)
    blockers = _issue_messages(normal_reports, {QualityIssueSeverity.BLOCKER})
    warnings = _issue_messages(normal_reports, {QualityIssueSeverity.WARNING})[:12]
    recommended_actions = _recommended_actions(normal_reports, category_scores, bool(benchmark_reports))

    return WorldHealthScore(
        world_id=world_id,
        overall_score=overall_score,
        category_scores=category_scores,
        blockers=blockers,
        warnings=warnings,
        recommended_actions=recommended_actions,
        source_report_ids=source_report_ids,
        summary={
            "source_reports": len(normal_reports),
            "benchmark_reports": len(benchmark_reports),
            "blockers": len(blockers),
            "warnings": len(_issue_messages(normal_reports, {QualityIssueSeverity.WARNING})),
            "interpretation": "Local heuristic score; not an absolute quality judgment.",
        },
    )


def empty_world_health_score(world_id: str) -> WorldHealthScore:
    category_scores = [
        WorldHealthCategoryScore(
            dimension=dimension,
            score=100,
            status=QualityMetricStatus.UNKNOWN,
            explanation="No local quality report has been run yet.",
        )
        for dimension in WorldHealthDimension
    ]
    return WorldHealthScore(
        world_id=world_id,
        overall_score=100,
        category_scores=category_scores,
        recommended_actions=["Run world health analysis to populate this dashboard."],
        summary={
            "source_reports": 0,
            "benchmark_reports": 0,
            "interpretation": "No reports available; score is a placeholder until analysis runs.",
        },
    )


def _score_dimension(
    dimension: WorldHealthDimension,
    reports: list[WorldQualityReport],
    benchmark_reports: list[BenchmarkReport],
) -> WorldHealthCategoryScore:
    issues = [
        issue
        for report in reports
        for issue in report.issues
        if _issue_dimension(issue.category) == dimension
    ]
    metrics = [
        metric
        for report in reports
        for metric in report.metrics
        if _metric_dimension(metric.category) == dimension
    ]
    blocker_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.BLOCKER)
    error_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.WARNING)
    score = max(0, 100 - blocker_count * 45 - error_count * 20 - warning_count * 7)

    if dimension == WorldHealthDimension.PERFORMANCE:
        regression_count = sum(len(report.regressions) for report in benchmark_reports)
        score = max(0, score - regression_count * 20)
        if not benchmark_reports and not metrics:
            return WorldHealthCategoryScore(
                dimension=dimension,
                score=100,
                status=QualityMetricStatus.UNKNOWN,
                explanation="No performance benchmark report has been attached yet.",
            )

    status = _status_for_score(score, blocker_count, error_count, warning_count)
    return WorldHealthCategoryScore(
        dimension=dimension,
        score=score,
        status=status,
        explanation=_dimension_explanation(dimension, score, blocker_count, error_count, warning_count),
        blocker_count=blocker_count,
        error_count=error_count,
        warning_count=warning_count,
    )


def _overall_score(category_scores: list[WorldHealthCategoryScore]) -> int:
    if not category_scores:
        return 100
    weighted_total = 0
    total_weight = 0
    for category in category_scores:
        weight = 2 if category.blocker_count else 1
        weighted_total += category.score * weight
        total_weight += weight
    return round(weighted_total / total_weight)


def _issue_dimension(category: str) -> WorldHealthDimension:
    normalized = category.lower()
    if any(token in normalized for token in ["validation", "structure", "schema"]):
        return WorldHealthDimension.STRUCTURE
    if any(token in normalized for token in ["dead_end", "quest_completion", "schedule"]):
        return WorldHealthDimension.REACHABILITY
    if any(token in normalized for token in ["visibility", "hidden", "leak", "secrecy"]):
        return WorldHealthDimension.SECRECY
    if any(token in normalized for token in ["narrative", "timeline", "social_consequence"]):
        return WorldHealthDimension.CONTINUITY
    if any(token in normalized for token in ["economy", "combat", "balance"]):
        return WorldHealthDimension.BALANCE
    if any(token in normalized for token in ["coverage", "playtest", "scenario"]):
        return WorldHealthDimension.COVERAGE
    if any(token in normalized for token in ["migration", "save_load"]):
        return WorldHealthDimension.MIGRATION_SAFETY
    if "performance" in normalized or "benchmark" in normalized:
        return WorldHealthDimension.PERFORMANCE
    return WorldHealthDimension.STRUCTURE


def _metric_dimension(category: str) -> WorldHealthDimension:
    return _issue_dimension(category)


def _status_for_score(
    score: int,
    blocker_count: int,
    error_count: int,
    warning_count: int,
) -> QualityMetricStatus:
    if blocker_count or score < 40:
        return QualityMetricStatus.BLOCKER
    if error_count or score < 70:
        return QualityMetricStatus.ERROR
    if warning_count or score < 90:
        return QualityMetricStatus.WARNING
    return QualityMetricStatus.OK


def _dimension_explanation(
    dimension: WorldHealthDimension,
    score: int,
    blocker_count: int,
    error_count: int,
    warning_count: int,
) -> str:
    if blocker_count:
        return f"{dimension.value} has {blocker_count} blocker issue(s); review before release."
    if error_count:
        return f"{dimension.value} has {error_count} error issue(s)."
    if warning_count:
        return f"{dimension.value} has {warning_count} warning issue(s)."
    return f"{dimension.value} looks healthy in the available local reports (score {score})."


def _issue_messages(
    reports: list[WorldQualityReport],
    severities: set[QualityIssueSeverity],
) -> list[str]:
    return [
        f"{issue.category}: {issue.message}"
        for report in reports
        for issue in report.issues
        if issue.severity in severities
    ]


def _recommended_actions(
    reports: list[WorldQualityReport],
    category_scores: list[WorldHealthCategoryScore],
    has_benchmarks: bool,
) -> list[str]:
    actions: list[str] = []
    for report in reports:
        for action in report.recommended_actions:
            if action not in actions:
                actions.append(action)
    for category in category_scores:
        if category.status in {QualityMetricStatus.BLOCKER, QualityMetricStatus.ERROR}:
            action = f"Review {category.dimension.value} issues before accepting this world."
            if action not in actions:
                actions.append(action)
    if not has_benchmarks:
        actions.append("Run the local benchmark suite to populate performance scoring.")
    return actions[:12]
