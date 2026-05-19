from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.world_state import FactVisibility, GameState
from app.engine.rules.knowledge import npc_knows
from app.llm.memory_store import MemoryRecord, MemoryVisibility


class RoleplayBoundaryConcept(StrEnum):
    AUTHORITATIVE_FACT = "authoritative_fact"
    VISIBLE_FACT = "visible_fact"
    NPC_KNOWN_FACT = "npc_known_fact"
    NARRATOR_SAFE_MEMORY = "narrator_safe_memory"
    RP_FLAVOR = "rp_flavor"
    EMOTIONAL_EXPRESSION = "emotional_expression"
    PROHIBITED_FACT_CREATION = "prohibited_fact_creation"
    DEBUG_ONLY_CONTEXT = "debug_only_context"


class RoleplayContextScope(StrEnum):
    PLAYER = "player"
    NARRATOR = "narrator"
    NPC_DIALOGUE = "npc_dialogue"
    AUTHORING = "authoring"
    DEBUG = "debug"


class RoleplayContextEntry(BaseModel):
    id: str
    concept: RoleplayBoundaryConcept
    content: str
    source: str = ""


class RoleplayExclusion(BaseModel):
    id: str
    concept: RoleplayBoundaryConcept
    reason: str


class RoleplayContext(BaseModel):
    scope: RoleplayContextScope
    actor_id: str = "player"
    npc_id: str | None = None
    entries: list[RoleplayContextEntry] = Field(default_factory=list)
    excluded: list[RoleplayExclusion] = Field(default_factory=list)


class RoleplayOutputIssue(BaseModel):
    code: str
    severity: str = "error"
    message: str
    safe_details: dict[str, str] = Field(default_factory=dict)


class RoleplayOutputCheckResult(BaseModel):
    ok: bool
    issues: list[RoleplayOutputIssue] = Field(default_factory=list)


class RoleplayOutputCandidate(BaseModel):
    text: str
    proposed_fact_creations: list[str] = Field(default_factory=list)
    proposed_state_changes: list[str] = Field(default_factory=list)


class RoleplayContextPolicy(BaseModel):
    """Shared v1.1 policy for RP prompt/context construction.

    This policy is deliberately read-only. It classifies facts, memories, and
    flavor text for later RP modules without mutating GameState or invoking an
    LLM.
    """

    allow_debug_context: bool = False

    def build_context(
        self,
        state: GameState,
        *,
        scope: RoleplayContextScope,
        actor_id: str = "player",
        npc_id: str | None = None,
        fact_ids: list[str] | None = None,
        memories: list[MemoryRecord] | None = None,
        rp_flavor: list[str] | None = None,
        emotional_expression: list[str] | None = None,
    ) -> RoleplayContext:
        context = RoleplayContext(scope=scope, actor_id=actor_id, npc_id=npc_id)
        for fact_id in sorted(set(fact_ids or [])):
            self._add_fact(context, state, fact_id)
        for memory in memories or []:
            self._add_memory(context, state, memory)
        for index, flavor in enumerate(rp_flavor or []):
            context.entries.append(
                RoleplayContextEntry(
                    id=f"rp_flavor:{index}",
                    concept=RoleplayBoundaryConcept.RP_FLAVOR,
                    content=flavor,
                    source="rp_flavor",
                )
            )
        for index, expression in enumerate(emotional_expression or []):
            context.entries.append(
                RoleplayContextEntry(
                    id=f"emotional_expression:{index}",
                    concept=RoleplayBoundaryConcept.EMOTIONAL_EXPRESSION,
                    content=expression,
                    source="emotional_expression",
                )
            )
        return context

    def check_output(
        self,
        candidate: RoleplayOutputCandidate,
    ) -> RoleplayOutputCheckResult:
        issues: list[RoleplayOutputIssue] = []
        for fact_id in candidate.proposed_fact_creations:
            issues.append(
                RoleplayOutputIssue(
                    code=RoleplayBoundaryConcept.PROHIBITED_FACT_CREATION.value,
                    message="RP output attempted to create an authoritative fact.",
                    safe_details={"candidate_id": fact_id},
                )
            )
        for change in candidate.proposed_state_changes:
            issues.append(
                RoleplayOutputIssue(
                    code="prohibited_state_change",
                    message="RP output attempted to declare a canonical state change.",
                    safe_details={"candidate_change": change},
                )
            )
        return RoleplayOutputCheckResult(ok=not issues, issues=issues)

    def _add_fact(self, context: RoleplayContext, state: GameState, fact_id: str) -> None:
        decision = _fact_context_decision(state, context, fact_id)
        if decision is None:
            context.entries.append(
                RoleplayContextEntry(
                    id=fact_id,
                    concept=RoleplayBoundaryConcept.VISIBLE_FACT
                    if context.scope != RoleplayContextScope.NPC_DIALOGUE
                    else RoleplayBoundaryConcept.NPC_KNOWN_FACT,
                    content=fact_id,
                    source="fact",
                )
            )
            return
        context.excluded.append(
            RoleplayExclusion(
                id=fact_id,
                concept=RoleplayBoundaryConcept.AUTHORITATIVE_FACT,
                reason=decision,
            )
        )

    def _add_memory(self, context: RoleplayContext, state: GameState, memory: MemoryRecord) -> None:
        reason = _memory_context_exclusion_reason(state, context, memory, self.allow_debug_context)
        if reason is None:
            context.entries.append(
                RoleplayContextEntry(
                    id=memory.id,
                    concept=RoleplayBoundaryConcept.NARRATOR_SAFE_MEMORY,
                    content=memory.content,
                    source="memory",
                )
            )
            return
        context.excluded.append(
            RoleplayExclusion(
                id=memory.id,
                concept=RoleplayBoundaryConcept.DEBUG_ONLY_CONTEXT
                if memory.visibility == MemoryVisibility.DEBUG_ONLY
                else RoleplayBoundaryConcept.NARRATOR_SAFE_MEMORY,
                reason=reason,
            )
        )


