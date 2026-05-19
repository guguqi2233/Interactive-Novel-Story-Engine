from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.rumor_crime_authoring import (
    ConsequenceGraphEdge,
    CrimeConsequenceNode,
    parse_rumor_crime_authoring,
    preview_rumor_crime_authoring,
)
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path, *, authoring: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "rumor_crime_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=authoring, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_rumors_yaml_parses_to_consequence_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)

    graph = parse_rumor_crime_authoring("mist_valley", ContentAuthoringService(worlds_root))

    assert graph.rumors[0].id == "forge_tools_missing_rumor"
    assert graph.facts[0].id == "village_square_is_misty"
    assert any(faction.id == "village_council" for faction in graph.factions)


def test_consequence_graph_can_be_generated(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    graph = parse_rumor_crime_authoring("mist_valley", ContentAuthoringService(worlds_root))

    graph.rumors[0].tags.append("theft")
    preview = preview_rumor_crime_authoring("mist_valley", graph, ContentAuthoringService(worlds_root))

    assert preview.validation.ok
    assert "rumors.yaml" in preview.yaml_contents
    assert preview.graph.trigger_nodes
    assert preview.graph.witness_nodes
    assert preview.graph.npc_reaction_nodes
    assert preview.graph.impact_summary["rumors"] >= 1


def test_invalid_fact_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.rumors[0].fact_id = "missing_fact"

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "rumor_missing_fact" for issue in preview.validation.errors)


def test_missing_faction_ref_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.reputation_effects[0].faction_id = "missing_faction"

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "reputation_effect_missing_faction" for issue in preview.validation.errors)


def test_missing_dedupe_key_warning(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.rumors[0].dedupe_key = None

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert preview.validation.ok
    assert any(issue.code == "consequence_missing_dedupe_key" for issue in preview.validation.warnings)


def test_hidden_fact_text_leakage_is_warned(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.rumors[0].text_for_player = "A sealed letter is hidden beneath a loose paving stone."

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert any(issue.code == "rumor_reveals_hidden_fact" for issue in preview.validation.warnings)


def test_duplicate_consequence_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.crimes.append(
        CrimeConsequenceNode(
            id=graph.rumors[0].id,
            crime_type="theft",
            trigger_condition="crime:theft",
        )
    )

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "duplicate_consequence_id" for issue in preview.validation.errors)


def test_loop_consequence_is_warned(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_rumor_crime_authoring("mist_valley", service)
    graph.edges.append(
        ConsequenceGraphEdge(
            source=graph.rumors[0].id,
            target=graph.rumors[0].id,
            type="loop",
        )
    )

    preview = preview_rumor_crime_authoring("mist_valley", graph, service)

    assert any(issue.code == "consequence_loop_warning" for issue in preview.validation.warnings)


def test_rumor_crime_preview_api_does_not_write_files(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    rumors_before = (worlds_root / "mist_valley" / "rumors.yaml").read_text(encoding="utf-8")
    graph_payload = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    graph_payload["rumors"][0]["spread_level"] = 3

    response = client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": graph_payload})

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert (worlds_root / "mist_valley" / "rumors.yaml").read_text(encoding="utf-8") == rumors_before


def test_rumor_crime_authoring_does_not_modify_active_game_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    session = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    before = client.get(f"/game/state/{session['session_id']}").json()["visible_state"]
    graph_payload = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    graph_payload["rumors"][0]["spread_level"] = 99

    preview = client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": graph_payload})
    after = client.get(f"/game/state/{session['session_id']}").json()["visible_state"]

    assert preview.status_code == 200
    assert after == before


def test_rumor_crime_save_uses_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    graph_payload = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    graph_payload["rumors"][0]["spread_level"] = 4

    saved = client.put("/authoring/worlds/mist_valley/rumor-crime", json={"graph": graph_payload})
    persisted = (worlds_root / "mist_valley" / "rumors.yaml").read_text(encoding="utf-8")

    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert "spread_level: 4" in persisted

    graph_payload["rumors"][0]["fact_id"] = "missing_fact"
    rejected = client.put("/authoring/worlds/mist_valley/rumor-crime", json={"graph": graph_payload})
    persisted_after_reject = (worlds_root / "mist_valley" / "rumors.yaml").read_text(encoding="utf-8")

    assert rejected.status_code == 200
    assert rejected.json()["saved"] is False
    assert persisted_after_reject == persisted
