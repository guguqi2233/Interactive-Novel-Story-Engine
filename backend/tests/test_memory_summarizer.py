import pytest

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.llm.fake_provider import FakeLLMProvider
from app.llm.memory_store import InMemoryMemoryStore
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
        state_delta=StateDelta(
            operation=StateDeltaOperation.INC,
            path="turn",
            value=1,
        ),
        narrative_text=f"叙事：{text}",
    )


def test_memory_summarizer_uses_fake_provider_json() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "summary": "玩家观察了雾谷广场。",
                "important_facts": ["广场有告示板"],
                "open_threads": ["寻找失踪工具"],
                "npc_relationship_changes": [],
            }
        ]
    )
    summarizer = MemorySummarizer(provider)

    summary = summarizer.summarize_recent(
        events=[
            make_event("event-1", 1, "观察广场"),
            make_event("event-2", 2, "查看告示板"),
        ],
        limit=2,
    )

    assert summary == MemorySummary(
        summary="玩家观察了雾谷广场。",
        important_facts=["广场有告示板"],
        open_threads=["寻找失踪工具"],
        npc_relationship_changes=[],
    )


def test_memory_summarizer_schema_error_is_not_silent() -> None:
    provider = FakeLLMProvider(json_responses=[{"summary": "缺少字段也可以有默认列表"}])
    summarizer = MemorySummarizer(provider)

    summary = summarizer.summarize_recent([make_event("event-1", 1, "观察")], limit=1)

    assert summary.important_facts == []
    assert summary.open_threads == []
    assert summary.npc_relationship_changes == []


def test_memory_summarizer_invalid_schema_raises() -> None:
    provider = FakeLLMProvider(json_responses=[{"summary": 123}])
    summarizer = MemorySummarizer(provider)

    with pytest.raises(LLMProviderError, match="schema validation"):
        summarizer.summarize_recent([make_event("event-1", 1, "观察")], limit=1)


def test_in_memory_memory_store_add_search_and_recent() -> None:
    store = InMemoryMemoryStore()
    first = MemorySummary(summary="玩家到达广场", important_facts=["广场"], open_threads=[])
    second = MemorySummary(summary="哈兰提到失踪工具", open_threads=["失踪工具"])

    store.add_memory(first)
    store.add_memory(second)

    assert store.search_memory("哈兰") == [second]
    assert store.list_recent_memories(1) == [second]
    assert store.list_recent_memories(0) == []

