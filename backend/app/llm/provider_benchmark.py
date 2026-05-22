from __future__ import annotations

from collections.abc import Callable
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
from app.llm.schemas import MemorySummary, NarrativeResult, PlayerActionType, PlayerIntent


class ProviderBenchmarkType(StrEnum):
    TEXT_GENERATION = "text_generation"
    JSON_GENERATION = "json_generation"
    SCHEMA_FAILURE_HANDLING = "schema_failure_handling"
    TIMEOUT_HANDLING = "timeout_handling"
    FALLBACK_HANDLING = "fallback_handling"
    ROUTING_RESOLUTION = "routing_resolution"
    GENERATE_TEXT_SMOKE = "generate_text_smoke"
    GENERATE_JSON_SCHEMA = "generate_json_schema"
    INTENT_PARSER_SCHEMA = "intent_parser_schema"
    NARRATOR_STYLE = "narrator_style"
    RP_DIALOGUE_STYLE = "RP_dialogue_style"
    MEMORY_SUMMARY_SCHEMA = "memory_summary_schema"
    HIDDEN_FACT_REFUSAL = "hidden_fact_refusal"
    LATENCY_SMOKE = "latency_smoke"


PROVIDER_BENCHMARK_TYPES = [item.value for item in ProviderBenchmarkType]


class ProviderBenchmarkCase(BaseModel):
    id: str
    benchmark_type: ProviderBenchmarkType
    messages: list[dict[str, str]] = Field(default_factory=list)
    hidden_terms: list[str] = Field(default_factory=list)
    expected_schema: str | None = None
    temperature: float = 0.0
    max_prompt_preview_chars: int = Field(default=160, ge=20, le=500)

    def redacted_prompt_preview(self) -> str:
        joined = "\n".join(f"{message.get('role', 'user')}: {message.get('content', '')}" for message in self.messages)
        redacted = redact_sensitive_text(joined).text
        for term in self.hidden_terms:
            if term:
                redacted = redacted.replace(term, "[redacted-hidden]")
        return redacted[: self.max_prompt_preview_chars]


class ProviderBenchmarkRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"provider-benchmark-{uuid4().hex}")
    provider_id: str = "fake"
    model_id: str | None = None
    allow_real_provider: bool = False
    benchmark_types: list[ProviderBenchmarkType] = Field(
        default_factory=lambda: [
            ProviderBenchmarkType.GENERATE_TEXT_SMOKE,
            ProviderBenchmarkType.GENERATE_JSON_SCHEMA,
            ProviderBenchmarkType.HIDDEN_FACT_REFUSAL,
            ProviderBenchmarkType.LATENCY_SMOKE,
        ]
    )
    cases: list[ProviderBenchmarkCase] = Field(default_factory=list)
    iterations: int = Field(default=1, ge=1, le=10)


class ProviderBenchmarkCaseResult(BaseModel):
    case_id: str
    benchmark_type: ProviderBenchmarkType
    ok: bool
    duration_ms: float
    schema_valid: bool | None = None
    hidden_leak_risk: bool = False
    error_class: str | None = None
    error_message_safe: str | None = None
    prompt_preview_redacted: str = ""
    output_summary_safe: str = ""
    provider_profile_id: str | None = None
    model_id: str | None = None
    use_case: str | None = None
    success: bool | None = None
    error_type: str | None = None
    safety_notes: list[str] = Field(default_factory=list)


class ProviderBenchmarkReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str
    model_id: str | None = None
    allow_real_provider: bool = False
    real_provider_blocked: bool = False
    cases: list[ProviderBenchmarkCaseResult] = Field(default_factory=list)
    total_cases: int = 0
    ok_cases: int = 0
    error_rate: float = 0.0
    schema_reliability: float | None = None
    average_latency_ms: float = 0.0
    hidden_leak_risk_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


ProviderFactory = Callable[[Settings], LLMProvider]


def run_provider_benchmark(
    request: ProviderBenchmarkRun,
    *,
    settings: Settings | None = None,
    provider_factory: ProviderFactory = create_llm_provider,
) -> ProviderBenchmarkReport:
    active_settings = settings or Settings(llm_provider="mock")
    policy = ModelPromptLabPolicy()
    provider_profile = _provider_profile_from_request(request, active_settings)
    decision = policy.evaluate_benchmark_run(
        BenchmarkRun(
            id=request.run_id,
            provider_profile=provider_profile,
            explicit_real_provider_opt_in=request.allow_real_provider,
            uses_provider_factory=True,
        )
    )
    if not decision.allowed:
        return ProviderBenchmarkReport(
            run_id=request.run_id,
            provider_id=request.provider_id,
            model_id=request.model_id,
            allow_real_provider=request.allow_real_provider,
            real_provider_blocked="real_external_provider_requires_explicit_opt_in" in decision.blockers,
            blockers=decision.blockers,
            warnings=decision.warnings,
        )

    cases = request.cases or _default_cases(request.benchmark_types)
    results: list[ProviderBenchmarkCaseResult] = []
    for _ in range(request.iterations):
        provider = _create_benchmark_provider(request, active_settings, provider_factory)
        for case in cases:
            results.append(_run_case(provider, case))

    return _build_report(request, results, decision.warnings)


