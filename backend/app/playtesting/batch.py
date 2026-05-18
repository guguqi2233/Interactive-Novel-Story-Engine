from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.playtesting.runner import PlaytestOptions, PlaytestReport, PlaytestScenario, run_playtest
from app.quality import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.scenarios.regression import sample_scenario_regression_cases


class PlaytestBatchRunRequest(BaseModel):
    world_id: str = "mist_valley"
    scenario_ids: list[str] = Field(default_factory=list)
    agent_types: list[str] = Field(default_factory=lambda: ["random_valid_action_agent"])
    seeds: list[int] = Field(default_factory=lambda: [123])
    steps: int = Field(default=25, ge=0, le=250)
    max_parallelism: int = Field(default=1, ge=1, le=16)
    stop_on_blocker: bool = False
    save_load_check: bool = False


class PlaytestBatchRunItem(BaseModel):
    run_index: int
    scenario_id: str | None = None
    agent_type: str
    seed: int
    passed: bool
    blocker: bool
    duration_ms: float
    turns_run: int
    issue_count: int
    safe_failure_reasons: list[str] = Field(default_factory=list)
    report: PlaytestReport


class PlaytestBatchCoverageSummary(BaseModel):
    action_types: dict[str, int] = Field(default_factory=dict)
    final_locations: dict[str, int] = Field(default_factory=dict)
    scenarios_run: list[str] = Field(default_factory=list)
    agents_run: list[str] = Field(default_factory=list)
    seeds_run: list[int] = Field(default_factory=list)


class PlaytestBatchPerformanceSummary(BaseModel):
    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0
    max_duration_ms: float = 0.0


class PlaytestBatchRun(BaseModel):
    local_only: bool = True
    run_id: str = Field(default_factory=lambda: f"playtest-batch-{uuid4()}")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    world_id: str
    total_runs: int = 0
    passed: int = 0
    failed: int = 0
    blockers: int = 0
    aggregate_issues: list[str] = Field(default_factory=list)
    coverage_summary: PlaytestBatchCoverageSummary = Field(default_factory=PlaytestBatchCoverageSummary)
    performance_summary: PlaytestBatchPerformanceSummary = Field(default_factory=PlaytestBatchPerformanceSummary)
    run_items: list[PlaytestBatchRunItem] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _redact_hidden_text(payload)


def run_playtest_batch(
    request: PlaytestBatchRunRequest,
    *,
    worlds_root: str = "worlds",
) -> PlaytestBatchRun:
    scenarios = _select_scenarios(request.world_id, request.scenario_ids)
    run_specs = _build_run_specs(request, scenarios)
    items: list[PlaytestBatchRunItem] = []

    for index, spec in enumerate(run_specs):
        item = _run_batch_item(index, request, spec, worlds_root=worlds_root)
        items.append(item)
        if request.stop_on_blocker and item.blocker:
            break

    passed = sum(1 for item in items if item.passed)
    blockers = sum(1 for item in items if item.blocker)
    aggregate_issues = _aggregate_issues(items)
    coverage = _coverage_summary(items)
    performance = _performance_summary(items)
    report = PlaytestBatchRun(
        world_id=request.world_id,
        total_runs=len(items),
        passed=passed,
        failed=len(items) - passed,
        blockers=blockers,
        aggregate_issues=aggregate_issues,
        coverage_summary=coverage,
        performance_summary=performance,
        run_items=items,
        quality_report=WorldQualityReport(world_id=request.world_id),
    )
    report.quality_report = _to_quality_report(report)
    return report


def _select_scenarios(world_id: str, scenario_ids: list[str]) -> list[PlaytestScenario]:
    scenarios = [scenario for scenario in _sample_playtest_scenarios() if scenario.world_id == world_id]
    if scenario_ids:
        wanted = set(scenario_ids)
        scenarios = [scenario for scenario in scenarios if scenario.id in wanted]
    return scenarios


def _sample_playtest_scenarios() -> list[PlaytestScenario]:
    playtest_scenarios = [
        PlaytestScenario(
            id=case.id,
            world_id=case.world_id,
            name=case.name,
            description=case.description,
            agent_type="quest_following_agent" if "quest" in case.tags else "explore_agent",
            max_steps=min(case.max_turns or 12, 25),
            seed=123,
            expected_outcomes={"visible_facts": case.expected_visible_facts},
            forbidden_outcomes={"visible_facts": case.forbidden_visible_facts},
            invariants=["hidden_facts_not_visible", "state_delta_required"],
            tags=case.tags,
        )
        for case in sample_scenario_regression_cases()
    ]
    if not playtest_scenarios:
        playtest_scenarios.append(
            PlaytestScenario(
                id="default_exploration",
                world_id="mist_valley",
                name="Default exploration",
                agent_type="explore_agent",
                max_steps=12,
                seed=123,
                tags=["exploration"],
            )
        )
    return playtest_scenarios