def _fact_context_decision(state: GameState, context: RoleplayContext, fact_id: str) -> str | None:
    fact = state.facts.get(fact_id)
    if fact is None:
        return "unknown_fact"
    if context.scope == RoleplayContextScope.DEBUG and context.actor_id != "player":
        return None
    if context.scope == RoleplayContextScope.NPC_DIALOGUE:
        if not context.npc_id:
            return "missing_npc"
        if npc_knows(state, context.npc_id, fact_id):
            return None
        if fact.visibility == FactVisibility.PUBLIC or fact.public:
            return None
        return "npc_unknown_fact"
    if fact_id in state.player_visible_facts:
        return None
    if fact.visibility == FactVisibility.PUBLIC or fact.public:
        return None
    if fact.visibility == FactVisibility.HIDDEN:
        return "hidden_fact_not_allowed"
    if fact.visibility == FactVisibility.DISCOVERABLE:
        return "undiscovered_fact_not_allowed"
    return "fact_not_allowed"


def _memory_context_exclusion_reason(
    state: GameState,
    context: RoleplayContext,
    memory: MemoryRecord,
    allow_debug_context: bool,
) -> str | None:
    if memory.visibility == MemoryVisibility.DEBUG_ONLY:
        if context.scope == RoleplayContextScope.DEBUG and allow_debug_context:
            return None
        return "debug_memory_not_allowed"
    if memory.visibility == MemoryVisibility.HIDDEN:
        return "hidden_memory_not_allowed"
    if context.scope == RoleplayContextScope.NPC_DIALOGUE:
        if not context.npc_id:
            return "missing_npc"
        for fact_id in memory.fact_ids:
            if _fact_context_decision(state, context, fact_id) is not None:
                return f"npc_memory_unknown_fact:{fact_id}"
        return None
    if memory.visibility not in {MemoryVisibility.NARRATOR_SAFE, MemoryVisibility.PLAYER_VISIBLE}:
        return f"memory_visibility_not_allowed:{memory.visibility}"
    for fact_id in memory.fact_ids:
        fact_decision = _fact_context_decision(state, context, fact_id)
        if fact_decision is not None:
            return f"memory_fact_not_allowed:{fact_id}:{fact_decision}"
    if "source_event_hidden" in memory.tags:
        return "hidden_source_event_not_allowed"
    return None

