from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.config import Settings
from app.desktop.startup_diagnostics import StartupDiagnosticsService
from app.desktop.workspaces import WorkspaceService


def _make_project_root(root: Path) -> Path:
    (root / "frontend").mkdir()
    (root / "frontend" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
    (root / "frontend" / "node_modules").mkdir()
    (root / "worlds" / "demo_world").mkdir(parents=True)
    (root / "worlds" / "demo_world" / "manifest.yaml").write_text("id: demo_world\nname: Demo\n", encoding="utf-8")
    return root


def test_startup_diagnostics_report_schema(tmp_path: Path) -> None:
    project_root = _make_project_root(tmp_path)
    (project_root / ".env").write_text("# local test env\n", encoding="utf-8")
    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=Settings(database_url=f"sqlite:///{project_root / 'data' / 'app.db'}"),
        workspace_service=WorkspaceService(default_workspace=project_root),
        command_checker=lambda _name: True,
        port_checker=lambda _host, _port: True,
    )

    report = service.run()

    assert report.local_only is True
    assert report.overall_status in {"pass", "warning"}
    assert any(check.check_id == "python_available" for check in report.checks)
    assert any(check.check_id == "workspace_valid" for check in report.checks)


def test_startup_diagnostics_missing_env_warning(tmp_path: Path) -> None:
    project_root = _make_project_root(tmp_path)
    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=Settings(database_url=f"sqlite:///{project_root / 'app.db'}"),
        workspace_service=WorkspaceService(default_workspace=project_root),
        command_checker=lambda _name: True,
        port_checker=lambda _host, _port: True,
    )

    report = service.run()

    assert any(check.check_id == "env_exists" and check.status == "warning" for check in report.checks)
    assert any(".env.example" in action for action in report.recommended_actions)


def test_startup_diagnostics_port_check_can_be_mocked(tmp_path: Path) -> None:
    project_root = _make_project_root(tmp_path)

    def fake_port_checker(_host: str, port: int) -> bool:
        return port != 8000

    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=Settings(database_url=f"sqlite:///{project_root / 'app.db'}"),
        workspace_service=WorkspaceService(default_workspace=project_root),
        command_checker=lambda _name: True,
        port_checker=fake_port_checker,
        backend_ports=(8000,),
        frontend_ports=(5173,),
    )

    report = service.run()

    ports_check = next(check for check in report.checks if check.check_id == "ports_available")
    assert ports_check.status == "warning"
    assert ports_check.safe_detail == "busy: backend:8000"


def test_startup_diagnostics_no_api_key_leakage(tmp_path: Path) -> None:
    project_root = _make_project_root(tmp_path)
    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=Settings(
            database_url="postgresql://user:secret-password@localhost/world",
            llm_api_key="sk-test-secret-that-must-not-appear",
            llm_provider="openai",
        ),
        workspace_service=WorkspaceService(default_workspace=project_root),
        command_checker=lambda _name: True,
        port_checker=lambda _host, _port: True,
    )

    payload = service.run().model_dump_json()

    assert "sk-test-secret-that-must-not-appear" not in payload
    assert "secret-password" not in payload
    assert "raw env" not in payload.lower()


def test_startup_diagnostics_cli_json(tmp_path: Path) -> None:
    project_root = _make_project_root(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.tools.startup_diagnostics",
            "--project-root",
            str(project_root),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode in {0, 1}
    assert "sk-" not in result.stdout
    assert "api_key" not in result.stdout.lower()
    payload = json.loads(result.stdout)
    assert payload["local_only"] is True
    assert "checks" in payload
