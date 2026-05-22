from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.state_delta import StateDelta, StateDeltaError, StateDeltaOperation, apply_delta
from app.core.world_state import GameState


MODULE_NAMESPACE_PREFIX = "modules"


class ModuleStateVisibilityPolicy(StrEnum):
    PUBLIC_SUMMARY = "public_summary"
    PLAYER_KNOWN = "player_known"
    DEBUG_ONLY = "debug_only"


class ModuleStateSavePolicy(StrEnum):
    PERSIST = "persist"
    EPHEMERAL = "ephemeral"


class ModuleStateField(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    field_type: str = "dict"
    required: bool = False
    default: Any = None
    description: str = ""

    @field_validator("name")
    @classmethod
    def reject_core_names(cls, value: str) -> str:
        if value in {"schema_version", "engine_version", "contract_version", "player", "facts", "npcs", "quests"}:
            raise ValueError("module state field cannot shadow core GameState fields")
        return value


class ModuleStateExtension(BaseModel):
    module_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    namespace: str
    fields: list[ModuleStateField] = Field(default_factory=list)
    default_values: dict[str, Any] = Field(default_factory=dict)
    migration_required: bool = False
    visibility_policy: ModuleStateVisibilityPolicy = ModuleStateVisibilityPolicy.PLAYER_KNOWN
    save_policy: ModuleStateSavePolicy = ModuleStateSavePolicy.PERSIST

    @model_validator(mode="after")
    def validate_namespace(self) -> "ModuleStateExtension":
        expected = f"state.modules.{self.module_id}"
        if self.namespace != expected:
            raise ValueError(f"module state namespace must be {expected}")
        field_names = {field.name for field in self.fields}
        unknown_defaults = set(self.default_values).difference(field_names)
        if unknown_defaults:
            raise ValueError(f"default_values contain undeclared fields: {', '.join(sorted(unknown_defaults))}")
        return self


def module_state_path(module_id: str, *parts: str) -> str:
    if not module_id or "." in module_id:
        raise StateDeltaError("module_id must be a non-empty id without dot separators")
    for part in parts:
        if not part or part in {"..", ".", "secrets", "api_key", "debug_memory", "raw_env"}:
            raise StateDeltaError(f"forbidden module state path segment: {part}")
    return ".".join([MODULE_NAMESPACE_PREFIX, module_id, *parts])


def validate_module_state_delta(delta: StateDelta, module_id: str) -> None:
    prefix = f"{MODULE_NAMESPACE_PREFIX}.{module_id}"
    if delta.path != prefix and not delta.path.startswith(f"{prefix}."):
        raise StateDeltaError(f"module StateDelta must stay inside {prefix}")
    if any(part in {"secrets", "api_key", "authorization", "raw_env", "debug_memory"} for part in delta.path.split(".")):
        raise StateDeltaError(f"forbidden sensitive module StateDelta path: {delta.path}")


def inject_module_defaults(state: GameState, extension: ModuleStateExtension) -> GameState:
    next_state = state.model_copy(deep=True)
    module_state = deepcopy(next_state.modules.get(extension.module_id, {}))
    for field in extension.fields:
        if field.name not in module_state:
            module_state[field.name] = deepcopy(extension.default_values.get(field.name, field.default))
    next_state.modules[extension.module_id] = module_state
    return next_state


def apply_module_delta(state: GameState, module_id: str, delta: StateDelta) -> GameState:
    validate_module_state_delta(delta, module_id)
    if module_id not in state.modules:
        state = state.model_copy(update={"modules": {**state.modules, module_id: {}}}, deep=True)
    return apply_delta(state, delta)


class ModuleMigrationType(StrEnum):
    ADD_MODULE_DEFAULTS = "add_module_defaults"
    UPGRADE_MODULE_SCHEMA = "upgrade_module_schema"
    DISABLE_MODULE_PRESERVE_STATE = "disable_module_preserve_state"
    REMOVE_MODULE_STATE = "remove_module_state"


class ModuleMigrationStep(BaseModel):
    step_id: str
    migration_type: ModuleMigrationType
    module_id: str
    description: str = ""
    defaults: dict[str, Any] = Field(default_factory=dict)
    from_schema_version: str | None = None
    to_schema_version: str | None = None
    destructive: bool = False

    @model_validator(mode="after")
    def validate_destructive_remove(self) -> "ModuleMigrationStep":
        if self.migration_type == ModuleMigrationType.REMOVE_MODULE_STATE and not self.destructive:
            raise ValueError("remove_module_state requires destructive=True and explicit confirmation")
        return self


class ModuleMigrationPlan(BaseModel):
    plan_id: str
    project_id: str = "local"
    module_id: str
    steps: list[ModuleMigrationStep] = Field(default_factory=list)
    requires_confirmation: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ModuleMigrationReport(BaseModel):
    plan_id: str
    dry_run: bool
    applied: bool = False
    module_id: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    resulting_module_state: dict[str, Any] = Field(default_factory=dict)
    migration_history: list[dict[str, Any]] = Field(default_factory=list)


class ModuleMigrationService:
    def plan_module_migration(
        self,
        *,
        state: GameState,
        extension: ModuleStateExtension,
        project_id: str = "local",
    ) -> ModuleMigrationPlan:
        warnings = ["module migration required"] if extension.migration_required else []
        step = ModuleMigrationStep(
            step_id=f"{extension.module_id}:defaults",
            migration_type=ModuleMigrationType.ADD_MODULE_DEFAULTS,
            module_id=extension.module_id,
            description="Inject declared module default state fields.",
            defaults=extension.default_values,
        )
        if extension.module_id in state.modules:
            step = step.model_copy(update={"migration_type": ModuleMigrationType.UPGRADE_MODULE_SCHEMA})
        return ModuleMigrationPlan(
            plan_id=f"{project_id}:{extension.module_id}:migration",
            project_id=project_id,
            module_id=extension.module_id,
            steps=[step],
            warnings=warnings,
        )

    def dry_run_module_migration(self, state: GameState, plan: ModuleMigrationPlan) -> ModuleMigrationReport:
        candidate = state.model_copy(deep=True)
        warnings = list(plan.warnings)
        errors = list(plan.errors)
        try:
            candidate = self._apply_steps(candidate, plan, confirm_destructive=False, record_history=False)
        except Exception as exc:
            errors.append(str(exc))
        return ModuleMigrationReport(
            plan_id=plan.plan_id,
            dry_run=True,
            applied=False,
            module_id=plan.module_id,
            warnings=warnings,
            errors=errors,
            resulting_module_state=deepcopy(candidate.modules.get(plan.module_id, {})),
            migration_history=list(state.module_migration_history),
        )

    def apply_module_migration(
        self,
        state: GameState,
        plan: ModuleMigrationPlan,
        *,
        confirm: bool = False,
        confirm_destructive: bool = False,
    ) -> tuple[GameState, ModuleMigrationReport]:
        if plan.requires_confirmation and not confirm:
            report = ModuleMigrationReport(
                plan_id=plan.plan_id,
                dry_run=False,
                applied=False,
                module_id=plan.module_id,
                warnings=list(plan.warnings),
                errors=["module migration apply requires explicit confirmation"],
            )
            return state, report
        try:
            migrated = self._apply_steps(state.model_copy(deep=True), plan, confirm_destructive=confirm_destructive, record_history=True)
        except Exception as exc:
            report = ModuleMigrationReport(
                plan_id=plan.plan_id,
                dry_run=False,
                applied=False,
                module_id=plan.module_id,
                warnings=list(plan.warnings),
                errors=[str(exc)],
                resulting_module_state=deepcopy(state.modules.get(plan.module_id, {})),
                migration_history=list(state.module_migration_history),
            )
            return state, report
        report = ModuleMigrationReport(
            plan_id=plan.plan_id,
            dry_run=False,
            applied=True,
            module_id=plan.module_id,
            warnings=list(plan.warnings),
            errors=[],
            resulting_module_state=deepcopy(migrated.modules.get(plan.module_id, {})),
            migration_history=list(migrated.module_migration_history),
        )
        return migrated, report

    def _apply_steps(
        self,
        state: GameState,
        plan: ModuleMigrationPlan,
        *,
        confirm_destructive: bool,
        record_history: bool,
    ) -> GameState:
        next_state = state.model_copy(deep=True)
        for step in plan.steps:
            if step.module_id != plan.module_id:
                raise ValueError("migration step module_id does not match plan")
            if step.migration_type in {ModuleMigrationType.ADD_MODULE_DEFAULTS, ModuleMigrationType.UPGRADE_MODULE_SCHEMA}:
                current = deepcopy(next_state.modules.get(step.module_id, {}))
                for key, value in step.defaults.items():
                    current.setdefault(key, deepcopy(value))
                next_state.modules[step.module_id] = current
            elif step.migration_type == ModuleMigrationType.DISABLE_MODULE_PRESERVE_STATE:
                current = deepcopy(next_state.modules.get(step.module_id, {}))
                current["_enabled"] = False
                next_state.modules[step.module_id] = current
            elif step.migration_type == ModuleMigrationType.REMOVE_MODULE_STATE:
                if not confirm_destructive:
                    raise ValueError("remove_module_state requires explicit destructive confirmation")
                next_state.modules.pop(step.module_id, None)
            else:
                raise ValueError(f"unsupported module migration type: {step.migration_type}")
        if record_history:
            history = list(next_state.module_migration_history)
            history.append(
                {
                    "plan_id": plan.plan_id,
                    "module_id": plan.module_id,
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "step_count": len(plan.steps),
                }
            )
            next_state.module_migration_history = history
        return next_state
