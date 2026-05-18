from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.engine.content.validation_graph import build_validation_graph
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path, *, authoring: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "validation_graph.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=authoring, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_validation_report_converts_to_graph() -> None:
    report = ValidationReport(world_id="test")
    report.add(
        ValidationSeverity.ERROR,
        "npcs.yaml.harlan.location_id",
        "NPC references missing location: nowhere",
        code="npc_missing_location",
        ref_id="nowhere",
    )

    graph = build_validation_graph(report)

    assert any(node.type == "file" and node.label == "npcs.yaml" for node in graph.nodes)
    assert any(node.type == "issue" and node.code == "npc_missing_location" for node in graph.nodes)
    assert any(edge.type == "missing_reference" for edge in graph.edges)


def test_missing_reference_generates_missing_reference_edge(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    locations_path = worlds_root / "mist_valley" / "locations.yaml"
    content = locations_path.read_text(encoding="utf-8").replace("blacksmith", "missing_blacksmith", 1)
    locations_path.write_text(content, encoding="utf-8")
    report = validate_world_pack("mist_valley", worlds_root)

    graph = build_validation_graph(report)

    assert any(edge.type == "missing_reference" for edge in graph.edges)


def test_visibility_risk_generates_visibility_edge() -> None:
    report = ValidationReport(world_id="test")
    report.add(
        ValidationSeverity.WARNING,
        "rumors.yaml.r1.text_for_player",
        "Rumor player-facing text appears to include the full hidden fact text.",
        code="rumor_reveals_hidden_fact",
        ref_id="secret_fact",
    )

    graph = build_validation_graph(report)

    assert any(edge.type == "visibility_risk" for edge in graph.edges)


def test_validation_graph_api_disabled_when_authoring_disabled(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root, authoring=False)

    response = client.get("/authoring/worlds/mist_valley/validation-graph")

    assert response.status_code == 403


def test_validation_graph_api_does_not_return_sensitive_data(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)

    response = client.get("/authoring/worlds/mist_valley/validation-graph")

    assert response.status_code == 200
    body = response.text.lower()
    assert "sk-" not in body
    assert "database_url" not in body
    assert str(tmp_path).lower() not in body
