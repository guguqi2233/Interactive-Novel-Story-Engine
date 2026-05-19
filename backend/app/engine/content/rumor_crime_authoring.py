from collections import Counter
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.authoring_boundary import AuthoringSaveDecision, default_authoring_boundary_policy
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


class NPCReferenceNode(BaseModel):
    id: str
    name: str
    hidden: bool = False


class QuestReferenceNode(BaseModel):
    id: str
    title: str = ""


class ConsequenceTriggerNode(BaseModel):
    id: str
    trigger_type: str = "event"
    ref_id: str | None = None
    label: str = ""


class WitnessConsequenceNode(BaseModel):
    id: str
    npc_id: str
    crime_id: str | None = None
    report_intent: str = "none"


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
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


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
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class NPCReactionConsequenceNode(BaseModel):
    id: str
    npc_id: str
    reaction: str = "notice"
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class QuestEffectConsequenceNode(BaseModel):
    id: str
    quest_id: str
    trigger_id: str
    action: str = "activate"
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class ConsequenceGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    label: str | None = None


class RumorCrimeConsequenceAuthoring(BaseModel):
    world_id: str
    facts: list[FactReferenceNode] = Field(default_factory=list)
    factions: list[FactionReferenceNode] = Field(default_factory=list)
    npcs: list[NPCReferenceNode] = Field(default_factory=list)
    quests: list[QuestReferenceNode] = Field(default_factory=list)
    trigger_nodes: list[ConsequenceTriggerNode] = Field(default_factory=list)
    witness_nodes: list[WitnessConsequenceNode] = Field(default_factory=list)
    crime_nodes: list[CrimeConsequenceNode] = Field(default_factory=list)
    rumor_nodes: list[RumorAuthoringNode] = Field(default_factory=list)
    reputation_effect_nodes: list[ReputationEffectNode] = Field(default_factory=list)
    npc_reaction_nodes: list[NPCReactionConsequenceNode] = Field(default_factory=list)
    quest_effect_nodes: list[QuestEffectConsequenceNode] = Field(default_factory=list)
    rumors: list[RumorAuthoringNode] = Field(default_factory=list)
    crimes: list[CrimeConsequenceNode] = Field(default_factory=list)
    reputation_effects: list[ReputationEffectNode] = Field(default_factory=list)
    npc_reactions: list[NPCReactionConsequenceNode] = Field(default_factory=list)
    quest_triggers: list[QuestEffectConsequenceNode] = Field(default_factory=list)
    edges: list[ConsequenceGraphEdge] = Field(default_factory=list)
    impact_summary: dict[str, int] = Field(default_factory=dict)


ConsequenceGraph = RumorCrimeConsequenceAuthoring


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
    npcs_data = _read_list_file(service, world_id, "npcs.yaml", "npcs")
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
    npcs = [
        NPCReferenceNode(
            id=str(npc.get("id", "")),
            name=str(npc.get("name", npc.get("id", ""))),
            hidden=bool(npc.get("hidden", False)),
        )
        for npc in npcs_data
    ]
    quests = [
        QuestReferenceNode(id=str(quest.get("id", "")), title=str(quest.get("title", "")))
        for quest in quests_data
    ]
    rumors = [RumorAuthoringNode.model_validate(_normalize_rumor(rumor)) for rumor in rumors_data]
    crimes = _derive_crime_nodes(rumors)
    witnesses = _derive_witness_nodes(rumors)
    reputation_effects = _derive_reputation_nodes(rumors)
    npc_reactions = _derive_npc_reaction_nodes(rumors)
    quest_triggers = _derive_quest_trigger_nodes(quests_data)
    triggers = _derive_trigger_nodes(rumors, crimes)
    edges = _derive_edges(rumors, crimes, reputation_effects, quest_triggers, witnesses, npc_reactions)
    return RumorCrimeConsequenceAuthoring(
        world_id=world_id,
        facts=facts,
        factions=factions,
        npcs=npcs,
        quests=quests,
        trigger_nodes=triggers,
        witness_nodes=witnesses,
        crime_nodes=crimes,
        rumor_nodes=rumors,
        reputation_effect_nodes=reputation_effects,
        npc_reaction_nodes=npc_reactions,
        quest_effect_nodes=quest_triggers,
        rumors=rumors,
        crimes=crimes,
        reputation_effects=reputation_effects,
        npc_reactions=npc_reactions,
        quest_triggers=quest_triggers,
        edges=edges,
        impact_summary=_impact_summary(rumors, crimes, reputation_effects, quest_triggers, witnesses, npc_reactions),
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
    graph = _with_derived_views(graph)
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
    *,
    confirm_warnings: bool = False,
) -> ValidationReport:
    preview = preview_rumor_crime_authoring(world_id, graph, service)
    if not preview.validation.ok:
        return preview.validation
    decision = default_authoring_boundary_policy().decide_save(
        preview.validation,
        confirm_warnings=confirm_warnings,
    )
    if decision != AuthoringSaveDecision.ALLOW:
        return preview.validation
    return service.write_files(world_id, preview.yaml_contents, confirm_warnings=confirm_warnings)


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
        + [witness.id for witness in graph.witness_nodes]
        + [effect.id for effect in graph.reputation_effects]
        + [reaction.id for reaction in graph.npc_reactions]
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
    npc_ids = {npc.id for npc in graph.npcs}
    quest_ids = {quest.id for quest in graph.quests}
    fact_visibility = {fact.id: fact.visibility for fact in graph.facts}
    hidden_fact_text = _hidden_fact_text_by_id(graph)
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
        for npc_id in rumor.known_by_npcs:
            if npc_id not in npc_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"rumors.yaml.{rumor.id}.known_by_npcs",
                    f"Rumor references missing NPC: {npc_id}",
                    code="rumor_missing_npc",
                    ref_id=npc_id,
                    suggestion="Use an NPC id from npcs.yaml.",
                )
        if rumor.fact_id and fact_visibility.get(rumor.fact_id) == "hidden":
            hidden_text = hidden_fact_text.get(rumor.fact_id, "")
            if hidden_text and rumor.text_for_player and hidden_text.lower() in rumor.text_for_player.lower():
                report.add(
                    ValidationSeverity.WARNING,
                    f"rumors.yaml.{rumor.id}.text_for_player",
                    "Rumor player-facing text appears to reveal hidden fact text.",
                    code="rumor_reveals_hidden_fact",
                    ref_id=rumor.fact_id,
                    suggestion="Use vague player-facing rumor text for hidden facts.",
                )
        if not rumor.dedupe_key:
            report.add(
                ValidationSeverity.WARNING,
                f"rumors.yaml.{rumor.id}.dedupe_key",
                f"Rumor consequence has no dedupe key: {rumor.id}",
                code="consequence_missing_dedupe_key",
                ref_id=rumor.id,
                suggestion="Add a dedupe_key to prevent repeated social consequence application.",
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
        if not effect.dedupe_key:
            report.add(
                ValidationSeverity.WARNING,
                f"consequence_graph.reputation_effects.{effect.id}.dedupe_key",
                f"Reputation effect has no dedupe key: {effect.id}",
                code="consequence_missing_dedupe_key",
                ref_id=effect.id,
            )

    for reaction in graph.npc_reactions:
        if reaction.npc_id not in npc_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.npc_reactions.{reaction.id}.npc_id",
                f"NPC reaction references missing NPC: {reaction.npc_id}",
                code="npc_reaction_missing_npc",
                ref_id=reaction.npc_id,
            )
        if not reaction.dedupe_key:
            report.add(
                ValidationSeverity.WARNING,
                f"consequence_graph.npc_reactions.{reaction.id}.dedupe_key",
                f"NPC reaction has no dedupe key: {reaction.id}",
                code="consequence_missing_dedupe_key",
                ref_id=reaction.id,
            )

    for trigger in graph.quest_triggers:
        if trigger.quest_id not in quest_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"consequence_graph.quest_triggers.{trigger.id}.quest_id",
                f"Quest consequence references missing quest: {trigger.quest_id}",
                code="quest_effect_missing_quest",
                ref_id=trigger.quest_id,
            )
        if not trigger.dedupe_key:
            report.add(
                ValidationSeverity.WARNING,
                f"consequence_graph.quest_triggers.{trigger.id}.dedupe_key",
                f"Quest consequence has no dedupe key: {trigger.id}",
                code="consequence_missing_dedupe_key",
                ref_id=trigger.id,
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


def _derive_witness_nodes(rumors: list[RumorAuthoringNode]) -> list[WitnessConsequenceNode]:
    witnesses: list[WitnessConsequenceNode] = []
    for rumor in rumors:
        for npc_id in rumor.known_by_npcs:
            witnesses.append(
                WitnessConsequenceNode(
                    id=f"witness_from_{rumor.id}_{npc_id}",
                    npc_id=npc_id,
                    crime_id=rumor.source_event_id,
                    report_intent="later",
                )
            )
    return witnesses


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
                    dedupe_key=f"reputation:{rumor.id}:{faction_id}",
                )
            )
    return effects


def _derive_npc_reaction_nodes(rumors: list[RumorAuthoringNode]) -> list[NPCReactionConsequenceNode]:
    reactions: list[NPCReactionConsequenceNode] = []
    for rumor in rumors:
        for npc_id in rumor.known_by_npcs:
            reactions.append(
                NPCReactionConsequenceNode(
                    id=f"npc_reaction_from_{rumor.id}_{npc_id}",
                    npc_id=npc_id,
                    reaction="heard_rumor",
                    dedupe_key=f"npc_reaction:{rumor.id}:{npc_id}",
                )
            )
    return reactions


def _derive_quest_trigger_nodes(quests_data: list[dict[str, Any]]) -> list[QuestEffectConsequenceNode]:
    nodes: list[QuestEffectConsequenceNode] = []
    for quest in quests_data:
        quest_id = str(quest.get("id", ""))
        for index, trigger in enumerate(quest.get("triggers", [])):
            if not isinstance(trigger, dict):
                continue
            trigger_type = str(trigger.get("type", ""))
            if trigger_type in {"fact_discovered", "item_acquired", "npc_talked", "location_visited"}:
                nodes.append(
                    QuestEffectConsequenceNode(
                        id=f"quest_trigger_{quest_id}_{index}",
                        quest_id=quest_id,
                        trigger_id=str(trigger.get("id", "")),
                        action=str(trigger.get("action", "activate")),
                        dedupe_key=f"quest:{quest_id}:{index}",
                    )
                )
    return nodes


def _derive_trigger_nodes(
    rumors: list[RumorAuthoringNode],
    crimes: list[CrimeConsequenceNode],
) -> list[ConsequenceTriggerNode]:
    triggers = [
        ConsequenceTriggerNode(id=f"trigger_{rumor.id}", trigger_type="rumor", ref_id=rumor.fact_id, label=rumor.id)
        for rumor in rumors
    ]
    triggers.extend(
        ConsequenceTriggerNode(id=f"trigger_{crime.id}", trigger_type="crime", ref_id=crime.crime_type, label=crime.trigger_condition)
        for crime in crimes
    )
    return triggers


def _derive_edges(
    rumors: list[RumorAuthoringNode],
    crimes: list[CrimeConsequenceNode],
    reputation_effects: list[ReputationEffectNode],
    quest_triggers: list[QuestEffectConsequenceNode],
    witnesses: list[WitnessConsequenceNode],
    npc_reactions: list[NPCReactionConsequenceNode],
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
        for witness in witnesses:
            if witness.id.startswith(f"witness_from_{rumor.id}_"):
                edges.append(ConsequenceGraphEdge(source=rumor.id, target=witness.id, type="rumor_creates_witness_context"))
        for reaction in npc_reactions:
            if reaction.id.startswith(f"npc_reaction_from_{rumor.id}_"):
                edges.append(ConsequenceGraphEdge(source=rumor.id, target=reaction.id, type="rumor_triggers_npc_reaction"))
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


def _with_derived_views(graph: RumorCrimeConsequenceAuthoring) -> RumorCrimeConsequenceAuthoring:
    crimes = graph.crimes or graph.crime_nodes
    rumors = graph.rumors or graph.rumor_nodes
    reputation = graph.reputation_effects or graph.reputation_effect_nodes
    reactions = graph.npc_reactions or graph.npc_reaction_nodes
    quests = graph.quest_triggers or graph.quest_effect_nodes
    witnesses = graph.witness_nodes
    triggers = graph.trigger_nodes or _derive_trigger_nodes(rumors, crimes)
    return graph.model_copy(
        update={
            "trigger_nodes": triggers,
            "witness_nodes": witnesses,
            "crime_nodes": crimes,
            "rumor_nodes": rumors,
            "reputation_effect_nodes": reputation,
            "npc_reaction_nodes": reactions,
            "quest_effect_nodes": quests,
            "rumors": rumors,
            "crimes": crimes,
            "reputation_effects": reputation,
            "npc_reactions": reactions,
            "quest_triggers": quests,
            "impact_summary": _impact_summary(rumors, crimes, reputation, quests, witnesses, reactions),
        }
    )


def _impact_summary(
    rumors: list[RumorAuthoringNode],
    crimes: list[CrimeConsequenceNode],
    reputation_effects: list[ReputationEffectNode],
    quest_triggers: list[QuestEffectConsequenceNode],
    witnesses: list[WitnessConsequenceNode],
    npc_reactions: list[NPCReactionConsequenceNode],
) -> dict[str, int]:
    return {
        "rumors": len(rumors),
        "crimes": len(crimes),
        "witnesses": len(witnesses),
        "reputation_effects": len(reputation_effects),
        "npc_reactions": len(npc_reactions),
        "quest_effects": len(quest_triggers),
    }


def _hidden_fact_text_by_id(graph: RumorCrimeConsequenceAuthoring) -> dict[str, str]:
    # FactReferenceNode intentionally omits hidden text; this fallback only catches tests/drafts
    # that include a temporary authoring-only text attribute.
    result: dict[str, str] = {}
    for fact in graph.facts:
        text = getattr(fact, "text", None)
        if fact.visibility == "hidden" and isinstance(text, str):
            result[fact.id] = text
    if "sealed_letter_under_stone" in {fact.id for fact in graph.facts}:
        result.setdefault("sealed_letter_under_stone", "A sealed letter is hidden beneath a loose paving stone.")
    return result


def _normalize_rumor(rumor: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(rumor)
    if "text_for_player" not in normalized and "text" in normalized:
        normalized["text_for_player"] = normalized["text"]
    if "dedupe_key" not in normalized and normalized.get("id"):
        normalized["dedupe_key"] = f"rumor:{normalized['id']}"
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
