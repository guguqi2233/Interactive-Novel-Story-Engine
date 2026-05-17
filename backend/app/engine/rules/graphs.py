from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.world_state import FactionState, GameState, NPCState
from app.engine.rules.factions import reputation_band


class GraphVisibility(StrEnum):
    PLAYER_VISIBLE = "player_visible"
    DEBUG_ONLY = "debug_only"


class GraphNodeType(StrEnum):
    NPC = "npc"
    FACTION = "faction"
    PLAYER = "player"
    LOCATION = "location"
    QUEST = "quest"


class GraphEdgeType(StrEnum):
    RELATIONSHIP = "relationship"
    FACTION_RELATION = "faction_relation"
    FACTION_MEMBERSHIP = "faction_membership"
    REPUTATION = "reputation"
    CONFLICT = "conflict"


class GraphNode(BaseModel):
    id: str
    label: str
    type: GraphNodeType
    visibility: GraphVisibility
    tags: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: GraphEdgeType
    weight: int | None = None
    label: str | None = None
    visibility: GraphVisibility
    metadata_safe: dict[str, str | int | float | bool] = Field(default_factory=dict)


class RelationshipGraph(BaseModel):
    local_only: bool = True
    scope: GraphVisibility
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class FactionGraph(BaseModel):
    local_only: bool = True
    scope: GraphVisibility
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


def build_relationship_graph(state: GameState, *, debug: bool = False) -> RelationshipGraph:
    scope = GraphVisibility.DEBUG_ONLY if debug else GraphVisibility.PLAYER_VISIBLE
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    for relationship in sorted(state.relationships.values(), key=lambda item: item.id):
        visibility = (
            GraphVisibility.PLAYER_VISIBLE
            if relationship.known_by_player
            else GraphVisibility.DEBUG_ONLY
        )
        if not debug and visibility != GraphVisibility.PLAYER_VISIBLE:
            continue
        if not debug and (
            not _actor_visible_to_player(state, relationship.source_id)
            or not _actor_visible_to_player(state, relationship.target_id)
        ):
            continue
        _add_actor_node(nodes, state, relationship.source_id, visibility, debug=debug)
        _add_actor_node(nodes, state, relationship.target_id, visibility, debug=debug)
        edges.append(
            GraphEdge(
                source=relationship.source_id,
                target=relationship.target_id,
                type=GraphEdgeType.RELATIONSHIP,
                weight=relationship.trust + relationship.affinity + relationship.obligation - relationship.fear,
                label=relationship.relation_type,
                visibility=visibility,
                metadata_safe={
                    "relationship_id": relationship.id,
                    "trust": relationship.trust,
                    "fear": relationship.fear,
                    "affinity": relationship.affinity,
                    "obligation": relationship.obligation,
                },
            )
        )

    return RelationshipGraph(scope=scope, nodes=_sorted_nodes(nodes), edges=edges)


