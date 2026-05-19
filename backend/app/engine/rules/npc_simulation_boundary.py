from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.world_state import FactVisibility, GameState
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.life_state import can_act
from app.engine.rules.visibility import get_visible_facts


class NPCSimulationBoundaryError(ValueError):
    """Raised when an NPC simulation boundary check cannot be resolved."""


class NPCSimulationIssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class NPCSimulationIssue(BaseModel):
    code: str
    message: str
    severity: NPCSimulationIssueSeverity = NPCSimulationIssueSeverity.ERROR
    ref_id: str | None = None


class NPCSimulationCheckResult(BaseModel):
    allowed: bool
    issues: list[NPCSimulationIssue] = Field(default_factory=list)

    @classmethod
    def allow(cls) -> "NPCSimulationCheckResult":
        return cls(allowed=True)

    @classmethod
    def block(cls, *issues: NPCSimulationIssue) -> "NPCSimulationCheckResult":
        return cls(allowed=False, issues=list(issues))


class NPCKnownContext(BaseModel):
    npc_id: str
    fact_ids: list[str] = Field(default_factory=list)
    rumor_ids: list[str] = Field(default_factory=list)
    crime_ids: list[str] = Field(default_factory=list)


class NPCVisibleContext(BaseModel):
    npc_id: str
    location_id: str
    visible_entity_ids: list[str] = Field(default_factory=list)


class NPCPrivateState(BaseModel):
    npc_id: str
    mood: str
    condition: str
    current_goal_id: str | None = None
    current_activity: str | None = None
    plan_state_keys: list[str] = Field(default_factory=list)


class NPCSimulationContext(BaseModel):
    npc_known_context: NPCKnownContext
    npc_visible_context: NPCVisibleContext
    npc_private_state: NPCPrivateState


class SimulationCandidateAction(BaseModel):
    npc_id: str
    action_type: str
    target_id: str | None = None
    required_fact_ids: list[str] = Field(default_factory=list)
    reason_code: str = "rule_candidate"
    visible_to_player: bool = False


class SimulationIntent(BaseModel):
    npc_id: str
    intent_type: str
    candidate_action: SimulationCandidateAction
    priority: int = 0
    source: str = "npc_simulation"


class SimulationPlan(BaseModel):
    npc_id: str
    intents: list[SimulationIntent] = Field(default_factory=list)
    max_steps: int = Field(default=3, ge=1)
    stop_reason: str | None = None


class SimulationEvent(BaseModel):
    event: Event
    debug_only: bool = False


class DebugOnlySimulationData(BaseModel):
    npc_id: str
    trace_id: str | None = None
    redacted: bool = True
    hidden_fact_ids: list[str] = Field(default_factory=list)
    blocked_reason_codes: list[str] = Field(default_factory=list)


