from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, RelationshipState


class RelationshipRuleError(ValueError):
    """Raised when relationship rules cannot resolve cleanly."""


class VisibleRelationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int
    fear: int
    affinity: int
    obligation: int
    tags: list[str] = Field(default_factory=list)


def relationship_id(source_id: str, target_id: str, relation_type: str = "general") -> str:
    return f"{source_id}:{relation_type}:{target_id}"


def get_relationship(
    state: GameState,
    source_id: str,
    target_id: str,
    relation_type: str | None = None,
) -> RelationshipState | None:
    if relation_type:
        direct = state.relationships.get(relationship_id(source_id, target_id, relation_type))
        if direct is not None:
            return direct
    for relationship in state.relationships.values():
        if relationship.source_id != source_id or relationship.target_id != target_id:
            continue
        if relation_type is None or relationship.relation_type == relation_type:
            return relationship
    return None


def change_trust(
    state: GameState,
    source_id: str,
    target_id: str,
    amount: int,
    reason: str,
    relation_type: str | None = None,
) -> list[StateDelta]:
    relationship = _require_relationship(state, source_id, target_id, relation_type)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"relationships.{relationship.id}.trust",
            value=amount,
            reason=reason,
            metadata={"source": "relationship", "relationship_id": relationship.id},
        )
    ]


def change_affinity(
    state: GameState,
    source_id: str,
    target_id: str,
    amount: int,
    reason: str,
    relation_type: str | None = None,
) -> list[StateDelta]:
    relationship = _require_relationship(state, source_id, target_id, relation_type)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"relationships.{relationship.id}.affinity",
            value=amount,
            reason=reason,
            metadata={"source": "relationship", "relationship_id": relationship.id},
        )
    ]


def change_fear(
    state: GameState,
    source_id: str,
    target_id: str,
    amount: int,
    reason: str,
    relation_type: str | None = None,
) -> list[StateDelta]:
    relationship = _require_relationship(state, source_id, target_id, relation_type)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"relationships.{relationship.id}.fear",
            value=amount,
            reason=reason,
            metadata={"source": "relationship", "relationship_id": relationship.id},
        )
    ]


def add_relationship(
    state: GameState,
    source_id: str,
    target_id: str,
    relation_type: str,
    *,
    trust: int = 0,
    fear: int = 0,
    affinity: int = 0,
    obligation: int = 0,
    tags: list[str] | None = None,
    known_by_player: bool = False,
    relationship_id_value: str | None = None,
) -> list[StateDelta]:
    _require_actor(state, source_id)
    _require_actor(state, target_id)
    new_id = relationship_id_value or relationship_id(source_id, target_id, relation_type)
    if new_id in state.relationships:
        raise RelationshipRuleError(f"Relationship already exists: {new_id}")
    relationship = RelationshipState(
        id=new_id,
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        trust=trust,
        fear=fear,
        affinity=affinity,
        obligation=obligation,
        tags=tags or [],
        known_by_player=known_by_player,
    )
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"relationships.{new_id}",
            value=relationship,
            reason="Create relationship.",
            metadata={"source": "relationship", "relationship_id": new_id},
        )
    ]


def get_visible_relationships(state: GameState) -> list[VisibleRelationship]:
    return [
        VisibleRelationship(
            id=relationship.id,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relation_type=relationship.relation_type,
            trust=relationship.trust,
            fear=relationship.fear,
            affinity=relationship.affinity,
            obligation=relationship.obligation,
            tags=relationship.tags,
        )
        for relationship in sorted(state.relationships.values(), key=lambda item: item.id)
        if relationship.known_by_player
    ]


def relationship_trust(state: GameState, source_id: str, target_id: str) -> int:
    relationship = get_relationship(state, source_id, target_id)
    return relationship.trust if relationship is not None else 0


def relationship_score(state: GameState, source_id: str, target_id: str) -> int:
    relationship = get_relationship(state, source_id, target_id)
    if relationship is None:
        return 0
    return relationship.trust + relationship.affinity + relationship.obligation - relationship.fear


def can_share_rumor(state: GameState, source_id: str, target_id: str) -> bool:
    relationship = get_relationship(state, source_id, target_id)
    if relationship is None:
        return True
    return relationship.trust >= 0


def build_relationship_event(event_id: str, turn: int, state_deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="relationship_change",
        result="success",
        state_deltas=state_deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in state_deltas),
    )


def _require_relationship(
    state: GameState,
    source_id: str,
    target_id: str,
    relation_type: str | None = None,
) -> RelationshipState:
    relationship = get_relationship(state, source_id, target_id, relation_type)
    if relationship is None:
        label = f"{source_id}->{target_id}" if relation_type is None else f"{source_id}:{relation_type}->{target_id}"
        raise RelationshipRuleError(f"Unknown relationship: {label}")
    return relationship


def _require_actor(state: GameState, actor_id: str) -> None:
    if actor_id != "player" and actor_id not in state.npcs:
        raise RelationshipRuleError(f"Unknown actor_id: {actor_id}")
