from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import CrimeState, FactionState, GameState, RumorState
from app.engine.rules.factions import reputation_band


class FactionConflictRuleError(ValueError):
    """Raised when faction conflict rules cannot resolve cleanly."""


class VisibleFactionConflict(BaseModel):
    faction_id: str
    alert_level: int
    conflict_level: int
    relationships_to_other_factions: dict[str, int] = Field(default_factory=dict)
    conflict_tags: list[str] = Field(default_factory=list)


def get_faction_relation(state: GameState, faction_id: str, target_faction_id: str) -> int:
    faction = _require_faction(state, faction_id)
    _require_faction(state, target_faction_id)
    return faction.relationships_to_other_factions.get(target_faction_id, 0)


def change_faction_relation(
    state: GameState,
    faction_id: str,
    target_faction_id: str,
    amount: int,
    reason: str,
) -> list[StateDelta]:
    faction = _require_faction(state, faction_id)
    _require_faction(state, target_faction_id)
    next_relations = dict(faction.relationships_to_other_factions)
    next_relations[target_faction_id] = next_relations.get(target_faction_id, 0) + amount
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"factions.{faction_id}.relationships_to_other_factions",
            value=next_relations,
            reason=reason,
            metadata={
                "source": "faction_conflict",
                "faction_id": faction_id,
                "target_faction_id": target_faction_id,
            },
        )
    ]


def change_alert_level(
    state: GameState,
    faction_id: str,
    amount: int,
    reason: str,
) -> list[StateDelta]:
    _require_faction(state, faction_id)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"factions.{faction_id}.alert_level",
            value=amount,
            reason=reason,
            metadata={"source": "faction_conflict", "faction_id": faction_id},
        )
    ]


def apply_faction_incident(
    state: GameState,
    *,
    incident_id: str,
    faction_id: str,
    alert_delta: int = 1,
    conflict_delta: int = 0,
    reason: str,
    target_faction_id: str | None = None,
) -> list[StateDelta]:
    _require_faction(state, faction_id)
    if target_faction_id is not None:
        _require_faction(state, target_faction_id)
    marker_key = _incident_marker(incident_id, faction_id, target_faction_id)
    if state.social_flags.get(marker_key) is True:
        return []
    deltas: list[StateDelta] = []
    if alert_delta:
        deltas.extend(change_alert_level(state, faction_id, alert_delta, reason))
    if conflict_delta:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"factions.{faction_id}.conflict_level",
                value=conflict_delta,
                reason=reason,
                metadata={"source": "faction_conflict", "faction_id": faction_id},
            )
        )
        if target_faction_id:
            deltas.extend(change_faction_relation(state, faction_id, target_faction_id, -abs(conflict_delta), reason))
    deltas.append(
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"social_flags.{marker_key}",
            value=True,
            reason="Faction conflict incident processed.",
            metadata={
                "source": "faction_conflict",
                "incident_id": incident_id,
                "faction_id": faction_id,
            },
        )
    )
    return deltas


def get_visible_faction_conflicts(state: GameState) -> list[VisibleFactionConflict]:
    return [
        VisibleFactionConflict(
            faction_id=faction.id,
            alert_level=faction.alert_level,
            conflict_level=faction.conflict_level,
            relationships_to_other_factions={
                target_id: value
                for target_id, value in sorted(faction.relationships_to_other_factions.items())
                if _faction_known_to_player(state.factions.get(target_id))
            },
            conflict_tags=faction.conflict_tags,
        )
        for faction in sorted(state.factions.values(), key=lambda item: item.id)
        if _faction_known_to_player(faction) and (faction.alert_level > 0 or faction.conflict_level > 0 or faction.conflict_tags)
    ]


def resolve_faction_conflicts_from_crimes(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for crime in sorted(state.crimes.values(), key=lambda item: item.id):
        victim_faction_id = _crime_victim_faction(state, crime)
        if victim_faction_id is None:
            continue
        deltas.extend(
            apply_faction_incident(
                state,
                incident_id=f"crime:{crime.id}",
                faction_id=victim_faction_id,
                alert_delta=max(1, crime.severity),
                conflict_delta=max(1, crime.severity // 2),
                reason=f"Crime against faction member: {crime.crime_type}.",
            )
        )
    return deltas


def resolve_faction_conflicts_from_rumors(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if not _rumor_is_public_incident(rumor):
            continue
        for faction_id in sorted(rumor.known_by_factions):
            if faction_id not in state.factions:
                continue
            deltas.extend(
                apply_faction_incident(
                    state,
                    incident_id=f"rumor:{rumor.id}:{faction_id}",
                    faction_id=faction_id,
                    alert_delta=1,
                    conflict_delta=0,
                    reason=f"Faction heard public rumor: {rumor.id}.",
                )
            )
    return deltas


def resolve_faction_conflicts_from_reputation(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for faction in sorted(state.factions.values(), key=lambda item: item.id):
        band = reputation_band(faction.reputation.value)
        if band.value not in {"hostile", "suspicious"}:
            continue
        deltas.extend(
            apply_faction_incident(
                state,
                incident_id=f"reputation:{faction.id}:{band.value}",
                faction_id=faction.id,
                alert_delta=2 if band.value == "hostile" else 1,
                conflict_delta=1 if band.value == "hostile" else 0,
                reason=f"Player reputation is {band.value}.",
            )
        )
    return deltas


def build_faction_conflict_event(event_id: str, turn: int, state_deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="faction_conflict",
        result="success",
        state_deltas=state_deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in state_deltas),
    )


def _require_faction(state: GameState, faction_id: str) -> FactionState:
    faction = state.factions.get(faction_id)
    if faction is None:
        raise FactionConflictRuleError(f"Unknown faction_id: {faction_id}")
    return faction


def _faction_known_to_player(faction: FactionState | None) -> bool:
    if faction is None:
        return False
    return faction.known_by_player or faction.reputation.known_to_player


def _crime_victim_faction(state: GameState, crime: CrimeState) -> str | None:
    for actor_id in (crime.victim_id, crime.target_id):
        if not actor_id:
            continue
        npc = state.npcs.get(actor_id)
        if npc and npc.faction_id:
            return npc.faction_id
    return None


def _rumor_is_public_incident(rumor: RumorState) -> bool:
    return rumor.known_by_player or "public" in rumor.tags or "crime" in rumor.tags or "combat" in rumor.tags


def _incident_marker(incident_id: str, faction_id: str, target_faction_id: str | None) -> str:
    target = target_faction_id or "none"
    safe_incident = incident_id.replace(":", "_")
    return f"faction_conflict_processed_{safe_incident}_{faction_id}_{target}"
