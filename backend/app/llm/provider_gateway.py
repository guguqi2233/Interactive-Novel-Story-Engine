from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.provider_profiles import ProviderCallTrace
from app.llm.provider_router import ProviderRouter, ProviderRoutingContext, ProviderRoutingUseCase


class ProviderGatewayResult(BaseModel):
    content: str | None = None
    parsed: BaseModel | None = None
    traces: list[ProviderCallTrace] = Field(default_factory=list)


class ProviderGateway:
    """Small local execution boundary for routed provider calls.

    The gateway does not build prompts, apply world state, or inspect hidden
    data. It only executes the same safe message payload against the selected
    provider and, when configured, a fallback provider.
    """

    def __init__(self, providers: dict[str, LLMProvider], *, router: ProviderRouter | None = None) -> None:
        self.providers = providers
        self.router = router or ProviderRouter()
        self.traces: list[ProviderCallTrace] = []

    def provider_for(self, context: ProviderRoutingContext) -> "RoutedLLMProvider":
        return RoutedLLMProvider(self, context)

    def generate_text(self, context: ProviderRoutingContext, messages: list[Message], temperature: float = 0.7) -> str:
        errors: list[str] = []
        for provider_id, model_id in self._provider_chain(context):
            provider = self.providers.get(provider_id)
            if provider is None:
                errors.append(f"provider_missing:{provider_id}")
                continue
            trace = ProviderCallTrace(provider_profile_id=provider_id, model_id=model_id, use_case=str(context.use_case), behavior="gateway_generate_text")
            try:
                result = provider.generate_text(messages, temperature=temperature)
                trace.success = True
                return result
            except LLMProviderError as exc:
                trace.error_type = _safe_error_type(exc)
                errors.append(trace.error_type)
            finally:
                self.traces.append(trace)
        raise LLMProviderError("; ".join(errors) or "provider_gateway_all_attempts_failed")

    def generate_json(self, context: ProviderRoutingContext, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        errors: list[str] = []
        for provider_id, model_id in self._provider_chain(context):
            provider = self.providers.get(provider_id)
            if provider is None:
                errors.append(f"provider_missing:{provider_id}")
                continue
            trace = ProviderCallTrace(provider_profile_id=provider_id, model_id=model_id, use_case=str(context.use_case), behavior=f"gateway_generate_json:{schema.__name__}")
            try:
                result = provider.generate_json(messages, schema=schema, temperature=temperature)
                trace.success = True
                return result
            except LLMProviderError as exc:
                trace.error_type = _safe_error_type(exc)
                errors.append(trace.error_type)
            finally:
                self.traces.append(trace)
        raise LLMProviderError("; ".join(errors) or "provider_gateway_all_attempts_failed")

    def _provider_chain(self, context: ProviderRoutingContext) -> list[tuple[str, str]]:
        decision = self.router.resolve_provider_for_use_case(context)
        chain = [(decision.provider_id, decision.model_id)]
        fallback_decision = self.router.fallback_for_use_case(context)
        if fallback_decision is not None:
            fallback = (fallback_decision.provider_id, fallback_decision.model_id)
            if fallback not in chain:
                chain.append(fallback)
        return chain


class RoutedLLMProvider(LLMProvider):
    def __init__(self, gateway: ProviderGateway, context: ProviderRoutingContext) -> None:
        self.gateway = gateway
        self.context = context

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return self.gateway.generate_text(self.context, messages, temperature=temperature)

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        return self.gateway.generate_json(self.context, messages, schema=schema, temperature=temperature)


def _safe_error_type(exc: Exception) -> str:
    text = str(exc).lower()
    if "timeout" in text:
        return "timeout"
    if "rate" in text:
        return "rate_limited"
    if "schema" in text or "json" in text:
        return "schema_validation_failed"
    if "safety" in text:
        return "safety_rejection"
    return exc.__class__.__name__


class WorldModeRoutedProvider(LLMProvider):
    """Route World intent JSON and narration JSON through separate use cases."""

    def __init__(self, gateway: ProviderGateway) -> None:
        self.gateway = gateway

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return self.gateway.generate_text(
            ProviderRoutingContext(mode="world", use_case=ProviderRoutingUseCase.WORLD_NARRATION),
            messages,
            temperature=temperature,
        )

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        use_case = (
            ProviderRoutingUseCase.WORLD_INTENT_PARSE
            if schema.__name__ == "PlayerIntent"
            else ProviderRoutingUseCase.WORLD_NARRATION
        )
        return self.gateway.generate_json(
            ProviderRoutingContext(mode="world", use_case=use_case),
            messages,
            schema=schema,
            temperature=temperature,
        )


def routed_provider_from_provider(
    provider: LLMProvider,
    *,
    provider_id: str,
    model_id: str,
    mode: str,
    use_case: ProviderRoutingUseCase | str,
) -> RoutedLLMProvider:
    from app.llm.provider_router import ProviderRoutingConfig, ProviderRoutingRule

    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase(str(use_case)),
                    primary_provider_id=provider_id,
                    primary_model_id=model_id,
                    require_json_support=ProviderRoutingUseCase(str(use_case))
                    in {
                        ProviderRoutingUseCase.WORLD_INTENT_PARSE,
                        ProviderRoutingUseCase.CROSS_MODE_DRAFT,
                        ProviderRoutingUseCase.STRUCTURED_JSON,
                        ProviderRoutingUseCase.QUALITY_EVAL,
                    },
                )
            ]
        )
    )
    return ProviderGateway({provider_id: provider}, router=router).provider_for(
        ProviderRoutingContext(mode=mode, use_case=use_case)
    )


