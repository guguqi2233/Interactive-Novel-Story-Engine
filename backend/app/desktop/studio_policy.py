from __future__ import annotations

import re
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Mapping

from pydantic import BaseModel, Field

from app.config import Settings


class DesktopPrivacyClass(StrEnum):
    SAFE = "safe"
    LOCAL_PRIVATE = "local_private"
    SECRET = "secret"
    DEBUG_ONLY = "debug_only"


class DesktopComponent(StrEnum):
    DESKTOP_SHELL = "desktop_shell"
    BACKEND_PROCESS = "backend_process"
    FRONTEND_APP = "frontend_app"
    LOCAL_WORKSPACE = "local_workspace"


class DesktopBoundaryDecision(BaseModel):
    allowed: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DesktopSafeConfigSummary(BaseModel):
    app_name: str
    app_env: str
    llm_provider: str
    llm_model: str
    api_key_configured: bool
    database_configured: bool
    database_path_hint: str
    authoring_api_enabled: bool
    debug_api_enabled: bool
    eval_api_enabled: bool
    playtest_api_enabled: bool
    usage_tracking_enabled: bool


class SecretConfig(BaseModel):
    llm_api_key: str | None = Field(default=None, repr=False)
    database_url: str | None = Field(default=None, repr=False)
    raw_env: dict[str, str] = Field(default_factory=dict, repr=False)


class BackupBundle(BaseModel):
    file_paths: list[str] = Field(default_factory=list)
    content_preview: str = ""


class ExportBundle(BaseModel):
    file_paths: list[str] = Field(default_factory=list)
    content_preview: str = ""
    safe_export: bool = True


class CrashReport(BaseModel):
    title: str
    message: str
    raw_env: dict[str, str] = Field(default_factory=dict)
    stack_trace: str = ""


class LocalLog(BaseModel):
    path: str
    text: str


