from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Protocol
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
    embedding: list[float] | None = None


class MemoryQuery(BaseModel):
    tags: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    substring: str | None = None
    semantic_query: str | None = None
    turn_from: int | None = Field(default=None, ge=0)
    turn_to: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=0)
    allowed_visibility: set[MemoryVisibility] | None = None


class EmbeddingProvider(Protocol):
    """Optional embedding provider abstraction; tests should use local/fake providers."""

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for text."""


class MemoryEmbeddingBackend(Protocol):
    """Optional vector retrieval hook without changing callers."""

    def search(self, query: str, memories: list[MemoryRecord], limit: int) -> list[MemoryRecord]:
        """Return records ranked by an embedding backend."""


class MemoryRepository(Protocol):
    """Minimal persistence protocol implemented by SQLiteSaveRepository."""

    def append_memory(self, save_id: str, memory: MemoryRecord) -> Any:
        """Persist or replace one memory record."""

    def save_memories(self, save_id: str, memories: list[MemoryRecord]) -> list[MemoryRecord]:
        """Replace all memories for one save."""

    def list_memories(self, save_id: str) -> list[MemoryRecord]:
        """List memories for one save."""


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
    def __init__(
        self,
        memories: list[MemoryRecord] | None = None,
        embedding_backend: MemoryEmbeddingBackend | None = None,
    ) -> None:
        self._memories: dict[str, MemoryRecord] = {
            memory.id: memory for memory in memories or []
        }
        self._embedding_backend = embedding_backend

    def add_memory(self, memory: MemoryRecord | MemorySummary) -> MemoryRecord:
        record = _coerce_memory_record(memory)
        self._memories[record.id] = record
        return record

    def search_memory(self, query: str | MemoryQuery) -> list[MemoryRecord]:
        memory_query = (
            MemoryQuery(substring=query) if isinstance(query, str) else query
        )
        if memory_query.semantic_query and self._embedding_backend is not None:
            return self._embedding_backend.search(
                memory_query.semantic_query,
                [
                    memory
                    for memory in self._memories.values()
                    if _matches_query_impl(memory, memory_query, include_semantic=False)
                ],
                memory_query.limit,
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


class SQLiteMemoryStore(MemoryStore):
    """SQLite-backed MemoryStore using the save repository memory table."""

    def __init__(
        self,
        repository: MemoryRepository,
        save_id: str,
        embedding_backend: MemoryEmbeddingBackend | None = None,
    ) -> None:
        self._repository = repository
        self._save_id = save_id
        self._embedding_backend = embedding_backend

    def add_memory(self, memory: MemoryRecord | MemorySummary) -> MemoryRecord:
        record = _coerce_memory_record(memory)
        self._repository.append_memory(self._save_id, record)
        return record

    def search_memory(self, query: str | MemoryQuery) -> list[MemoryRecord]:
        return _search_records(
            self._repository.list_memories(self._save_id),
            query,
            self._embedding_backend,
        )

    def list_recent_memories(
        self,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return _rank_recent_memories(
            [
                memory
                for memory in self._repository.list_memories(self._save_id)
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
            MemoryQuery(entity_ids=[entity_id], limit=limit, allowed_visibility=allowed_visibility)
        )

    def search_by_fact(
        self,
        fact_id: str,
        limit: int = 10,
        allowed_visibility: set[MemoryVisibility] | None = None,
    ) -> list[MemoryRecord]:
        return self.search_memory(
            MemoryQuery(fact_ids=[fact_id], limit=limit, allowed_visibility=allowed_visibility)
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
        memories = self._repository.list_memories(self._save_id)
        return _rank_memories(memories, len(memories))

    def replace_all(self, memories: list[MemoryRecord]) -> list[MemoryRecord]:
        return self._repository.save_memories(self._save_id, memories)


class LocalVectorMemoryStore(InMemoryMemoryStore):
    """Local vector-ready store with deterministic fallback when no backend exists."""

    def __init__(
        self,
        memories: list[MemoryRecord] | None = None,
        embedding_backend: MemoryEmbeddingBackend | None = None,
    ) -> None:
        super().__init__(memories=memories, embedding_backend=embedding_backend)


OptionalVectorMemoryStore = LocalVectorMemoryStore


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
        visibility=MemoryVisibility.DEBUG_ONLY,
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
    return _matches_query_impl(memory, query, include_semantic=True)


def _matches_query_impl(memory: MemoryRecord, query: MemoryQuery, *, include_semantic: bool) -> bool:
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
    if include_semantic and query.semantic_query and query.semantic_query.lower() not in memory.content.lower():
        return False
    if query.turn_from is not None and memory.created_turn < query.turn_from:
        return False
    if query.turn_to is not None and memory.created_turn > query.turn_to:
        return False
    return True


def _search_records(
    memories: list[MemoryRecord],
    query: str | MemoryQuery,
    embedding_backend: MemoryEmbeddingBackend | None = None,
) -> list[MemoryRecord]:
    memory_query = MemoryQuery(substring=query) if isinstance(query, str) else query
    candidates = [
        memory
        for memory in memories
        if _matches_query_impl(memory, memory_query, include_semantic=embedding_backend is None)
    ]
    if memory_query.semantic_query and embedding_backend is not None:
        return embedding_backend.search(memory_query.semantic_query, candidates, memory_query.limit)
    return _rank_memories(candidates, memory_query.limit)


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
