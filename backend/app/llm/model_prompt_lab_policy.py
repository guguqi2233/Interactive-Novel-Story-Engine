from __future__ import annotations

import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.llm.prompt_profiles import PromptProfile


class PromptLabPrivacyClass(StrEnum):
    NORMAL = "normal"
    DEBUG = "debug"
    HIDDEN = "hidden"


class PromptLabOperation(StrEnum):
    COMPARE_MODEL_OUTPUT = "compare_model_output"
    STRUCTURED_OUTPUT_RELIABILITY = "structured_output_reliability"
    COST_LATENCY_TRACKING = "cost_latency_tracking"
    PROMPT_PROFILE_COMPARE = "prompt_profile_compare"
    CONTEXT_INSPECTION = "context_inspection"
    COMPATIBILITY_MATRIX = "compatibility_matrix"
    BENCHMARK_RUN = "benchmark_run"
    PROMPT_EXPERIMENT = "prompt_experiment"


class PromptLabDecision(BaseModel):
    allowed: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProviderProfile(BaseModel):
    provider_id: str = "local_stub"
    provider_type: Literal["mock", "fake", "local_stub", "local_http", "openai"] = "local_stub"
    model_id: str = "local_stub"
    uses_real_external_api: bool = False
    api_key_configured: bool = False
    base_url: str | None = None
    supports_json_mode: bool = True
    supports_streaming: bool = False

    @model_validator(mode="after")
    def _derive_real_provider_flag(self) -> ProviderProfile:
        if self.provider_type == "openai":
            self.uses_real_external_api = True
        return self

    def frontend_summary(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "model_id": self.model_id,
            "uses_real_external_api": self.uses_real_external_api,
            "api_key_configured": self.api_key_configured,
            "base_url": "[redacted]" if self.base_url else None,
            "supports_json_mode": self.supports_json_mode,
            "supports_streaming": self.supports_streaming,
        }


class ModelCapability(BaseModel):
    provider_id: str
    model_id: str
    supports_json_mode: bool = True
    supports_schema_validation: bool = True
    context_window_tokens: int | None = None
    notes: str = ""


class RedactedPrompt(BaseModel):
    text: str
    redaction_count: int = 0
    contains_sensitive_material: bool = False


class DebugOnlyPromptData(BaseModel):
    label: str
    safe_summary: str
    privacy_class: PromptLabPrivacyClass = PromptLabPrivacyClass.DEBUG


class ContextSegment(BaseModel):
    label: str
    content: str
    privacy_class: PromptLabPrivacyClass = PromptLabPrivacyClass.NORMAL
    safe_summary: str = ""

    def normal_view(self) -> dict[str, str]:
        if self.privacy_class == PromptLabPrivacyClass.NORMAL:
            redacted = redact_sensitive_text(self.content)
            return {
                "label": self.label,
                "privacy_class": self.privacy_class.value,
                "content": redacted.text,
            }
        return {
            "label": self.label,
            "privacy_class": self.privacy_class.value,
            "content": self.safe_summary or f"[redacted:{self.privacy_class.value}]",
        }


class ContextSnapshot(BaseModel):
    id: str
    segments: list[ContextSegment] = Field(default_factory=list)
    default_view: PromptLabPrivacyClass = PromptLabPrivacyClass.NORMAL

    def normal_view(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "default_view": self.default_view.value,
            "segments": [segment.normal_view() for segment in self.segments],
        }


class PromptExperiment(BaseModel):
    id: str
    name: str
    prompt_profile_ids: list[str] = Field(default_factory=list)
    operation: PromptLabOperation = PromptLabOperation.PROMPT_EXPERIMENT
    writes_game_state: bool = False
    stores_full_prompt: bool = False


class BenchmarkRun(BaseModel):
    id: str
    operation: PromptLabOperation = PromptLabOperation.BENCHMARK_RUN
    provider_profile: ProviderProfile = Field(default_factory=ProviderProfile)
    explicit_real_provider_opt_in: bool = False
    uses_provider_factory: bool = True
    writes_game_state: bool = False
    records_api_key: bool = False
    records_full_sensitive_prompt: bool = False
    debug_context_in_normal_ui: bool = False


