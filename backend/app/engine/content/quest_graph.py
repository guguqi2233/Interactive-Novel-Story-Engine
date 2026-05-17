from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.world_loader import QuestDef


class QuestGraphError(ValueError):
    """Raised when quest graph authoring input is invalid."""


class QuestObjectiveNode(BaseModel):
    id: str
    text: str


class QuestStageNode(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[QuestObjectiveNode] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)


class QuestTriggerNode(BaseModel):
    type: str
    id: str
    action: str
    objective_id: str | None = None
    next_stage: str | None = None


class QuestGraphNode(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    visibility: str
    stages: list[QuestStageNode] = Field(default_factory=list)
    triggers: list[QuestTriggerNode] = Field(default_factory=list)


class QuestGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    quest_id: str
    label: str | None = None


class QuestGraph(BaseModel):
    world_id: str
    quests: list[QuestGraphNode] = Field(default_factory=list)
    edges: list[QuestGraphEdge] = Field(default_factory=list)


class QuestGraphPreview(BaseModel):
    world_id: str
    graph: QuestGraph
    yaml_content: str


def parse_quest_graph(world_id: str, authoring_service: ContentAuthoringService) -> QuestGraph:
    try:
        content = authoring_service.read_file(world_id, "quests.yaml")
    except AuthoringError as exc:
        raise QuestGraphError(str(exc)) from exc
    return quest_yaml_to_graph(world_id, content)


def preview_quest_graph(
    world_id: str,
    graph: QuestGraph,
    authoring_service: ContentAuthoringService,
) -> QuestGraphPreview:
    if graph.world_id != world_id:
        raise QuestGraphError("Quest graph world_id does not match request world_id")
    yaml_content = quest_graph_to_yaml(graph)
    # Reuse existing draft validation. This writes nothing and catches invalid edges.
    authoring_service.validate_draft(world_id, "quests.yaml", yaml_content)
    return QuestGraphPreview(world_id=world_id, graph=graph, yaml_content=yaml_content)


def quest_yaml_to_graph(world_id: str, content: str) -> QuestGraph:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise QuestGraphError(f"Invalid quests.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise QuestGraphError("Expected quests.yaml to contain a mapping")
    raw_quests = data.get("quests", [])
    if not isinstance(raw_quests, list):
        raise QuestGraphError("Expected quests.yaml key 'quests' to be a list")

    quests: list[QuestGraphNode] = []
    edges: list[QuestGraphEdge] = []
    for raw_quest in raw_quests:
        try:
            quest = QuestDef.model_validate(raw_quest)
        except ValidationError as exc:
            raise QuestGraphError(f"Quest schema validation failed: {exc}") from exc
        stages = [
            QuestStageNode(
                id=stage.id,
                title=stage.title,
                description=stage.description,
                objectives=[QuestObjectiveNode(id=objective, text=objective) for objective in stage.objectives],
                next_stages=stage.next_stages,
            )
            for stage in quest.stages
        ]
        triggers = [
            QuestTriggerNode(
                type=trigger.type.value,
                id=trigger.id,
                action=trigger.action.value,
                objective_id=trigger.objective_id,
                next_stage=trigger.next_stage,
            )
            for trigger in quest.triggers
        ]
        quests.append(
            QuestGraphNode(
                id=quest.id,
                title=quest.title,
                description=quest.description,
                initial_stage=quest.initial_stage,
                visibility=quest.visibility.value,
                stages=stages,
                triggers=triggers,
            )
        )
        for stage in quest.stages:
            for target_stage in stage.next_stages:
                edges.append(
                    QuestGraphEdge(
                        source=f"{quest.id}:{stage.id}",
                        target=f"{quest.id}:{target_stage}",
                        type="next_stage",
                        quest_id=quest.id,
                    )
                )
        for trigger in quest.triggers:
            if trigger.next_stage:
                edges.append(
                    QuestGraphEdge(
                        source=f"trigger:{quest.id}:{trigger.type.value}:{trigger.id}",
                        target=f"{quest.id}:{trigger.next_stage}",
                        type="trigger_next_stage",
                        quest_id=quest.id,
                        label=trigger.action.value,
                    )
                )
    return QuestGraph(world_id=world_id, quests=quests, edges=edges)


def quest_graph_to_yaml(graph: QuestGraph) -> str:
    quests: list[dict[str, Any]] = []
    for quest in graph.quests:
        quests.append(
            {
                "id": quest.id,
                "title": quest.title,
                "description": quest.description,
                "initial_stage": quest.initial_stage,
                "visibility": quest.visibility,
                "stages": [
                    {
                        "id": stage.id,
                        "title": stage.title,
                        "description": stage.description,
                        "objectives": [objective.text for objective in stage.objectives],
                        "next_stages": stage.next_stages,
                    }
                    for stage in quest.stages
                ],
                "triggers": [
                    _trigger_to_mapping(trigger)
                    for trigger in quest.triggers
                ],
            }
        )
    return yaml.safe_dump({"quests": quests}, sort_keys=False, allow_unicode=True)


def _trigger_to_mapping(trigger: QuestTriggerNode) -> dict[str, Any]:
    data: dict[str, Any] = {
        "type": trigger.type,
        "id": trigger.id,
        "action": trigger.action,
    }
    if trigger.objective_id:
        data["objective_id"] = trigger.objective_id
    if trigger.next_stage:
        data["next_stage"] = trigger.next_stage
    return data
