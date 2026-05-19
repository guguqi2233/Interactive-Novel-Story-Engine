from datetime import datetime, timezone

from pydantic import BaseModel

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCSocialDisposition, PrimaryEmotion
from app.engine.rules.factions import reputation_band
from app.engine.rules.relationships import get_relationship


class NPCSocialDispositionRuleError(ValueError):
    """Raised when NPC social disposition rules cannot resolve a request."""


class NPCBehaviorWeights(BaseModel):
    help_actor: int = 0
    warn_actor: int = 0
    avoid_actor: int = 0
    report_to_faction: int = 0
    share_rumor: int = 0
    keep_secret: int = 0


class NPCDispositionUpdateResult(BaseModel):
    state_deltas: list[StateDelta]
    event: Event | None = None
    disposition: NPCSocialDisposition


def derive_from_relationships(state: GameState, npc_id: str) -> NPCSocialDisposition:
    npc = _get_npc(state, npc_id)
    player_relationship = get_relationship(state, npc_id, "player")
    trust_player = player_relationship.trust if player_relationship else npc.relationship_to_player
    fear_player = max(0, player_relationship.fear if player_relationship else 0, npc.emotional_state.stress // 2)
    loyalty_to_npcs: dict[str, int] = {}
    for relationship in sorted(state.relationships.values(), key=lambda item: item.id):
        if relationship.source_id != npc_id or relationship.target_id == "player":
            continue
        loyalty_to_npcs[relationship.target_id] = _clamp_0_100(relationship.trust + relationship.affinity + relationship.obligation)
    loyalty_to_faction = 0
    if npc.faction_id and npc.faction_id in state.factions:
        faction = state.factions[npc.faction_id]
        band = reputation_band(faction.reputation.value)
        loyalty_to_faction = {
            "hostile": 20,
            "suspicious": 35,
            "neutral": 50,
            "friendly": 70,
            "trusted": 85,
        }[band.value]
        if faction.conflict_level or faction.alert_level:
            loyalty_to_faction = _clamp_0_100(loyalty_to_faction + min(20, faction.conflict_level * 5 + faction.alert_level * 2))
    if npc.emotional_state.primary_emotion == PrimaryEmotion.AFRAID:
        fear_player = _clamp_0_100(fear_player + npc.emotional_state.intensity // 3)
    risk_tolerance = _clamp_0_100(50 - fear_player // 2 + max(0, trust_player) // 5)
    conflict_tolerance = _clamp_0_100(50 - fear_player // 3 + loyalty_to_faction // 5)
    secrecy_preference = _clamp_0_100(50 + fear_player // 4 + loyalty_to_faction // 5)
    return NPCSocialDisposition(
        trust_player=_clamp_signed(trust_player),
        fear_player=fear_player,
        loyalty_to_faction=loyalty_to_faction,
        loyalty_to_npcs=loyalty_to_npcs,
        moral_flexibility=npc.social_disposition.moral_flexibility,
        risk_tolerance=risk_tolerance,
        conflict_tolerance=conflict_tolerance,
        secrecy_preference=secrecy_preference,
    )


def update_from_event(
    state: GameState,
    npc_id: str,
    event_type: str,
    *,
    event_id: str | None = None,
    severity: int = 1,
    target_npc_id: str | None = None,
) -> NPCDispositionUpdateResult:
    current = _get_npc(state, npc_id).social_disposition
    severity = max(1, severity)
    event_key = event_type.lower()
    updates: dict[str, object] = {}
    if event_key in {"witnessed_violence", "violence", "combat", "assault"}:
        updates = {
            "fear_player": _clamp_0_100(current.fear_player + 8 * severity),
            "risk_tolerance": _clamp_0_100(current.risk_tolerance - 5 * severity),
            "conflict_tolerance": _clamp_0_100(current.conflict_tolerance - 4 * severity),
        }
    elif event_key in {"helped", "repeated_help", "friendly_interaction"}:
        updates = {
            "trust_player": _clamp_signed(current.trust_player + 6 * severity),
            "fear_player": _clamp_0_100(current.fear_player - 2 * severity),
        }
    elif event_key in {"faction_conflict", "faction_alert"}:
        updates = {
            "loyalty_to_faction": _clamp_0_100(current.loyalty_to_faction + 5 * severity),
            "conflict_tolerance": _clamp_0_100(current.conflict_tolerance + 2 * severity),
            "secrecy_preference": _clamp_0_100(current.secrecy_preference + 2 * severity),
        }
    elif event_key in {"helped_npc", "protected_ally"} and target_npc_id:
        loyalty = dict(current.loyalty_to_npcs)
        loyalty[target_npc_id] = _clamp_0_100(loyalty.get(target_npc_id, 0) + 5 * severity)
        updates = {"loyalty_to_npcs": loyalty}
    next_disposition = current.model_copy(update=updates)
    delta = StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"npcs.{npc_id}.social_disposition",
        value=next_disposition.model_dump(mode="json"),
        caused_by_event_id=event_id,
        reason="NPC social disposition updated by deterministic event rule.",
        metadata={"source": "npc_social_disposition", "npc_id": npc_id, "event_type": event_key},
    )
    event = Event(
        event_id=f"npc-social-disposition-{state.turn}-{npc_id}-{event_id or event_key}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_social_disposition_update",
        target_id=npc_id,
        result=event_key,
        state_deltas=[delta],
        visible_to_player=False,
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )
    return NPCDispositionUpdateResult(state_deltas=[delta], event=event, disposition=next_disposition)


def disposition_to_behavior_weights(disposition: NPCSocialDisposition) -> NPCBehaviorWeights:
    return NPCBehaviorWeights(
        help_actor=max(0, disposition.trust_player) + disposition.loyalty_to_npcs.get("player", 0),
        warn_actor=max(0, disposition.trust_player) + disposition.secrecy_preference // 4,
        avoid_actor=disposition.fear_player + max(0, 50 - disposition.risk_tolerance),
        report_to_faction=disposition.loyalty_to_faction + max(0, 50 - disposition.moral_flexibility),
        share_rumor=max(0, disposition.trust_player) + max(0, 50 - disposition.secrecy_preference),
        keep_secret=disposition.secrecy_preference + max(0, 50 - disposition.trust_player),
    )


def disposition_to_dialogue_tone(disposition: NPCSocialDisposition) -> str:
    trust = _band_signed(disposition.trust_player)
    fear = _band(disposition.fear_player)
    loyalty = _band(disposition.loyalty_to_faction)
    risk = _band(disposition.risk_tolerance)
    secrecy = _band(disposition.secrecy_preference)
    return f"trust={trust}; fear={fear}; faction_loyalty={loyalty}; risk={risk}; secrecy={secrecy}"


def build_disposition_event(event_id: str, turn: int, npc_id: str, state_deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="npc_social_disposition_update",
        target_id=npc_id,
        result="success",
        state_deltas=state_deltas,
        visible_to_player=False,
        created_at=datetime.fromtimestamp(turn, timezone.utc),
    )


def _get_npc(state: GameState, npc_id: str):
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise NPCSocialDispositionRuleError(f"Unknown NPC: {npc_id}")
    return npc


def _clamp_0_100(value: int) -> int:
    return min(100, max(0, value))


def _clamp_signed(value: int) -> int:
    return min(100, max(-100, value))


def _band(value: int) -> str:
    if value >= 70:
        return "high"
    if value >= 35:
        return "medium"
    if value > 0:
        return "low"
    return "none"


def _band_signed(value: int) -> str:
    if value >= 50:
        return "high"
    if value > 0:
        return "positive"
    if value <= -50:
        return "hostile"
    if value < 0:
        return "guarded"
    return "neutral"
