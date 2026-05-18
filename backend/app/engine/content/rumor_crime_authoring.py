from collections import Counter
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.rules.crime import CRIME_TYPES


class RumorCrimeAuthoringError(ValueError):
    """Raised when rumor/crime consequence authoring input is invalid."""


class FactReferenceNode(BaseModel):
    id: str
    visibility: str
    tags: list[str] = Field(default_factory=list)


class FactionReferenceNode(BaseModel):
    id: str
    name: str
    known_by_player: bool = False


class RumorAuthoringNode(BaseModel):
    id: str
    fact_id: str | None = None
    source_event_id: str | None = None
    text_for_player: str | None = None
    truth_status: str = "unknown"
    known_by_npcs: list[str] = Field(default_factory=list)
    known_by_factions: list[str] = Field(default_factory=list)
    known_by_player: bool = False
    spread_level: int = 0
    created_turn: int = 0
    tags: list[str] = Field(default_factory=list)


class CrimeConsequenceNode(BaseModel):
    id: str
    crime_type: str = "theft"
    trigger_condition: str = ""
    severity: int = 1
    visibility: str = "hidden"
    tags: list[str] = Field(default_factory=list)


class ReputationEffectNode(BaseModel):
    id: str
    faction_id: str
    amount: int = 0
    reason: str = ""


class QuestTriggerConsequenceNode(BaseModel):
    id: str
    quest_id: str
    trigger_id: str
    action: str = "activate"


class ConsequenceGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    label: str | None = None


class RumorCrimeConsequenceAuthoring(BaseModel):
    world_id: str
    facts: list[FactReferenceNode] = Field(default_factory=list)
    factions: list[FactionReferenceNode] = Field(default_factory=list)
    rumors: list[RumorAuthoringNode] = Field(default_factory=list)
    crimes: list[CrimeConsequenceNode] = Field(default_factory=list)
    reputation_effects: list[ReputationEffectNode] = Field(default_factory=list)
    quest_triggers: list[QuestTriggerConsequenceNode] = Field(default_factory=list)
    edges: list[ConsequenceGraphEdge] = Field(default_factory=list)


class RumorCrimeConsequencePreview(BaseModel):
    graph: RumorCrimeConsequenceAuthoring
    yaml_contents: dict[str, str]
    validation: ValidationReport
    confirmation_required: bool = False


def parse_rumor_crime_authoring(
    world_id: str,
    service: ContentAuthoringService,
) -> RumorCrimeConsequenceAuthoring:
    facts_data = _read_list_file(service, world_id, "facts.yaml", "facts")
    factions_data = _read_list_file(service, world_id, "factions.yaml", "factions")
    rumors_data = _read_list_file(service, world_id, "rumors.yaml", "rumors")
    quests_data = _read_list_file(service, world_id, "quests.yaml", "quests")

    facts = [
        FactReferenceNode(
            id=str(fact.get("id", "")),
            visibility=str(fact.get("visibility", "hidden")),
            tags=[str(tag) for tag in fact.get("tags", [])],
        )
        for fact in facts_data
    ]
    factions = [
        FactionReferenceNode(
            id=str(faction.get("id", "")),
            name=str(faction.get("name", faction.get("id", ""))),
            known_by_player=bool(faction.get("known_by_player", False)),
        )
        for faction in factions_data
    ]
    rumors = [RumorAuthoringNode.model_validate(_normalize_rumor(rumor)) for rumor in rumors_data]
    crimes = _derive_crime_nodes(rumors)
    reputation_effects = _derive_reputation_nodes(rumors)
    quest_triggers = _derive_quest_trigger_nodes(quests_data)
    edges = _derive_edges(rumors, crimes, reputation_effects, quest_triggers)
    return RumorCrimeConsequenceAuthoring(
        world_id=world_id,
        facts=facts,
        factions=factions,
        rumors=rumors,
        crimes=crimes,
        reputation_effects=reputation_effects,
        quest_triggers=quest_triggers,
        edges=edges,
    )


def rumor_crime_to_yaml(graph: RumorCrimeConsequenceAuthoring) -> dict[str, str]:
    rumors_yaml = yaml.safe_dump(
        {"rumors": [_without_empty_optional_lists(rumor.model_dump(mode="json")) for rumor in graph.rumors]},
        sort_keys=False,
        allow_unicode=True,
    )
    return {"rumors.yaml": rumors_yaml}


