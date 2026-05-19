from app.core.state_delta import apply_delta
from app.core.world_state import (
    FactionState,
    GameState,
    LocationState,
    NPCSocialDisposition,
    NPCState,
    RelationshipState,
    ReputationState,
    load_game_state_payload,
)
from app.engine.rules.npc_social_disposition import (
    derive_from_relationships,
    disposition_to_behavior_weights,
    disposition_to_dialogue_tone,
    update_from_event,
)


def make_state() -> GameState:
    return GameState(
        world_id="npc-social-disposition-test",
        locations={"square": LocationState(id="square", name="Square")},
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(value=30),
                conflict_level=1,
                alert_level=2,
            )
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", faction_id="watch"),
            "mira": NPCState(id="mira", location_id="square"),
        },
        relationships={
            "harlan_player": RelationshipState(
                id="harlan_player",
                source_id="harlan",
                target_id="player",
                relation_type="general",
                trust=20,
                fear=5,
                known_by_player=False,
            ),
            "harlan_mira": RelationshipState(
                id="harlan_mira",
                source_id="harlan",
                target_id="mira",
                relation_type="ally",
                trust=20,
                affinity=20,
                obligation=10,
                known_by_player=False,
            ),
        },
    )


def test_witnessed_violence_increases_fear() -> None:
    state = make_state()
    result = update_from_event(state, "harlan", "witnessed_violence", event_id="violence-1", severity=2)
    next_state = apply_delta(state, result.state_deltas[0])

    assert next_state.npcs["harlan"].social_disposition.fear_player == 16
    assert next_state.npcs["harlan"].social_disposition.risk_tolerance == 40


def test_repeated_help_increases_trust() -> None:
    state = make_state()
    result = update_from_event(state, "harlan", "repeated_help", event_id="help-1", severity=3)
    next_state = apply_delta(state, result.state_deltas[0])

    assert next_state.npcs["harlan"].social_disposition.trust_player == 18


def test_faction_conflict_influences_loyalty_behavior() -> None:
    state = make_state()
    derived = derive_from_relationships(state, "harlan")
    updated = update_from_event(
        state.model_copy(update={"npcs": {"harlan": state.npcs["harlan"].model_copy(update={"social_disposition": derived}), "mira": state.npcs["mira"]}}),
        "harlan",
        "faction_conflict",
        severity=2,
    )

    assert derived.loyalty_to_faction >= 70
    assert updated.disposition.loyalty_to_faction > derived.loyalty_to_faction
    assert disposition_to_behavior_weights(updated.disposition).report_to_faction >= updated.disposition.loyalty_to_faction


def test_low_risk_tolerance_weights_avoid() -> None:
    disposition = NPCSocialDisposition(fear_player=60, risk_tolerance=10)

    weights = disposition_to_behavior_weights(disposition)

    assert weights.avoid_actor > weights.share_rumor


def test_high_loyalty_weights_report_to_faction() -> None:
    disposition = NPCSocialDisposition(loyalty_to_faction=90, moral_flexibility=10)

    weights = disposition_to_behavior_weights(disposition)

    assert weights.report_to_faction >= 130


def test_update_uses_state_delta_and_event() -> None:
    state = make_state()
    result = update_from_event(state, "harlan", "repeated_help", event_id="help-1", severity=1)

    assert result.state_deltas[0].path == "npcs.harlan.social_disposition"
    assert result.state_deltas[0].metadata["source"] == "npc_social_disposition"
    assert result.event is not None
    assert result.event.action_type == "npc_social_disposition_update"
    assert result.event.state_deltas == result.state_deltas


def test_save_load_preserves_social_disposition() -> None:
    state = make_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"social_disposition": NPCSocialDisposition(trust_player=45, fear_player=12, loyalty_to_faction=80)}
    )

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].social_disposition.trust_player == 45
    assert restored.npcs["harlan"].social_disposition.loyalty_to_faction == 80


def test_dialogue_tone_is_safe_summary() -> None:
    summary = disposition_to_dialogue_tone(
        NPCSocialDisposition(trust_player=70, fear_player=20, loyalty_to_faction=80, risk_tolerance=30, secrecy_preference=60)
    )

    assert summary == "trust=high; fear=low; faction_loyalty=high; risk=low; secrecy=medium"
    assert "hidden" not in summary
