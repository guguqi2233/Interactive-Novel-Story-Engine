from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.world_state import RelationshipState
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.authoring_boundary import AuthoringSaveDecision, default_authoring_boundary_policy
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.content.world_loader import FactionDef, NPCDef, RelationshipDef
from app.engine.rules.relationship_tone import derive_tone_from_relationship, tone_summary_for_prompt


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
    visibility: str = "hidden"
    x: float = 0.0
    y: float = 0.0


class FactionAuthoringEdge(BaseModel):
    source_faction_id: str
    target_faction_id: str
    relation_type: str = "neutral"
    relation: int = 0
    conflict_level: int = 0
    visibility: str = "hidden"
    conflict_tags: list[str] = Field(default_factory=list)


class FactionAuthoringGraph(BaseModel):
    world_id: str
    faction_nodes: list[FactionAuthoringNode] = Field(default_factory=list)
    factions: list[FactionAuthoringNode] = Field(default_factory=list)
    relation_edges: list[FactionAuthoringEdge] = Field(default_factory=list)
    conflict_edges: list[FactionAuthoringEdge] = Field(default_factory=list)
    alliance_edges: list[FactionAuthoringEdge] = Field(default_factory=list)
    hostility_edges: list[FactionAuthoringEdge] = Field(default_factory=list)
    visibility_fields: list[str] = Field(default_factory=lambda: ["known_by_player", "visibility"])
    conflict_tag_index: list[str] = Field(default_factory=list)


class RelationshipAuthoringNode(BaseModel):
    id: str
    label: str
    node_type: str
    hidden: bool = False
    x: float = 0.0
    y: float = 0.0


class RelationshipTonePreview(BaseModel):
    preset_id: str = "derived"
    summary: str = ""
    address_style: str = "neutral"
    formality: str = "medium"
    warmth: int = 0
    tension: int = 0
    intimacy: int = 0
    respect: int = 50
    resentment: int = 0
    fear: int = 0
    avoidance: int = 0
    trust_expression: str = "reserved"


class RelationshipTonePreset(BaseModel):
    id: str
    label: str
    description: str = ""


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
    hidden_relationship: bool = False
    hidden_authoring_note: str | None = None
    tone_preset: str | None = None
    rp_tone_preview: RelationshipTonePreview = Field(default_factory=RelationshipTonePreview)


class RelationshipAuthoringGraph(BaseModel):
    world_id: str
    npc_nodes: list[RelationshipAuthoringNode] = Field(default_factory=list)
    nodes: list[RelationshipAuthoringNode] = Field(default_factory=list)
    relationship_edges: list[RelationshipAuthoringEdge] = Field(default_factory=list)
    relationships: list[RelationshipAuthoringEdge] = Field(default_factory=list)
    hidden_relationship_fields: list[str] = Field(default_factory=lambda: ["hidden_authoring_note"])
    relationship_tone_presets: list[RelationshipTonePreset] = Field(default_factory=list)
    rp_tone_preview_fields: list[str] = Field(default_factory=lambda: [
        "summary",
        "address_style",
        "formality",
        "warmth",
        "tension",
        "intimacy",
        "respect",
        "resentment",
        "fear",
        "avoidance",
        "trust_expression",
    ])


class SocialAuthoringGraph(BaseModel):
    world_id: str
    faction_graph: FactionAuthoringGraph
    relationship_graph: RelationshipAuthoringGraph


