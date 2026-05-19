from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import ActorCondition, FactState, FactVisibility
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.npc_simulation_boundary import (
    NPCSimulationPolicy,
    SimulationCandidateAction,
    SimulationEvent,
    SimulationIntent,
    SimulationPlan,
)


def test_unknown_hidden_fact_does_not_enter_simulation_context() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.facts["unknown_hidden_cache"] = FactState(
        id="unknown_hidden_cache",
        text="A hidden cache nobody in this test knows about.",
        visibility=FactVisibility.HIDDEN,
        known_by=set(),
    )

    context = NPCSimulationPolicy().build_context(state, "harlan")

    assert "unknown_hidden_cache" not in context.npc_known_context.fact_ids


def test_hidden_fact_outside_npc_knowledge_does_not_enter_plan() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.facts["unknown_hidden_cache"] = FactState(
        id="unknown_hidden_cache",
        text="A hidden cache nobody in this test knows about.",
        visibility=FactVisibility.HIDDEN,
        known_by=set(),
    )
    policy = NPCSimulationPolicy()
    context = policy.build_context(state, "harlan")
    candidate = SimulationCandidateAction(
        npc_id="harlan",
        action_type="spread_rumor",
        target_id="forge_tools_missing_rumor",
        required_fact_ids=["unknown_hidden_cache"],
    )
    plan = SimulationPlan(
        npc_id="harlan",
        intents=[
            SimulationIntent(
                npc_id="harlan",
                intent_type="spread_known_rumor",
                candidate_action=candidate,
            )
        ],
    )

    result = policy.validate_plan(state, context, plan)

    assert not result.allowed
    assert any(issue.code == "npc_unknown_fact" for issue in result.issues)


def test_candidate_action_validation_does_not_mutate_game_state() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    before = state.model_dump(mode="json")
    policy = NPCSimulationPolicy()
    context = policy.build_context(state, "harlan")
    candidate = SimulationCandidateAction(
        npc_id="harlan",
        action_type="guard_location",
        target_id=state.npcs["harlan"].location_id,
        required_fact_ids=["old_bridge_creaks_at_midnight"],
    )

    result = policy.validate_candidate_action(state, context, candidate)

    assert result.allowed
    assert state.model_dump(mode="json") == before


def test_simulation_event_must_record_state_delta() -> None:
    policy = NPCSimulationPolicy()
    empty_event = Event(
        event_id="npc-sim-empty",
        turn=1,
        actor_id="system",
        action_type="npc_simulation",
        target_id="harlan",
        result="guard_location",
        visible_to_player=False,
        allow_empty_delta=True,
    )

    empty_result = policy.validate_simulation_event(SimulationEvent(event=empty_event))

    assert not empty_result.allowed
    assert any(issue.code == "event_missing_state_delta" for issue in empty_result.issues)

    delta_event = Event(
        event_id="npc-sim-delta",
        turn=1,
        actor_id="system",
        action_type="npc_simulation",
        target_id="harlan",
        result="guard_location",
        visible_to_player=False,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.harlan.current_activity",
                value="guarding:blacksmith",
                reason="NPC simulation selected a guard duty.",
            )
        ],
    )

    assert policy.validate_simulation_event(SimulationEvent(event=delta_event)).allowed


def test_dead_npc_cannot_simulate() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )
    policy = NPCSimulationPolicy()
    context = policy.build_context(state, "harlan")
    candidate = SimulationCandidateAction(
        npc_id="harlan",
        action_type="guard_location",
        target_id="blacksmith",
    )

    lifecycle = policy.can_simulate_npc(state, "harlan")
    candidate_result = policy.validate_candidate_action(state, context, candidate)

    assert not lifecycle.allowed
    assert any(issue.code == "npc_inactive" for issue in lifecycle.issues)
    assert not candidate_result.allowed
    assert any(issue.code == "npc_inactive" for issue in candidate_result.issues)
