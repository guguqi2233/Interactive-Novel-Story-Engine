from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Literal, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.event_log import Event, EventLog
from app.core.world_state import GameState
from app.llm.provider_base import LLMProvider, Message
from app.platform.narrative_project import validate_project_id, validate_project_relative_path
from app.platform.project_repository import ProjectRepository
from app.platform.rp_mature import MatureExportFilter, MatureExportPolicy
from app.platform.security import contains_secret_text, redact_text, safe_identifier, validate_relative_package_path
from app.platform.shared_libraries import (
    CharacterLibrary,
    CrossModeLink,
    CrossModeLinkRegistry,
    LoreFactLibrary,
    ProjectPromptProfile,
    PromptProfileLibrary,
    TimelineLibrary,
    WorldBible,
    WorldBibleEntryType,
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class NovelModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NovelDraftStatus(StrEnum):
    DRAFT = "draft"
    REVISED = "revised"
    REVIEWED = "reviewed"
    EXPORTED = "exported"
    ARCHIVED = "archived"


class NovelProjectSection(NovelModel):
    manuscripts_path: str = "novel/manuscripts"
    outlines_path: str = "novel/outlines"
    chapters_path: str = "novel/chapters"
    scenes_path: str = "novel/scenes"
    arcs_path: str = "novel/arcs"
    plot_threads_path: str = "novel/plot_threads"
    foreshadowing_path: str = "novel/foreshadowing"
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
        "exports_path",
    )
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return validate_project_relative_path(value)


class NovelManuscript(NovelModel):
    manuscript_id: str = "manuscript"
    project_id: str = "local_project"
    title: str = "Untitled Manuscript"
    description: str = ""
    genre_tags: list[str] = Field(default_factory=list)
    target_style: str = ""
    outline_refs: list[str] = Field(default_factory=list)
    chapter_refs: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_world_bible_id: str | None = None
    linked_timeline_id: str | None = None
    default_prompt_profile_id: str | None = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @field_validator("manuscript_id", "project_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe novel id")
        return value


class NovelOutlineNode(NovelModel):
    node_id: str
    parent_id: str | None = None
    node_type: Literal["act", "volume", "chapter", "scene", "beat", "note"] = "note"
    title: str
    summary: str = ""
    order_index: int = 0
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    linked_plot_thread_ids: list[str] = Field(default_factory=list)
    linked_world_bible_entry_ids: list[str] = Field(default_factory=list)
    status: NovelDraftStatus = NovelDraftStatus.DRAFT


class NovelOutline(NovelModel):
    outline_id: str = "outline"
    project_id: str = "local_project"
    manuscript_id: str | None = None
    title: str = "Outline"
    summary: str = ""
    nodes: list[NovelOutlineNode] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_world_bible_entry_ids: list[str] = Field(default_factory=list)
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    status: NovelDraftStatus = NovelDraftStatus.DRAFT
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class NovelChapter(NovelModel):
    chapter_id: str = "chapter"
    project_id: str = "local_project"
    manuscript_id: str | None = None
    title: str = "Untitled Chapter"
    order_index: int = 0
    summary: str = ""
    scene_refs: list[str] = Field(default_factory=list)
    draft_text: str = ""
    status: NovelDraftStatus = NovelDraftStatus.DRAFT
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    authoring_notes: str = ""
    visibility: Literal["normal", "authoring_only", "hidden"] = "normal"
    prompt_profile_id: str | None = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def reject_secrets(self) -> "NovelChapter":
        if contains_secret_text(self.draft_text) or contains_secret_text(self.authoring_notes):
            raise ValueError("NovelChapter must not contain API keys or secrets")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "project_id": self.project_id,
            "manuscript_id": self.manuscript_id,
            "title": self.title,
            "order_index": self.order_index,
            "summary": redact_text(self.summary),
            "scene_refs": self.scene_refs,
            "status": self.status.value,
            "linked_timeline_event_ids": self.linked_timeline_event_ids,
            "linked_character_ids": self.linked_character_ids,
            "linked_fact_ids": self.linked_fact_ids,
            "visibility": self.visibility,
            "prompt_profile_id": self.prompt_profile_id,
            "draft_preview": redact_text(self.draft_text[:240]) if self.visibility == "normal" else "[redacted]",
        }


class NovelScene(NovelModel):
    scene_id: str = "scene"
    project_id: str = "local_project"
    chapter_id: str
    title: str = "Untitled Scene"
    summary: str = ""
    draft_text: str = ""
    pov_character_id: str | None = None
    location_ref: str | None = None
    timeline_event_refs: list[str] = Field(default_factory=list)
    linked_world_event_ids: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    status: NovelDraftStatus = NovelDraftStatus.DRAFT
    prompt_profile_id: str | None = None
    visibility: Literal["normal", "authoring_only", "hidden"] = "normal"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "chapter_id": self.chapter_id,
            "title": self.title,
            "summary": redact_text(self.summary),
            "status": self.status.value,
            "visibility": self.visibility,
            "draft_preview": redact_text(self.draft_text[:180]) if self.visibility == "normal" else "[redacted]",
        }


class CharacterArcTurningPoint(NovelModel):
    order_index: int
    title: str
    summary: str = ""
    linked_scene_id: str | None = None


