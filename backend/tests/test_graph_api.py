from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import FactState, FactVisibility, NPCState, RelationshipState
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, debug_enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "graph_api.db")
    app.state.settings = Settings(
        enable_debug_api=debug_enabled,
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def test_player_relationship_graph_only_contains_known_visible_relationships(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    game_loop.state.relationships["hidden_rivalry"] = RelationshipState(
        id="hidden_rivalry",
        source_id="harlan",
        target_id="player",
        relation_type="rival",
        trust=-5,
        known_by_player=False,
    )

    response = client.get(f"/game/{session_id}/graphs/relationships")

    assert response.status_code == 200
    payload = response.json()
    edge_ids = {edge["metadata_safe"]["relationship_id"] for edge in payload["edges"]}
    assert "harlan_player_wary" in edge_ids
    assert "hidden_rivalry" not in edge_ids
    assert all(edge["visibility"] == "player_visible" for edge in payload["edges"])


def test_hidden_npc_relationship_does_not_enter_player_graph(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    game_loop.state.npcs["shadow"] = NPCState(
        id="shadow",
        location_id="village_square",
        visible=True,
        hidden=True,
    )
    game_loop.state.relationships["shadow_player"] = RelationshipState(
        id="shadow_player",
        source_id="shadow",
        target_id="player",
        relation_type="watching",
        trust=0,
        known_by_player=True,
    )

    response = client.get(f"/game/{session_id}/graphs/relationships")

    assert response.status_code == 200
    assert "shadow" not in response.text


def test_hidden_npc_relationship_does_not_enter_visible_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    game_loop.state.npcs["shadow"] = NPCState(
        id="shadow",
        location_id="village_square",
        visible=True,
        hidden=True,
    )
    game_loop.state.relationships["shadow_player"] = RelationshipState(
        id="shadow_player",
        source_id="shadow",
        target_id="player",
        relation_type="watching",
        trust=0,
        known_by_player=True,
    )

    response = client.get(f"/game/state/{session_id}")

    assert response.status_code == 200
    assert "shadow_player" not in response.text
    assert "shadow" not in response.text


def test_debug_graph_disabled_returns_forbidden(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=False)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/graphs/relationships")

    assert response.status_code == 403
    assert response.json()["detail"] == "Debug API is disabled"


def test_debug_relationship_graph_returns_debug_only_relationships(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    game_loop.state.relationships["hidden_rivalry"] = RelationshipState(
        id="hidden_rivalry",
        source_id="harlan",
        target_id="player",
        relation_type="rival",
        trust=-5,
        known_by_player=False,
    )

    response = client.get(f"/debug/sessions/{session_id}/graphs/relationships")

    assert response.status_code == 200
    payload = response.json()
    edge_ids = {edge["metadata_safe"]["relationship_id"] for edge in payload["edges"]}
    assert "hidden_rivalry" in edge_ids
    assert any(edge["visibility"] == "debug_only" for edge in payload["edges"])


def test_player_faction_graph_only_shows_known_factions(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]

    response = client.get(f"/game/{session_id}/graphs/factions")

    assert response.status_code == 200
    payload = response.json()
    node_ids = {node["id"] for node in payload["nodes"]}
    assert "village_council" in node_ids
    assert "old_road_smugglers" not in node_ids
    assert all(node["visibility"] == "player_visible" for node in payload["nodes"])


def test_debug_faction_graph_can_show_hidden_faction(tmp_path: Path) -> None:
    client = make_client(tmp_path, debug_enabled=True)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]

    response = client.get(f"/debug/sessions/{session_id}/graphs/factions")

    assert response.status_code == 200
    payload = response.json()
    node_ids = {node["id"] for node in payload["nodes"]}
    assert "old_road_smugglers" in node_ids
    assert any(node["visibility"] == "debug_only" for node in payload["nodes"])


def test_graph_api_does_not_leak_hidden_facts(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    game_loop.state.facts["hidden_graph_fact"] = FactState(
        id="hidden_graph_fact",
        text="The hidden graph phrase should not leak.",
        visibility=FactVisibility.HIDDEN,
    )

    relationship_response = client.get(f"/game/{session_id}/graphs/relationships")
    faction_response = client.get(f"/game/{session_id}/graphs/factions")

    combined = relationship_response.text + faction_response.text
    assert relationship_response.status_code == 200
    assert faction_response.status_code == 200
    assert "hidden_graph_fact" not in combined
    assert "hidden graph phrase" not in combined.lower()
    assert "super-secret-test-key" not in combined


def test_graph_api_does_not_modify_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    before = game_loop.state.model_dump_json()

    client.get(f"/game/{session_id}/graphs/relationships")
    client.get(f"/game/{session_id}/graphs/factions")
    client.get(f"/debug/sessions/{session_id}/graphs/relationships")
    client.get(f"/debug/sessions/{session_id}/graphs/factions")

    assert game_loop.state.model_dump_json() == before
