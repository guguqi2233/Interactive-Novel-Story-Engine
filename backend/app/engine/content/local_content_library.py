from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from shutil import copytree
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.character_pack_builder import CharacterPackExportRequest, export_character_pack
from app.engine.content.import_export import ArchiveExport, ImportExportService, ImportResult, PackageDryRunResult
from app.engine.content.mod_loader import ModLoader
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.content.validation_gate import AuthoringOperationType, AuthoringValidationGateRequest
from app.engine.content.world_loader import WorldManifest
from app.llm.prompt_profiles import get_default_prompt_profile_store


class LocalContentLibraryError(ValueError):
    """Raised when a local library operation is unsafe or invalid."""


class LocalContentType(StrEnum):
    WORLD = "world"
    CHARACTER_PACK = "character_pack"
    TEMPLATE_PACK = "template_pack"
    SCENARIO_SUITE = "scenario_suite"
    PROMPT_PROFILE = "prompt_profile"
    RP_PROFILE = "RP_profile"
    MOD = "mod"


class LocalContentLibraryItem(BaseModel):
    id: str
    content_type: LocalContentType
    name: str
    version: str | None = None
    description: str = ""
    path_label: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=lambda: ["inspect", "validate", "export"])


class LocalContentLibrary(BaseModel):
    local_only: bool = True
    items: list[LocalContentLibraryItem] = Field(default_factory=list)


class LocalContentLibraryImportRequest(BaseModel):
    archive_base64: str
    overwrite: bool = False
    confirm_apply: bool = False


class LocalContentLibraryExportRequest(BaseModel):
    content_type: LocalContentType
    item_id: str


class LocalContentLibraryDuplicateRequest(BaseModel):
    content_type: LocalContentType
    item_id: str
    new_id: str


