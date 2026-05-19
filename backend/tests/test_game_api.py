from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.evals.narrative_quality import NarrativeQualityCaseResult, NarrativeQualityReport
from app.main import app
from app.roleplay.dialogue import DialogueManager
from app.roleplay.dialogue import GroupDialogueManager
from app.session_store import InMemorySessionStore


@pytest.fixture(autouse=True)
def reset_app_overrides() -> None:
    yield
    for name in ("settings", "worlds_root", "mods_root"):
        if hasattr(app.state, name):
            delattr(app.state, name)


def make_client(tmp_path: Path | None = None) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.dialogue_manager = DialogueManager()
    app.state.group_dialogue_manager = GroupDialogueManager()
    if tmp_path is not None:
        app.state.save_repository = SQLiteSaveRepository(tmp_path / "api_save.db")
    if hasattr(app.state, "settings"):
        delattr(app.state, "settings")
    if hasattr(app.state, "worlds_root"):
        delattr(app.state, "worlds_root")
    return TestClient(app)


def assert_visible_state_schema(visible_state: dict) -> None:
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
        "factions",
        "known_rumors",
    }
    assert set(visible_state["time"]) >= {"day", "minutes_of_day", "time_of_day", "formatted"}
    assert set(visible_state["location"]) >= {"id", "name", "exits"}
    assert isinstance(visible_state["inventory"], list)
    assert isinstance(visible_state["visible_objects"], list)
    assert isinstance(visible_state["visible_npcs"], list)
    assert isinstance(visible_state["known_facts"], list)
    assert isinstance(visible_state["quests"], list)
    assert isinstance(visible_state["factions"], list)
    assert isinstance(visible_state["known_rumors"], list)


def test_studio_status_returns_safe_summary(tmp_path: Path) -> None:
    app.state.settings = Settings(
        enable_authoring_api=False,
        enable_debug_api=False,
        enable_perf_logging=False,
        llm_provider="local_stub",
        llm_api_key="super-secret-test-key",
    )
    client = make_client(tmp_path)
    app.state.settings = Settings(
        enable_authoring_api=False,
        enable_debug_api=False,
        enable_perf_logging=False,
        llm_provider="local_stub",
        llm_api_key="super-secret-test-key",
    )

    response = client.get("/studio/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend_status"] == "ok"
    assert payload["engine_version"]
    assert payload["schema_version"]
    assert payload["authoring_api_enabled"] is False
    assert payload["debug_api_enabled"] is False
    assert payload["performance_logging_enabled"] is False
    assert payload["llm_provider"] == "local_stub"
    assert "super-secret-test-key" not in response.text
    assert "llm_api_key" not in response.text
    assert "state_deltas" not in response.text
    assert "sealed_letter" not in response.text


def test_studio_status_handles_empty_worlds_and_saves(tmp_path: Path) -> None:
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "empty_studio.db")
    app.state.session_store = InMemorySessionStore()
    app.state.worlds_root = str(tmp_path / "worlds")
    app.state.settings = Settings(enable_authoring_api=False, enable_debug_api=False)
    client = TestClient(app)

    response = client.get("/studio/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["worlds_count"] == 0
    assert payload["recent_saves"] == []
    assert payload["validation_summaries"] == []


def test_narrative_eval_api_runs_and_returns_safe_report(tmp_path: Path) -> None:
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "eval_api.db")
    app.state.session_store = InMemorySessionStore()
    app.state.narrative_eval_reports = []
    app.state.settings = Settings(enable_debug_api=True, llm_api_key="super-secret-test-key")
    client = TestClient(app)

    run_response = client.post("/evals/narrative/run")
    recent_response = client.get("/evals/narrative/recent")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert set(payload) >= {
        "run_id",
        "created_at",
        "total_cases",
        "passed",
        "failed",
        "skipped",
        "failure_reasons",
        "categories",
        "case_results",
    }
    assert "super-secret-test-key" not in run_response.text
    assert "sealed_letter" not in run_response.text
    assert recent_response.status_code == 200
    assert recent_response.json()["reports"][0]["run_id"] == payload["run_id"]

    detail_response = client.get(f"/evals/narrative/{payload['run_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["run_id"] == payload["run_id"]


def test_narrative_eval_api_obeys_debug_toggle(tmp_path: Path) -> None:
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "eval_disabled.db")
    app.state.session_store = InMemorySessionStore()
    app.state.narrative_eval_reports = []
    app.state.settings = Settings(enable_debug_api=False)
    client = TestClient(app)

    assert client.get("/evals/narrative/recent").status_code == 403
    assert client.post("/evals/narrative/run").status_code == 403


