from app.core.state_delta import apply_delta
from app.core.world_state import CrimeState, CrimeStatus, GameState, LocationState, NPCState, RelationshipState, RumorState
from app.engine.rules.npc_memory_reactions import (
    NPCMemoryReactionRule,
    NPCMemoryReactionType,
    resolve_npc_memory_reactions,
)
from app.llm.memory_store import MemoryRecord, MemoryVisibility


def make_state() -> GameState:
    return GameState(
        world_id="npc-memory-reactions-test",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={"harlan": NPCState(id="harlan", location_id="square")},
        crimes={
            "theft-1": CrimeState(
                id="theft-1",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                severity=2,
                status=CrimeStatus.WITNESSED,
                witnessed_by=["harlan"],
            ),
            "hidden-crime": CrimeState(
                id="hidden-crime",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                severity=3,
                status=CrimeStatus.WITNESSED,
                witnessed_by=[],
            ),
        },
        rumors={
            "rumor-1": RumorState(
                id="rumor-1",
                text_for_player="A safe known rumor.",
                known_by_npcs={"harlan"},
            )
        },
        relationships={
            "harlan:general:player": RelationshipState(
                id="harlan:general:player",
                source_id="harlan",
                target_id="player",
                relation_type="general",
                trust=1,
            )
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_witnessed_theft_memory_increases_suspicion() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="memory-theft",
        content="Harlan saw the theft.",
        tags=["crime", "theft", "crime:theft-1"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
        importance=5,
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].suspicion == 1
    assert any(delta.metadata.get("source") == "npc_memory_reaction" for delta in result.state_deltas)


def test_unknown_crime_does_not_trigger_report_crime() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="memory-hidden-crime",
        content="A crime Harlan does not know.",
        tags=["crime", "crime:hidden-crime"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )
    rule = NPCMemoryReactionRule(
        id="report-hidden-crime",
        reaction_type=NPCMemoryReactionType.REPORT_CRIME,
        required_tags=["crime"],
        target_id="hidden-crime",
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory], [rule])

    assert result.state_deltas == []
    assert result.events == []
    assert result.skipped_memory_ids == ["memory-hidden-crime"]


def test_hidden_memory_does_not_trigger_reaction() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="hidden-memory",
        content="Secret debug-only clue.",
        tags=["crime", "theft", "crime:theft-1"],
        visibility=MemoryVisibility.HIDDEN,
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory])

    assert result.state_deltas == []
    assert result.events == []
    assert result.skipped_memory_ids == ["hidden-memory"]


def test_known_rumor_triggers_spread_rumor_intent() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="rumor-memory",
        content="Harlan remembers the rumor.",
        tags=["rumor", "rumor:rumor-1"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].intent_queue[0].intent_type == "spread_rumor"
    assert next_state.npcs["harlan"].intent_queue[0].target_id == "rumor-1"


def test_relationship_memory_can_soften_tone() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="relationship-memory",
        content="A previous kind exchange.",
        tags=["relationship"],
        entity_ids=["relationship:harlan:player"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory])
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].mood == "softened"


def test_reaction_records_event() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="memory-theft",
        content="Harlan saw the theft.",
        tags=["crime", "theft", "crime:theft-1"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )

    result = resolve_npc_memory_reactions(state, "harlan", [memory])

    assert result.events
    assert result.events[0].actor_id == "system"
    assert result.events[0].action_type == "npc_memory_reaction"
    assert result.events[0].state_deltas == result.state_deltas


def test_dedupe_marker_prevents_repeated_reaction() -> None:
    state = make_state()
    memory = MemoryRecord(
        id="memory-theft",
        content="Harlan saw the theft.",
        tags=["crime", "theft", "crime:theft-1"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )
    first = resolve_npc_memory_reactions(state, "harlan", [memory])
    next_state = apply_all(state, first.state_deltas)

    second = resolve_npc_memory_reactions(next_state, "harlan", [memory])

    assert first.state_deltas
    assert second.state_deltas == []
    assert second.events == []
