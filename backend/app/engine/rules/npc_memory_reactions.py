from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCIntent
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_intents import enqueue_intent
from app.llm.memory_store import MemoryRecord, MemoryVisibility


class NPCMemoryReactionType(StrEnum):
    REMEMBER_EVENT = "remember_event"
    AVOID_ACTOR = "avoid_actor"
    SEEK_ACTOR = "seek_actor"
    REPORT_CRIME = "report_crime"
    SPREAD_KNOWN_RUMOR = "spread_known_rumor"
    INCREASE_SUSPICION = "increase_suspicion"
    SOFTEN_TONE = "soften_tone"
    REFUSE_TALK = "refuse_talk"
    ENQUEUE_INTENT = "enqueue_intent"


class NPCMemoryReactionRule(BaseModel):
    id: str
    reaction_type: NPCMemoryReactionType
    required_tags: list[str] = Field(default_factory=list)
    target_id: str | None = None
    target_type: str | None = None
    intent_type: str | None = None
    priority: int = 0
    suspicion_delta: int = Field(default=1, ge=0)
    mood: str | None = None
    preconditions: list[str] = Field(default_factory=list)


class NPCMemoryReactionResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    triggered_rule_ids: list[str] = Field(default_factory=list)
    skipped_memory_ids: list[str] = Field(default_factory=list)


DEFAULT_MEMORY_REACTION_RULES = [
    NPCMemoryReactionRule(
        id="witnessed-theft-increase-suspicion",
        reaction_type=NPCMemoryReactionType.INCREASE_SUSPICION,
        required_tags=["crime", "theft"],
        suspicion_delta=1,
    ),
    NPCMemoryReactionRule(
        id="known-rumor-spread-intent",
        reaction_type=NPCMemoryReactionType.SPREAD_KNOWN_RUMOR,
        required_tags=["rumor"],
        intent_type="spread_rumor",
        target_type="rumor",
        priority=3,
    ),
    NPCMemoryReactionRule(
        id="relationship-memory-soften-tone",
        reaction_type=NPCMemoryReactionType.SOFTEN_TONE,
        required_tags=["relationship"],
        mood="softened",
    ),
]


def resolve_npc_memory_reactions(
    state: GameState,
    npc_id: str,
    memories: list[MemoryRecord],
    rules: list[NPCMemoryReactionRule] | None = None,
) -> NPCMemoryReactionResult:
    if npc_id not in state.npcs or not can_act(state, npc_id):
        return NPCMemoryReactionResult()
    result = NPCMemoryReactionResult()
    for memory in sorted(memories, key=lambda item: (-item.importance, -item.created_turn, item.id)):
        if not _memory_allowed_for_npc(state, npc_id, memory):
            result.skipped_memory_ids.append(memory.id)
            continue
        for rule in rules or DEFAULT_MEMORY_REACTION_RULES:
            if not _rule_matches_memory(rule, memory):
                continue
            source_id = f"memory:{memory.id}:rule:{rule.id}"
            if _already_reacted(state, npc_id, rule.reaction_type, source_id):
                continue
            deltas = _reaction_deltas(state, npc_id, memory, rule)
            if not deltas:
                continue
            marker = _reaction_marker(npc_id, rule.reaction_type, source_id)
            deltas.append(marker)
            result.state_deltas.extend(deltas)
            result.events.append(_build_reaction_event(state, npc_id, rule, memory, deltas))
            result.triggered_rule_ids.append(rule.id)
    return result


