from app.config import Settings, get_settings
from app.llm.local_provider import LocalHTTPProvider, LocalStubProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider, OpenAICompatibleTransport
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_capabilities import get_default_provider_capability_registry
from collections.abc import Callable, Mapping
from typing import Any

from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.provider_profiles import ProviderProfileV2, ProviderProfileType, ProviderSecretResolver
from app.llm.usage_tracker import wrap_provider_for_usage_tracking


def create_llm_provider(
    settings: Settings | None = None,
    *,
    local_http_transport: Callable[[str, dict[str, Any], float], Mapping[str, Any]] | None = None,
    openai_compatible_transport: OpenAICompatibleTransport | None = None,
    provider_profile: ProviderProfileV2 | None = None,
    secret_resolver: ProviderSecretResolver | None = None,
    local_stub_invalid_json: bool = False,
) -> LLMProvider:
    resolved_settings = settings or get_settings()
    provider_name = str(provider_profile.provider_type).strip().lower() if provider_profile else resolved_settings.llm_provider.strip().lower()
    registry = get_default_provider_capability_registry()
    supported_providers = registry.factory_supported_provider_ids()

    provider: LLMProvider
    if provider_name == "mock":
        provider = MockLLMProvider()
    elif provider_name == "local_stub":
        provider = LocalStubProvider(invalid_json=local_stub_invalid_json)
    elif provider_name == "local_http":
        if provider_profile is not None:
            profile = provider_profile.model_copy(update={"requires_api_key": provider_profile.requires_api_key if provider_profile.requires_api_key is not None else False})
            provider = OpenAICompatibleProvider(profile, secret_resolver=secret_resolver, transport=openai_compatible_transport)
        else:
            provider = LocalHTTPProvider(settings=resolved_settings, transport=local_http_transport)
    elif provider_name == "openai":
        provider = OpenAIProvider(settings=resolved_settings, profile=provider_profile, secret_resolver=secret_resolver)
    elif provider_name in {"openai_compatible", "relay", "custom"}:
        profile = provider_profile or ProviderProfileV2(
            provider_profile_id=provider_name,
            display_name=provider_name,
            provider_type=ProviderProfileType(provider_name),
            base_url=resolved_settings.local_llm_base_url,
            api_key_env="LLM_API_KEY" if resolved_settings.llm_api_key else None,
            requires_api_key=False if provider_name == "openai_compatible" and not resolved_settings.llm_api_key else None,
        )
        provider = OpenAICompatibleProvider(profile, secret_resolver=secret_resolver, transport=openai_compatible_transport)
    else:
        raise LLMProviderError(
            f"Unsupported LLM_PROVIDER: {resolved_settings.llm_provider}. "
            f"Supported providers: {', '.join(supported_providers)}"
        )

    model_id = provider_profile.primary_model_id() if provider_profile else _model_id_for_settings(resolved_settings)
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
    if provider_name in {"local_http", "openai_compatible", "relay"}:
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