def preview_rumor_crime_authoring(
    world_id: str,
    graph: RumorCrimeConsequenceAuthoring,
    service: ContentAuthoringService,
) -> RumorCrimeConsequencePreview:
    _validate_world_id(world_id, graph)
    yaml_contents = rumor_crime_to_yaml(graph)
    report = service.validate_drafts(world_id, yaml_contents)
    _add_consequence_graph_validation(graph, report)
    return RumorCrimeConsequencePreview(
        graph=graph,
        yaml_contents=yaml_contents,
        validation=report,
        confirmation_required=report.ok and bool(report.warnings),
    )


def validate_rumor_crime_authoring(
    world_id: str,
    graph: RumorCrimeConsequenceAuthoring,
    service: ContentAuthoringService,
) -> ValidationReport:
    return preview_rumor_crime_authoring(world_id, graph, service).validation


def save_rumor_crime_authoring(
    world_id: str,
    graph: RumorCrimeConsequenceAuthoring,
    service: ContentAuthoringService,
) -> ValidationReport:
    preview = preview_rumor_crime_authoring(world_id, graph, service)
    if not preview.validation.ok:
        return preview.validation
    return service.write_files(world_id, preview.yaml_contents)


def _validate_world_id(world_id: str, graph: RumorCrimeConsequenceAuthoring) -> None:
    if graph.world_id != world_id:
        raise RumorCrimeAuthoringError(
            f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}"
        )


def _add_consequence_graph_validation(
    graph: RumorCrimeConsequenceAuthoring,
    report: ValidationReport,
) -> None:
    consequence_ids = (
        [crime.id for crime in graph.crimes]
        + [rumor.id for rumor in graph.rumors]
        + [effect.id for effect in graph.reputation_effects]
        + [trigger.id for trigger in graph.quest_triggers]
    )
    for consequence_id, count in Counter(consequence_ids).items():
        if count > 1:
            report.add(
                ValidationSeverity.ERROR,
                "consequence_graph",
                f"Duplicate consequence id: {consequence_id}",
                code="duplicate_consequence_id",
                ref_id=consequence_id,
                suggestion="Use unique ids across crime, rumor, reputation, and quest consequence nodes.",
            )

    fact_ids = {fact.id for fact in graph.facts}
    faction_ids = {faction.id for faction in graph.factions}
    for rumor in graph.rumors:
        if rumor.fact_id and rumor.fact_id not in fact_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"rumors.yaml.{rumor.id}.fact_id",
                f"Rumor references missing fact: {rumor.fact_id}",
                code="rumor_missing_fact",
                ref_id=rumor.fact_id,
                suggestion="Use a fact id from facts.yaml or clear fact_id.",
            )
        for faction_id in rumor.known_by_factions:
            if faction_id not in faction_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"rumors.yaml.{rumor.id}.known_by_factions",
                    f"Rumor references missing faction: {faction_id}",
                    code="rumor_missing_faction",
                    ref_id=faction_id,
                    suggestion="Use a faction id from factions.yaml.",
                )

    for crime in graph.crimes:
        if crime.crime_type not in CRIME_TYPES:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.crimes.{crime.id}.crime_type",
                f"Unsupported crime type: {crime.crime_type}",
                code="invalid_crime_type",
                ref_id=crime.crime_type,
                suggestion="Use a deterministic crime type supported by crime.py.",
            )

    for effect in graph.reputation_effects:
        if effect.faction_id not in faction_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.reputation_effects.{effect.id}.faction_id",
                f"Reputation effect references missing faction: {effect.faction_id}",
                code="reputation_effect_missing_faction",
                ref_id=effect.faction_id,
                suggestion="Use a faction id from factions.yaml.",
            )

    node_ids = set(consequence_ids)
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in graph.edges:
        if edge.source not in node_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.edges.{edge.source}",
                f"Edge source does not exist: {edge.source}",
                code="consequence_edge_missing_source",
                ref_id=edge.source,
            )
        if edge.target not in node_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.edges.{edge.target}",
                f"Edge target does not exist: {edge.target}",
                code="consequence_edge_missing_target",
                ref_id=edge.target,
            )
        adjacency.setdefault(edge.source, []).append(edge.target)
        if edge.source == edge.target:
            report.add(
                ValidationSeverity.WARNING,
                f"consequence_graph.edges.{edge.source}",
                f"Consequence edge loops to itself: {edge.source}",
                code="consequence_loop_warning",
                ref_id=edge.source,
                suggestion="Self-loops are authoring warnings and should not become runtime consequence loops.",
            )

    for cycle_start in _cycle_nodes(adjacency):
        report.add(
            ValidationSeverity.WARNING,
            f"consequence_graph.edges.{cycle_start}",
            f"Consequence graph contains a cycle involving: {cycle_start}",
            code="consequence_loop_warning",
            ref_id=cycle_start,
            suggestion="Review the graph so social tick consequences do not repeatedly trigger each other.",
        )


