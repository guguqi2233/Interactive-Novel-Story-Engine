from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    GameState,
    NPCIntent,
    NPCPlan,
    NPCPlanStatus,
    NPCPlanStep,
    NPCPlanStepStatus,
    NPCPlanStepType,
)
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_planning import NPCPlanStep as RuntimeNPCPlanStep
from app.engine.rules.npc_planning import resolve_plan_step
from app.engine.rules.npc_simulation_boundary import NPCSimulationPolicy


class NPCPlanRuleError(ValueError):
    """Raised when NPC short-term plan rules cannot resolve a request."""


class NPCPlanRuleResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    plan: NPCPlan | None = None
    rejected_reason: str | None = None


ALLOWED_STEP_TYPES = {
    NPCPlanStepType.MOVE,
    NPCPlanStepType.TALK,
    NPCPlanStepType.REPORT,
    NPCPlanStepType.SPREAD_RUMOR,
    NPCPlanStepType.REST,
    NPCPlanStepType.GUARD,
    NPCPlanStepType.AVOID,
    NPCPlanStepType.SEEK_ITEM,
}

MAX_PLAN_STEPS = 3


def build_plan_from_intent(state: GameState, npc_id: str, intent: NPCIntent) -> NPCPlanRuleResult:
    _get_npc(state, npc_id)
    if intent.npc_id != npc_id:
        return NPCPlanRuleResult(rejected_reason="intent_npc_mismatch")
    if not can_act(state, npc_id):
        return NPCPlanRuleResult(rejected_reason="npc_inactive")

    steps = _steps_for_intent(intent)
    status = NPCPlanStatus.PLANNED
    if not steps:
        status = NPCPlanStatus.BLOCKED
    plan = NPCPlan(
        id=f"plan-{intent.id}",
        npc_id=npc_id,
        source_intent_id=intent.id,
        goal_id=intent.source_goal_id,
        status=status,
        steps=steps,
        created_turn=state.turn,
        expires_turn=intent.expires_turn,
    )
    validation = validate_plan(state, plan)
    if validation.rejected_reason is not None:
        plan = plan.model_copy(update={"status": NPCPlanStatus.BLOCKED})

    queue = [*state.npcs[npc_id].plans, plan]
    deltas = [_set_plans_delta(npc_id, queue, "NPC short-term plan built.", {"plan_id": plan.id, "status": plan.status.value})]
    return NPCPlanRuleResult(
        state_deltas=deltas,
        events=[_build_plan_event(state, npc_id, "npc_plan_built", plan, deltas)],
        plan=plan,
        rejected_reason=validation.rejected_reason,
    )


def validate_plan(state: GameState, plan: NPCPlan) -> NPCPlanRuleResult:
    if plan.npc_id not in state.npcs:
        return NPCPlanRuleResult(plan=plan, rejected_reason="npc_missing")
    if len(plan.steps) > MAX_PLAN_STEPS:
        return NPCPlanRuleResult(plan=plan, rejected_reason="plan_step_limit")
    if plan.expires_turn is not None and plan.expires_turn <= state.turn:
        return NPCPlanRuleResult(plan=plan, rejected_reason="plan_expired")
    known = NPCSimulationPolicy().build_context(state, plan.npc_id).npc_known_context
    for step in plan.steps:
        if step.step_type not in ALLOWED_STEP_TYPES:
            return NPCPlanRuleResult(plan=plan, rejected_reason="step_type_forbidden")
        target_issue = _target_rejection_reason(state, step)
        if target_issue is not None:
            return NPCPlanRuleResult(plan=plan, rejected_reason=target_issue)
        for precondition in step.preconditions:
            if precondition.startswith("fact:") and precondition.removeprefix("fact:") not in known.fact_ids:
                return NPCPlanRuleResult(plan=plan, rejected_reason="npc_unknown_fact")
            if precondition.startswith("rumor:") and precondition.removeprefix("rumor:") not in known.rumor_ids:
                return NPCPlanRuleResult(plan=plan, rejected_reason="npc_unknown_rumor")
            if precondition.startswith("crime:") and precondition.removeprefix("crime:") not in known.crime_ids:
                return NPCPlanRuleResult(plan=plan, rejected_reason="npc_unknown_crime")
    return NPCPlanRuleResult(plan=plan)