class DesktopStudioPolicy:
    """Local-only v1.7 desktop studio boundary policy.

    The policy is intentionally pure: it does not call LLM providers, read the
    filesystem, write backups, or mutate GameState. Callers pass candidate data
    in and receive safe summaries or validation decisions back.
    """

    secret_env_names = {
        "LLM_API_KEY",
        "OPENAI_API_KEY",
        "API_KEY",
        "ANTHROPIC_API_KEY",
        "SECRET_KEY",
        "DATABASE_URL",
    }
    frontend_allowed_env_names = {"VITE_API_BASE_URL"}
    forbidden_backup_names = {".env", ".env.local", ".env.production", "env"}
    forbidden_backup_suffixes = {".log", ".db", ".sqlite", ".sqlite3", ".cache"}
    forbidden_executable_suffixes = {
        ".appimage",
        ".bat",
        ".cmd",
        ".cjs",
        ".deb",
        ".dll",
        ".dmg",
        ".exe",
        ".js",
        ".mjs",
        ".msi",
        ".pkg",
        ".ps1",
        ".py",
        ".rpm",
        ".sh",
        ".so",
    }
    forbidden_bundle_dirs = {
        ".cache",
        "backups",
        "cache",
        "caches",
        "crash-reports",
        "desktop-build",
        "desktop-dist",
        "desktop-release",
        "desktop_build",
        "electron-dist",
        "frontend/dist",
        "installers",
        "logs",
        "node_modules",
        "release",
        "src-tauri/gen",
        "src-tauri/target",
        "tauri-dist",
    }

    def build_safe_config_summary(self, settings: Settings) -> DesktopSafeConfigSummary:
        return DesktopSafeConfigSummary(
            app_name=settings.app_name,
            app_env=settings.app_env,
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            api_key_configured=bool(settings.llm_api_key),
            database_configured=bool(settings.database_url),
            database_path_hint=_database_hint(settings.database_url),
            authoring_api_enabled=settings.enable_authoring_api,
            debug_api_enabled=settings.enable_debug_api,
            eval_api_enabled=settings.enable_eval_api,
            playtest_api_enabled=settings.enable_playtest_api,
            usage_tracking_enabled=settings.enable_usage_tracking,
        )

    def validate_frontend_config(self, env: Mapping[str, str]) -> DesktopBoundaryDecision:
        blockers: list[str] = []
        warnings: list[str] = []
        for name, value in env.items():
            upper = name.upper()
            if upper in self.secret_env_names or "KEY" in upper or "SECRET" in upper or "TOKEN" in upper:
                blockers.append(f"frontend_secret_env:{name}")
            elif name.startswith("VITE_") and name not in self.frontend_allowed_env_names:
                warnings.append(f"frontend_unreviewed_vite_env:{name}")
            if _contains_secret_text(value):
                blockers.append(f"frontend_secret_value:{name}")
        return DesktopBoundaryDecision(allowed=not blockers, blockers=blockers, warnings=warnings)

    def validate_backup_bundle(self, bundle: BackupBundle) -> DesktopBoundaryDecision:
        return self._validate_file_bundle(bundle.file_paths, bundle.content_preview, bundle_kind="backup")

    def validate_export_bundle(self, bundle: ExportBundle) -> DesktopBoundaryDecision:
        decision = self._validate_file_bundle(bundle.file_paths, bundle.content_preview, bundle_kind="export")
        if not bundle.safe_export:
            decision.warnings.append("export_bundle_not_safe_profile")
        return decision

    def sanitize_crash_report(self, report: CrashReport) -> dict[str, str | bool]:
        message = redact_desktop_secret_text(report.message).text
        stack_trace = redact_desktop_secret_text(report.stack_trace).text
        return {
            "title": report.title,
            "message": message,
            "stack_trace": stack_trace,
            "raw_env_included": False,
        }

    def redact_log(self, log: LocalLog) -> LocalLog:
        return log.model_copy(update={"text": redact_desktop_secret_text(log.text).text})

    def validate_launcher_script(self, script_text: str) -> DesktopBoundaryDecision:
        blockers: list[str] = []
        lowered = script_text.lower()
        if re.search(r"sk-[A-Za-z0-9_-]{16,}", script_text):
            blockers.append("launcher_contains_secret_literal")
        if "vite_llm_api_key" in lowered or "vite_openai_api_key" in lowered:
            blockers.append("launcher_exposes_api_key_to_frontend")
        if "llm_api_key" in lowered and "not read by this script" not in lowered:
            blockers.append("launcher_reads_llm_api_key")
        return DesktopBoundaryDecision(allowed=not blockers, blockers=blockers)

    def _validate_file_bundle(
        self,
        file_paths: list[str],
        content_preview: str,
        *,
        bundle_kind: str,
    ) -> DesktopBoundaryDecision:
        blockers: list[str] = []
        for raw_path in file_paths:
            path = PurePosixPath(raw_path.replace("\\", "/"))
            lowered = path.as_posix().lower()
            if path.name.lower() in self.forbidden_backup_names:
                blockers.append(f"{bundle_kind}_contains_forbidden_file:{raw_path}")
            if path.suffix.lower() in self.forbidden_backup_suffixes:
                blockers.append(f"{bundle_kind}_contains_forbidden_suffix:{raw_path}")
            if path.suffix.lower() in self.forbidden_executable_suffixes:
                blockers.append(f"{bundle_kind}_contains_executable_file:{raw_path}")
            if any(lowered == directory or lowered.startswith(f"{directory}/") for directory in self.forbidden_bundle_dirs):
                blockers.append(f"{bundle_kind}_contains_forbidden_directory:{raw_path}")
            if ".." in path.parts or path.is_absolute():
                blockers.append(f"{bundle_kind}_contains_unsafe_path:{raw_path}")
        if _contains_secret_text(content_preview):
            blockers.append(f"{bundle_kind}_contains_secret_preview")
        return DesktopBoundaryDecision(allowed=not blockers, blockers=blockers)


_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?i)(LLM_API_KEY|OPENAI_API_KEY|API_KEY|SECRET_KEY)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


class RedactedDesktopText(BaseModel):
    text: str
    redaction_count: int = 0


def redact_desktop_secret_text(text: str) -> RedactedDesktopText:
    redacted = text
    count = 0
    for pattern in _SECRET_PATTERNS:
        redacted, replacements = pattern.subn("[redacted-secret]", redacted)
        count += replacements
    return RedactedDesktopText(text=redacted, redaction_count=count)


def _contains_secret_text(text: str) -> bool:
    if not text:
        return False
    return redact_desktop_secret_text(text).redaction_count > 0


def _database_hint(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return f"sqlite local file: {PurePosixPath(database_url.removeprefix('sqlite:///').replace('\\', '/')).name}"
    if database_url.startswith("sqlite://"):
        return "sqlite configured"
    return "database configured"
