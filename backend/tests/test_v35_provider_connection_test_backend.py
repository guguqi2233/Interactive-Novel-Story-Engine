from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


TRANSIENT_SENTINEL = "sk-test-transient-authfail-secret"


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


def test_provider_connection_fake_provider_connected(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post("/projects/demo/providers/test-connection", json={"provider_type": "mock", "timeout_seconds": 1})
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "connected"
    assert payload["provider_type"] == "mock"
    assert payload["redaction_applied"] is True


def test_provider_connection_missing_secret_is_safe(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post("/projects/demo/providers/test-connection", json={"provider_type": "openai", "api_key_env": "MISSING_OPENAI_KEY_FOR_TEST"})
        raw_key_response = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_type": "openai", "api_key": "sk-test-extra-raw-key-must-not-echo"},
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "missing_secret"
    assert payload["error_type"] == "missing_secret"
    assert "MISSING_OPENAI_KEY_FOR_TEST" not in response.text
    assert raw_key_response.status_code == 200
    assert raw_key_response.json()["status"] == "missing_secret"
    assert "sk-test-extra-raw-key-must-not-echo" not in raw_key_response.text


def test_provider_connection_auth_failure_redacts_transient_key(tmp_path: Path, caplog) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_type": "openai", "transient_api_key": TRANSIENT_SENTINEL, "timeout_seconds": 1},
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "auth_failed"
    assert payload["error_type"] == "auth_failed"
    assert TRANSIENT_SENTINEL not in response.text
    assert TRANSIENT_SENTINEL not in caplog.text
    assert "Authorization" not in response.text


def test_provider_connection_timeout_and_invalid_base_url_are_safe(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        timeout_response = client.post(
            "/projects/demo/providers/test-connection",
            json={
                "provider_type": "openai_compatible",
                "base_url": "http://timeout.local/v1",
                "transient_api_key": "sk-test-timeout-secret",
                "timeout_seconds": 1,
            },
        )
        invalid_response = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_type": "local_http", "base_url": "not-a-url", "timeout_seconds": 1},
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert timeout_response.status_code == 200
    assert timeout_response.json()["status"] == "timeout"
    assert "sk-test-timeout-secret" not in timeout_response.text
    assert invalid_response.status_code == 200
    assert invalid_response.json()["status"] == "invalid_base_url"


def test_provider_connection_transient_key_is_not_saved_to_profile(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    profile = {
        "provider_profile_id": "relay_safe",
        "display_name": "Relay Safe",
        "provider_type": "relay",
        "base_url": "http://relay.local/v1",
        "api_key_env": "RELAY_API_KEY",
    }
    try:
        created = client.post("/projects/demo/providers", json=profile)
        response = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_profile_id": "relay_safe", "transient_api_key": "sk-test-one-shot-secret", "timeout_seconds": 1},
        )
        profile_text = (Path(repo.load_project("demo").project_root) / "providers" / "profiles" / "relay_safe.yaml").read_text(encoding="utf-8")
    finally:
        _restore(previous_repo, previous_settings)

    assert created.status_code == 200
    assert response.status_code == 200
    assert response.json()["status"] == "connected"
    assert "sk-test-one-shot-secret" not in response.text
    assert "sk-test-one-shot-secret" not in profile_text
    assert "transient_api_key" not in profile_text


def test_provider_profile_rejects_secret_ref_that_looks_like_raw_key(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        raw_key = client.post(
            "/projects/demo/providers",
            json={
                "provider_profile_id": "bad_raw_key",
                "display_name": "Bad Raw Key",
                "provider_type": "relay",
                "base_url": "http://relay.local/v1",
                "secret_ref": "sk-test-secret-ref-should-not-persist",
            },
        )
        auth_header = client.post(
            "/projects/demo/providers",
            json={
                "provider_profile_id": "bad_auth_header",
                "display_name": "Bad Auth Header",
                "provider_type": "relay",
                "base_url": "http://relay.local/v1",
                "secret_ref": "Authorization:Bearer sk-test-secret-ref",
            },
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert raw_key.status_code == 422
    assert auth_header.status_code == 422
    assert "sk-test-secret-ref-should-not-persist" not in raw_key.text
    assert "sk-test-secret-ref" not in auth_header.text


def test_provider_safe_summary_redacts_secret_ref_value(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        created = client.post(
            "/projects/demo/providers",
            json={
                "provider_profile_id": "safe_ref",
                "display_name": "Safe Ref",
                "provider_type": "relay",
                "base_url": "http://relay.local/v1",
                "secret_ref": "local/provider-secret",
            },
        )
        listed = client.get("/projects/demo/providers")
    finally:
        _restore(previous_repo, previous_settings)

    assert created.status_code == 200
    assert listed.status_code == 200
    combined = created.text + listed.text
    assert "local/provider-secret" not in combined
    assert '"secret_ref":"[configured]"' in combined
    assert '"secret_ref_configured":true' in combined