def test_narrative_eval_api_redacts_legacy_hidden_failure_reasons(tmp_path: Path) -> None:
    hidden_text = "hidden launch code"
    report = NarrativeQualityReport(
        run_id="legacy-eval-report",
        total_cases=1,
        passed=0,
        failed=1,
        failure_reasons={"case": [f"no_hidden_fact_leakage:forbidden:{hidden_text}"]},
        case_results=[
            NarrativeQualityCaseResult(
                case_id="case",
                category="visibility",
                passed=False,
                failure_reasons=[f"no_hidden_fact_leakage:forbidden:{hidden_text}"],
            )
        ],
    )
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "eval_redaction.db")
    app.state.session_store = InMemorySessionStore()
    app.state.narrative_eval_reports = [report]
    app.state.settings = Settings(enable_debug_api=True)
    client = TestClient(app)

    response = client.get("/evals/narrative/legacy-eval-report")

    assert response.status_code == 200
    assert hidden_text not in response.text
    assert ":forbidden:[redacted]" in response.text


def test_start_game_returns_initial_visible_state() -> None:
    client = make_client()

    response = client.post("/game/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["world_id"] == "mist_valley"
    assert payload["turn"] == 0
    assert payload["visible_state"]["world_id"] == "mist_valley"
    assert payload["visible_state"]["turn"] == 0
    assert payload["visible_state"]["location"]["id"] == "village_square"
    assert_visible_state_schema(payload["visible_state"])
    assert "sealed_letter" not in str(payload["visible_state"])


def test_start_game_defaults_to_mist_valley() -> None:
    client = make_client()

    response = client.post("/game/start")

    assert response.status_code == 200
    assert response.json()["world_id"] == "mist_valley"


def test_start_game_accepts_world_id() -> None:
    client = make_client()

    response = client.post("/game/start", json={"world_id": "mist_valley"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "mist_valley"
    assert payload["visible_state"]["world_id"] == "mist_valley"


def test_start_game_unknown_world_returns_clear_404() -> None:
    client = make_client()

    response = client.post("/game/start", json={"world_id": "missing_world"})

    assert response.status_code == 404
    assert response.json()["detail"] == "World pack not found: missing_world"


def test_visible_state_time_inventory_and_quests_are_present() -> None:
    client = make_client()

    visible_state = client.post("/game/start").json()["visible_state"]

    assert visible_state["time"]["formatted"] == "Day 1, 08:00"
    assert visible_state["time"]["time_of_day"] == "morning"
    assert visible_state["inventory"] == []
    assert visible_state["quests"][0]["id"] == "missing_tools"
    assert visible_state["quests"][0]["status"] == "active"
    assert visible_state["quests"][0]["current_stage"] == "ask_harlan"
    assert not any(quest["id"] == "sealed_letter" for quest in visible_state["quests"])
    assert any(faction["id"] == "village_council" for faction in visible_state["factions"])
    assert not any(faction["id"] == "old_road_smugglers" for faction in visible_state["factions"])


def test_visible_state_exposes_only_visible_objects_npcs_and_known_facts() -> None:
    client = make_client()

    visible_state = client.post("/game/start").json()["visible_state"]

    assert {"id": "notice_board"} in visible_state["visible_objects"]
    assert not any(item["id"] == "sealed_letter" for item in visible_state["visible_objects"])
    assert not any(npc["id"] == "harlan" for npc in visible_state["visible_npcs"])
    assert any(fact["id"] == "village_square_is_misty" for fact in visible_state["known_facts"])
    assert "sealed_letter_under_stone" not in str(visible_state)
    assert "secrets" not in str(visible_state)


def test_game_input_returns_narrative_and_updates_turn() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "\u89c2\u5bdf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["narrative_text"]
    assert payload["suggested_actions"]
    assert payload["turn"] == 1
    assert payload["visible_state"]["turn"] == 1
    assert "sealed_letter" not in str(payload)


def test_game_input_can_move_session_state() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "smithy"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["visible_state"]["location"]["id"] == "blacksmith"
    assert payload["turn"] == 1


def test_dialogue_mode_api_uses_safe_context_and_rule_delta() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "smithy"})

    start_response = client.post(
        "/game/dialogue/start",
        json={"game_session_id": session_id, "focus_npc_id": "harlan", "dialogue_mode": "focused"},
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()
    dialogue_session_id = start_payload["dialogue_session"]["session_id"]
    assert start_payload["dialogue_session"]["focus_npc_id"] == "harlan"
    assert "sealed_letter_under_stone" not in str(start_payload)
    assert "state_deltas" not in str(start_payload)

    continue_response = client.post(
        "/game/dialogue/continue",
        json={"dialogue_session_id": dialogue_session_id, "player_input": "thank you for helping"},
    )

    assert continue_response.status_code == 200
    payload = continue_response.json()
    assert payload["dialogue_session"]["status"] == "active"
    assert "relationship_tone_summary" in payload["dialogue_context"]
    assert "hidden_facts" not in str(payload)


def test_get_game_state_returns_current_visible_state() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/game/state/{session_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["visible_state"]["location"]["id"] == "village_square"
    assert "sealed_letter" not in str(payload)


def test_unknown_session_returns_clear_404() -> None:
    client = make_client()

    response = client.post(
        "/game/input",
        json={"session_id": "missing", "player_input": "\u89c2\u5bdf"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown game session: missing"


def test_save_game_success(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.post(f"/game/{session_id}/save")

    assert response.status_code == 200
    payload = response.json()
    assert payload["save_id"]
    assert payload["session_id"] == session_id
    assert payload["world_id"] == "mist_valley"
    assert payload["turn"] == 0

    saves = client.get("/game/saves").json()["saves"]
    assert saves[0]["save_id"] == payload["save_id"]
    assert saves[0]["world_id"] == "mist_valley"
    assert saves[0]["world_name"] == "Mist Valley"
    assert saves[0]["turn"] == 0
    assert saves[0]["current_location_name"] == "Village Square"
    assert saves[0]["formatted_time"] == "Day 1, 08:00"
    assert "hidden_facts" not in str(saves)


def test_list_saves_world_filter_and_summary_do_not_leak_hidden_facts(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    client.post(f"/game/{session_id}/save")

    filtered = client.get("/game/saves?world_id=mist_valley")
    missing_world = client.get("/game/saves?world_id=missing_world")

    assert filtered.status_code == 200
    assert len(filtered.json()["saves"]) == 1
    assert missing_world.status_code == 200
    assert missing_world.json()["saves"] == []
    assert "sealed_letter_under_stone" not in str(filtered.json())
    assert "state_deltas" not in str(filtered.json())


def test_load_game_success(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    response = client.post(f"/game/load/{save_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["save_id"] == save_id
    assert payload["session_id"] != session_id
    assert payload["turn"] == 0
    assert payload["visible_state"]["world_id"] == "mist_valley"
    assert "sealed_letter" not in str(payload)
    assert "hidden_facts" not in str(payload)


def test_loaded_game_can_continue_without_turn_drift(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    first_input = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "smithy"},
    )
    assert first_input.json()["turn"] == 1
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    loaded_session_id = client.post(f"/game/load/{save_id}").json()["session_id"]

    response = client.post(
        "/game/input",
        json={"session_id": loaded_session_id, "player_input": "\u89c2\u5bdf"},
    )

    assert response.status_code == 200
    assert response.json()["turn"] == 2


def test_load_missing_save_returns_clear_404(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post("/game/load/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Save not found: missing"


def test_delete_save_success_and_missing_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    delete_response = client.delete(f"/game/saves/{save_id}")
    missing_response = client.delete("/game/saves/missing")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"save_id": save_id, "deleted": True}
    assert client.get("/game/saves").json()["saves"] == []
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Save not found: missing"


def test_save_load_api_does_not_leak_hidden_facts(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    list_payload = client.get("/game/saves").json()
    load_payload = client.post(f"/game/load/{save_id}").json()

    assert "sealed_letter_under_stone" not in str(list_payload)
    assert "sealed_letter_under_stone" not in str(load_payload)
    assert "hidden_facts" not in str(list_payload)
    assert "hidden_facts" not in str(load_payload)


def test_save_migration_status_for_current_save(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    response = client.get(f"/game/saves/{save_id}/migration-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["save_id"] == save_id
    assert payload["schema_version"] == "0.6"
    assert payload["needs_migration"] is False
    assert "state_json" not in str(payload)
    assert "state_deltas" not in str(payload)


def test_migration_list_api_returns_available_migrations() -> None:
    client = make_client()

    response = client.get("/migrations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["migrations"][0]["migration_id"] == "legacy->0.6"


def test_save_migration_alias_apply_migrates_and_records_history(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    repository = app.state.save_repository
    save = repository.get_save(save_id)
    state_payload = json.loads(save.state_json)
    state_payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(state_payload), save_id),
        )

    response = client.post(f"/saves/{save_id}/migrate")
    migrated = repository.get_save(save_id)

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is False
    assert payload["backup_save_id"] == f"{save_id}.backup"
    assert payload["applied_migrations"][0]["migration_id"] == "legacy->0.6"
    assert migrated.schema_version == "0.6"
    assert "legacy->0.6" in migrated.migration_history


def test_missing_save_migration_api_returns_clear_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    status_response = client.get("/saves/missing/migration-status")
    dry_run_response = client.post("/saves/missing/migrate-dry-run")

    assert status_response.status_code == 404
    assert status_response.json()["detail"] == "Save not found: missing"
    assert dry_run_response.status_code == 400
    assert dry_run_response.json()["detail"] == "Save not found: missing"


def test_save_migration_dry_run_does_not_mutate_legacy_save(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start").json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    repository = app.state.save_repository
    save = repository.get_save(save_id)
    state_payload = json.loads(save.state_json)
    state_payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(state_payload), save_id),
        )

    response = client.post(f"/game/saves/{save_id}/migrate-dry-run")
    after = repository.get_save(save_id)

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["applied_migrations"][0]["migration_id"] == "legacy->0.6"
    assert after.schema_version == "legacy"
    assert after.migration_history == "[]"
