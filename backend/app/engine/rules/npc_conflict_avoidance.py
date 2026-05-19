from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    ActorCondition,
    CombatStatus,
    GameState,
    NPCFactionDutyStatus,
    NPCFactionDutyType,
    NPCIntent,
    PrimaryEmotion,
)
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_intents import enqueue_intent


class ConflictAvoidanceBehavior(StrEnum):
    AVOID_LOCATION = "avoid_location"
    FLEE_FROM_ACTOR = "flee_from_actor"
    AVOID_ACTOR = "avoid_actor"
    SEEK_GUARD = "seek_guard"
    CALL_FOR_HELP = "call_for_help"
    HIDE = "hide"
    REFUSE_CONFRONTATION = "refuse_confrontation"
    REST = "rest"


class ConflictAvoidanceCandidate(BaseModel):
    npc_id: str
    behavior_type: ConflictAvoidanceBehavior
    target_id: str | None = None
    target_type: str | None = None
    reason_code: str
    intent: NPCIntent | None = None
    plan_candidate: dict[str, str] | None = None


class ConflictAvoidanceResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    candidates: list[ConflictAvoidanceCandidate] = Field(default_factory=list)
    rejected_reason: str | None = None


def resolve_conflict_avoidance(state: GameState, npc_id: str) -> ConflictAvoidanceResult:
    npc = state.npcs.get(npc_id)
    if npc is None:
        return ConflictAvoidanceResult(rejected_reason="npc_missing")
    if not can_act(state, npc_id):
        return ConflictAvoidanceResult(rejected_reason="npc_inactive")

    candidate = _choose_candidate(state, npc_id)
    if candidate is None:
        return ConflictAvoidanceResult()
    if _already_processed(state, candidate):
        return ConflictAvoidanceResult()

    intent = _intent_for_candidate(state, candidate)
    queued = enqueue_intent(state, npc_id, intent)
    if queued.rejected_reason is not None or queued.selected_intent is None:
        return ConflictAvoidanceResult(candidates=[candidate], rejected_reason=queued.rejected_reason)

    candidate = candidate.model_copy(
        update={
            "intent": queued.selected_intent,
            "plan_candidate": {
                "source": "npc_conflict_avoidance",
                "behavior_type": candidate.behavior_type.value,
            },
        }
    )
    marker = _avoidance_marker(candidate)
    deltas = [*queued.state_deltas, marker]
    return ConflictAvoidanceResult(
        state_deltas=deltas,
        events=[_build_avoidance_event(state, candidate, deltas)],
        candidates=[candidate],
    )


def _choose_candidate(state: GameState, npc_id: str) -> ConflictAvoidanceCandidate | None:
    npc = state.npcs[npc_id]
    visible_hostile = _visible_hostile_actor(state, npc_id)
    if visible_hostile and _has_active_guard_duty(state, npc_id):
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.CALL_FOR_HELP,
            target_id=visible_hostile,
            target_type="actor",
            reason_code="guard_duty_visible_hostile",
        )
    if npc.condition in {ActorCondition.WOUNDED, ActorCondition.CRITICAL} or npc.hp < npc.max_hp:
        if visible_hostile:
            return ConflictAvoidanceCandidate(
                npc_id=npc_id,
                behavior_type=ConflictAvoidanceBehavior.FLEE_FROM_ACTOR,
                target_id=visible_hostile,
                target_type="actor",
                reason_code="injured_visible_hostile",
            )
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.REST,
            target_id=npc.location_id,
            target_type="location",
            reason_code="injured_rest",
        )
    if visible_hostile:
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.FLEE_FROM_ACTOR,
            target_id=visible_hostile,
            target_type="actor",
            reason_code="visible_hostile_actor",
        )
    if npc.social_disposition.fear_player >= 65 and _actor_visible_to_npc(state, npc_id, state.player.id):
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.AVOID_ACTOR,
            target_id=state.player.id,
            target_type="actor",
            reason_code="high_fear_player",
        )
    if _location_is_dangerous(state, npc.location_id):
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.AVOID_LOCATION,
            target_id=npc.location_id,
            target_type="location",
            reason_code="dangerous_location",
        )
    if npc.emotional_state.primary_emotion == PrimaryEmotion.AFRAID and npc.emotional_state.intensity >= 70:
        return ConflictAvoidanceCandidate(
            npc_id=npc_id,
            behavior_type=ConflictAvoidanceBehavior.HIDE,
            target_id=npc.location_id,
            target_type="location",
            reason_code="afraid_hide",
        )
    return None


