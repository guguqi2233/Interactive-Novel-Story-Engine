from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.world_state import NPCGoalState
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.validator import ValidationReport
from app.engine.content.world_loader import NPCDef


class NPCGoalAuthoringError(ValueError):
    """Raised when NPC goal authoring input is invalid."""


class NPCGoalAuthoringNode(BaseModel):
    npc_id: str
    name: str
    hidden: bool = False
    goals: list[NPCGoalState] = Field(default_factory=list)
    priorities: dict[str, int] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    current_goal_id: str | None = None
    plan_state: dict[str, Any] = Field(default_factory=dict)


class NPCGoalAuthoringGraph(BaseModel):
    world_id: str
    npcs: list[NPCGoalAuthoringNode] = Field(default_factory=list)


class NPCGoalAuthoringPreview(BaseModel):
    world_id: str
    graph: NPCGoalAuthoringGraph
    yaml_content: str
    validation: ValidationReport
    confirmation_required: bool = False


def parse_npc_goal_graph(
    world_id: str,
    authoring_service: ContentAuthoringService,
) -> NPCGoalAuthoringGraph:
    try:
        content = authoring_service.read_file(world_id, "npcs.yaml")
    except AuthoringError as exc:
        raise NPCGoalAuthoringError(str(exc)) from exc
    return npc_yaml_to_goal_graph(world_id, content)


def preview_npc_goal_graph(
    world_id: str,
    graph: NPCGoalAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> NPCGoalAuthoringPreview:
    if graph.world_id != world_id:
        raise NPCGoalAuthoringError("NPC goal graph world_id does not match request world_id")
    yaml_content = npc_goal_graph_to_yaml(world_id, graph, authoring_service)
    validation = authoring_service.validate_draft(world_id, "npcs.yaml", yaml_content)
    return NPCGoalAuthoringPreview(
        world_id=world_id,
        graph=graph,
        yaml_content=yaml_content,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_npc_goal_graph(
    world_id: str,
    graph: NPCGoalAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> ValidationReport:
    return preview_npc_goal_graph(world_id, graph, authoring_service).validation


def save_npc_goal_graph(
    world_id: str,
    graph: NPCGoalAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> ValidationReport:
    preview = preview_npc_goal_graph(world_id, graph, authoring_service)
    if not preview.validation.ok:
        return preview.validation
    return authoring_service.write_file(world_id, "npcs.yaml", preview.yaml_content)


def npc_yaml_to_goal_graph(world_id: str, content: str) -> NPCGoalAuthoringGraph:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise NPCGoalAuthoringError(f"Invalid npcs.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise NPCGoalAuthoringError("Expected npcs.yaml to contain a mapping")
    raw_npcs = data.get("npcs", [])
    if not isinstance(raw_npcs, list):
        raise NPCGoalAuthoringError("Expected npcs.yaml key 'npcs' to be a list")

    nodes: list[NPCGoalAuthoringNode] = []
    for raw_npc in raw_npcs:
        try:
            npc = NPCDef.model_validate(raw_npc)
        except ValidationError as exc:
            raise NPCGoalAuthoringError(f"NPC schema validation failed: {exc}") from exc
        nodes.append(
            NPCGoalAuthoringNode(
                npc_id=npc.id,
                name=npc.name,
                hidden=npc.hidden,
                goals=[goal for goal in npc.goals if isinstance(goal, NPCGoalState)],
                priorities=npc.priorities,
                constraints=npc.constraints,
                current_goal_id=npc.current_goal_id,
                plan_state=npc.plan_state,
            )
        )
    return NPCGoalAuthoringGraph(world_id=world_id, npcs=nodes)


def npc_goal_graph_to_yaml(
    world_id: str,
    graph: NPCGoalAuthoringGraph,
    authoring_service: ContentAuthoringService,
) -> str:
    try:
        data = yaml.safe_load(authoring_service.read_file(world_id, "npcs.yaml")) or {}
    except (AuthoringError, yaml.YAMLError) as exc:
        raise NPCGoalAuthoringError(f"Cannot read existing npcs.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise NPCGoalAuthoringError("Expected npcs.yaml to contain a mapping")
    raw_npcs = data.get("npcs", [])
    if not isinstance(raw_npcs, list):
        raise NPCGoalAuthoringError("Expected npcs.yaml key 'npcs' to be a list")

    graph_by_id = {node.npc_id: node for node in graph.npcs}
    updated_npcs: list[dict[str, Any]] = []
    for raw_npc in raw_npcs:
        if not isinstance(raw_npc, dict):
            updated_npcs.append(raw_npc)
            continue
        npc_id = str(raw_npc.get("id", ""))
        node = graph_by_id.get(npc_id)
        if node is None:
            updated_npcs.append(raw_npc)
            continue
        updated = dict(raw_npc)
        updated["goals"] = [goal.model_dump(mode="json") for goal in node.goals]
        updated["priorities"] = node.priorities
        updated["constraints"] = node.constraints
        updated["current_goal_id"] = node.current_goal_id
        updated["plan_state"] = node.plan_state
        updated_npcs.append(updated)

    data["npcs"] = updated_npcs
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
