from pydantic import BaseModel, Field

from app.core.world_state import FactVisibility, GameState
from app.engine.actions.schemas import ActionResult
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.emotions import emotion_to_dialogue_tone
from app.engine.rules.relationship_tone import RelationshipTone
from app.engine.rules.relationship_tone import get_tone_for_dialogue, tone_summary_for_prompt
from app.roleplay.example_dialogues import build_example_dialogue_context
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


class RPMemoryContext(BaseModel):
    speaker_safe_memories: list[MemoryRecord] = Field(default_factory=list)
    player_visible_shared_memories: list[MemoryRecord] = Field(default_factory=list)
    relationship_memories: list[MemoryRecord] = Field(default_factory=list)
    recent_dialogue_memories: list[MemoryRecord] = Field(default_factory=list)
    excluded_memory_reasons: list[ExcludedMemoryReason] = Field(default_factory=list)


class RPMemoryContextBuilder:
    """Build safe RP memory context for one dialogue speaker.

    RP memories are style/context hints. They never become authoritative facts
    and never alter GameState or NPC knowledge.
    """

    def __init__(
        self,
        memory_store: MemoryStore,
        *,
        limit: int = 8,
        include_debug_reasons: bool = False,
    ) -> None:
        self._memory_store = memory_store
        self._limit = limit
        self._include_debug_reasons = include_debug_reasons

    def build(
        self,
        *,
        state: GameState,
        dialogue_session: object,
        speaker_npc_id: str,
        player_id: str,
        location_id: str,
        visible_facts: list[str],
        npc_known_facts: list[str],
        relationship_tone: RelationshipTone,
        emotional_state: object,
    ) -> RPMemoryContext:
        candidates = self._collect_candidates(
            state=state,
            dialogue_session=dialogue_session,
            speaker_npc_id=speaker_npc_id,
            player_id=player_id,
            location_id=location_id,
            relationship_tone=relationship_tone,
            emotional_state=emotional_state,
        )
        safe: list[MemoryRecord] = []
        player_shared: list[MemoryRecord] = []
        relationship: list[MemoryRecord] = []
        recent_dialogue: list[MemoryRecord] = []
        excluded: list[ExcludedMemoryReason] = []
        visible_fact_set = set(visible_facts)
        npc_fact_set = set(npc_known_facts)

        for memory in candidates:
            reason = _rp_memory_exclusion_reason(
                state,
                memory,
                speaker_npc_id=speaker_npc_id,
                visible_facts=visible_fact_set,
                npc_known_facts=npc_fact_set,
            )
            if reason is not None:
                excluded.append(ExcludedMemoryReason(memory_id=memory.id, reason=reason))
                continue
            safe.append(memory)
            if memory.visibility == MemoryVisibility.PLAYER_VISIBLE:
                player_shared.append(memory)
            if _is_relationship_memory(memory, speaker_npc_id, player_id):
                relationship.append(memory)
            if _is_recent_dialogue_memory(memory, state.turn):
                recent_dialogue.append(memory)

        return RPMemoryContext(
            speaker_safe_memories=_rank_context_memories(safe, self._limit),
            player_visible_shared_memories=_rank_context_memories(player_shared, self._limit),
            relationship_memories=_rank_context_memories(relationship, self._limit),
            recent_dialogue_memories=_rank_context_memories(recent_dialogue, self._limit),
            excluded_memory_reasons=excluded if self._include_debug_reasons else [],
        )

    def _collect_candidates(
        self,
        *,
        state: GameState,
        dialogue_session: object,
        speaker_npc_id: str,
        player_id: str,
        location_id: str,
        relationship_tone: RelationshipTone,
        emotional_state: object,
    ) -> list[MemoryRecord]:
        candidates: dict[str, MemoryRecord] = {}

        def add(memories: list[MemoryRecord]) -> None:
            for memory in memories:
                candidates[memory.id] = memory

        add(self._memory_store.list_recent_memories(limit=self._limit * 2))
        for entity_id in [
            speaker_npc_id,
            f"npc:{speaker_npc_id}",
            player_id,
            f"actor:{player_id}",
            location_id,
            f"location:{location_id}",
            f"relationship:{speaker_npc_id}:{player_id}",
            f"relationship:{player_id}:{speaker_npc_id}",
        ]:
            add(self._memory_store.search_by_entity(entity_id, limit=self._limit))
        for topic in sorted(set(getattr(dialogue_session, "active_topics", []))):
            add(self._memory_store.search_by_tags([f"topic:{topic}"], limit=self._limit))
        emotion = getattr(emotional_state, "primary_emotion", None)
        emotion_value = getattr(emotion, "value", str(emotion)) if emotion is not None else ""
        if emotion_value:
            add(self._memory_store.search_by_tags([f"emotion:{emotion_value}"], limit=self._limit))
        if relationship_tone.tension >= 60:
            add(self._memory_store.search_by_tags(["tone:tension"], limit=self._limit))
        if relationship_tone.warmth >= 60:
            add(self._memory_store.search_by_tags(["tone:warmth"], limit=self._limit))
        add(self._memory_store.search_by_tags(["dialogue"], limit=self._limit))
        add(self._memory_store.search_by_turn_range(max(0, state.turn - 5), state.turn, limit=self._limit))
        return list(candidates.values())


