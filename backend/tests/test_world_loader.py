from pathlib import Path

import pytest

from app.engine.content.world_loader import WorldLoader, WorldLoaderError


def test_loads_example_world_pack() -> None:
    pack = WorldLoader("worlds").load("mist_valley")
    state = pack.to_game_state()

    assert pack.manifest.world_id == "mist_valley"
    assert state.world_id == "mist_valley"
    assert state.player.location_id == "village_square"
    assert "blacksmith" in state.locations
    assert state.npcs["harlan"].location_id == "blacksmith"
    assert "sealed_letter" in state.objects


def test_owner_item_is_preserved_in_game_state(tmp_path: Path) -> None:
    write_world(tmp_path, "owned_item")
    (tmp_path / "owned_item" / "items.yaml").write_text(
        """
items:
  - id: pocket_watch
    name: Pocket Watch
    owner_id: player
""".strip(),
        encoding="utf-8",
    )

    state = WorldLoader(tmp_path).load("owned_item").to_game_state()

    assert state.objects["pocket_watch"].location_id == "player"


def test_missing_required_field_reports_schema_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "broken",
        locations_yaml="""
locations:
  - id: village_square
    description: Missing name.
    exits: {}
""",
    )

    with pytest.raises(WorldLoaderError, match="schema validation failed"):
        WorldLoader(tmp_path).load("broken")


def test_exit_to_missing_location_errors(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "broken",
        locations_yaml="""
locations:
  - id: village_square
    name: Village Square
    description: Start.
    exits:
      north: nowhere
""",
    )

    with pytest.raises(WorldLoaderError, match="exit north points to missing location: nowhere"):
        WorldLoader(tmp_path).load("broken")


def test_npc_in_missing_location_errors(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        "broken",
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: nowhere
    personality: Wary.
    knowledge: []
""",
    )

    with pytest.raises(WorldLoaderError, match="NPC harlan references missing location_id: nowhere"):
        WorldLoader(tmp_path).load("broken")


def write_world(
    root: Path,
    world_id: str,
    locations_yaml: str | None = None,
    npcs_yaml: str | None = None,
) -> None:
    world_path = root / world_id
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: broken
name: Broken World
version: 0.1.0
start_location_id: village_square
description: Test world.
""".strip(),
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        (locations_yaml or """
locations:
  - id: village_square
    name: Village Square
    description: Start.
    exits: {}
""").strip(),
        encoding="utf-8",
    )
    (world_path / "npcs.yaml").write_text(
        (npcs_yaml or """
npcs:
  - id: harlan
    name: Harlan
    location_id: village_square
    personality: Wary.
    knowledge: []
""").strip(),
        encoding="utf-8",
    )
    (world_path / "items.yaml").write_text("items: []", encoding="utf-8")
    (world_path / "quests.yaml").write_text("quests: []", encoding="utf-8")
