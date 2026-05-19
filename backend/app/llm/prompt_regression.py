from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from statistics import mean
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.llm.model_prompt_lab_policy import BenchmarkRun, ModelPromptLabPolicy, ProviderProfile, redact_sensitive_text
from app.llm.narrator_style_lab import NarratorStyleExperiment, run_narrator_style_experiment
from app.llm.npc_voice_style_lab import NPCVoiceDialogueTestCase, NPCVoiceStyleExperiment, run_npc_voice_style_experiment
from app.llm.prompt_ab_test import PromptABTestCase, PromptABTestRun, PromptABUseCase, run_prompt_ab_test
from app.llm.prompt_profiles import PromptProfileStore
from app.llm.structured_output_reliability import (
    StructuredOutputReliabilityRun,
    StructuredOutputSchemaName,
    StructuredOutputTestCase,
    run_structured_output_reliability,
)


class PromptRegressionCaseType(StrEnum):
    INTENT_PARSER_SCHEMA = "intent_parser_schema"
    NARRATOR_CONSISTENCY = "narrator_consistency"
    RP_DIALOGUE_BOUNDARY = "RP_dialogue_boundary"
    NPC_VOICE_CONSISTENCY = "NPC_voice_consistency"
    MEMORY_SUMMARY_SCHEMA = "memory_summary_schema"
    HIDDEN_LEAK = "hidden_leak"
    STRUCTURED_JSON_RELIABILITY = "structured_JSON_reliability"


PROMPT_REGRESSION_CASE_TYPES = [item.value for item in PromptRegressionCaseType]


class PromptRegressionCase(BaseModel):
    id: str
    case_type: PromptRegressionCaseType
    input_text: str = "search the square"
    hidden_terms: list[str] = Field(default_factory=lambda: ["the mayor forged the charter"])
    unknown_fact_terms: list[str] = Field(default_factory=lambda: ["unknown forbidden fact"])
    visible_facts: list[str] = Field(default_factory=lambda: ["visible_square"])
    expected_schema: str | None = None

    def safe_input_preview(self) -> str:
        text = redact_sensitive_text(self.input_text).text
        for term in self.hidden_terms + self.unknown_fact_terms:
            if term:
                text = text.replace(term, "[redacted-hidden]")
        return text[:160]


class PromptRegressionRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"prompt-regression-{uuid4().hex}")
    baseline_profile_id: str = "default_safe"
    candidate_profile_id: str = "default_safe"
    baseline_provider_id: str = "fake"
    baseline_model_id: str | None = None
    candidate_provider_id: str = "fake"
    candidate_model_id: str | None = None
    cases: list[PromptRegressionCase] = Field(default_factory=list)
    allow_real_provider: bool = False


class PromptRegressionVariantMetrics(BaseModel):
    provider_id: str
    model_id: str | None = None
    profile_id: str
    ok: bool
    schema_valid_rate: float | None = None
    hidden_leak_count: int = 0
    blocker_count: int = 0
    latency_ms: float = 0.0
    cost_estimated: float = 0.0
    safe_summary: str = ""


class PromptRegressionCaseResult(BaseModel):
    case_id: str
    case_type: PromptRegressionCaseType
    input_preview_redacted: str
    baseline: PromptRegressionVariantMetrics
    candidate: PromptRegressionVariantMetrics
    regressions: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    safety_blockers: list[str] = Field(default_factory=list)
    latency_delta_ms: float = 0.0
    cost_delta: float = 0.0


class PromptRegressionReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    baseline_profile_id: str
    candidate_profile_id: str
    baseline_provider_id: str
    baseline_model_id: str | None = None
    candidate_provider_id: str
    candidate_model_id: str | None = None
    pass_fail: str
    cases: list[PromptRegressionCaseResult] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    safety_blockers: list[str] = Field(default_factory=list)
    latency_cost_delta: dict[str, float] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_prompt_regression(
    request: PromptRegressionRun,
    *,
    prompt_store: PromptProfileStore | None = None,
    settings: Settings | None = None,
) -> PromptRegressionReport:
    active_settings = settings or Settings(llm_provider="mock")
    provider_blockers, provider_warnings = _validate_provider_access(request, active_settings)
    if provider_blockers:
        return _blocked_report(request, provider_blockers, provider_warnings)
    cases = request.cases or _default_cases()
    store = prompt_store or PromptProfileStore()
    try:
        store.get_profile(request.baseline_profile_id)
        store.get_profile(request.candidate_profile_id)
    except ValueError as exc:
        return _blocked_report(request, [str(exc)], provider_warnings)
    results = [_run_case(request, case, store, active_settings) for case in cases]
    regressions = [item for result in results for item in result.regressions]
    improvements = [item for result in results for item in result.improvements]
    safety_blockers = [item for result in results for item in result.safety_blockers]
    average_latency_delta = round(mean([result.latency_delta_ms for result in results]), 3) if results else 0.0
    total_cost_delta = round(sum(result.cost_delta for result in results), 8)
    return PromptRegressionReport(
        run_id=request.run_id,
        baseline_profile_id=request.baseline_profile_id,
        candidate_profile_id=request.candidate_profile_id,
        baseline_provider_id=request.baseline_provider_id,
        baseline_model_id=request.baseline_model_id,
        candidate_provider_id=request.candidate_provider_id,
        candidate_model_id=request.candidate_model_id,
        pass_fail="fail" if regressions or safety_blockers else "pass",
        cases=results,
        regressions=regressions,
        improvements=improvements,
        safety_blockers=safety_blockers,
        latency_cost_delta={
            "average_latency_delta_ms": average_latency_delta,
            "total_cost_delta": total_cost_delta,
        },
        warnings=provider_warnings,
    )


def _run_case(
    request: PromptRegressionRun,
    case: PromptRegressionCase,
    store: PromptProfileStore,
    settings: Settings,
) -> PromptRegressionCaseResult:
    baseline = _run_variant(request, case, store, settings, candidate=False)
    candidate = _run_variant(request, case, store, settings, candidate=True)
    regressions: list[str] = []
    improvements: list[str] = []
    safety_blockers: list[str] = []
    if candidate.hidden_leak_count > baseline.hidden_leak_count:
        regressions.append(f"{case.id}:hidden_leak_regression")
        safety_blockers.append(f"{case.id}:hidden_leak_regression")
    if candidate.blocker_count > baseline.blocker_count:
        regressions.append(f"{case.id}:blocker_count_regression")
    if _schema_rate(candidate) < _schema_rate(baseline):
        regressions.append(f"{case.id}:schema_reliability_regression")
    if candidate.latency_ms - baseline.latency_ms > 1000:
        regressions.append(f"{case.id}:latency_regression")
    if candidate.hidden_leak_count < baseline.hidden_leak_count:
        improvements.append(f"{case.id}:hidden_leak_improved")
    if _schema_rate(candidate) > _schema_rate(baseline):
        improvements.append(f"{case.id}:schema_reliability_improved")
    return PromptRegressionCaseResult(
        case_id=case.id,
        case_type=case.case_type,
        input_preview_redacted=case.safe_input_preview(),
        baseline=baseline,
        candidate=candidate,
        regressions=regressions,
        improvements=improvements,
        safety_blockers=safety_blockers,
        latency_delta_ms=round(candidate.latency_ms - baseline.latency_ms, 3),
        cost_delta=round(candidate.cost_estimated - baseline.cost_estimated, 8),
    )


