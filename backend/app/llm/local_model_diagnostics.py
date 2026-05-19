from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.llm.model_prompt_lab_policy import redact_sensitive_text
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.provider_capabilities import ProviderCapabilityRegistry
from app.llm.schemas import PlayerActionType, PlayerIntent


class LocalModelDiagnosticRequest(BaseModel):
    run_id: str = Field(default_factory=lambda: f"local-model-diagnostic-{uuid4().hex}")
    provider_id: str = "local_http"
    base_url: str | None = None
    model_id: str | None = None
    allow_real_local_check: bool = False
    health_check_path: str | None = None
    timeout_seconds: float = Field(default=2.0, gt=0, le=60)
    fake_mode: str | None = None


class LocalModelDiagnosticCheck(BaseModel):
    name: str
    status: str
    latency_ms: float | None = None
    safe_detail: str = ""
    error_type: str | None = None


class LocalModelDiagnosticReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_id: str
    model_id: str | None = None
    base_url_configured: bool = False
    allow_real_local_check: bool = False
    checks: list[LocalModelDiagnosticCheck] = Field(default_factory=list)
    declared_context_window: int | None = None
    pass_fail: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_local_model_diagnostics(
    request: LocalModelDiagnosticRequest,
    *,
    settings: Settings | None = None,
    registry: ProviderCapabilityRegistry | None = None,
) -> LocalModelDiagnosticReport:
    active_settings = settings or Settings(llm_provider="mock")
    active_registry = registry or ProviderCapabilityRegistry()
    provider_id = request.provider_id.strip().lower()
    model_id = request.model_id or _model_for_provider(provider_id, active_settings)
    base_url = request.base_url or active_settings.local_llm_base_url
    checks: list[LocalModelDiagnosticCheck] = []
    blockers: list[str] = []
    warnings: list[str] = []
    if provider_id not in {"local_http", "local_stub"}:
        blockers.append("diagnostics_support_local_http_or_local_stub_only")
        checks.append(LocalModelDiagnosticCheck(name="provider_supported", status="failed", safe_detail="Unsupported local provider."))
        return _report(request, model_id, bool(base_url), checks, blockers, warnings, None)

    checks.append(
        LocalModelDiagnosticCheck(
            name="base_url_configured",
            status="passed" if provider_id == "local_stub" or bool(base_url) else "failed",
            safe_detail="configured" if bool(base_url) else "LOCAL_LLM_BASE_URL is required for local_http.",
        )
    )
    if provider_id == "local_http" and not base_url:
        blockers.append("local_http_base_url_missing")
        return _report(request, model_id, False, checks, blockers, warnings, _context_window(active_registry, provider_id, model_id))

    if provider_id == "local_http" and not request.allow_real_local_check and not request.fake_mode:
        warnings.append("real_local_check_skipped_without_explicit_opt_in")
        for check_name in ["health_check_endpoint", "generate_text_smoke", "generate_json_smoke", "timeout_behavior", "error_parsing"]:
            checks.append(LocalModelDiagnosticCheck(name=check_name, status="skipped", safe_detail="Set allow_real_local_check or fake_mode to run."))
        return _report(request, model_id, True, checks, blockers, warnings, _context_window(active_registry, provider_id, model_id))

    provider = _provider_for_request(request, active_settings, base_url, model_id)
    checks.append(_health_check(request))
    checks.append(_generate_text_check(provider))
    checks.append(_generate_json_check(provider))
    checks.append(_timeout_check(request, active_settings, base_url, model_id))
    checks.append(_error_parsing_check(request, active_settings, base_url, model_id))
    if any(check.status == "failed" for check in checks):
        blockers.extend(f"{check.name}_failed" for check in checks if check.status == "failed")
    return _report(request, model_id, bool(base_url), checks, blockers, warnings, _context_window(active_registry, provider_id, model_id))


