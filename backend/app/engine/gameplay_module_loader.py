from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES, compare_versions
from app.engine.content.validator import ValidationIssue, ValidationSeverity
from app.engine.action_mod_validator import validate_action_mod_files
from app.engine.gameplay_modules import ModuleEventType, ModulePermission, ModuleStateExtension


class GameplayModuleLoaderError(ValueError):
    """Raised when a gameplay module manifest is unsafe or invalid."""


class GameplayModuleType(str):
    ACTION_PACK = "action_pack"
    RULE_PACK = "rule_pack"
    GAMEPLAY_SYSTEM = "gameplay_system"
    HYBRID = "hybrid"


class GameplayModulePermissions(BaseModel):
    execute_code: bool = False
    access_network: bool = False
    access_filesystem: bool = False
    call_llm: bool = False
    modify_game_state_directly: bool = False


class GameplayModuleSaveCompatibility(BaseModel):
    safe_to_add_mid_save: bool = True
    migration_required: bool = False
    requires_new_game: bool = False
    migration_defaults: dict[str, Any] = Field(default_factory=dict)


class GameplayActionDeclaration(BaseModel):
    id: str
    action_type: str
    handler: str | None = None

    @field_validator("id", "action_type")
    @classmethod
    def validate_safe_identifier(cls, value: str) -> str:
        if not _is_safe_dotted_id(value):
            raise ValueError("Action ids and types must be safe dot identifiers")
        return value


class GameplayRuleDeclaration(BaseModel):
    id: str
    rule_type: str

    @field_validator("id", "rule_type")
    @classmethod
    def validate_safe_identifier(cls, value: str) -> str:
        if not _is_safe_dotted_id(value):
            raise ValueError("Rule ids and types must be safe dot identifiers")
        return value


class GameplayModuleManifest(BaseModel):
    id: str
    name: str
    version: str
    module_type: str
    engine_version_min: str
    schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    required_systems: list[str] = Field(default_factory=list)
    provided_actions: list[GameplayActionDeclaration] = Field(default_factory=list)
    provided_rules: list[GameplayRuleDeclaration] = Field(default_factory=list)
    state_schema_extensions: list[ModuleStateExtension] = Field(default_factory=list)
    event_types: list[ModuleEventType] = Field(default_factory=list)
    permissions: GameplayModulePermissions = Field(default_factory=GameplayModulePermissions)
    save_compatibility: GameplayModuleSaveCompatibility = Field(default_factory=GameplayModuleSaveCompatibility)
    quality_tests: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not _is_safe_id(value):
            raise ValueError("Module id must be a safe local identifier")
        return value

    @field_validator("module_type")
    @classmethod
    def validate_module_type(cls, value: str) -> str:
        allowed = {
            GameplayModuleType.ACTION_PACK,
            GameplayModuleType.RULE_PACK,
            GameplayModuleType.GAMEPLAY_SYSTEM,
            GameplayModuleType.HYBRID,
        }
        if value not in allowed:
            raise ValueError(f"Unsupported gameplay module type: {value}")
        return value

    @field_validator("dependencies", "conflicts", "required_systems", "quality_tests")
    @classmethod
    def validate_safe_refs(cls, values: list[str]) -> list[str]:
        for value in values:
            if not _is_safe_dotted_id(value) or "/" in value or "\\" in value or ".." in value:
                raise ValueError(f"Unsafe gameplay module reference: {value}")
        return values

    @model_validator(mode="after")
    def validate_manifest(self) -> "GameplayModuleManifest":
        if not self.provided_actions and not self.provided_rules and not self.state_schema_extensions:
            raise ValueError("Gameplay module must provide actions, rules, or state schema extensions")
        return self


class GameplayModuleInfo(BaseModel):
    manifest: GameplayModuleManifest
    path: Path
    model_config = {"arbitrary_types_allowed": True}


class GameplayModuleDependencyReport(BaseModel):
    ok: bool
    missing_dependencies: dict[str, list[str]] = Field(default_factory=dict)


class GameplayModuleConflictReport(BaseModel):
    ok: bool
    conflicts: list[tuple[str, str]] = Field(default_factory=list)


