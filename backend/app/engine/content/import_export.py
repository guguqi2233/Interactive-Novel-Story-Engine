import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel, Field, ValidationError

from app.compatibility.contracts import PACKAGE_CONTRACT_VERSION
from app.core.event_log import Event
from app.core.world_state import GameState
from app.db.migrations import CURRENT_ENGINE_VERSION, CURRENT_SAVE_SCHEMA_VERSION
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES, ModLoader
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.validator import ValidationReport, validate_world_pack
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGate,
    AuthoringValidationGateRequest,
)
from app.scenarios.regression import sample_scenario_regression_cases


class ImportExportError(ValueError):
    """Raised when a local import/export archive is unsafe or invalid."""


class ExportManifest(BaseModel):
    export_type: str
    id: str
    schema_version: str = "0.7"
    content_pack_version: str | None = None
    mod_version: str | None = None
    files: list[str] = Field(default_factory=list)


class LocalPackageManifest(BaseModel):
    package_id: str
    package_type: str
    contract_version: str = PACKAGE_CONTRACT_VERSION
    version: str = "0.8.16"
    engine_version_min: str = "0.8.0"
    schema_version: str = CURRENT_SAVE_SCHEMA_VERSION
    content_pack_version: str | None = None
    included_files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    redaction_policy: str = "safe_no_secrets"
    notes: str = ""


class PackageDryRunResult(BaseModel):
    ok: bool
    package_id: str
    package_type: str
    manifest: LocalPackageManifest | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    compatibility_warnings: list[str] = Field(default_factory=list)
    migration_needed: bool = False
    migration_warnings: list[str] = Field(default_factory=list)


class ImportResult(BaseModel):
    imported: bool
    import_type: str
    id: str
    validation_ok: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    migration_needed: bool = False
    migration_warnings: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ArchiveExport:
    file_name: str
    archive_base64: str


