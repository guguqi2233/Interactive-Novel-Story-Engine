from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel, Field

from app.compatibility.contracts import PACKAGE_CONTRACT_VERSION
from app.engine.actions.declarative import DeclarativeActionDefinition
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES
from app.engine.gameplay_module_debugger import _read_action_definitions
from app.engine.gameplay_module_loader import GameplayModuleLoader, GameplayModuleLoaderError, GameplayModuleManifest
from app.quality.gameplay_module_quality import GameplayModuleQualityGateReport, run_gameplay_module_quality_gate


class GameplayModulePackageError(ValueError):
    """Raised when a gameplay module package is unsafe or invalid."""


SENSITIVE_FILE_NAMES = {".env", "env", "secrets.yaml", "secrets.json"}
SENSITIVE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log"}
SECRET_TOKENS = ("api_key", "apikey", "secret_key", "private_key", "bearer ", "sk-")


class GameplayModulePackageManifest(BaseModel):
    package_id: str
    package_type: str = "gameplay_module"
    contract_version: str = PACKAGE_CONTRACT_VERSION
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    module_manifest: GameplayModuleManifest
    action_definitions: list[DeclarativeActionDefinition] = Field(default_factory=list)
    rule_configs: list[str] = Field(default_factory=list)
    quality_tests: list[str] = Field(default_factory=list)
    example_content: list[str] = Field(default_factory=list)
    docs: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    redaction_policy: str = "safe_no_secrets"


class GameplayModulePackageExport(BaseModel):
    exported: bool
    file_name: str
    archive_base64: str
    manifest: GameplayModulePackageManifest
    contains_api_key: bool = False
    executable_files_rejected: bool = True


class GameplayModulePackageImportRequest(BaseModel):
    archive_base64: str
    confirm_apply: bool = False
    overwrite: bool = False


class GameplayModulePackageImportReport(BaseModel):
    ok: bool
    imported: bool = False
    dry_run: bool = True
    module_id: str = ""
    manifest: GameplayModulePackageManifest | None = None
    quality_gate: GameplayModuleQualityGateReport | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    writes_to_disk: bool = False
    executes_code: bool = False
    calls_llm: bool = False


def export_gameplay_module_package(
    module_id: str,
    *,
    modules_root: str | Path = "gameplay_modules",
) -> GameplayModulePackageExport:
    loader = GameplayModuleLoader(modules_root)
    module = next((item for item in loader.discover_modules() if item.manifest.id == module_id), None)
    if module is None:
        raise GameplayModulePackageError(f"Gameplay module not found: {module_id}")
    validation = loader.validate_module(module_id)
    if validation.errors:
        raise GameplayModulePackageError("Gameplay module validation blocked export.")
    files = _package_files(module.path)
    file_map = {f"gameplay_modules/{module_id}/{path.relative_to(module.path).as_posix()}": path.read_bytes() for path in files}
    manifest = GameplayModulePackageManifest(
        package_id=module_id,
        module_manifest=module.manifest,
        action_definitions=_read_action_definitions(module.path),
        rule_configs=sorted(path for path in file_map if "/rules" in path or "rule" in Path(path).name.lower()),
        quality_tests=module.manifest.quality_tests,
        example_content=sorted(path for path in file_map if "/examples/" in path or "example" in Path(path).name.lower()),
        docs=sorted(path for path in file_map if Path(path).suffix.lower() in {".md", ".txt"}),
    )
    manifest.checksums = {path: _sha256_bytes(content) for path, content in sorted(file_map.items())}
    manifest_bytes = manifest.model_dump_json().encode("utf-8")
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("gameplay_module_package_manifest.json", manifest_bytes)
        for path, content in sorted(file_map.items()):
            archive.writestr(path, content)
    return GameplayModulePackageExport(
        exported=True,
        file_name=f"{module_id}.gameplay-module.zip",
        archive_base64=base64.b64encode(buffer.getvalue()).decode("ascii"),
        manifest=manifest,
    )


def import_gameplay_module_package_dry_run(
    request: GameplayModulePackageImportRequest,
) -> GameplayModulePackageImportReport:
    with TemporaryDirectory(prefix="gameplay_module_import_", ignore_cleanup_errors=True) as temp_dir:
        root = Path(temp_dir)
        return _dry_run_in_root(request.archive_base64, root)


def import_gameplay_module_package_apply(
    request: GameplayModulePackageImportRequest,
    *,
    modules_root: str | Path = "gameplay_modules",
) -> GameplayModulePackageImportReport:
    if not request.confirm_apply:
        return GameplayModulePackageImportReport(
            ok=False,
            errors=["Gameplay module import apply requires explicit confirmation."],
        )
    with TemporaryDirectory(prefix="gameplay_module_import_", ignore_cleanup_errors=True) as temp_dir:
        root = Path(temp_dir)
        report = _dry_run_in_root(request.archive_base64, root)
        if not report.ok or report.manifest is None:
            report.dry_run = False
            return report
        target_root = Path(modules_root)
        target = _safe_module_target(target_root, report.module_id)
        if target.exists() and not request.overwrite:
            report.ok = False
            report.dry_run = False
            report.errors.append("Gameplay module already exists; overwrite requires explicit flag.")
            return report
        if target.exists():
            rmtree(target)
        source = root / "gameplay_modules" / report.module_id
        target.parent.mkdir(parents=True, exist_ok=True)
        copytree(source, target)
        report.imported = True
        report.dry_run = False
        report.writes_to_disk = True
        return report


