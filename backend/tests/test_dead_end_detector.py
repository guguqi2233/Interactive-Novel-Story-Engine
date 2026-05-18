import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssueSeverity
from app.quality.dead_end_detector import analyze_dead_ends


def test_missing_required_item_path_is_caught(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        quests_yaml="""
quests:
  - id: key_quest
    title: Key Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [take_key]
        next_stages: []
    triggers:
      - type: item_acquired
        id: missing_key
        action: complete_objective
        objective_id: take_key
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)

    assert analysis.required_item_unreachable[0].code == "required_item_missing"
    assert analysis.required_item_unreachable[0].severity == QualityIssueSeverity.BLOCKER


def test_undiscoverable_hidden_fact_is_caught_without_leaking_text(tmp_path: Path) -> None:
    hidden_text = "Mayor hid the bridge ledger under the shrine."
    write_world(
        tmp_path,
        facts_yaml=f"""
facts:
  - id: hidden_ledger_truth
    text: {hidden_text}
    visibility: hidden
    known_by: []
""",
        quests_yaml="""
quests:
  - id: clue_quest
    title: Clue Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [discover_truth]
        next_stages: []
    triggers:
      - type: fact_discovered
        id: hidden_ledger_truth
        action: complete_objective
        objective_id: discover_truth
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(analysis.model_dump_normal(), ensure_ascii=False)

    assert analysis.required_fact_undiscoverable[0].code == "required_fact_hidden_without_discovery"
    assert analysis.hidden_clue_never_discoverable[0].code == "hidden_clue_never_discoverable"
    assert hidden_text not in normal_payload
    assert "hidden_ledger_truth" in normal_payload


def test_hidden_fact_with_search_discovery_path_is_not_dead_end(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        facts_yaml="""
facts:
  - id: loose_stone_letter
    text: A letter waits under the loose stone.
    visibility: hidden
    known_by: []
    tags:
      - searchable
      - location:square
""",
        quests_yaml="""
quests:
  - id: letter_quest
    title: Letter Quest
    initial_stage: start
    visibility: hidden
    stages:
      - id: start
        title: Start
        objectives: [discover_letter]
        next_stages: []
    triggers:
      - type: fact_discovered
        id: loose_stone_letter
        action: complete_objective
        objective_id: discover_letter
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)

    assert not analysis.required_fact_undiscoverable
    assert not analysis.hidden_clue_never_discoverable


def test_locked_location_without_access_path_is_caught(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      north: sealed_room
  - id: sealed_room
    name: Sealed Room
    description: Locked.
    exits: {}
    visual:
      visibility: hidden
      tags: [locked]
""",
        quests_yaml="""
quests:
  - id: sealed_room_quest
    title: Sealed Room Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [enter_room]
        next_stages: []
    triggers:
      - type: location_visited
        id: sealed_room
        action: complete_objective
        objective_id: enter_room
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)

    assert analysis.locked_door_without_key_path[0].entity_id == "sealed_room"
    assert analysis.locked_door_without_key_path[0].severity == QualityIssueSeverity.ERROR


def test_npc_schedule_conflict_is_caught(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      east: forge
      west: bridge
  - id: forge
    name: Forge
    description: Hot.
    exits:
      west: square
  - id: bridge
    name: Bridge
    description: Foggy.
    exits:
      east: square
""",
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: forge
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: forge
        activity: hammering
      - time_of_day: morning
        location_id: bridge
        activity: watching
""",
        quests_yaml="""
quests:
  - id: talk_quest
    title: Talk Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [talk_harlan]
        next_stages: []
    triggers:
      - type: npc_talked
        id: harlan
        action: complete_objective
        objective_id: talk_harlan
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)

    assert analysis.schedule_conflicts[0].code == "npc_schedule_conflicting_locations"


def test_fallback_access_path_avoids_locked_location_blocker(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      north: sealed_room
  - id: sealed_room
    name: Sealed Room
    description: Locked.
    exits: {}
    visual:
      visibility: hidden
      tags: [locked]
""",
        items_yaml="""
items:
  - id: old_key
    name: Old Key
    description: Opens the sealed room.
    location_id: square
    portable: true
    tags:
      - key
      - opens:sealed_room
""",
        quests_yaml="""
quests:
  - id: sealed_room_quest
    title: Sealed Room Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [enter_room]
        next_stages: []
    triggers:
      - type: location_visited
        id: sealed_room
        action: complete_objective
        objective_id: enter_room
""",
    )

    analysis = analyze_dead_ends("test_world", worlds_root=tmp_path)

    assert not analysis.locked_door_without_key_path


def test_dead_end_analysis_api_returns_safe_report(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        quests_yaml="""
quests:
  - id: key_quest
    title: Key Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [take_key]
        next_stages: []
    triggers:
      - type: item_acquired
        id: missing_key
        action: complete_objective
        objective_id: take_key
""",
    )
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post(
            "/quality/worlds/test_world/dead-ends/analyze",
            json={"coverage": {"visited_locations": ["square"]}},
        )
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert "quality_report" in payload
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "API key" not in serialized
    assert payload["quality_report"]["issues"][0]["safe_details"]["entity_id"] == "missing_key"


def write_world(
    root: Path,
    *,
    locations_yaml: str | None = None,
    npcs_yaml: str | None = None,
    items_yaml: str | None = None,
    facts_yaml: str | None = None,
    quests_yaml: str | None = None,
) -> None:
    world = root / "test_world"
    world.mkdir()
    (world / "manifest.yaml").write_text(
        """
world_id: test_world
name: Test World
version: "1.0"
start_location_id: square
""",
        encoding="utf-8",
    )
    (world / "locations.yaml").write_text(
        locations_yaml
        or """
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
""",
        encoding="utf-8",
    )
    (world / "npcs.yaml").write_text(npcs_yaml or "npcs: []\n", encoding="utf-8")
    (world / "items.yaml").write_text(items_yaml or "items: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text(facts_yaml or "facts: []\n", encoding="utf-8")
    (world / "factions.yaml").write_text("factions: []\n", encoding="utf-8")
    (world / "rumors.yaml").write_text("rumors: []\n", encoding="utf-8")
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
    (world / "quests.yaml").write_text(quests_yaml or "quests: []\n", encoding="utf-8")
