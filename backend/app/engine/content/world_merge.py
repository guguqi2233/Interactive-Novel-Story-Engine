from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES, LIST_FILE_KEYS, ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGateRequest,
)
from app.engine.content.world_branching import WorldBranchService, _read_yaml_mapping, _stable_hash


class MergeConflictType(StrEnum):
    SAME_ENTITY_CHANGED = "same_entity_changed"
    DELETED_CHANGED = "entity_deleted_in_one_branch_changed_in_another"
    ID_COLLISION = "id_collision"
    HIDDEN_VISIBILITY_MISMATCH = "hidden_visibility_mismatch"
    QUEST_GRAPH_CONFLICT = "quest_graph_conflict"
    RELATIONSHIP_CONFLICT = "relationship_conflict"
    RP_PROFILE_CONFLICT = "rp_profile_conflict"


class MergeResolutionChoice(StrEnum):
    BASE = "base"
    OURS = "ours"
    THEIRS = "theirs"
    CUSTOM = "custom"


class MergeConflict(BaseModel):
    conflict_id: str
    conflict_type: MergeConflictType
    file_name: str
    entity_id: str
    message: str
    base: dict[str, Any] | None = None
    ours: dict[str, Any] | None = None
    theirs: dict[str, Any] | None = None
    raw_base: dict[str, Any] | None = Field(default=None, exclude=True)
    raw_ours: dict[str, Any] | None = Field(default=None, exclude=True)
    raw_theirs: dict[str, Any] | None = Field(default=None, exclude=True)


class MergeResolution(BaseModel):
    conflict_id: str
    choice: MergeResolutionChoice = MergeResolutionChoice.BASE
    custom: dict[str, Any] | None = None


class WorldMergeDraft(BaseModel):
    world_id: str
    ours: str
    theirs: str
    conflicts: list[MergeConflict] = Field(default_factory=list)
    resolutions: list[MergeResolution] = Field(default_factory=list)
    proposed_files: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    writes_to_disk: bool = False
    saved: bool = False


class WorldMergePreviewRequest(BaseModel):
    ours: str
    theirs: str
    resolutions: list[MergeResolution] = Field(default_factory=list)


class WorldMergeSaveRequest(WorldMergePreviewRequest):
    confirm_save: bool = False
    confirm_warnings: bool = False


class WorldMergeService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)
        self.authoring = ContentAuthoringService(self.worlds_root)
        self.branches = WorldBranchService(self.worlds_root)

    def preview_merge(self, world_id: str, request: WorldMergePreviewRequest) -> WorldMergeDraft:
        base_path = self.authoring._safe_world_path(world_id)
        ours_path = self.branches._resolve_world_or_branch_path(world_id, request.ours)
        theirs_path = self.branches._resolve_world_or_branch_path(world_id, request.theirs)
        conflicts: list[MergeConflict] = []
        proposed_files: dict[str, str] = {}
        resolution_map = {resolution.conflict_id: resolution for resolution in request.resolutions}
        for file_name in ALLOWED_AUTHORING_FILES:
            key = LIST_FILE_KEYS.get(file_name)
            if key is None:
                continue
            base_items = _items_by_id(file_name, _read_yaml_mapping(base_path / file_name))
            ours_items = _items_by_id(file_name, _read_yaml_mapping(ours_path / file_name))
            theirs_items = _items_by_id(file_name, _read_yaml_mapping(theirs_path / file_name))
            merged = dict(base_items)
            for entity_id in sorted(set(base_items) | set(ours_items) | set(theirs_items)):
                base = base_items.get(entity_id)
                ours = ours_items.get(entity_id)
                theirs = theirs_items.get(entity_id)
                conflict = _detect_conflict(file_name, entity_id, base, ours, theirs)
                if conflict:
                    conflicts.append(conflict)
                    chosen = _resolve_conflict(conflict, resolution_map.get(conflict.conflict_id))
                else:
                    chosen = _auto_merge_entity(base, ours, theirs)
                if chosen is None:
                    merged.pop(entity_id, None)
                else:
                    merged[entity_id] = chosen
            proposed_files[file_name] = yaml.safe_dump({key: list(merged.values())}, sort_keys=False, allow_unicode=True)
        validation = self._validate_merge_draft(world_id, proposed_files)
        unresolved = [conflict for conflict in conflicts if conflict.conflict_id not in resolution_map]
        for conflict in unresolved:
            validation.add(
                ValidationSeverity.WARNING,
                conflict.file_name,
                f"Merge conflict is unresolved and currently uses base version: {conflict.entity_id}",
                code=f"merge_{conflict.conflict_type.value}",
                ref_id=conflict.entity_id,
            )
        return WorldMergeDraft(
            world_id=world_id,
            ours=request.ours,
            theirs=request.theirs,
            conflicts=conflicts,
            resolutions=request.resolutions,
            proposed_files=proposed_files,
            validation=validation,
            writes_to_disk=False,
            saved=False,
        )

    def save_merge(self, world_id: str, request: WorldMergeSaveRequest) -> WorldMergeDraft:
        draft = self.preview_merge(world_id, request)
        if not request.confirm_save:
            draft.validation.add(
                ValidationSeverity.ERROR,
                "world_merge",
                "Merge save requires explicit confirmation.",
                code="merge_save_requires_confirmation",
            )
            return draft
        if not draft.validation.ok or (draft.validation.warnings and not request.confirm_warnings):
            return draft
        gate = self.authoring.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.MERGE,
                draft_content=draft.proposed_files,
                affected_files=list(draft.proposed_files),
                validation_report=draft.validation,
                confirm_warnings=request.confirm_warnings,
            )
        )
        draft.validation = gate.validation_report
        if not gate.allowed_to_save:
            return draft
        report = self.authoring.write_files(world_id, draft.proposed_files, confirm_warnings=request.confirm_warnings)
        draft.validation = report
        draft.writes_to_disk = report.ok
        draft.saved = report.ok
        return draft

    def _validate_merge_draft(self, world_id: str, proposed_files: dict[str, str]) -> ValidationReport:
        with TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir) / "worlds"
            from shutil import copytree

            copytree(self.authoring._safe_world_path(world_id), temp_root / world_id)
            for file_name, content in proposed_files.items():
                (temp_root / world_id / file_name).write_text(content, encoding="utf-8")
            return validate_world_pack(world_id, worlds_root=temp_root)