class ImportExportService:
    def __init__(
        self,
        *,
        worlds_root: str | Path = "worlds",
        mods_root: str | Path = "mods",
        templates_root: str | Path = "templates",
        repository: SQLiteSaveRepository,
    ) -> None:
        self.worlds_root = Path(worlds_root)
        self.mods_root = Path(mods_root)
        self.templates_root = Path(templates_root)
        self.repository = repository
        self.validation_gate = AuthoringValidationGate(self.worlds_root)

    def export_world(self, world_id: str) -> ArchiveExport:
        world_path = self._safe_existing_dir(self.worlds_root, world_id, "world")
        gate = self.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=world_id,
                operation_type=AuthoringOperationType.EXPORT,
                affected_files=[name for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()],
                confirm_warnings=True,
            )
        )
        if not gate.validation_report.ok:
            raise ImportExportError("Authoring Validation Gate blocked world export.")
        manifest = ExportManifest(
            export_type="world",
            id=world_id,
            files=[f"worlds/{world_id}/{name}" for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()],
        )
        package_manifest = LocalPackageManifest(
            package_id=world_id,
            package_type="world",
            content_pack_version=manifest.content_pack_version,
            included_files=manifest.files,
            notes="Local world package export.",
        )
        archive = _make_archive(manifest, world_path, f"worlds/{world_id}", package_manifest=package_manifest)
        return ArchiveExport(file_name=f"{world_id}.world.zip", archive_base64=_b64(archive))

    def import_world(self, archive_base64: str, *, overwrite: bool = False) -> ImportResult:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _extract_safe_archive(_unb64(archive_base64), root)
            if manifest.export_type != "world":
                raise ImportExportError("Archive is not a world export.")
            source = root / "worlds" / manifest.id
            if not source.is_dir():
                raise ImportExportError("World archive missing world directory.")
            target = self._safe_new_or_existing_dir(self.worlds_root, manifest.id, overwrite, "world")
            report = validate_world_pack(manifest.id, worlds_root=root / "worlds")
            gate = AuthoringValidationGate(root / "worlds").evaluate(
                AuthoringValidationGateRequest(
                    world_id=manifest.id,
                    operation_type=AuthoringOperationType.IMPORT,
                    affected_files=[name for name in ALLOWED_AUTHORING_FILES if (source / name).exists()],
                    validation_report=report,
                    confirm_warnings=True,
                )
            )
            report = gate.validation_report
            if not report.ok:
                return _result_from_validation("world", manifest.id, report)
            if target.exists() and overwrite:
                _clear_directory(target)
            copytree(source, target, dirs_exist_ok=overwrite)
            return _result_from_validation("world", manifest.id, report, imported=True)

    def export_mod(self, mod_id: str) -> ArchiveExport:
        loader = ModLoader(self.mods_root)
        mod = next((item for item in loader.discover_mods() if item.manifest.id == mod_id), None)
        if mod is None:
            raise ImportExportError(f"Mod not found: {mod_id}")
        manifest = ExportManifest(
            export_type="mod",
            id=mod_id,
            mod_version=mod.manifest.version,
            files=[str(path.relative_to(mod.path.parent)).replace("\\", "/") for path in mod.path.rglob("*") if path.is_file()],
        )
        package_manifest = LocalPackageManifest(
            package_id=mod_id,
            package_type="mod",
            content_pack_version=mod.manifest.content_schema_version,
            included_files=manifest.files,
            dependencies=mod.manifest.dependencies,
            conflicts=mod.manifest.conflicts,
            notes=mod.manifest.migration_notes,
        )
        archive = _make_archive(manifest, mod.path, f"mods/{mod_id}", package_manifest=package_manifest)
        return ArchiveExport(file_name=f"{mod_id}.mod.zip", archive_base64=_b64(archive))

    def import_mod(self, archive_base64: str, *, overwrite: bool = False) -> ImportResult:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _extract_safe_archive(_unb64(archive_base64), root)
            if manifest.export_type != "mod":
                raise ImportExportError("Archive is not a mod export.")
            source = root / "mods" / manifest.id
            if not source.is_dir():
                raise ImportExportError("Mod archive missing mod directory.")
            target = self._safe_new_or_existing_dir(self.mods_root, manifest.id, overwrite, "mod")
            temp_loader = ModLoader(root / "mods")
            report = temp_loader.validate_mod(manifest.id)
            if not report.ok:
                return ImportResult(
                    imported=False,
                    import_type="mod",
                    id=manifest.id,
                    validation_ok=False,
                    errors=[issue.message for issue in report.errors],
                    warnings=[issue.message for issue in report.warnings],
                )
            if target.exists() and overwrite:
                _clear_directory(target)
            copytree(source, target, dirs_exist_ok=overwrite)
            return ImportResult(imported=True, import_type="mod", id=manifest.id, validation_ok=True)

    def export_save(self, save_id: str) -> ArchiveExport:
        save = self.repository.get_save(save_id)
        events = self.repository.list_events(save_id)
        payload = {
            "save": save.model_dump(mode="json"),
            "events": [json.loads(event.model_dump_json()) for event in events],
        }
        manifest = ExportManifest(export_type="save", id=save_id, files=["save_bundle.json"])
        package_manifest = LocalPackageManifest(
            package_id=save_id,
            package_type="save_bundle",
            content_pack_version=save.content_pack_version,
            included_files=["save_bundle.json"],
            notes="Local save bundle export. Contains runtime state and EventLog.",
        )
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("export_manifest.json", manifest.model_dump_json())
            content = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            package_manifest.checksums = {"save_bundle.json": _sha256_text(content)}
            archive.writestr("local_package_manifest.json", package_manifest.model_dump_json())
            archive.writestr("save_bundle.json", content)
        return ArchiveExport(file_name=f"{save_id}.save.zip", archive_base64=_b64(buffer.getvalue()))

    def export_template_pack(self, pack_id: str = "local_templates") -> ArchiveExport:
        if not _is_safe_id(pack_id):
            raise ImportExportError(f"Invalid id: {pack_id}")
        renderer = ScenarioTemplateRenderer(templates_root=self.templates_root, worlds_root=self.worlds_root)
        renderer.list_templates()
        manifest = ExportManifest(
            export_type="template_pack",
            id=pack_id,
            files=[f"templates/{path.name}" for path in sorted(self.templates_root.glob("*.yaml")) if path.is_file()],
        )
        package_manifest = LocalPackageManifest(
            package_id=pack_id,
            package_type="template_pack",
            included_files=manifest.files,
            notes="Local scenario template pack.",
        )
        archive = _make_archive(manifest, self.templates_root, "templates", package_manifest=package_manifest)
        return ArchiveExport(file_name=f"{pack_id}.templates.zip", archive_base64=_b64(archive))

    def export_scenario_suite(self, suite_id: str = "local_scenarios") -> ArchiveExport:
        if not _is_safe_id(suite_id):
            raise ImportExportError(f"Invalid id: {suite_id}")
        content = json.dumps(
            {"cases": [case.model_dump(mode="json") for case in sample_scenario_regression_cases()]},
            ensure_ascii=False,
            sort_keys=True,
        )
        manifest = ExportManifest(export_type="scenario_suite", id=suite_id, files=["scenario_suite.json"])
        package_manifest = LocalPackageManifest(
            package_id=suite_id,
            package_type="scenario_suite",
            included_files=["scenario_suite.json"],
            checksums={"scenario_suite.json": _sha256_text(content)},
            notes="Local scenario regression suite package.",
        )
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("export_manifest.json", manifest.model_dump_json())
            archive.writestr("local_package_manifest.json", package_manifest.model_dump_json())
            archive.writestr("scenario_suite.json", content)
        return ArchiveExport(file_name=f"{suite_id}.scenarios.zip", archive_base64=_b64(buffer.getvalue()))

    def dry_run_import_package(self, archive_base64: str, *, overwrite: bool = False) -> PackageDryRunResult:
        try:
            with TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                export_manifest, package_manifest = _extract_safe_package(_unb64(archive_base64), root)
                result = PackageDryRunResult(
                    ok=True,
                    package_id=package_manifest.package_id,
                    package_type=package_manifest.package_type,
                    manifest=package_manifest,
                )
                if export_manifest.id != package_manifest.package_id:
                    result.errors.append("Package manifest id does not match export manifest id.")
                if not _package_type_matches(export_manifest.export_type, package_manifest.package_type):
                    result.errors.append("Package type does not match export type.")
                if package_manifest.engine_version_min and _compare_version(CURRENT_ENGINE_VERSION, package_manifest.engine_version_min) < 0:
                    result.compatibility_warnings.append(
                        f"Engine {CURRENT_ENGINE_VERSION} is below package minimum {package_manifest.engine_version_min}."
                    )
                self._collect_package_conflicts(root, export_manifest, package_manifest, result, overwrite=overwrite)
                result.ok = not result.errors and not result.conflicts
                return result
        except ImportExportError as exc:
            return PackageDryRunResult(ok=False, package_id="", package_type="", errors=[str(exc)])

    def apply_import_package(
        self,
        archive_base64: str,
        *,
        overwrite: bool = False,
        confirm_apply: bool = False,
    ) -> ImportResult:
        if not confirm_apply:
            raise ImportExportError("Package import apply requires explicit confirmation.")
        dry_run = self.dry_run_import_package(archive_base64, overwrite=overwrite)
        if not dry_run.ok:
            raise ImportExportError("; ".join(dry_run.errors))
        package_type = dry_run.package_type
        if package_type == "world":
            self._gate_world_package_import(archive_base64)
        if package_type == "world":
            return self.import_world(archive_base64, overwrite=overwrite)
        if package_type == "mod":
            return self.import_mod(archive_base64, overwrite=overwrite)
        if package_type == "save_bundle":
            return self.import_save(archive_base64, overwrite=overwrite)
        if package_type == "template_pack":
            return self._import_template_pack(archive_base64, overwrite=overwrite)
        if package_type == "scenario_suite":
            return self._import_scenario_suite(archive_base64)
        raise ImportExportError(f"Unsupported package_type: {package_type}")

    def _gate_world_package_import(self, archive_base64: str) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            export_manifest, _package_manifest = _extract_safe_package(_unb64(archive_base64), root)
            source = root / "worlds" / export_manifest.id
            report = validate_world_pack(export_manifest.id, worlds_root=root / "worlds")
            gate = AuthoringValidationGate(root / "worlds").evaluate(
                AuthoringValidationGateRequest(
                    world_id=export_manifest.id,
                    operation_type=AuthoringOperationType.APPLY_PACK,
                    affected_files=[name for name in ALLOWED_AUTHORING_FILES if (source / name).exists()],
                    validation_report=report,
                    confirm_warnings=True,
                )
            )
            if not gate.validation_report.ok:
                raise ImportExportError("Authoring Validation Gate blocked package import apply.")

    def _import_template_pack(self, archive_base64: str, *, overwrite: bool = False) -> ImportResult:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, package_manifest = _extract_safe_package(_unb64(archive_base64), root)
            if package_manifest.package_type != "template_pack":
                raise ImportExportError("Archive is not a template pack.")
            source = root / "templates"
            if not source.is_dir():
                raise ImportExportError("Template package missing templates directory.")
            self.templates_root.mkdir(parents=True, exist_ok=True)
            for path in sorted(source.glob("*.yaml")):
                target = self.templates_root / path.name
                if target.exists() and not overwrite:
                    raise ImportExportError(f"Template already exists: {path.stem}")
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            ScenarioTemplateRenderer(templates_root=self.templates_root, worlds_root=self.worlds_root).list_templates()
            return ImportResult(imported=True, import_type="template_pack", id=manifest.id, validation_ok=True)

    def _import_scenario_suite(self, archive_base64: str) -> ImportResult:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, package_manifest = _extract_safe_package(_unb64(archive_base64), root)
            if package_manifest.package_type != "scenario_suite":
                raise ImportExportError("Archive is not a scenario suite.")
            suite_path = root / "scenario_suite.json"
            if not suite_path.exists():
                raise ImportExportError("Scenario suite package missing scenario_suite.json.")
            try:
                payload = json.loads(suite_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ImportExportError("Invalid scenario suite JSON.") from exc
            if not isinstance(payload.get("cases"), list):
                raise ImportExportError("Scenario suite must contain cases list.")
            return ImportResult(imported=True, import_type="scenario_suite", id=manifest.id, validation_ok=True)

    def _collect_package_conflicts(
        self,
        root: Path,
        export_manifest: ExportManifest,
        package_manifest: LocalPackageManifest,
        result: PackageDryRunResult,
        *,
        overwrite: bool,
    ) -> None:
        package_type = package_manifest.package_type
        if package_type == "world":
            if (self.worlds_root / package_manifest.package_id).exists() and not overwrite:
                result.conflicts.append(f"World already exists: {package_manifest.package_id}")
            report = validate_world_pack(package_manifest.package_id, worlds_root=root / "worlds")
            result.errors.extend(issue.message for issue in report.errors)
            result.warnings.extend(issue.message for issue in report.warnings)
        elif package_type == "mod":
            if (self.mods_root / package_manifest.package_id).exists() and not overwrite:
                result.conflicts.append(f"Mod already exists: {package_manifest.package_id}")
            report = ModLoader(root / "mods").validate_mod(package_manifest.package_id)
            result.errors.extend(issue.message for issue in report.errors)
            result.warnings.extend(issue.message for issue in report.warnings)
        elif package_type == "save_bundle":
            if self._save_exists(package_manifest.package_id) and not overwrite:
                result.conflicts.append(f"Save already exists: {package_manifest.package_id}")
            bundle_path = root / "save_bundle.json"
            if not bundle_path.exists():
                result.errors.append("Save bundle missing save_bundle.json.")
            else:
                try:
                    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
                    state = GameState.model_validate_json(payload["save"]["state_json"])
                    result.migration_needed = state.schema_version != CURRENT_SAVE_SCHEMA_VERSION
                except Exception as exc:
                    result.errors.append(f"Invalid save bundle data: {exc}")
        elif package_type == "template_pack":
            source = root / "templates"
            if not source.is_dir():
                result.errors.append("Template package missing templates directory.")
            else:
                for path in sorted(source.glob("*.yaml")):
                    if (self.templates_root / path.name).exists() and not overwrite:
                        result.conflicts.append(f"Template already exists: {path.stem}")
        elif package_type == "scenario_suite":
            if not (root / "scenario_suite.json").exists():
                result.errors.append("Scenario suite package missing scenario_suite.json.")
        else:
            result.errors.append(f"Unsupported package_type: {package_type}")
        if result.conflicts:
            result.ok = False

    def import_save(self, archive_base64: str, *, overwrite: bool = False) -> ImportResult:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _extract_safe_archive(_unb64(archive_base64), root)
            if manifest.export_type != "save":
                raise ImportExportError("Archive is not a save export.")
            bundle_path = root / "save_bundle.json"
            if not bundle_path.exists():
                raise ImportExportError("Save archive missing save_bundle.json.")
            try:
                payload = json.loads(bundle_path.read_text(encoding="utf-8"))
                save_payload = payload.get("save", {})
                save_id = str(save_payload.get("save_id") or manifest.id)
            except (json.JSONDecodeError, AttributeError) as exc:
                raise ImportExportError("Invalid save bundle payload.") from exc
            if self._save_exists(save_id) and not overwrite:
                raise ImportExportError(f"Save already exists: {save_id}")
            try:
                state = GameState.model_validate_json(save_payload["state_json"])
                events = [Event.model_validate(event) for event in payload.get("events", [])]
            except (KeyError, ValidationError) as exc:
                raise ImportExportError(f"Invalid save bundle data: {exc}") from exc
            self.repository.save_snapshot(save_id, state, events)
            status = MigrationService(self.repository).status(save_id)
            return ImportResult(
                imported=True,
                import_type="save",
                id=save_id,
                validation_ok=True,
                migration_needed=status.needs_migration,
                migration_warnings=status.warnings,
            )

    def _save_exists(self, save_id: str) -> bool:
        try:
            self.repository.get_save(save_id)
        except Exception:
            return False
        return True

    def _safe_existing_dir(self, root: Path, item_id: str, label: str) -> Path:
        path = _safe_child(root, item_id)
        if not path.is_dir():
            raise ImportExportError(f"{label.title()} not found: {item_id}")
        return path

    def _safe_new_or_existing_dir(self, root: Path, item_id: str, overwrite: bool, label: str) -> Path:
        path = _safe_child(root, item_id)
        if path.exists() and not overwrite:
            raise ImportExportError(f"{label.title()} already exists: {item_id}")
        return path


def _make_archive(
    manifest: ExportManifest,
    source_dir: Path,
    archive_prefix: str,
    *,
    package_manifest: LocalPackageManifest | None = None,
) -> bytes:
    _validate_archive_source(source_dir)
    checksums: dict[str, str] = {}
    files_to_write: list[tuple[Path, str]] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        _validate_file_name(path.name)
        relative = path.relative_to(source_dir).as_posix()
        archive_name = f"{archive_prefix}/{relative}"
        files_to_write.append((path, archive_name))
        checksums[archive_name] = _sha256_bytes(path.read_bytes())
    if package_manifest is not None:
        package_manifest.included_files = sorted(checksums)
        package_manifest.checksums = checksums
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("export_manifest.json", manifest.model_dump_json())
        if package_manifest is not None:
            archive.writestr("local_package_manifest.json", package_manifest.model_dump_json())
        for path, archive_name in files_to_write:
            archive.write(path, archive_name)
    return buffer.getvalue()


def _extract_safe_archive(archive_bytes: bytes, target_root: Path) -> ExportManifest:
    try:
        with ZipFile(BytesIO(archive_bytes), "r") as archive:
            names = archive.namelist()
            if "export_manifest.json" not in names:
                raise ImportExportError("Archive missing export_manifest.json.")
            for name in names:
                _validate_zip_member(name)
                if name.endswith("/"):
                    continue
                _validate_file_name(Path(name).name)
            try:
                manifest = ExportManifest.model_validate_json(archive.read("export_manifest.json"))
            except (ValidationError, KeyError) as exc:
                raise ImportExportError(f"Invalid export manifest: {exc}") from exc
            archive.extractall(target_root)
    except BadZipFile as exc:
        raise ImportExportError("Archive payload is not a valid zip file.") from exc
    return manifest


def _extract_safe_package(archive_bytes: bytes, target_root: Path) -> tuple[ExportManifest, LocalPackageManifest]:
    try:
        with ZipFile(BytesIO(archive_bytes), "r") as archive:
            names = archive.namelist()
            if "export_manifest.json" not in names:
                raise ImportExportError("Archive missing export_manifest.json.")
            if "local_package_manifest.json" not in names:
                raise ImportExportError("Archive missing local_package_manifest.json.")
            for name in names:
                _validate_zip_member(name)
                if name.endswith("/"):
                    continue
                _validate_file_name(Path(name).name)
            try:
                export_manifest = ExportManifest.model_validate_json(archive.read("export_manifest.json"))
                raw_package_manifest = json.loads(archive.read("local_package_manifest.json").decode("utf-8"))
                if "contract_version" not in raw_package_manifest:
                    raise ImportExportError("Package manifest missing contract_version.")
                package_manifest = LocalPackageManifest.model_validate(raw_package_manifest)
                if package_manifest.contract_version != PACKAGE_CONTRACT_VERSION:
                    raise ImportExportError(
                        f"Unsupported package contract_version: {package_manifest.contract_version}"
                    )
            except (ValidationError, KeyError) as exc:
                raise ImportExportError(f"Invalid local package manifest: {exc}") from exc
            _validate_package_checksums(archive, package_manifest)
            archive.extractall(target_root)
            return export_manifest, package_manifest
    except BadZipFile as exc:
        raise ImportExportError("Archive payload is not a valid zip file.") from exc


def _validate_zip_member(name: str) -> None:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ImportExportError(f"Unsafe archive path: {name}")


def _validate_file_name(name: str) -> None:
    lower = name.lower()
    if lower in {".env", "env", "secrets.yaml", "secrets.json"}:
        raise ImportExportError("Archive contains disallowed sensitive file.")
    if lower.endswith((".db", ".sqlite", ".sqlite3", ".log")):
        raise ImportExportError("Archive contains disallowed local data file.")
    if Path(name).suffix.lower() in FORBIDDEN_CODE_SUFFIXES:
        raise ImportExportError("Archive contains executable code.")


def _validate_package_checksums(archive: ZipFile, manifest: LocalPackageManifest) -> None:
    for name in manifest.included_files:
        _validate_zip_member(name)
        if name not in archive.namelist():
            raise ImportExportError(f"Package missing included file: {name}")
        expected = manifest.checksums.get(name)
        if not expected:
            raise ImportExportError(f"Package missing checksum for: {name}")
        actual = _sha256_bytes(archive.read(name))
        if actual != expected:
            raise ImportExportError(f"Checksum mismatch for: {name}")


def _validate_archive_source(source_dir: Path) -> None:
    for path in source_dir.rglob("*"):
        if path.is_file():
            _validate_file_name(path.name)


def _safe_child(root: Path, item_id: str) -> Path:
    if not item_id or not all(character.isalnum() or character in {"_", "-"} for character in item_id):
        raise ImportExportError(f"Invalid id: {item_id}")
    resolved_root = root.resolve()
    path = (resolved_root / item_id).resolve()
    if resolved_root != path and resolved_root not in path.parents:
        raise ImportExportError("Path escapes local content root.")
    return path


def _clear_directory(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _clear_directory(child)
            child.rmdir()
        else:
            child.unlink()


def _result_from_validation(
    import_type: str,
    item_id: str,
    report: ValidationReport,
    *,
    imported: bool = False,
) -> ImportResult:
    return ImportResult(
        imported=imported,
        import_type=import_type,
        id=item_id,
        validation_ok=report.ok,
        errors=[issue.message for issue in report.errors],
        warnings=[issue.message for issue in report.warnings],
    )


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise ImportExportError("Archive payload is not valid base64.") from exc


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _package_type_matches(export_type: str, package_type: str) -> bool:
    return export_type == package_type or (export_type == "save" and package_type == "save_bundle")


def _compare_version(left: str, right: str) -> int:
    def parse(value: str) -> list[int]:
        parts: list[int] = []
        for raw in value.replace("-", ".").split("."):
            digits = "".join(character for character in raw if character.isdigit())
            if not digits:
                break
            parts.append(int(digits))
        return parts or [0]

    left_parts = parse(left)
    right_parts = parse(right)
    length = max(len(left_parts), len(right_parts))
    left_parts.extend([0] * (length - len(left_parts)))
    right_parts.extend([0] * (length - len(right_parts)))
    if left_parts < right_parts:
        return -1
    if left_parts > right_parts:
        return 1
    return 0