def _reaction_deltas(
    state: GameState,
    npc_id: str,
    memory: MemoryRecord,
    rule: NPCMemoryReactionRule,
) -> list[StateDelta]:
    if rule.reaction_type == NPCMemoryReactionType.INCREASE_SUSPICION:
        return [
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"npcs.{npc_id}.suspicion",
                value=max(1, rule.suspicion_delta),
                reason="NPC memory reaction increased suspicion.",
                metadata=_metadata(npc_id, rule, memory),
            )
        ]
    if rule.reaction_type == NPCMemoryReactionType.SOFTEN_TONE:
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.mood",
                value=rule.mood or "softened",
                reason="NPC memory reaction softened tone.",
                metadata=_metadata(npc_id, rule, memory),
            )
        ]
    if rule.reaction_type == NPCMemoryReactionType.REFUSE_TALK:
        return [
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"npcs.{npc_id}.status_effects",
                value="refuse_talk",
                reason="NPC memory reaction refuses talk.",
                metadata=_metadata(npc_id, rule, memory),
            )
        ]
    if rule.reaction_type in {
        NPCMemoryReactionType.REPORT_CRIME,
        NPCMemoryReactionType.SPREAD_KNOWN_RUMOR,
        NPCMemoryReactionType.AVOID_ACTOR,
        NPCMemoryReactionType.SEEK_ACTOR,
        NPCMemoryReactionType.ENQUEUE_INTENT,
    }:
        intent = _intent_for_rule(state, npc_id, memory, rule)
        if intent is None:
            return []
        queued = enqueue_intent(state, npc_id, intent)
        return queued.state_deltas
    if rule.reaction_type == NPCMemoryReactionType.REMEMBER_EVENT:
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.plan_state.last_remembered_memory_id",
                value=memory.id,
                reason="NPC remembered an allowed memory.",
                metadata=_metadata(npc_id, rule, memory),
            )
        ]
    return []


def _intent_for_rule(
    state: GameState,
    npc_id: str,
    memory: MemoryRecord,
    rule: NPCMemoryReactionRule,
) -> NPCIntent | None:
    intent_type = _intent_type_for_reaction(rule)
    target_id = _target_id_for_reaction(state, npc_id, memory, rule)
    target_type = rule.target_type or _target_type_for_reaction(rule)
    if intent_type is None or target_id is None:
        return None
    preconditions = list(rule.preconditions)
    if intent_type == "report_crime":
        if target_id not in _known_crime_ids(state, npc_id):
            return None
        preconditions.append(f"crime:{target_id}")
    if intent_type == "spread_rumor":
        if target_id not in _known_rumor_ids(state, npc_id):
            return None
        preconditions.append(f"rumor:{target_id}")
    return NPCIntent(
        id=f"memory-{rule.id}-{memory.id}",
        npc_id=npc_id,
        intent_type=intent_type,
        priority=rule.priority,
        target_id=target_id,
        target_type=target_type,
        created_turn=state.turn,
        preconditions=sorted(set(preconditions)),
        debug_reason=f"memory_reaction:{rule.id}",
    )


def _intent_type_for_reaction(rule: NPCMemoryReactionRule) -> str | None:
    if rule.intent_type:
        return rule.intent_type
    mapping = {
        NPCMemoryReactionType.REPORT_CRIME: "report_crime",
        NPCMemoryReactionType.SPREAD_KNOWN_RUMOR: "spread_rumor",
        NPCMemoryReactionType.AVOID_ACTOR: "avoid_actor",
        NPCMemoryReactionType.SEEK_ACTOR: "talk_to_npc",
        NPCMemoryReactionType.ENQUEUE_INTENT: "guard_location",
    }
    return mapping.get(rule.reaction_type)


def _target_type_for_reaction(rule: NPCMemoryReactionRule) -> str | None:
    mapping = {
        NPCMemoryReactionType.REPORT_CRIME: "crime",
        NPCMemoryReactionType.SPREAD_KNOWN_RUMOR: "rumor",
        NPCMemoryReactionType.AVOID_ACTOR: "npc",
        NPCMemoryReactionType.SEEK_ACTOR: "npc",
    }
    return mapping.get(rule.reaction_type)


