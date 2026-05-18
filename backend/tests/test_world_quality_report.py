import json

import pytest
from pydantic import ValidationError

from app.core.world_state import FactState, FactVisibility, GameState
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.quality import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
    world_quality_report_from_validation_report,
)


def test_world_quality_report_json_serializable() -> None:
    report = WorldQualityReport(
        world_id="mist_valley",
        categories=["validation"],
        metrics=[
            QualityMetric(
                name="validation_errors",
                value=0,
                unit="count",
                category="validation",
                threshold=0,
                status=QualityMetricStatus.OK,
            )
        ],
        issues=[
            QualityIssue(
                id="issue-1",
                severity=QualityIssueSeverity.INFO,
                category="validation",
                message="No blocking quality issue.",
            )
        ],
        summary={"ok": True},
    )

    payload = report.model_dump(mode="json")

    assert payload["world_id"] == "mist_valley"
    assert json.loads(json.dumps(payload))["metrics"][0]["name"] == "validation_errors"


def test_quality_issue_severity_validation() -> None:
    issue = QualityIssue(
        id="issue-1",
        severity="warning",
        category="validation",
        message="Check this world pack reference.",
    )

    assert issue.severity == QualityIssueSeverity.WARNING
    with pytest.raises(ValidationError):
        QualityIssue(
            id="issue-2",
            severity="critical",
            category="validation",
            message="Invalid severity should fail.",
        )


def test_hidden_details_debug_only_not_in_normal_summary() -> None:
    hidden_text = "the buried monarch is still alive"
    report = WorldQualityReport(
        world_id="mist_valley",
        categories=["leak_regression"],
        issues=[
            QualityIssue(
                id="hidden-leak-1",
                severity=QualityIssueSeverity.WARNING,
                category="visibility",
                message="A hidden fact was referenced by an authoring-only fixture.",
                safe_details={"safe_hint": "hidden fact reference was detected"},
                hidden_details_debug_only={"hidden_fact_text": hidden_text},
            )
        ],
        summary={
            "safe": "debug detail stripped in normal output",
            "hidden_details_debug_only": {"hidden_fact_text": hidden_text},
        },
    )

    normal_payload = report.model_dump_normal()
    serialized = json.dumps(normal_payload)

    assert hidden_text not in serialized
    assert "hidden_details_debug_only" not in serialized
    assert normal_payload["issues"][0]["safe_details"]["safe_hint"] == "hidden fact reference was detected"


def test_quality_report_can_include_validation_issues() -> None:
    validation = ValidationReport(world_id="mist_valley")
    validation.add(
        ValidationSeverity.ERROR,
        "quests.yaml[0].stages[1].next_stages",
        "Unknown next_stage: missing_stage",
        code="unknown_next_stage",
        ref_id="missing_stage",
        suggestion="Point next_stages at an existing stage id.",
    )
    validation.add(
        ValidationSeverity.WARNING,
        "facts.yaml[0].description",
        "Hidden fact text may be player-facing.",
        code="hidden_fact_visibility_risk",
        ref_id="fact_secret",
    )

    report = world_quality_report_from_validation_report(validation)

    assert report.world_id == "mist_valley"
    assert [issue.severity for issue in report.issues] == [
        QualityIssueSeverity.ERROR,
        QualityIssueSeverity.WARNING,
    ]
    assert report.issues[0].file == "quests.yaml"
    assert report.issues[0].entity_id == "missing_stage"
    assert report.summary["validation"]["errors"] == 1
    assert any(metric.name == "validation_warnings" and metric.value == 1 for metric in report.metrics)


def test_quality_report_does_not_modify_game_state() -> None:
    state = GameState(
        world_id="mist_valley",
        facts={
            "fact_hidden": FactState(
                id="fact_hidden",
                text="a hidden truth",
                visibility=FactVisibility.HIDDEN,
            )
        },
    )
    before = state.model_dump(mode="json")

    report = WorldQualityReport(
        world_id=state.world_id,
        issues=[
            QualityIssue(
                id="visibility-1",
                severity=QualityIssueSeverity.INFO,
                category="visibility",
                message="Hidden fact remained hidden.",
                hidden_details_debug_only={"fact_id": "fact_hidden"},
            )
        ],
    )
    _ = report.model_dump_normal()

    assert state.model_dump(mode="json") == before
