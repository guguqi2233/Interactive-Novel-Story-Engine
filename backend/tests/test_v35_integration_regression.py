from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, PlayerState
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.desktop.diagnostics_bundle import DiagnosticsBundleCreateRequest, DiagnosticsBundleService
from app.desktop.local_logs import LocalLogService
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


TRANSIENT_KEY = "sk-test-v35-integration-transient-secret"


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
) -> tuple[TestClient, ProjectRepository, object, object]:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(
        enable_authoring_api=True,
        enable_debug_api=debug,
        llm_provider="mock",
    )
    return TestClient(app), repo, previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def _create_provider(client: TestClient, provider_id: str = "relay_safe") -> None:
    response = client.post(
        "/projects/demo/providers",
        json={
            "provider_profile_id": provider_id,
            "display_name": "Relay Safe",
            "provider_type": "relay",
            "base_url": "http://relay.local/v1",
            "api_key_env": "RELAY_API_KEY",
        },
    )
    assert response.status_code == 200


def _create_plain_local_provider(client: TestClient) -> None:
    response = client.post(
        "/projects/demo/providers",
        json={
            "provider_profile_id": "plain_local",
            "display_name": "Plain Local",
            "provider_type": "local_stub",
            "requires_api_key": False,
            "model_profiles": [
                {
                    "model_id": "plain",
                    "display_name": "Plain",
                    "supports_text": True,
                    "supports_json": False,
                    "enabled": True,
                }
            ],
        },
    )
    assert response.status_code == 200


def _legacy_state() -> GameState:
    return GameState(
        world_id="migration-world",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
        facts={
            "public_fact": FactState(
                id="public_fact",
                text="The square is open.",
                visibility=FactVisibility.PUBLIC,
            ),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="A sealed cache is below the stones.",
                visibility=FactVisibility.HIDDEN,
            ),
        },
        player_visible_facts={"public_fact"},
    )


def _legacy_event() -> Event:
    return Event(
        event_id="event-1",
        turn=1,
        actor_id="player",
        action_type="wait",
        result="success",
        visible_to_player=True,
        state_deltas=[StateDelta(operation=StateDeltaOperation.INC, path="turn", value=1)],
        allow_empty_delta=False,
    )


def _force_legacy_save(repository: SQLiteSaveRepository, save_id: str, state: GameState) -> None:
    repository.create_save(save_id, state)
    payload = state.model_dump(mode="json")
    payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(payload), save_id),
        )


def test_v35_gameplay_replay_debug_gate_and_visible_state_boundaries(tmp_path: Path) -> None:
    client, _repo, previous_repo, previous_settings = _client(tmp_path, debug=False)
    try:
        start = client.post("/game/start", json={"world_id": "mist_valley"})
        assert start.status_code == 200
        session_id = start.json()["session_id"]

        action = client.post(
            "/game/input",
            json={"session_id": session_id, "player_input": "look around"},
        )
        assert action.status_code == 200

        state_before = client.get(f"/game/state/{session_id}")
        assert state_before.status_code == 200
        normal_payload = state_before.text
        assert "visible_state" in normal_payload
        assert "state_deltas" not in normal_payload
        assert "npc_knowledge" not in normal_payload
        assert "A sealed cache is below the stones." not in normal_payload
        assert TRANSIENT_KEY not in normal_payload

        disabled_timeline = client.get(f"/debug/sessions/{session_id}/timeline")
        disabled_events = client.get(f"/debug/sessions/{session_id}/events")
        assert disabled_timeline.status_code == 403
        assert disabled_events.status_code == 403

        app.state.settings = Settings(
            enable_authoring_api=True,
            enable_debug_api=True,
            llm_provider="mock",
        )
        timeline = client.get(f"/debug/sessions/{session_id}/timeline")
        events = client.get(f"/debug/sessions/{session_id}/events")
        state_after = client.get(f"/game/state/{session_id}")
    finally:
        _restore(previous_repo, previous_settings)

    assert timeline.status_code == 200
    assert events.status_code == 200
    assert "state_deltas" in events.text
    assert "Authorization" not in timeline.text + events.text
    assert TRANSIENT_KEY not in timeline.text + events.text
    assert state_after.json() == state_before.json()


