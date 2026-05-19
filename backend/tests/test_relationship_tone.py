from app.core.world_state import EmotionalState, GameState, NPCState, PrimaryEmotion, RelationshipState
from app.engine.rules.graphs import build_relationship_graph
from app.engine.rules.relationship_tone import (
    RelationshipTone,
    apply_tone_modifier,
    derive_tone_from_relationship,
    get_tone_for_dialogue,
    tone_summary_for_prompt,
)
from app.llm.context_builder import build_npc_dialogue_profile_context


def _state_with_relationship(relationship: RelationshipState) -> GameState:
    return GameState(
        world_id="test_world",
        npcs={"harlan": NPCState(id="harlan", location_id="square")},
        relationships={relationship.id: relationship},
    )


def test_friendly_relationship_derives_warm_tone() -> None:
    relationship = RelationshipState(
        id="harlan_player_friend",
        source_id="harlan",
        target_id="player",
        relation_type="friend",
        trust=45,
        affinity=30,
        fear=0,
        known_by_player=True,
    )

    tone = derive_tone_from_relationship(relationship)

    assert tone.warmth >= 70
    assert tone.address_style in {"friendly address", "familiar address"}
    assert tone.trust_expression in {"warmer", "open"}


def test_hostile_relationship_derives_cold_hostile_tone() -> None:
    relationship = RelationshipState(
        id="harlan_player_hostile",
        source_id="harlan",
        target_id="player",
        relation_type="hostile",
        trust=-50,
        affinity=-10,
        fear=10,
        known_by_player=True,
    )

    tone = derive_tone_from_relationship(relationship)

    assert tone.tension >= 70
    assert tone.address_style == "cold distant address"
    assert tone.trust_expression == "guarded"


def test_high_fear_makes_address_more_cautious() -> None:
    relationship = RelationshipState(
        id="harlan_player_afraid",
        source_id="harlan",
        target_id="player",
        relation_type="fearful",
        trust=10,
        affinity=0,
        fear=75,
        known_by_player=True,
    )

    tone = derive_tone_from_relationship(relationship)

    assert tone.address_style == "cautious formal address"
    assert tone.fear == 75
    assert tone.avoidance >= 75


def test_high_intimacy_changes_address_style() -> None:
    relationship = RelationshipState(
        id="harlan_player_close",
        source_id="harlan",
        target_id="player",
        relation_type="close",
        trust=40,
        affinity=70,
        fear=0,
        known_by_player=True,
    )

    tone = derive_tone_from_relationship(relationship)

    assert tone.intimacy >= 90
    assert tone.address_style == "familiar address"
    assert tone.formality == "low"


def test_hidden_relationship_still_not_in_player_visible_graph() -> None:
    state = _state_with_relationship(
        RelationshipState(
            id="hidden_shadow",
            source_id="harlan",
            target_id="player",
            relation_type="secret",
            trust=90,
            known_by_player=False,
        )
    )

    graph = build_relationship_graph(state, debug=False)

    assert graph.edges == []


def test_tone_summary_does_not_leak_hidden_facts() -> None:
    relationship = RelationshipState(
        id="harlan_player_secret",
        source_id="harlan",
        target_id="player",
        relation_type="secret",
        trust=20,
        affinity=10,
        tags=["hidden_fact:mayor_hides_tools"],
        known_by_player=False,
    )

    summary = tone_summary_for_prompt(derive_tone_from_relationship(relationship))

    assert "mayor_hides_tools" not in summary
    assert "hidden_fact" not in summary
    assert "warmth=" in summary


def test_tone_does_not_modify_relationship_values() -> None:
    state = _state_with_relationship(
        RelationshipState(
            id="harlan_player_friend",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=35,
            affinity=20,
        )
    )

    before = state.relationships["harlan_player_friend"].model_copy(deep=True)
    tone = get_tone_for_dialogue(state, "harlan", "player")
    modified = apply_tone_modifier(tone, "recent_betrayal")

    assert state.relationships["harlan_player_friend"] == before
    assert modified.tension > tone.tension


def test_emotional_state_can_influence_tone() -> None:
    state = _state_with_relationship(
        RelationshipState(
            id="harlan_player",
            source_id="harlan",
            target_id="player",
            relation_type="general",
            trust=5,
            affinity=0,
        )
    )
    state.npcs["harlan"].emotional_state = EmotionalState(
        primary_emotion=PrimaryEmotion.DEFENSIVE,
        intensity=80,
        stress=80,
    )

    tone = get_tone_for_dialogue(state, "harlan", "player")

    assert tone.tension >= 35
    assert tone.avoidance >= 20


def test_dialogue_context_includes_safe_relationship_tone_summary() -> None:
    state = _state_with_relationship(
        RelationshipState(
            id="harlan_player_friend",
            source_id="harlan",
            target_id="player",
            relation_type="friend",
            trust=50,
            affinity=20,
            known_by_player=False,
            tags=["hidden_fact:secret"],
        )
    )

    context = build_npc_dialogue_profile_context(state, "harlan")

    assert "trust_expression=" in context.relationship_tone_summary
    assert "hidden_fact" not in context.relationship_tone_summary
    assert "secret" not in context.relationship_tone_summary
