from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from app.config import Settings
from app.engine.content.batch_lorebook_classification import BatchLorebookClassificationReport
from app.engine.content.side_quest_generator import QuestDraft, QuestDraftStage
from app.llm.model_prompt_lab_policy import BenchmarkRun, ModelPromptLabPolicy, ProviderProfile, redact_sensitive_text
from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.provider_profiles import ProviderCapabilityReport
from app.llm.provider_factory import create_llm_provider
from app.llm.schemas import MemorySummary, NarrativeResult, PlayerActionType, PlayerIntent
from app.platform.cross_mode import CrossModeDraft
from app.platform.novel_studio import GeneratedNovelDraft
from app.platform.tavern_studio import GeneratedTavernReply
from app.roleplay.character_cards import (
    CharacterCardImportReport,
    CharacterCardInputFormat,
    NormalizedCharacterCard,
    RPProfileCandidate,
    VoiceProfileCandidate,
    ExampleDialogueCandidate,
)
from app.roleplay.lorebooks import LorebookInputFormat
from app.roleplay.output_consistency import RPConsistencyDecision, RPConsistencyReport


class StructuredOutputSchemaName(StrEnum):
    PLAYER_INTENT = "PlayerIntent"
    NARRATIVE_RESULT = "NarrativeResult"
    MEMORY_SUMMARY = "MemorySummary"
    QUEST_DRAFT = "QuestDraft"
    CHARACTER_CARD_IMPORT_RESULT = "CharacterCardImportResult"
    LOREBOOK_CLASSIFICATION_RESULT = "LorebookClassificationResult"
    RP_CONSISTENCY_REPORT = "RPConsistencyReport"
    GENERATED_NOVEL_DRAFT = "GeneratedNovelDraft"
    GENERATED_TAVERN_REPLY = "GeneratedTavernReply"
    CROSS_MODE_DRAFT = "CrossModeDraft"
    PROVIDER_CAPABILITY_REPORT = "ProviderCapabilityReport"


STRUCTURED_OUTPUT_SCHEMA_NAMES = [item.value for item in StructuredOutputSchemaName]


class StructuredOutputTestCase(BaseModel):
    id: str
    schema_name: StructuredOutputSchemaName
    messages: list[dict[str, str]] = Field(default_factory=list)
    hidden_terms: list[str] = Field(default_factory=list)
    retry_once: bool = True
    temperature: float = 0.0
    max_prompt_preview_chars: int = Field(default=160, ge=20, le=500)

    def redacted_prompt_preview(self) -> str:
        joined = "\n".join(f"{message.get('role', 'user')}: {message.get('content', '')}" for message in self.messages)
        redacted = redact_sensitive_text(joined).text
        for term in self.hidden_terms:
            if term:
                redacted = redacted.replace(term, "[redacted-hidden]")
        return redacted[: self.max_prompt_preview_chars]


class StructuredOutputReliabilityRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"structured-output-{uuid4().hex}")
    provider_id: str = "fake"
    model_id: str | None = None
    allow_real_provider: bool = False
    cases: list[StructuredOutputTestCase] = Field(default_factory=list)


class StructuredOutputCaseResult(BaseModel):
    case_id: str
    schema_name: StructuredOutputSchemaName
    ok: bool
    valid_json: bool
    schema_valid: bool
    retried: bool = False
    retry_succeeded: bool = False
    invalid_field: bool = False
    refusal_or_empty: bool = False
    hidden_policy_violation: bool = False
    duration_ms: float = 0.0
    prompt_preview_redacted: str = ""
    output_summary_safe: str = ""
    error_class: str | None = None
    error_message_safe: str | None = None
    provider_profile_id: str | None = None
    success: bool | None = None
    validation_errors: list[str] = Field(default_factory=list)
    retry_count: int = 0
    fallback_used: bool = False


class StructuredOutputReliabilityReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str
    model_id: str | None = None
    allow_real_provider: bool = False
    real_provider_blocked: bool = False
    total_cases: int = 0
    valid_json_rate: float = 0.0
    schema_valid_rate: float = 0.0
    retry_success_rate: float = 0.0
    invalid_field_rate: float = 0.0
    refusal_or_empty_rate: float = 0.0
    hidden_policy_violation_rate: float = 0.0
    cases: list[StructuredOutputCaseResult] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_structured_output_reliability(
    request: StructuredOutputReliabilityRun,
    *,
    settings: Settings | None = None,
) -> StructuredOutputReliabilityReport:
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
        return StructuredOutputReliabilityReport(
            run_id=request.run_id,
            provider_id=request.provider_id,
            model_id=request.model_id,
            allow_real_provider=request.allow_real_provider,
            real_provider_blocked="real_external_provider_requires_explicit_opt_in" in decision.blockers,
            blockers=decision.blockers,
            warnings=decision.warnings,
        )
    provider = _create_provider(request, active_settings)
    cases = request.cases or _default_cases()
    results = [_run_case(provider, case) for case in cases]
    return _build_report(request, results, decision.warnings)