def _target_id_for_reaction(
    state: GameState,
    npc_id: str,
    memory: MemoryRecord,
    rule: NPCMemoryReactionRule,
) -> str | None:
    if rule.target_id:
        return rule.target_id
    if rule.reaction_type == NPCMemoryReactionType.REPORT_CRIME:
        for crime_id in _known_crime_ids(state, npc_id):
            if crime_id in memory.entity_ids or f"crime:{crime_id}" in memory.tags:
                return crime_id
        return next(iter(_known_crime_ids(state, npc_id)), None)
    if rule.reaction_type == NPCMemoryReactionType.SPREAD_KNOWN_RUMOR:
        for rumor_id in _known_rumor_ids(state, npc_id):
            if rumor_id in memory.entity_ids or f"rumor:{rumor_id}" in memory.tags:
                return rumor_id
        return next(iter(_known_rumor_ids(state, npc_id)), None)
    for entity_id in memory.entity_ids:
        if entity_id != npc_id and entity_id in state.npcs:
            return entity_id
    return None


def _memory_allowed_for_npc(state: GameState, npc_id: str, memory: MemoryRecord) -> bool:
    if memory.visibility in {MemoryVisibility.HIDDEN, MemoryVisibility.DEBUG_ONLY}:
        return False
    for fact_id in memory.fact_ids:
        fact = state.facts.get(fact_id)
        if fact is not None and fact.public:
            continue
        if fact_id in state.player_visible_facts:
            continue
        if not npc_knows(state, npc_id, fact_id) and npc_id not in (fact.known_by if fact else set()):
            return False
    for tag in memory.tags:
        if tag.startswith("crime:") and tag.removeprefix("crime:") not in _known_crime_ids(state, npc_id):
            return False
        if tag.startswith("rumor:") and tag.removeprefix("rumor:") not in _known_rumor_ids(state, npc_id):
            return False
    return True


def _rule_matches_memory(rule: NPCMemoryReactionRule, memory: MemoryRecord) -> bool:
    return set(rule.required_tags).issubset(memory.tags)


def _known_crime_ids(state: GameState, npc_id: str) -> set[str]:
    return {
        crime.id
        for crime in state.crimes.values()
        if npc_id in crime.witnessed_by or npc_knows(state, npc_id, f"crime:{crime.id}")
    }


def _known_rumor_ids(state: GameState, npc_id: str) -> set[str]:
    return {
        rumor.id
        for rumor in state.rumors.values()
        if npc_id in rumor.known_by_npcs
    }


def _metadata(npc_id: str, rule: NPCMemoryReactionRule, memory: MemoryRecord) -> dict[str, str]:
    return {
        "source": "npc_memory_reaction",
        "npc_id": npc_id,
        "reaction": rule.reaction_type.value,
        "rule_id": rule.id,
        "memory_id": memory.id,
    }


def _build_reaction_event(
    state: GameState,
    npc_id: str,
    rule: NPCMemoryReactionRule,
    memory: MemoryRecord,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"npc-memory-reaction-{state.turn}-{npc_id}-{rule.id}-{memory.id}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_memory_reaction",
        target_id=npc_id,
        result=rule.reaction_type.value,
        state_deltas=deltas,
        visible_to_player=False,
    )


def _already_reacted(state: GameState, npc_id: str, reaction: NPCMemoryReactionType, source_id: str) -> bool:
    return state.social_flags.get(_reaction_key(npc_id, reaction, source_id)) is True


def _reaction_marker(npc_id: str, reaction: NPCMemoryReactionType, source_id: str) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_reaction_key(npc_id, reaction, source_id)}",
        value=True,
        reason="NPC memory reaction processed.",
        metadata={"source": "npc_memory_reaction", "npc_id": npc_id, "reaction": reaction.value, "source_id": source_id},
    )


def _reaction_key(npc_id: str, reaction: NPCMemoryReactionType, source_id: str) -> str:
    safe_source = source_id.replace(":", "_").replace("-", "_")
    return f"npc_memory_reaction_{npc_id}_{reaction.value}_{safe_source}"
