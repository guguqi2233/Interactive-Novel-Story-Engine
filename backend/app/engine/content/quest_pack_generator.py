from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.quest_graph import QuestGraph, generate_scenario_regression_draft, quest_yaml_to_graph
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.scenarios.regression import ScenarioRegressionCase


class QuestPackGeneratorError(ValueError):
    """Raised when a quest pack generator draft is invalid or unsafe."""


class QuestPackGeneratorDraft(BaseModel):
    target_world_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    pack_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    theme: str = "local mystery"
    quest_count: int = Field(default=1, ge=1, le=20)
    involved_npcs: list[str] = Field(default_factory=list)
    involved_locations: list[str] = Field(default_factory=list)
    involved_factions: list[str] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)
    mystery_mode: bool = False
    failure_paths_enabled: bool = False
    reward_policy: str = "story"
    llm_assisted: bool = False


class QuestPackGeneratedContent(BaseModel):
    quest_candidates: list[dict[str, Any]] = Field(default_factory=list)
    fact_candidates: list[dict[str, Any]] = Field(default_factory=list)
    rumor_candidates: list[dict[str, Any]] = Field(default_factory=list)
    consequence_candidates: list[dict[str, Any]] = Field(default_factory=list)
    scenario_regression_candidates: list[ScenarioRegressionCase] = Field(default_factory=list)
    quest_graph: QuestGraph | None = None
    quality_checks: ValidationReport


class QuestPackGeneratorPreview(BaseModel):
    draft: QuestPackGeneratorDraft
    generated: QuestPackGeneratedContent
    yaml_contents: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    writes_to_disk: bool = False
    applied: bool = False
    confirmation_required: bool = False


class QuestPackGeneratorApplyRequest(BaseModel):
    draft: QuestPackGeneratorDraft
    confirm_apply: bool = False
    confirm_warnings: bool = False


def preview_quest_pack_generator(
    draft: QuestPackGeneratorDraft,
    service: ContentAuthoringService,
) -> QuestPackGeneratorPreview:
    report = ValidationReport(world_id=draft.target_world_id)
    _validate_draft(draft, service, report)
    generated = (
        _generate_content(draft, service, report)
        if not report.errors
        else QuestPackGeneratedContent(quality_checks=ValidationReport(world_id=draft.target_world_id))
    )
    yaml_contents = _generated_to_yaml(draft, generated, service, report) if not report.errors else {}
    if not report.errors:
        draft_report = service.validate_drafts(draft.target_world_id, yaml_contents)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
    return QuestPackGeneratorPreview(
        draft=draft,
        generated=generated,
        yaml_contents=yaml_contents,
        validation=report,
        writes_to_disk=False,
        applied=False,
        confirmation_required=report.ok and bool(report.warnings),
    )


def validate_quest_pack_generator(
    draft: QuestPackGeneratorDraft,
    service: ContentAuthoringService,
) -> QuestPackGeneratorPreview:
    return preview_quest_pack_generator(draft, service)


def apply_quest_pack_generator(
    request: QuestPackGeneratorApplyRequest,
    service: ContentAuthoringService,
) -> QuestPackGeneratorPreview:
    preview = validate_quest_pack_generator(request.draft, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "quest_pack_generator.apply",
            "Quest pack apply requires explicit confirmation.",
            code="quest_pack_apply_requires_confirmation",
        )
        preview.confirmation_required = True
        return preview
    if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        preview.confirmation_required = preview.validation.ok and bool(preview.validation.warnings)
        return preview
    validation = service.write_files(
        request.draft.target_world_id,
        preview.yaml_contents,
        confirm_warnings=request.confirm_warnings,
    )
    preview.validation = validation
    preview.writes_to_disk = validation.ok
    preview.applied = validation.ok
    preview.confirmation_required = validation.ok and bool(validation.warnings) and not request.confirm_warnings
    return preview


