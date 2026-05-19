from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class FactionTemplateError(ValueError):
    """Raised when a faction template operation is invalid or unsafe."""


class FactionTemplateRelation(BaseModel):
    target_faction_id: str
    value: int = Field(default=0, ge=-100, le=100)
    relation_type: str = "neutral"
    conflict_level: int = Field(default=0, ge=0, le=100)
    hidden: bool = False


class FactionTemplateDuty(BaseModel):
    duty_type: str
    target_id: str | None = None
    target_type: str | None = None
    priority: int = 0


class FactionTemplateQuestHook(BaseModel):
    id: str
    title: str
    description: str = ""
    visibility: str = "public"


class FactionTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    faction_type: str
    default_reputation: int = Field(default=0, ge=-100, le=100)
    relations: list[FactionTemplateRelation] = Field(default_factory=list)
    duties: list[FactionTemplateDuty] = Field(default_factory=list)
    ranks: list[str] = Field(default_factory=list)
    typical_npc_archetypes: list[str] = Field(default_factory=list)
    rumor_policies: dict[str, Any] = Field(default_factory=dict)
    crime_policies: dict[str, Any] = Field(default_factory=dict)
    quest_hooks: list[FactionTemplateQuestHook] = Field(default_factory=list)
    hidden: bool = False
    tags: list[str] = Field(default_factory=list)


class FactionTemplatePreviewRequest(BaseModel):
    target_world_id: str
    faction_id: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    confirm_apply: bool = False
    confirm_warnings: bool = False


class FactionTemplateGeneratedContent(BaseModel):
    factions_draft: list[dict[str, Any]] = Field(default_factory=list)
    npc_faction_duty_candidates: list[dict[str, Any]] = Field(default_factory=list)
    relationship_candidates: list[dict[str, Any]] = Field(default_factory=list)
    quest_hook_candidates: list[dict[str, Any]] = Field(default_factory=list)


class FactionTemplatePreview(BaseModel):
    template: FactionTemplate
    target_world_id: str
    generated: FactionTemplateGeneratedContent
    yaml_contents: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    writes_to_disk: bool = False
    applied: bool = False
    confirmation_required: bool = False


class FactionTemplateList(BaseModel):
    local_only: bool = True
    templates: list[FactionTemplate] = Field(default_factory=list)


def list_faction_templates() -> list[FactionTemplate]:
    return [FactionTemplate.model_validate(item) for item in _BUILT_IN_TEMPLATES]


def get_faction_template(template_id: str) -> FactionTemplate:
    for template in list_faction_templates():
        if template.id == template_id:
            return template
    raise FactionTemplateError(f"Unknown faction template: {template_id}")


def preview_faction_template(
    template_id: str,
    request: FactionTemplatePreviewRequest,
    service: ContentAuthoringService,
) -> FactionTemplatePreview:
    return preview_faction_template_object(get_faction_template(template_id), request, service)


def preview_faction_template_object(
    template: FactionTemplate,
    request: FactionTemplatePreviewRequest,
    service: ContentAuthoringService,
) -> FactionTemplatePreview:
    report = ValidationReport(world_id=request.target_world_id)
    faction_id = request.faction_id or template.id
    _validate_template(template, request.target_world_id, faction_id, service, report)
    generated = _generate(template, faction_id) if not report.errors else FactionTemplateGeneratedContent()
    yaml_contents = _generated_to_yaml(request.target_world_id, generated, service, report) if not report.errors else {}
    if not report.errors:
        draft_report = service.validate_drafts(request.target_world_id, yaml_contents)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
    return FactionTemplatePreview(
        template=template,
        target_world_id=request.target_world_id,
        generated=generated,
        yaml_contents=yaml_contents,
        validation=report,
        writes_to_disk=False,
        applied=False,
        confirmation_required=report.ok and bool(report.warnings),
    )