class NPCSimulationPolicy(BaseModel):
    allowed_action_types: set[str] = Field(
        default_factory=lambda: {
            "choose_goal",
            "queue_intent",
            "move_to_location",
            "talk_to_npc",
            "report_crime",
            "spread_rumor",
            "flee_location",
            "guard_location",
            "rest_if_injured",
            "avoid_conflict",
            "execute_faction_duty",
        }
    )
    max_candidate_actions: int = Field(default=12, ge=1)
    max_plan_steps: int = Field(default=3, ge=1)
    require_state_delta_effects: bool = True
    require_event_record: bool = True
    allow_llm_planning: bool = False
    allow_external_network: bool = False
    block_inactive_npcs: bool = True

    def build_context(self, state: GameState, npc_id: str) -> NPCSimulationContext:
        npc = state.npcs.get(npc_id)
        if npc is None:
            raise NPCSimulationBoundaryError(f"NPC not found: {npc_id}")

        known_fact_ids = [
            fact_id
            for fact_id in sorted(state.facts)
            if self._fact_available_to_npc(state, npc_id, fact_id)
        ]
        known_rumor_ids = [
            rumor.id
            for rumor in sorted(state.rumors.values(), key=lambda item: item.id)
            if npc_id in rumor.known_by_npcs
        ]
        known_crime_ids = [
            crime.id
            for crime in sorted(state.crimes.values(), key=lambda item: item.id)
            if npc_id in crime.witnessed_by or npc_knows(state, npc_id, f"crime:{crime.id}")
        ]
        visible_entity_ids = sorted(set(get_visible_facts(state, npc_id, npc.location_id)))
        return NPCSimulationContext(
            npc_known_context=NPCKnownContext(
                npc_id=npc_id,
                fact_ids=known_fact_ids,
                rumor_ids=known_rumor_ids,
                crime_ids=known_crime_ids,
            ),
            npc_visible_context=NPCVisibleContext(
                npc_id=npc_id,
                location_id=npc.location_id,
                visible_entity_ids=visible_entity_ids,
            ),
            npc_private_state=NPCPrivateState(
                npc_id=npc_id,
                mood=npc.mood,
                condition=npc.condition.value,
                current_goal_id=npc.current_goal_id,
                current_activity=npc.current_activity,
                plan_state_keys=sorted(npc.plan_state.keys()),
            ),
        )

    def can_simulate_npc(self, state: GameState, npc_id: str) -> NPCSimulationCheckResult:
        if npc_id not in state.npcs:
            return NPCSimulationCheckResult.block(
                NPCSimulationIssue(
                    code="npc_missing",
                    message="NPC does not exist.",
                    ref_id=npc_id,
                )
            )
        if self.block_inactive_npcs and not can_act(state, npc_id):
            return NPCSimulationCheckResult.block(
                NPCSimulationIssue(
                    code="npc_inactive",
                    message="Dead, incapacitated, or stunned NPCs cannot run ordinary simulation.",
                    ref_id=npc_id,
                )
            )
        return NPCSimulationCheckResult.allow()

    def validate_candidate_action(
        self,
        state: GameState,
        context: NPCSimulationContext,
        candidate: SimulationCandidateAction,
    ) -> NPCSimulationCheckResult:
        issues: list[NPCSimulationIssue] = []
        if candidate.npc_id != context.npc_known_context.npc_id:
            issues.append(
                NPCSimulationIssue(
                    code="context_npc_mismatch",
                    message="Candidate action is not scoped to the provided NPC context.",
                    ref_id=candidate.npc_id,
                )
            )
        lifecycle = self.can_simulate_npc(state, candidate.npc_id)
        issues.extend(lifecycle.issues)
        if candidate.action_type not in self.allowed_action_types:
            issues.append(
                NPCSimulationIssue(
                    code="action_type_forbidden",
                    message="Candidate action type is not permitted by NPC simulation policy.",
                    ref_id=candidate.action_type,
                )
            )
        known_facts = set(context.npc_known_context.fact_ids)
        for fact_id in candidate.required_fact_ids:
            if fact_id not in known_facts:
                issues.append(
                    NPCSimulationIssue(
                        code="npc_unknown_fact",
                        message="Candidate action references a fact outside the NPC known context.",
                        ref_id=fact_id,
                    )
                )
        return NPCSimulationCheckResult(allowed=not issues, issues=issues)

    def validate_plan(
        self,
        state: GameState,
        context: NPCSimulationContext,
        plan: SimulationPlan,
    ) -> NPCSimulationCheckResult:
        issues: list[NPCSimulationIssue] = []
        if plan.npc_id != context.npc_known_context.npc_id:
            issues.append(
                NPCSimulationIssue(
                    code="plan_npc_mismatch",
                    message="Simulation plan is not scoped to the provided NPC context.",
                    ref_id=plan.npc_id,
                )
            )
        if len(plan.intents) > min(plan.max_steps, self.max_plan_steps):
            issues.append(
                NPCSimulationIssue(
                    code="plan_step_limit",
                    message="Simulation plan exceeds the finite step budget.",
                    ref_id=plan.npc_id,
                )
            )
        for intent in plan.intents:
            candidate_result = self.validate_candidate_action(state, context, intent.candidate_action)
            issues.extend(candidate_result.issues)
        return NPCSimulationCheckResult(allowed=not issues, issues=issues)

    def validate_simulation_event(self, simulation_event: SimulationEvent) -> NPCSimulationCheckResult:
        if self.require_event_record and not simulation_event.event.event_id:
            return NPCSimulationCheckResult.block(
                NPCSimulationIssue(
                    code="event_missing",
                    message="Simulation behavior must be represented by an Event.",
                )
            )
        if self.require_state_delta_effects and not simulation_event.event.state_deltas:
            return NPCSimulationCheckResult.block(
                NPCSimulationIssue(
                    code="event_missing_state_delta",
                    message="Simulation events that change state must record StateDelta entries.",
                    ref_id=simulation_event.event.event_id,
                )
            )
        return NPCSimulationCheckResult.allow()

    def _fact_available_to_npc(self, state: GameState, npc_id: str, fact_id: str) -> bool:
        fact = state.facts.get(fact_id)
        if fact is None:
            return False
        if fact.public or fact.visibility == FactVisibility.PUBLIC:
            return True
        return npc_knows(state, npc_id, fact_id) or npc_id in fact.known_by
