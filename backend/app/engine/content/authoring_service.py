from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

import yaml
from pydantic import BaseModel

from app.core.instrumentation import record_performance_sample
from app.engine.content.map_visual import build_authoring_map_visual_graph
from app.engine.content.validator import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    validate_world_pack,
)
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGate,
    AuthoringValidationGateRequest,
)
from app.engine.content.world_loader import (
    MapVisualEdge,
    MapVisualEdgeType,
    MapVisualGraph,
    MapVisibility,
    WorldLoader,
    WorldLoaderError,
    WorldManifest,
)


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
    "example_dialogues.yaml",
    "scene_moods.yaml",
    "dialogue_scenes.yaml",
    "group_rp_scenes.yaml",
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
    "example_dialogues.yaml": "example_dialogues",
    "scene_moods.yaml": "scene_mood_presets",
    "dialogue_scenes.yaml": "dialogue_scenes",
    "group_rp_scenes.yaml": "group_rp_scenes",
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
        self.validation_gate = AuthoringValidationGate(self.worlds_root)

    def list_worlds(self) -> list[AuthoringWorldSummary]:
        if not self.worlds_root.exists():
            return []
        worlds: list[AuthoringWorldSummary] = []
        for world_path in sorted(self.worlds_root.iterdir(), key=lambda path: path.name):
            if world_path.is_dir() and not world_path.name.startswith("."):
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

    def write_file(
        self,
        world_id: str,
        file_name: str,
        content: str,
        *,
        confirm_warnings: bool = False,
    ) -> ValidationReport:
        path = self._safe_file_path(world_id, file_name)
        self._parse_yaml(content, file_name)
        report = self.validate_draft(world_id, file_name, content)
        gate = self.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.SAVE,
                draft_content={file_name: content},
                affected_files=[file_name],
                validation_report=report,
                confirm_warnings=confirm_warnings,
            )
        )
        report = gate.validation_report
        if not gate.allowed_to_save:
            return report
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

    def validate_drafts(
        self,
        world_id: str,
        proposed_files: dict[str, str],
    ) -> ValidationReport:
        if not proposed_files:
            return self.validate_world(world_id)
        for file_name, content in proposed_files.items():
            self._safe_file_path(world_id, file_name)
            try:
                self._parse_yaml(content, file_name)
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
        with TemporaryDirectory() as temp_dir:
            temp_worlds_root = Path(temp_dir) / "worlds"
            source_world = self._safe_world_path(world_id)
            draft_world = temp_worlds_root / world_id
            copytree(source_world, draft_world)
            for file_name, content in proposed_files.items():
                (draft_world / file_name).write_text(content, encoding="utf-8")
            return validate_world_pack(world_id, worlds_root=temp_worlds_root)

    def write_files(
        self,
        world_id: str,
        proposed_files: dict[str, str],
        *,
        confirm_warnings: bool = False,
    ) -> ValidationReport:
        report = self.validate_drafts(world_id, proposed_files)
        gate = self.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.SAVE,
                draft_content=proposed_files,
                affected_files=list(proposed_files),
                validation_report=report,
                confirm_warnings=confirm_warnings,
            )
        )
        report = gate.validation_report
        if not gate.allowed_to_save:
            return report
        backups: dict[Path, str | None] = {}
        paths: dict[Path, str] = {}
        for file_name, content in proposed_files.items():
            path = self._safe_file_path(world_id, file_name)
            backups[path] = path.read_text(encoding="utf-8") if path.exists() else None
            paths[path] = content
        try:
            for path, content in paths.items():
                path.write_text(content, encoding="utf-8")
            persisted_report = self.validate_world(world_id)
            if persisted_report.ok:
                return persisted_report
            report = persisted_report
        except Exception as exc:
            report = ValidationReport(world_id=world_id)
            report.add(
                ValidationSeverity.ERROR,
                "authoring",
                f"Failed to save content files: {exc}",
                code="authoring_multi_file_write_failed",
            )
        for path, backup in backups.items():
            if backup is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(backup, encoding="utf-8")
        return report

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

    def get_map_graph(self, world_id: str) -> MapVisualGraph:
        self._safe_world_path(world_id)
        try:
            pack = WorldLoader(self.worlds_root).load(world_id)
        except WorldLoaderError as exc:
            raise AuthoringError(str(exc)) from exc
        return build_authoring_map_visual_graph(pack)

    def map_graph_to_locations_yaml(self, world_id: str, graph: MapVisualGraph) -> str:
        self._safe_world_path(world_id)
        current_content = self.read_file(world_id, "locations.yaml")
        current_data = _safe_parse_mapping(current_content)
        current_locations = _items_by_id("locations.yaml", current_data)
        exits_by_source: dict[str, dict[str, str]] = {node.location_id: {} for node in graph.nodes}
        edge_metadata_by_source: dict[str, dict[str, dict[str, Any]]] = {
            node.location_id: {} for node in graph.nodes
        }
        for edge in graph.edges:
            exits_by_source.setdefault(edge.source_location_id, {})[edge.label] = edge.target_location_id
            if _edge_has_authoring_metadata(edge):
                edge_metadata_by_source.setdefault(edge.source_location_id, {})[edge.label] = {
                    key: value
                    for key, value in edge.model_dump(mode="json").items()
                    if key not in {"source_location_id", "label"} and value not in (None, [], {}, "")
                }

        locations: list[dict[str, Any]] = []
        for node in graph.nodes:
            existing = dict(current_locations.get(node.location_id, {}))
            existing["id"] = node.location_id
            existing["name"] = node.name
            existing.setdefault("description", "")
            existing["exits"] = dict(sorted(exits_by_source.get(node.location_id, {}).items()))
            metadata = edge_metadata_by_source.get(node.location_id, {})
            if metadata:
                existing["exit_metadata"] = dict(sorted(metadata.items()))
            else:
                existing.pop("exit_metadata", None)
            visual = dict(existing.get("visual") or {})
            visual.update(
                {
                    "x": node.x,
                    "y": node.y,
                    "region_id": node.region_id,
                    "layer_id": node.layer_id,
                    "icon": node.icon,
                    "color_tag": node.color_tag,
                    "display_group": node.display_group,
                    "tags": node.tags,
                    "visibility": node.visibility.value,
                }
            )
            existing["visual"] = {
                key: value
                for key, value in visual.items()
                if value is not None and value != []
            }
            locations.append(existing)
        return yaml.safe_dump({"locations": locations}, sort_keys=False, allow_unicode=True)

    def preview_map_graph(self, world_id: str, graph: MapVisualGraph) -> AuthoringPreviewReport:
        content = self.map_graph_to_locations_yaml(world_id, graph)
        preview = self.preview_file_change(world_id, "locations.yaml", content)
        _add_map_graph_validation_issues(graph, preview.validation_report)
        return preview

    def validate_map_graph(self, world_id: str, graph: MapVisualGraph) -> ValidationReport:
        content = self.map_graph_to_locations_yaml(world_id, graph)
        report = self.validate_draft(world_id, "locations.yaml", content)
        _add_map_graph_validation_issues(graph, report)
        return report

    def write_map_graph(
        self,
        world_id: str,
        graph: MapVisualGraph,
        *,
        confirm_warnings: bool = False,
    ) -> ValidationReport:
        content = self.map_graph_to_locations_yaml(world_id, graph)
        report = self.validate_map_graph(world_id, graph)
        gate = self.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.SAVE,
                draft_content={"locations.yaml": content},
                affected_files=["locations.yaml"],
                validation_report=report,
                confirm_warnings=confirm_warnings,
            )
        )
        if not gate.allowed_to_save:
            return gate.validation_report
        return self.write_file(
            world_id,
            "locations.yaml",
            content,
            confirm_warnings=confirm_warnings,
        )

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


