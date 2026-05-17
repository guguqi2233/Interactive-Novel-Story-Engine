from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

import yaml
from pydantic import BaseModel

from app.core.instrumentation import record_performance_sample
from app.engine.content.validator import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    validate_world_pack,
)
from app.engine.content.world_loader import WorldManifest


ALLOWED_AUTHORING_FILES: tuple[str, ...] = (
    "manifest.yaml",
    "locations.yaml",
    "npcs.yaml",
    "items.yaml",
    "quests.yaml",
    "facts.yaml",
    "factions.yaml",
    "rumors.yaml",
    "relationships.yaml",
)

LIST_FILE_KEYS: dict[str, str] = {
    "locations.yaml": "locations",
    "npcs.yaml": "npcs",
    "items.yaml": "items",
    "quests.yaml": "quests",
    "facts.yaml": "facts",
    "factions.yaml": "factions",
    "rumors.yaml": "rumors",
    "relationships.yaml": "relationships",
}


class AuthoringError(ValueError):
    """Raised when local authoring input is invalid or unsafe."""


class AuthoringWorldSummary(BaseModel):
    world_id: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    file_count: int = 0


class AuthoringDiffSummary(BaseModel):
    added_ids: list[str] = []
    removed_ids: list[str] = []
    changed_ids: list[str] = []
    line_count_before: int = 0
    line_count_after: int = 0


class AuthoringImpactReport(BaseModel):
    removed_ids: list[str] = []
    renamed_ids: list[str] = []
    changed_location_exits: list[str] = []
    removed_locations: list[str] = []
    removed_npcs: list[str] = []
    removed_items: list[str] = []
    removed_facts: list[str] = []
    removed_quests: list[str] = []
    removed_factions: list[str] = []
    may_break_saves: bool = False
    notes: list[str] = []


class AuthoringPreviewReport(BaseModel):
    parsed_ok: bool
    validation_report: ValidationReport
    normalized_yaml: str | None = None
    diff_summary: AuthoringDiffSummary
    affected_refs: list[str] = []
    potential_save_migration_required: bool = False
    impact: AuthoringImpactReport


