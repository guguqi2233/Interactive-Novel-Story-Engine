from collections import defaultdict, deque
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.authoring_boundary import AuthoringSaveDecision, default_authoring_boundary_policy
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.content.world_loader import QuestDef


class QuestGraphError(ValueError):
    """Raised when quest graph authoring input is invalid."""


class ObjectiveNode(BaseModel):
    id: str
    text: str
    visibility: str = "public"
    hidden_authoring_note: str | None = None
    x: float = 0.0
    y: float = 0.0


class StageNode(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[ObjectiveNode] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)
    failure_stages: list[str] = Field(default_factory=list)
    alternate_stages: list[str] = Field(default_factory=list)
    x: float = 0.0
    y: float = 0.0


class TriggerNode(BaseModel):
    type: str
    id: str
    action: str
    objective_id: str | None = None
    next_stage: str | None = None
    x: float = 0.0
    y: float = 0.0


class RewardNode(BaseModel):
    id: str
    text: str
    reward_type: str = "generic"
    x: float = 0.0
    y: float = 0.0


class ConsequenceNode(BaseModel):
    id: str
    text: str
    consequence_type: str = "generic"
    x: float = 0.0
    y: float = 0.0


class QuestNode(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    visibility: str
    stages: list[StageNode] = Field(default_factory=list)
    triggers: list[TriggerNode] = Field(default_factory=list)
    rewards: list[RewardNode] = Field(default_factory=list)
    consequences: list[ConsequenceNode] = Field(default_factory=list)
    x: float = 0.0
    y: float = 0.0


class QuestGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    quest_id: str
    label: str | None = None
    source_stage_id: str | None = None
    target_stage_id: str | None = None
    condition: dict[str, str] | None = None


class QuestGraph(BaseModel):
    world_id: str
    quests: list[QuestNode] = Field(default_factory=list)
    edges: list[QuestGraphEdge] = Field(default_factory=list)
    quest_nodes: list[QuestNode] = Field(default_factory=list)
    stage_nodes: list[StageNode] = Field(default_factory=list)
    objective_nodes: list[ObjectiveNode] = Field(default_factory=list)
    trigger_nodes: list[TriggerNode] = Field(default_factory=list)
    reward_nodes: list[RewardNode] = Field(default_factory=list)
    consequence_nodes: list[ConsequenceNode] = Field(default_factory=list)
    failure_path_edges: list[QuestGraphEdge] = Field(default_factory=list)
    optional_path_edges: list[QuestGraphEdge] = Field(default_factory=list)


class QuestGraphPreview(BaseModel):
    world_id: str
    graph: QuestGraph
    yaml_content: str
    validation: ValidationReport
    confirmation_required: bool = False


QuestObjectiveNode = ObjectiveNode
QuestStageNode = StageNode
QuestTriggerNode = TriggerNode
QuestRewardNode = RewardNode
QuestConsequenceNode = ConsequenceNode
QuestGraphNode = QuestNode


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
    graph = _with_derived_graph_nodes(graph)
    yaml_content = quest_graph_to_yaml(graph)
    validation = validate_quest_graph(world_id, graph, authoring_service)
    return QuestGraphPreview(
        world_id=world_id,
        graph=graph,
        yaml_content=yaml_content,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def save_quest_graph(
    world_id: str,
    graph: QuestGraph,
    authoring_service: ContentAuthoringService,
    *,
    confirm_warnings: bool = False,
) -> ValidationReport:
    preview = preview_quest_graph(world_id, graph, authoring_service)
    if not preview.validation.ok:
        return preview.validation
    decision = default_authoring_boundary_policy().decide_save(
        preview.validation,
        confirm_warnings=confirm_warnings,
    )
    if decision != AuthoringSaveDecision.ALLOW:
        return preview.validation
    return authoring_service.write_file(
        world_id,
        "quests.yaml",
        preview.yaml_content,
        confirm_warnings=confirm_warnings,
    )


def validate_quest_graph(
    world_id: str,
    graph: QuestGraph,
    authoring_service: ContentAuthoringService,
) -> ValidationReport:
    yaml_content = quest_graph_to_yaml(graph)
    report = authoring_service.validate_draft(world_id, "quests.yaml", yaml_content)
    _add_graph_validation_issues(graph, report)
    return report


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

    quests: list[QuestNode] = []
    edges: list[QuestGraphEdge] = []
    for raw_quest in raw_quests:
        try:
            quest = QuestDef.model_validate(raw_quest)
        except ValidationError as exc:
            raise QuestGraphError(f"Quest schema validation failed: {exc}") from exc
        raw_stage_by_id = {
            str(raw_stage.get("id")): raw_stage
            for raw_stage in raw_quest.get("stages", [])
            if isinstance(raw_stage, dict)
        }
        stages = [
            StageNode(
                id=stage.id,
                title=stage.title,
                description=stage.description,
                objectives=[
                    _objective_node(objective, index=index)
                    for index, objective in enumerate(
                        raw_stage_by_id.get(stage.id, {}).get("objectives", stage.objectives)
                    )
                ],
                next_stages=stage.next_stages,
                failure_stages=stage.failure_stages,
                alternate_stages=stage.alternate_stages,
            )
            for stage in quest.stages
        ]
        triggers = [
            TriggerNode(
                type=trigger.type.value,
                id=trigger.id,
                action=trigger.action.value,
                objective_id=trigger.objective_id,
                next_stage=trigger.next_stage,
            )
            for trigger in quest.triggers
        ]
        rewards = [_reward_node(raw_reward) for raw_reward in raw_quest.get("rewards", [])]
        consequences = [_consequence_node(raw_consequence) for raw_consequence in raw_quest.get("consequences", [])]
        quests.append(
            QuestNode(
                id=quest.id,
                title=quest.title,
                description=quest.description,
                initial_stage=quest.initial_stage,
                visibility=quest.visibility.value,
                stages=stages,
                triggers=triggers,
                rewards=rewards,
                consequences=consequences,
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
                        source_stage_id=stage.id,
                        target_stage_id=target_stage,
                    )
                )
            for target_stage in stage.failure_stages:
                edges.append(
                    QuestGraphEdge(
                        source=f"{quest.id}:{stage.id}",
                        target=f"{quest.id}:{target_stage}",
                        type="failure_path",
                        quest_id=quest.id,
                        label="failure",
                        source_stage_id=stage.id,
                        target_stage_id=target_stage,
                    )
                )
            for target_stage in stage.alternate_stages:
                edges.append(
                    QuestGraphEdge(
                        source=f"{quest.id}:{stage.id}",
                        target=f"{quest.id}:{target_stage}",
                        type="alternate_path",
                        quest_id=quest.id,
                        label="alternate",
                        source_stage_id=stage.id,
                        target_stage_id=target_stage,
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
                        target_stage_id=trigger.next_stage,
                        condition={"type": trigger.type.value, "id": trigger.id},
                    )
                )
    return _with_derived_graph_nodes(QuestGraph(world_id=world_id, quests=quests, edges=edges))


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
                        "objectives": [_objective_to_mapping(objective) for objective in stage.objectives],
                        "next_stages": stage.next_stages,
                        **({"failure_stages": stage.failure_stages} if stage.failure_stages else {}),
                        **({"alternate_stages": stage.alternate_stages} if stage.alternate_stages else {}),
                    }
                    for stage in quest.stages
                ],
                "triggers": [
                    _trigger_to_mapping(trigger)
                    for trigger in quest.triggers
                ],
                **({"rewards": [_reward_to_mapping(reward) for reward in quest.rewards]} if quest.rewards else {}),
                **(
                    {"consequences": [_consequence_to_mapping(consequence) for consequence in quest.consequences]}
                    if quest.consequences
                    else {}
                ),
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