def _edge_has_authoring_metadata(edge: MapVisualEdge) -> bool:
    return (
        edge.edge_type not in {MapVisualEdgeType.EXIT, MapVisualEdgeType.ONE_WAY}
        or edge.visibility != MapVisibility.PUBLIC
        or edge.travel_cost != 1
        or bool(edge.discovery_rules)
        or bool(edge.unlock_condition)
    )


def _add_map_graph_validation_issues(graph: MapVisualGraph, report: ValidationReport) -> None:
    node_ids = {node.location_id for node in graph.nodes}
    region_ids = {region.id for region in graph.regions}
    outgoing: dict[str, list[MapVisualEdge]] = {node_id: [] for node_id in node_ids}
    incoming: dict[str, list[MapVisualEdge]] = {node_id: [] for node_id in node_ids}
    for node in graph.nodes:
        if node.region_id and region_ids and node.region_id not in region_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"locations.yaml.{node.location_id}.visual.region_id",
                f"Map node references invalid region id: {node.region_id}",
                code="map_visual_invalid_region_id",
                suggestion="Use a region id declared in graph.regions.",
            )
    for edge in graph.edges:
        if edge.source_location_id not in node_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"locations.yaml.{edge.source_location_id}.exits.{edge.label}",
                f"Map edge source location does not exist: {edge.source_location_id}",
                code="map_visual_invalid_location_id",
            )
            continue
        outgoing.setdefault(edge.source_location_id, []).append(edge)
        if edge.target_location_id not in node_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"locations.yaml.{edge.source_location_id}.exits.{edge.label}",
                f"Map edge target location does not exist: {edge.target_location_id}",
                code="map_visual_edge_target_missing",
                suggestion="Pick an existing location id as the target.",
            )
            continue
        incoming.setdefault(edge.target_location_id, []).append(edge)
        if edge.edge_type == MapVisualEdgeType.HIDDEN and edge.visibility != MapVisibility.HIDDEN:
            report.add(
                ValidationSeverity.WARNING,
                f"locations.yaml.{edge.source_location_id}.exit_metadata.{edge.label}",
                "Hidden map edge is not marked hidden and may leak a hidden path in authoring previews.",
                code="map_visual_hidden_edge_leakage_risk",
                suggestion="Set edge visibility to hidden for hidden paths.",
            )
        if edge.edge_type == MapVisualEdgeType.LOCKED and not edge.unlock_condition:
            report.add(
                ValidationSeverity.WARNING,
                f"locations.yaml.{edge.source_location_id}.exit_metadata.{edge.label}",
                "Locked edge has no unlock path or condition.",
                code="map_visual_locked_edge_without_unlock_path",
                suggestion="Add unlock_condition or discovery rules for this locked edge.",
            )
    _warn_unreachable_regions(graph, outgoing, incoming, report)
    _warn_circular_one_way_edges(graph, report)