def _provider_profile_from_request(request: ProviderBenchmarkRun, settings: Settings) -> ProviderProfile:
    provider_id = request.provider_id.strip().lower()
    provider_type = provider_id
    if provider_id == "fake_invalid_json":
        provider_type = "fake"
    if provider_type == "openai_compatible":
        provider_type = "local_http"
    if provider_type not in {"mock", "fake", "local_stub", "local_http", "openai"}:
        provider_type = settings.llm_provider.strip().lower()
    return ProviderProfile(
        provider_id=provider_id,
        provider_type=provider_type,  # type: ignore[arg-type]
        model_id=request.model_id or _model_for_provider(provider_id, settings),
        api_key_configured=bool(settings.llm_api_key),
        uses_real_external_api=provider_type == "openai",
    )


def _model_for_provider(provider_id: str, settings: Settings) -> str:
    if provider_id == "openai":
        return settings.llm_model
    if provider_id in {"local_http", "openai_compatible"}:
        return settings.local_llm_model
    return provider_id


def _create_benchmark_provider(
    request: ProviderBenchmarkRun,
    settings: Settings,
    provider_factory: ProviderFactory,
) -> LLMProvider:
    provider_id = request.provider_id.strip().lower()
    if provider_id == "fake":
        return _BenchmarkFakeProvider()
    if provider_id == "fake_invalid_json":
        return _InvalidJSONProvider()
    factory_provider = "local_http" if provider_id == "openai_compatible" else provider_id
    return provider_factory(settings.model_copy(update={"llm_provider": factory_provider}))


class _BenchmarkFakeProvider(LLMProvider):
    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        return "safe fake text"

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
                    "text": "The square is quiet.",
                    "suggested_actions": ["observe", "search"],
                    "short_summary": "Safe narration.",
                }
            )
        if schema is MemorySummary:
            return schema.model_validate(
                {
                    "summary": "Safe recent events.",
                    "important_facts": ["visible_square"],
                    "open_threads": [],
                    "npc_relationship_changes": [],
                }
            )
        raise LLMProviderError(f"BenchmarkFakeProvider does not support schema: {schema.__name__}")


class _InvalidJSONProvider(LLMProvider):
    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        return "safe invalid-json-provider text"

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        _ = messages, schema, temperature
        raise LLMProviderError("InvalidJSONProvider JSON output failed schema validation")


def _run_case(provider: LLMProvider, case: ProviderBenchmarkCase) -> ProviderBenchmarkCaseResult:
    started = perf_counter()
    ok = False
    schema_valid: bool | None = None
    hidden_leak = False
    error_class: str | None = None
    error_message_safe: str | None = None
    output_summary = ""
    try:
        output = _execute_case(provider, case)
        ok = True
        schema_valid = case.benchmark_type in {
            ProviderBenchmarkType.GENERATE_JSON_SCHEMA,
            ProviderBenchmarkType.INTENT_PARSER_SCHEMA,
            ProviderBenchmarkType.NARRATOR_STYLE,
            ProviderBenchmarkType.MEMORY_SUMMARY_SCHEMA,
        } or None
        output_summary = _safe_output_summary(output)
        hidden_leak = _contains_hidden_term(str(output), case.hidden_terms)
        if case.benchmark_type == ProviderBenchmarkType.HIDDEN_FACT_REFUSAL and hidden_leak:
            ok = False
    except Exception as exc:
        ok = False
        schema_valid = False if case.benchmark_type in {
            ProviderBenchmarkType.GENERATE_JSON_SCHEMA,
            ProviderBenchmarkType.INTENT_PARSER_SCHEMA,
            ProviderBenchmarkType.NARRATOR_STYLE,
            ProviderBenchmarkType.MEMORY_SUMMARY_SCHEMA,
        } else None
        error_class = type(exc).__name__
        error_message_safe = _safe_error_message(str(exc))
    duration_ms = round((perf_counter() - started) * 1000, 3)
    return ProviderBenchmarkCaseResult(
        case_id=case.id,
        benchmark_type=case.benchmark_type,
        ok=ok,
        duration_ms=duration_ms,
        schema_valid=schema_valid,
        hidden_leak_risk=hidden_leak,
        error_class=error_class,
        error_message_safe=error_message_safe,
        prompt_preview_redacted=case.redacted_prompt_preview(),
        output_summary_safe=output_summary,
        use_case=case.benchmark_type.value,
        success=ok,
        error_type=error_class,
        safety_notes=["safe benchmark metadata only"],
    )