def advance_plan(state: GameState, npc_id: str, plan_id: str) -> NPCPlanRuleResult:
    npc = _get_npc(state, npc_id)
    plan = _find_plan(npc.plans, plan_id)
    if not can_act(state, npc_id):
        return _update_plan(state, npc_id, plan, plan.model_copy(update={"status": NPCPlanStatus.BLOCKED}), "npc_plan_blocked")
    validation = validate_plan(state, plan)
    if validation.rejected_reason is not None:
        return _update_plan(state, npc_id, plan, plan.model_copy(update={"status": NPCPlanStatus.BLOCKED}), "npc_plan_blocked")
    if plan.status in {NPCPlanStatus.COMPLETED, NPCPlanStatus.FAILED, NPCPlanStatus.CANCELLED, NPCPlanStatus.BLOCKED}:
        return NPCPlanRuleResult(plan=plan, rejected_reason=f"plan_{plan.status.value}")
    if plan.current_step_index >= len(plan.steps):
        return _update_plan(state, npc_id, plan, plan.model_copy(update={"status": NPCPlanStatus.COMPLETED}), "npc_plan_completed")

    step = plan.steps[plan.current_step_index]
    runtime_step = _runtime_step_from_plan(state, plan, step)
    effect_deltas = resolve_plan_step(state, runtime_step)
    if not effect_deltas:
        failed_step = step.model_copy(update={"status": NPCPlanStepStatus.BLOCKED})
        blocked_plan = _replace_step(plan, failed_step).model_copy(update={"status": NPCPlanStatus.BLOCKED})
        return _update_plan(state, npc_id, plan, blocked_plan, "npc_plan_blocked")

    completed_step = step.model_copy(update={"status": NPCPlanStepStatus.COMPLETED})
    next_index = plan.current_step_index + 1
    next_status = NPCPlanStatus.COMPLETED if next_index >= len(plan.steps) else NPCPlanStatus.ACTIVE
    updated_plan = _replace_step(plan, completed_step).model_copy(
        update={"status": next_status, "current_step_index": next_index}
    )
    queue = [updated_plan if existing.id == plan.id else existing for existing in npc.plans]
    plan_delta = _set_plans_delta(npc_id, queue, "NPC short-term plan advanced.", {"plan_id": plan.id, "status": next_status.value})
    deltas = [*effect_deltas, plan_delta]
    return NPCPlanRuleResult(
        state_deltas=deltas,
        events=[_build_plan_event(state, npc_id, "npc_plan_advanced", updated_plan, deltas)],
        plan=updated_plan,
    )


def cancel_plan(state: GameState, npc_id: str, plan_id: str) -> NPCPlanRuleResult:
    plan = _find_plan(_get_npc(state, npc_id).plans, plan_id)
    return _update_plan(state, npc_id, plan, plan.model_copy(update={"status": NPCPlanStatus.CANCELLED}), "npc_plan_cancelled")


def fail_plan(state: GameState, npc_id: str, plan_id: str) -> NPCPlanRuleResult:
    plan = _find_plan(_get_npc(state, npc_id).plans, plan_id)
    return _update_plan(state, npc_id, plan, plan.model_copy(update={"status": NPCPlanStatus.FAILED}), "npc_plan_failed")


def _steps_for_intent(intent: NPCIntent) -> list[NPCPlanStep]:
    common = {"preconditions": intent.preconditions}
    if intent.intent_type == "report_crime":
        return [NPCPlanStep(step_type=NPCPlanStepType.REPORT, target_id=intent.target_id, expected_result="crime_reported", **common)]
    if intent.intent_type == "visit_location":
        return [NPCPlanStep(step_type=NPCPlanStepType.MOVE, target_id=intent.target_id, expected_result="npc_moved", **common)]
    if intent.intent_type == "spread_rumor":
        return [NPCPlanStep(step_type=NPCPlanStepType.SPREAD_RUMOR, target_id=intent.target_id, expected_result="rumor_spread", **common)]
    if intent.intent_type == "talk_to_npc":
        return [NPCPlanStep(step_type=NPCPlanStepType.TALK, target_id=intent.target_id, expected_result="conversation_started", **common)]
    if intent.intent_type == "guard_location":
        return [NPCPlanStep(step_type=NPCPlanStepType.GUARD, target_id=intent.target_id, expected_result="location_guarded", **common)]
    if intent.intent_type == "rest":
        return [NPCPlanStep(step_type=NPCPlanStepType.REST, target_id=intent.target_id, expected_result="npc_rested", **common)]
    if intent.intent_type == "avoid_actor":
        return [NPCPlanStep(step_type=NPCPlanStepType.AVOID, target_id=intent.target_id, expected_result="npc_avoided_threat", **common)]
    if intent.intent_type == "seek_item":
        return [NPCPlanStep(step_type=NPCPlanStepType.SEEK_ITEM, target_id=intent.target_id, expected_result="item_sought", **common)]
    return []


