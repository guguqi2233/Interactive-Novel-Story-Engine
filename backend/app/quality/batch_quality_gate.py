from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.engine.content.content_batch_validator import (
    BatchPackageType,
    ContentBatchValidationRequest,
    ContentBatchValidationTarget,
    validate_content_batch,
)
from app.quality.gate import QualityGateConfig, QualityGateProfile, run_quality_gate


class BatchQualityGateThresholds(BaseModel):
    max_warnings: int = Field(default=999, ge=0)
    min_health_score: int = Field(default=0, ge=0, le=100)


class BatchQualityGateRequest(BaseModel):
    package_ids: list[str] = Field(default_factory=list)
    world_ids: list[str] = Field(default_factory=list)
    profile: QualityGateProfile = QualityGateProfile.FAST
    thresholds: BatchQualityGateThresholds = Field(default_factory=BatchQualityGateThresholds)
    include_playtests: bool = False
    include_hidden_leak_suite: bool = True
    include_migration_check: bool = True
    package_type: BatchPackageType = BatchPackageType.SCRIPT_PACKAGE
    worlds_root: str = "worlds"
    packages_root: str = "packages"
    mods_root: str = "mods"


class BatchQualityGateItemResult(BaseModel):
    item_id: str
    item_type: str
    passed: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class BatchQualityGateReport(BaseModel):
    local_only: bool = True
    passed: bool
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    per_item_results: list[BatchQualityGateItemResult] = Field(default_factory=list)
    aggregate_summary: dict[str, Any] = Field(default_factory=dict)
    recommended_actions: list[str] = Field(default_factory=list)
    hidden_details_redacted: bool = True
    writes_to_disk: bool = False
    active_game_state_modified: bool = False


def run_batch_quality_gate(request: BatchQualityGateRequest) -> BatchQualityGateReport:
    results: list[BatchQualityGateItemResult] = []
    for world_id in request.world_ids:
        results.append(_world_result(world_id, request))
    if request.package_ids:
        results.extend(_package_results(request))
    blockers = _redact_list([blocker for result in results for blocker in result.blockers])
    warnings = _redact_list([warning for result in results for warning in result.warnings])
    if not request.include_migration_check:
        warnings.append("Migration check skipped by request.")
    if len(warnings) > request.thresholds.max_warnings:
        blockers.append(f"Warning threshold exceeded: {len(warnings)} > {request.thresholds.max_warnings}")
    passed = all(result.passed for result in results) and not blockers
    return BatchQualityGateReport(
        passed=passed,
        blockers=blockers,
        warnings=warnings,
        per_item_results=results,
        aggregate_summary={
            "total": len(results),
            "passed": sum(1 for result in results if result.passed),
            "failed": sum(1 for result in results if not result.passed),
            "profile": request.profile.value,
            "include_playtests": request.include_playtests,
            "include_hidden_leak_suite": request.include_hidden_leak_suite,
            "include_migration_check": request.include_migration_check,
        },
        recommended_actions=_recommended_actions(results, blockers, warnings),
    )


def _world_result(world_id: str, request: BatchQualityGateRequest) -> BatchQualityGateItemResult:
    config = QualityGateConfig(
        profile=request.profile,
        allow_warnings=True,
        fail_on_error=True,
        fail_on_blocker=True,
        min_health_score=request.thresholds.min_health_score,
        playtest_steps=2 if request.include_playtests else 0,
        benchmark_iterations=1,
        mod_max_combinations=1,
    )
    result = run_quality_gate(world_id, config, worlds_root=request.worlds_root, mods_root=request.mods_root)
    blockers = _redact_list([*result.blockers, *result.errors])
    warnings = _redact_list(result.warnings)
    return BatchQualityGateItemResult(
        item_id=_redact(world_id),
        item_type="world",
        passed=result.passed,
        blockers=blockers,
        warnings=warnings,
        summary={
            "health_score": result.health_score,
            "report_links": len(result.report_links),
            "profile": result.summary.get("profile"),
        },
    )


def _package_results(request: BatchQualityGateRequest) -> list[BatchQualityGateItemResult]:
    targets = [
        ContentBatchValidationTarget(package_type=request.package_type, id=package_id)
        for package_id in request.package_ids
    ]
    batch = validate_content_batch(
        ContentBatchValidationRequest(
            targets=targets,
            worlds_root=request.worlds_root,
            packages_root=request.packages_root,
            mods_root=request.mods_root,
            normal_report=True,
        )
    )
    results: list[BatchQualityGateItemResult] = []
    for item in batch.per_package_report:
        blockers = _redact_list([issue.message for issue in item.errors])
        warnings = _redact_list([issue.message for issue in item.warnings])
        results.append(
            BatchQualityGateItemResult(
                item_id=_redact(item.id),
                item_type=item.package_type.value,
                passed=item.status != "failed",
                blockers=blockers,
                warnings=warnings,
                summary={"status": item.status, "errors": len(item.errors), "warnings": len(item.warnings)},
            )
        )
    return results


def _recommended_actions(
    results: list[BatchQualityGateItemResult],
    blockers: list[str],
    warnings: list[str],
) -> list[str]:
    actions: list[str] = []
    if blockers:
        actions.append("Fix blockers before release/export.")
    if warnings:
        actions.append("Review warnings and rerun Batch Quality Gate.")
    for result in results:
        if not result.passed:
            actions.append(f"Inspect {result.item_type}:{result.item_id}.")
    if not actions:
        actions.append("Batch is eligible for local export or release review.")
    return actions


def _redact_list(values: list[str]) -> list[str]:
    return [_redact(value) for value in values]


def _redact(value: str) -> str:
    text = value
    for token in ("sk-", "api_key", "apikey", "secret", "hidden", "private_self_summary", ".env", "sealed_letter_under_stone"):
        text = text.replace(token, "[redacted]")
        text = text.replace(token.upper(), "[redacted]")
    return text
