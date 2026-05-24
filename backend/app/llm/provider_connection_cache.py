from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider_connection_test import ProviderConnectionStatus
from app.llm.provider_redaction import provider_redactor
from app.platform.narrative_project import validate_project_relative_path
from app.platform.security import safe_identifier


DEFAULT_PROVIDER_CONNECTION_STATUS_TTL_SECONDS = 15 * 60
PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH = "providers/connection_status_cache.json"


class ProviderConnectionStatusCacheEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_profile_id: str
    status: str
    tested_at: str
    latency_ms: float | None = None
    safe_error_type: str | None = None
    model_count: int = Field(default=0, ge=0)
    redaction_applied: bool = True

    def safe_summary(
        self,
        *,
        now: datetime | None = None,
        ttl_seconds: int = DEFAULT_PROVIDER_CONNECTION_STATUS_TTL_SECONDS,
    ) -> dict[str, Any]:
        age_seconds = self.age_seconds(now=now)
        stale = age_seconds is None or age_seconds > ttl_seconds
        return {
            **self.model_dump(mode="json"),
            "age_seconds": age_seconds,
            "ttl_seconds": ttl_seconds,
            "stale": stale,
            "cache_state": "stale" if stale else "fresh",
        }

    def age_seconds(self, *, now: datetime | None = None) -> int | None:
        try:
            tested_at = datetime.fromisoformat(self.tested_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        if tested_at.tzinfo is None:
            tested_at = tested_at.replace(tzinfo=UTC)
        current = now or datetime.now(UTC)
        return max(0, int((current - tested_at).total_seconds()))


class ProviderConnectionStatusCache:
    """Safe local cache for Provider connection metadata.

    The cache intentionally stores only status metadata. It does not store raw
    raw provider response payloads, a raw error body, env values,
    Authorization headers, API keys, transient API keys, transient_api_key
    payload fields, ProviderProfile secret values, or safe_message text from a
    connection test.
    """

    def __init__(self, project_root: str | Path, *, ttl_seconds: int = DEFAULT_PROVIDER_CONNECTION_STATUS_TTL_SECONDS) -> None:
        self.project_root = Path(project_root).resolve()
        self.ttl_seconds = ttl_seconds
        relative_path = validate_project_relative_path(PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH)
        self.cache_path = (self.project_root / relative_path).resolve()
        if self.project_root not in self.cache_path.parents:
            raise ValueError("Provider connection status cache escaped project root")
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def load_status(self, provider_profile_id: str) -> ProviderConnectionStatusCacheEntry | None:
        if not safe_identifier(provider_profile_id):
            raise ValueError("Unsafe provider profile id")
        return self._load_entries().get(provider_profile_id)

    def safe_status(self, provider_profile_id: str) -> dict[str, Any] | None:
        entry = self.load_status(provider_profile_id)
        if entry is None:
            return None
        return entry.safe_summary(ttl_seconds=self.ttl_seconds)

    def save_status(
        self,
        provider_profile_id: str,
        status: ProviderConnectionStatus,
        *,
        model_count: int = 0,
    ) -> ProviderConnectionStatusCacheEntry:
        if not safe_identifier(provider_profile_id):
            raise ValueError("Unsafe provider profile id")
        safe_status = provider_redactor.redact_text(status.status).text
        safe_error_type = provider_redactor.redact_text(status.error_type).text if status.error_type else None
        entry = ProviderConnectionStatusCacheEntry(
            provider_profile_id=provider_profile_id,
            status=safe_status,
            tested_at=status.tested_at,
            latency_ms=status.latency_ms,
            safe_error_type=safe_error_type or None,
            model_count=max(0, int(model_count)),
            redaction_applied=True,
        )
        entries = self._load_entries()
        entries[provider_profile_id] = entry
        self._write_entries(entries)
        return entry

    def missing_status(self, provider_profile_id: str, *, enabled: bool, model_count: int = 0) -> dict[str, Any]:
        if not safe_identifier(provider_profile_id):
            raise ValueError("Unsafe provider profile id")
        return {
            "provider_profile_id": provider_profile_id,
            "status": "configured_not_tested" if enabled else "unconfigured",
            "tested_at": None,
            "latency_ms": None,
            "safe_error_type": None,
            "model_count": max(0, int(model_count)),
            "redaction_applied": True,
            "age_seconds": None,
            "ttl_seconds": self.ttl_seconds,
            "stale": True,
            "cache_state": "missing",
        }

    def _load_entries(self) -> dict[str, ProviderConnectionStatusCacheEntry]:
        if not self.cache_path.exists():
            return {}
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        entries: dict[str, ProviderConnectionStatusCacheEntry] = {}
        for provider_profile_id, value in payload.items():
            if not isinstance(provider_profile_id, str) or not safe_identifier(provider_profile_id):
                continue
            if not isinstance(value, dict):
                continue
            try:
                entry = ProviderConnectionStatusCacheEntry.model_validate(value)
            except Exception:
                continue
            entries[provider_profile_id] = entry
        return entries

    def _write_entries(self, entries: dict[str, ProviderConnectionStatusCacheEntry]) -> None:
        payload = {
            provider_profile_id: entry.model_dump(mode="json", exclude_none=True)
            for provider_profile_id, entry in sorted(entries.items())
        }
        self.cache_path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
