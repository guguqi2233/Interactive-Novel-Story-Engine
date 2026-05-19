from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.llm.model_prompt_lab_policy import redact_sensitive_text
from app.llm.provider_benchmark import ProviderBenchmarkReport
from app.llm.provider_capabilities import ModelCapability, ProviderCapabilityRegistry
from app.llm.structured_output_reliability import StructuredOutputReliabilityReport
from app.llm.usage_tracker import ModelUsageRecord


class ModelCompatibilityUseCase(StrEnum):
    INTENT_PARSER = "intent_parser"
    NARRATOR = "narrator"
    RP_DIALOGUE = "RP_dialogue"
    MEMORY_SUMMARY = "memory_summary"
    CHARACTER_IMPORT = "character_import"
    LOREBOOK_CLASSIFICATION = "lorebook_classification"
    QUEST_DRAFT = "quest_draft"
    STRUCTURED_JSON = "structured_json"
    EMBEDDING = "embedding"


MODEL_COMPATIBILITY_USE_CASES = [item.value for item in ModelCompatibilityUseCase]


class ModelUseCaseCompatibility(BaseModel):
    provider_id: str
    model_id: str
    use_case: ModelCompatibilityUseCase
    supported: bool
    recommended: bool
    caution: bool
    unsupported: bool
    reason: str
    last_tested_at: datetime | None = None


class ModelCompatibilityMatrix(BaseModel):
    matrix_id: str = Field(default_factory=lambda: f"model-compatibility-{uuid4().hex}")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    use_cases: list[ModelCompatibilityUseCase] = Field(
        default_factory=lambda: list(ModelCompatibilityUseCase)
    )
    rows: list[ModelUseCaseCompatibility] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_summary: dict[str, Any] = Field(default_factory=dict)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def build_model_compatibility_matrix(
    *,
    registry: ProviderCapabilityRegistry | None = None,
    benchmark_reports: list[ProviderBenchmarkReport] | None = None,
    structured_reports: list[StructuredOutputReliabilityReport] | None = None,
    usage_records: list[ModelUsageRecord] | None = None,
) -> ModelCompatibilityMatrix:
    active_registry = registry or ProviderCapabilityRegistry()
    benchmark_index = _latest_benchmark_index(benchmark_reports or [])
    structured_index = _latest_structured_index(structured_reports or [])
    usage_index = _usage_latency_index(usage_records or [])
    rows: list[ModelUseCaseCompatibility] = []
    for model in active_registry.list_models():
        for use_case in ModelCompatibilityUseCase:
            rows.append(
                _evaluate_model_use_case(
                    model,
                    use_case,
                    benchmark_index.get((model.provider_id, model.model_id)),
                    structured_index.get((model.provider_id, model.model_id)),
                    usage_index.get((model.provider_id, model.model_id)),
                )
            )
    return ModelCompatibilityMatrix(
        rows=rows,
        source_summary={
            "declared_model_count": len(active_registry.list_models()),
            "benchmark_report_count": len(benchmark_reports or []),
            "structured_report_count": len(structured_reports or []),
            "usage_record_count": len(usage_records or []),
            "real_provider_calls_performed": False,
        },
        warnings=["compatibility_matrix_is_advisory"],
    )


