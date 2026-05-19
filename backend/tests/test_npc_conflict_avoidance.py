from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    GameState,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCSocialDisposition,
    NPCState,
    PlayerState,
)
from app.engine.rules.npc_conflict_avoidance import (
    ConflictAvoidanceBehavior,
    resolve_conflict_avoidance,
)


def make_state() -> GameState:
    return GameState(
        world_id="npc-conflict-avoidance-test",
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Square", exits={"north": "gate"}),
            "gate": LocationState(id="gate", name="Gate"),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "bandit": NPCState(id="bandit", location_id="square"),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_injured_npc_generates_rest_intent() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"condition": ActorCondition.WOUNDED, "hp": 6}
    )

    result = resolve_conflict_avoidance(state, "harlan")
    next_state = apply_all(state, result.state_deltas)

    assert result.candidates[0].behavior_type == ConflictAvoidanceBehavior.REST
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "rest"
    assert result.events[0].action_type == "npc_conflict_avoidance"


def test_high_fear_npc_avoids_player() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"social_disposition": NPCSocialDisposition(fear_player=80)}
    )

    result = resolve_conflict_avoidance(state, "harlan")
    next_state = apply_all(state, result.state_deltas)

    assert result.candidates[0].behavior_type == ConflictAvoidanceBehavior.AVOID_ACTOR
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "avoid_actor"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "player"


def test_visible_hostile_actor_triggers_flee() -> None:
    state = make_state()
    state.npcs["bandit"] = state.npcs["bandit"].model_copy(update={"hostile_to": ["harlan"]})

    result = resolve_conflict_avoidance(state, "harlan")
    next_state = apply_all(state, result.state_deltas)

    assert result.candidates[0].behavior_type == ConflictAvoidanceBehavior.FLEE_FROM_ACTOR
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "flee_from_actor"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "bandit"


def test_hidden_npc_flee_does_not_leak_to_player_visible_event() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"hidden": True, "discovered_by": []})
    state.npcs["bandit"] = state.npcs["bandit"].model_copy(update={"hostile_to": ["harlan"]})

    result = resolve_conflict_avoidance(state, "harlan")

    assert result.candidates[0].behavior_type == ConflictAvoidanceBehavior.FLEE_FROM_ACTOR
    assert result.events[0].visible_to_player is False
    assert all(delta.metadata.get("visible_to_player") != "true" for delta in result.state_deltas)


def test_guard_duty_npc_calls_for_help_instead_of_fleeing() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-square",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="square",
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"faction_duties": [duty]})
    state.npcs["bandit"] = state.npcs["bandit"].model_copy(update={"hostile_to": ["harlan"]})

    result = resolve_conflict_avoidance(state, "harlan")
    next_state = apply_all(state, result.state_deltas)

    assert result.candidates[0].behavior_type == ConflictAvoidanceBehavior.CALL_FOR_HELP
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "call_for_help"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "bandit"


def test_dead_or_incapacitated_npc_does_not_execute_avoidance() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = resolve_conflict_avoidance(state, "harlan")

    assert result.rejected_reason == "npc_inactive"
    assert result.state_deltas == []
    assert result.events == []
