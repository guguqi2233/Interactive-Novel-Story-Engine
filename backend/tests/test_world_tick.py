from random import Random
from pathlib import Path

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    GameTime,
    LocationState,
    NPCScheduleEntry,
    NPCState,
    PlayerState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestTrigger,
    QuestTriggerAction,
    QuestTriggerType,
    QuestVisibility,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.world_tick import run_world_tick
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.session_store import build_visible_state


def make_tick_state(minutes_of_day: int = 16 * 60 + 45) -> GameState:
    return GameState(
        world_id="tick-test",
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
                suspicion=2,
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


def make_loop(state: GameState) -> GameLoop:
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
    return GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )


def test_wait_runs_schedule_tick_and_moves_npc() -> None:
    game_loop = make_loop(make_tick_state())

    result = game_loop.step("wait")

    assert result.state.npcs["harlan"].location_id == "square"
    assert result.system_events
    assert result.system_events[0].action_type == "world_tick"
    assert any(
        delta.path == "npcs.harlan.location_id"
        for delta in result.system_events[0].state_deltas
    )


def test_world_tick_decays_npc_suspicion() -> None:
    state = make_tick_state(minutes_of_day=8 * 60)

    tick_result = run_world_tick(state, Random(1))
    next_state = state
    for delta in tick_result.state_deltas:
        next_state = apply_delta(next_state, delta)

    assert next_state.npcs["harlan"].suspicion == 1
    assert any(delta.path == "npcs.harlan.suspicion" for delta in tick_result.state_deltas)


def test_hidden_npc_tick_does_not_leak_to_visible_state() -> None:
    state = make_tick_state(minutes_of_day=18 * 60)
    state.npcs["harlan"].hidden = True

    tick_result = run_world_tick(state, Random(1))
    next_state = state
    for delta in tick_result.state_deltas:
        next_state = apply_delta(next_state, delta)
    visible_state = build_visible_state(next_state)

    assert visible_state.visible_npcs == []
    assert "harlan" not in visible_state.model_dump_json()


def test_tick_delayed_fact_can_advance_quest_trigger() -> None:
    state = make_tick_state(minutes_of_day=10 * 60)
    state.quests["hidden_letter"] = QuestState(
        id="hidden_letter",
        title="Hidden Letter",
        initial_stage="find",
        current_stage="find",
        visibility=QuestVisibility.HIDDEN,
        status=QuestStatus.INACTIVE,
        known_to_player=False,
        stages={
            "find": QuestStage(
                id="find",
                title="Find the letter",
                objectives=["discover_letter"],
            )
        },
        triggers=[
            QuestTrigger(
                type=QuestTriggerType.FACT_DISCOVERED,
                id="letter_fact",
                action=QuestTriggerAction.COMPLETE_OBJECTIVE,
                objective_id="discover_letter",
            )
        ],
    )
    state.delayed_consequences = [
        {
            "id": "letter-revealed",
            "due_day": 1,
            "due_minutes_of_day": 9 * 60,
            "state_deltas": [
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path="player_visible_facts",
                    value="letter_fact",
                    metadata={"visible_to_player": "true"},
                ).model_dump(mode="json")
            ],
        }
    ]

    tick_result = run_world_tick(state, Random(1))
    next_state = state
    for delta in tick_result.state_deltas:
        next_state = apply_delta(next_state, delta)

    assert "letter_fact" in next_state.player_visible_facts
    assert next_state.quests["hidden_letter"].status == QuestStatus.ACTIVE
    assert "discover_letter" in next_state.quests["hidden_letter"].completed_objectives
    assert tick_result.event is not None
    assert tick_result.event.visible_to_player is True


def test_delayed_consequence_resolves_and_is_removed() -> None:
    state = make_tick_state(minutes_of_day=10 * 60)
    state.delayed_consequences = [
        {
            "id": "lower-suspicion",
            "due_day": 1,
            "due_minutes_of_day": 9 * 60,
            "state_deltas": [
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="npcs.harlan.suspicion",
                    value=0,
                ).model_dump(mode="json")
            ],
        }
    ]

    tick_result = run_world_tick(state, Random(1))
    next_state = state
    for delta in tick_result.state_deltas:
        next_state = apply_delta(next_state, delta)

    assert next_state.npcs["harlan"].suspicion == 0
    assert next_state.delayed_consequences == []


def test_loaded_state_tick_still_runs(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(Path(tmp_path) / "tick_save.db")
    repository.create_save("save-tick", make_tick_state(minutes_of_day=18 * 60))
    loaded = repository.load_save("save-tick")

    tick_result = run_world_tick(loaded, Random(1))

    assert any(delta.path == "npcs.harlan.location_id" for delta in tick_result.state_deltas)
