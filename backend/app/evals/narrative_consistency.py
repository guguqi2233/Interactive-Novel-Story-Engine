from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.schemas import NarrativeResult
from app.quality import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class NarrativeConsistencyRule(StrEnum):
    NO_CONTRADICTION_WITH_ACTION_RESULT = "no_contradiction_with_action_result"
    NO_CONTRADICTION_WITH_VISIBLE_STATE = "no_contradiction_with_visible_state"
    NO_CONTRADICTION_WITH_TIMELINE = "no_contradiction_with_timeline"
    NO_DEAD_NPC_SPEAKING = "no_dead_npc_speaking"
    NO_NPC_KNOWING_UNKNOWN_FACT = "no_npc_knowing_unknown_fact"
    NO_ITEM_INVENTED = "no_item_invented"
    NO_LOCATION_INVENTED = "no_location_invented"
    NO_QUEST_STAGE_INVENTED = "no_quest_stage_invented"
    NO_HIDDEN_WITNESS_REVEALED = "no_hidden_witness_revealed"
    NO_MEMORY_AS_AUTHORITATIVE_FACT = "no_memory_treated_as_authoritative_fact"


class NarrativeConsistencyCase(BaseModel):
    id: str
    world_id: str = "test_world"
    action_result: ActionResult
    narrative: NarrativeResult
    visible_state: dict[str, Any] = Field(default_factory=dict)
    timeline_facts: list[str] = Field(default_factory=list)
    known_items: list[str] = Field(default_factory=list)
    known_locations: list[str] = Field(default_factory=list)
    known_quest_stages: list[str] = Field(default_factory=list)
    dead_npc_ids: list[str] = Field(default_factory=list)
    npc_known_facts: dict[str, list[str]] = Field(default_factory=dict)
    npc_fact_mentions: dict[str, list[str]] = Field(default_factory=dict)
    hidden_witness_ids: list[str] = Field(default_factory=list)
    memory_only_facts: list[str] = Field(default_factory=list)
    authoritative_facts: list[str] = Field(default_factory=list)
    invented_item_terms: list[str] = Field(default_factory=list)
    invented_location_terms: list[str] = Field(default_factory=list)
    invented_quest_stage_terms: list[str] = Field(default_factory=list)


class NarrativeConsistencyCaseResult(BaseModel):
    case_id: str
    category: str = "narrative_consistency"
    passed: bool
    skipped: bool = False
    failure_reasons: list[str] = Field(default_factory=list)


