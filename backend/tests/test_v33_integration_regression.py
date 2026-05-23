from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"


def _client(tmp_path: Path, *, debug_enabled: bool = False) -> TestClient:
    database_path = tmp_path / "v33.sqlite"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=f"sqlite:///{database_path}",
        llm_provider="mock",
        llm_api_key="sk-test-v33-secret-must-not-appear",
        enable_debug_api=debug_enabled,
        enable_authoring_api=True,
        enable_module_api=True,
        enable_eval_api=True,
        enable_playtest_api=True,
    )
    return TestClient(app)


def _assert_visible_state(payload: dict) -> None:
    visible_state = payload["visible_state"]
    assert set(visible_state) >= {
        "world_id",
        "turn",
        "time",
        "location",
        "inventory",
        "visible_objects",
        "visible_npcs",
        "known_facts",
        "quests",
    }
    serialized = json.dumps(visible_state, ensure_ascii=False).lower()
    assert "state_delta" not in serialized
    assert "npc secret" not in serialized
    assert "debug memory" not in serialized
    assert "sk-test-v33-secret-must-not-appear" not in serialized


def test_v33_world_game_api_save_and_eventlog_boundaries(tmp_path: Path) -> None:
    client = _client(tmp_path)

    start = client.post("/game/start", json={"world_id": "mist_valley"})
    assert start.status_code == 200, start.text
    _assert_visible_state(start.json())
    session_id = start.json()["session_id"]

    game_input = client.post("/game/input", json={"session_id": session_id, "player_input": "search"})
    assert game_input.status_code == 200, game_input.text
    _assert_visible_state(game_input.json())
    assert isinstance(game_input.json()["suggested_actions"], list)

    state = client.get(f"/game/state/{session_id}")
    assert state.status_code == 200
    _assert_visible_state(state.json())

    game_loop = app.state.session_store.get_session(session_id)
    assert game_loop is not None
    events = game_loop.event_log.list_events()
    assert events, "world-changing flow must record EventLog entries"
    assert any(event.state_deltas for event in events), "successful world actions must carry StateDelta entries"

    save = client.post(f"/game/{session_id}/save")
    assert save.status_code == 200, save.text
    saves = client.get("/game/saves")
    assert saves.status_code == 200
    assert saves.json()["saves"]
    save_id = saves.json()["saves"][0]["save_id"]
    loaded = client.post(f"/game/load/{save_id}")
    assert loaded.status_code == 200
    _assert_visible_state(loaded.json())

    combined = "\n".join([start.text, game_input.text, state.text, saves.text, loaded.text]).lower()
    assert "sk-test-v33-secret-must-not-appear" not in combined
    assert "raw_env" not in combined
    assert "provider_secret" not in combined


def test_v33_debug_timeline_is_gated_and_raw_deltas_are_not_normal_api(tmp_path: Path) -> None:
    disabled_client = _client(tmp_path, debug_enabled=False)
    start = disabled_client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start.json()["session_id"]
    disabled_client.post("/game/input", json={"session_id": session_id, "player_input": "search"})

    debug_disabled = disabled_client.get(f"/debug/sessions/{session_id}/events")
    assert debug_disabled.status_code == 403
    assert "Debug API is disabled" in debug_disabled.text

    state = disabled_client.get(f"/game/state/{session_id}")
    assert state.status_code == 200
    assert "state_deltas" not in state.text

    enabled_root = tmp_path / "enabled"
    enabled_root.mkdir()
    enabled_client = _client(enabled_root, debug_enabled=True)
    enabled_start = enabled_client.post("/game/start", json={"world_id": "mist_valley"})
    enabled_session_id = enabled_start.json()["session_id"]
    enabled_client.post("/game/input", json={"session_id": enabled_session_id, "player_input": "search"})
    debug_enabled = enabled_client.get(f"/debug/sessions/{enabled_session_id}/events")
    assert debug_enabled.status_code == 200
    assert debug_enabled.json()["events"]
    assert "state_deltas" in debug_enabled.text
    assert "sk-test-v33-secret-must-not-appear" not in debug_enabled.text


def test_v33_provider_gateway_world_routing_and_safe_status(tmp_path: Path) -> None:
    client = _client(tmp_path)
    status = client.get("/studio/config")
    if status.status_code == 404:
        status = client.get("/studio/status")
    assert status.status_code == 200
    assert "sk-test-v33-secret-must-not-appear" not in status.text
    assert "llm_api_key" not in status.text

    session_store = (REPO_ROOT / "backend" / "app" / "session_store.py").read_text(encoding="utf-8")
    assert "world_routed_provider_from_settings" in session_store
    assert "IntentParser(provider" in session_store
    assert "Narrator(provider" in session_store


def test_v33_frontend_world_ui_pro_static_regression() -> None:
    app_source = (FRONTEND / "src" / "App.tsx").read_text(encoding="utf-8")
    world_source = (FRONTEND / "src" / "worldUi.tsx").read_text(encoding="utf-8")
    package_source = (FRONTEND / "package.json").read_text(encoding="utf-8")
    check_source = (FRONTEND / "scripts" / "check-v33-world-ui.mjs").read_text(encoding="utf-8")
    combined = f"{app_source}\n{world_source}\n{package_source}\n{check_source}"

    for token in [
        "WorldWorkspaceShell",
        "WorldPlayMainView",
        "MapLocationPanel",
        "NPCRelationshipPanel",
        "QuestJournalPanel",
        "InventoryTradePanel",
        "TacticalCombatPanel",
        "EconomyDashboardPanel",
        "FactionWarDashboardPanel",
        "DeductionBoardPanel",
        "SurvivalTravelPanel",
        "WorldAdvancedModulePanels",
        "WorldTimelineEventLogPanel",
        "VisibleStateInspector",
        "WorldSaveLoadPanel",
        "WorldQualityPlaytestPanel",
        "WorldPromptProviderPanel",
        "WorldActionInputPanel",
        "DebugGate",
        "check:v33-world-ui",
    ]:
        assert token in combined

    assert "visible_state" in combined
    assert "API key" in combined
    assert "hidden facts" in combined
    assert "NPC secrets" in combined
    assert "raw state_deltas" in combined
    assert "ENABLE_DEBUG_API" in combined
    assert "does not directly modify GameState" in combined
    assert "No account" in combined
    assert "No cloud sync" in combined
    assert "No online marketplace" in combined
    assert "No online play" in combined

    assert not re.search(r"<input[^>]+name=[\"']api_key[\"']", combined, flags=re.IGNORECASE)
    assert "sk-test-v33-secret-must-not-appear" not in combined
    assert not re.search(r"<button[^>]*>\s*(Account|Cloud Sync|Online Play|Online Marketplace)\s*</button>", combined, flags=re.IGNORECASE)
    assert "apply_delta(" not in app_source
    assert "StateDelta(" not in app_source
    assert "submitPlayerInput(sessionId" in app_source


def test_v33_world_ui_normal_components_do_not_render_hidden_debug_or_mature_content() -> None:
    world_source = (FRONTEND / "src" / "worldUi.tsx").read_text(encoding="utf-8")
    normal_component_area = world_source.split("export function DebugGate", maxsplit=1)[0]

    assert "raw GameState" in normal_component_area
    assert "not raw GameState" not in normal_component_area.lower()
    assert "mature_only" not in normal_component_area
    assert "private memory" not in normal_component_area.lower()
    assert "provider secret" in normal_component_area
    assert "api_key" not in normal_component_area.lower()
    assert "JSON.stringify(event.state_deltas" not in normal_component_area
    assert "DebugGate" in world_source