def _provider_for_request(
    request: LocalModelDiagnosticRequest,
    settings: Settings,
    base_url: str | None,
    model_id: str | None,
) -> LLMProvider:
    if request.provider_id == "local_stub":
        return create_llm_provider(
            _settings_for_provider(request, settings, base_url, model_id, provider_id="local_stub"),
            local_stub_invalid_json=request.fake_mode == "invalid_json",
        )
    transport = None if request.allow_real_local_check and not request.fake_mode else _fake_transport(request.fake_mode or "ok")
    return create_llm_provider(
        _settings_for_provider(request, settings, base_url, model_id, provider_id="local_http"),
        local_http_transport=transport,
    )


def _settings_for_provider(
    request: LocalModelDiagnosticRequest,
    settings: Settings,
    base_url: str | None,
    model_id: str | None,
    *,
    provider_id: str,
) -> Settings:
    return Settings(
        **settings.model_copy(
            update={
                "llm_provider": provider_id,
                "local_llm_base_url": base_url or "http://127.0.0.1:11434/v1",
                "local_llm_model": model_id or settings.local_llm_model,
                "local_llm_timeout_seconds": request.timeout_seconds,
            }
        ).model_dump()
    )


def _health_check(request: LocalModelDiagnosticRequest) -> LocalModelDiagnosticCheck:
    if not request.health_check_path:
        return LocalModelDiagnosticCheck(name="health_check_endpoint", status="skipped", safe_detail="No health_check_path configured.")
    if request.allow_real_local_check:
        return LocalModelDiagnosticCheck(name="health_check_endpoint", status="skipped", safe_detail="Health endpoint probing is not bound to a specific local product.")
    return LocalModelDiagnosticCheck(name="health_check_endpoint", status="passed", safe_detail="fake health check passed")


def _generate_text_check(provider: LLMProvider) -> LocalModelDiagnosticCheck:
    started = perf_counter()
    try:
        text = provider.generate_text(_safe_messages(), temperature=0.0)
        return LocalModelDiagnosticCheck(
            name="generate_text_smoke",
            status="passed" if text else "failed",
            latency_ms=round((perf_counter() - started) * 1000, 3),
            safe_detail=redact_sensitive_text(text).text[:80] if text else "empty text response",
        )
    except Exception as exc:
        return _failed_check("generate_text_smoke", exc, started)


def _generate_json_check(provider: LLMProvider) -> LocalModelDiagnosticCheck:
    started = perf_counter()
    try:
        parsed = provider.generate_json(_safe_messages(), PlayerIntent, temperature=0.0)
        return LocalModelDiagnosticCheck(
            name="generate_json_smoke",
            status="passed",
            latency_ms=round((perf_counter() - started) * 1000, 3),
            safe_detail=f"schema_valid:{parsed.action_type.value if isinstance(parsed.action_type, PlayerActionType) else parsed.action_type}",
        )
    except Exception as exc:
        return _failed_check("generate_json_smoke", exc, started)


def _timeout_check(
    request: LocalModelDiagnosticRequest,
    settings: Settings,
    base_url: str | None,
    model_id: str | None,
) -> LocalModelDiagnosticCheck:
    if request.fake_mode != "timeout":
        return LocalModelDiagnosticCheck(name="timeout_behavior", status="skipped", safe_detail="timeout simulation not requested")
    provider = create_llm_provider(
        _settings_for_provider(request, settings, base_url, model_id, provider_id="local_http"),
        local_http_transport=_fake_transport("timeout"),
    )
    started = perf_counter()
    try:
        provider.generate_text(_safe_messages(), temperature=0.0)
    except Exception as exc:
        return LocalModelDiagnosticCheck(
            name="timeout_behavior",
            status="passed" if "timed out" in str(exc).lower() or "timeout" in str(exc).lower() else "failed",
            latency_ms=round((perf_counter() - started) * 1000, 3),
            safe_detail=_safe_error_message(str(exc)),
            error_type=type(exc).__name__,
        )
    return LocalModelDiagnosticCheck(name="timeout_behavior", status="failed", safe_detail="timeout simulation did not fail")


