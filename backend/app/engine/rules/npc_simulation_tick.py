from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, apply_delta
from app.core.world_state import GameState, NPCPlanStatus
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_conflict_avoidance import resolve_conflict_avoidance
from app.engine.rules.npc_daily_replanning import run_daily_replanning, should_run_daily_replanning_on_tick
from app.engine.rules.npc_faction_duties import duty_to_intent, get_active_duties
from app.engine.rules.npc_intents import prune_expired_intents, select_next_intent
from app.engine.rules.npc_memory_reactions import resolve_npc_memory_reactions
from app.engine.rules.npc_plans import advance_plan, build_plan_from_intent
from app.engine.rules.npc_relationship_behavior import resolve_relationship_behaviors
from app.engine.rules.npc_rumor_decisions import decide_npc_rumor_action
from app.llm.memory_store import MemoryRecord


class NPCSimulationTickBudget(BaseModel):
    max_npcs_per_tick: int = Field(default=10, ge=0)
    max_intents_per_npc: int = Field(default=3, ge=0)
    max_plan_steps_per_tick: int = Field(default=5, ge=0)
    max_events_per_tick: int = Field(default=20, ge=0)


class NPCSimulationTickDebugEntry(BaseModel):
    npc_id: str
    phase: str
    detail: str = ""


class NPCSimulationTickResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    processed_npc_ids: list[str] = Field(default_factory=list)
    skipped_npc_ids: list[str] = Field(default_factory=list)
    debug_output: list[NPCSimulationTickDebugEntry] = Field(default_factory=list)
    budget_exhausted: bool = False


PHASES = [
    "prune_expired_intents",
    "daily_replanning",
    "memory_reactions",
    "relationship_behavior",
    "faction_duties",
    "rumor_decisions",
    "conflict_avoidance",
    "select_intent",
    "build_or_advance_plan",
]


def run_npc_simulation_tick(
    state: GameState,
    *,
    budget: NPCSimulationTickBudget | None = None,
    memories_by_npc: dict[str, list[MemoryRecord]] | None = None,
) -> NPCSimulationTickResult:
    active_budget = budget or NPCSimulationTickBudget()
    working_state = state
    result = NPCSimulationTickResult()
    plan_steps_used = 0

    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if len(result.processed_npc_ids) >= active_budget.max_npcs_per_tick:
            result.budget_exhausted = True
            break
        if not can_act(working_state, npc.id):
            result.skipped_npc_ids.append(npc.id)
            result.debug_output.append(NPCSimulationTickDebugEntry(npc_id=npc.id, phase="skip", detail="npc_inactive"))
            continue

        intent_budget = _IntentBudget(active_budget.max_intents_per_npc)
        result.processed_npc_ids.append(npc.id)

        for phase in PHASES:
            if len(result.events) >= active_budget.max_events_per_tick:
                result.budget_exhausted = True
                break
            if phase == "build_or_advance_plan" and plan_steps_used >= active_budget.max_plan_steps_per_tick:
                result.budget_exhausted = True
                break
            phase_result, plan_step_used = _run_phase(
                working_state,
                npc.id,
                phase,
                memories_by_npc or {},
                intent_budget,
            )
            if phase_result is None:
                result.debug_output.append(NPCSimulationTickDebugEntry(npc_id=npc.id, phase=phase, detail="no_op"))
                continue
            if not _can_accept_phase(result, phase_result, active_budget):
                result.budget_exhausted = True
                break
            result.state_deltas.extend(phase_result.state_deltas)
            result.events.extend(phase_result.events)
            result.debug_output.extend(phase_result.debug_output)
            plan_steps_used += plan_step_used
            for delta in phase_result.state_deltas:
                working_state = apply_delta(working_state, delta)
        if result.budget_exhausted:
            break
    return result


class _IntentBudget:
    def __init__(self, remaining: int) -> None:
        self.remaining = remaining

    def spend_for(self, phase_result: NPCSimulationTickResult) -> bool:
        intent_events = sum(
            1
            for event in phase_result.events
            if any(delta.path.endswith(".intent_queue") for delta in event.state_deltas)
        )
        if intent_events > self.remaining:
            return False
        self.remaining -= intent_events
        return True


