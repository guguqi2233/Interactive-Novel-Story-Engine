from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from app.llm.schemas import MemorySummary


class MemoryVisibility(StrEnum):
    PLAYER_VISIBLE = "player_visible"
    NARRATOR_SAFE = "narrator_safe"
    DEBUG_ONLY = "debug_only"
    HIDDEN = "hidden"


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"memory-{uuid4().hex}")
    content: str
    source_event_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    visibility: MemoryVisibility = MemoryVisibility.NARRATOR_SAFE
    importance: int = Field(default=0, ge=0)
    created_turn: int = Field(default=0, ge=0)


class MemoryQuery(BaseModel):
    tags: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    substring: str | None = None
    turn_from: int | None = Field(default=None, ge=0)
    turn_to: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=0)
    allowed_visibility: set[MemoryVisibility] | None = None


class MemoryEmbeddingBackend(Protocol):
    """Optional future hook for local/vector retrieval without changing callers."""

    def search(self, query: str, memories: list[MemoryRecord], limit: int) -> list[MemoryRecord]:
        """Return records ranked by an embedding backend."""


class MemoryStore(ABC):
    @abstractmethod
    def add_memory(self, memory: MemoryRecord | MemorySummary) -> MemoryRecord:
        """Persist one memory record and return the stored record."""

    @abstractmethod
    def search_memory(self, query: str | MemoryQuery) -> list[MemoryRecord]:
        """Return memories relevant to a structured or substring query."""

    @abstractmethod
    def list_recent_memories(
        self,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        """Return recent memories newest first."""

    @abstractmethod
    def search_by_tags(
        self,
        tags: list[str],
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        """Return memories containing all requested tags."""

    @abstractmethod
    def search_by_entity(
        self,
        entity_id: str,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        """Return memories linked to one entity."""

    @abstractmethod
    def search_by_fact(
        self,
        fact_id: str,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        """Return memories linked to one fact."""

    @abstractmethod
    def search_by_turn_range(
        self,
        turn_from: int,
        turn_to: int,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        """Return memories created within a turn range."""


class InMemoryMemoryStore(MemoryStore):
    def __init__(self, memories: list[MemoryRecord] | None = None) -> None:
        self._memories: dict[str, MemoryRecord] = {
            memory.id: memory for memory in memories or []
        }

    def add_memory(self, memory: MemoryRecord | MemorySummary) -> MemoryRecord:
        record = _coerce_memory_record(memory)
        self._memories[record.id] = record
        return record

    def search_memory(self, query: str | MemoryQuery) -> list[MemoryRecord]:
        memory_query = (
            MemoryQuery(substring=query) if isinstance(query, str) else query
        )
        return _rank_memories(
            [
                memory
                for memory in self._memories.values()
                if _matches_query(memory, memory_query)
            ],
            memory_query.limit,
        )

    def list_recent_memories(
        self,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        if limit <= 0:
            return []
        return _rank_recent_memories(
            [
                memory
                for memory in self._memories.values()
                if _visibility_allowed(memory, allowed_visibility)
            ],
            limit,
        )

    def search_by_tags(
        self,
        tags: list[str],
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return self.search_memory(
            MemoryQuery(tags=tags, limit=limit, allowed_visibility=allowed_visibility)
        )

    def search_by_entity(
        self,
        entity_id: str,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return self.search_memory(
            MemoryQuery(
                entity_ids=[entity_id],
                limit=limit,
                allowed_visibility=allowed_visibility,
            )
        )

    def search_by_fact(
        self,
        fact_id: str,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return self.search_memory(
            MemoryQuery(
                fact_ids=[fact_id],
                limit=limit,
                allowed_visibility=allowed_visibility,
            )
        )

    def search_by_turn_range(
        self,
        turn_from: int,
        turn_to: int,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return self.search_memory(
            MemoryQuery(
                turn_from=turn_from,
                turn_to=turn_to,
                limit=limit,
                allowed_visibility=allowed_visibility,
            )
        )

    def list_all(self) -> list[MemoryRecord]:
        return _rank_memories(list(self._memories.values()), len(self._memories))


NARRATOR_SAFE_MEMORY_VISIBILITIES = {
    MemoryVisibility.PLAYER_VISIBLE,
    MemoryVisibility.NARRATOR_SAFE,
}
PLAYER_VISIBLE_MEMORY_VISIBILITIES = {MemoryVisibility.PLAYER_VISIBLE}


def filter_narrator_safe_memories(memories: list[MemoryRecord]) -> list[MemoryRecord]:
    return [
        memory
        for memory in memories
        if memory.visibility in NARRATOR_SAFE_MEMORY_VISIBILITIES
    ]


def filter_player_visible_memories(memories: list[MemoryRecord]) -> list[MemoryRecord]:
    return [
        memory
        for memory in memories
        if memory.visibility in PLAYER_VISIBLE_MEMORY_VISIBILITIES
    ]


def _coerce_memory_record(memory: MemoryRecord | MemorySummary) -> MemoryRecord:
    if isinstance(memory, MemoryRecord):
        return memory
    return MemoryRecord(
        content=_memory_summary_text(memory),
        tags=["summary"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
    )


def _memory_summary_text(memory: MemorySummary) -> str:
    return " ".join(
        [
            memory.summary,
            *memory.important_facts,
            *memory.open_threads,
            *memory.npc_relationship_changes,
        ]
    )


def _matches_query(memory: MemoryRecord, query: MemoryQuery) -> bool:
    if not _visibility_allowed(memory, query.allowed_visibility):
        return False
    if query.tags and not set(query.tags).issubset(memory.tags):
        return False
    if query.entity_ids and not set(query.entity_ids).issubset(memory.entity_ids):
        return False
    if query.fact_ids and not set(query.fact_ids).issubset(memory.fact_ids):
        return False
    if query.substring and query.substring.lower() not in memory.content.lower():
        return False
    if query.turn_from is not None and memory.created_turn < query.turn_from:
        return False
    if query.turn_to is not None and memory.created_turn > query.turn_to:
        return False
    return True


def _visibility_allowed(
    memory: MemoryRecord,
    allowed_visibility: set[MemoryVisibility] | None,
) -> bool:
    return allowed_visibility is None or memory.visibility in allowed_visibility


def _rank_memories(memories: list[MemoryRecord], limit: int) -> list[MemoryRecord]:
    if limit <= 0:
        return []
    return sorted(
        memories,
        key=lambda memory: (-memory.importance, -memory.created_turn, memory.id),
    )[:limit]


def _rank_recent_memories(memories: list[MemoryRecord], limit: int) -> list[MemoryRecord]:
    if limit <= 0:
        return []
    return sorted(
        memories,
        key=lambda memory: (-memory.created_turn, -memory.importance, memory.id),
    )[:limit]
