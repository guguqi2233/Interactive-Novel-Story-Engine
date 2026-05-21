from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from app.engine.action_registry import ActionRegistry
from app.engine.gameplay_module_loader import GameplayModuleLoader, GameplayModuleLoaderError, GameplayModuleManifest


class ModuleLifecycleState(StrEnum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    COMPATIBLE = "compatible"
    ENABLED = "enabled"
    DISABLED = "disabled"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"


class ModuleCompatibilityReport(BaseModel):
    module_id: str
    ok: bool
    state: ModuleLifecycleState
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ModuleSafeSummary(BaseModel):
    module_id: str
    name: str
    version: str
    state: ModuleLifecycleState
    actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ModuleRegistry:
    def __init__(self, modules_root: str | Path = "gameplay_modules", action_registry: ActionRegistry | None = None) -> None:
        self.loader = GameplayModuleLoader(modules_root)
        self.action_registry = action_registry or ActionRegistry()
        self._enabled: set[str] = set()

    def list_modules(self) -> list[ModuleSafeSummary]:
        summaries: list[ModuleSafeSummary] = []
        for info in self.loader.discover_modules():
            state = ModuleLifecycleState.ENABLED if info.manifest.id in self._enabled else ModuleLifecycleState.DISCOVERED
            summaries.append(_summary(info.manifest, state))
        return summaries

    def validate(self, module_id: str) -> ModuleCompatibilityReport:
        try:
            report = self.loader.validate_module(module_id)
        except GameplayModuleLoaderError as exc:
            return ModuleCompatibilityReport(module_id=module_id, ok=False, state=ModuleLifecycleState.BLOCKED, errors=[str(exc)])
        return ModuleCompatibilityReport(
            module_id=module_id,
            ok=report.ok,
            state=ModuleLifecycleState.VALIDATED if report.ok else ModuleLifecycleState.BLOCKED,
            errors=[issue.message for issue in report.errors],
            warnings=[issue.message for issue in report.warnings],
        )

    def enable_dry_run(self, module_id: str) -> ModuleCompatibilityReport:
        report = self.validate(module_id)
        if not report.ok:
            return report
        deps = self.loader.resolve_dependencies([module_id, *self._enabled])
        conflicts = self.loader.detect_conflicts([module_id, *self._enabled])
        errors: list[str] = []
        if not deps.ok:
            errors.append(f"Missing dependencies: {deps.missing_dependencies}")
        if not conflicts.ok:
            errors.append(f"Module conflicts: {conflicts.conflicts}")
        return ModuleCompatibilityReport(
            module_id=module_id,
            ok=not errors,
            state=ModuleLifecycleState.COMPATIBLE if not errors else ModuleLifecycleState.BLOCKED,
            errors=errors,
            warnings=report.warnings,
        )

    def enable(self, module_id: str, *, confirm_enable: bool = False) -> ModuleCompatibilityReport:
        if not confirm_enable:
            return ModuleCompatibilityReport(module_id=module_id, ok=False, state=ModuleLifecycleState.BLOCKED, errors=["confirm_enable is required"])
        report = self.enable_dry_run(module_id)
        if report.ok:
            self._enabled.add(module_id)
            report.state = ModuleLifecycleState.ENABLED
        return report

    def disable(self, module_id: str, *, confirm_disable: bool = False) -> ModuleCompatibilityReport:
        if not confirm_disable:
            return ModuleCompatibilityReport(module_id=module_id, ok=False, state=ModuleLifecycleState.BLOCKED, errors=["confirm_disable is required"])
        self._enabled.discard(module_id)
        return ModuleCompatibilityReport(module_id=module_id, ok=True, state=ModuleLifecycleState.DISABLED)


def _summary(manifest: GameplayModuleManifest, state: ModuleLifecycleState) -> ModuleSafeSummary:
    return ModuleSafeSummary(
        module_id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        state=state,
        actions=[action.id for action in manifest.provided_actions],
    )

