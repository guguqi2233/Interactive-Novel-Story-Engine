from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


TRANSIENT_MODEL_KEY = "sk-test-model-discovery-secret"


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


def _create_provider(client: TestClient, provider_id: str = "relay_safe") -> None:
    response = client.post(
        "/projects/demo/providers",
        json={
            "provider_profile_id": provider_id,
            "display_name": "Relay Safe",
            "provider_type": "relay",
            "base_url": "http://relay.local/v1",
            "api_key_env": "RELAY_API_KEY",
        },
    )
    assert response.status_code == 200


def test_fetch_models_fake_openai_compatible_success(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "openai_compatible",
                "base_url": "http://compatible.local/v1",
                "transient_api_key": TRANSIENT_MODEL_KEY,
            },
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    report = response.json()["report"]
    assert report["status"] == "ok"
    assert {model["model_id"] for model in report["models"]} == {"fake-chat-small", "fake-json-pro"}
    assert TRANSIENT_MODEL_KEY not in response.text
    assert "api_key" not in response.text


def test_fetch_models_custom_endpoint_success_and_unsupported(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        custom = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "custom",
                "base_url": "http://custom.local/v1",
                "model_list_endpoint": "/custom/models",
                "transient_api_key": "sk-test-custom-model-secret",
            },
        )
        unsupported = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "custom",
                "base_url": "http://unsupported.local/v1",
                "model_list_endpoint": "/unsupported",
                "transient_api_key": "sk-test-unsupported-model-secret",
            },
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert custom.status_code == 200
    assert custom.json()["report"]["status"] == "ok"
    assert {model["model_id"] for model in custom.json()["report"]["models"]} == {"custom-story", "custom-quality"}
    assert unsupported.status_code == 200
    assert unsupported.json()["report"]["status"] == "unsupported_model_list"
    assert "sk-test-custom-model-secret" not in custom.text
    assert "sk-test-unsupported-model-secret" not in unsupported.text


def test_sync_models_saves_model_profiles_without_saving_transient_key(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _create_provider(client)
        response = client.post(
            "/projects/demo/providers/sync-models",
            json={"provider_profile_id": "relay_safe", "transient_api_key": TRANSIENT_MODEL_KEY},
        )
        models_response = client.get("/projects/demo/providers/relay_safe/models")
        profile_text = (Path(repo.load_project("demo").project_root) / "providers" / "profiles" / "relay_safe.yaml").read_text(encoding="utf-8")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    report = response.json()["report"]
    assert report["status"] == "ok"
    assert report["added"] == 2
    assert report["updated"] == 0
    assert report["disabled"] == 0
    assert models_response.status_code == 200
    assert len(models_response.json()["models"]) == 2
    assert "last_seen_at" in profile_text
    assert TRANSIENT_MODEL_KEY not in response.text
    assert TRANSIENT_MODEL_KEY not in models_response.text
    assert TRANSIENT_MODEL_KEY not in profile_text
    assert "transient_api_key" not in profile_text


def test_manual_model_add_and_disabled_model_survives_sync(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _create_provider(client)
        manual = client.patch(
            "/projects/demo/providers/relay_safe/models",
            json={
                "models": [
                    {
                        "model_id": "manual-disabled",
                        "display_name": "Manual Disabled",
                        "supports_text": True,
                        "supports_json": False,
                        "enabled": False,
                    }
                ]
            },
        )
        sync = client.post(
            "/projects/demo/providers/sync-models",
            json={"provider_profile_id": "relay_safe", "transient_api_key": "sk-test-manual-sync-secret"},
        )
        models = client.get("/projects/demo/providers/relay_safe/models")
    finally:
        _restore(previous_repo, previous_settings)

    assert manual.status_code == 200
    assert manual.json()["models"][0]["provider_profile_id"] == "relay_safe"
    assert sync.status_code == 200
    assert sync.json()["report"]["added"] == 2
    assert sync.json()["report"]["unchanged"] == 1
    by_id = {model["model_id"]: model for model in models.json()["models"]}
    assert by_id["manual-disabled"]["enabled"] is False
    assert "sk-test-manual-sync-secret" not in sync.text
