from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.crash_reports import CrashReportService
from app.desktop.startup_diagnostics import StartupDiagnosticsService
from app.desktop.studio_policy import BackupBundle, CrashReport, DesktopStudioPolicy
from app.desktop.update_notes import LocalUpdateNotesService
from app.desktop.workspaces import RecentProjectsService, WorkspaceService
from app.main import app
from app.session_store import InMemorySessionStore


FAKE_KEY = "sk-test-secret-that-must-not-appear"


def test_v17_desktop_boundary_redacts_config_frontend_backup_and_crash_data(tmp_path: Path) -> None:
    policy = DesktopStudioPolicy()
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'private' / 'world.db'}",
        llm_provider="openai",
        llm_api_key=FAKE_KEY,
    )

    safe_config = policy.build_safe_config_summary(settings)
    frontend_decision = policy.validate_frontend_config({"VITE_API_BASE_URL": "http://127.0.0.1:8000"})
    unsafe_frontend = policy.validate_frontend_config({"VITE_LLM_API_KEY": FAKE_KEY})
    backup_decision = policy.validate_backup_bundle(
        BackupBundle(
            file_paths=[
                "worlds/demo/manifest.yaml",
                ".env",
                "logs/backend.log",
                "cache/tmp.bin",
                "saves/run.sqlite",
            ],
            content_preview=f"LLM_API_KEY={FAKE_KEY}",
        )
    )
    crash = policy.sanitize_crash_report(
        CrashReport(
            title="startup failed",
            message=f"provider failed with LLM_API_KEY={FAKE_KEY}",
            raw_env={"LLM_API_KEY": FAKE_KEY},
            stack_trace=f"RuntimeError: {FAKE_KEY}",
        )
    )

    serialized = f"{safe_config.model_dump_json()} {crash}"
    assert safe_config.api_key_configured is True
    assert frontend_decision.allowed is True
    assert unsafe_frontend.allowed is False
    assert backup_decision.allowed is False
    assert "backup_contains_forbidden_file:.env" in backup_decision.blockers
    assert "backup_contains_secret_preview" in backup_decision.blockers
    assert FAKE_KEY not in serialized
    assert "raw_env_included': False" in str(crash)


def test_v17_launcher_diagnostics_scripts_and_packaging_safety_static_checks(tmp_path: Path) -> None:
    project_root = _make_workspace_project(tmp_path)
    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=Settings(database_url=f"sqlite:///{project_root / 'data' / 'app.db'}", llm_api_key=FAKE_KEY),
        workspace_service=WorkspaceService(default_workspace=project_root),
        command_checker=lambda _name: True,
        port_checker=lambda _host, port: port != 8000,
        backend_ports=(8000,),
        frontend_ports=(5173,),
    )

    report = service.run()
    scripts = [
        Path("scripts/start_local_studio.ps1").read_text(encoding="utf-8"),
        Path("scripts/start_local_studio.sh").read_text(encoding="utf-8"),
    ]
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    packaging_doc = Path("docs/DESKTOP_PACKAGING.md").read_text(encoding="utf-8")

    assert report.local_only is True
    assert any(check.check_id == "env_exists" and check.status == "warning" for check in report.checks)
    assert any(check.check_id == "ports_available" and check.status == "warning" for check in report.checks)
    assert FAKE_KEY not in report.model_dump_json()
    for script in scripts:
        assert "SkipStartupDiagnostics" in script or "skip-startup-diagnostics" in script
        assert FAKE_KEY not in script
        assert "sk-" not in script
    for expected in ["frontend/dist/", "desktop-dist/", "desktop_build/", "logs/", "crash-reports/", "backups/"]:
        assert expected in gitignore
    assert "Packaging Safety Checklist" in packaging_doc
    assert "No desktop workflow calls a real LLM provider" in packaging_doc


def test_v17_project_selector_recent_projects_and_path_redaction(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    first = _make_workspace(tmp_path / "first", "world_a")
    second = _make_workspace(tmp_path / "second", "world_b")

    first_added = client.post("/studio/workspaces", json={"path": str(first), "name": "First"}).json()
    second_added = client.post("/studio/workspaces", json={"path": str(second), "name": "Second"}).json()
    rejected = client.post("/studio/workspaces", json={"path": "../outside"})
    client.post("/studio/workspaces/select", json={"workspace_id": first_added["workspace_id"], "last_world_id": "world_a"})
    client.post("/studio/workspaces/select", json={"workspace_id": second_added["workspace_id"], "last_world_id": "world_b"})

    listed = client.get("/studio/workspaces")
    recent = client.get("/studio/recent-projects")

    assert listed.status_code == 200
    assert len(listed.json()["workspaces"]) >= 2
    assert rejected.status_code == 400
    assert [item["display_name"] for item in recent.json()["projects"][:2]] == ["Second", "First"]
    assert str(tmp_path) not in listed.text
    assert str(tmp_path) not in recent.text
    assert FAKE_KEY not in listed.text


def test_v17_config_update_notes_health_and_crash_reports_are_safe(tmp_path: Path) -> None:
    client = _make_client(tmp_path, debug_enabled=True)
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "V1_7_RELEASE_NOTES.md").write_text(
        f"# v1.7 Release Notes\nLocal notes with API key {FAKE_KEY}\n## Known Limitations\n- Local only.\n",
        encoding="utf-8",
    )
    update_notes = LocalUpdateNotesService(docs_root).build_index()
    report = app.state.crash_report_service.record_backend_exception(
        RuntimeError(f"boom Authorization: Bearer token123 {FAKE_KEY} raw_prompt='hidden text'"),
        context={"hidden_fact_text": "The secret shrine key is buried."},
    )

    config = client.get("/studio/config/summary")
    issues = client.get("/studio/config/issues")
    template = client.post("/studio/config/generate-template")
    health = client.get("/studio/health")
    crash = client.get(f"/debug/crash-reports/{report.id}")

    for response in [config, issues, template, health, crash]:
        assert response.status_code == 200
        assert FAKE_KEY not in response.text
        assert "raw env" not in response.text.lower()
    assert update_notes.local_only is True
    assert FAKE_KEY not in update_notes.model_dump_json()
    assert health.json()["local_only"] is True
    assert isinstance(crash.json()["context_safe_summary"], dict)
    assert "secret shrine" not in crash.text.lower()