class CharacterArc(NovelModel):
    arc_id: str
    project_id: str = "local_project"
    character_id: str
    title: str
    premise: str = ""
    start_state: str = ""
    end_state: str = ""
    key_turning_points: list[CharacterArcTurningPoint] = Field(default_factory=list)
    linked_chapter_ids: list[str] = Field(default_factory=list)
    linked_scene_ids: list[str] = Field(default_factory=list)
    linked_timeline_event_ids: list[str] = Field(default_factory=list)
    status: NovelDraftStatus = NovelDraftStatus.DRAFT
    authoring_notes: str = ""

    def safe_summary(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload["authoring_notes"] = "[redacted]" if self.authoring_notes else ""
        return payload


class PlotThread(NovelModel):
    plot_thread_id: str
    title: str
    description: str = ""
    thread_type: Literal["main", "side", "mystery", "romance", "conflict", "worldbuilding"] = "side"
    status: Literal["open", "developing", "resolved", "abandoned"] = "open"
    linked_chapter_ids: list[str] = Field(default_factory=list)
    linked_scene_ids: list[str] = Field(default_factory=list)
    linked_character_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    authoring_notes: str = ""


class ForeshadowingItem(NovelModel):
    foreshadowing_id: str
    setup_scene_id: str
    payoff_scene_id: str | None = None
    hint_text: str
    hidden_truth_ref: str | None = None
    status: Literal["planted", "reinforced", "paid_off", "abandoned"] = "planted"
    visibility: Literal["normal", "authoring_only", "hidden"] = "normal"

    def safe_summary(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        if self.hidden_truth_ref:
            payload["hidden_truth_ref"] = "[hidden-ref]"
        if self.visibility != "normal":
            payload["hint_text"] = "[redacted]"
        return payload


def _ensure_safe_id(value: str) -> str:
    if not safe_identifier(value):
        raise ValueError(f"Unsafe id: {value}")
    return value


def _write_yaml(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(model.model_dump(mode="json"), sort_keys=True, allow_unicode=True), encoding="utf-8")


def _read_yaml(path: Path, model: type[NovelModel]) -> Any:
    return model.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


class NovelRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.novel_root = (self.project_root / "novel").resolve()
        if self.project_root not in self.novel_root.parents:
            raise ValueError("Novel root escaped project root")

    def _dir(self, section: str) -> Path:
        safe = validate_project_relative_path(f"novel/{section}")
        target = (self.project_root / safe).resolve()
        if self.project_root not in target.parents:
            raise ValueError("Novel repository path escaped project root")
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _path(self, section: str, item_id: str) -> Path:
        _ensure_safe_id(item_id)
        return self._dir(section) / f"{item_id}.yaml"

    def create_manuscript(self, manuscript: NovelManuscript) -> NovelManuscript:
        self.save_manuscript(manuscript)
        return manuscript

    def load_manuscript(self, manuscript_id: str) -> NovelManuscript:
        return _read_yaml(self._path("manuscripts", manuscript_id), NovelManuscript)

    def save_manuscript(self, manuscript: NovelManuscript) -> NovelManuscript:
        updated = manuscript.model_copy(update={"updated_at": now_iso()})
        _write_yaml(self._path("manuscripts", updated.manuscript_id), updated)
        return updated

    def list_manuscripts(self) -> list[NovelManuscript]:
        return sorted((_read_yaml(path, NovelManuscript) for path in self._dir("manuscripts").glob("*.yaml")), key=lambda item: item.title)

    def create_outline(self, outline: NovelOutline) -> NovelOutline:
        return self.save_outline(outline)

    def save_outline(self, outline: NovelOutline) -> NovelOutline:
        updated = outline.model_copy(update={"updated_at": now_iso()})
        _write_yaml(self._path("outlines", updated.outline_id), updated)
        return updated

    def load_outline(self, outline_id: str) -> NovelOutline:
        return _read_yaml(self._path("outlines", outline_id), NovelOutline)

    def list_outlines(self) -> list[NovelOutline]:
        return sorted((_read_yaml(path, NovelOutline) for path in self._dir("outlines").glob("*.yaml")), key=lambda item: item.title)

    def create_chapter(self, chapter: NovelChapter) -> NovelChapter:
        return self.save_chapter(chapter)

    def save_chapter(self, chapter: NovelChapter) -> NovelChapter:
        updated = chapter.model_copy(update={"updated_at": now_iso()})
        _write_yaml(self._path("chapters", updated.chapter_id), updated)
        return updated

    def load_chapter(self, chapter_id: str) -> NovelChapter:
        return _read_yaml(self._path("chapters", chapter_id), NovelChapter)

    def list_chapters(self) -> list[NovelChapter]:
        return sorted((_read_yaml(path, NovelChapter) for path in self._dir("chapters").glob("*.yaml")), key=lambda item: (item.order_index, item.chapter_id))

    def create_scene(self, scene: NovelScene) -> NovelScene:
        return self.save_scene(scene)

    def save_scene(self, scene: NovelScene) -> NovelScene:
        updated = scene.model_copy(update={"updated_at": now_iso()})
        _write_yaml(self._path("scenes", updated.scene_id), updated)
        return updated

    def load_scene(self, scene_id: str) -> NovelScene:
        return _read_yaml(self._path("scenes", scene_id), NovelScene)

    def list_scenes(self) -> list[NovelScene]:
        return sorted((_read_yaml(path, NovelScene) for path in self._dir("scenes").glob("*.yaml")), key=lambda item: (item.chapter_id, item.scene_id))

    def save_character_arc(self, arc: CharacterArc) -> CharacterArc:
        _write_yaml(self._path("arcs", arc.arc_id), arc)
        return arc

    def list_character_arcs(self) -> list[CharacterArc]:
        return sorted((_read_yaml(path, CharacterArc) for path in self._dir("arcs").glob("*.yaml")), key=lambda item: item.arc_id)

    def save_plot_thread(self, thread: PlotThread) -> PlotThread:
        _write_yaml(self._path("plot_threads", thread.plot_thread_id), thread)
        return thread

    def list_plot_threads(self) -> list[PlotThread]:
        return sorted((_read_yaml(path, PlotThread) for path in self._dir("plot_threads").glob("*.yaml")), key=lambda item: item.plot_thread_id)

    def save_foreshadowing_item(self, item: ForeshadowingItem) -> ForeshadowingItem:
        _write_yaml(self._path("foreshadowing", item.foreshadowing_id), item)
        return item

    def list_foreshadowing(self) -> list[ForeshadowingItem]:
        return sorted((_read_yaml(path, ForeshadowingItem) for path in self._dir("foreshadowing").glob("*.yaml")), key=lambda item: item.foreshadowing_id)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "manuscripts": len(self.list_manuscripts()),
            "chapters": len(self.list_chapters()),
            "scenes": len(self.list_scenes()),
        }


class OutlineValidationReport(NovelModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OutlineService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def get_outline_tree(self, outline_id: str) -> list[dict[str, Any]]:
        outline = self.repository.load_outline(outline_id)
        by_parent: dict[str | None, list[NovelOutlineNode]] = {}
        for node in outline.nodes:
            by_parent.setdefault(node.parent_id, []).append(node)
        for values in by_parent.values():
            values.sort(key=lambda item: (item.order_index, item.node_id))

        def build(parent: str | None) -> list[dict[str, Any]]:
            return [node.model_dump(mode="json") | {"children": build(node.node_id)} for node in by_parent.get(parent, [])]

        return build(None)

    def add_outline_node(self, outline_id: str, node: NovelOutlineNode) -> NovelOutline:
        outline = self.repository.load_outline(outline_id)
        outline.nodes.append(node)
        report = self.validate_outline(outline)
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        return self.repository.save_outline(outline)

    def update_outline_node(self, outline_id: str, node_id: str, updates: dict[str, Any]) -> NovelOutline:
        outline = self.repository.load_outline(outline_id)
        nodes = [node for node in outline.nodes if node.node_id == node_id]
        if not nodes:
            raise ValueError("Outline node not found")
        node = nodes[0].model_copy(update=updates)
        outline.nodes = [node if item.node_id == node_id else item for item in outline.nodes]
        report = self.validate_outline(outline)
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        return self.repository.save_outline(outline)

    def delete_outline_node(self, outline_id: str, node_id: str) -> NovelOutline:
        outline = self.repository.load_outline(outline_id)
        child_ids = {node.node_id for node in outline.nodes if node.parent_id == node_id}
        if child_ids:
            raise ValueError("Cannot delete outline node with children")
        outline.nodes = [node for node in outline.nodes if node.node_id != node_id]
        return self.repository.save_outline(outline)

    def reorder_outline_node(self, outline_id: str, node_id: str, order_index: int) -> NovelOutline:
        return self.update_outline_node(outline_id, node_id, {"order_index": order_index})

    def validate_outline(self, outline: NovelOutline) -> OutlineValidationReport:
        errors: list[str] = []
        ids = {node.node_id for node in outline.nodes}
        for node in outline.nodes:
            if node.parent_id and node.parent_id not in ids:
                errors.append(f"parent_id not found for {node.node_id}")
        for node in outline.nodes:
            seen: set[str] = set()
            current = node
            while current.parent_id:
                if current.parent_id in seen:
                    errors.append(f"parent cycle detected at {node.node_id}")
                    break
                seen.add(current.parent_id)
                current = next((candidate for candidate in outline.nodes if candidate.node_id == current.parent_id), current)
                if current.node_id == node.node_id:
                    errors.append(f"parent cycle detected at {node.node_id}")
                    break
        return OutlineValidationReport(ok=not errors, errors=errors)


class ChapterSceneService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def create_chapter(self, chapter: NovelChapter) -> NovelChapter:
        return self.repository.create_chapter(chapter)

    def update_chapter(self, chapter_id: str, updates: dict[str, Any]) -> NovelChapter:
        chapter = self.repository.load_chapter(chapter_id).model_copy(update=updates | {"updated_at": now_iso()})
        return self.repository.save_chapter(chapter)

    def delete_chapter(self, chapter_id: str, *, cascade: bool = False) -> bool:
        scenes = self.list_scenes_for_chapter(chapter_id)
        if scenes and not cascade:
            raise ValueError("Cannot delete non-empty chapter without cascade confirmation")
        for scene in scenes:
            self._delete_scene_file(scene.scene_id)
        self.repository._path("chapters", chapter_id).unlink(missing_ok=True)
        return True

    def reorder_chapters(self, chapter_order: list[str]) -> list[NovelChapter]:
        chapters = {chapter.chapter_id: chapter for chapter in self.repository.list_chapters()}
        updated: list[NovelChapter] = []
        for index, chapter_id in enumerate(chapter_order):
            if chapter_id not in chapters:
                raise ValueError(f"Unknown chapter: {chapter_id}")
            updated.append(self.repository.save_chapter(chapters[chapter_id].model_copy(update={"order_index": index})))
        return updated

    def create_scene(self, scene: NovelScene) -> NovelScene:
        chapter = self.repository.load_chapter(scene.chapter_id)
        saved = self.repository.create_scene(scene)
        if scene.scene_id not in chapter.scene_refs:
            self.repository.save_chapter(chapter.model_copy(update={"scene_refs": chapter.scene_refs + [scene.scene_id]}))
        return saved

    def update_scene(self, scene_id: str, updates: dict[str, Any]) -> NovelScene:
        scene = self.repository.load_scene(scene_id).model_copy(update=updates | {"updated_at": now_iso()})
        return self.repository.save_scene(scene)

    def delete_scene(self, scene_id: str) -> bool:
        scene = self.repository.load_scene(scene_id)
        chapter = self.repository.load_chapter(scene.chapter_id)
        self.repository.save_chapter(chapter.model_copy(update={"scene_refs": [item for item in chapter.scene_refs if item != scene_id]}))
        self._delete_scene_file(scene_id)
        return True

    def _delete_scene_file(self, scene_id: str) -> None:
        self.repository._path("scenes", scene_id).unlink(missing_ok=True)

    def move_scene_to_chapter(self, scene_id: str, target_chapter_id: str) -> NovelScene:
        scene = self.repository.load_scene(scene_id)
        old = self.repository.load_chapter(scene.chapter_id)
        target = self.repository.load_chapter(target_chapter_id)
        self.repository.save_chapter(old.model_copy(update={"scene_refs": [item for item in old.scene_refs if item != scene_id]}))
        if scene_id not in target.scene_refs:
            self.repository.save_chapter(target.model_copy(update={"scene_refs": target.scene_refs + [scene_id]}))
        return self.repository.save_scene(scene.model_copy(update={"chapter_id": target_chapter_id}))

    def list_scenes_for_chapter(self, chapter_id: str) -> list[NovelScene]:
        return [scene for scene in self.repository.list_scenes() if scene.chapter_id == chapter_id]

    def validate_chapter_scene_refs(self) -> OutlineValidationReport:
        errors: list[str] = []
        chapter_ids = {chapter.chapter_id for chapter in self.repository.list_chapters()}
        for scene in self.repository.list_scenes():
            if scene.chapter_id not in chapter_ids:
                errors.append(f"scene without chapter: {scene.scene_id}")
        return OutlineValidationReport(ok=not errors, errors=errors)


class CharacterArcService:
    def __init__(self, repository: NovelRepository, characters: CharacterLibrary | None = None) -> None:
        self.repository = repository
        self.characters = characters

    def create_arc(self, arc: CharacterArc) -> CharacterArc:
        report = self.validate_arc(arc)
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        return self.repository.save_character_arc(arc)

    def update_arc(self, arc_id: str, updates: dict[str, Any]) -> CharacterArc:
        arc = next((item for item in self.repository.list_character_arcs() if item.arc_id == arc_id), None)
        if arc is None:
            raise ValueError("Character arc not found")
        updated = arc.model_copy(update=updates)
        report = self.validate_arc(updated)
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        return self.repository.save_character_arc(updated)

    def list_arcs_for_character(self, character_id: str) -> list[CharacterArc]:
        return [arc for arc in self.repository.list_character_arcs() if arc.character_id == character_id]

    def link_arc_to_scene(self, arc_id: str, scene_id: str) -> CharacterArc:
        arc = next((item for item in self.repository.list_character_arcs() if item.arc_id == arc_id), None)
        if arc is None:
            raise ValueError("Character arc not found")
        if scene_id not in {scene.scene_id for scene in self.repository.list_scenes()}:
            raise ValueError("Scene not found")
        if scene_id not in arc.linked_scene_ids:
            arc.linked_scene_ids.append(scene_id)
        return self.repository.save_character_arc(arc)

    def validate_arc(self, arc: CharacterArc) -> OutlineValidationReport:
        errors: list[str] = []
        if self.characters and arc.character_id not in self.characters.characters:
            errors.append("character_id not found")
        scene_ids = {scene.scene_id for scene in self.repository.list_scenes()}
        for scene_id in arc.linked_scene_ids:
            if scene_id not in scene_ids:
                errors.append(f"linked scene not found: {scene_id}")
        orders = [point.order_index for point in arc.key_turning_points]
        if orders != sorted(orders):
            errors.append("turning points must be sorted")
        return OutlineValidationReport(ok=not errors, errors=errors)


class PlotThreadService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def create_thread(self, thread: PlotThread) -> PlotThread:
        self._validate_refs(thread.linked_scene_ids)
        return self.repository.save_plot_thread(thread)

    def update_thread(self, thread_id: str, updates: dict[str, Any]) -> PlotThread:
        thread = next((item for item in self.repository.list_plot_threads() if item.plot_thread_id == thread_id), None)
        if thread is None:
            raise ValueError("Plot thread not found")
        updated = thread.model_copy(update=updates)
        self._validate_refs(updated.linked_scene_ids)
        return self.repository.save_plot_thread(updated)

    def _validate_refs(self, scene_ids: list[str]) -> None:
        existing = {scene.scene_id for scene in self.repository.list_scenes()}
        missing = [scene_id for scene_id in scene_ids if scene_id not in existing]
        if missing:
            raise ValueError(f"Missing scene refs: {', '.join(missing)}")


class ForeshadowingService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def create_item(self, item: ForeshadowingItem) -> ForeshadowingItem:
        self._validate_item(item)
        return self.repository.save_foreshadowing_item(item)

    def update_item(self, item_id: str, updates: dict[str, Any]) -> ForeshadowingItem:
        item = next((candidate for candidate in self.repository.list_foreshadowing() if candidate.foreshadowing_id == item_id), None)
        if item is None:
            raise ValueError("Foreshadowing item not found")
        updated = item.model_copy(update=updates)
        self._validate_item(updated)
        return self.repository.save_foreshadowing_item(updated)

    def _validate_item(self, item: ForeshadowingItem) -> None:
        scene_ids = {scene.scene_id for scene in self.repository.list_scenes()}
        for ref in (item.setup_scene_id, item.payoff_scene_id):
            if ref and ref not in scene_ids:
                raise ValueError(f"Missing scene ref: {ref}")


class NovelTimelineSummary(NovelModel):
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)
    hidden_events_excluded: int = 0


class NovelTimelineService:
    def __init__(self, repository: NovelRepository, timeline: TimelineLibrary, links: CrossModeLinkRegistry | None = None) -> None:
        self.repository = repository
        self.timeline = timeline
        self.links = links

    def link_scene_to_timeline_event(self, scene_id: str, timeline_event_id: str, *, create_cross_mode_link: bool = False) -> NovelScene:
        if timeline_event_id not in self.timeline.events:
            raise ValueError("Timeline event not found")
        scene = self.repository.load_scene(scene_id)
        refs = list(dict.fromkeys(scene.timeline_event_refs + [timeline_event_id]))
        updated = self.repository.save_scene(scene.model_copy(update={"timeline_event_refs": refs}))
        if create_cross_mode_link and self.links is not None:
            self.links.create_link(
                CrossModeLink(
                    link_id=f"timeline_{timeline_event_id}_{scene_id}",
                    project_id=scene.project_id,
                    source_mode="world" if self.timeline.events[timeline_event_id].event_type == "world" else "novel",
                    source_ref=f"timeline:{timeline_event_id}",
                    target_mode="novel",
                    target_ref=f"scene:{scene_id}",
                    link_type="world_event_to_novel_scene",
                )
            )
        return updated

    def unlink_scene_from_timeline_event(self, scene_id: str, timeline_event_id: str) -> NovelScene:
        scene = self.repository.load_scene(scene_id)
        return self.repository.save_scene(scene.model_copy(update={"timeline_event_refs": [item for item in scene.timeline_event_refs if item != timeline_event_id]}))

    def list_timeline_for_manuscript(self, manuscript_id: str) -> NovelTimelineSummary:
        chapters = [chapter for chapter in self.repository.list_chapters() if chapter.manuscript_id == manuscript_id]
        scene_ids = {scene_id for chapter in chapters for scene_id in chapter.scene_refs}
        events: list[dict[str, Any]] = []
        excluded = 0
        for scene in self.repository.list_scenes():
            if scene.scene_id not in scene_ids:
                continue
            for event_id in scene.timeline_event_refs:
                event = self.timeline.events.get(event_id)
                if event is None:
                    continue
                summary = event.safe_summary()
                if summary is None:
                    excluded += 1
                else:
                    events.append(summary)
        return NovelTimelineSummary(timeline_events=events, hidden_events_excluded=excluded)

    def build_novel_timeline_summary(self, manuscript_id: str) -> NovelTimelineSummary:
        return self.list_timeline_for_manuscript(manuscript_id)


class NovelWorldBibleContextRequest(NovelModel):
    project_id: str
    manuscript_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    requested_tags: list[str] = Field(default_factory=list)
    include_authoring_notes: bool = False
    view_mode: Literal["normal", "authoring", "debug", "export"] = "normal"


class ExcludedNovelContextEntry(NovelModel):
    entry_id: str
    source: str
    reason: str


class NovelWorldBibleContext(NovelModel):
    flavor_lore: list[str] = Field(default_factory=list)
    safe_structured_fact_summaries: list[dict[str, Any]] = Field(default_factory=list)
    authoring_notes: list[dict[str, str]] = Field(default_factory=list)
    excluded_entries_debug: list[ExcludedNovelContextEntry] = Field(default_factory=list)


class NovelWorldBibleContextBuilder:
    def __init__(self, world_bible: WorldBible | None = None, lore_facts: LoreFactLibrary | None = None) -> None:
        self.world_bible = world_bible
        self.lore_facts = lore_facts

    def build(self, request: NovelWorldBibleContextRequest) -> NovelWorldBibleContext:
        if request.include_authoring_notes and request.view_mode not in {"authoring", "debug"}:
            raise ValueError("authoring notes require authoring or debug view")
        tags = set(request.requested_tags)
        context = NovelWorldBibleContext()
        if self.world_bible is not None:
            for lore in self.world_bible.flavor_lore:
                if not contains_secret_text(lore):
                    context.flavor_lore.append(redact_text(lore))
            for entry in self.world_bible.entries.values():
                if tags and not tags.intersection(entry.tags):
                    continue
                if entry.entry_type == WorldBibleEntryType.HIDDEN or entry.visibility == "hidden":
                    if request.view_mode == "debug":
                        context.excluded_entries_debug.append(ExcludedNovelContextEntry(entry_id=entry.id, source="world_bible", reason="hidden"))
                    continue
                if entry.entry_type == WorldBibleEntryType.AUTHORING_NOTE or entry.visibility == "authoring_only":
                    if request.include_authoring_notes and request.view_mode in {"authoring", "debug"}:
                        context.authoring_notes.append({"entry_id": entry.id, "label": "authoring_note", "text": redact_text(entry.content)})
                    continue
                if entry.entry_type in {WorldBibleEntryType.FLAVOR, WorldBibleEntryType.STYLE_NOTE}:
                    context.flavor_lore.append(redact_text(entry.content))
                elif entry.entry_type == WorldBibleEntryType.STRUCTURED_FACT:
                    context.safe_structured_fact_summaries.append({"entry_id": entry.id, "title": entry.title, "summary": redact_text(entry.content), "tags": entry.tags})
            if self.world_bible.setting_notes_authoring_only and request.include_authoring_notes and request.view_mode in {"authoring", "debug"}:
                context.authoring_notes.append({"entry_id": self.world_bible.world_bible_id, "label": "authoring_note", "text": redact_text(self.world_bible.setting_notes_authoring_only)})
        if self.lore_facts is not None:
            for entry in self.lore_facts.entries.values():
                if tags and not tags.intersection(entry.tags):
                    continue
                if entry.fact_type == "hidden" or entry.visibility == "hidden":
                    if request.view_mode == "debug":
                        context.excluded_entries_debug.append(ExcludedNovelContextEntry(entry_id=entry.id, source="lore_fact", reason="hidden"))
                    continue
                if entry.fact_type == "authoring_note" or entry.visibility == "authoring_only":
                    if request.include_authoring_notes and request.view_mode in {"authoring", "debug"}:
                        context.authoring_notes.append({"entry_id": entry.id, "label": "authoring_note", "text": entry.safe_text()})
                    continue
                if entry.safe_for_novel:
                    target = context.safe_structured_fact_summaries if entry.fact_type == "structured" else context.flavor_lore
                    if isinstance(target, list) and entry.fact_type == "structured":
                        context.safe_structured_fact_summaries.append({"entry_id": entry.id, "title": entry.title, "summary": entry.safe_text(), "tags": entry.tags})
                    else:
                        context.flavor_lore.append(entry.safe_text())
        return context


class NovelPromptContext(NovelModel):
    project_id: str
    manuscript_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    prompt_profile_id: str | None = None
    chapter_summary: str = ""
    scene_summary: str = ""
    safe_character_summaries: list[dict[str, Any]] = Field(default_factory=list)
    safe_world_bible_context: NovelWorldBibleContext = Field(default_factory=NovelWorldBibleContext)
    safe_timeline_summary: list[dict[str, Any]] = Field(default_factory=list)
    style_instructions: str = ""

    @model_validator(mode="after")
    def validate_no_hidden_or_secrets(self) -> "NovelPromptContext":
        payload = self.model_dump_json().lower()
        if "state_delta" in payload or "api_key" in payload or contains_secret_text(payload):
            raise ValueError("NovelPromptContext contains forbidden prompt material")
        return self


class NovelPromptContextBuilder:
    def __init__(self, prompt_profiles: PromptProfileLibrary, characters: CharacterLibrary | None = None) -> None:
        self.prompt_profiles = prompt_profiles
        self.characters = characters

    def select_profile(self, profile_id: str | None) -> ProjectPromptProfile | None:
        if profile_id is None:
            profiles = self.prompt_profiles.for_mode("novel")
            return profiles[0].validate_safe() if profiles else None
        profile = self.prompt_profiles.profiles.get(profile_id)
        if profile is None or "novel" not in profile.mode_scopes:
            raise ValueError("Prompt profile is not available for novel mode")
        return profile.validate_safe()

    def build(
        self,
        *,
        manuscript: NovelManuscript,
        chapter: NovelChapter | None = None,
        scene: NovelScene | None = None,
        world_bible_context: NovelWorldBibleContext | None = None,
        timeline_summary: list[dict[str, Any]] | None = None,
    ) -> NovelPromptContext:
        profile = self.select_profile(scene.prompt_profile_id if scene and scene.prompt_profile_id else chapter.prompt_profile_id if chapter and chapter.prompt_profile_id else manuscript.default_prompt_profile_id)
        character_ids = scene.linked_character_ids if scene else chapter.linked_character_ids if chapter else manuscript.linked_character_ids
        summaries = []
        if self.characters is not None:
            summaries = [profile.safe_summary() for cid in character_ids if (profile := self.characters.get_character(cid)) is not None]
        return NovelPromptContext(
            project_id=manuscript.project_id,
            manuscript_id=manuscript.manuscript_id,
            chapter_id=chapter.chapter_id if chapter else None,
            scene_id=scene.scene_id if scene else None,
            prompt_profile_id=profile.profile_id if profile else None,
            chapter_summary=redact_text(chapter.summary if chapter else ""),
            scene_summary=redact_text(scene.summary if scene else ""),
            safe_character_summaries=summaries,
            safe_world_bible_context=world_bible_context or NovelWorldBibleContext(),
            safe_timeline_summary=timeline_summary or [],
            style_instructions=profile.novel_style if profile else manuscript.target_style,
        )


class GeneratedNovelDraft(NovelModel):
    text: str
    summary: str = ""
    used_prompt_profile_id: str | None = None
    source_context_refs: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_safe_output(self) -> "GeneratedNovelDraft":
        if contains_secret_text(self.text) or "state_delta" in self.text.lower():
            raise ValueError("Generated draft contains forbidden material")
        return self


class NovelDraftGenerationService:
    def __init__(self, provider: LLMProvider, repository: NovelRepository | None = None) -> None:
        self.provider = provider
        self.repository = repository

    def generate_scene_draft(self, context: NovelPromptContext) -> GeneratedNovelDraft:
        return self._generate("Generate a safe novel scene draft.", context)

    def rewrite_scene_style(self, context: NovelPromptContext, text: str) -> GeneratedNovelDraft:
        return self._generate(f"Rewrite this draft in the requested style:\n{redact_text(text)}", context)

    def summarize_chapter(self, context: NovelPromptContext) -> GeneratedNovelDraft:
        return self._generate("Summarize this chapter draft.", context)

    def expand_outline_node(self, context: NovelPromptContext, node_summary: str) -> GeneratedNovelDraft:
        return self._generate(f"Expand this outline node into draft prose:\n{redact_text(node_summary)}", context)

    def save_scene_draft(self, scene_id: str, draft: GeneratedNovelDraft, *, explicit_confirm: bool = False, overwrite: bool = False) -> NovelScene:
        if self.repository is None:
            raise ValueError("NovelRepository is required to save generated drafts")
        if not explicit_confirm:
            raise ValueError("explicit_confirm is required to save generated drafts")
        scene = self.repository.load_scene(scene_id)
        if scene.draft_text and not overwrite:
            raise ValueError("Refusing to overwrite existing draft_text without overwrite confirmation")
        return self.repository.save_scene(scene.model_copy(update={"draft_text": draft.text, "summary": draft.summary or scene.summary}))

    def _generate(self, instruction: str, context: NovelPromptContext) -> GeneratedNovelDraft:
        payload = context.model_dump_json()
        if contains_secret_text(payload) or "hidden fact" in payload.lower() or "state_delta" in payload.lower():
            raise ValueError("NovelPromptContext contains unsafe generation input")
        return self.provider.generate_json(
            [
                Message(role="system", content="You write novel drafts only. Do not create world facts or state changes."),
                Message(role="user", content=f"{instruction}\nContext:\n{payload}"),
            ],
            GeneratedNovelDraft,
        )


class NovelConsistencyIssue(NovelModel):
    severity: Literal["info", "warning", "error", "blocker"]
    code: str
    message: str
    ref_type: str = ""
    ref_id: str = ""
    safe_detail: str = ""


class NovelConsistencyReport(NovelModel):
    project_id: str
    manuscript_id: str | None = None
    issues: list[NovelConsistencyIssue] = Field(default_factory=list)
    status: Literal["pass", "warning", "fail"] = "pass"
    created_at: str = Field(default_factory=now_iso)


class NovelConsistencyChecker:
    def __init__(self, repository: NovelRepository, characters: CharacterLibrary | None = None, timeline: TimelineLibrary | None = None, hidden_labels: Iterable[str] = ()) -> None:
        self.repository = repository
        self.characters = characters
        self.timeline = timeline
        self.hidden_labels = {label.lower() for label in hidden_labels}

    def check(self, manuscript_id: str | None = None) -> NovelConsistencyReport:
        issues: list[NovelConsistencyIssue] = []
        chapters = [c for c in self.repository.list_chapters() if manuscript_id is None or c.manuscript_id == manuscript_id]
        orders = [chapter.order_index for chapter in chapters]
        if len(orders) != len(set(orders)):
            issues.append(NovelConsistencyIssue(severity="error", code="duplicated_chapter_order", message="Duplicate chapter order detected"))
        expected = list(range(len(chapters)))
        if sorted(orders) and sorted(orders) != expected:
            issues.append(NovelConsistencyIssue(severity="warning", code="chapter_order_gap", message="Chapter order has gaps"))
        chapter_ids = {chapter.chapter_id for chapter in chapters}
        for scene in self.repository.list_scenes():
            if scene.chapter_id not in chapter_ids:
                issues.append(NovelConsistencyIssue(severity="error", code="scene_without_chapter", message="Scene references missing chapter", ref_type="scene", ref_id=scene.scene_id))
        if self.characters:
            for chapter in chapters:
                for cid in chapter.linked_character_ids:
                    if cid not in self.characters.characters:
                        issues.append(NovelConsistencyIssue(severity="error", code="missing_character_ref", message="Linked character missing", ref_type="chapter", ref_id=chapter.chapter_id, safe_detail=cid))
        if self.timeline:
            for chapter in chapters:
                for tid in chapter.linked_timeline_event_ids:
                    if tid not in self.timeline.events:
                        issues.append(NovelConsistencyIssue(severity="error", code="missing_timeline_ref", message="Linked timeline event missing", ref_type="chapter", ref_id=chapter.chapter_id, safe_detail=tid))
        scene_order = {scene.scene_id: index for index, scene in enumerate(sorted(self.repository.list_scenes(), key=lambda s: (s.chapter_id, s.scene_id)))}
        for item in self.repository.list_foreshadowing():
            if item.status in {"planted", "reinforced"} and not item.payoff_scene_id:
                issues.append(NovelConsistencyIssue(severity="warning", code="unresolved_foreshadowing", message="Foreshadowing has no payoff", ref_type="foreshadowing", ref_id=item.foreshadowing_id))
            if item.payoff_scene_id and scene_order.get(item.payoff_scene_id, 10**9) < scene_order.get(item.setup_scene_id, -1):
                issues.append(NovelConsistencyIssue(severity="error", code="payoff_before_setup", message="Foreshadowing payoff appears before setup", ref_type="foreshadowing", ref_id=item.foreshadowing_id))
        for thread in self.repository.list_plot_threads():
            if thread.status == "abandoned" and not thread.authoring_notes:
                issues.append(NovelConsistencyIssue(severity="warning", code="abandoned_plot_thread_without_note", message="Abandoned plot thread lacks note", ref_type="plot_thread", ref_id=thread.plot_thread_id))
        for chapter in chapters:
            text = chapter.draft_text.lower()
            if chapter.authoring_notes and chapter.authoring_notes in chapter.draft_text:
                issues.append(NovelConsistencyIssue(severity="blocker", code="authoring_notes_in_export_candidate", message="Authoring notes appear in draft text", ref_type="chapter", ref_id=chapter.chapter_id))
            for label in self.hidden_labels:
                if label and label in text:
                    issues.append(NovelConsistencyIssue(severity="error", code="hidden_fact_reference", message="Hidden fact reference risk detected", ref_type="chapter", ref_id=chapter.chapter_id, safe_detail="[hidden-ref]"))
        status: Literal["pass", "warning", "fail"] = "pass"
        if any(issue.severity in {"error", "blocker"} for issue in issues):
            status = "fail"
        elif issues:
            status = "warning"
        return NovelConsistencyReport(project_id=chapters[0].project_id if chapters else "unknown", manuscript_id=manuscript_id, issues=issues, status=status)


class NovelExportRequest(NovelModel):
    manuscript_id: str
    format: Literal["markdown", "txt"] = "markdown"
    chapter_ids: list[str] = Field(default_factory=list)
    include_scenes: bool = True
    run_consistency_check: bool = True
    filename: str | None = None
    include_mature_content: bool = False


class NovelExportResult(NovelModel):
    export_id: str
    format: str
    path: str
    chapters_exported: list[str]
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class NovelExportService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def export(self, request: NovelExportRequest) -> NovelExportResult:
        manuscript = self.repository.load_manuscript(request.manuscript_id)
        chapters = [
            chapter
            for chapter in self.repository.list_chapters()
            if (chapter.manuscript_id == manuscript.manuscript_id or not chapter.manuscript_id)
            and chapter.visibility == "normal"
        ]
        if request.chapter_ids:
            wanted = set(request.chapter_ids)
            chapters = [chapter for chapter in chapters if chapter.chapter_id in wanted]
        if request.run_consistency_check:
            report = NovelConsistencyChecker(self.repository).check(manuscript.manuscript_id)
            if any(issue.severity == "blocker" for issue in report.issues):
                raise ValueError("Consistency blocker prevents export")
        rendered = self._render(manuscript, chapters, request.format, request.include_scenes)
        filtered = MatureExportFilter().filter_text(
            rendered,
            MatureExportPolicy(
                include_mature_content=request.include_mature_content,
                include_mature_memory=request.include_mature_content,
            ),
        )
        if filtered is None:
            raise ValueError("Novel export contains forbidden content")
        rendered = filtered
        if contains_secret_text(rendered) or "state_delta" in rendered.lower():
            raise ValueError("Novel export contains forbidden content")
        filename = request.filename or f"{manuscript.manuscript_id}.{ 'md' if request.format == 'markdown' else 'txt'}"
        safe_name = validate_relative_package_path(filename)
        if "/" in safe_name:
            raise ValueError("Export filename must not contain directories")
        path = self.repository._dir("exports") / safe_name
        path.write_text(rendered, encoding="utf-8")
        return NovelExportResult(export_id=Path(filename).stem, format=request.format, path=str(path), chapters_exported=[chapter.chapter_id for chapter in chapters])

    def _render(self, manuscript: NovelManuscript, chapters: list[NovelChapter], fmt: str, include_scenes: bool) -> str:
        if fmt == "markdown":
            lines = [f"# {manuscript.title}", ""]
            for chapter in chapters:
                lines.extend([f"## {chapter.title}", "", redact_text(chapter.draft_text), ""])
                if include_scenes:
                    for scene in self.repository.list_scenes():
                        if scene.chapter_id == chapter.chapter_id and scene.visibility == "normal":
                            lines.extend([f"### {scene.title}", "", redact_text(scene.draft_text), ""])
            return "\n".join(lines)
        lines = [manuscript.title, "=" * len(manuscript.title), ""]
        for chapter in chapters:
            lines.extend([chapter.title, "-" * len(chapter.title), redact_text(chapter.draft_text), ""])
            if include_scenes:
                for scene in self.repository.list_scenes():
                    if scene.chapter_id == chapter.chapter_id and scene.visibility == "normal":
                        lines.extend([scene.title, redact_text(scene.draft_text), ""])
        return "\n".join(lines)


class NovelDraftSnapshot(NovelModel):
    snapshot_id: str
    project_id: str = "local_project"
    manuscript_id: str | None = None
    target_type: Literal["chapter", "scene"]
    target_id: str
    title: str = ""
    draft_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)

    @field_validator("snapshot_id", "target_id")
    @classmethod
    def validate_snapshot_ids(cls, value: str) -> str:
        return _ensure_safe_id(value)

    @model_validator(mode="after")
    def validate_snapshot_safe(self) -> "NovelDraftSnapshot":
        payload = json.dumps({"text": self.draft_text, "metadata": self.metadata}, sort_keys=True)
        lowered = payload.lower()
        if contains_secret_text(payload) or "hidden fact" in lowered or "state_delta" in lowered or "raw_prompt" in lowered:
            raise ValueError("NovelDraftSnapshot contains forbidden context")
        return self


