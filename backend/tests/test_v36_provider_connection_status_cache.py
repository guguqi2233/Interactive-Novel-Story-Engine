from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_connection_cache import ProviderConnectionStatusCache
from app.llm.provider_connection_test import ProviderConnectionStatus
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


TRANSIENT_CACHE_KEY = "sk-test-v36-cache-transient-secret"


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _client(tmp_path: Path) -> tuple[TestClient, ProjectRepository, object, object]:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    return TestClient(app), repo, previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def test_provider_connection_status_cache_save_load_and_stale(tmp_path: Path) -> None:
    cache = ProviderConnectionStatusCache(tmp_path, ttl_seconds=1)
    now = datetime.now(UTC)
    status = ProviderConnectionStatus(
        status="connected",
        safe_message="Provider connection test succeeded.",
        provider_type="mock",
        tested_at=now.isoformat(),
        latency_ms=2.5,
        error_type=None,
        redaction_applied=True,
    )

    saved = cache.save_status("mock_profile", status, model_count=2)
    loaded = cache.load_status("mock_profile")
    fresh = cache.safe_status("mock_profile")
    old_status = status.model_copy(update={"tested_at": (now - timedelta(seconds=30)).isoformat(), "status": "timeout", "error_type": "timeout"})
    cache.save_status("old_profile", old_status, model_count=0)
    stale = cache.safe_status("old_profile")

    assert loaded == saved
    assert fresh is not None
    assert fresh["cache_state"] == "fresh"
    assert fresh["stale"] is False
    assert stale is not None
    assert stale["cache_state"] == "stale"
    assert stale["stale"] is True


def test_provider_connection_status_cache_file_has_only_allowed_fields(tmp_path: Path) -> None:
    cache = ProviderConnectionStatusCache(tmp_path)
    status = ProviderConnectionStatus(
        status="auth_failed",
        safe_message="Raw provider body Authorization: Bearer sk-test-cache-safe-message-secret",
        provider_type="relay",
        tested_at=datetime.now(UTC).isoformat(),
        latency_ms=1.0,
        error_type="auth_failed sk-test-cache-error-secret",
        redaction_applied=True,
    )

    cache.save_status("relay_safe", status, model_count=3)
    payload = json.loads(cache.cache_path.read_text(encoding="utf-8"))
    cache_text = cache.cache_path.read_text(encoding="utf-8")
    allowed_fields = {
        "provider_profile_id",
        "status",
        "tested_at",
        "latency_ms",
        "safe_error_type",
        "model_count",
        "redaction_applied",
    }

    assert set(payload["relay_safe"]).issubset(allowed_fields)
    assert "safe_message" not in cache_text
    assert "Authorization" not in cache_text
    assert "sk-test-cache-safe-message-secret" not in cache_text
    assert "sk-test-cache-error-secret" not in cache_text
    assert "[REDACTED_API_KEY]" in cache_text


def test_provider_connection_manual_refresh_writes_safe_cache_without_transient_key(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        created = client.post(
            "/projects/demo/providers",
            json={
                "provider_profile_id": "relay_safe",
                "display_name": "Relay Safe",
                "provider_type": "relay",
                "base_url": "http://relay.local/v1",
                "api_key_env": "RELAY_API_KEY",
            },
        )
        refreshed = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_profile_id": "relay_safe", "transient_api_key": TRANSIENT_CACHE_KEY, "timeout_seconds": 1},
        )
        status = client.get("/projects/demo/providers/relay_safe/status")
        cache_file = Path(repo.load_project("demo").project_root) / "providers" / "connection_status_cache.json"
        cache_text = cache_file.read_text(encoding="utf-8")
    finally:
        _restore(previous_repo, previous_settings)

    assert created.status_code == 200
    assert refreshed.status_code == 200
    assert refreshed.json()["status"] == "connected"
    assert status.status_code == 200
    assert status.json()["status"] == "configured"
    assert status.json()["connection_cache"]["cache_state"] == "fresh"
    assert status.json()["connection_cache"]["stale"] is False
    assert TRANSIENT_CACHE_KEY not in refreshed.text
    assert TRANSIENT_CACHE_KEY not in status.text
    assert TRANSIENT_CACHE_KEY not in cache_text
    assert "transient_api_key" not in cache_text
    assert "Authorization" not in cache_text
    assert "safe_message" not in cache_text


def test_provider_profile_status_missing_cache_is_stale(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        created = client.post(
            "/projects/demo/providers",
            json={
                "provider_profile_id": "mock_safe",
                "display_name": "Mock Safe",
                "provider_type": "mock",
                "model_profiles": [{"model_id": "mock-model"}],
            },
        )
        status = client.get("/projects/demo/providers/mock_safe/status")
    finally:
        _restore(previous_repo, previous_settings)

    assert created.status_code == 200
    assert status.status_code == 200
    assert status.json()["status"] == "configured"
    payload = status.json()["connection_cache"]
    assert payload["cache_state"] == "missing"
    assert payload["stale"] is True
    assert payload["model_count"] == 1
