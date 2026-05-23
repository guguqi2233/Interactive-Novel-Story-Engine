from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.world_state import GameState, NPCState
from app.llm.provider_base import LLMProvider, Message
from app.platform.narrative_project import validate_project_relative_path
from app.platform.project_repository import ProjectRepository
from app.platform.rp_mature import CrossModeRPSafetyMetadata, MatureExportFilter, MatureExportPolicy, run_rp_mature_quality_gate
from app.platform.security import contains_secret_text, redact_text
from app.platform.shared_libraries import (
    CharacterLibrary,
    CharacterProfile,
    CrossModeLink,
    CrossModeLinkRegistry,
    LoreFactLibrary,
    ProjectMemoryLibrary,
    ProjectPromptProfile,
    PromptProfileLibrary,
    WorldBible,
    WorldBibleEntryType,
)


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_id(value: str, field: str = "id") -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError(f"Unsafe {field}")
    return value


def _contains_forbidden_permission(text: str) -> bool:
    lowered = text.lower()
    forbidden = {
        "can_access_hidden_facts",
        "can_modify_state",
        "can_override_action_result",
        "can_bypass_visibility",
        "state_delta",
        "raw gamestate",
        "modify gamestate",
        "override action result",
    }
    return any(term in lowered for term in forbidden)


def _redacted_list(values: Iterable[str]) -> list[str]:
    return [redact_text(value) for value in values if value]


def _contains_key_like_text(text: str) -> bool:
    return bool(re.search(r"\bsk-[A-Za-z0-9_-]{8,}\b", text))


class TavernModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TavernSessionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TavernSpeakerType(StrEnum):
    USER = "user"
    CHARACTER = "character"
    NARRATOR = "narrator"
    SYSTEM = "system"


class TavernVisibility(StrEnum):
    TAVERN_SAFE = "tavern_safe"
    MATURE_ONLY = "mature_only"
    AUTHORING_ONLY = "authoring_only"
    HIDDEN = "hidden"
    DEBUG_ONLY = "debug_only"


class TavernProjectSection(TavernModel):
    characters_path: str = "tavern/characters"
    sessions_path: str = "tavern/sessions"
    messages_path: str = "tavern/messages"
    lorebooks_path: str = "tavern/lorebooks"
    scene_presets_path: str = "tavern/scene_presets"
    memory_path: str = "tavern/memory"
    proposals_path: str = "tavern/proposals"
    linked_character_library: str | None = None
    linked_memory_library: str | None = None
    default_prompt_profile_id: str | None = None
    default_provider_profile_id: str | None = None

    @field_validator("characters_path", "sessions_path", "messages_path", "lorebooks_path", "scene_presets_path", "memory_path", "proposals_path")
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return validate_project_relative_path(value)


class TavernPreferences(TavernModel):
    project_id: str
    default_character_id: str | None = None
    default_session_id: str | None = None
    default_prompt_profile_id: str | None = None
    default_provider_profile_id: str | None = None
    show_rp_memory_panel: bool = True
    show_emotion_panel: bool = True
    show_relationship_tone_panel: bool = True
    default_scene_mood_preset_id: str | None = None
    mature_module_visible: bool = False
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_safe_preferences(self) -> "TavernPreferences":
        payload = self.model_dump_json()
        lowered = payload.lower()
        if contains_secret_text(payload) or _contains_key_like_text(payload) or any(
            token in lowered for token in ("hidden fact", "npc secret", "mature_only", "private persona", "state_delta", "raw prompt")
        ):
            raise ValueError("TavernPreferences contain forbidden content")
        return self


