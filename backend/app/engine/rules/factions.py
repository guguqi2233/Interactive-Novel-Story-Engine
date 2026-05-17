from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactionState, GameState


class FactionRuleError(ValueError):
    """Raised when faction reputation rules cannot resolve cleanly."""


class ReputationBand(StrEnum):
    HOSTILE = "hostile"
    SUSPICIOUS = "suspicious"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    TRUSTED = "trusted"


class VisibleFaction(BaseModel):
    id: str
    name: str
    description: str = ""
    reputation: int
    band: ReputationBand
    tags: list[str] = Field(default_factory=list)


def get_reputation(state: GameState, faction_id: str) -> int:
    return _get_faction(state, faction_id).reputation.value


def change_reputation(
    state: GameState,
    faction_id: str,
    amount: int,
    reason: str,
) -> list[StateDelta]:
    _get_faction(state, faction_id)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"factions.{faction_id}.reputation.value",
            value=amount,
            reason=reason,
            metadata={"event_type": "faction_reputation_changed", "faction_id": faction_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"factions.{faction_id}.reputation.recent_reasons",
            value=reason,
            reason=reason,
            metadata={"event_type": "faction_reputation_changed", "faction_id": faction_id},
        ),
    ]


def set_reputation(
    state: GameState,
    faction_id: str,
    value: int,
    reason: str,
) -> list[StateDelta]:
    _get_faction(state, faction_id)
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"factions.{faction_id}.reputation.value",
            value=value,
            reason=reason,
            metadata={"event_type": "faction_reputation_changed", "faction_id": faction_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"factions.{faction_id}.reputation.recent_reasons",
            value=reason,
            reason=reason,
            metadata={"event_type": "faction_reputation_changed", "faction_id": faction_id},
        ),
    ]


def get_visible_factions(state: GameState) -> list[VisibleFaction]:
    return [
        _to_visible_faction(faction)
        for faction in sorted(state.factions.values(), key=lambda item: item.id)
        if faction.reputation.known_to_player
    ]


def build_reputation_event(
    event_id: str,
    turn: int,
    faction_id: str,
    state_deltas: list[StateDelta],
    visible_to_player: bool = False,
) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="faction_reputation_changed",
        target_id=faction_id,
        result="success",
        state_deltas=state_deltas,
        visible_to_player=visible_to_player,
    )


def reputation_band(value: int) -> ReputationBand:
    if value <= -50:
        return ReputationBand.HOSTILE
    if value <= -10:
        return ReputationBand.SUSPICIOUS
    if value < 25:
        return ReputationBand.NEUTRAL
    if value < 60:
        return ReputationBand.FRIENDLY
    return ReputationBand.TRUSTED


def _get_faction(state: GameState, faction_id: str) -> FactionState:
    faction = state.factions.get(faction_id)
    if faction is None:
        raise FactionRuleError(f"Unknown faction_id: {faction_id}")
    return faction


def _to_visible_faction(faction: FactionState) -> VisibleFaction:
    return VisibleFaction(
        id=faction.id,
        name=faction.name,
        description=faction.description,
        reputation=faction.reputation.value,
        band=reputation_band(faction.reputation.value),
        tags=faction.tags,
    )
