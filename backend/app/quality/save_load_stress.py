import json
from typing import Any

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.timeline_replay import ReplaySummary, replay_dry_run, state_checksum
from app.core.world_state import GameState
from app.db.migration_service import MigrationService, MigrationStatus
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.engine.content.import_export import ImportExportError, ImportExportService, ImportResult, PackageDryRunResult
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class StressScenarioResult(BaseModel):
    name: str
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class StressTestReport(BaseModel):
    run_id: str
    world_id: str
    save_id: str
    turns: int = 0
    event_count: int = 0
    state_delta_count: int = 0
    save_load_cycles: int = 0
    scenarios: list[StressScenarioResult] = Field(default_factory=list)
    migration_status_before: MigrationStatus | None = None
    migration_status_after: MigrationStatus | None = None
    migration_dry_run_applied_count: int = 0
    migration_apply_applied_count: int = 0
    import_dry_run: PackageDryRunResult | None = None
    import_result: ImportResult | None = None
    replay_summary: ReplaySummary | None = None
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _strip_debug_only(payload)


def run_save_load_migration_stress(
    *,
    repository: SQLiteSaveRepository,
    save_id: str,
    initial_state: GameState,
    events: list[Event],
    save_load_cycles: int = 3,
    migration_service: MigrationService | None = None,
    import_export_service: ImportExportService | None = None,
    import_overwrite: bool = True,
) -> StressTestReport:
    service = migration_service or MigrationService(repository)
    scenarios: list[StressScenarioResult] = []
    event_count = len(events)
    delta_count = sum(len(event.state_deltas) for event in events)

    report = StressTestReport(
        run_id=f"save-load-migration-stress:{save_id}",
        world_id=initial_state.world_id,
        save_id=save_id,
        turns=max((event.turn for event in events), default=initial_state.turn),
        event_count=event_count,
        state_delta_count=delta_count,
        save_load_cycles=save_load_cycles,
        quality_report=WorldQualityReport(world_id=initial_state.world_id),
    )

    _run_save_load_cycles(
        report,
        scenarios,
        repository,
        save_id,
        initial_state,
        events,
        save_load_cycles,
    )
    _run_migration_cycle(report, scenarios, service, save_id)
    if import_export_service is not None:
        _run_import_export_cycle(report, scenarios, import_export_service, save_id, import_overwrite)
    _run_replay_cycle(report, scenarios, initial_state, events)

    report.scenarios = scenarios
    report.quality_report = stress_report_to_quality_report(report)
    return report


def stress_report_to_quality_report(report: StressTestReport) -> WorldQualityReport:
    issues: list[QualityIssue] = []
    for scenario in report.scenarios:
        if scenario.passed:
            continue
        for index, error in enumerate(scenario.errors or ["stress scenario failed"]):
            issues.append(
                QualityIssue(
                    id=f"save_load_migration_stress:{scenario.name}:{index}",
                    severity=QualityIssueSeverity.ERROR,
                    category="save_load_migration_stress",
                    message=f"Stress scenario failed: {scenario.name}",
                    safe_details={"scenario": scenario.name, "reason": error},
                )
            )
    replay_violations = report.replay_summary.invariant_violations if report.replay_summary else []
    for index, violation in enumerate(replay_violations):
        issues.append(
            QualityIssue(
                id=f"save_load_migration_stress:replay:{index}",
                severity=QualityIssueSeverity.ERROR,
                category="save_load_migration_stress",
                message="Replay dry-run reported an invariant violation.",
                safe_details={"reason": violation},
            )
        )
    error_count = len(issues)
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["save_load_migration_stress"],
        metrics=[
            QualityMetric(name="stress_turns", value=report.turns, category="save_load_migration_stress", status=QualityMetricStatus.OK),
            QualityMetric(name="stress_events", value=report.event_count, category="save_load_migration_stress", status=QualityMetricStatus.OK),
            QualityMetric(name="stress_state_deltas", value=report.state_delta_count, category="save_load_migration_stress", status=QualityMetricStatus.OK),
            QualityMetric(name="save_load_cycles", value=report.save_load_cycles, category="save_load_migration_stress", status=QualityMetricStatus.OK),
            QualityMetric(name="stress_failures", value=error_count, category="save_load_migration_stress", threshold=0, status=QualityMetricStatus.ERROR if error_count else QualityMetricStatus.OK),
        ],
        issues=issues,
        summary={
            "turns": report.turns,
            "event_count": report.event_count,
            "state_delta_count": report.state_delta_count,
            "save_load_cycles": report.save_load_cycles,
            "scenario_count": len(report.scenarios),
            "passed_scenarios": sum(1 for scenario in report.scenarios if scenario.passed),
            "failed_scenarios": sum(1 for scenario in report.scenarios if not scenario.passed),
            "migration_dry_run_applied_count": report.migration_dry_run_applied_count,
            "migration_apply_applied_count": report.migration_apply_applied_count,
            "replay_event_count": report.replay_summary.event_count if report.replay_summary else 0,
            "hidden_details_debug_only": {"save_id": report.save_id},
        },
        recommended_actions=_recommended_actions(error_count),
    )


