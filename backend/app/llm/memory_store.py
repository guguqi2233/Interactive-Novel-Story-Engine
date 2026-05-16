from abc import ABC, abstractmethod

from app.llm.schemas import MemorySummary


class MemoryStore(ABC):
    @abstractmethod
    def add_memory(self, memory: MemorySummary) -> None:
        """Persist one memory summary."""

    @abstractmethod
    def search_memory(self, query: str) -> list[MemorySummary]:
        """Return memories relevant to a simple query."""

    @abstractmethod
    def list_recent_memories(self, limit: int = 10) -> list[MemorySummary]:
        """Return recent memories in newest-last order."""


class InMemoryMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._memories: list[MemorySummary] = []

    def add_memory(self, memory: MemorySummary) -> None:
        self._memories.append(memory)

    def search_memory(self, query: str) -> list[MemorySummary]:
        normalized_query = query.lower()
        return [
            memory
            for memory in self._memories
            if normalized_query in _memory_search_text(memory).lower()
        ]

    def list_recent_memories(self, limit: int = 10) -> list[MemorySummary]:
        if limit <= 0:
            return []
        return self._memories[-limit:]


def _memory_search_text(memory: MemorySummary) -> str:
    return " ".join(
        [
            memory.summary,
            *memory.important_facts,
            *memory.open_threads,
            *memory.npc_relationship_changes,
        ]
    )

