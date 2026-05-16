from pathlib import Path
from random import Random

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import GameState, LocationState, PlayerState
from app.db.repository import SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.action_dispatcher import ActionDispatcher
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