class TavernSessionRecoveryRecord(TavernModel):
    record_id: str
    project_id: str
    target_type: Literal["message", "session_settings", "multi_npc_scene"] = "message"
    target_id: str
    safe_draft_text: str = ""
    safe_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_safe_recovery(self) -> "TavernSessionRecoveryRecord":
        payload = self.model_dump_json()
        lowered = payload.lower()
        if contains_secret_text(payload) or _contains_key_like_text(payload) or any(
            token in lowered for token in ("hidden fact", "npc secret", "mature_only", "private persona", "raw prompt", "debug memory", "state_delta")
        ):
            raise ValueError("Tavern recovery record contains forbidden content")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "project_id": self.project_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "safe_draft_text": redact_text(self.safe_draft_text),
            "safe_metadata": _redact_obj(self.safe_metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TavernSessionExportRequest(TavernModel):
    scope: Literal["current_session", "selected_sessions", "all_sessions"] = "current_session"
    session_ids: list[str] = Field(default_factory=list)
    format: Literal["json_safe", "markdown_transcript"] = "json_safe"
    include_mature_private: bool = False
    include_debug: bool = False
    explicit_confirm: bool = False


class TavernSessionExportPreview(TavernModel):
    project_id: str
    dry_run: bool = True
    format: Literal["json_safe", "markdown_transcript"] = "json_safe"
    session_count: int = 0
    message_count: int = 0
    safe_sample_summaries: list[str] = Field(default_factory=list)
    excluded_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    filtering_policy: list[str] = Field(default_factory=list)


class TavernSessionExportResult(TavernSessionExportPreview):
    dry_run: bool = False
    exported: bool = False
    export_id: str = ""
    content_preview: str = ""


class RPSafetyDashboardIssue(TavernModel):
    severity: Literal["info", "warning", "error", "blocker"] = "warning"
    category: str
    safe_summary: str
    affected_session_id: str | None = None
    affected_character_id: str | None = None
    suggested_action: str = "Review local RP safety settings."


class RPSafetyDashboardReport(TavernModel):
    project_id: str
    overall_status: Literal["pass", "warning", "fail", "not_run"] = "not_run"
    blocker_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    categories: dict[str, Literal["pass", "warning", "fail", "not_run"]] = Field(default_factory=dict)
    issues: list[RPSafetyDashboardIssue] = Field(default_factory=list)


class TavernSceneContext(TavernModel):
    location_ref: str | None = None
    scene_title: str = ""
    scene_summary: str = ""
    mood_tags: list[str] = Field(default_factory=list)
    scene_mood_preset_id: str | None = None
    relationship_tone_id: str | None = None
    authoring_notes: str = ""

    def safe_summary(self) -> dict[str, Any]:
        return {
            "location_ref": self.location_ref,
            "scene_title": redact_text(self.scene_title),
            "scene_summary": redact_text(self.scene_summary),
            "mood_tags": list(self.mood_tags),
            "scene_mood_preset_id": self.scene_mood_preset_id,
            "relationship_tone_id": self.relationship_tone_id,
        }


class TavernCharacter(TavernModel):
    tavern_character_id: str
    project_id: str
    display_name: str
    description: str = ""
    linked_character_profile_id: str | None = None
    linked_world_npc_id: str | None = None
    rp_profile_id: str | None = None
    voice_profile_id: str | None = None
    default_prompt_profile_id: str | None = None
    lorebook_refs: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @field_validator("tavern_character_id", "project_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        return _safe_id(value)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "tavern_character_id": self.tavern_character_id,
            "project_id": self.project_id,
            "display_name": redact_text(self.display_name),
            "description": redact_text(self.description),
            "linked_character_profile_id": self.linked_character_profile_id,
            "linked_world_npc_id": self.linked_world_npc_id,
            "rp_profile_id": self.rp_profile_id,
            "voice_profile_id": self.voice_profile_id,
            "default_prompt_profile_id": self.default_prompt_profile_id,
            "lorebook_refs": list(self.lorebook_refs),
            "safety_flags": list(self.safety_flags),
        }


class TavernMessage(TavernModel):
    message_id: str
    session_id: str
    speaker_type: TavernSpeakerType
    speaker_id: str | None = None
    content: str
    created_at: str = Field(default_factory=now_iso)
    visibility: TavernVisibility = TavernVisibility.TAVERN_SAFE
    source_refs: list[str] = Field(default_factory=list)
    proposed_world_effects: list[str] = Field(default_factory=list)

    @field_validator("message_id", "session_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        return _safe_id(value)

    def safe_summary(self) -> dict[str, Any] | None:
        if self.visibility != TavernVisibility.TAVERN_SAFE:
            return None
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "speaker_type": self.speaker_type.value,
            "speaker_id": self.speaker_id,
            "content": redact_text(self.content),
            "created_at": self.created_at,
            "source_refs": list(self.source_refs),
            "proposed_world_effects": _redacted_list(self.proposed_world_effects),
        }


class TavernSession(TavernModel):
    session_id: str
    project_id: str
    title: str
    character_ids: list[str] = Field(default_factory=list)
    scene_context: TavernSceneContext = Field(default_factory=TavernSceneContext)
    message_refs: list[str] = Field(default_factory=list)
    messages: list[TavernMessage] = Field(default_factory=list)
    multi_character_scene_refs: list[str] = Field(default_factory=list)
    linked_memory_ids: list[str] = Field(default_factory=list)
    linked_world_refs: list[str] = Field(default_factory=list)
    prompt_profile_id: str | None = None
    status: TavernSessionStatus = TavernSessionStatus.DRAFT
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @field_validator("session_id", "project_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        return _safe_id(value)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "title": redact_text(self.title),
            "character_ids": list(self.character_ids),
            "scene_context": self.scene_context.safe_summary(),
            "message_count": len(self.message_refs) + len(self.messages),
            "linked_memory_ids": list(self.linked_memory_ids),
            "linked_world_refs": list(self.linked_world_refs),
            "prompt_profile_id": self.prompt_profile_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ImportedCharacterCard(TavernModel):
    name: str
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_message: str = ""
    example_dialogue: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    creator_notes: str = ""
    system_prompt_like_text: str = ""
    lorebook_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_no_secret(self) -> "ImportedCharacterCard":
        if contains_secret_text(self.model_dump_json()):
            raise ValueError("Character card must not contain API keys or secrets")
        return self


class TavernRPProfile(TavernModel):
    rp_profile_id: str
    tavern_character_id: str | None = None
    character_id: str | None = None
    public_persona: str = ""
    private_persona_authoring_only: str = ""
    roleplay_rules: list[str] = Field(default_factory=list)
    emotional_baseline: str = ""
    relationship_defaults: dict[str, str] = Field(default_factory=dict)
    taboo_topics: list[str] = Field(default_factory=list)
    consent_boundaries: list[str] = Field(default_factory=lambda: ["safe"])
    safety_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rules(self) -> "TavernRPProfile":
        if any(_contains_forbidden_permission(rule) for rule in self.roleplay_rules):
            raise ValueError("RPProfile rules cannot grant state or hidden-fact permissions")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "rp_profile_id": self.rp_profile_id,
            "tavern_character_id": self.tavern_character_id,
            "character_id": self.character_id,
            "public_persona": redact_text(self.public_persona),
            "roleplay_rules": _redacted_list(self.roleplay_rules),
            "emotional_baseline": redact_text(self.emotional_baseline),
            "relationship_defaults": {key: redact_text(value) for key, value in self.relationship_defaults.items()},
            "taboo_topics": list(self.taboo_topics),
            "consent_boundaries": list(self.consent_boundaries),
            "safety_flags": list(self.safety_flags),
        }


class TavernVoiceProfile(TavernModel):
    voice_profile_id: str
    tone: str = ""
    speech_habits: list[str] = Field(default_factory=list)
    vocabulary_style: str = ""
    sentence_length: Literal["short", "medium", "long", "mixed"] = "mixed"
    catchphrases: list[str] = Field(default_factory=list)
    emotional_markers: list[str] = Field(default_factory=list)
    example_dialogue_refs: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "voice_profile_id": self.voice_profile_id,
            "tone": redact_text(self.tone),
            "speech_habits": _redacted_list(self.speech_habits),
            "vocabulary_style": redact_text(self.vocabulary_style),
            "sentence_length": self.sentence_length,
            "catchphrases": _redacted_list(self.catchphrases),
            "emotional_markers": _redacted_list(self.emotional_markers),
            "example_dialogue_refs": list(self.example_dialogue_refs),
        }


class CharacterCardImportResult(TavernModel):
    tavern_character: TavernCharacter
    character_profile: CharacterProfile | None = None
    rp_profile: TavernRPProfile | None = None
    warnings: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "tavern_character": self.tavern_character.safe_summary(),
            "character_profile": self.character_profile.safe_summary() if self.character_profile else None,
            "rp_profile": self.rp_profile.safe_summary() if self.rp_profile else None,
            "warnings": list(self.warnings),
        }


class CharacterCardImportService:
    def parse_card(self, raw_content: str) -> ImportedCharacterCard:
        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError:
            payload = yaml.safe_load(raw_content)
        if not isinstance(payload, dict):
            raise ValueError("Character card payload must be a JSON/YAML object")
        return ImportedCharacterCard.model_validate(payload)

    def import_card(self, project_id: str, raw_content: str, *, create_character_profile: bool = True, create_rp_profile: bool = True) -> CharacterCardImportResult:
        card = self.parse_card(raw_content)
        character_id = _safe_id(re.sub(r"[^A-Za-z0-9_-]+", "_", card.name.strip().lower()).strip("_") or "tavern_character")
        warnings: list[str] = []
        unsafe_text = f"{card.system_prompt_like_text}\n{card.creator_notes}"
        if _contains_forbidden_permission(unsafe_text):
            warnings.append("Imported prompt-like text requested unsafe permissions and was kept out of prompt-safe fields.")
        tavern_character = TavernCharacter(
            tavern_character_id=character_id,
            project_id=project_id,
            display_name=card.name,
            description=card.description,
            linked_character_profile_id=character_id if create_character_profile else None,
            rp_profile_id=f"rp_{character_id}" if create_rp_profile else None,
            lorebook_refs=card.lorebook_refs,
            safety_flags=warnings,
        )
        profile = CharacterProfile(
            character_id=character_id,
            name=card.name,
            description=card.description,
            public_profile=card.personality,
            private_notes_authoring_only=card.creator_notes,
            role_tags=card.tags,
        ) if create_character_profile else None
        rp_profile = TavernRPProfile(
            rp_profile_id=f"rp_{character_id}",
            tavern_character_id=character_id,
            public_persona=card.personality or card.description,
            private_persona_authoring_only=card.creator_notes,
            roleplay_rules=[],
        ) if create_rp_profile else None
        return CharacterCardImportResult(tavern_character=tavern_character, character_profile=profile, rp_profile=rp_profile, warnings=warnings)


class MultiCharacterSceneStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class MultiCharacterScene(TavernModel):
    scene_id: str
    project_id: str
    session_id: str
    title: str = "Multi-NPC Scene"
    character_ids: list[str] = Field(default_factory=list)
    scene_context: TavernSceneContext = Field(default_factory=TavernSceneContext)
    turn_order: list[str] = Field(default_factory=list)
    active_speaker_id: str | None = None
    status: MultiCharacterSceneStatus = MultiCharacterSceneStatus.DRAFT

    def safe_summary(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "title": self.title,
            "character_ids": list(self.character_ids),
            "participant_ids": list(self.character_ids),
            "scene_context": self.scene_context.safe_summary(),
            "turn_order": list(self.turn_order),
            "active_speaker_id": self.active_speaker_id,
            "current_turn_index": self.turn_order.index(self.active_speaker_id) if self.active_speaker_id in self.turn_order else 0,
            "message_ids": [],
            "safety_notes": [
                "multi_npc_scene_does_not_modify_world_gamestate",
                "hidden_facts_and_npc_secrets_are_filtered",
            ],
            "status": self.status.value,
        }


class TavernMemoryType(StrEnum):
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"
    PROMISE = "promise"
    MOOD = "mood"
    SCENE_CONTEXT = "scene_context"
    SUMMARY = "summary"
    BOUNDARY = "boundary"
    PROPOSAL = "proposal"


class TavernMemoryRecord(TavernModel):
    memory_id: str
    project_id: str
    session_id: str
    character_ids: list[str] = Field(default_factory=list)
    memory_type: TavernMemoryType = TavernMemoryType.SUMMARY
    content: str
    visibility: TavernVisibility = TavernVisibility.TAVERN_SAFE
    linked_message_ids: list[str] = Field(default_factory=list)
    proposed_world_effect_id: str | None = None
    authoritative: Literal[False] = False
    created_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any] | None:
        if self.visibility != TavernVisibility.TAVERN_SAFE:
            return None
        return {
            "memory_id": self.memory_id,
            "session_id": self.session_id,
            "character_ids": list(self.character_ids),
            "memory_type": self.memory_type.value,
            "content": redact_text(self.content),
            "linked_message_ids": list(self.linked_message_ids),
            "authoritative": False,
        }


class TavernMemoryContext(TavernModel):
    memories: list[dict[str, Any]] = Field(default_factory=list)


class TavernMemoryService:
    def __init__(self, records: list[TavernMemoryRecord] | None = None) -> None:
        self.records = records or []

    def add_tavern_memory(self, record: TavernMemoryRecord) -> TavernMemoryRecord:
        self.records.append(record)
        return record

    def list_tavern_memories(self, *, session_id: str | None = None) -> list[TavernMemoryRecord]:
        return [record for record in self.records if session_id is None or record.session_id == session_id]

    def search_tavern_memories(self, *, character_id: str | None = None) -> list[TavernMemoryRecord]:
        return [record for record in self.records if character_id is None or character_id in record.character_ids]

    def build_tavern_memory_context(self, *, session_id: str | None = None, character_id: str | None = None) -> TavernMemoryContext:
        records = self.list_tavern_memories(session_id=session_id)
        if character_id:
            records = [record for record in records if character_id in record.character_ids]
        summaries = [summary for record in records if (summary := record.safe_summary()) is not None]
        return TavernMemoryContext(memories=summaries)


class TavernLorebookEntry(TavernModel):
    lorebook_entry_id: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    trigger_keywords: list[str] = Field(default_factory=list)
    visibility: Literal["public", "tavern_safe", "authoring_only", "hidden", "debug_only"] = "tavern_safe"
    linked_fact_ids: list[str] = Field(default_factory=list)
    safe_for_tavern: bool = True
    character_scope: list[str] | None = None

    def safe_entry(self) -> dict[str, Any] | None:
        if not self.safe_for_tavern or self.visibility not in {"public", "tavern_safe"}:
            return None
        return {"id": self.lorebook_entry_id, "title": redact_text(self.title), "content": redact_text(self.content), "tags": list(self.tags)}


class TavernLoreContext(TavernModel):
    safe_lore_entries: list[dict[str, Any]] = Field(default_factory=list)
    tavern_safe_memory: list[dict[str, Any]] = Field(default_factory=list)
    excluded_entries_debug: list[dict[str, str]] = Field(default_factory=list)


class TavernLoreContextBuilder:
    def __init__(
        self,
        *,
        lorebook_entries: list[TavernLorebookEntry] | None = None,
        world_bible: WorldBible | None = None,
        lore_facts: LoreFactLibrary | None = None,
        memory_context: TavernMemoryContext | None = None,
        npc_known_fact_ids: set[str] | None = None,
    ) -> None:
        self.lorebook_entries = lorebook_entries or []
        self.world_bible = world_bible
        self.lore_facts = lore_facts
        self.memory_context = memory_context or TavernMemoryContext()
        self.npc_known_fact_ids = npc_known_fact_ids or set()

    def build(self, *, project_id: str, session_id: str, character_id: str, recent_user_message: str, scene_context: TavernSceneContext) -> TavernLoreContext:
        del project_id, session_id
        search_text = f"{recent_user_message} {scene_context.scene_title} {scene_context.scene_summary} {' '.join(scene_context.mood_tags)}".lower()
        safe: list[dict[str, Any]] = []
        excluded: list[dict[str, str]] = []
        for entry in self.lorebook_entries:
            if entry.character_scope and character_id not in entry.character_scope:
                excluded.append({"id": entry.lorebook_entry_id, "reason": "character_scope"})
                continue
            if entry.trigger_keywords and not any(keyword.lower() in search_text for keyword in entry.trigger_keywords):
                continue
            if any(fid not in self.npc_known_fact_ids for fid in entry.linked_fact_ids):
                excluded.append({"id": entry.lorebook_entry_id, "reason": "npc_unknown_fact"})
                continue
            summary = entry.safe_entry()
            if summary is None:
                excluded.append({"id": entry.lorebook_entry_id, "reason": "not_tavern_safe"})
                continue
            safe.append(summary)
        if self.world_bible:
            for entry in self.world_bible.entries.values():
                if entry.entry_type in {WorldBibleEntryType.HIDDEN, WorldBibleEntryType.AUTHORING_NOTE} or entry.visibility in {"hidden", "authoring_only", "debug_only"}:
                    excluded.append({"id": entry.id, "reason": "world_bible_hidden_or_authoring"})
                    continue
                if entry.entry_type in {WorldBibleEntryType.FLAVOR, WorldBibleEntryType.STYLE_NOTE}:
                    safe.append({"id": entry.id, "title": redact_text(entry.title), "content": redact_text(entry.content), "tags": list(entry.tags)})
        if self.lore_facts:
            for entry in self.lore_facts.get_tavern_safe_lore():
                if entry.linked_world_fact_id and entry.linked_world_fact_id not in self.npc_known_fact_ids:
                    excluded.append({"id": entry.id, "reason": "npc_unknown_fact"})
                    continue
                safe.append({"id": entry.id, "title": redact_text(entry.title), "content": redact_text(entry.text), "tags": list(entry.tags)})
        return TavernLoreContext(safe_lore_entries=safe, tavern_safe_memory=list(self.memory_context.memories), excluded_entries_debug=excluded)


