from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory, mkdtemp
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES, LIST_FILE_KEYS, ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.engine.content.world_branching import WorldBranchService, _read_yaml_mapping, _stable_hash


class ContentDiffKind(StrEnum):
    FILE = "file_diff"
    ENTITY = "entity_diff"
    GRAPH = "graph_diff"
    PACKAGE = "package_diff"
    SCHEMA = "schema_diff"
    VISIBILITY = "visibility_diff"
    RP_PROFILE = "rp_profile_diff"


class ContentDiffRef(BaseModel):
    world_id: str | None = None
    branch_id: str | None = None
    files: dict[str, str] = Field(default_factory=dict)


class ContentDiffEntity(BaseModel):
    file_name: str
    entity_id: str
    entity_type: str
    diff_type: ContentDiffKind
    summary: str


class ContentDiffReview(BaseModel):
    local_only: bool = True
    normal_view: bool = True
    diff_types: list[ContentDiffKind] = Field(default_factory=list)
    added: list[ContentDiffEntity] = Field(default_factory=list)
    removed: list[ContentDiffEntity] = Field(default_factory=list)
    changed: list[ContentDiffEntity] = Field(default_factory=list)
    renamed_candidates: list[str] = Field(default_factory=list)
    visibility_risk: list[str] = Field(default_factory=list)
    migration_impact: list[str] = Field(default_factory=list)
    validation_issues: list[str] = Field(default_factory=list)


class ContentDiffReviewRequest(BaseModel):
    base: ContentDiffRef
    proposed: ContentDiffRef
    diff_types: list[ContentDiffKind] = Field(default_factory=lambda: [ContentDiffKind.FILE, ContentDiffKind.ENTITY])
    normal_view: bool = True


class ContentDiffReviewService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)
        self.authoring = ContentAuthoringService(self.worlds_root)
        self.branches = WorldBranchService(self.worlds_root)

    def review(self, request: ContentDiffReviewRequest) -> ContentDiffReview:
        cleanup_roots: list[Path] = []
        try:
            base_path, base_world_id, base_cleanup = self._materialize_ref(request.base, "base")
            proposed_path, proposed_world_id, proposed_cleanup = self._materialize_ref(request.proposed, base_world_id or "proposed")
            cleanup_roots.extend([path for path in (base_cleanup, proposed_cleanup) if path is not None])
            review = ContentDiffReview(normal_view=request.normal_view, diff_types=request.diff_types)
            for file_name in ALLOWED_AUTHORING_FILES:
                key = LIST_FILE_KEYS.get(file_name)
                if key is None:
                    continue
                base_items = _items_by_id(file_name, _read_yaml_mapping(base_path / file_name))
                proposed_items = _items_by_id(file_name, _read_yaml_mapping(proposed_path / file_name))
                entity_type = key.removesuffix("s")
                base_ids = set(base_items)
                proposed_ids = set(proposed_items)
                for entity_id in sorted(proposed_ids - base_ids):
                    review.added.append(_entity(file_name, entity_id, entity_type, base_items.get(entity_id), proposed_items[entity_id]))
                for entity_id in sorted(base_ids - proposed_ids):
                    review.removed.append(_entity(file_name, entity_id, entity_type, base_items[entity_id], None))
                    review.migration_impact.append(f"{file_name}:{entity_id}: removed entity may affect saves or references")
                for entity_id in sorted(base_ids & proposed_ids):
                    before = base_items[entity_id]
                    after = proposed_items[entity_id]
                    if _stable_hash(before) == _stable_hash(after):
                        continue
                    kind = _diff_kind(file_name, before, after)
                    review.changed.append(_entity(file_name, entity_id, entity_type, before, after, kind=kind))
                    if _visibility(before) != _visibility(after):
                        review.visibility_risk.append(f"{file_name}:{entity_id}: visibility changed {_visibility(before)} -> {_visibility(after)}")
                    if file_name == "npcs.yaml" and _stable_hash(before.get("rp_profile")) != _stable_hash(after.get("rp_profile")):
                        review.visibility_risk.extend(_rp_hidden_risks(file_name, entity_id, after))
                removed = sorted(base_ids - proposed_ids)
                added = sorted(proposed_ids - base_ids)
                if len(removed) == 1 and len(added) == 1:
                    review.renamed_candidates.append(f"{file_name}:{removed[0]} -> {added[0]}")
            validation = validate_world_pack(proposed_world_id, worlds_root=proposed_path.parent)
            review.validation_issues = _validation_issue_summaries(validation)
            review.visibility_risk.extend(_visibility_issue_summaries(validation))
            review.visibility_risk = sorted(set(review.visibility_risk))
            review.migration_impact = sorted(set(review.migration_impact))
            return review
        finally:
            for root in cleanup_roots:
                rmtree(root, ignore_errors=True)

    def _materialize_ref(self, ref: ContentDiffRef, fallback_world_id: str) -> tuple[Path, str, Path | None]:
        if ref.files:
            world_id = ref.world_id or fallback_world_id
            if not _safe_id(world_id):
                raise ValueError(f"Invalid world id: {world_id}")
            base_world = self.authoring._safe_world_path(world_id) if ref.world_id else None
            tmpdir = Path(mkdtemp())
            root = tmpdir / "worlds"
            world_path = root / world_id
            if base_world:
                from shutil import copytree

                copytree(base_world, world_path)
            else:
                world_path.mkdir(parents=True)
            for file_name, content in ref.files.items():
                if file_name not in ALLOWED_AUTHORING_FILES or Path(file_name).name != file_name:
                    raise ValueError(f"File is not authoring-allowed: {file_name}")
                yaml.safe_load(content)
                (world_path / file_name).write_text(content, encoding="utf-8")
            return world_path, world_id, tmpdir
        if ref.world_id and ref.branch_id:
            return self.branches._resolve_world_or_branch_path(ref.world_id, ref.branch_id), ref.world_id, None
        if ref.world_id:
            return self.authoring._safe_world_path(ref.world_id), ref.world_id, None
        raise ValueError("Content diff ref requires world_id or files.")


