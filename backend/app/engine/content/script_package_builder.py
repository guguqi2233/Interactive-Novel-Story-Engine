from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel, Field, field_validator

from app.db.migrations import CURRENT_ENGINE_VERSION, CURRENT_SAVE_SCHEMA_VERSION
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES
from app.engine.content.validator import ValidationReport, ValidationSeverity


class ScriptPackageBuilderError(ValueError):
    """Raised when a script package build request is invalid or unsafe."""


SECRET_TOKENS = ("api_key", "apikey", "secret_key", "private_key", "bearer ", "sk-", "BEGIN PRIVATE KEY")
SENSITIVE_FILE_NAMES = {".env", "env", "secrets.yaml", "secrets.json"}
SENSITIVE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".log")


class ScriptPackageFile(BaseModel):
    path: str
    content: str = ""
    hidden: bool = False


class ScriptPackageManifest(BaseModel):
    package_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    version: str = "1.0"
    target_engine_version: str = CURRENT_ENGINE_VERSION
    target_schema_version: str = CURRENT_SAVE_SCHEMA_VERSION
    included_worlds: list[str] = Field(default_factory=list)
    included_quests: list[str] = Field(default_factory=list)
    included_characters: list[str] = Field(default_factory=list)
    included_templates: list[str] = Field(default_factory=list)
    included_scenarios: list[str] = Field(default_factory=list)
    included_quality_profile: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    normal_manifest: bool = True


class ScriptPackageBuildRequest(BaseModel):
    manifest: ScriptPackageManifest
    files: list[ScriptPackageFile] = Field(default_factory=list)
    available_dependency_ids: list[str] = Field(default_factory=list)
    packages_root: str = "packages"
    confirm_apply: bool = False
    normal_report: bool = True

    @field_validator("packages_root")
    @classmethod
    def _packages_root_must_not_be_sensitive(cls, value: str) -> str:
        parts = {part.lower() for part in Path(value).parts}
        if parts & {".env", "secrets.yaml", "secrets.json"}:
            raise ValueError("Script package builder cannot use sensitive config paths.")
        return value


class ScriptPackageBuildReport(BaseModel):
    manifest: ScriptPackageManifest
    validation: ValidationReport
    dry_run: bool = True
    applied: bool = False
    package_dir: str | None = None
    archive_file_name: str | None = None
    archive_base64: str | None = None
    files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    normal_manifest: dict[str, Any] = Field(default_factory=dict)