class DraftVersionCompareResult(NovelModel):
    left_snapshot_id: str | None = None
    right_snapshot_id: str | None = None
    changed: bool
    added_lines: int = 0
    removed_lines: int = 0
    safe_summary: str


class DraftVersionService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def _path(self, snapshot_id: str) -> Path:
        return self.repository._path("draft_snapshots", snapshot_id)

    def create_snapshot(
        self,
        *,
        target_type: Literal["chapter", "scene"],
        target_id: str,
        snapshot_id: str | None = None,
        title: str | None = None,
    ) -> NovelDraftSnapshot:
        if target_type == "chapter":
            target = self.repository.load_chapter(target_id)
            if target.visibility != "normal":
                raise ValueError("Draft snapshots are available only for normal visible Novel drafts")
            draft_text = target.draft_text
            manuscript_id = target.manuscript_id
            title = title or target.title
            project_id = target.project_id
        else:
            target = self.repository.load_scene(target_id)
            if target.visibility != "normal":
                raise ValueError("Draft snapshots are available only for normal visible Novel drafts")
            draft_text = target.draft_text
            manuscript_id = None
            title = title or target.title
            project_id = target.project_id
        sid = snapshot_id or f"{target_type}_{target_id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        snapshot = NovelDraftSnapshot(
            snapshot_id=sid,
            project_id=project_id,
            manuscript_id=manuscript_id,
            target_type=target_type,
            target_id=target_id,
            title=title or "",
            draft_text=draft_text,
            metadata={"source": "user_draft_snapshot"},
        )
        _write_yaml(self._path(snapshot.snapshot_id), snapshot)
        return snapshot

    def list_snapshots(self, target_id: str | None = None) -> list[NovelDraftSnapshot]:
        snapshots = [_read_yaml(path, NovelDraftSnapshot) for path in self.repository._dir("draft_snapshots").glob("*.yaml")]
        if target_id:
            snapshots = [snapshot for snapshot in snapshots if snapshot.target_id == target_id]
        return sorted(snapshots, key=lambda item: item.created_at, reverse=True)

    def load_snapshot(self, snapshot_id: str) -> NovelDraftSnapshot:
        return _read_yaml(self._path(snapshot_id), NovelDraftSnapshot)

    def compare_snapshots(self, left: str | None, right: str | None = None, *, current_text: str | None = None) -> DraftVersionCompareResult:
        left_text = self.load_snapshot(left).draft_text if left else ""
        right_text = self.load_snapshot(right).draft_text if right else current_text or ""
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()
        added = max(0, len(right_lines) - len(left_lines))
        removed = max(0, len(left_lines) - len(right_lines))
        changed = left_text != right_text
        return DraftVersionCompareResult(
            left_snapshot_id=left,
            right_snapshot_id=right,
            changed=changed,
            added_lines=added,
            removed_lines=removed,
            safe_summary="Draft text changed." if changed else "No draft text changes.",
        )

    def restore_snapshot_confirmed(self, snapshot_id: str, *, explicit_confirm: bool = False, overwrite: bool = False) -> NovelChapter | NovelScene:
        if not explicit_confirm:
            raise ValueError("explicit_confirm is required")
        snapshot = self.load_snapshot(snapshot_id)
        if snapshot.target_type == "chapter":
            chapter = self.repository.load_chapter(snapshot.target_id)
            if chapter.draft_text and not overwrite:
                raise ValueError("Refusing to overwrite existing chapter draft without overwrite confirmation")
            return self.repository.save_chapter(chapter.model_copy(update={"draft_text": snapshot.draft_text}))
        scene = self.repository.load_scene(snapshot.target_id)
        if scene.draft_text and not overwrite:
            raise ValueError("Refusing to overwrite existing scene draft without overwrite confirmation")
        return self.repository.save_scene(scene.model_copy(update={"draft_text": snapshot.draft_text}))


