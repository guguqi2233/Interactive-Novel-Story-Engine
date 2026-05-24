from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


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


def _create_assignment_providers(client: TestClient) -> None:
    low_json = client.post(
        "/projects/demo/providers",
        json={
            "provider_profile_id": "low_json",
            "display_name": "Low JSON",
            "provider_type": "local_stub",
            "model_profiles": [{"model_id": "plain", "supports_json": False, "recommended_use_cases": ["narration"]}],
            "requires_api_key": False,
        },
    )
    strong_json = client.post(
        "/projects/demo/providers",
        json={
            "provider_profile_id": "strong_json",
            "display_name": "Strong JSON",
            "provider_type": "local_stub",
            "model_profiles": [{"model_id": "json-pro", "supports_json": True, "recommended_use_cases": ["structured_output", "quality"]}],
            "requires_api_key": False,
        },
    )
    assert low_json.status_code == 200
    assert strong_json.status_code == 200


def test_project_model_assignment_save_validate_and_fallback_chain(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    config = {
        "rules": [
            {
                "use_case": "novel_draft",
                "primary_provider_id": "low_json",
                "primary_model_id": "plain",
                "fallback_provider_id": "strong_json",
                "fallback_model_id": "json-pro",
                "require_json_support": False,
                "require_local_only": True,
                "enabled": True,
            }
        ]
    }
    try:
        _create_assignment_providers(client)
        validate = client.post("/projects/demo/providers/model-assignments/validate", json=config)
        save = client.post("/projects/demo/providers/model-assignments/save", json=config)
        fetched = client.get("/projects/demo/providers/model-assignments")
        saved_text = (Path(repo.load_project("demo").project_root) / "providers" / "model_assignments.yaml").read_text(encoding="utf-8")
    finally:
        _restore(previous_repo, previous_settings)

    assert validate.status_code == 200
    assert save.status_code == 200
    assert fetched.status_code == 200
    assert save.json()["rules"][0]["use_case"] == "novel_draft"
    assert fetched.json()["fallback_chains"]["novel_draft"] == ["low_json/plain", "strong_json/json-pro"]
    combined = validate.text + save.text + fetched.text + saved_text
    assert "sk-" not in combined
    assert "api_key" not in combined


def test_project_model_assignment_json_capability_warning_with_fallback(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    config = {
        "rules": [
            {
                "use_case": "world_intent_parse",
                "primary_provider_id": "low_json",
                "primary_model_id": "plain",
                "fallback_provider_id": "strong_json",
                "fallback_model_id": "json-pro",
                "require_json_support": True,
                "require_local_only": True,
                "enabled": True,
            }
        ]
    }
    try:
        _create_assignment_providers(client)
        validate = client.post("/projects/demo/providers/model-assignments/validate", json=config)
        save = client.post("/projects/demo/providers/model-assignments/save", json=config)
    finally:
        _restore(previous_repo, previous_settings)

    assert validate.status_code == 200
    report = validate.json()["validation_reports"][0]
    assert report["ok"] is True
    assert "primary_model_lacks_json_support_fallback_will_be_used" in report["warnings"]
    assert save.status_code == 200


def test_project_model_assignment_blocks_missing_json_without_fallback(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    config = {
        "rules": [
            {
                "use_case": "structured_json",
                "primary_provider_id": "low_json",
                "primary_model_id": "plain",
                "require_json_support": True,
                "require_local_only": True,
                "enabled": True,
            }
        ]
    }
    try:
        _create_assignment_providers(client)
        validate = client.post("/projects/demo/providers/model-assignments/validate", json=config)
        save = client.post("/projects/demo/providers/model-assignments/save", json=config)
    finally:
        _restore(previous_repo, previous_settings)

    assert validate.status_code == 200
    assert validate.json()["validation_reports"][0]["ok"] is False
    assert "json_use_case_requires_json_support_or_json_fallback" in validate.json()["validation_reports"][0]["errors"]
    assert save.status_code == 400
