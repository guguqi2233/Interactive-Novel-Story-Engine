from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.platform.narrative_project import validate_project_id
from app.platform.security import contains_secret_text, redact_text, safe_identifier


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class LibraryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _safe_id(value: str) -> str:
    if not safe_identifier(value):
        raise ValueError("Unsafe id")
    return value


class CharacterProfile(LibraryModel):
    character_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    role_tags: list[str] = Field(default_factory=list)
    age_category: Literal["unknown", "minor", "adult", "elder", "nonhuman"] = "unknown"
    public_profile: str = ""
    private_notes_authoring_only: str = ""
    voice_profile: dict[str, Any] = Field(default_factory=dict)
    rp_profile_ref: str | None = None
    world_npc_refs: list[str] = Field(default_factory=list)
    novel_character_refs: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)

    @field_validator("character_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _safe_id(value)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "aliases": self.aliases,
            "description": self.description,
            "role_tags": self.role_tags,
            "age_category": self.age_category,
            "public_profile": self.public_profile,
            "world_npc_refs": self.world_npc_refs,
            "novel_character_refs": self.novel_character_refs,
            "safety_flags": self.safety_flags,
        }


class CharacterLibrary(LibraryModel):
    project_id: str
    characters: dict[str, CharacterProfile] = Field(default_factory=dict)

    @field_validator("project_id")
    @classmethod
    def validate_project(cls, value: str) -> str:
        return validate_project_id(value)

    def add_character(self, profile: CharacterProfile) -> None:
        self.characters[profile.character_id] = profile

    def get_character(self, character_id: str) -> CharacterProfile | None:
        return self.characters.get(character_id)

    def link_world_npc(self, character_id: str, npc_id: str) -> None:
        profile = self.characters[character_id]
        if npc_id not in profile.world_npc_refs:
            profile.world_npc_refs.append(npc_id)

    def safe_summary(self) -> dict[str, Any]:
        return {"project_id": self.project_id, "characters": [item.safe_summary() for item in self.characters.values()]}


class WorldBibleEntryType(StrEnum):
    FLAVOR = "flavor"
    STRUCTURED_FACT = "structured_fact"
    HIDDEN = "hidden"
    AUTHORING_NOTE = "authoring_note"
    STYLE_NOTE = "style_note"


class WorldBibleEntry(LibraryModel):
    id: str
    title: str
    content: str
    entry_type: WorldBibleEntryType = WorldBibleEntryType.FLAVOR
    visibility: Literal["public", "narrator_safe", "authoring_only", "hidden"] = "public"
    tags: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _safe_id(value)

    @property
    def is_safe_context(self) -> bool:
        return self.entry_type in {WorldBibleEntryType.FLAVOR, WorldBibleEntryType.STYLE_NOTE} and self.visibility in {"public", "narrator_safe"}


class WorldBible(LibraryModel):
    world_bible_id: str
    project_id: str
    title: str
    overview: str = ""
    flavor_lore: list[str] = Field(default_factory=list)
    structured_facts_refs: list[str] = Field(default_factory=list)
    hidden_facts_refs: list[str] = Field(default_factory=list)
    setting_notes_authoring_only: str = ""
    timeline_refs: list[str] = Field(default_factory=list)
    linked_world_ids: list[str] = Field(default_factory=list)
    entries: dict[str, WorldBibleEntry] = Field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "world_bible_id": self.world_bible_id,
            "project_id": self.project_id,
            "title": self.title,
            "overview": self.overview,
            "flavor_lore": self.flavor_lore,
            "entries": [entry.model_dump(mode="json") for entry in self.entries.values() if entry.is_safe_context],
        }


class TimelineEvent(LibraryModel):
    timeline_event_id: str
    project_id: str
    title: str
    description: str = ""
    event_type: Literal["novel", "tavern", "world", "authoring", "imported", "draft"] = "draft"
    source_ref: str | None = None
    linked_event_ids: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    linked_location_ids: list[str] = Field(default_factory=list)
    chronological_index: int | None = None
    in_world_time: str | None = None
    authoring_only: bool = False
    visibility: Literal["public", "narrator_safe", "authoring_only", "hidden"] = "public"

    def safe_summary(self) -> dict[str, Any] | None:
        if self.authoring_only or self.visibility in {"authoring_only", "hidden"}:
            return None
        return self.model_dump(mode="json")