class WritingSessionState(NovelModel):
    session_id: str
    project_id: str
    manuscript_id: str
    started_at: str = Field(default_factory=now_iso)
    ended_at: str | None = None
    active_chapter_id: str | None = None
    active_scene_id: str | None = None
    word_count_start: int = 0
    word_count_current: int = 0
    local_goal_words: int | None = None
    notes: str = ""

    @field_validator("session_id", "project_id", "manuscript_id")
    @classmethod
    def validate_session_ids(cls, value: str) -> str:
        return _ensure_safe_id(value)

    @model_validator(mode="after")
    def validate_session_safe(self) -> "WritingSessionState":
        if contains_secret_text(self.notes) or "hidden fact" in self.notes.lower():
            raise ValueError("WritingSessionState notes contain forbidden content")
        return self


class WritingSessionService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def _path(self, session_id: str) -> Path:
        return self.repository._path("writing_sessions", session_id)

    def start_session(
        self,
        *,
        session_id: str,
        manuscript_id: str,
        active_chapter_id: str | None = None,
        active_scene_id: str | None = None,
        local_goal_words: int | None = None,
    ) -> WritingSessionState:
        manuscript = self.repository.load_manuscript(manuscript_id)
        start_count = _word_count_for_manuscript(self.repository, manuscript_id)
        session = WritingSessionState(
            session_id=session_id,
            project_id=manuscript.project_id,
            manuscript_id=manuscript_id,
            active_chapter_id=active_chapter_id,
            active_scene_id=active_scene_id,
            word_count_start=start_count,
            word_count_current=start_count,
            local_goal_words=local_goal_words,
        )
        _write_yaml(self._path(session.session_id), session)
        return session

    def update_session_stats(self, session_id: str, **updates: Any) -> WritingSessionState:
        session = self.get_session(session_id)
        current = _word_count_for_manuscript(self.repository, session.manuscript_id)
        updated = session.model_copy(update={"word_count_current": current} | updates)
        _write_yaml(self._path(session_id), updated)
        return updated

    def end_session(self, session_id: str) -> WritingSessionState:
        return self.update_session_stats(session_id, ended_at=now_iso())

    def get_session(self, session_id: str) -> WritingSessionState:
        return _read_yaml(self._path(session_id), WritingSessionState)

    def get_current_session(self, manuscript_id: str | None = None) -> WritingSessionState | None:
        sessions = [_read_yaml(path, WritingSessionState) for path in self.repository._dir("writing_sessions").glob("*.yaml")]
        open_sessions = [session for session in sessions if session.ended_at is None and (manuscript_id is None or session.manuscript_id == manuscript_id)]
        return sorted(open_sessions, key=lambda item: item.started_at, reverse=True)[0] if open_sessions else None


