from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.scenario_templates import ScenarioTemplate, ScenarioTemplateOutputFile, ScenarioTemplateType
from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.engine.content.validation_gate import AuthoringOperationType, AuthoringValidationGateRequest


class TemplateWizardError(ValueError):
    """Raised when a template wizard draft is invalid or unsafe."""


class TemplateWizardType(StrEnum):
    WORLD = "world"
    LOCATION_CLUSTER = "location_cluster"
    QUESTLINE = "questline"
    NPC_SET = "npc_set"
    CHARACTER_PACK = "character_pack"
    DIALOGUE_SCENE = "dialogue_scene"
    GROUP_RP_SCENE = "group_rp_scene"
    FACTION_CONFLICT = "faction_conflict"
    MYSTERY_CASE = "mystery_case"


class TemplateWizardStep(StrEnum):
    CHOOSE_TEMPLATE_TYPE = "choose_template_type"
    FILL_VARIABLES = "fill_variables"
    PREVIEW_GENERATED_CONTENT = "preview_generated_content"
    VALIDATE = "validate"
    SAVE_APPLY = "save_apply"


class TemplateWizardDraft(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    template_type: TemplateWizardType
    current_step: TemplateWizardStep = TemplateWizardStep.CHOOSE_TEMPLATE_TYPE
    variables: dict[str, str] = Field(default_factory=dict)
    target_world_id: str | None = None
    save_as_template: bool = False


class TemplateWizardGeneratedFile(BaseModel):
    file_name: str
    content: str


class TemplateWizardPreview(BaseModel):
    draft: TemplateWizardDraft
    generated_files: list[TemplateWizardGeneratedFile] = Field(default_factory=list)
    validation: ValidationReport | None = None
    writes_to_disk: bool = False
    applied: bool = False
    saved_template: bool = False


class TemplateWizardApplyRequest(BaseModel):
    draft: TemplateWizardDraft
    confirm_apply: bool = False
    confirm_warnings: bool = False


def preview_template_wizard_draft(
    draft: TemplateWizardDraft,
    service: ContentAuthoringService,
) -> TemplateWizardPreview:
    report = ValidationReport(world_id=draft.target_world_id or _variable(draft, "world_id", draft.id))
    _validate_variables(draft, report)
    files = _generate_files(draft) if not report.errors else []
    validation = _validate_generated_files(draft, files, service, report)
    return TemplateWizardPreview(
        draft=draft.model_copy(update={"current_step": TemplateWizardStep.PREVIEW_GENERATED_CONTENT}),
        generated_files=files,
        validation=validation,
        writes_to_disk=False,
    )


def validate_template_wizard_draft(
    draft: TemplateWizardDraft,
    service: ContentAuthoringService,
) -> TemplateWizardPreview:
    preview = preview_template_wizard_draft(draft, service)
    preview.draft.current_step = TemplateWizardStep.VALIDATE
    return preview


def apply_template_wizard_draft(
    request: TemplateWizardApplyRequest,
    service: ContentAuthoringService,
    *,
    templates_root: str | Path = "templates",
) -> TemplateWizardPreview:
    preview = validate_template_wizard_draft(request.draft, service)
    if not request.confirm_apply:
        if preview.validation is None:
            preview.validation = ValidationReport(world_id=request.draft.target_world_id or request.draft.id)
        preview.validation.add(
            ValidationSeverity.ERROR,
            "template_wizard.apply",
            "Template Wizard apply requires explicit confirmation.",
            code="template_wizard_apply_requires_confirmation",
        )
        return preview
    if preview.validation is None or not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        return preview
    if request.draft.save_as_template:
        _save_wizard_template(request.draft, preview.generated_files, templates_root)
        preview.saved_template = True
        preview.writes_to_disk = True
        preview.draft.current_step = TemplateWizardStep.SAVE_APPLY
        return preview
    if request.draft.template_type == TemplateWizardType.WORLD:
        world_id = _variable(request.draft, "world_id", request.draft.id)
        world_path = _safe_new_world_path(service, world_id)
        gate = service.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.APPLY_TEMPLATE,
                draft_content={file.file_name: file.content for file in preview.generated_files},
                affected_files=[file.file_name for file in preview.generated_files],
                validation_report=preview.validation,
                confirm_warnings=request.confirm_warnings,
            )
        )
        preview.validation = gate.validation_report
        if not gate.allowed_to_save:
            return preview
        world_path.mkdir(parents=True)
        try:
            for file in preview.generated_files:
                (world_path / file.file_name).write_text(file.content, encoding="utf-8")
        except Exception:
            for child in world_path.iterdir():
                child.unlink()
            world_path.rmdir()
            raise
        final_validation = validate_world_pack(world_id, worlds_root=service.worlds_root)
        if not final_validation.ok:
            for child in world_path.iterdir():
                child.unlink()
            world_path.rmdir()
            preview.validation = final_validation
            return preview
        preview.validation = final_validation
    else:
        if not request.draft.target_world_id:
            raise TemplateWizardError("Applying non-world wizard drafts requires target_world_id.")
        report = service.write_files(
            request.draft.target_world_id,
            {file.file_name: file.content for file in preview.generated_files},
            confirm_warnings=request.confirm_warnings,
        )
        preview.validation = report
        if not report.ok:
            return preview
    preview.applied = True
    preview.writes_to_disk = True
    preview.draft.current_step = TemplateWizardStep.SAVE_APPLY
    return preview