class TimelineLibrary(LibraryModel):
    project_id: str
    events: dict[str, TimelineEvent] = Field(default_factory=dict)

    def add_timeline_event(self, event: TimelineEvent) -> None:
        self.events[event.timeline_event_id] = event

    def list_timeline(self) -> list[TimelineEvent]:
        return sorted(self.events.values(), key=lambda item: (item.chronological_index is None, item.chronological_index or 0, item.timeline_event_id))

    def safe_timeline_summary(self) -> list[dict[str, Any]]:
        return [summary for event in self.list_timeline() if (summary := event.safe_summary()) is not None]


class LoreFactEntry(LibraryModel):
    id: str
    project_id: str
    title: str
    text: str
    fact_type: Literal["flavor", "structured", "hidden", "draft", "authoring_note"] = "draft"
    visibility: Literal["public", "narrator_safe", "tavern_safe", "novel_safe", "authoring_only", "hidden"] = "authoring_only"
    source_mode: Literal["novel", "tavern", "world", "authoring", "imported"] = "authoring"
    linked_world_fact_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    safe_for_narrator: bool = False
    safe_for_tavern: bool = False
    safe_for_novel: bool = False
    safe_for_world_import: bool = False

    def safe_text(self) -> str:
        if self.fact_type in {"hidden", "authoring_note"} or self.visibility in {"hidden", "authoring_only"}:
            return "[redacted]"
        return redact_text(self.text)


class LoreFactLibrary(LibraryModel):
    project_id: str
    entries: dict[str, LoreFactEntry] = Field(default_factory=dict)

    def add_draft_lore(self, entry: LoreFactEntry) -> None:
        self.entries[entry.id] = entry

    def get_novel_safe_lore(self) -> list[LoreFactEntry]:
        return [entry for entry in self.entries.values() if entry.safe_for_novel and entry.fact_type != "hidden"]

    def get_tavern_safe_lore(self) -> list[LoreFactEntry]:
        return [entry for entry in self.entries.values() if entry.safe_for_tavern and entry.fact_type != "hidden"]

    def get_world_import_candidates(self) -> list[LoreFactEntry]:
        return [entry for entry in self.entries.values() if entry.safe_for_world_import and entry.fact_type in {"structured", "draft"}]


class ProjectPromptProfile(LibraryModel):
    profile_id: str
    mode_scopes: list[Literal["novel", "tavern", "world", "authoring", "quality"]] = Field(default_factory=list)
    narrator_style: str = ""
    rp_style: str = ""
    novel_style: str = ""
    intent_parser_variant: str = "default"
    memory_summary_variant: str = "default"
    temperature_overrides: dict[str, float] = Field(default_factory=dict)
    max_output_tokens: int | None = None
    can_access_hidden_facts: Literal[False] = False
    can_modify_state: Literal[False] = False
    can_override_action_result: Literal[False] = False
    can_bypass_visibility: Literal[False] = False

    @model_validator(mode="after")
    def validate_safe(self) -> "ProjectPromptProfile":
        if contains_secret_text(self.model_dump_json()):
            raise ValueError("Prompt profile must not contain secrets")
        return self


class PromptProfileLibrary(LibraryModel):
    project_id: str
    profiles: dict[str, ProjectPromptProfile] = Field(default_factory=dict)

    def for_mode(self, mode: str) -> list[ProjectPromptProfile]:
        return [profile for profile in self.profiles.values() if mode in profile.mode_scopes]


