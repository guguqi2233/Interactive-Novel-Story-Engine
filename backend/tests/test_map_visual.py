from pathlib import Path

import pytest

from app.db.repository import SQLiteSaveRepository
from app.engine.content.map_visual import (
    build_authoring_map_visual_graph,
    build_player_visible_map_visual_graph,
)
from app.engine.content.world_loader import MapVisibility, WorldLoader, WorldLoaderError
from app.engine.content.validator import ValidationSeverity, validate_world_pack
from app.session_store import build_visible_state


def test_old_locations_without_visual_still_load(tmp_path: Path) -> None:
    write_world(tmp_path, "old_map")

    pack = WorldLoader(tmp_path).load("old_map")
    graph = build_authoring_map_visual_graph(pack)

    assert pack.locations[0].visual is None
    assert [node.location_id for node in graph.nodes] == ["square", "forge"]
    assert graph.nodes[0].x == 0.0
    assert graph.nodes[1].x == 160.0


def test_locations_visual_fields_parse_into_authoring_graph(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "visual_map",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: forge
    visual:
      x: 12.5
      y: 44
      region_id: village
      icon: plaza
      color_tag: civic
      display_group: village_center
      notes: Authoring-only note.
      tags:
        - hub
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      south: square
    visual:
      x: 80
      y: 44
      region_id: village
      icon: hammer
      color_tag: craft
      display_group: village_center
""",
    )

    pack = WorldLoader(tmp_path).load("visual_map")
    graph = build_authoring_map_visual_graph(pack)

    square = next(node for node in graph.nodes if node.location_id == "square")
    assert square.x == 12.5
    assert square.y == 44
    assert square.region_id == "village"
    assert square.tags == ["hub"]
    assert square.icon == "plaza"
    assert "Authoring-only note" not in square.model_dump_json()


def test_exits_generate_map_edges(tmp_path: Path) -> None:
    write_world(tmp_path, "edge_map")
    pack = WorldLoader(tmp_path).load("edge_map")

    graph = build_authoring_map_visual_graph(pack)

    edges = {(edge.source_location_id, edge.target_location_id, edge.label) for edge in graph.edges}
    assert ("square", "forge", "north") in edges
    assert ("forge", "square", "south") in edges
    assert all(edge.edge_type == "exit" for edge in graph.edges)


def test_invalid_exit_reports_loader_and_validator_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "bad_exit",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      north: nowhere
""",
    )

    with pytest.raises(WorldLoaderError, match="missing location: nowhere"):
        WorldLoader(tmp_path).load("bad_exit")

    report = validate_world_pack("bad_exit", worlds_root=tmp_path)
    assert not report.ok
    assert any("Exit points to missing location: nowhere" in issue.message for issue in report.errors)


def test_invalid_visual_coordinate_reports_schema_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "bad_visual",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
    visual:
      x: not-a-number
      y: 0
""",
    )

    with pytest.raises(WorldLoaderError, match="schema validation failed"):
        WorldLoader(tmp_path).load("bad_visual")

    report = validate_world_pack("bad_visual", worlds_root=tmp_path)
    assert not report.ok
    assert any(issue.file == "locations.yaml" for issue in report.errors)


def test_hidden_edge_is_filtered_from_player_visible_map(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "hidden_edge",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: secret_room
  - id: secret_room
    name: Secret Room
    description: A hidden chamber.
    exits:
      south: square
    visual:
      x: 100
      y: 0
      visibility: hidden
""",
    )

    pack = WorldLoader(tmp_path).load("hidden_edge")
    authoring_graph = build_authoring_map_visual_graph(pack)
    player_graph = build_player_visible_map_visual_graph(pack, ["square", "secret_room"])

    assert any(edge.visibility == MapVisibility.HIDDEN for edge in authoring_graph.edges)
    assert any(node.location_id == "secret_room" for node in authoring_graph.nodes)
    assert all(node.location_id != "secret_room" for node in player_graph.nodes)
    assert all(
        not (
            edge.source_location_id == "square"
            and edge.target_location_id == "forge"
            and edge.label == "north"
        )
        for edge in player_graph.edges
    )


