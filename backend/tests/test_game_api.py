from fastapi.testclient import TestClient

from app.main import app
from app.session_store import InMemorySessionStore


def make_client() -> TestClient:
    app.state.session_store = InMemorySessionStore()
    return TestClient(app)


def test_start_game_returns_initial_visible_state() -> None:
    client = make_client()

    response = client.post("/game/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["turn"] == 0
    assert payload["visible_state"]["location_id"] == "village_square"
    assert "sealed_letter" not in payload["visible_state"]["visible_facts"]


def test_game_input_returns_narrative_and_updates_turn() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "观察四周"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["narrative_text"]
    assert payload["suggested_actions"]
    assert payload["turn"] == 1
    assert "sealed_letter" not in str(payload)


def test_game_input_can_move_session_state() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "去铁匠铺"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["visible_state"]["location_id"] == "blacksmith"
    assert payload["turn"] == 1


def test_get_game_state_returns_current_visible_state() -> None:
    client = make_client()
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/game/state/{session_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["visible_state"]["location_id"] == "village_square"
    assert "sealed_letter" not in str(payload)


def test_unknown_session_returns_clear_404() -> None:
    client = make_client()

    response = client.post(
        "/game/input",
        json={"session_id": "missing", "player_input": "观察"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown game session: missing"