class NovelSearchResult(NovelModel):
    result_type: Literal["chapter", "scene", "plot_thread", "foreshadowing", "character_arc"]
    result_id: str
    title: str
    status: str = ""
    safe_summary: str = ""
    tags: list[str] = Field(default_factory=list)


class NovelSearchService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def search(
        self,
        *,
        keyword: str = "",
        tag: str = "",
        status: str = "",
        character_id: str = "",
        chapter_id: str = "",
        include_authoring: bool = False,
    ) -> list[NovelSearchResult]:
        lowered = keyword.lower().strip()
        results: list[NovelSearchResult] = []
        for chapter in self.repository.list_chapters():
            if chapter.visibility != "normal":
                continue
            if status and chapter.status.value != status:
                continue
            if character_id and character_id not in chapter.linked_character_ids:
                continue
            haystack = " ".join([chapter.title, chapter.summary, chapter.draft_text if chapter.visibility == "normal" else ""]).lower()
            if lowered and lowered not in haystack:
                continue
            results.append(NovelSearchResult(result_type="chapter", result_id=chapter.chapter_id, title=chapter.title, status=chapter.status.value, safe_summary=redact_text(chapter.summary)))
        for scene in self.repository.list_scenes():
            if scene.visibility != "normal":
                continue
            if chapter_id and scene.chapter_id != chapter_id:
                continue
            if status and scene.status.value != status:
                continue
            if character_id and character_id not in scene.linked_character_ids and character_id != (scene.pov_character_id or ""):
                continue
            haystack = " ".join([scene.title, scene.summary, scene.draft_text if scene.visibility == "normal" else ""]).lower()
            if lowered and lowered not in haystack:
                continue
            results.append(NovelSearchResult(result_type="scene", result_id=scene.scene_id, title=scene.title, status=scene.status.value, safe_summary=redact_text(scene.summary)))
        for thread in self.repository.list_plot_threads():
            if status and thread.status != status:
                continue
            if character_id and character_id not in thread.linked_character_ids:
                continue
            if chapter_id and chapter_id not in thread.linked_chapter_ids:
                continue
            haystack = " ".join([thread.title, thread.description, thread.authoring_notes if include_authoring else ""]).lower()
            if lowered and lowered not in haystack:
                continue
            results.append(NovelSearchResult(result_type="plot_thread", result_id=thread.plot_thread_id, title=thread.title, status=thread.status, safe_summary=redact_text(thread.description)))
        for item in self.repository.list_foreshadowing():
            if status and item.status != status:
                continue
            if chapter_id and item.setup_scene_id != chapter_id and item.payoff_scene_id != chapter_id:
                continue
            haystack = item.hint_text.lower() if item.visibility == "normal" else ""
            if lowered and lowered not in haystack:
                continue
            results.append(NovelSearchResult(result_type="foreshadowing", result_id=item.foreshadowing_id, title=item.foreshadowing_id, status=item.status, safe_summary=redact_text(item.safe_summary().get("hint_text", ""))))
        for arc in self.repository.list_character_arcs():
            if status and arc.status.value != status:
                continue
            if character_id and arc.character_id != character_id:
                continue
            haystack = " ".join([arc.title, arc.premise, arc.start_state, arc.end_state, arc.authoring_notes if include_authoring else ""]).lower()
            if lowered and lowered not in haystack:
                continue
            results.append(NovelSearchResult(result_type="character_arc", result_id=arc.arc_id, title=arc.title, status=arc.status.value, safe_summary=redact_text(arc.premise)))
        if tag:
            results = [result for result in results if tag in result.tags]
        return results


