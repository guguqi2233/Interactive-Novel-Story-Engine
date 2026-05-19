from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.world_loader import WorldLoader
from app.playtesting.batch import PlaytestBatchRunRequest, run_playtest_batch
from app.quality.benchmarks import BenchmarkRunRequest, run_benchmark_suite
from app.quality.combat_balance import analyze_combat_balance
from app.quality.dead_end_detector import analyze_dead_ends
from app.quality.economy_balance import analyze_economy_balance
from app.quality.health_score import build_world_health_score
from app.quality.mod_compat_stress import ModCompatibilityStressRequest, run_mod_compatibility_stress
from app.quality.npc_behavior_coverage import analyze_npc_behavior_coverage
from app.quality.npc_simulation_quality import analyze_npc_simulation_quality_for_world
from app.quality.quest_analysis import analyze_quest_completion
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    WorldQualityReport,
    world_quality_report_from_validation_report,
)
from app.quality.save_load_stress import run_save_load_migration_stress
from app.quality.schedule_conflict_detector import analyze_schedule_conflicts
from app.quality.social_consequence_coverage import analyze_social_consequence_coverage
from app.scenarios.regression import sample_scenario_regression_cases, run_scenario_regression_suite
from app.session_store import create_initial_state


class QualityGateProfile(StrEnum):
    FAST = "fast"
    STANDARD = "standard"
    STRICT = "strict"


class QualityGateConfig(BaseModel):
    profile: QualityGateProfile = QualityGateProfile.STANDARD
    allow_warnings: bool = True
    fail_on_error: bool = True
    fail_on_blocker: bool = True
    max_performance_p95_ms: float | None = None
    min_health_score: int = Field(default=70, ge=0, le=100)
    benchmark_iterations: int = Field(default=1, ge=1, le=5)
    playtest_seeds: list[int] = Field(default_factory=lambda: [123])
    playtest_steps: int = Field(default=8, ge=0, le=250)
    mod_max_combinations: int = Field(default=3, ge=1, le=25)


class QualityGateReportLink(BaseModel):
    category: str
    report_id: str


class QualityGateResult(BaseModel):
    local_only: bool = True
    gate_id: str = Field(default_factory=lambda: f"quality-gate-{uuid4()}")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    world_id: str
    passed: bool
    blockers: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    report_links: list[QualityGateReportLink] = Field(default_factory=list)
    health_score: int | None = None
    summary: dict[str, Any] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict[str, Any]:
        return _redact_hidden_text(self.model_dump(mode="json", exclude_none=True))


