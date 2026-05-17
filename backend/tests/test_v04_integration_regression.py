from pathlib import Path
from random import Random

from app.core.event_log import Event, EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    ActorCondition,
    GameState,
    LocationState,
    NPCState,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.life_state import can_talk
from app.engine.rules.rumors import propagate_rumors
from app.engine.rules.schedule import resolve_npc_schedules
from app.engine.rules.world_tick import run_world_tick
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.memory_store import (
    InMemoryMemoryStore,
    MemoryRecord,
    MemoryVisibility,
    filter_narrator_safe_memories,
)
from app.llm.narrator import Narrator
from app.session_store import build_visible_state


def make_loop(state: GameState, json_responses: list[dict[str, object]]) -> GameLoop:
    provider = FakeLLMProvider(json_responses=json_responses)
    return GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )


def intent_response(action_type: str, target_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "action_type": action_type,
        "raw_text": action_type if target_id is None else f"{action_type} {target_id}",
        "confidence": 1.0,
        "requires_clarification": False,
    }
    if target_id is not None:
        payload["target_id"] = target_id
    return payload


def narrative_response(text: str = "Resolved.") -> dict[str, object]:
    return {"text": text, "suggested_actions": [], "short_summary": text}


def make_mist_valley_state() -> GameState:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.objects["council_chest"] = WorldObjectState(
        id="council_chest",
        name="Council Chest",
        description="A locked chest near the notice board.",
        location_id=state.player.location_id,
        portable=False,
        visible=True,
        locked=True,
        lock_difficulty=99,
    )
    state.npcs["hidden_watcher"] = NPCState(
        id="hidden_watcher",
        location_id=state.player.location_id,
        faction_id="village_council",
        hidden=True,
        discovered_by=[],
        alertness=4,
        schedule=[
            {"time_of_day": "morning", "location_id": state.player.location_id, "activity": "watching"}
        ],
    )
    state.npcs["harlan"].location_id = state.player.location_id
    state.npcs["harlan"].alertness = 4
    return state


def apply_deltas(state: GameState, deltas: list[StateDelta]) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def replay_events(initial_state: GameState, events: list[Event]) -> GameState:
    state = initial_state
    for event in events:
        assert event.state_deltas or event.allow_empty_delta
        state = apply_deltas(state, event.state_deltas)
    return state


def test_v04_social_consequence_flow_from_mist_valley() -> None:
    state = make_mist_valley_state()
    loop = make_loop(
        state,
        [
            intent_response("lockpick", "council_chest"),
            narrative_response("The lock resists with an ugly scrape."),
            intent_response("wait"),
            narrative_response("Time passes."),
        ],
    )

    first = loop.step("lockpick council_chest")
    assert first.event is not None
    assert first.event.action_type == "lockpick"
    assert loop.state.witnesses
    assert any(witness.npc_id == "hidden_watcher" for witness in loop.state.witnesses.values())
    assert loop.state.crimes
    crime = next(iter(loop.state.crimes.values()))
    assert crime.status == "reported"
    assert loop.state.rumors
    assert loop.state.factions["village_council"].reputation.value < 0
    assert loop.state.npcs["harlan"].goals or loop.state.npcs["harlan"].suspicion >= 0

    loop.step("wait")
    assert any("harlan" in rumor.known_by_npcs for rumor in loop.state.rumors.values())

    visible_state = build_visible_state(loop.state)
    visible_payload = visible_state.model_dump_json()
    assert visible_state.known_crimes
    assert all(faction.id != "old_road_smugglers" for faction in visible_state.factions)
    assert "hidden_watcher" not in visible_payload
    assert "mayor_hides_missing_tools" not in visible_payload
    assert all(event.state_deltas or event.allow_empty_delta for event in loop.event_log.list_events())
    assert any(event.actor_id == "system" for event in loop.event_log.list_events())