def _reward_node(raw_reward: Any) -> RewardNode:
    if isinstance(raw_reward, str):
        return RewardNode(id=raw_reward, text=raw_reward)
    if isinstance(raw_reward, dict):
        reward_id = str(raw_reward.get("id") or raw_reward.get("text") or "reward")
        return RewardNode(
            id=reward_id,
            text=str(raw_reward.get("text") or reward_id),
            reward_type=str(raw_reward.get("type") or raw_reward.get("reward_type") or "generic"),
        )
    return RewardNode(id=str(raw_reward), text=str(raw_reward))


def _objective_node(raw_objective: Any, *, index: int = 0) -> ObjectiveNode:
    if isinstance(raw_objective, str):
        return ObjectiveNode(id=raw_objective, text=raw_objective, x=160.0 * index, y=160.0)
    if isinstance(raw_objective, dict):
        objective_id = str(raw_objective.get("id") or raw_objective.get("text") or "objective")
        return ObjectiveNode(
            id=objective_id,
            text=str(raw_objective.get("text") or objective_id),
            visibility=str(raw_objective.get("visibility") or "public"),
            hidden_authoring_note=raw_objective.get("hidden_authoring_note"),
            x=float(raw_objective.get("x") or 160.0 * index),
            y=float(raw_objective.get("y") or 160.0),
        )
    return ObjectiveNode(id=str(raw_objective), text=str(raw_objective), x=160.0 * index, y=160.0)


