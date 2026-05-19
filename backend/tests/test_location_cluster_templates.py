from __future__ import annotations

from pathlib import Path
from shutil import copytree

from app.core.world_state import GameState
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.location_cluster_templates import (
    LocationClusterPreviewRequest,
    LocationClusterTemplate,
    apply_location_cluster_draft,
    list_location_cluster_templates,
    preview_location_cluster,
    preview_location_cluster_template,
)
from app.engine.content.world_loader import MapVisualEdge, MapVisualGraph, MapVisualNode


def _service(tmp_path: Path) -> ContentAuthoringService:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return ContentAuthoringService(worlds_root)


def _request(**variables: str) -> LocationClusterPreviewRequest:
    return LocationClusterPreviewRequest(
        target_world_id="mist_valley",
        variables={"prefix": "river", "display_name": "River Gate", **variables},
    )


def test_location_cluster_templates_load() -> None:
    templates = list_location_cluster_templates()

    assert {template.id for template in templates} >= {"village_cluster", "basement_cluster"}
    assert all(template.location_nodes for template in templates)


def test_location_cluster_preview_generates_map_visual_graph(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_location_cluster("village_cluster", _request(), service)

    assert isinstance(preview.graph, MapVisualGraph)
    assert preview.writes_to_disk is False
    assert preview.validation.ok
    assert "river_square" in {node.location_id for node in preview.graph.nodes}


def test_location_cluster_hidden_edge_is_marked_hidden(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_location_cluster("village_cluster", _request(), service)

    assert preview.graph.hidden_edges
    assert all(edge.edge_type == "hidden" and edge.visibility == "hidden" for edge in preview.graph.hidden_edges)


def test_location_cluster_invalid_edge_is_caught(tmp_path: Path) -> None:
    service = _service(tmp_path)
    template = LocationClusterTemplate(
        id="bad_cluster",
        name="Bad Cluster",
        cluster_type="test",
        required_variables=["prefix"],
        location_nodes=[
            MapVisualNode(id="{prefix}_a", name="A", location_id="{prefix}_a"),
        ],
        exit_edges=[
            MapVisualEdge(source_location_id="{prefix}_a", target_location_id="{prefix}_missing", label="east"),
        ],
    )

    preview = preview_location_cluster_template(template, _request(), service)

    assert not preview.validation.ok
    assert any(issue.code == "location_cluster_invalid_edge" for issue in preview.validation.errors)


def test_location_cluster_apply_does_not_modify_active_game_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    state = GameState(world_id="mist_valley")
    before = state.model_dump(mode="json")

    preview_location_cluster("village_cluster", _request(), service)
    result = apply_location_cluster_draft(
        "village_cluster",
        LocationClusterPreviewRequest(
            target_world_id="mist_valley",
            variables={"prefix": "river", "display_name": "River Gate"},
            confirm_apply=True,
            confirm_warnings=True,
        ),
        service,
    )

    assert result.applied is True
    assert state.model_dump(mode="json") == before


def test_location_cluster_preview_does_not_write_disk(tmp_path: Path) -> None:
    service = _service(tmp_path)
    path = service.worlds_root / "mist_valley" / "locations.yaml"
    before = path.read_text(encoding="utf-8")

    preview_location_cluster("village_cluster", _request(), service)

    assert path.read_text(encoding="utf-8") == before
