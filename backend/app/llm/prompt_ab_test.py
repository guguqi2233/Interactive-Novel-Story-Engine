from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from statistics import mean
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.intent_parser import IntentParser
from app.llm.memory_summarizer import MemorySummarizer
from app.llm.model_prompt_lab_policy import BenchmarkRun, ModelPromptLabPolicy, ProviderProfile, redact_sensitive_text
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.provider_factory import create_llm_provider
from app.llm.prompt_profiles import PromptProfile, PromptProfileStore
from app.llm.schemas import MemorySummary, NarrativeResult, PlayerActionType, PlayerIntent


class PromptABUseCase(StrEnum):
    NARRATOR = "narrator"
    RP_DIALOGUE = "RP_dialogue"
    INTENT_PARSER = "intent_parser"
    MEMORY_SUMMARY = "memory_summary"


class PromptABTestCase(BaseModel):
    id: str
    input_text: str = "search the square"
    visible_facts: list[str] = Field(default_factory=lambda: ["visible_square"])
    hidden_terms: list[str] = Field(default_factory=list)
    expected_schema: str | None = None
    tags: list[str] = Field(default_factory=list)
    max_prompt_preview_chars: int = Field(default=160, ge=20, le=500)

    def redacted_input_preview(self) -> str:
        redacted = redact_sensitive_text(self.input_text).text
        for term in self.hidden_terms:
            if term:
                redacted = redacted.replace(term, "[redacted-hidden]")
        return redacted[: self.max_prompt_preview_chars]


class PromptABTestRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"prompt-ab-{uuid4().hex}")
    profile_a_id: str
    profile_b_id: str
    test_cases: list[PromptABTestCase] = Field(default_factory=list)
    provider_id: str = "fake"
    model_id: str | None = None
    use_case: PromptABUseCase = PromptABUseCase.NARRATOR
    allow_real_provider: bool = False


class PromptABVariantResult(BaseModel):
    profile_id: str
    ok: bool
    latency_ms: float
    schema_valid: bool | None = None
    hidden_leak: bool = False
    consistency_flags: list[str] = Field(default_factory=list)
    style_metrics: dict[str, float] = Field(default_factory=dict)
    output_summary_safe: str = ""
    error_class: str | None = None
    error_message_safe: str | None = None


class PromptABCaseResult(BaseModel):
    case_id: str
    input_preview_redacted: str
    variant_a: PromptABVariantResult
    variant_b: PromptABVariantResult


class PromptABTestReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    profile_a_id: str
    profile_b_id: str
    provider_id: str
    model_id: str | None = None
    use_case: PromptABUseCase
    pass_fail: str
    cases: list[PromptABCaseResult] = Field(default_factory=list)
    schema_reliability: dict[str, float] = Field(default_factory=dict)
    hidden_leak_flags: list[str] = Field(default_factory=list)
    consistency_flags: list[str] = Field(default_factory=list)
    style_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    latency_cost_summary: dict[str, float] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_prompt_ab_test(
    request: PromptABTestRun,
    *,
    prompt_store: PromptProfileStore | None = None,
    settings: Settings | None = None,
) -> PromptABTestReport:
    active_settings = settings or Settings(llm_provider="mock")
    policy = ModelPromptLabPolicy()
    provider_profile = _provider_profile_from_request(request, active_settings)
    provider_decision = policy.evaluate_benchmark_run(
        BenchmarkRun(
            id=request.run_id,
            provider_profile=provider_profile,
            explicit_real_provider_opt_in=request.allow_real_provider,
            uses_provider_factory=True,
        )
    )
    if not provider_decision.allowed:
        return _blocked_report(request, provider_decision.blockers, provider_decision.warnings)

    store = prompt_store or PromptProfileStore()
    try:
        profile_a = policy.validate_prompt_profile(store.get_profile(request.profile_a_id))
        profile_b = policy.validate_prompt_profile(store.get_profile(request.profile_b_id))
    except ValueError as exc:
        return _blocked_report(request, [str(exc)], provider_decision.warnings)

    cases = request.test_cases or _default_cases(request.use_case)
    results = [
        _run_case_pair(request, case, profile_a, profile_b)
        for case in cases
    ]
    return _build_report(request, results, provider_decision.warnings)


def _run_case_pair(
    request: PromptABTestRun,
    case: PromptABTestCase,
    profile_a: PromptProfile,
    profile_b: PromptProfile,
) -> PromptABCaseResult:
    return PromptABCaseResult(
        case_id=case.id,
        input_preview_redacted=case.redacted_input_preview(),
        variant_a=_run_variant(request, case, profile_a),
        variant_b=_run_variant(request, case, profile_b),
    )


