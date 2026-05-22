from __future__ import annotations

from pydantic import BaseModel, Field

from app.engine.action_registry import ActionMetadata
from app.engine.module_state import ModuleMigrationPlan, ModuleStateExtension
from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions
from app.playtesting.module_playtest import ModulePlaytestReport, run_all_module_playtests
from app.quality.module_compatibility_stress import ModuleCompatibilityStressReport, run_default_module_compatibility_stress


class ModuleQualityGateConfig(BaseModel):
    require_playtests: bool = True
    require_event_log: bool = True
    require_save_load: bool = True
    fail_on_hidden_leak: bool = True
    fail_on_action_conflict: bool = True
    fail_on_migration_failure: bool = True
    fail_on_dangerous_permission: bool = True


class ModuleQualityGateResult(BaseModel):
    passed: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    module_ids: list[str] = Field(default_factory=list)
    playtest_reports: list[ModulePlaytestReport] = Field(default_factory=list)
    compatibility_reports: list[ModuleCompatibilityStressReport] = Field(default_factory=list)


def run_module_quality_gate(
    *,
    module_ids: list[str] | None = None,
    config: ModuleQualityGateConfig | None = None,
    permissions: dict[str, ModulePermissionSet] | None = None,
    state_extensions: list[ModuleStateExtension] | None = None,
    migration_plans: list[ModuleMigrationPlan] | None = None,
    action_metadata: list[ActionMetadata] | None = None,
    playtest_reports: list[ModulePlaytestReport] | None = None,
    compatibility_reports: list[ModuleCompatibilityStressReport] | None = None,
) -> ModuleQualityGateResult:
    config = config or ModuleQualityGateConfig()
    blockers: list[str] = []
    warnings: list[str] = []
    playtest_reports = playtest_reports if playtest_reports is not None else run_all_module_playtests()
    compatibility_reports = compatibility_reports if compatibility_reports is not None else run_default_module_compatibility_stress()
    module_ids = module_ids or sorted({report.module_id for report in playtest_reports})

    for module_id, permission_set in (permissions or {}).items():
        permission_report = validate_module_permissions(permission_set)
        if not permission_report.ok and config.fail_on_dangerous_permission:
            blockers.append(f"dangerous permission requested by {module_id}")

    for extension in state_extensions or []:
        if extension.namespace != f"state.modules.{extension.module_id}":
            blockers.append(f"invalid module state namespace for {extension.module_id}")

    for plan in migration_plans or []:
        if plan.errors and config.fail_on_migration_failure:
            blockers.append(f"migration failure in {plan.module_id}")

    for metadata in action_metadata or []:
        if metadata.source.value == "core" and config.fail_on_action_conflict:
            blockers.append(f"module action conflicts with core action: {metadata.id}")

    if config.require_playtests:
        for report in playtest_reports:
            if not report.success:
                blockers.append(f"module playtest failed: {report.scenario_id}")
            if config.fail_on_hidden_leak and report.hidden_leak_detected:
                blockers.append(f"hidden leak in module playtest: {report.scenario_id}")
            if config.require_event_log and report.event_count <= 0:
                blockers.append(f"missing EventLog coverage: {report.scenario_id}")
            if config.require_save_load and not report.save_load_stable:
                blockers.append(f"save/load instability: {report.scenario_id}")

    for report in compatibility_reports:
        if not report.passed:
            blocker_codes = [issue.code for issue in report.issues if issue.severity == "blocker"]
            if blocker_codes:
                blockers.append(f"compatibility stress failed for {','.join(report.module_ids)}: {','.join(blocker_codes)}")

    return ModuleQualityGateResult(
        passed=not blockers,
        blockers=blockers,
        warnings=warnings,
        module_ids=module_ids,
        playtest_reports=playtest_reports,
        compatibility_reports=compatibility_reports,
    )
