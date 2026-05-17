from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.schemas import NarrativeResult


class NarrativeQualityRule(StrEnum):
    NO_CONTRADICTION_WITH_ACTION_RESULT = "no_contradiction_with_action_result"
    NO_INVENTED_KEY_ITEM = "no_invented_key_item"
    NO_INVENTED_NPC = "no_invented_npc"
    NO_INVENTED_LOCATION = "no_invented_location"
    NO_HIDDEN_FACT_LEAKAGE = "no_hidden_fact_leakage"
    CONCISE_ENOUGH = "concise_enough"
    MENTIONS_VISIBLE_CONSEQUENCE = "mentions_visible_consequence_when_relevant"
    DOES_NOT_REVEAL_HIDDEN_WITNESS = "does_not_reveal_hidden_witness"
    SUGGESTED_ACTIONS_ARE_LEGAL = "suggested_actions_are_legal_or_marked"


class NarrativeQualityCase(BaseModel):
    id: str
    player_input: str = ""
    action_result: ActionResult
    narrative: NarrativeResult
    known_items: list[str] = Field(default_factory=list)
    known_npcs: list[str] = Field(default_factory=list)
    known_locations: list[str] = Field(default_factory=list)
    hidden_fact_texts: list[str] = Field(default_factory=list)
    hidden_witness_ids: list[str] = Field(default_factory=list)
    allowed_suggested_actions: list[str] = Field(default_factory=list)
    required_mentions: list[str] = Field(default_factory=list)
    invented_item_terms: list[str] = Field(default_factory=list)
    invented_npc_terms: list[str] = Field(default_factory=list)
    invented_location_terms: list[str] = Field(default_factory=list)
    max_text_chars: int = 600
    require_visible_consequence: bool = False


class NarrativeQualityCaseResult(BaseModel):
    case_id: str
    category: str = "general"
    passed: bool
    skipped: bool = False
    failure_reasons: list[str] = Field(default_factory=list)


class NarrativeQualityReport(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_cases: int
    passed: int
    failed: int
    skipped: int = 0
    failure_reasons: dict[str, list[str]] = Field(default_factory=dict)
    categories: dict[str, dict[str, int]] = Field(default_factory=dict)
    results: list[NarrativeQualityCaseResult] = Field(default_factory=list)
    case_results: list[NarrativeQualityCaseResult] = Field(default_factory=list)


def evaluate_narrative_quality(case: NarrativeQualityCase) -> NarrativeQualityCaseResult:
    text = case.narrative.text
    lower_text = text.lower()
    reasons: list[str] = []

    _check_action_result_contradiction(case, lower_text, reasons)
    _check_forbidden_terms(NarrativeQualityRule.NO_INVENTED_KEY_ITEM, case.invented_item_terms, lower_text, reasons)
    _check_forbidden_terms(NarrativeQualityRule.NO_INVENTED_NPC, case.invented_npc_terms, lower_text, reasons)
    _check_forbidden_terms(
        NarrativeQualityRule.NO_INVENTED_LOCATION,
        case.invented_location_terms,
        lower_text,
        reasons,
    )
    _check_forbidden_terms(NarrativeQualityRule.NO_HIDDEN_FACT_LEAKAGE, case.hidden_fact_texts, text, reasons)
    _check_forbidden_terms(
        NarrativeQualityRule.DOES_NOT_REVEAL_HIDDEN_WITNESS,
        case.hidden_witness_ids,
        text,
        reasons,
    )
    if len(text) > case.max_text_chars:
        reasons.append(f"{NarrativeQualityRule.CONCISE_ENOUGH}:text_too_long")
    if case.require_visible_consequence:
        missing_mentions = [
            required
            for required in case.required_mentions
            if required.lower() not in lower_text
        ]
        if missing_mentions:
            reasons.append(
                f"{NarrativeQualityRule.MENTIONS_VISIBLE_CONSEQUENCE}:missing:{','.join(missing_mentions)}"
            )
    illegal_suggestions = [
        suggestion
        for suggestion in case.narrative.suggested_actions
        if not _suggested_action_allowed(suggestion, case.allowed_suggested_actions)
    ]
    if illegal_suggestions:
        reasons.append(
            f"{NarrativeQualityRule.SUGGESTED_ACTIONS_ARE_LEGAL}:illegal:{','.join(illegal_suggestions)}"
        )

    return NarrativeQualityCaseResult(
        case_id=case.id,
        category=_case_category(case),
        passed=not reasons,
        failure_reasons=reasons,
    )


def run_narrative_quality_evals(cases: list[NarrativeQualityCase]) -> NarrativeQualityReport:
    results = [evaluate_narrative_quality(case) for case in cases]
    failures = {result.case_id: result.failure_reasons for result in results if not result.passed}
    passed = sum(1 for result in results if result.passed)
    categories = _category_summary(results)
    return NarrativeQualityReport(
        total_cases=len(results),
        passed=passed,
        failed=len(results) - passed,
        failure_reasons=failures,
        categories=categories,
        results=results,
        case_results=results,
    )


def sample_narrative_quality_cases() -> list[NarrativeQualityCase]:
    return [
        NarrativeQualityCase(
            id="sample_success",
            player_input="observe",
            action_result=ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Observed current location.",
                visible_facts=["square"],
            ),
            narrative=NarrativeResult(
                text="你看清了广场的出口，周围暂时没有新的危险。",
                suggested_actions=["observe", "search"],
                short_summary="The player observed the square.",
            ),
            allowed_suggested_actions=["observe", "search", "wait 30"],
            required_mentions=["出口"],
            require_visible_consequence=True,
        )
    ]