class NPCDialogueProfileContext(BaseModel):
    npc_id: str
    public_persona: str = ""
    attachment_style: str = ""
    trust_expression_style: str = ""
    conflict_expression_style: str = ""
    intimacy_expression_style: str = ""
    deception_style: str = ""
    boundaries: list[str] = Field(default_factory=list)
    tone: str = ""
    sentence_length: str = "mixed"
    vocabulary_style: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    speech_habits: list[str] = Field(default_factory=list)
    silence_style: str = ""
    emotional_tells: list[str] = Field(default_factory=list)
    dialogue_style: str = ""
    emotional_mask: str = ""
    example_dialogue_refs: list[str] = Field(default_factory=list)
    example_dialogue_summaries: list[str] = Field(default_factory=list)
    taboo_topic_count: int = 0
    emotional_tone: str = "calm"
    emotion_intensity_band: str = "none"
    relationship_tone_summary: str = ""


def build_npc_dialogue_profile_context(state: GameState, npc_id: str) -> NPCDialogueProfileContext:
    """Return expression-only NPC RP fields safe for dialogue prompts.

    This intentionally excludes private_self_summary and taboo topic text.
    Taboo topics are authoring constraints, not NPC knowledge grants.
    """
    npc = state.npcs[npc_id]
    rp = npc.rp_profile
    voice = npc.voice_profile
    return NPCDialogueProfileContext(
        npc_id=npc_id,
        public_persona=rp.public_persona,
        attachment_style=rp.attachment_style,
        trust_expression_style=rp.trust_expression_style,
        conflict_expression_style=rp.conflict_expression_style,
        intimacy_expression_style=rp.intimacy_expression_style,
        deception_style=rp.deception_style,
        boundaries=list(rp.boundaries),
        tone=voice.tone,
        sentence_length=voice.sentence_length,
        vocabulary_style=voice.vocabulary_style,
        catchphrases=list(voice.catchphrases),
        speech_habits=sorted(set(voice.speech_habits) | set(npc.speech_habits)),
        silence_style=voice.silence_style,
        emotional_tells=list(voice.emotional_tells),
        dialogue_style=npc.dialogue_style,
        emotional_mask=npc.emotional_mask,
        example_dialogue_refs=list(npc.example_dialogue_refs),
        example_dialogue_summaries=build_example_dialogue_context(state, npc_id),
        taboo_topic_count=len(npc.taboo_topics),
        emotional_tone=emotion_to_dialogue_tone(npc.emotional_state),
        emotion_intensity_band=_intensity_band(npc.emotional_state.intensity),
        relationship_tone_summary=tone_summary_for_prompt(get_tone_for_dialogue(state, npc_id, "player")),
    )


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


def _rp_memory_exclusion_reason(
    state: GameState,
    memory: MemoryRecord,
    *,
    speaker_npc_id: str,
    visible_facts: set[str],
    npc_known_facts: set[str],
) -> str | None:
    if memory.visibility == MemoryVisibility.HIDDEN:
        return f"rp_visibility:{memory.visibility}"
    if memory.visibility == MemoryVisibility.DEBUG_ONLY:
        return f"rp_visibility:{memory.visibility}"
    if speaker_npc_id not in state.npcs:
        return f"unknown_npc:{speaker_npc_id}"
    for fact_id in memory.fact_ids:
        fact = state.facts.get(fact_id)
        if fact is None:
            continue
        player_can_see = fact.visibility == FactVisibility.PUBLIC or fact_id in visible_facts
        if not player_can_see:
            return f"rp_hidden_or_unknown_fact:{fact_id}"
        npc_can_use = fact.visibility == FactVisibility.PUBLIC or fact_id in npc_known_facts or npc_knows(state, speaker_npc_id, fact_id)
        if not npc_can_use:
            return f"rp_npc_unknown_fact:{fact_id}"
    if "source_event_hidden" in memory.tags:
        return "rp_hidden_source_event"
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


def _is_relationship_memory(memory: MemoryRecord, speaker_npc_id: str, player_id: str) -> bool:
    relationship_tags = {
        "relationship",
        f"relationship:{speaker_npc_id}:{player_id}",
        f"relationship:{player_id}:{speaker_npc_id}",
    }
    relationship_entities = {
        f"relationship:{speaker_npc_id}:{player_id}",
        f"relationship:{player_id}:{speaker_npc_id}",
    }
    return bool(relationship_tags.intersection(memory.tags) or relationship_entities.intersection(memory.entity_ids))


def _is_recent_dialogue_memory(memory: MemoryRecord, current_turn: int) -> bool:
    return "dialogue" in memory.tags or current_turn - memory.created_turn <= 5


def _intensity_band(value: int) -> str:
    if value >= 70:
        return "high"
    if value >= 35:
        return "medium"
    if value > 0:
        return "low"
    return "none"