def _objective_to_mapping(objective: ObjectiveNode) -> str | dict[str, Any]:
    if objective.visibility == "public" and not objective.hidden_authoring_note:
        return objective.text
    data: dict[str, Any] = {
        "id": objective.id,
        "text": objective.text,
        "visibility": objective.visibility,
    }
    if objective.hidden_authoring_note:
        data["hidden_authoring_note"] = objective.hidden_authoring_note
    return data


def _reward_to_mapping(reward: RewardNode) -> str | dict[str, str]:
    if reward.reward_type == "generic" and reward.id == reward.text:
        return reward.text
    return {"id": reward.id, "text": reward.text, "type": reward.reward_type}


def _consequence_node(raw_consequence: Any) -> ConsequenceNode:
    if isinstance(raw_consequence, str):
        return ConsequenceNode(id=raw_consequence, text=raw_consequence)
    if isinstance(raw_consequence, dict):
        consequence_id = str(raw_consequence.get("id") or raw_consequence.get("text") or "consequence")
        return ConsequenceNode(
            id=consequence_id,
            text=str(raw_consequence.get("text") or consequence_id),
            consequence_type=str(raw_consequence.get("type") or raw_consequence.get("consequence_type") or "generic"),
        )
    return ConsequenceNode(id=str(raw_consequence), text=str(raw_consequence))


def _consequence_to_mapping(consequence: ConsequenceNode) -> str | dict[str, str]:
    if consequence.consequence_type == "generic" and consequence.id == consequence.text:
        return consequence.text
    return {"id": consequence.id, "text": consequence.text, "type": consequence.consequence_type}


def _with_derived_graph_nodes(graph: QuestGraph) -> QuestGraph:
    graph.quest_nodes = list(graph.quests)
    graph.stage_nodes = [stage for quest in graph.quests for stage in quest.stages]
    graph.objective_nodes = [objective for stage in graph.stage_nodes for objective in stage.objectives]
    graph.trigger_nodes = [trigger for quest in graph.quests for trigger in quest.triggers]
    graph.reward_nodes = [reward for quest in graph.quests for reward in quest.rewards]
    graph.consequence_nodes = [consequence for quest in graph.quests for consequence in quest.consequences]
    graph.failure_path_edges = [edge for edge in graph.edges if edge.type == "failure_path"]
    graph.optional_path_edges = [edge for edge in graph.edges if edge.type in {"alternate_path", "optional_path"}]
    return graph


