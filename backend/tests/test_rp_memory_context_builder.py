from copy import deepcopy

from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    RelationshipState,
)
from app.engine.rules.relationship_tone import get_tone_for_dialogue
from app.llm.context_builder import RPMemoryContextBuilder
from app.llm.memory_store import InMemoryMemoryStore, MemoryRecord, MemoryVisibility
from app.roleplay.dialogue import DialogueManager, DialogueMode, DialogueSession


def make_state() -> GameState:
    return GameState(
        world_id="rp-memory-test",
        turn=10,
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public_fact"},
        facts={
            "public_fact": FactState(
                id="public_fact",
                text="The square bell is public.",
                visibility=FactVisibility.PUBLIC,
                public=True,
                known_by={"player", "mira"},
            ),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="Mira hides a debt.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
                known_by={"mira"},
            ),
        },
        npcs={
            "mira": NPCState(
                id="mira",
                location_id="square",
                visible=True,
                knowledge=["public_fact"],
            )
        },
        relationships={
            "mira_player_friend": RelationshipState(
                id="mira_player_friend",
                source_id="mira",
                target_id="player",
                relation_type="friend",
                trust=25,
                affinity=20,
                known_by_player=True,
            )
        },
    )


def memory(
    memory_id: str,
    content: str,
    *,
    visibility: MemoryVisibility = MemoryVisibility.NARRATOR_SAFE,
    fact_ids: list[str] | None = None,
    entity_ids: list[str] | None = None,
    tags: list[str] | None = None,
    created_turn: int = 9,
    importance: int = 1,
) -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        content=content,
        visibility=visibility,
        fact_ids=fact_ids or [],
        entity_ids=entity_ids or [],
        tags=tags or [],
        created_turn=created_turn,
        importance=importance,
    )


def session() -> DialogueSession:
    return DialogueSession(
        session_id="dialogue-1",
        participant_ids=["player", "mira"],
        focus_npc_id="mira",
        started_turn=10,
        last_turn=10,
        dialogue_mode=DialogueMode.CASUAL,
        active_topics=["apology"],
    )


def build_context(store: InMemoryMemoryStore, state: GameState | None = None):
    state = state or make_state()
    return RPMemoryContextBuilder(store, include_debug_reasons=True).build(
        state=state,
        dialogue_session=session(),
        speaker_npc_id="mira",
        player_id="player",
        location_id="square",
        visible_facts=list(state.player_visible_facts),
        npc_known_facts=["public_fact"],
        relationship_tone=get_tone_for_dialogue(state, "mira", "player"),
        emotional_state=state.npcs["mira"].emotional_state,
    )


def test_relationship_memory_enters_safe_context() -> None:
    record = memory(
        "memory-relationship",
        "Mira remembers the player's apology.",
        entity_ids=["relationship:mira:player"],
        tags=["relationship", "topic:apology"],
        fact_ids=["public_fact"],
    )

    context = build_context(InMemoryMemoryStore([record]))

    assert context.speaker_safe_memories == [record]
    assert context.relationship_memories == [record]


def test_hidden_and_debug_memory_are_filtered() -> None:
    hidden = memory("memory-hidden", "Secret.", visibility=MemoryVisibility.HIDDEN)
    debug = memory("memory-debug", "Raw debug delta.", visibility=MemoryVisibility.DEBUG_ONLY)

    context = build_context(InMemoryMemoryStore([hidden, debug]))

    assert context.speaker_safe_memories == []
    assert {reason.memory_id for reason in context.excluded_memory_reasons} == {
        "memory-hidden",
        "memory-debug",
    }


def test_npc_unknown_memory_is_filtered() -> None:
    state = make_state()
    state.facts["known_to_player_only"] = FactState(
        id="known_to_player_only",
        text="The player saw a blue ribbon.",
        visibility=FactVisibility.DISCOVERABLE,
        known_by={"player"},
    )
    state.player_visible_facts.add("known_to_player_only")
    unknown = memory(
        "memory-npc-unknown",
        "The player saw a blue ribbon.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
        fact_ids=["known_to_player_only"],
    )

    context = build_context(InMemoryMemoryStore([unknown]), state)

    assert context.speaker_safe_memories == []
    assert any("rp_npc_unknown_fact" in reason.reason for reason in context.excluded_memory_reasons)


def test_memory_does_not_override_authoritative_gamestate_fact() -> None:
    record = memory(
        "memory-conflict",
        "Memory claims the public bell is gone.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
        fact_ids=["public_fact"],
    )
    state = make_state()
    before = deepcopy(state.model_dump(mode="json"))

    context = build_context(InMemoryMemoryStore([record]), state)

    assert context.speaker_safe_memories == [record]
    assert state.model_dump(mode="json") == before
    assert state.facts["public_fact"].text == "The square bell is public."


def test_excluded_reasons_are_debug_only_by_default() -> None:
    hidden = memory("memory-hidden", "Secret.", visibility=MemoryVisibility.HIDDEN)
    state = make_state()
    default_context = RPMemoryContextBuilder(InMemoryMemoryStore([hidden])).build(
        state=state,
        dialogue_session=session(),
        speaker_npc_id="mira",
        player_id="player",
        location_id="square",
        visible_facts=list(state.player_visible_facts),
        npc_known_facts=["public_fact"],
        relationship_tone=get_tone_for_dialogue(state, "mira", "player"),
        emotional_state=state.npcs["mira"].emotional_state,
    )

    assert default_context.excluded_memory_reasons == []


def test_dialogue_mode_uses_safe_rp_memory() -> None:
    safe = memory(
        "memory-dialogue",
        "Mira remembers a careful apology.",
        tags=["dialogue", "relationship"],
        entity_ids=["npc:mira"],
        fact_ids=["public_fact"],
    )
    hidden = memory(
        "memory-hidden",
        "Mira hides a debt.",
        visibility=MemoryVisibility.NARRATOR_SAFE,
        fact_ids=["hidden_fact"],
    )
    manager = DialogueManager(memory_store=InMemoryMemoryStore([safe, hidden]))
    state = make_state()

    context = manager.build_dialogue_context(state, focus_npc_id="mira")

    assert len(context.rp_memory_summaries) == 1
    assert "memory_ref=speaker_safe" in context.rp_memory_summaries[0]
    assert "Mira remembers a careful apology" not in context.rp_memory_summaries[0]
    assert "memory-dialogue" not in context.rp_memory_summaries[0]
    assert "memory-hidden" not in " ".join(context.rp_memory_summaries)
