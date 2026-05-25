from __future__ import annotations

import json
from pathlib import Path

from app.llm.provider_connection_cache import ProviderConnectionStatusCache
from app.llm.provider_model_assignment import ProviderModelAssignmentRepository, MODEL_ASSIGNMENT_USE_CASES, validate_provider_model_assignments
from app.llm.provider_profiles import ProviderProfileRepository
from app.platform.project_validation import validate_project
from app.quality.project_gate import ProjectQualityGateConfig, run_project_quality_gate


ROOT = Path(__file__).resolve().parents[2]
DEMO_PROJECT = ROOT / "examples" / "demo_local_narrative_project"


def test_v37_demo_project_quality_gate_passes() -> None:
    report = validate_project(DEMO_PROJECT)
    assert report.ok, [issue.model_dump(mode="json") for issue in report.errors]

    gate = run_project_quality_gate(
        DEMO_PROJECT,
        ProjectQualityGateConfig(profile="fast", include_cross_mode=True),
    )

    assert gate.passed, gate.model_dump(mode="json")
    assert gate.blockers == []
    assert gate.errors == []


def test_v37_demo_project_provider_metadata_is_local_stub_only() -> None:
    profiles = ProviderProfileRepository(DEMO_PROJECT).list_provider_profiles()
    assert [profile.provider_profile_id for profile in profiles] == ["local_stub"]

    profile = profiles[0]
    assert profile.provider_type == "local_stub"
    assert profile.api_key_env is None
    assert profile.secret_ref is None
    assert profile.key_required() is False
    assert profile.model_profiles[0].supports_json is True

    assignments = ProviderModelAssignmentRepository(DEMO_PROJECT).load()
    summary = validate_provider_model_assignments(assignments, profiles)
    assert not summary.warnings
    assert {str(rule.use_case) for rule in summary.rules} == {str(use_case) for use_case in MODEL_ASSIGNMENT_USE_CASES}

    cached = ProviderConnectionStatusCache(DEMO_PROJECT).safe_status("local_stub")
    assert cached is not None
    assert cached["status"] == "connected"
    serialized = json.dumps(cached, sort_keys=True).lower()
    assert "sk-" not in serialized
    assert "authorization" not in serialized
    assert "transient" not in serialized


def test_v37_demo_project_contains_no_runtime_artifacts_or_sensitive_payloads() -> None:
    forbidden_names = {".env", "secrets.yaml", "secrets.yml", "secrets.json"}
    forbidden_suffixes = {".db", ".sqlite", ".sqlite3", ".log", ".py", ".js", ".sh", ".ps1", ".cmd", ".bat", ".exe"}
    forbidden_parts = {"node_modules", "dist", "frontend/dist", "logs", "cache", "caches", "backups", "crash-reports"}
    forbidden_text_markers = (
        "sk-",
        "authorization",
        "bearer ",
        "api_key",
        "transient_api_key",
        "debug_memory",
        "raw_state_delta",
        "raw state_delta",
        "state_delta",
        "mature_only",
    )

    assert DEMO_PROJECT.exists()
    for path in DEMO_PROJECT.rglob("*"):
        rel = path.relative_to(DEMO_PROJECT).as_posix().lower()
        assert not any(part in rel.split("/") for part in forbidden_parts), rel
        if path.is_dir():
            continue
        assert path.name.lower() not in forbidden_names, rel
        assert path.suffix.lower() not in forbidden_suffixes, rel
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        assert not any(marker in text for marker in forbidden_text_markers), rel

    rp_profile = (DEMO_PROJECT / "tavern" / "profiles" / "rp_lina.yaml").read_text(encoding="utf-8")
    assert 'private_persona_authoring_only: ""' in rp_profile