class LocalContentLibraryService:
    def __init__(self, import_export: ImportExportService) -> None:
        self.import_export = import_export
        self.worlds_root = import_export.worlds_root
        self.mods_root = import_export.mods_root
        self.templates_root = import_export.templates_root

    def list_items(self, content_type: LocalContentType | None = None) -> LocalContentLibrary:
        items = [
            *self._world_items(),
            *self._mod_items(),
            *self._template_items(),
            self._scenario_suite_item(),
            *self._prompt_profile_items(),
            *self._rp_profile_items(),
        ]
        if content_type:
            items = [item for item in items if item.content_type == content_type]
        return LocalContentLibrary(items=sorted(items, key=lambda item: (item.content_type.value, item.id)))

    def inspect_item(self, item_id: str) -> LocalContentLibraryItem:
        safe_id = _safe_id(item_id)
        for item in self.list_items().items:
            if item.id == safe_id:
                return item
        raise LocalContentLibraryError(f"Library item not found: {safe_id}")

    def validate_item(self, item_id: str) -> ValidationReport:
        item = self.inspect_item(item_id)
        report = ValidationReport(world_id=item.id)
        if item.content_type == LocalContentType.WORLD:
            from app.engine.content.validator import validate_world_pack

            return validate_world_pack(item.id, worlds_root=self.worlds_root)
        if item.content_type == LocalContentType.MOD:
            mod_report = ModLoader(self.mods_root).validate_mod(item.id)
            for issue in mod_report.errors:
                report.errors.append(issue)
            for issue in mod_report.warnings:
                report.warnings.append(issue)
            report.ok = mod_report.ok
            return report
        if item.content_type == LocalContentType.TEMPLATE_PACK:
            try:
                ScenarioTemplateRenderer(self.templates_root, self.worlds_root).list_templates()
            except Exception as exc:
                report.add(ValidationSeverity.ERROR, "templates", str(exc), code="library_template_invalid")
            return report
        return report

    def export_item(self, request: LocalContentLibraryExportRequest) -> ArchiveExport:
        item_id = _safe_id(request.item_id)
        if request.content_type == LocalContentType.WORLD:
            return self.import_export.export_world(item_id)
        if request.content_type == LocalContentType.MOD:
            return self.import_export.export_mod(item_id)
        if request.content_type == LocalContentType.TEMPLATE_PACK:
            return self.import_export.export_template_pack(item_id)
        if request.content_type == LocalContentType.SCENARIO_SUITE:
            return self.import_export.export_scenario_suite(item_id)
        if request.content_type == LocalContentType.CHARACTER_PACK:
            pack = export_character_pack(CharacterPackExportRequest(world_id=item_id), self._authoring_service())
            import json
            from io import BytesIO
            from zipfile import ZIP_DEFLATED, ZipFile
            import base64

            buffer = BytesIO()
            with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
                archive.writestr("character_pack.json", pack.model_dump_json())
            return ArchiveExport(file_name=f"{item_id}.characters.zip", archive_base64=base64.b64encode(buffer.getvalue()).decode("ascii"))
        raise LocalContentLibraryError(f"Export is not supported for {request.content_type.value}")

    def import_archive(self, request: LocalContentLibraryImportRequest) -> PackageDryRunResult | ImportResult:
        if request.confirm_apply:
            return self.import_export.apply_import_package(
                request.archive_base64,
                overwrite=request.overwrite,
                confirm_apply=True,
            )
        return self.import_export.dry_run_import_package(
            request.archive_base64,
            overwrite=request.overwrite,
        )

    def duplicate_item(self, request: LocalContentLibraryDuplicateRequest) -> LocalContentLibraryItem:
        item_id = _safe_id(request.item_id)
        new_id = _safe_id(request.new_id)
        if request.content_type != LocalContentType.WORLD:
            raise LocalContentLibraryError("Duplicate currently supports world packs only.")
        source = _safe_child(self.worlds_root, item_id)
        target = _safe_child(self.worlds_root, new_id)
        if not source.is_dir():
            raise LocalContentLibraryError(f"World not found: {item_id}")
        if target.exists():
            raise LocalContentLibraryError(f"Target already exists: {new_id}")
        copytree(source, target)
        manifest_path = target / "manifest.yaml"
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            data["world_id"] = new_id
            data["name"] = f"{data.get('name', item_id)} Copy"
            manifest_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        service = self._authoring_service()
        validation = service.validate_world(new_id)
        gate = service.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=new_id,
                operation_type=AuthoringOperationType.IMPORT,
                affected_files=[],
                validation_report=validation,
                confirm_warnings=True,
            )
        )
        if not gate.allowed_to_save:
            from shutil import rmtree

            rmtree(target, ignore_errors=True)
            raise LocalContentLibraryError("Duplicated world failed validation gate.")
        return self.inspect_item(new_id)

    def _world_items(self) -> list[LocalContentLibraryItem]:
        if not self.worlds_root.exists():
            return []
        items: list[LocalContentLibraryItem] = []
        for path in sorted(self.worlds_root.iterdir(), key=lambda item: item.name):
            if not path.is_dir() or path.name.startswith("."):
                continue
            manifest = _read_manifest(path / "manifest.yaml")
            items.append(
                LocalContentLibraryItem(
                    id=path.name,
                    content_type=LocalContentType.WORLD,
                    name=manifest.name if manifest else path.name,
                    version=manifest.version if manifest else None,
                    description=manifest.description if manifest else "",
                    path_label=f"worlds/{path.name}",
                    metadata={"start_location_id": manifest.start_location_id if manifest else None},
                    capabilities=["inspect", "validate", "export", "duplicate"],
                )
            )
        return items

    def _mod_items(self) -> list[LocalContentLibraryItem]:
        try:
            mods = ModLoader(self.mods_root).discover_mods()
        except Exception:
            return []
        return [
            LocalContentLibraryItem(
                id=mod.manifest.id,
                content_type=LocalContentType.MOD,
                name=mod.manifest.name,
                version=mod.manifest.version,
                description=mod.manifest.description,
                path_label=f"mods/{mod.manifest.id}",
                metadata={"dependencies": mod.manifest.dependencies, "conflicts": mod.manifest.conflicts},
                capabilities=["inspect", "validate", "export"],
            )
            for mod in mods
        ]

    def _template_items(self) -> list[LocalContentLibraryItem]:
        if not self.templates_root.exists():
            return []
        count = len([path for path in self.templates_root.glob("*.yaml") if path.is_file()])
        return [
            LocalContentLibraryItem(
                id="local_templates",
                content_type=LocalContentType.TEMPLATE_PACK,
                name="Local Templates",
                path_label="templates",
                metadata={"template_count": count},
                capabilities=["inspect", "validate", "export"],
            )
        ]

    def _scenario_suite_item(self) -> LocalContentLibraryItem:
        return LocalContentLibraryItem(
            id="local_scenarios",
            content_type=LocalContentType.SCENARIO_SUITE,
            name="Local Scenario Regression Suite",
            path_label="scenario_suite",
            capabilities=["inspect", "validate", "export"],
        )

    def _prompt_profile_items(self) -> list[LocalContentLibraryItem]:
        profiles = get_default_prompt_profile_store().list_profiles()
        return [
            LocalContentLibraryItem(
                id=profile.id,
                content_type=LocalContentType.PROMPT_PROFILE,
                name=profile.name,
                description=profile.description,
                path_label="prompt_profiles",
                metadata={"tags": getattr(profile, "tags", []), "llm_scope": "profile_only"},
                capabilities=["inspect", "validate"],
            )
            for profile in profiles
        ]

    def _rp_profile_items(self) -> list[LocalContentLibraryItem]:
        items: list[LocalContentLibraryItem] = []
        for world in self._world_items():
            npc_path = self.worlds_root / world.id / "npcs.yaml"
            if not npc_path.exists():
                continue
            data = yaml.safe_load(npc_path.read_text(encoding="utf-8")) or {}
            for npc in data.get("npcs", []) if isinstance(data, dict) else []:
                if isinstance(npc, dict) and npc.get("rp_profile"):
                    npc_id = str(npc.get("id", ""))
                    items.append(
                        LocalContentLibraryItem(
                            id=f"{world.id}:{npc_id}",
                            content_type=LocalContentType.RP_PROFILE,
                            name=str(npc.get("name", npc_id)),
                            path_label=f"worlds/{world.id}/npcs",
                            metadata={"world_id": world.id, "npc_id": npc_id, "private_fields_redacted": True},
                            capabilities=["inspect", "validate"],
                        )
                    )
        return items

    def _authoring_service(self):
        from app.engine.content.authoring_service import ContentAuthoringService

        return ContentAuthoringService(self.worlds_root)


def _read_manifest(path: Path) -> WorldManifest | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return WorldManifest.model_validate(data) if isinstance(data, dict) else None
    except Exception:
        return None


def _safe_id(item_id: str) -> str:
    if not item_id or not all(character.isalnum() or character in {"_", "-", ":"} for character in item_id):
        raise LocalContentLibraryError(f"Invalid library id: {item_id}")
    if ".." in item_id or "/" in item_id or "\\" in item_id:
        raise LocalContentLibraryError(f"Invalid library id: {item_id}")
    return item_id


def _safe_child(root: Path, item_id: str) -> Path:
    safe = _safe_id(item_id)
    resolved_root = root.resolve()
    path = (resolved_root / safe).resolve()
    if resolved_root != path and resolved_root not in path.parents:
        raise LocalContentLibraryError("Path escapes local content root.")
    return path