class SceneMoodPreset(TavernModel):
    preset_id: str
    name: str
    description: str = ""
    mood_tags: list[str] = Field(default_factory=list)
    narration_style: str = ""
    pacing: str = "steady"
    sensory_focus: list[str] = Field(default_factory=list)
    emotional_tone: str = "neutral"
    max_intensity: int = Field(default=50, ge=0, le=100)
    safety_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_style_only(self) -> "SceneMoodPreset":
        if _contains_forbidden_permission(self.model_dump_json()):
            raise ValueError("SceneMoodPreset cannot grant state, action, or hidden-fact permissions")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "name": redact_text(self.name),
            "description": redact_text(self.description),
            "mood_tags": list(self.mood_tags),
            "narration_style": redact_text(self.narration_style),
            "pacing": redact_text(self.pacing),
            "sensory_focus": _redacted_list(self.sensory_focus),
            "emotional_tone": redact_text(self.emotional_tone),
            "max_intensity": self.max_intensity,
            "safety_flags": list(self.safety_flags),
        }


ToneBand = Literal["very_low", "low", "neutral", "high", "very_high"]


class RelationshipTone(TavernModel):
    tone_id: str
    character_a_id: str
    character_b_id: str
    trust_band: ToneBand = "neutral"
    affinity_band: ToneBand = "neutral"
    fear_band: ToneBand = "neutral"
    tension_band: ToneBand = "neutral"
    intimacy_band: ToneBand | None = None
    respect_band: ToneBand = "neutral"
    tone_notes_authoring_only: str = ""
    tavern_safe_summary: str = ""

    def safe_summary(self) -> dict[str, Any]:
        return {
            "tone_id": self.tone_id,
            "character_a_id": self.character_a_id,
            "character_b_id": self.character_b_id,
            "trust_band": self.trust_band,
            "affinity_band": self.affinity_band,
            "fear_band": self.fear_band,
            "tension_band": self.tension_band,
            "intimacy_band": self.intimacy_band,
            "respect_band": self.respect_band,
            "tavern_safe_summary": redact_text(self.tavern_safe_summary),
        }


class RelationshipToneChangeProposal(TavernModel):
    proposal_id: str
    tone_id: str
    requested_change: dict[str, str] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    modifies_world_state: Literal[False] = False


class RelationshipToneService:
    def derive_tone_from_tavern_memory(self, memories: list[TavernMemoryRecord], character_a_id: str, character_b_id: str) -> RelationshipTone:
        content = " ".join(record.content.lower() for record in memories if record.visibility == TavernVisibility.TAVERN_SAFE)
        trust: ToneBand = "high" if "trust" in content or "promise" in content else "neutral"
        tension: ToneBand = "high" if "conflict" in content or "boundary" in content else "neutral"
        return RelationshipTone(tone_id=f"tone_{character_a_id}_{character_b_id}", character_a_id=character_a_id, character_b_id=character_b_id, trust_band=trust, tension_band=tension, tavern_safe_summary="Tavern-only relationship tone.")

    def derive_tone_from_world_relationship_safe(self, summary: dict[str, Any]) -> RelationshipTone | None:
        if summary.get("hidden_relationship") or summary.get("visibility") == "hidden":
            return None
        trust = _band_from_int(int(summary.get("trust", 0)))
        fear = _band_from_int(int(summary.get("fear", 0)))
        affinity = _band_from_int(int(summary.get("affinity", 0)))
        return RelationshipTone(tone_id=str(summary.get("id", "world_tone")), character_a_id=str(summary.get("source_id", "a")), character_b_id=str(summary.get("target_id", "b")), trust_band=trust, fear_band=fear, affinity_band=affinity, tavern_safe_summary="Derived from safe world relationship summary.")

    def build_relationship_tone_context(self, tone: RelationshipTone) -> dict[str, Any]:
        return tone.safe_summary()

    def propose_tone_change(self, tone: RelationshipTone, requested_change: dict[str, str], source_refs: list[str] | None = None) -> RelationshipToneChangeProposal:
        return RelationshipToneChangeProposal(proposal_id=f"proposal_{tone.tone_id}_{now_iso().replace(':', '').replace('-', '')}", tone_id=tone.tone_id, requested_change=requested_change, source_refs=source_refs or [])


def _band_from_int(value: int) -> ToneBand:
    if value <= -50:
        return "very_low"
    if value < 0:
        return "low"
    if value >= 75:
        return "very_high"
    if value > 25:
        return "high"
    return "neutral"


class TavernPromptContext(TavernModel):
    project_id: str
    session_id: str
    character_id: str
    prompt_profile_id: str | None = None
    current_speaker_safe_profile: dict[str, Any] = Field(default_factory=dict)
    rp_profile_safe_summary: dict[str, Any] = Field(default_factory=dict)
    voice_profile_safe_summary: dict[str, Any] = Field(default_factory=dict)
    scene_mood_safe_summary: dict[str, Any] = Field(default_factory=dict)
    relationship_tone_safe_summary: dict[str, Any] = Field(default_factory=dict)
    recent_safe_messages: list[dict[str, Any]] = Field(default_factory=list)
    tavern_safe_memory: list[dict[str, Any]] = Field(default_factory=list)
    safe_lorebook_entries: list[dict[str, Any]] = Field(default_factory=list)
    style_instructions: str = ""
    safety_notes: list[str] = Field(default_factory=list)
    source_context_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_safe_context(self) -> "TavernPromptContext":
        payload = self.model_dump_json().lower()
        if contains_secret_text(payload) or "state_delta" in payload or "hidden fact" in payload or "private_persona" in payload:
            raise ValueError("TavernPromptContext contains unsafe prompt material")
        return self


class TavernPromptContextBuilder:
    def __init__(self, prompt_profiles: PromptProfileLibrary | None = None) -> None:
        self.prompt_profiles = prompt_profiles

    def select_profile(self, *profile_ids: str | None) -> ProjectPromptProfile | None:
        if self.prompt_profiles is None:
            return None
        for profile_id in profile_ids:
            if not profile_id:
                continue
            profile = self.prompt_profiles.profiles.get(profile_id)
            if profile is None:
                raise ValueError(f"Prompt profile not found: {profile_id}")
            if "tavern" not in profile.mode_scopes:
                raise ValueError("Prompt profile is not scoped for tavern")
            return profile
        return None

    def build(
        self,
        *,
        session: TavernSession,
        character: TavernCharacter,
        project_section: TavernProjectSection | None = None,
        rp_profile: TavernRPProfile | None = None,
        voice_profile: TavernVoiceProfile | None = None,
        scene_mood: SceneMoodPreset | None = None,
        relationship_tone: RelationshipTone | None = None,
        lore_context: TavernLoreContext | None = None,
    ) -> TavernPromptContext:
        profile = self.select_profile(session.prompt_profile_id, character.default_prompt_profile_id, project_section.default_prompt_profile_id if project_section else None)
        messages = [summary for message in session.messages if (summary := message.safe_summary()) is not None]
        lore = lore_context or TavernLoreContext()
        return TavernPromptContext(
            project_id=session.project_id,
            session_id=session.session_id,
            character_id=character.tavern_character_id,
            prompt_profile_id=profile.profile_id if profile else None,
            current_speaker_safe_profile=character.safe_summary(),
            rp_profile_safe_summary=rp_profile.safe_summary() if rp_profile else {},
            voice_profile_safe_summary=voice_profile.safe_summary() if voice_profile else {},
            scene_mood_safe_summary=scene_mood.safe_summary() if scene_mood else {},
            relationship_tone_safe_summary=relationship_tone.safe_summary() if relationship_tone else {},
            recent_safe_messages=messages[-12:],
            tavern_safe_memory=lore.tavern_safe_memory,
            safe_lorebook_entries=lore.safe_lore_entries,
            style_instructions=redact_text(profile.rp_style if profile else ""),
            safety_notes=["Tavern context is style-only and non-authoritative."],
            source_context_refs=[f"session:{session.session_id}", f"character:{character.tavern_character_id}"],
        )


