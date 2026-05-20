from __future__ import annotations

import importlib.util
import re
import shutil
import socket
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import Settings
from app.desktop.crash_reports import CrashReportService
from app.desktop.workspaces import WorkspaceService


StartupDiagnosticStatus = Literal["pass", "warning", "error"]


class StartupDiagnosticItem(BaseModel):
    check_id: str
    label: str
    status: StartupDiagnosticStatus
    message: str
    safe_detail: str | None = None


class StartupDiagnosticReport(BaseModel):
    local_only: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_status: StartupDiagnosticStatus
    checks: list[StartupDiagnosticItem]
    recommended_actions: list[str] = Field(default_factory=list)


CommandChecker = Callable[[str], bool]
PortChecker = Callable[[str, int], bool]


class StartupDiagnosticsService:
    def __init__(
        self,
        *,
        project_root: Path,
        settings: Settings,
        workspace_service: WorkspaceService | None = None,
        crash_report_service: CrashReportService | None = None,
        command_checker: CommandChecker | None = None,
        port_checker: PortChecker | None = None,
        backend_ports: Sequence[int] = (8000,),
        frontend_ports: Sequence[int] = (5173,),
    ) -> None:
        self.project_root = project_root.resolve()
        self.settings = settings
        self.workspace_service = workspace_service
        self.crash_report_service = crash_report_service
        self.command_checker = command_checker or _default_command_checker
        self.port_checker = port_checker or _default_port_checker
        self.backend_ports = tuple(backend_ports)
        self.frontend_ports = tuple(frontend_ports)

    def run(self) -> StartupDiagnosticReport:
        checks = [
            self._check_python_available(),
            self._check_node_npm_available(),
            self._check_backend_deps(),
            self._check_frontend_deps(),
            self._check_ports_available(),
            self._check_env_exists(),
            self._check_database_path(),
            self._check_workspace_valid(),
            self._check_frontend_build_exists(),
            self._check_previous_crash_reports(),
        ]
        overall_status: StartupDiagnosticStatus = "pass"
        if any(check.status == "error" for check in checks):
            overall_status = "error"
        elif any(check.status == "warning" for check in checks):
            overall_status = "warning"
        return StartupDiagnosticReport(
            overall_status=overall_status,
            checks=checks,
            recommended_actions=self._recommended_actions(checks),
        )

    def _check_python_available(self) -> StartupDiagnosticItem:
        if not self.command_checker("python") and not sys.executable:
            return _item("python_available", "Python available", "error", "Python was not found on PATH.")
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info < (3, 11):
            return _item(
                "python_available",
                "Python available",
                "error",
                "Python 3.11+ is required.",
                f"detected Python {version}",
            )
        return _item("python_available", "Python available", "pass", "Python is available.", f"detected Python {version}")

    def _check_node_npm_available(self) -> StartupDiagnosticItem:
        node_ok = self.command_checker("node")
        npm_ok = self.command_checker("npm") or self.command_checker("npm.cmd")
        if node_ok and npm_ok:
            return _item("node_npm_available", "Node/npm available", "pass", "Node and npm are available.")
        missing = []
        if not node_ok:
            missing.append("node")
        if not npm_ok:
            missing.append("npm")
        return _item(
            "node_npm_available",
            "Node/npm available",
            "warning",
            "Node/npm command availability check failed.",
            f"missing: {', '.join(missing)}",
        )

    def _check_backend_deps(self) -> StartupDiagnosticItem:
        required_modules = ("fastapi", "pydantic", "uvicorn")
        missing = [name for name in required_modules if importlib.util.find_spec(name) is None]
        if missing:
            return _item(
                "backend_deps_installed",
                "Backend dependencies installed",
                "error",
                "Backend dependencies are missing.",
                f"missing: {', '.join(missing)}",
            )
        return _item("backend_deps_installed", "Backend dependencies installed", "pass", "Backend dependencies are importable.")

    def _check_frontend_deps(self) -> StartupDiagnosticItem:
        package_json = self.project_root / "frontend" / "package.json"
        node_modules = self.project_root / "frontend" / "node_modules"
        if not package_json.exists():
            return _item("frontend_deps_installed", "Frontend dependencies installed", "error", "frontend/package.json was not found.")
        if not node_modules.exists():
            return _item(
                "frontend_deps_installed",
                "Frontend dependencies installed",
                "warning",
                "frontend/node_modules was not found.",
                "run npm install in frontend/",
            )
        return _item("frontend_deps_installed", "Frontend dependencies installed", "pass", "Frontend dependencies appear installed.")

    def _check_ports_available(self) -> StartupDiagnosticItem:
        busy: list[str] = []
        for port in self.backend_ports:
            if not self.port_checker("127.0.0.1", port):
                busy.append(f"backend:{port}")
        for port in self.frontend_ports:
            if not self.port_checker("127.0.0.1", port):
                busy.append(f"frontend:{port}")
        if busy:
            return _item(
                "ports_available",
                "Ports available",
                "warning",
                "One or more default local ports are already in use.",
                f"busy: {', '.join(busy)}",
            )
        return _item("ports_available", "Ports available", "pass", "Default local ports are available.")

    def _check_env_exists(self) -> StartupDiagnosticItem:
        if (self.project_root / ".env").exists():
            return _item("env_exists", ".env exists", "pass", ".env exists. Contents were not read.")
        return _item(
            "env_exists",
            ".env exists",
            "warning",
            ".env was not found. The launcher can continue with safe local defaults.",
            "copy .env.example to .env only if local customization is needed",
        )

    def _check_database_path(self) -> StartupDiagnosticItem:
        database_url = self.settings.database_url or ""
        if not database_url:
            return _item("database_path_accessible", "Database path accessible", "error", "DATABASE_URL is empty.")
        if database_url.startswith("sqlite:///"):
            raw_path = database_url.removeprefix("sqlite:///")
            database_path = Path(raw_path)
            if not database_path.is_absolute():
                database_path = self.project_root / database_path
            parent = database_path.parent
            if parent.exists() and parent.is_dir():
                return _item(
                    "database_path_accessible",
                    "Database path accessible",
                    "pass",
                    "SQLite database parent directory is accessible.",
                    _redact_path(parent),
                )
            return _item(
                "database_path_accessible",
                "Database path accessible",
                "warning",
                "SQLite database parent directory does not exist.",
                _redact_path(parent),
            )
        return _item(
            "database_path_accessible",
            "Database path accessible",
            "warning",
            "Non-SQLite DATABASE_URL is configured; startup diagnostics did not connect to it.",
            "database URL redacted",
        )

    def _check_workspace_valid(self) -> StartupDiagnosticItem:
        if self.workspace_service is None:
            return _item("workspace_valid", "Workspace valid", "warning", "No workspace service was provided.")
        current = self.workspace_service.get_current_workspace()
        if current is None:
            return _item("workspace_valid", "Workspace valid", "warning", "No current workspace is selected.")
        if current.safe_status != "ok":
            return _item("workspace_valid", "Workspace valid", "warning", "Current workspace is not fully valid.", current.safe_status)
        return _item(
            "workspace_valid",
            "Workspace valid",
            "pass",
            "Current workspace summary is valid.",
            f"{current.name}; worlds={current.world_count}",
        )

    def _check_frontend_build_exists(self) -> StartupDiagnosticItem:
        build_path = self.project_root / "frontend" / "dist" / "index.html"
        if build_path.exists():
            return _item("frontend_build_exists", "Frontend build exists", "pass", "Built frontend is present.")
        return _item(
            "frontend_build_exists",
            "Frontend build exists",
            "warning",
            "Built frontend was not found. This is only required when using built preview mode.",
        )

    def _check_previous_crash_reports(self) -> StartupDiagnosticItem:
        if self.crash_report_service is None:
            return _item("previous_crash_reports", "Previous crash reports", "pass", "Crash report service was not configured.")
        report_list = self.crash_report_service.list_crash_reports()
        count = len(report_list.reports) if hasattr(report_list, "reports") else len(report_list)
        if count:
            return _item(
                "previous_crash_reports",
                "Previous crash reports",
                "warning",
                "Previous local crash reports exist.",
                f"count={count}",
            )
        return _item("previous_crash_reports", "Previous crash reports", "pass", "No previous crash reports were found.")

    @staticmethod
    def _recommended_actions(checks: Sequence[StartupDiagnosticItem]) -> list[str]:
        actions: list[str] = []
        by_id = {check.check_id: check for check in checks}
        if by_id.get("env_exists") and by_id["env_exists"].status == "warning":
            actions.append("Create .env from .env.example only if you need custom local provider or database settings.")
        if by_id.get("frontend_deps_installed") and by_id["frontend_deps_installed"].status != "pass":
            actions.append("Run npm install inside frontend/ before starting the frontend dev server.")
        if by_id.get("ports_available") and by_id["ports_available"].status != "pass":
            actions.append("Stop the process using the busy port or start the studio with alternate ports.")
        return actions


def sanitize_startup_diagnostic_text(value: str) -> str:
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED_API_KEY]", value)
    redacted = re.sub(r"(?i)(api[_-]?key|llm_api_key|openai_api_key)\s*[:=]\s*[^,\s]+", r"\1=[REDACTED]", redacted)
    redacted = re.sub(r"(?i)(password=)[^@\s]+", r"\1[REDACTED]", redacted)
    return redacted


def _item(
    check_id: str,
    label: str,
    status: StartupDiagnosticStatus,
    message: str,
    safe_detail: str | None = None,
) -> StartupDiagnosticItem:
    return StartupDiagnosticItem(
        check_id=check_id,
        label=label,
        status=status,
        message=sanitize_startup_diagnostic_text(message),
        safe_detail=sanitize_startup_diagnostic_text(safe_detail) if safe_detail else None,
    )


def _default_command_checker(name: str) -> bool:
    return shutil.which(name) is not None


def _default_port_checker(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _redact_path(path: Path) -> str:
    parts = path.resolve().parts
    if len(parts) <= 2:
        return path.anchor or "[path]"
    return str(Path(parts[0], "...", parts[-1]))
