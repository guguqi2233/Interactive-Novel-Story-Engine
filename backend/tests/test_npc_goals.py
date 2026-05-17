from pathlib import Path

from app.core.state_delta import apply_delta
from app.core.world_state import ActorCondition, GameState, NPCGoalState, NPCGoalStatus, NPCState
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.npc_goals import (
    activate_goal,
    build_goal_event,
    choose_goal,
    complete_goal,
    fail_goal,
    get_active_goals,
    goal_is_allowed,
)


def make_state() -> GameState:
    return GameState(
        world_id="npc-goal-test",
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=["known_fact"],
                goals=[
                    NPCGoalState(
                        id="low",
                        description="Low priority active goal.",
                        priority=1,
                        status=NPCGoalStatus.ACTIVE,
                        conditions=["knows:known_fact"],
                        allowed_actions=["talk"],
                    ),
                    NPCGoalState(
                        id="high",
                        description="High priority active goal.",
                        priority=5,
                        status=NPCGoalStatus.ACTIVE,
                        conditions=["knows:known_fact"],
                        allowed_actions=["talk", "move"],
                        forbidden_actions=["attack"],
                    ),
                    NPCGoalState(
                        id="blocked",
                        description="Blocked goal.",
                        priority=9,
                        status=NPCGoalStatus.BLOCKED,
                    ),
                    NPCGoalState(
                        id="completed",
                        description="Completed goal.",
                        priority=10,
                        status=NPCGoalStatus.COMPLETED,
                    ),
                    NPCGoalState(
                        id="unknown",
                        description="Requires unknown fact.",
                        priority=20,
                        status=NPCGoalStatus.ACTIVE,
                        conditions=["knows:unknown_fact"],
                    ),
                ],
            )
        },
        npc_knowledge={"harlan": {"known_fact"}},
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_npc_goals_load_from_yaml() -> None:
    state = WorldLoader().load("mist_valley").to_game_state()

    goals = [goal for goal in state.npcs["harlan"].goals if isinstance(goal, NPCGoalState)]

    assert [goal.id for goal in goals] == ["share_bridge_warning", "recover_missing_tools"]
    assert goals[0].status == NPCGoalStatus.ACTIVE
    assert state.npcs["harlan"].priorities["community_safety"] == 5
    assert "avoid_unnecessary_violence" in state.npcs["harlan"].constraints


def test_choose_goal_selects_highest_priority_active_goal() -> None:
    goal = choose_goal(make_state(), "harlan")

    assert goal is not None
    assert goal.id == "high"


def test_blocked_and_completed_goals_are_not_selected() -> None:
    active_goal_ids = [goal.id for goal in get_active_goals(make_state(), "harlan")]

    assert "blocked" not in active_goal_ids
    assert "completed" not in active_goal_ids


def test_dead_npc_does_not_choose_goal() -> None:
    state = make_state()
    state = state.model_copy(update={
        "npcs": {
            **state.npcs,
            "harlan": state.npcs["harlan"].model_copy(
                update={"alive": False, "condition": ActorCondition.DEAD}
            ),
        }
    })

    assert choose_goal(state, "harlan") is None


def test_unknown_fact_condition_does_not_activate_goal() -> None:
    active_goal_ids = [goal.id for goal in get_active_goals(make_state(), "harlan")]

    assert "unknown" not in active_goal_ids


def test_goal_status_changes_use_state_delta_and_event() -> None:
    state = make_state()

    deltas = complete_goal(state, "harlan", "high")
    event = build_goal_event("goal-event-1", 1, "harlan", "npc_goal_completed", deltas)
    next_state = apply_all(state, event.state_deltas)
    high_goal = next(goal for goal in next_state.npcs["harlan"].goals if isinstance(goal, NPCGoalState) and goal.id == "high")

    assert high_goal.status == NPCGoalStatus.COMPLETED
    assert event.actor_id == "system"
    assert event.state_deltas == deltas


def test_goal_allowed_actions_and_forbidden_actions() -> None:
    state = make_state()

    assert goal_is_allowed(state, "harlan", "high", "talk")
    assert not goal_is_allowed(state, "harlan", "high", "attack")
    assert not goal_is_allowed(state, "harlan", "high", "lockpick")


def test_activate_and_fail_goal_state_deltas() -> None:
    state = make_state()

    activated = apply_all(state, activate_goal(state, "harlan", "low"))
    failed = apply_all(activated, fail_goal(activated, "harlan", "low"))
    goal = next(goal for goal in failed.npcs["harlan"].goals if isinstance(goal, NPCGoalState) and goal.id == "low")

    assert activated.npcs["harlan"].current_goal_id == "low"
    assert goal.status == NPCGoalStatus.FAILED


def test_save_load_preserves_goal_state(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "npc_goals.db")
    state = apply_all(make_state(), complete_goal(make_state(), "harlan", "high"))

    repository.save_snapshot("save-1", state, [])
    loaded = repository.load_save("save-1")
    goal = next(goal for goal in loaded.npcs["harlan"].goals if isinstance(goal, NPCGoalState) and goal.id == "high")

    assert goal.status == NPCGoalStatus.COMPLETED