class ProjectProviderProfile(LibraryModel):
    provider_profile_id: str
    provider_type: Literal["openai", "openai_compatible", "local_http", "mock", "local_stub"]
    display_name: str
    base_url_ref: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    local_secret_ref: str | None = None
    model_profiles: list[dict[str, Any]] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    allowed_modes: list[Literal["novel", "tavern", "world", "quality", "authoring"]] = Field(default_factory=list)
    cost_tracking_enabled: bool = False
    fallback_profile_id: str | None = None

    @field_validator("api_key_env")
    @classmethod
    def validate_api_key_env_ref(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if re.search(r"sk-[A-Za-z0-9_-]{8,}", value) or "PRIVATE KEY" in value:
            raise ValueError("Provider profile api_key_env must be an env-var reference, not a secret value")
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]{0,127}", value):
            raise ValueError("Provider profile api_key_env must be a safe environment variable name")
        return value

    @field_validator("local_secret_ref")
    @classmethod
    def validate_local_secret_ref(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if re.search(r"sk-[A-Za-z0-9_-]{8,}", value) or "PRIVATE KEY" in value or "authorization" in value.lower():
            raise ValueError("Provider profile local_secret_ref must be a reference, not a secret value")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*(?:/[A-Za-z0-9][A-Za-z0-9_.:-]*){0,7}", value):
            raise ValueError("Provider profile local_secret_ref must be a safe local reference")
        return value

    @model_validator(mode="before")
    @classmethod
    def reject_raw_key(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if str(key).lower() in {"api_key", "llm_api_key", "openai_api_key"}:
                    raise ValueError("Provider profile must not contain raw API key")
                if str(key).lower() in {"api_key_env", "local_secret_ref"}:
                    continue
                if isinstance(value, str) and contains_secret_text(value):
                    raise ValueError("Provider profile must not contain secrets")
        return data

    def safe_export(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ProviderProfileLibrary(LibraryModel):
    project_id: str
    profiles: dict[str, ProjectProviderProfile] = Field(default_factory=dict)

    def for_mode(self, mode: str) -> list[ProjectProviderProfile]:
        return [profile for profile in self.profiles.values() if mode in profile.allowed_modes]


class ProjectMemoryRecord(LibraryModel):
    memory_id: str
    project_id: str
    source_mode: Literal["novel", "tavern", "world", "authoring", "quality"]
    content: str
    source_refs: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    visibility: Literal["player_visible", "narrator_safe", "tavern_safe", "novel_safe", "mature_only", "debug_only", "hidden"] = "hidden"
    authoritative: Literal[False] = False
    importance: float = 0.0
    created_at: str = Field(default_factory=now_iso)

    def safe_content(self) -> str:
        if self.visibility in {"debug_only", "hidden", "mature_only"}:
            return "[redacted]"
        return redact_text(self.content)


class ProjectMemoryLibrary(LibraryModel):
    project_id: str
    memories: dict[str, ProjectMemoryRecord] = Field(default_factory=dict)

    def get_memory_context_for_mode(self, mode: str) -> list[ProjectMemoryRecord]:
        allowed = {
            "novel": {"novel_safe", "narrator_safe", "player_visible"},
            "tavern": {"tavern_safe", "player_visible"},
            "world": {"narrator_safe", "player_visible"},
            "quality": {"narrator_safe", "player_visible"},
        }.get(mode, {"player_visible"})
        return [record for record in self.memories.values() if record.visibility in allowed]


class CrossModeLink(LibraryModel):
    link_id: str
    project_id: str
    source_mode: Literal["novel", "tavern", "world", "script", "quality", "settings"]
    source_ref: str
    target_mode: Literal["novel", "tavern", "world", "script", "quality", "settings"]
    target_ref: str
    link_type: str
    status: Literal["draft", "validated", "broken", "deprecated"] = "draft"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    notes: str = ""
    hidden: bool = False

    def safe_summary(self) -> dict[str, Any] | None:
        if self.hidden:
            return None
        payload = self.model_dump(mode="json")
        payload["notes"] = redact_text(self.notes)
        return payload


class CrossModeLinkValidationReport(LibraryModel):
    ok: bool
    link_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CrossModeLinkRegistry(LibraryModel):
    project_id: str
    links: dict[str, CrossModeLink] = Field(default_factory=dict)

    def create_link(self, link: CrossModeLink) -> CrossModeLink:
        self.links[link.link_id] = link
        return link

    def validate_link(self, link_id: str, existing_refs: set[str] | None = None) -> CrossModeLinkValidationReport:
        link = self.links[link_id]
        errors: list[str] = []
        if existing_refs is not None:
            if link.source_ref not in existing_refs:
                errors.append("source_ref not found")
            if link.target_ref not in existing_refs:
                errors.append("target_ref not found")
        if errors:
            link.status = "broken"
        else:
            link.status = "validated"
        link.updated_at = now_iso()
        return CrossModeLinkValidationReport(ok=not errors, link_id=link_id, errors=errors)

    def list_links_for_ref(self, ref: str) -> list[CrossModeLink]:
        return [link for link in self.links.values() if link.source_ref == ref or link.target_ref == ref]

    def mark_broken(self, link_id: str) -> CrossModeLink:
        self.links[link_id].status = "broken"
        self.links[link_id].updated_at = now_iso()
        return self.links[link_id]

    def delete_link(self, link_id: str) -> bool:
        return self.links.pop(link_id, None) is not None
