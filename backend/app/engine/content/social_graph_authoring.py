from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.validator import ValidationReport
from app.engine.content.world_loader import FactionDef, NPCDef, RelationshipDef


class SocialGraphAuthoringError(ValueError):
    """Raised when social graph authoring input is invalid."""


class FactionAuthoringNode(BaseModel):
    id: str
    name: str
    description: str = ""
    known_by_player: bool = False
    default_reputation: int = 0
    default_alert_level: int = 0
    default_conflict_level: int = 0
    tags: list[str] = Field(default_factory=list)
    conflict_tags: list[str] = Field(default_factory=list)


class FactionAuthoringEdge(BaseModel):
    source_faction_id: str
    target_faction_id: str
    relation: int = 0
    conflict_level: int = 0
    visibility: str = "hidden"


class FactionAuthoringGraph(BaseModel):
    world_id: str
    factions: list[FactionAuthoringNode] = Field(default_factory=list)
    conflict_edges: list[FactionAuthoringEdge] = Field(default_factory=list)


class RelationshipAuthoringNode(BaseModel):
    id: str
    label: str
    node_type: str
    hidden: bool = False


class RelationshipAuthoringEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int = 0
    fear: int = 0
    affinity: int = 0
    obligation: int = 0
    tags: list[str] = Field(default_factory=list)
    known_by_player: bool = False


class RelationshipAuthoringGraph(BaseModel):
    world_id: str
    nodes: list[RelationshipAuthoringNode] = Field(default_factory=list)
    relationships: list[RelationshipAuthoringEdge] = Field(default_factory=list)


class SocialAuthoringGraph(BaseModel):
    world_id: str
    faction_graph: FactionAuthoringGraph
    relationship_graph: RelationshipAuthoringGraph


class SocialAuthoringPreview(BaseModel):
    world_id: str
    graph: SocialAuthoringGraph
    yaml_contents: dict[str, str]
    validation: ValidationReport
    confirmation_required: bool = False


def parse_social_authoring_graph(
    world_id: str,
    authoring_service: ContentAuthoringService,
) -> SocialAuthoringGraph:
    try:
        factions_content = authoring_service.read_file(world_id, "factions.yaml")
    except AuthoringError as exc:
        raise SocialGraphAuthoringError(str(exc)) from exc
    try:
        relationships_content = authoring_service.read_file(world_id, "relationships.yaml")
    except AuthoringError:
        relationships_content = "relationships: []\n"
    try:
        npcs_content = authoring_service.read_file(world_id, "npcs.yaml")
    except AuthoringError as exc:
        raise SocialGraphAuthoringError(str(exc)) from exc
    return SocialAuthoringGraph(
        world_id=world_id,
        faction_graph=factions_yaml_to_graph(world_id, factions_content),
        relationship_graph=relationships_yaml_to_graph(world_id, relationships_content, npcs_content),
    )


