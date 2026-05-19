from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    FactionState,
    GameState,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCState,
    ReputationState,
    load_game_state_payload,
)
from app.engine.rules.npc_faction_duties import (
    duty_preconditions_met,
    duty_to_intent,
    duty_to_plan,
    get_active_duties,
)


def make_state() -> GameState:
    return GameState(
        world_id="npc-faction-duty-test",
        locations={
            "square": LocationState(id="square", name="Square"),
            "gate": LocationState(id="gate", name="Gate"),
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(value=0, known_to_player=True),
            )
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", faction_id="watch"),
            "mira": NPCState(id="mira", location_id="square", faction_id="watch"),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_guard_duty_generates_guard_location_intent() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-gate",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="gate",
        target_type="location",
        priority=4,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"faction_duties": [duty]})

    result = duty_to_intent(state, "harlan", duty)
    next_state = apply_all(state, result.state_deltas)

    assert result.intent is not None
    assert result.intent.intent_type == "guard_location"
    assert result.intent.target_id == "gate"
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "guard_location"


def test_report_crime_duty_requires_npc_known_crime() -> None:
    state = make_state()
    state.crimes["crime-1"] = CrimeState(
        id="crime-1",
        crime_type="theft",
        actor_id="player",
        location_id="square",
        status=CrimeStatus.WITNESSED,
        witnessed_by=[],
    )
    duty = NPCFactionDuty(
        id="report-crime",
        duty_type=NPCFactionDutyType.REPORT_CRIME_TO_FACTION,
        target_id="crime-1",
        target_type="crime",
        required_crime_ids=["crime-1"],
    )

    unknown = duty_to_intent(state, "harlan", duty)
    state.crimes["crime-1"] = state.crimes["crime-1"].model_copy(update={"witnessed_by": ["harlan"]})
    known = duty_to_intent(state, "harlan", duty)

    assert unknown.rejected_reason == "npc_unknown_crime"
    assert known.intent is not None
    assert known.intent.intent_type == "report_crime"


def test_hostile_faction_reputation_triggers_refuse_intent() -> None:
    state = make_state()
    state.factions["watch"].reputation = ReputationState(value=-60, known_to_player=True)
    duty = NPCFactionDuty(
        id="refuse-hostile-player",
        duty_type=NPCFactionDutyType.REFUSE_HOSTILE_ACTOR,
        target_id="player",
        target_type="npc",
    )

    result = duty_to_intent(state, "harlan", duty)

    assert result.intent is not None
    assert result.intent.intent_type == "refuse_hostile_actor"
    assert result.intent.target_id == "player"


def test_invalid_duty_target_is_captured_by_validation() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-nowhere",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="nowhere",
        target_type="location",
    )

    result = duty_preconditions_met(state, "harlan", duty)

    assert result.rejected_reason == "target_location_missing"


def test_dead_npc_does_not_execute_duty() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )
    duty = NPCFactionDuty(
        id="guard-gate",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="gate",
    )

    assert get_active_duties(state, "harlan") == []
    assert duty_to_intent(state, "harlan", duty).rejected_reason == "npc_inactive"


def test_duty_generates_event_and_plan_candidate() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-gate",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="gate",
        target_type="location",
    )

    result = duty_to_plan(state, "harlan", duty)

    assert result.events
    assert result.events[0].actor_id == "system"
    assert result.events[0].action_type == "npc_faction_duty"
    assert result.events[0].state_deltas
    assert result.plan is not None
    assert result.plan.steps[0].step_type == "guard"


def test_save_load_preserves_faction_duties() -> None:
    state = make_state()
    duty = NPCFactionDuty(
        id="guard-gate",
        duty_type=NPCFactionDutyType.GUARD_LOCATION,
        target_id="gate",
        priority=3,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"faction_duties": [duty]})

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].faction_duties[0].id == "guard-gate"
    assert restored.npcs["harlan"].faction_duties[0].duty_type == NPCFactionDutyType.GUARD_LOCATION
