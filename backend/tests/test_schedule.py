from random import Random
from pathlib import Path

import pytest

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import apply_delta
from app.core.world_state import GameState, GameTime, LocationState, NPCScheduleEntry, NPCState, PlayerState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader, WorldLoaderError
from app.engine.rules.schedule import ScheduleRuleError, resolve_npc_schedules
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.session_store import build_visible_state
from app.db.repository import SQLiteSaveRepository


def make_state(minutes_of_day: int = 8 * 60) -> GameState:
    return GameState(
        world_id="schedule-test",
        current_time=GameTime(day=1, minutes_of_day=minutes_of_day),
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Square"),
            "forge": LocationState(id="forge", name="Forge"),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="forge",
                schedule=[
                    NPCScheduleEntry(
                        time_of_day="morning",
                        location_id="forge",
                        activity="working the forge",
                    ),
                    NPCScheduleEntry(
                        time_of_day="evening",
                        location_id="square",
                        activity="watching the square",
                    ),
                ],
            )
        },
    )


def test_morning_npc_stays_at_scheduled_location() -> None:
    state = make_state(minutes_of_day=8 * 60)

    deltas = resolve_npc_schedules(state)

    assert [delta.path for delta in deltas] == ["npcs.harlan.current_activity"]
    next_state = apply_delta(state, deltas[0])
    assert next_state.npcs["harlan"].location_id == "forge"
    assert next_state.npcs["harlan"].current_activity == "working the forge"


def test_evening_npc_moves_to_scheduled_location() -> None:
    state = make_state(minutes_of_day=18 * 60)

    deltas = resolve_npc_schedules(state)
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)

    assert any(delta.path == "npcs.harlan.location_id" for delta in deltas)
    assert next_state.npcs["harlan"].location_id == "square"
    assert next_state.npcs["harlan"].current_activity == "watching the square"


def test_invalid_schedule_location_errors() -> None:
    state = make_state()
    state.npcs["harlan"].schedule[0].location_id = "missing"

    with pytest.raises(ScheduleRuleError, match="missing location_id: missing"):
        resolve_npc_schedules(state)


def test_world_loader_rejects_invalid_schedule_location(tmp_path: Path) -> None:
    world_path = tmp_path / "bad_schedule"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: bad_schedule
name: Bad Schedule
start_location_id: square
""".strip(),
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
""".strip(),
        encoding="utf-8",
    )
    (world_path / "npcs.yaml").write_text(
        """
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Wary.
    schedule:
      - time_of_day: morning
        location_id: missing
        activity: vanishing
""".strip(),
        encoding="utf-8",
    )
    (world_path / "items.yaml").write_text("items: []", encoding="utf-8")
    (world_path / "quests.yaml").write_text("quests: []", encoding="utf-8")

    with pytest.raises(WorldLoaderError, match="schedule references missing location_id: missing"):
        WorldLoader(tmp_path).load("bad_schedule")


def test_schedule_produces_system_event_after_time_advances() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "wait",
                "raw_text": "wait",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            {
                "text": "Time passes.",
                "suggested_actions": [],
                "short_summary": "Waited.",
            },
        ]
    )
    game_loop = GameLoop(
        state=make_state(minutes_of_day=16 * 60 + 45),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )

    result = game_loop.step("wait")
    events = game_loop.event_log.list_events()

    assert result.state.npcs["harlan"].location_id == "square"
    assert result.system_events
    assert events[-1].actor_id == "system"
    assert events[-1].action_type == "world_tick"
    assert any(delta.path == "npcs.harlan.location_id" for delta in events[-1].state_deltas)


def test_loaded_state_schedule_still_resolves(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "schedule_save.db")
    repository.create_save("save-1", make_state(minutes_of_day=18 * 60))

    state = repository.load_save("save-1")

    deltas = resolve_npc_schedules(state)

    assert any(delta.path == "npcs.harlan.location_id" for delta in deltas)


def test_hidden_npc_does_not_leak_to_visible_state() -> None:
    state = make_state()
    state.npcs["harlan"].location_id = "square"
    state.npcs["harlan"].hidden = True

    visible_state = build_visible_state(state)

    assert visible_state.visible_npcs == []
    assert "harlan" not in visible_state.model_dump_json()