def _warn_unreachable_regions(
    graph: MapVisualGraph,
    outgoing: dict[str, list[MapVisualEdge]],
    incoming: dict[str, list[MapVisualEdge]],
    report: ValidationReport,
) -> None:
    region_nodes: dict[str, list[str]] = {}
    for node in graph.nodes:
        if node.region_id:
            region_nodes.setdefault(node.region_id, []).append(node.location_id)
    for region_id, node_ids in sorted(region_nodes.items()):
        has_connection = any(
            edge.target_location_id not in node_ids
            for node_id in node_ids
            for edge in outgoing.get(node_id, [])
        ) or any(
            edge.source_location_id not in node_ids
            for node_id in node_ids
            for edge in incoming.get(node_id, [])
        )
        if not has_connection and len(region_nodes) > 1:
            report.add(
                ValidationSeverity.WARNING,
                f"locations.yaml.visual.regions.{region_id}",
                f"Region has no visible connection to other regions: {region_id}",
                code="map_visual_unreachable_region_warning",
                suggestion="Add at least one inter-region edge if this region should be reachable.",
            )


def _warn_circular_one_way_edges(graph: MapVisualGraph, report: ValidationReport) -> None:
    one_way_pairs = {
        (edge.source_location_id, edge.target_location_id)
        for edge in graph.edges
        if edge.edge_type == MapVisualEdgeType.ONE_WAY
    }
    for source_id, target_id in sorted(one_way_pairs):
        if (target_id, source_id) in one_way_pairs:
            report.add(
                ValidationSeverity.WARNING,
                f"locations.yaml.{source_id}.exits",
                f"One-way exits form a circular pair: {source_id} <-> {target_id}",
                code="map_visual_circular_one_way_warning",
                suggestion="Use normal exit edges for bidirectional travel.",
            )
