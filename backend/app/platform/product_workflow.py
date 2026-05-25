from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from app.config import Settings
from app.llm.provider_connection_cache import (
    PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH,
    ProviderConnectionStatusCacheEntry,
)
from app.llm.provider_model_assignment import (
    MODEL_ASSIGNMENT_USE_CASES,
    validate_provider_model_assignments,
)
from app.llm.provider_profiles import ProviderProfileV2
from app.llm.provider_router import ProviderRoutingConfig
from app.platform.project_repository import ProjectRepository
from app.platform.project_workspace import validate_project_workspace


ProductWorkflowCheckStatus = Literal["ready", "warning", "missing", "disabled", "not_checked"]

_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}", re.IGNORECASE),
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"(?i)BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    re.compile(r"(?i)\btransient_api_key\b"),
    re.compile(r"(?i)\b(raw_prompt|raw_output|raw_provider_response)\b"),
)
_PRIVACY_SCAN_SUFFIXES = {".json", ".yaml", ".yml", ".txt", ".md", ".log"}
_PRIVACY_SCAN_MAX_BYTES = 1_000_000
_CROSS_MODE_REQUIRED_DIRS = ("drafts", "proposals", "reviews", "apply_plans", "audit")


class ProductWorkflowCheckItem(BaseModel):
    id: str
    label: str
    status: ProductWorkflowCheckStatus
    safe_summary: str
    next_action: str
    jump_target: str


