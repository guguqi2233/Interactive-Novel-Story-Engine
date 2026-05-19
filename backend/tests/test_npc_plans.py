from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    GameState,
    LocationState,
    NPCIntent,
    NPCPlanStatus,
    NPCState,
    WorldObjectState,
    load_game_state_payload,
)
from app.engine.rules.npc_plans import advance_plan, build_plan_from_intent, validate_plan
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="npc-plan-test",
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "forge"}),
            "forge": LocationState(id="forge", name="Forge", exits={"west": "square"}),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", knowledge=["crime:crime-1"]),
            "mira": NPCState(id="mira", location_id="square"),
        },
        crimes={
            "crime-1": CrimeState(
                id="crime-1",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                status=CrimeStatus.WITNESSED,
                witnessed_by=["mira"],
            )
        },
        npc_knowledge={"harlan": {"crime:crime-1"}},
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_report_crime_intent_builds_report_plan() -> None:
    state = make_state()
    intent = NPCIntent(
        id="report-crime-1",
        npc_id="harlan",
        intent_type="report_crime",
        target_id="crime-1",
        target_type="crime",
        created_turn=state.turn,
        preconditions=["crime:crime-1"],
    )

    result = build_plan_from_intent(state, "harlan", intent)

    assert result.plan is not None
    assert result.plan.status == NPCPlanStatus.PLANNED
    assert result.plan.steps[0].step_type == "report"
    assert result.plan.steps[0].target_id == "crime-1"
    assert result.state_deltas[0].path == "npcs.harlan.plans"


def test_visit_location_intent_builds_move_plan() -> None:
    state = make_state()
    intent = NPCIntent(
        id="visit-forge",
        npc_id="harlan",
        intent_type="visit_location",
        target_id="forge",
        target_type="location",
        created_turn=state.turn,
    )

    result = build_plan_from_intent(state, "harlan", intent)

    assert result.plan is not None
    assert result.plan.steps[0].step_type == "move"
    assert result.plan.steps[0].expected_result == "npc_moved"


def test_invalid_target_blocks_plan() -> None:
    state = make_state()
    intent = NPCIntent(
        id="visit-nowhere",
        npc_id="harlan",
        intent_type="visit_location",
        target_id="nowhere",
        target_type="location",
        created_turn=state.turn,
    )

    result = build_plan_from_intent(state, "harlan", intent)

    assert result.plan is not None
    assert result.plan.status == NPCPlanStatus.BLOCKED
    assert result.rejected_reason == "target_location_missing"
    assert validate_plan(state, result.plan).rejected_reason == "target_location_missing"


def test_plan_step_execution_produces_state_delta() -> None:
    state = make_state()
    built = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="visit-forge", npc_id="harlan", intent_type="visit_location", target_id="forge"),
    )
    state = apply_all(state, built.state_deltas)

    advanced = advance_plan(state, "harlan", "plan-visit-forge")
    next_state = apply_all(state, advanced.state_deltas)

    assert any(delta.path == "npcs.harlan.location_id" for delta in advanced.state_deltas)
    assert next_state.npcs["harlan"].location_id == "forge"
    assert next_state.npcs["harlan"].plans[0].status == NPCPlanStatus.COMPLETED


def test_plan_status_change_records_event() -> None:
    state = make_state()
    built = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="visit-forge", npc_id="harlan", intent_type="visit_location", target_id="forge"),
    )
    state = apply_all(state, built.state_deltas)

    advanced = advance_plan(state, "harlan", "plan-visit-forge")

    assert built.events[0].actor_id == "system"
    assert built.events[0].action_type == "npc_plan_built"
    assert advanced.events[0].action_type == "npc_plan_advanced"
    assert advanced.events[0].state_deltas == advanced.state_deltas


def test_dead_npc_cannot_build_plan_from_intent() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="visit-forge", npc_id="harlan", intent_type="visit_location", target_id="forge"),
    )

    assert result.rejected_reason == "npc_inactive"
    assert result.plan is None
    assert result.state_deltas == []
    assert result.events == []


def test_dead_npc_does_not_execute_plan() -> None:
    state = make_state()
    built = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="visit-forge", npc_id="harlan", intent_type="visit_location", target_id="forge"),
    )
    state = apply_all(state, built.state_deltas)
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = advance_plan(state, "harlan", "plan-visit-forge")

    assert result.plan is not None
    assert result.plan.status == NPCPlanStatus.BLOCKED
    assert not any(delta.path == "npcs.harlan.location_id" for delta in result.state_deltas)


def test_hidden_target_does_not_leak_to_player_visible_state() -> None:
    state = make_state()
    state.objects["hidden_relic"] = WorldObjectState(
        id="hidden_relic",
        name="Hidden Relic",
        location_id="square",
        hidden=True,
        visible=True,
    )
    built = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="seek-hidden", npc_id="harlan", intent_type="seek_item", target_id="hidden_relic"),
    )
    next_state = apply_all(state, built.state_deltas)
    visible_state = build_visible_state(next_state)

    assert "hidden_relic" not in visible_state.model_dump_json()


def test_save_load_preserves_plan() -> None:
    state = make_state()
    built = build_plan_from_intent(
        state,
        "harlan",
        NPCIntent(id="visit-forge", npc_id="harlan", intent_type="visit_location", target_id="forge"),
    )
    state = apply_all(state, built.state_deltas)

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].plans[0].id == "plan-visit-forge"
    assert restored.npcs["harlan"].plans[0].steps[0].step_type == "move"