def _validate_draft(draft: QuestPackGeneratorDraft, service: ContentAuthoringService, report: ValidationReport) -> None:
    ids = _load_world_ids(draft.target_world_id, service, report)
    for npc_id in draft.involved_npcs:
        if npc_id not in ids["npcs"]:
            report.add(ValidationSeverity.ERROR, f"quest_pack.npcs.{npc_id}", f"Unknown NPC id: {npc_id}", code="quest_pack_missing_npc", ref_id=npc_id)
    for location_id in draft.involved_locations:
        if location_id not in ids["locations"]:
            report.add(ValidationSeverity.ERROR, f"quest_pack.locations.{location_id}", f"Unknown location id: {location_id}", code="quest_pack_missing_location", ref_id=location_id)
    for faction_id in draft.involved_factions:
        if faction_id not in ids["factions"]:
            report.add(ValidationSeverity.ERROR, f"quest_pack.factions.{faction_id}", f"Unknown faction id: {faction_id}", code="quest_pack_missing_faction", ref_id=faction_id)
    for fact_id in draft.required_facts:
        if fact_id not in ids["facts"]:
            report.add(ValidationSeverity.ERROR, f"quest_pack.facts.{fact_id}", f"Unknown fact id: {fact_id}", code="quest_pack_missing_fact", ref_id=fact_id)
    unsafe = "\n".join([draft.theme, draft.reward_policy]).lower()
    if any(token in unsafe for token in ("sk-", "api_key", "apikey", ".env", "http://", "https://", "script")):
        report.add(ValidationSeverity.ERROR, "quest_pack.safety", "Quest pack drafts cannot contain API keys, scripts, environment references, or remote URLs.", code="quest_pack_unsafe_reference")


