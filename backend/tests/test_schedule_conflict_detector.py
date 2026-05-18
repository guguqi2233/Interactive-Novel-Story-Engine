import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssueSeverity
from app.quality.schedule_conflict_detector import analyze_schedule_conflicts


def test_invalid_schedule_location_is_caught(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: missing_forge
        activity: hammering
""",
    )

    report = analyze_schedule_conflicts("test_world", worlds_root=tmp_path)

    assert report.invalid_schedule_locations[0].safe_details["location_id"] == "missing_forge"
    assert report.invalid_schedule_locations[0].severity == QualityIssueSeverity.ERROR


def test_overlapping_schedule_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml=TWO_REACHABLE_LOCATIONS,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: square
        activity: talking
      - time_of_day: morning
        location_id: forge
        activity: working
""",
    )

    report = analyze_schedule_conflicts("test_world", worlds_root=tmp_path)

    assert report.overlapping_time_blocks[0].safe_details["time_of_day"] == "morning"
    assert report.overlapping_time_blocks[0].severity == QualityIssueSeverity.WARNING


def test_quest_required_npc_unavailable_is_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
  - id: sealed_forge
    name: Sealed Forge
    description: Unreachable.
    exits: {}
""",
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: sealed_forge
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: sealed_forge
        activity: waiting
""",
        quests_yaml="""
quests:
  - id: talk_harlan
    title: Talk Harlan
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [talk]
        next_stages: []
    triggers:
      - type: npc_talked
        id: harlan
        action: complete_objective
        objective_id: talk
""",
    )

    report = analyze_schedule_conflicts("test_world", worlds_root=tmp_path)

    assert report.quest_required_npc_unavailable[0].entity_id == "harlan"
    assert report.quest_required_npc_unavailable[0].severity == QualityIssueSeverity.ERROR


def test_hidden_npc_details_do_not_enter_normal_report(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: hidden_spy
    name: Hidden Spy
    location_id: square
    personality: Secretive.
    hidden: true
    schedule:
      - time_of_day: morning
        location_id: missing_lair
        activity: secret meeting
""",
    )

    report = analyze_schedule_conflicts("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert "hidden_spy" not in normal_payload
    assert "Hidden Spy" not in normal_payload
    assert "secret meeting" not in normal_payload
    assert "hidden_spy" in debug_payload
    assert report.invalid_schedule_locations[0].hidden_details_debug_only is not None


def test_valid_schedule_has_no_blocker(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml=TWO_REACHABLE_LOCATIONS,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: square
        activity: talking
      - time_of_day: evening
        location_id: forge
        activity: working
""",
        quests_yaml="""
quests:
  - id: talk_harlan
    title: Talk Harlan
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [talk]
        next_stages: []
    triggers:
      - type: npc_talked
        id: harlan
        action: complete_objective
        objective_id: talk
""",
    )

    report = analyze_schedule_conflicts("test_world", worlds_root=tmp_path)

    assert not any(issue.severity == QualityIssueSeverity.BLOCKER for issue in report.quality_report.issues)
    assert not report.invalid_schedule_locations
    assert not report.quest_required_npc_unavailable


def test_schedule_conflict_api(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: missing_forge
        activity: hammering
""",
    )
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post("/quality/worlds/test_world/schedules/analyze", json={})
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert payload["invalid_schedule_locations"][0]["safe_details"]["location_id"] == "missing_forge"


TWO_REACHABLE_LOCATIONS = """
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      east: forge
  - id: forge
    name: Forge
    description: Work.
    exits:
      west: square
"""


def write_world(
    root: Path,
    *,
    locations_yaml: str | None = None,
    npcs_yaml: str | None = None,
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
    (world / "items.yaml").write_text("items: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text("facts: []\n", encoding="utf-8")
    (world / "factions.yaml").write_text("factions: []\n", encoding="utf-8")
    (world / "rumors.yaml").write_text("rumors: []\n", encoding="utf-8")
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
    (world / "quests.yaml").write_text(quests_yaml or "quests: []\n", encoding="utf-8")
