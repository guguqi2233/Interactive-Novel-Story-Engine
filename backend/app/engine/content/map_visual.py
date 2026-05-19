from collections.abc import Iterable

from app.engine.content.world_loader import (
    LocationDef,
    MapVisualEdge,
    MapVisualEdgeType,
    MapVisualGraph,
    MapVisualLayer,
    MapVisualNode,
    MapVisualRegion,
    MapVisibility,
    WorldPack,
)


def build_authoring_map_visual_graph(pack: WorldPack) -> MapVisualGraph:
    """Build the complete authoring map graph without mutating the content pack."""
    edges = _edges_from_locations(pack.locations)
    graph = MapVisualGraph(
        nodes=[_node_from_location(location, index) for index, location in enumerate(pack.locations)],
        edges=edges,
        regions=_regions_from_locations(pack.locations),
        layers=_layers_from_locations(pack.locations),
        conditional_edges=[edge for edge in edges if edge.edge_type == MapVisualEdgeType.CONDITIONAL],
        locked_edges=[edge for edge in edges if edge.edge_type == MapVisualEdgeType.LOCKED],
        hidden_edges=[
            edge
            for edge in edges
            if edge.edge_type == MapVisualEdgeType.HIDDEN or edge.visibility == MapVisibility.HIDDEN
        ],
    )
    return graph


def build_player_visible_map_visual_graph(
    pack: WorldPack,
    known_location_ids: Iterable[str],
) -> MapVisualGraph:
    """Build a player-safe map graph from known locations only."""
    known_ids = set(known_location_ids)
    authoring_graph = build_authoring_map_visual_graph(pack)
    visible_nodes = [
        node
        for node in authoring_graph.nodes
        if node.location_id in known_ids and node.visibility != MapVisibility.HIDDEN
    ]
    visible_location_ids = {node.location_id for node in visible_nodes}
    visible_edges = [
        edge
        for edge in authoring_graph.edges
        if edge.visibility != MapVisibility.HIDDEN
        and edge.source_location_id in visible_location_ids
        and edge.target_location_id in visible_location_ids
    ]
    return MapVisualGraph(
        nodes=visible_nodes,
        edges=visible_edges,
        regions=[
            region
            for region in authoring_graph.regions
            if any(node.region_id == region.id for node in visible_nodes)
        ],
        layers=[
            layer
            for layer in authoring_graph.layers
            if any(node.layer_id == layer.id for node in visible_nodes)
        ],
    )


def _node_from_location(location: LocationDef, index: int) -> MapVisualNode:
    visual = location.visual
    return MapVisualNode(
        id=location.id,
        name=location.name,
        location_id=location.id,
        x=visual.x if visual else float(index * 160),
        y=visual.y if visual else 0.0,
        region_id=visual.region_id if visual else None,
        layer_id=visual.layer_id if visual else None,
        tags=list(visual.tags) if visual else [],
        visibility=visual.visibility if visual else MapVisibility.PUBLIC,
        icon=visual.icon if visual else None,
        color_tag=visual.color_tag if visual else None,
        display_group=visual.display_group if visual else None,
    )


def _edges_from_locations(locations: list[LocationDef]) -> list[MapVisualEdge]:
    by_id = {location.id: location for location in locations}
    edges: list[MapVisualEdge] = []
    for source in locations:
        for label, target_location_id in sorted(source.exits.items()):
            target = by_id.get(target_location_id)
            metadata = source.exit_metadata.get(label)
            inferred_type = _edge_type(source, target)
            inferred_visibility = _edge_visibility(source, target)
            edges.append(
                MapVisualEdge(
                    source_location_id=source.id,
                    target_location_id=target_location_id,
                    edge_type=metadata.edge_type if metadata else inferred_type,
                    label=label,
                    visibility=metadata.visibility if metadata else inferred_visibility,
                    travel_cost=metadata.travel_cost if metadata else 1,
                    discovery_rules=list(metadata.discovery_rules) if metadata else [],
                    unlock_condition=metadata.unlock_condition if metadata else None,
                )
            )
    return edges


def _regions_from_locations(locations: list[LocationDef]) -> list[MapVisualRegion]:
    region_ids = sorted(
        {
            location.visual.region_id
            for location in locations
            if location.visual and location.visual.region_id
        }
    )
    return [MapVisualRegion(id=region_id, name=region_id.replace("_", " ").title()) for region_id in region_ids]


def _layers_from_locations(locations: list[LocationDef]) -> list[MapVisualLayer]:
    layer_ids = sorted(
        {
            location.visual.layer_id
            for location in locations
            if location.visual and location.visual.layer_id
        }
    )
    return [
        MapVisualLayer(id=layer_id, name=layer_id.replace("_", " ").title(), order=index)
        for index, layer_id in enumerate(layer_ids)
    ]


def _edge_type(source: LocationDef, target: LocationDef | None) -> MapVisualEdgeType:
    if target is None:
        return MapVisualEdgeType.EXIT
    source_visibility = source.visual.visibility if source.visual else MapVisibility.PUBLIC
    target_visibility = target.visual.visibility if target.visual else MapVisibility.PUBLIC
    if source_visibility == MapVisibility.HIDDEN or target_visibility == MapVisibility.HIDDEN:
        return MapVisualEdgeType.HIDDEN
    return MapVisualEdgeType.EXIT if source.id in target.exits.values() else MapVisualEdgeType.ONE_WAY


def _edge_visibility(source: LocationDef, target: LocationDef | None) -> MapVisibility:
    if target is None:
        return MapVisibility.PUBLIC
    source_visibility = source.visual.visibility if source.visual else MapVisibility.PUBLIC
    target_visibility = target.visual.visibility if target.visual else MapVisibility.PUBLIC
    if source_visibility == MapVisibility.HIDDEN or target_visibility == MapVisibility.HIDDEN:
        return MapVisibility.HIDDEN
    if (
        source_visibility == MapVisibility.DISCOVERABLE
        or target_visibility == MapVisibility.DISCOVERABLE
    ):
        return MapVisibility.DISCOVERABLE
    return MapVisibility.PUBLIC