def _generate_content(
    draft: QuestPackGeneratorDraft,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> QuestPackGeneratedContent:
    npcs = draft.involved_npcs or sorted(_load_world_ids(draft.target_world_id, service, report)["npcs"])[:1] or ["player"]
    locations = draft.involved_locations or sorted(_load_world_ids(draft.target_world_id, service, report)["locations"])[:1] or ["start"]
    quests: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    rumors: list[dict[str, Any]] = []
    for index in range(draft.quest_count):
        quest_id = f"{draft.pack_id}_quest_{index + 1}"
        npc_id = npcs[index % len(npcs)]
        location_id = locations[index % len(locations)]
        clue_fact_id = draft.required_facts[index % len(draft.required_facts)] if draft.required_facts else f"{quest_id}_clue"
        if not draft.required_facts:
            facts.append(
                {
                    "id": clue_fact_id,
                    "text": f"Hidden quest clue for {quest_id}.",
                    "visibility": "hidden" if draft.mystery_mode else "discoverable",
                    "known_by": [npc_id] if npc_id != "player" else [],
                    "tags": ["quest_pack_generator", "clue", f"location:{location_id}"],
                }
            )
        start_stage = {
            "id": "start",
            "title": "Start",
            "description": "Begin the generated questline.",
            "objectives": [{"id": f"talk_{npc_id}", "text": "Speak with the involved NPC.", "visibility": "public"}],
            "next_stages": ["investigate"],
        }
        investigate_objective: dict[str, Any] = {"id": f"discover_{clue_fact_id}", "text": "Find the next clue.", "visibility": "public"}
        if draft.mystery_mode:
            investigate_objective = {**investigate_objective, "visibility": "hidden", "hidden_authoring_note": "Mystery clue objective remains authoring-only until discovered."}
        investigate_stage = {
            "id": "investigate",
            "title": "Investigate",
            "description": "Follow the generated lead without exposing hidden answers.",
            "objectives": [investigate_objective],
            "next_stages": [],
        }
        if draft.failure_paths_enabled:
            start_stage["failure_stages"] = ["failed"]
            investigate_stage["failure_stages"] = ["failed"]
        stages = [start_stage, investigate_stage]
        if draft.failure_paths_enabled:
            stages.append({"id": "failed", "title": "Failed Lead", "description": "The lead goes cold.", "objectives": [], "next_stages": []})
        quests.append(
            {
                "id": quest_id,
                "title": f"{draft.theme.title()} {index + 1}",
                "description": "A generated quest draft with local validation coverage.",
                "initial_stage": "start",
                "visibility": "public",
                "stages": stages,
                "triggers": [
                    {"type": "npc_talked", "id": npc_id, "action": "complete_objective", "objective_id": f"talk_{npc_id}", "next_stage": "investigate"},
                    {"type": "fact_discovered", "id": clue_fact_id, "action": "complete_objective", "objective_id": f"discover_{clue_fact_id}"},
                ],
                "rewards": [{"id": f"{quest_id}_reward", "text": draft.reward_policy, "reward_type": "policy"}],
            }
        )
        if draft.mystery_mode:
            rumors.append({"id": f"{quest_id}_rumor", "text": "A vague rumor points toward a generated mystery.", "visibility": "public", "known_by": [npc_id], "tags": ["quest_pack_generator"]})
    temp_quests_yaml = yaml.safe_dump({"quests": quests}, sort_keys=False, allow_unicode=True)
    graph = quest_yaml_to_graph(draft.target_world_id, temp_quests_yaml)
    scenarios = [
        generate_scenario_regression_draft(draft.target_world_id, QuestGraph(world_id=draft.target_world_id, quests=[quest], edges=[]))
        for quest in graph.quests
    ]
    quality = ValidationReport(world_id=draft.target_world_id)
    if draft.mystery_mode:
        quality.add(ValidationSeverity.WARNING, "quest_pack.mystery_mode", "Mystery mode generated hidden clue objectives; review visibility before release.", code="quest_pack_hidden_objective_review")
    return QuestPackGeneratedContent(
        quest_candidates=quests,
        fact_candidates=facts,
        rumor_candidates=rumors,
        scenario_regression_candidates=scenarios,
        quest_graph=graph,
        quality_checks=quality,
    )


def _generated_to_yaml(
    draft: QuestPackGeneratorDraft,
    generated: QuestPackGeneratedContent,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> dict[str, str]:
    existing_quests = _read_list_file(service, draft.target_world_id, "quests.yaml", "quests", report)
    existing_facts = _read_list_file(service, draft.target_world_id, "facts.yaml", "facts", report)
    existing_rumors = _read_list_file(service, draft.target_world_id, "rumors.yaml", "rumors", report, required=False)
    if report.errors:
        return {}
    existing_ids = {str(quest.get("id", "")) for quest in existing_quests}
    if any(str(quest.get("id", "")) in existing_ids for quest in generated.quest_candidates):
        report.add(ValidationSeverity.ERROR, "quest_pack.quest_ids", "Generated quest id collides with an existing quest.", code="quest_pack_duplicate_quest")
        return {}
    contents = {
        "quests.yaml": yaml.safe_dump({"quests": existing_quests + generated.quest_candidates}, sort_keys=False, allow_unicode=True),
        "facts.yaml": yaml.safe_dump({"facts": existing_facts + generated.fact_candidates}, sort_keys=False, allow_unicode=True),
    }
    if generated.rumor_candidates:
        contents["rumors.yaml"] = yaml.safe_dump({"rumors": existing_rumors + generated.rumor_candidates}, sort_keys=False, allow_unicode=True)
    return contents


def _load_world_ids(world_id: str, service: ContentAuthoringService, report: ValidationReport) -> dict[str, set[str]]:
    return {
        "npcs": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "npcs.yaml", "npcs", report)},
        "locations": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "locations.yaml", "locations", report)},
        "factions": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "factions.yaml", "factions", report, required=False)},
        "facts": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "facts.yaml", "facts", report)},
    }


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
    report: ValidationReport,
    *,
    required: bool = True,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except AuthoringError:
        if required:
            report.add(ValidationSeverity.ERROR, file_name, f"Required content file is missing: {file_name}", code="quest_pack_missing_file")
        return []
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        report.add(ValidationSeverity.ERROR, file_name, f"Invalid YAML: {exc}", code="quest_pack_invalid_yaml")
        return []
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)]
