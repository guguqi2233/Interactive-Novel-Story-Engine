from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState, GameTime

MINUTES_PER_DAY = 24 * 60


def advance_time(state: GameState, minutes: int) -> GameState:
    if minutes < 0:
        raise ValueError("Cannot advance time by negative minutes")
    return apply_delta(state, make_time_delta(state, minutes))


def make_time_delta(state: GameState, minutes: int) -> StateDelta:
    if minutes < 0:
        raise ValueError("Cannot advance time by negative minutes")
    total_minutes = state.current_time.minutes_of_day + minutes
    extra_days, minutes_of_day = divmod(total_minutes, MINUTES_PER_DAY)
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path="current_time",
        value=GameTime(
            day=state.current_time.day + extra_days,
            minutes_of_day=minutes_of_day,
        ),
        reason=f"Advance game time by {minutes} minutes.",
    )


def get_time_of_day(state: GameState) -> str:
    minutes = state.current_time.minutes_of_day
    if 5 * 60 <= minutes < 12 * 60:
        return "morning"
    if 12 * 60 <= minutes < 17 * 60:
        return "afternoon"
    if 17 * 60 <= minutes < 21 * 60:
        return "evening"
    return "night"


def format_game_time(state: GameState) -> str:
    hours, minutes = divmod(state.current_time.minutes_of_day, 60)
    return f"Day {state.current_time.day}, {hours:02d}:{minutes:02d}"