class NovelPreferences(NovelModel):
    project_id: str
    default_manuscript_id: str | None = None
    default_export_format: Literal["markdown", "txt"] = "markdown"
    show_word_count: bool = True
    show_world_bible_sidebar: bool = True
    show_timeline_panel: bool = True
    autosave_reminder_enabled: bool = True
    default_prompt_profile_id: str | None = None
    updated_at: str = Field(default_factory=now_iso)

    @model_validator(mode="after")
    def validate_preferences_safe(self) -> "NovelPreferences":
        payload = self.model_dump_json()
        if contains_secret_text(payload) or "hidden fact" in payload.lower():
            raise ValueError("NovelPreferences contain forbidden content")
        return self


class NovelPreferencesService:
    def __init__(self, repository: NovelRepository) -> None:
        self.repository = repository

    def load_preferences(self, project_id: str) -> NovelPreferences:
        path = self.repository._dir("preferences") / "novel_preferences.yaml"
        if not path.exists():
            return NovelPreferences(project_id=project_id)
        return _read_yaml(path, NovelPreferences)

    def save_preferences(self, preferences: NovelPreferences) -> NovelPreferences:
        updated = preferences.model_copy(update={"updated_at": now_iso()})
        _write_yaml(self.repository._dir("preferences") / "novel_preferences.yaml", updated)
        return updated