def run_quality_gate(
    world_id: str,
    config: QualityGateConfig | None = None,
    *,
    worlds_root: str = "worlds",
    mods_root: str = "mods",
) -> QualityGateResult:
    config = resolved_gate_config(config)
    reports: list[WorldQualityReport] = []
    links: list[QualityGateReportLink] = []
    skipped: list[str] = []

    validation_report = ContentAuthoringService(worlds_root).validate_world(world_id)
    _append_report(reports, links, "validate_world", world_quality_report_from_validation_report(validation_report))

    _append_report(reports, links, "quest_completion", analyze_quest_completion(world_id, worlds_root=worlds_root).quality_report)
    _append_report(reports, links, "dead_ends", analyze_dead_ends(world_id, worlds_root=worlds_root).quality_report)
    _append_report(reports, links, "npc_coverage", analyze_npc_behavior_coverage(world_id, worlds_root=worlds_root).quality_report)
    _append_report(
        reports,
        links,
        "npc_simulation_quality",
        analyze_npc_simulation_quality_for_world(world_id, worlds_root=worlds_root).quality_report,
    )
    _append_report(reports, links, "schedule_conflict", analyze_schedule_conflicts(world_id, worlds_root=worlds_root).quality_report)
    _append_report(reports, links, "economy_balance", analyze_economy_balance(world_id, worlds_root=worlds_root).quality_report)
    _append_report(reports, links, "combat_balance", analyze_combat_balance(world_id, worlds_root=worlds_root).quality_report)
    _append_report(
        reports,
        links,
        "social_consequence_coverage",
        analyze_social_consequence_coverage(world_id, worlds_root=worlds_root).quality_report,
    )

    with TemporaryDirectory(prefix="llm_world_quality_gate_", ignore_cleanup_errors=True) as temp_dir:
        world_loader = WorldLoader(worlds_root)
        state = create_initial_state(world_loader, world_id)
        stress_repo = SQLiteSaveRepository(Path(temp_dir) / "quality_gate_stress.db")
        stress = run_save_load_migration_stress(
            repository=stress_repo,
            save_id=f"quality-gate-{world_id}",
            initial_state=state,
            events=[],
            save_load_cycles=1,
        )
        _append_report(reports, links, "save_load_migration_stress", stress.quality_report)

        benchmark = run_benchmark_suite(
            BenchmarkRunRequest(
                world_id=world_id,
                worlds_root=worlds_root,
                iterations=config.benchmark_iterations,
                benchmarks=["validate_world", "save_load", "memory_search"],
                thresholds_ms={"quality_gate_p95": config.max_performance_p95_ms}
                if config.max_performance_p95_ms is not None
                else {},
            )
        )

    scenario_cases = [case for case in sample_scenario_regression_cases() if case.world_id == world_id]
    scenario_run = run_scenario_regression_suite(scenario_cases[:2], worlds_root=worlds_root) if scenario_cases else None
    if scenario_run is not None:
        _append_report(reports, links, "scenario_regression", _scenario_quality_report(world_id, scenario_run))

    batch = run_playtest_batch(
        PlaytestBatchRunRequest(
            world_id=world_id,
            seeds=config.playtest_seeds,
            steps=config.playtest_steps,
            save_load_check=True,
            stop_on_blocker=True,
        ),
        worlds_root=worlds_root,
    )
    _append_report(reports, links, "hidden_leak_regression", batch.quality_report)

    mod_report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(
            selected_worlds=[world_id],
            max_combinations=config.mod_max_combinations,
            seed=123,
            scenario_cases=scenario_cases,
        ),
        mods_root=mods_root,
    )
    _append_report(reports, links, "mod_compatibility_smoke", mod_report.quality_report)

    health = build_world_health_score(world_id, reports, benchmark_reports=[benchmark])
    blockers, errors, warnings = _collect_issues(reports)
    performance_errors = _performance_errors(benchmark, config.max_performance_p95_ms)
    errors.extend(performance_errors)
    performance_blockers, performance_warnings = _performance_budget_issues(benchmark)
    blockers.extend(performance_blockers)
    warnings.extend(performance_warnings)
    if health.overall_score < config.min_health_score:
        errors.append(f"World health score {health.overall_score} is below threshold {config.min_health_score}.")

    passed = _passed(config, blockers, errors, warnings)
    return QualityGateResult(
        world_id=world_id,
        passed=passed,
        blockers=blockers,
        errors=errors,
        warnings=warnings,
        report_links=links,
        skipped=skipped,
        health_score=health.overall_score,
        summary={
            "profile": config.profile.value,
            "checks": [
                "validate_world",
                "hidden_leak_regression",
                "quest_completion_analysis",
                "dead_end_detector",
                "npc_coverage",
                "npc_simulation_quality",
                "schedule_conflict_detector",
                "economy_balance",
                "combat_balance",
                "social_consequence_coverage",
                "save_load_migration_stress",
                "performance_benchmark",
                "scenario_regression",
                "mod_compatibility_smoke",
            ],
            "reports": len(reports),
            "skipped": skipped,
            "benchmark_id": benchmark.benchmark_id,
            "scenario_regression_run_id": scenario_run.run_id if scenario_run else None,
            "playtest_batch_run_id": batch.run_id,
            "mod_compatibility_report_id": mod_report.report_id,
            "benchmark_regressions": [
                regression.model_dump(mode="json")
                for regression in benchmark.regressions
            ],
        },
    )


def resolved_gate_config(config: QualityGateConfig | None = None) -> QualityGateConfig:
    raw_config = config or QualityGateConfig()
    profile_defaults = _profile_defaults(raw_config.profile)
    data = profile_defaults.model_dump()
    explicit = raw_config.model_fields_set
    for field_name in explicit:
        data[field_name] = getattr(raw_config, field_name)
    return QualityGateConfig.model_validate(data)