def _build_run_specs(
    request: PlaytestBatchRunRequest,
    scenarios: list[PlaytestScenario],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    selected_scenarios: list[PlaytestScenario | None] = scenarios if request.scenario_ids else [None]
    agent_types = request.agent_types or ["random_valid_action_agent"]
    seeds = request.seeds or [123]
    for scenario in selected_scenarios:
        for agent_type in agent_types:
            for seed in seeds:
                specs.append({"scenario": scenario, "agent_type": agent_type, "seed": seed})
    return specs


def _run_batch_item(
    index: int,
    request: PlaytestBatchRunRequest,
    spec: dict[str, Any],
    *,
    worlds_root: str,
) -> PlaytestBatchRunItem:
    scenario: PlaytestScenario | None = spec["scenario"]
    agent_type = scenario.agent_type if scenario and not request.agent_types else spec["agent_type"]
    seed = int(spec["seed"])
    steps = scenario.max_steps if scenario else request.steps
    started = perf_counter()
    with TemporaryDirectory(prefix="llm_world_playtest_batch_", ignore_cleanup_errors=True) as temp_dir:
        report = run_playtest(
            PlaytestOptions(
                world_id=request.world_id,
                strategy=agent_type,
                max_steps=steps,
                seed=seed,
                save_every=1 if request.save_load_check and steps > 0 else None,
                database_path=str(Path(temp_dir) / "batch.db") if request.save_load_check else None,
                worlds_root=worlds_root,
                stop_on_error=True,
            )
        )
    duration_ms = (perf_counter() - started) * 1000.0
    reasons = _failure_reasons(report)
    blocker = bool(report.visibility_leaks or report.invariant_violations or report.errors or report.save_load_failures)
    return PlaytestBatchRunItem(
        run_index=index,
        scenario_id=scenario.id if scenario else None,
        agent_type=agent_type,
        seed=seed,
        passed=not reasons,
        blocker=blocker,
        duration_ms=round(duration_ms, 3),
        turns_run=report.turns_run,
        issue_count=len(reasons),
        safe_failure_reasons=reasons,
        report=report,
    )


def _failure_reasons(report: PlaytestReport) -> list[str]:
    reasons = [
        *report.errors,
        *report.invariant_violations,
        *report.visibility_leaks,
        *report.save_load_failures,
    ]
    return sorted({_safe_text(reason) for reason in reasons})


def _aggregate_issues(items: list[PlaytestBatchRunItem]) -> list[str]:
    issues: set[str] = set()
    for item in items:
        issues.update(item.safe_failure_reasons)
    return sorted(issues)


def _coverage_summary(items: list[PlaytestBatchRunItem]) -> PlaytestBatchCoverageSummary:
    action_types: dict[str, int] = {}
    final_locations: dict[str, int] = {}
    scenarios: set[str] = set()
    agents: set[str] = set()
    seeds: set[int] = set()
    for item in items:
        if item.scenario_id:
            scenarios.add(item.scenario_id)
        agents.add(item.agent_type)
        seeds.add(item.seed)
        final_location = item.report.final_state_summary.location_id
        final_locations[final_location] = final_locations.get(final_location, 0) + 1
        for action in item.report.actions_taken:
            action_types[action.action_type] = action_types.get(action.action_type, 0) + 1
    return PlaytestBatchCoverageSummary(
        action_types=dict(sorted(action_types.items())),
        final_locations=dict(sorted(final_locations.items())),
        scenarios_run=sorted(scenarios),
        agents_run=sorted(agents),
        seeds_run=sorted(seeds),
    )


def _performance_summary(items: list[PlaytestBatchRunItem]) -> PlaytestBatchPerformanceSummary:
    durations = [item.duration_ms for item in items]
    total = sum(durations)
    return PlaytestBatchPerformanceSummary(
        total_duration_ms=round(total, 3),
        average_duration_ms=round(total / len(durations), 3) if durations else 0.0,
        max_duration_ms=round(max(durations), 3) if durations else 0.0,
    )


def _to_quality_report(report: PlaytestBatchRun) -> WorldQualityReport:
    issues = [
        QualityIssue(
            id=f"playtest_batch_issue:{index}",
            severity=QualityIssueSeverity.BLOCKER if "leak" in issue.lower() else QualityIssueSeverity.ERROR,
            category="playtest_batch",
            message="Playtest batch issue detected.",
            safe_details={"reason": issue},
        )
        for index, issue in enumerate(report.aggregate_issues)
    ]
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["playtest_batch"],
        metrics=[
            QualityMetric(
                name="playtest_batch_total_runs",
                value=report.total_runs,
                category="playtest_batch",
                status=QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="playtest_batch_failed_runs",
                value=report.failed,
                category="playtest_batch",
                threshold=0,
                status=QualityMetricStatus.ERROR if report.failed else QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="playtest_batch_blockers",
                value=report.blockers,
                category="playtest_batch",
                threshold=0,
                status=QualityMetricStatus.BLOCKER if report.blockers else QualityMetricStatus.OK,
            ),
        ],
        issues=issues,
        summary={
            "total_runs": report.total_runs,
            "passed": report.passed,
            "failed": report.failed,
            "blockers": report.blockers,
            "coverage": report.coverage_summary.model_dump(mode="json"),
            "performance": report.performance_summary.model_dump(mode="json"),
        },
        recommended_actions=["Inspect failed batch items before accepting this world build."] if issues else [],
    ).normal_copy()


def _safe_text(value: str) -> str:
    return str(value).replace("A sealed letter is hidden beneath a loose paving stone.", "[hidden text redacted]")


def _redact_hidden_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_hidden_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_hidden_text(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value
