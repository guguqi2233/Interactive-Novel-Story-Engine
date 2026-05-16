import json
from collections.abc import Iterable

from pydantic import ValidationError

from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT


class FakeLLMProvider(LLMProvider):
    def __init__(
        self,
        text_responses: Iterable[str] | None = None,
        json_responses: Iterable[dict[str, object] | str] | None = None,
    ) -> None:
        self._text_responses = list(text_responses or [])
        self._json_responses = list(json_responses or [])

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        if not self._text_responses:
            raise LLMProviderError("FakeLLMProvider has no text response configured")
        return self._text_responses.pop(0)

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        if not self._json_responses:
            raise LLMProviderError("FakeLLMProvider has no JSON response configured")

        raw_response = self._json_responses.pop(0)
        payload = json.loads(raw_response) if isinstance(raw_response, str) else raw_response

        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise LLMProviderError("FakeLLMProvider JSON output failed schema validation") from exc

