from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.config import Settings
from app.desktop.health import DesktopHealthCheckReport
from app.desktop.local_config import LocalConfigSummary
from app.desktop.studio_policy import redact_desktop_secret_text
from app.desktop.workspaces import ProjectWorkspace


class LocalStudioStatus(BaseModel):
    local_only: bool = True
    backend_running: bool = True
    app_version: str
    project_root_configured: bool
    database_configured: bool
    provider_profiles_count: int = 1
    provider_secrets_configured_count: int = 0
    debug_enabled: bool
    authoring_enabled: bool
    quality_api_enabled: bool
    current_workspace: ProjectWorkspace | None = None
    warnings: list[str] = Field(default_factory=list)
    safe_errors: list[str] = Field(default_factory=list)


class LocalStudioHealth(BaseModel):
    local_only: bool = True
    backend_running: bool = True
    app_version: str
    health: DesktopHealthCheckReport


class LocalStudioConfigSummary(BaseModel):
    local_only: bool = True
    app_version: str
    project_root_configured: bool
    database_configured: bool
    provider_profiles_count: int = 1
    provider_secrets_configured_count: int = 0
    debug_enabled: bool
    authoring_enabled: bool
    module_api_enabled: bool
    quality_api_enabled: bool
    config: LocalConfigSummary
    warnings: list[str] = Field(default_factory=list)


class LocalStudioStartupCheck(BaseModel):
    check_id: str
    label: str
    status: str
    safe_summary: str


class LocalStudioStartupChecks(BaseModel):
    local_only: bool = True
    generated_at: str
    checks: list[LocalStudioStartupCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LocalStudioRecentErrors(BaseModel):
    local_only: bool = True
    safe_errors: list[str] = Field(default_factory=list)


def build_local_studio_status(
    settings: Settings,
    *,
    workspace: ProjectWorkspace | None,
    app_version: str,
    recent_errors: list[str] | None = None,
) -> LocalStudioStatus:
    warnings: list[str] = []
    if not settings.database_url:
        warnings.append("database_not_configured")
    if settings.llm_provider.lower() == "openai" and not settings.llm_api_key:
        warnings.append("provider_secret_missing")
    return LocalStudioStatus(
        app_version=app_version,
        project_root_configured=workspace is not None,
        database_configured=bool(settings.database_url),
        provider_profiles_count=1,
        provider_secrets_configured_count=1 if bool(settings.llm_api_key) else 0,
        debug_enabled=bool(settings.enable_debug_api),
        authoring_enabled=bool(settings.enable_authoring_api),
        quality_api_enabled=bool(settings.enable_eval_api or settings.enable_debug_api or settings.enable_playtest_api),
        current_workspace=workspace,
        warnings=warnings,
        safe_errors=_redact_errors(recent_errors or []),
    )


def build_local_studio_config_summary(
    settings: Settings,
    config: LocalConfigSummary,
    *,
    app_version: str,
    workspace: ProjectWorkspace | None,
) -> LocalStudioConfigSummary:
    warnings: list[str] = []
    if workspace is None:
        warnings.append("workspace_not_selected")
    if not settings.database_url:
        warnings.append("database_not_configured")
    return LocalStudioConfigSummary(
        app_version=app_version,
        project_root_configured=workspace is not None,
        database_configured=bool(settings.database_url),
        provider_profiles_count=1,
        provider_secrets_configured_count=1 if bool(settings.llm_api_key) else 0,
        debug_enabled=bool(settings.enable_debug_api),
        authoring_enabled=bool(settings.enable_authoring_api),
        module_api_enabled=bool(getattr(settings, "enable_module_api", False)),
        quality_api_enabled=bool(settings.enable_eval_api or settings.enable_debug_api or settings.enable_playtest_api),
        config=config,
        warnings=warnings,
    )


def build_startup_checks(settings: Settings, *, repo_root: Path) -> LocalStudioStartupChecks:
    checks = [
        LocalStudioStartupCheck(
            check_id="backend",
            label="Backend import",
            status="pass",
            safe_summary="Backend application module is available.",
        ),
        LocalStudioStartupCheck(
            check_id="database",
            label="Database configured",
            status="pass" if settings.database_url else "warning",
            safe_summary="Database URL is configured." if settings.database_url else "DATABASE_URL is missing.",
        ),
        LocalStudioStartupCheck(
            check_id="frontend_package",
            label="Frontend package",
            status="pass" if (repo_root / "frontend" / "package.json").exists() else "error",
            safe_summary="frontend/package.json is present.",
        ),
        LocalStudioStartupCheck(
            check_id="launcher_scripts",
            label="Launcher scripts",
            status="pass"
            if (repo_root / "scripts" / "start_local_studio.ps1").exists()
            and (repo_root / "scripts" / "start_local_studio.sh").exists()
            else "warning",
            safe_summary="Local launcher scripts are present or documented as optional.",
        ),
        LocalStudioStartupCheck(
            check_id="local_only",
            label="Local-only boundary",
            status="pass",
            safe_summary="No account, cloud sync, or online marketplace is required.",
        ),
    ]
    return LocalStudioStartupChecks(generated_at=datetime.now(UTC).isoformat(), checks=checks)


def _redact_errors(errors: list[str]) -> list[str]:
    return [redact_desktop_secret_text(error).text for error in errors[:20]]


def safe_model_dump(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value