def _items_by_id(file_name: str, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    key = LIST_FILE_KEYS.get(file_name)
    values = data.get(key, []) if key else []
    if not isinstance(values, list):
        return {}
    return {str(item["id"]): dict(item) for item in values if isinstance(item, dict) and item.get("id") is not None}


def _entity(file_name: str, entity_id: str, entity_type: str, before: dict[str, Any] | None, after: dict[str, Any] | None, *, kind: ContentDiffKind = ContentDiffKind.ENTITY) -> ContentDiffEntity:
    return ContentDiffEntity(file_name=file_name, entity_id=entity_id, entity_type=entity_type, diff_type=kind, summary=_safe_summary(before, after))


def _safe_summary(before: dict[str, Any] | None, after: dict[str, Any] | None) -> str:
    current = after or before or {}
    visibility = _visibility(current)
    if visibility in {"hidden", "discoverable"}:
        return f"{current.get('id') or 'entity'} ({visibility}, details redacted)"
    name = str(current.get("name") or current.get("title") or current.get("id") or "entity")
    return f"{name} ({visibility})"


def _diff_kind(file_name: str, before: dict[str, Any], after: dict[str, Any]) -> ContentDiffKind:
    if _visibility(before) != _visibility(after):
        return ContentDiffKind.VISIBILITY
    if file_name in {"locations.yaml", "quests.yaml", "relationships.yaml"}:
        return ContentDiffKind.GRAPH
    if file_name == "npcs.yaml" and _stable_hash(before.get("rp_profile")) != _stable_hash(after.get("rp_profile")):
        return ContentDiffKind.RP_PROFILE
    return ContentDiffKind.ENTITY


def _visibility(value: dict[str, Any] | None) -> str:
    if value is None:
        return "removed"
    if bool(value.get("hidden")):
        return "hidden"
    return str(value.get("visibility", "public"))


def _rp_hidden_risks(file_name: str, entity_id: str, value: dict[str, Any]) -> list[str]:
    profile = value.get("rp_profile")
    if isinstance(profile, dict) and profile.get("private_self_summary"):
        return [f"{file_name}:{entity_id}: RP profile has private fields; normal diff redacts details"]
    return []


def _validation_issue_summaries(report: ValidationReport) -> list[str]:
    return [f"{issue.file}:{issue.path}:{issue.code}" for issue in [*report.errors, *report.warnings]]


def _visibility_issue_summaries(report: ValidationReport) -> list[str]:
    return [
        f"{issue.file}:{issue.path}:{issue.code}"
        for issue in [*report.errors, *report.warnings]
        if "hidden" in issue.message.lower() or "visibility" in issue.code or "leak" in issue.code
    ]


def _safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)
