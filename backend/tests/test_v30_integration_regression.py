from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.backup_restore import (
    BackupCreateRequest,
    BackupService,
    RestoreApplyRequest,
    RestoreDryRunRequest,
    RestoreService,
)
from app.desktop.diagnostics_bundle import DiagnosticsBundleCreateRequest, DiagnosticsBundleService
from app.desktop.local_logs import LocalLogService
from app.desktop.recovery import RecoveryService
from app.desktop.workspaces import RecentProjectsService, WorkspaceService
from app.main import app
from app.session_store import InMemorySessionStore


FAKE_SECRET = "sk-test-v30-integration-secret-must-not-appear"
HIDDEN_TEXT = "hidden integration fact must not appear"
MATURE_TEXT = "mature private integration note must not appear"


def _client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "studio.db"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=f"sqlite:///{database_path}",
        llm_provider="local_stub",
        llm_api_key=None,
        enable_debug_api=False,
        enable_authoring_api=True,
        enable_module_api=True,
        enable_eval_api=True,
    )
    app.state.workspace_service = WorkspaceService(default_workspace=tmp_path)
    app.state.recent_projects_service = RecentProjectsService()
    return TestClient(app)


def _assert_safe_text(text: str, tmp_path: Path) -> None:
    forbidden = [
        FAKE_SECRET,
        "OPENAI_API_KEY=",
        "LLM_API_KEY=",
        "Authorization: Bearer",
        "postgres://user:pass",
        HIDDEN_TEXT,
        MATURE_TEXT,
        str(tmp_path),
    ]
    for needle in forbidden:
        assert needle not in text


def test_v30_local_studio_backend_endpoints_return_safe_summaries(tmp_path: Path) -> None:
    client = _client(tmp_path)

    workspace = client.get("/studio/workspaces").json()["workspaces"][0]
    select_response = client.post("/studio/workspaces/select", json={"workspace_id": workspace["workspace_id"]})
    assert select_response.status_code == 200

    responses = [
        client.get("/local-studio/status"),
        client.get("/local-studio/config-summary"),
        client.get("/local-studio/health"),
        client.get("/local-studio/startup-checks"),
        client.get("/local-studio/recent-errors"),
        client.get("/studio/recent-projects"),
        client.get("/local-studio/recovery/issues"),
        client.post("/local-studio/recovery/plan"),
    ]

    assert all(response.status_code == 200 for response in responses)
    combined = "\n".join(response.text for response in responses)
    _assert_safe_text(combined, tmp_path)
    assert responses[0].json()["local_only"] is True
    assert responses[1].json()["provider_secrets_configured_count"] == 0
    assert responses[5].json()["projects"]
    assert "Current Workspace" in combined