def test_v35_provider_connectivity_model_sync_assignment_and_secret_boundaries(tmp_path: Path) -> None:
    client, repo, previous_repo, previous_settings = _client(tmp_path)
    try:
        connected = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_type": "mock", "timeout_seconds": 1},
        )
        missing_secret = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_type": "openai", "api_key_env": "MISSING_V35_INTEGRATION_KEY"},
        )
        auth_failed = client.post(
            "/projects/demo/providers/test-connection",
            json={
                "provider_type": "openai_compatible",
                "base_url": "http://raw-secret-error.local/v1",
                "transient_api_key": TRANSIENT_KEY,
                "timeout_seconds": 1,
            },
        )

        _create_provider(client)
        fetched = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "openai_compatible",
                "base_url": "http://compatible.local/v1",
                "transient_api_key": TRANSIENT_KEY,
            },
        )
        synced = client.post(
            "/projects/demo/providers/sync-models",
            json={"provider_profile_id": "relay_safe", "transient_api_key": TRANSIENT_KEY},
        )
        models = client.get("/projects/demo/providers/relay_safe/models")
        unsupported = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "custom",
                "base_url": "http://unsupported.local/v1",
                "model_list_endpoint": "/unsupported",
                "transient_api_key": TRANSIENT_KEY,
            },
        )
        assignment = client.post(
            "/projects/demo/providers/model-assignments/validate",
            json={
                "rules": [
                    {
                        "use_case": "world_intent_parse",
                        "primary_provider_id": "relay_safe",
                        "primary_model_id": "fake-chat-small",
                        "fallback_provider_id": "relay_safe",
                        "fallback_model_id": "fake-json-pro",
                        "require_json_support": True,
                        "require_local_only": False,
                        "enabled": True,
                    }
                ]
            },
        )
        _create_plain_local_provider(client)
        json_capability_block = client.post(
            "/projects/demo/providers/model-assignments/validate",
            json={
                "rules": [
                    {
                        "use_case": "structured_json",
                        "primary_provider_id": "plain_local",
                        "primary_model_id": "plain",
                        "require_json_support": True,
                        "require_local_only": True,
                        "enabled": True,
                    }
                ]
            },
        )
        profile_text = (Path(repo.load_project("demo").project_root) / "providers" / "profiles" / "relay_safe.yaml").read_text(
            encoding="utf-8"
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert connected.status_code == 200
    assert connected.json()["status"] == "connected"
    assert missing_secret.status_code == 200
    assert missing_secret.json()["status"] == "missing_secret"
    assert "MISSING_V35_INTEGRATION_KEY" not in missing_secret.text
    assert auth_failed.status_code == 200
    assert auth_failed.json()["status"] == "auth_failed"
    assert fetched.status_code == 200
    assert {model["model_id"] for model in fetched.json()["report"]["models"]} == {
        "fake-chat-small",
        "fake-json-pro",
    }
    assert synced.status_code == 200
    assert synced.json()["report"]["added"] == 2
    assert models.status_code == 200
    assert len(models.json()["models"]) == 2
    assert unsupported.status_code == 200
    assert unsupported.json()["report"]["status"] == "unsupported_model_list"
    assert assignment.status_code == 200
    assert assignment.json()["validation_reports"][0]["ok"] is True
    assert assignment.json()["fallback_chains"]["world_intent_parse"] == [
        "relay_safe/fake-chat-small",
        "relay_safe/fake-json-pro",
    ]
    assert json_capability_block.status_code == 200
    assert json_capability_block.json()["validation_reports"][0]["ok"] is False
    assert "json_use_case_requires_json_support_or_json_fallback" in json_capability_block.json()["validation_reports"][0]["errors"]

    combined = "\n".join(
        [
            connected.text,
            missing_secret.text,
            auth_failed.text,
            fetched.text,
            synced.text,
            models.text,
            unsupported.text,
            assignment.text,
            json_capability_block.text,
            profile_text,
        ]
    )
    assert TRANSIENT_KEY not in combined
    assert "Authorization" not in combined
    assert "transient_api_key" not in profile_text


def test_v35_diagnostics_logs_and_save_migration_dry_run_are_redacted_and_read_only(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "provider.log").write_text(
        (
            f"provider failed transient_api_key={TRANSIENT_KEY} "
            "Authorization: Bearer sk-test-v35-log-bearer-secret "
            "raw_provider_response={api_key:'sk-test-v35-raw-log-secret'}"
        ),
        encoding="utf-8",
    )

    log_response = LocalLogService(tmp_path).list_safe_logs(limit=10)
    log_payload = json.dumps([entry.model_dump(mode="json") for entry in log_response.logs])
    diagnostics = DiagnosticsBundleService(tmp_path)
    request = DiagnosticsBundleCreateRequest(project_id="demo")
    preview = diagnostics.preview_bundle(request)
    created = diagnostics.create_bundle(request)
    bundle = next((tmp_path / "exports" / "diagnostics").glob("*.zip"))
    with zipfile.ZipFile(bundle, "r") as archive:
        bundle_payload = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())

    repository = SQLiteSaveRepository(tmp_path / "migration.db")
    state = _legacy_state()
    _force_legacy_save(repository, "save-1", state)
    repository.append_event("save-1", _legacy_event())
    migration = MigrationService(repository).dry_run("save-1")
    save_after_dry_run = repository.get_save("save-1")
    migration_payload = json.dumps(migration.model_dump(mode="json"), default=str)

    assert log_response.logs
    assert any(entry.redacted for entry in log_response.logs)
    assert created.created is True
    assert preview.safe_payload["provider"] == {
        "configured": "safe_summary_only",
        "credential_status": "redacted",
    }
    assert migration.dry_run is True
    assert save_after_dry_run.schema_version == "legacy"
    assert save_after_dry_run.migration_history == "[]"

    combined = "\n".join([log_payload, bundle_payload, migration_payload])
    assert TRANSIENT_KEY not in combined
    assert "Authorization" not in combined
    assert "sk-test-v35-log-bearer-secret" not in combined
    assert "sk-test-v35-raw-log-secret" not in combined
    assert "raw_provider_response" not in combined
    assert "A sealed cache is below the stones." not in combined


