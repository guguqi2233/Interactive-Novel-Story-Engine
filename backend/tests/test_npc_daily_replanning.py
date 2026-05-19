from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    GameState,
    GameTime,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCGoalState,
    NPCGoalStatus,
    NPCIntent,
    NPCPlan,
    NPCPlanStep,
    NPCPlanStepType,
    NPCState,
    load_game_state_payload,
)
from app.engine.rules.npc_daily_replanning import DailyReplanningTrigger, run_daily_replanning
from app.engine.rules.world_tick import run_world_tick


def make_state() -> GameState:
    return GameState(
        world_id="npc-daily-replanning-test",
        current_time=GameTime(day=2, minutes_of_day=8 * 60),
        locations={
            "square": LocationState(id="square", name="Square"),
            "gate": LocationState(id="gate", name="Gate"),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_new_day_triggers_replanning_from_world_tick() -> None:
    state = make_state()
    state.social_flags["npc_daily_replanning_day_1_harlan"] = True

    result = run_world_tick(state)

    assert result.event is not None
    assert any(delta.metadata.get("source") == "npc_daily_replanning" for delta in result.state_deltas)
    assert any(delta.path == "social_flags.npc_daily_replanning_day_2_harlan" for delta in result.state_deltas)


def test_completed_goal_is_not_selected() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "current_goal_id": "done",
            "goals": [
                NPCGoalState(id="done", priority=10, status=NPCGoalStatus.COMPLETED),
                NPCGoalState(id="active", priority=5, status=NPCGoalStatus.ACTIVE),
            ],
        }
    )

    result = run_daily_replanning(state, DailyReplanningTrigger.NEW_DAY)
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].current_goal_id == "active"


def test_impossible_plan_is_cancelled() -> None:
    state = make_state()
    plan = NPCPlan(
        id="plan-missing-location",
        npc_id="harlan",
        source_intent_id="visit-missing",
        steps=[
            NPCPlanStep(
                step_type=NPCPlanStepType.MOVE,
                target_id="missing-location",
                expected_result="npc_moved",
            )
        ],
        created_turn=state.turn,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"plans": [plan]})

    result = run_daily_replanning(state)
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].plans[0].status == "cancelled"


def test_faction_duty_is_added_to_intent_queue() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-gate",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="gate",
        target_type="location",
        priority=4,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"faction_duties": [duty]})

    result = run_daily_replanning(state)
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "guard_location"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "gate"


def test_expired_intents_are_pruned() -> None:
    state = make_state()
    expired = NPCIntent(
        id="old-rest",
        npc_id="harlan",
        intent_type="rest",
        created_turn=0,
        expires_turn=state.turn,
    )
    active = NPCIntent(
        id="fresh-rest",
        npc_id="harlan",
        intent_type="rest",
        created_turn=state.turn,
        expires_turn=state.turn + 10,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"intent_queue": [expired, active]})

    result = run_daily_replanning(state)
    next_state = apply_all(state, result.state_deltas)

    assert [intent.id for intent in next_state.npcs["harlan"].intent_queue] == ["fresh-rest"]


def test_replanning_records_system_event() -> None:
    state = make_state()

    result = run_daily_replanning(state, DailyReplanningTrigger.MAJOR_EVENT)

    assert result.events
    assert result.events[0].actor_id == "system"
    assert result.events[0].action_type == "npc_daily_replanning"
    assert result.events[0].state_deltas == result.state_deltas


def test_dead_npc_does_not_do_daily_replanning() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = run_daily_replanning(state)

    assert result.state_deltas == []
    assert result.events == []
    assert result.replanned_npc_ids == []


def test_save_load_then_next_day_replanning_works() -> None:
    state = make_state()
    first = run_daily_replanning(state)
    day_two_state = apply_all(state, first.state_deltas)
    restored = load_game_state_payload(day_two_state.model_dump(mode="json"))
    day_three_state = restored.model_copy(update={"current_time": GameTime(day=3, minutes_of_day=8 * 60)})

    second = run_daily_replanning(day_three_state)
    next_state = apply_all(day_three_state, second.state_deltas)

    assert second.replanned_npc_ids == ["harlan"]
    assert next_state.social_flags["npc_daily_replanning_day_3_harlan"] is True
