from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.compatibility.contracts import PROVIDER_CONTRACT_VERSION
from app.config import Settings


class ProviderType(StrEnum):
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    LOCAL_HTTP = "local_http"
    LOCAL_STUB = "local_stub"
    MOCK = "mock"
    RELAY = "relay"


class ProviderCapability(BaseModel):
    contract_version: str = PROVIDER_CONTRACT_VERSION
    provider_id: str
    provider_type: ProviderType
    supports_text: bool = True
    supports_json: bool = True
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_embeddings: bool = False
    context_window: int | None = None
    max_output_tokens: int | None = None
    recommended_use_cases: list[str] = Field(default_factory=list)
    json_reliability_rating: str | None = None
    cost_input_per_1k: float | None = None
    cost_output_per_1k: float | None = None
    requires_api_key: bool = False
    local_only: bool = True
    notes: str = ""

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ModelCapability(BaseModel):
    contract_version: str = PROVIDER_CONTRACT_VERSION
    provider_id: str
    provider_type: ProviderType
    model_id: str
    supports_text: bool = True
    supports_json: bool = True
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_embeddings: bool = False
    context_window: int | None = None
    max_output_tokens: int | None = None
    recommended_use_cases: list[str] = Field(default_factory=list)
    json_reliability_rating: str | None = None
    cost_input_per_1k: float | None = None
    cost_output_per_1k: float | None = None
    requires_api_key: bool = False
    local_only: bool = True
    notes: str = ""

    def supports_use_case(self, use_case: str) -> bool:
        return use_case in self.recommended_use_cases

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ModelUseCaseValidation(BaseModel):
    allowed: bool
    provider_id: str
    model_id: str
    use_case: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProviderCapabilityRegistry:
    """Local declared provider/model capability registry.

    This registry is metadata only. It does not instantiate providers, call
    endpoints, read secrets, or validate whether a remote model truly exists.
    """

    def __init__(
        self,
        *,
        providers: list[ProviderCapability] | None = None,
        models: list[ModelCapability] | None = None,
    ) -> None:
        self._providers = {provider.provider_id: provider for provider in providers or default_provider_capabilities()}
        self._models = {(model.provider_id, model.model_id): model for model in models or default_model_capabilities()}

    def list_providers(self) -> list[ProviderCapability]:
        return sorted(self._providers.values(), key=lambda provider: provider.provider_id)

    def list_models(self, provider_id: str | None = None) -> list[ModelCapability]:
        models = self._models.values()
        if provider_id is not None:
            self._require_provider(provider_id)
            models = [model for model in models if model.provider_id == provider_id]
        return sorted(models, key=lambda model: (model.provider_id, model.model_id))

    def get_capability(self, provider_id: str, model_id: str | None = None) -> ProviderCapability | ModelCapability:
        if model_id is None:
            return self._require_provider(provider_id)
        return self._require_model(provider_id, model_id)

    def validate_model_for_use_case(self, provider_id: str, model_id: str, use_case: str) -> ModelUseCaseValidation:
        model = self._require_model(provider_id, model_id)
        blockers: list[str] = []
        warnings: list[str] = []
        if use_case == "structured_output" and not model.supports_json:
            blockers.append("model_does_not_support_json")
        if use_case == "streaming" and not model.supports_streaming:
            blockers.append("model_does_not_support_streaming")
        if use_case == "tools" and not model.supports_tools:
            blockers.append("model_does_not_support_tools")
        if use_case == "embeddings" and not model.supports_embeddings:
            blockers.append("model_does_not_support_embeddings")
        if use_case not in model.recommended_use_cases:
            warnings.append("use_case_not_recommended")
        return ModelUseCaseValidation(
            allowed=not blockers,
            provider_id=provider_id,
            model_id=model_id,
            use_case=use_case,
            blockers=blockers,
            warnings=warnings,
        )

    def safe_summary_for_frontend(self, settings: Settings | None = None) -> dict[str, Any]:
        current_provider = settings.llm_provider if settings is not None else None
        current_model = _current_model_id(settings) if settings is not None else None
        return {
            "current_provider": current_provider,
            "current_model": current_model,
            "api_key_configured": bool(settings and settings.llm_api_key),
            "local_http_configured": bool(settings and settings.local_llm_base_url),
            "providers": [provider.safe_summary() for provider in self.list_providers()],
            "models": [model.safe_summary() for model in self.list_models()],
        }

    def factory_supported_provider_ids(self) -> list[str]:
        return ["mock", "local_stub", "local_http", "openai"]

    def _require_provider(self, provider_id: str) -> ProviderCapability:
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ValueError(f"Unknown provider capability: {provider_id}")
        return provider

    def _require_model(self, provider_id: str, model_id: str) -> ModelCapability:
        self._require_provider(provider_id)
        model = self._models.get((provider_id, model_id))
        if model is None:
            raise ValueError(f"Unknown model capability: {provider_id}/{model_id}")
        return model