def build_faction_graph(state: GameState, *, debug: bool = False) -> FactionGraph:
    scope = GraphVisibility.DEBUG_ONLY if debug else GraphVisibility.PLAYER_VISIBLE
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    for faction in sorted(state.factions.values(), key=lambda item: item.id):
        if not debug and not _faction_visible_to_player(faction):
            continue
        visibility = (
            GraphVisibility.PLAYER_VISIBLE
            if _faction_visible_to_player(faction)
            else GraphVisibility.DEBUG_ONLY
        )
        nodes[faction.id] = _faction_node(faction, visibility)
        edges.append(
            GraphEdge(
                source="player",
                target=faction.id,
                type=GraphEdgeType.REPUTATION,
                weight=faction.reputation.value,
                label=reputation_band(faction.reputation.value).value,
                visibility=visibility,
                metadata_safe={"band": reputation_band(faction.reputation.value).value},
            )
        )
        _add_player_node(nodes, GraphVisibility.PLAYER_VISIBLE)
        for target_faction_id, relation_value in sorted(
            faction.relationships_to_other_factions.items()
        ):
            target_faction = state.factions.get(target_faction_id)
            if target_faction is None:
                continue
            if not debug and not _faction_visible_to_player(target_faction):
                continue
            target_visibility = (
                GraphVisibility.PLAYER_VISIBLE
                if _faction_visible_to_player(target_faction)
                else GraphVisibility.DEBUG_ONLY
            )
            nodes[target_faction.id] = _faction_node(target_faction, target_visibility)
            edge_visibility = (
                GraphVisibility.PLAYER_VISIBLE
                if visibility == GraphVisibility.PLAYER_VISIBLE
                and target_visibility == GraphVisibility.PLAYER_VISIBLE
                else GraphVisibility.DEBUG_ONLY
            )
            if debug or edge_visibility == GraphVisibility.PLAYER_VISIBLE:
                edges.append(
                    GraphEdge(
                        source=faction.id,
                        target=target_faction.id,
                        type=GraphEdgeType.FACTION_RELATION,
                        weight=relation_value,
                        label="faction relation",
                        visibility=edge_visibility,
                    )
                )

    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if not npc.faction_id or npc.faction_id not in nodes:
            continue
        if not debug and not _npc_visible_to_player(npc):
            continue
        visibility = GraphVisibility.PLAYER_VISIBLE if _npc_visible_to_player(npc) else GraphVisibility.DEBUG_ONLY
        _add_actor_node(nodes, state, npc.id, visibility, debug=debug)
        if debug or visibility == GraphVisibility.PLAYER_VISIBLE:
            edges.append(
                GraphEdge(
                    source=npc.id,
                    target=npc.faction_id,
                    type=GraphEdgeType.FACTION_MEMBERSHIP,
                    label="member",
                    visibility=visibility,
                )
            )

    return FactionGraph(scope=scope, nodes=_sorted_nodes(nodes), edges=edges)


def _add_player_node(nodes: dict[str, GraphNode], visibility: GraphVisibility) -> None:
    nodes.setdefault(
        "player",
        GraphNode(
            id="player",
            label="Player",
            type=GraphNodeType.PLAYER,
            visibility=visibility,
            tags=[],
        ),
    )


def _add_actor_node(
    nodes: dict[str, GraphNode],
    state: GameState,
    actor_id: str,
    visibility: GraphVisibility,
    *,
    debug: bool,
) -> None:
    if actor_id == "player":
        _add_player_node(nodes, GraphVisibility.PLAYER_VISIBLE)
        return
    npc = state.npcs.get(actor_id)
    if npc is None:
        return
    if not debug and not _npc_visible_to_player(npc):
        return
    nodes.setdefault(
        actor_id,
        GraphNode(
            id=actor_id,
            label=actor_id,
            type=GraphNodeType.NPC,
            visibility=visibility if _npc_visible_to_player(npc) else GraphVisibility.DEBUG_ONLY,
            tags=["hidden"] if npc.hidden else [],
        ),
    )


def _faction_node(faction: FactionState, visibility: GraphVisibility) -> GraphNode:
    return GraphNode(
        id=faction.id,
        label=faction.name,
        type=GraphNodeType.FACTION,
        visibility=visibility,
        tags=faction.tags,
    )


def _actor_visible_to_player(state: GameState, actor_id: str) -> bool:
    if actor_id == "player":
        return True
    npc = state.npcs.get(actor_id)
    return npc is not None and _npc_visible_to_player(npc)


def _npc_visible_to_player(npc: NPCState) -> bool:
    return npc.visible and not npc.hidden


def _faction_visible_to_player(faction: FactionState) -> bool:
    return faction.known_by_player or faction.reputation.known_to_player


def _sorted_nodes(nodes: dict[str, GraphNode]) -> list[GraphNode]:
    return sorted(nodes.values(), key=lambda item: (item.type.value, item.id))
