from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    FactionState,
    GameState,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCIntent,
    NPCState,
    RelationshipState,
)
from app.engine.rules.npc_simulation_tick import NPCSimulationTickBudget, run_npc_simulation_tick


def make_state() -> GameState:
    return GameState(
        world_id="npc-simulation-tick-test",
        locations={
            "square": LocationState(id="square", name="Square", exits={"north": "gate"}),
            "gate": LocationState(id="gate", name="Gate"),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "mira": NPCState(id="mira", location_id="square"),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_tick_order_is_stable() -> None:
    state = make_state()
    state.relationships["harlan_player"] = RelationshipState(
        id="harlan_player",
        source_id="harlan",
        target_id="player",
        relation_type="friend",
        trust=60,
    )

    result = run_npc_simulation_tick(
        state,
        budget=NPCSimulationTickBudget(max_npcs_per_tick=1, max_intents_per_npc=2),
    )

    phases = [entry.phase for entry in result.debug_output if entry.npc_id == "harlan"]
    assert phases[:9] == [
        "prune_expired_intents",
        "daily_replanning",
        "memory_reactions",
        "relationship_behavior",
        "faction_duties",
        "rumor_decisions",
        "conflict_avoidance",
        "select_intent",
        "build_or_advance_plan",
    ]


def test_tick_respects_max_npc_budget() -> None:
    state = make_state()

    result = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1))

    assert result.processed_npc_ids == ["harlan"]
    assert result.budget_exhausted is True


def test_intent_budget_prevents_unbounded_generation() -> None:
    state = make_state()
    state.relationships["harlan_player"] = RelationshipState(
        id="harlan_player",
        source_id="harlan",
        target_id="player",
        relation_type="friend",
        trust=70,
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "faction_id": "watch",
            "faction_duties": [
                NPCFactionDuty(
                    id="guard-square",
                    duty_type=NPCFactionDutyType.GUARD_LOCATION,
                    target_id="square",
                )
            ],
        }
    )

    result = run_npc_simulation_tick(
        state,
        budget=NPCSimulationTickBudget(max_npcs_per_tick=1, max_intents_per_npc=1),
    )
    next_state = apply_all(state, result.state_deltas)

    assert len(next_state.npcs["harlan"].intent_queue) <= 1
    assert result.budget_exhausted is True


def test_hidden_npc_action_is_not_visible() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(update={"hidden": True, "discovered_by": []})
    state.npcs["mira"] = state.npcs["mira"].model_copy(update={"hostile_to": ["harlan"]})

    result = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1))

    assert result.events
    assert all(event.visible_to_player is False for event in result.events)
    assert all(delta.metadata.get("visible_to_player") != "true" for delta in result.state_deltas)


def test_system_events_are_recorded() -> None:
    state = make_state()
    state.factions["watch"] = FactionState(id="watch", name="Watch")
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "faction_id": "watch",
            "faction_duties": [
                NPCFactionDuty(
                    id="guard-square",
                    duty_type=NPCFactionDutyType.GUARD_LOCATION,
                    target_id="square",
                )
            ],
        }
    )

    result = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1))

    assert result.events
    assert all(event.actor_id == "system" for event in result.events)
    assert all(event.state_deltas for event in result.events)


def test_state_delta_application_builds_plan_from_selected_intent() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "intent_queue": [
                NPCIntent(
                    id="visit-gate",
                    npc_id="harlan",
                    intent_type="visit_location",
                    priority=5,
                    target_id="gate",
                    target_type="location",
                    created_turn=0,
                )
            ]
        }
    )

    result = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1))
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].plans
    assert next_state.npcs["harlan"].plans[0].source_intent_id == "visit-gate"


def test_dead_npc_is_skipped() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1))

    assert result.skipped_npc_ids == ["harlan"]
    assert result.processed_npc_ids == ["mira"]
