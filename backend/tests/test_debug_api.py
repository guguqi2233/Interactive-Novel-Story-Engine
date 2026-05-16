from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, debug_enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "debug_api.db")
    app.state.settings = Settings(
        enable_debug_api=debug_enabled,
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def test_debug_enabled_reads_session_events(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]

    client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "smithy"},
    )
    response = client.get(f"/debug/sessions/{session_id}/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert len(payload["events"]) >= 1
    assert set(payload["events"][0]) >= {
        "turn",
        "event_id",
        "actor_id",
        "action_type",
        "result",
        "state_deltas",
        "visible_to_player",
        "created_at",
    }


def test_debug_disabled_returns_forbidden(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=False)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/events")

    assert response.status_code == 403
    assert response.json()["detail"] == "Debug API is disabled"


def test_debug_response_does_not_include_api_key(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "wait"},
    )

    payload = client.get(f"/debug/sessions/{session_id}/events").text

    assert "super-secret-test-key" not in payload
    assert "llm_api_key" not in payload


def test_debug_save_events_are_ordered_by_turn(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "smithy"},
    )
    client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "search"},
    )
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    response = client.get(f"/debug/saves/{save_id}/events")

    assert response.status_code == 200
    events = response.json()["events"]
    assert [event["turn"] for event in events] == sorted(event["turn"] for event in events)
    player_events = [event for event in events if event["actor_id"] == "player"]
    assert [event["action_type"] for event in player_events] == ["move", "search"]
