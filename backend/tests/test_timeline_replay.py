from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, debug_enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "timeline_replay.db")
    app.state.worlds_root = "worlds"
    app.state.settings = Settings(
        enable_debug_api=debug_enabled,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def _make_saved_game(client: TestClient) -> tuple[str, str]:
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "smithy"})
    client.post("/game/input", json={"session_id": session_id, "player_input": "search"})
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    return session_id, save_id


def test_timeline_api_disabled_when_debug_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=False)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/timeline")

    assert response.status_code == 403


def test_debug_enabled_returns_session_timeline(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id, _ = _make_saved_game(client)

    response = client.get(f"/debug/sessions/{session_id}/timeline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "session"
    assert payload["source_id"] == session_id
    assert payload["event_count"] >= 2
    assert payload["turns"][0]["events"][0]["state_deltas"]


def test_timeline_is_stably_sorted_by_turn(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    _, save_id = _make_saved_game(client)

    events = client.get(f"/debug/saves/{save_id}/timeline").json()["turns"]
    turns = [turn["turn"] for turn in events]

    assert turns == sorted(turns)


def test_timeline_supports_turn_range_and_filter(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id, _ = _make_saved_game(client)

    response = client.get(f"/debug/sessions/{session_id}/timeline", params={"turn_from": 1, "event_filter": "player"})

    assert response.status_code == 200
    for turn in response.json()["turns"]:
        assert turn["turn"] >= 1
        assert all(event["event_kind"] == "player" for event in turn["events"])


def test_replay_dry_run_does_not_write_database_and_is_deterministic(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    _, save_id = _make_saved_game(client)
    before = client.get(f"/debug/saves/{save_id}/timeline").json()

    first = client.post(f"/debug/saves/{save_id}/replay-dry-run").json()
    second = client.post(f"/debug/saves/{save_id}/replay-dry-run").json()
    after = client.get(f"/debug/saves/{save_id}/timeline").json()

    assert first["replay_summary"]["event_count"] == second["replay_summary"]["event_count"]
    assert first["replay_summary"]["final_state_checksum"] == second["replay_summary"]["final_state_checksum"]
    assert before == after


def test_timeline_does_not_return_api_key_or_raw_env(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id, _ = _make_saved_game(client)

    body = client.get(f"/debug/sessions/{session_id}/timeline").text.lower()

    assert "super-secret-test-key" not in body
    assert "llm_api_key" not in body
    assert "database_url" not in body


def test_player_api_does_not_return_raw_state_deltas(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id, _ = _make_saved_game(client)

    payload = client.get(f"/game/state/{session_id}").text

    assert "state_deltas" not in payload
