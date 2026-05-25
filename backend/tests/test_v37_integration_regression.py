from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_connection_cache import ProviderConnectionStatusCache
from app.llm.provider_connection_test import ProviderConnectionStatus
from app.llm.provider_model_assignment import (
    MODEL_ASSIGNMENT_USE_CASES,
    ProviderModelAssignmentRepository,
    validate_provider_model_assignments,
)
from app.llm.provider_profiles import ModelProfile, ProviderProfileRepository, ProviderProfileV2
from app.llm.provider_router import JSON_ROUTING_USE_CASES, ProviderRoutingConfig, ProviderRoutingRule
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.project_validation import validate_project
from app.quality.project_gate import ProjectQualityGateConfig, run_project_quality_gate


ROOT = Path(__file__).resolve().parents[2]
DEMO_PROJECT = ROOT / "examples" / "demo_local_narrative_project"

SECRET_LIKE_RE = re.compile(
    r"sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}|authorization\s*[:=]\s*bearer\s+(?!\[?redacted\]?\b)\S+|BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY",
    re.IGNORECASE,
)
FORBIDDEN_SAFE_RESPONSE_TOKENS = (
    "transient_api_key",
    "raw_provider_response",
    "raw_prompt",
    "raw_output",
    "raw_state_delta",
    "raw state_delta",
    "hidden_fact_text",
    "npc_secret",
)


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _client(tmp_path: Path, *, debug_enabled: bool = True) -> tuple[TestClient, ProjectRepository, object, object]:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=debug_enabled, llm_provider="mock")
    return TestClient(app), repo, previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def _project_root(repo: ProjectRepository) -> Path:
    return Path(repo.load_project("demo").project_root)


def _configure_local_stub_provider(root: Path) -> None:
    profile = ProviderProfileV2(
        provider_profile_id="local_stub",
        display_name="Local Stub",
        provider_type="local_stub",
        requires_api_key=False,
        model_profiles=[
            ModelProfile(
                model_id="json-pro",
                display_name="JSON Pro",
                provider_profile_id="local_stub",
                supports_text=True,
                supports_json=True,
                supports_streaming=True,
                supports_tools=False,
                recommended_use_cases=[str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES],
                enabled=True,
                last_seen_at=datetime.now(UTC).isoformat(),
            )
        ],
    )
    ProviderProfileRepository(root).save_provider_profile(profile)
    ProviderConnectionStatusCache(root).save_status(
        "local_stub",
        ProviderConnectionStatus(
            status="connected",
            safe_message="Fake local provider connection succeeded.",
            provider_type="local_stub",
            tested_at=datetime.now(UTC).isoformat(),
            latency_ms=1.0,
            redaction_applied=True,
        ),
        model_count=1,
    )
    ProviderModelAssignmentRepository(root).save(
        ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=use_case,
                    primary_provider_id="local_stub",
                    primary_model_id="json-pro",
                    require_json_support=use_case in JSON_ROUTING_USE_CASES,
                    require_local_only=True,
                    enabled=True,
                )
                for use_case in MODEL_ASSIGNMENT_USE_CASES
            ]
        )
    )


