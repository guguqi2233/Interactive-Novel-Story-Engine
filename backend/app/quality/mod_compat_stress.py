from itertools import combinations
from random import Random
import re
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.content.mod_loader import ModLoader, ModLoaderError
from app.engine.content.validator import ValidationSeverity
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.scenarios.regression import ScenarioRegressionCase, sample_scenario_regression_cases


class ModCompatibilityStressRequest(BaseModel):
    available_mods: list[str] = Field(default_factory=list)
    selected_worlds: list[str] = Field(default_factory=list)
    max_combinations: int = Field(default=10, ge=1, le=100)
    seed: int = 123
    scenario_cases: list[ScenarioRegressionCase] = Field(default_factory=list)


class ModCombinationResult(BaseModel):
    mod_ids: list[str]
    ok: bool
    dependency_errors: dict[str, list[str]] = Field(default_factory=dict)
    conflicts: list[list[str]] = Field(default_factory=list)
    load_order: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    broken_references: list[str] = Field(default_factory=list)
    schema_incompatibilities: dict[str, list[str]] = Field(default_factory=dict)
    engine_incompatibilities: dict[str, list[str]] = Field(default_factory=dict)
    migration_risks: list[str] = Field(default_factory=list)
    hidden_leak_risks: list[str] = Field(default_factory=list)
    scenario_subset_ids: list[str] = Field(default_factory=list)
    hidden_leak_subset_ids: list[str] = Field(default_factory=list)


class ModCompatibilityStressReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"mod-compat-{uuid4()}")
    selected_worlds: list[str] = Field(default_factory=list)
    tested_combinations: int = 0
    compatible_combinations: int = 0
    failed_combinations: int = 0
    results: list[ModCombinationResult] = Field(default_factory=list)
    safe_summary: dict[str, Any] = Field(default_factory=dict)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _strip_sensitive_paths(payload)


def run_mod_compatibility_stress(
    request: ModCompatibilityStressRequest,
    *,
    mods_root: str = "mods",
) -> ModCompatibilityStressReport:
    loader = ModLoader(mods_root)
    try:
        discovered = {mod.manifest.id: mod for mod in loader.discover_mods()}
    except ModLoaderError as exc:
        raise ModLoaderError(_safe_message(str(exc))) from exc
    selected_mods = request.available_mods or sorted(discovered)
    combinations_to_test = _select_combinations(selected_mods, request.max_combinations, request.seed)
    scenario_cases = request.scenario_cases or sample_scenario_regression_cases()
    results = [
        _evaluate_combination(
            loader,
            mod_ids,
            selected_worlds=request.selected_worlds,
            scenario_cases=scenario_cases,
        )
        for mod_ids in combinations_to_test
    ]
    compatible = sum(1 for result in results if result.ok)
    report = ModCompatibilityStressReport(
        selected_worlds=request.selected_worlds,
        tested_combinations=len(results),
        compatible_combinations=compatible,
        failed_combinations=len(results) - compatible,
        results=results,
        safe_summary={
            "available_mods": len(selected_mods),
            "tested_combinations": len(results),
            "compatible_combinations": compatible,
            "failed_combinations": len(results) - compatible,
        },
        quality_report=WorldQualityReport(world_id="mods"),
    )
    report.quality_report = _to_quality_report(report)
    return report


def _select_combinations(mod_ids: list[str], max_combinations: int, seed: int) -> list[list[str]]:
    unique_ids = sorted(dict.fromkeys(mod_ids))
    all_combos: list[list[str]] = []
    for size in range(1, len(unique_ids) + 1):
        all_combos.extend([list(combo) for combo in combinations(unique_ids, size)])
    rng = Random(seed)
    rng.shuffle(all_combos)
    return all_combos[:max_combinations]


