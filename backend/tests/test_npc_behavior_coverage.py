import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.main import app
from app.quality.npc_behavior_coverage import analyze_npc_behavior_coverage


def test_npc_with_unused_goal_is_warning(tmp_path: Path) -> None:
    write_world(tmp_path, npcs_yaml=NPC_WITH_GOALS)

    report = analyze_npc_behavior_coverage("test_world", worlds_root=tmp_path)

    assert report.total_npcs == 1
    assert report.npcs_with_goals == 1
    assert report.unused_goal_warnings[0].safe_details["goal_id"] == "share_rumor"
    assert any(issue.category == "npc_behavior_coverage" for issue in report.quality_report.issues)


def test_npc_never_reachable_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
  - id: sealed_cell
    name: Sealed Cell
    description: Cut off.
    exits: {}
""",
        npcs_yaml="""
npcs:
  - id: prisoner
    name: Prisoner
    location_id: sealed_cell
    personality: Quiet.
""",
    )

    report = analyze_npc_behavior_coverage("test_world", worlds_root=tmp_path)

    assert report.unreachable_npc_warnings[0].entity_id == "prisoner"
    assert report.unreachable_npc_warnings[0].safe_details["code"] == "npc_never_reachable"


def test_schedule_move_and_reaction_coverage_metrics_update(tmp_path: Path) -> None:
    write_world(tmp_path, npcs_yaml=NPC_WITH_GOALS)
    events = [
        Event(
            event_id="schedule-1",
            turn=1,
            actor_id="system",
            action_type="world_tick",
            result="success",
            visible_to_player=False,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="npcs.harlan.location_id",
                    value="square",
                    reason="schedule",
                    metadata={"source": "npc_schedule", "npc_id": "harlan"},
                )
            ],
        ),
        Event(
            event_id="reaction-1",
            turn=2,
            actor_id="system",
            action_type="world_tick",
            result="success",
            visible_to_player=False,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="social_flags.npc_reaction_harlan_spread_rumor_rumor_bridge",
                    value=True,
                    reason="reaction",
                    metadata={"source": "npc_reaction", "npc_id": "harlan", "reaction": "spread_rumor"},
                )
            ],
        ),
        Event(
            event_id="planning-1",
            turn=3,
            actor_id="system",
            action_type="npc_planning",
            target_id="harlan",
            result="spread_rumor",
            visible_to_player=True,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path="rumors.bridge.known_by_npcs",
                    value="mira",
                    reason="spread",
                    metadata={"source": "npc_planning", "npc_id": "harlan", "goal_id": "share_rumor", "plan_type": "spread_rumor"},
                )
            ],
        ),
    ]

    report = analyze_npc_behavior_coverage("test_world", worlds_root=tmp_path, events=events)

    assert report.schedule_moves_executed == 1
    assert report.reactions_triggered == 1
    assert report.rumor_spread_actions == 2
    assert report.planning_actions_executed["spread_rumor"] >= 1
    assert not report.unused_goal_warnings


def test_goal_status_and_combat_crime_metrics_update(tmp_path: Path) -> None:
    write_world(tmp_path, npcs_yaml=NPC_WITH_GOALS)
    events = [
        Event(
            event_id="goal-1",
            turn=1,
            actor_id="system",
            action_type="npc_goal",
            target_id="harlan",
            result="npc_goal_changed",
            visible_to_player=False,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="npcs.harlan.goals",
                    value=[],
                    reason="goal active",
                    metadata={"source": "npc_goal", "npc_id": "harlan", "goal_id": "share_rumor", "status": "active"},
                ),
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="npcs.harlan.goals",
                    value=[],
                    reason="goal completed",
                    metadata={"source": "npc_goal", "npc_id": "harlan", "goal_id": "share_rumor", "status": "completed"},
                ),
            ],
        ),
        Event(
            event_id="crime-report",
            turn=2,
            actor_id="system",
            action_type="npc_planning",
            target_id="harlan",
            result="report_crime",
            visible_to_player=False,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="crimes.theft.status",
                    value="reported",
                    reason="reported",
                    metadata={"source": "npc_planning", "npc_id": "harlan", "plan_type": "report_crime"},
                )
            ],
        ),
        Event(
            event_id="combat-1",
            turn=3,
            actor_id="player",
            action_type="attack",
            target_id="harlan",
            result="combat:hit",
            visible_to_player=True,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path="npcs.harlan.hp",
                    value=-1,
                    reason="hit",
                    metadata={"source": "combat", "target_id": "harlan"},
                )
            ],
        ),
    ]

    report = analyze_npc_behavior_coverage("test_world", worlds_root=tmp_path, events=events)

    assert report.goals_activated == 1
    assert report.goals_completed == 1
    assert report.crime_reports >= 1
    assert report.combat_participation >= 2


def test_hidden_npc_only_appears_in_debug_details(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: hidden_spy
    name: Hidden Spy
    location_id: sealed_cell
    personality: Silent.
    hidden: true
    goals:
      - id: watch_player
        description: Watch from hiding.
        priority: 1
        status: active
        conditions: []
        desired_state: {}
        allowed_actions: [guard_location]
        forbidden_actions: []
""",
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
  - id: sealed_cell
    name: Sealed Cell
    description: Secret.
    exits: {}
""",
    )

    report = analyze_npc_behavior_coverage("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert "hidden_spy" not in normal_payload
    assert "Hidden Spy" not in normal_payload
    assert "hidden_spy" in debug_payload
    assert report.quality_report.issues[0].hidden_details_debug_only is not None


def test_npc_behavior_coverage_api(tmp_path: Path) -> None:
    write_world(tmp_path, npcs_yaml=NPC_WITH_GOALS)
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post(
            "/quality/worlds/test_world/npc-coverage/analyze",
            json={
                "events": [
                    {
                        "event_id": "talk-1",
                        "turn": 1,
                        "actor_id": "player",
                        "action_type": "talk",
                        "result": "success",
                        "visible_to_player": True,
                        "target_id": "harlan",
                        "state_deltas": [
                            {
                                "operation": "set",
                                "path": "npcs.harlan.current_activity",
                                "value": "talking",
                                "reason": "talked",
                                "metadata": {"source": "test"},
                            }
                        ],
                    }
                ]
            },
        )
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert payload["npcs_seen_by_player"] == 1
    assert payload["npcs_talked_to"] == 1


NPC_WITH_GOALS = """
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    goals:
      - id: share_rumor
        description: Share a rumor.
        priority: 3
        status: active
        conditions: []
        desired_state: {}
        allowed_actions: [spread_rumor]
        forbidden_actions: []
"""


def write_world(
    root: Path,
    *,
    locations_yaml: str | None = None,
    npcs_yaml: str | None = None,
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
    (world / "quests.yaml").write_text("quests: []\n", encoding="utf-8")
