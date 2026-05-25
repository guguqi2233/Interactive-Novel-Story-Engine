from __future__ import annotations

import json
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


def _client(tmp_path: Path, *, debug_enabled: bool = True) -> tuple[TestClient, ProjectRepository, object, object]:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=debug_enabled, llm_provider="mock")
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


def _configure_provider(root: Path, *, save_assignment: bool = True, save_connection: bool = True) -> None:
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
                supports_json=True,
                supports_streaming=True,
                recommended_use_cases=[str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES],
            )
        ],
    )
    ProviderProfileRepository(root).save_provider_profile(profile)
    if save_connection:
        status = ProviderConnectionStatus(
            status="connected",
            safe_message="Provider connection test succeeded.",
            provider_type="local_stub",
            tested_at=datetime.now(UTC).isoformat(),
            latency_ms=1.5,
            redaction_applied=True,
        )
        ProviderConnectionStatusCache(root).save_status("local_stub", status, model_count=1)
    if save_assignment:
        rules = [
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
        ProviderModelAssignmentRepository(root).save(ProviderRoutingConfig(rules=rules))


def _complete_local_fixture(root: Path, *, include_backup: bool = True) -> None:
    _configure_provider(root)
    for relative in (
        "cross_mode/drafts",
        "cross_mode/proposals",
        "cross_mode/reviews",
        "cross_mode/apply_plans",
        "cross_mode/audit",
        "exports/diagnostics",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / "cross_mode" / "drafts" / "README.safe.txt").write_text("safe local cross-mode draft marker", encoding="utf-8")
    (root / "cross_mode" / "proposals" / "proposal.safe.json").write_text(
        json.dumps({"validated": True, "auto_apply": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "reviews" / "review.safe.json").write_text(
        json.dumps({"reviewed": True, "hidden_details_included": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "apply_plans" / "apply_plan.safe.json").write_text(
        json.dumps({"requires_confirm": True, "auto_apply": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "audit" / "audit.safe.json").write_text(
        json.dumps({"audit_trail": True, "state_mutated_by_draft": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "exports" / "diagnostics" / "preview.json").write_text(
        json.dumps({"redacted": True, "uploaded": False, "contains_secrets": False}, sort_keys=True),
        encoding="utf-8",
    )
    if include_backup:
        (root / "backups").mkdir(parents=True, exist_ok=True)
        (root / "backups" / "backup_manifest.json").write_text(
            json.dumps({"local_only": True, "contains_secrets": False}, sort_keys=True),
            encoding="utf-8",
        )


def _item(payload: dict[str, object], item_id: str) -> dict[str, object]:
    for item in payload["items"]:  # type: ignore[index]
        if item["id"] == item_id:
            return item
    raise AssertionError(f"Missing workflow item: {item_id}")


def _assert_safe_response(text: str) -> None:
    assert "sk-" not in text
    assert "Authorization" not in text
    assert "Bearer" not in text
    assert "transient_api_key" not in text
    assert "raw_provider_response" not in text
    assert "raw_prompt" not in text
    assert "raw_output" not in text


def test_workflow_check_complete_fixture_returns_ready(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _complete_local_fixture(_project_root(repo))
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "ready"
    assert payload["ready_count"] == 15
    assert payload["privacy_boundaries_pass"] is True
    assert all(item["status"] == "ready" for item in payload["items"])
    _assert_safe_response(response.text)


def test_workflow_check_missing_provider_returns_warning(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "warning"
    assert _item(payload, "provider_configured")["status"] == "warning"
    assert _item(payload, "connection_status_checked")["status"] == "warning"
    _assert_safe_response(response.text)


def test_workflow_check_missing_model_assignment_returns_warning(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        root = _project_root(repo)
        _configure_provider(root, save_assignment=False)
        for relative in (
            "cross_mode/drafts",
            "cross_mode/proposals",
            "cross_mode/reviews",
            "cross_mode/apply_plans",
            "cross_mode/audit",
            "exports/diagnostics",
        ):
            (root / relative).mkdir(parents=True, exist_ok=True)
        (root / "cross_mode" / "proposals" / "proposal.safe.json").write_text("{}", encoding="utf-8")
        (root / "cross_mode" / "reviews" / "review.safe.json").write_text("{}", encoding="utf-8")
        (root / "cross_mode" / "apply_plans" / "apply_plan.safe.json").write_text("{}", encoding="utf-8")
        (root / "cross_mode" / "audit" / "audit.safe.json").write_text("{}", encoding="utf-8")
        (root / "backups").mkdir(parents=True, exist_ok=True)
        (root / "backups" / "backup_manifest.json").write_text("{}", encoding="utf-8")
        (root / "exports" / "diagnostics" / "preview.json").write_text(
            json.dumps({"redacted": True, "uploaded": False, "contains_secrets": False}, sort_keys=True),
            encoding="utf-8",
        )
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert _item(payload, "model_assignment_complete")["status"] == "warning"
    assert "model assignment config is missing" in str(_item(payload, "model_assignment_complete")["safe_summary"]).lower()
    _assert_safe_response(response.text)


def test_workflow_check_missing_backup_returns_warning(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        _complete_local_fixture(_project_root(repo), include_backup=False)
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "warning"
    assert _item(payload, "backup_restore_available")["status"] == "warning"
    assert "No safe backup metadata marker" in _item(payload, "backup_restore_available")["safe_summary"]
    _assert_safe_response(response.text)


def test_workflow_check_debug_disabled_does_not_expose_debug_data(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path, debug_enabled=False)
    try:
        _complete_local_fixture(_project_root(repo))
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert _item(payload, "debug_replay_available")["status"] == "disabled"
    assert "raw state_deltas" not in response.text
    _assert_safe_response(response.text)


def test_workflow_check_privacy_scans_backup_export_diagnostics_metadata(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        root = _project_root(repo)
        _complete_local_fixture(root)
        (root / "backups" / "unsafe_manifest.json").write_text(
            json.dumps({"contains_secrets": True, "note": "sk-live-v37-secret-must-not-echo-123456"}),
            encoding="utf-8",
        )
        response = client.get("/projects/demo/workflow-check")
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "missing"
    assert payload["privacy_boundaries_pass"] is False
    assert _item(payload, "privacy_boundaries_pass")["status"] == "missing"
    assert "sk-live-v37-secret-must-not-echo-123456" not in response.text
    _assert_safe_response(response.text)