def _generate_files(draft: TemplateWizardDraft) -> list[TemplateWizardGeneratedFile]:
    if draft.template_type == TemplateWizardType.WORLD:
        return _world_files(draft)
    file_name, root_key, item = _single_item_template(draft)
    existing = _existing_items(draft, file_name, root_key)
    return [
        TemplateWizardGeneratedFile(
            file_name=file_name,
            content=yaml.safe_dump({root_key: existing + [item]}, sort_keys=False, allow_unicode=True),
        )
    ]


def _single_item_template(draft: TemplateWizardDraft) -> tuple[str, str, dict[str, Any]]:
    item_id = _variable(draft, "id", draft.id)
    name = _variable(draft, "name", draft.name)
    location_id = _variable(draft, "location_id", "village_square")
    npc_id = _variable(draft, "npc_id", "harlan")
    if draft.template_type == TemplateWizardType.LOCATION_CLUSTER:
        return "locations.yaml", "locations", {"id": item_id, "name": name, "description": _variable(draft, "description", "A new location cluster."), "exits": {}}
    if draft.template_type == TemplateWizardType.QUESTLINE:
        return "quests.yaml", "quests", {"id": item_id, "title": name, "description": _variable(draft, "description", "A new questline."), "initial_stage": "start", "visibility": "public", "stages": [{"id": "start", "title": "Start", "description": "Begin the thread.", "objectives": ["begin_" + item_id], "next_stages": []}], "triggers": [{"type": "npc_talked", "id": npc_id, "action": "complete_objective", "objective_id": "begin_" + item_id}]}
    if draft.template_type in {TemplateWizardType.NPC_SET, TemplateWizardType.CHARACTER_PACK}:
        return "npcs.yaml", "npcs", {"id": item_id, "name": name, "location_id": location_id, "personality": _variable(draft, "personality", "Locally grounded and story-ready.")}
    if draft.template_type == TemplateWizardType.DIALOGUE_SCENE:
        return "dialogue_scenes.yaml", "dialogue_scenes", {"id": item_id, "name": name, "participant_ids": [npc_id], "focus_npc_id": npc_id, "location_id": location_id, "dialogue_mode": "focused", "opening_context": _variable(draft, "opening_context", "A grounded conversation begins."), "allowed_topics": _csv(draft, "allowed_topics"), "forbidden_topics": _csv(draft, "forbidden_topics"), "required_visible_facts": [], "possible_outcomes": []}
    if draft.template_type == TemplateWizardType.GROUP_RP_SCENE:
        participants = _csv(draft, "participant_ids") or [npc_id]
        return "group_rp_scenes.yaml", "group_rp_scenes", {"id": item_id, "name": name, "scene_type": _variable(draft, "scene_type", "meeting"), "participant_ids": participants, "required_roles": [{"role_id": "speaker", "npc_id": participants[0], "label": "Speaker", "required": True}], "location_id": location_id, "turn_order_policy": "round_robin", "speaker_selection_policy": "deterministic", "scene_mood": _empty_to_none(_variable(draft, "scene_mood", "")), "starting_tension": int(_variable(draft, "starting_tension", "10")), "opening_public_context": _variable(draft, "opening_public_context", "A group scene begins."), "allowed_topics": _csv(draft, "allowed_topics"), "forbidden_topics": _csv(draft, "forbidden_topics"), "exit_conditions": _csv(draft, "exit_conditions"), "allow_dead_participants": False}
    if draft.template_type == TemplateWizardType.FACTION_CONFLICT:
        return "factions.yaml", "factions", {"id": item_id, "name": name, "description": _variable(draft, "description", "A faction with editable conflict hooks."), "default_reputation": 0, "known_by_player": True, "relations": {}}
    return "facts.yaml", "facts", {"id": item_id, "text": _variable(draft, "clue_text", name), "visibility": "public", "known_by": ["player"], "tags": ["mystery"]}


def _world_files(draft: TemplateWizardDraft) -> list[TemplateWizardGeneratedFile]:
    world_id = _variable(draft, "world_id", draft.id)
    world_name = _variable(draft, "world_name", draft.name)
    start_location_id = _variable(draft, "start_location_id", "start")
    npc_id = _variable(draft, "npc_id", "guide")
    files = {
        "manifest.yaml": {"world_id": world_id, "name": world_name, "version": "0.1.0", "description": _variable(draft, "description", "A wizard-created local world."), "start_location_id": start_location_id},
        "locations.yaml": {"locations": [{"id": start_location_id, "name": _variable(draft, "start_location_name", "Start"), "description": "The first authored location.", "exits": {}}]},
        "npcs.yaml": {"npcs": [{"id": npc_id, "name": _variable(draft, "npc_name", "Guide"), "location_id": start_location_id, "personality": "Helpful and observant."}]},
        "items.yaml": {"items": []},
        "quests.yaml": {"quests": []},
        "facts.yaml": {"facts": [{"id": "world_ready", "text": f"{world_name} is ready for play.", "visibility": "public", "known_by": ["player"], "tags": ["template_wizard"]}]},
        "factions.yaml": {"factions": []},
        "rumors.yaml": {"rumors": []},
        "relationships.yaml": {"relationships": []},
    }
    return [TemplateWizardGeneratedFile(file_name=name, content=yaml.safe_dump(content, sort_keys=False, allow_unicode=True)) for name, content in files.items()]


