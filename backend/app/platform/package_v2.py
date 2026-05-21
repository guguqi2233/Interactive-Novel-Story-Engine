from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.migrations import CURRENT_ENGINE_VERSION
from app.platform.security import contains_secret_text, safe_identifier, sha256_bytes, validate_relative_package_path


PACKAGE_V2_CONTRACT_VERSION = "2"


class PackageV2Manifest(BaseModel):
    package_id: str
    package_type: Literal[
        "world",
        "module",
        "plugin",
        "script",
        "character_transfer",
        "prompt_experiment",
        "backup",
        "campaign_export",
    ]
    version: str = "2.0.0"
    contract_version: str = PACKAGE_V2_CONTRACT_VERSION
    engine_version_min: str = CURRENT_ENGINE_VERSION
    schema_versions: dict[str, str] = Field(default_factory=dict)
    included_files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    redaction_policy: Literal["safe_no_secrets", "authoring_redacted", "debug_local_only"] = "safe_no_secrets"
    compatibility_policy: Literal["strict", "allow_legacy_with_warnings", "migration_required"] = "strict"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    signature: dict[str, str] | None = None

    @field_validator("package_id")
    @classmethod
    def validate_package_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe package_id")
        return value

    @field_validator("included_files")
    @classmethod
    def validate_included_files(cls, values: list[str]) -> list[str]:
        return [validate_relative_package_path(value) for value in values]

    @model_validator(mode="after")
    def validate_manifest(self) -> "PackageV2Manifest":
        if str(self.contract_version) != PACKAGE_V2_CONTRACT_VERSION:
            raise ValueError("Unsupported package v2 contract_version")
        missing = [path for path in self.included_files if path not in self.checksums]
        if missing:
            raise ValueError(f"Missing checksums for included files: {missing}")
        return self


class PackageV2ValidationReport(BaseModel):
    ok: bool
    package_id: str | None = None
    package_type: str | None = None
    manifest: PackageV2Manifest | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    legacy_v1_detected: bool = False
    compatibility_checked: bool = False


class PackageV2ImportResult(BaseModel):
    imported: bool
    dry_run: bool
    report: PackageV2ValidationReport
    requires_confirmation: bool = True
    output_path: str | None = None


class PackageV2ExportResult(BaseModel):
    package_id: str
    package_type: str
    manifest: PackageV2Manifest
    archive_base64: str
    file_name: str


class PackageV2Validator:
    def validate_archive(self, archive_base64: str) -> PackageV2ValidationReport:
        try:
            raw = base64.b64decode(archive_base64)
        except Exception as exc:
            return PackageV2ValidationReport(ok=False, errors=[f"Invalid base64 package: {exc}"])
        with TemporaryDirectory() as temp_dir:
            return self._validate_zip(raw, Path(temp_dir))

    def _validate_zip(self, raw: bytes, temp_root: Path) -> PackageV2ValidationReport:
        try:
            with ZipFile(BytesIO(raw)) as archive:
                names = archive.namelist()
                if "package_v2_manifest.json" not in names:
                    if "local_package_manifest.json" in names:
                        return PackageV2ValidationReport(
                            ok=True,
                            warnings=["Legacy v1 package detected; v2 migration warning required."],
                            legacy_v1_detected=True,
                            compatibility_checked=True,
                        )
                    return PackageV2ValidationReport(ok=False, errors=["package_v2_manifest.json is required"])
                for name in names:
                    validate_relative_package_path(name)
                manifest = PackageV2Manifest.model_validate(json.loads(archive.read("package_v2_manifest.json").decode("utf-8")))
                errors: list[str] = []
                warnings: list[str] = []
                for path in manifest.included_files:
                    if path not in names:
                        errors.append(f"Included file missing from archive: {path}")
                        continue
                    data = archive.read(path)
                    if sha256_bytes(data) != manifest.checksums[path]:
                        errors.append(f"Checksum mismatch: {path}")
                    if _looks_text(path, data) and contains_secret_text(data.decode("utf-8", errors="ignore")):
                        errors.append(f"Secret-like text found in package file: {path}")
                    if manifest.redaction_policy == "safe_no_secrets" and _looks_hidden_payload(path, data):
                        errors.append(f"Hidden/debug payload is not allowed in safe package: {path}")
                return PackageV2ValidationReport(
                    ok=not errors,
                    package_id=manifest.package_id,
                    package_type=manifest.package_type,
                    manifest=manifest,
                    errors=errors,
                    warnings=warnings,
                    compatibility_checked=True,
                )
        except (BadZipFile, ValueError, json.JSONDecodeError) as exc:
            return PackageV2ValidationReport(ok=False, errors=[str(exc)])


class PackageV2Importer:
    def __init__(self, validator: PackageV2Validator | None = None) -> None:
        self.validator = validator or PackageV2Validator()

    def dry_run(self, archive_base64: str) -> PackageV2ImportResult:
        report = self.validator.validate_archive(archive_base64)
        return PackageV2ImportResult(imported=False, dry_run=True, report=report)

    def apply(self, archive_base64: str, *, confirm_apply: bool = False, output_root: str | Path | None = None) -> PackageV2ImportResult:
        report = self.validator.validate_archive(archive_base64)
        if not confirm_apply:
            report.ok = False
            report.errors.append("confirm_apply is required")
            return PackageV2ImportResult(imported=False, dry_run=False, report=report)
        if not report.ok:
            return PackageV2ImportResult(imported=False, dry_run=False, report=report)
        # v2 apply only records validated metadata in this stable contract layer.
        return PackageV2ImportResult(imported=True, dry_run=False, report=report, output_path=str(output_root) if output_root else None)


class PackageV2Exporter:
    def export_files(
        self,
        *,
        package_id: str,
        package_type: PackageV2Manifest.model_fields["package_type"].annotation,
        files: dict[str, bytes],
        schema_versions: dict[str, str] | None = None,
    ) -> PackageV2ExportResult:
        checked: dict[str, bytes] = {}
        checksums: dict[str, str] = {}
        for path, data in files.items():
            safe_path = validate_relative_package_path(path)
            if _looks_text(safe_path, data) and contains_secret_text(data.decode("utf-8", errors="ignore")):
                raise ValueError(f"Secret-like text found in export file: {safe_path}")
            if _looks_hidden_payload(safe_path, data):
                raise ValueError(f"Hidden/debug payload is not allowed in safe package: {safe_path}")
            checked[safe_path] = data
            checksums[safe_path] = sha256_bytes(data)
        manifest = PackageV2Manifest(
            package_id=package_id,
            package_type=package_type,
            schema_versions=schema_versions or {},
            included_files=sorted(checked),
            checksums=checksums,
        )
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("package_v2_manifest.json", json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2))
            for path in sorted(checked):
                archive.writestr(path, checked[path])
        return PackageV2ExportResult(
            package_id=package_id,
            package_type=package_type,
            manifest=manifest,
            archive_base64=base64.b64encode(buffer.getvalue()).decode("ascii"),
            file_name=f"{package_id}.package-v2.zip",
        )


def _looks_text(path: str, data: bytes) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in {".json", ".yaml", ".yml", ".txt", ".md", ".csv"} or b"\x00" not in data[:256]


def _looks_hidden_payload(path: str, data: bytes) -> bool:
    text = data.decode("utf-8", errors="ignore").lower() if _looks_text(path, data) else ""
    markers = ("hidden_fact_text", "npc_secret", "debug_memory", "raw_state_delta", "raw_prompt")
    return any(marker in path.lower() or marker in text for marker in markers)

