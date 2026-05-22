from __future__ import annotations

from pydantic import BaseModel, Field

from app.engine.action_registry import ActionMetadata, ActionRegistry
from app.engine.advanced_modules import AdvancedModuleId
from app.engine.module_state import ModuleStateExtension, ModuleStateField
from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions


class ModuleCompatibilityStressIssue(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    modules: list[str] = Field(default_factory=list)


class ModuleCompatibilityStressReport(BaseModel):
    module_ids: list[str] = Field(default_factory=list)
    passed: bool
    issues: list[ModuleCompatibilityStressIssue] = Field(default_factory=list)
    load_order: list[str] = Field(default_factory=list)


DEFAULT_STRESS_COMBINATIONS: list[list[str]] = [
    [AdvancedModuleId.TACTICAL_COMBAT, AdvancedModuleId.MAGIC],
    [AdvancedModuleId.TACTICAL_COMBAT, AdvancedModuleId.HACKING],
    [AdvancedModuleId.ECONOMY_SIM, AdvancedModuleId.FACTION_WAR],
    [AdvancedModuleId.CRAFTING, AdvancedModuleId.ECONOMY_SIM],
    [AdvancedModuleId.SURVIVAL_TRAVEL, AdvancedModuleId.FACTION_WAR],
    [AdvancedModuleId.CULTIVATION, AdvancedModuleId.MAGIC],
    [AdvancedModuleId.DEDUCTION, "crime_witness"],
    [
        AdvancedModuleId.TACTICAL_COMBAT,
        AdvancedModuleId.ECONOMY_SIM,
        AdvancedModuleId.FACTION_WAR,
        AdvancedModuleId.MAGIC,
        AdvancedModuleId.HACKING,
        AdvancedModuleId.CRAFTING,
        AdvancedModuleId.DEDUCTION,
        AdvancedModuleId.SURVIVAL_TRAVEL,
        AdvancedModuleId.CULTIVATION,
    ],
]


def run_module_compatibility_stress(
    module_ids: list[str],
    *,
    extensions: list[ModuleStateExtension] | None = None,
    actions: list[ActionMetadata] | None = None,
    permissions: dict[str, ModulePermissionSet] | None = None,
    migration_failures: list[str] | None = None,
    hidden_leak_modules: list[str] | None = None,
) -> ModuleCompatibilityStressReport:
    issues: list[ModuleCompatibilityStressIssue] = []
    seen_namespaces: dict[str, str] = {}
    for extension in extensions or _default_extensions(module_ids):
        namespace = extension.namespace
        if namespace in seen_namespaces:
            issues.append(ModuleCompatibilityStressIssue(code="state_namespace_conflict", severity="blocker", message=f"State namespace conflict: {namespace}", modules=[seen_namespaces[namespace], extension.module_id]))
        seen_namespaces[namespace] = extension.module_id

    registry = ActionRegistry(include_core=True)
    action_ids: set[str] = set()
    alias_map: dict[str, list[str]] = {}
    for metadata in actions or []:
        if metadata.id in action_ids:
            issues.append(ModuleCompatibilityStressIssue(code="action_id_conflict", severity="blocker", message=f"Action id conflict: {metadata.id}", modules=[metadata.module_id or "unknown"]))
        action_ids.add(metadata.id)
        for alias in [metadata.id, metadata.label, *metadata.aliases]:
            alias_map.setdefault(alias.lower(), []).append(metadata.id)
        if registry.get_action_definition(metadata.id):
            issues.append(ModuleCompatibilityStressIssue(code="action_core_conflict", severity="blocker", message=f"Action conflicts with core action: {metadata.id}", modules=[metadata.module_id or "unknown"]))
    for alias, ids in alias_map.items():
        if len(set(ids)) > 1:
            issues.append(ModuleCompatibilityStressIssue(code="alias_conflict", severity="blocker", message=f"Alias conflict: {alias}", modules=sorted(set(ids))))

    for module_id, permission_set in (permissions or {}).items():
        report = validate_module_permissions(permission_set)
        if not report.ok:
            issues.append(ModuleCompatibilityStressIssue(code="permission_conflict", severity="blocker", message="Dangerous permission requested.", modules=[module_id]))
    for module_id in migration_failures or []:
        issues.append(ModuleCompatibilityStressIssue(code="migration_conflict", severity="blocker", message="Module migration failed.", modules=[module_id]))
    for module_id in hidden_leak_modules or []:
        issues.append(ModuleCompatibilityStressIssue(code="hidden_leak_risk", severity="blocker", message="Hidden leak risk detected.", modules=[module_id]))

    load_order = sorted(str(module_id) for module_id in module_ids)
    return ModuleCompatibilityStressReport(
        module_ids=[str(module_id) for module_id in module_ids],
        passed=not any(issue.severity == "blocker" for issue in issues),
        issues=issues,
        load_order=load_order,
    )


def run_default_module_compatibility_stress() -> list[ModuleCompatibilityStressReport]:
    return [run_module_compatibility_stress([str(item) for item in combination]) for combination in DEFAULT_STRESS_COMBINATIONS]


def _default_extensions(module_ids: list[str]) -> list[ModuleStateExtension]:
    return [
        ModuleStateExtension(
            module_id=str(module_id),
            namespace=f"state.modules.{module_id}",
            fields=[ModuleStateField(name="enabled", field_type="bool", default=True)],
            default_values={"enabled": True},
        )
        for module_id in module_ids
    ]
