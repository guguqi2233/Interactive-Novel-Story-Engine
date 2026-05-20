from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import Settings
from app.desktop.local_config import LocalConfigIssue, LocalConfigManager, LocalConfigSummary
from app.desktop.workspaces import ProjectWorkspace, WorkspaceService


DesktopHealthStatus = Literal["pass", "warning", "error"]


class DesktopHealthCheckItem(BaseModel):
    check_id: str
    label: str
    status: DesktopHealthStatus
    message: str
    safe_detail: str | None = None


class DesktopHealthCheckReport(BaseModel):
    local_only: bool = True
    overall_status: DesktopHealthStatus
    checks: list[DesktopHealthCheckItem] = Field(default_factory=list)
    provider_config: LocalConfigSummary
    current_workspace: ProjectWorkspace | None = None
    recent_errors: list[str] = Field(default_factory=list)


class DesktopHealthCheckService:
    """Safe local desktop diagnostics.

    Health checks never return raw env, API keys, hidden facts, or full local
    paths. They do not call providers and do not mutate GameState.
    """

    def __init__(
        self,
        settings: Settings,
        workspace_service: WorkspaceService,
        *,
        database_check: Callable[[], None] | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.settings = settings
        self.workspace_service = workspace_service
        self.database_check = database_check
        self.project_root = (project_root or Path.cwd()).resolve()
        self.config_manager = LocalConfigManager(settings)

    def run(self) -> DesktopHealthCheckReport:
        checks = [
            self._backend_check(),
            self._frontend_check(),
            self._database_check(),
            self._config_check(),
            self._workspace_check(),
            self._worlds_directory_check(),
            self._authoring_api_check(),
            self._debug_api_check(),
            self._provider_check(),
            self._recent_errors_check(),
        ]
        return DesktopHealthCheckReport(
            overall_status=_overall_status(checks),
            checks=checks,
            provider_config=_health_safe_config_summary(self.config_manager.get_safe_summary()),
            current_workspace=self.workspace_service.get_current_workspace(),
            recent_errors=[],
        )

    def _backend_check(self) -> DesktopHealthCheckItem:
        return DesktopHealthCheckItem(
            check_id="backend_alive",
            label="Backend alive",
            status="pass",
            message="Backend process responded to the local Studio health check.",
        )

    def _frontend_check(self) -> DesktopHealthCheckItem:
        return DesktopHealthCheckItem(
            check_id="frontend_reachable",
            label="Frontend reachable",
            status="warning",
            message="Frontend reachability is checked by the browser shell; backend reports this as optional.",
        )

    def _database_check(self) -> DesktopHealthCheckItem:
        if not self.settings.database_url:
            return DesktopHealthCheckItem(
                check_id="database_reachable",
                label="Database reachable",
                status="error",
                message="DATABASE_URL is not configured.",
                safe_detail="not configured",
            )
        try:
            if self.database_check is not None:
                self.database_check()
        except Exception:
            return DesktopHealthCheckItem(
                check_id="database_reachable",
                label="Database reachable",
                status="error",
                message="Database check failed.",
                safe_detail="configured but unreachable",
            )
        return DesktopHealthCheckItem(
            check_id="database_reachable",
            label="Database reachable",
            status="pass",
            message="Database configuration is present and the local repository responded.",
            safe_detail="configured",
        )

    def _config_check(self) -> DesktopHealthCheckItem:
        issues = self.config_manager.validate_config()
        errors = [issue for issue in issues if issue.severity == "error"]
        warnings = [issue for issue in issues if issue.severity == "warning"]
        if errors:
            return DesktopHealthCheckItem(
                check_id="config_summary_valid",
                label="Config summary valid",
                status="error",
                message=f"{len(errors)} blocking local config issue(s) found.",
            )
        if warnings:
            return DesktopHealthCheckItem(
                check_id="config_summary_valid",
                label="Config summary valid",
                status="warning",
                message=f"{len(warnings)} local config warning(s) found.",
            )
        return DesktopHealthCheckItem(
            check_id="config_summary_valid",
            label="Config summary valid",
            status="pass",
            message="Safe local config summary has no blocking issues.",
        )

    def _workspace_check(self) -> DesktopHealthCheckItem:
        workspace = self.workspace_service.get_current_workspace()
        if workspace is None:
            return DesktopHealthCheckItem(
                check_id="current_workspace_valid",
                label="Current workspace valid",
                status="warning",
                message="No current workspace is selected.",
            )
        if workspace.safe_status != "ok":
            return DesktopHealthCheckItem(
                check_id="current_workspace_valid",
                label="Current workspace valid",
                status="warning",
                message=f"Current workspace status is {workspace.safe_status}.",
                safe_detail=workspace.path_redacted,
            )
        return DesktopHealthCheckItem(
            check_id="current_workspace_valid",
            label="Current workspace valid",
            status="pass",
            message="Current workspace reference is available.",
            safe_detail=workspace.path_redacted,
        )

    def _worlds_directory_check(self) -> DesktopHealthCheckItem:
        workspace = self.workspace_service.get_current_workspace()
        if workspace is None:
            return DesktopHealthCheckItem(
                check_id="worlds_directory_valid",
                label="Worlds directory valid",
                status="warning",
                message="Worlds directory cannot be checked without a selected workspace.",
            )
        if workspace.world_count <= 0:
            return DesktopHealthCheckItem(
                check_id="worlds_directory_valid",
                label="Worlds directory valid",
                status="warning",
                message="No world manifests were found in the selected workspace.",
                safe_detail=workspace.path_redacted,
            )
        return DesktopHealthCheckItem(
            check_id="worlds_directory_valid",
            label="Worlds directory valid",
            status="pass",
            message=f"{workspace.world_count} world pack(s) found.",
            safe_detail=workspace.path_redacted,
        )

    def _authoring_api_check(self) -> DesktopHealthCheckItem:
        return DesktopHealthCheckItem(
            check_id="authoring_api_state",
            label="Authoring API state",
            status="pass" if self.settings.enable_authoring_api else "warning",
            message="Authoring API enabled." if self.settings.enable_authoring_api else "Authoring API is disabled.",
        )

    def _debug_api_check(self) -> DesktopHealthCheckItem:
        return DesktopHealthCheckItem(
            check_id="debug_api_state",
            label="Debug API state",
            status="pass" if self.settings.enable_debug_api else "warning",
            message="Debug API enabled." if self.settings.enable_debug_api else "Debug API is disabled.",
        )

    def _provider_check(self) -> DesktopHealthCheckItem:
        issues = self.config_manager.check_provider_config()
        errors = [issue for issue in issues if issue.severity == "error"]
        warnings = [issue for issue in issues if issue.severity == "warning"]
        provider = self.settings.llm_provider.strip().lower()
        if errors:
            return DesktopHealthCheckItem(
                check_id="provider_config_safe_summary",
                label="Provider config safe summary",
                status="error",
                message=f"Provider {provider} has blocking configuration issues.",
            )
        if warnings:
            return DesktopHealthCheckItem(
                check_id="provider_config_safe_summary",
                label="Provider config safe summary",
                status="warning",
                message=f"Provider {provider} has non-secret configuration warnings.",
            )
        return DesktopHealthCheckItem(
            check_id="provider_config_safe_summary",
            label="Provider config safe summary",
            status="pass",
            message=f"Provider {provider} safe summary is valid.",
        )

    def _recent_errors_check(self) -> DesktopHealthCheckItem:
        return DesktopHealthCheckItem(
            check_id="recent_errors",
            label="Recent errors",
            status="pass",
            message="No recent error cache is attached to the desktop health check.",
        )


def _overall_status(checks: list[DesktopHealthCheckItem]) -> DesktopHealthStatus:
    if any(check.status == "error" for check in checks):
        return "error"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "pass"


def _health_safe_config_summary(summary: LocalConfigSummary) -> LocalConfigSummary:
    return summary.model_copy(
        update={
            "issues": [
                LocalConfigIssue(
                    code=issue.code,
                    severity=issue.severity,
                    message=issue.message,
                    safe_field="provider_config",
                )
                for issue in summary.issues
            ]
        }
    )
