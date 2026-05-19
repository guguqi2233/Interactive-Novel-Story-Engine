from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCIntent, PrimaryEmotion, RumorState
from app.engine.rules.life_state import can_act
from app.engine.rules.relationships import get_relationship, relationship_score
from app.engine.rules.npc_intents import enqueue_intent


class NPCRumorDecisionType(StrEnum):
    KEEP_SECRET = "keep_secret"
    SHARE_WITH_ACTOR = "share_with_actor"
    SHARE_WITH_FACTION = "share_with_faction"
    DISTORT_RUMOR = "distort_rumor"
    IGNORE_RUMOR = "ignore_rumor"
    REPORT_RUMOR = "report_rumor"
    ENQUEUE_SPREAD_RUMOR_INTENT = "enqueue_spread_rumor_intent"


class NPCRumorDecision(BaseModel):
    npc_id: str
    rumor_id: str
    decision: NPCRumorDecisionType
    target_id: str | None = None
    target_type: str | None = None
    priority: int = 0
    reasons: list[str] = Field(default_factory=list)
    intent: NPCIntent | None = None


class NPCRumorDecisionResult(BaseModel):
    decision: NPCRumorDecision | None = None
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    rejected_reason: str | None = None


def decide_npc_rumor_action(
    state: GameState,
    npc_id: str,
    rumor_id: str,
    *,
    target_actor_id: str | None = None,
    target_faction_id: str | None = None,
) -> NPCRumorDecisionResult:
    if npc_id not in state.npcs:
        return NPCRumorDecisionResult(rejected_reason="npc_missing")
    if not can_act(state, npc_id):
        return NPCRumorDecisionResult(rejected_reason="npc_inactive")
    rumor = state.rumors.get(rumor_id)
    if rumor is None:
        return NPCRumorDecisionResult(rejected_reason="rumor_missing")
    if npc_id not in rumor.known_by_npcs:
        return NPCRumorDecisionResult(
            decision=NPCRumorDecision(
                npc_id=npc_id,
                rumor_id=rumor_id,
                decision=NPCRumorDecisionType.IGNORE_RUMOR,
                reasons=["npc_unknown_rumor"],
            ),
            rejected_reason="npc_unknown_rumor",
        )
    if _already_decided(state, npc_id, rumor_id):
        return NPCRumorDecisionResult(rejected_reason="rumor_decision_already_processed")

    decision = _build_decision(
        state,
        npc_id,
        rumor,
        target_actor_id=target_actor_id,
        target_faction_id=target_faction_id,
    )
    deltas = _decision_deltas(state, decision)
    marker = _decision_marker(npc_id, rumor_id, decision.decision)
    deltas.append(marker)
    return NPCRumorDecisionResult(
        decision=decision,
        state_deltas=deltas,
        events=[_build_decision_event(state, decision, deltas)],
    )


def _build_decision(
    state: GameState,
    npc_id: str,
    rumor: RumorState,
    *,
    target_actor_id: str | None,
    target_faction_id: str | None,
) -> NPCRumorDecision:
    npc = state.npcs[npc_id]
    reasons: list[str] = []
    secrecy = _secrecy_level(rumor)
    source_credibility = rumor.credibility or rumor.spread_level
    emotional_boost = _emotional_boost(state, npc_id)
    if secrecy >= 2:
        reasons.append("secret_rumor")
    if source_credibility > 0:
        reasons.append("credible_source")
    if emotional_boost > 0:
        reasons.append("emotional_intensity")

    if target_faction_id and npc.faction_id and target_faction_id == npc.faction_id and _faction_aligned(state, rumor, target_faction_id):
        return NPCRumorDecision(
            npc_id=npc_id,
            rumor_id=rumor.id,
            decision=NPCRumorDecisionType.SHARE_WITH_FACTION,
            target_id=target_faction_id,
            target_type="faction",
            priority=5 + source_credibility + emotional_boost,
            reasons=[*reasons, "faction_aligned"],
        )

    if target_actor_id:
        trust = relationship_score(state, npc_id, target_actor_id)
        relationship = get_relationship(state, npc_id, target_actor_id)
        fear = relationship.fear if relationship else 0
        if secrecy >= 2 and trust < 60:
            return NPCRumorDecision(
                npc_id=npc_id,
                rumor_id=rumor.id,
                decision=NPCRumorDecisionType.KEEP_SECRET,
                target_id=target_actor_id,
                target_type="npc",
                priority=3,
                reasons=[*reasons, "insufficient_trust_for_secret"],
            )
        if trust >= 20 and fear < 50:
            intent = _spread_intent(state, npc_id, rumor.id, target_actor_id, 4 + trust // 20 + emotional_boost)
            return NPCRumorDecision(
                npc_id=npc_id,
                rumor_id=rumor.id,
                decision=NPCRumorDecisionType.ENQUEUE_SPREAD_RUMOR_INTENT,
                target_id=target_actor_id,
                target_type="npc",
                priority=intent.priority,
                reasons=[*reasons, "trusted_target"],
                intent=intent,
            )
        if trust < 0:
            return NPCRumorDecision(
                npc_id=npc_id,
                rumor_id=rumor.id,
                decision=NPCRumorDecisionType.DISTORT_RUMOR,
                target_id=target_actor_id,
                target_type="npc",
                priority=2,
                reasons=[*reasons, "low_trust"],
            )

    if "report" in rumor.tags or "crime" in rumor.tags:
        return NPCRumorDecision(
            npc_id=npc_id,
            rumor_id=rumor.id,
            decision=NPCRumorDecisionType.REPORT_RUMOR,
            target_id=npc.faction_id,
            target_type="faction" if npc.faction_id else None,
            priority=4 + source_credibility,
            reasons=[*reasons, "reportable_tag"],
        )

    return NPCRumorDecision(
        npc_id=npc_id,
        rumor_id=rumor.id,
        decision=NPCRumorDecisionType.IGNORE_RUMOR,
        priority=0,
        reasons=[*reasons, "no_rule_matched"],
    )


def _decision_deltas(state: GameState, decision: NPCRumorDecision) -> list[StateDelta]:
    if decision.decision == NPCRumorDecisionType.ENQUEUE_SPREAD_RUMOR_INTENT and decision.intent is not None:
        return enqueue_intent(state, decision.npc_id, decision.intent).state_deltas
    if decision.decision == NPCRumorDecisionType.SHARE_WITH_FACTION and decision.target_id:
        if decision.target_id in state.rumors[decision.rumor_id].known_by_factions:
            return []
        return [
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"rumors.{decision.rumor_id}.known_by_factions",
                value=decision.target_id,
                reason="NPC rumor decision shared a known rumor with an aligned faction.",
                metadata=_metadata(decision),
            )
        ]
    if decision.decision in {
        NPCRumorDecisionType.KEEP_SECRET,
        NPCRumorDecisionType.DISTORT_RUMOR,
        NPCRumorDecisionType.IGNORE_RUMOR,
        NPCRumorDecisionType.REPORT_RUMOR,
    }:
        npc = state.npcs[decision.npc_id]
        rumor_decisions = dict(npc.plan_state.get("rumor_decisions", {}))
        rumor_decisions[decision.rumor_id] = decision.decision.value
        next_plan_state = dict(npc.plan_state)
        next_plan_state["rumor_decisions"] = rumor_decisions
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{decision.npc_id}.plan_state",
                value=next_plan_state,
                reason="NPC recorded a bounded rumor decision.",
                metadata=_metadata(decision),
            )
        ]
    return []


