from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from app.core.state_delta import StateDeltaOperation
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.roleplay.dialogue import DialogueMode


class DialogueSceneAuthoringError(ValueError):
    """Raised when dialogue scene authoring input is invalid."""


class DialogueSceneOutcomeTemplate(BaseModel):
    id: str
    description: str = ""
    state_delta_operation: str | None = None
    state_delta_path: str | None = None
    allowed: bool = False


class DialogueSceneTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    participant_ids: list[str] = Field(default_factory=list)
    focus_npc_id: str
    location_id: str
    dialogue_mode: DialogueMode = DialogueMode.FOCUSED
    scene_mood: str | None = None
    rp_prompt_profile_id: str | None = None
    opening_context: str = ""
    allowed_topics: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    required_visible_facts: list[str] = Field(default_factory=list)
    possible_outcomes: list[DialogueSceneOutcomeTemplate] = Field(default_factory=list)

    @field_validator("participant_ids", "allowed_topics", "forbidden_topics", "required_visible_facts")
    @classmethod
    def reject_path_like_values(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized = value.replace("\\", "/")
            if "../" in normalized or normalized.startswith("/") or normalized.startswith("~"):
                raise ValueError(f"Unsafe dialogue scene value: {value}")
        return values


class DialogueSceneAuthoring(BaseModel):
    world_id: str
    templates: list[DialogueSceneTemplate] = Field(default_factory=list)


class DialogueScenePreview(BaseModel):
    world_id: str
    graph: DialogueSceneAuthoring
    yaml_content: str
    validation: ValidationReport
    prompt_preview: dict[str, str] = Field(default_factory=dict)
    confirmation_required: bool = False


class DialogueSceneSaveResponse(DialogueScenePreview):
    saved: bool = False


def parse_dialogue_scene_authoring(world_id: str, service: ContentAuthoringService) -> DialogueSceneAuthoring:
    try:
        content = service.read_file(world_id, "dialogue_scenes.yaml")
    except Exception:
        return DialogueSceneAuthoring(world_id=world_id, templates=[])
    data = yaml.safe_load(content) or {}
    if not isinstance(data, dict):
        raise DialogueSceneAuthoringError("dialogue_scenes.yaml must contain a mapping.")
    values = data.get("dialogue_scenes", [])
    if not isinstance(values, list):
        raise DialogueSceneAuthoringError("dialogue_scenes.yaml dialogue_scenes must be a list.")
    return DialogueSceneAuthoring(
        world_id=world_id,
        templates=[DialogueSceneTemplate.model_validate(item) for item in values if isinstance(item, dict)],
    )


def dialogue_scenes_to_yaml(world_id: str, graph: DialogueSceneAuthoring) -> str:
    if graph.world_id != world_id:
        raise DialogueSceneAuthoringError(f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}")
    return yaml.safe_dump(
        {
            "dialogue_scenes": [
                template.model_dump(mode="json", exclude_none=True)
                for template in sorted(graph.templates, key=lambda item: item.id)
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    )


def preview_dialogue_scene_authoring(
    world_id: str,
    graph: DialogueSceneAuthoring,
    service: ContentAuthoringService,
) -> DialogueScenePreview:
    yaml_content = dialogue_scenes_to_yaml(world_id, graph)
    validation = service.validate_draft(world_id, "dialogue_scenes.yaml", yaml_content)
    _add_dialogue_scene_validation(validation, graph, service)
    return DialogueScenePreview(
        world_id=world_id,
        graph=graph,
        yaml_content=yaml_content,
        validation=validation,
        prompt_preview={template.id: _safe_prompt_preview(template, service, world_id) for template in graph.templates},
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_dialogue_scene_authoring(
    world_id: str,
    graph: DialogueSceneAuthoring,
    service: ContentAuthoringService,
) -> DialogueScenePreview:
    return preview_dialogue_scene_authoring(world_id, graph, service)


def save_dialogue_scene_authoring(
    world_id: str,
    graph: DialogueSceneAuthoring,
    service: ContentAuthoringService,
    *,
    confirm_warnings: bool = False,
) -> DialogueSceneSaveResponse:
    preview = preview_dialogue_scene_authoring(world_id, graph, service)
    if not preview.validation.ok or (preview.validation.warnings and not confirm_warnings):
        return DialogueSceneSaveResponse(**preview.model_dump(), saved=False)
    validation = service.write_file(world_id, "dialogue_scenes.yaml", preview.yaml_content, confirm_warnings=confirm_warnings)
    return DialogueSceneSaveResponse(
        world_id=world_id,
        graph=graph,
        yaml_content=preview.yaml_content,
        validation=validation,
        prompt_preview=preview.prompt_preview,
        confirmation_required=validation.ok and bool(validation.warnings) and not confirm_warnings,
        saved=validation.ok,
    )


def _add_dialogue_scene_validation(
    validation: ValidationReport,
    graph: DialogueSceneAuthoring,
    service: ContentAuthoringService,
) -> None:
    npcs = {str(item.get("id", "")) for item in _read_list_file(service, graph.world_id, "npcs.yaml", "npcs")}
    locations = {str(item.get("id", "")) for item in _read_list_file(service, graph.world_id, "locations.yaml", "locations")}
    facts = _fact_visibility(service, graph.world_id)
    moods = {str(item.get("id", "")) for item in _read_list_file(service, graph.world_id, "scene_moods.yaml", "scene_mood_presets", required=False)}
    seen: set[str] = set()
    for template in graph.templates:
        if template.id in seen:
            validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}", "Duplicate dialogue scene template id.", code="dialogue_scene_duplicate_id", ref_id=template.id)
        seen.add(template.id)
        participants = set(template.participant_ids + [template.focus_npc_id])
        for npc_id in sorted(participants):
            if npc_id not in npcs:
                validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.participant_ids", "Dialogue scene participant does not exist.", code="dialogue_scene_missing_participant", ref_id=npc_id)
        if template.focus_npc_id not in template.participant_ids:
            validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.focus_npc_id", "Focus NPC must be included in participant_ids.", code="dialogue_scene_focus_not_participant", ref_id=template.focus_npc_id)
        if template.location_id not in locations:
            validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.location_id", "Dialogue scene location does not exist.", code="dialogue_scene_missing_location", ref_id=template.location_id)
        if template.scene_mood and template.scene_mood not in moods:
            validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.scene_mood", "Scene mood preset does not exist.", code="dialogue_scene_missing_mood", ref_id=template.scene_mood)
        for fact_id in template.required_visible_facts:
            visibility = facts.get(fact_id)
            if visibility is None:
                validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.required_visible_facts", "Required visible fact does not exist.", code="dialogue_scene_missing_visible_fact", ref_id=fact_id)
            elif visibility != "public":
                validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.required_visible_facts", "Required dialogue fact is hidden and cannot be prompt-required.", code="dialogue_scene_hidden_required_fact", ref_id=fact_id)
        hidden_topics = _hidden_topic_terms(service, graph.world_id)
        for topic in template.forbidden_topics:
            if topic in hidden_topics and topic in template.allowed_topics:
                validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.forbidden_topics", "Hidden forbidden topic cannot also be promptable.", code="dialogue_scene_hidden_topic_promptable", ref_id=topic)
        for outcome in template.possible_outcomes:
            if outcome.state_delta_operation or outcome.state_delta_path:
                if not outcome.allowed:
                    validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.possible_outcomes", "StateDelta outcome templates are disabled unless explicitly allowed.", code="dialogue_scene_outcome_delta_not_allowed", ref_id=outcome.id)
                elif outcome.state_delta_operation not in {operation.value for operation in StateDeltaOperation}:
                    validation.add(ValidationSeverity.ERROR, f"dialogue_scenes.{template.id}.possible_outcomes", "Possible outcome uses an invalid StateDelta operation.", code="dialogue_scene_invalid_delta_operation", ref_id=outcome.id)


def _safe_prompt_preview(template: DialogueSceneTemplate, service: ContentAuthoringService, world_id: str) -> str:
    hidden_terms = _hidden_topic_terms(service, world_id)
    safe_opening = template.opening_context
    for term in sorted(hidden_terms | set(template.forbidden_topics), key=len, reverse=True):
        if term:
            safe_opening = safe_opening.replace(term, "[filtered-topic]")
    safe_topics = [topic for topic in template.allowed_topics if topic not in set(template.forbidden_topics) and topic not in hidden_terms]
    return (
        f"scene={template.id}; focus={template.focus_npc_id}; mode={template.dialogue_mode.value}; "
        f"mood={template.scene_mood or 'default'}; topics={','.join(safe_topics)}; opening={safe_opening}"
    )


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
    *,
    required: bool = True,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except Exception as exc:
        if required:
            raise DialogueSceneAuthoringError(str(exc)) from exc
        return []
    data = yaml.safe_load(content) or {}
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _fact_visibility(service: ContentAuthoringService, world_id: str) -> dict[str, str]:
    return {
        str(fact.get("id", "")): str(fact.get("visibility", "hidden"))
        for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False)
    }


def _hidden_topic_terms(service: ContentAuthoringService, world_id: str) -> set[str]:
    terms: set[str] = set()
    for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False):
        if str(fact.get("visibility", "")) != "public":
            terms.add(str(fact.get("id", "")))
            text = str(fact.get("text", ""))
            if text:
                terms.add(text)
    return terms
