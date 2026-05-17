import pytest

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState
from app.llm.fake_provider import FakeLLMProvider
from app.llm.memory_store import InMemoryMemoryStore, MemoryVisibility
from app.llm.memory_summarizer import MemorySummarizer
from app.llm.provider_base import LLMProviderError
from app.llm.schemas import MemorySummary


def make_event(event_id: str, turn: int, text: str) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="player",
        action_type="observe",
        result="success",
        visible_to_player=True,
        input_text=text,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.INC,
                path="turn",
                value=1,
            )
        ],
        narrative_text=f"narrative: {text}",
    )


def test_memory_summarizer_uses_fake_provider_json() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "summary": "The player examined the square.",
                "important_facts": ["The square has a well."],
                "open_threads": ["Who moved the lantern?"],
                "npc_relationship_changes": [],
            }
        ]
    )
    summarizer = MemorySummarizer(provider)

    summary = summarizer.summarize_recent(
        events=[
            make_event("event-1", 1, "observe square"),
            make_event("event-2", 2, "inspect well"),
        ],
        limit=2,
    )

    assert summary == MemorySummary(
        summary="The player examined the square.",
        important_facts=["The square has a well."],
        open_threads=["Who moved the lantern?"],
        npc_relationship_changes=[],
    )


def test_memory_summarizer_schema_error_is_not_silent() -> None:
    provider = FakeLLMProvider(json_responses=[{"summary": "partial summary"}])
    summarizer = MemorySummarizer(provider)

    summary = summarizer.summarize_recent([make_event("event-1", 1, "observe")], limit=1)

    assert summary.important_facts == []
    assert summary.open_threads == []
    assert summary.npc_relationship_changes == []


def test_memory_summarizer_invalid_schema_raises() -> None:
    provider = FakeLLMProvider(json_responses=[{"summary": 123}])
    summarizer = MemorySummarizer(provider)

    with pytest.raises(LLMProviderError, match="schema validation"):
        summarizer.summarize_recent([make_event("event-1", 1, "observe")], limit=1)


def test_in_memory_memory_store_accepts_legacy_summary_records() -> None:
    store = InMemoryMemoryStore()
    first = MemorySummary(summary="The player found a coin.", important_facts=["coin"], open_threads=[])
    second = MemorySummary(summary="Harlan mentioned the sealed gate.", open_threads=["sealed gate"])

    store.add_memory(first)
    second_record = store.add_memory(second)

    assert store.search_memory("sealed gate") == [second_record]
    assert len(store.list_recent_memories(1)) == 1
    assert store.list_recent_memories(0) == []
    assert second_record.visibility == MemoryVisibility.NARRATOR_SAFE


def test_memory_summarizer_does_not_mutate_game_state() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "summary": "safe summary",
                "important_facts": [],
                "open_threads": [],
                "npc_relationship_changes": [],
            }
        ]
    )
    summarizer = MemorySummarizer(provider)
    state = GameState(world_id="memory-test")
    before = state.model_dump_json()

    summarizer.summarize_recent([make_event("event-1", 1, "observe")], limit=1)

    assert state.model_dump_json() == before