def _check_action_result_contradiction(
    case: NarrativeQualityCase,
    lower_text: str,
    reasons: list[str],
) -> None:
    success_words = ["succeeded", "successfully", "成功", "顺利", "打开了", "击中了"]
    failure_words = ["failed", "failure", "失败", "没能", "无法", "没有成功"]
    level = case.action_result.success_level
    if level in {SuccessLevel.FAILURE, SuccessLevel.INVALID} and any(word in lower_text for word in success_words):
        reasons.append(f"{NarrativeQualityRule.NO_CONTRADICTION_WITH_ACTION_RESULT}:failure_described_as_success")
    if level == SuccessLevel.SUCCESS and any(word in lower_text for word in failure_words):
        reasons.append(f"{NarrativeQualityRule.NO_CONTRADICTION_WITH_ACTION_RESULT}:success_described_as_failure")


def _check_forbidden_terms(
    rule: NarrativeQualityRule,
    terms: list[str],
    text: str,
    reasons: list[str],
) -> None:
    text_to_search = text.lower()
    for term in terms:
        if term and term.lower() in text_to_search:
            reasons.append(f"{rule}:forbidden:{_redacted_term_marker(term)}")


def _redacted_term_marker(term: str) -> str:
    digest = sha256(term.encode("utf-8")).hexdigest()[:12]
    return f"[redacted:{digest}]"


def _suggested_action_allowed(suggestion: str, allowed_actions: list[str]) -> bool:
    normalized = suggestion.strip().lower()
    allowed = {action.strip().lower() for action in allowed_actions}
    if normalized in allowed:
        return True
    return normalized.startswith(("suggest:", "try ", "consider ", "maybe "))


def _case_category(case: NarrativeQualityCase) -> str:
    if case.hidden_fact_texts or case.hidden_witness_ids:
        return "visibility"
    if case.invented_item_terms or case.invented_npc_terms or case.invented_location_terms:
        return "invention"
    if case.require_visible_consequence or case.required_mentions:
        return "continuity"
    if case.allowed_suggested_actions:
        return "suggested_actions"
    return "general"


def _category_summary(results: list[NarrativeQualityCaseResult]) -> dict[str, dict[str, int]]:
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