def _spread_intent(state: GameState, npc_id: str, rumor_id: str, target_actor_id: str, priority: int) -> NPCIntent:
    return NPCIntent(
        id=f"rumor-decision-spread-{npc_id}-{rumor_id}-{target_actor_id}",
        npc_id=npc_id,
        intent_type="spread_rumor",
        priority=priority,
        target_id=rumor_id,
        target_type="rumor",
        created_turn=state.turn,
        preconditions=[f"rumor:{rumor_id}"],
        debug_reason="npc_rumor_decision",
    )


def _secrecy_level(rumor: RumorState) -> int:
    if "secret" in rumor.tags or "private" in rumor.tags:
        return 2
    if rumor.fact_id:
        return 1
    return 0


def _emotional_boost(state: GameState, npc_id: str) -> int:
    emotion = state.npcs[npc_id].emotional_state
    if emotion.primary_emotion in {PrimaryEmotion.AFRAID, PrimaryEmotion.ANGRY, PrimaryEmotion.SUSPICIOUS}:
        return emotion.intensity // 25
    return 0


def _faction_aligned(state: GameState, rumor: RumorState, faction_id: str) -> bool:
    if faction_id in rumor.known_by_factions:
        return True
    if faction_id not in state.factions:
        return False
    faction = state.factions[faction_id]
    return bool(set(rumor.tags).intersection(faction.tags)) or "faction" in rumor.tags


def _metadata(decision: NPCRumorDecision) -> dict[str, str]:
    return {
        "source": "npc_rumor_decision",
        "npc_id": decision.npc_id,
        "rumor_id": decision.rumor_id,
        "decision": decision.decision.value,
    }


def _build_decision_event(state: GameState, decision: NPCRumorDecision, deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=f"npc-rumor-decision-{state.turn}-{decision.npc_id}-{decision.rumor_id}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_rumor_decision",
        target_id=decision.npc_id,
        result=decision.decision.value,
        state_deltas=deltas,
        visible_to_player=False,
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )


def _already_decided(state: GameState, npc_id: str, rumor_id: str) -> bool:
    prefix = f"npc_rumor_decision_{npc_id}_{_safe_id(rumor_id)}_"
    return any(key.startswith(prefix) and value is True for key, value in state.social_flags.items())


def _decision_marker(npc_id: str, rumor_id: str, decision: NPCRumorDecisionType) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_decision_key(npc_id, rumor_id, decision)}",
        value=True,
        reason="NPC rumor decision processed.",
        metadata={"source": "npc_rumor_decision", "npc_id": npc_id, "rumor_id": rumor_id, "decision": decision.value},
    )


def _decision_key(npc_id: str, rumor_id: str, decision: NPCRumorDecisionType) -> str:
    return f"npc_rumor_decision_{npc_id}_{_safe_id(rumor_id)}_{decision.value}"


def _safe_id(value: str) -> str:
    return value.replace(":", "_").replace("-", "_")