class SafeEvalCase(BaseModel):
    id: str
    name: str
    input_summary: str
    visible_fact_ids: list[str] = Field(default_factory=list)
    prompt_profile_id: str = "default_safe"
    contains_hidden_text: bool = False
    contains_api_key: bool = False


class ModelPromptLabPolicy:
    """Read-only safety policy for v1.5 Model & Prompt Lab.

    The policy validates lab runs and prompt/profile metadata. It never calls a
    provider and never mutates GameState.
    """

    allowed_operations = {
        PromptLabOperation.COMPARE_MODEL_OUTPUT,
        PromptLabOperation.STRUCTURED_OUTPUT_RELIABILITY,
        PromptLabOperation.COST_LATENCY_TRACKING,
        PromptLabOperation.PROMPT_PROFILE_COMPARE,
        PromptLabOperation.CONTEXT_INSPECTION,
        PromptLabOperation.COMPATIBILITY_MATRIX,
        PromptLabOperation.BENCHMARK_RUN,
        PromptLabOperation.PROMPT_EXPERIMENT,
    }

    def validate_prompt_profile(self, profile_data: PromptProfile | dict[str, Any]) -> PromptProfile:
        profile = profile_data if isinstance(profile_data, PromptProfile) else PromptProfile.model_validate(profile_data)
        if profile.rp_profile.hidden_fact_policy != "deny":
            raise ValueError("Prompt Lab prompt_profile cannot enable hidden facts")
        if profile.rp_profile.state_modification_policy != "deny":
            raise ValueError("Prompt Lab prompt_profile cannot enable state modification")
        profile.validate_security_boundary()
        return profile

    def build_context_snapshot(self, snapshot_id: str, segments: list[ContextSegment]) -> ContextSnapshot:
        return ContextSnapshot(id=snapshot_id, segments=segments)

    def redact_prompt(self, text: str) -> RedactedPrompt:
        return redact_sensitive_text(text)

    def evaluate_benchmark_run(self, run: BenchmarkRun) -> PromptLabDecision:
        blockers: list[str] = []
        warnings: list[str] = []
        if run.operation not in self.allowed_operations:
            blockers.append(f"operation_not_allowed:{run.operation}")
        if run.writes_game_state:
            blockers.append("benchmark_must_not_write_game_state")
        if not run.uses_provider_factory:
            blockers.append("provider_must_use_factory_or_router")
        if run.records_api_key:
            blockers.append("benchmark_must_not_record_api_key")
        if run.records_full_sensitive_prompt:
            blockers.append("benchmark_must_not_record_full_sensitive_prompt")
        if run.debug_context_in_normal_ui:
            blockers.append("debug_context_must_not_enter_normal_ui")
        if run.provider_profile.uses_real_external_api and not run.explicit_real_provider_opt_in:
            blockers.append("real_external_provider_requires_explicit_opt_in")
        if run.provider_profile.uses_real_external_api:
            warnings.append("real_external_provider")
        return PromptLabDecision(allowed=not blockers, blockers=blockers, warnings=warnings)

    def frontend_provider_summary(self, provider_profile: ProviderProfile) -> dict[str, Any]:
        return provider_profile.frontend_summary()

    def validate_safe_eval_case(self, eval_case: SafeEvalCase) -> PromptLabDecision:
        blockers: list[str] = []
        if eval_case.contains_hidden_text:
            blockers.append("safe_eval_case_must_not_contain_hidden_text")
        if eval_case.contains_api_key:
            blockers.append("safe_eval_case_must_not_contain_api_key")
        return PromptLabDecision(allowed=not blockers, blockers=blockers)


_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(LLM_API_KEY|OPENAI_API_KEY|API_KEY)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


def redact_sensitive_text(text: str) -> RedactedPrompt:
    redacted = text
    count = 0
    for pattern in _SENSITIVE_PATTERNS:
        redacted, replacements = pattern.subn("[redacted-secret]", redacted)
        count += replacements
    return RedactedPrompt(
        text=redacted,
        redaction_count=count,
        contains_sensitive_material=count > 0,
    )