def _run_variant(
    request: PromptABTestRun,
    case: PromptABTestCase,
    profile: PromptProfile,
) -> PromptABVariantResult:
    provider = _create_provider(request, profile)
    started = perf_counter()
    try:
        output = _execute_case(provider, request.use_case, case, profile)
        latency = round((perf_counter() - started) * 1000, 3)
        output_text = _output_text(output)
        hidden_leak = _contains_hidden_term(output_text, case.hidden_terms)
        consistency_flags = _consistency_flags(output_text, case, request.use_case)
        schema_valid = request.use_case in {
            PromptABUseCase.NARRATOR,
            PromptABUseCase.INTENT_PARSER,
            PromptABUseCase.MEMORY_SUMMARY,
        } or None
        return PromptABVariantResult(
            profile_id=profile.id,
            ok=not hidden_leak,
            latency_ms=latency,
            schema_valid=schema_valid,
            hidden_leak=hidden_leak,
            consistency_flags=consistency_flags,
            style_metrics=_style_metrics(output_text, profile, request.use_case),
            output_summary_safe=_safe_output_summary(output),
        )
    except Exception as exc:
        latency = round((perf_counter() - started) * 1000, 3)
        return PromptABVariantResult(
            profile_id=profile.id,
            ok=False,
            latency_ms=latency,
            schema_valid=False if request.use_case != PromptABUseCase.RP_DIALOGUE else None,
            error_class=type(exc).__name__,
            error_message_safe=_safe_error_message(str(exc)),
        )


def _execute_case(provider: LLMProvider, use_case: PromptABUseCase, case: PromptABTestCase, profile: PromptProfile) -> object:
    if use_case == PromptABUseCase.INTENT_PARSER:
        return IntentParser(provider, prompt_profile=profile).parse(case.input_text)
    if use_case == PromptABUseCase.NARRATOR:
        return Narrator(provider, prompt_profile=profile).render(
            player_input=case.input_text,
            action_result=ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Safe visible result.",
                visible_facts=case.visible_facts,
            ),
            visible_facts=case.visible_facts,
            current_location="square",
            tone="neutral",
        )
    if use_case == PromptABUseCase.MEMORY_SUMMARY:
        return MemorySummarizer(provider, prompt_profile=profile).summarize_recent(events=[], limit=0)
    if use_case == PromptABUseCase.RP_DIALOGUE:
        return provider.generate_text(
            [
                {"role": "system", "content": f"RP style: {profile.rp_profile.style_summary()}"},
                {"role": "user", "content": case.input_text},
            ],
            temperature=0.2,
        )
    raise ValueError(f"Unsupported Prompt A/B use case: {use_case}")


def _create_provider(request: PromptABTestRun, profile: PromptProfile) -> LLMProvider:
    if request.provider_id == "fake":
        return _PromptABFakeProvider(profile)
    if request.provider_id == "fake_leaky":
        return _PromptABFakeProvider(profile, leak_text="the mayor forged the charter")
    provider_name = "local_http" if request.provider_id == "openai_compatible" else request.provider_id
    return create_llm_provider(Settings(llm_provider=provider_name, llm_model=request.model_id or "gpt-4.1-mini"))


class _PromptABFakeProvider(LLMProvider):
    def __init__(self, profile: PromptProfile, leak_text: str = "") -> None:
        self._profile = profile
        self._leak_text = leak_text

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        suffix = f" {self._leak_text}" if self._leak_text else ""
        return f"{self._profile.name} voice: calm local reply.{suffix}"

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        _ = messages, temperature
        if schema is PlayerIntent:
            return schema.model_validate(
                {
                    "action_type": PlayerActionType.SEARCH.value,
                    "raw_text": "search the square",
                    "confidence": 0.9,
                    "requires_clarification": False,
                }
            )
        if schema is NarrativeResult:
            return schema.model_validate(
                {
                    "text": f"{self._profile.name} narration stays grounded.",
                    "suggested_actions": ["observe", "search"],
                    "short_summary": "Safe A/B narration.",
                }
            )
        if schema is MemorySummary:
            return schema.model_validate(
                {
                    "summary": "Safe memory summary.",
                    "important_facts": ["visible_square"],
                    "open_threads": [],
                    "npc_relationship_changes": [],
                }
            )
        raise LLMProviderError(f"PromptABFakeProvider does not support schema: {schema.__name__}")


def _provider_profile_from_request(request: PromptABTestRun, settings: Settings) -> ProviderProfile:
    provider_id = request.provider_id.strip().lower()
    provider_type = provider_id
    if provider_id == "fake_leaky":
        provider_type = "fake"
    if provider_id == "openai_compatible":
        provider_type = "local_http"
    if provider_type not in {"mock", "fake", "local_stub", "local_http", "openai"}:
        provider_type = settings.llm_provider.strip().lower()
    return ProviderProfile(
        provider_id=provider_id,
        provider_type=provider_type,  # type: ignore[arg-type]
        model_id=request.model_id or provider_id,
        api_key_configured=bool(settings.llm_api_key),
        uses_real_external_api=provider_type == "openai",
    )


def _default_cases(use_case: PromptABUseCase) -> list[PromptABTestCase]:
    return [
        PromptABTestCase(
            id=f"default_{use_case.value}",
            input_text="search the square",
            expected_schema=_schema_name(use_case),
        )
    ]