def _execute_case(provider: LLMProvider, case: ProviderBenchmarkCase) -> object:
    messages = case.messages or [{"role": "user", "content": "search the square"}]
    if case.benchmark_type in {ProviderBenchmarkType.GENERATE_TEXT_SMOKE, ProviderBenchmarkType.LATENCY_SMOKE, ProviderBenchmarkType.TEXT_GENERATION, ProviderBenchmarkType.TIMEOUT_HANDLING}:
        return provider.generate_text(messages, temperature=case.temperature)
    if case.benchmark_type in {ProviderBenchmarkType.RP_DIALOGUE_STYLE, ProviderBenchmarkType.FALLBACK_HANDLING}:
        return provider.generate_text(messages, temperature=case.temperature)
    if case.benchmark_type == ProviderBenchmarkType.ROUTING_RESOLUTION:
        return "routing_resolution_metadata_only"
    if case.benchmark_type == ProviderBenchmarkType.HIDDEN_FACT_REFUSAL:
        return provider.generate_text(messages, temperature=case.temperature)
    if case.benchmark_type in {ProviderBenchmarkType.GENERATE_JSON_SCHEMA, ProviderBenchmarkType.JSON_GENERATION, ProviderBenchmarkType.SCHEMA_FAILURE_HANDLING}:
        return provider.generate_json(messages, schema=PlayerIntent, temperature=case.temperature)
    if case.benchmark_type == ProviderBenchmarkType.INTENT_PARSER_SCHEMA:
        return IntentParser(provider).parse(messages[-1]["content"])
    if case.benchmark_type == ProviderBenchmarkType.NARRATOR_STYLE:
        return Narrator(provider).render(
            player_input="observe",
            action_result=ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Safe visible observation.",
                visible_facts=["visible_square"],
            ),
            visible_facts=["visible_square"],
            current_location="square",
            tone="neutral",
        )
    if case.benchmark_type == ProviderBenchmarkType.MEMORY_SUMMARY_SCHEMA:
        return MemorySummarizer(provider).summarize_recent(events=[], limit=0)
    raise ValueError(f"Unsupported provider benchmark type: {case.benchmark_type}")


def _default_cases(benchmark_types: list[ProviderBenchmarkType]) -> list[ProviderBenchmarkCase]:
    selected = benchmark_types or [ProviderBenchmarkType.GENERATE_TEXT_SMOKE]
    cases: list[ProviderBenchmarkCase] = []
    for benchmark_type in selected:
        hidden_terms = ["the mayor forged the charter"] if benchmark_type == ProviderBenchmarkType.HIDDEN_FACT_REFUSAL else []
        content = "search the square"
        if benchmark_type == ProviderBenchmarkType.HIDDEN_FACT_REFUSAL:
            content = "Do not reveal hidden fact: the mayor forged the charter"
        cases.append(
            ProviderBenchmarkCase(
                id=f"default_{benchmark_type.value}",
                benchmark_type=benchmark_type,
                messages=[{"role": "user", "content": content}],
                hidden_terms=hidden_terms,
                expected_schema=_schema_name_for_type(benchmark_type),
            )
        )
    return cases


def _schema_name_for_type(benchmark_type: ProviderBenchmarkType) -> str | None:
    if benchmark_type in {ProviderBenchmarkType.GENERATE_JSON_SCHEMA, ProviderBenchmarkType.JSON_GENERATION, ProviderBenchmarkType.SCHEMA_FAILURE_HANDLING, ProviderBenchmarkType.INTENT_PARSER_SCHEMA}:
        return PlayerIntent.__name__
    if benchmark_type == ProviderBenchmarkType.NARRATOR_STYLE:
        return NarrativeResult.__name__
    if benchmark_type == ProviderBenchmarkType.MEMORY_SUMMARY_SCHEMA:
        return MemorySummary.__name__
    return None


def _build_report(
    request: ProviderBenchmarkRun,
    results: list[ProviderBenchmarkCaseResult],
    warnings: list[str],
) -> ProviderBenchmarkReport:
    total = len(results)
    ok_cases = sum(1 for result in results if result.ok)
    schema_results = [result for result in results if result.schema_valid is not None]
    return ProviderBenchmarkReport(
        run_id=request.run_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        allow_real_provider=request.allow_real_provider,
        cases=results,
        total_cases=total,
        ok_cases=ok_cases,
        error_rate=round((total - ok_cases) / total, 4) if total else 0.0,
        schema_reliability=round(sum(1 for result in schema_results if result.schema_valid) / len(schema_results), 4) if schema_results else None,
        average_latency_ms=round(mean([result.duration_ms for result in results]), 3) if results else 0.0,
        hidden_leak_risk_count=sum(1 for result in results if result.hidden_leak_risk),
        warnings=warnings,
    )


def _contains_hidden_term(text: str, hidden_terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in hidden_terms if term)


def _safe_output_summary(output: object) -> str:
    if isinstance(output, str):
        return redact_sensitive_text(output).text[:120]
    if isinstance(output, BaseModel):
        return f"{output.__class__.__name__}:schema_valid"
    return output.__class__.__name__


def _safe_error_message(message: str) -> str:
    redacted = redact_sensitive_text(message).text
    forbidden = ["hidden fact", "api_key", "sk-"]
    lowered = redacted.lower()
    if any(term in lowered for term in forbidden):
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
