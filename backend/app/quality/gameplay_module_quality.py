from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.engine.action_mod_validator import ActionModValidationReport, validate_action_mods
from app.engine.actions.declarative import DeclarativeActionDefinition
from app.engine.gameplay_module_loader import (
    GameplayModuleLoader,
    GameplayModuleLoaderError,
    GameplayModuleManifest,
    GameplayModuleValidationReport,
)
from app.engine.content.validator import ValidationIssue, ValidationSeverity
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class GameplayModuleQualityCheckStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"


class GameplayModuleQualityGateCheck(BaseModel):
    name: str
    status: GameplayModuleQualityCheckStatus
    summary: str
    issue_codes: list[str] = Field(default_factory=list)


class GameplayModuleQualityGateReport(BaseModel):
    module_id: str
    passed: bool
    checks: list[GameplayModuleQualityGateCheck] = Field(default_factory=list)
    blockers: list[QualityIssue] = Field(default_factory=list)
    warnings: list[QualityIssue] = Field(default_factory=list)
    quality_report: WorldQualityReport
    summary: dict[str, Any] = Field(default_factory=dict)

    def normal_copy(self) -> "GameplayModuleQualityGateReport":
        return self.model_copy(
            update={
                "blockers": [issue.normal_copy() for issue in self.blockers],
                "warnings": [issue.normal_copy() for issue in self.warnings],
                "quality_report": self.quality_report.normal_copy(),
                "summary": _strip_debug_only(self.summary),
            },
            deep=True,
        )

    def model_dump_normal(self) -> dict[str, Any]:
        return self.normal_copy().model_dump(mode="json", exclude_none=True)


def run_action_mod_quality_gate(
    action_definitions: list[DeclarativeActionDefinition],
    *,
    module_id: str = "standalone",
    manifest: object | None = None,
) -> WorldQualityReport:
    validation = validate_action_mods(action_definitions, module_id=module_id, manifest=manifest)
    return action_mod_validation_to_quality_report(validation)


def action_mod_validation_to_quality_report(report: ActionModValidationReport) -> WorldQualityReport:
    issues: list[QualityIssue] = []
    for issue in report.errors:
        issues.append(
            QualityIssue(
                id=f"action_mod:{issue.code}:{issue.path}",
                severity=QualityIssueSeverity.ERROR,
                category="gameplay_module_action_mod",
                file=issue.file,
                path=issue.path,
                entity_id=issue.ref_id,
                message=issue.message,
                safe_details={"code": issue.code, "suggestion": issue.suggestion},
            )
        )
    for issue in report.warnings:
        issues.append(
            QualityIssue(
                id=f"action_mod:{issue.code}:{issue.path}",
                severity=QualityIssueSeverity.WARNING,
                category="gameplay_module_action_mod",
                file=issue.file,
                path=issue.path,
                entity_id=issue.ref_id,
                message=issue.message,
                safe_details={"code": issue.code, "suggestion": issue.suggestion},
            )
        )
    return WorldQualityReport(
        world_id=report.module_id,
        categories=["gameplay_module_action_mod"],
        issues=issues,
        metrics=[
            QualityMetric(
                name="action_mod_validation_errors",
                value=len(report.errors),
                category="gameplay_module_action_mod",
                threshold=0,
                status=QualityMetricStatus.OK if not report.errors else QualityMetricStatus.ERROR,
            ),
            QualityMetric(
                name="action_mod_validation_warnings",
                value=len(report.warnings),
                category="gameplay_module_action_mod",
                status=QualityMetricStatus.OK if not report.warnings else QualityMetricStatus.WARNING,
            ),
        ],
        summary={
            "ok": report.ok,
            "errors": len(report.errors),
            "warnings": len(report.warnings),
        },
        recommended_actions=["Fix Action Mod validation errors before enabling or exporting gameplay modules."]
        if report.errors
        else [],
    )


