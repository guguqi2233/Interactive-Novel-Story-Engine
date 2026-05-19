from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.world_state import GameState
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.content.world_loader import (
    MapVisualEdge,
    MapVisualEdgeType,
    MapVisualGraph,
    MapVisualLayer,
    MapVisualNode,
    MapVisualRegion,
    MapVisibility,
)


class LocationClusterTemplateError(ValueError):
    """Raised when a location cluster template is invalid or unsafe."""


class LocationClusterTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    cluster_type: str
    required_variables: list[str] = Field(default_factory=list)
    location_nodes: list[MapVisualNode] = Field(default_factory=list)
    exit_edges: list[MapVisualEdge] = Field(default_factory=list)
    optional_hidden_edges: list[MapVisualEdge] = Field(default_factory=list)
    default_visual_layout: str = "grid"
    tags: list[str] = Field(default_factory=list)


class LocationClusterPreviewRequest(BaseModel):
    target_world_id: str
    variables: dict[str, str] = Field(default_factory=dict)
    confirm_apply: bool = False
    confirm_warnings: bool = False


class LocationClusterPreview(BaseModel):
    template: LocationClusterTemplate
    target_world_id: str
    graph: MapVisualGraph
    validation: ValidationReport
    yaml_content: str = ""
    writes_to_disk: bool = False
    applied: bool = False
    active_game_state_changed: bool = False
    confirmation_required: bool = False


class LocationClusterTemplateList(BaseModel):
    local_only: bool = True
    templates: list[LocationClusterTemplate] = Field(default_factory=list)


def list_location_cluster_templates() -> list[LocationClusterTemplate]:
    return [LocationClusterTemplate.model_validate(item) for item in _BUILT_IN_TEMPLATES]


def get_location_cluster_template(template_id: str) -> LocationClusterTemplate:
    for template in list_location_cluster_templates():
        if template.id == template_id:
            return template
    raise LocationClusterTemplateError(f"Unknown location cluster template: {template_id}")


def preview_location_cluster_template(
    template: LocationClusterTemplate,
    request: LocationClusterPreviewRequest,
    service: ContentAuthoringService,
    *,
    active_state: GameState | None = None,
) -> LocationClusterPreview:
    before = active_state.model_dump(mode="json") if active_state is not None else None
    report = ValidationReport(world_id=request.target_world_id)
    _validate_variables(template, request.variables, report)
    rendered = _render_template(template, request.variables)
    _validate_template_edges(rendered, report)
    graph = _merge_with_world_graph(request.target_world_id, rendered, service, report) if not report.errors else rendered
    yaml_content = service.map_graph_to_locations_yaml(request.target_world_id, graph) if not report.errors else ""
    if not report.errors:
        draft_report = service.validate_draft(request.target_world_id, "locations.yaml", yaml_content)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
        from app.engine.content.authoring_service import _add_map_graph_validation_issues

        _add_map_graph_validation_issues(graph, report)
    after = active_state.model_dump(mode="json") if active_state is not None else None
    return LocationClusterPreview(
        template=template,
        target_world_id=request.target_world_id,
        graph=graph,
        validation=report,
        yaml_content=yaml_content,
        writes_to_disk=False,
        applied=False,
        active_game_state_changed=before != after if before is not None else False,
        confirmation_required=report.ok and bool(report.warnings),
    )


def preview_location_cluster(
    template_id: str,
    request: LocationClusterPreviewRequest,
    service: ContentAuthoringService,
) -> LocationClusterPreview:
    return preview_location_cluster_template(get_location_cluster_template(template_id), request, service)


def apply_location_cluster_draft(
    template_id: str,
    request: LocationClusterPreviewRequest,
    service: ContentAuthoringService,
) -> LocationClusterPreview:
    preview = preview_location_cluster(template_id, request, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "location_cluster.apply",
            "Location cluster apply requires explicit confirmation.",
            code="location_cluster_apply_requires_confirmation",
        )
        preview.confirmation_required = True
        return preview
    if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        preview.confirmation_required = preview.validation.ok and bool(preview.validation.warnings)
        return preview
    validation = service.write_map_graph(
        request.target_world_id,
        preview.graph,
        confirm_warnings=request.confirm_warnings,
    )
    preview.validation = validation
    preview.writes_to_disk = validation.ok
    preview.applied = validation.ok
    preview.confirmation_required = validation.ok and bool(validation.warnings) and not request.confirm_warnings
    return preview


def _validate_variables(template: LocationClusterTemplate, variables: dict[str, str], report: ValidationReport) -> None:
    for variable in template.required_variables:
        if not variables.get(variable):
            report.add(
                ValidationSeverity.ERROR,
                f"location_cluster.{template.id}.variables.{variable}",
                f"Missing required variable: {variable}",
                code="location_cluster_missing_variable",
                ref_id=variable,
            )
    joined = "\n".join(variables.values()).lower()
    if any(token in joined for token in ("sk-", "api_key", ".env", "http://", "https://", "script")):
        report.add(
            ValidationSeverity.ERROR,
            f"location_cluster.{template.id}.variables",
            "Location cluster variables cannot contain API keys, scripts, remote URLs, or environment references.",
            code="location_cluster_unsafe_variable",
        )


