from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import CrimeStatus, GameState
from app.engine.rules.crime import apply_crime_consequences
from app.engine.rules.rumors import propagate_rumors


def run_social_consequence_tick(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    working_state = state

    for delta in _resolve_crime_reports(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    for delta in propagate_rumors(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    return deltas


def _resolve_crime_reports(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    working_state = state
    for crime in sorted(state.crimes.values(), key=lambda item: item.id):
        if crime.status not in {CrimeStatus.HIDDEN, CrimeStatus.WITNESSED}:
            continue
        marker_key = _crime_consequence_marker(crime.id)
        if state.social_flags.get(marker_key) is True:
            continue
        if not crime.witnessed_by:
            continue
        crime_deltas = apply_crime_consequences(working_state, crime.id)
        for delta in crime_deltas:
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)
        marker_delta = StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"social_flags.{marker_key}",
            value=True,
            reason="Social consequence processed for crime.",
            metadata={
                "source": "social_consequence_tick",
                "crime_id": crime.id,
                "consequence_id": marker_key,
            },
        )
        deltas.append(marker_delta)
        working_state = apply_delta(working_state, marker_delta)
    return deltas


def _crime_consequence_marker(crime_id: str) -> str:
    return f"crime_consequence_processed_{crime_id}"