class GeneratedTavernReply(TavernModel):
    content: str
    speaker_id: str
    used_prompt_profile_id: str | None = None
    source_context_refs: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    proposed_world_effects: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_safe_output(self) -> "GeneratedTavernReply":
        payload = self.model_dump_json().lower()
        if contains_secret_text(payload) or "state_delta" in payload or "hidden fact" in payload:
            raise ValueError("Generated Tavern reply contains forbidden material")
        return self


class TavernResponseGenerationService:
    def __init__(self, provider: LLMProvider, repository: "TavernRepository | None" = None) -> None:
        self.provider = provider
        self.repository = repository

    def generate_character_reply(self, context: TavernPromptContext) -> GeneratedTavernReply:
        return self._generate("Generate a safe Tavern RP character reply.", context)

    def regenerate_last_reply(self, context: TavernPromptContext, last_message_id: str, *, explicit_confirm: bool = False) -> GeneratedTavernReply:
        if not explicit_confirm:
            raise ValueError("explicit_confirm is required to regenerate an existing reply")
        return self._generate(f"Regenerate reply for message {last_message_id}.", context)

    def summarize_session_for_tavern_memory(self, context: TavernPromptContext) -> GeneratedTavernReply:
        return self._generate("Summarize this Tavern session as non-authoritative RP memory.", context)

    def _generate(self, instruction: str, context: TavernPromptContext) -> GeneratedTavernReply:
        payload = context.model_dump_json()
        if contains_secret_text(payload) or "hidden fact" in payload.lower() or "state_delta" in payload.lower():
            raise ValueError("TavernPromptContext contains unsafe generation input")
        return self.provider.generate_json(
            [
                Message(role="system", content="You write Tavern RP replies only. Do not create world facts, StateDeltas, or GameState changes."),
                Message(role="user", content=f"{instruction}\nContext:\n{payload}"),
            ],
            GeneratedTavernReply,
        )


class TavernChatResponse(TavernModel):
    message_id: str
    character_id: str
    content: str
    safety_notes: list[str] = Field(default_factory=list)
    proposed_world_effects: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class SingleCharacterChatService:
    def __init__(self, repository: "TavernRepository", generator: TavernResponseGenerationService, context_builder: TavernPromptContextBuilder | None = None) -> None:
        self.repository = repository
        self.generator = generator
        self.context_builder = context_builder or TavernPromptContextBuilder()

    def chat(self, *, project_id: str, session_id: str, user_message: str, character_id: str) -> TavernChatResponse:
        user = self.repository.append_message(TavernMessage(message_id=f"msg_{now_iso().replace(':', '').replace('-', '')}_user", session_id=session_id, speaker_type=TavernSpeakerType.USER, content=user_message))
        del user, project_id
        session = self.repository.load_session(session_id)
        character = self.repository.load_tavern_character(character_id)
        context = self.context_builder.build(session=session, character=character, project_section=TavernProjectSection())
        draft = self.generator.generate_character_reply(context)
        message = self.repository.append_message(TavernMessage(message_id=f"msg_{now_iso().replace(':', '').replace('-', '')}_character", session_id=session_id, speaker_type=TavernSpeakerType.CHARACTER, speaker_id=character_id, content=draft.content, source_refs=draft.source_context_refs, proposed_world_effects=draft.proposed_world_effects))
        return TavernChatResponse(message_id=message.message_id, character_id=character_id, content=redact_text(message.content), safety_notes=draft.safety_notes, proposed_world_effects=_redacted_list(draft.proposed_world_effects), created_at=message.created_at)


class TavernWorldProposalType(StrEnum):
    RELATIONSHIP_CHANGE = "relationship_change"
    FACT_DISCOVERY = "fact_discovery"
    QUEST_HINT = "quest_hint"
    PROMISE_OR_DEAL = "promise_or_deal"
    NPC_MOOD_CHANGE = "npc_mood_change"
    MEMORY_TO_WORLD_FACT_CANDIDATE = "memory_to_world_fact_candidate"
    SCENE_TO_TIMELINE_EVENT_CANDIDATE = "scene_to_timeline_event_candidate"


class TavernWorldProposalStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    READY = "ready"
    REJECTED = "rejected"
    INVALID = "invalid"


class TavernWorldProposal(TavernModel):
    proposal_id: str
    project_id: str
    source_session_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    proposal_type: TavernWorldProposalType
    proposed_content: dict[str, Any] = Field(default_factory=dict)
    target_world_refs: list[str] = Field(default_factory=list)
    validation_status: TavernWorldProposalStatus = TavernWorldProposalStatus.DRAFT
    warnings: list[str] = Field(default_factory=list)
    rp_safety_metadata: CrossModeRPSafetyMetadata | None = None
    created_at: str = Field(default_factory=now_iso)

    def normal_summary(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "project_id": self.project_id,
            "source_session_id": self.source_session_id,
            "source_message_ids": list(self.source_message_ids),
            "proposal_type": self.proposal_type.value,
            "proposed_content": _redact_obj(self.proposed_content),
            "target_world_refs": list(self.target_world_refs),
            "validation_status": self.validation_status.value,
            "warnings": _redacted_list(self.warnings),
            "rp_safety_metadata": self.rp_safety_metadata.safe_summary() if self.rp_safety_metadata else None,
            "created_at": self.created_at,
        }