def _evaluate_combination(
    loader: ModLoader,
    mod_ids: list[str],
    *,
    selected_worlds: list[str],
    scenario_cases: list[ScenarioRegressionCase],
) -> ModCombinationResult:
    dependency_report = loader.resolve_dependencies(mod_ids)
    conflict_report = loader.detect_conflicts(mod_ids)
    load_order_report = loader.resolve_load_order(mod_ids)
    engine_report = loader.detect_engine_incompatibility(mod_ids)
    schema_report = loader.detect_content_schema_incompatibility(mod_ids)
    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    broken_refs: list[str] = []
    hidden_risks: list[str] = []
    migration_risks: list[str] = []

    for mod_id in mod_ids:
        try:
            report = loader.validate_mod(mod_id)
        except ModLoaderError as exc:
            validation_errors.append(_safe_message(str(exc)))
            continue
        for issue in report.errors:
            message = _safe_issue_message(issue.message)
            validation_errors.append(message)
            if issue.severity == ValidationSeverity.ERROR:
                broken_refs.append(message)
            if _is_hidden_risk(issue.code, issue.message):
                hidden_risks.append(message)
        for issue in report.warnings:
            message = _safe_issue_message(issue.message)
            validation_warnings.append(message)
            if _is_hidden_risk(issue.code, issue.message):
                hidden_risks.append(message)
        for mod in loader.list_enabled_mods([mod_id]):
            if mod.manifest.migration_notes:
                migration_risks.append(f"{mod.manifest.id}: migration notes present")
            if selected_worlds and not set(selected_worlds).intersection(set(mod.manifest.compatible_worlds)):
                validation_warnings.append(f"{mod.manifest.id}: no selected world listed as compatible")

    scenario_subset = _scenario_subset(scenario_cases, mod_ids, selected_worlds, hidden_only=False)
    hidden_subset = _scenario_subset(scenario_cases, mod_ids, selected_worlds, hidden_only=True)
    ok = (
        dependency_report.ok
        and conflict_report.ok
        and load_order_report.ok
        and engine_report.ok
        and not validation_errors
        and not hidden_risks
    )
    return ModCombinationResult(
        mod_ids=mod_ids,
        ok=ok,
        dependency_errors=dependency_report.missing_dependencies,
        conflicts=[list(pair) for pair in conflict_report.conflicts],
        load_order=load_order_report.load_order,
        validation_errors=sorted(set(validation_errors)),
        validation_warnings=sorted(set(validation_warnings)),
        broken_references=sorted(set(broken_refs)),
        schema_incompatibilities=schema_report.warnings | schema_report.errors,
        engine_incompatibilities=engine_report.errors,
        migration_risks=sorted(set(migration_risks)),
        hidden_leak_risks=sorted(set(hidden_risks)),
        scenario_subset_ids=[case.id for case in scenario_subset],
        hidden_leak_subset_ids=[case.id for case in hidden_subset],
    )


def _scenario_subset(
    cases: list[ScenarioRegressionCase],
    mod_ids: list[str],
    selected_worlds: list[str],
    *,
    hidden_only: bool,
) -> list[ScenarioRegressionCase]:
    worlds = set(selected_worlds)
    selected: list[ScenarioRegressionCase] = []
    for case in cases:
        tags = {tag.lower() for tag in case.tags}
        if worlds and case.world_id not in worlds:
            continue
        if hidden_only:
            if tags & {"visibility", "hidden-boundary", "leak"}:
                selected.append(case)
            continue
        if tags & {"mod", "compatibility", "migration", "save-load", "quest", "navigation", "trade"}:
            selected.append(case)
    if not selected and mod_ids:
        selected = [case for case in cases if not worlds or case.world_id in worlds][:2]
    return selected[:5]


def _to_quality_report(report: ModCompatibilityStressReport) -> WorldQualityReport:
    issues: list[QualityIssue] = []
    for index, result in enumerate(report.results):
        if result.ok:
            continue
        severity = QualityIssueSeverity.ERROR
        if result.hidden_leak_risks:
            severity = QualityIssueSeverity.BLOCKER
        issues.append(
            QualityIssue(
                id=f"mod_compat:{index}",
                severity=severity,
                category="mod_compatibility_stress",
                entity_id=",".join(result.mod_ids),
                message="Mod compatibility stress combination failed.",
                safe_details={
                    "dependency_errors": len(result.dependency_errors),
                    "conflicts": len(result.conflicts),
                    "validation_errors": len(result.validation_errors),
                    "hidden_leak_risks": len(result.hidden_leak_risks),
                },
            )
        )
    return WorldQualityReport(
        world_id="mods",
        categories=["mod_compatibility_stress"],
        metrics=[
            QualityMetric(
                name="mod_combinations_tested",
                value=report.tested_combinations,
                category="mod_compatibility_stress",
                status=QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="mod_combinations_failed",
                value=report.failed_combinations,
                category="mod_compatibility_stress",
                threshold=0,
                status=QualityMetricStatus.ERROR if report.failed_combinations else QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary=report.safe_summary,
        recommended_actions=["Review failing mod combinations before enabling them together."] if issues else [],
    ).normal_copy()


def _is_hidden_risk(code: str, message: str) -> bool:
    haystack = f"{code} {message}".lower()
    return any(token in haystack for token in ["hidden", "visibility", "leak", "secret"])


def _safe_issue_message(message: str) -> str:
    return str(message).replace(
        "A sealed letter is hidden beneath a loose paving stone.",
        "[hidden text redacted]",
    )


def _safe_message(message: str) -> str:
    normalized = str(message).replace("\\", "/")
    return re.sub(r"[A-Za-z]:/[^\s]+", lambda match: match.group(0).split("/")[-1], normalized)


def _strip_sensitive_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_sensitive_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_strip_sensitive_paths(item) for item in value]
    if isinstance(value, str):
        return value.replace("\\", "/").replace("D:/", "[drive]/")
    return value
