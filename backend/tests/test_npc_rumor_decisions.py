from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    EmotionalState,
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    PrimaryEmotion,
    RelationshipState,
    RumorState,
)
from app.engine.rules.npc_rumor_decisions import NPCRumorDecisionType, decide_npc_rumor_action
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="npc-rumor-decision-test",
        turn=7,
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", faction_id="watch"),
            "mira": NPCState(id="mira", location_id="square"),
        },
        factions={"watch": FactionState(id="watch", name="Watch", tags=["law"])},
        relationships={
            "harlan_mira": RelationshipState(
                id="harlan_mira",
                source_id="harlan",
                target_id="mira",
                relation_type="friend",
                trust=50,
            )
        },
        rumors={
            "rumor-1": RumorState(
                id="rumor-1",
                text_for_player="A safe public-facing rumor.",
                known_by_npcs={"harlan"},
                spread_level=1,
            )
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_unknown_rumor_is_not_spread() -> None:
    state = make_state()
    state.rumors["rumor-1"] = state.rumors["rumor-1"].model_copy(update={"known_by_npcs": set()})

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")

    assert result.rejected_reason == "npc_unknown_rumor"
    assert result.state_deltas == []
    assert result.events == []
    assert result.decision is not None
    assert result.decision.decision == NPCRumorDecisionType.IGNORE_RUMOR


def test_high_trust_relationship_enqueues_spread_intent() -> None:
    state = make_state()

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")
    next_state = apply_all(state, result.state_deltas)

    assert result.decision is not None
    assert result.decision.decision == NPCRumorDecisionType.ENQUEUE_SPREAD_RUMOR_INTENT
    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "spread_rumor"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "rumor-1"


def test_dead_npc_does_not_make_rumor_decision() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")

    assert result.rejected_reason == "npc_inactive"
    assert result.decision is None
    assert result.state_deltas == []
    assert result.events == []


def test_low_trust_relationship_distorts_rumor() -> None:
    state = make_state()
    state.relationships["harlan_mira"] = state.relationships["harlan_mira"].model_copy(update={"trust": -20})

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")
    next_state = apply_all(state, result.state_deltas)

    assert result.decision is not None
    assert result.decision.decision == NPCRumorDecisionType.DISTORT_RUMOR
    assert next_state.npcs["harlan"].plan_state["rumor_decisions"]["rumor-1"] == "distort_rumor"


def test_faction_aligned_rumor_can_share_with_faction() -> None:
    state = make_state()
    state.rumors["rumor-1"] = state.rumors["rumor-1"].model_copy(update={"tags": ["law", "faction"]})

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_faction_id="watch")
    next_state = apply_all(state, result.state_deltas)

    assert result.decision is not None
    assert result.decision.decision == NPCRumorDecisionType.SHARE_WITH_FACTION
    assert "watch" in next_state.rumors["rumor-1"].known_by_factions


def test_secret_rumor_does_not_enter_player_facing_text() -> None:
    state = make_state()
    state.facts["hidden_fact"] = FactState(
        id="hidden_fact",
        text="The mayor hid the missing tools under the shrine.",
        visibility=FactVisibility.HIDDEN,
    )
    state.rumors["secret-rumor"] = RumorState(
        id="secret-rumor",
        fact_id="hidden_fact",
        text_for_player="The mayor hid the missing tools under the shrine.",
        known_by_npcs={"harlan"},
        known_by_player=True,
        tags=["secret"],
    )
    state.rumors["rumor-1"] = state.rumors["rumor-1"].model_copy(update={"known_by_player": True})

    payload = build_visible_state(state).model_dump(mode="json")

    assert "mayor hid the missing tools" not in str(payload)
    rumor_text_by_id = {rumor["id"]: rumor["text_for_player"] for rumor in payload["known_rumors"]}
    assert rumor_text_by_id["rumor-1"] == "A safe public-facing rumor."
    assert rumor_text_by_id["secret-rumor"] == (
        "You have heard a vague rumor, but not enough to confirm the details."
    )


def test_decision_is_deterministic() -> None:
    state = make_state()
    state.npcs["harlan"].emotional_state = EmotionalState(
        primary_emotion=PrimaryEmotion.SUSPICIOUS,
        intensity=75,
    )

    first = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")
    second = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_decision_records_event() -> None:
    state = make_state()

    result = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")

    assert result.events
    assert result.events[0].actor_id == "system"
    assert result.events[0].action_type == "npc_rumor_decision"
    assert result.events[0].state_deltas == result.state_deltas


def test_decision_marker_prevents_repeated_processing() -> None:
    state = make_state()
    first = decide_npc_rumor_action(state, "harlan", "rumor-1", target_actor_id="mira")
    next_state = apply_all(state, first.state_deltas)

    second = decide_npc_rumor_action(next_state, "harlan", "rumor-1", target_actor_id="mira")

    assert first.state_deltas
    assert second.rejected_reason == "rumor_decision_already_processed"
    assert second.state_deltas == []
