from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel


class ProviderRedactionResult(BaseModel):
    text: str
    redaction_count: int = 0


class ProviderRedactionService:
    """Redacts provider secrets before they can reach responses, logs, or bundles."""

    _OPENAI_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
    _BEARER = re.compile(r"(authorization\s*[:=]\s*)(bearer\s+)?[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
    _KEY_ASSIGNMENT = re.compile(
        r"((?:transient[_-]?)?api[_-]?key|secret[_-]?ref|provider[_-]?secret|relay[_-]?token|access[_-]?token|token|password)\s*[:=]\s*['\"]?[^'\",\s}\]]+",
        re.IGNORECASE,
    )
    _URL_QUERY_SECRET = re.compile(
        r"([?&](?:api[_-]?key|key|token|access[_-]?token|secret|signature|sig|auth|authorization)=)[^&#\s\"'<>]+",
        re.IGNORECASE,
    )
    _URL_PATH_SECRET = re.compile(
        r"(/(?:token|tokens|key|keys|secret|secrets|bearer|auth)/)[A-Za-z0-9._~+/=-]{8,}",
        re.IGNORECASE,
    )
    _RELAY_TOKEN = re.compile(r"\brelay[-_][A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE)
    _RAW_PROVIDER_BLOCK = re.compile(
        r"(raw[_\s-]?provider[_\s-]?(?:error|response)|provider[_\s-]?raw[_\s-]?response|raw[_\s-]?response)\s*[:=]\s*[^}\n]+",
        re.IGNORECASE,
    )

    def redact_text(self, value: str | None, *, extra_secrets: list[str | None] | None = None) -> ProviderRedactionResult:
        if not value:
            return ProviderRedactionResult(text="", redaction_count=0)
        text = str(value)
        count = 0

        for secret in extra_secrets or []:
            if secret:
                text, changed = self._replace_exact(text, secret, "[REDACTED_PROVIDER_SECRET]")
                count += changed

        text, changed = self._sub(self._BEARER, "[REDACTED_AUTHORIZATION]", text)
        count += changed
        text, changed = self._sub(self._OPENAI_KEY, "[REDACTED_API_KEY]", text)
        count += changed
        text, changed = self._sub(self._RELAY_TOKEN, "[REDACTED_RELAY_TOKEN]", text)
        count += changed
        text, changed = self._sub(self._KEY_ASSIGNMENT, lambda match: f"{match.group(1)}=[REDACTED_PROVIDER_SECRET]", text)
        count += changed
        text, changed = self._sub(self._URL_QUERY_SECRET, r"\1[REDACTED_PROVIDER_SECRET]", text)
        count += changed
        text, changed = self._sub(self._URL_PATH_SECRET, r"\1[REDACTED_PROVIDER_SECRET]", text)
        count += changed
        text, changed = self._sub(self._RAW_PROVIDER_BLOCK, "[REDACTED_PROVIDER_RESPONSE]", text)
        count += changed

        return ProviderRedactionResult(text=text, redaction_count=count)

    def redact_mapping(self, value: Any, *, extra_secrets: list[str | None] | None = None) -> Any:
        if isinstance(value, str):
            return self.redact_text(value, extra_secrets=extra_secrets).text
        if isinstance(value, list):
            return [self.redact_mapping(item, extra_secrets=extra_secrets) for item in value]
        if isinstance(value, tuple):
            return tuple(self.redact_mapping(item, extra_secrets=extra_secrets) for item in value)
        if isinstance(value, dict):
            redacted: dict[Any, Any] = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if "raw_provider" in key_text or key_text in {"raw_response", "provider_raw_response"}:
                    redacted[key] = "[REDACTED_PROVIDER_RESPONSE]"
                    continue
                if any(token in key_text for token in ("api_key", "secret_ref", "authorization", "provider_secret", "transient_api_key")):
                    redacted[key] = "[REDACTED_PROVIDER_SECRET]"
                    continue
                redacted[key] = self.redact_mapping(item, extra_secrets=extra_secrets)
            return redacted
        return value

    def redact_url(self, value: str | None, *, extra_secrets: list[str | None] | None = None) -> ProviderRedactionResult:
        if not value:
            return ProviderRedactionResult(text="", redaction_count=0)
        result = self.redact_text(value, extra_secrets=extra_secrets)
        try:
            parsed = urlsplit(result.text)
        except ValueError:
            return result
        if not parsed.query:
            return result
        changed = 0
        safe_query: list[tuple[str, str]] = []
        for key, item in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower().replace("-", "_") in {"api_key", "key", "token", "access_token", "secret", "signature", "sig", "auth", "authorization"}:
                safe_query.append((key, "[REDACTED_PROVIDER_SECRET]"))
                changed += 1
            else:
                safe_query.append((key, item))
        if not changed:
            return result
        return ProviderRedactionResult(
            text=urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(safe_query), parsed.fragment)),
            redaction_count=result.redaction_count + changed,
        )

    def _replace_exact(self, text: str, needle: str, replacement: str) -> tuple[str, int]:
        count = text.count(needle)
        if not count:
            return text, 0
        return text.replace(needle, replacement), count

    def _sub(self, pattern: re.Pattern[str], repl: str | Any, text: str) -> tuple[str, int]:
        return pattern.subn(repl, text)


provider_redactor = ProviderRedactionService()


def redact_provider_text(value: str | None, *, extra_secrets: list[str | None] | None = None) -> str:
    return provider_redactor.redact_text(value, extra_secrets=extra_secrets).text