def _run_case(provider: LLMProvider, case: StructuredOutputTestCase) -> StructuredOutputCaseResult:
    started = perf_counter()
    retried = False
    retry_succeeded = False
    try:
        output = _execute_case(provider, case)
        result = _result_from_output(case, output, perf_counter() - started)
    except Exception as exc:
        if case.retry_once:
            retried = True
            try:
                output = _execute_case(provider, case)
                retry_succeeded = True
                result = _result_from_output(case, output, perf_counter() - started)
            except Exception as retry_exc:
                result = _result_from_exception(case, retry_exc, perf_counter() - started)
        else:
            result = _result_from_exception(case, exc, perf_counter() - started)
    result.retried = retried
    result.retry_succeeded = retry_succeeded and result.ok
    result.retry_count = 1 if retried else 0
    result.success = result.ok
    return result


def _execute_case(provider: LLMProvider, case: StructuredOutputTestCase) -> BaseModel:
    messages = case.messages or [{"role": "user", "content": f"Return {case.schema_name.value} JSON."}]
    return provider.generate_json(messages, _schema_for_case(case.schema_name), temperature=case.temperature)


def _result_from_output(case: StructuredOutputTestCase, output: BaseModel, elapsed_seconds: float) -> StructuredOutputCaseResult:
    output_text = output.model_dump_json() if isinstance(output, BaseModel) else str(output)
    hidden_violation = _contains_hidden_term(output_text, case.hidden_terms)
    return StructuredOutputCaseResult(
        case_id=case.id,
        schema_name=case.schema_name,
        ok=not hidden_violation,
        valid_json=True,
        schema_valid=True,
        hidden_policy_violation=hidden_violation,
        duration_ms=round(elapsed_seconds * 1000, 3),
        prompt_preview_redacted=case.redacted_prompt_preview(),
        output_summary_safe=_safe_output_summary(output),
    )


def _result_from_exception(case: StructuredOutputTestCase, exc: Exception, elapsed_seconds: float) -> StructuredOutputCaseResult:
    message = str(exc)
    lowered = message.lower()
    invalid_json = "invalid_json" in lowered or "json" in lowered and "invalid" in lowered
    refusal = "refusal" in lowered or "empty" in lowered
    schema_violation = isinstance(exc, ValidationError) or "schema" in lowered or "validation" in lowered
    invalid_field = schema_violation and not invalid_json
    hidden_violation = "hidden_policy_violation" in lowered
    return StructuredOutputCaseResult(
        case_id=case.id,
        schema_name=case.schema_name,
        ok=False,
        valid_json=not invalid_json,
        schema_valid=False,
        invalid_field=invalid_field,
        refusal_or_empty=refusal,
        hidden_policy_violation=hidden_violation,
        duration_ms=round(elapsed_seconds * 1000, 3),
        prompt_preview_redacted=case.redacted_prompt_preview(),
        error_class=type(exc).__name__,
        error_message_safe=_safe_error_message(message),
        validation_errors=[_safe_error_message(message)] if schema_violation or invalid_json else [],
    )


def _build_report(
    request: StructuredOutputReliabilityRun,
    results: list[StructuredOutputCaseResult],
    warnings: list[str],
) -> StructuredOutputReliabilityReport:
    total = len(results)
    retried = [result for result in results if result.retried]
    return StructuredOutputReliabilityReport(
        run_id=request.run_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        allow_real_provider=request.allow_real_provider,
        total_cases=total,
        valid_json_rate=_rate(results, lambda result: result.valid_json),
        schema_valid_rate=_rate(results, lambda result: result.schema_valid),
        retry_success_rate=round(sum(1 for result in retried if result.retry_succeeded) / len(retried), 4) if retried else 0.0,
        invalid_field_rate=_rate(results, lambda result: result.invalid_field),
        refusal_or_empty_rate=_rate(results, lambda result: result.refusal_or_empty),
        hidden_policy_violation_rate=_rate(results, lambda result: result.hidden_policy_violation),
        cases=results,
        warnings=warnings,
    )


def _rate(results: list[StructuredOutputCaseResult], predicate: Any) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if predicate(result)) / len(results), 4)


def _provider_profile_from_request(request: StructuredOutputReliabilityRun, settings: Settings) -> ProviderProfile:
    provider_id = request.provider_id.strip().lower()
    provider_type = "fake" if provider_id.startswith("fake") else provider_id
    if provider_type == "openai_compatible":
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


def _create_provider(request: StructuredOutputReliabilityRun, settings: Settings) -> LLMProvider:
    provider_id = request.provider_id.strip().lower()
    if provider_id.startswith("fake"):
        return _StructuredOutputFakeProvider(provider_id)
    factory_provider = "local_http" if provider_id == "openai_compatible" else provider_id
    return create_llm_provider(settings.model_copy(update={"llm_provider": factory_provider, "llm_model": request.model_id or settings.llm_model}))


