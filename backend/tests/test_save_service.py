from pathlib import Path
from random import Random

from app.core.event_log import Event
from app.core.event_log import EventLog
from app.core.game_loop import GameLoop, GameLoopResult
from app.core.world_state import GameState, LocationState, PlayerState
from app.db.repository import SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.action_dispatcher import ActionDispatcher
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator


def test_save_service_persists_game_loop_step(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "service_save.db")
    service = SaveService(repository)
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "observe",
                "raw_text": "观察",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            {
                "text": "你看见广场。",
                "suggested_actions": ["等待"],
                "short_summary": "玩家观察了广场。",
            },
        ]
    )
    game_loop = GameLoop(
        state=GameState(
            world_id="service-test",
            player=PlayerState(location_id="square"),
            locations={"square": LocationState(id="square", name="Town Square")},
        ),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )

    service.create_save("save-1", game_loop)
    result = game_loop.step("观察")
    service.persist_step("save-1", result)

    assert repository.load_save("save-1").turn == 1
    assert len(repository.list_events("save-1")) == 1


def test_save_service_persists_system_events_from_step_result(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "service_system_events.db")
    service = SaveService(repository)
    state = GameState(
        world_id="service-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
    )
    game_loop = GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(FakeLLMProvider()),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(FakeLLMProvider()),
        rng=Random(1),
    )
    player_event = Event(
        event_id="player-event",
        turn=0,
        actor_id="player",
        action_type="wait",
        result="success",
        allow_empty_delta=True,
        visible_to_player=True,
    )
    system_event = Event(
        event_id="system-event",
        turn=0,
        actor_id="system",
        action_type="world_tick",
        result="success",
        allow_empty_delta=True,
        visible_to_player=False,
    )
    result = GameLoopResult(
        state=state,
        intent=PlayerIntent(
            action_type=PlayerActionType.WAIT,
            raw_text="wait",
            confidence=1.0,
            requires_clarification=False,
        ),
        action_result=None,
        narrative=NarrativeResult(text="Wait.", suggested_actions=[], short_summary="Wait."),
        event=player_event,
        system_events=[system_event],
    )

    service.create_save("save-1", game_loop)
    service.persist_step("save-1", result)

    event_ids = [event.event_id for event in repository.list_events("save-1")]
    assert event_ids == ["player-event", "system-event"]