def test_v04_combat_life_save_load_and_dead_actor_boundaries(tmp_path: Path) -> None:
    state = make_mist_valley_state()
    state.npcs["harlan"].hp = 3
    state.npcs["harlan"].max_hp = 10
    loop = make_loop(
        state,
        [
            intent_response("attack", "harlan"),
            narrative_response("The blow lands."),
        ],
    )

    result = loop.step("attack harlan")
    assert result.event is not None
    assert result.event.action_type == "attack"
    assert any(delta.path == "npcs.harlan.hp" for delta in result.event.state_deltas)
    assert loop.state.npcs["harlan"].hp == 0
    assert loop.state.npcs["harlan"].condition in {
        ActorCondition.INCAPACITATED,
        ActorCondition.DEAD,
    }
    assert loop.state.crimes
    assert next(iter(loop.state.crimes.values())).crime_type in {"assault", "murder"}

    if loop.state.npcs["harlan"].condition != ActorCondition.DEAD:
        loop.state = apply_delta(
            loop.state,
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.harlan.condition",
                value=ActorCondition.DEAD,
            ),
        )
        loop.state = apply_delta(
            loop.state,
            StateDelta(operation=StateDeltaOperation.SET, path="npcs.harlan.alive", value=False),
        )

    assert can_talk(loop.state, "harlan") is False
    assert resolve_npc_schedules(loop.state) == []
    assert propagate_rumors(loop.state) == []

    repository = SQLiteSaveRepository(tmp_path / "v04_combat.db")
    repository.save_snapshot("save-1", loop.state, loop.event_log.list_events())
    loaded_state = repository.load_save("save-1")
    loaded_events = repository.list_events("save-1")

    assert loaded_state.combats == loop.state.combats
    assert loaded_state.npcs["harlan"].hp == 0
    assert loaded_state.crimes == loop.state.crimes
    assert [event.model_dump(mode="json") for event in loaded_events] == [
        event.model_dump(mode="json") for event in loop.event_log.list_events()
    ]


def test_v04_memory_retrieval_is_safe_and_non_authoritative(tmp_path: Path) -> None:
    state = make_mist_valley_state()
    before_state_json = state.model_dump_json()
    store = InMemoryMemoryStore()
    safe = MemoryRecord(
        id="memory-safe",
        content="Harlan discussed the old bridge clue.",
        source_event_ids=["event-1"],
        tags=["quest", "bridge"],
        entity_ids=["harlan"],
        fact_ids=["old_bridge_creaks_at_midnight"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
        importance=3,
        created_turn=2,
    )
    hidden = MemoryRecord(
        id="memory-hidden",
        content="Debug note about an unseen witness.",
        tags=["debug"],
        entity_ids=["hidden_watcher"],
        visibility=MemoryVisibility.DEBUG_ONLY,
        created_turn=3,
    )

    store.add_memory(safe)
    store.add_memory(hidden)

    assert store.search_by_tags(["bridge"]) == [safe]
    assert store.search_by_entity("harlan") == [safe]
    assert store.search_by_fact("old_bridge_creaks_at_midnight") == [safe]
    assert filter_narrator_safe_memories(store.list_recent_memories()) == [safe]
    assert state.model_dump_json() == before_state_json

    repository = SQLiteSaveRepository(tmp_path / "v04_memory.db")
    repository.save_snapshot("save-1", state, [], memories=store.list_all())
    loaded_memories = repository.list_memories("save-1")
    assert {memory.id for memory in loaded_memories} == {"memory-safe", "memory-hidden"}
    assert repository.load_save("save-1").model_dump(mode="json") == state.model_dump(mode="json")


def test_v04_save_load_tick_and_replay_preserve_social_state(tmp_path: Path) -> None:
    initial_state = make_mist_valley_state()
    loop = make_loop(
        initial_state.model_copy(deep=True),
        [
            intent_response("lockpick", "council_chest"),
            narrative_response("The lock is damaged."),
            intent_response("wait"),
            narrative_response("A little time passes."),
        ],
    )
    loop.step("lockpick council_chest")
    loop.step("wait")
    repository = SQLiteSaveRepository(Path(tmp_path) / "v04_social.db")
    repository.save_snapshot("save-1", loop.state, loop.event_log.list_events())

    loaded_state = repository.load_save("save-1")
    loaded_events = repository.list_events("save-1")
    tick = run_world_tick(loaded_state, Random(0))
    continued_state = apply_deltas(loaded_state, tick.state_deltas)
    replayed_state = replay_events(initial_state, loaded_events)

    assert loaded_state.crimes == loop.state.crimes
    assert loaded_state.rumors == loop.state.rumors
    assert loaded_state.factions == loop.state.factions
    assert loaded_state.combats == loop.state.combats
    assert continued_state.turn == loaded_state.turn
    assert replayed_state.crimes == loop.state.crimes
    assert replayed_state.rumors == loop.state.rumors
    assert replayed_state.factions == loop.state.factions
    assert "hidden_watcher" not in build_visible_state(loaded_state).model_dump_json()