class GameplayModuleValidationReport(BaseModel):
    module_id: str
    ok: bool = True
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)

    def add(self, severity: ValidationSeverity, path: str, message: str, *, code: str, ref_id: str | None = None) -> None:
        issue = ValidationIssue(
            severity=severity,
            file="gameplay_module.yaml",
            path=path,
            code=code,
            message=message,
            ref_id=ref_id,
        )
        if severity == ValidationSeverity.ERROR:
            self.errors.append(issue)
        else:
            self.warnings.append(issue)
        self.ok = not self.errors


class GameplayModuleLoader:
    def __init__(self, modules_root: str | Path = "gameplay_modules") -> None:
        self.modules_root = Path(modules_root)

    def discover_modules(self) -> list[GameplayModuleInfo]:
        if not self.modules_root.exists():
            return []
        modules: list[GameplayModuleInfo] = []
        for module_path in sorted(self.modules_root.iterdir(), key=lambda path: path.name):
            if not module_path.is_dir():
                continue
            manifest_path = module_path / "gameplay_module.yaml"
            if not manifest_path.exists():
                continue
            modules.append(GameplayModuleInfo(manifest=self._read_manifest(manifest_path), path=module_path))
        return modules

    def load_manifest_only(self, module_id: str) -> GameplayModuleManifest:
        return self._get_module(module_id).manifest

    def validate_module(self, module_id: str) -> GameplayModuleValidationReport:
        module = self._get_module(module_id)
        report = GameplayModuleValidationReport(module_id=module.manifest.id)
        self._validate_manifest_versions(module.manifest, report)
        self._validate_permissions(module.manifest, report)
        self._validate_state_schema_extensions(module.manifest, report)
        self._validate_save_compatibility(module.manifest, report)
        self._validate_no_executable_code(module, report)
        self._validate_action_mods(module, report)
        report.ok = not report.errors
        return report

    def resolve_dependencies(self, enabled_module_ids: list[str] | None = None) -> GameplayModuleDependencyReport:
        modules = {module.manifest.id: module.manifest for module in self.discover_modules()}
        selected_ids = set(enabled_module_ids or modules)
        missing: dict[str, list[str]] = {}
        for module_id in sorted(selected_ids):
            manifest = modules.get(module_id)
            if manifest is None:
                missing[module_id] = ["module_not_found"]
                continue
            absent = [dependency for dependency in manifest.dependencies if _dependency_id(dependency) not in selected_ids]
            if absent:
                missing[module_id] = absent
        return GameplayModuleDependencyReport(ok=not missing, missing_dependencies=missing)

    def detect_conflicts(self, enabled_module_ids: list[str] | None = None) -> GameplayModuleConflictReport:
        modules = {module.manifest.id: module.manifest for module in self.discover_modules()}
        selected_ids = set(enabled_module_ids or modules)
        conflicts: set[tuple[str, str]] = set()
        for module_id in selected_ids:
            manifest = modules.get(module_id)
            if manifest is None:
                continue
            for conflict_id in manifest.conflicts:
                active_conflict_id = _dependency_id(conflict_id)
                if active_conflict_id in selected_ids:
                    conflicts.add(tuple(sorted((module_id, active_conflict_id))))
        return GameplayModuleConflictReport(ok=not conflicts, conflicts=sorted(conflicts))

    def _get_module(self, module_id: str) -> GameplayModuleInfo:
        if not _is_safe_id(module_id):
            raise GameplayModuleLoaderError(f"Invalid gameplay module id: {module_id}")
        for module in self.discover_modules():
            if module.manifest.id == module_id:
                return module
        raise GameplayModuleLoaderError(f"Gameplay module not found: {module_id}")

    def _read_manifest(self, manifest_path: Path) -> GameplayModuleManifest:
        root = self.modules_root.resolve()
        resolved = manifest_path.resolve()
        if root != resolved and root not in resolved.parents:
            raise GameplayModuleLoaderError(f"Gameplay module manifest escapes module root: {manifest_path}")
        try:
            data = _read_yaml_mapping(resolved)
            return GameplayModuleManifest.model_validate(data)
        except (ValidationError, ValueError) as exc:
            raise GameplayModuleLoaderError(f"Invalid gameplay module manifest {manifest_path}: {exc}") from exc

    def _validate_manifest_versions(self, manifest: GameplayModuleManifest, report: GameplayModuleValidationReport) -> None:
        if compare_versions(CURRENT_ENGINE_VERSION, manifest.engine_version_min) < 0:
            report.add(
                ValidationSeverity.ERROR,
                "gameplay_module.yaml.engine_version_min",
                f"Engine {CURRENT_ENGINE_VERSION} is below required minimum {manifest.engine_version_min}.",
                code="gameplay_module_engine_version_incompatible",
                ref_id=manifest.id,
            )
        if compare_versions(CURRENT_GAME_STATE_SCHEMA_VERSION, manifest.schema_version) != 0:
            report.add(
                ValidationSeverity.WARNING,
                "gameplay_module.yaml.schema_version",
                f"Gameplay module schema {manifest.schema_version} differs from engine schema {CURRENT_GAME_STATE_SCHEMA_VERSION}.",
                code="gameplay_module_schema_version_mismatch",
                ref_id=manifest.id,
            )

    def _validate_permissions(self, manifest: GameplayModuleManifest, report: GameplayModuleValidationReport) -> None:
        permission_map = manifest.permissions.model_dump()
        for key, enabled in permission_map.items():
            if enabled:
                report.add(
                    ValidationSeverity.ERROR,
                    f"gameplay_module.yaml.permissions.{key}",
                    f"Gameplay module permission {key}=true is not allowed in declarative modules.",
                    code="gameplay_module_forbidden_permission",
                    ref_id=manifest.id,
                )

    def _validate_state_schema_extensions(self, manifest: GameplayModuleManifest, report: GameplayModuleValidationReport) -> None:
        seen: set[str] = set()
        for extension in manifest.state_schema_extensions:
            path = extension.path_prefix
            if path in seen:
                report.add(
                    ValidationSeverity.ERROR,
                    "gameplay_module.yaml.state_schema_extensions",
                    f"Duplicate state extension path: {path}",
                    code="gameplay_module_duplicate_state_extension",
                    ref_id=manifest.id,
                )
            seen.add(path)
            if not path.startswith("flags.") and not path.startswith("social_flags.") and not path.startswith("module_state."):
                report.add(
                    ValidationSeverity.ERROR,
                    "gameplay_module.yaml.state_schema_extensions",
                    f"State extension path is outside approved module-safe prefixes: {path}",
                    code="gameplay_module_unsafe_state_extension",
                    ref_id=manifest.id,
                )

    def _validate_save_compatibility(self, manifest: GameplayModuleManifest, report: GameplayModuleValidationReport) -> None:
        compatibility = manifest.save_compatibility
        if compatibility.requires_new_game and compatibility.safe_to_add_mid_save:
            report.add(
                ValidationSeverity.ERROR,
                "gameplay_module.yaml.save_compatibility",
                "requires_new_game cannot also be safe_to_add_mid_save.",
                code="gameplay_module_invalid_save_compatibility",
                ref_id=manifest.id,
            )
        if compatibility.migration_required and not compatibility.migration_defaults:
            report.add(
                ValidationSeverity.ERROR,
                "gameplay_module.yaml.save_compatibility.migration_defaults",
                "migration_required requires migration_defaults.",
                code="gameplay_module_missing_migration_defaults",
                ref_id=manifest.id,
            )

    def _validate_no_executable_code(self, module: GameplayModuleInfo, report: GameplayModuleValidationReport) -> None:
        root = module.path.resolve()
        for path in sorted(root.rglob("*"), key=lambda item: str(item)):
            if not path.is_file():
                continue
            if path.suffix.lower() in FORBIDDEN_CODE_SUFFIXES:
                report.add(
                    ValidationSeverity.ERROR,
                    str(path.relative_to(root)),
                    "Gameplay module package contains executable code; only declarative data is allowed.",
                    code="gameplay_module_executable_code_forbidden",
                    ref_id=path.name,
                )

    def _validate_action_mods(self, module: GameplayModuleInfo, report: GameplayModuleValidationReport) -> None:
        action_report = validate_action_mod_files(module.path, module.manifest)
        report.errors.extend(action_report.errors)
        report.warnings.extend(action_report.warnings)
        report.ok = not report.errors


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise GameplayModuleLoaderError(f"Invalid YAML in file: {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise GameplayModuleLoaderError(f"Expected YAML mapping in file: {path.name}")
    return data


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _is_safe_dotted_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-", "."} for character in value)


def _dependency_id(value: str) -> str:
    for operator in [">=", "<=", "==", ">", "<"]:
        if operator in value:
            return value.split(operator, 1)[0].strip()
    return value.strip()