def test_hidden_edge_metadata_is_filtered_from_player_visible_map(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "hidden_edge_metadata",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: forge
    exit_metadata:
      north:
        edge_type: hidden
        visibility: hidden
        discovery_rules:
          - learn_secret_path
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      south: square
""",
    )

    pack = WorldLoader(tmp_path).load("hidden_edge_metadata")
    authoring_graph = build_authoring_map_visual_graph(pack)
    player_graph = build_player_visible_map_visual_graph(pack, ["square", "forge"])

    assert any(edge.edge_type == "hidden" for edge in authoring_graph.edges)
    assert authoring_graph.hidden_edges
    assert all(
        not (
            edge.source_location_id == "square"
            and edge.target_location_id == "forge"
            and edge.label == "north"
        )
        for edge in player_graph.edges
    )


def test_hidden_visual_exit_does_not_enter_player_visible_state(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "hidden_runtime_exit",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: secret_room
      east: forge
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      west: square
  - id: secret_room
    name: Secret Room
    description: A hidden chamber.
    exits:
      south: square
    visual:
      visibility: hidden
""",
    )

    state = WorldLoader(tmp_path).load("hidden_runtime_exit").to_game_state()
    visible_state = build_visible_state(state)

    assert visible_state.location.exits == {"east": "forge"}
    assert "secret_room" not in visible_state.model_dump_json()


def test_authoring_map_contains_complete_hidden_content(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "authoring_full",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: secret_room
  - id: secret_room
    name: Secret Room
    description: A hidden chamber.
    exits: {}
    visual:
      visibility: hidden
""",
    )

    graph = build_authoring_map_visual_graph(WorldLoader(tmp_path).load("authoring_full"))

    assert {node.location_id for node in graph.nodes} == {"square", "secret_room"}
    assert {edge.target_location_id for edge in graph.edges} == {"secret_room"}


def test_visual_fields_do_not_enter_game_state_or_save_payload(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "visual_state",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits: {}
    visual:
      x: 10
      y: 20
      region_id: village
      notes: Authoring-only note.
""",
    )

    state = WorldLoader(tmp_path).load("visual_state").to_game_state()
    payload = state.model_dump(mode="json")
    repository = SQLiteSaveRepository(tmp_path / "saves.db")
    save_id = "visual_state_save"
    repository.create_save(save_id, state)
    loaded_state = repository.load_save(save_id)

    assert "visual" not in payload["locations"]["square"]
    assert "Authoring-only note" not in state.model_dump_json()
    assert loaded_state.locations["square"].name == "Square"
    assert "Authoring-only note" not in loaded_state.model_dump_json()


def test_visual_region_consistency_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "region_warning",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: forge
    visual:
      region_id: village
      display_group: center
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      south: square
    visual:
      region_id: outskirts
      display_group: center
""",
    )

    report = validate_world_pack("region_warning", worlds_root=tmp_path)

    assert report.ok
    assert any(
        issue.code == "map_visual_inconsistent_region_group"
        for issue in report.warnings
    )


def write_world(
    root: Path,
    world_id: str,
    locations_yaml: str | None = None,
) -> None:
    world_path = root / world_id
    world_path.mkdir(parents=True)
    (world_path / "manifest.yaml").write_text(
        f"""
world_id: {world_id}
name: Test World
version: 0.8.0
start_location_id: square
description: Test world.
""".strip(),
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        (locations_yaml or """
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: forge
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      south: square
""").strip(),
        encoding="utf-8",
    )
    (world_path / "npcs.yaml").write_text("npcs: []", encoding="utf-8")
    (world_path / "items.yaml").write_text("items: []", encoding="utf-8")
    (world_path / "quests.yaml").write_text("quests: []", encoding="utf-8")
    (world_path / "facts.yaml").write_text("facts: []", encoding="utf-8")
    (world_path / "factions.yaml").write_text("factions: []", encoding="utf-8")
    (world_path / "rumors.yaml").write_text("rumors: []", encoding="utf-8")
    (world_path / "relationships.yaml").write_text("relationships: []", encoding="utf-8")
