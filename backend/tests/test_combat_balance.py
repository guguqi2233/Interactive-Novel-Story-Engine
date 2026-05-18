import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssueSeverity
from app.quality.combat_balance import analyze_combat_balance


def test_unavoidable_lethal_encounter_is_reported(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: arena
    name: Arena
    description: No way out.
    exits: {}
""",
        npcs_yaml="""
npcs:
  - id: iron_duelist
    name: Iron Duelist
    location_id: arena
    personality: Merciless.
    tags: [enemy, lethal]
    hp: 40
    max_hp: 40
    attack: 10
    defense: 2
    hostile_to: [player]
""",
    )

    report = analyze_combat_balance("test_world", worlds_root=tmp_path)

    assert report.unavoidable_lethal_encounters
    assert report.unavoidable_lethal_encounters[0].severity == QualityIssueSeverity.ERROR
    assert report.enemy_stat_outliers[0].severity == QualityIssueSeverity.WARNING


def test_quest_critical_npc_death_without_fallback_is_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Quest giver.
    tags: [quest_critical, enemy]
    alive: false
    condition: dead
    hp: 0
    attack: 3
""",
        quests_yaml="""
quests:
  - id: ask_harlan
    title: Ask Harlan
    description: Harlan must explain the route.
    initial_stage: start
    current_stage: start
    stages:
      - id: start
        title: Start
        objectives: [talk_harlan]
        next_stages: [done]
      - id: done
        title: Done
        objectives: []
        next_stages: []
    triggers:
      - type: npc_talked
        id: harlan
        action: complete_objective
        objective_id: talk_harlan
""",
    )

    report = analyze_combat_balance("test_world", worlds_root=tmp_path)

    assert report.dead_required_npc_issues
    assert report.dead_required_npc_issues[0].severity == QualityIssueSeverity.ERROR
    assert report.quest_critical_death_issues
    assert report.quest_critical_death_issues[0].severity == QualityIssueSeverity.ERROR


def test_non_lethal_objective_without_non_lethal_path_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        quests_yaml="""
quests:
  - id: capture_bandit
    title: Capture the Bandit
    description: Bring the bandit in alive.
    initial_stage: start
    current_stage: start
    stages:
      - id: start
        title: Capture
        objectives: [alive_capture]
        next_stages: [done]
      - id: done
        title: Done
        objectives: []
        next_stages: []
    triggers:
      - type: npc_talked
        id: guard
        action: complete_objective
        objective_id: report_capture
""",
    )

    report = analyze_combat_balance("test_world", worlds_root=tmp_path)

    assert report.non_lethal_path_issues
    assert report.non_lethal_path_issues[0].severity == QualityIssueSeverity.WARNING


def test_hidden_witness_details_are_debug_only(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: bandit
    name: Bandit
    location_id: square
    personality: Angry.
    tags: [enemy, public_combat]
    attack: 4
    hostile_to: [player]
  - id: hidden_spy
    name: Hidden Spy
    location_id: square
    personality: Watches silently.
    hidden: true
    tags: [witness]
""",
    )

    report = analyze_combat_balance("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert report.hidden_witness_leak_risks
    assert "hidden_spy" not in normal_payload
    assert "Hidden Spy" not in normal_payload
    assert "hidden_spy" in debug_payload


def test_valid_combat_setup_has_no_blocker(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: bandit
    name: Bandit
    location_id: square
    personality: Angry.
    tags: [enemy, flee_warning]
    hp: 10
    max_hp: 10
    attack: 3
    defense: 1
    hostile_to: [player]
""",
    )

    report = analyze_combat_balance("test_world", worlds_root=tmp_path)

    assert report.combatant_npcs == 1
    assert not any(issue.severity == QualityIssueSeverity.BLOCKER for issue in report.quality_report.issues)
    assert not report.unavoidable_lethal_encounters
    assert not report.quest_critical_death_issues


def test_combat_balance_api(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: arena
    name: Arena
    description: No way out.
    exits: {}
""",
        npcs_yaml="""
npcs:
  - id: iron_duelist
    name: Iron Duelist
    location_id: arena
    personality: Merciless.
    tags: [enemy, lethal]
    attack: 10
    hostile_to: [player]
""",
    )
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post("/quality/worlds/test_world/combat/analyze", json={})
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert payload["unavoidable_lethal_encounters"][0]["severity"] == "error"


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
    exits:
      north: road
  - id: road
    name: Road
    description: A reachable road.
    exits:
      south: square
""",
        encoding="utf-8",
    )
    (world / "items.yaml").write_text(
        """
items:
  - id: apple
    name: Apple
    location_id: square
    base_price: 10
    tradeable: true
""",
        encoding="utf-8",
    )
    (world / "npcs.yaml").write_text(
        npcs_yaml
        or """
npcs:
  - id: guard
    name: Guard
    location_id: square
    personality: Watchful.
""",
        encoding="utf-8",
    )
    (world / "quests.yaml").write_text(quests_yaml or "quests: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text("facts: []\n", encoding="utf-8")
    (world / "factions.yaml").write_text("factions: []\n", encoding="utf-8")
    (world / "rumors.yaml").write_text("rumors: []\n", encoding="utf-8")
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