def run_gameplay_module_quality_gate(
    module_id: str,
    *,
    modules_root: str | Path = "gameplay_modules",
) -> GameplayModuleQualityGateReport:
    """Run a no-execution safety gate for a declarative gameplay module."""

    loader = GameplayModuleLoader(modules_root)
    try:
        manifest = loader.load_manifest_only(module_id)
        validation = loader.validate_module(module_id)
    except GameplayModuleLoaderError as exc:
        validation = GameplayModuleValidationReport(module_id=module_id)
        validation.add(
            ValidationSeverity.ERROR,
            "gameplay_module.yaml",
            "Gameplay module manifest could not be loaded safely.",
            code="gameplay_module_manifest_invalid",
            ref_id=module_id,
        )
        manifest = None
        loader_error = str(exc)
    else:
        loader_error = None

    issues = _quality_issues_from_module_validation(validation)
    manifest_warnings = _quality_test_warnings(module_id, manifest)
    issues.extend(manifest_warnings)
    quality_report = _quality_report_from_issues(module_id, issues)
    checks = _build_checks(validation, manifest, loader_error=loader_error)

    blockers = [
        issue
        for issue in issues
        if issue.severity in {QualityIssueSeverity.ERROR, QualityIssueSeverity.BLOCKER}
    ]
    warnings = [issue for issue in issues if issue.severity == QualityIssueSeverity.WARNING]
    passed = not blockers
    summary = {
        "module_id": module_id,
        "passed": passed,
        "blockers": len(blockers),
        "warnings": len(warnings),
        "checks": {check.name: check.status.value for check in checks},
        "executes_module_code": False,
        "calls_real_llm": False,
        "modifies_active_save": False,
        "normal_report_redacted": True,
    }
    return GameplayModuleQualityGateReport(
        module_id=module_id,
        passed=passed,
        checks=checks,
        blockers=blockers,
        warnings=warnings,
        quality_report=quality_report.normal_copy(),
        summary=summary,
    ).normal_copy()


def _quality_issues_from_module_validation(report: GameplayModuleValidationReport) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for issue in report.errors:
        issues.append(_quality_issue_from_module_issue(issue, QualityIssueSeverity.ERROR))
    for issue in report.warnings:
        issues.append(_quality_issue_from_module_issue(issue, QualityIssueSeverity.WARNING))
    return issues


def _quality_issue_from_module_issue(issue: ValidationIssue, severity: QualityIssueSeverity) -> QualityIssue:
    return QualityIssue(
        id=f"gameplay_module:{issue.code}:{issue.path}",
        severity=severity,
        category="gameplay_module_quality_gate",
        file=issue.file,
        path=issue.path,
        entity_id=issue.ref_id,
        message=_safe_module_issue_message(issue),
        safe_details={"code": issue.code, "ref_id": issue.ref_id, "suggestion": issue.suggestion},
    )


def _safe_module_issue_message(issue: ValidationIssue) -> str:
    hidden_leak_codes = {
        "action_mod_hidden_output_visible",
        "action_mod_hidden_outcome_visible_policy",
    }
    if issue.code in hidden_leak_codes:
        return "Module hidden output policy would expose hidden gameplay content in a normal/player-visible result."
    return issue.message


def _quality_test_warnings(module_id: str, manifest: GameplayModuleManifest | None) -> list[QualityIssue]:
    if manifest is None:
        return []
    required_tests = {
        "action_mod_validation": "Gameplay module should declare action mod validation coverage.",
        "hidden_leak_suite": "Gameplay module should declare hidden leak suite coverage.",
        "module_regression": "Gameplay module should declare module regression coverage.",
    }
    declared = set(manifest.quality_tests)
    warnings: list[QualityIssue] = []
    for test_id, message in required_tests.items():
        if test_id not in declared:
            warnings.append(
                QualityIssue(
                    id=f"gameplay_module_quality_gate:missing_quality_test:{test_id}",
                    severity=QualityIssueSeverity.WARNING,
                    category="gameplay_module_quality_gate",
                    file="gameplay_module.yaml",
                    path="quality_tests",
                    entity_id=module_id,
                    message=message,
                    safe_details={"code": "gameplay_module_missing_quality_test", "test_id": test_id},
                )
            )
    return warnings


def _quality_report_from_issues(module_id: str, issues: list[QualityIssue]) -> WorldQualityReport:
    errors = [issue for issue in issues if issue.severity in {QualityIssueSeverity.ERROR, QualityIssueSeverity.BLOCKER}]
    warnings = [issue for issue in issues if issue.severity == QualityIssueSeverity.WARNING]
    return WorldQualityReport(
        world_id=module_id,
        categories=["gameplay_module_quality_gate"],
        issues=issues,
        metrics=[
            QualityMetric(
                name="gameplay_module_quality_gate_errors",
                value=len(errors),
                category="gameplay_module_quality_gate",
                threshold=0,
                status=QualityMetricStatus.OK if not errors else QualityMetricStatus.ERROR,
            ),
            QualityMetric(
                name="gameplay_module_quality_gate_warnings",
                value=len(warnings),
                category="gameplay_module_quality_gate",
                status=QualityMetricStatus.OK if not warnings else QualityMetricStatus.WARNING,
            ),
        ],
        summary={"ok": not errors, "errors": len(errors), "warnings": len(warnings)},
        recommended_actions=["Fix module quality gate blockers before enabling, packaging, or publishing gameplay modules."]
        if errors
        else [],
    )


