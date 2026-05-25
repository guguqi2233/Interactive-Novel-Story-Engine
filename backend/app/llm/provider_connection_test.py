from __future__ import annotations
import json
from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider_base import LLMProviderError
from app.llm.provider_profiles import ProviderProfileType, ProviderProfileV2, ProviderSecretResolver
from app.llm.provider_redaction import provider_redactor


REMOTE_BASE_URL_TYPES = {
    ProviderProfileType.OPENAI_COMPATIBLE,
    ProviderProfileType.RELAY,
    ProviderProfileType.LOCAL_HTTP,
    ProviderProfileType.CUSTOM,
}


class ProviderConnectionTestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider_profile_id: str | None = None
    provider_type: ProviderProfileType | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    api_key_env: str | None = None
    secret_ref: str | None = None
    local_secret_ref: str | None = None
    transient_api_key: str | None = Field(default=None, repr=False)
    timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    allow_real_connection: bool = False


class ProviderConnectionStatus(BaseModel):
    status: str
    safe_message: str
    provider_type: str
    tested_at: str
    latency_ms: float | None = None
    error_type: str | None = None
    redaction_applied: bool = True


class ProviderConnectionClientResult(BaseModel):
    status: str
    safe_message: str
    error_type: str | None = None


class ProviderConnectionTestClient(Protocol):
    def test_connection(
        self,
        profile: ProviderProfileV2,
        *,
        api_key: str | None,
        base_url: str | None,
        timeout_seconds: float,
    ) -> ProviderConnectionClientResult:
        ...


class FakeProviderConnectionTestClient:
    """Deterministic local client for connection tests.

    This client intentionally does not perform network I/O. Tests and CI can
    use payload markers to exercise provider-like outcomes without contacting a
    provider endpoint or logging secrets.
    """

    def test_connection(
        self,
        profile: ProviderProfileV2,
        *,
        api_key: str | None,
        base_url: str | None,
        timeout_seconds: float,
    ) -> ProviderConnectionClientResult:
        signal = f"{profile.provider_profile_id} {base_url or ''} {api_key or ''}".lower()
        if "timeout" in signal:
            return ProviderConnectionClientResult(status="timeout", safe_message="Provider connection timed out.", error_type="timeout")
        if "authfail" in signal or "auth-fail" in signal:
            return ProviderConnectionClientResult(status="auth_failed", safe_message="Provider authentication failed.", error_type="auth_failed")
        if "raw-secret-error" in signal:
            raw_provider_key = "sk-" + "test-raw-provider-secret"
            query_key = "sk-" + "test-query-secret"
            return ProviderConnectionClientResult(
                status="auth_failed",
                safe_message=(
                    f"Raw provider error Authorization: Bearer {raw_provider_key} "
                    "secret_ref=local/provider-secret raw_provider_error={token:'relay-token-secret-value'} "
                    f"https://relay.local/v1?api_key={query_key}"
                ),
                error_type="auth_failed",
            )
        if "model-list-fail" in signal:
            return ProviderConnectionClientResult(status="model_list_failed", safe_message="Provider connected but model list check failed.", error_type="model_list_failed")
        if "disconnected" in signal:
            return ProviderConnectionClientResult(status="disconnected", safe_message="Provider endpoint is not reachable.", error_type="disconnected")
        return ProviderConnectionClientResult(status="connected", safe_message="Provider connection test succeeded.")


ProviderHTTPGetTransport = Callable[[str, float, dict[str, str]], tuple[int, str]]


class HTTPProviderConnectionTestClient:
    """Opt-in real HTTP connection probe for trusted local user actions.

    Tests should pass an injected transport. The default transport is used only
    when a user explicitly opts in through the local UI/API.
    """

    def __init__(self, transport: ProviderHTTPGetTransport | None = None) -> None:
        self._transport = transport or _default_http_get

    def test_connection(
        self,
        profile: ProviderProfileV2,
        *,
        api_key: str | None,
        base_url: str | None,
        timeout_seconds: float,
    ) -> ProviderConnectionClientResult:
        url = _provider_models_url(profile, base_url, None)
        headers = _provider_headers(api_key)
        try:
            status_code, body = self._transport(url, timeout_seconds, headers)  # type: ignore[misc]
        except TimeoutError:
            return ProviderConnectionClientResult(status="timeout", safe_message="Provider connection timed out.", error_type="timeout")
        except Exception:
            return ProviderConnectionClientResult(status="disconnected", safe_message="Provider connection failed safely.", error_type="provider_error")
        if status_code in {401, 403}:
            return ProviderConnectionClientResult(status="auth_failed", safe_message="Provider authentication failed.", error_type="auth_failed")
        if 200 <= status_code < 300:
            return ProviderConnectionClientResult(status="connected", safe_message="Provider connection test succeeded.")
        if status_code in {404, 405}:
            return ProviderConnectionClientResult(status="model_list_failed", safe_message="Provider connected but model list check failed.", error_type="model_list_failed")
        safe_status = "Provider connection failed safely."
        if _looks_like_json_object(body):
            safe_status = "Provider endpoint responded but did not confirm model connectivity."
        return ProviderConnectionClientResult(status="disconnected", safe_message=safe_status, error_type="disconnected")


def redact_provider_connection_text(text: str, *, transient_api_key: str | None = None) -> str:
    return provider_redactor.redact_text(text, extra_secrets=[transient_api_key]).text


def build_provider_profile_for_connection_test(
    request: ProviderConnectionTestRequest,
    *,
    existing_profile: ProviderProfileV2 | None = None,
) -> ProviderProfileV2:
    if existing_profile is not None:
        payload = existing_profile.model_dump(mode="json")
        for field_name in ("provider_type", "base_url", "base_url_env", "api_key_env", "secret_ref", "local_secret_ref"):
            value = getattr(request, field_name)
            if value is not None:
                payload[field_name] = value
        return ProviderProfileV2.model_validate(payload)

    provider_type = request.provider_type or ProviderProfileType.MOCK
    return ProviderProfileV2(
        provider_profile_id=request.provider_profile_id or "connection_test",
        display_name="Connection Test",
        provider_type=provider_type,
        base_url=request.base_url,
        base_url_env=request.base_url_env,
        api_key_env=request.api_key_env,
        secret_ref=request.secret_ref,
        local_secret_ref=request.local_secret_ref,
        requires_api_key=_provider_requires_secret(provider_type),
    )


def test_provider_connection_safe(
    profile: ProviderProfileV2,
    request: ProviderConnectionTestRequest,
    *,
    secret_resolver: ProviderSecretResolver | None = None,
    client: ProviderConnectionTestClient | None = None,
) -> ProviderConnectionStatus:
    resolver = secret_resolver or ProviderSecretResolver()
    connection_client = client or (HTTPProviderConnectionTestClient() if request.allow_real_connection else FakeProviderConnectionTestClient())
    tested_at = datetime.now(UTC).isoformat()
    start = perf_counter()
    transient_key = request.transient_api_key

    base_url_status = _resolve_and_validate_base_url(profile, resolver, transient_key=transient_key)
    if isinstance(base_url_status, ProviderConnectionStatus):
        return base_url_status
    base_url = base_url_status

    api_key_status = _resolve_api_key(profile, resolver, transient_key=transient_key)
    if isinstance(api_key_status, ProviderConnectionStatus):
        return api_key_status
    api_key = api_key_status

    try:
        result = connection_client.test_connection(profile, api_key=api_key, base_url=base_url, timeout_seconds=request.timeout_seconds)
    except TimeoutError:
        result = ProviderConnectionClientResult(status="timeout", safe_message="Provider connection timed out.", error_type="timeout")
    except Exception:
        result = ProviderConnectionClientResult(status="disconnected", safe_message="Provider connection failed safely.", error_type="provider_error")

    latency_ms = round((perf_counter() - start) * 1000, 2)
    safe_message = redact_provider_connection_text(result.safe_message, transient_api_key=transient_key)
    return ProviderConnectionStatus(
        status=result.status,
        safe_message=safe_message,
        provider_type=str(profile.provider_type),
        tested_at=tested_at,
        latency_ms=latency_ms,
        error_type=result.error_type,
        redaction_applied=True,
    )


def _provider_requires_secret(provider_type: ProviderProfileType | str) -> bool:
    return str(provider_type) in {"openai", "openai_compatible", "relay", "custom"}


def _resolve_api_key(
    profile: ProviderProfileV2,
    resolver: ProviderSecretResolver,
    *,
    transient_key: str | None,
) -> str | ProviderConnectionStatus | None:
    if transient_key:
        return transient_key
    if not profile.key_required():
        return None
    try:
        return resolver.resolve_api_key(profile)
    except LLMProviderError:
        return _status("missing_secret", "Provider secret is not configured.", profile, "missing_secret")


def _resolve_and_validate_base_url(
    profile: ProviderProfileV2,
    resolver: ProviderSecretResolver,
    *,
    transient_key: str | None,
) -> str | ProviderConnectionStatus | None:
    try:
        base_url = resolver.resolve_base_url(profile)
    except LLMProviderError:
        return _status("invalid_base_url", "Provider base URL is not configured.", profile, "invalid_base_url")

    provider_type = ProviderProfileType(str(profile.provider_type))
    if provider_type in REMOTE_BASE_URL_TYPES:
        if not base_url:
            return _status("invalid_base_url", "Provider base URL is required for this provider type.", profile, "invalid_base_url")
        if not _is_valid_http_url(base_url):
            safe = redact_provider_connection_text("Provider base URL is invalid.", transient_api_key=transient_key)
            return _status("invalid_base_url", safe, profile, "invalid_base_url")
    return base_url


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    return True


def _status(status: str, safe_message: str, profile: ProviderProfileV2, error_type: str | None) -> ProviderConnectionStatus:
    return ProviderConnectionStatus(
        status=status,
        safe_message=safe_message,
        provider_type=str(profile.provider_type),
        tested_at=datetime.now(UTC).isoformat(),
        latency_ms=None,
        error_type=error_type,
        redaction_applied=True,
    )


def _provider_models_url(profile: ProviderProfileV2, base_url: str | None, model_list_endpoint: str | None) -> str:
    provider_type = ProviderProfileType(str(profile.provider_type))
    root = base_url or ("https://api.openai.com/v1" if provider_type == ProviderProfileType.OPENAI else None)
    if not root:
        raise ValueError("Provider base URL is required")
    endpoint = model_list_endpoint or "/models"
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        parsed = urlparse(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Provider model list endpoint is invalid")
        return endpoint
    return f"{root.rstrip('/')}/{endpoint.lstrip('/')}"


def _provider_headers(api_key: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _default_http_get(url: str, timeout_seconds: float, headers: dict[str, str]) -> tuple[int, str]:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return int(getattr(response, "status", 200)), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(exc.code), body
    except URLError as exc:
        raise LLMProviderError("Provider endpoint could not be reached") from exc


def _looks_like_json_object(text: str) -> bool:
    try:
        return isinstance(json.loads(text), dict)
    except Exception:
        return False