class TavernWorldProposalValidationReport(TavernModel):
    ok: bool
    proposal_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TavernToWorldProposalService:
    def __init__(self, repository: "TavernRepository | None" = None, links: CrossModeLinkRegistry | None = None) -> None:
        self.repository = repository
        self.links = links
        self._proposals: dict[str, TavernWorldProposal] = {}

    def create_proposal_from_message(self, *, project_id: str, session_id: str, message: TavernMessage, proposal_type: TavernWorldProposalType, proposed_content: dict[str, Any], target_world_refs: list[str] | None = None, create_link: bool = False) -> TavernWorldProposal:
        proposal = TavernWorldProposal(proposal_id=f"proposal_{message.message_id}", project_id=project_id, source_session_id=session_id, source_message_ids=[message.message_id], proposal_type=proposal_type, proposed_content=proposed_content, target_world_refs=target_world_refs or [], rp_safety_metadata=CrossModeRPSafetyMetadata(mature_policy_checked=True, consent_checked=True, visibility_checked=True, safe_notes=["Tavern to World content remains proposal-only."]))
        return self._store(proposal, create_link=create_link, source_ref=f"tavern:message:{message.message_id}")

    def create_proposal_from_memory(self, *, project_id: str, memory: TavernMemoryRecord, proposal_type: TavernWorldProposalType = TavernWorldProposalType.FACT_DISCOVERY, target_world_refs: list[str] | None = None) -> TavernWorldProposal:
        contains_mature = memory.visibility == TavernVisibility.MATURE_ONLY
        safe_content = "[mature memory filtered]" if contains_mature else redact_text(memory.content)
        proposal = TavernWorldProposal(proposal_id=f"proposal_{memory.memory_id}", project_id=project_id, source_session_id=memory.session_id, source_message_ids=list(memory.linked_message_ids), proposal_type=proposal_type, proposed_content={"summary": safe_content}, target_world_refs=target_world_refs or [], rp_safety_metadata=CrossModeRPSafetyMetadata(mature_policy_checked=True, consent_checked=True, visibility_checked=memory.visibility == TavernVisibility.TAVERN_SAFE, contains_mature_memory=contains_mature, mature_memory_filtered=True, safe_notes=["Tavern memory to World remains proposal-only."]))
        return self._store(proposal, source_ref=f"tavern:memory:{memory.memory_id}")

    def validate_proposal(self, proposal: TavernWorldProposal) -> TavernWorldProposalValidationReport:
        errors: list[str] = []
        allowed = ("world:", "npc:", "fact:", "quest:", "location:", "relationship:", "timeline:")
        for ref in proposal.target_world_refs:
            if ".." in ref or not ref.startswith(allowed):
                errors.append(f"Invalid target_world_ref: {redact_text(ref)}")
        payload = json.dumps(proposal.normal_summary(), ensure_ascii=False).lower()
        if contains_secret_text(payload) or "state_delta" in payload:
            errors.append("Proposal contains forbidden secret or StateDelta material")
        if proposal.proposal_type == TavernWorldProposalType.PROMISE_OR_DEAL and proposal.proposed_content.get("quest_completed"):
            errors.append("RP promise/deal cannot directly complete quests")
        if proposal.rp_safety_metadata is None:
            errors.append("Tavern to World proposal is missing RP safety metadata")
        elif proposal.rp_safety_metadata.contains_mature_content or proposal.rp_safety_metadata.contains_mature_memory:
            errors.append("Mature content cannot enter World facts through Tavern proposal")
        return TavernWorldProposalValidationReport(ok=not errors, proposal_id=proposal.proposal_id, errors=errors, warnings=list(proposal.warnings))

    def list_proposals(self) -> list[TavernWorldProposal]:
        if self.repository:
            return self.repository.list_proposals()
        return list(self._proposals.values())

    def reject_proposal(self, proposal_id: str) -> TavernWorldProposal:
        proposal = self._load(proposal_id).model_copy(update={"validation_status": TavernWorldProposalStatus.REJECTED})
        return self._store(proposal)

    def mark_proposal_ready(self, proposal_id: str) -> TavernWorldProposal:
        proposal = self._load(proposal_id)
        report = self.validate_proposal(proposal)
        status = TavernWorldProposalStatus.READY if report.ok else TavernWorldProposalStatus.INVALID
        return self._store(proposal.model_copy(update={"validation_status": status, "warnings": report.warnings + report.errors}))

    def _load(self, proposal_id: str) -> TavernWorldProposal:
        if self.repository:
            return self.repository.load_proposal(proposal_id)
        return self._proposals[proposal_id]

    def _store(self, proposal: TavernWorldProposal, *, create_link: bool = False, source_ref: str | None = None) -> TavernWorldProposal:
        if self.repository:
            self.repository.save_proposal(proposal)
        self._proposals[proposal.proposal_id] = proposal
        if create_link and self.links and source_ref:
            self.links.create_link(CrossModeLink(link_id=f"link_{proposal.proposal_id}", project_id=proposal.project_id, source_mode="tavern", source_ref=source_ref, target_mode="world", target_ref=f"world:proposal:{proposal.proposal_id}", link_type="rp_outcome_to_world_proposal"))
        return proposal


class WorldNpcToTavernAdapterResult(TavernModel):
    tavern_character: TavernCharacter
    rp_profile: TavernRPProfile
    voice_profile: TavernVoiceProfile
    cross_mode_link: CrossModeLink | None = None
    warnings: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "tavern_character": self.tavern_character.safe_summary(),
            "rp_profile": self.rp_profile.safe_summary(),
            "voice_profile": self.voice_profile.safe_summary(),
            "cross_mode_link": self.cross_mode_link.safe_summary() if self.cross_mode_link else None,
            "warnings": list(self.warnings),
        }


class WorldNpcToTavernAdapterService:
    def adapt(self, *, project_id: str, world_id: str, npc: NPCState, mode: Literal["player_safe", "authoring"] = "player_safe", player_visible_fact_ids: set[str] | None = None, create_link: bool = True) -> WorldNpcToTavernAdapterResult:
        if mode == "player_safe" and (npc.hidden or not npc.visible):
            raise ValueError("NPC is not visible in player_safe mode")
        visible_facts = player_visible_fact_ids or set()
        safe_knowledge = [fact_id for fact_id in npc.knowledge if fact_id in visible_facts]
        warnings = ["World NPC adapter creates Tavern drafts only; it does not modify NPC or GameState."]
        if npc.secrets:
            warnings.append("Sensitive NPC fields were excluded.")
        character_id = _safe_id(f"{world_id}_{npc.id}")
        tavern_character = TavernCharacter(tavern_character_id=character_id, project_id=project_id, display_name=npc.id, description=npc.rp_profile.public_persona, linked_world_npc_id=npc.id, rp_profile_id=f"rp_{character_id}", voice_profile_id=f"voice_{character_id}", lorebook_refs=safe_knowledge, safety_flags=warnings)
        private = "[authoring-only redacted]" if mode == "authoring" and npc.rp_profile.private_self_summary else ""
        rp_profile = TavernRPProfile(rp_profile_id=f"rp_{character_id}", tavern_character_id=character_id, public_persona=npc.rp_profile.public_persona, private_persona_authoring_only=private, emotional_baseline=npc.emotional_mask, taboo_topics=list(npc.taboo_topics))
        voice_profile = TavernVoiceProfile(voice_profile_id=f"voice_{character_id}", tone=npc.voice_profile.tone or npc.dialogue_style, speech_habits=list(npc.speech_habits or npc.voice_profile.speech_habits), vocabulary_style=npc.voice_profile.vocabulary_style, sentence_length=npc.voice_profile.sentence_length, catchphrases=list(npc.voice_profile.catchphrases), emotional_markers=list(npc.voice_profile.emotional_tells))
        link = CrossModeLink(link_id=f"link_{character_id}", project_id=project_id, source_mode="world", source_ref=f"world:npc:{npc.id}", target_mode="tavern", target_ref=f"tavern:character:{character_id}", link_type="world_npc_to_tavern_character") if create_link else None
        return WorldNpcToTavernAdapterResult(tavern_character=tavern_character, rp_profile=rp_profile, voice_profile=voice_profile, cross_mode_link=link, warnings=warnings)


