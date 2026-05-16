import pytest
from pydantic import ValidationError

from app.core.event_log import Event, EventLog, EventLogError
from app.core.state_delta import StateDelta, StateDeltaOperation


def make_delta(path: str = "player.location_id", value: str = "smithy") -> StateDelta:
    return StateDelta(operation=StateDeltaOperation.SET, path=path, value=value)


def make_event(event_id: str, turn: int) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="player",
        action_type="move",
        target_id="smithy",
        input_text="Go to the smithy.",
        result="accepted",
        state_delta=make_delta(),
        visible_to_player=True,
        narrative_text="You walk to the smithy.",
    )


def test_append_then_read_event() -> None:
    event_log = EventLog()
    event = make_event("event-1", 1)

    event_log.append(event)

    assert event_log.list_events() == [event]


def test_turn_order_cannot_move_backwards() -> None:
    event_log = EventLog([make_event("event-1", 2)])

    with pytest.raises(EventLogError, match="Event turn cannot move backwards"):
        event_log.append(make_event("event-2", 1))


def test_get_events_since_returns_events_from_turn_onward() -> None:
    event_log = EventLog(
        [
            make_event("event-1", 1),
            make_event("event-2", 2),
            make_event("event-3", 3),
        ]
    )

    events = event_log.get_events_since(2)

    assert [event.event_id for event in events] == ["event-2", "event-3"]


def test_get_latest_returns_latest_n_events() -> None:
    event_log = EventLog(
        [
            make_event("event-1", 1),
            make_event("event-2", 2),
            make_event("event-3", 3),
        ]
    )

    events = event_log.get_latest(2)

    assert [event.event_id for event in events] == ["event-2", "event-3"]


def test_event_requires_state_delta_by_default() -> None:
    with pytest.raises(ValidationError, match="Event must include state_deltas"):
        Event(
            event_id="event-1",
            turn=1,
            actor_id="player",
            action_type="look",
            result="accepted",
            visible_to_player=True,
        )


def test_event_can_explicitly_allow_empty_delta() -> None:
    event = Event(
        event_id="event-1",
        turn=1,
        actor_id="player",
        action_type="look",
        result="accepted",
        visible_to_player=True,
        allow_empty_delta=True,
    )

    assert event.state_delta is None
    assert event.state_deltas == []


def test_event_accepts_multiple_state_deltas() -> None:
    first_delta = make_delta()
    second_delta = StateDelta(operation=StateDeltaOperation.INC, path="turn", value=1)

    event = Event(
        event_id="event-1",
        turn=1,
        actor_id="player",
        action_type="move",
        result="success",
        visible_to_player=True,
        state_deltas=[first_delta, second_delta],
    )

    assert event.state_delta is None
    assert event.state_deltas == [first_delta, second_delta]