def test_v30_backup_restore_integration_filters_and_requires_confirmation(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY={FAKE_SECRET}\n", encoding="utf-8")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "local.log").write_text(FAKE_SECRET, encoding="utf-8")
    (tmp_path / "cache").mkdir()
    service = BackupService(tmp_path)
    request = BackupCreateRequest(project_id="integration_project", target_dir="backups")

    dry_run = service.create_backup_dry_run(request)

    assert dry_run.dry_run is True
    assert not (tmp_path / "backups").exists()
    assert ".env" in dry_run.excluded_items
    assert "API key" in dry_run.excluded_items
    assert "mature/private content" in dry_run.excluded_items

    try:
        service.create_backup(request)
    except ValueError as exc:
        assert "explicit_confirm" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("backup creation must require explicit confirmation")

    created = service.create_backup(request.model_copy(update={"explicit_confirm": True}))
    backup_path = next((tmp_path / "backups").glob("*.zip"))
    with zipfile.ZipFile(backup_path, "r") as archive:
        names = archive.namelist()
        payload = "\n".join(archive.read(name).decode("utf-8") for name in names)

    assert created.created is True
    assert ".env" not in names
    assert "logs/local.log" not in names
    _assert_safe_text(payload, tmp_path)
    assert "mature/private content" in created.manifest.excluded_items

    restore = RestoreService(tmp_path, service)
    dry_restore = restore.restore_dry_run(
        RestoreDryRunRequest(backup_path=str(backup_path), target_project_id="restored_project")
    )
    assert dry_restore.dry_run is True
    assert not (tmp_path / "restored-projects" / "restored_project").exists()

    try:
        restore.restore_apply_confirmed(
            RestoreApplyRequest(backup_path=str(backup_path), target_project_id="restored_project")
        )
    except ValueError as exc:
        assert "explicit_confirm" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("restore apply must require explicit confirmation")

    corrupted = tmp_path / "backups" / "corrupted.zip"
    with zipfile.ZipFile(corrupted, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("project_safe_summary.json", "{}")
    try:
        service.validate_backup(str(corrupted))
    except ValueError as exc:
        assert "manifest" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("corrupted backup must be rejected")


def test_v30_diagnostics_and_logs_do_not_write_or_leak_by_default(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "desktop-backend.err.log").write_text(
        "\n".join(
            [
                f"OPENAI_API_KEY={FAKE_SECRET}",
                "Authorization: Bearer secret-token",
                "DATABASE_URL=postgres://user:pass@host/db",
                f"hidden fact: {HIDDEN_TEXT}",
                f"mature/private content: {MATURE_TEXT}",
                "raw state_deltas: [{\"op\":\"replace\"}]",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "unsafe.log").write_text(f"OPENAI_API_KEY={FAKE_SECRET}", encoding="utf-8")

    log_response = LocalLogService(tmp_path).list_safe_logs(limit=20)
    log_payload = json.dumps([entry.model_dump(mode="json") for entry in log_response.logs])

    assert log_response.logs
    _assert_safe_text(log_payload, tmp_path)
    assert "unsafe.log" not in log_payload
    assert "[redacted-secret]" in log_payload
    assert any(entry.redacted for entry in log_response.logs)

    diagnostics = DiagnosticsBundleService(tmp_path)
    preview = diagnostics.preview_bundle(DiagnosticsBundleCreateRequest(project_id="integration_project"))

    assert preview.writes_file is False
    assert not (tmp_path / "exports").exists()
    assert ".env" in preview.manifest.excluded_sections
    assert "mature/private content" in preview.manifest.excluded_sections

    created = diagnostics.create_bundle(DiagnosticsBundleCreateRequest(project_id="integration_project"))
    bundle_path = next((tmp_path / "exports" / "diagnostics").glob("*.zip"))
    with zipfile.ZipFile(bundle_path, "r") as archive:
        payload = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())

    assert created.created is True
    _assert_safe_text(payload, tmp_path)
    assert "raw state_deltas" in payload
    assert diagnostics.validate_bundle(str(bundle_path)).valid is True


def test_v30_recovery_and_recent_projects_reports_are_secret_safe(tmp_path: Path) -> None:
    workspace_service = WorkspaceService(default_workspace=tmp_path)
    workspace = workspace_service.get_current_workspace()
    assert workspace is not None
    recent = RecentProjectsService()
    recent.record_opened_project(workspace, last_world_id="mist_valley")
    recent_payload = json.dumps([entry.model_dump(mode="json") for entry in recent.list_recent_projects()])

    _assert_safe_text(recent_payload, tmp_path)
    assert "mist_valley" in recent_payload
    assert "path_redacted" in recent_payload

    recovery = RecoveryService()
    issues = recovery.detect_recovery_issues(
        provider_secret_configured=False,
        database_configured=True,
        debug_enabled=False,
        quality_blockers=2,
    )
    plan = recovery.dry_run_recovery(issues)
    plan_payload = plan.model_dump_json()

    _assert_safe_text(plan_payload, tmp_path)
    assert "provider_missing_secret" in plan_payload
    assert "quality_gate_blockers" in plan.blockers
    assert plan.local_only is True


def test_v30_frontend_local_studio_surfaces_and_secret_boundaries_are_static_safe() -> None:
    root = Path(__file__).resolve().parents[2]
    app_tsx = (root / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    api_ts = (root / "frontend" / "src" / "api.ts").read_text(encoding="utf-8")
    package_json = json.loads((root / "frontend" / "package.json").read_text(encoding="utf-8"))
    ux_check = (root / "frontend" / "scripts" / "check-v30-local-studio-ux.mjs").read_text(encoding="utf-8")

    required_surfaces = [
        "Local Launcher / Startup Status",
        "Project Picker",
        "Recent Projects",
        "Local Config Wizard",
        "Provider Setup Wizard",
        "Desktop Health Check",
        "One-Click Quality Gate",
        "Backup / Restore Wizard",
        "Error Recovery Wizard",
        "Local Log Viewer",
        "Diagnostics Bundle UI",
        "Offline Help Center",
        "First-Run Onboarding",
        "Settings / Preferences Sections",
    ]
    for surface in required_surfaces:
        assert surface in app_tsx or surface in ux_check

    assert "check:v30-ux" in package_json["scripts"]
    combined = app_tsx + api_ts
    assert 'name="api_key"' not in combined
    assert "plaintext API key" in combined
    assert "api_key_env" in combined
    assert "secret_ref" in combined
    assert "/local-studio/status" in api_ts
    assert "/local-studio/backups/dry-run" in api_ts
    assert "/local-studio/diagnostics/preview" in api_ts

    dependencies = package_json.get("dependencies", {}) | package_json.get("devDependencies", {})
    large_ui_deps = {"@mui/material", "antd", "chakra-ui", "@blueprintjs/core", "semantic-ui-react"}
    assert not large_ui_deps.intersection(dependencies)


def test_v30_scripts_docs_and_world_boundary_static_checks() -> None:
    root = Path(__file__).resolve().parents[2]
    ps1 = (root / "scripts" / "start_local_studio.ps1").read_text(encoding="utf-8")
    sh = (root / "scripts" / "start_local_studio.sh").read_text(encoding="utf-8")
    packaging = (root / "docs" / "DESKTOP_PACKAGING.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    desktop_files = [
        root / "backend" / "app" / "desktop" / "local_studio.py",
        root / "backend" / "app" / "desktop" / "backup_restore.py",
        root / "backend" / "app" / "desktop" / "recovery.py",
        root / "backend" / "app" / "desktop" / "local_logs.py",
        root / "backend" / "app" / "desktop" / "diagnostics_bundle.py",
    ]

    assert "Local-first: no account, no cloud sync, no online marketplace, no telemetry upload." in ps1
    assert "Local-first: no account, no cloud sync, no online marketplace, no telemetry upload." in sh
    assert "VITE_API_BASE_URL" in ps1 + sh
    assert FAKE_SECRET not in ps1 + sh + packaging + readme

    for required_exclusion in [
        ".env",
        "API keys",
        "local secrets",
        "database files",
        "logs",
        "caches",
        "node_modules",
        "frontend/dist",
        "desktop build outputs",
        "mature/private content",
        "crash reports",
    ]:
        assert required_exclusion in packaging

    assert "v3.0: Local Desktop Studio Polish" in readme
    assert "It does not implement accounts, cloud sync, online" in readme
    assert "marketplaces, remote package auto-download" in readme

    desktop_source = "\n".join(path.read_text(encoding="utf-8") for path in desktop_files)
    assert "from app.core.world_state import GameState" not in desktop_source
    assert "StateDelta(" not in desktop_source
    assert "EventLog(" not in desktop_source
    assert "requests." not in desktop_source
    assert "httpx." not in desktop_source
