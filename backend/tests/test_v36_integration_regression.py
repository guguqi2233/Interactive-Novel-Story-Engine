from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_connection_cache import ProviderConnectionStatusCache
from app.llm.provider_connection_test import ProviderConnectionStatus
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


ROOT = Path(__file__).resolve().parents[2]
TRANSIENT_KEY = "sk-test-v36-integration-transient-secret"


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _client(
    tmp_path: Path,
    *,
    debug: bool = False,
) -> tuple[TestClient, object, object]:
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = _project_repo(tmp_path)
    app.state.settings = Settings(
        enable_authoring_api=True,
        enable_debug_api=debug,
        llm_provider="mock",
    )
    return TestClient(app), previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def _component_source(source: str, name: str) -> str:
    marker = f"function {name}"
    start = source.find(marker)
    assert start >= 0, f"Missing component {name}"
    next_function = source.find("\nfunction ", start + len(marker))
    next_const = source.find("\nconst ", start + len(marker))
    candidates = [index for index in [next_function, next_const] if index >= 0]
    end = min(candidates) if candidates else len(source)
    return source[start:end]


def test_v36_frontend_integration_check_script_and_previous_smoke_scripts_are_registered() -> None:
    package_json = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    check_script = ROOT / "frontend" / "scripts" / "check-v36-integration-regression.mjs"
    script_source = check_script.read_text(encoding="utf-8")

    assert check_script.exists()
    for script_name in [
        "check:v29-ui",
        "check:v30-ux",
        "check:v31-novel-ui",
        "check:v32-tavern-ui",
        "check:v33-world-ui",
        "check:v34-authoring-ui",
        "check:v35-qa-debug-provider-ui",
        "check:v36-performance-a11y",
        "check:v36-integration-regression",
    ]:
        assert script_name in package_json["scripts"]

    # The integration check runs only allowlisted local static checks with the
    # Node executable; it does not expose a generic shell or provider call.
    assert "execFileSync(process.execPath" in script_source
    assert "previousVersionSmokeScripts" in script_source
    assert "v36SafetyScripts" in script_source
    assert "PROVIDER_TEST_MODE" in script_source
    assert "child_process.exec(" not in script_source
    assert "npm" not in script_source
    assert "http.request" not in script_source
    assert "fetch(" not in script_source


def test_v36_long_list_debug_and_visibility_static_boundaries() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    error_boundary = (ROOT / "frontend" / "src" / "errorBoundary.tsx").read_text(encoding="utf-8")
    safe_cache = (ROOT / "frontend" / "src" / "safeApiCache.ts").read_text(encoding="utf-8")

    required_tokens = [
        'data-windowed-eventlog="true"',
        "visibleEvents.map((event)",
        'data-windowed-timeline="true"',
        "windowedTurns.map((turnGroup)",
        'data-windowed-statedelta="true"',
        "visibleRows.map((row)",
        'data-windowed-quality-report="true"',
        'data-windowed-hidden-leak-report="true"',
        'data-windowed-provider-model-list="true"',
        "visibleModelRows.map((model)",
        "function lazyNamed",
        "<Suspense",
        "<AppErrorBoundary",
        "SHORTCUT_DANGEROUS_ACTION_BLOCKLIST",
        "REDUCED_MOTION_PREF_KEY",
        "prefers-reduced-motion: reduce",
    ]
    for token in required_tokens:
        assert token in app_source

    state_delta_use = app_source.index("<StateDeltaViewerPanel")
    debug_gate_before = app_source.rfind("<DebugGate", 0, state_delta_use)
    debug_gate_close_before = app_source.rfind("</DebugGate>", 0, state_delta_use)
    assert debug_gate_before >= 0
    assert debug_gate_before > debug_gate_close_before

    eventlog_source = _component_source(app_source, "EventLogViewerPanel")
    timeline_source = _component_source(app_source, "TimelineReplayPanel")
    state_delta_source = _component_source(app_source, "StateDeltaViewerPanel")
    provider_source = _component_source(app_source, "ProviderConnectivityDashboard")
    quality_source = _component_source(app_source, "UnifiedQualityGateDashboard")
    hidden_leak_source = _component_source(app_source, "HiddenLeakReportPanel")

    assert "filteredEvents.map(" not in eventlog_source
    assert "JSON.stringify(event" not in eventlog_source
    assert "filteredTurns.map(" not in timeline_source
    assert "<span>{event.result}</span>" not in timeline_source
    assert "<span>{event.action_type}</span>" not in timeline_source
    assert "<span>{event.actor_id}</span>" not in timeline_source
    assert "timelineEventSafeSummary" in app_source
    assert "data-timeline-redacted-normal-summary" in app_source
    assert "Hidden/debug summary is redacted from normal replay view." in app_source
    assert "filteredRows.map(" not in state_delta_source
    assert "filteredModelRows.map(" not in provider_source
    assert "filteredIssues.map(" not in quality_source
    assert "filteredIssues.map(" not in hidden_leak_source

    assert "redactedValue" in state_delta_source
    assert "Hidden text and secrets are never printed" in hidden_leak_source
    assert "formatSafeErrorSummary" in error_boundary
    assert "stack trace redacted" in error_boundary
    assert "containsUnsafeCachePayload" in safe_cache
    assert "const safeApiCacheStore = new Map" in safe_cache
    for forbidden_storage in ["localStorage", "sessionStorage", "indexedDB", "serviceWorker"]:
      assert forbidden_storage not in safe_cache

    combined = "\n".join([app_source, error_boundary, safe_cache])
    assert 'name="api_key"' not in combined
    assert "sk-live-" not in combined
    assert "sk-prod-" not in combined
    assert "remotePackageDownload" not in combined
    assert "cloudSyncEnabled" not in combined


