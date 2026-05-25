from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from time import perf_counter, sleep
from typing import Any, Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.platform.narrative_project import validate_project_relative_path
from app.platform.security import contains_secret_text, redact_text, safe_identifier


SAFE_SECRET_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*(?:/[A-Za-z0-9][A-Za-z0-9_.:-]*){0,7}")
LOCAL_SECRET_DIR_ENV = "AI_NARRATIVE_STUDIO_LOCAL_SECRET_DIR"
UNSAFE_SECRET_REF_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"(?i)authorization\s*[:=]?\s*bearer"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|relay[_-]?token|password)\s*[:=]"),
    re.compile(r"(?i)BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    re.compile(r"[?&](?:api[_-]?key|token|secret|signature|sig|auth)=", re.IGNORECASE),
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ProviderProfileType(StrEnum):
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    LOCAL_HTTP = "local_http"
    RELAY = "relay"
    CUSTOM = "custom"
    MOCK = "mock"
    LOCAL_STUB = "local_stub"


class ProviderMode(StrEnum):
    NOVEL = "novel"
    TAVERN = "tavern"
    WORLD = "world"
    CROSS_MODE = "cross_mode"
    QUALITY = "quality"
    AUTHORING = "authoring"


class ProviderRetryPolicy(BaseModel):
    max_attempts: int = Field(default=1, ge=1, le=5)
    backoff_seconds: float = Field(default=0.0, ge=0, le=10)


class ProviderCostHint(BaseModel):
    input_per_1k: float | None = Field(default=None, ge=0)
    output_per_1k: float | None = Field(default=None, ge=0)
    currency: str = "USD"


class ProviderSafetyPolicy(BaseModel):
    allowed_modes: list[ProviderMode] = Field(default_factory=list)
    disallowed_modes: list[ProviderMode] = Field(default_factory=list)
    allow_sensitive_prompts: bool = False
    allow_mature_content: bool = False
    allowed_content_ratings: list[str] = Field(default_factory=lambda: ["safe"])
    allow_explicit_adult: bool = False
    require_local_only_for_mature: bool = False
    allow_debug_prompts: bool = False
    log_prompts: bool = False
    log_outputs: bool = False
    redact_secrets: bool = True
    require_local_only: bool = False

    @model_validator(mode="after")
    def validate_safe_logging(self) -> "ProviderSafetyPolicy":
        if not self.redact_secrets and (self.log_prompts or self.log_outputs):
            raise ValueError("Provider safety policy cannot log prompts/outputs without redaction")
        if self.allow_explicit_adult and not self.allow_mature_content:
            raise ValueError("Explicit adult content requires allow_mature_content=True")
        return self


class ModelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    display_name: str = ""
    provider_profile_id: str | None = None
    context_window: int | None = Field(default=None, gt=0)
    supports_text: bool = True
    supports_json: bool = True
    supports_tools: bool = False
    supports_streaming: bool = False
    supports_embeddings: bool = False
    supports_long_context: bool = False
    max_output_tokens: int | None = Field(default=None, gt=0)
    recommended_use_cases: list[str] = Field(default_factory=list)
    structured_output_reliability_hint: str | None = None
    cost_hint: ProviderCostHint | None = None
    enabled: bool = True
    last_seen_at: str | None = None

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ProviderProfileV2(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    provider_profile_id: str
    display_name: str
    provider_type: ProviderProfileType
    base_url: str | None = None
    base_url_env: str | None = None
    api_key_env: str | None = None
    secret_ref: str | None = None
    local_secret_ref: str | None = None
    model_profiles: list[ModelProfile] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    allowed_modes: list[ProviderMode] = Field(default_factory=list)
    default_timeout_seconds: float = Field(default=30.0, gt=0, le=600)
    retry_policy: ProviderRetryPolicy = Field(default_factory=ProviderRetryPolicy)
    fallback_profile_ids: list[str] = Field(default_factory=list)
    cost_tracking: bool = False
    safety_policy: ProviderSafetyPolicy = Field(default_factory=ProviderSafetyPolicy)
    model_mapping: dict[str, str] = Field(default_factory=dict)
    provider_notes: str = ""
    enabled: bool = True
    requires_api_key: bool | None = None

    @field_validator("provider_profile_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe provider profile id")
        return value

    @field_validator("api_key_env", "base_url_env")
    @classmethod
    def validate_env_ref(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "sk-" in value.lower() or "private key" in value.lower():
            raise ValueError("Provider env refs must not contain secret values")
        if not value.isupper() or not all(ch.isalnum() or ch == "_" for ch in value):
            raise ValueError("Provider env refs must be environment variable names")
        return value

    @field_validator("secret_ref", "local_secret_ref")
    @classmethod
    def validate_secret_ref(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if stripped != value or not stripped:
            raise ValueError("Provider secret_ref must be a non-empty safe reference")
        if not SAFE_SECRET_REF_PATTERN.fullmatch(stripped):
            raise ValueError("Provider secret_ref must be a safe local reference, not a secret value")
        if any(pattern.search(stripped) for pattern in UNSAFE_SECRET_REF_PATTERNS):
            raise ValueError("Provider secret_ref must not contain secret-like values")
        return stripped

    @model_validator(mode="before")
    @classmethod
    def reject_raw_key(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                lowered = str(key).lower()
                if lowered in {"api_key", "llm_api_key", "openai_api_key"}:
                    raise ValueError("ProviderProfileV2 must not contain raw API keys")
                if lowered in {"api_key_env", "secret_ref", "local_secret_ref"}:
                    continue
                if isinstance(value, str) and contains_secret_text(value):
                    raise ValueError("ProviderProfileV2 must not contain secrets")
        return data

    def key_required(self) -> bool:
        if self.requires_api_key is not None:
            return self.requires_api_key
        return str(self.provider_type) in {"openai", "openai_compatible", "relay", "custom"}

    def primary_model_id(self) -> str:
        if self.model_profiles:
            return self.model_profiles[0].model_id
        return str(self.provider_type)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider_profile_id": self.provider_profile_id,
            "display_name": self.display_name,
            "provider_type": str(self.provider_type),
            "base_url_configured": bool(self.base_url or self.base_url_env),
            "base_url_source": "env" if self.base_url_env else "profile" if self.base_url else None,
            "api_key_env": self.api_key_env,
            "secret_ref": "[configured]" if self.secret_ref else None,
            "secret_ref_configured": bool(self.secret_ref),
            "local_secret_ref": "[configured]" if self.local_secret_ref else None,
            "local_secret_ref_configured": bool(self.local_secret_ref),
            "model_profiles": [model.safe_summary() for model in self.model_profiles],
            "capabilities": list(self.capabilities),
            "allowed_modes": [str(mode) for mode in self.allowed_modes],
            "enabled": self.enabled,
            "cost_tracking": self.cost_tracking,
            "safety_policy": self.safety_policy.model_dump(mode="json"),
            "provider_notes": redact_text(self.provider_notes),
        }


class ProviderSecretResolver:
    def __init__(self, *, local_secret_dir: str | Path | None = None) -> None:
        self.local_secret_dir = Path(local_secret_dir).expanduser().resolve() if local_secret_dir else None

    def resolve_api_key(self, profile: ProviderProfileV2) -> str | None:
        if profile.api_key_env:
            value = os.getenv(profile.api_key_env)
            if not value:
                raise LLMProviderError(f"Missing provider secret env var: {profile.api_key_env}")
            return value
        if profile.secret_ref:
            raise LLMProviderError(f"Provider secret_ref is not available in this local secret resolver: {profile.secret_ref}")
        if profile.local_secret_ref:
            return self.resolve_local_secret_ref(profile.local_secret_ref)
        if profile.key_required():
            raise LLMProviderError("Provider API key is required but no api_key_env, secret_ref, or local_secret_ref is configured")
        return None

    def resolve_local_secret_ref(self, local_secret_ref: str) -> str:
        path = self.local_secret_path(local_secret_ref)
        if not path.exists() or not path.is_file():
            raise LLMProviderError("Provider local_secret_ref is not available in this local secret resolver")
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise LLMProviderError("Provider local_secret_ref could not be read safely") from exc
        if not value:
            raise LLMProviderError("Provider local_secret_ref resolved to an empty secret")
        return value

    def local_secret_path(self, local_secret_ref: str) -> Path:
        safe_ref = ProviderProfileV2.validate_secret_ref(local_secret_ref)
        if safe_ref is None:
            raise LLMProviderError("Provider local_secret_ref is required")
        base_dir = self._local_secret_base_dir()
        relative = Path(*safe_ref.split("/"))
        target = (base_dir / f"{relative.as_posix()}.secret").resolve()
        if base_dir not in target.parents and target.parent != base_dir:
            raise LLMProviderError("Provider local_secret_ref path escaped local secret store")
        return target

    def _local_secret_base_dir(self) -> Path:
        if self.local_secret_dir is not None:
            base_dir = self.local_secret_dir
        else:
            raw = os.getenv(LOCAL_SECRET_DIR_ENV)
            if raw:
                base_dir = Path(raw).expanduser().resolve()
            elif os.name == "nt":
                base = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
                base_dir = Path(base).expanduser().resolve() / "AI Narrative Studio" / "provider-secrets"
            else:
                base_dir = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config").expanduser().resolve() / "ai-narrative-studio" / "provider-secrets"
        workspace = Path.cwd().resolve()
        if base_dir == workspace or workspace in base_dir.parents:
            raise LLMProviderError("Provider local secret store must be outside the project workspace")
        return base_dir

    def resolve_base_url(self, profile: ProviderProfileV2) -> str | None:
        if profile.base_url_env:
            value = os.getenv(profile.base_url_env)
            if not value:
                raise LLMProviderError(f"Missing provider base_url env var: {profile.base_url_env}")
            return value
        return profile.base_url


class FakeProviderSecretResolver(ProviderSecretResolver):
    def __init__(self, secrets: dict[str, str] | None = None, base_urls: dict[str, str] | None = None) -> None:
        super().__init__()
        self.secrets = secrets or {}
        self.base_urls = base_urls or {}

    def resolve_api_key(self, profile: ProviderProfileV2) -> str | None:
        if profile.api_key_env and profile.api_key_env in self.secrets:
            return self.secrets[profile.api_key_env]
        if profile.secret_ref and profile.secret_ref in self.secrets:
            return self.secrets[profile.secret_ref]
        if profile.local_secret_ref and profile.local_secret_ref in self.secrets:
            return self.secrets[profile.local_secret_ref]
        return super().resolve_api_key(profile)

    def resolve_base_url(self, profile: ProviderProfileV2) -> str | None:
        if profile.base_url_env and profile.base_url_env in self.base_urls:
            return self.base_urls[profile.base_url_env]
        return super().resolve_base_url(profile)


class ProviderProfileRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.profiles_root = (self.project_root / "providers" / "profiles").resolve()
        if self.project_root not in self.profiles_root.parents:
            raise ValueError("Provider profile repository escaped project root")
        self.profiles_root.mkdir(parents=True, exist_ok=True)

    def create_provider_profile(self, profile: ProviderProfileV2) -> ProviderProfileV2:
        return self.save_provider_profile(profile)

    def load_provider_profile(self, provider_profile_id: str) -> ProviderProfileV2:
        return ProviderProfileV2.model_validate(self._read_yaml(provider_profile_id))

    def save_provider_profile(self, profile: ProviderProfileV2) -> ProviderProfileV2:
        self.validate_provider_profile(profile)
        target = self._path_for_id(profile.provider_profile_id)
        target.write_text(yaml.safe_dump(profile.model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8")
        return profile

    def list_provider_profiles(self) -> list[ProviderProfileV2]:
        return sorted(
            [ProviderProfileV2.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {}) for path in self.profiles_root.glob("*.yaml")],
            key=lambda item: item.provider_profile_id,
        )

    def list_safe_summaries(self) -> list[dict[str, Any]]:
        return [profile.safe_summary() for profile in self.list_provider_profiles()]

    def update_provider_profile(self, provider_profile_id: str, updates: dict[str, Any]) -> ProviderProfileV2:
        current = self.load_provider_profile(provider_profile_id)
        updated = current.model_copy(update=updates)
        return self.save_provider_profile(ProviderProfileV2.model_validate(updated.model_dump(mode="json")))

    def delete_provider_profile(self, provider_profile_id: str) -> None:
        self._path_for_id(provider_profile_id).unlink(missing_ok=True)

    def validate_provider_profile(self, profile: ProviderProfileV2) -> None:
        if self._contains_secret_value(profile.model_dump(mode="json")):
            raise ValueError("Provider profile must not contain secrets")

    def _contains_secret_value(self, value: Any, *, key: str = "") -> bool:
        if key in {"api_key_env", "base_url_env", "secret_ref", "local_secret_ref"}:
            return False
        if isinstance(value, str):
            return contains_secret_text(value)
        if isinstance(value, dict):
            return any(self._contains_secret_value(item, key=str(item_key)) for item_key, item in value.items())
        if isinstance(value, list):
            return any(self._contains_secret_value(item) for item in value)
        return False

    def _path_for_id(self, provider_profile_id: str) -> Path:
        if not safe_identifier(provider_profile_id):
            raise ValueError("Unsafe provider profile id")
        safe = validate_project_relative_path(f"providers/profiles/{provider_profile_id}.yaml")
        target = (self.project_root / safe).resolve()
        if self.profiles_root not in target.parents and target.parent != self.profiles_root:
            raise ValueError("Provider profile path escaped repository")
        return target

    def _read_yaml(self, provider_profile_id: str) -> dict[str, Any]:
        path = self._path_for_id(provider_profile_id)
        if not path.exists():
            raise FileNotFoundError(f"Provider profile not found: {provider_profile_id}")
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


class ProviderCapabilityReport(BaseModel):
    provider_profile_id: str
    model_id: str
    detection_source: Literal["profile_declared", "registry_declared", "dry_run"] = "profile_declared"
    supports_text: bool = True
    supports_json: bool = True
    supports_tools: bool = False
    supports_streaming: bool = False
    supports_embeddings: bool = False
    supports_long_context: bool = False
    context_window: int | None = None
    max_output_tokens: int | None = None
    recommended_use_cases: list[str] = Field(default_factory=list)
    structured_output_reliability_hint: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class CapabilityDetectionService:
    JSON_USE_CASES = {"world_intent_parse", "structured_json", "cross_mode_draft", "quality_eval"}

    def detect_from_profile(self, profile: ProviderProfileV2, model_id: str | None = None) -> list[ProviderCapabilityReport]:
        models = profile.model_profiles or [ModelProfile(model_id=model_id or profile.primary_model_id(), display_name=profile.primary_model_id())]
        reports: list[ProviderCapabilityReport] = []
        for model in models:
            if model_id and model.model_id != model_id:
                continue
            reports.append(
                ProviderCapabilityReport(
                    provider_profile_id=profile.provider_profile_id,
                    model_id=model.model_id,
                    supports_text=model.supports_text,
                    supports_json=model.supports_json,
                    supports_tools=model.supports_tools,
                    supports_streaming=model.supports_streaming,
                    supports_embeddings=model.supports_embeddings,
                    supports_long_context=model.supports_long_context or bool(model.context_window and model.context_window >= 32000),
                    context_window=model.context_window,
                    max_output_tokens=model.max_output_tokens,
                    recommended_use_cases=model.recommended_use_cases,
                    structured_output_reliability_hint=model.structured_output_reliability_hint,
                    warnings=[] if profile.enabled else ["provider_disabled"],
                )
            )
        return reports

    def validate_model_capabilities(self, report: ProviderCapabilityReport, *, mode: str, use_case: str) -> ProviderCapabilityReport:
        warnings = list(report.warnings)
        errors = list(report.errors)
        if not report.supports_text:
            errors.append("model_must_support_text")
        if use_case in self.JSON_USE_CASES and not report.supports_json:
            errors.append("use_case_requires_json_support")
        if mode == "novel" and not report.supports_text:
            errors.append("novel_mode_requires_text")
        if mode == "tavern" and not report.supports_text:
            errors.append("tavern_mode_requires_text")
        return report.model_copy(update={"warnings": warnings, "errors": errors})

    def list_capabilities_for_mode(self, profiles: list[ProviderProfileV2], mode: str) -> list[ProviderCapabilityReport]:
        reports: list[ProviderCapabilityReport] = []
        for profile in profiles:
            if profile.allowed_modes and ProviderMode(mode) not in profile.allowed_modes:
                continue
            reports.extend(self.detect_from_profile(profile))
        return reports


class ModelCapabilityMatrixRow(BaseModel):
    provider_profile_id: str
    provider_type: str
    model_id: str
    display_name: str = ""
    capabilities: dict[str, Any] = Field(default_factory=dict)
    allowed_modes: list[str] = Field(default_factory=list)
    recommended_use_cases: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disabled_reasons: list[str] = Field(default_factory=list)
    enabled: bool = True


class ModelCapabilityMatrix(BaseModel):
    project_id: str
    generated_at: str = Field(default_factory=now_iso)
    rows: list[ModelCapabilityMatrixRow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def build_model_capability_matrix(project_id: str, profiles: list[ProviderProfileV2]) -> ModelCapabilityMatrix:
    detector = CapabilityDetectionService()
    rows: list[ModelCapabilityMatrixRow] = []
    for profile in profiles:
        for report in detector.detect_from_profile(profile):
            disabled = [] if profile.enabled else ["provider_disabled"]
            if profile.allowed_modes:
                for mode in profile.allowed_modes:
                    checked = detector.validate_model_capabilities(report, mode=str(mode), use_case="structured_json")
                    if checked.errors:
                        break
            rows.append(
                ModelCapabilityMatrixRow(
                    provider_profile_id=profile.provider_profile_id,
                    provider_type=str(profile.provider_type),
                    model_id=report.model_id,
                    display_name=report.model_id,
                    capabilities={
                        "supports_text": report.supports_text,
                        "supports_json": report.supports_json,
                        "supports_tools": report.supports_tools,
                        "supports_streaming": report.supports_streaming,
                        "supports_embeddings": report.supports_embeddings,
                        "supports_long_context": report.supports_long_context,
                        "context_window": report.context_window,
                        "max_output_tokens": report.max_output_tokens,
                    },
                    allowed_modes=[str(mode) for mode in profile.allowed_modes],
                    recommended_use_cases=report.recommended_use_cases,
                    warnings=report.warnings + ([] if report.supports_json else ["missing_json_capability_for_structured_modes"]),
                    disabled_reasons=disabled,
                    enabled=profile.enabled,
                )
            )
    return ModelCapabilityMatrix(project_id=project_id, rows=rows)


class ProviderSimulationBehavior(StrEnum):
    SUCCESS_TEXT = "success_text"
    SUCCESS_JSON = "success_json"
    INVALID_JSON = "invalid_json"
    SCHEMA_MISMATCH = "schema_mismatch"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_ERROR = "provider_error"
    SAFETY_REJECTION = "safety_rejection"
    SLOW_RESPONSE = "slow_response"


class ProviderSimulationProfile(BaseModel):
    simulation_id: str = Field(default_factory=lambda: f"sim-{uuid4().hex}")
    default_behavior: ProviderSimulationBehavior = ProviderSimulationBehavior.SUCCESS_TEXT
    behavior_by_use_case: dict[str, ProviderSimulationBehavior] = Field(default_factory=dict)
    text_response: str = "safe simulated text"
    json_response: dict[str, Any] = Field(default_factory=dict)
    slow_response_seconds: float = Field(default=0.01, ge=0, le=1)


class ProviderCallTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid4().hex}")
    provider_profile_id: str = "simulation"
    model_id: str = "simulation"
    use_case: str = "unknown"
    behavior: str = ""
    success: bool = False
    error_type: str | None = None
    duration_ms: float = 0.0

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class SimulatedProvider(LLMProvider):
    def __init__(self, profile: ProviderSimulationProfile, *, provider_profile_id: str = "simulation", model_id: str = "simulation") -> None:
        self.profile = profile
        self.provider_profile_id = provider_profile_id
        self.model_id = model_id
        self.traces: list[ProviderCallTrace] = []

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        behavior = self._behavior("generate_text")
        return self._run(behavior, "generate_text", lambda: self.profile.text_response)

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        behavior = self._behavior(f"generate_json:{schema.__name__}")

        def work() -> SchemaT:
            if behavior == ProviderSimulationBehavior.INVALID_JSON:
                raise LLMProviderError("invalid_json: simulated malformed JSON")
            payload = self.profile.json_response or self._sample_for_schema(schema)
            if behavior == ProviderSimulationBehavior.SCHEMA_MISMATCH:
                payload = {"invalid": "payload"}
            try:
                return schema.model_validate(payload)
            except ValidationError as exc:
                raise LLMProviderError("simulated provider JSON output failed schema validation") from exc

        return self._run(behavior, f"generate_json:{schema.__name__}", work)

    def _behavior(self, use_case: str) -> ProviderSimulationBehavior:
        return self.profile.behavior_by_use_case.get(use_case, self.profile.default_behavior)

    def _run(self, behavior: ProviderSimulationBehavior, use_case: str, work: Any) -> Any:
        started = perf_counter()
        trace = ProviderCallTrace(provider_profile_id=self.provider_profile_id, model_id=self.model_id, use_case=use_case, behavior=str(behavior))
        try:
            if behavior == ProviderSimulationBehavior.TIMEOUT:
                raise LLMProviderError("timeout: simulated provider timeout")
            if behavior == ProviderSimulationBehavior.RATE_LIMIT:
                raise LLMProviderError("rate_limited: simulated provider rate limit")
            if behavior == ProviderSimulationBehavior.PROVIDER_ERROR:
                raise LLMProviderError("provider_error: simulated provider failure")
            if behavior == ProviderSimulationBehavior.SAFETY_REJECTION:
                raise LLMProviderError("safety_rejection: simulated provider safety rejection")
            if behavior == ProviderSimulationBehavior.SLOW_RESPONSE:
                sleep(self.profile.slow_response_seconds)
            result = work()
            trace.success = True
            return result
        except Exception as exc:
            trace.error_type = type(exc).__name__
            raise
        finally:
            trace.duration_ms = round((perf_counter() - started) * 1000, 3)
            self.traces.append(trace)

    def _sample_for_schema(self, schema: type[SchemaT]) -> dict[str, Any]:
        name = schema.__name__
        if name == "PlayerIntent":
            return {"action_type": "observe", "raw_text": "observe", "confidence": 0.9, "requires_clarification": False}
        if name == "NarrativeResult":
            return {"text": "Safe simulated narration.", "suggested_actions": ["observe"], "short_summary": "safe"}
        if name == "MemorySummary":
            return {"summary": "Safe simulated memory.", "important_facts": [], "open_threads": []}
        if name == "GeneratedNovelDraft":
            return {"text": "Safe simulated novel draft.", "summary": "safe"}
        if name == "GeneratedTavernReply":
            return {"content": "Safe simulated reply.", "speaker_id": "character"}
        if name == "CrossModeDraft":
            return {"artifact_id": "sim_draft", "project_id": "demo", "direction": "novel_to_world", "artifact_type": "fact_draft"}
        if name == "ProviderCapabilityReport":
            return {"provider_profile_id": "simulation", "model_id": "simulation"}
        return {}
