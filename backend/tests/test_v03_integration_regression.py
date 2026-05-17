from pathlib import Path
from random import Random
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event, EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    LockState,
    NPCScheduleEntry,
    NPCState,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.schemas import ActionResult
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.inventory import pick_up_item
from app.engine.rules.quests import resolve_quest_triggers
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.memory_summarizer import MemorySummarizer
from app.llm.narrator import Narrator
from app.llm.provider_base import Message
from app.llm.schemas import MemorySummary, NarrativeResult, PlayerActionType, PlayerIntent
from app.main import app
from app.session_store import build_visible_state


class SpyNarrator(Narrator):
    def __init__(self) -> None:
        self.visible_fact_calls: list[list[str]] = []

    def render(
        self,
        player_input: str,
        action_result: ActionResult,
        visible_facts: list[str],
        current_location: str,
        tone: str,
    ) -> NarrativeResult:
        self.visible_fact_calls.append(list(visible_facts))
        return NarrativeResult(
            text=f"Rendered {player_input}",
            suggested_actions=[],
            short_summary=f"{action_result.success_level.value}:{current_location}",
        )


def test_v03_full_system_regression_flow(tmp_path: Path) -> None:
    initial_state = _enhanced_mist_valley_state()
    event_log = EventLog()
    spy_narrator = SpyNarrator()
    game_loop = GameLoop(
        state=initial_state,
        event_log=event_log,
        intent_parser=IntentParser(_intent_provider()),
        action_dispatcher=ActionDispatcher(),
        narrator=spy_narrator,
        rng=Random(1),
    )

    observe = game_loop.step("observe")
    search = game_loop.step("search")
    _apply_pickup_player_action(game_loop, "sealed_letter")
    move = game_loop.step("smithy")
    wait = game_loop.step("wait until evening")
    lockpick = game_loop.step("lockpick cache")
    sneak = game_loop.step("sneak square")
    talk = game_loop.step("talk harlan")

    assert observe.event is not None and observe.event.action_type == "observe"
    assert search.event is not None and search.event.action_type == "search"
    assert "player" in game_loop.state.objects["sealed_letter"].discovered_by
    assert game_loop.state.objects["sealed_letter"].owner_id == "player"
    assert move.event is not None and game_loop.state.locations[move.state.player.location_id].id == "blacksmith"
    assert wait.system_events
    assert game_loop.state.npcs["harlan"].location_id == "village_square"
    assert lockpick.action_result is not None
    assert game_loop.state.objects["locked_cache"].locked is False
    assert sneak.event is not None and sneak.event.action_type == "sneak"
    assert talk.event is not None and talk.event.action_type == "talk"
    assert "take_letter" in game_loop.state.quests["sealed_letter"].completed_objectives
    assert "talk_to_harlan" in game_loop.state.quests["missing_tools"].completed_objectives
    assert game_loop.state.quests["missing_tools"].current_stage == "follow_bridge_clue"

    visible_state = build_visible_state(game_loop.state)
    visible_dump = visible_state.model_dump_json()
    assert "sealed_letter_under_stone" not in visible_dump
    assert "hidden_watcher" not in visible_dump
    assert "mayor_hides_missing_tools" not in visible_dump
    assert any(item.id == "sealed_letter" for item in visible_state.inventory)

    narrator_payload = str(spy_narrator.visible_fact_calls)
    assert "sealed_letter_under_stone" not in narrator_payload
    assert "mayor_hides_missing_tools" not in narrator_payload
    assert "hidden_watcher" not in narrator_payload

    for event in event_log.list_events():
        assert event.state_deltas
        assert all(isinstance(delta, StateDelta) for delta in event.state_deltas)

    repository = SQLiteSaveRepository(tmp_path / "v03_regression.db")
    repository.save_snapshot("v03-save", game_loop.state, event_log.list_events())
    loaded_state = repository.load_save("v03-save")
    loaded_events = repository.list_events("v03-save")
    assert loaded_state == game_loop.state
    assert len(loaded_events) == len(event_log.list_events())

    replay_state = _replay_events(_enhanced_mist_valley_state(), loaded_events)
    assert replay_state == loaded_state

    restored_loop = GameLoop(
        state=loaded_state,
        event_log=EventLog(loaded_events),
        intent_parser=IntentParser(_single_intent_provider("observe")),
        action_dispatcher=ActionDispatcher(),
        narrator=SpyNarrator(),
        rng=Random(1),
    )
    previous_turn = restored_loop.state.turn
    continued = restored_loop.step("observe")
    assert continued.state.turn == previous_turn + 1
    assert len(restored_loop.event_log.list_events()) >= len(loaded_events) + 1
    assert restored_loop.event_log.get_latest(1)[0].turn == continued.state.turn

    app.state.save_repository = repository
    app.state.settings = Settings(enable_debug_api=True)
    timeline_response = TestClient(app).get("/debug/saves/v03-save/events")
    assert timeline_response.status_code == 200
    timeline_events = timeline_response.json()["events"]
    assert [event["turn"] for event in timeline_events] == sorted(
        event["turn"] for event in timeline_events
    )
    assert any(event["action_type"] == "world_tick" for event in timeline_events)