FactionConflictAuthoringGraph = FactionAuthoringGraph


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
    _add_faction_conflict_validation(graph.faction_graph, validation)
    _add_relationship_authoring_validation(graph.relationship_graph, validation)
    return SocialAuthoringPreview(
        world_id=world_id,
        graph=_with_relationship_previews(graph),
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
    *,
    confirm_warnings: bool = False,
) -> ValidationReport:
    preview = preview_social_authoring_graph(world_id, graph, authoring_service)
    if not preview.validation.ok:
        return preview.validation
    decision = default_authoring_boundary_policy().decide_save(
        preview.validation,
        confirm_warnings=confirm_warnings,
    )
    if decision != AuthoringSaveDecision.ALLOW:
        return preview.validation
    return authoring_service.write_files(
        world_id,
        preview.yaml_contents,
        confirm_warnings=confirm_warnings,
    )


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
                visibility="player_visible" if faction.known_by_player else "hidden",
                x=120 + len(factions) * 140,
                y=120,
            )
        )
        for target_id, relation in sorted(faction.relations.items()):
            edges.append(
                FactionAuthoringEdge(
                    source_faction_id=faction.id,
                    target_faction_id=target_id,
                    relation_type=_faction_relation_type(relation),
                    relation=relation,
                    conflict_level=faction.default_conflict_level,
                    visibility="player_visible" if faction.known_by_player and known_by_faction.get(target_id, False) else "hidden",
                    conflict_tags=faction.conflict_tags,
                )
            )
    return _with_faction_conflict_views(FactionAuthoringGraph(world_id=world_id, factions=factions, conflict_edges=edges))


def relationships_yaml_to_graph(
    world_id: str,
    relationships_content: str,
    npcs_content: str,
) -> RelationshipAuthoringGraph:
    npc_data = _load_mapping(npcs_content, "npcs.yaml")
    raw_npcs = npc_data.get("npcs", [])
    if not isinstance(raw_npcs, list):
        raise SocialGraphAuthoringError("Expected npcs.yaml key 'npcs' to be a list")
    nodes = [RelationshipAuthoringNode(id="player", label="Player", node_type="player", x=80, y=120)]
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
                x=80 + len(nodes) * 120,
                y=120,
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
        payload["rp_tone_preview"] = _tone_preview_from_payload(payload).model_dump(mode="json")
        relationships.append(RelationshipAuthoringEdge(**payload))
    return RelationshipAuthoringGraph(
        world_id=world_id,
        npc_nodes=nodes,
        nodes=nodes,
        relationship_edges=relationships,
        relationships=relationships,
        relationship_tone_presets=_relationship_tone_presets(),
    )


