import base64
import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel, Field, ValidationError

from app.core.event_log import Event
from app.core.world_state import GameState
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES, ModLoader
from app.engine.content.validator import ValidationReport, validate_world_pack


class ImportExportError(ValueError):
    """Raised when a local import/export archive is unsafe or invalid."""


class ExportManifest(BaseModel):
    export_type: str
    id: str
    schema_version: str = "0.7"
    content_pack_version: str | None = None
    mod_version: str | None = None
    files: list[str] = Field(default_factory=list)


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
        repository: SQLiteSaveRepository,
    ) -> None:
        self.worlds_root = Path(worlds_root)
        self.mods_root = Path(mods_root)
        self.repository = repository

    def export_world(self, world_id: str) -> ArchiveExport:
        world_path = self._safe_existing_dir(self.worlds_root, world_id, "world")
        manifest = ExportManifest(
            export_type="world",
            id=world_id,
            files=[f"worlds/{world_id}/{name}" for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()],
        )
        archive = _make_archive(manifest, world_path, f"worlds/{world_id}")
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
        archive = _make_archive(manifest, mod.path, f"mods/{mod_id}")
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
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("export_manifest.json", manifest.model_dump_json())
            archive.writestr("save_bundle.json", json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return ArchiveExport(file_name=f"{save_id}.save.zip", archive_base64=_b64(buffer.getvalue()))

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


def _make_archive(manifest: ExportManifest, source_dir: Path, archive_prefix: str) -> bytes:
    _validate_archive_source(source_dir)
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("export_manifest.json", manifest.model_dump_json())
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            _validate_file_name(path.name)
            relative = path.relative_to(source_dir).as_posix()
            archive.write(path, f"{archive_prefix}/{relative}")
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
