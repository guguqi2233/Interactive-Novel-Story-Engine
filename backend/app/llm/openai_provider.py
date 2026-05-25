from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.provider_profiles import ProviderProfileV2, ProviderSecretResolver


OpenAIClientFactory = Callable[..., Any]


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        profile: ProviderProfileV2 | None = None,
        secret_resolver: ProviderSecretResolver | None = None,
        client_factory: OpenAIClientFactory | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._profile = profile
        self._resolver = secret_resolver or ProviderSecretResolver()
        self._api_key = self._resolve_api_key()
        if not self._api_key:
            raise LLMProviderError("LLM_API_KEY is required for OpenAIProvider")
        self._base_url = self._resolver.resolve_base_url(profile) if profile is not None else None
        self._model = profile.primary_model_id() if profile is not None else self._settings.llm_model
        self._client_factory = client_factory
        self._client: Any | None = None

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        response = self._get_client().responses.create(
            model=self._model,
            input=messages,
            temperature=temperature,
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text:
            raise LLMProviderError("OpenAIProvider returned empty text output")
        return output_text

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        response = self._get_client().responses.parse(
            model=self._model,
            input=messages,
            text_format=schema,
            temperature=temperature,
        )
        parsed = getattr(response, "output_parsed", None)
        if isinstance(parsed, schema):
            return parsed
        if isinstance(parsed, BaseModel):
            return schema.model_validate(parsed.model_dump())
        try:
            return schema.model_validate(parsed)
        except ValidationError as exc:
            raise LLMProviderError("OpenAIProvider JSON output failed schema validation") from exc

    def _get_client(self) -> Any:
        if self._client is None:
            if self._client_factory is not None:
                kwargs: dict[str, Any] = {"api_key": self._api_key}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = self._client_factory(**kwargs)
                return self._client
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMProviderError("The openai package is required for OpenAIProvider") from exc
            kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _resolve_api_key(self) -> str | None:
        if self._profile is not None:
            return self._resolver.resolve_api_key(self._profile)
        return self._settings.llm_api_key