def social_graph_to_yaml(graph: SocialAuthoringGraph) -> dict[str, str]:
    faction_by_id = {faction.id: faction for faction in graph.faction_graph.factions}
    relations_by_source: dict[str, dict[str, int]] = {faction.id: {} for faction in graph.faction_graph.factions}
    conflict_by_source: dict[str, int] = {faction.id: faction.default_conflict_level for faction in graph.faction_graph.factions}
    conflict_tags_by_source: dict[str, set[str]] = {
        faction.id: set(faction.conflict_tags)
        for faction in graph.faction_graph.factions
    }
    for edge in graph.faction_graph.conflict_edges:
        relations_by_source.setdefault(edge.source_faction_id, {})[edge.target_faction_id] = edge.relation
        conflict_by_source[edge.source_faction_id] = max(conflict_by_source.get(edge.source_faction_id, 0), edge.conflict_level)
        conflict_tags_by_source.setdefault(edge.source_faction_id, set()).update(edge.conflict_tags)

    factions = [
        {
            "id": faction.id,
            "name": faction.name,
            "description": faction.description,
            "default_reputation": faction.default_reputation,
            "known_by_player": faction.known_by_player,
            "relations": relations_by_source.get(faction.id, {}),
            "conflict_tags": sorted(conflict_tags_by_source.get(faction.id, set(faction.conflict_tags))),
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
            "hidden_relationship": relationship.hidden_relationship,
            **({"hidden_authoring_note": relationship.hidden_authoring_note} if relationship.hidden_authoring_note else {}),
            **({"tone_preset": relationship.tone_preset} if relationship.tone_preset else {}),
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


def _with_faction_conflict_views(graph: FactionAuthoringGraph) -> FactionAuthoringGraph:
    factions = [
        faction.model_copy(update={"visibility": "player_visible" if faction.known_by_player else "hidden"})
        for faction in graph.factions
    ]
    edge_tags = {tag for edge in graph.conflict_edges for tag in edge.conflict_tags}
    faction_tags = {tag for faction in factions for tag in faction.conflict_tags}
    edges = [
        edge.model_copy(update={"relation_type": edge.relation_type or _faction_relation_type(edge.relation)})
        for edge in graph.conflict_edges
    ]
    return graph.model_copy(
        update={
            "faction_nodes": factions,
            "factions": factions,
            "relation_edges": edges,
            "conflict_edges": edges,
            "alliance_edges": [edge for edge in edges if edge.relation_type == "alliance"],
            "hostility_edges": [edge for edge in edges if edge.relation_type in {"hostility", "conflict"}],
            "conflict_tag_index": sorted(edge_tags | faction_tags),
        }
    )


def _faction_relation_type(relation: int) -> str:
    if relation >= 25:
        return "alliance"
    if relation <= -25:
        return "hostility"
    if relation < 0:
        return "conflict"
    return "neutral"


def _add_faction_conflict_validation(graph: FactionAuthoringGraph, report: ValidationReport) -> None:
    faction_ids = {faction.id for faction in graph.factions}
    seen: set[tuple[str, str]] = set()
    valid_relation_types = {"alliance", "hostility", "conflict", "neutral"}
    for faction in graph.factions:
        if faction.default_alert_level < 0 or faction.default_alert_level > 100:
            report.add(
                ValidationSeverity.ERROR,
                f"factions.yaml.{faction.id}.default_alert_level",
                f"Faction alert level must be between 0 and 100: {faction.default_alert_level}",
                code="faction_invalid_alert_level",
                ref_id=faction.id,
            )
        if faction.default_conflict_level < 0 or faction.default_conflict_level > 100:
            report.add(
                ValidationSeverity.ERROR,
                f"factions.yaml.{faction.id}.default_conflict_level",
                f"Faction conflict level must be between 0 and 100: {faction.default_conflict_level}",
                code="faction_invalid_conflict_level",
                ref_id=faction.id,
            )
    for edge in graph.conflict_edges:
        if edge.source_faction_id not in faction_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"factions.yaml.{edge.source_faction_id}.relations",
                f"Faction relation source does not exist: {edge.source_faction_id}",
                code="faction_relation_missing_source",
                ref_id=edge.source_faction_id,
            )
        if edge.target_faction_id not in faction_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"factions.yaml.{edge.source_faction_id}.relations.{edge.target_faction_id}",
                f"Faction relation references missing faction: {edge.target_faction_id}",
                code="faction_relation_missing_faction",
                ref_id=edge.target_faction_id,
            )
        if edge.relation_type not in valid_relation_types:
            report.add(
                ValidationSeverity.ERROR,
                f"factions.yaml.{edge.source_faction_id}.relations.{edge.target_faction_id}.relation_type",
                f"Faction conflict relation type is invalid: {edge.relation_type}",
                code="faction_invalid_conflict_relation",
                ref_id=edge.relation_type,
            )
        key = (edge.source_faction_id, edge.target_faction_id)
        if key in seen:
            report.add(
                ValidationSeverity.WARNING,
                f"factions.yaml.{edge.source_faction_id}.relations.{edge.target_faction_id}",
                f"Duplicate faction relation edge: {edge.source_faction_id} -> {edge.target_faction_id}",
                code="duplicate_faction_relation",
                ref_id=edge.target_faction_id,
                suggestion="Keep one relation edge for each source/target pair.",
            )
        seen.add(key)


def _with_relationship_previews(graph: SocialAuthoringGraph) -> SocialAuthoringGraph:
    relationships = [
        relationship.model_copy(update={"rp_tone_preview": _tone_preview_from_edge(relationship)})
        for relationship in graph.relationship_graph.relationships
    ]
    relationship_graph = graph.relationship_graph.model_copy(
        update={
            "npc_nodes": graph.relationship_graph.nodes,
            "relationship_edges": relationships,
            "relationships": relationships,
            "relationship_tone_presets": _relationship_tone_presets(),
        }
    )
    return graph.model_copy(update={"relationship_graph": relationship_graph})


def _tone_preview_from_edge(edge: RelationshipAuthoringEdge) -> RelationshipTonePreview:
    return _tone_preview_from_payload(edge.model_dump(mode="json"))


