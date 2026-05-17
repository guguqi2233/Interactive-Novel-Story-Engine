import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.config import Settings
from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent


class LocalStubProvider(LLMProvider):
    """Mock-compatible local provider for tests and offline development."""

    def __init__(self, invalid_json: bool = False) -> None:
        self.invalid_json = invalid_json

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return "local stub text"

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        payload = self._payload_for_schema(messages, schema)
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise LLMProviderError("LocalStubProvider JSON output failed schema validation") from exc

    def _payload_for_schema(self, messages: list[Message], schema: type[SchemaT]) -> dict[str, object]:
        if self.invalid_json:
            return {"invalid": "payload"}
        latest = messages[-1]["content"].lower() if messages else ""
        if schema is PlayerIntent:
            if "search" in latest:
                action_type = PlayerActionType.SEARCH
            elif "smithy" in latest or "blacksmith" in latest:
                return {
                    "action_type": PlayerActionType.MOVE.value,
                    "target_id": "blacksmith",
                    "raw_text": latest,
                    "confidence": 0.9,
                    "requires_clarification": False,
                }
            elif "wait" in latest:
                action_type = PlayerActionType.WAIT
            else:
                action_type = PlayerActionType.OBSERVE
            return {
                "action_type": action_type.value,
                "raw_text": latest,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if schema is NarrativeResult:
            return {
                "text": "本地模型占位叙事：世界规则已经完成结算。",
                "suggested_actions": ["observe", "search"],
                "short_summary": "Local stub narrator response.",
            }
        raise LLMProviderError(f"LocalStubProvider does not support schema: {schema.__name__}")


LocalHTTPTransport = Callable[[str, dict[str, Any], float], Mapping[str, Any]]


class LocalHTTPProvider(LLMProvider):
    """Configurable local HTTP provider using an OpenAI-compatible chat shape."""

    def __init__(self, settings: Settings, transport: LocalHTTPTransport | None = None) -> None:
        if not settings.local_llm_base_url:
            raise LLMProviderError("LOCAL_LLM_BASE_URL is required when LLM_PROVIDER=local_http")
        self.base_url = settings.local_llm_base_url.rstrip("/")
        self.model = settings.local_llm_model
        self.timeout_seconds = settings.local_llm_timeout_seconds
        self.json_mode = settings.local_llm_json_mode
        self._transport = transport or self._default_transport

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        response = self._chat(messages=messages, temperature=temperature, json_mode=False)
        return self._extract_text(response)

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        response = self._chat(messages=messages, temperature=temperature, json_mode=self.json_mode)
        raw_payload = self._extract_json_payload(response)
        try:
            return schema.model_validate(raw_payload)
        except ValidationError as exc:
            raise LLMProviderError(
                f"LocalHTTPProvider JSON output failed schema validation for {schema.__name__}"
            ) from exc

    def _chat(self, messages: list[Message], temperature: float, json_mode: bool) -> Mapping[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return self._transport(f"{self.base_url}/chat/completions", payload, self.timeout_seconds)

    def _default_transport(self, url: str, payload: dict[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise LLMProviderError(f"LocalHTTPProvider request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise LLMProviderError("LocalHTTPProvider could not reach LOCAL_LLM_BASE_URL") from exc
        except TimeoutError as exc:
            raise LLMProviderError("LocalHTTPProvider request timed out") from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LocalHTTPProvider returned non-JSON HTTP response") from exc
        if not isinstance(decoded, Mapping):
            raise LLMProviderError("LocalHTTPProvider returned a JSON response that was not an object")
        return decoded

    def _extract_text(self, response: Mapping[str, Any]) -> str:
        content = self._extract_content(response)
        if not isinstance(content, str):
            raise LLMProviderError("LocalHTTPProvider text response did not contain string content")
        return content

    def _extract_json_payload(self, response: Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(response.get("json"), Mapping):
            return response["json"]  # type: ignore[return-value]
        if isinstance(response.get("data"), Mapping):
            return response["data"]  # type: ignore[return-value]
        content = self._extract_content(response)
        if isinstance(content, Mapping):
            return content
        if not isinstance(content, str):
            raise LLMProviderError("LocalHTTPProvider JSON response did not contain JSON content")
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LocalHTTPProvider JSON response could not be parsed") from exc
        if not isinstance(decoded, Mapping):
            raise LLMProviderError("LocalHTTPProvider JSON response was not an object")
        return decoded

    def _extract_content(self, response: Mapping[str, Any]) -> Any:
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, Mapping):
                message = first_choice.get("message")
                if isinstance(message, Mapping) and "content" in message:
                    return message["content"]
                if "text" in first_choice:
                    return first_choice["text"]
        message = response.get("message")
        if isinstance(message, Mapping) and "content" in message:
            return message["content"]
        for key in ("content", "text", "response"):
            if key in response:
                return response[key]
        raise LLMProviderError("LocalHTTPProvider response did not include model content")
