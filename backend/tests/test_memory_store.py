from pathlib import Path

from app.core.world_state import GameState
from app.db.repository import SQLiteSaveRepository
from app.llm.memory_store import (
    InMemoryMemoryStore,
    MemoryQuery,
    MemoryRecord,
    MemoryVisibility,
    filter_narrator_safe_memories,
    filter_player_visible_memories,
)


def make_record(
    memory_id: str,
    content: str,
    *,
    tags: list[str] | None = None,
    entity_ids: list[str] | None = None,
    fact_ids: list[str] | None = None,
    visibility: MemoryVisibility = MemoryVisibility.NARRATOR_SAFE,
    importance: int = 0,
    created_turn: int = 1,
) -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        content=content,
        tags=tags or [],
        entity_ids=entity_ids or [],
        fact_ids=fact_ids or [],
        visibility=visibility,
        importance=importance,
        created_turn=created_turn,
    )


def test_add_memory_and_search_by_tag() -> None:
    store = InMemoryMemoryStore()
    record = make_record("memory-1", "The player found a brass key.", tags=["item", "key"])

    store.add_memory(record)

    assert store.search_by_tags(["key"]) == [record]


def test_search_by_entity_and_fact() -> None:
    store = InMemoryMemoryStore()
    record = make_record(
        "memory-1",
        "Harlan mentioned the old well.",
        entity_ids=["npc:harlan"],
        fact_ids=["fact:old_well"],
    )
    store.add_memory(record)

    assert store.search_by_entity("npc:harlan") == [record]
    assert store.search_by_fact("fact:old_well") == [record]


def test_search_by_substring_and_turn_range_is_deterministic() -> None:
    store = InMemoryMemoryStore()
    old = make_record("memory-old", "Gate rumor", created_turn=1, importance=1)
    new = make_record("memory-new", "Gate clue", created_turn=5, importance=1)
    important = make_record("memory-important", "Gate warning", created_turn=2, importance=5)

    store.add_memory(old)
    store.add_memory(new)
    store.add_memory(important)

    results = store.search_memory(MemoryQuery(substring="gate", turn_from=1, turn_to=5))

    assert results == [important, new, old]


def test_hidden_memory_is_not_narrator_context() -> None:
    hidden = make_record(
        "memory-hidden",
        "The hidden faction ordered the theft.",
        visibility=MemoryVisibility.HIDDEN,
    )
    debug = make_record(
        "memory-debug",
        "Debug-only state delta details.",
        visibility=MemoryVisibility.DEBUG_ONLY,
    )
    safe = make_record(
        "memory-safe",
        "The player noticed fresh footprints.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )

    assert filter_narrator_safe_memories([hidden, debug, safe]) == [safe]


def test_debug_only_memory_is_not_player_response() -> None:
    debug = make_record(
        "memory-debug",
        "Debug-only consequence chain.",
        visibility=MemoryVisibility.DEBUG_ONLY,
    )
    player_visible = make_record(
        "memory-player",
        "The village now speaks of the broken lock.",
        visibility=MemoryVisibility.PLAYER_VISIBLE,
    )

    assert filter_player_visible_memories([debug, player_visible]) == [player_visible]


def test_memory_store_save_load_round_trip(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "memory.db")
    state = GameState(world_id="memory-test")
    first = make_record(
        "memory-1",
        "The player helped the blacksmith.",
        tags=["quest"],
        entity_ids=["npc:blacksmith"],
        created_turn=2,
    )
    second = make_record(
        "memory-2",
        "Hidden investigation note.",
        visibility=MemoryVisibility.DEBUG_ONLY,
        created_turn=3,
    )

    repository.save_snapshot("save-1", state, [], memories=[first, second])

    loaded = repository.list_memories("save-1")

    assert loaded == [second, first]


def test_repository_can_replace_memories_without_touching_state(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "memory.db")
    state = GameState(world_id="memory-test", turn=4)
    repository.create_save("save-1", state)

    repository.save_memories("save-1", [make_record("memory-1", "first")])
    repository.save_memories("save-1", [make_record("memory-2", "second")])

    assert [memory.id for memory in repository.list_memories("save-1")] == ["memory-2"]
    assert repository.load_save("save-1").turn == 4