def preview_social_authoring_graph(
    world_id: str,
    graph: SocialAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> SocialAuthoringPreview:
    if graph.world_id != world_id:
        raise SocialGraphAuthoringError("Social graph world_id does not match request world_id")
    yaml_contents = social_graph_to_yaml(graph)
    validation = authoring_service.validate_drafts(world_id, yaml_contents)
    return SocialAuthoringPreview(
        world_id=world_id,
        graph=graph,
        yaml_contents=yaml_contents,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_social_authoring_graph(
    world_id: str,
    graph: SocialAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> ValidationReport:
    return preview_social_authoring_graph(world_id, graph, authoring_service).validation


def save_social_authoring_graph(
    world_id: str,
    graph: SocialAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> ValidationReport:
    preview = preview_social_authoring_graph(world_id, graph, authoring_service)
    if not preview.validation.ok:
        return preview.validation
    return authoring_service.write_files(world_id, preview.yaml_contents)


def factions_yaml_to_graph(world_id: str, content: str) -> FactionAuthoringGraph:
    data = _load_mapping(content, "factions.yaml")
    raw_factions = data.get("factions", [])
    if not isinstance(raw_factions, list):
        raise SocialGraphAuthoringError("Expected factions.yaml key 'factions' to be a list")
    factions: list[FactionAuthoringNode] = []
    edges: list[FactionAuthoringEdge] = []
    known_by_faction: dict[str, bool] = {}
    for raw_faction in raw_factions:
        try:
            faction = FactionDef.model_validate(raw_faction)
        except ValidationError as exc:
            raise SocialGraphAuthoringError(f"Faction schema validation failed: {exc}") from exc
        known_by_faction[faction.id] = faction.known_by_player
        factions.append(
            FactionAuthoringNode(
                id=faction.id,
                name=faction.name,
                description=faction.description,
                known_by_player=faction.known_by_player,
                default_reputation=faction.default_reputation,
                default_alert_level=faction.default_alert_level,
                default_conflict_level=faction.default_conflict_level,
                tags=faction.tags,
                conflict_tags=faction.conflict_tags,
            )
        )
        for target_id, relation in sorted(faction.relations.items()):
            edges.append(
                FactionAuthoringEdge(
                    source_faction_id=faction.id,
                    target_faction_id=target_id,
                    relation=relation,
                    conflict_level=faction.default_conflict_level,
                    visibility="player_visible" if faction.known_by_player and known_by_faction.get(target_id, False) else "hidden",
                )
            )
    return FactionAuthoringGraph(world_id=world_id, factions=factions, conflict_edges=edges)


def relationships_yaml_to_graph(
    world_id: str,
    relationships_content: str,
    npcs_content: str,
) -> RelationshipAuthoringGraph:
    npc_data = _load_mapping(npcs_content, "npcs.yaml")
    raw_npcs = npc_data.get("npcs", [])
    if not isinstance(raw_npcs, list):
        raise SocialGraphAuthoringError("Expected npcs.yaml key 'npcs' to be a list")
    nodes = [RelationshipAuthoringNode(id="player", label="Player", node_type="player")]
    for raw_npc in raw_npcs:
        try:
            npc = NPCDef.model_validate(raw_npc)
        except ValidationError as exc:
            raise SocialGraphAuthoringError(f"NPC schema validation failed: {exc}") from exc
        nodes.append(
            RelationshipAuthoringNode(
                id=npc.id,
                label=npc.name,
                node_type="npc",
                hidden=npc.hidden,
            )
        )

    data = _load_mapping(relationships_content, "relationships.yaml")
    raw_relationships = data.get("relationships", [])
    if not isinstance(raw_relationships, list):
        raise SocialGraphAuthoringError("Expected relationships.yaml key 'relationships' to be a list")
    relationships: list[RelationshipAuthoringEdge] = []
    for raw_relationship in raw_relationships:
        try:
            relationship = RelationshipDef.model_validate(raw_relationship)
        except ValidationError as exc:
            raise SocialGraphAuthoringError(f"Relationship schema validation failed: {exc}") from exc
        payload = relationship.model_dump(mode="json")
        payload["id"] = relationship.relationship_id()
        relationships.append(RelationshipAuthoringEdge(**payload))
    return RelationshipAuthoringGraph(world_id=world_id, nodes=nodes, relationships=relationships)


def social_graph_to_yaml(graph: SocialAuthoringGraph) -> dict[str, str]:
    faction_by_id = {faction.id: faction for faction in graph.faction_graph.factions}
    relations_by_source: dict[str, dict[str, int]] = {faction.id: {} for faction in graph.faction_graph.factions}
    conflict_by_source: dict[str, int] = {faction.id: faction.default_conflict_level for faction in graph.faction_graph.factions}
    for edge in graph.faction_graph.conflict_edges:
        relations_by_source.setdefault(edge.source_faction_id, {})[edge.target_faction_id] = edge.relation
        conflict_by_source[edge.source_faction_id] = max(conflict_by_source.get(edge.source_faction_id, 0), edge.conflict_level)

    factions = [
        {
            "id": faction.id,
            "name": faction.name,
            "description": faction.description,
            "default_reputation": faction.default_reputation,
            "known_by_player": faction.known_by_player,
            "relations": relations_by_source.get(faction.id, {}),
            "conflict_tags": faction.conflict_tags,
            "default_conflict_level": conflict_by_source.get(faction.id, 0),
            "default_alert_level": faction.default_alert_level,
            "tags": faction.tags,
        }
        for faction in sorted(faction_by_id.values(), key=lambda item: item.id)
    ]
    relationships = [
        {
            "id": relationship.id,
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "relation_type": relationship.relation_type,
            "trust": relationship.trust,
            "fear": relationship.fear,
            "affinity": relationship.affinity,
            "obligation": relationship.obligation,
            "tags": relationship.tags,
            "known_by_player": relationship.known_by_player,
        }
        for relationship in sorted(graph.relationship_graph.relationships, key=lambda item: item.id)
    ]
    return {
        "factions.yaml": yaml.safe_dump({"factions": factions}, sort_keys=False, allow_unicode=True),
        "relationships.yaml": yaml.safe_dump({"relationships": relationships}, sort_keys=False, allow_unicode=True),
    }


def _load_mapping(content: str, file_name: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise SocialGraphAuthoringError(f"Invalid {file_name}: {exc}") from exc
    if not isinstance(data, dict):
        raise SocialGraphAuthoringError(f"Expected {file_name} to contain a mapping")
    return data