class ProductWorkflowCheckReport(BaseModel):
    local_only: bool = True
    project_id: str
    overall_status: ProductWorkflowCheckStatus
    ready_count: int = 0
    warning_count: int = 0
    missing_count: int = 0
    disabled_count: int = 0
    not_checked_count: int = 0
    privacy_boundaries_pass: bool = True
    items: list[ProductWorkflowCheckItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: str


class ProductWorkflowCheckService:
    """Read-only local product workflow checker.

    The checker intentionally reads existing safe metadata and project-local
    markers only. It does not run Provider tests, call LLMs, create directories,
    mutate GameState, write EventLog, create backups, export diagnostics, or
    apply Cross-Mode proposals.
    """

    def __init__(self, project_repository: ProjectRepository, *, settings: Settings | None = None) -> None:
        self.project_repository = project_repository
        self.settings = settings or Settings(llm_provider="mock")

    def check(self, project_id: str) -> ProductWorkflowCheckReport:
        project = self.project_repository.load_project(project_id)
        root = Path(project.project_root).resolve()
        workspace = validate_project_workspace(root, base_root=self.project_repository.root)
        profiles = self._read_provider_profiles(root)
        connection_cache = self._read_connection_cache(root)
        assignment_config = self._read_assignment_config(root)
        privacy_warnings = self._privacy_warnings(root)

        items = [
            self._project_created_opened_item(project.project_id, workspace.ok and not workspace.missing, len(workspace.missing)),
            self._provider_configured_item(profiles),
            self._connection_checked_item(profiles, connection_cache),
            self._model_list_item(profiles),
            self._model_assignment_item(assignment_config, profiles),
            self._directory_item("novel_workflow_available", "Novel workflow available", root, ("novel", "manuscripts"), "novel"),
            self._directory_item("tavern_workflow_available", "Tavern workflow available", root, ("tavern", "sessions"), "tavern"),
            self._directory_item("world_workflow_available", "World workflow available", root, ("world", "content_pack"), "world"),
            self._cross_mode_item(root),
            self._authoring_mod_item(root),
            self._quality_gate_item(root),
            self._debug_replay_item(),
            self._backup_restore_item(root),
            self._export_diagnostics_item(root),
            self._privacy_item(privacy_warnings),
        ]
        counts = _status_counts(items)
        warnings = [item.safe_summary for item in items if item.status in {"warning", "missing"}]
        overall_status: ProductWorkflowCheckStatus
        if counts["missing"] > 0:
            overall_status = "missing"
        elif counts["warning"] > 0 or counts["disabled"] > 0 or counts["not_checked"] > 0:
            overall_status = "warning"
        else:
            overall_status = "ready"
        return ProductWorkflowCheckReport(
            project_id=project.project_id,
            overall_status=overall_status,
            ready_count=counts["ready"],
            warning_count=counts["warning"],
            missing_count=counts["missing"],
            disabled_count=counts["disabled"],
            not_checked_count=counts["not_checked"],
            privacy_boundaries_pass=not privacy_warnings,
            items=items,
            warnings=warnings,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def _project_created_opened_item(self, project_id: str, workspace_ok: bool, missing_count: int) -> ProductWorkflowCheckItem:
        if workspace_ok:
            return _item(
                "project_created_opened",
                "Project created/opened",
                "ready",
                f"Local project {project_id} is available with required workspace sections.",
                "Continue the local complete product workflow from Project Home.",
                "project",
            )
        return _item(
            "project_created_opened",
            "Project created/opened",
            "warning",
            f"Project {project_id} is open, but {missing_count} workspace section(s) are missing.",
            "Run project validation or create missing local workspace sections.",
            "project",
        )

    def _provider_configured_item(self, profiles: list[ProviderProfileV2]) -> ProductWorkflowCheckItem:
        enabled = [profile for profile in profiles if profile.enabled]
        if enabled:
            return _item(
                "provider_configured",
                "Provider configured",
                "ready",
                f"{len(enabled)} enabled ProviderProfile record(s) found. Only api_key_env/secret_ref/local_secret_ref metadata is used.",
                "Open Provider Connectivity to review local status or add another safe profile.",
                "provider",
            )
        return _item(
            "provider_configured",
            "Provider configured",
            "warning",
            "No enabled ProviderProfile was found. Missing provider returns warning; no real provider test was run.",
            "Configure mock, local_stub, local_http, OpenAI-compatible, relay-style, or custom provider metadata.",
            "provider",
        )

    def _connection_checked_item(
        self,
        profiles: list[ProviderProfileV2],
        connection_cache: dict[str, ProviderConnectionStatusCacheEntry],
    ) -> ProductWorkflowCheckItem:
        if not profiles:
            return _item(
                "connection_status_checked",
                "Connection status checked",
                "warning",
                "Connection status cannot be checked until a ProviderProfile exists.",
                "Configure a local provider profile, then run the safe fake/local connection test.",
                "provider",
            )
        connected = [entry for entry in connection_cache.values() if entry.status == "connected"]
        if connected:
            return _item(
                "connection_status_checked",
                "Connection status checked",
                "ready",
                f"{len(connected)} provider connection status cache entrie(s) are connected. Cache stores status metadata only.",
                "Refresh manually if the Provider Connectivity Dashboard reports stale status.",
                "provider",
            )
        if connection_cache:
            statuses = sorted({entry.status for entry in connection_cache.values()})
            return _item(
                "connection_status_checked",
                "Connection status checked",
                "warning",
                f"Provider connection cache exists but no connected status was found: {', '.join(statuses)}.",
                "Run a local fake/client connection test or fix missing_secret/auth_failed warnings.",
                "provider",
            )
        return _item(
            "connection_status_checked",
            "Connection status checked",
            "warning",
            "Provider connection has not been tested in the local status cache.",
            "Run Test Connection from Provider Connectivity. Tests use fake/local clients in CI.",
            "provider",
        )

    def _model_list_item(self, profiles: list[ProviderProfileV2]) -> ProductWorkflowCheckItem:
        model_count = sum(len(profile.model_profiles) for profile in profiles)
        if model_count:
            return _item(
                "model_list_available",
                "Model list available or manual model configured",
                "ready",
                f"{model_count} safe ModelProfile entrie(s) are available from synced or manual local metadata.",
                "Review model capabilities and assignment by mode.",
                "provider",
            )
        return _item(
            "model_list_available",
            "Model list available or manual model configured",
            "warning",
            "No ModelProfile entries are available yet.",
            "Fetch models from a fake/local provider path or add a manual model_id.",
            "provider",
        )

    def _model_assignment_item(
        self,
        config: ProviderRoutingConfig,
        profiles: list[ProviderProfileV2],
    ) -> ProductWorkflowCheckItem:
        if not config.rules:
            return _item(
                "model_assignment_complete",
                "Model assignment complete",
                "warning",
                "Provider model assignment config is missing.",
                "Assign models by Novel, Tavern, World, Cross-Mode, and Quality use case.",
                "provider",
            )
        supported = {str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES}
        assigned = {str(rule.use_case) for rule in config.rules if rule.enabled}
        missing = sorted(supported - assigned)
        summary = validate_provider_model_assignments(config, profiles)
        has_errors = any(not report.get("ok", False) for report in summary.validation_reports)
        if missing or has_errors:
            detail = f"Missing {len(missing)} use case assignment(s)." if missing else "One or more model assignment rules need review."
            return _item(
                "model_assignment_complete",
                "Model assignment complete",
                "warning",
                detail,
                "Open Model Assignment and validate routing capability warnings.",
                "provider",
            )
        return _item(
            "model_assignment_complete",
            "Model assignment complete",
            "ready",
            f"All {len(supported)} supported use case(s) have enabled model assignments and safe validation reports.",
            "Keep assignments local and refresh only when provider model metadata changes.",
            "provider",
        )

    def _directory_item(
        self,
        item_id: str,
        label: str,
        root: Path,
        path_parts: tuple[str, ...],
        jump_target: str,
    ) -> ProductWorkflowCheckItem:
        exists = _project_path(root, *path_parts).exists()
        return _item(
            item_id,
            label,
            "ready" if exists else "warning",
            f"{'/'.join(path_parts)} {'exists' if exists else 'is not initialized'} for local workflow access.",
            "Open the matching Studio panel and create local draft data if needed.",
            jump_target,
        )

    def _cross_mode_item(self, root: Path) -> ProductWorkflowCheckItem:
        cross_mode_root = _project_path(root, "cross_mode")
        missing = [name for name in _CROSS_MODE_REQUIRED_DIRS if not (cross_mode_root / name).exists()]
        has_closure_marker = any(
            _has_non_placeholder_file(cross_mode_root / name)
            for name in ("proposals", "reviews", "apply_plans", "audit")
        )
        ready = cross_mode_root.exists() and not missing and has_closure_marker
        return _item(
            "cross_mode_proposals_available",
            "Cross-Mode proposals available",
            "ready" if ready else "warning",
            "Cross-Mode draft/proposal/review/apply/audit markers are initialized."
            if ready
            else f"Cross-Mode closure is incomplete: {len(missing)} required folder(s) missing or no safe proposal/review/apply/audit marker exists.",
            "Create or review a Novel/Tavern/World draft through validation, confirm-gated apply, and audit.",
            "cross_mode",
        )

    def _authoring_mod_item(self, root: Path) -> ProductWorkflowCheckItem:
        mods_dir = _project_path(root, "scripts", "mods")
        if not getattr(self.settings, "enable_authoring_api", False):
            return _item(
                "authoring_mod_available",
                "Authoring / Mod available",
                "disabled",
                "Authoring API is disabled; editors remain read-only/unavailable instead of writing active GameState.",
                "Enable authoring locally only when editing draft packages.",
                "authoring",
            )
        return _item(
            "authoring_mod_available",
            "Authoring / Mod available",
            "ready" if mods_dir.exists() else "warning",
            "Authoring and Mod draft directories are available." if mods_dir.exists() else "Authoring/Mod draft directory is missing.",
            "Open Authoring / Mod Studio for validation, dry-run, and safe apply.",
            "authoring",
        )

    def _quality_gate_item(self, root: Path) -> ProductWorkflowCheckItem:
        quality_dir = _project_path(root, "quality", "reports")
        return _item(
            "quality_gate_runnable",
            "Quality Gate runnable",
            "ready" if quality_dir.exists() else "warning",
            "Quality report directory is available for deterministic local checks." if quality_dir.exists() else "Quality report directory is missing.",
            "Run local Quality Gate with fake/mock provider paths only.",
            "quality",
        )

    def _debug_replay_item(self) -> ProductWorkflowCheckItem:
        debug_enabled = bool(getattr(self.settings, "enable_debug_api", False))
        return _item(
            "debug_replay_available",
            "Debug / Replay available",
            "ready" if debug_enabled else "disabled",
            "Debug API is enabled; raw debug views remain gated." if debug_enabled else "Debug API is disabled; normal QA views remain available without raw debug data.",
            "Open QA / Replay. Enable debug locally only for explicit raw inspection.",
            "qa_debug",
        )

    def _backup_restore_item(self, root: Path) -> ProductWorkflowCheckItem:
        backup_root = root / "backups"
        has_safe_marker = backup_root.exists() and _has_safe_policy_marker(
            backup_root,
            require_no_upload=False,
            require_secret_exclusion=True,
        )
        return _item(
            "backup_restore_available",
            "Backup / Restore available",
            "ready" if has_safe_marker else "warning",
            "Safe backup metadata marker confirms secrets are excluded by default."
            if has_safe_marker
            else "No safe backup metadata marker was found for this project.",
            "Run Backup dry-run first and ensure the manifest records secret exclusion before restore confirm.",
            "backup",
        )

    def _export_diagnostics_item(self, root: Path) -> ProductWorkflowCheckItem:
        exports_dir = _project_path(root, "exports")
        has_safe_marker = exports_dir.exists() and _has_safe_policy_marker(
            exports_dir,
            require_no_upload=True,
            require_secret_exclusion=True,
        )
        return _item(
            "export_diagnostics_available",
            "Export / Diagnostics available",
            "ready" if has_safe_marker else "warning",
            "Safe export/diagnostics preview marker confirms redaction and no upload."
            if has_safe_marker
            else "No safe export/diagnostics preview marker was found.",
            "Preview export/diagnostics and confirm the marker records redaction, secret exclusion, and no upload.",
            "diagnostics",
        )

    def _privacy_item(self, privacy_warnings: list[str]) -> ProductWorkflowCheckItem:
        return _item(
            "privacy_boundaries_pass",
            "Privacy boundaries pass",
            "ready" if not privacy_warnings else "missing",
            "No raw secrets, transient keys, raw prompts, raw outputs, or raw provider responses were found in checked workflow metadata."
            if not privacy_warnings
            else f"Privacy metadata check found {len(privacy_warnings)} unsafe pattern(s).",
            "Keep API keys in env/secret_ref and rerun local privacy checks.",
            "privacy",
        )

    def _read_provider_profiles(self, root: Path) -> list[ProviderProfileV2]:
        profiles_root = _project_path(root, "providers", "profiles")
        if not profiles_root.exists():
            return []
        profiles: list[ProviderProfileV2] = []
        for path in sorted(profiles_root.glob("*.yaml")):
            try:
                profiles.append(ProviderProfileV2.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
            except Exception:
                continue
        return profiles

    def _read_connection_cache(self, root: Path) -> dict[str, ProviderConnectionStatusCacheEntry]:
        cache_path = _project_path(root, *PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH.split("/"))
        if not cache_path.exists():
            return {}
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        entries: dict[str, ProviderConnectionStatusCacheEntry] = {}
        for provider_profile_id, value in payload.items():
            if not isinstance(provider_profile_id, str) or not isinstance(value, dict):
                continue
            try:
                entries[provider_profile_id] = ProviderConnectionStatusCacheEntry.model_validate(value)
            except Exception:
                continue
        return entries

    def _read_assignment_config(self, root: Path) -> ProviderRoutingConfig:
        path = _project_path(root, "providers", "model_assignments.yaml")
        if not path.exists():
            return ProviderRoutingConfig()
        try:
            return ProviderRoutingConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        except Exception:
            return ProviderRoutingConfig()

    def _privacy_warnings(self, root: Path) -> list[str]:
        warnings: list[str] = []
        for relative in (
            ("providers", "profiles"),
            ("providers", "model_assignments.yaml"),
            tuple(PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH.split("/")),
            ("backups",),
            ("exports",),
            ("diagnostics",),
            ("logs",),
        ):
            path = _project_path(root, *relative)
            if not path.exists():
                continue
            for candidate in _privacy_scan_candidates(path):
                text = _safe_read_text(candidate)
                if text is None:
                    continue
                if any(pattern.search(text) for pattern in _SECRET_VALUE_PATTERNS):
                    warnings.append("Unsafe sensitive pattern in checked workflow metadata")
        return warnings


def _item(
    item_id: str,
    label: str,
    status: ProductWorkflowCheckStatus,
    safe_summary: str,
    next_action: str,
    jump_target: str,
) -> ProductWorkflowCheckItem:
    return ProductWorkflowCheckItem(
        id=item_id,
        label=label,
        status=status,
        safe_summary=safe_summary,
        next_action=next_action,
        jump_target=jump_target,
    )


def _status_counts(items: list[ProductWorkflowCheckItem]) -> dict[str, int]:
    return {
        "ready": sum(1 for item in items if item.status == "ready"),
        "warning": sum(1 for item in items if item.status == "warning"),
        "missing": sum(1 for item in items if item.status == "missing"),
        "disabled": sum(1 for item in items if item.status == "disabled"),
        "not_checked": sum(1 for item in items if item.status == "not_checked"),
    }


def _has_non_placeholder_file(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    for candidate in path.rglob("*"):
        if candidate.is_file() and candidate.name != ".gitkeep":
            return True
    return False


def _has_safe_policy_marker(root: Path, *, require_no_upload: bool, require_secret_exclusion: bool) -> bool:
    for candidate in _privacy_scan_candidates(root):
        if candidate.name == ".gitkeep":
            continue
        payload = _read_structured_marker(candidate)
        if not isinstance(payload, dict):
            continue
        secret_safe = not require_secret_exclusion or _marker_confirms_secret_exclusion(payload)
        upload_safe = not require_no_upload or _marker_confirms_no_upload(payload)
        if secret_safe and upload_safe:
            return True
    return False


def _marker_confirms_secret_exclusion(payload: dict[str, object]) -> bool:
    true_keys = {
        "exclude_secrets",
        "excludes_secrets",
        "secrets_excluded",
        "redacted",
        "redaction_applied",
        "provider_secrets_excluded",
    }
    false_keys = {
        "contains_secrets",
        "include_secrets",
        "includes_secrets",
        "export_secrets",
    }
    return any(payload.get(key) is True for key in true_keys) or any(payload.get(key) is False for key in false_keys)


def _marker_confirms_no_upload(payload: dict[str, object]) -> bool:
    return (
        payload.get("local_only") is True
        or payload.get("uploaded") is False
        or payload.get("upload") is False
        or payload.get("uploads_data") is False
    )


def _read_structured_marker(path: Path) -> object | None:
    text = _safe_read_text(path)
    if text is None:
        return None
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text)
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None
    return None


def _privacy_scan_candidates(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if _is_text_scan_candidate(path) else []
    return [candidate for candidate in sorted(path.rglob("*")) if candidate.is_file() and _is_text_scan_candidate(candidate)]


def _is_text_scan_candidate(path: Path) -> bool:
    return path.name.lower().startswith(".env") or path.suffix.lower() in _PRIVACY_SCAN_SUFFIXES


def _safe_read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > _PRIVACY_SCAN_MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _project_path(root: Path, *parts: str) -> Path:
    candidate = root.joinpath(*parts).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Workflow check path escaped project root")
    return candidate
