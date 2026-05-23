from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.backup_restore import BackupCreateRequest, BackupService, RestoreApplyRequest, RestoreDryRunRequest, RestoreService
from app.desktop.diagnostics_bundle import DiagnosticsBundleCreateRequest, DiagnosticsBundleService
from app.desktop.local_logs import LocalLogService
from app.desktop.recovery import RecoveryApplyRequest, RecoveryService
from app.desktop.workspaces import RecentProjectsService, WorkspaceService
from app.main import app
from app.session_store import InMemorySessionStore


def _client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "studio.db"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=f"sqlite:///{database_path}",
        llm_provider="openai",
        llm_api_key="sk-test-secret-that-must-not-appear",
        enable_debug_api=False,
        enable_authoring_api=True,
        enable_eval_api=True,
    )
    app.state.workspace_service = WorkspaceService(default_workspace=tmp_path)
    app.state.recent_projects_service = RecentProjectsService()
    return TestClient(app)


def test_local_studio_status_and_config_are_safe(tmp_path: Path) -> None:
    client = _client(tmp_path)

    status = client.get("/local-studio/status")
    config = client.get("/local-studio/config-summary")
    startup = client.get("/local-studio/startup-checks")

    assert status.status_code == 200
    assert config.status_code == 200
    assert startup.status_code == 200
    combined = status.text + config.text + startup.text
    assert "sk-test-secret-that-must-not-appear" not in combined
    assert "LLM_API_KEY" not in combined
    assert str(tmp_path) not in combined
    assert status.json()["local_only"] is True
    assert config.json()["provider_secrets_configured_count"] == 1


def test_backup_restore_dry_run_and_confirmed_apply_are_safe(tmp_path: Path) -> None:
    service = BackupService(tmp_path)
    request = BackupCreateRequest(project_id="demo", target_dir="backups")

    plan = service.create_backup_dry_run(request)

    assert plan.dry_run is True
    assert not (tmp_path / "backups").exists()
    assert ".env" in plan.excluded_items
    assert "API key" in plan.excluded_items

    try:
        service.create_backup(request)
    except ValueError as exc:
        assert "explicit_confirm" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("backup creation should require explicit confirm")

    created = service.create_backup(request.model_copy(update={"explicit_confirm": True}))
    assert created.created is True
    assert created.backup_path_summary
    assert "sk-" not in created.model_dump_json()
    assert ".env" in created.manifest.excluded_items

    restore = RestoreService(tmp_path, service)
    backup_path = next((tmp_path / "backups").glob("*.zip"))
    dry_run = restore.restore_dry_run(RestoreDryRunRequest(backup_path=str(backup_path), target_project_id="restored"))
    assert dry_run.dry_run is True
    assert not (tmp_path / "restored-projects" / "restored").exists()

    try:
        restore.restore_apply_confirmed(RestoreApplyRequest(backup_path=str(backup_path), target_project_id="restored"))
    except ValueError as exc:
        assert "explicit_confirm" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("restore apply should require explicit confirm")

    applied = restore.restore_apply_confirmed(
        RestoreApplyRequest(backup_path=str(backup_path), target_project_id="restored", explicit_confirm=True)
    )
    assert applied.restored is True
    assert (tmp_path / "restored-projects" / "restored").exists()


def test_local_log_viewer_redacts_and_rejects_unsafe_paths(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "desktop-backend.err.log").write_text(
        "Authorization: Bearer secret-token\nDATABASE_URL=postgres://user:pass@host/db\nOPENAI_API_KEY=sk-test-secret-that-must-not-appear\n",
        encoding="utf-8",
    )
    (tmp_path / "other.log").write_text("OPENAI_API_KEY=sk-test-secret-that-must-not-appear", encoding="utf-8")

    response = LocalLogService(tmp_path).list_safe_logs(limit=10)
    text = json.dumps([entry.model_dump(mode="json") for entry in response.logs])

    assert response.logs
    assert "sk-test-secret-that-must-not-appear" not in text
    assert "postgres://user:pass" not in text
    assert "Authorization: Bearer secret-token" not in text
    assert "other.log" not in text
    assert "[redacted-secret]" in text


def test_recovery_service_blocks_destructive_and_does_not_include_secrets() -> None:
    service = RecoveryService()
    issues = service.detect_recovery_issues(
        provider_secret_configured=False,
        database_configured=True,
        debug_enabled=False,
        quality_blockers=1,
    )
    plan = service.dry_run_recovery(issues)

    assert any(issue.issue_id == "provider_missing_secret" for issue in issues)
    assert "quality_gate_blockers" in plan.blockers
    assert "sk-" not in plan.model_dump_json()
    try:
        service.apply_safe_recovery_confirmed(issues, RecoveryApplyRequest(explicit_confirm=True, allow_destructive=True))
    except ValueError as exc:
        assert "destructive" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("destructive recovery should be blocked")


def test_diagnostics_bundle_preview_create_and_validate_are_safe(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "desktop-backend.err.log").write_text("OPENAI_API_KEY=sk-test-secret-that-must-not-appear", encoding="utf-8")
    service = DiagnosticsBundleService(tmp_path)
    request = DiagnosticsBundleCreateRequest(project_id="demo")

    preview = service.preview_bundle(request)

    assert preview.writes_file is False
    assert not (tmp_path / "exports").exists()
    assert ".env" in preview.manifest.excluded_sections
    assert "API key" in preview.manifest.excluded_sections

    created = service.create_bundle(request)
    bundle = next((tmp_path / "exports" / "diagnostics").glob("*.zip"))
    with zipfile.ZipFile(bundle, "r") as archive:
      payload = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())

    assert created.created is True
    assert "sk-test-secret-that-must-not-appear" not in payload
    assert ".env" in payload
    assert "raw state_deltas" in payload
    validation = service.validate_bundle(str(bundle))
    assert validation.valid is True


def test_local_studio_log_and_diagnostics_api_are_safe(tmp_path: Path) -> None:
    client = _client(tmp_path)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "desktop-backend.err.log").write_text("OPENAI_API_KEY=sk-test-secret-that-must-not-appear", encoding="utf-8")

    log_response = client.get("/local-studio/logs/recent")
    diagnostics = client.post("/local-studio/diagnostics/preview", json={"project_id": "demo"})

    assert log_response.status_code == 200
    assert diagnostics.status_code == 200
    combined = log_response.text + diagnostics.text
    assert "sk-test-secret-that-must-not-appear" not in combined
    assert "raw state_deltas" in diagnostics.text