def world_routed_provider_from_provider(provider: LLMProvider, *, provider_id: str, model_id: str) -> WorldModeRoutedProvider:
    from app.llm.provider_router import ProviderRoutingConfig, ProviderRoutingRule

    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.WORLD_INTENT_PARSE,
                    primary_provider_id=provider_id,
                    primary_model_id=model_id,
                    require_json_support=True,
                ),
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.WORLD_NARRATION,
                    primary_provider_id=provider_id,
                    primary_model_id=model_id,
                ),
            ]
        )
    )
    return WorldModeRoutedProvider(ProviderGateway({provider_id: provider}, router=router))


def routed_provider_from_settings(
    settings: object,
    *,
    mode: str,
    use_case: ProviderRoutingUseCase | str,
) -> RoutedLLMProvider:
    from app.llm.provider_factory import create_llm_provider

    provider_id = _provider_id_for_settings(settings)
    model_id = _model_id_for_settings(settings)
    return routed_provider_from_provider(
        create_llm_provider(settings),  # type: ignore[arg-type]
        provider_id=provider_id,
        model_id=model_id,
        mode=mode,
        use_case=use_case,
    )


def world_routed_provider_from_settings(settings: object) -> WorldModeRoutedProvider:
    from app.llm.provider_factory import create_llm_provider

    provider_id = _provider_id_for_settings(settings)
    model_id = _model_id_for_settings(settings)
    return world_routed_provider_from_provider(create_llm_provider(settings), provider_id=provider_id, model_id=model_id)  # type: ignore[arg-type]


def project_provider_gateway_from_project(
    project_root: str,
    *,
    secret_resolver: object | None = None,
    openai_compatible_transport: object | None = None,
    local_http_transport: object | None = None,
) -> ProviderGateway:
    """Build a runtime ProviderGateway from project-safe provider metadata.

    This does not test connections, fetch models, or mutate project files. It
    instantiates provider runtime objects only from ProviderProfile metadata,
    with secrets resolved by the backend-only resolver.
    """

    from app.config import Settings
    from app.llm.provider_factory import create_llm_provider
    from app.llm.provider_model_assignment import ProviderModelAssignmentRepository, build_project_provider_registry
    from app.llm.provider_profiles import ProviderProfileRepository, ProviderSecretResolver

    profiles = [profile for profile in ProviderProfileRepository(project_root).list_provider_profiles() if profile.enabled]
    providers: dict[str, LLMProvider] = {}
    resolver = secret_resolver if secret_resolver is not None else ProviderSecretResolver()
    for profile in profiles:
        providers[profile.provider_profile_id] = create_llm_provider(
            Settings(llm_provider=str(profile.provider_type)),
            provider_profile=profile,
            secret_resolver=resolver,  # type: ignore[arg-type]
            openai_compatible_transport=openai_compatible_transport,  # type: ignore[arg-type]
            local_http_transport=local_http_transport,  # type: ignore[arg-type]
        )
    config = ProviderModelAssignmentRepository(project_root).load()
    router = ProviderRouter(registry=build_project_provider_registry(profiles), config=config)
    return ProviderGateway(providers, router=router)


def _provider_id_for_settings(settings: object) -> str:
    return str(getattr(settings, "llm_provider", "mock")).strip().lower()


def _model_id_for_settings(settings: object) -> str:
    provider = _provider_id_for_settings(settings)
    if provider == "openai":
        return str(getattr(settings, "llm_model", "gpt-4.1-mini"))
    if provider == "local_http":
        return str(getattr(settings, "local_llm_model", "local-model"))
    if provider == "openai_compatible":
        return "openai-compatible-chat"
    if provider == "relay":
        return "relay-chat"
    return provider
