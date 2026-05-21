from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.migrations import CURRENT_ENGINE_VERSION
from app.platform.security import contains_secret_text, safe_identifier


NARRATIVE_PROJECT_SCHEMA_VERSION = "2.1"
NARRATIVE_PROJECT_VERSION = "2.1.0"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def validate_project_id(value: str) -> str:
    if not safe_identifier(value):
        raise ValueError("Unsafe project id")
    return value


def validate_project_relative_path(value: str) -> str:
    normalized = str(value).replace("\\", "/").strip()
    parts = Path(normalized).parts
    if normalized in {"", "."} or Path(normalized).is_absolute() or normalized.startswith("/") or ".." in parts:
        raise ValueError(f"Unsafe project relative path: {value}")
    if normalized.lower().startswith(("logs/", "cache/", "caches/", "node_modules/", "frontend/dist/", "backups/", "crash-reports/")):
        raise ValueError(f"Forbidden project path: {value}")
    if Path(normalized).name.lower().startswith(".env"):
        raise ValueError(f"Forbidden project path: {value}")
    return normalized


class StrictProjectModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectModeConfig(StrictProjectModel):
    novel_enabled: bool = True
    tavern_enabled: bool = True
    world_enabled: bool = True
    script_platform_enabled: bool = True
    quality_enabled: bool = True


class ProjectLibraryRefs(StrictProjectModel):
    character_library: str | None = None
    world_bible: str | None = None
    timeline: str | None = None
    lore_facts: str | None = None
    prompt_profiles: str | None = None
    provider_profiles: str | None = None
    memory_library: str | None = None


class ProjectSafetyPolicy(StrictProjectModel):
    local_only: bool = True
    allow_debug_exports: bool = False
    allow_mature_content: bool = False
    allow_external_providers: bool = False
    export_secrets: Literal[False] = False


class ProjectSettings(StrictProjectModel):
    default_mode: Literal["novel", "tavern", "world", "script", "quality", "settings"] = "world"
    ui_locale: str = "en"
    notes: str = ""

    @field_validator("notes")
    @classmethod
    def reject_secret_notes(cls, value: str) -> str:
        if contains_secret_text(value):
            raise ValueError("Project settings notes must not contain secrets")
        return value


class NarrativeProject(StrictProjectModel):
    project_id: str = "local_project"
    name: str = "Local Narrative Project"
    description: str = ""
    version: str = NARRATIVE_PROJECT_VERSION
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    engine_version: str = CURRENT_ENGINE_VERSION
    schema_version: str = NARRATIVE_PROJECT_SCHEMA_VERSION
    default_world_id: str | None = None
    active_campaign_id: str | None = None
    project_root: str = "."
    modes: ProjectModeConfig = Field(default_factory=ProjectModeConfig)
    libraries: ProjectLibraryRefs = Field(default_factory=ProjectLibraryRefs)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    safety_policy: ProjectSafetyPolicy = Field(default_factory=ProjectSafetyPolicy)
    migration_history: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("project_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_project_id(value)

    @field_validator("default_world_id", "active_campaign_id")
    @classmethod
    def validate_optional_ref(cls, value: str | None) -> str | None:
        if value is not None and not safe_identifier(value):
            raise ValueError("Unsafe project reference id")
        return value

    @model_validator(mode="after")
    def validate_safe_project(self) -> "NarrativeProject":
        if self.safety_policy.export_secrets is not False:
            raise ValueError("NarrativeProject cannot export secrets")
        if contains_secret_text(self.description):
            raise ValueError("NarrativeProject description must not contain secrets")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "default_world_id": self.default_world_id,
            "active_campaign_id": self.active_campaign_id,
            "modes": self.modes.model_dump(mode="json"),
            "libraries": self.libraries.model_dump(mode="json"),
            "safety_policy": self.safety_policy.model_dump(mode="json"),
        }