def test_v35_frontend_qa_debug_provider_static_boundaries() -> None:
    frontend = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    check_script = Path("frontend/scripts/check-v35-qa-debug-provider-ui.mjs").read_text(encoding="utf-8")
    combined = frontend + "\n" + api + "\n" + check_script

    required_tokens = [
        "TimelineReplayPanel",
        "EventLogViewerPanel",
        "StateDeltaViewerPanel",
        "VisibleDebugStateCompare",
        "HiddenLeakReportPanel",
        "UnifiedQualityGateDashboard",
        "ProviderConnectivityDashboard",
        "ProviderUsageCostDashboard",
        "SafeDebugExportWizard",
        "DebugGate",
        "ENABLE_DEBUG_API required",
        "no online marketplace",
        "no remote download",
    ]
    for token in required_tokens:
        assert token in combined

    assert 'name="api_key"' not in combined
    assert "sk-live-" not in combined
    assert "BEGIN OPENAI" not in combined
    assert "remotePackageDownload" not in combined
    assert "cloudSyncEnabled" not in combined
    assert "state_deltas" not in _component_source(frontend, "ProviderConnectivityDashboard")
    assert "state_deltas" not in _component_source(frontend, "ProviderUsageCostDashboard")
    assert "JSON.stringify(debugState" not in combined


def _component_source(source: str, name: str) -> str:
    marker = f"function {name}"
    start = source.find(marker)
    assert start >= 0, f"Missing component {name}"
    next_function = source.find("\nfunction ", start + len(marker))
    next_const = source.find("\nconst ", start + len(marker))
    candidates = [index for index in [next_function, next_const] if index >= 0]
    end = min(candidates) if candidates else len(source)
    return source[start:end]