def _validate_generated_files(
    draft: TemplateWizardDraft,
    files: list[TemplateWizardGeneratedFile],
    service: ContentAuthoringService,
    report: ValidationReport,
) -> ValidationReport:
    if report.errors:
        return report
    if draft.template_type == TemplateWizardType.WORLD:
        world_id = _variable(draft, "world_id", draft.id)
        if (service.worlds_root / world_id).exists():
            report.add(ValidationSeverity.ERROR, "template_wizard.world_id", "World pack already exists.", code="template_wizard_world_exists", ref_id=world_id)
            return report
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "worlds"
            world_path = root / world_id
            world_path.mkdir(parents=True)
            for file in files:
                (world_path / file.file_name).write_text(file.content, encoding="utf-8")
            validation = validate_world_pack(world_id, worlds_root=root)
    else:
        if not draft.target_world_id:
            report.add(ValidationSeverity.ERROR, "template_wizard.target_world_id", "Non-world wizard drafts require target_world_id.", code="template_wizard_missing_target_world")
            return report
        validation = service.validate_drafts(draft.target_world_id, {file.file_name: file.content for file in files})
    report.errors.extend(validation.errors)
    report.warnings.extend(validation.warnings)
    report.suggestions.extend(validation.suggestions)
    return report


def _save_wizard_template(draft: TemplateWizardDraft, files: list[TemplateWizardGeneratedFile], templates_root: str | Path) -> None:
    root = Path(templates_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = (root / f"{draft.id}.yaml").resolve()
    if root != path.parent:
        raise TemplateWizardError("Template save path escapes templates root.")
    template_type = ScenarioTemplateType.WORLD if draft.template_type == TemplateWizardType.WORLD else ScenarioTemplateType.LOCATION_CLUSTER
    template = ScenarioTemplate(
        id=draft.id,
        name=draft.name,
        description="Created by Template Wizard.",
        template_type=template_type,
        output_files=[ScenarioTemplateOutputFile(file_name=file.file_name, content=file.content) for file in files],
        tags=["template_wizard", draft.template_type.value],
    )
    path.write_text(yaml.safe_dump(template.model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8")


def _validate_variables(draft: TemplateWizardDraft, report: ValidationReport) -> None:
    values = {**draft.variables, "id": draft.id, "name": draft.name}
    if draft.target_world_id:
        values["target_world_id"] = draft.target_world_id
    for key, value in values.items():
        if not _safe_variable_name(key) or _unsafe_value(value):
            report.add(ValidationSeverity.ERROR, f"template_wizard.variables.{key}", "Template Wizard variable is unsafe.", code="template_wizard_invalid_variable", ref_id=key)
    required = {"id", "name"}
    if draft.template_type == TemplateWizardType.WORLD:
        required |= {"world_id", "world_name"}
    for key in sorted(required):
        value = draft.variables.get(key) if key not in {"id", "name"} else getattr(draft, key)
        if not str(value or "").strip():
            report.add(ValidationSeverity.ERROR, f"template_wizard.variables.{key}", "Template Wizard variable is required.", code="template_wizard_missing_variable", ref_id=key)


def _existing_items(draft: TemplateWizardDraft, file_name: str, root_key: str) -> list[dict[str, Any]]:
    return []


def _variable(draft: TemplateWizardDraft, key: str, default: str) -> str:
    value = draft.variables.get(key, default)
    return str(value if value not in (None, "") else default)


def _csv(draft: TemplateWizardDraft, key: str) -> list[str]:
    return [item.strip() for item in _variable(draft, key, "").split(",") if item.strip()]


def _empty_to_none(value: str) -> str | None:
    return value or None


def _safe_variable_name(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _unsafe_value(value: str) -> bool:
    normalized = str(value).replace("\\", "/").lower()
    return "../" in normalized or normalized.startswith("/") or normalized.startswith("~") or "http://" in normalized or "https://" in normalized or "api_key" in normalized or "sk-" in normalized


def _safe_new_world_path(service: ContentAuthoringService, world_id: str) -> Path:
    root = service.worlds_root.resolve()
    path = (root / world_id).resolve()
    if root != path and root not in path.parents:
        raise TemplateWizardError("World path escapes worlds root.")
    if path.exists():
        raise TemplateWizardError(f"World pack already exists: {world_id}")
    return path