def test_v17_workspace_templates_do_not_copy_env_or_overwrite_existing_workspace(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    blank_target = tmp_path / "blank"
    world_target = tmp_path / "world_project"
    duplicate = tmp_path / "duplicate"
    duplicate.mkdir()
    (duplicate / "README.md").write_text("existing", encoding="utf-8")

    templates = client.get("/studio/workspace-templates")
    blank = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "blank_studio", "path": str(blank_target), "name": "Blank"},
    )
    world = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "world_project", "path": str(world_target), "name": "World"},
    )
    duplicate_response = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "blank_studio", "path": str(duplicate), "name": "Duplicate"},
    )

    assert templates.status_code == 200
    assert {item["template_id"] for item in templates.json()["templates"]} >= {"blank_studio", "world_project"}
    assert blank.status_code == 200
    assert world.status_code == 200
    assert duplicate_response.status_code == 400
    assert not (blank_target / ".env").exists()
    assert not (world_target / ".env").exists()
    assert (world_target / "worlds" / "starter_world" / "manifest.yaml").exists()
    assert "LLM_API_KEY" not in (blank_target / "config.template.env").read_text(encoding="utf-8")


def test_v17_desktop_management_does_not_modify_game_state_or_call_real_provider(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    workspace = _make_workspace(tmp_path / "project", "demo_world")

    before_sessions = dict(getattr(app.state.session_store, "_sessions"))
    client.post("/studio/workspaces", json={"path": str(workspace), "name": "Demo"})
    client.get("/studio/config/summary")
    client.get("/studio/health")
    client.get("/studio/update-notes")
    after_sessions = dict(getattr(app.state.session_store, "_sessions"))

    assert before_sessions == after_sessions == {}
    assert app.state.settings.llm_provider == "mock"


def test_v17_cli_and_git_tracked_artifact_safety() -> None:
    cli = subprocess.run(
        [sys.executable, "-m", "backend.app.tools.startup_diagnostics", "--json"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    forbidden = [
        line
        for line in tracked.stdout.splitlines()
        if line == ".env"
        or line.startswith(("logs/", "crash-reports/", "backups/", "frontend/dist/", "desktop-dist/", "desktop_build/"))
        or line.endswith((".db", ".sqlite", ".sqlite3", ".log"))
        or "/node_modules/" in line
    ]

    assert cli.returncode in {0, 1}
    assert '"local_only": true' in cli.stdout
    assert FAKE_KEY not in cli.stdout
    assert "LLM_API_KEY" not in cli.stdout
    assert tracked.returncode == 0
    assert forbidden == []


def _make_client(tmp_path: Path, *, debug_enabled: bool = False) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v17.db")
    app.state.settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'v17.db'}",
        llm_provider="mock",
        llm_api_key=FAKE_KEY,
        enable_debug_api=debug_enabled,
        enable_authoring_api=False,
        enable_eval_api=False,
        enable_playtest_api=False,
    )
    app.state.workspace_service = WorkspaceService(default_workspace=tmp_path)
    app.state.recent_projects_service = RecentProjectsService()
    app.state.crash_report_service = CrashReportService()
    return TestClient(app)


def _make_workspace(root: Path, world_id: str = "demo_world") -> Path:
    workspace = root / "workspace"
    world = workspace / "worlds" / world_id
    world.mkdir(parents=True)
    (world / "manifest.yaml").write_text(f"id: {world_id}\nname: Demo\n", encoding="utf-8")
    return workspace


def _make_workspace_project(root: Path) -> Path:
    (root / "frontend").mkdir(parents=True)
    (root / "frontend" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
    (root / "frontend" / "node_modules").mkdir()
    (root / "worlds" / "demo_world").mkdir(parents=True)
    (root / "worlds" / "demo_world" / "manifest.yaml").write_text("id: demo_world\nname: Demo\n", encoding="utf-8")
    return root