class ContentAuthoringService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)

    def list_worlds(self) -> list[AuthoringWorldSummary]:
        if not self.worlds_root.exists():
            return []
        worlds: list[AuthoringWorldSummary] = []
        for world_path in sorted(self.worlds_root.iterdir(), key=lambda path: path.name):
            if world_path.is_dir():
                worlds.append(self.get_world_summary(world_path.name))
        return worlds

    def get_world_summary(self, world_id: str) -> AuthoringWorldSummary:
        world_path = self._safe_world_path(world_id)
        manifest = self._read_manifest(world_path / "manifest.yaml")
        existing_files = [name for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()]
        return AuthoringWorldSummary(
            world_id=world_id,
            name=manifest.name if manifest else None,
            description=manifest.description if manifest else "",
            version=manifest.version if manifest else None,
            file_count=len(existing_files),
        )

    def list_files(self, world_id: str) -> list[str]:
        world_path = self._safe_world_path(world_id)
        return [name for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()]

    def read_file(self, world_id: str, file_name: str) -> str:
        path = self._safe_file_path(world_id, file_name)
        if not path.exists():
            raise AuthoringError(f"Content file not found: {file_name}")
        return path.read_text(encoding="utf-8")

    def write_file(self, world_id: str, file_name: str, content: str) -> ValidationReport:
        path = self._safe_file_path(world_id, file_name)
        self._parse_yaml(content, file_name)
        previous_content = path.read_text(encoding="utf-8") if path.exists() else None
        path.write_text(content, encoding="utf-8")
        report = self.validate_world(world_id)
        if not report.ok:
            if previous_content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(previous_content, encoding="utf-8")
        return report

    def validate_world(self, world_id: str) -> ValidationReport:
        self._safe_world_path(world_id)
        started = perf_counter()
        report = validate_world_pack(world_id, worlds_root=self.worlds_root)
        record_performance_sample(
            "authoring.validation",
            (perf_counter() - started) * 1000,
            tags={"world_id": world_id},
        )
        return report

    def preview_file_change(
        self,
        world_id: str,
        file_name: str,
        proposed_content: str,
    ) -> AuthoringPreviewReport:
        path = self._safe_file_path(world_id, file_name)
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""
        parse_error: str | None = None
        parsed_data: dict[str, Any] | None = None
        try:
            parsed_data = self._parse_yaml(proposed_content, file_name)
        except AuthoringError as exc:
            parse_error = str(exc)

        report = self.validate_draft(world_id, file_name, proposed_content)
        if parse_error:
            report.add(
                ValidationSeverity.ERROR,
                file_name,
                parse_error,
                code="draft_yaml_parse_error",
                suggestion="Fix YAML syntax before saving.",
            )

        impact = self.analyze_file_impact(world_id, file_name, proposed_content)
        diff_summary = _diff_summary(file_name, old_content, proposed_content)
        affected_refs = sorted(
            set(diff_summary.added_ids)
            | set(diff_summary.removed_ids)
            | set(diff_summary.changed_ids)
            | set(impact.changed_location_exits)
        )
        return AuthoringPreviewReport(
            parsed_ok=parse_error is None,
            validation_report=report,
            normalized_yaml=(
                yaml.safe_dump(parsed_data, sort_keys=False, allow_unicode=True)
                if parsed_data is not None
                else None
            ),
            diff_summary=diff_summary,
            affected_refs=affected_refs,
            potential_save_migration_required=impact.may_break_saves,
            impact=impact,
        )

    def validate_draft(
        self,
        world_id: str,
        file_name: str,
        proposed_content: str,
    ) -> ValidationReport:
        self._safe_file_path(world_id, file_name)
        try:
            self._parse_yaml(proposed_content, file_name)
        except AuthoringError as exc:
            report = ValidationReport(world_id=world_id)
            report.add(
                ValidationSeverity.ERROR,
                file_name,
                str(exc),
                code="draft_yaml_parse_error",
                suggestion="Fix YAML syntax before saving.",
            )
            return report
        return self._validate_with_draft_file(world_id, file_name, proposed_content)

    def analyze_file_impact(
        self,
        world_id: str,
        file_name: str,
        proposed_content: str,
    ) -> AuthoringImpactReport:
        path = self._safe_file_path(world_id, file_name)
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""
        old_data = _safe_parse_mapping(old_content)
        new_data = _safe_parse_mapping(proposed_content)
        old_ids = _ids_for_file(file_name, old_data)
        new_ids = _ids_for_file(file_name, new_data)
        removed_ids = sorted(old_ids - new_ids)
        added_ids = sorted(new_ids - old_ids)
        renamed_ids = _guess_renamed_ids(removed_ids, added_ids)
        changed_location_exits = (
            _changed_location_exits(old_data, new_data) if file_name == "locations.yaml" else []
        )
        removed_by_kind = {
            "locations.yaml": "removed_locations",
            "npcs.yaml": "removed_npcs",
            "items.yaml": "removed_items",
            "facts.yaml": "removed_facts",
            "quests.yaml": "removed_quests",
            "factions.yaml": "removed_factions",
        }
        impact = AuthoringImpactReport(
            removed_ids=removed_ids,
            renamed_ids=renamed_ids,
            changed_location_exits=changed_location_exits,
            may_break_saves=bool(removed_ids or renamed_ids or changed_location_exits),
        )
        field_name = removed_by_kind.get(file_name)
        if field_name:
            setattr(impact, field_name, removed_ids)
        if removed_ids:
            impact.notes.append("Removed ids may break existing saves or references.")
        if changed_location_exits:
            impact.notes.append("Changed exits may affect navigation and saved player/NPC positions.")
        if renamed_ids:
            impact.notes.append("Potential renames require manual save/content review.")
        return impact

    def create_world(
        self,
        world_id: str,
        name: str,
        description: str = "",
        start_location_id: str = "start",
    ) -> tuple[AuthoringWorldSummary, ValidationReport]:
        world_path = self._safe_new_world_path(world_id)
        world_path.mkdir(parents=True)
        files = self._initial_world_files(world_id, name, description, start_location_id)
        for file_name, data in files.items():
            (world_path / file_name).write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        report = self.validate_world(world_id)
        return self.get_world_summary(world_id), report

    def _safe_world_path(self, world_id: str) -> Path:
        if not _is_safe_id(world_id):
            raise AuthoringError(f"Invalid world_id: {world_id}")
        root = self.worlds_root.resolve()
        path = (root / world_id).resolve()
        if root != path and root not in path.parents:
            raise AuthoringError("World path escapes worlds root")
        if not path.exists() or not path.is_dir():
            raise AuthoringError(f"World pack not found: {world_id}")
        return path

    def _safe_new_world_path(self, world_id: str) -> Path:
        if not _is_safe_id(world_id):
            raise AuthoringError(f"Invalid world_id: {world_id}")
        root = self.worlds_root.resolve()
        path = (root / world_id).resolve()
        if root != path and root not in path.parents:
            raise AuthoringError("World path escapes worlds root")
        if path.exists():
            raise AuthoringError(f"World pack already exists: {world_id}")
        return path

    def _safe_file_path(self, world_id: str, file_name: str) -> Path:
        if file_name not in ALLOWED_AUTHORING_FILES or Path(file_name).name != file_name:
            raise AuthoringError(f"File is not authoring-allowed: {file_name}")
        world_path = self._safe_world_path(world_id)
        path = (world_path / file_name).resolve()
        if world_path.resolve() != path.parent:
            raise AuthoringError("Content file path escapes world pack")
        return path

    def _validate_with_draft_file(
        self,
        world_id: str,
        file_name: str,
        proposed_content: str,
    ) -> ValidationReport:
        world_path = self._safe_world_path(world_id)
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir) / "worlds"
            copytree(world_path, tmp_root / world_id)
            (tmp_root / world_id / file_name).write_text(proposed_content, encoding="utf-8")
            return validate_world_pack(world_id, worlds_root=tmp_root)

    def _read_manifest(self, path: Path) -> WorldManifest | None:
        if not path.exists():
            return None
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                return None
            return WorldManifest.model_validate(data)
        except (yaml.YAMLError, ValueError):
            return None

    def _parse_yaml(self, content: str, file_name: str) -> Any:
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise AuthoringError(f"Invalid YAML in {file_name}: {exc}") from exc
        if not isinstance(data, dict):
            raise AuthoringError(f"Expected YAML mapping in {file_name}")
        return data

    def _initial_world_files(
        self,
        world_id: str,
        name: str,
        description: str,
        start_location_id: str,
    ) -> dict[str, dict[str, Any]]:
        files: dict[str, dict[str, Any]] = {
            "manifest.yaml": {
                "world_id": world_id,
                "name": name,
                "version": "0.1.0",
                "description": description,
                "start_location_id": start_location_id,
            },
            "locations.yaml": {
                "locations": [
                    {
                        "id": start_location_id,
                        "name": "Start",
                        "description": "A new local world begins here.",
                        "exits": {},
                    }
                ]
            },
        }
        for file_name, key in LIST_FILE_KEYS.items():
            files.setdefault(file_name, {key: []})
        return files


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _safe_parse_mapping(content: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _ids_for_file(file_name: str, data: dict[str, Any]) -> set[str]:
    key = LIST_FILE_KEYS.get(file_name)
    if key is None:
        return set()
    raw_items = data.get(key, [])
    if not isinstance(raw_items, list):
        return set()
    return {
        str(item["id"])
        for item in raw_items
        if isinstance(item, dict) and item.get("id") is not None
    }


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


def _diff_summary(file_name: str, before: str, after: str) -> AuthoringDiffSummary:
    before_data = _safe_parse_mapping(before)
    after_data = _safe_parse_mapping(after)
    before_items = _items_by_id(file_name, before_data)
    after_items = _items_by_id(file_name, after_data)
    before_ids = set(before_items)
    after_ids = set(after_items)
    changed_ids = sorted(
        item_id
        for item_id in before_ids & after_ids
        if before_items[item_id] != after_items[item_id]
    )
    return AuthoringDiffSummary(
        added_ids=sorted(after_ids - before_ids),
        removed_ids=sorted(before_ids - after_ids),
        changed_ids=changed_ids,
        line_count_before=len(before.splitlines()),
        line_count_after=len(after.splitlines()),
    )


def _changed_location_exits(
    before_data: dict[str, Any],
    after_data: dict[str, Any],
) -> list[str]:
    before_locations = _items_by_id("locations.yaml", before_data)
    after_locations = _items_by_id("locations.yaml", after_data)
    changed: list[str] = []
    for location_id in sorted(set(before_locations) & set(after_locations)):
        if before_locations[location_id].get("exits", {}) != after_locations[location_id].get("exits", {}):
            changed.append(location_id)
    return changed


def _guess_renamed_ids(removed_ids: list[str], added_ids: list[str]) -> list[str]:
    if len(removed_ids) == 1 and len(added_ids) == 1:
        return [f"{removed_ids[0]} -> {added_ids[0]}"]
    return []
