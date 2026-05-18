from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import RelationshipState
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.social_graph_authoring import (
    parse_social_authoring_graph,
    preview_social_authoring_graph,
    social_graph_to_yaml,
)
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path, *, authoring: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "social_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=authoring, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_faction_authoring_graph_parses(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)

    graph = parse_social_authoring_graph("mist_valley", ContentAuthoringService(worlds_root))

    assert [faction.id for faction in graph.faction_graph.factions] == [
        "village_council",
        "old_road_smugglers",
    ]
    assert any(edge.source_faction_id == "village_council" for edge in graph.faction_graph.conflict_edges)


def test_relationship_authoring_graph_parses(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)

    graph = parse_social_authoring_graph("mist_valley", ContentAuthoringService(worlds_root))

    assert any(node.id == "harlan" for node in graph.relationship_graph.nodes)
    assert graph.relationship_graph.relationships[0].id == "harlan_player_wary"


def test_social_graph_roundtrip_to_yaml(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    graph = parse_social_authoring_graph("mist_valley", ContentAuthoringService(worlds_root))
    graph.relationship_graph.relationships[0].trust = 7
    graph.faction_graph.factions[0].default_conflict_level = 2

    yaml_contents = social_graph_to_yaml(graph)

    assert "trust: 7" in yaml_contents["relationships.yaml"]
    assert "default_conflict_level: 2" in yaml_contents["factions.yaml"]


def test_invalid_npc_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.relationship_graph.relationships[0].source_id = "missing_npc"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "relationship_missing_source" for issue in preview.validation.errors)


def test_invalid_faction_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.faction_graph.conflict_edges[0].target_faction_id = "missing_faction"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "faction_relation_missing_faction" for issue in preview.validation.errors)


def test_hidden_relationship_stays_out_of_player_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    state = app.state.session_store.get_session(session_id).state
    state.relationships["hidden_edge"] = RelationshipState(
        id="hidden_edge",
        source_id="harlan",
        target_id="player",
        relation_type="secret",
        known_by_player=False,
    )

    response = client.get(f"/game/{session_id}/graphs/relationships")

    assert response.status_code == 200
    assert "hidden_edge" not in response.text


def test_social_graph_preview_api_does_not_write_files(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    factions_before = (worlds_root / "mist_valley" / "factions.yaml").read_text(encoding="utf-8")
    relationships_before = (worlds_root / "mist_valley" / "relationships.yaml").read_text(encoding="utf-8")
    graph_payload = client.get("/authoring/worlds/mist_valley/social/graph").json()
    graph_payload["relationship_graph"]["relationships"][0]["trust"] = 11

    response = client.post("/authoring/worlds/mist_valley/social/graph/preview", json={"graph": graph_payload})

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert (worlds_root / "mist_valley" / "factions.yaml").read_text(encoding="utf-8") == factions_before
    assert (worlds_root / "mist_valley" / "relationships.yaml").read_text(encoding="utf-8") == relationships_before


def test_social_graph_save_uses_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    graph_payload = client.get("/authoring/worlds/mist_valley/social/graph").json()
    graph_payload["relationship_graph"]["relationships"][0]["affinity"] = 9

    saved = client.put("/authoring/worlds/mist_valley/social/graph", json={"graph": graph_payload})
    persisted = (worlds_root / "mist_valley" / "relationships.yaml").read_text(encoding="utf-8")

    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert "affinity: 9" in persisted

    graph_payload["relationship_graph"]["relationships"][0]["trust"] = 999
    rejected = client.put("/authoring/worlds/mist_valley/social/graph", json={"graph": graph_payload})
    persisted_after_reject = (worlds_root / "mist_valley" / "relationships.yaml").read_text(encoding="utf-8")

    assert rejected.status_code == 200
    assert rejected.json()["saved"] is False
    assert "trust: 999" not in persisted_after_reject
