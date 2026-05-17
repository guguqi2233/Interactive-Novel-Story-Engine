from random import Random

import pytest

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.schemas import SuccessLevel
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProviderError, Message, SchemaT
from app.llm.schemas import PlayerActionType


def make_state() -> GameState:
    return GameState(
        world_id="loop-test",
        turn=0,
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Town Square", exits={"east": "smithy"}),
            "smithy": LocationState(id="smithy", name="Blacksmith", exits={"west": "square"}),
        },
        objects={"well": WorldObjectState(id="well", location_id="square")},
    )


def make_loop(json_responses: list[dict[str, object]]) -> GameLoop:
    provider = FakeLLMProvider(json_responses=json_responses)
    return GameLoop(
        state=make_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )


def narrative_response(text: str = "Narrated.") -> dict[str, object]:
    return {
        "text": text,
        "suggested_actions": ["observe"],
        "short_summary": "Summary.",
    }


def test_observe_complete_flow() -> None:
    game_loop = make_loop(
        [
            {
                "action_type": "observe",
                "raw_text": "observe",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            narrative_response("You look around."),
        ]
    )

    result = game_loop.step("observe")

    assert result.intent.action_type == PlayerActionType.OBSERVE
    assert result.action_result is not None
    assert result.action_result.success_level == SuccessLevel.SUCCESS
    assert result.state.turn == 1
    assert result.narrative.text == "You look around."


def test_move_complete_flow() -> None:
    game_loop = make_loop(
        [
            {
                "action_type": "move",
                "target_id": "smithy",
                "raw_text": "go east",
                "confidence": 0.95,
                "requires_clarification": False,
            },
            narrative_response("You go to the smithy."),
        ]
    )

    result = game_loop.step("go east")

    assert result.state.player.location_id == "smithy"
    assert result.state.turn == 1
    assert result.event is not None
    assert result.event.action_type == "move"


def test_unknown_does_not_modify_state_but_records_event() -> None:
    game_loop = make_loop(
        [
            {
                "action_type": "unknown",
                "raw_text": "???",
                "confidence": 0.1,
                "requires_clarification": False,
            }
        ]
    )
    before = game_loop.state

    result = game_loop.step("???")

    assert result.state == before
    events = game_loop.event_log.list_events()
    assert len(events) == 1
    assert result.event == events[0]
    assert result.event is not None
    assert result.event.allow_empty_delta is True
    assert result.event.result == "unknown"
    assert result.narrative.text == "I could not understand that action."


def test_clarification_does_not_modify_state_but_records_event() -> None:
    game_loop = make_loop(
        [
            {
                "action_type": "unknown",
                "raw_text": "unclear",
                "confidence": 0.2,
                "requires_clarification": True,
                "clarification_question": "What do you mean?",
            }
        ]
    )
    before = game_loop.state

    result = game_loop.step("unclear")

    assert result.state == before
    events = game_loop.event_log.list_events()
    assert len(events) == 1
    assert result.event == events[0]
    assert result.event is not None
    assert result.event.allow_empty_delta is True
    assert result.event.result == "clarification"
    assert result.narrative.text == "What do you mean?"


def test_event_is_recorded_after_handled_action() -> None:
    game_loop = make_loop(
        [
            {
                "action_type": "observe",
                "raw_text": "observe",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            narrative_response("You observe the square."),
        ]
    )

    result = game_loop.step("observe")
    events = game_loop.event_log.list_events()

    assert len(events) == 1
    assert events[0] == result.event
    assert events[0].input_text == "observe"
    assert events[0].narrative_text == "You observe the square."
    assert len(events[0].state_deltas) == 2
    assert [delta.path for delta in events[0].state_deltas] == ["current_time", "turn"]


def test_narrator_failure_does_not_commit_state_or_event() -> None:
    provider = FailingNarratorProvider(
        json_responses=[
            {
                "action_type": "move",
                "target_id": "smithy",
                "raw_text": "go east",
                "confidence": 0.95,
                "requires_clarification": False,
            }
        ]
    )
    game_loop = GameLoop(
        state=make_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )

    before = game_loop.state

    with pytest.raises(LLMProviderError):
        game_loop.step("go east")

    assert game_loop.state == before
    assert game_loop.event_log.list_events() == []


class FailingNarratorProvider(FakeLLMProvider):
    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        if schema.__name__ == "NarrativeResult":
            raise LLMProviderError("Narrator failed")
        return super().generate_json(messages, schema, temperature)