def _dry_run_in_root(archive_base64: str, root: Path) -> GameplayModulePackageImportReport:
    try:
        manifest = _extract_package(archive_base64, root)
        loader = GameplayModuleLoader(root / "gameplay_modules")
        validation = loader.validate_module(manifest.module_manifest.id)
        quality_gate = run_gameplay_module_quality_gate(manifest.module_manifest.id, modules_root=root / "gameplay_modules")
    except (GameplayModulePackageError, GameplayModuleLoaderError, ValueError) as exc:
        return GameplayModulePackageImportReport(ok=False, errors=[str(exc)])
    errors = [issue.message for issue in validation.errors]
    warnings = [issue.message for issue in validation.warnings]
    if quality_gate and not quality_gate.passed:
        errors.append("Gameplay module quality gate failed.")
    return GameplayModulePackageImportReport(
        ok=not errors,
        module_id=manifest.module_manifest.id,
        manifest=manifest,
        quality_gate=quality_gate,
        errors=errors,
        warnings=warnings,
    )


def _extract_package(archive_base64: str, root: Path) -> GameplayModulePackageManifest:
    try:
        raw = base64.b64decode(archive_base64.encode("ascii"))
        archive = ZipFile(BytesIO(raw), "r")
    except (ValueError, BadZipFile) as exc:
        raise GameplayModulePackageError("Invalid gameplay module archive.") from exc
    with archive:
        names = archive.namelist()
        for name in names:
            _validate_archive_name(name)
        if "gameplay_module_package_manifest.json" not in names:
            raise GameplayModulePackageError("Gameplay module package manifest is missing.")
        raw_manifest = json.loads(archive.read("gameplay_module_package_manifest.json").decode("utf-8"))
        if "contract_version" not in raw_manifest:
            raise GameplayModulePackageError("Gameplay module package manifest missing contract_version.")
        manifest = GameplayModulePackageManifest.model_validate(raw_manifest)
        if manifest.contract_version != PACKAGE_CONTRACT_VERSION:
            raise GameplayModulePackageError(
                f"Unsupported gameplay module package contract_version: {manifest.contract_version}"
            )
        _validate_checksums(archive, manifest)
        for name in names:
            if name == "gameplay_module_package_manifest.json" or name.endswith("/"):
                continue
            target = (root / name).resolve()
            if root.resolve() != target and root.resolve() not in target.parents:
                raise GameplayModulePackageError("Gameplay module package contains zip slip path.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    return manifest


def _validate_archive_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if normalized.startswith("/") or ".." in parts:
        raise GameplayModulePackageError("Gameplay module package contains zip slip path.")
    suffix = Path(normalized).suffix.lower()
    file_name = Path(normalized).name.lower()
    if suffix in FORBIDDEN_CODE_SUFFIXES:
        raise GameplayModulePackageError("Gameplay module package contains executable code.")
    if file_name in SENSITIVE_FILE_NAMES or suffix in SENSITIVE_SUFFIXES:
        raise GameplayModulePackageError("Gameplay module package contains sensitive local files.")


def _validate_checksums(archive: ZipFile, manifest: GameplayModulePackageManifest) -> None:
    actual_files = sorted(
        name
        for name in archive.namelist()
        if name != "gameplay_module_package_manifest.json" and not name.endswith("/")
    )
    if sorted(manifest.checksums) != actual_files:
        raise GameplayModulePackageError("Gameplay module package checksums do not match included files.")
    for name in actual_files:
        expected = manifest.checksums.get(name)
        actual = _sha256_bytes(archive.read(name))
        if expected != actual:
            raise GameplayModulePackageError(f"Gameplay module package checksum mismatch: {name}")


def _package_files(module_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(module_path.rglob("*"), key=lambda item: str(item)):
        if not path.is_file():
            continue
        relative = path.relative_to(module_path).as_posix()
        _validate_archive_name(f"gameplay_modules/{module_path.name}/{relative}")
        content = path.read_text(encoding="utf-8", errors="ignore")
        if _contains_secret_like_text(content):
            raise GameplayModulePackageError("Gameplay module package contains secret-like text.")
        files.append(path)
    return files


def _safe_module_target(modules_root: Path, module_id: str) -> Path:
    if not module_id or any(token in module_id for token in ("/", "\\", "..")):
        raise GameplayModulePackageError("Invalid gameplay module id.")
    root = modules_root.resolve()
    target = (root / module_id).resolve()
    if root != target and root not in target.parents:
        raise GameplayModulePackageError("Gameplay module import target escapes module root.")
    return target


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _contains_secret_like_text(value: str) -> bool:
    lowered = value.lower()
    return any(token.lower() in lowered for token in SECRET_TOKENS)
