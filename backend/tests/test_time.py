from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import GameState, GameTime, LocationState, PlayerState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.time import advance_time, format_game_time, get_time_of_day
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state() -> GameState:
    return GameState(
        world_id="time-test",
        current_time=GameTime(day=1, minutes_of_day=8 * 60),
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "smithy"}),
            "smithy": LocationState(id="smithy", name="Smithy"),
        },
    )


def make_intent(action_type: PlayerActionType, minutes: int | None = None) -> PlayerIntent:
    return PlayerIntent(
        action_type=action_type,
        raw_text="test",
        confidence=1.0,
        requires_clarification=False,
        minutes=minutes,
    )


def test_time_advances() -> None:
    state = advance_time(make_state(), 45)

    assert state.current_time.day == 1
    assert state.current_time.minutes_of_day == 8 * 60 + 45
    assert get_time_of_day(state) == "morning"
    assert format_game_time(state) == "Day 1, 08:45"


def test_time_rolls_over_to_next_day() -> None:
    state = GameState(
        world_id="time-test",
        current_time=GameTime(day=1, minutes_of_day=23 * 60 + 50),
    )

    next_state = advance_time(state, 20)

    assert next_state.current_time.day == 2
    assert next_state.current_time.minutes_of_day == 10
    assert format_game_time(next_state) == "Day 2, 00:10"


def test_wait_advances_specified_minutes() -> None:
    state = make_state()
    intent = make_intent(PlayerActionType.WAIT, minutes=45)

    result = ActionDispatcher().resolve(intent, state, Random(1))
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)

    assert next_state.current_time.minutes_of_day == 8 * 60 + 45


def test_actions_produce_time_state_delta() -> None:
    state = make_state()
    result = ActionDispatcher().resolve(make_intent(PlayerActionType.OBSERVE), state, Random(1))

    assert result.state_deltas
    assert result.state_deltas[0].path == "current_time"
    next_state = apply_delta(state, result.state_deltas[0])
    assert next_state.current_time.minutes_of_day == 8 * 60 + 5

