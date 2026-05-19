from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    NPCFactionDuty,
    NPCFactionDutyStatus,
    NPCFactionDutyType,
    NPCGoalStatus,
    NPCIntent,
    NPCPlan,
    NPCPlanStatus,
)
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_goals import choose_goal
from app.engine.rules.npc_intents import enqueue_intent, prune_expired_intents
from app.engine.rules.npc_plans import validate_plan


class DailyReplanningTrigger(StrEnum):
    NEW_DAY = "new_day"
    MAJOR_EVENT = "major_event"
    GOAL_COMPLETED = "goal_completed"
    GOAL_FAILED = "goal_failed"
    SCHEDULE_CHANGE = "schedule_change"
    FACTION_DUTY_UPDATE = "faction_duty_update"
    INJURY_RECOVERY = "injury_recovery"


class NPCDailyReplanningResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    replanned_npc_ids: list[str] = Field(default_factory=list)


OPEN_PLAN_STATUSES = {NPCPlanStatus.PLANNED, NPCPlanStatus.ACTIVE}


def should_run_daily_replanning_on_tick(state: GameState) -> bool:
    if state.current_time.day <= 1:
        return False
    previous_day = state.current_time.day - 1
    has_previous_marker = any(
        state.social_flags.get(f"npc_daily_replanning_day_{previous_day}_{npc_id}") is True
        for npc_id in state.npcs
    )
    has_current_marker_for_all = all(_already_replanned_today(state, npc_id) for npc_id in state.npcs)
    return has_previous_marker and not has_current_marker_for_all


def run_daily_replanning(
    state: GameState,
    trigger: DailyReplanningTrigger | str = DailyReplanningTrigger.NEW_DAY,
    npc_ids: list[str] | None = None,
) -> NPCDailyReplanningResult:
    trigger_value = DailyReplanningTrigger(trigger).value
    working_state = state
    result = NPCDailyReplanningResult()
    selected_ids = set(npc_ids) if npc_ids is not None else None
    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if selected_ids is not None and npc.id not in selected_ids:
            continue
        if not can_act(working_state, npc.id):
            continue
        if trigger_value == DailyReplanningTrigger.NEW_DAY.value and _already_replanned_today(working_state, npc.id):
            continue
        npc_deltas = _replan_npc(working_state, npc.id, trigger_value)
        if not npc_deltas:
            continue
        result.state_deltas.extend(npc_deltas)
        result.events.append(_build_replanning_event(working_state, npc.id, trigger_value, npc_deltas))
        result.replanned_npc_ids.append(npc.id)
        for delta in npc_deltas:
            working_state = apply_delta(working_state, delta)
    return result


def _replan_npc(state: GameState, npc_id: str, trigger: str) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    working_state = state

    prune_result = prune_expired_intents(working_state, npc_id)
    for delta in prune_result.state_deltas:
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    plan_delta = _cancel_impossible_plans(working_state, npc_id)
    if plan_delta is not None:
        deltas.append(plan_delta)
        working_state = apply_delta(working_state, plan_delta)

    goal_delta = _reevaluate_goal(working_state, npc_id)
    if goal_delta is not None:
        deltas.append(goal_delta)
        working_state = apply_delta(working_state, goal_delta)

    for duty in _active_duties(working_state, npc_id):
        if _daily_duty_already_enqueued(working_state, npc_id, duty.id):
            continue
        intent = _intent_for_daily_duty(working_state, npc_id, duty)
        if intent is None:
            continue
        queued = enqueue_intent(working_state, npc_id, intent)
        if queued.rejected_reason is not None:
            continue
        for delta in queued.state_deltas:
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)
        marker = _daily_duty_marker(working_state, npc_id, duty.id)
        deltas.append(marker)
        working_state = apply_delta(working_state, marker)

    day_marker = _day_marker(working_state, npc_id, trigger)
    deltas.append(day_marker)
    return deltas


def _reevaluate_goal(state: GameState, npc_id: str) -> StateDelta | None:
    selected = choose_goal(state, npc_id)
    current = state.npcs[npc_id].current_goal_id
    next_goal_id = selected.id if selected is not None else None
    if current == next_goal_id:
        return None
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"npcs.{npc_id}.current_goal_id",
        value=next_goal_id,
        reason="NPC daily replanning reevaluated current goal.",
        metadata={"source": "npc_daily_replanning", "npc_id": npc_id, "goal_id": next_goal_id or ""},
    )


def _cancel_impossible_plans(state: GameState, npc_id: str) -> StateDelta | None:
    npc = state.npcs[npc_id]
    updated_plans: list[NPCPlan] = []
    changed = False
    for plan in npc.plans:
        if plan.status in OPEN_PLAN_STATUSES and validate_plan(state, plan).rejected_reason is not None:
            updated_plans.append(plan.model_copy(update={"status": NPCPlanStatus.CANCELLED}))
            changed = True
        else:
            updated_plans.append(plan)
    if not changed:
        return None
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"npcs.{npc_id}.plans",
        value=[plan.model_dump(mode="json") for plan in updated_plans],
        reason="NPC daily replanning cancelled impossible plans.",
        metadata={"source": "npc_daily_replanning", "npc_id": npc_id, "action": "cancel_impossible_plans"},
    )