def _runtime_step_from_plan(state: GameState, plan: NPCPlan, step: NPCPlanStep) -> RuntimeNPCPlanStep:
    mapping = {
        NPCPlanStepType.MOVE: "move_to_location",
        NPCPlanStepType.TALK: "talk_to_npc",
        NPCPlanStepType.REPORT: "report_crime",
        NPCPlanStepType.SPREAD_RUMOR: "spread_rumor",
        NPCPlanStepType.REST: "rest_if_injured",
        NPCPlanStepType.GUARD: "guard_location",
        NPCPlanStepType.AVOID: "flee_location",
    }
    return RuntimeNPCPlanStep(
        npc_id=plan.npc_id,
        goal_id=plan.goal_id,
        plan_type=mapping.get(step.step_type, "seek_item"),
        target_id=step.target_id,
        reason_code=f"intent:{plan.source_intent_id}",
        visible_to_player=_npc_visible_to_player(state, plan.npc_id),
    )


def _target_rejection_reason(state: GameState, step: NPCPlanStep) -> str | None:
    if step.step_type == NPCPlanStepType.MOVE and step.target_id not in state.locations:
        return "target_location_missing"
    if step.step_type == NPCPlanStepType.TALK and step.target_id not in state.npcs:
        return "target_npc_missing"
    if step.step_type == NPCPlanStepType.REPORT and step.target_id not in state.crimes:
        return "target_crime_missing"
    if step.step_type == NPCPlanStepType.SPREAD_RUMOR and step.target_id not in state.rumors:
        return "target_rumor_missing"
    if step.step_type == NPCPlanStepType.SEEK_ITEM and step.target_id not in state.objects:
        return "target_item_missing"
    return None


def _replace_step(plan: NPCPlan, step: NPCPlanStep) -> NPCPlan:
    steps = list(plan.steps)
    steps[plan.current_step_index] = step
    return plan.model_copy(update={"steps": steps})


def _update_plan(
    state: GameState,
    npc_id: str,
    before: NPCPlan,
    after: NPCPlan,
    action_type: str,
) -> NPCPlanRuleResult:
    npc = _get_npc(state, npc_id)
    queue = [after if plan.id == before.id else plan for plan in npc.plans]
    deltas = [_set_plans_delta(npc_id, queue, "NPC short-term plan status changed.", {"plan_id": after.id, "status": after.status.value})]
    return NPCPlanRuleResult(
        state_deltas=deltas,
        events=[_build_plan_event(state, npc_id, action_type, after, deltas)],
        plan=after,
    )


def _find_plan(plans: list[NPCPlan], plan_id: str) -> NPCPlan:
    for plan in plans:
        if plan.id == plan_id:
            return plan
    raise NPCPlanRuleError(f"NPC plan not found: {plan_id}")


def _get_npc(state: GameState, npc_id: str):
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise NPCPlanRuleError(f"NPC not found: {npc_id}")
    return npc


def _set_plans_delta(npc_id: str, plans: list[NPCPlan], reason: str, metadata: dict[str, str]) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"npcs.{npc_id}.plans",
        value=[plan.model_dump(mode="json") for plan in plans],
        reason=reason,
        metadata={"source": "npc_plan", "npc_id": npc_id, **metadata},
    )


def _build_plan_event(
    state: GameState,
    npc_id: str,
    action_type: str,
    plan: NPCPlan,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"{action_type}-{state.turn}-{npc_id}-{plan.id}",
        turn=state.turn,
        actor_id="system",
        action_type=action_type,
        target_id=npc_id,
        result=plan.status.value,
        state_deltas=deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in deltas),
    )


def _npc_visible_to_player(state: GameState, npc_id: str) -> bool:
    npc = state.npcs[npc_id]
    return npc.location_id == state.player.location_id and npc.visible and (not npc.hidden or state.player.id in npc.discovered_by)