def _render_template(template: LocationClusterTemplate, variables: dict[str, str]) -> MapVisualGraph:
    prefix = _slug(variables.get("prefix") or template.id)
    region = _slug(variables.get("region_id") or prefix)
    display = variables.get("display_name") or template.name
    nodes: list[MapVisualNode] = []
    for node in template.location_nodes:
        node_id = _render_id(node.location_id, prefix)
        nodes.append(
            node.model_copy(
                update={
                    "id": node_id,
                    "location_id": node_id,
                    "name": node.name.replace("{name}", display),
                    "region_id": node.region_id or region,
                    "tags": sorted(set([*node.tags, *template.tags])),
                }
            )
        )
    edges = [_render_edge(edge, prefix, hidden=False) for edge in template.exit_edges]
    hidden_edges = [_render_edge(edge, prefix, hidden=True) for edge in template.optional_hidden_edges]
    return MapVisualGraph(
        nodes=nodes,
        edges=[*edges, *hidden_edges],
        regions=[MapVisualRegion(id=region, name=display)],
        layers=[MapVisualLayer(id="surface", name="Surface", order=0)],
        hidden_edges=hidden_edges,
    )


def _render_edge(edge: MapVisualEdge, prefix: str, *, hidden: bool) -> MapVisualEdge:
    rendered = edge.model_copy(
        update={
            "source_location_id": _render_id(edge.source_location_id, prefix),
            "target_location_id": _render_id(edge.target_location_id, prefix),
            "edge_type": MapVisualEdgeType.HIDDEN if hidden else edge.edge_type,
            "visibility": MapVisibility.HIDDEN if hidden else edge.visibility,
        }
    )
    return rendered


def _render_id(value: str, prefix: str) -> str:
    return value.replace("{prefix}", prefix)


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value.strip()).strip("_") or "cluster"


def _validate_template_edges(graph: MapVisualGraph, report: ValidationReport) -> None:
    node_ids = {node.location_id for node in graph.nodes}
    for edge in graph.edges:
        if edge.source_location_id not in node_ids or edge.target_location_id not in node_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"location_cluster.edges.{edge.label}",
                "Cluster edge references a missing generated location.",
                code="location_cluster_invalid_edge",
                ref_id=f"{edge.source_location_id}->{edge.target_location_id}",
            )
        if edge.edge_type == MapVisualEdgeType.HIDDEN and edge.visibility != MapVisibility.HIDDEN:
            report.add(
                ValidationSeverity.ERROR,
                f"location_cluster.edges.{edge.label}",
                "Hidden cluster edges must be marked hidden.",
                code="location_cluster_hidden_edge_not_hidden",
            )


def _merge_with_world_graph(
    world_id: str,
    cluster_graph: MapVisualGraph,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> MapVisualGraph:
    current = service.get_map_graph(world_id)
    current_ids = {node.location_id for node in current.nodes}
    for node in cluster_graph.nodes:
        if node.location_id in current_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"location_cluster.nodes.{node.location_id}",
                f"Location already exists: {node.location_id}",
                code="location_cluster_duplicate_location",
                ref_id=node.location_id,
            )
    return MapVisualGraph(
        nodes=[*current.nodes, *cluster_graph.nodes],
        edges=[*current.edges, *cluster_graph.edges],
        regions=[*current.regions, *cluster_graph.regions],
        layers=current.layers or cluster_graph.layers,
        hidden_edges=[*current.hidden_edges, *cluster_graph.hidden_edges],
    )


def _node(location_id: str, name: str, x: float, y: float) -> dict[str, Any]:
    return {
        "id": location_id,
        "name": name,
        "location_id": location_id,
        "x": x,
        "y": y,
        "region_id": None,
        "layer_id": "surface",
        "tags": [],
        "visibility": "public",
        "icon": "marker",
    }


def _edge(source: str, target: str, label: str) -> dict[str, Any]:
    return {
        "source_location_id": source,
        "target_location_id": target,
        "edge_type": "exit",
        "label": label,
        "visibility": "public",
        "travel_cost": 1,
    }


_BUILT_IN_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "village_cluster",
        "name": "Village Cluster",
        "cluster_type": "village",
        "required_variables": ["prefix"],
        "location_nodes": [
            _node("{prefix}_square", "{name} Square", 0, 0),
            _node("{prefix}_market", "{name} Market", 160, 0),
            _node("{prefix}_shrine", "{name} Shrine", 0, -140),
        ],
        "exit_edges": [
            _edge("{prefix}_square", "{prefix}_market", "east"),
            _edge("{prefix}_market", "{prefix}_square", "west"),
            _edge("{prefix}_square", "{prefix}_shrine", "north"),
            _edge("{prefix}_shrine", "{prefix}_square", "south"),
        ],
        "optional_hidden_edges": [
            {**_edge("{prefix}_market", "{prefix}_shrine", "hidden_path"), "edge_type": "hidden", "visibility": "hidden", "discovery_rules": ["authoring:hidden_path"]}
        ],
        "default_visual_layout": "triangle",
        "tags": ["settlement", "starter"],
    },
    {
        "id": "basement_cluster",
        "name": "Basement Cluster",
        "cluster_type": "basement",
        "required_variables": ["prefix"],
        "location_nodes": [
            _node("{prefix}_stairs", "{name} Stairs", 0, 0),
            _node("{prefix}_storage", "{name} Storage", 160, 0),
            _node("{prefix}_locked_room", "{name} Locked Room", 320, 0),
        ],
        "exit_edges": [
            _edge("{prefix}_stairs", "{prefix}_storage", "east"),
            _edge("{prefix}_storage", "{prefix}_stairs", "west"),
            {**_edge("{prefix}_storage", "{prefix}_locked_room", "locked_door"), "edge_type": "locked", "unlock_condition": "key:basement_key"},
        ],
        "optional_hidden_edges": [],
        "default_visual_layout": "line",
        "tags": ["interior", "underground"],
    },
]