def _add_graph_validation_issues(graph: QuestGraph, report: ValidationReport) -> None:
    for quest in graph.quests:
        stage_ids = {stage.id for stage in quest.stages}
        stage_by_id = {stage.id: stage for stage in quest.stages}
        objective_ids = {objective.id for stage in quest.stages for objective in stage.objectives}
        completion_objectives = {
            trigger.objective_id
            for trigger in quest.triggers
            if trigger.action == "complete_objective" and trigger.objective_id
        }
        if not stage_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.stages",
                f"Quest {quest.id} has no stages.",
                code="quest_has_no_stages",
                suggestion="Add at least one stage.",
            )
            continue
        if quest.initial_stage not in stage_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.initial_stage",
                f"Initial stage does not exist: {quest.initial_stage}",
                code="quest_missing_initial_stage",
                ref_id=quest.initial_stage,
            )
        adjacency: dict[str, set[str]] = defaultdict(set)
        incoming: dict[str, int] = {stage_id: 0 for stage_id in stage_ids}
        for stage in quest.stages:
            targets = [*stage.next_stages, *stage.failure_stages, *stage.alternate_stages]
            for target in targets:
                if target not in stage_ids:
                    continue
                adjacency[stage.id].add(target)
                incoming[target] = incoming.get(target, 0) + 1

        reachable = _reachable_stage_ids(quest.initial_stage, adjacency) if quest.initial_stage in stage_ids else set()
        for stage_id in sorted(stage_ids - reachable):
            report.add(
                ValidationSeverity.WARNING,
                f"quests.yaml.{quest.id}.stages.{stage_id}",
                f"Stage is not reachable from initial_stage: {stage_id}",
                code="quest_unreachable_stage",
                ref_id=stage_id,
                suggestion="Connect it from another stage or make it the initial stage.",
            )
        terminal_stages = [
            stage.id
            for stage in quest.stages
            if not stage.next_stages and not stage.failure_stages and not stage.alternate_stages
        ]
        if not terminal_stages:
            report.add(
                ValidationSeverity.WARNING,
                f"quests.yaml.{quest.id}.stages",
                f"Quest {quest.id} has no terminal stage.",
                code="quest_missing_terminal_stage",
                suggestion="Leave at least one final stage without outgoing stage transitions.",
            )
        if _has_cycle(stage_by_id, adjacency):
            report.add(
                ValidationSeverity.WARNING,
                f"quests.yaml.{quest.id}.stages",
                f"Quest {quest.id} has a circular stage path.",
                code="quest_circular_path",
                suggestion="Circular paths are allowed, but ensure runtime triggers cannot loop forever.",
            )
        for stage in quest.stages:
            for objective in stage.objectives:
                if objective.id not in completion_objectives:
                    report.add(
                        ValidationSeverity.WARNING,
                        f"quests.yaml.{quest.id}.stages.{stage.id}.objectives.{objective.id}",
                        f"Objective has no completion trigger path: {objective.id}",
                        code="quest_objective_without_completion_path",
                        ref_id=objective.id,
                        suggestion="Add a complete_objective trigger for this objective.",
                    )
                if objective.visibility == "hidden" and quest.visibility == "public":
                    report.add(
                        ValidationSeverity.WARNING,
                        f"quests.yaml.{quest.id}.stages.{stage.id}.objectives.{objective.id}",
                        f"Hidden objective is inside a public quest and must stay out of player-visible quest context: {objective.id}",
                        code="quest_hidden_objective_leak_risk",
                        ref_id=objective.id,
                        suggestion="Keep visibility hidden or move the objective to a hidden quest/stage.",
                    )
        for trigger in quest.triggers:
            if trigger.objective_id and trigger.objective_id not in objective_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"quests.yaml.{quest.id}.triggers.{trigger.id}.objective_id",
                    f"Trigger references missing objective: {trigger.objective_id}",
                    code="quest_trigger_missing_objective",
                    ref_id=trigger.objective_id,
                    suggestion="Use an objective id from this quest graph.",
                )


def generate_scenario_regression_draft(world_id: str, graph: QuestGraph) -> Any:
    from app.scenarios.regression import ScenarioRegressionCase

    if graph.world_id != world_id:
        raise QuestGraphError("Quest graph world_id does not match request world_id")
    quest = graph.quests[0] if graph.quests else None
    quest_id = quest.id if quest else "quest"
    expected_quest_states = {quest_id: "active"} if quest else {}
    return ScenarioRegressionCase(
        id=f"{world_id}_{quest_id}_quest_graph_draft",
        world_id=world_id,
        name=f"{quest.title if quest else 'Quest'} graph draft",
        description="Draft generated locally from the quest graph editor. Review inputs before saving as regression coverage.",
        input_sequence=["observe"],
        expected_quest_states=expected_quest_states,
        max_turns=3,
        tags=["quest-graph-draft", "authoring"],
    )


def _reachable_stage_ids(initial_stage: str, adjacency: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque([initial_stage])
    while queue:
        stage_id = queue.popleft()
        if stage_id in seen:
            continue
        seen.add(stage_id)
        queue.extend(sorted(adjacency.get(stage_id, set()) - seen))
    return seen


def _has_cycle(stage_by_id: dict[str, StageNode], adjacency: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str) -> bool:
        if stage_id in visiting:
            return True
        if stage_id in visited:
            return False
        visiting.add(stage_id)
        for target in adjacency.get(stage_id, set()):
            if visit(target):
                return True
        visiting.remove(stage_id)
        visited.add(stage_id)
        return False

    return any(visit(stage_id) for stage_id in stage_by_id)