def _run_phase(
    state: GameState,
    npc_id: str,
    phase: str,
    memories_by_npc: dict[str, list[MemoryRecord]],
    intent_budget: _IntentBudget,
) -> tuple[NPCSimulationTickResult | None, int]:
    if phase == "prune_expired_intents":
        pruned = prune_expired_intents(state, npc_id)
        return _wrap(npc_id, phase, pruned.state_deltas, pruned.events), 0
    if phase == "daily_replanning":
        if not should_run_daily_replanning_on_tick(state):
            return None, 0
        daily = run_daily_replanning(state, npc_ids=[npc_id])
        return _accept_intents(intent_budget, _wrap(npc_id, phase, daily.state_deltas, daily.events)), 0
    if phase == "memory_reactions":
        memories = memories_by_npc.get(npc_id, [])
        if not memories:
            return None, 0
        memory = resolve_npc_memory_reactions(state, npc_id, memories)
        return _accept_intents(intent_budget, _wrap(npc_id, phase, memory.state_deltas, memory.events)), 0
    if phase == "relationship_behavior":
        target_id = _first_relationship_target(state, npc_id)
        if target_id is None:
            return None, 0
        relationship = resolve_relationship_behaviors(state, npc_id, target_id)
        return _accept_intents(intent_budget, _wrap(npc_id, phase, relationship.state_deltas, relationship.events)), 0
    if phase == "faction_duties":
        return _run_faction_duty_phase(state, npc_id, intent_budget), 0
    if phase == "rumor_decisions":
        return _run_rumor_phase(state, npc_id, intent_budget), 0
    if phase == "conflict_avoidance":
        avoidance = resolve_conflict_avoidance(state, npc_id)
        return _accept_intents(intent_budget, _wrap(npc_id, phase, avoidance.state_deltas, avoidance.events)), 0
    if phase == "select_intent":
        selected = select_next_intent(state, npc_id)
        detail = selected.id if selected is not None else "none"
        return NPCSimulationTickResult(debug_output=[NPCSimulationTickDebugEntry(npc_id=npc_id, phase=phase, detail=detail)]), 0
    if phase == "build_or_advance_plan":
        return _run_plan_phase(state, npc_id)
    return None, 0


def _run_faction_duty_phase(
    state: GameState,
    npc_id: str,
    intent_budget: _IntentBudget,
) -> NPCSimulationTickResult | None:
    for duty in get_active_duties(state, npc_id):
        duty_result = duty_to_intent(state, npc_id, duty)
        wrapped = _wrap(npc_id, "faction_duties", duty_result.state_deltas, duty_result.events)
        if wrapped.state_deltas:
            return _accept_intents(intent_budget, wrapped)
    return None


def _run_rumor_phase(
    state: GameState,
    npc_id: str,
    intent_budget: _IntentBudget,
) -> NPCSimulationTickResult | None:
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if npc_id not in rumor.known_by_npcs:
            continue
        decision = decide_npc_rumor_action(
            state,
            npc_id,
            rumor.id,
            target_actor_id=_first_other_npc(state, npc_id),
            target_faction_id=state.npcs[npc_id].faction_id,
        )
        wrapped = _wrap(npc_id, "rumor_decisions", decision.state_deltas, decision.events)
        if wrapped.state_deltas:
            return _accept_intents(intent_budget, wrapped)
    return None


def _run_plan_phase(state: GameState, npc_id: str) -> tuple[NPCSimulationTickResult | None, int]:
    plan = _first_open_plan(state, npc_id)
    if plan is not None:
        advanced = advance_plan(state, npc_id, plan.id)
        return _wrap(npc_id, "build_or_advance_plan", advanced.state_deltas, advanced.events), 1
    selected = select_next_intent(state, npc_id)
    if selected is None:
        return None, 0
    built = build_plan_from_intent(state, npc_id, selected)
    return _wrap(npc_id, "build_or_advance_plan", built.state_deltas, built.events), 0


def _wrap(
    npc_id: str,
    phase: str,
    state_deltas: list[StateDelta],
    events: list[Event],
) -> NPCSimulationTickResult:
    detail = f"deltas={len(state_deltas)} events={len(events)}"
    return NPCSimulationTickResult(
        state_deltas=state_deltas,
        events=events,
        debug_output=[NPCSimulationTickDebugEntry(npc_id=npc_id, phase=phase, detail=detail)],
    )


def _accept_intents(
    intent_budget: _IntentBudget,
    phase_result: NPCSimulationTickResult,
) -> NPCSimulationTickResult | None:
    if not intent_budget.spend_for(phase_result):
        return NPCSimulationTickResult(
            budget_exhausted=True,
            debug_output=[
                NPCSimulationTickDebugEntry(npc_id="system", phase="budget", detail="max_intents_per_npc")
            ],
        )
    return phase_result


def _can_accept_phase(
    current: NPCSimulationTickResult,
    phase_result: NPCSimulationTickResult,
    budget: NPCSimulationTickBudget,
) -> bool:
    if phase_result.budget_exhausted:
        return False
    return len(current.events) + len(phase_result.events) <= budget.max_events_per_tick


def _first_relationship_target(state: GameState, npc_id: str) -> str | None:
    for relationship in sorted(state.relationships.values(), key=lambda item: item.id):
        if relationship.source_id == npc_id:
            return relationship.target_id
    return None


def _first_other_npc(state: GameState, npc_id: str) -> str | None:
    for other_id in sorted(state.npcs):
        if other_id != npc_id:
            return other_id
    return None


def _first_open_plan(state: GameState, npc_id: str):
    for plan in sorted(state.npcs[npc_id].plans, key=lambda item: (item.created_turn, item.id)):
        if plan.status in {NPCPlanStatus.PLANNED, NPCPlanStatus.ACTIVE}:
            return plan
    return None
