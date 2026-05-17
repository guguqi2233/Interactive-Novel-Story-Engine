from random import Random
from pathlib import Path

from app.core.state_delta import apply_delta
from app.core.world_state import (
    CrimeState,
    CrimeStatus,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.rules.world_tick import run_world_tick
from app.session_store import build_visible_state


def make_social_tick_state(hidden_witness: bool = False) -> GameState:
    return GameState(
        world_id="social-tick-test",
        turn=4,
        locations={"square": LocationState(id="square", name="Square")},
        player={"location_id": "square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                faction_id="watch",
                hidden=hidden_witness,
                alertness=1,
            ),
            "mira": NPCState(id="mira", location_id="square"),
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(value=0, known_to_player=True),
            )
        },
        crimes={
            "crime_1": CrimeState(
                id="crime_1",
                crime_type="theft",
                actor_id="player",
                target_id="coin",
                location_id="square",
                turn=4,
                created_turn=4,
                witnessed_by=["harlan"],
                witness_ids=["harlan"],
                severity=2,
                status=CrimeStatus.WITNESSED,
            )
        },
    )


def apply_tick(state: GameState) -> GameState:
    tick = run_world_tick(state, Random(0))
    next_state = state
    for delta in tick.state_deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_witnessed_crime_becomes_reported_after_tick() -> None:
    state = apply_tick(make_social_tick_state())

    assert state.crimes["crime_1"].status == CrimeStatus.REPORTED
    assert state.crimes["crime_1"].reported_to == ["watch"]


def test_reported_crime_affects_faction_reputation_after_tick() -> None:
    state = apply_tick(make_social_tick_state())

    assert state.factions["watch"].reputation.value == -2
    assert state.factions["watch"].reputation.recent_reasons == ["Reported theft."]


def test_rumor_spreads_after_tick() -> None:
    state = apply_tick(make_social_tick_state())

    assert "rumor_crime_1" in state.rumors
    assert "harlan" in state.rumors["rumor_crime_1"].known_by_npcs

    state = apply_tick(state)

    assert "mira" in state.rumors["rumor_crime_1"].known_by_npcs


def test_same_crime_does_not_repeat_reputation_loss() -> None:
    state = apply_tick(make_social_tick_state())
    reputation_after_first_tick = state.factions["watch"].reputation.value

    state = apply_tick(state)

    assert state.factions["watch"].reputation.value == reputation_after_first_tick
    assert state.social_flags["crime_consequence_processed_crime_1"] is True


def test_hidden_witness_consequence_does_not_enter_visible_state() -> None:
    state = apply_tick(make_social_tick_state(hidden_witness=True))
    visible_state = build_visible_state(state)

    assert "harlan" not in visible_state.model_dump_json()
    assert visible_state.known_crimes[0].id == "crime_1"


def test_tick_generates_system_event_for_social_consequence() -> None:
    tick = run_world_tick(make_social_tick_state(), Random(0))

    assert tick.event is not None
    assert tick.event.actor_id == "system"
    assert tick.event.action_type == "world_tick"
    assert any(delta.metadata.get("source") == "social_consequence_tick" for delta in tick.event.state_deltas)


def test_tick_order_is_deterministic() -> None:
    first = run_world_tick(make_social_tick_state(), Random(0))
    second = run_world_tick(make_social_tick_state(), Random(999))

    assert [(delta.path, delta.operation, delta.value) for delta in first.state_deltas] == [
        (delta.path, delta.operation, delta.value) for delta in second.state_deltas
    ]


def test_save_load_then_tick_continues_social_consequence(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(Path(tmp_path) / "social_tick.db")
    repository.create_save("save-1", make_social_tick_state())
    loaded = repository.load_save("save-1")

    state = apply_tick(loaded)

    assert state.crimes["crime_1"].status == CrimeStatus.REPORTED
    assert state.factions["watch"].reputation.value == -2
