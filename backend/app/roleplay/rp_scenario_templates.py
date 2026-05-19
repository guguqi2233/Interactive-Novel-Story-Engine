from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.core.world_state import GameState
from app.roleplay.dialogue import DialogueMode, DialogueSession, GroupDialogueScene


class RPScenarioTemplateError(ValueError):
    """Raised when an RP scenario template is invalid or unsafe."""


class RPSceneType(StrEnum):
    FIRST_MEETING = "first_meeting"
    INTERROGATION = "interrogation"
    RECONCILIATION = "reconciliation"
    ARGUMENT = "argument"
    CONFESSION = "confession"
    NEGOTIATION = "negotiation"
    GROUP_MEETING = "group_meeting"
    SECRET_REVEAL = "secret_reveal"


class RPScenarioTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    scene_type: RPSceneType
    required_participants: list[str] = Field(default_factory=list)
    optional_participants: list[str] = Field(default_factory=list)
    suggested_mood: str = "neutral"
    suggested_mood_preset_id: str | None = None
    suggested_dialogue_mode: DialogueMode = DialogueMode.FOCUSED
    opening_context: str = ""
    allowed_topics: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    required_visible_facts: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator(
        "required_participants",
        "optional_participants",
        "allowed_topics",
        "forbidden_topics",
        "required_visible_facts",
        "tags",
    )
    @classmethod
    def validate_safe_terms(cls, values: list[str]) -> list[str]:
        for value in values:
            if _looks_like_path_traversal(value):
                raise ValueError(f"Unsafe RP scenario template value: {value}")
        return values

    @model_validator(mode="after")
    def validate_participants(self) -> "RPScenarioTemplate":
        if not self.required_participants:
            raise ValueError("RP scenario template requires at least one participant")
        overlap = set(self.required_participants) & set(self.optional_participants)
        if overlap:
            raise ValueError(f"Participant cannot be both required and optional: {sorted(overlap)}")
        return self


class RPScenarioDraft(BaseModel):
    draft_id: str
    template_id: str
    scene_type: RPSceneType
    participant_ids: list[str] = Field(default_factory=list)
    focus_npc_id: str | None = None
    dialogue_mode: DialogueMode
    scene_mood: str = "neutral"
    scene_mood_preset_id: str | None = None
    active_topics: list[str] = Field(default_factory=list)
    opening_context_summary: str = ""
    dialogue_session_draft: DialogueSession | None = None
    group_scene_draft: GroupDialogueScene | None = None


class RPScenarioTemplatePreview(BaseModel):
    template: RPScenarioTemplate
    draft: RPScenarioDraft
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    writes_to_disk: bool = False
    modifies_game_state: bool = False
    requires_confirmation: bool = True
    applied: bool = False