def _word_count_for_manuscript(repository: NovelRepository, manuscript_id: str) -> int:
    chapters = [chapter for chapter in repository.list_chapters() if chapter.manuscript_id == manuscript_id]
    scenes = repository.list_scenes()
    text = " ".join(chapter.draft_text for chapter in chapters)
    chapter_ids = {chapter.chapter_id for chapter in chapters}
    text += " " + " ".join(scene.draft_text for scene in scenes if scene.chapter_id in chapter_ids and scene.visibility == "normal")
    return len([part for part in text.split() if part.strip()])


class WorldContentDraft(NovelModel):
    draft_id: str
    source_novel_ref: str
    draft_type: Literal["npc", "location", "quest", "fact", "item", "faction", "timeline_event"]
    proposed_content: dict[str, Any]
    validation_status: Literal["draft", "valid", "warning", "invalid"] = "draft"
    warnings: list[str] = Field(default_factory=list)
    linked_cross_mode_link_id: str | None = None
    created_at: str = Field(default_factory=now_iso)


class NovelToWorldDraftService:
    def __init__(self, repository: NovelRepository, links: CrossModeLinkRegistry | None = None) -> None:
        self.repository = repository
        self.links = links

    def convert_character_ref(self, character_id: str, *, project_id: str = "local_project", create_link: bool = False) -> WorldContentDraft:
        draft = WorldContentDraft(draft_id=f"npc_{character_id}", source_novel_ref=f"character:{character_id}", draft_type="npc", proposed_content={"npc_id": character_id, "name": character_id, "description": "Draft NPC candidate"}, validation_status="warning", warnings=["Requires NPC schema validation"])
        if create_link and self.links is not None:
            link_id = f"novel_character_{character_id}_npc"
            self.links.create_link(CrossModeLink(link_id=link_id, project_id=project_id, source_mode="novel", source_ref=f"character:{character_id}", target_mode="world", target_ref=f"npc:{character_id}", link_type="character_profile_to_world_npc"))
            draft.linked_cross_mode_link_id = link_id
        return draft

    def convert_plot_thread(self, thread: PlotThread) -> WorldContentDraft:
        return WorldContentDraft(draft_id=f"quest_{thread.plot_thread_id}", source_novel_ref=f"plot_thread:{thread.plot_thread_id}", draft_type="quest", proposed_content={"quest_id": thread.plot_thread_id, "title": thread.title, "summary": redact_text(thread.description)}, validation_status="warning", warnings=["Requires quest schema validation"])


