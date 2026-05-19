from __future__ import annotations

from enum import StrEnum
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class GroupRPSceneAuthoringError(ValueError):
    """Raised when group RP scene authoring input is invalid."""


class GroupRPSceneType(StrEnum):
    MEETING = "meeting"
    TRIAL = "trial"
    ARGUMENT = "argument"
    NEGOTIATION = "negotiation"
    BANQUET = "banquet"
    STANDOFF = "standoff"
    SECRET_REVEAL = "secret_reveal"


class TurnOrderPolicy(StrEnum):
    ROUND_ROBIN = "round_robin"
    TENSION_PRIORITY = "tension_priority"
    ROLE_PRIORITY = "role_priority"
    MANUAL = "manual"


class SpeakerSelectionPolicy(StrEnum):
    DETERMINISTIC = "deterministic"
    RELATIONSHIP_TENSION = "relationship_tension"
    EMOTIONAL_INTENSITY = "emotional_intensity"
    MANUAL = "manual"


class GroupRPParticipantRole(BaseModel):
    role_id: str
    npc_id: str
    label: str = ""
    required: bool = True


class GroupRPSceneTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = ""
    scene_type: GroupRPSceneType = GroupRPSceneType.MEETING
    participant_ids: list[str] = Field(default_factory=list)
    required_roles: list[GroupRPParticipantRole] = Field(default_factory=list)
    location_id: str
    turn_order_policy: TurnOrderPolicy = TurnOrderPolicy.ROUND_ROBIN
    speaker_selection_policy: SpeakerSelectionPolicy = SpeakerSelectionPolicy.DETERMINISTIC
    scene_mood: str | None = None
    starting_tension: int = Field(default=0, ge=0, le=100)
    opening_public_context: str = ""
    allowed_topics: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    exit_conditions: list[str] = Field(default_factory=list)
    allow_dead_participants: bool = False

    @field_validator("participant_ids", "allowed_topics", "forbidden_topics", "exit_conditions")
    @classmethod
    def reject_path_like_values(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized = value.replace("\\", "/")
            if "../" in normalized or normalized.startswith("/") or normalized.startswith("~"):
                raise ValueError(f"Unsafe group RP scene value: {value}")
        return values


class GroupRPSceneAuthoring(BaseModel):
    world_id: str
    templates: list[GroupRPSceneTemplate] = Field(default_factory=list)


class GroupRPScenePreview(BaseModel):
    world_id: str
    graph: GroupRPSceneAuthoring
    yaml_content: str
    validation: ValidationReport
    safe_prompt_preview: dict[str, str] = Field(default_factory=dict)
    confirmation_required: bool = False


class GroupRPSceneSaveResponse(GroupRPScenePreview):
    saved: bool = False


def parse_group_rp_scene_authoring(world_id: str, service: ContentAuthoringService) -> GroupRPSceneAuthoring:
    try:
        content = service.read_file(world_id, "group_rp_scenes.yaml")
    except Exception:
        return GroupRPSceneAuthoring(world_id=world_id, templates=[])
    data = yaml.safe_load(content) or {}
    if not isinstance(data, dict):
        raise GroupRPSceneAuthoringError("group_rp_scenes.yaml must contain a mapping.")
    values = data.get("group_rp_scenes", [])
    if not isinstance(values, list):
        raise GroupRPSceneAuthoringError("group_rp_scenes.yaml group_rp_scenes must be a list.")
    return GroupRPSceneAuthoring(
        world_id=world_id,
        templates=[GroupRPSceneTemplate.model_validate(item) for item in values if isinstance(item, dict)],
    )


def group_rp_scenes_to_yaml(world_id: str, graph: GroupRPSceneAuthoring) -> str:
    if graph.world_id != world_id:
        raise GroupRPSceneAuthoringError(f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}")
    return yaml.safe_dump(
        {
            "group_rp_scenes": [
                template.model_dump(mode="json", exclude_none=True)
                for template in sorted(graph.templates, key=lambda item: item.id)
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    )


def preview_group_rp_scene_authoring(
    world_id: str,
    graph: GroupRPSceneAuthoring,
    service: ContentAuthoringService,
) -> GroupRPScenePreview:
    yaml_content = group_rp_scenes_to_yaml(world_id, graph)
    validation = service.validate_draft(world_id, "group_rp_scenes.yaml", yaml_content)
    _add_group_rp_scene_validation(validation, graph, service)
    return GroupRPScenePreview(
        world_id=world_id,
        graph=graph,
        yaml_content=yaml_content,
        validation=validation,
        safe_prompt_preview={template.id: _safe_prompt_preview(template, service, world_id) for template in graph.templates},
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_group_rp_scene_authoring(
    world_id: str,
    graph: GroupRPSceneAuthoring,
    service: ContentAuthoringService,
) -> GroupRPScenePreview:
    return preview_group_rp_scene_authoring(world_id, graph, service)


def save_group_rp_scene_authoring(
    world_id: str,
    graph: GroupRPSceneAuthoring,
    service: ContentAuthoringService,
    *,
    confirm_warnings: bool = False,
) -> GroupRPSceneSaveResponse:
    preview = preview_group_rp_scene_authoring(world_id, graph, service)
    if not preview.validation.ok or (preview.validation.warnings and not confirm_warnings):
        return GroupRPSceneSaveResponse(**preview.model_dump(), saved=False)
    validation = service.write_file(world_id, "group_rp_scenes.yaml", preview.yaml_content, confirm_warnings=confirm_warnings)
    return GroupRPSceneSaveResponse(
        world_id=world_id,
        graph=graph,
        yaml_content=preview.yaml_content,
        validation=validation,
        safe_prompt_preview=preview.safe_prompt_preview,
        confirmation_required=validation.ok and bool(validation.warnings) and not confirm_warnings,
        saved=validation.ok,
    )


def _add_group_rp_scene_validation(
    validation: ValidationReport,
    graph: GroupRPSceneAuthoring,
    service: ContentAuthoringService,
) -> None:
    npc_data = {str(item.get("id", "")): item for item in _read_list_file(service, graph.world_id, "npcs.yaml", "npcs")}
    locations = {str(item.get("id", "")) for item in _read_list_file(service, graph.world_id, "locations.yaml", "locations")}
    moods = {str(item.get("id", "")) for item in _read_list_file(service, graph.world_id, "scene_moods.yaml", "scene_mood_presets", required=False)}
    hidden_terms = _hidden_topic_terms(service, graph.world_id)
    seen: set[str] = set()
    for template in graph.templates:
        if template.id in seen:
            validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}", "Duplicate group RP scene template id.", code="group_rp_scene_duplicate_id", ref_id=template.id)
        seen.add(template.id)
        if template.location_id not in locations:
            validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.location_id", "Group RP scene location does not exist.", code="group_rp_scene_missing_location", ref_id=template.location_id)
        if template.scene_mood and template.scene_mood not in moods:
            validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.scene_mood", "Scene mood preset does not exist.", code="group_rp_scene_missing_mood", ref_id=template.scene_mood)
        for npc_id in template.participant_ids:
            npc = npc_data.get(npc_id)
            if npc is None:
                validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.participant_ids", "Group RP participant does not exist.", code="group_rp_scene_missing_participant", ref_id=npc_id)
                continue
            if _is_dead_or_incapacitated(npc) and not template.allow_dead_participants:
                validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.participant_ids", "Dead or incapacitated participants require explicit allow_dead_participants.", code="group_rp_scene_dead_participant_not_allowed", ref_id=npc_id)
        participant_set = set(template.participant_ids)
        for role in template.required_roles:
            if role.required and role.npc_id not in participant_set:
                validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.required_roles", "Required role NPC is not in participant_ids.", code="group_rp_scene_required_role_unsatisfied", ref_id=role.npc_id)
        if template.turn_order_policy not in set(TurnOrderPolicy):
            validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.turn_order_policy", "Invalid turn order policy.", code="group_rp_scene_invalid_turn_order_policy", ref_id=str(template.turn_order_policy))
        opening = template.opening_public_context.lower()
        for term in hidden_terms:
            if term and term.lower() in opening:
                validation.add(ValidationSeverity.ERROR, f"group_rp_scenes.{template.id}.opening_public_context", "Hidden fact appears in opening public context.", code="group_rp_scene_hidden_fact_in_opening", ref_id=template.id)
                break


def _safe_prompt_preview(template: GroupRPSceneTemplate, service: ContentAuthoringService, world_id: str) -> str:
    hidden_terms = _hidden_topic_terms(service, world_id)
    opening = template.opening_public_context
    for term in sorted(hidden_terms | set(template.forbidden_topics), key=len, reverse=True):
        if term:
            opening = opening.replace(term, "[filtered-topic]")
    topics = [topic for topic in template.allowed_topics if topic not in set(template.forbidden_topics) and topic not in hidden_terms]
    return (
        f"group_scene={template.id}; type={template.scene_type.value}; participants={len(template.participant_ids)}; "
        f"turn_order={template.turn_order_policy.value}; speaker={template.speaker_selection_policy.value}; "
        f"mood={template.scene_mood or 'default'}; tension={template.starting_tension}; "
        f"topics={','.join(topics)}; opening={opening}"
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
            raise GroupRPSceneAuthoringError(str(exc)) from exc
        return []
    data = yaml.safe_load(content) or {}
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _hidden_topic_terms(service: ContentAuthoringService, world_id: str) -> set[str]:
    terms: set[str] = set()
    for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False):
        if str(fact.get("visibility", "")) != "public":
            terms.add(str(fact.get("id", "")))
            text = str(fact.get("text", ""))
            if text:
                terms.add(text)
    return terms


def _is_dead_or_incapacitated(npc: dict[str, Any]) -> bool:
    condition = str(npc.get("condition", "")).lower()
    status_effects = {str(item).lower() for item in npc.get("status_effects", []) if isinstance(item, str)}
    return npc.get("alive") is False or condition in {"dead", "incapacitated"} or bool(status_effects & {"dead", "incapacitated"})
