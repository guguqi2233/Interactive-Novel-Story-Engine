from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel, Field

from app.db.migrations import CURRENT_ENGINE_VERSION
from app.platform.narrative_project import NarrativeProject, NARRATIVE_PROJECT_SCHEMA_VERSION
from app.platform.project_repository import ProjectRepository
from app.platform.security import contains_secret_text, safe_identifier, sha256_bytes, validate_relative_package_path


PROJECT_PACKAGE_MANIFEST = "project_package_manifest.json"


class ProjectPackageManifest(BaseModel):
    package_id: str
    package_type: Literal["narrative_project"] = "narrative_project"
    project_id: str
    project_name: str
    version: str = "2.1.0"
    engine_version: str = CURRENT_ENGINE_VERSION
    schema_version: str = NARRATIVE_PROJECT_SCHEMA_VERSION
    included_sections: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    notes: str = ""
    export_mode: Literal["normal", "authoring", "debug"] = "normal"


class ProjectPackageReport(BaseModel):
    ok: bool
    dry_run: bool = True
    imported: bool = False
    manifest: ProjectPackageManifest | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    output_path: str | None = None


class ProjectPackageExportResult(BaseModel):
    manifest: ProjectPackageManifest
    archive_base64: str
    file_name: str


def export_project(
    project_id: str,
    repository: ProjectRepository,
    *,
    sections: list[str] | None = None,
    export_mode: Literal["normal", "authoring", "debug"] = "normal",
    include_debug: bool = False,
) -> ProjectPackageExportResult:
    if export_mode == "debug" and not include_debug:
        raise ValueError("debug export requires include_debug=True")
    project = repository.load_project(project_id)
    root = Path(project.project_root)
    files: dict[str, bytes] = {}
    allowed_sections = sections or ["project.yaml", "novel", "tavern", "world/content_pack", "scripts", "providers/profiles", "quality/reports", "cross_mode/drafts", "cross_mode/proposals", "cross_mode/reviews", "cross_mode/apply_plans", "cross_mode/audit"]
    for section in allowed_sections:
        source = root / section
        if source.is_file():
            _add_file(files, source, root)
        elif source.is_dir():
            for path in sorted(item for item in source.rglob("*") if item.is_file()):
                _add_file(files, path, root)
    checksums = {path: sha256_bytes(data) for path, data in files.items()}
    manifest = ProjectPackageManifest(
        package_id=f"{project.project_id}_project",
        project_id=project.project_id,
        project_name=project.name,
        included_sections=sorted(files),
        checksums=checksums,
        export_mode=export_mode,
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(PROJECT_PACKAGE_MANIFEST, json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))
        for path in sorted(files):
            archive.writestr(path, files[path])
    return ProjectPackageExportResult(
        manifest=manifest,
        archive_base64=base64.b64encode(buffer.getvalue()).decode("ascii"),
        file_name=f"{manifest.package_id}.zip",
    )


def import_project_dry_run(archive_base64: str, target_root: str | Path, repository: ProjectRepository) -> ProjectPackageReport:
    return _validate_archive(archive_base64, target_root, repository)


def import_project_apply(
    archive_base64: str,
    target_root: str | Path,
    repository: ProjectRepository,
    *,
    confirm_apply: bool = False,
) -> ProjectPackageReport:
    report = _validate_archive(archive_base64, target_root, repository)
    if not confirm_apply:
        report.ok = False
        report.errors.append("confirm_apply is required")
        return report
    if not report.ok or report.manifest is None:
        return report
    output = Path(target_root).resolve() / report.manifest.project_id
    if output.exists():
        report.ok = False
        report.errors.append("duplicate project_id")
        return report
    output.mkdir(parents=True)
    raw = base64.b64decode(archive_base64)
    with ZipFile(BytesIO(raw)) as archive:
        for name in archive.namelist():
            if name == PROJECT_PACKAGE_MANIFEST:
                continue
            target = (output / validate_relative_package_path(name)).resolve()
            if output not in target.parents and target != output:
                raise ValueError("Unsafe package path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    report.imported = True
    report.dry_run = False
    report.output_path = str(output)
    return report


def _validate_archive(archive_base64: str, target_root: str | Path, repository: ProjectRepository) -> ProjectPackageReport:
    try:
        raw = base64.b64decode(archive_base64)
    except Exception as exc:
        return ProjectPackageReport(ok=False, errors=[f"Invalid base64: {exc}"])
    try:
        with TemporaryDirectory():
            with ZipFile(BytesIO(raw)) as archive:
                names = archive.namelist()
                if PROJECT_PACKAGE_MANIFEST not in names:
                    return ProjectPackageReport(ok=False, errors=["project_package_manifest.json is required"])
                for name in names:
                    validate_relative_package_path(name)
                manifest = ProjectPackageManifest.model_validate(json.loads(archive.read(PROJECT_PACKAGE_MANIFEST).decode("utf-8")))
                errors: list[str] = []
                if not safe_identifier(manifest.project_id):
                    errors.append("unsafe project_id")
                if (Path(target_root).resolve() / manifest.project_id).exists():
                    errors.append("duplicate project_id")
                for path in manifest.included_sections:
                    if path not in names:
                        errors.append(f"Missing included file: {path}")
                        continue
                    data = archive.read(path)
                    if manifest.checksums.get(path) != sha256_bytes(data):
                        errors.append(f"Checksum mismatch: {path}")
                    if _looks_text(path, data) and contains_secret_text(data.decode("utf-8", errors="ignore")):
                        errors.append(f"Secret-like text found: {path}")
                    if path.startswith("cross_mode/") and _looks_text(path, data):
                        lowered = data.decode("utf-8", errors="ignore").lower()
                        if "raw state_delta" in lowered or "raw_state_delta" in lowered or "debug memory" in lowered:
                            errors.append(f"Forbidden cross-mode debug material: {path}")
                return ProjectPackageReport(ok=not errors, manifest=manifest, errors=errors)
    except (BadZipFile, ValueError, json.JSONDecodeError) as exc:
        return ProjectPackageReport(ok=False, errors=[str(exc)])


def _add_file(files: dict[str, bytes], path: Path, root: Path) -> None:
    rel = validate_relative_package_path(path.relative_to(root).as_posix())
    data = path.read_bytes()
    if _looks_text(rel, data):
        text = data.decode("utf-8", errors="ignore")
        lowered = text.lower()
        if contains_secret_text(text):
            return
        if rel.startswith("cross_mode/") and ("raw_state_delta" in lowered or "raw state_delta" in lowered or "debug memory" in lowered):
            return
    files[rel] = data


def _looks_text(path: str, data: bytes) -> bool:
    return Path(path).suffix.lower() in {".json", ".yaml", ".yml", ".txt", ".md", ".csv"} or b"\x00" not in data[:256]
