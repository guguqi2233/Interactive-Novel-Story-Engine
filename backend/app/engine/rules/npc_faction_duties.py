from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    GameState,
    NPCFactionDuty,
    NPCFactionDutyStatus,
    NPCFactionDutyType,
    NPCIntent,
    NPCPlan,
)
from app.engine.rules.factions import ReputationBand, reputation_band
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_intents import enqueue_intent
from app.engine.rules.npc_plans import build_plan_from_intent
from app.engine.rules.npc_simulation_boundary import NPCSimulationPolicy


class NPCFactionDutyRuleError(ValueError):
    """Raised when NPC faction duty rules cannot resolve a request."""


class NPCFactionDutyResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    duty: NPCFactionDuty | None = None
    intent: NPCIntent | None = None
    plan: NPCPlan | None = None
    rejected_reason: str | None = None


def get_active_duties(state: GameState, npc_id: str) -> list[NPCFactionDuty]:
    npc = _get_npc(state, npc_id)
    if not can_act(state, npc_id):
        return []
    return [
        duty
        for duty in sorted(npc.faction_duties, key=lambda item: (-item.priority, item.created_turn, item.id))
        if duty.status == NPCFactionDutyStatus.ACTIVE and not _is_expired(state, duty)
    ]


def duty_preconditions_met(state: GameState, npc_id: str, duty: NPCFactionDuty) -> NPCFactionDutyResult:
    npc = _get_npc(state, npc_id)
    if not can_act(state, npc_id):
        return NPCFactionDutyResult(duty=duty, rejected_reason="npc_inactive")
    if npc.faction_id is None:
        return NPCFactionDutyResult(duty=duty, rejected_reason="npc_missing_faction")
    if duty.faction_id is not None and duty.faction_id != npc.faction_id:
        return NPCFactionDutyResult(duty=duty, rejected_reason="duty_faction_mismatch")
    if npc.faction_id not in state.factions:
        return NPCFactionDutyResult(duty=duty, rejected_reason="faction_missing")
    if _is_expired(state, duty):
        return NPCFactionDutyResult(duty=duty, rejected_reason="duty_expired")
    if state.social_flags.get(_duty_key(npc_id, duty.id)) is True:
        return NPCFactionDutyResult(duty=duty, rejected_reason="duty_already_generated")
    target_issue = _target_rejection_reason(state, npc_id, duty)
    if target_issue is not None:
        return NPCFactionDutyResult(duty=duty, rejected_reason=target_issue)
    known = NPCSimulationPolicy().build_context(state, npc_id).npc_known_context
    if not set(duty.required_fact_ids).issubset(known.fact_ids):
        return NPCFactionDutyResult(duty=duty, rejected_reason="npc_unknown_fact")
    if not set(duty.required_rumor_ids).issubset(known.rumor_ids):
        return NPCFactionDutyResult(duty=duty, rejected_reason="npc_unknown_rumor")
    if not set(duty.required_crime_ids).issubset(known.crime_ids):
        return NPCFactionDutyResult(duty=duty, rejected_reason="npc_unknown_crime")
    if duty.duty_type == NPCFactionDutyType.REFUSE_HOSTILE_ACTOR:
        band = reputation_band(state.factions[npc.faction_id].reputation.value)
        if band != ReputationBand.HOSTILE:
            return NPCFactionDutyResult(duty=duty, rejected_reason="faction_not_hostile")
    return NPCFactionDutyResult(duty=duty)


def duty_to_intent(state: GameState, npc_id: str, duty: NPCFactionDuty) -> NPCFactionDutyResult:
    preconditions = duty_preconditions_met(state, npc_id, duty)
    if preconditions.rejected_reason is not None:
        return preconditions
    intent = _intent_for_duty(state, npc_id, duty)
    if intent is None:
        return NPCFactionDutyResult(duty=duty, rejected_reason="duty_no_intent")
    queued = enqueue_intent(state, npc_id, intent)
    if queued.rejected_reason is not None:
        return NPCFactionDutyResult(duty=duty, intent=intent, rejected_reason=queued.rejected_reason)
    marker = _duty_marker(npc_id, duty)
    deltas = [*queued.state_deltas, marker]
    return NPCFactionDutyResult(
        state_deltas=deltas,
        events=[_build_duty_event(state, npc_id, duty, intent, deltas)],
        duty=duty,
        intent=queued.selected_intent,
    )


def duty_to_plan(state: GameState, npc_id: str, duty: NPCFactionDuty) -> NPCFactionDutyResult:
    intent_result = duty_to_intent(state, npc_id, duty)
    if intent_result.rejected_reason is not None or intent_result.intent is None:
        return intent_result
    working_state = state
    for delta in intent_result.state_deltas:
        if delta.path.startswith(f"npcs.{npc_id}.intent_queue"):
            # Build a plan against a transient queue state without mutating the caller.
            from app.core.state_delta import apply_delta

            working_state = apply_delta(working_state, delta)
    plan_result = build_plan_from_intent(working_state, npc_id, intent_result.intent)
    return NPCFactionDutyResult(
        state_deltas=[*intent_result.state_deltas, *plan_result.state_deltas],
        events=[*intent_result.events, *plan_result.events],
        duty=duty,
        intent=intent_result.intent,
        plan=plan_result.plan,
        rejected_reason=plan_result.rejected_reason,
    )


