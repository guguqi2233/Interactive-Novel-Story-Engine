from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    GameState,
    LocationState,
    NPCState,
    RelationshipState,
    RumorState,
)
from app.engine.rules.npc_relationship_behavior import (
    RelationshipBehaviorRule,
    RelationshipBehaviorType,
    resolve_relationship_behaviors,
)
from app.session_store import build_visible_state


def make_state(relationship: RelationshipState) -> GameState:
    return GameState(
        world_id="relationship-behavior-test",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "mira": NPCState(id="mira", location_id="square"),
        },
        relationships={relationship.id: relationship},
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_high_trust_generates_help_or_warn_intent() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_trust",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=60,
            affinity=20,
            known_by_player=True,
        )
    )
    rule = RelationshipBehaviorRule(
        id="trusted-help",
        behavior_type=RelationshipBehaviorType.HELP_ACTOR,
        min_trust=50,
        priority=5,
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "talk_to_npc"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "player"
    assert result.candidates[0].behavior_type == RelationshipBehaviorType.HELP_ACTOR


def test_high_fear_generates_avoid_intent() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_fear",
            source_id="harlan",
            target_id="player",
            relation_type="fear",
            fear=70,
            trust=0,
        )
    )
    rule = RelationshipBehaviorRule(
        id="fear-avoid",
        behavior_type=RelationshipBehaviorType.AVOID_ACTOR,
        min_fear=50,
        priority=8,
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "avoid_actor"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "player"


def test_dead_npc_generates_no_relationship_behavior() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_trust",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=80,
        )
    )
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )
    rule = RelationshipBehaviorRule(
        id="trusted-help",
        behavior_type=RelationshipBehaviorType.HELP_ACTOR,
        min_trust=50,
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])

    assert result.state_deltas == []
    assert result.events == []
    assert result.candidates == []


def test_hostile_npc_can_report_actor() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_hostile",
            source_id="harlan",
            target_id="player",
            relation_type="hostile",
            trust=-60,
            fear=10,
        )
    )
    state.crimes["crime-1"] = CrimeState(
        id="crime-1",
        crime_type="theft",
        actor_id="player",
        location_id="square",
        status=CrimeStatus.WITNESSED,
        witnessed_by=["harlan"],
    )
    rule = RelationshipBehaviorRule(
        id="hostile-report",
        behavior_type=RelationshipBehaviorType.REPORT_ACTOR,
        max_trust=-20,
        min_hostility=30,
        priority=6,
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "report_crime"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "crime-1"


def test_npc_unknown_fact_does_not_share() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_trust",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=70,
        )
    )
    state.rumors["rumor-1"] = RumorState(id="rumor-1", text_for_player="Safe rumor.", known_by_npcs={"harlan"})
    rule = RelationshipBehaviorRule(
        id="share-unknown-fact",
        behavior_type=RelationshipBehaviorType.SHARE_KNOWN_RUMOR,
        min_trust=50,
        required_fact_ids=["unknown_secret"],
        required_rumor_ids=["rumor-1"],
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])

    assert result.state_deltas == []
    assert result.events == []
    assert result.skipped_rule_ids == ["share-unknown-fact"]


def test_hidden_relationship_does_not_enter_player_api() -> None:
    state = make_state(
        RelationshipState(
            id="hidden_harlan_player",
            source_id="harlan",
            target_id="player",
            relation_type="secret",
            trust=80,
            known_by_player=False,
        )
    )

    payload = build_visible_state(state).model_dump(mode="json")

    assert payload["relationships"] == []
    assert "hidden_harlan_player" not in str(payload)


def test_behavior_uses_state_delta_and_event() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_trust",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=60,
        )
    )
    rule = RelationshipBehaviorRule(
        id="trusted-warn",
        behavior_type=RelationshipBehaviorType.WARN_ACTOR,
        min_trust=50,
    )

    result = resolve_relationship_behaviors(state, "harlan", "player", [rule])

    assert result.state_deltas
    assert all(delta.metadata.get("source") in {"npc_intent", "npc_relationship_behavior"} for delta in result.state_deltas)
    assert result.events[0].actor_id == "system"
    assert result.events[0].action_type == "npc_relationship_behavior"
    assert result.events[0].state_deltas == result.state_deltas


def test_behavior_is_deterministic() -> None:
    state = make_state(
        RelationshipState(
            id="harlan_player_fear",
            source_id="harlan",
            target_id="player",
            relation_type="fear",
            fear=80,
        )
    )
    rules = [
        RelationshipBehaviorRule(
            id="fear-avoid",
            behavior_type=RelationshipBehaviorType.AVOID_ACTOR,
            min_fear=50,
            priority=8,
        )
    ]

    first = resolve_relationship_behaviors(state, "harlan", "player", rules)
    second = resolve_relationship_behaviors(state, "harlan", "player", rules)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