def _complete_local_product_fixture(root: Path) -> None:
    _configure_local_stub_provider(root)
    for relative in (
        "novel/manuscripts",
        "novel/chapters",
        "novel/scenes",
        "tavern/sessions",
        "tavern/characters",
        "world/content_pack",
        "cross_mode/drafts",
        "cross_mode/proposals",
        "cross_mode/reviews",
        "cross_mode/apply_plans",
        "cross_mode/audit",
        "scripts/mods",
        "quality/reports",
        "quality/playtests",
        "backups",
        "exports",
        "exports/diagnostics",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / "cross_mode" / "drafts" / "safe_draft.txt").write_text("safe cross-mode draft marker", encoding="utf-8")
    (root / "cross_mode" / "proposals" / "safe_proposal.json").write_text(
        json.dumps({"validated": True, "auto_apply": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "reviews" / "safe_review.json").write_text(
        json.dumps({"reviewed": True, "hidden_details_included": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "apply_plans" / "safe_apply_plan.json").write_text(
        json.dumps({"requires_confirm": True, "auto_apply": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "cross_mode" / "audit" / "safe_audit.json").write_text(
        json.dumps({"audit_trail": True, "state_mutated_by_draft": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "backups" / "backup_manifest.json").write_text(
        json.dumps({"local_only": True, "contains_secrets": False}, sort_keys=True),
        encoding="utf-8",
    )
    (root / "exports" / "diagnostics" / "preview.json").write_text(
        json.dumps({"redacted": True, "uploaded": False}, sort_keys=True),
        encoding="utf-8",
    )


def _item(payload: dict[str, object], item_id: str) -> dict[str, object]:
    for item in payload["items"]:  # type: ignore[index]
        if item["id"] == item_id:
            return item
    raise AssertionError(f"Missing item: {item_id}")


def _assert_safe_text(text: str) -> None:
    assert not SECRET_LIKE_RE.search(text)
    lowered = text.lower()
    for token in FORBIDDEN_SAFE_RESPONSE_TOKENS:
        assert token not in lowered


def _assert_project_tree_has_no_sensitive_payloads(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        _assert_safe_text(text)
        assert path.name.lower() != ".env"
        assert path.suffix.lower() not in {".db", ".sqlite", ".sqlite3", ".log", ".exe", ".bat", ".cmd"}


def test_v37_local_complete_product_e2e_workflow_and_provider_checklists_are_safe(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        root = _project_root(repo)
        _complete_local_product_fixture(root)
        workflow_response = client.get("/projects/demo/workflow-check")
        provider_response = client.get("/projects/demo/providers/setup-checklist")
    finally:
        _restore(previous_repo, previous_settings)

    assert workflow_response.status_code == 200
    workflow = workflow_response.json()
    assert workflow["overall_status"] == "ready"
    assert workflow["privacy_boundaries_pass"] is True
    for item_id in (
        "project_created_opened",
        "provider_configured",
        "connection_status_checked",
        "model_list_available",
        "model_assignment_complete",
        "novel_workflow_available",
        "tavern_workflow_available",
        "world_workflow_available",
        "cross_mode_proposals_available",
        "authoring_mod_available",
        "quality_gate_runnable",
        "debug_replay_available",
        "backup_restore_available",
        "export_diagnostics_available",
        "privacy_boundaries_pass",
    ):
        assert _item(workflow, item_id)["status"] == "ready"

    assert provider_response.status_code == 200
    provider = provider_response.json()
    assert provider["overall_status"] == "pass"
    for item in provider["items"]:
        assert item["status"] == "pass"
    _assert_safe_text(workflow_response.text)
    _assert_safe_text(provider_response.text)
    _assert_project_tree_has_no_sensitive_payloads(root)


def test_v37_provider_model_assignment_uses_local_stub_and_preserves_capability_validation(tmp_path: Path) -> None:
    _repo = _project_repo(tmp_path)
    root = tmp_path / "projects" / "demo"
    _configure_local_stub_provider(root)

    profiles = ProviderProfileRepository(root).list_provider_profiles()
    assert [profile.provider_type for profile in profiles] == ["local_stub"]
    assert profiles[0].api_key_env is None
    assert profiles[0].secret_ref is None
    assert profiles[0].key_required() is False

    config = ProviderModelAssignmentRepository(root).load()
    summary = validate_provider_model_assignments(config, profiles)
    assert not summary.warnings
    assert {str(rule.use_case) for rule in summary.rules} == {str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES}
    assert any(str(rule.use_case) == "world_intent_parse" and rule.require_json_support for rule in summary.rules)

    cache = ProviderConnectionStatusCache(root).safe_status("local_stub")
    assert cache is not None
    assert cache["status"] == "connected"
    _assert_safe_text(json.dumps(cache, sort_keys=True))


def test_v37_demo_project_quality_gate_passes_without_real_provider() -> None:
    validation = validate_project(DEMO_PROJECT)
    assert validation.ok, [issue.model_dump(mode="json") for issue in validation.errors]

    gate = run_project_quality_gate(
        DEMO_PROJECT,
        ProjectQualityGateConfig(profile="fast", include_cross_mode=True),
    )

    assert gate.passed, gate.model_dump(mode="json")
    assert gate.blockers == []
    assert gate.errors == []
    profiles = ProviderProfileRepository(DEMO_PROJECT).list_provider_profiles()
    assert profiles
    assert {profile.provider_type for profile in profiles} == {"local_stub"}


def test_v37_frontend_complete_product_surfaces_are_safe_and_local_only() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    desktop_source = (ROOT / "frontend" / "src" / "desktopUi.tsx").read_text(encoding="utf-8")
    provider_source = (ROOT / "frontend" / "src" / "providerUi.tsx").read_text(encoding="utf-8")
    combined = "\n".join([app_source, desktop_source, provider_source])

    for token in (
        'data-v37-product-readiness="safe-summary"',
        'data-v37-provider-setup-checklist="safe-summary"',
        "End-to-End Local Workflow Checker",
        "Product Acceptance Checklist UI",
        "Product readiness safe summaries never include",
        "Privacy / Safety review is read-only and safe-summary only",
        "no hidden content text",
        "no raw state_deltas",
        "No account, no cloud sync, no online marketplace",
    ):
        assert token in combined

    assert not SECRET_LIKE_RE.search(combined)
    assert not re.search(r"<input[^>]+(?:name|id)=['\"]api[_-]?key['\"]", combined, re.IGNORECASE)
    assert not re.search(r"create(Account|CloudSync|OnlineMarketplace|RemoteDownload)", combined)
    assert "raw provider responses are never rendered" in provider_source.lower()
