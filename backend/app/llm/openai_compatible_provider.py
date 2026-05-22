from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.provider_profiles import ProviderProfileV2, ProviderSecretResolver


OpenAICompatibleTransport = Callable[[str, dict[str, Any], float, dict[str, str]], Mapping[str, Any]]


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible chat-completions provider for custom/relay endpoints."""

    def __init__(
        self,
        profile: ProviderProfileV2,
        *,
        secret_resolver: ProviderSecretResolver | None = None,
        transport: OpenAICompatibleTransport | None = None,
    ) -> None:
        self.profile = profile
        self._resolver = secret_resolver or ProviderSecretResolver()
        base_url = self._resolver.resolve_base_url(profile)
        if not base_url:
            raise LLMProviderError("OpenAI-compatible provider requires base_url or base_url_env")
        self.base_url = base_url.rstrip("/")
        self.model = profile.primary_model_id()
        self.timeout_seconds = profile.default_timeout_seconds
        self._api_key = self._resolver.resolve_api_key(profile)
        self._transport = transport or self._default_transport

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        response = self._chat(messages, temperature=temperature, json_mode=False)
        return _extract_text(response)

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        response = self._chat(messages, temperature=temperature, json_mode=True)
        raw = _extract_text(response)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("OpenAI-compatible provider returned invalid JSON") from exc
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise LLMProviderError("OpenAI-compatible provider JSON output failed schema validation") from exc

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider_profile_id": self.profile.provider_profile_id,
            "provider_type": str(self.profile.provider_type),
            "model_id": self.model,
            "base_url_configured": True,
            "api_key_configured": bool(self._api_key),
        }

    def _chat(self, messages: list[Message], *, temperature: float, json_mode: bool) -> Mapping[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": temperature}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        last_error: Exception | None = None
        for _ in range(self.profile.retry_policy.max_attempts):
            try:
                return self._transport(f"{self.base_url}/chat/completions", payload, self.timeout_seconds, headers)
            except Exception as exc:  # noqa: PERF203 - retry is intentionally tiny and explicit
                last_error = exc
        raise LLMProviderError(f"OpenAI-compatible provider request failed: {type(last_error).__name__}") from last_error

    def _default_transport(self, url: str, payload: dict[str, Any], timeout_seconds: float, headers: dict[str, str]) -> Mapping[str, Any]:
        try:
            request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise LLMProviderError(f"OpenAI-compatible provider HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise LLMProviderError("OpenAI-compatible provider connection failed") from exc
        except TimeoutError as exc:
            raise LLMProviderError("OpenAI-compatible provider request timed out") from exc
        except json.JSONDecodeError as exc:
            raise LLMProviderError("OpenAI-compatible provider returned non-JSON HTTP response") from exc


def _extract_text(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, Mapping):
            message = first.get("message")
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(first.get("text"), str):
                return first["text"]
    for key in ("content", "text", "response"):
        value = response.get(key)
        if isinstance(value, str):
            return value
    raise LLMProviderError("OpenAI-compatible provider returned empty text output")

