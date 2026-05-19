from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, NPCIntent, NPCState
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


def test_npc_simulation_debug_disabled_returns_forbidden(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=False)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/npc-simulation")

    assert response.status_code == 403


def test_npc_simulation_debug_enabled_returns_summary(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/npc-simulation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["npcs"]
    assert {"npc_id", "intent_count", "plan_count", "known_fact_ids"} <= set(payload["npcs"][0])


def test_npc_simulation_dry_run_does_not_modify_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    npc_id = sorted(game_loop.state.npcs)[0]
    game_loop.state.npcs[npc_id].intent_queue.append(
        NPCIntent(
            id="debug-visit",
            npc_id=npc_id,
            intent_type="visit_location",
            target_id=game_loop.state.npcs[npc_id].location_id,
            target_type="location",
            created_turn=game_loop.state.turn,
            debug_reason="debug dry run",
        )
    )
    before = game_loop.state.model_dump(mode="json")

    response = client.post(f"/debug/sessions/{session_id}/npc-simulation/dry-run-tick")
    after = game_loop.state.model_dump(mode="json")

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["state_unchanged"] is True
    assert before == after


def test_player_api_does_not_return_simulation_debug_data(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    npc_id = sorted(game_loop.state.npcs)[0]
    game_loop.state.npcs[npc_id].intent_queue.append(
        NPCIntent(
            id="debug-secret",
            npc_id=npc_id,
            intent_type="rest",
            created_turn=game_loop.state.turn,
            debug_reason="debug-only reason",
        )
    )

    payload = client.get(f"/game/{session_id}").text

    assert "intent_queue" not in payload
    assert "debug-only reason" not in payload
    assert "debug_reason" not in payload


def test_npc_simulation_debug_does_not_return_api_key_or_raw_env(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]

    payload = client.post(f"/debug/sessions/{session_id}/npc-simulation/dry-run-tick").text

    assert "super-secret-test-key" not in payload
    assert "llm_api_key" not in payload
    assert "raw_env" not in payload


def test_hidden_fact_text_is_redacted_from_simulation_debug(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    npc_id = sorted(game_loop.state.npcs)[0]
    game_loop.state.facts["hidden_fact"] = FactState(
        id="hidden_fact",
        text="The hidden shrine key is buried under the well.",
        visibility=FactVisibility.HIDDEN,
        known_by={npc_id},
    )
    game_loop.state.npcs[npc_id] = game_loop.state.npcs[npc_id].model_copy(
        update={"knowledge": [*game_loop.state.npcs[npc_id].knowledge, "hidden_fact"]}
    )

    response = client.get(f"/debug/sessions/{session_id}/npcs/{npc_id}/simulation")

    assert response.status_code == 200
    payload = response.json()
    assert "hidden_fact" in payload["hidden_fact_ids"]
    assert "hidden shrine key" not in response.text


def test_npc_behavior_timeline_is_sorted_and_redacted(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    npc_id = sorted(game_loop.state.npcs)[0]
    game_loop.event_log.append(
        Event(
            event_id="npc-intent-enqueued-3",
            turn=3,
            actor_id="system",
            action_type="npc_intent_enqueued",
            target_id=npc_id,
            result="queued sk-test-secret",
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"npcs.{npc_id}.intent_queue",
                    value=[],
                    reason="The hidden shrine key is under the well.",
                    metadata={"npc_id": npc_id, "intent_id": "intent-1", "debug_reason": "sk-test-secret"},
                )
            ],
            visible_to_player=False,
        )
    )
    game_loop.event_log.append(
        Event(
            event_id="npc-plan-built-5",
            turn=5,
            actor_id="system",
            action_type="npc_plan_built",
            target_id=npc_id,
            result="planned",
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"npcs.{npc_id}.location_id",
                    value="square",
                    metadata={"npc_id": npc_id, "plan_id": "plan-1"},
                )
            ],
            visible_to_player=False,
        )
    )

    response = client.get(f"/debug/sessions/{session_id}/npcs/{npc_id}/behavior-timeline?turn_from=3&turn_to=5")

    assert response.status_code == 200
    payload = response.json()
    assert [entry["turn"] for entry in payload["entries"]] == [3, 5]
    assert payload["entries"][0]["intent_id"] == "intent-1"
    assert payload["entries"][1]["location_id"] == "square"
    assert "sk-test-secret" not in response.text
    assert "hidden shrine key" not in response.text


def test_npc_behavior_timeline_debug_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=False)
    session_id = client.post("/game/start").json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/npcs/harlan/behavior-timeline")

    assert response.status_code == 403


def test_player_api_does_not_return_behavior_timeline(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]

    payload = client.get(f"/game/{session_id}").text

    assert "behavior-timeline" not in payload
    assert "NPCBehaviorTimeline" not in payload