class NarrativeConsistencyReport(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_cases: int
    passed: int
    failed: int
    skipped: int = 0
    failure_reasons: dict[str, list[str]] = Field(default_factory=dict)
    categories: dict[str, dict[str, int]] = Field(default_factory=dict)
    case_results: list[NarrativeConsistencyCaseResult] = Field(default_factory=list)
    quality_report: WorldQualityReport | None = None


def evaluate_narrative_consistency(case: NarrativeConsistencyCase) -> NarrativeConsistencyCaseResult:
    text = case.narrative.text
    lower_text = text.lower()
    reasons: list[str] = []

    _check_action_result(case, lower_text, reasons)
    _check_visible_state(case, lower_text, reasons)
    _check_timeline(case, lower_text, reasons)
    _check_dead_npcs(case, lower_text, reasons)
    _check_npc_unknown_facts(case, lower_text, reasons)
    _check_forbidden_terms(NarrativeConsistencyRule.NO_ITEM_INVENTED, case.invented_item_terms, lower_text, reasons)
    _check_forbidden_terms(
        NarrativeConsistencyRule.NO_LOCATION_INVENTED,
        case.invented_location_terms,
        lower_text,
        reasons,
    )
    _check_forbidden_terms(
        NarrativeConsistencyRule.NO_QUEST_STAGE_INVENTED,
        case.invented_quest_stage_terms,
        lower_text,
        reasons,
    )
    _check_forbidden_terms(
        NarrativeConsistencyRule.NO_HIDDEN_WITNESS_REVEALED,
        case.hidden_witness_ids,
        text,
        reasons,
    )
    _check_memory_authority(case, lower_text, reasons)

    return NarrativeConsistencyCaseResult(
        case_id=case.id,
        passed=not reasons,
        failure_reasons=reasons,
    )


def run_narrative_consistency_evals(cases: list[NarrativeConsistencyCase]) -> NarrativeConsistencyReport:
    results = [evaluate_narrative_consistency(case) for case in cases]
    passed = sum(1 for result in results if result.passed)
    failures = {result.case_id: result.failure_reasons for result in results if not result.passed}
    world_id = cases[0].world_id if cases else "unknown"
    return NarrativeConsistencyReport(
        total_cases=len(results),
        passed=passed,
        failed=len(results) - passed,
        failure_reasons=failures,
        categories=_category_summary(results),
        case_results=results,
        quality_report=_to_world_quality_report(world_id, results),
    )


def _check_action_result(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    success_words = ["succeeded", "successfully", "worked", "opened", "unlocked"]
    failure_words = ["failed", "could not", "cannot", "blocked", "stuck"]
    if case.action_result.success_level in {SuccessLevel.FAILURE, SuccessLevel.INVALID}:
        if any(word in lower_text for word in success_words):
            reasons.append(f"{NarrativeConsistencyRule.NO_CONTRADICTION_WITH_ACTION_RESULT}:failure_described_as_success")
    if case.action_result.success_level == SuccessLevel.SUCCESS:
        if any(word in lower_text for word in failure_words):
            reasons.append(f"{NarrativeConsistencyRule.NO_CONTRADICTION_WITH_ACTION_RESULT}:success_described_as_failure")


def _check_visible_state(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    forbidden = _as_str_list(case.visible_state.get("forbidden_terms", []))
    _check_forbidden_terms(
        NarrativeConsistencyRule.NO_CONTRADICTION_WITH_VISIBLE_STATE,
        forbidden,
        lower_text,
        reasons,
    )


def _check_timeline(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    forbidden = [fact for fact in case.timeline_facts if fact.startswith("not:")]
    _check_forbidden_terms(
        NarrativeConsistencyRule.NO_CONTRADICTION_WITH_TIMELINE,
        [fact.removeprefix("not:") for fact in forbidden],
        lower_text,
        reasons,
    )


def _check_dead_npcs(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    for npc_id in case.dead_npc_ids:
        normalized = npc_id.lower()
        if normalized and normalized in lower_text and any(word in lower_text for word in ["says", "speaks", "tells", "whispers"]):
            reasons.append(f"{NarrativeConsistencyRule.NO_DEAD_NPC_SPEAKING}:npc:{_redacted_term_marker(npc_id)}")


def _check_npc_unknown_facts(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    for npc_id, mentioned_facts in case.npc_fact_mentions.items():
        known = {fact.lower() for fact in case.npc_known_facts.get(npc_id, [])}
        if npc_id.lower() not in lower_text:
            continue
        for fact in mentioned_facts:
            if fact.lower() not in known and fact.lower() in lower_text:
                reasons.append(
                    f"{NarrativeConsistencyRule.NO_NPC_KNOWING_UNKNOWN_FACT}:npc:{_redacted_term_marker(npc_id)}:fact:{_redacted_term_marker(fact)}"
                )


def _check_memory_authority(
    case: NarrativeConsistencyCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    authoritative = {fact.lower() for fact in case.authoritative_facts}
    for memory_fact in case.memory_only_facts:
        if memory_fact.lower() in authoritative:
            continue
        if memory_fact.lower() in lower_text and any(
            marker in lower_text
            for marker in ["it is certain", "it is fact", "the truth is", "proves that", "confirms that"]
        ):
            reasons.append(
                f"{NarrativeConsistencyRule.NO_MEMORY_AS_AUTHORITATIVE_FACT}:memory:{_redacted_term_marker(memory_fact)}"
            )


def _check_forbidden_terms(
    rule: NarrativeConsistencyRule,
    terms: list[str],
    lower_text: str,
    reasons: list[str],
) -> None:
    for term in terms:
        normalized = term.lower()
        if normalized and normalized in lower_text:
            reasons.append(f"{rule}:forbidden:{_redacted_term_marker(term)}")


def _to_world_quality_report(
    world_id: str,
    results: list[NarrativeConsistencyCaseResult],
) -> WorldQualityReport:
    issues = [
        QualityIssue(
            id=f"narrative_consistency:{result.case_id}:{index}",
            severity=QualityIssueSeverity.ERROR,
            category="narrative_consistency",
            entity_id=result.case_id,
            message="Narrative consistency eval failed.",
            safe_details={"reason": reason},
        )
        for result in results
        if not result.passed
        for index, reason in enumerate(result.failure_reasons)
    ]
    return WorldQualityReport(
        world_id=world_id,
        categories=["narrative_consistency"],
        metrics=[
            QualityMetric(
                name="narrative_consistency_cases",
                value=len(results),
                category="narrative_consistency",
                status=QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="narrative_consistency_failures",
                value=sum(1 for result in results if not result.passed),
                category="narrative_consistency",
                threshold=0,
                status=QualityMetricStatus.ERROR if issues else QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary={
            "total_cases": len(results),
            "passed": sum(1 for result in results if result.passed),
            "failed": sum(1 for result in results if not result.passed),
        },
        recommended_actions=["Review failed narrative consistency cases before release."] if issues else [],
    ).normal_copy()


def _category_summary(results: list[NarrativeConsistencyCaseResult]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for result in results:
        bucket = summary.setdefault(result.category, {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
        bucket["total"] += 1
        if result.skipped:
            bucket["skipped"] += 1
        elif result.passed:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return summary


def _redacted_term_marker(term: str) -> str:
    digest = sha256(term.encode("utf-8")).hexdigest()[:12]
    return f"[redacted:{digest}]"


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