class ChapterDraftImportProposal(NovelModel):
    source_event_ids: list[str]
    safe_event_summaries: list[str]
    suggested_chapter_title: str
    draft_summary: str
    draft_text: str | None = None
    hidden_events_excluded_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class EventLogToNovelDraftService:
    def __init__(self, repository: NovelRepository, generation_service: NovelDraftGenerationService | None = None) -> None:
        self.repository = repository
        self.generation_service = generation_service

    def preview_import(self, event_log: EventLog, *, turn_start: int, turn_end: int) -> ChapterDraftImportProposal:
        summaries: list[str] = []
        source_ids: list[str] = []
        excluded = 0
        for event in event_log.list_events():
            if event.turn < turn_start or event.turn > turn_end:
                continue
            summary = self._safe_event_summary(event)
            if summary is None:
                excluded += 1
                continue
            summaries.append(summary)
            source_ids.append(event.event_id)
        return ChapterDraftImportProposal(
            source_event_ids=source_ids,
            safe_event_summaries=summaries,
            suggested_chapter_title=f"Turns {turn_start}-{turn_end}",
            draft_summary=" ".join(summaries[:3]),
            draft_text="\n\n".join(summaries) if summaries else None,
            hidden_events_excluded_count=excluded,
        )

    def apply_import(self, proposal: ChapterDraftImportProposal, target_chapter_id: str, *, explicit_confirm: bool = False, overwrite: bool = False) -> NovelChapter:
        if not explicit_confirm:
            raise ValueError("explicit_confirm is required")
        chapter = self.repository.load_chapter(target_chapter_id)
        if chapter.draft_text and not overwrite:
            raise ValueError("Refusing to overwrite existing chapter draft")
        return self.repository.save_chapter(chapter.model_copy(update={"draft_text": proposal.draft_text or "", "summary": proposal.draft_summary}))

    def _safe_event_summary(self, event: Event) -> str | None:
        if not event.visible_to_player:
            return None
        text = event.visible_summary or event.narrative_text or event.result
        if contains_secret_text(text) or "state_delta" in text.lower():
            return None
        return redact_text(text)


class NovelQualityEvalCase(NovelModel):
    case_id: str
    project_id: str
    manuscript_id: str
    chapter_ids: list[str] = Field(default_factory=list)
    enabled_rules: list[str] = Field(default_factory=list)


class NovelQualityReport(NovelConsistencyReport):
    case_id: str | None = None


class NovelQualityEvaluator:
    def __init__(self, checker: NovelConsistencyChecker) -> None:
        self.checker = checker

    def run(self, case: NovelQualityEvalCase) -> NovelQualityReport:
        report = self.checker.check(case.manuscript_id)
        issues = list(report.issues)
        chapters = [chapter for chapter in self.checker.repository.list_chapters() if not case.chapter_ids or chapter.chapter_id in case.chapter_ids]
        seen_orders: set[int] = set()
        for chapter in chapters:
            if not chapter.title.strip():
                issues.append(NovelConsistencyIssue(severity="warning", code="missing_chapter_title", message="Chapter title is missing", ref_type="chapter", ref_id=chapter.chapter_id))
            if not chapter.draft_text.strip():
                issues.append(NovelConsistencyIssue(severity="warning", code="empty_draft", message="Chapter draft is empty", ref_type="chapter", ref_id=chapter.chapter_id))
            if chapter.order_index in seen_orders:
                issues.append(NovelConsistencyIssue(severity="error", code="duplicated_chapter_order", message="Duplicate chapter order", ref_type="chapter", ref_id=chapter.chapter_id))
            seen_orders.add(chapter.order_index)
        status: Literal["pass", "warning", "fail"] = "pass"
        if any(issue.severity in {"error", "blocker"} for issue in issues):
            status = "fail"
        elif issues:
            status = "warning"
        return NovelQualityReport(project_id=case.project_id, manuscript_id=case.manuscript_id, case_id=case.case_id, issues=issues, status=status)


def get_novel_repository_for_project(project_id: str, project_repository: ProjectRepository) -> NovelRepository:
    project = project_repository.load_project(project_id)
    return NovelRepository(project.project_root)