def _run_variant(
    request: PromptRegressionRun,
    case: PromptRegressionCase,
    store: PromptProfileStore,
    settings: Settings,
    *,
    candidate: bool,
) -> PromptRegressionVariantMetrics:
    provider_id = request.candidate_provider_id if candidate else request.baseline_provider_id
    model_id = request.candidate_model_id if candidate else request.baseline_model_id
    profile_id = request.candidate_profile_id if candidate else request.baseline_profile_id
    effective_provider_id = _effective_provider(provider_id)
    if case.case_type in {
        PromptRegressionCaseType.INTENT_PARSER_SCHEMA,
        PromptRegressionCaseType.MEMORY_SUMMARY_SCHEMA,
        PromptRegressionCaseType.STRUCTURED_JSON_RELIABILITY,
    }:
        report = run_structured_output_reliability(
            StructuredOutputReliabilityRun(
                provider_id=effective_provider_id,
                model_id=model_id,
                allow_real_provider=request.allow_real_provider,
                cases=[_structured_case(case)],
            ),
            settings=settings,
        )
        latency = _with_latency_adjustment(report.cases[0].duration_ms if report.cases else 0.0, provider_id)
        return PromptRegressionVariantMetrics(
            provider_id=provider_id,
            model_id=model_id,
            profile_id=profile_id,
            ok=report.schema_valid_rate >= 1.0 and report.hidden_policy_violation_rate == 0.0 and not report.blockers,
            schema_valid_rate=report.schema_valid_rate,
            hidden_leak_count=sum(1 for item in report.cases if item.hidden_policy_violation),
            blocker_count=len(report.blockers) + sum(1 for item in report.cases if not item.ok),
            latency_ms=latency,
            safe_summary=f"schema_rate={report.schema_valid_rate}",
        )
    if case.case_type == PromptRegressionCaseType.NARRATOR_CONSISTENCY:
        report = run_narrator_style_experiment(
            NarratorStyleExperiment(
                prompt_profile_id=profile_id,
                provider_id=effective_provider_id,
                model_id=model_id,
                allow_real_provider=request.allow_real_provider,
                player_input=case.input_text,
                visible_facts=case.visible_facts,
                hidden_terms=case.hidden_terms,
            ),
            prompt_store=store,
            settings=settings,
        )
        return PromptRegressionVariantMetrics(
            provider_id=provider_id,
            model_id=model_id,
            profile_id=profile_id,
            ok=report.pass_fail == "pass",
            hidden_leak_count=sum(1 for finding in report.findings if finding.check == "no_hidden_fact_leak" and not finding.passed),
            blocker_count=len(report.blockers),
            latency_ms=_with_latency_adjustment(report.latency_ms, provider_id),
            safe_summary=report.output_summary_safe,
        )
    if case.case_type == PromptRegressionCaseType.NPC_VOICE_CONSISTENCY:
        report = run_npc_voice_style_experiment(
            NPCVoiceStyleExperiment(
                npc_id="regression_npc",
                rp_prompt_profile_id=profile_id,
                provider_id=effective_provider_id,
                model_id=model_id,
                allow_real_provider=request.allow_real_provider,
                dialogue_test_cases=[
                    NPCVoiceDialogueTestCase(
                        id=case.id,
                        player_line=case.input_text,
                        unknown_fact_terms=case.unknown_fact_terms,
                        hidden_terms=case.hidden_terms,
                    )
                ],
            ),
            prompt_store=store,
            settings=settings,
        )
        return PromptRegressionVariantMetrics(
            provider_id=provider_id,
            model_id=model_id,
            profile_id=profile_id,
            ok=report.pass_fail == "pass",
            hidden_leak_count=sum(1 for finding in report.findings if finding.check == "no_hidden_fact_leak" and not finding.passed),
            blocker_count=len(report.blockers),
            latency_ms=_with_latency_adjustment(report.latency_ms, provider_id),
            safe_summary="; ".join(report.output_summaries_safe[:1]),
        )
    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id=profile_id,
            profile_b_id=profile_id,
            provider_id=effective_provider_id,
            model_id=model_id,
            allow_real_provider=request.allow_real_provider,
            use_case=PromptABUseCase.RP_DIALOGUE,
            test_cases=[
                PromptABTestCase(
                    id=case.id,
                    input_text=case.input_text,
                    hidden_terms=case.hidden_terms,
                    visible_facts=case.visible_facts,
                )
            ],
        ),
        prompt_store=store,
        settings=settings,
    )
    hidden_count = len(report.hidden_leak_flags)
    return PromptRegressionVariantMetrics(
        provider_id=provider_id,
        model_id=model_id,
        profile_id=profile_id,
        ok=report.pass_fail == "pass",
        schema_valid_rate=next(iter(report.schema_reliability.values()), None),
        hidden_leak_count=hidden_count,
        blocker_count=len(report.blockers) + hidden_count,
        latency_ms=_with_latency_adjustment(report.latency_cost_summary.get("average_latency_ms", 0.0), provider_id),
        safe_summary=report.pass_fail,
    )


def _structured_case(case: PromptRegressionCase) -> StructuredOutputTestCase:
    schema_name = StructuredOutputSchemaName.PLAYER_INTENT
    if case.case_type == PromptRegressionCaseType.MEMORY_SUMMARY_SCHEMA:
        schema_name = StructuredOutputSchemaName.MEMORY_SUMMARY
    elif case.case_type == PromptRegressionCaseType.STRUCTURED_JSON_RELIABILITY:
        schema_name = StructuredOutputSchemaName.NARRATIVE_RESULT
    return StructuredOutputTestCase(
        id=case.id,
        schema_name=schema_name,
        messages=[{"role": "user", "content": case.input_text}],
        hidden_terms=case.hidden_terms,
        retry_once=False,
    )