def _intent_for_duty(state: GameState, npc_id: str, duty: NPCFactionDuty) -> NPCIntent | None:
    intent_type = _intent_type_for_duty(duty)
    target_id = _target_for_duty(state, npc_id, duty)
    if intent_type is None or target_id is None:
        return None
    preconditions = [f"fact:{fact_id}" for fact_id in duty.required_fact_ids]
    preconditions.extend(f"rumor:{rumor_id}" for rumor_id in duty.required_rumor_ids)
    preconditions.extend(f"crime:{crime_id}" for crime_id in duty.required_crime_ids)
    return NPCIntent(
        id=f"faction-duty-{duty.id}",
        npc_id=npc_id,
        intent_type=intent_type,
        priority=duty.priority,
        target_id=target_id,
        target_type=_target_type_for_intent(intent_type),
        created_turn=state.turn,
        expires_turn=duty.expires_turn,
        preconditions=sorted(set(preconditions)),
        debug_reason=f"faction_duty:{duty.id}",
    )


def _intent_type_for_duty(duty: NPCFactionDuty) -> str | None:
    return {
        NPCFactionDutyType.GUARD_LOCATION: "guard_location",
        NPCFactionDutyType.PATROL_ROUTE: "visit_location",
        NPCFactionDutyType.REPORT_CRIME_TO_FACTION: "report_crime",
        NPCFactionDutyType.PROTECT_FACTION_MEMBER: "protect_faction_member",
        NPCFactionDutyType.REFUSE_HOSTILE_ACTOR: "refuse_hostile_actor",
        NPCFactionDutyType.SPREAD_FACTION_RUMOR: "spread_rumor",
        NPCFactionDutyType.SEEK_INFORMATION: "seek_information",
        NPCFactionDutyType.ENFORCE_CURFEW: "enforce_curfew",
    }.get(duty.duty_type)


def _target_for_duty(state: GameState, npc_id: str, duty: NPCFactionDuty) -> str | None:
    if duty.duty_type == NPCFactionDutyType.PATROL_ROUTE:
        return duty.route_location_ids[0] if duty.route_location_ids else duty.target_id
    if duty.duty_type == NPCFactionDutyType.REPORT_CRIME_TO_FACTION:
        if duty.target_id:
            return duty.target_id
        known = NPCSimulationPolicy().build_context(state, npc_id).npc_known_context.crime_ids
        return known[0] if known else None
    if duty.duty_type == NPCFactionDutyType.SPREAD_FACTION_RUMOR:
        if duty.target_id:
            return duty.target_id
        known = NPCSimulationPolicy().build_context(state, npc_id).npc_known_context.rumor_ids
        return known[0] if known else None
    if duty.duty_type == NPCFactionDutyType.REFUSE_HOSTILE_ACTOR:
        return duty.target_id or state.player.id
    if duty.duty_type == NPCFactionDutyType.GUARD_LOCATION:
        return duty.target_id or state.npcs[npc_id].location_id
    return duty.target_id


def _target_type_for_intent(intent_type: str) -> str:
    return {
        "guard_location": "location",
        "visit_location": "location",
        "report_crime": "crime",
        "spread_rumor": "rumor",
        "protect_faction_member": "npc",
        "refuse_hostile_actor": "npc",
        "seek_information": "fact",
        "enforce_curfew": "location",
    }.get(intent_type, "npc")


def _target_rejection_reason(state: GameState, npc_id: str, duty: NPCFactionDuty) -> str | None:
    target = _target_for_duty(state, npc_id, duty)
    if duty.duty_type in {NPCFactionDutyType.GUARD_LOCATION, NPCFactionDutyType.PATROL_ROUTE, NPCFactionDutyType.ENFORCE_CURFEW}:
        ids = duty.route_location_ids if duty.duty_type == NPCFactionDutyType.PATROL_ROUTE else [target]
        if any(location_id not in state.locations for location_id in ids if location_id):
            return "target_location_missing"
    if duty.duty_type == NPCFactionDutyType.REPORT_CRIME_TO_FACTION and target not in state.crimes:
        return "target_crime_missing"
    if duty.duty_type == NPCFactionDutyType.SPREAD_FACTION_RUMOR and target not in state.rumors:
        return "target_rumor_missing"
    if duty.duty_type == NPCFactionDutyType.PROTECT_FACTION_MEMBER:
        if target not in state.npcs:
            return "target_npc_missing"
        if state.npcs[target].faction_id != state.npcs[npc_id].faction_id:
            return "target_not_faction_member"
    return None


def _is_expired(state: GameState, duty: NPCFactionDuty) -> bool:
    return duty.expires_turn is not None and duty.expires_turn <= state.turn


def _get_npc(state: GameState, npc_id: str):
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise NPCFactionDutyRuleError(f"NPC not found: {npc_id}")
    return npc


def _duty_marker(npc_id: str, duty: NPCFactionDuty) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_duty_key(npc_id, duty.id)}",
        value=True,
        reason="NPC faction duty generated a bounded intent.",
        metadata={"source": "npc_faction_duty", "npc_id": npc_id, "duty_id": duty.id},
    )


def _build_duty_event(
    state: GameState,
    npc_id: str,
    duty: NPCFactionDuty,
    intent: NPCIntent,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"npc-faction-duty-{state.turn}-{npc_id}-{duty.id}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_faction_duty",
        target_id=npc_id,
        result=intent.intent_type,
        state_deltas=deltas,
        visible_to_player=False,
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )


def _duty_key(npc_id: str, duty_id: str) -> str:
    return f"npc_faction_duty_{npc_id}_{duty_id.replace(':', '_').replace('-', '_')}"
