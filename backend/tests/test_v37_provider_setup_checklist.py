from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_connection_cache import ProviderConnectionStatusCache
from app.llm.provider_connection_test import ProviderConnectionStatus
from app.llm.provider_model_assignment import MODEL_ASSIGNMENT_USE_CASES, ProviderModelAssignmentRepository
from app.llm.provider_profiles import ModelProfile, ProviderProfileRepository, ProviderProfileV2
from app.llm.provider_router import JSON_ROUTING_USE_CASES, ProviderRoutingConfig, ProviderRoutingRule
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
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app), repo, previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def _project_root(repo: ProjectRepository) -> Path:
    return Path(repo.load_project("demo").project_root)


def _configure_provider(root: Path, *, supports_json: bool = True, save_assignments: bool = True) -> None:
    profile = ProviderProfileV2(
        provider_profile_id="local_stub",
        display_name="Local Stub",
        provider_type="local_stub",
        requires_api_key=False,
        model_profiles=[
            ModelProfile(
                model_id="json-pro",
                display_name="JSON Pro",
                provider_profile_id="local_stub",
                supports_text=True,
                supports_json=supports_json,
                supports_streaming=True,
                recommended_use_cases=[str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES],
                last_seen_at=datetime.now(UTC).isoformat(),
            )
        ],
    )
    ProviderProfileRepository(root).save_provider_profile(profile)
    ProviderConnectionStatusCache(root).save_status(
        "local_stub",
        ProviderConnectionStatus(
            status="connected",
            safe_message="Provider connection test succeeded.",
            provider_type="local_stub",
            tested_at=datetime.now(UTC).isoformat(),
            latency_ms=2.0,
            redaction_applied=True,
        ),
        model_count=1,
    )
    if save_assignments:
        ProviderModelAssignmentRepository(root).save(
            ProviderRoutingConfig(
                rules=[
                    ProviderRoutingRule(
                        use_case=use_case,
                        primary_provider_id="local_stub",
                        primary_model_id="json-pro",
                        require_json_support=use_case in JSON_ROUTING_USE_CASES,
                        require_local_only=True,
                        enabled=True,
                    )
                    for use_case in MODEL_ASSIGNMENT_USE_CASES
                ]
            )
        )


def _item(payload: dict[str, object], item_id: str) -> dict[str, object]:
    for item in payload["items"]:  # type: ignore[index]
        if item["id"] == item_id:
            return item
    raise AssertionError(f"Missing provider checklist item: {item_id}")


def _assert_no_secrets(text: str) -> None:
    assert "sk-" not in text
    assert "Authorization" not in text
    assert "Bearer" not in text
    assert "transient_api_key" not in text
    assert "raw_provider_response" not in text


def test_provider_setup_checklist_complete_fake_provider_returns_ready(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _configure_provider(_project_root(repo))
        response = client.get("/projects/demo/providers/setup-checklist")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "pass"
    assert payload["pass_count"] == 14
    assert all(item["status"] == "pass" for item in payload["items"])
    _assert_no_secrets(response.text)


def test_provider_setup_checklist_missing_model_assignment_warning(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _configure_provider(_project_root(repo), save_assignments=False)
        response = client.get("/projects/demo/providers/setup-checklist")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "warning"
    assert _item(payload, "novel_model_assigned")["status"] == "warning"
    assert _item(payload, "modelprofile_synced")["status"] == "pass"
    _assert_no_secrets(response.text)


def test_provider_setup_checklist_missing_json_capability_warning(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _configure_provider(_project_root(repo), supports_json=False)
        response = client.get("/projects/demo/providers/setup-checklist")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "warning"
    assert _item(payload, "world_intent_parser_model_assigned")["status"] == "warning"
    assert _item(payload, "json_capable_warning_resolved")["status"] == "warning"
    assert "JSON capability warnings" in _item(payload, "json_capable_warning_resolved")["safe_summary"]
    _assert_no_secrets(response.text)


def test_provider_setup_checklist_missing_provider_is_missing(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.get("/projects/demo/providers/setup-checklist")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "missing"
    assert _item(payload, "provider_profile_exists")["status"] == "missing"
    assert _item(payload, "no_real_key_stored")["status"] == "pass"
    assert _item(payload, "no_transient_key_persisted")["status"] == "pass"
    _assert_no_secrets(response.text)
