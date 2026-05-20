from random import Random

from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.world_state import (
    CoverState,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    StealthState,
)
from app.engine.rules.stealth import StealthActionHandler, run_detection_check
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state() -> GameState:
    return GameState(
        world_id="stealth-expansion-test",
        player=PlayerState(location_id="alley", stealth_modifier=4),
        locations={
            "alley": LocationState(id="alley", name="Alley", cover_level=6, light_level=1),
            "plaza": LocationState(id="plaza", name="Plaza", cover_level=0, light_level=10),
        },
        cover_states={
            "alley": CoverState(id="alley", location_id="alley", cover_level=6, light_level=1),
            "plaza": CoverState(id="plaza", location_id="plaza", cover_level=0, light_level=10),
        },
        npcs={
            "guard": NPCState(id="guard", location_id="alley", alertness=1),
            "captain": NPCState(id="captain", location_id="alley", alertness=10),
            "hidden_observer": NPCState(id="hidden_observer", location_id="alley", hidden=True, alertness=12),
        },
    )


def make_intent(raw_text: str, target_id: str | None = None) -> PlayerIntent:
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


def test_hide_success_sets_hidden_stealth_state() -> None:
    state = make_state()
    state.npcs["captain"].location_id = "plaza"
    state.npcs["hidden_observer"].location_id = "plaza"

    attempt = StealthActionHandler().resolve_with_event(make_intent("hide"), state, Random(5))
    next_state = apply_all(state, attempt.action_result.state_deltas)

    assert attempt.action_result.success_level == "success"
    assert next_state.stealth["player"].hidden is True
    assert next_state.stealth["player"].stealth_score > 0


def test_high_light_reduces_detection_score() -> None:
    state = make_state()
    state.npcs = {}

    alley = run_detection_check(state, "player", "alley", Random(1))
    plaza = run_detection_check(state, "player", "plaza", Random(1))

    assert plaza.score < alley.score


def test_noise_event_increases_visible_npc_alertness() -> None:
    state = make_state()
    attempt = StealthActionHandler().resolve_with_event(make_intent("create noise"), state, Random(1))
    next_state = apply_all(state, attempt.action_result.state_deltas)

    assert attempt.action_result.success_level == "success"
    assert next_state.noise_events
    assert next_state.npcs["guard"].alertness == state.npcs["guard"].alertness + 1
    assert next_state.npcs["hidden_observer"].alertness == state.npcs["hidden_observer"].alertness


def test_hidden_observer_identity_not_in_player_narrative() -> None:
    state = make_state()
    state.npcs["guard"].location_id = "plaza"
    state.npcs["captain"].location_id = "plaza"

    attempt = StealthActionHandler().resolve_with_event(make_intent("hide"), state, Random(1))
    serialized = attempt.action_result.model_dump_json()

    assert attempt.detection is not None
    assert attempt.detection.hidden_observer is True
    assert "hidden_observer" not in serialized
    assert "hidden_observer" not in attempt.event.model_dump_json()


def test_failed_shadow_npc_increases_suspicion() -> None:
    state = make_state()
    state.npcs["hidden_observer"].location_id = "plaza"

    attempt = StealthActionHandler().resolve_with_event(make_intent("shadow npc", "captain"), state, Random(1))
    next_state = apply_all(state, attempt.action_result.state_deltas)

    assert attempt.action_result.success_level == "failure"
    assert next_state.npcs["captain"].suspicion >= state.npcs["captain"].suspicion + 2


def test_stealth_actions_return_state_delta_and_event() -> None:
    state = make_state()
    attempt = StealthActionHandler().resolve_with_event(make_intent("set decoy", "coin"), state, Random(1))

    assert isinstance(attempt.event, Event)
    assert attempt.event.action_type == "set_decoy"
    assert attempt.event.state_deltas == attempt.action_result.state_deltas
    assert all(delta.caused_by_event_id == attempt.event.event_id for delta in attempt.action_result.state_deltas)


def test_save_load_preserves_stealth_state() -> None:
    state = make_state()
    state.stealth["player"] = StealthState(actor_id="player", hidden=True, stealth_score=42, shadowing_target_id="guard")

    loaded = GameState.model_validate_json(state.model_dump_json())

    assert loaded.stealth["player"].hidden is True
    assert loaded.stealth["player"].stealth_score == 42
    assert loaded.stealth["player"].shadowing_target_id == "guard"

