from app.config import Settings, get_settings
from app.llm.local_provider import LocalHTTPProvider, LocalStubProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_capabilities import get_default_provider_capability_registry
from collections.abc import Callable, Mapping
from typing import Any

from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.usage_tracker import wrap_provider_for_usage_tracking


def create_llm_provider(
    settings: Settings | None = None,
    *,
    local_http_transport: Callable[[str, dict[str, Any], float], Mapping[str, Any]] | None = None,
    local_stub_invalid_json: bool = False,
) -> LLMProvider:
    resolved_settings = settings or get_settings()
    provider_name = resolved_settings.llm_provider.strip().lower()
    registry = get_default_provider_capability_registry()
    supported_providers = registry.factory_supported_provider_ids()

    provider: LLMProvider
    if provider_name == "mock":
        provider = MockLLMProvider()
    elif provider_name == "local_stub":
        provider = LocalStubProvider(invalid_json=local_stub_invalid_json)
    elif provider_name == "local_http":
        provider = LocalHTTPProvider(settings=resolved_settings, transport=local_http_transport)
    elif provider_name == "openai":
        provider = OpenAIProvider(settings=resolved_settings)
    else:
        raise LLMProviderError(
            f"Unsupported LLM_PROVIDER: {resolved_settings.llm_provider}. "
            f"Supported providers: {', '.join(supported_providers)}"
        )

    model_id = _model_id_for_settings(resolved_settings)
    input_cost, output_cost = _cost_for_model(registry, provider_name, model_id)
    return wrap_provider_for_usage_tracking(
        provider,
        provider_id=provider_name,
        model_id=model_id,
        enabled=bool(getattr(resolved_settings, "enable_usage_tracking", False)),
        input_cost_per_1k=input_cost,
        output_cost_per_1k=output_cost,
    )


def _model_id_for_settings(settings: Settings) -> str:
    provider_name = settings.llm_provider.strip().lower()
    if provider_name == "openai":
        return settings.llm_model
    if provider_name == "local_http":
        return settings.local_llm_model
    return provider_name


def _cost_for_model(registry: object, provider_id: str, model_id: str) -> tuple[float, float]:
    try:
        capability = registry.get_capability(provider_id, model_id)  # type: ignore[attr-defined]
    except Exception:
        try:
            capability = registry.get_capability(provider_id)  # type: ignore[attr-defined]
        except Exception:
            return 0.0, 0.0
    return (
        float(getattr(capability, "cost_input_per_1k", None) or 0.0),
        float(getattr(capability, "cost_output_per_1k", None) or 0.0),
    )
