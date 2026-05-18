from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import (
    ALLOWED_AUTHORING_FILES,
    LIST_FILE_KEYS,
    AuthoringError,
    ContentAuthoringService,
)
from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack


BRANCH_METADATA_FILE = "branch.yaml"


class WorldBranch(BaseModel):
    branch_id: str
    world_id: str
    base_world_id: str
    name: str
    created_at: str
    description: str = ""
    content_path: str
    parent_branch_id: str | None = None


class WorldEntityRef(BaseModel):
    file: str
    entity_id: str
    entity_type: str


class ChangedEntityRef(WorldEntityRef):
    before_hash: str
    after_hash: str


class RenameCandidate(BaseModel):
    file: str
    removed_id: str
    added_id: str
    confidence: float = 0.5


class BranchMigrationImpact(BaseModel):
    entity: WorldEntityRef
    reason: str


class WorldDiff(BaseModel):
    local_only: bool = True
    world_id: str
    other: str
    added_entities: list[WorldEntityRef] = Field(default_factory=list)
    removed_entities: list[WorldEntityRef] = Field(default_factory=list)
    changed_entities: list[ChangedEntityRef] = Field(default_factory=list)
    renamed_candidates: list[RenameCandidate] = Field(default_factory=list)
    broken_references: list[str] = Field(default_factory=list)
    migration_impacts: list[BranchMigrationImpact] = Field(default_factory=list)
    visibility_risks: list[str] = Field(default_factory=list)


class WorldBranchCreateRequest(BaseModel):
    branch_id: str | None = None
    name: str
    description: str = ""
    parent_branch_id: str | None = None


class WorldDiffDraftRequest(BaseModel):
    proposed_files: dict[str, str]
    other: str | None = None