def default_provider_capabilities() -> list[ProviderCapability]:
    return [
        ProviderCapability(
            provider_id="mock",
            provider_type=ProviderType.MOCK,
            recommended_use_cases=["tests", "offline_development", "structured_output"],
            json_reliability_rating="deterministic",
            local_only=True,
            notes="Deterministic mock provider for tests and local development.",
        ),
        ProviderCapability(
            provider_id="local_stub",
            provider_type=ProviderType.LOCAL_STUB,
            recommended_use_cases=["tests", "offline_development", "structured_output", "narration"],
            json_reliability_rating="deterministic",
            local_only=True,
            notes="Offline local stub provider; no model service is called.",
        ),
        ProviderCapability(
            provider_id="local_http",
            provider_type=ProviderType.LOCAL_HTTP,
            supports_streaming=False,
            recommended_use_cases=["local_model_experiment", "structured_output", "narration", "rp_expression"],
            json_reliability_rating="provider_dependent",
            local_only=True,
            notes="OpenAI-compatible local HTTP endpoint selected explicitly through LLM_PROVIDER.",
        ),
        ProviderCapability(
            provider_id="openai",
            provider_type=ProviderType.OPENAI,
            supports_streaming=False,
            recommended_use_cases=["real_provider_benchmark", "structured_output", "narration", "rp_expression"],
            json_reliability_rating="provider_dependent",
            requires_api_key=True,
            local_only=False,
            notes="External OpenAI API provider; requires explicit configuration and credentials.",
        ),
        ProviderCapability(
            provider_id="openai_compatible",
            provider_type=ProviderType.OPENAI_COMPATIBLE,
            recommended_use_cases=["compatibility_metadata", "local_model_experiment"],
            json_reliability_rating="provider_dependent",
            local_only=False,
            notes="Declared compatibility profile; concrete runtime selection is currently local_http.",
        ),
    ]


def default_model_capabilities() -> list[ModelCapability]:
    return [
        ModelCapability(
            provider_id="mock",
            provider_type=ProviderType.MOCK,
            model_id="mock",
            recommended_use_cases=["tests", "offline_development", "structured_output"],
            json_reliability_rating="deterministic",
        ),
        ModelCapability(
            provider_id="local_stub",
            provider_type=ProviderType.LOCAL_STUB,
            model_id="local_stub",
            recommended_use_cases=["tests", "offline_development", "structured_output", "narration"],
            json_reliability_rating="deterministic",
        ),
        ModelCapability(
            provider_id="local_http",
            provider_type=ProviderType.LOCAL_HTTP,
            model_id="local-model",
            recommended_use_cases=["local_model_experiment", "structured_output", "narration", "rp_expression"],
            json_reliability_rating="provider_dependent",
            notes="Declared default local HTTP model id; actual local model is configured by LOCAL_LLM_MODEL.",
        ),
        ModelCapability(
            provider_id="openai",
            provider_type=ProviderType.OPENAI,
            model_id="gpt-4.1-mini",
            context_window=128000,
            max_output_tokens=16384,
            recommended_use_cases=["real_provider_benchmark", "structured_output", "narration", "rp_expression"],
            json_reliability_rating="high",
            requires_api_key=True,
            local_only=False,
            notes="Declared metadata only; registry does not call the provider.",
        ),
        ModelCapability(
            provider_id="openai_compatible",
            provider_type=ProviderType.OPENAI_COMPATIBLE,
            model_id="openai-compatible-chat",
            recommended_use_cases=["compatibility_metadata", "local_model_experiment", "structured_output"],
            json_reliability_rating="provider_dependent",
            local_only=False,
            notes="Generic OpenAI-compatible metadata profile.",
        ),
    ]


def get_default_provider_capability_registry() -> ProviderCapabilityRegistry:
    return ProviderCapabilityRegistry()


def _current_model_id(settings: Settings | None) -> str | None:
    if settings is None:
        return None
    provider = settings.llm_provider.strip().lower()
    if provider == "local_http":
        return settings.local_llm_model
    if provider == "openai":
        return settings.llm_model
    return provider