def _cycle_nodes(adjacency: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            cycles.add(node_id)
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for target in adjacency.get(node_id, []):
            visit(target)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(adjacency):
        visit(node_id)
    return sorted(cycles)


def _derive_crime_nodes(rumors: list[RumorAuthoringNode]) -> list[CrimeConsequenceNode]:
    crime_tags = sorted({tag for rumor in rumors for tag in rumor.tags if tag in CRIME_TYPES})
    return [
        CrimeConsequenceNode(
            id=f"crime_template_{crime_type}",
            crime_type=crime_type,
            trigger_condition=f"crime:{crime_type}",
            severity=2,
            visibility="hidden",
            tags=["derived", crime_type],
        )
        for crime_type in crime_tags
    ]


def _derive_reputation_nodes(rumors: list[RumorAuthoringNode]) -> list[ReputationEffectNode]:
    effects: list[ReputationEffectNode] = []
    for rumor in rumors:
        for faction_id in rumor.known_by_factions:
            effects.append(
                ReputationEffectNode(
                    id=f"reputation_from_{rumor.id}_{faction_id}",
                    faction_id=faction_id,
                    amount=0,
                    reason=f"Faction hears rumor {rumor.id}.",
                )
            )
    return effects


def _derive_quest_trigger_nodes(quests_data: list[dict[str, Any]]) -> list[QuestTriggerConsequenceNode]:
    nodes: list[QuestTriggerConsequenceNode] = []
    for quest in quests_data:
        quest_id = str(quest.get("id", ""))
        for index, trigger in enumerate(quest.get("triggers", [])):
            if not isinstance(trigger, dict):
                continue
            trigger_type = str(trigger.get("type", ""))
            if trigger_type in {"fact_discovered", "item_acquired", "npc_talked", "location_visited"}:
                nodes.append(
                    QuestTriggerConsequenceNode(
                        id=f"quest_trigger_{quest_id}_{index}",
                        quest_id=quest_id,
                        trigger_id=str(trigger.get("id", "")),
                        action=str(trigger.get("action", "activate")),
                    )
                )
    return nodes


def _derive_edges(
    rumors: list[RumorAuthoringNode],
    crimes: list[CrimeConsequenceNode],
    reputation_effects: list[ReputationEffectNode],
    quest_triggers: list[QuestTriggerConsequenceNode],
) -> list[ConsequenceGraphEdge]:
    edges: list[ConsequenceGraphEdge] = []
    for crime in crimes:
        for rumor in rumors:
            if crime.crime_type in rumor.tags:
                edges.append(
                    ConsequenceGraphEdge(
                        source=crime.id,
                        target=rumor.id,
                        type="crime_creates_rumor",
                        label=crime.crime_type,
                    )
                )
    for rumor in rumors:
        for effect in reputation_effects:
            if effect.id.startswith(f"reputation_from_{rumor.id}_"):
                edges.append(
                    ConsequenceGraphEdge(
                        source=rumor.id,
                        target=effect.id,
                        type="rumor_reaches_faction",
                    )
                )
        for trigger in quest_triggers:
            if trigger.trigger_id == rumor.fact_id:
                edges.append(
                    ConsequenceGraphEdge(
                        source=rumor.id,
                        target=trigger.id,
                        type="rumor_related_quest_trigger",
                    )
                )
    return edges


def _normalize_rumor(rumor: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(rumor)
    if "text_for_player" not in normalized and "text" in normalized:
        normalized["text_for_player"] = normalized["text"]
    return normalized


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except Exception as exc:
        raise RumorCrimeAuthoringError(str(exc)) from exc
    data = yaml.safe_load(content) or {}
    if not isinstance(data, dict):
        raise RumorCrimeAuthoringError(f"Expected YAML mapping in {file_name}")
    raw_items = data.get(root_key, [])
    if not isinstance(raw_items, list):
        raise RumorCrimeAuthoringError(f"Expected list key {root_key} in {file_name}")
    return [dict(item) for item in raw_items if isinstance(item, dict)]


def _without_empty_optional_lists(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value is not None and value != []
    }
