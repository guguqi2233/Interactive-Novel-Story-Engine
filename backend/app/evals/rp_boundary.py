from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.world_state import GameState
from app.engine.actions.schemas import ActionResult
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.roleplay.boundary import RoleplayOutputCandidate
from app.roleplay.output_consistency import RPOutputConsistencyChecker


class RPBoundaryRule(StrEnum):
    NO_HIDDEN_FACT_LEAKAGE = "no_hidden_fact_leakage"
    NO_NPC_UNKNOWN_FACT = "no_npc_unknown_fact"
    NO_PROFILE_STATE_PERMISSION = "no_profile_state_permission"
    NO_VOICE_ACTION_RESULT_OVERRIDE = "no_voice_action_result_override"
    NO_EXAMPLE_DIALOGUE_AS_FACT = "no_example_dialogue_as_fact"
    NO_LOREBOOK_HIDDEN_PROMPT_ENTRY = "no_lorebook_hidden_prompt_entry"
    NO_LLM_EMOTIONAL_STATE_WRITE = "no_llm_emotional_state_write"
    NO_TONE_AS_RELATIONSHIP_VALUE = "no_tone_as_relationship_value"
    NO_GROUP_CONTEXT_CROSSOVER = "no_group_context_crossover"
    NO_SCENE_MOOD_FACT_OVERRIDE = "no_scene_mood_fact_override"
    SAFE_RP_OUTPUT = "safe_rp_output"


class RPBoundaryEvalCase(BaseModel):
    id: str
    rule: RPBoundaryRule
    generated_text: str
    state: GameState | None = None
    visible_facts: list[str] = Field(default_factory=list)
    npc_known_facts: list[str] = Field(default_factory=list)
    forbidden_hidden_terms: list[str] = Field(default_factory=list)
    forbidden_hidden_ids: list[str] = Field(default_factory=list)
    allowed_flavor_terms: list[str] = Field(default_factory=list)
    speaker_npc_id: str | None = None
    action_result: ActionResult | None = None
    candidate: RoleplayOutputCandidate | None = None
    expected_issue_codes: list[str] = Field(default_factory=list)
    should_pass: bool = False
    safe_description: str = ""


class RPBoundaryEvalResult(BaseModel):
    case_id: str
    rule: RPBoundaryRule
    passed: bool
    safe_reason: str
    issue_codes: list[str] = Field(default_factory=list)


class RPBoundaryEvalReport(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_cases: int
    passed: int
    failed: int
    case_results: list[RPBoundaryEvalResult] = Field(default_factory=list)
    quality_report: WorldQualityReport | None = None


def evaluate_rp_boundary_case(case: RPBoundaryEvalCase) -> RPBoundaryEvalResult:
    report = RPOutputConsistencyChecker().check(
        generated_text=case.generated_text,
        state=case.state,
        action_result=case.action_result,
        visible_facts=case.visible_facts,
        npc_known_facts=case.npc_known_facts,
        forbidden_hidden_terms=case.forbidden_hidden_terms,
        forbidden_hidden_ids=case.forbidden_hidden_ids,
        allowed_flavor_terms=case.allowed_flavor_terms,
        speaker_npc_id=case.speaker_npc_id,
        candidate=case.candidate,
    )
    issue_codes = sorted({issue.code for issue in report.issues})
    if case.should_pass:
        passed = report.ok and not issue_codes
    else:
        expected = set(case.expected_issue_codes)
        passed = bool(expected) and expected.issubset(set(issue_codes))
    return RPBoundaryEvalResult(
        case_id=case.id,
        rule=case.rule,
        passed=passed,
        safe_reason=_safe_reason(case, issue_codes, passed),
        issue_codes=issue_codes,
    )


def run_rp_boundary_evals(cases: list[RPBoundaryEvalCase]) -> RPBoundaryEvalReport:
    results = [evaluate_rp_boundary_case(case) for case in cases]
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    report = RPBoundaryEvalReport(
        total_cases=len(results),
        passed=passed,
        failed=failed,
        case_results=results,
    )
    report.quality_report = _quality_report_from_rp_boundary(report)
    return report


def _safe_reason(case: RPBoundaryEvalCase, issue_codes: list[str], passed: bool) -> str:
    if passed:
        return f"{case.rule.value}: expected boundary behavior observed."
    if case.should_pass:
        return f"{case.rule.value}: safe output was unexpectedly flagged with {', '.join(issue_codes) or 'no issues'}."
    expected = ", ".join(case.expected_issue_codes) or "an expected issue"
    observed = ", ".join(issue_codes) or "no issues"
    return f"{case.rule.value}: expected {expected}; observed {observed}."


def _quality_report_from_rp_boundary(report: RPBoundaryEvalReport) -> WorldQualityReport:
    issues = [
        QualityIssue(
            id=f"rp_boundary:{result.case_id}",
            severity=QualityIssueSeverity.ERROR,
            category="rp_boundary",
            message="RP boundary eval case failed.",
            safe_details={
                "case_id": result.case_id,
                "rule": result.rule.value,
                "reason": result.safe_reason,
                "issue_codes": ",".join(result.issue_codes),
            },
        )
        for result in report.case_results
        if not result.passed
    ]
    metrics = [
        QualityMetric(
            name="rp_boundary_cases",
            value=report.total_cases,
            category="rp_boundary",
            status=QualityMetricStatus.OK,
        ),
        QualityMetric(
            name="rp_boundary_failed",
            value=report.failed,
            category="rp_boundary",
            threshold=0,
            status=QualityMetricStatus.OK if report.failed == 0 else QualityMetricStatus.ERROR,
        ),
    ]
    return WorldQualityReport(
        world_id="rp_boundary_eval",
        categories=["rp_boundary"],
        metrics=metrics,
        issues=issues,
        summary={
            "total_cases": report.total_cases,
            "passed": report.passed,
            "failed": report.failed,
        },
        recommended_actions=[] if report.failed == 0 else ["Fix RP boundary regressions before enabling RP prompts."],
    )
