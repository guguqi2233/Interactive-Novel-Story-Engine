from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.engine.content.validator import ValidationIssue, ValidationReport, ValidationSeverity


class QualityIssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class QualityMetricStatus(StrEnum):
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"
    UNKNOWN = "unknown"


class QualityRunMetadata(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    world_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: str = CURRENT_ENGINE_VERSION
    schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    content_pack_version: str | None = None
    tool_name: str = "world_quality"


class QualityIssue(BaseModel):
    id: str
    severity: QualityIssueSeverity
    category: str
    file: str | None = None
    path: str | None = None
    entity_id: str | None = None
    message: str
    safe_details: dict[str, Any] = Field(default_factory=dict)
    hidden_details_debug_only: dict[str, Any] | None = None

    def normal_copy(self) -> "QualityIssue":
        """Return a player-safe/local-normal view without debug-only hidden details."""
        return self.model_copy(
            update={
                "safe_details": _strip_debug_only(self.safe_details),
                "hidden_details_debug_only": None,
            },
            deep=True,
        )


class QualityMetric(BaseModel):
    name: str
    value: int | float | str | bool
    unit: str | None = None
    category: str
    threshold: int | float | str | None = None
    status: QualityMetricStatus = QualityMetricStatus.UNKNOWN


class WorldQualityReport(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    world_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: str = CURRENT_ENGINE_VERSION
    schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    content_pack_version: str | None = None
    categories: list[str] = Field(default_factory=list)
    metrics: list[QualityMetric] = Field(default_factory=list)
    issues: list[QualityIssue] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    recommended_actions: list[str] = Field(default_factory=list)

    @classmethod
    def from_metadata(
        cls,
        metadata: QualityRunMetadata,
        *,
        categories: list[str] | None = None,
        metrics: list[QualityMetric] | None = None,
        issues: list[QualityIssue] | None = None,
        summary: dict[str, Any] | None = None,
        recommended_actions: list[str] | None = None,
    ) -> "WorldQualityReport":
        return cls(
            run_id=metadata.run_id,
            world_id=metadata.world_id,
            created_at=metadata.created_at,
            engine_version=metadata.engine_version,
            schema_version=metadata.schema_version,
            content_pack_version=metadata.content_pack_version,
            categories=categories or [],
            metrics=metrics or [],
            issues=issues or [],
            summary=summary or {},
            recommended_actions=recommended_actions or [],
        )

    def normal_copy(self) -> "WorldQualityReport":
        """Return the safe report form for non-debug APIs and player-adjacent UI."""
        return self.model_copy(
            update={
                "issues": [issue.normal_copy() for issue in self.issues],
                "summary": _strip_debug_only(self.summary),
            },
            deep=True,
        )

    def model_dump_normal(self) -> dict[str, Any]:
        return self.normal_copy().model_dump(mode="json", exclude_none=True)


def quality_issue_from_validation_issue(
    issue: ValidationIssue,
    *,
    category: str = "validation",
) -> QualityIssue:
    return QualityIssue(
        id=f"validation:{issue.file}:{issue.path}:{issue.code}",
        severity=_quality_severity_from_validation(issue.severity),
        category=category,
        file=issue.file,
        path=issue.path,
        entity_id=issue.ref_id,
        message=issue.message,
        safe_details={
            "code": issue.code,
            "ref_id": issue.ref_id,
            "suggestion": issue.suggestion,
        },
    )


def quality_issues_from_validation_report(report: ValidationReport) -> list[QualityIssue]:
    return [
        quality_issue_from_validation_issue(issue)
        for issue in [*report.errors, *report.warnings, *report.suggestions]
    ]


def world_quality_report_from_validation_report(
    report: ValidationReport,
    *,
    metadata: QualityRunMetadata | None = None,
    content_pack_version: str | None = None,
) -> WorldQualityReport:
    run_metadata = metadata or QualityRunMetadata(
        world_id=report.world_id,
        content_pack_version=content_pack_version,
    )
    issues = quality_issues_from_validation_report(report)
    metrics = [
        QualityMetric(
            name="validation_errors",
            value=len(report.errors),
            category="validation",
            threshold=0,
            status=QualityMetricStatus.OK if not report.errors else QualityMetricStatus.ERROR,
        ),
        QualityMetric(
            name="validation_warnings",
            value=len(report.warnings),
            category="validation",
            status=QualityMetricStatus.OK if not report.warnings else QualityMetricStatus.WARNING,
        ),
        QualityMetric(
            name="validation_suggestions",
            value=len(report.suggestions),
            category="validation",
            status=QualityMetricStatus.INFO if report.suggestions else QualityMetricStatus.OK,
        ),
    ]
    summary = {
        "ok": report.ok,
        "validation": {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "suggestions": len(report.suggestions),
        },
    }
    recommended_actions = _recommended_actions_for_validation_report(report)
    return WorldQualityReport.from_metadata(
        run_metadata,
        categories=["validation"],
        metrics=metrics,
        issues=issues,
        summary=summary,
        recommended_actions=recommended_actions,
    )


def _quality_severity_from_validation(severity: ValidationSeverity) -> QualityIssueSeverity:
    if severity == ValidationSeverity.ERROR:
        return QualityIssueSeverity.ERROR
    if severity == ValidationSeverity.WARNING:
        return QualityIssueSeverity.WARNING
    return QualityIssueSeverity.INFO


def _recommended_actions_for_validation_report(report: ValidationReport) -> list[str]:
    actions: list[str] = []
    if report.errors:
        actions.append("Fix validation errors before publishing or running scenario regression.")
    if report.warnings:
        actions.append("Review validation warnings for possible broken references or visibility risks.")
    if report.suggestions:
        actions.append("Consider authoring suggestions when polishing the world pack.")
    return actions


def _strip_debug_only(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_debug_only(item)
            for key, item in value.items()
            if key != "hidden_details_debug_only" and not str(key).endswith("_debug_only")
        }
    if isinstance(value, list):
        return [_strip_debug_only(item) for item in value]
    return value