def _evaluate_model_use_case(
    model: ModelCapability,
    use_case: ModelCompatibilityUseCase,
    benchmark: ProviderBenchmarkReport | None,
    structured: StructuredOutputReliabilityReport | None,
    average_latency_ms: float | None,
) -> ModelUseCaseCompatibility:
    blockers: list[str] = []
    cautions: list[str] = []
    capability_key = _capability_use_case(use_case)
    if use_case == ModelCompatibilityUseCase.EMBEDDING:
        if not model.supports_embeddings:
            blockers.append("model_does_not_support_embeddings")
    elif use_case in {
        ModelCompatibilityUseCase.INTENT_PARSER,
        ModelCompatibilityUseCase.MEMORY_SUMMARY,
        ModelCompatibilityUseCase.CHARACTER_IMPORT,
        ModelCompatibilityUseCase.LOREBOOK_CLASSIFICATION,
        ModelCompatibilityUseCase.QUEST_DRAFT,
        ModelCompatibilityUseCase.STRUCTURED_JSON,
    }:
        if not model.supports_json:
            blockers.append("model_does_not_support_json")
    elif not model.supports_text:
        blockers.append("model_does_not_support_text")

    declared_recommended = capability_key in model.recommended_use_cases
    if not declared_recommended and not blockers:
        cautions.append("use_case_not_declared_recommended")

    if structured is not None:
        if structured.schema_valid_rate < 0.5:
            blockers.append("structured_output_reliability_too_low")
        elif structured.schema_valid_rate < 0.8:
            cautions.append("structured_output_reliability_low")
        if structured.hidden_policy_violation_rate > 0:
            cautions.append("hidden_policy_violation_reported")

    latency_ms = average_latency_ms
    if latency_ms is None and benchmark is not None and benchmark.average_latency_ms:
        latency_ms = benchmark.average_latency_ms
    if latency_ms is not None and latency_ms > 2000:
        cautions.append("latency_high")

    if benchmark is not None:
        if benchmark.error_rate >= 0.5:
            cautions.append("benchmark_error_rate_high")
        if benchmark.hidden_leak_risk_count > 0:
            cautions.append("hidden_leak_risk_reported")

    supported = not blockers
    recommended = supported and declared_recommended and not cautions
    caution = supported and bool(cautions)
    unsupported = not supported
    reason_parts = blockers or cautions or ["declared_capability_match"]
    return ModelUseCaseCompatibility(
        provider_id=model.provider_id,
        model_id=model.model_id,
        use_case=use_case,
        supported=supported,
        recommended=recommended,
        caution=caution,
        unsupported=unsupported,
        reason=", ".join(reason_parts),
        last_tested_at=_latest_time(benchmark, structured),
    )


def _capability_use_case(use_case: ModelCompatibilityUseCase) -> str:
    if use_case in {
        ModelCompatibilityUseCase.INTENT_PARSER,
        ModelCompatibilityUseCase.MEMORY_SUMMARY,
        ModelCompatibilityUseCase.CHARACTER_IMPORT,
        ModelCompatibilityUseCase.LOREBOOK_CLASSIFICATION,
        ModelCompatibilityUseCase.QUEST_DRAFT,
        ModelCompatibilityUseCase.STRUCTURED_JSON,
    }:
        return "structured_output"
    if use_case == ModelCompatibilityUseCase.NARRATOR:
        return "narration"
    if use_case == ModelCompatibilityUseCase.RP_DIALOGUE:
        return "rp_expression"
    if use_case == ModelCompatibilityUseCase.EMBEDDING:
        return "embeddings"
    return use_case.value


def _latest_benchmark_index(
    reports: list[ProviderBenchmarkReport],
) -> dict[tuple[str, str], ProviderBenchmarkReport]:
    index: dict[tuple[str, str], ProviderBenchmarkReport] = {}
    for report in sorted(reports, key=lambda item: item.created_at):
        model_id = report.model_id or report.provider_id
        index[(report.provider_id, model_id)] = report
    return index


def _latest_structured_index(
    reports: list[StructuredOutputReliabilityReport],
) -> dict[tuple[str, str], StructuredOutputReliabilityReport]:
    index: dict[tuple[str, str], StructuredOutputReliabilityReport] = {}
    for report in sorted(reports, key=lambda item: item.created_at):
        model_id = report.model_id or report.provider_id
        index[(report.provider_id, model_id)] = report
    return index


def _usage_latency_index(records: list[ModelUsageRecord]) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for record in records:
        grouped.setdefault((record.provider_id, record.model_id), []).append(record.duration_ms)
    return {
        key: round(sum(values) / len(values), 3)
        for key, values in grouped.items()
        if values
    }


def _latest_time(
    benchmark: ProviderBenchmarkReport | None,
    structured: StructuredOutputReliabilityReport | None,
) -> datetime | None:
    values = [item.created_at for item in (benchmark, structured) if item is not None]
    return max(values) if values else None


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
    forbidden = ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-", "hidden_prompt"]
    return not any(term in lowered for term in forbidden)
