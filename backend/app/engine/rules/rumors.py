from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, RumorState, RumorTruthStatus
from app.engine.rules.life_state import can_talk
from app.engine.rules.relationships import can_share_rumor, relationship_score


class RumorRuleError(ValueError):
    """Raised when rumor rules cannot resolve cleanly."""


class VisibleRumor(BaseModel):
    id: str
    text_for_player: str
    truth_status: RumorTruthStatus = RumorTruthStatus.UNKNOWN
    spread_level: int = 0
    tags: list[str] = Field(default_factory=list)


def create_rumor(
    state: GameState,
    rumor_id: str,
    text_for_player: str,
    fact_id: str | None = None,
    source_event_id: str | None = None,
    truth_status: RumorTruthStatus = RumorTruthStatus.UNKNOWN,
    known_by_npcs: list[str] | None = None,
    known_by_factions: list[str] | None = None,
    known_by_player: bool = False,
    spread_level: int = 0,
    tags: list[str] | None = None,
) -> list[StateDelta]:
    if rumor_id in state.rumors:
        raise RumorRuleError(f"Rumor already exists: {rumor_id}")
    if fact_id is not None and fact_id not in state.facts:
        raise RumorRuleError(f"Unknown fact_id for rumor {rumor_id}: {fact_id}")
    for npc_id in known_by_npcs or []:
        _require_npc(state, npc_id)
    for faction_id in known_by_factions or []:
        _require_faction(state, faction_id)
    rumor = RumorState(
        id=rumor_id,
        source_event_id=source_event_id,
        fact_id=fact_id,
        text_for_player=text_for_player,
        truth_status=truth_status,
        known_by_npcs=set(known_by_npcs or []),
        known_by_factions=set(known_by_factions or []),
        known_by_player=known_by_player,
        spread_level=spread_level,
        created_turn=state.turn,
        tags=tags or [],
        text=text_for_player,
        known_by=set(known_by_npcs or []) | set(known_by_factions or []),
        credibility=spread_level,
        known_to_player=known_by_player,
    )
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"rumors.{rumor_id}",
            value=rumor,
            reason="Create rumor.",
            metadata={"source": "rumor", "rumor_id": rumor_id},
        )
    ]


def add_rumor_to_npc(state: GameState, rumor_id: str, npc_id: str) -> list[StateDelta]:
    rumor = _require_rumor(state, rumor_id)
    _require_npc(state, npc_id)
    if npc_id in rumor.known_by_npcs:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"rumors.{rumor_id}.known_by_npcs",
            value=npc_id,
            reason=f"NPC {npc_id} heard rumor {rumor_id}.",
            metadata={"source": "rumor_propagation", "rumor_id": rumor_id, "npc_id": npc_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"rumors.{rumor_id}.known_by",
            value=npc_id,
            reason=f"NPC {npc_id} heard rumor {rumor_id}.",
            metadata={"source": "rumor_propagation", "rumor_id": rumor_id, "npc_id": npc_id},
        ),
    ]


def add_rumor_to_faction(state: GameState, rumor_id: str, faction_id: str) -> list[StateDelta]:
    rumor = _require_rumor(state, rumor_id)
    _require_faction(state, faction_id)
    if faction_id in rumor.known_by_factions:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"rumors.{rumor_id}.known_by_factions",
            value=faction_id,
            reason=f"Faction {faction_id} heard rumor {rumor_id}.",
            metadata={"source": "rumor_propagation", "rumor_id": rumor_id, "faction_id": faction_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"rumors.{rumor_id}.known_by",
            value=faction_id,
            reason=f"Faction {faction_id} heard rumor {rumor_id}.",
            metadata={"source": "rumor_propagation", "rumor_id": rumor_id, "faction_id": faction_id},
        ),
    ]


def mark_rumor_known_by_player(state: GameState, rumor_id: str) -> list[StateDelta]:
    rumor = _require_rumor(state, rumor_id)
    if rumor.known_by_player:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"rumors.{rumor_id}.known_by_player",
            value=True,
            reason=f"Player heard rumor {rumor_id}.",
            metadata={
                "source": "rumor_discovery",
                "rumor_id": rumor_id,
                "visible_to_player": "true",
            },
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"rumors.{rumor_id}.known_to_player",
            value=True,
            reason=f"Player heard rumor {rumor_id}.",
            metadata={
                "source": "rumor_discovery",
                "rumor_id": rumor_id,
                "visible_to_player": "true",
            },
        ),
    ]


