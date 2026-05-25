from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from app.llm.provider_connection_cache import (
    PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH,
    ProviderConnectionStatusCacheEntry,
)
from app.llm.provider_model_assignment import validate_provider_model_assignments
from app.llm.provider_profiles import ProviderProfileV2
from app.llm.provider_router import JSON_ROUTING_USE_CASES, ProviderRoutingConfig
from app.platform.project_repository import ProjectRepository


ProviderSetupChecklistStatus = Literal["pass", "warning", "missing"]

_REAL_KEY_PATTERNS = (
    re.compile(r"(?im)^\s*(api_key|llm_api_key|openai_api_key)\s*:"),
    re.compile(r"sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}", re.IGNORECASE),
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"(?i)BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
)
_TRANSIENT_KEY_PATTERNS = (
    re.compile(r"(?i)\btransient_api_key\b"),
    re.compile(r"(?i)\btransient[_-]?key\b\s*[:=]"),
)

_PROVIDER_SETUP_USE_CASES: dict[str, list[str]] = {
    "novel_model_assigned": ["novel_draft"],
    "tavern_model_assigned": ["tavern_reply", "multi_npc_reply"],
    "world_intent_parser_model_assigned": ["world_intent_parse"],
    "world_narrator_model_assigned": ["world_narration"],
    "cross_mode_model_assigned": ["cross_mode_draft"],
    "quality_summary_model_assigned": ["quality_eval", "cheap_summary"],
}


class ProviderSetupChecklistItem(BaseModel):
    id: str
    label: str
    status: ProviderSetupChecklistStatus
    safe_summary: str
    next_action: str
    jump_target: str