def test_v03_llm_boundaries_and_memory_summary_do_not_mutate_state() -> None:
    state = _enhanced_mist_valley_state()
    events = [
        Event(
            event_id="event-1",
            turn=1,
            actor_id="player",
            action_type="observe",
            result="success",
            visible_to_player=True,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path="turn",
                    value=1,
                )
            ],
        )
    ]
    before = state.model_copy(deep=True)
    provider = FakeLLMProvider(
        json_responses=[
            {
                "summary": "The player observed the square.",
                "important_facts": ["village_square_is_misty"],
                "open_threads": [],
                "npc_relationship_changes": [],
            }
        ]
    )

    summary = MemorySummarizer(provider).summarize_recent(events, limit=1)

    assert summary == MemorySummary(
        summary="The player observed the square.",
        important_facts=["village_square_is_misty"],
        open_threads=[],
        npc_relationship_changes=[],
    )
    assert state == before


def _enhanced_mist_valley_state() -> GameState:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"].secrets.append("mayor_hides_missing_tools")
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="objects.lockpick_tool",
            value=WorldObjectState(
                id="lockpick_tool",
                name="Lockpick Tool",
                owner_id="player",
                portable=True,
                tags=["tool:lockpick"],
            ),
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="objects.locked_cache",
            value=WorldObjectState(
                id="locked_cache",
                name="Locked Cache",
                location_id="blacksmith",
                portable=False,
                locked=True,
                lock_difficulty=3,
                lock_state=LockState.INTACT,
            ),
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="npcs.hidden_watcher",
            value=NPCState(
                id="hidden_watcher",
                location_id="blacksmith",
                hidden=True,
                discovered_by=[],
                schedule=[
                    NPCScheduleEntry(
                        time_of_day="evening",
                        location_id="village_square",
                        activity="watching unseen",
                    )
                ],
            ),
        ),
    ]
    for delta in deltas:
        state = apply_delta(state, delta)
    return state


def _intent_provider() -> FakeLLMProvider:
    return FakeLLMProvider(
        json_responses=[
            _intent_payload("observe"),
            _intent_payload("search"),
            _intent_payload("move", target_id="blacksmith"),
            _intent_payload("wait", minutes=570),
            _intent_payload("lockpick", target_id="locked_cache"),
            _intent_payload("sneak", target_id="village_square"),
            _intent_payload("talk", target_id="harlan"),
        ]
    )


def _single_intent_provider(action_type: str) -> FakeLLMProvider:
    return FakeLLMProvider(json_responses=[_intent_payload(action_type)])


def _intent_payload(
    action_type: str,
    target_id: str | None = None,
    minutes: int | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "action_type": action_type,
        "raw_text": action_type,
        "confidence": 1.0,
        "requires_clarification": False,
    }
    if target_id is not None:
        payload["target_id"] = target_id
    if minutes is not None:
        payload["minutes"] = minutes
    return payload


def _apply_pickup_player_action(game_loop: GameLoop, item_id: str) -> None:
    before_state = game_loop.state
    pickup_deltas = pick_up_item(before_state, before_state.player.id, item_id)
    after_pickup = before_state
    for delta in pickup_deltas:
        after_pickup = apply_delta(after_pickup, delta)

    intent = PlayerIntent(
        action_type=PlayerActionType.USE_ITEM,
        target_id=item_id,
        raw_text=f"pick up {item_id}",
        confidence=1.0,
        requires_clarification=False,
    )
    action_result = ActionResult(
        success_level="success",
        reason="Picked up item through inventory rule.",
        state_deltas=pickup_deltas,
        visible_facts=[item_id],
    )
    quest_deltas = resolve_quest_triggers(before_state, after_pickup, intent, action_result)
    next_state = after_pickup
    for delta in quest_deltas:
        next_state = apply_delta(next_state, delta)
    turn_delta = StateDelta(
        operation=StateDeltaOperation.INC,
        path="turn",
        value=1,
        reason="Inventory player action advances the game turn.",
    )
    next_state = apply_delta(next_state, turn_delta)
    event = Event(
        event_id=str(uuid4()),
        turn=next_state.turn,
        actor_id=next_state.player.id,
        action_type="pick_up",
        target_id=item_id,
        input_text=f"pick up {item_id}",
        result="success",
        state_deltas=[*pickup_deltas, *quest_deltas, turn_delta],
        visible_to_player=True,
        narrative_text="Picked up item.",
    )
    game_loop.state = next_state
    game_loop.event_log.append(event)


def _replay_events(initial_state: GameState, events: list[Event]) -> GameState:
    state = initial_state
    for event in events:
        for delta in event.state_deltas:
            state = apply_delta(state, delta)
    return state