def _redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_redact_obj(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact_obj(item) for key, item in value.items() if str(key).lower() not in {"hidden", "debug", "secret"}}
    return value


class TavernRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.section = TavernProjectSection()
        for directory in (
            self.section.characters_path,
            self.section.sessions_path,
            self.section.messages_path,
            self.section.lorebooks_path,
            self.section.scene_presets_path,
            self.section.memory_path,
            self.section.proposals_path,
            "tavern/preferences",
            "tavern/recovery",
            "tavern/scenes",
            "tavern/profiles",
        ):
            self._dir(directory).mkdir(parents=True, exist_ok=True)

    def create_tavern_character(self, character: TavernCharacter) -> TavernCharacter:
        return self.save_tavern_character(character)

    def load_tavern_character(self, character_id: str) -> TavernCharacter:
        return TavernCharacter.model_validate(self._read_yaml(self.section.characters_path, character_id))

    def save_tavern_character(self, character: TavernCharacter) -> TavernCharacter:
        updated = character.model_copy(update={"updated_at": now_iso()})
        self._write_yaml(self.section.characters_path, updated.tavern_character_id, updated)
        return updated

    def list_tavern_characters(self) -> list[TavernCharacter]:
        return sorted([TavernCharacter.model_validate(item) for item in self._read_all(self.section.characters_path)], key=lambda item: item.display_name)

    def create_session(self, session: TavernSession) -> TavernSession:
        return self.save_session(session)

    def load_session(self, session_id: str) -> TavernSession:
        session = TavernSession.model_validate(self._read_yaml(self.section.sessions_path, session_id))
        messages = self.list_messages(session_id)
        return session.model_copy(update={"messages": messages, "message_refs": [message.message_id for message in messages]})

    def save_session(self, session: TavernSession) -> TavernSession:
        updated = session.model_copy(update={"updated_at": now_iso(), "messages": []})
        self._write_yaml(self.section.sessions_path, updated.session_id, updated)
        return self.load_session(session.session_id) if (self._path(self.section.sessions_path, session.session_id)).exists() else updated

    def list_sessions(self) -> list[TavernSession]:
        return sorted([self.load_session(str(item.get("session_id"))) for item in self._read_all(self.section.sessions_path)], key=lambda item: item.created_at)

    def append_message(self, message: TavernMessage) -> TavernMessage:
        self._write_yaml(f"{self.section.messages_path}/{message.session_id}", message.message_id, message)
        try:
            session = self.load_session(message.session_id)
            refs = list(dict.fromkeys(session.message_refs + [message.message_id]))
            self.save_session(session.model_copy(update={"message_refs": refs, "messages": []}))
        except FileNotFoundError:
            pass
        return message

    def list_messages(self, session_id: str) -> list[TavernMessage]:
        return sorted([TavernMessage.model_validate(item) for item in self._read_all(f"{self.section.messages_path}/{session_id}")], key=lambda item: item.created_at)

    def archive_session(self, session_id: str) -> TavernSession:
        session = self.load_session(session_id)
        return self.save_session(session.model_copy(update={"status": TavernSessionStatus.ARCHIVED}))

    def save_scene_mood_preset(self, preset: SceneMoodPreset) -> SceneMoodPreset:
        self._write_yaml(self.section.scene_presets_path, preset.preset_id, preset)
        return preset

    def list_scene_mood_presets(self) -> list[SceneMoodPreset]:
        return sorted([SceneMoodPreset.model_validate(item) for item in self._read_all(self.section.scene_presets_path)], key=lambda item: item.name)

    def load_scene_mood_preset(self, preset_id: str) -> SceneMoodPreset:
        return SceneMoodPreset.model_validate(self._read_yaml(self.section.scene_presets_path, preset_id))

    def save_memory(self, record: TavernMemoryRecord) -> TavernMemoryRecord:
        self._write_yaml(self.section.memory_path, record.memory_id, record)
        return record

    def list_memories(self) -> list[TavernMemoryRecord]:
        return sorted([TavernMemoryRecord.model_validate(item) for item in self._read_all(self.section.memory_path)], key=lambda item: item.created_at)

    def save_proposal(self, proposal: TavernWorldProposal) -> TavernWorldProposal:
        self._write_yaml(self.section.proposals_path, proposal.proposal_id, proposal)
        return proposal

    def load_proposal(self, proposal_id: str) -> TavernWorldProposal:
        return TavernWorldProposal.model_validate(self._read_yaml(self.section.proposals_path, proposal_id))

    def list_proposals(self) -> list[TavernWorldProposal]:
        return sorted([TavernWorldProposal.model_validate(item) for item in self._read_all(self.section.proposals_path)], key=lambda item: item.created_at)

    def load_preferences(self, project_id: str) -> TavernPreferences:
        path = self._path("tavern/preferences", "tavern_preferences")
        if not path.exists():
            return TavernPreferences(project_id=project_id)
        return TavernPreferences.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    def save_preferences(self, preferences: TavernPreferences) -> TavernPreferences:
        updated = preferences.model_copy(update={"updated_at": now_iso()})
        self._write_yaml("tavern/preferences", "tavern_preferences", updated)
        return updated

    def save_recovery_record(self, record: TavernSessionRecoveryRecord) -> TavernSessionRecoveryRecord:
        updated = record.model_copy(update={"updated_at": now_iso()})
        self._write_yaml("tavern/recovery", updated.record_id, updated)
        return updated

    def list_recovery_records(self) -> list[TavernSessionRecoveryRecord]:
        return sorted([TavernSessionRecoveryRecord.model_validate(item) for item in self._read_all("tavern/recovery")], key=lambda item: item.created_at)

    def load_recovery_record(self, record_id: str) -> TavernSessionRecoveryRecord:
        return TavernSessionRecoveryRecord.model_validate(self._read_yaml("tavern/recovery", record_id))

    def delete_recovery_record(self, record_id: str) -> None:
        path = self._path("tavern/recovery", record_id)
        if path.exists():
            path.unlink()

    def _dir(self, rel: str) -> Path:
        safe = validate_project_relative_path(rel)
        path = (self.project_root / safe).resolve()
        if self.project_root not in path.parents and path != self.project_root:
            raise ValueError("Tavern repository path escaped project root")
        return path

    def _path(self, rel: str, item_id: str) -> Path:
        _safe_id(item_id, "item_id")
        return self._dir(rel) / f"{item_id}.yaml"

    def _write_yaml(self, rel: str, item_id: str, model: BaseModel) -> None:
        path = self._path(rel, item_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = model.model_dump(mode="json")
        if contains_secret_text(json.dumps(payload, ensure_ascii=False)):
            raise ValueError("Refusing to store Tavern data containing secrets")
        path.write_text(yaml.safe_dump(payload, sort_keys=True, allow_unicode=True), encoding="utf-8")

    def _read_yaml(self, rel: str, item_id: str) -> dict[str, Any]:
        path = self._path(rel, item_id)
        if not path.exists():
            raise FileNotFoundError(item_id)
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _read_all(self, rel: str) -> list[dict[str, Any]]:
        directory = self._dir(rel)
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.yaml")):
            if path.name.lower().startswith(".env"):
                continue
            items.append(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        return items


class TavernSessionExportService:
    filtering_policy = [
        "API key excluded",
        "hidden facts excluded",
        "NPC secrets excluded",
        "mature/private excluded by default",
        "debug data excluded",
    ]

    def __init__(self, repository: TavernRepository) -> None:
        self.repository = repository

    def preview_export(self, project_id: str, request: TavernSessionExportRequest) -> TavernSessionExportPreview:
        sessions = self._select_sessions(request)
        messages = [(session, message) for session in sessions for message in self.repository.list_messages(session.session_id)]
        safe_messages = [message for _, message in messages if message.safe_summary() is not None]
        excluded = len(messages) - len(safe_messages)
        samples = [str(message.safe_summary().get("content", ""))[:160] for message in safe_messages[:5] if message.safe_summary()]
        return TavernSessionExportPreview(
            project_id=project_id,
            format=request.format,
            session_count=len(sessions),
            message_count=len(safe_messages),
            safe_sample_summaries=samples,
            excluded_items=[f"{excluded} non-normal or filtered message(s)"] if excluded else [],
            warnings=[],
            filtering_policy=list(self.filtering_policy),
        )

    def create_export(self, project_id: str, request: TavernSessionExportRequest) -> TavernSessionExportResult:
        if not request.explicit_confirm:
            raise ValueError("explicit_confirm is required")
        preview = self.preview_export(project_id, request)
        content = self._render_export(request)
        if contains_secret_text(content) or _contains_key_like_text(content) or "state_delta" in content.lower():
            raise ValueError("Tavern export contains forbidden content")
        return TavernSessionExportResult(
            **preview.model_dump(mode="json", exclude={"dry_run"}),
            dry_run=False,
            exported=True,
            export_id=f"tavern_export_{now_iso().replace(':', '').replace('-', '')}",
            content_preview=content[:2000],
        )

    def _select_sessions(self, request: TavernSessionExportRequest) -> list[TavernSession]:
        sessions = self.repository.list_sessions()
        if request.scope == "all_sessions":
            return sessions
        selected = set(request.session_ids)
        if request.scope == "current_session":
            selected = {request.session_ids[0]} if request.session_ids else set()
        return [session for session in sessions if session.session_id in selected]

    def _render_export(self, request: TavernSessionExportRequest) -> str:
        policy = MatureExportPolicy(include_mature_content=request.include_mature_private, include_mature_memory=request.include_mature_private, include_debug=request.include_debug)
        export_filter = MatureExportFilter()
        sessions = self._select_sessions(request)
        if request.format == "markdown_transcript":
            lines: list[str] = ["# Tavern Session Safe Export", ""]
            for session in sessions:
                lines.extend([f"## {redact_text(session.title)}", ""])
                for message in self.repository.list_messages(session.session_id):
                    summary = message.safe_summary()
                    if summary is None:
                        continue
                    text = export_filter.filter_text(str(summary.get("content", "")), policy)
                    if text:
                        lines.append(f"- **{summary.get('speaker_type', 'speaker')}**: {text}")
            return "\n".join(lines)
        payload = {
            "local_only": True,
            "sessions": [
                {
                    "session": session.safe_summary(),
                    "messages": [summary for message in self.repository.list_messages(session.session_id) if (summary := message.safe_summary()) is not None],
                }
                for session in sessions
            ],
            "filtering_policy": list(self.filtering_policy),
        }
        return json.dumps(export_filter.filter_payload(payload, policy), ensure_ascii=False, indent=2)


class TavernRPSafetyDashboardService:
    categories = {
        "hidden_facts": "pass",
        "npc_secrets_knowledge": "pass",
        "private_persona": "pass",
        "mature_memory": "pass",
        "provider_safety_routing": "pass",
        "world_consistency": "pass",
        "proposal_validation": "pass",
        "export_safety": "pass",
    }

    def __init__(self, repository: TavernRepository) -> None:
        self.repository = repository

    def run(self, project_id: str) -> RPSafetyDashboardReport:
        issues: list[RPSafetyDashboardIssue] = []
        gate = run_rp_mature_quality_gate(self.repository.project_root)
        for blocker in gate.blockers:
            issues.append(RPSafetyDashboardIssue(severity="blocker", category="mature_memory", safe_summary=redact_text(blocker), suggested_action="Review Mature Module and export settings."))
        for error in gate.errors:
            issues.append(RPSafetyDashboardIssue(severity="error", category="export_safety", safe_summary=redact_text(error), suggested_action="Review normal export filtering."))
        for proposal in self.repository.list_proposals():
            if proposal.validation_status in {"invalid", "warning", "unvalidated"}:
                issues.append(RPSafetyDashboardIssue(severity="warning", category="proposal_validation", safe_summary=f"Proposal {proposal.proposal_id} requires validation.", affected_session_id=proposal.source_session_id, suggested_action="Validate the Tavern to World proposal before review."))
            if proposal.rp_safety_metadata and proposal.rp_safety_metadata.contains_mature_memory:
                issues.append(RPSafetyDashboardIssue(severity="warning", category="mature_memory", safe_summary="A proposal references mature memory metadata; normal view remains filtered.", affected_session_id=proposal.source_session_id, suggested_action="Keep mature memory excluded unless policy explicitly allows it."))
        categories = dict(self.categories)
        for issue in issues:
            categories[issue.category] = "fail" if issue.severity in {"error", "blocker"} else "warning"
        blockers = sum(1 for issue in issues if issue.severity == "blocker")
        errors = sum(1 for issue in issues if issue.severity == "error")
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        status: Literal["pass", "warning", "fail", "not_run"] = "fail" if blockers or errors else "warning" if warnings else "pass"
        return RPSafetyDashboardReport(project_id=project_id, overall_status=status, blocker_count=blockers, error_count=errors, warning_count=warnings, categories=categories, issues=issues)


class MultiCharacterSceneService:
    def __init__(self, scenes: list[MultiCharacterScene] | None = None, characters: list[TavernCharacter] | None = None) -> None:
        self.scenes = {scene.scene_id: scene for scene in scenes or []}
        self.character_ids = {character.tavern_character_id for character in characters or []}

    def create_multi_character_scene(self, scene: MultiCharacterScene) -> MultiCharacterScene:
        missing = [cid for cid in scene.character_ids if self.character_ids and cid not in self.character_ids]
        if missing:
            raise ValueError(f"Unknown Tavern character(s): {', '.join(missing)}")
        self.scenes[scene.scene_id] = scene
        return scene

    def list_scenes_for_session(self, session_id: str) -> list[MultiCharacterScene]:
        return [scene for scene in self.scenes.values() if scene.session_id == session_id]

    def update_scene_context(self, scene_id: str, scene_context: TavernSceneContext) -> MultiCharacterScene:
        scene = self.scenes[scene_id].model_copy(update={"scene_context": scene_context})
        self.scenes[scene_id] = scene
        return scene


def get_tavern_repository_for_project(project_id: str, project_repository: ProjectRepository) -> TavernRepository:
    project = project_repository.load_project(project_id)
    return TavernRepository(project.project_root)