def _run_save_load_cycles(
    report: StressTestReport,
    scenarios: list[StressScenarioResult],
    repository: SQLiteSaveRepository,
    save_id: str,
    state: GameState,
    events: list[Event],
    cycles: int,
) -> None:
    try:
        repository.save_snapshot(save_id, state, events)
        expected_state_checksum = state_checksum(state)
        expected_event_ids = [event.event_id for event in events]
        for cycle in range(cycles):
            loaded_state = repository.load_save(save_id)
            loaded_events = repository.list_events(save_id)
            if state_checksum(loaded_state) != expected_state_checksum:
                raise SaveRepositoryError(f"State checksum mismatch at cycle {cycle}")
            if [event.event_id for event in loaded_events] != expected_event_ids:
                raise SaveRepositoryError(f"EventLog mismatch at cycle {cycle}")
            repository.save_snapshot(save_id, loaded_state, loaded_events)
        scenarios.append(
            StressScenarioResult(
                name="multiple_save_load_cycles",
                passed=True,
                details={"cycles": cycles, "state_checksum": expected_state_checksum, "event_count": len(events)},
            )
        )
    except Exception as exc:
        scenarios.append(
            StressScenarioResult(
                name="multiple_save_load_cycles",
                passed=False,
                errors=[str(exc)],
            )
        )


def _run_migration_cycle(
    report: StressTestReport,
    scenarios: list[StressScenarioResult],
    service: MigrationService,
    save_id: str,
) -> None:
    try:
        report.migration_status_before = service.status(save_id)
        dry_run = service.dry_run(save_id)
        report.migration_dry_run_applied_count = len(dry_run.applied_migrations)
        status_after_dry_run = service.status(save_id)
        if status_after_dry_run.schema_version != report.migration_status_before.schema_version:
            raise SaveRepositoryError("Migration dry-run changed save schema_version")
        applied = service.apply(save_id)
        report.migration_apply_applied_count = len(applied.applied_migrations)
        report.migration_status_after = service.status(save_id)
        scenarios.append(
            StressScenarioResult(
                name="migration_dry_run_then_apply",
                passed=True,
                details={
                    "dry_run_applied_migrations": report.migration_dry_run_applied_count,
                    "apply_applied_migrations": report.migration_apply_applied_count,
                    "schema_version_after": report.migration_status_after.schema_version,
                },
            )
        )
    except Exception as exc:
        scenarios.append(
            StressScenarioResult(
                name="migration_dry_run_then_apply",
                passed=False,
                errors=[str(exc)],
            )
        )


def _run_import_export_cycle(
    report: StressTestReport,
    scenarios: list[StressScenarioResult],
    service: ImportExportService,
    save_id: str,
    overwrite: bool,
) -> None:
    try:
        exported = service.export_save(save_id)
        report.import_dry_run = service.dry_run_import_package(exported.archive_base64, overwrite=overwrite)
        if not report.import_dry_run.ok:
            raise ImportExportError("; ".join([*report.import_dry_run.errors, *report.import_dry_run.conflicts]))
        report.import_result = service.apply_import_package(
            exported.archive_base64,
            overwrite=overwrite,
            confirm_apply=True,
        )
        if not report.import_result.imported:
            raise ImportExportError("Save bundle import did not report imported=true")
        scenarios.append(
            StressScenarioResult(
                name="import_export_save_bundle",
                passed=True,
                details={
                    "migration_needed": report.import_result.migration_needed,
                    "validation_ok": report.import_result.validation_ok,
                },
            )
        )
    except Exception as exc:
        scenarios.append(
            StressScenarioResult(
                name="import_export_save_bundle",
                passed=False,
                errors=[str(exc)],
            )
        )


def _run_replay_cycle(
    report: StressTestReport,
    scenarios: list[StressScenarioResult],
    initial_state: GameState,
    events: list[Event],
) -> None:
    try:
        first = replay_dry_run(initial_state, events)
        second = replay_dry_run(initial_state, events)
        report.replay_summary = first
        if first.model_dump(mode="json") != second.model_dump(mode="json"):
            raise ValueError("Replay dry-run is not deterministic")
        if first.failed_event_id:
            raise ValueError(f"Replay failed at event {first.failed_event_id}")
        scenarios.append(
            StressScenarioResult(
                name="replay_dry_run",
                passed=not first.invariant_violations,
                details={"event_count": first.event_count, "final_state_checksum": first.final_state_checksum},
                errors=first.invariant_violations,
            )
        )
    except Exception as exc:
        scenarios.append(
            StressScenarioResult(
                name="replay_dry_run",
                passed=False,
                errors=[str(exc)],
            )
        )


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


def _recommended_actions(error_count: int) -> list[str]:
    if not error_count:
        return []
    return ["Inspect save/load cycles, migration reports, import/export bundle validation, and replay dry-run failures."]
