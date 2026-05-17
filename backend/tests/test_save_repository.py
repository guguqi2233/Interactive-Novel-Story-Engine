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
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.INC,
                path="turn",
                value=1,
            )
        ],
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
    assert events[0].state_deltas[0].operation == StateDeltaOperation.INC
    assert len(events[0].state_deltas) == 1


def test_list_events_preserves_append_sequence(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state())

    repository.append_event("save-1", make_event("event-2", turn=2))
    repository.append_event("save-1", make_event("event-1", turn=1))
    events = repository.list_events("save-1")

    assert [event.event_id for event in events] == ["event-2", "event-1"]


def test_save_snapshot_preserves_event_log_sequence_for_same_turn(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    player_event = make_event("z-player-event", turn=1)
    system_event = make_event("a-system-event", turn=1)
    system_event.actor_id = "system"
    system_event.action_type = "world_tick"

    repository.save_snapshot("save-1", make_state(turn=1), [player_event, system_event])
    events = repository.list_events("save-1")

    assert [event.event_id for event in events] == ["z-player-event", "a-system-event"]


def test_missing_save_errors_are_clear(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    with pytest.raises(SaveRepositoryError, match="Save not found: missing"):
        repository.load_save("missing")


def test_list_saves_can_filter_by_world_id(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state())
    other_state = make_state()
    other_state.world_id = "other-world"
    repository.create_save("save-2", other_state)

    saves = repository.list_saves(world_id="other-world")

    assert [save.save_id for save in saves] == ["save-2"]


def test_delete_save_removes_state_events_and_memories(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.create_save("save-1", make_state())
    repository.append_event("save-1", make_event())

    repository.delete_save("save-1")

    with pytest.raises(SaveRepositoryError, match="Save not found: save-1"):
        repository.load_save("save-1")