def build_script_package_dry_run(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    return _build_report(request, dry_run=True, include_archive=False)


def validate_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    return _build_report(request, dry_run=True, include_archive=False)


def build_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    report = _build_report(request, dry_run=False, include_archive=False)
    if not request.confirm_apply:
        report.validation.add(
            ValidationSeverity.ERROR,
            "script_package.build",
            "Script package build requires explicit confirmation.",
            code="script_package_build_requires_confirmation",
        )
        return report
    if not report.validation.ok:
        return report
    package_dir = _safe_package_dir(Path(request.packages_root), request.manifest.package_id)
    if package_dir.exists():
        report.validation.add(
            ValidationSeverity.ERROR,
            "script_package.build",
            "Script package already exists; automatic overwrite is not allowed.",
            code="script_package_overwrite_rejected",
            ref_id=request.manifest.package_id,
        )
        return report
    package_dir.mkdir(parents=True)
    manifest = report.manifest
    (package_dir / "script_package_manifest.json").write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    for file in request.files:
        relative = _safe_relative_path(file.path)
        target = (package_dir / relative.as_posix()).resolve()
        if package_dir.resolve() != target.parent and package_dir.resolve() not in target.parents:
            raise ScriptPackageBuilderError("Script package file path escapes package root.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file.content, encoding="utf-8")
    report.applied = True
    report.dry_run = False
    report.package_dir = str(package_dir)
    return report


def export_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    report = _build_report(request, dry_run=True, include_archive=True)
    if not report.validation.ok:
        return report
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("script_package_manifest.json", report.manifest.model_dump_json())
        for file in request.files:
            relative = _safe_relative_path(file.path).as_posix()
            archive.writestr(relative, file.content)
    report.archive_file_name = f"{request.manifest.package_id}.script.zip"
    report.archive_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return report


def _build_report(
    request: ScriptPackageBuildRequest,
    *,
    dry_run: bool,
    include_archive: bool,
) -> ScriptPackageBuildReport:
    validation = ValidationReport(world_id=request.manifest.package_id)
    manifest = request.manifest.model_copy(deep=True)
    file_map = _package_file_map(request, validation)
    payload = _script_package_payload(manifest, request.files)
    file_map["script_package_payload.json"] = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    manifest.checksums = {path: _sha256_text(content) for path, content in sorted(file_map.items())}
    _validate_manifest(manifest, request, validation)
    _validate_secret_free(manifest.model_dump(mode="json"), validation)
    _validate_secret_free([file.model_dump(mode="json") for file in request.files], validation)
    normal_manifest = _normal_manifest(manifest, request.normal_report)
    return ScriptPackageBuildReport(
        manifest=manifest,
        validation=validation,
        dry_run=dry_run,
        applied=False,
        archive_file_name=f"{manifest.package_id}.script.zip" if include_archive and validation.ok else None,
        files=sorted(file_map),
        dependencies=manifest.dependencies,
        conflicts=manifest.conflicts,
        normal_manifest=normal_manifest,
    )


def _script_package_payload(manifest: ScriptPackageManifest, files: list[ScriptPackageFile]) -> dict[str, Any]:
    return {
        "package_id": manifest.package_id,
        "included_worlds": manifest.included_worlds,
        "included_quests": manifest.included_quests,
        "included_characters": manifest.included_characters,
        "included_templates": manifest.included_templates,
        "included_scenarios": manifest.included_scenarios,
        "included_quality_profile": manifest.included_quality_profile,
        "files": [{"path": file.path, "hidden": file.hidden} for file in files],
    }


def _validate_manifest(
    manifest: ScriptPackageManifest,
    request: ScriptPackageBuildRequest,
    validation: ValidationReport,
) -> None:
    included_ids = set(
        manifest.included_worlds
        + manifest.included_quests
        + manifest.included_characters
        + manifest.included_templates
        + manifest.included_scenarios
    )
    for value in included_ids | set(manifest.dependencies) | set(manifest.conflicts):
        if not _is_safe_id(value):
            validation.add(
                ValidationSeverity.ERROR,
                "script_package.manifest",
                f"Unsafe package reference id: {value}",
                code="script_package_unsafe_ref",
                ref_id=value,
            )
    available = set(request.available_dependency_ids)
    if available:
        missing = sorted(dep for dep in manifest.dependencies if dep not in available and dep not in included_ids)
        for dep in missing:
            validation.add(
                ValidationSeverity.ERROR,
                "script_package.dependencies",
                f"Missing dependency: {dep}",
                code="script_package_missing_dependency",
                ref_id=dep,
            )
    conflicts = sorted(set(manifest.conflicts) & (included_ids | set(manifest.dependencies)))
    for conflict in conflicts:
        validation.add(
            ValidationSeverity.ERROR,
            "script_package.conflicts",
            f"Package conflict captured: {conflict}",
            code="script_package_conflict_detected",
            ref_id=conflict,
        )
    if not included_ids and not request.files:
        validation.add(
            ValidationSeverity.WARNING,
            "script_package",
            "Script package has no selected content.",
            code="script_package_empty",
        )


def _package_file_map(request: ScriptPackageBuildRequest, validation: ValidationReport) -> dict[str, str]:
    files: dict[str, str] = {}
    for file in request.files:
        try:
            relative = _safe_relative_path(file.path)
        except ScriptPackageBuilderError as exc:
            validation.add(ValidationSeverity.ERROR, "script_package.files", str(exc), code="script_package_unsafe_path")
            continue
        name = relative.name.lower()
        suffix = relative.suffix.lower()
        if name in SENSITIVE_FILE_NAMES or suffix in SENSITIVE_SUFFIXES:
            validation.add(
                ValidationSeverity.ERROR,
                f"script_package.files.{file.path}",
                "Script package cannot contain .env, database, or log files.",
                code="script_package_sensitive_file_rejected",
                ref_id=file.path,
            )
        if suffix in FORBIDDEN_CODE_SUFFIXES:
            validation.add(
                ValidationSeverity.ERROR,
                f"script_package.files.{file.path}",
                "Script package cannot contain executable code.",
                code="script_package_executable_rejected",
                ref_id=file.path,
            )
        files[relative.as_posix()] = file.content
    return files


def _safe_relative_path(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or normalized.startswith("/") or normalized.startswith("~") or ".." in path.parts:
        raise ScriptPackageBuilderError(f"Unsafe script package path: {value}")
    return path


def _safe_package_dir(packages_root: Path, package_id: str) -> Path:
    root = packages_root.resolve()
    target = (root / "script_packages" / package_id).resolve()
    if root != target and root not in target.parents:
        raise ScriptPackageBuilderError("Script package path escapes packages root.")
    return target


def _validate_secret_free(value: Any, validation: ValidationReport) -> None:
    for text in _iter_strings(value):
        lowered = text.lower()
        if any(token.lower() in lowered for token in SECRET_TOKENS):
            validation.add(
                ValidationSeverity.ERROR,
                "script_package",
                "Script package contains API key or sensitive configuration text.",
                code="script_package_secret_rejected",
            )
            return


def _normal_manifest(manifest: ScriptPackageManifest, normal_report: bool) -> dict[str, Any]:
    data = manifest.model_dump(mode="json")
    if normal_report:
        data.pop("checksums", None)
        data["normal_manifest"] = True
    return data


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for key, child in value.items() for item in _iter_strings(key) + _iter_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _iter_strings(child)]
    return []


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
