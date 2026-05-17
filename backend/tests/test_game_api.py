from pathlib import Path

from fastapi.testclient import TestClient

from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path | None = None) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    if tmp_path is not None:
        app.state.save_repository = SQLiteSaveRepository(tmp_path / "api_save.db")
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
    assert saves[0]["turn"] == 0
    assert "hidden_facts" not in str(saves)


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