def _build_checks(
    validation: GameplayModuleValidationReport,
    manifest: GameplayModuleManifest | None,
    *,
    loader_error: str | None,
) -> list[GameplayModuleQualityGateCheck]:
    codes = {issue.code for issue in [*validation.errors, *validation.warnings]}
    return [
        _check("manifest_valid", not loader_error, "Manifest loads as declarative metadata only.", ["gameplay_module_manifest_invalid"] if loader_error else []),
        _check("permissions_safe", "gameplay_module_forbidden_permission" not in codes, "Module permissions remain within the safe declarative boundary.", _matching(codes, {"gameplay_module_forbidden_permission", "action_mod_execute_code_forbidden"})),
        _check("actions_valid", not any(code.startswith("action_mod_") for code in codes), "Declarative action definitions pass action mod validation.", [code for code in sorted(codes) if code.startswith("action_mod_")]),
        _check("state_schema_extensions_valid", not any(code in codes for code in {"gameplay_module_unsafe_state_extension", "gameplay_module_duplicate_state_extension"}), "State schema extensions use module-safe prefixes.", _matching(codes, {"gameplay_module_unsafe_state_extension", "gameplay_module_duplicate_state_extension"})),
        _check("save_compatibility_valid", not any(code in codes for code in {"gameplay_module_invalid_save_compatibility", "gameplay_module_missing_migration_defaults"}), "Save compatibility and migration defaults are declared safely.", _matching(codes, {"gameplay_module_invalid_save_compatibility", "gameplay_module_missing_migration_defaults"})),
        _declared_test_check("action_tests_pass", manifest, "action_mod_validation", "Action validation coverage is declared and loader validation passed.", codes),
        _check("hidden_leak_suite_pass", not any(code in codes for code in {"action_mod_hidden_output_visible", "action_mod_hidden_outcome_visible_policy"}), "Hidden module output is not exposed to normal/player-visible reports.", _matching(codes, {"action_mod_hidden_output_visible", "action_mod_hidden_outcome_visible_policy"})),
        _declared_test_check("module_regression_pass", manifest, "module_regression", "Module regression coverage is declared and metadata validation passed.", codes),
        _check("no_forbidden_paths", not any("forbidden_state_delta_path" in code or "unsafe_state_extension" in code for code in codes), "StateDelta paths stay inside approved declarative prefixes.", [code for code in sorted(codes) if "forbidden_state_delta_path" in code or "unsafe_state_extension" in code]),
        _check("no_execute_code", not any(code in codes for code in {"gameplay_module_executable_code_forbidden", "gameplay_module_forbidden_permission", "action_mod_execute_code_forbidden"}), "Module package contains no executable code permission or executable files.", _matching(codes, {"gameplay_module_executable_code_forbidden", "gameplay_module_forbidden_permission", "action_mod_execute_code_forbidden"})),
    ]


def _declared_test_check(
    name: str,
    manifest: GameplayModuleManifest | None,
    test_id: str,
    summary: str,
    validation_codes: set[str],
) -> GameplayModuleQualityGateCheck:
    if any(code.startswith("action_mod_") for code in validation_codes):
        return _check(name, False, summary, [code for code in sorted(validation_codes) if code.startswith("action_mod_")])
    if manifest is None:
        return GameplayModuleQualityGateCheck(
            name=name,
            status=GameplayModuleQualityCheckStatus.SKIPPED,
            summary="Skipped because the manifest could not be loaded.",
            issue_codes=["gameplay_module_manifest_invalid"],
        )
    if test_id not in set(manifest.quality_tests):
        return GameplayModuleQualityGateCheck(
            name=name,
            status=GameplayModuleQualityCheckStatus.WARNING,
            summary=f"{summary} Missing declared quality test: {test_id}.",
            issue_codes=["gameplay_module_missing_quality_test"],
        )
    return _check(name, True, summary, [])


def _check(
    name: str,
    passed: bool,
    summary: str,
    issue_codes: list[str],
) -> GameplayModuleQualityGateCheck:
    return GameplayModuleQualityGateCheck(
        name=name,
        status=GameplayModuleQualityCheckStatus.PASS if passed else GameplayModuleQualityCheckStatus.FAIL,
        summary=summary,
        issue_codes=sorted(set(issue_codes)),
    )


def _matching(codes: set[str], expected: set[str]) -> list[str]:
    return sorted(codes & expected)


def _strip_debug_only(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_debug_only(item)
            for key, item in value.items()
            if key != "hidden_details_debug_only" and not str(key).endswith("_debug_only")
        }
    if isinstance(value, list):
        return [_strip_debug_only(item) for item in value]
    return value
