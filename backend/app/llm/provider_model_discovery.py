from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider_connection_test import (
    ProviderConnectionTestRequest,
    build_provider_profile_for_connection_test,
    redact_provider_connection_text,
    test_provider_connection_safe,
)
from app.llm.provider_profiles import ModelProfile, ProviderProfileType, ProviderProfileV2
from app.llm.provider_redaction import provider_redactor


DISCOVERABLE_PROVIDER_TYPES = {
    ProviderProfileType.OPENAI_COMPATIBLE,
    ProviderProfileType.RELAY,
    ProviderProfileType.CUSTOM,
    ProviderProfileType.LOCAL_HTTP,
}


class ProviderModelFetchRequest(ProviderConnectionTestRequest):
    model_config = ConfigDict(extra="ignore")

    model_list_endpoint: str | None = None


class ProviderModelSyncRequest(ProviderModelFetchRequest):
    disable_missing: bool = False


class ProviderModelPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    models: list[ModelProfile] = Field(default_factory=list)


class ProviderModelDiscoveryReport(BaseModel):
    status: str
    safe_message: str
    provider_profile_id: str
    provider_type: str
    fetched_at: str
    models: list[ModelProfile] = Field(default_factory=list)
    error_type: str | None = None
    redaction_applied: bool = True


class ProviderModelSyncReport(BaseModel):
    status: str
    safe_message: str
    provider_profile_id: str
    provider_type: str
    synced_at: str
    added: int = 0
    updated: int = 0
    disabled: int = 0
    unchanged: int = 0
    models: list[ModelProfile] = Field(default_factory=list)
    error_type: str | None = None
    redaction_applied: bool = True


class ProviderModelDiscoveryClient(Protocol):
    def fetch_models(
        self,
        profile: ProviderProfileV2,
        *,
        model_list_endpoint: str | None,
        transient_api_key: str | None,
    ) -> list[dict[str, Any]]:
        ...


class FakeProviderModelDiscoveryClient:
    """Deterministic model list client that never performs network I/O."""

    def fetch_models(
        self,
        profile: ProviderProfileV2,
        *,
        model_list_endpoint: str | None,
        transient_api_key: str | None,
    ) -> list[dict[str, Any]]:
        signal = f"{profile.provider_profile_id} {profile.base_url or ''} {model_list_endpoint or ''}".lower()
        if "raw-secret-error" in signal:
            raw_model_key = "sk-" + "test-model-raw-secret"
            raise RuntimeError(f"raw provider response Authorization: Bearer {raw_model_key} secret_ref=local/model-secret")
        if "unsupported" in signal:
            raise UnsupportedModelListError("Provider does not expose a model list endpoint.")
        if "custom" in (model_list_endpoint or "").lower():
            return [
                {"id": "custom-story", "display_name": "Custom Story", "supports_json": True, "supports_streaming": True},
                {"id": "custom-quality", "display_name": "Custom Quality", "supports_json": True, "recommended_use_cases": ["quality"]},
            ]
        return [
            {"id": "fake-chat-small", "display_name": "Fake Chat Small", "supports_json": True, "supports_streaming": True},
            {"id": "fake-json-pro", "display_name": "Fake JSON Pro", "supports_json": True, "supports_tools": True, "recommended_use_cases": ["world", "quality"]},
        ]


class UnsupportedModelListError(Exception):
    pass


def fetch_provider_models_safe(
    profile: ProviderProfileV2,
    request: ProviderModelFetchRequest,
    *,
    client: ProviderModelDiscoveryClient | None = None,
) -> ProviderModelDiscoveryReport:
    fetched_at = datetime.now(UTC).isoformat()
    connection = test_provider_connection_safe(profile, request)
    if connection.status != "connected":
        return ProviderModelDiscoveryReport(
            status=connection.status,
            safe_message=connection.safe_message,
            provider_profile_id=profile.provider_profile_id,
            provider_type=str(profile.provider_type),
            fetched_at=fetched_at,
            error_type=connection.error_type,
            redaction_applied=True,
        )

    provider_type = ProviderProfileType(str(profile.provider_type))
    if provider_type not in DISCOVERABLE_PROVIDER_TYPES:
        return ProviderModelDiscoveryReport(
            status="unsupported_model_list",
            safe_message="Provider type does not support model list discovery.",
            provider_profile_id=profile.provider_profile_id,
            provider_type=str(profile.provider_type),
            fetched_at=fetched_at,
            error_type="unsupported_model_list",
            redaction_applied=True,
        )

    discovery_client = client or FakeProviderModelDiscoveryClient()
    try:
        raw_models = discovery_client.fetch_models(profile, model_list_endpoint=request.model_list_endpoint, transient_api_key=request.transient_api_key)
    except UnsupportedModelListError:
        return ProviderModelDiscoveryReport(
            status="unsupported_model_list",
            safe_message="Provider model list endpoint is unsupported.",
            provider_profile_id=profile.provider_profile_id,
            provider_type=str(profile.provider_type),
            fetched_at=fetched_at,
            error_type="unsupported_model_list",
            redaction_applied=True,
        )
    except Exception:
        return ProviderModelDiscoveryReport(
            status="model_list_failed",
            safe_message=provider_redactor.redact_text(
                "Provider model list request failed safely.",
                extra_secrets=[request.transient_api_key],
            ).text,
            provider_profile_id=profile.provider_profile_id,
            provider_type=str(profile.provider_type),
            fetched_at=fetched_at,
            error_type="model_list_failed",
            redaction_applied=True,
        )

    models = [_model_from_provider_payload(item, provider_profile_id=profile.provider_profile_id, last_seen_at=fetched_at) for item in raw_models]
    return ProviderModelDiscoveryReport(
        status="ok",
        safe_message=redact_provider_connection_text("Provider model list fetched.", transient_api_key=request.transient_api_key),
        provider_profile_id=profile.provider_profile_id,
        provider_type=str(profile.provider_type),
        fetched_at=fetched_at,
        models=models,
        redaction_applied=True,
    )


