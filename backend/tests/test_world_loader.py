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
    assert "village_square_is_misty" in state.facts


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

    assert state.objects["pocket_watch"].owner_id == "player"
    assert state.objects["pocket_watch"].location_id is None


def test_discoverable_fact_waits_for_discovery() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    assert "old_bridge_creaks_at_midnight" in state.facts
    assert "old_bridge_creaks_at_midnight" not in state.player_visible_facts


def test_missing_facts_yaml_allows_empty_facts(tmp_path: Path) -> None:
    write_world(tmp_path, "no_facts")

    state = WorldLoader(tmp_path).load("no_facts").to_game_state()

    assert state.facts == {}
    assert state.player_visible_facts == set()


def test_fact_known_by_missing_npc_errors(tmp_path: Path) -> None:
    write_world(tmp_path, "bad_fact")
    (tmp_path / "bad_fact" / "facts.yaml").write_text(
        """
facts:
  - id: impossible_rumor
    text: A rumor known by nobody valid.
    visibility: hidden
    known_by:
      - missing_npc
    tags: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(WorldLoaderError, match="Fact impossible_rumor known_by references missing NPC id: missing_npc"):
        WorldLoader(tmp_path).load("bad_fact")


def test_hidden_fact_does_not_enter_player_visible_facts(tmp_path: Path) -> None:
    write_world(tmp_path, "hidden_fact")
    (tmp_path / "hidden_fact" / "facts.yaml").write_text(
        """
facts:
  - id: buried_key
    text: A key is buried under the old tree.
    visibility: hidden
    known_by:
      - harlan
    tags:
      - secret
""".strip(),
        encoding="utf-8",
    )

    state = WorldLoader(tmp_path).load("hidden_fact").to_game_state()

    assert "buried_key" in state.facts
    assert "buried_key" not in state.player_visible_facts


def test_public_fact_enters_player_visible_facts(tmp_path: Path) -> None:
    write_world(tmp_path, "public_fact")
    (tmp_path / "public_fact" / "facts.yaml").write_text(
        """
facts:
  - id: bell_tower_visible
    text: The bell tower is visible from the square.
    visibility: public
    known_by:
      - player
      - harlan
    tags:
      - landmark
""".strip(),
        encoding="utf-8",
    )

    state = WorldLoader(tmp_path).load("public_fact").to_game_state()

    assert "bell_tower_visible" in state.facts
    assert "bell_tower_visible" in state.player_visible_facts


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