def _active_duties(state: GameState, npc_id: str) -> list[NPCFactionDuty]:
    return [
        duty
        for duty in sorted(state.npcs[npc_id].faction_duties, key=lambda item: (-item.priority, item.created_turn, item.id))
        if duty.status == NPCFactionDutyStatus.ACTIVE
        and (duty.expires_turn is None or duty.expires_turn > state.turn)
    ]


def _intent_for_daily_duty(state: GameState, npc_id: str, duty: NPCFactionDuty) -> NPCIntent | None:
    intent_type = {
        NPCFactionDutyType.GUARD_LOCATION: "guard_location",
        NPCFactionDutyType.PATROL_ROUTE: "visit_location",
        NPCFactionDutyType.REPORT_CRIME_TO_FACTION: "report_crime",
        NPCFactionDutyType.SPREAD_FACTION_RUMOR: "spread_rumor",
        NPCFactionDutyType.PROTECT_FACTION_MEMBER: "protect_faction_member",
        NPCFactionDutyType.REFUSE_HOSTILE_ACTOR: "refuse_hostile_actor",
        NPCFactionDutyType.SEEK_INFORMATION: "seek_information",
        NPCFactionDutyType.ENFORCE_CURFEW: "enforce_curfew",
    }[duty.duty_type]
    target_id = _duty_target(state, npc_id, duty)
    if target_id is None:
        return None
    preconditions = [f"fact:{fact_id}" for fact_id in duty.required_fact_ids]
    preconditions.extend(f"rumor:{rumor_id}" for rumor_id in duty.required_rumor_ids)
    preconditions.extend(f"crime:{crime_id}" for crime_id in duty.required_crime_ids)
    return NPCIntent(
        id=f"daily-duty-{state.current_time.day}-{duty.id}",
        npc_id=npc_id,
        intent_type=intent_type,
        priority=duty.priority,
        target_id=target_id,
        target_type=duty.target_type or _target_type_for_intent(intent_type),
        created_turn=state.turn,
        expires_turn=duty.expires_turn,
        preconditions=sorted(set(preconditions)),
        debug_reason=f"daily_replanning:{duty.id}",
    )


def _duty_target(state: GameState, npc_id: str, duty: NPCFactionDuty) -> str | None:
    if duty.duty_type == NPCFactionDutyType.PATROL_ROUTE:
        return duty.route_location_ids[0] if duty.route_location_ids else duty.target_id
    if duty.duty_type == NPCFactionDutyType.GUARD_LOCATION:
        return duty.target_id or state.npcs[npc_id].location_id
    if duty.duty_type == NPCFactionDutyType.REPORT_CRIME_TO_FACTION:
        return duty.target_id or _first_known_crime(state, npc_id)
    if duty.duty_type == NPCFactionDutyType.SPREAD_FACTION_RUMOR:
        return duty.target_id or _first_known_rumor(state, npc_id)
    if duty.duty_type == NPCFactionDutyType.REFUSE_HOSTILE_ACTOR:
        return duty.target_id or state.player.id
    return duty.target_id


def _first_known_crime(state: GameState, npc_id: str) -> str | None:
    for crime in sorted(state.crimes.values(), key=lambda item: item.id):
        if npc_id in crime.witnessed_by or f"crime:{crime.id}" in state.npcs[npc_id].knowledge:
            return crime.id
    return None


def _first_known_rumor(state: GameState, npc_id: str) -> str | None:
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if npc_id in rumor.known_by_npcs:
            return rumor.id
    return None


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


def _already_replanned_today(state: GameState, npc_id: str) -> bool:
    return state.social_flags.get(_day_key(state, npc_id)) is True


def _daily_duty_already_enqueued(state: GameState, npc_id: str, duty_id: str) -> bool:
    return state.social_flags.get(_daily_duty_key(state, npc_id, duty_id)) is True


def _day_marker(state: GameState, npc_id: str, trigger: str) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_day_key(state, npc_id)}",
        value=True,
        reason="NPC daily replanning completed for the day.",
        metadata={"source": "npc_daily_replanning", "npc_id": npc_id, "trigger": trigger},
    )


def _daily_duty_marker(state: GameState, npc_id: str, duty_id: str) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_daily_duty_key(state, npc_id, duty_id)}",
        value=True,
        reason="NPC daily duty was enqueued during replanning.",
        metadata={"source": "npc_daily_replanning", "npc_id": npc_id, "duty_id": duty_id},
    )


def _day_key(state: GameState, npc_id: str) -> str:
    return f"npc_daily_replanning_day_{state.current_time.day}_{npc_id}"


def _daily_duty_key(state: GameState, npc_id: str, duty_id: str) -> str:
    safe_duty = duty_id.replace(":", "_").replace("-", "_")
    return f"npc_daily_replanning_duty_{state.current_time.day}_{npc_id}_{safe_duty}"


def _build_replanning_event(
    state: GameState,
    npc_id: str,
    trigger: str,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"npc-daily-replanning-{state.current_time.day}-{state.turn}-{npc_id}-{trigger}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_daily_replanning",
        target_id=npc_id,
        result=trigger,
        state_deltas=deltas,
        visible_to_player=False,
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )
