from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.scenarios.regression import ScenarioRegressionCase


class MysteryTemplateError(ValueError):
    """Raised when a mystery template operation is invalid or unsafe."""


class MysteryFact(BaseModel):
    id: str
    text: str
    visibility: str = "hidden"
    tags: list[str] = Field(default_factory=list)


class MysterySuspect(BaseModel):
    npc_id: str
    motive: str = ""
    knows_truth: bool = False


class MysteryClue(BaseModel):
    id: str
    text_for_player: str
    location_id: str
    fact_id: str | None = None
    evidence_item_id: str | None = None


class MysteryRedHerring(BaseModel):
    id: str
    text_for_player: str
    marked_red_herring: bool = True


class MysteryWitnessStatement(BaseModel):
    id: str
    npc_id: str
    text_for_player: str
    supports_clue_id: str | None = None


class MysteryTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    mystery_type: str
    truth_fact: MysteryFact
    suspects: list[MysterySuspect] = Field(default_factory=list)
    clues: list[MysteryClue] = Field(default_factory=list)
    red_herrings: list[MysteryRedHerring] = Field(default_factory=list)
    witness_statements: list[MysteryWitnessStatement] = Field(default_factory=list)
    reveal_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    required_locations: list[str] = Field(default_factory=list)
    required_npcs: list[str] = Field(default_factory=list)


class MysteryTemplatePreviewRequest(BaseModel):
    target_world_id: str
    variables: dict[str, str] = Field(default_factory=dict)
    confirm_apply: bool = False
    confirm_warnings: bool = False


class MysteryTemplateGeneratedContent(BaseModel):
    facts_draft: list[dict[str, Any]] = Field(default_factory=list)
    npc_knowledge_draft: dict[str, list[str]] = Field(default_factory=dict)
    questline_draft: list[dict[str, Any]] = Field(default_factory=list)
    rumor_draft: list[dict[str, Any]] = Field(default_factory=list)
    evidence_items_draft: list[dict[str, Any]] = Field(default_factory=list)
    scenario_regression_draft: list[ScenarioRegressionCase] = Field(default_factory=list)


class MysteryTemplatePreview(BaseModel):
    template: MysteryTemplate
    target_world_id: str
    generated: MysteryTemplateGeneratedContent
    yaml_contents: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    writes_to_disk: bool = False
    applied: bool = False
    confirmation_required: bool = False


class MysteryTemplateList(BaseModel):
    local_only: bool = True
    templates: list[MysteryTemplate] = Field(default_factory=list)


def list_mystery_templates() -> list[MysteryTemplate]:
    return [MysteryTemplate.model_validate(item) for item in _BUILT_IN_TEMPLATES]


def get_mystery_template(template_id: str) -> MysteryTemplate:
    for template in list_mystery_templates():
        if template.id == template_id:
            return template
    raise MysteryTemplateError(f"Unknown mystery template: {template_id}")


def preview_mystery_template(
    template_id: str,
    request: MysteryTemplatePreviewRequest,
    service: ContentAuthoringService,
) -> MysteryTemplatePreview:
    template = get_mystery_template(template_id)
    report = ValidationReport(world_id=request.target_world_id)
    _validate_template(template, request.target_world_id, service, report)
    generated = _generate(template, request.target_world_id) if not report.errors else MysteryTemplateGeneratedContent()
    yaml_contents = _generated_to_yaml(request.target_world_id, generated, service, report) if not report.errors else {}
    if not report.errors:
        draft_report = service.validate_drafts(request.target_world_id, yaml_contents)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
        _add_hidden_leak_checks(template, generated, report)
    return MysteryTemplatePreview(
        template=template,
        target_world_id=request.target_world_id,
        generated=generated,
        yaml_contents=yaml_contents,
        validation=report,
        writes_to_disk=False,
        applied=False,
        confirmation_required=report.ok and bool(report.warnings),
    )


def apply_mystery_template(
    template_id: str,
    request: MysteryTemplatePreviewRequest,
    service: ContentAuthoringService,
) -> MysteryTemplatePreview:
    preview = preview_mystery_template(template_id, request, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "mystery_template.apply",
            "Mystery template apply requires explicit confirmation.",
            code="mystery_template_apply_requires_confirmation",
        )
        preview.confirmation_required = True
        return preview
    if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        preview.confirmation_required = preview.validation.ok and bool(preview.validation.warnings)
        return preview
    validation = service.write_files(
        request.target_world_id,
        preview.yaml_contents,
        confirm_warnings=request.confirm_warnings,
    )
    preview.validation = validation
    preview.writes_to_disk = validation.ok
    preview.applied = validation.ok
    preview.confirmation_required = validation.ok and bool(validation.warnings) and not request.confirm_warnings
    return preview


def _validate_template(template: MysteryTemplate, world_id: str, service: ContentAuthoringService, report: ValidationReport) -> None:
    if template.truth_fact.visibility != "hidden":
        report.add(ValidationSeverity.ERROR, f"mystery.{template.id}.truth_fact", "truth_fact must be hidden.", code="mystery_truth_not_hidden")
    ids = _load_world_ids(world_id, service, report)
    for npc_id in set(template.required_npcs) | {suspect.npc_id for suspect in template.suspects} | {statement.npc_id for statement in template.witness_statements}:
        if npc_id not in ids["npcs"]:
            report.add(ValidationSeverity.ERROR, f"mystery.{template.id}.npcs.{npc_id}", f"Unknown NPC id: {npc_id}", code="mystery_missing_npc", ref_id=npc_id)
    for location_id in set(template.required_locations) | {clue.location_id for clue in template.clues}:
        if location_id not in ids["locations"]:
            report.add(ValidationSeverity.ERROR, f"mystery.{template.id}.locations.{location_id}", f"Unknown location id: {location_id}", code="mystery_missing_location", ref_id=location_id)
    for red_herring in template.red_herrings:
        if not red_herring.marked_red_herring:
            report.add(ValidationSeverity.ERROR, f"mystery.{template.id}.red_herrings.{red_herring.id}", "red_herrings must be explicitly marked.", code="mystery_red_herring_not_marked")


def _generate(template: MysteryTemplate, world_id: str) -> MysteryTemplateGeneratedContent:
    truth_id = template.truth_fact.id
    facts = [
        {
            "id": truth_id,
            "text": template.truth_fact.text,
            "visibility": "hidden",
            "known_by": [suspect.npc_id for suspect in template.suspects if suspect.knows_truth],
            "tags": sorted(set(["mystery_template", "truth", *template.truth_fact.tags])),
        }
    ]
    items = []
    clues = []
    for clue in template.clues:
        clue_fact_id = clue.fact_id or f"{clue.id}_fact"
        clues.append(clue_fact_id)
        facts.append(
            {
                "id": clue_fact_id,
                "text": clue.text_for_player,
                "visibility": "discoverable",
                "known_by": [],
                "tags": ["mystery_template", "clue", f"location:{clue.location_id}"],
            }
        )
        if clue.evidence_item_id:
            items.append(
                {
                    "id": clue.evidence_item_id,
                    "name": clue.text_for_player[:48],
                    "description": clue.text_for_player,
                    "location_id": clue.location_id,
                    "portable": True,
                    "hidden": True,
                    "discoverable": True,
                    "tags": ["mystery_template", "evidence"],
                    "base_price": 0,
                    "tradeable": False,
                }
            )
    facts.extend(
        {
            "id": red.id,
            "text": red.text_for_player,
            "visibility": "discoverable",
            "known_by": [],
            "tags": ["mystery_template", "red_herring"],
        }
        for red in template.red_herrings
    )
    facts.extend(
        {
            "id": statement.id,
            "text": statement.text_for_player,
            "visibility": "discoverable",
            "known_by": [statement.npc_id],
            "tags": ["mystery_template", "witness_statement"],
        }
        for statement in template.witness_statements
    )
    npc_knowledge = {suspect.npc_id: [truth_id] for suspect in template.suspects if suspect.knows_truth}
    quest_id = f"{template.id}_case"
    first_npc = template.required_npcs[0] if template.required_npcs else (template.suspects[0].npc_id if template.suspects else "player")
    first_clue = clues[0] if clues else truth_id
    quest = {
        "id": quest_id,
        "title": template.name,
        "description": f"Investigate a {template.mystery_type} case through safe clue paths.",
        "initial_stage": "start",
        "visibility": "public",
        "stages": [
            {"id": "start", "title": "Start", "description": "Interview the first witness.", "objectives": [{"id": "interview", "text": "Interview a witness.", "visibility": "public"}], "next_stages": ["follow_clue"]},
            {"id": "follow_clue", "title": "Follow Clue", "description": "Find evidence without exposing the truth.", "objectives": [{"id": "find_clue", "text": "Find the next clue.", "visibility": "public"}], "next_stages": []},
            {"id": "failed", "title": "Cold Case", "description": "The case stalls.", "objectives": [], "next_stages": []},
        ],
        "triggers": [
            {"type": "npc_talked", "id": first_npc, "action": "complete_objective", "objective_id": "interview", "next_stage": "follow_clue"},
            {"type": "fact_discovered", "id": first_clue, "action": "complete_objective", "objective_id": "find_clue"},
        ],
        "rewards": [{"id": f"{quest_id}_review", "text": "Review the accusation path before release.", "reward_type": "authoring"}],
    }
    rumors = [
        {
            "id": f"{template.id}_public_rumor",
            "fact_id": first_clue,
            "text_for_player": "People repeat a partial account that does not reveal the case truth.",
            "truth_status": "unknown",
            "known_by_npcs": [first_npc] if first_npc != "player" else [],
            "known_by_player": False,
            "spread_level": 1,
            "tags": ["mystery_template"],
        }
    ]
    scenario = ScenarioRegressionCase(
        id=f"{world_id}_{quest_id}_mystery_template",
        world_id=world_id,
        name=f"{template.name} mystery draft",
        description="Generated locally from Mystery Template System. Verifies the hidden truth stays hidden.",
        input_sequence=["observe"],
        forbidden_visible_facts=[truth_id],
        expected_quest_states={quest_id: "active"},
        max_turns=3,
        tags=["mystery-template", "hidden-boundary"],
    )
    return MysteryTemplateGeneratedContent(
        facts_draft=facts,
        npc_knowledge_draft=npc_knowledge,
        questline_draft=[quest],
        rumor_draft=rumors,
        evidence_items_draft=items,
        scenario_regression_draft=[scenario],
    )


def _generated_to_yaml(world_id: str, generated: MysteryTemplateGeneratedContent, service: ContentAuthoringService, report: ValidationReport) -> dict[str, str]:
    facts = _read_list_file(service, world_id, "facts.yaml", "facts", report)
    npcs = _read_list_file(service, world_id, "npcs.yaml", "npcs", report)
    quests = _read_list_file(service, world_id, "quests.yaml", "quests", report)
    rumors = _read_list_file(service, world_id, "rumors.yaml", "rumors", report, required=False)
    items = _read_list_file(service, world_id, "items.yaml", "items", report)
    if report.errors:
        return {}
    knowledge_by_npc = generated.npc_knowledge_draft
    updated_npcs = []
    for npc in npcs:
        updated = dict(npc)
        npc_id = str(updated.get("id", ""))
        if npc_id in knowledge_by_npc:
            updated["knowledge"] = sorted(set([str(item) for item in updated.get("knowledge", [])] + knowledge_by_npc[npc_id]))
            updated["secrets"] = sorted(set([str(item) for item in updated.get("secrets", [])] + knowledge_by_npc[npc_id]))
        updated_npcs.append(updated)
    return {
        "facts.yaml": yaml.safe_dump({"facts": facts + generated.facts_draft}, sort_keys=False, allow_unicode=True),
        "npcs.yaml": yaml.safe_dump({"npcs": updated_npcs}, sort_keys=False, allow_unicode=True),
        "quests.yaml": yaml.safe_dump({"quests": quests + generated.questline_draft}, sort_keys=False, allow_unicode=True),
        "rumors.yaml": yaml.safe_dump({"rumors": rumors + generated.rumor_draft}, sort_keys=False, allow_unicode=True),
        "items.yaml": yaml.safe_dump({"items": items + generated.evidence_items_draft}, sort_keys=False, allow_unicode=True),
    }


def _add_hidden_leak_checks(template: MysteryTemplate, generated: MysteryTemplateGeneratedContent, report: ValidationReport) -> None:
    truth_text = template.truth_fact.text.lower()
    player_text = yaml.safe_dump(
        {
            "clues": [clue.text_for_player for clue in template.clues],
            "red_herrings": [red.text_for_player for red in template.red_herrings],
            "witnesses": [statement.text_for_player for statement in template.witness_statements],
            "rumors": generated.rumor_draft,
            "quests": generated.questline_draft,
        },
        sort_keys=False,
        allow_unicode=True,
    ).lower()
    if truth_text and truth_text in player_text:
        report.add(ValidationSeverity.ERROR, f"mystery.{template.id}.hidden_leak", "Player-facing mystery text includes the hidden truth.", code="mystery_hidden_truth_leak")


def _load_world_ids(world_id: str, service: ContentAuthoringService, report: ValidationReport) -> dict[str, set[str]]:
    return {
        "npcs": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "npcs.yaml", "npcs", report)},
        "locations": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "locations.yaml", "locations", report)},
    }


def _read_list_file(service: ContentAuthoringService, world_id: str, file_name: str, root_key: str, report: ValidationReport, *, required: bool = True) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except AuthoringError:
        if required:
            report.add(ValidationSeverity.ERROR, file_name, f"Required content file is missing: {file_name}", code="mystery_missing_file")
        return []
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        report.add(ValidationSeverity.ERROR, file_name, f"Invalid YAML: {exc}", code="mystery_invalid_yaml")
        return []
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)]


_BUILT_IN_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "missing_heirloom_case",
        "name": "Missing Heirloom Case",
        "mystery_type": "theft",
        "truth_fact": {
            "id": "missing_heirloom_truth",
            "text": "Harlan hid the heirloom to prevent a panic.",
            "visibility": "hidden",
            "tags": ["theft", "motive"],
        },
        "suspects": [{"npc_id": "harlan", "motive": "protect the village", "knows_truth": True}],
        "clues": [{"id": "heirloom_clue_1", "text_for_player": "Fresh soot marks the edge of a wrapped bundle.", "location_id": "blacksmith", "evidence_item_id": "soot_marked_cloth"}],
        "red_herrings": [{"id": "heirloom_red_herring_smugglers", "text_for_player": "Someone saw old road boot prints near the square.", "marked_red_herring": True}],
        "witness_statements": [{"id": "heirloom_witness_harlan", "npc_id": "harlan", "text_for_player": "Harlan says he heard movement before dawn.", "supports_clue_id": "heirloom_clue_1"}],
        "reveal_conditions": ["discover:heirloom_clue_1_fact", "talk:harlan"],
        "failure_conditions": ["accuse_without_evidence"],
        "required_locations": ["blacksmith", "village_square"],
        "required_npcs": ["harlan"],
    }
]
