from pydantic import BaseModel, Field

from app.core.world_state import FactVisibility, GameState
from app.engine.actions.schemas import ActionResult
from app.engine.rules.knowledge import npc_knows
from app.llm.memory_store import (
    MemoryRecord,
    MemoryStore,
    MemoryVisibility,
    filter_narrator_safe_memories,
    filter_player_visible_memories,
)


class ExcludedMemoryReason(BaseModel):
    memory_id: str
    reason: str


class MemoryContext(BaseModel):
    narrator_safe_memories: list[MemoryRecord] = Field(default_factory=list)
    player_visible_memories: list[MemoryRecord] = Field(default_factory=list)
    npc_known_memories: list[MemoryRecord] = Field(default_factory=list)
    excluded_memory_reasons: list[ExcludedMemoryReason] = Field(default_factory=list)


class MemoryContextBuilder:
    def __init__(self, memory_store: MemoryStore, *, limit: int = 20) -> None:
        self._memory_store = memory_store
        self._limit = limit

    def build(
        self,
        state: GameState,
        actor_id: str,
        current_location: str,
        action_result: ActionResult,
        visible_facts: list[str],
        current_npc_id: str | None = None,
    ) -> MemoryContext:
        candidates = self._collect_candidates(
            state=state,
            actor_id=actor_id,
            current_location=current_location,
            action_result=action_result,
            visible_facts=visible_facts,
            current_npc_id=current_npc_id,
        )
        excluded: list[ExcludedMemoryReason] = []
        narrator_safe: list[MemoryRecord] = []
        player_visible: list[MemoryRecord] = []
        npc_known: list[MemoryRecord] = []

        for memory in candidates:
            narrator_reason = _narrator_exclusion_reason(state, memory)
            if narrator_reason is None:
                narrator_safe.append(memory)
            else:
                excluded.append(ExcludedMemoryReason(memory_id=memory.id, reason=narrator_reason))

            player_reason = _player_exclusion_reason(state, memory)
            if player_reason is None:
                player_visible.append(memory)
            elif player_reason != narrator_reason:
                excluded.append(ExcludedMemoryReason(memory_id=memory.id, reason=player_reason))

            if current_npc_id is not None:
                npc_reason = _npc_exclusion_reason(state, current_npc_id, memory)
                if npc_reason is None:
                    npc_known.append(memory)
                elif npc_reason not in {narrator_reason, player_reason}:
                    excluded.append(ExcludedMemoryReason(memory_id=memory.id, reason=npc_reason))

        return MemoryContext(
            narrator_safe_memories=_rank_context_memories(narrator_safe, self._limit),
            player_visible_memories=_rank_context_memories(player_visible, self._limit),
            npc_known_memories=_rank_context_memories(npc_known, self._limit),
            excluded_memory_reasons=excluded,
        )

    def _collect_candidates(
        self,
        state: GameState,
        actor_id: str,
        current_location: str,
        action_result: ActionResult,
        visible_facts: list[str],
        current_npc_id: str | None,
    ) -> list[MemoryRecord]:
        candidates: dict[str, MemoryRecord] = {}

        def add(memories: list[MemoryRecord]) -> None:
            for memory in memories:
                candidates[memory.id] = memory

        add(self._memory_store.list_recent_memories(limit=self._limit * 2))
        for entity_id in _candidate_entity_ids(actor_id, current_location, current_npc_id):
            add(self._memory_store.search_by_entity(entity_id, limit=self._limit))
        for fact_id in sorted(set(visible_facts) | set(action_result.visible_facts)):
            add(self._memory_store.search_by_fact(fact_id, limit=self._limit))
        for quest_id in sorted(state.quests):
            add(self._memory_store.search_by_tags([f"quest:{quest_id}"], limit=self._limit))
        add(self._memory_store.search_by_tags(["quest"], limit=self._limit))
        return list(candidates.values())


def _candidate_entity_ids(actor_id: str, current_location: str, current_npc_id: str | None) -> list[str]:
    entity_ids = [
        actor_id,
        f"actor:{actor_id}",
        current_location,
        f"location:{current_location}",
    ]
    if current_npc_id:
        entity_ids.extend([current_npc_id, f"npc:{current_npc_id}"])
    return entity_ids


def _narrator_exclusion_reason(state: GameState, memory: MemoryRecord) -> str | None:
    if memory not in filter_narrator_safe_memories([memory]):
        return f"visibility:{memory.visibility}"
    return _hidden_or_unknown_fact_reason(state, memory, audience="narrator")


def _player_exclusion_reason(state: GameState, memory: MemoryRecord) -> str | None:
    if memory not in filter_player_visible_memories([memory]):
        return f"player_visibility:{memory.visibility}"
    return _hidden_or_unknown_fact_reason(state, memory, audience="player")


def _npc_exclusion_reason(state: GameState, npc_id: str, memory: MemoryRecord) -> str | None:
    if memory.visibility in {MemoryVisibility.HIDDEN, MemoryVisibility.DEBUG_ONLY}:
        return f"npc_visibility:{memory.visibility}"
    if npc_id not in state.npcs:
        return f"unknown_npc:{npc_id}"
    for fact_id in memory.fact_ids:
        if fact_id in state.player_visible_facts:
            continue
        fact = state.facts.get(fact_id)
        if fact is not None and fact.visibility == FactVisibility.PUBLIC:
            continue
        if not npc_knows(state, npc_id, fact_id):
            return f"npc_unknown_fact:{fact_id}"
    return None


def _hidden_or_unknown_fact_reason(state: GameState, memory: MemoryRecord, *, audience: str) -> str | None:
    for fact_id in memory.fact_ids:
        fact = state.facts.get(fact_id)
        if fact is None:
            continue
        if fact.visibility == FactVisibility.HIDDEN and fact_id not in state.player_visible_facts:
            return f"{audience}_unknown_hidden_fact:{fact_id}"
        if fact.visibility == FactVisibility.DISCOVERABLE and fact_id not in state.player_visible_facts:
            return f"{audience}_unknown_discoverable_fact:{fact_id}"
    if "source_event_hidden" in memory.tags and memory.visibility != MemoryVisibility.DEBUG_ONLY:
        return f"{audience}_hidden_source_event"
    return None


def _rank_context_memories(memories: list[MemoryRecord], limit: int) -> list[MemoryRecord]:
    return sorted(
        memories,
        key=lambda memory: (
            _location_priority(memory),
            -memory.importance,
            -memory.created_turn,
            memory.id,
        ),
    )[:limit]


def _location_priority(memory: MemoryRecord) -> int:
    return 0 if any(entity_id.startswith("location:") for entity_id in memory.entity_ids) else 1