def _intent_for_candidate(state: GameState, candidate: ConflictAvoidanceCandidate) -> NPCIntent:
    intent_type = {
        ConflictAvoidanceBehavior.AVOID_LOCATION: "avoid_location",
        ConflictAvoidanceBehavior.FLEE_FROM_ACTOR: "flee_from_actor",
        ConflictAvoidanceBehavior.AVOID_ACTOR: "avoid_actor",
        ConflictAvoidanceBehavior.SEEK_GUARD: "seek_guard",
        ConflictAvoidanceBehavior.CALL_FOR_HELP: "call_for_help",
        ConflictAvoidanceBehavior.HIDE: "hide",
        ConflictAvoidanceBehavior.REFUSE_CONFRONTATION: "refuse_confrontation",
        ConflictAvoidanceBehavior.REST: "rest",
    }[candidate.behavior_type]
    return NPCIntent(
        id=f"conflict-avoidance-{candidate.behavior_type.value}-{candidate.npc_id}-{candidate.target_id or 'none'}",
        npc_id=candidate.npc_id,
        intent_type=intent_type,
        priority=_priority_for_candidate(candidate),
        target_id=candidate.target_id,
        target_type=candidate.target_type,
        created_turn=state.turn,
        debug_reason=f"conflict_avoidance:{candidate.reason_code}",
    )


def _priority_for_candidate(candidate: ConflictAvoidanceCandidate) -> int:
    return {
        ConflictAvoidanceBehavior.CALL_FOR_HELP: 9,
        ConflictAvoidanceBehavior.FLEE_FROM_ACTOR: 8,
        ConflictAvoidanceBehavior.REST: 7,
        ConflictAvoidanceBehavior.AVOID_ACTOR: 6,
        ConflictAvoidanceBehavior.AVOID_LOCATION: 5,
        ConflictAvoidanceBehavior.HIDE: 5,
        ConflictAvoidanceBehavior.SEEK_GUARD: 4,
        ConflictAvoidanceBehavior.REFUSE_CONFRONTATION: 4,
    }[candidate.behavior_type]


def _visible_hostile_actor(state: GameState, npc_id: str) -> str | None:
    npc = state.npcs[npc_id]
    if (
        npc.location_id == state.player.location_id
        and state.player.combat_stance == "aggressive"
        and _actor_visible_to_npc(state, npc_id, state.player.id)
    ):
        return state.player.id
    for other in sorted(state.npcs.values(), key=lambda item: item.id):
        if other.id == npc_id or other.location_id != npc.location_id:
            continue
        if not can_act(state, other.id):
            continue
        if npc_id in other.hostile_to and _actor_visible_to_npc(state, npc_id, other.id):
            return other.id
    return None


def _has_active_guard_duty(state: GameState, npc_id: str) -> bool:
    npc = state.npcs[npc_id]
    for duty in npc.faction_duties:
        if duty.status != NPCFactionDutyStatus.ACTIVE:
            continue
        if duty.expires_turn is not None and duty.expires_turn <= state.turn:
            continue
        if duty.duty_type in {NPCFactionDutyType.GUARD_LOCATION, NPCFactionDutyType.PROTECT_FACTION_MEMBER}:
            return True
    return False


def _location_is_dangerous(state: GameState, location_id: str) -> bool:
    for combat in state.combats.values():
        if combat.location_id == location_id and combat.status == CombatStatus.ACTIVE:
            return True
    location = state.locations.get(location_id)
    return location is not None and location.light_level <= 1 and location.cover_level == 0


def _actor_visible_to_npc(state: GameState, npc_id: str, actor_id: str) -> bool:
    npc = state.npcs[npc_id]
    if actor_id == state.player.id:
        return npc.location_id == state.player.location_id
    target = state.npcs.get(actor_id)
    if target is None or target.location_id != npc.location_id or not target.visible:
        return False
    return not target.hidden or npc_id in target.discovered_by


def _already_processed(state: GameState, candidate: ConflictAvoidanceCandidate) -> bool:
    return state.social_flags.get(_avoidance_key(candidate)) is True


def _avoidance_marker(candidate: ConflictAvoidanceCandidate) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_avoidance_key(candidate)}",
        value=True,
        reason="NPC conflict avoidance generated a bounded intent.",
        metadata={
            "source": "npc_conflict_avoidance",
            "npc_id": candidate.npc_id,
            "behavior_type": candidate.behavior_type.value,
            "reason_code": candidate.reason_code,
        },
    )


def _avoidance_key(candidate: ConflictAvoidanceCandidate) -> str:
    target = (candidate.target_id or "none").replace(":", "_").replace("-", "_")
    return f"npc_conflict_avoidance_{candidate.npc_id}_{candidate.behavior_type.value}_{target}"


def _build_avoidance_event(
    state: GameState,
    candidate: ConflictAvoidanceCandidate,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"npc-conflict-avoidance-{state.turn}-{candidate.npc_id}-{candidate.behavior_type.value}-{candidate.target_id or 'none'}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_conflict_avoidance",
        target_id=candidate.npc_id,
        result=candidate.behavior_type.value,
        state_deltas=deltas,
        visible_to_player=_candidate_visible_to_player(state, candidate),
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )


def _candidate_visible_to_player(state: GameState, candidate: ConflictAvoidanceCandidate) -> bool:
    npc = state.npcs[candidate.npc_id]
    return npc.location_id == state.player.location_id and npc.visible and (not npc.hidden or state.player.id in npc.discovered_by)