def _error_parsing_check(
    request: LocalModelDiagnosticRequest,
    settings: Settings,
    base_url: str | None,
    model_id: str | None,
) -> LocalModelDiagnosticCheck:
    if request.fake_mode != "error":
        return LocalModelDiagnosticCheck(name="error_parsing", status="skipped", safe_detail="error simulation not requested")
    provider = create_llm_provider(
        _settings_for_provider(request, settings, base_url, model_id, provider_id="local_http"),
        local_http_transport=_fake_transport("error"),
    )
    started = perf_counter()
    try:
        provider.generate_text(_safe_messages(), temperature=0.0)
    except Exception as exc:
        return LocalModelDiagnosticCheck(
            name="error_parsing",
            status="passed",
            latency_ms=round((perf_counter() - started) * 1000, 3),
            safe_detail=_safe_error_message(str(exc)),
            error_type=type(exc).__name__,
        )
    return LocalModelDiagnosticCheck(name="error_parsing", status="failed", safe_detail="error simulation did not fail")


def _fake_transport(mode: str):
    def transport(url: str, payload: dict[str, Any], timeout_seconds: float) -> Mapping[str, Any]:
        _ = url, timeout_seconds
        messages = payload.get("messages") or []
        joined = " ".join(str(message.get("content", "")) for message in messages if isinstance(message, dict))
        if "the mayor forged the charter" in joined.lower() or "hidden fact" in joined.lower() or "sk-" in joined.lower():
            raise LLMProviderError("diagnostic prompt contained forbidden hidden or secret text")
        if mode == "timeout":
            raise LLMProviderError("LocalHTTPProvider request timed out")
        if mode == "error":
            raise LLMProviderError("LocalHTTPProvider returned safe fake error response")
        if payload.get("response_format"):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"action_type":"observe","raw_text":"observe locally","confidence":0.9,"requires_clarification":false}'
                        }
                    }
                ]
            }
        return {"choices": [{"message": {"content": "local diagnostic text ok"}}]}

    return transport


def _safe_messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "Local diagnostic only. Do not use world facts."},
        {"role": "user", "content": "Say ok or return observe intent JSON."},
    ]


def _failed_check(name: str, exc: Exception, started: float) -> LocalModelDiagnosticCheck:
    return LocalModelDiagnosticCheck(
        name=name,
        status="failed",
        latency_ms=round((perf_counter() - started) * 1000, 3),
        safe_detail=_safe_error_message(str(exc)),
        error_type=type(exc).__name__,
    )


def _report(
    request: LocalModelDiagnosticRequest,
    model_id: str | None,
    base_url_configured: bool,
    checks: list[LocalModelDiagnosticCheck],
    blockers: list[str],
    warnings: list[str],
    context_window: int | None,
) -> LocalModelDiagnosticReport:
    return LocalModelDiagnosticReport(
        run_id=request.run_id,
        provider_id=request.provider_id,
        model_id=model_id,
        base_url_configured=base_url_configured,
        allow_real_local_check=request.allow_real_local_check,
        checks=checks,
        declared_context_window=context_window,
        pass_fail="fail" if blockers else "pass",
        blockers=blockers,
        warnings=warnings,
    )


def _model_for_provider(provider_id: str, settings: Settings) -> str:
    if provider_id == "local_http":
        return settings.local_llm_model
    if provider_id == "local_stub":
        return "local_stub"
    return provider_id


def _context_window(registry: ProviderCapabilityRegistry, provider_id: str, model_id: str | None) -> int | None:
    if model_id is None:
        return None
    try:
        capability = registry.get_capability(provider_id, model_id)
    except Exception:
        return None
    return getattr(capability, "context_window", None)


def _safe_error_message(message: str) -> str:
    redacted = redact_sensitive_text(message).text
    lowered = redacted.lower()
    if "hidden fact" in lowered or "the mayor forged the charter" in lowered or "sk-" in lowered or "api_key" in lowered:
        return "[redacted]"
    return redacted[:160]


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            stripped = _strip_sensitive(item)
            if _safe_key_value(str(key), stripped):
                safe[str(key)] = stripped
        return safe
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = redact_sensitive_text(value).text
        lowered = redacted.lower()
        if "hidden fact" in lowered or "the mayor forged the charter" in lowered:
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    forbidden = ["api_key", "llm_api_key", "raw_env", "secret", "sk-"]
    return not any(term in lowered for term in forbidden)
