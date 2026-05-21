from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.platform.narrative_project import validate_project_relative_path
from app.platform.security import contains_secret_text, redact_text, safe_identifier


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ModeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModeRouteContext(ModeModel):
    project_id: str
    mode: Literal["novel", "tavern", "world", "script", "quality", "settings"]
    active_world_id: str | None = None
    active_session_id: str | None = None
    prompt_profile_id: str | None = None
    provider_profile_id: str | None = None


class ModeStatus(ModeModel):
    mode: str
    enabled: bool
    configured: bool
    missing_requirements: list[str] = Field(default_factory=list)
    safe_summary: dict[str, Any] = Field(default_factory=dict)


class ModeRouter:
    def modes_for_project(self, project: Any) -> list[ModeStatus]:
        return [self.status_for_mode(project, mode) for mode in ("novel", "tavern", "world", "script", "quality", "settings")]

    def status_for_mode(self, project: Any, mode: str) -> ModeStatus:
        modes = getattr(project, "modes", None)
        enabled = {
            "novel": bool(getattr(modes, "novel_enabled", True)),
            "tavern": bool(getattr(modes, "tavern_enabled", True)),
            "world": bool(getattr(modes, "world_enabled", True)),
            "script": bool(getattr(modes, "script_platform_enabled", True)),
            "quality": bool(getattr(modes, "quality_enabled", True)),
            "settings": True,
        }.get(mode, False)
        missing: list[str] = []
        if mode == "world" and not getattr(project, "default_world_id", None):
            missing.append("default_world_id not configured")
        return ModeStatus(
            mode=mode,
            enabled=enabled,
            configured=enabled and not missing,
            missing_requirements=missing,
            safe_summary={"project_id": project.project_id, "stub": mode in {"novel", "tavern"}},
        )


class NovelProjectSection(ModeModel):
    manuscripts_path: str = "novel/manuscripts"
    outlines_path: str = "novel/outlines"
    chapters_path: str = "novel/chapters"
    scenes_path: str = "novel/scenes"
    arcs_path: str = "novel/arcs"
    plot_threads_path: str = "novel/plot_threads"
    foreshadowing_path: str = "novel/foreshadowing"
    drafts_path: str = "novel/drafts"
    exports_path: str = "novel/exports"
    linked_character_library: str | None = None
    linked_world_bible: str | None = None
    linked_timeline: str | None = None
    default_prompt_profile_id: str | None = None

    @field_validator(
        "manuscripts_path",
        "outlines_path",
        "chapters_path",
        "scenes_path",
        "arcs_path",
        "plot_threads_path",
        "foreshadowing_path",
        "drafts_path",
        "exports_path",
    )
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return validate_project_relative_path(value)


class NovelOutlineDraft(ModeModel):
    outline_id: str
    project_id: str
    title: str
    summary: str = ""
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_world_bible_entry_ids: list[str] = Field(default_factory=list)
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    status: Literal["draft", "review", "archived"] = "draft"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ChapterDraft(ModeModel):
    chapter_id: str
    project_id: str
    title: str
    outline_id: str | None = None
    order_index: int = 0
    content: str = ""
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    authoring_only: bool = True
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_no_secret(self) -> "ChapterDraft":
        if contains_secret_text(self.content):
            raise ValueError("ChapterDraft must not contain API keys or secrets")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "project_id": self.project_id,
            "title": self.title,
            "outline_id": self.outline_id,
            "order_index": self.order_index,
            "linked_character_ids": self.linked_character_ids,
            "linked_fact_ids": self.linked_fact_ids,
            "authoring_only": self.authoring_only,
            "content_preview": redact_text(self.content[:160]) if not self.authoring_only else "[authoring draft]",
        }


class NovelModeProjectState(ModeModel):
    project_id: str
    section: NovelProjectSection = Field(default_factory=NovelProjectSection)
    outlines: dict[str, NovelOutlineDraft] = Field(default_factory=dict)
    chapters: dict[str, ChapterDraft] = Field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "outlines_count": len(self.outlines),
            "chapters_count": len(self.chapters),
            "linked_character_library": self.section.linked_character_library,
            "linked_world_bible": self.section.linked_world_bible,
            "linked_timeline": self.section.linked_timeline,
            "message": "Novel Studio MVP coming in v2.2",
        }


class TavernProjectSection(ModeModel):
    characters_path: str = "tavern/characters"
    sessions_path: str = "tavern/sessions"
    lorebooks_path: str = "tavern/lorebooks"
    linked_character_library: str | None = None
    linked_memory_library: str | None = None
    default_prompt_profile_id: str | None = None
    default_provider_profile_id: str | None = None

    @field_validator("characters_path", "sessions_path", "lorebooks_path")
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return validate_project_relative_path(value)


class TavernMessageDraft(ModeModel):
    message_id: str
    session_id: str
    speaker_ref: str
    content: str
    visibility: Literal["tavern_safe", "authoring_only", "hidden"] = "tavern_safe"
    linked_memory_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any] | None:
        if self.visibility != "tavern_safe":
            return None
        return {"message_id": self.message_id, "session_id": self.session_id, "speaker_ref": self.speaker_ref, "content": redact_text(self.content)}


class RPProposalDraft(ModeModel):
    proposal_id: str
    proposal_type: Literal["relationship_change", "new_fact", "memory"] = "memory"
    status: Literal["draft", "review", "rejected", "accepted_for_validation"] = "draft"
    summary: str = ""
    creates_state_delta: Literal[False] = False
    creates_world_fact: Literal[False] = False


class TavernSessionDraft(ModeModel):
    session_id: str
    project_id: str
    title: str
    linked_character_ids: list[str] = Field(default_factory=list)
    messages: list[TavernMessageDraft] = Field(default_factory=list)
    proposals: list[RPProposalDraft] = Field(default_factory=list)
    status: Literal["draft", "active_stub", "archived"] = "draft"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "title": self.title,
            "character_count": len(self.linked_character_ids),
            "message_count": len(self.messages),
            "proposal_count": len(self.proposals),
            "messages": [summary for message in self.messages if (summary := message.safe_summary()) is not None],
        }


class TavernModeProjectState(ModeModel):
    project_id: str
    section: TavernProjectSection = Field(default_factory=TavernProjectSection)
    sessions: dict[str, TavernSessionDraft] = Field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "character_count": 0,
            "session_count": len(self.sessions),
            "linked_memory_library": self.section.linked_memory_library,
            "message": "Tavern Studio MVP coming in v2.3",
        }


class WorldProjectSection(ModeModel):
    content_pack_path: str = "world/content_pack"
    saves_path: str = "world/saves"
    campaigns_path: str = "world/campaigns"
    default_world_id: str = "mist_valley"
    linked_world_bible_id: str | None = None
    linked_character_library_id: str | None = None

    @field_validator("content_pack_path", "saves_path", "campaigns_path")
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return validate_project_relative_path(value)


def resolve_project_world_path(project_root: str | Path, section: WorldProjectSection, world_id: str) -> Path:
    if not safe_identifier(world_id):
        raise ValueError("Unsafe world_id")
    root = Path(project_root).resolve()
    base = (root / section.content_pack_path).resolve()
    candidate_nested = (base / world_id).resolve()
    candidate_single = base.resolve()
    if candidate_nested.exists():
        candidate = candidate_nested
    else:
        candidate = candidate_single
    if not (candidate == base or base in candidate.parents):
        raise ValueError("Resolved world path escaped project content pack path")
    return candidate