def _detect_conflict(
    file_name: str,
    entity_id: str,
    base: dict[str, Any] | None,
    ours: dict[str, Any] | None,
    theirs: dict[str, Any] | None,
) -> MergeConflict | None:
    if base is None and ours is not None and theirs is not None and _hash(ours) != _hash(theirs):
        return _conflict(MergeConflictType.ID_COLLISION, file_name, entity_id, "Both branches add the same id differently.", base, ours, theirs)
    ours_changed = _hash(base) != _hash(ours)
    theirs_changed = _hash(base) != _hash(theirs)
    if not (ours_changed and theirs_changed):
        return None
    if (ours is None) != (theirs is None):
        return _conflict(MergeConflictType.DELETED_CHANGED, file_name, entity_id, "One branch deletes this entity while the other changes it.", base, ours, theirs)
    if _visibility(base) != _visibility(ours) or _visibility(base) != _visibility(theirs) or _visibility(ours) != _visibility(theirs):
        return _conflict(MergeConflictType.HIDDEN_VISIBILITY_MISMATCH, file_name, entity_id, "Branches disagree on hidden/player-visible visibility.", base, ours, theirs)
    if file_name == "quests.yaml":
        return _conflict(MergeConflictType.QUEST_GRAPH_CONFLICT, file_name, entity_id, "Both branches changed the same quest graph.", base, ours, theirs)
    if file_name == "relationships.yaml":
        return _conflict(MergeConflictType.RELATIONSHIP_CONFLICT, file_name, entity_id, "Both branches changed the same relationship.", base, ours, theirs)
    if file_name == "npcs.yaml" and (_hash((ours or {}).get("rp_profile")) != _hash((theirs or {}).get("rp_profile"))):
        return _conflict(MergeConflictType.RP_PROFILE_CONFLICT, file_name, entity_id, "Both branches changed the same RP profile.", base, ours, theirs)
    if _hash(ours) != _hash(theirs):
        return _conflict(MergeConflictType.SAME_ENTITY_CHANGED, file_name, entity_id, "Both branches changed the same entity differently.", base, ours, theirs)
    return None


def _conflict(kind: MergeConflictType, file_name: str, entity_id: str, message: str, base: dict[str, Any] | None, ours: dict[str, Any] | None, theirs: dict[str, Any] | None) -> MergeConflict:
    return MergeConflict(
        conflict_id=f"{file_name}:{entity_id}:{kind.value}",
        conflict_type=kind,
        file_name=file_name,
        entity_id=entity_id,
        message=message,
        base=_redacted_entity(file_name, base),
        ours=_redacted_entity(file_name, ours),
        theirs=_redacted_entity(file_name, theirs),
        raw_base=base,
        raw_ours=ours,
        raw_theirs=theirs,
    )


def _resolve_conflict(conflict: MergeConflict, resolution: MergeResolution | None) -> dict[str, Any] | None:
    if resolution is None or resolution.choice == MergeResolutionChoice.BASE:
        return conflict.raw_base
    if resolution.choice == MergeResolutionChoice.OURS:
        return conflict.raw_ours
    if resolution.choice == MergeResolutionChoice.THEIRS:
        return conflict.raw_theirs
    return resolution.custom


def _redacted_entity(file_name: str, value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    safe: dict[str, Any] = {
        "id": value.get("id"),
        "visibility": _visibility(value),
        "details_redacted": True,
    }
    if file_name == "relationships.yaml":
        safe.update(
            {
                "source_id": value.get("source_id"),
                "target_id": value.get("target_id"),
                "relation_type": value.get("relation_type"),
            }
        )
    return safe


def _auto_merge_entity(base: dict[str, Any] | None, ours: dict[str, Any] | None, theirs: dict[str, Any] | None) -> dict[str, Any] | None:
    if _hash(base) != _hash(ours) and _hash(base) == _hash(theirs):
        return ours
    if _hash(base) == _hash(ours) and _hash(base) != _hash(theirs):
        return theirs
    return theirs if theirs is not None else ours


def _items_by_id(file_name: str, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    key = LIST_FILE_KEYS.get(file_name)
    values = data.get(key, []) if key else []
    return {str(item["id"]): dict(item) for item in values if isinstance(item, dict) and item.get("id") is not None} if isinstance(values, list) else {}


def _hash(value: Any) -> str:
    return _stable_hash(value)


def _visibility(value: dict[str, Any] | None) -> str:
    if value is None:
        return "deleted"
    if bool(value.get("hidden")):
        return "hidden"
    return str(value.get("visibility", value.get("known_by_player", "public")))