class RPScenarioTemplateRenderer:
    DISALLOWED_TEMPLATE_SUFFIXES = {
        ".bat",
        ".cmd",
        ".com",
        ".dll",
        ".exe",
        ".js",
        ".mjs",
        ".ps1",
        ".psm1",
        ".py",
        ".sh",
        ".vbs",
        ".jar",
        ".msi",
    }

    def __init__(self, templates_root: str | Path = "templates/rp") -> None:
        self.templates_root = Path(templates_root)

    def list_templates(self) -> list[RPScenarioTemplate]:
        if not self.templates_root.exists():
            return []
        self._assert_templates_root_safe()
        return [self._load_template(path) for path in sorted(self.templates_root.glob("*.yaml"), key=lambda item: item.name)]

    def get_template(self, template_id: str) -> RPScenarioTemplate:
        self._assert_templates_root_safe()
        if not _is_safe_id(template_id):
            raise RPScenarioTemplateError(f"Invalid RP scenario template id: {template_id}")
        path = (self.templates_root / f"{template_id}.yaml").resolve()
        root = self.templates_root.resolve()
        if root != path.parent:
            raise RPScenarioTemplateError("RP scenario template path escapes templates root")
        if not path.exists():
            raise RPScenarioTemplateError(f"RP scenario template not found: {template_id}")
        return self._load_template(path)

    def preview_template(
        self,
        template_id: str,
        *,
        participant_ids: list[str] | None = None,
        game_session_id: str | None = None,
        state: GameState | None = None,
    ) -> RPScenarioTemplatePreview:
        template = self.get_template(template_id)
        warnings, errors = self._validate_template_for_state(template, participant_ids or [], state)
        draft = self._build_draft(template, participant_ids or [], game_session_id, state)
        return RPScenarioTemplatePreview(template=template, draft=draft, warnings=warnings, errors=errors)

    def apply_template(
        self,
        template_id: str,
        *,
        participant_ids: list[str] | None = None,
        game_session_id: str | None = None,
        state: GameState | None = None,
        confirm_apply: bool = False,
    ) -> RPScenarioTemplatePreview:
        if not confirm_apply:
            raise RPScenarioTemplateError("RP scenario template apply requires explicit confirmation")
        preview = self.preview_template(
            template_id,
            participant_ids=participant_ids,
            game_session_id=game_session_id,
            state=state,
        )
        if preview.errors:
            raise RPScenarioTemplateError("; ".join(preview.errors))
        preview.applied = True
        return preview

    def _build_draft(
        self,
        template: RPScenarioTemplate,
        participant_ids: list[str],
        game_session_id: str | None,
        state: GameState | None,
    ) -> RPScenarioDraft:
        participants = self._resolve_participants(template, participant_ids)
        safe_topics = [topic for topic in template.allowed_topics if topic not in set(template.forbidden_topics)]
        draft = RPScenarioDraft(
            draft_id=str(uuid4()),
            template_id=template.id,
            scene_type=template.scene_type,
            participant_ids=participants,
            focus_npc_id=participants[0] if participants else None,
            dialogue_mode=template.suggested_dialogue_mode,
            scene_mood=template.suggested_mood,
            scene_mood_preset_id=template.suggested_mood_preset_id,
            active_topics=safe_topics,
            opening_context_summary=_safe_opening_context(template),
        )
        if len(participants) >= 2:
            draft.group_scene_draft = GroupDialogueScene(
                scene_id=f"draft-{uuid4()}",
                game_session_id=game_session_id,
                participant_ids=participants,
                location_id=state.player.location_id if state else "",
                active_speaker_id=participants[0],
                turn_order=participants,
                scene_topic=", ".join(safe_topics[:3]),
                scene_mood=template.suggested_mood,
                scene_mood_preset_id=template.suggested_mood_preset_id,
                status="paused",
            )
        else:
            draft.dialogue_session_draft = DialogueSession(
                session_id=f"draft-{uuid4()}",
                game_session_id=game_session_id,
                participant_ids=["player", participants[0]],
                focus_npc_id=participants[0],
                started_turn=state.turn if state else 0,
                last_turn=state.turn if state else 0,
                dialogue_mode=template.suggested_dialogue_mode,
                active_topics=safe_topics,
                scene_mood_preset_id=template.suggested_mood_preset_id,
                safe_context_summary="RP scenario draft; start through DialogueManager to enter play.",
                status="paused",
            )
        return draft

    def _validate_template_for_state(
        self,
        template: RPScenarioTemplate,
        participant_ids: list[str],
        state: GameState | None,
    ) -> tuple[list[str], list[str]]:
        warnings: list[str] = []
        errors: list[str] = []
        participants = self._resolve_participants(template, participant_ids)
        missing = [npc_id for npc_id in template.required_participants if npc_id not in participants]
        if missing:
            errors.append(f"Missing required participants: {', '.join(missing)}")
        if not participants:
            errors.append("RP scenario draft requires at least one participant")
        if any(topic in template.allowed_topics for topic in template.forbidden_topics):
            warnings.append("Forbidden topics were removed from the safe draft topics")
        if state is not None:
            visible_npcs = {
                npc_id
                for npc_id, npc in state.npcs.items()
                if npc.location_id == state.player.location_id and npc.visible and not npc.hidden
            }
            hidden_participants = [npc_id for npc_id in participants if npc_id not in visible_npcs]
            if hidden_participants:
                errors.append(f"Participants are not player-visible: {', '.join(hidden_participants)}")
            known_facts = set(state.player_visible_facts)
            missing_facts = [fact_id for fact_id in template.required_visible_facts if fact_id not in known_facts]
            if missing_facts:
                errors.append(f"Required visible facts are not known: {', '.join(missing_facts)}")
        elif template.required_visible_facts:
            warnings.append("Required visible facts cannot be verified without a game session")
        return warnings, errors

    def _resolve_participants(self, template: RPScenarioTemplate, participant_ids: list[str]) -> list[str]:
        if participant_ids:
            return _dedupe(participant_ids)
        return _dedupe(template.required_participants + template.optional_participants)

    def _load_template(self, path: Path) -> RPScenarioTemplate:
        root = self.templates_root.resolve()
        resolved = path.resolve()
        if root != resolved.parent:
            raise RPScenarioTemplateError("RP scenario template path escapes templates root")
        if resolved.suffix.lower() != ".yaml":
            raise RPScenarioTemplateError(f"RP scenario templates must be YAML: {resolved.name}")
        try:
            data = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RPScenarioTemplateError(f"Invalid RP scenario template YAML: {resolved.name}: {exc}") from exc
        if not isinstance(data, dict):
            raise RPScenarioTemplateError(f"Expected RP scenario template mapping: {resolved.name}")
        try:
            return RPScenarioTemplate.model_validate(data)
        except ValidationError as exc:
            raise RPScenarioTemplateError(f"RP scenario template schema validation failed: {resolved.name}: {exc}") from exc

    def _assert_templates_root_safe(self) -> None:
        if not self.templates_root.exists():
            return
        root = self.templates_root.resolve()
        for path in self.templates_root.rglob("*"):
            resolved = path.resolve()
            if root != resolved and root not in resolved.parents:
                raise RPScenarioTemplateError("RP scenario template path escapes templates root")
            if path.is_file() and path.suffix.lower() in self.DISALLOWED_TEMPLATE_SUFFIXES:
                raise RPScenarioTemplateError(f"Executable files are not allowed in RP scenario templates: {path.name}")


def _safe_opening_context(template: RPScenarioTemplate) -> str:
    context = template.opening_context
    for forbidden in template.forbidden_topics:
        context = context.replace(forbidden, "[filtered-topic]")
    return context


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _looks_like_path_traversal(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return "../" in normalized or normalized.startswith("/") or normalized.startswith("~")