def _tone_preview_from_payload(payload: dict[str, Any]) -> RelationshipTonePreview:
    state = RelationshipState(
        id=str(payload.get("id") or "preview"),
        source_id=str(payload.get("source_id") or "source"),
        target_id=str(payload.get("target_id") or "target"),
        relation_type=str(payload.get("relation_type") or "general"),
        trust=int(payload.get("trust") or 0),
        fear=int(payload.get("fear") or 0),
        affinity=int(payload.get("affinity") or 0),
        obligation=int(payload.get("obligation") or 0),
        tags=list(payload.get("tags") or []),
        known_by_player=bool(payload.get("known_by_player") or False),
    )
    tone = derive_tone_from_relationship(state)
    preset_id = str(payload.get("tone_preset") or "derived")
    return RelationshipTonePreview(
        preset_id=preset_id,
        summary=tone_summary_for_prompt(tone),
        address_style=tone.address_style,
        formality=tone.formality,
        warmth=tone.warmth,
        tension=tone.tension,
        intimacy=tone.intimacy,
        respect=tone.respect,
        resentment=tone.resentment,
        fear=tone.fear,
        avoidance=tone.avoidance,
        trust_expression=tone.trust_expression,
    )


def _relationship_tone_presets() -> list[RelationshipTonePreset]:
    return [
        RelationshipTonePreset(id="derived", label="Derived", description="Compute RP tone from relationship values."),
        RelationshipTonePreset(id="guarded", label="Guarded", description="Reserved, tense, low trust delivery."),
        RelationshipTonePreset(id="warm", label="Warm", description="Friendly, lower formality delivery."),
        RelationshipTonePreset(id="fearful", label="Fearful", description="Cautious address with high avoidance."),
    ]


def _add_relationship_authoring_validation(graph: RelationshipAuthoringGraph, report: ValidationReport) -> None:
    actor_ids = {node.id for node in graph.nodes}
    seen: set[tuple[str, str, str]] = set()
    preset_ids = {preset.id for preset in _relationship_tone_presets()}
    for relationship in graph.relationships:
        relationship_key = (relationship.source_id, relationship.target_id, relationship.relation_type)
        if relationship_key in seen:
            report.add(
                ValidationSeverity.ERROR,
                f"relationships.yaml.{relationship.id}",
                f"Duplicate relationship edge: {relationship.source_id} -> {relationship.target_id} ({relationship.relation_type})",
                code="duplicate_relationship_edge",
                ref_id=relationship.id,
                suggestion="Use one edge per source/target/relation_type.",
            )
        seen.add(relationship_key)
        if relationship.source_id not in actor_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"relationships.yaml.{relationship.id}.source_id",
                f"Relationship source references missing NPC: {relationship.source_id}",
                code="relationship_missing_source",
                ref_id=relationship.source_id,
            )
        if relationship.target_id not in actor_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"relationships.yaml.{relationship.id}.target_id",
                f"Relationship target references missing NPC: {relationship.target_id}",
                code="relationship_missing_target",
                ref_id=relationship.target_id,
            )
        for field_name in ("trust", "fear", "affinity", "obligation"):
            value = getattr(relationship, field_name)
            if value < -100 or value > 100:
                report.add(
                    ValidationSeverity.ERROR,
                    f"relationships.yaml.{relationship.id}.{field_name}",
                    f"Relationship {field_name} must be between -100 and 100: {value}",
                    code=f"relationship_invalid_{field_name}",
                    ref_id=relationship.id,
                )
        if relationship.hidden_relationship and relationship.known_by_player:
            report.add(
                ValidationSeverity.ERROR,
                f"relationships.yaml.{relationship.id}.known_by_player",
                "Hidden relationship cannot be marked player-visible.",
                code="hidden_relationship_player_visible",
                ref_id=relationship.id,
                suggestion="Clear known_by_player before saving a hidden relationship.",
            )
        if relationship.tone_preset and relationship.tone_preset not in preset_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"relationships.yaml.{relationship.id}.tone_preset",
                f"Unknown RP tone preset: {relationship.tone_preset}",
                code="relationship_invalid_tone_preset",
                ref_id=relationship.tone_preset,
                suggestion="Use one of the relationship_tone_presets ids.",
            )
