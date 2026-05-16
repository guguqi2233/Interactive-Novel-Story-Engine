from random import Random

from app.core.event_log import EventLog
from app.core.state_delta import apply_delta
from app.core.world_state import GameState, LocationState, LockState, PlayerState, WorldObjectState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.lockpick import LockpickActionHandler
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state(has_tool: bool = True) -> GameState:
    objects = {
        "locked_chest": WorldObjectState(
            id="locked_chest",
            location_id="square",
            locked=True,
            lock_difficulty=4,
            lock_state=LockState.INTACT,
            tags=["container"],
        ),
        "hidden_chest": WorldObjectState(
            id="hidden_chest",
            location_id="square",
            hidden=True,
            locked=True,
            lock_difficulty=3,
            lock_state=LockState.INTACT,
        ),
    }
    if has_tool:
        objects["lockpick_set"] = WorldObjectState(
            id="lockpick_set",
            owner_id="player",
            portable=True,
            tags=["tool:lockpick"],
        )
    return GameState(
        world_id="lockpick-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        objects=objects,
    )


def make_intent(target_id: str | None = "locked_chest") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.LOCKPICK,
        target_id=target_id,
        raw_text="lockpick",
        confidence=0.9,
        requires_clarification=False,
    )


def apply_all(state: GameState, result) -> GameState:
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_lockpick_success_unlocks_target() -> None:
    state = make_state()
    result = LockpickActionHandler().resolve(make_intent(), state, Random(5))
    next_state = apply_all(state, result)

    assert result.success_level == "success"
    assert next_state.objects["locked_chest"].locked is False
    assert next_state.objects["locked_chest"].lock_state == LockState.OPENED


def test_lockpick_partial_success_changes_lock_state_or_fact() -> None:
    state = make_state(has_tool=False)
    result = LockpickActionHandler().resolve(make_intent(), state, Random(9))
    next_state = apply_all(state, result)

    assert result.success_level == "partial_success"
    assert next_state.objects["locked_chest"].lock_state == LockState.SCRATCHED
    assert "locked_chest_lock_scratched" in next_state.facts


def test_lockpick_failure_consumes_time_and_generates_event() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "lockpick",
                "target_id": "locked_chest",
                "raw_text": "lockpick",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            {
                "text": "The lock resists.",
                "suggested_actions": [],
                "short_summary": "Failed lockpick.",
            },
        ]
    )
    state = make_state(has_tool=False)
    state.objects["locked_chest"].lock_difficulty = 10
    game_loop = __import__("app.core.game_loop", fromlist=["GameLoop"]).GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )

    result = game_loop.step("lockpick")

    assert result.event is not None
    assert result.event.action_type == "lockpick"
    assert result.action_result is not None
    assert result.action_result.success_level == "failure"
    assert any(delta.path == "current_time" for delta in result.event.state_deltas)
    assert game_loop.event_log.list_events()


def test_lockpick_invalid_target_returns_invalid() -> None:
    result = LockpickActionHandler().resolve(make_intent("missing"), make_state(), Random(1))

    assert result.success_level == "invalid"
    assert result.state_deltas == []


def test_lockpick_hidden_undiscovered_target_is_invalid() -> None:
    result = LockpickActionHandler().resolve(make_intent("hidden_chest"), make_state(), Random(5))

    assert result.success_level == "invalid"
    assert "hidden_chest" not in str(result.visible_facts)


def test_lockpick_without_tool_is_harder_or_fails() -> None:
    state = make_state(has_tool=False)
    result = LockpickActionHandler().resolve(make_intent(), state, Random(2))

    assert result.success_level == "failure"
    assert result.state_deltas[0].path == "current_time"


def test_lockpick_does_not_leak_hidden_facts() -> None:
    result = LockpickActionHandler().resolve(make_intent("hidden_chest"), make_state(), Random(5))

    assert "secret" not in str(result)
    assert "hidden_facts" not in str(result.visible_facts)


def test_lockpick_fact_enters_facts_by_state_delta() -> None:
    state = make_state(has_tool=False)
    result = LockpickActionHandler().resolve(make_intent(), state, Random(1))

    assert any(delta.path == "facts.locked_chest_lock_scratched" for delta in result.state_deltas)
    next_state = apply_all(state, result)
    assert "locked_chest_lock_scratched" in next_state.facts
