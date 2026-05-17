from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.engine.content.validator import ValidationIssue, ValidationReport, ValidationSeverity, validate_world_pack


class ModLoaderError(ValueError):
    """Raised when a local mod package is unsafe or invalid."""


class ModManifest(BaseModel):
    id: str
    name: str
    version: str
    engine_version_min: str
    engine_version_max: str | None = None
    content_schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    dependencies: list[str] = Field(default_factory=list)
    optional_dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    load_order_hint: int = 0
    compatible_worlds: list[str] = Field(default_factory=list)
    migration_notes: str = ""
    entry_worlds: list[str] = Field(default_factory=list)
    content_paths: list[str] = Field(default_factory=list)
    author: str | None = None
    description: str = ""
    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_lists(self) -> "ModManifest":
        if not self.entry_worlds:
            raise ValueError("Mod manifest requires at least one entry_worlds item")
        if not self.content_paths:
            raise ValueError("Mod manifest requires at least one content_paths item")
        return self


class ModInfo(BaseModel):
    manifest: ModManifest
    path: Path

    model_config = {"arbitrary_types_allowed": True}


class ModValidationReport(BaseModel):
    mod_id: str
    ok: bool = True
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationIssue] = Field(default_factory=list)
    world_reports: dict[str, ValidationReport] = Field(default_factory=dict)

    def add(
        self,
        severity: ValidationSeverity,
        path: str,
        message: str,
        *,
        code: str,
        ref_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        issue = ValidationIssue(
            severity=severity,
            file=_file_from_path(path),
            path=path,
            code=code,
            message=message,
            ref_id=ref_id,
            suggestion=suggestion,
        )
        if severity == ValidationSeverity.ERROR:
            self.errors.append(issue)
        elif severity == ValidationSeverity.WARNING:
            self.warnings.append(issue)
        else:
            self.suggestions.append(issue)
        self.ok = not self.errors and all(report.ok for report in self.world_reports.values())


class DependencyResolutionReport(BaseModel):
    ok: bool
    missing_dependencies: dict[str, list[str]] = Field(default_factory=dict)


class ConflictReport(BaseModel):
    ok: bool
    conflicts: list[tuple[str, str]] = Field(default_factory=list)


class ModVersionReport(BaseModel):
    ok: bool
    errors: dict[str, list[str]] = Field(default_factory=dict)
    warnings: dict[str, list[str]] = Field(default_factory=dict)


class LoadOrderReport(BaseModel):
    ok: bool
    load_order: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


FORBIDDEN_CODE_SUFFIXES = {
    ".py",
    ".pyc",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".bat",
    ".cmd",
    ".ps1",
    ".exe",
    ".dll",
}


class ModLoader:
    def __init__(self, mods_root: str | Path = "mods") -> None:
        self.mods_root = Path(mods_root)

    def discover_mods(self) -> list[ModInfo]:
        if not self.mods_root.exists():
            return []
        mods: list[ModInfo] = []
        for mod_path in sorted(self.mods_root.iterdir(), key=lambda path: path.name):
            if not mod_path.is_dir():
                continue
            manifest_path = mod_path / "mod.yaml"
            if not manifest_path.exists():
                continue
            mods.append(ModInfo(manifest=self._read_manifest(manifest_path), path=mod_path))
        return mods

    def validate_mod(self, mod_id: str) -> ModValidationReport:
        mod = self._get_mod(mod_id)
        report = ModValidationReport(mod_id=mod.manifest.id)
        self._validate_manifest_version(mod, report)
        self._validate_safe_paths(mod, report)
        self._validate_no_executable_code(mod, report)
        self._validate_worlds(mod, report)
        report.ok = not report.errors and all(world_report.ok for world_report in report.world_reports.values())
        return report

    def validate_mod_version(self, mod_id: str) -> ModVersionReport:
        mod = self._get_mod(mod_id)
        errors: dict[str, list[str]] = {}
        warnings: dict[str, list[str]] = {}
        self._collect_version_issues(mod.manifest, errors, warnings)
        return ModVersionReport(ok=not errors, errors=errors, warnings=warnings)

    def resolve_dependencies(self, enabled_mod_ids: list[str] | None = None) -> DependencyResolutionReport:
        mods = {mod.manifest.id: mod.manifest for mod in self.discover_mods()}
        selected_ids = set(enabled_mod_ids or mods)
        missing: dict[str, list[str]] = {}
        for mod_id in sorted(selected_ids):
            manifest = mods.get(mod_id)
            if manifest is None:
                missing[mod_id] = ["mod_not_found"]
                continue
            absent = [
                dependency
                for dependency in manifest.dependencies
                if _dependency_id(dependency) not in selected_ids
            ]
            if absent:
                missing[mod_id] = absent
        return DependencyResolutionReport(ok=not missing, missing_dependencies=missing)

    def detect_dependency_errors(self, enabled_mod_ids: list[str] | None = None) -> DependencyResolutionReport:
        return self.resolve_dependencies(enabled_mod_ids)

    def detect_conflicts(self, enabled_mod_ids: list[str] | None = None) -> ConflictReport:
        mods = {mod.manifest.id: mod.manifest for mod in self.discover_mods()}
        selected_ids = set(enabled_mod_ids or mods)
        conflicts: set[tuple[str, str]] = set()
        for mod_id in selected_ids:
            manifest = mods.get(mod_id)
            if manifest is None:
                continue
            for conflict_id in manifest.conflicts:
                active_conflict_id = _dependency_id(conflict_id)
                if active_conflict_id in selected_ids:
                    conflicts.add(tuple(sorted((mod_id, active_conflict_id))))
        return ConflictReport(ok=not conflicts, conflicts=sorted(conflicts))

    def detect_engine_incompatibility(self, enabled_mod_ids: list[str] | None = None) -> ModVersionReport:
        errors: dict[str, list[str]] = {}
        warnings: dict[str, list[str]] = {}
        for mod in self.list_enabled_mods(enabled_mod_ids):
            self._collect_engine_issues(mod.manifest, errors, warnings)
        return ModVersionReport(ok=not errors, errors=errors, warnings=warnings)

    def detect_content_schema_incompatibility(self, enabled_mod_ids: list[str] | None = None) -> ModVersionReport:
        errors: dict[str, list[str]] = {}
        warnings: dict[str, list[str]] = {}
        for mod in self.list_enabled_mods(enabled_mod_ids):
            self._collect_content_schema_issues(mod.manifest, errors, warnings)
        return ModVersionReport(ok=not errors, errors=errors, warnings=warnings)

    def resolve_load_order(self, enabled_mod_ids: list[str] | None = None) -> LoadOrderReport:
        mods = {mod.manifest.id: mod.manifest for mod in self.discover_mods()}
        selected_ids = sorted(enabled_mod_ids or mods)
        dependency_report = self.resolve_dependencies(selected_ids)
        if not dependency_report.ok:
            return LoadOrderReport(
                ok=False,
                errors=[
                    f"{mod_id} missing dependencies: {','.join(dependencies)}"
                    for mod_id, dependencies in sorted(dependency_report.missing_dependencies.items())
                ],
            )
        remaining = set(selected_ids)
        resolved: list[str] = []
        while remaining:
            ready = [
                mod_id
                for mod_id in remaining
                if all(_dependency_id(dependency) in resolved for dependency in mods[mod_id].dependencies)
            ]
            if not ready:
                return LoadOrderReport(ok=False, errors=["cyclic_mod_dependency"])
            ready.sort(key=lambda mod_id: (mods[mod_id].load_order_hint, mod_id))
            next_mod = ready[0]
            resolved.append(next_mod)
            remaining.remove(next_mod)
        return LoadOrderReport(ok=True, load_order=resolved)

    def list_enabled_mods(self, enabled_mod_ids: list[str] | None = None) -> list[ModInfo]:
        discovered = {mod.manifest.id: mod for mod in self.discover_mods()}
        order_report = self.resolve_load_order(enabled_mod_ids)
        selected_ids = order_report.load_order if order_report.ok else sorted(enabled_mod_ids or discovered)
        return [discovered[mod_id] for mod_id in selected_ids if mod_id in discovered]

    def _get_mod(self, mod_id: str) -> ModInfo:
        if not _is_safe_id(mod_id):
            raise ModLoaderError(f"Invalid mod_id: {mod_id}")
        for mod in self.discover_mods():
            if mod.manifest.id == mod_id:
                return mod
        raise ModLoaderError(f"Mod not found: {mod_id}")

    def _read_manifest(self, path: Path) -> ModManifest:
        try:
            data = _read_yaml_mapping(path)
            return ModManifest.model_validate(data)
        except (ValidationError, ValueError) as exc:
            raise ModLoaderError(f"Invalid mod manifest {path}: {exc}") from exc

    def _validate_safe_paths(self, mod: ModInfo, report: ModValidationReport) -> None:
        for forbidden_field, values in {
            "dependencies": mod.manifest.dependencies,
            "optional_dependencies": mod.manifest.optional_dependencies,
            "conflicts": mod.manifest.conflicts,
        }.items():
            for value in values:
                if any(part in value for part in ["/", "\\", ".."]):
                    report.add(
                        ValidationSeverity.ERROR,
                        f"mod.yaml.{forbidden_field}",
                        f"Unsafe mod reference: {value}",
                        code="unsafe_mod_reference",
                        ref_id=value,
                    )
        for content_path in mod.manifest.content_paths:
            try:
                self._safe_mod_relative_path(mod.path, content_path)
            except ModLoaderError as exc:
                report.add(
                    ValidationSeverity.ERROR,
                    "mod.yaml.content_paths",
                    str(exc),
                    code="unsafe_content_path",
                    ref_id=content_path,
                    suggestion="Use a relative content path inside the mod directory.",
                )

    def _validate_manifest_version(self, mod: ModInfo, report: ModValidationReport) -> None:
        errors: dict[str, list[str]] = {}
        warnings: dict[str, list[str]] = {}
        self._collect_version_issues(mod.manifest, errors, warnings)
        for messages in errors.values():
            for message in messages:
                report.add(
                    ValidationSeverity.ERROR,
                    "mod.yaml.version",
                    message,
                    code="mod_version_incompatible",
                    ref_id=mod.manifest.id,
                )
        for messages in warnings.values():
            for message in messages:
                report.add(
                    ValidationSeverity.WARNING,
                    "mod.yaml.version",
                    message,
                    code="mod_version_warning",
                    ref_id=mod.manifest.id,
                )

    def _collect_version_issues(
        self,
        manifest: ModManifest,
        errors: dict[str, list[str]],
        warnings: dict[str, list[str]],
    ) -> None:
        self._collect_engine_issues(manifest, errors, warnings)
        self._collect_content_schema_issues(manifest, errors, warnings)

    def _collect_engine_issues(
        self,
        manifest: ModManifest,
        errors: dict[str, list[str]],
        warnings: dict[str, list[str]],
    ) -> None:
        if compare_versions(CURRENT_ENGINE_VERSION, manifest.engine_version_min) < 0:
            errors.setdefault(manifest.id, []).append(
                f"Engine {CURRENT_ENGINE_VERSION} is below required minimum {manifest.engine_version_min}."
            )
        if manifest.engine_version_max and compare_versions(CURRENT_ENGINE_VERSION, manifest.engine_version_max) > 0:
            errors.setdefault(manifest.id, []).append(
                f"Engine {CURRENT_ENGINE_VERSION} is above supported maximum {manifest.engine_version_max}."
            )

    def _collect_content_schema_issues(
        self,
        manifest: ModManifest,
        errors: dict[str, list[str]],
        warnings: dict[str, list[str]],
    ) -> None:
        if compare_versions(CURRENT_GAME_STATE_SCHEMA_VERSION, manifest.content_schema_version) != 0:
            warnings.setdefault(manifest.id, []).append(
                f"Content schema {manifest.content_schema_version} differs from engine schema "
                f"{CURRENT_GAME_STATE_SCHEMA_VERSION}."
            )

    def _validate_no_executable_code(self, mod: ModInfo, report: ModValidationReport) -> None:
        try:
            root = mod.path.resolve()
        except OSError as exc:
            report.add(ValidationSeverity.ERROR, str(mod.path), str(exc), code="invalid_mod_path")
            return
        for path in sorted(root.rglob("*"), key=lambda item: str(item)):
            if not path.is_file():
                continue
            if path.suffix.lower() in FORBIDDEN_CODE_SUFFIXES:
                report.add(
                    ValidationSeverity.ERROR,
                    str(path.relative_to(root)),
                    "Mod package contains executable code; only YAML/content data is allowed.",
                    code="mod_executable_code_forbidden",
                    ref_id=path.name,
                    suggestion="Remove executable scripts or code from the local mod package.",
                )

    def _validate_worlds(self, mod: ModInfo, report: ModValidationReport) -> None:
        for content_path in mod.manifest.content_paths:
            try:
                worlds_root = self._safe_mod_relative_path(mod.path, content_path)
            except ModLoaderError:
                continue
            for world_id in mod.manifest.entry_worlds:
                if not _is_safe_id(world_id):
                    report.add(
                        ValidationSeverity.ERROR,
                        "mod.yaml.entry_worlds",
                        f"Invalid entry world id: {world_id}",
                        code="invalid_entry_world",
                        ref_id=world_id,
                    )
                    continue
                world_report = validate_world_pack(world_id, worlds_root=worlds_root)
                report.world_reports[f"{content_path}:{world_id}"] = world_report
                for issue in world_report.errors:
                    report.errors.append(issue)
                for issue in world_report.warnings:
                    report.warnings.append(issue)
                for issue in world_report.suggestions:
                    report.suggestions.append(issue)

    def _safe_mod_relative_path(self, mod_path: Path, relative_path: str) -> Path:
        if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
            raise ModLoaderError(f"Unsafe mod content path: {relative_path}")
        root = mod_path.resolve()
        path = (root / relative_path).resolve()
        if root != path and root not in path.parents:
            raise ModLoaderError(f"Mod content path escapes mod directory: {relative_path}")
        if not path.exists() or not path.is_dir():
            raise ModLoaderError(f"Mod content path not found: {relative_path}")
        return path


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ModLoaderError(f"Invalid YAML in file: {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ModLoaderError(f"Expected YAML mapping in file: {path.name}")
    return data


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def parse_version(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw_part in value.replace("-", ".").split("."):
        digits = "".join(character for character in raw_part if character.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts or [0])


def compare_versions(left: str, right: str) -> int:
    left_parts = list(parse_version(left))
    right_parts = list(parse_version(right))
    length = max(len(left_parts), len(right_parts))
    left_parts.extend([0] * (length - len(left_parts)))
    right_parts.extend([0] * (length - len(right_parts)))
    if left_parts < right_parts:
        return -1
    if left_parts > right_parts:
        return 1
    return 0


def _dependency_id(value: str) -> str:
    for operator in [">=", "<=", "==", ">", "<"]:
        if operator in value:
            return value.split(operator, 1)[0].strip()
    return value.strip()


def _file_from_path(path: str) -> str:
    if ".yaml" in path:
        return path.split(".yaml", 1)[0] + ".yaml"
    if path.endswith(".yaml"):
        return path
    return Path(path).name or "mod"
