from random import Random

from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.world_state import (
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    LeverageState,
    LocationState,
    NPCState,
    RelationshipState,
    ReputationState,
    SocialMoveDefinition,
)
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.social_manipulation import SocialManipulationActionHandler
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state() -> GameState:
    return GameState(
        world_id="social-manipulation-test",
        player={"location_id": "square", "currency": 20},
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", faction_id="watch", knowledge=["public_clue", "hidden_secret"]),
        },
        relationships={
            "harlan_player": RelationshipState(
                id="harlan_player",
                source_id="harlan",
                target_id="player",
                relation_type="general",
                trust=2,
                affinity=1,
                known_by_player=True,
            )
        },
        factions={
            "watch": FactionState(id="watch", name="Watch", reputation=ReputationState(value=10, known_to_player=True)),
        },
        facts={
            "public_clue": FactState(id="public_clue", text="The gate was open.", visibility=FactVisibility.DISCOVERABLE),
            "hidden_secret": FactState(id="hidden_secret", text="Hidden culprit truth.", visibility=FactVisibility.HIDDEN),
            "leverage_fact": FactState(id="leverage_fact", text="Harlan hid contraband.", visibility=FactVisibility.HIDDEN),
        },
    )


def intent(raw_text: str, target_id: str = "harlan") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        target_id=target_id,
        confidence=0.9,
        requires_clarification=False,
    )


def apply_all(state: GameState, deltas) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_persuade_success_changes_relationship() -> None:
    state = make_state()

    result = ActionDispatcher().resolve(intent("persuade", "harlan"), state, Random(0))
    next_state = apply_all(state, result.state_deltas)

    assert result.success_level == "success"
    assert next_state.relationships["harlan_player"].trust > state.relationships["harlan_player"].trust


def test_bribe_requires_currency() -> None:
    state = make_state()
    state.player.currency = 0

    result = ActionDispatcher().resolve(intent("bribe", "harlan"), state, Random(0))

    assert result.success_level == "failure"
    assert "insufficient currency" in result.reason
    assert result.state_deltas == []


def test_blackmail_requires_known_leverage_fact() -> None:
    state = make_state()
    missing = ActionDispatcher().resolve(intent("blackmail", "harlan"), state, Random(0))
    state.leverages["lev_1"] = LeverageState(id="lev_1", target_npc_id="harlan", fact_id="leverage_fact", known_by_player=True, strength=80, hidden=True)
    state.player_visible_facts.add("leverage_fact")

    success = ActionDispatcher().resolve(intent("blackmail", "harlan"), state, Random(0))
    next_state = apply_all(state, success.state_deltas)

    assert missing.success_level == "failure"
    assert success.success_level == "success"
    assert next_state.leverages["lev_1"].used is True
    assert next_state.relationships["harlan_player"].fear > state.relationships["harlan_player"].fear


def test_deceive_failure_increases_suspicion() -> None:
    state = make_state()
    state.relationships["harlan_player"].trust = -10
    state.npcs["harlan"].emotional_state.stress = 80

    result = ActionDispatcher().resolve(intent("deceive", "harlan"), state, Random(1))
    next_state = apply_all(state, result.state_deltas)

    assert result.success_level == "failure"
    assert next_state.npcs["harlan"].suspicion == state.npcs["harlan"].suspicion + 1


def test_extract_information_only_reveals_npc_known_non_hidden_facts() -> None:
    state = make_state()

    result = ActionDispatcher().resolve(intent("extract information", "harlan"), state, Random(0))
    next_state = apply_all(state, result.state_deltas)
    payload = result.model_dump_json()

    assert result.success_level == "success"
    assert "public_clue" in next_state.player_visible_facts
    assert "hidden_secret" not in next_state.player_visible_facts
    assert "Hidden culprit truth" not in payload


def test_extract_information_does_not_reveal_unknown_or_hidden_fact() -> None:
    state = make_state()
    state.npcs["harlan"].knowledge = ["hidden_secret"]

    result = ActionDispatcher().resolve(intent("extract information", "harlan"), state, Random(0))
    next_state = apply_all(state, result.state_deltas)

    assert result.success_level == "failure"
    assert "hidden_secret" not in next_state.player_visible_facts


def test_social_manipulation_returns_state_delta_and_event() -> None:
    state = make_state()
    attempt = SocialManipulationActionHandler().resolve_with_event(intent("comfort", "harlan"), state, Random(0))

    assert isinstance(attempt.event, Event)
    assert attempt.event.action_type == "comfort"
    assert attempt.event.state_deltas == attempt.action_result.state_deltas
    assert all(delta.caused_by_event_id == attempt.event.event_id for delta in attempt.action_result.state_deltas)


def test_save_load_preserves_social_manipulation_schema() -> None:
    state = make_state()
    state.social_moves["persuade"] = SocialMoveDefinition(id="persuade", move_type="persuade", label="Persuade", difficulty=8)
    state.leverages["lev_1"] = LeverageState(id="lev_1", target_npc_id="harlan", fact_id="leverage_fact", known_by_player=True, strength=50)

    loaded = GameState.model_validate_json(state.model_dump_json())

    assert loaded.social_moves["persuade"].difficulty == 8
    assert loaded.leverages["lev_1"].fact_id == "leverage_fact"