class WorldBranchService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)
        self.authoring_service = ContentAuthoringService(self.worlds_root)

    def list_branches(self, world_id: str) -> list[WorldBranch]:
        self.authoring_service._safe_world_path(world_id)
        branches_root = self._branches_root(world_id)
        if not branches_root.exists():
            return []
        branches: list[WorldBranch] = []
        for metadata_path in sorted(branches_root.glob(f"*/{BRANCH_METADATA_FILE}")):
            try:
                data = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
                branch = WorldBranch.model_validate(data)
            except (yaml.YAMLError, ValueError):
                continue
            branches.append(branch)
        return branches

    def create_branch(self, world_id: str, request: WorldBranchCreateRequest) -> WorldBranch:
        source_world = self.authoring_service._safe_world_path(world_id)
        branch_id = request.branch_id or f"{world_id}_{uuid4().hex[:8]}"
        if not _is_safe_branch_id(branch_id):
            raise AuthoringError(f"Invalid branch_id: {branch_id}")
        branch_root = self._branch_content_path(world_id, branch_id)
        if branch_root.exists():
            raise AuthoringError(f"World branch already exists: {branch_id}")
        branch_root.mkdir(parents=True)
        for file_name in ALLOWED_AUTHORING_FILES:
            source_file = source_world / file_name
            if source_file.exists() and source_file.is_file():
                (branch_root / file_name).write_text(source_file.read_text(encoding="utf-8"), encoding="utf-8")
        branch = WorldBranch(
            branch_id=branch_id,
            world_id=branch_id,
            base_world_id=world_id,
            name=request.name,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=request.description,
            content_path=f".branches/{world_id}/{branch_id}",
            parent_branch_id=request.parent_branch_id,
        )
        (branch_root / BRANCH_METADATA_FILE).write_text(
            yaml.safe_dump(branch.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return branch

    def diff_world(self, world_id: str, other: str) -> WorldDiff:
        base_path = self.authoring_service._safe_world_path(world_id)
        other_path = self._resolve_world_or_branch_path(world_id, other)
        return self._diff_paths(world_id, other, base_path, other_path)

    def diff_draft(self, world_id: str, request: WorldDiffDraftRequest) -> WorldDiff:
        base_path = self.authoring_service._safe_world_path(world_id)
        for file_name, content in request.proposed_files.items():
            self.authoring_service._safe_file_path(world_id, file_name)
            self.authoring_service._parse_yaml(content, file_name)
        with TemporaryDirectory() as temp_dir:
            draft_root = Path(temp_dir) / "worlds" / world_id
            copytree(base_path, draft_root)
            for file_name, content in request.proposed_files.items():
                (draft_root / file_name).write_text(content, encoding="utf-8")
            return self._diff_paths(world_id, request.other or "draft", base_path, draft_root)

    def _diff_paths(self, world_id: str, other: str, before_path: Path, after_path: Path) -> WorldDiff:
        diff = WorldDiff(world_id=world_id, other=other)
        for file_name in ALLOWED_AUTHORING_FILES:
            before_data = _read_yaml_mapping(before_path / file_name)
            after_data = _read_yaml_mapping(after_path / file_name)
            before_items = _items_by_id(file_name, before_data)
            after_items = _items_by_id(file_name, after_data)
            entity_type = LIST_FILE_KEYS.get(file_name, file_name).removesuffix("s")
            before_ids = set(before_items)
            after_ids = set(after_items)
            for entity_id in sorted(after_ids - before_ids):
                diff.added_entities.append(
                    WorldEntityRef(file=file_name, entity_id=entity_id, entity_type=entity_type)
                )
            for entity_id in sorted(before_ids - after_ids):
                removed = WorldEntityRef(file=file_name, entity_id=entity_id, entity_type=entity_type)
                diff.removed_entities.append(removed)
                diff.migration_impacts.append(
                    BranchMigrationImpact(entity=removed, reason="Removed ids may break saves or references.")
                )
            for entity_id in sorted(before_ids & after_ids):
                before_hash = _stable_hash(before_items[entity_id])
                after_hash = _stable_hash(after_items[entity_id])
                if before_hash != after_hash:
                    diff.changed_entities.append(
                        ChangedEntityRef(
                            file=file_name,
                            entity_id=entity_id,
                            entity_type=entity_type,
                            before_hash=before_hash,
                            after_hash=after_hash,
                        )
                    )
            removed_ids = sorted(before_ids - after_ids)
            added_ids = sorted(after_ids - before_ids)
            if len(removed_ids) == 1 and len(added_ids) == 1:
                diff.renamed_candidates.append(
                    RenameCandidate(file=file_name, removed_id=removed_ids[0], added_id=added_ids[0])
                )
        report = validate_world_pack(after_path.name, worlds_root=after_path.parent)
        diff.broken_references = _issue_messages(report, ValidationSeverity.ERROR)
        diff.visibility_risks = [
            issue.message
            for issue in [*report.warnings, *report.errors]
            if "visibility" in issue.code or "hidden" in issue.message.lower() or "leak" in issue.code
        ]
        diff.visibility_risks.extend(_rumor_visibility_risks(after_path))
        diff.visibility_risks = sorted(set(diff.visibility_risks))
        return diff

    def _resolve_world_or_branch_path(self, world_id: str, other: str) -> Path:
        if not _is_safe_branch_id(other):
            raise AuthoringError(f"Invalid diff target: {other}")
        branch_path = self._branch_content_path(world_id, other)
        if branch_path.exists() and branch_path.is_dir():
            return branch_path
        return self.authoring_service._safe_world_path(other)

    def _branches_root(self, world_id: str) -> Path:
        if not _is_safe_branch_id(world_id):
            raise AuthoringError(f"Invalid world_id: {world_id}")
        root = (self.worlds_root / ".branches" / world_id).resolve()
        worlds_root = self.worlds_root.resolve()
        if worlds_root not in root.parents:
            raise AuthoringError("Branch path escapes worlds root")
        return root

    def _branch_content_path(self, world_id: str, branch_id: str) -> Path:
        if not _is_safe_branch_id(branch_id):
            raise AuthoringError(f"Invalid branch_id: {branch_id}")
        path = (self._branches_root(world_id) / branch_id).resolve()
        root = self._branches_root(world_id).resolve()
        if root != path and root not in path.parents:
            raise AuthoringError("Branch content path escapes branch root")
        return path


def _is_safe_branch_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _items_by_id(file_name: str, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    key = LIST_FILE_KEYS.get(file_name)
    if key is None:
        return {}
    raw_items = data.get(key, [])
    if not isinstance(raw_items, list):
        return {}
    return {
        str(item["id"]): item
        for item in raw_items
        if isinstance(item, dict) and item.get("id") is not None
    }


def _stable_hash(value: Any) -> str:
    import hashlib
    import json

    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _issue_messages(report: ValidationReport, severity: ValidationSeverity) -> list[str]:
    issues = report.errors if severity == ValidationSeverity.ERROR else report.warnings
    return [f"{issue.file}:{issue.path}:{issue.code}:{issue.message}" for issue in issues]


def _rumor_visibility_risks(world_path: Path) -> list[str]:
    facts = _items_by_id("facts.yaml", _read_yaml_mapping(world_path / "facts.yaml"))
    rumors = _items_by_id("rumors.yaml", _read_yaml_mapping(world_path / "rumors.yaml"))
    risks: list[str] = []
    hidden_fact_texts = [
        str(fact.get("text", "")).strip().lower()
        for fact in facts.values()
        if fact.get("visibility") == "hidden" and str(fact.get("text", "")).strip()
    ]
    for rumor_id, rumor in sorted(rumors.items()):
        fact_id = str(rumor.get("fact_id") or "")
        text_for_player = str(rumor.get("text_for_player") or "").strip().lower()
        if rumor.get("known_by_player") is True and fact_id in facts and facts[fact_id].get("visibility") == "hidden":
            risks.append(f"Rumor {rumor_id} is player-known and references hidden fact {fact_id}.")
        if text_for_player and any(hidden_text and hidden_text in text_for_player for hidden_text in hidden_fact_texts):
            risks.append(f"Rumor {rumor_id} player text appears to include hidden fact text.")
    return risks