def _schema_name(use_case: PromptABUseCase) -> str | None:
    if use_case == PromptABUseCase.INTENT_PARSER:
        return PlayerIntent.__name__
    if use_case == PromptABUseCase.NARRATOR:
        return NarrativeResult.__name__
    if use_case == PromptABUseCase.MEMORY_SUMMARY:
        return MemorySummary.__name__
    return None


def _build_report(request: PromptABTestRun, results: list[PromptABCaseResult], warnings: list[str]) -> PromptABTestReport:
    variant_results = [result.variant_a for result in results] + [result.variant_b for result in results]
    hidden_flags = [
        f"{case.case_id}:{variant.profile_id}"
        for case in results
        for variant in [case.variant_a, case.variant_b]
        if variant.hidden_leak
    ]
    consistency = sorted({flag for variant in variant_results for flag in variant.consistency_flags})
    return PromptABTestReport(
        run_id=request.run_id,
        profile_a_id=request.profile_a_id,
        profile_b_id=request.profile_b_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        use_case=request.use_case,
        pass_fail="fail" if hidden_flags or any(not variant.ok for variant in variant_results) else "pass",
        cases=results,
        schema_reliability=_schema_reliability(variant_results),
        hidden_leak_flags=hidden_flags,
        consistency_flags=consistency,
        style_metrics=_aggregate_style_metrics(variant_results),
        latency_cost_summary={
            "average_latency_ms": round(mean([variant.latency_ms for variant in variant_results]), 3) if variant_results else 0.0,
            "estimated_cost": 0.0,
        },
        warnings=warnings,
    )


def _blocked_report(request: PromptABTestRun, blockers: list[str], warnings: list[str]) -> PromptABTestReport:
    return PromptABTestReport(
        run_id=request.run_id,
        profile_a_id=request.profile_a_id,
        profile_b_id=request.profile_b_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        use_case=request.use_case,
        pass_fail="fail",
        blockers=blockers,
        warnings=warnings,
    )


def _schema_reliability(variants: list[PromptABVariantResult]) -> dict[str, float]:
    grouped: dict[str, list[PromptABVariantResult]] = {}
    for variant in variants:
        if variant.schema_valid is None:
            continue
        grouped.setdefault(variant.profile_id, []).append(variant)
    return {
        profile_id: round(sum(1 for variant in items if variant.schema_valid) / len(items), 4)
        for profile_id, items in grouped.items()
        if items
    }


def _aggregate_style_metrics(variants: list[PromptABVariantResult]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, float]]] = {}
    for variant in variants:
        grouped.setdefault(variant.profile_id, []).append(variant.style_metrics)
    return {
        profile_id: {
            key: round(mean([item.get(key, 0.0) for item in items]), 4)
            for key in sorted({metric_key for item in items for metric_key in item})
        }
        for profile_id, items in grouped.items()
    }


def _style_metrics(text: str, profile: PromptProfile, use_case: PromptABUseCase) -> dict[str, float]:
    words = [word for word in text.split() if word]
    return {
        "word_count": float(len(words)),
        "profile_style_marker": 1.0 if profile.name.lower() in text.lower() else 0.0,
        "rp_style_case": 1.0 if use_case == PromptABUseCase.RP_DIALOGUE else 0.0,
    }


def _consistency_flags(text: str, case: PromptABTestCase, use_case: PromptABUseCase) -> list[str]:
    flags: list[str] = []
    lowered = text.lower()
    if "state_delta" in lowered or "gamestate" in lowered:
        flags.append("raw_state_reference")
    if use_case != PromptABUseCase.INTENT_PARSER and "quest complete" in lowered:
        flags.append("unauthorized_quest_claim")
    if _contains_hidden_term(text, case.hidden_terms):
        flags.append("hidden_leak")
    return flags


def _contains_hidden_term(text: str, hidden_terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in hidden_terms if term)


def _output_text(output: object) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, NarrativeResult):
        return output.text
    if isinstance(output, MemorySummary):
        return output.summary
    if isinstance(output, PlayerIntent):
        return output.raw_text
    return str(output)


def _safe_output_summary(output: object) -> str:
    text = _output_text(output)
    return redact_sensitive_text(text).text[:120]


def _safe_error_message(message: str) -> str:
    redacted = redact_sensitive_text(message).text
    if "hidden fact" in redacted.lower() or "sk-" in redacted.lower() or "api_key" in redacted.lower():
        return "[redacted]"
    return redacted[:160]


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            stripped = _strip_sensitive(item)
            if _safe_key_value(str(key), stripped):
                safe[str(key)] = stripped
        return safe
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = redact_sensitive_text(value).text
        lowered = redacted.lower()
        if "hidden fact" in lowered or "the mayor forged the charter" in lowered:
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    forbidden = ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-"]
    return not any(term in lowered for term in forbidden)
