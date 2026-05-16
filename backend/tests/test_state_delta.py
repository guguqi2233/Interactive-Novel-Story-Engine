import pytest

from app.core.state_delta import (
    StateDelta,
    StateDeltaError,
    StateDeltaOperation,
    apply_delta,
    inverse_delta,
    rollback_delta,
)
from app.core.world_state import GameState, NPCState


def make_state() -> GameState:
    return GameState(
        world_id="test-world",
        player_visible_facts={"knows_square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="smithy",
                suspicion=1,
                knowledge={"forge_secret"},
            )
        },
        flags={"met_blacksmith": False},
    )


def test_set_can_modify_field() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.SET, path="player.location_id", value="smithy")

    next_state = apply_delta(state, delta)

    assert next_state.player.location_id == "smithy"
    assert state.player.location_id == "start"


def test_inc_can_increase_number() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.INC, path="npcs.harlan.suspicion", value=2)

    next_state = apply_delta(state, delta)

    assert next_state.npcs["harlan"].suspicion == 3


def test_add_does_not_duplicate_existing_value() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.ADD, path="player.inventory", value="iron_key")

    once = apply_delta(state, delta)
    twice = apply_delta(once, delta)

    assert twice.player.inventory == ["iron_key"]


def test_remove_can_remove_value() -> None:
    state = make_state()
    added = apply_delta(
        state,
        StateDelta(operation=StateDeltaOperation.ADD, path="player.inventory", value="iron_key"),
    )

    next_state = apply_delta(
        added,
        StateDelta(operation=StateDeltaOperation.REMOVE, path="player.inventory", value="iron_key"),
    )

    assert next_state.player.inventory == []


def test_invalid_path_raises_clear_error() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.SET, path="npcs.missing.suspicion", value=1)

    with pytest.raises(StateDeltaError, match="Invalid state path segment: missing"):
        apply_delta(state, delta)


def test_delta_does_not_silently_fail_for_wrong_type() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.INC, path="player.location_id", value=1)

    with pytest.raises(StateDeltaError, match="Cannot inc non-numeric path"):
        apply_delta(state, delta)


def test_inverse_delta_can_rollback_set() -> None:
    state = make_state()
    delta = StateDelta(operation=StateDeltaOperation.SET, path="flags.met_blacksmith", value=True)
    inverse = inverse_delta(state, delta)

    changed = apply_delta(state, delta)
    restored = rollback_delta(changed, inverse)

    assert changed.flags["met_blacksmith"] is True
    assert restored.flags["met_blacksmith"] is False

