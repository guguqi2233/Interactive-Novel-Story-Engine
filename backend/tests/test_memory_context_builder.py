from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.context_builder import MemoryContextBuilder
from app.llm.memory_store import InMemoryMemoryStore, MemoryRecord, MemoryVisibility


def make_state() -> GameState:
    return GameState(
        world_id="memory-context-test",
        locations={
            "square": LocationState(
                id="square",
                name="Square",
                description="A test square.",
            )
        },
        facts={
            "public_fact": FactState(
                id="public_fact",
                text="The square is public.",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="A hidden witness saw everything.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
            "discoverable_fact": FactState(
                id="discoverable_fact",
                text="A loose stone hides a note.",
                visibility=FactVisibility.DISCOVERABLE,
            ),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                mood="neutral",
                relationship_to_player=0,
                knowledge=["public_fact"],
            )
        },
        player_visible_facts={"public_fact"},
    )


def make_result() -> ActionResult:
    return ActionResult(
        success_level=SuccessLevel.SUCCESS,
        reason="Observed safely.",
        visible_facts=["public_fact"],
    )


def memory(
    memory_id: str,
    content: str,
    *,
    visibility: MemoryVisibility = MemoryVisibility.NARRATOR_SAFE,
    entity_ids: list[str] | None = None,
    fact_ids: list[str] | None = None,
    tags: list[str] | None = None,
    importance: int = 0,
    created_turn: int = 1,
) -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        content=content,
        visibility=visibility,
        entity_ids=entity_ids or [],
        fact_ids=fact_ids or [],
        tags=tags or [],
        importance=importance,
        created_turn=created_turn,
    )


def test_player_visible_memory_enters_narrator_context() -> None:
    state = make_state()
    record = memory(
        "memory-player",
        "The player saw the public notice.",
        visibility=MemoryVisibility.PLAYER_VISIBLE,
        fact_ids=["public_fact"],
    )
    builder = MemoryContextBuilder(InMemoryMemoryStore([record]))

    context = builder.build(state, "player", "square", make_result(), ["public_fact"])

    assert context.narrator_safe_memories == [record]
    assert context.player_visible_memories == [record]


def test_hidden_and_debug_memory_are_filtered_from_narrator() -> None:
    state = make_state()
    hidden = memory("memory-hidden", "Hidden note.", visibility=MemoryVisibility.HIDDEN)
    debug = memory("memory-debug", "Debug delta.", visibility=MemoryVisibility.DEBUG_ONLY)
    builder = MemoryContextBuilder(InMemoryMemoryStore([hidden, debug]))

    context = builder.build(state, "player", "square", make_result(), ["public_fact"])

    assert context.narrator_safe_memories == []
    assert {reason.memory_id for reason in context.excluded_memory_reasons} == {
        "memory-hidden",
        "memory-debug",
    }


def test_npc_unknown_memory_does_not_enter_npc_context() -> None:
    state = make_state()
    unknown = memory(
        "memory-unknown",
        "The hidden witness is afraid.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
        fact_ids=["hidden_fact"],
    )
    known = memory(
        "memory-known",
        "Harlan knows the square is public.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
        fact_ids=["public_fact"],
    )
    builder = MemoryContextBuilder(InMemoryMemoryStore([unknown, known]))

    context = builder.build(
        state,
        "player",
        "square",
        make_result(),
        ["public_fact"],
        current_npc_id="harlan",
    )

    assert context.npc_known_memories == [known]
    assert any(
        reason.memory_id == "memory-unknown" and "npc_unknown_fact" in reason.reason
        for reason in context.excluded_memory_reasons
    )


def test_location_related_memory_is_prioritized() -> None:
    state = make_state()
    location_memory = memory(
        "memory-location",
        "The square bell rang.",
        entity_ids=["location:square"],
        importance=1,
    )
    generic_memory = memory("memory-generic", "A very important old event.", importance=9)
    builder = MemoryContextBuilder(InMemoryMemoryStore([generic_memory, location_memory]))

    context = builder.build(state, "player", "square", make_result(), ["public_fact"])

    assert context.narrator_safe_memories[:2] == [location_memory, generic_memory]


def test_fact_related_memory_is_retrieved() -> None:
    state = make_state()
    record = memory(
        "memory-fact",
        "The public fact mattered yesterday.",
        fact_ids=["public_fact"],
    )
    builder = MemoryContextBuilder(InMemoryMemoryStore([record]))

    context = builder.build(state, "player", "square", make_result(), ["public_fact"])

    assert context.narrator_safe_memories == [record]


def test_context_builder_does_not_modify_game_state() -> None:
    state = make_state()
    before = state.model_dump_json()
    builder = MemoryContextBuilder(
        InMemoryMemoryStore(
            [
                memory(
                    "memory-hidden",
                    "Hidden thing.",
                    visibility=MemoryVisibility.HIDDEN,
                    fact_ids=["hidden_fact"],
                )
            ]
        )
    )

    builder.build(state, "player", "square", make_result(), ["public_fact"])

    assert state.model_dump_json() == before
