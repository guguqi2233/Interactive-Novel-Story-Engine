from typing import Any

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        if not self._settings.llm_api_key:
            raise LLMProviderError("LLM_API_KEY is required for OpenAIProvider")
        self._client: Any | None = None

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        response = self._get_client().responses.create(
            model=self._settings.llm_model,
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
            model=self._settings.llm_model,
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
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMProviderError("The openai package is required for OpenAIProvider") from exc
            self._client = OpenAI(api_key=self._settings.llm_api_key)
        return self._client

