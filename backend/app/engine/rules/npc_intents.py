from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCIntent, NPCIntentStatus
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_simulation_boundary import NPCSimulationPolicy


class NPCIntentRuleError(ValueError):
    """Raised when NPC intent queue rules cannot resolve a request."""


class NPCIntentRuleResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    selected_intent: NPCIntent | None = None
    rejected_reason: str | None = None


ORDINARY_INTENT_TYPES = {
    "report_crime",
    "spread_rumor",
    "visit_location",
    "avoid_actor",
    "talk_to_npc",
    "guard_location",
    "rest",
    "seek_item",
    "avoid_location",
    "flee_from_actor",
    "seek_guard",
    "call_for_help",
    "hide",
    "refuse_confrontation",
    "protect_faction_member",
    "refuse_hostile_actor",
    "seek_information",
    "enforce_curfew",
}

OPEN_INTENT_STATUSES = {NPCIntentStatus.QUEUED, NPCIntentStatus.ACTIVE}


def enqueue_intent(state: GameState, npc_id: str, intent: NPCIntent) -> NPCIntentRuleResult:
    npc = _get_npc(state, npc_id)
    normalized = intent.model_copy(update={"npc_id": npc_id})
    rejected = _rejection_reason_for_intent(state, normalized)
    if rejected is not None:
        return NPCIntentRuleResult(rejected_reason=rejected)
    queue = [*npc.intent_queue, normalized]
    deltas = [_set_queue_delta(npc_id, queue, "NPC intent queued.", {"intent_id": normalized.id, "status": normalized.status.value})]
    return NPCIntentRuleResult(
        state_deltas=deltas,
        events=[_build_intent_event(state, npc_id, "npc_intent_enqueued", normalized, deltas)],
        selected_intent=normalized,
    )


def cancel_intent(state: GameState, npc_id: str, intent_id: str, reason: str = "cancelled") -> NPCIntentRuleResult:
    return _set_intent_status(state, npc_id, intent_id, NPCIntentStatus.CANCELLED, reason)


def complete_intent(state: GameState, npc_id: str, intent_id: str, reason: str = "completed") -> NPCIntentRuleResult:
    return _set_intent_status(state, npc_id, intent_id, NPCIntentStatus.COMPLETED, reason)


def fail_intent(state: GameState, npc_id: str, intent_id: str, reason: str = "failed") -> NPCIntentRuleResult:
    return _set_intent_status(state, npc_id, intent_id, NPCIntentStatus.FAILED, reason)


def select_next_intent(state: GameState, npc_id: str) -> NPCIntent | None:
    npc = _get_npc(state, npc_id)
    if not can_act(state, npc_id):
        return None
    candidates = [
        intent
        for intent in npc.intent_queue
        if intent.status == NPCIntentStatus.QUEUED
        and not _is_expired(state, intent)
        and _rejection_reason_for_intent(state, intent) is None
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda intent: (-intent.priority, intent.created_turn, intent.id))[0]


def prune_expired_intents(state: GameState, npc_id: str) -> NPCIntentRuleResult:
    npc = _get_npc(state, npc_id)
    expired = [
        intent
        for intent in npc.intent_queue
        if intent.status in OPEN_INTENT_STATUSES and _is_expired(state, intent)
    ]
    if not expired:
        return NPCIntentRuleResult()
    expired_ids = {intent.id for intent in expired}
    queue = [intent for intent in npc.intent_queue if intent.id not in expired_ids]
    deltas = [
        _set_queue_delta(
            npc_id,
            queue,
            "Expired NPC intents were pruned.",
            {"expired_intent_ids": ",".join(sorted(expired_ids))},
        )
    ]
    return NPCIntentRuleResult(
        state_deltas=deltas,
        events=[_build_prune_event(state, npc_id, sorted(expired_ids), deltas)],
    )


def _set_intent_status(
    state: GameState,
    npc_id: str,
    intent_id: str,
    status: NPCIntentStatus,
    reason: str,
) -> NPCIntentRuleResult:
    npc = _get_npc(state, npc_id)
    queue: list[NPCIntent] = []
    selected: NPCIntent | None = None
    for intent in npc.intent_queue:
        if intent.id == intent_id:
            selected = intent.model_copy(update={"status": status, "debug_reason": reason})
            queue.append(selected)
        else:
            queue.append(intent)
    if selected is None:
        raise NPCIntentRuleError(f"NPC intent not found: {npc_id}.{intent_id}")
    deltas = [_set_queue_delta(npc_id, queue, f"NPC intent {status.value}.", {"intent_id": intent_id, "status": status.value})]
    return NPCIntentRuleResult(
        state_deltas=deltas,
        events=[_build_intent_event(state, npc_id, f"npc_intent_{status.value}", selected, deltas)],
        selected_intent=selected,
    )


def _rejection_reason_for_intent(state: GameState, intent: NPCIntent) -> str | None:
    if intent.npc_id not in state.npcs:
        return "npc_missing"
    if not can_act(state, intent.npc_id):
        return "npc_inactive"
    if intent.intent_type not in ORDINARY_INTENT_TYPES:
        return "intent_type_forbidden"
    if _is_expired(state, intent):
        return "intent_expired"
    known = NPCSimulationPolicy().build_context(state, intent.npc_id).npc_known_context
    for precondition in intent.preconditions:
        if precondition.startswith("fact:") and precondition.removeprefix("fact:") not in known.fact_ids:
            return "npc_unknown_fact"
        if precondition.startswith("rumor:") and precondition.removeprefix("rumor:") not in known.rumor_ids:
            return "npc_unknown_rumor"
        if precondition.startswith("crime:") and precondition.removeprefix("crime:") not in known.crime_ids:
            return "npc_unknown_crime"
    return None


def _is_expired(state: GameState, intent: NPCIntent) -> bool:
    return intent.expires_turn is not None and intent.expires_turn <= state.turn


def _get_npc(state: GameState, npc_id: str):
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise NPCIntentRuleError(f"NPC not found: {npc_id}")
    return npc


def _set_queue_delta(npc_id: str, queue: list[NPCIntent], reason: str, metadata: dict[str, str]) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"npcs.{npc_id}.intent_queue",
        value=[intent.model_dump(mode="json") for intent in queue],
        reason=reason,
        metadata={"source": "npc_intent", "npc_id": npc_id, **metadata},
    )


def _build_intent_event(
    state: GameState,
    npc_id: str,
    action_type: str,
    intent: NPCIntent,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"{action_type}-{state.turn}-{npc_id}-{intent.id}",
        turn=state.turn,
        actor_id="system",
        action_type=action_type,
        target_id=npc_id,
        result=intent.status.value,
        state_deltas=deltas,
        visible_to_player=False,
    )


def _build_prune_event(state: GameState, npc_id: str, expired_ids: list[str], deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=f"npc_intents_pruned-{state.turn}-{npc_id}-{'-'.join(expired_ids)}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_intents_pruned",
        target_id=npc_id,
        result="expired_pruned",
        state_deltas=deltas,
        visible_to_player=False,
    )