def get_visible_rumors(state: GameState) -> list[VisibleRumor]:
    return [
        VisibleRumor(
            id=rumor.id,
            text_for_player=_safe_rumor_text(state, rumor),
            truth_status=rumor.truth_status,
            spread_level=rumor.spread_level,
            tags=rumor.tags,
        )
        for rumor in sorted(state.rumors.values(), key=lambda item: item.id)
        if rumor.known_by_player
    ]


def propagate_rumors(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if not rumor.known_by_npcs:
            continue
        for source_npc_id in sorted(rumor.known_by_npcs):
            source_npc = state.npcs.get(source_npc_id)
            if source_npc is None:
                continue
            if not can_talk(state, source_npc_id):
                continue
            target_npc_id = best_rumor_target(state, source_npc_id, set(rumor.known_by_npcs))
            if target_npc_id is None:
                continue
            deltas.extend(add_rumor_to_npc(state, rumor.id, target_npc_id))
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"rumors.{rumor.id}.spread_level",
                    value=1,
                    reason=f"Rumor {rumor.id} spread from {source_npc_id} to {target_npc_id}.",
                    metadata={
                        "source": "rumor_propagation",
                        "rumor_id": rumor.id,
                        "from_npc_id": source_npc_id,
                        "to_npc_id": target_npc_id,
                    },
                )
            )
            return deltas
    return deltas


def best_rumor_target(state: GameState, source_npc_id: str, excluded_ids: set[str] | None = None) -> str | None:
    source_npc = state.npcs.get(source_npc_id)
    if source_npc is None or not can_talk(state, source_npc_id):
        return None
    blocked = excluded_ids or set()
    candidates = [
        target
        for target in state.npcs.values()
        if target.id != source_npc_id
        and target.id not in blocked
        and target.location_id == source_npc.location_id
        and can_talk(state, target.id)
        and can_share_rumor(state, source_npc_id, target.id)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda npc: (-relationship_score(state, source_npc_id, npc.id), npc.id))
    return candidates[0].id


def build_rumor_event(event_id: str, turn: int, state_deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="rumor_spread",
        result="success",
        state_deltas=state_deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in state_deltas),
    )


def _safe_rumor_text(state: GameState, rumor: RumorState) -> str:
    if _rumor_points_to_unknown_protected_fact(state, rumor):
        if _rumor_text_reveals_fact(state, rumor):
            return "You have heard a vague rumor, but not enough to confirm the details."
    if rumor.text_for_player:
        return rumor.text_for_player
    if rumor.fact_id and rumor.fact_id in state.player_visible_facts:
        fact = state.facts.get(rumor.fact_id)
        if fact and fact.text:
            return fact.text
    return "You have heard a vague rumor, but not enough to confirm the details."


def _rumor_points_to_unknown_protected_fact(state: GameState, rumor: RumorState) -> bool:
    if not rumor.fact_id or rumor.fact_id in state.player_visible_facts:
        return False
    fact = state.facts.get(rumor.fact_id)
    if fact is None:
        return False
    return fact.visibility.value in {"hidden", "discoverable"}


def _rumor_text_reveals_fact(state: GameState, rumor: RumorState) -> bool:
    if not rumor.fact_id or not rumor.text_for_player:
        return False
    fact = state.facts.get(rumor.fact_id)
    if fact is None or not fact.text:
        return False
    return fact.text.strip().lower() in rumor.text_for_player.strip().lower()


def _require_rumor(state: GameState, rumor_id: str) -> RumorState:
    rumor = state.rumors.get(rumor_id)
    if rumor is None:
        raise RumorRuleError(f"Unknown rumor_id: {rumor_id}")
    return rumor


def _require_npc(state: GameState, npc_id: str) -> None:
    if npc_id not in state.npcs:
        raise RumorRuleError(f"Unknown npc_id: {npc_id}")


def _require_faction(state: GameState, faction_id: str) -> None:
    if faction_id not in state.factions:
        raise RumorRuleError(f"Unknown faction_id: {faction_id}")