class _StructuredOutputFakeProvider(LLMProvider):
    def __init__(self, mode: str) -> None:
        self._mode = mode
        self._attempts: dict[str, int] = defaultdict(int)

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        return "structured output reliability fake provider"

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        _ = messages, temperature
        key = schema.__name__
        self._attempts[key] += 1
        if self._mode == "fake_invalid_json":
            raise LLMProviderError("invalid_json: provider returned malformed JSON")
        if self._mode == "fake_schema_violation":
            raise LLMProviderError("schema validation failed: invalid field type")
        if self._mode == "fake_retry" and self._attempts[key] == 1:
            raise LLMProviderError("invalid_json: first attempt malformed JSON")
        if self._mode == "fake_hidden_violation":
            raise LLMProviderError("hidden_policy_violation: output mentioned hidden text")
        if self._mode == "fake_empty":
            raise LLMProviderError("empty provider response")
        return _sample_for_schema(schema)


def _schema_for_case(schema_name: StructuredOutputSchemaName) -> type[BaseModel]:
    mapping: dict[StructuredOutputSchemaName, type[BaseModel]] = {
        StructuredOutputSchemaName.PLAYER_INTENT: PlayerIntent,
        StructuredOutputSchemaName.NARRATIVE_RESULT: NarrativeResult,
        StructuredOutputSchemaName.MEMORY_SUMMARY: MemorySummary,
        StructuredOutputSchemaName.QUEST_DRAFT: QuestDraft,
        StructuredOutputSchemaName.CHARACTER_CARD_IMPORT_RESULT: CharacterCardImportReport,
        StructuredOutputSchemaName.LOREBOOK_CLASSIFICATION_RESULT: BatchLorebookClassificationReport,
        StructuredOutputSchemaName.RP_CONSISTENCY_REPORT: RPConsistencyReport,
        StructuredOutputSchemaName.GENERATED_NOVEL_DRAFT: GeneratedNovelDraft,
        StructuredOutputSchemaName.GENERATED_TAVERN_REPLY: GeneratedTavernReply,
        StructuredOutputSchemaName.CROSS_MODE_DRAFT: CrossModeDraft,
        StructuredOutputSchemaName.PROVIDER_CAPABILITY_REPORT: ProviderCapabilityReport,
    }
    return mapping[schema_name]


def _sample_for_schema(schema: type[Any]) -> BaseModel:
    if schema is PlayerIntent:
        return PlayerIntent(action_type=PlayerActionType.SEARCH, raw_text="search the square", confidence=0.9, requires_clarification=False)
    if schema is NarrativeResult:
        return NarrativeResult(text="The square is quiet.", suggested_actions=["observe"], short_summary="Safe narration.")
    if schema is MemorySummary:
        return MemorySummary(summary="Safe memory summary.", important_facts=["visible_square"])
    if schema is QuestDraft:
        return QuestDraft(title="Safe Errand", premise="A local visible errand.", stages=[QuestDraftStage(id="start", title="Start")])
    if schema is CharacterCardImportReport:
        return CharacterCardImportReport(
            ok=True,
            source_format=CharacterCardInputFormat.JSON,
            normalized_card=NormalizedCharacterCard(name="Mira"),
            rp_profile_candidate=RPProfileCandidate(name="Mira"),
            voice_profile_candidate=VoiceProfileCandidate(name="Mira"),
            example_dialogue_candidate=ExampleDialogueCandidate(lines=[]),
        )
    if schema is BatchLorebookClassificationReport:
        return BatchLorebookClassificationReport(target_world_id="test_world", total_entries=0)
    if schema is RPConsistencyReport:
        return RPConsistencyReport(ok=True, decision=RPConsistencyDecision.ACCEPT)
    if schema is GeneratedNovelDraft:
        return GeneratedNovelDraft(text="Safe generated novel draft.", summary="safe")
    if schema is GeneratedTavernReply:
        return GeneratedTavernReply(content="Safe Tavern reply.", speaker_id="mira")
    if schema is CrossModeDraft:
        return CrossModeDraft(artifact_id="structured_output_draft", project_id="demo", direction="novel_to_world", artifact_type="fact_draft")
    if schema is ProviderCapabilityReport:
        return ProviderCapabilityReport(provider_profile_id="fake", model_id="fake")
    raise LLMProviderError(f"Unsupported structured output schema: {schema.__name__}")


def _default_cases() -> list[StructuredOutputTestCase]:
    return [
        StructuredOutputTestCase(id=f"default_{schema_name.value}", schema_name=schema_name)
        for schema_name in StructuredOutputSchemaName
    ]


def _contains_hidden_term(text: str, hidden_terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in hidden_terms if term)


def _safe_output_summary(output: object) -> str:
    if isinstance(output, BaseModel):
        return f"{output.__class__.__name__}:schema_valid"
    return redact_sensitive_text(str(output)).text[:120]


def _safe_error_message(message: str) -> str:
    redacted = redact_sensitive_text(message).text
    lowered = redacted.lower()
    if "hidden fact" in lowered or "the mayor forged the charter" in lowered or "sk-" in lowered or "api_key" in lowered:
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
    return not any(term in lowered for term in ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-"])