def _profile_defaults(profile: QualityGateProfile) -> QualityGateConfig:
    if profile == QualityGateProfile.STRICT:
        return QualityGateConfig(
            profile=profile,
            allow_warnings=False,
            fail_on_error=True,
            fail_on_blocker=True,
            min_health_score=85,
            benchmark_iterations=3,
            playtest_seeds=[101, 202, 303],
            playtest_steps=16,
            mod_max_combinations=8,
        )
    if profile == QualityGateProfile.FAST:
        return QualityGateConfig(
            profile=profile,
            allow_warnings=True,
            fail_on_error=True,
            fail_on_blocker=True,
            min_health_score=60,
            benchmark_iterations=1,
            playtest_seeds=[123],
            playtest_steps=4,
            mod_max_combinations=2,
        )
    return QualityGateConfig(
        profile=QualityGateProfile.STANDARD,
        allow_warnings=True,
        fail_on_error=True,
        fail_on_blocker=True,
        min_health_score=70,
        benchmark_iterations=1,
        playtest_seeds=[123],
        playtest_steps=8,
        mod_max_combinations=3,
    )


def _append_report(
    reports: list[WorldQualityReport],
    links: list[QualityGateReportLink],
    category: str,
    report: WorldQualityReport,
) -> None:
    safe_report = report.normal_copy()
    reports.append(safe_report)
    links.append(QualityGateReportLink(category=category, report_id=safe_report.run_id))


def _scenario_quality_report(world_id: str, scenario_run: Any) -> WorldQualityReport:
    issues: list[QualityIssue] = []
    for result in scenario_run.case_results:
        if result.passed:
            continue
        issues.append(
            QualityIssue(
                id=f"quality_gate_scenario:{result.case_id}",
                severity=QualityIssueSeverity.ERROR,
                category="scenario_regression",
                message="Scenario regression case failed.",
                safe_details={"case_id": result.case_id, "reasons": result.failure_reasons},
            )
        )
    return WorldQualityReport(
        world_id=world_id,
        categories=["scenario_regression"],
        issues=issues,
        summary={"passed": scenario_run.passed, "failed": scenario_run.failed, "total": scenario_run.total_cases},
    ).normal_copy()


def _collect_issues(reports: list[WorldQualityReport]) -> tuple[list[str], list[str], list[str]]:
    blockers: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    for report in reports:
        for issue in report.normal_copy().issues:
            message = _redact_hidden_text(issue.message)
            if issue.severity == QualityIssueSeverity.BLOCKER:
                blockers.append(message)
            elif issue.severity == QualityIssueSeverity.ERROR:
                errors.append(message)
            elif issue.severity == QualityIssueSeverity.WARNING:
                warnings.append(message)
    return sorted(set(blockers)), sorted(set(errors)), sorted(set(warnings))


def _performance_errors(benchmark: Any, max_p95: float | None) -> list[str]:
    if max_p95 is None:
        return []
    observed = max(benchmark.p95.values(), default=0.0)
    if observed > max_p95:
        return [f"Performance p95 {observed:.3f}ms exceeds threshold {max_p95:.3f}ms."]
    return []


def _performance_budget_issues(benchmark: Any) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    for regression in getattr(benchmark, "regressions", []):
        message = (
            f"Performance budget {regression.benchmark_type} observed "
            f"{regression.observed_ms:.3f}ms over {regression.threshold_ms:.3f}ms."
        )
        if regression.severity == "blocker":
            blockers.append(message)
        elif regression.severity == "warning":
            warnings.append(message)
    return sorted(set(blockers)), sorted(set(warnings))


def _passed(config: QualityGateConfig, blockers: list[str], errors: list[str], warnings: list[str]) -> bool:
    if config.fail_on_blocker and blockers:
        return False
    if config.fail_on_error and errors:
        return False
    if not config.allow_warnings and warnings:
        return False
    return True


def _redact_hidden_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_hidden_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_hidden_text(item) for item in value]
    if isinstance(value, str):
        return value.replace("A sealed letter is hidden beneath a loose paving stone.", "[hidden text redacted]")
    return value
