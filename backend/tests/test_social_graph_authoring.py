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
    assert graph.faction_graph.faction_nodes
    assert graph.faction_graph.hostility_edges


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
    graph.faction_graph.conflict_edges[0].relation_type = "hostility"
    graph.faction_graph.conflict_edges[0].conflict_tags = ["law_vs_smuggling", "border_tension"]

    yaml_contents = social_graph_to_yaml(graph)

    assert "trust: 7" in yaml_contents["relationships.yaml"]
    assert "default_conflict_level: 2" in yaml_contents["factions.yaml"]
    assert "border_tension" in yaml_contents["factions.yaml"]


def test_relationship_graph_roundtrip_preserves_hidden_fields_and_tone_preview(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    graph = parse_social_authoring_graph("mist_valley", ContentAuthoringService(worlds_root))
    relationship = graph.relationship_graph.relationships[0]
    relationship.hidden_relationship = True
    relationship.known_by_player = False
    relationship.hidden_authoring_note = "Private grudge."
    relationship.tone_preset = "guarded"

    yaml_contents = social_graph_to_yaml(graph)
    (worlds_root / "mist_valley" / "relationships.yaml").write_text(
        yaml_contents["relationships.yaml"],
        encoding="utf-8",
    )
    reparsed = parse_social_authoring_graph("mist_valley", ContentAuthoringService(worlds_root))

    assert "hidden_relationship: true" in yaml_contents["relationships.yaml"]
    assert "hidden_authoring_note: Private grudge." in yaml_contents["relationships.yaml"]
    assert relationship.rp_tone_preview.summary
    assert reparsed.relationship_graph.relationships[0].tone_preset == "guarded"


def test_invalid_npc_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.relationship_graph.relationships[0].source_id = "missing_npc"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "relationship_missing_source" for issue in preview.validation.errors)


def test_duplicate_relationship_and_invalid_tone_preset_are_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    duplicate = graph.relationship_graph.relationships[0].model_copy(update={"id": "duplicate_edge"})
    graph.relationship_graph.relationships.append(duplicate)
    graph.relationship_graph.relationships[0].tone_preset = "not_a_preset"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "duplicate_relationship_edge" for issue in preview.validation.errors)
    assert any(issue.code == "relationship_invalid_tone_preset" for issue in preview.validation.errors)


def test_hidden_relationship_marked_player_visible_is_rejected(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.relationship_graph.relationships[0].hidden_relationship = True
    graph.relationship_graph.relationships[0].known_by_player = True

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "hidden_relationship_player_visible" for issue in preview.validation.errors)


def test_invalid_faction_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.faction_graph.conflict_edges[0].target_faction_id = "missing_faction"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "faction_relation_missing_faction" for issue in preview.validation.errors)


def test_invalid_faction_conflict_relation_and_alert_are_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.faction_graph.factions[0].default_alert_level = 999
    graph.faction_graph.conflict_edges[0].relation_type = "not_valid"

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "faction_invalid_alert_level" for issue in preview.validation.errors)
    assert any(issue.code == "faction_invalid_conflict_relation" for issue in preview.validation.errors)


def test_duplicate_faction_relation_warns(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    graph.faction_graph.conflict_edges.append(graph.faction_graph.conflict_edges[0].model_copy())

    preview = preview_social_authoring_graph("mist_valley", graph, service)

    assert preview.validation.ok
    assert any(issue.code == "duplicate_faction_relation" for issue in preview.validation.warnings)


def test_hidden_faction_conflict_stays_out_of_player_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]

    response = client.get(f"/game/{session_id}/graphs/factions")

    assert response.status_code == 200
    assert "old_road_smugglers" not in response.text
    assert "law_vs_smuggling" not in response.text


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


def test_rp_tone_preset_preview_does_not_change_relationship_values(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_social_authoring_graph("mist_valley", service)
    relationship = graph.relationship_graph.relationships[0]
    before = (relationship.trust, relationship.fear, relationship.affinity, relationship.obligation)
    relationship.tone_preset = "warm"

    preview = preview_social_authoring_graph("mist_valley", graph, service)
    preview_relationship = preview.graph.relationship_graph.relationships[0]

    assert (preview_relationship.trust, preview_relationship.fear, preview_relationship.affinity, preview_relationship.obligation) == before
    assert preview_relationship.rp_tone_preview.preset_id == "warm"
    assert preview_relationship.rp_tone_preview.summary


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