def test_v36_provider_status_cache_stale_refresh_and_secret_boundaries(tmp_path: Path) -> None:
    cache = ProviderConnectionStatusCache(tmp_path, ttl_seconds=5)
    now = datetime.now(UTC)
    current_status = ProviderConnectionStatus(
        status="connected",
        safe_message=f"Connected with Authorization: Bearer {TRANSIENT_KEY}",
        provider_type="relay",
        tested_at=now.isoformat(),
        latency_ms=12.0,
        error_type=None,
        redaction_applied=True,
    )
    stale_status = ProviderConnectionStatus(
        status=f"timeout {TRANSIENT_KEY}",
        safe_message=f"Timed out with transient_api_key={TRANSIENT_KEY}",
        provider_type="relay",
        tested_at=(now - timedelta(seconds=60)).isoformat(),
        latency_ms=None,
        error_type=f"timeout {TRANSIENT_KEY}",
        redaction_applied=True,
    )

    cache.save_status("relay_current", current_status, model_count=42)
    cache.save_status("relay_stale", stale_status, model_count=0)
    current = cache.safe_status("relay_current")
    stale = cache.safe_status("relay_stale")
    cache_payload = cache.cache_path.read_text(encoding="utf-8")

    assert current is not None
    assert current["cache_state"] == "fresh"
    assert current["stale"] is False
    assert current["model_count"] == 42
    assert stale is not None
    assert stale["cache_state"] == "stale"
    assert stale["stale"] is True

    assert TRANSIENT_KEY not in cache_payload
    assert "transient_api_key" not in cache_payload
    assert "Authorization" not in cache_payload
    assert "safe_message" not in cache_payload
    assert "raw_provider_response" not in cache_payload
    assert "api_key" not in cache_payload


def test_v36_debug_replay_is_read_only_and_normal_state_stays_visible_only(tmp_path: Path) -> None:
    client, previous_repo, previous_settings = _client(tmp_path, debug=False)
    try:
        start = client.post("/game/start", json={"world_id": "mist_valley"})
        assert start.status_code == 200
        session_id = start.json()["session_id"]
        action = client.post("/game/input", json={"session_id": session_id, "player_input": "look around"})
        assert action.status_code == 200

        normal_state = client.get(f"/game/state/{session_id}")
        assert normal_state.status_code == 200
        disabled_events = client.get(f"/debug/sessions/{session_id}/events")
        disabled_timeline = client.get(f"/debug/sessions/{session_id}/timeline")
        assert disabled_events.status_code == 403
        assert disabled_timeline.status_code == 403

        app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
        debug_events = client.get(f"/debug/sessions/{session_id}/events")
        debug_timeline = client.get(f"/debug/sessions/{session_id}/timeline")
        state_after_debug_reads = client.get(f"/game/state/{session_id}")
    finally:
        _restore(previous_repo, previous_settings)

    assert "visible_state" in normal_state.text
    assert "state_deltas" not in normal_state.text
    assert "npc_knowledge" not in normal_state.text
    assert TRANSIENT_KEY not in normal_state.text
    assert debug_events.status_code == 200
    assert debug_timeline.status_code == 200
    assert "state_deltas" in debug_events.text
    assert "Authorization" not in debug_events.text + debug_timeline.text
    assert state_after_debug_reads.json() == normal_state.json()
