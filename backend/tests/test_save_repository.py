from pathlib import Path

import pytest

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository


def make_state(turn: int = 0) -> GameState:
    return GameState(
        world_id="save-test",
        turn=turn,
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
        objects={
            "coin": WorldObjectState(
                id="coin",
                location_id="square",
                discovered_by=["player"],
            )
        },
        player_visible_facts={"coin"},
    )


def make_event(event_id: str = "event-1", turn: int = 1) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="player",
        action_type="wait",
        result="success",
        visible_to_player=True,
        input_text="等待",
        state_delta=StateDelta(
            operation=StateDeltaOperation.INC,
            path="turn",
            value=1,
        ),
        narrative_text="时间过去了。",
    )


def make_repository(tmp_path: Path) -> SQLiteSaveRepository:
    return SQLiteSaveRepository(tmp_path / "test_save.db")


def test_create_and_load_save_round_trips_game_state(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    state = make_state()

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded == state
    assert loaded.player_visible_facts == {"coin"}


def test_save_state_updates_existing_save(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state(turn=0))

    repository.save_state("save-1", make_state(turn=3))
    loaded = repository.load_save("save-1")

    assert loaded.turn == 3


def test_append_and_list_events_round_trips_full_event_json(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state())
    event = make_event()

    repository.append_event("save-1", event)
    events = repository.list_events("save-1")

    assert events == [event]
    assert events[0].state_delta is not None
    assert events[0].state_delta.operation == StateDeltaOperation.INC
    assert len(events[0].state_deltas) == 1


def test_list_events_orders_by_turn(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state())

    repository.append_event("save-1", make_event("event-2", turn=2))
    repository.append_event("save-1", make_event("event-1", turn=1))
    events = repository.list_events("save-1")

    assert [event.event_id for event in events] == ["event-1", "event-2"]


def test_missing_save_errors_are_clear(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    with pytest.raises(SaveRepositoryError, match="Save not found: missing"):
        repository.load_save("missing")