class ProviderSetupChecklistReport(BaseModel):
    local_only: bool = True
    project_id: str
    overall_status: ProviderSetupChecklistStatus
    pass_count: int = 0
    warning_count: int = 0
    missing_count: int = 0
    items: list[ProviderSetupChecklistItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: str


class ProviderSetupChecklistService:
    """Read-only Provider setup checklist.

    This service only inspects project-local safe metadata. It does not test
    connections, fetch models, persist transient keys, call Provider Gateway, or
    change routing semantics.
    """

    def __init__(self, project_repository: ProjectRepository) -> None:
        self.project_repository = project_repository

    def check(self, project_id: str) -> ProviderSetupChecklistReport:
        project = self.project_repository.load_project(project_id)
        root = Path(project.project_root).resolve()
        profiles = _read_provider_profiles(root)
        cache = _read_connection_cache(root)
        config = _read_assignment_config(root)
        enabled_profiles = [profile for profile in profiles if profile.enabled]
        assignment_summary = validate_provider_model_assignments(config, profiles) if config.rules else None
        validation_by_use_case = {
            str(report["rule"]["use_case"]): report
            for report in (assignment_summary.validation_reports if assignment_summary else [])
            if isinstance(report, dict) and isinstance(report.get("rule"), dict)
        }
        real_key_findings = _privacy_findings(root, _REAL_KEY_PATTERNS)
        transient_findings = _privacy_findings(root, _TRANSIENT_KEY_PATTERNS)

        items = [
            _provider_profile_exists_item(enabled_profiles),
            _secret_configured_item(enabled_profiles),
            _connection_tested_item(enabled_profiles, cache),
            _models_available_item(enabled_profiles),
            _model_profile_synced_item(enabled_profiles),
            _assignment_item("novel_model_assigned", "Novel model assigned", config, validation_by_use_case),
            _assignment_item("tavern_model_assigned", "Tavern model assigned", config, validation_by_use_case),
            _assignment_item("world_intent_parser_model_assigned", "World intent parser model assigned", config, validation_by_use_case),
            _assignment_item("world_narrator_model_assigned", "World narrator model assigned", config, validation_by_use_case),
            _assignment_item("cross_mode_model_assigned", "Cross-Mode model assigned", config, validation_by_use_case),
            _assignment_item("quality_summary_model_assigned", "Quality / summary model assigned", config, validation_by_use_case),
            _json_warning_item(config, validation_by_use_case),
            _privacy_item("no_real_key_stored", "No real key stored in project", real_key_findings, "ProviderProfile stores api_key_env/secret_ref/local_secret_ref metadata only."),
            _privacy_item("no_transient_key_persisted", "No transient key persisted", transient_findings, "One-time connection-test key input is absent from provider metadata/cache."),
        ]
        counts = _status_counts(items)
        overall: ProviderSetupChecklistStatus
        if counts["missing"]:
            overall = "missing"
        elif counts["warning"]:
            overall = "warning"
        else:
            overall = "pass"
        return ProviderSetupChecklistReport(
            project_id=project.project_id,
            overall_status=overall,
            pass_count=counts["pass"],
            warning_count=counts["warning"],
            missing_count=counts["missing"],
            items=items,
            warnings=[item.safe_summary for item in items if item.status != "pass"],
            generated_at=datetime.now(UTC).isoformat(),
        )


def _provider_profile_exists_item(profiles: list[ProviderProfileV2]) -> ProviderSetupChecklistItem:
    if profiles:
        return _item(
            "provider_profile_exists",
            "Provider profile exists",
            "pass",
            f"{len(profiles)} enabled ProviderProfile record(s) are available.",
            "Review Provider Connectivity if another local provider is needed.",
            "provider_setup",
        )
    return _item(
        "provider_profile_exists",
        "Provider profile exists",
        "missing",
        "No enabled ProviderProfile exists.",
        "Create a mock/local_stub/local_http or env/secret_ref/local_secret_ref-based provider profile.",
        "provider_setup",
    )


def _secret_configured_item(profiles: list[ProviderProfileV2]) -> ProviderSetupChecklistItem:
    if not profiles:
        return _item("secret_configured", "Secret configured via api_key_env, secret_ref, or local_secret_ref", "missing", "Provider profile is missing.", "Create a provider profile first.", "provider_setup")
    requiring_secret = [profile for profile in profiles if profile.key_required()]
    if not requiring_secret:
        return _item(
            "secret_configured",
            "Secret configured via api_key_env, secret_ref, or local_secret_ref",
            "pass",
            "Enabled providers do not require API keys, or use local_stub/mock/local metadata.",
            "Use api_key_env, secret_ref, or local_secret_ref only if adding a provider that requires a secret.",
            "provider_setup",
        )
    missing = [profile.provider_profile_id for profile in requiring_secret if not (profile.api_key_env or profile.secret_ref or profile.local_secret_ref)]
    if missing:
        return _item(
            "secret_configured",
            "Secret configured via api_key_env, secret_ref, or local_secret_ref",
            "missing",
            f"{len(missing)} provider(s) require api_key_env, secret_ref, or local_secret_ref metadata.",
            "Set api_key_env, secret_ref, or local_secret_ref. Do not paste a plaintext API key.",
            "provider_setup",
        )
    return _item(
        "secret_configured",
        "Secret configured via api_key_env, secret_ref, or local_secret_ref",
        "pass",
        f"{len(requiring_secret)} secret-requiring provider(s) use safe secret metadata.",
        "Keep raw key values outside project files.",
        "provider_setup",
    )


def _connection_tested_item(profiles: list[ProviderProfileV2], cache: dict[str, ProviderConnectionStatusCacheEntry]) -> ProviderSetupChecklistItem:
    if not profiles:
        return _item("connection_tested", "Connection tested", "missing", "No provider profile exists for connection status.", "Create a provider profile, then run safe local Test Connection.", "connection")
    connected = [entry for entry in cache.values() if entry.status == "connected"]
    if connected:
        return _item("connection_tested", "Connection tested", "pass", f"{len(connected)} provider connection status entrie(s) are connected.", "Refresh manually when stale.", "connection")
    if cache:
        statuses = ", ".join(sorted({entry.status for entry in cache.values()}))
        return _item("connection_tested", "Connection tested", "warning", f"Connection cache exists but reports: {statuses}.", "Run Test Connection with fake/local client or fix safe status warnings.", "connection")
    return _item("connection_tested", "Connection tested", "warning", "No provider connection status cache exists yet.", "Run Test Connection. CI and tests use fake clients only.", "connection")


def _models_available_item(profiles: list[ProviderProfileV2]) -> ProviderSetupChecklistItem:
    model_count = sum(len(profile.model_profiles) for profile in profiles)
    if model_count:
        return _item("models_fetched_or_manual", "Models fetched or manually added", "pass", f"{model_count} ModelProfile row(s) are available.", "Review model capability badges before assigning modes.", "models")
    return _item("models_fetched_or_manual", "Models fetched or manually added", "warning", "No models have been fetched or manually added.", "Fetch models with a fake/local path or add a manual model_id.", "models")


def _model_profile_synced_item(profiles: list[ProviderProfileV2]) -> ProviderSetupChecklistItem:
    synced = [model for profile in profiles for model in profile.model_profiles if model.provider_profile_id or model.last_seen_at or model.enabled]
    if synced:
        return _item("modelprofile_synced", "ModelProfile synced", "pass", f"{len(synced)} safe ModelProfile entrie(s) are stored in project metadata.", "Keep sync reports redacted and local-only.", "models")
    return _item("modelprofile_synced", "ModelProfile synced", "warning", "No saved ModelProfile metadata is available.", "Sync or manually add model metadata before assignment.", "models")


def _assignment_item(
    item_id: str,
    label: str,
    config: ProviderRoutingConfig,
    validation_by_use_case: dict[str, dict[str, object]],
) -> ProviderSetupChecklistItem:
    use_cases = _PROVIDER_SETUP_USE_CASES[item_id]
    assigned = [rule for rule in config.rules if rule.enabled and str(rule.use_case) in use_cases]
    if not assigned:
        return _item(item_id, label, "warning", f"No enabled assignment for {', '.join(use_cases)}.", "Open Model Assignment and assign provider/model metadata.", "assignment")
    validation_reports = [validation_by_use_case.get(str(rule.use_case)) for rule in assigned]
    invalid = [report for report in validation_reports if report and not report.get("ok")]
    if invalid:
        return _item(item_id, label, "warning", f"{label} has capability or routing warnings that need review.", "Validate routing and choose a compatible model/fallback.", "assignment")
    return _item(item_id, label, "pass", f"{label} uses {len(assigned)} enabled routing rule(s).", "Keep Provider Gateway routing metadata validated.", "assignment")


def _json_warning_item(config: ProviderRoutingConfig, validation_by_use_case: dict[str, dict[str, object]]) -> ProviderSetupChecklistItem:
    json_rules = [rule for rule in config.rules if rule.enabled and str(rule.use_case) in {str(item) for item in JSON_ROUTING_USE_CASES}]
    if not json_rules:
        return _item("json_capable_warning_resolved", "JSON-capable model warning resolved for structured use cases", "warning", "No structured JSON use case assignments are configured.", "Assign JSON-capable models for structured use cases.", "assignment")
    warning_reports: list[dict[str, object]] = []
    for rule in json_rules:
        report = validation_by_use_case.get(str(rule.use_case))
        if not report or not report.get("ok") or report.get("warnings"):
            warning_reports.append(report or {"ok": False})
    if warning_reports:
        return _item(
            "json_capable_warning_resolved",
            "JSON-capable model warning resolved for structured use cases",
            "warning",
            f"{len(warning_reports)} structured use case assignment(s) still have JSON capability warnings.",
            "Choose supports_json models or JSON-capable fallback chains.",
            "assignment",
        )
    return _item(
        "json_capable_warning_resolved",
        "JSON-capable model warning resolved for structured use cases",
        "pass",
        f"{len(json_rules)} structured use case assignment(s) validate with JSON-capable models.",
        "Keep structured output use cases on supports_json models.",
        "assignment",
    )


def _privacy_item(item_id: str, label: str, findings: list[str], pass_summary: str) -> ProviderSetupChecklistItem:
    if findings:
        return _item(item_id, label, "missing", f"{len(findings)} unsafe provider metadata finding(s) need removal.", "Remove unsafe key-like values and keep only api_key_env/secret_ref/local_secret_ref metadata.", "privacy")
    return _item(item_id, label, "pass", pass_summary, "No action needed; continue using local secret boundaries.", "privacy")


def _read_provider_profiles(root: Path) -> list[ProviderProfileV2]:
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


def _read_connection_cache(root: Path) -> dict[str, ProviderConnectionStatusCacheEntry]:
    path = _project_path(root, *PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH.split("/"))
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
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


def _read_assignment_config(root: Path) -> ProviderRoutingConfig:
    path = _project_path(root, "providers", "model_assignments.yaml")
    if not path.exists():
        return ProviderRoutingConfig()
    try:
        return ProviderRoutingConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    except Exception:
        return ProviderRoutingConfig()


def _privacy_findings(root: Path, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    findings: list[str] = []
    for relative in (
        ("providers", "profiles"),
        ("providers", "model_assignments.yaml"),
        tuple(PROVIDER_CONNECTION_STATUS_CACHE_RELATIVE_PATH.split("/")),
    ):
        path = _project_path(root, *relative)
        if not path.exists():
            continue
        candidates = sorted(path.glob("*.yaml")) if path.is_dir() else [path]
        for candidate in candidates:
            try:
                text = candidate.read_text(encoding="utf-8")
            except OSError:
                continue
            if any(pattern.search(text) for pattern in patterns):
                findings.append(candidate.name)
    return findings


def _item(
    item_id: str,
    label: str,
    status: ProviderSetupChecklistStatus,
    safe_summary: str,
    next_action: str,
    jump_target: str,
) -> ProviderSetupChecklistItem:
    return ProviderSetupChecklistItem(
        id=item_id,
        label=label,
        status=status,
        safe_summary=safe_summary,
        next_action=next_action,
        jump_target=jump_target,
    )


def _status_counts(items: list[ProviderSetupChecklistItem]) -> dict[str, int]:
    return {
        "pass": sum(1 for item in items if item.status == "pass"),
        "warning": sum(1 for item in items if item.status == "warning"),
        "missing": sum(1 for item in items if item.status == "missing"),
    }


def _project_path(root: Path, *parts: str) -> Path:
    candidate = root.joinpath(*parts).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Provider setup checklist path escaped project root")
    return candidate