def _validate_provider_access(request: PromptRegressionRun, settings: Settings) -> tuple[list[str], list[str]]:
    policy = ModelPromptLabPolicy()
    blockers: list[str] = []
    warnings: list[str] = []
    for provider_id, model_id, label in [
        (request.baseline_provider_id, request.baseline_model_id, "baseline"),
        (request.candidate_provider_id, request.candidate_model_id, "candidate"),
    ]:
        decision = policy.evaluate_benchmark_run(
            BenchmarkRun(
                id=f"{request.run_id}:{label}",
                provider_profile=ProviderProfile(
                    provider_id=provider_id,
                    provider_type=_provider_type(provider_id, settings),  # type: ignore[arg-type]
                    model_id=model_id or provider_id,
                    api_key_configured=bool(settings.llm_api_key),
                    uses_real_external_api=_provider_type(provider_id, settings) == "openai",
                ),
                explicit_real_provider_opt_in=request.allow_real_provider,
                uses_provider_factory=True,
            )
        )
        blockers.extend(decision.blockers)
        warnings.extend(decision.warnings)
    return sorted(set(blockers)), sorted(set(warnings))


def _provider_type(provider_id: str, settings: Settings) -> str:
    if provider_id in {
        "fake_leaky",
        "fake_hidden_leak",
        "fake_unknown_fact",
        "fake_invalid_json",
        "fake_schema_violation",
        "fake_retry",
        "fake_empty",
        "fake_slow",
    }:
        return "fake"
    if provider_id == "openai_compatible":
        return "local_http"
    if provider_id in {"mock", "fake", "local_stub", "local_http", "openai"}:
        return provider_id
    return settings.llm_provider


def _effective_provider(provider_id: str) -> str:
    if provider_id == "fake_slow":
        return "fake"
    return provider_id


def _with_latency_adjustment(latency_ms: float, provider_id: str) -> float:
    if provider_id == "fake_slow":
        return round(latency_ms + 2500.0, 3)
    return latency_ms


def _schema_rate(metrics: PromptRegressionVariantMetrics) -> float:
    return metrics.schema_valid_rate if metrics.schema_valid_rate is not None else (1.0 if metrics.ok else 0.0)


def _default_cases() -> list[PromptRegressionCase]:
    return [
        PromptRegressionCase(id="intent_parser_schema", case_type=PromptRegressionCaseType.INTENT_PARSER_SCHEMA),
        PromptRegressionCase(id="narrator_consistency", case_type=PromptRegressionCaseType.NARRATOR_CONSISTENCY),
        PromptRegressionCase(id="rp_dialogue_boundary", case_type=PromptRegressionCaseType.RP_DIALOGUE_BOUNDARY),
        PromptRegressionCase(id="npc_voice_consistency", case_type=PromptRegressionCaseType.NPC_VOICE_CONSISTENCY),
        PromptRegressionCase(id="memory_summary_schema", case_type=PromptRegressionCaseType.MEMORY_SUMMARY_SCHEMA),
        PromptRegressionCase(id="hidden_leak", case_type=PromptRegressionCaseType.HIDDEN_LEAK),
        PromptRegressionCase(id="structured_json", case_type=PromptRegressionCaseType.STRUCTURED_JSON_RELIABILITY),
    ]


def _blocked_report(request: PromptRegressionRun, blockers: list[str], warnings: list[str]) -> PromptRegressionReport:
    return PromptRegressionReport(
        run_id=request.run_id,
        baseline_profile_id=request.baseline_profile_id,
        candidate_profile_id=request.candidate_profile_id,
        baseline_provider_id=request.baseline_provider_id,
        baseline_model_id=request.baseline_model_id,
        candidate_provider_id=request.candidate_provider_id,
        candidate_model_id=request.candidate_model_id,
        pass_fail="fail",
        blockers=blockers,
        warnings=warnings,
    )


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
        if "hidden fact" in lowered or "the mayor forged the charter" in lowered or "unknown forbidden fact" in lowered:
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    forbidden = ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-"]
    return not any(term in lowered for term in forbidden)