def apply_faction_template(
    template_id: str,
    request: FactionTemplatePreviewRequest,
    service: ContentAuthoringService,
) -> FactionTemplatePreview:
    preview = preview_faction_template(template_id, request, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "faction_template.apply",
            "Faction template apply requires explicit confirmation.",
            code="faction_template_apply_requires_confirmation",
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


def _validate_template(
    template: FactionTemplate,
    world_id: str,
    faction_id: str,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> None:
    ids = _load_world_ids(world_id, service, report)
    if faction_id in ids["factions"]:
        report.add(
            ValidationSeverity.ERROR,
            f"faction_template.{template.id}.faction_id",
            f"Faction already exists: {faction_id}",
            code="faction_template_duplicate_faction",
            ref_id=faction_id,
        )
    known_after_apply = set(ids["factions"]) | {faction_id}
    for relation in template.relations:
        if relation.target_faction_id not in known_after_apply:
            report.add(
                ValidationSeverity.ERROR,
                f"faction_template.{template.id}.relations.{relation.target_faction_id}",
                f"Relation target faction does not exist: {relation.target_faction_id}",
                code="faction_template_invalid_relation",
                ref_id=relation.target_faction_id,
            )
    unsafe = "\n".join([template.name, template.faction_type, *template.ranks, *template.typical_npc_archetypes]).lower()
    if any(token in unsafe for token in ("sk-", "api_key", ".env", "http://", "https://", "script")):
        report.add(
            ValidationSeverity.ERROR,
            f"faction_template.{template.id}.safety",
            "Faction templates cannot contain API keys, scripts, remote URLs, or environment references.",
            code="faction_template_unsafe_reference",
        )


def _generate(template: FactionTemplate, faction_id: str) -> FactionTemplateGeneratedContent:
    relations = {relation.target_faction_id: relation.value for relation in template.relations}
    faction = {
        "id": faction_id,
        "name": template.name,
        "description": f"{template.faction_type} faction generated from local template.",
        "default_reputation": template.default_reputation,
        "known_by_player": not template.hidden,
        "relations": relations,
        "default_alert_level": 0,
        "conflict_tags": [template.faction_type],
        "tags": sorted(set([template.faction_type, *template.tags, *(["hidden"] if template.hidden else [])])),
        "ranks": template.ranks,
        "rumor_policies": template.rumor_policies,
        "crime_policies": template.crime_policies,
    }
    duty_candidates = [
        {
            "id": f"{faction_id}_{duty.duty_type}_{index + 1}",
            "duty_type": duty.duty_type,
            "priority": duty.priority,
            "faction_id": faction_id,
            "target_id": duty.target_id,
            "target_type": duty.target_type,
            "debug_reason": "candidate_only",
        }
        for index, duty in enumerate(template.duties)
    ]
    relationship_candidates = [
        {
            "id": f"{faction_id}_{relation.target_faction_id}_{relation.relation_type}",
            "source_faction_id": faction_id,
            "target_faction_id": relation.target_faction_id,
            "relation_type": relation.relation_type,
            "relation": relation.value,
            "conflict_level": relation.conflict_level,
            "visibility": "hidden" if template.hidden or relation.hidden else "player_visible",
            "conflict_tags": [template.faction_type],
        }
        for relation in template.relations
    ]
    quest_hooks = [
        {
            "id": hook.id,
            "title": hook.title,
            "description": hook.description or f"Quest hook for {template.name}.",
            "initial_stage": "start",
            "visibility": hook.visibility,
            "stages": [
                {
                    "id": "start",
                    "title": "Start",
                    "description": "Review the generated faction hook before release.",
                    "objectives": [f"review_{hook.id}"],
                    "next_stages": [],
                }
            ],
            "triggers": [],
            "rewards": [{"id": f"{hook.id}_reward", "text": "Faction hook reviewed.", "reward_type": "authoring"}],
        }
        for hook in template.quest_hooks
    ]
    return FactionTemplateGeneratedContent(
        factions_draft=[faction],
        npc_faction_duty_candidates=duty_candidates,
        relationship_candidates=relationship_candidates,
        quest_hook_candidates=quest_hooks,
    )


def _generated_to_yaml(
    world_id: str,
    generated: FactionTemplateGeneratedContent,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> dict[str, str]:
    factions = _read_list_file(service, world_id, "factions.yaml", "factions", report)
    quests = _read_list_file(service, world_id, "quests.yaml", "quests", report)
    if report.errors:
        return {}
    return {
        "factions.yaml": yaml.safe_dump(
            {"factions": factions + generated.factions_draft},
            sort_keys=False,
            allow_unicode=True,
        ),
        "quests.yaml": yaml.safe_dump(
            {"quests": quests + generated.quest_hook_candidates},
            sort_keys=False,
            allow_unicode=True,
        ),
    }


def _load_world_ids(world_id: str, service: ContentAuthoringService, report: ValidationReport) -> dict[str, set[str]]:
    return {
        "factions": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "factions.yaml", "factions", report)},
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
            report.add(ValidationSeverity.ERROR, file_name, f"Required content file is missing: {file_name}", code="faction_template_missing_file")
        return []
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        report.add(ValidationSeverity.ERROR, file_name, f"Invalid YAML: {exc}", code="faction_template_invalid_yaml")
        return []
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)]


_BUILT_IN_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "city_watch",
        "name": "City Watch",
        "faction_type": "law",
        "default_reputation": 0,
        "relations": [
            {"target_faction_id": "old_road_smugglers", "value": -25, "relation_type": "hostile", "conflict_level": 2}
        ],
        "duties": [
            {"duty_type": "guard_location", "target_type": "location", "priority": 5},
            {"duty_type": "report_crime_to_faction", "priority": 4},
        ],
        "ranks": ["captain", "watcher", "recruit"],
        "typical_npc_archetypes": ["guard", "investigator", "captain"],
        "rumor_policies": {"public_crime_rumors": "investigate"},
        "crime_policies": {"violent_crime": "raise_alert"},
        "quest_hooks": [{"id": "city_watch_patrol_hook", "title": "Patrol Report"}],
        "hidden": False,
        "tags": ["civic"],
    },
    {
        "id": "secret_cell",
        "name": "Secret Cell",
        "faction_type": "covert",
        "default_reputation": 0,
        "relations": [{"target_faction_id": "village_council", "value": -10, "relation_type": "hidden_hostility", "conflict_level": 1, "hidden": True}],
        "duties": [{"duty_type": "seek_information", "priority": 5}],
        "ranks": ["handler", "agent"],
        "typical_npc_archetypes": ["informant", "saboteur"],
        "rumor_policies": {"secrets": "withhold"},
        "crime_policies": {"witnessed": "avoid_report"},
        "quest_hooks": [{"id": "secret_cell_contact_hook", "title": "Hidden Contact", "visibility": "hidden"}],
        "hidden": True,
        "tags": ["hidden"],
    },
]