def sync_provider_models_safe(
    profile: ProviderProfileV2,
    request: ProviderModelSyncRequest,
    *,
    client: ProviderModelDiscoveryClient | None = None,
) -> tuple[ProviderProfileV2, ProviderModelSyncReport]:
    report = fetch_provider_models_safe(profile, request, client=client)
    synced_at = datetime.now(UTC).isoformat()
    if report.status != "ok":
        return profile, ProviderModelSyncReport(
            status=report.status,
            safe_message=report.safe_message,
            provider_profile_id=profile.provider_profile_id,
            provider_type=str(profile.provider_type),
            synced_at=synced_at,
            error_type=report.error_type,
            redaction_applied=True,
        )

    existing = {model.model_id: model for model in profile.model_profiles}
    fetched = {model.model_id: model for model in report.models}
    added = updated = disabled = unchanged = 0
    merged: dict[str, ModelProfile] = {}

    for model_id, discovered in fetched.items():
        current = existing.get(model_id)
        if current is None:
            added += 1
            merged[model_id] = discovered
            continue
        candidate = discovered.model_copy(update={"enabled": current.enabled})
        if _model_without_seen(candidate) == _model_without_seen(current):
            unchanged += 1
            merged[model_id] = current.model_copy(update={"last_seen_at": discovered.last_seen_at})
        else:
            updated += 1
            merged[model_id] = candidate

    for model_id, current in existing.items():
        if model_id in merged:
            continue
        if request.disable_missing and current.enabled:
            disabled += 1
            merged[model_id] = current.model_copy(update={"enabled": False})
        else:
            unchanged += 1
            merged[model_id] = current

    saved = profile.model_copy(update={"model_profiles": sorted(merged.values(), key=lambda item: item.model_id)})
    return saved, ProviderModelSyncReport(
        status="ok",
        safe_message="Provider models synced to safe ModelProfile metadata.",
        provider_profile_id=profile.provider_profile_id,
        provider_type=str(profile.provider_type),
        synced_at=synced_at,
        added=added,
        updated=updated,
        disabled=disabled,
        unchanged=unchanged,
        models=saved.model_profiles,
        redaction_applied=True,
    )


def build_provider_profile_for_model_request(
    request: ProviderModelFetchRequest,
    *,
    existing_profile: ProviderProfileV2 | None = None,
) -> ProviderProfileV2:
    return build_provider_profile_for_connection_test(request, existing_profile=existing_profile)


def _model_from_provider_payload(payload: dict[str, Any], *, provider_profile_id: str, last_seen_at: str) -> ModelProfile:
    model_id = str(payload.get("id") or payload.get("model_id") or "").strip()
    if not model_id:
        raise ValueError("Provider model payload missing model id")
    return ModelProfile(
        model_id=model_id,
        display_name=str(payload.get("display_name") or payload.get("name") or model_id),
        provider_profile_id=provider_profile_id,
        supports_text=bool(payload.get("supports_text", True)),
        supports_json=bool(payload.get("supports_json", True)),
        supports_streaming=bool(payload.get("supports_streaming", False)),
        supports_tools=bool(payload.get("supports_tools", False)),
        context_window=payload.get("context_window"),
        max_output_tokens=payload.get("max_output_tokens"),
        recommended_use_cases=list(payload.get("recommended_use_cases") or []),
        enabled=bool(payload.get("enabled", True)),
        last_seen_at=last_seen_at,
    )


def _model_without_seen(model: ModelProfile) -> dict[str, Any]:
    data = model.model_dump(mode="json", exclude_none=True)
    data.pop("last_seen_at", None)
    return data
