from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.map_visual import build_authoring_map_visual_graph
from app.engine.content.quest_graph import quest_graph_to_yaml, quest_yaml_to_graph
from app.engine.content.validator import validate_world_pack
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.world_tick import run_world_tick
from app.llm.intent_parser import IntentParser
from app.llm.memory_store import InMemoryMemoryStore, MemoryQuery, MemoryRecord, MemoryVisibility
from app.llm.narrator import Narrator
from app.playtesting.provider import PlaytestLLMProvider
from app.playtesting.runner import PlaytestScenario, PlaytestScenarioType, run_playtest_scenario
from app.session_store import create_initial_state


class BenchmarkType(str):
    GAME_LOOP_TURN = "game_loop_turn"
    WORLD_TICK = "world_tick"
    SAVE_LOAD = "save_load"
    MIGRATION_DRY_RUN = "migration_dry_run"
    VALIDATE_WORLD = "validate_world"
    MAP_GRAPH_BUILD = "map_graph_build"
    QUEST_GRAPH_ROUNDTRIP = "quest_graph_roundtrip"
    MEMORY_SEARCH = "memory_search"
    SCENARIO_REGRESSION_RUN = "scenario_regression_run"


BENCHMARK_TYPES = [
    BenchmarkType.GAME_LOOP_TURN,
    BenchmarkType.WORLD_TICK,
    BenchmarkType.SAVE_LOAD,
    BenchmarkType.MIGRATION_DRY_RUN,
    BenchmarkType.VALIDATE_WORLD,
    BenchmarkType.MAP_GRAPH_BUILD,
    BenchmarkType.QUEST_GRAPH_ROUNDTRIP,
    BenchmarkType.MEMORY_SEARCH,
    BenchmarkType.SCENARIO_REGRESSION_RUN,
]


DEFAULT_PERFORMANCE_BUDGET: dict[str, "PerformanceBudgetEntry"] = {}


class BenchmarkRunRequest(BaseModel):
    world_id: str = "mist_valley"
    worlds_root: str = "worlds"
    iterations: int = Field(default=3, ge=1, le=25)
    benchmarks: list[str] = Field(default_factory=lambda: list(BENCHMARK_TYPES))
    thresholds_ms: dict[str, float] = Field(default_factory=dict)
    budget_path: str | None = None
    use_v1_budget: bool = True


class BenchmarkSample(BaseModel):
    benchmark_type: str
    duration_ms: float
    ok: bool = True
    safe_details: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class BenchmarkRegression(BaseModel):
    benchmark_type: str
    threshold_ms: float
    observed_ms: float
    severity: str = "warning"
    budget_name: str | None = None


class PerformanceBudgetEntry(BaseModel):
    target_ms: float = Field(ge=0)
    warning_ms: float = Field(ge=0)
    blocker_ms: float = Field(ge=0)
    measurement_method: str
    known_caveats: list[str] = Field(default_factory=list)


DEFAULT_PERFORMANCE_BUDGET = {
    BenchmarkType.GAME_LOOP_TURN: PerformanceBudgetEntry(
        target_ms=150,
        warning_ms=300,
        blocker_ms=1000,
        measurement_method="Benchmark suite p95/max timing for one mock-provider game_loop.step('observe').",
        known_caveats=["Local CPU, antivirus, and debug logging can affect short-running timings."],
    ),
    BenchmarkType.WORLD_TICK: PerformanceBudgetEntry(
        target_ms=50,
        warning_ms=150,
        blocker_ms=500,
        measurement_method="Benchmark suite p95/max timing for one deterministic world_tick.",
        known_caveats=["Larger worlds may require a documented budget update."],
    ),
    BenchmarkType.SAVE_LOAD: PerformanceBudgetEntry(
        target_ms=80,
        warning_ms=200,
        blocker_ms=750,
        measurement_method="Temporary SQLite save_snapshot plus load_save benchmark.",
        known_caveats=["Disk and filesystem cache differences can shift timing."],
    ),
    BenchmarkType.MIGRATION_DRY_RUN: PerformanceBudgetEntry(
        target_ms=80,
        warning_ms=200,
        blocker_ms=750,
        measurement_method="Temporary SQLite save migration dry-run benchmark.",
        known_caveats=["Current-schema saves are expected to be no-op dry-runs."],
    ),
    BenchmarkType.VALIDATE_WORLD: PerformanceBudgetEntry(
        target_ms=150,
        warning_ms=500,
        blocker_ms=1500,
        measurement_method="validate_world_pack over the sample world.",
        known_caveats=["Content-heavy worlds can exceed the sample-world budget."],
    ),
    BenchmarkType.MAP_GRAPH_BUILD: PerformanceBudgetEntry(
        target_ms=80,
        warning_ms=250,
        blocker_ms=1000,
        measurement_method="World load plus authoring map graph construction.",
        known_caveats=["Large location graphs should define their own budget before v1.1."],
    ),
    BenchmarkType.QUEST_GRAPH_ROUNDTRIP: PerformanceBudgetEntry(
        target_ms=100,
        warning_ms=350,
        blocker_ms=1200,
        measurement_method="quests.yaml -> graph -> YAML -> graph roundtrip.",
        known_caveats=["Complex quest packs may need a documented larger authoring budget."],
    ),
    BenchmarkType.MEMORY_SEARCH: PerformanceBudgetEntry(
        target_ms=20,
        warning_ms=80,
        blocker_ms=250,
        measurement_method="Local in-memory search across 100 safe benchmark records.",
        known_caveats=["External vector backends are not part of this local smoke budget."],
    ),
    BenchmarkType.SCENARIO_REGRESSION_RUN: PerformanceBudgetEntry(
        target_ms=250,
        warning_ms=750,
        blocker_ms=2500,
        measurement_method="Two-step deterministic scenario regression smoke run.",
        known_caveats=["Long scenario suites are measured separately by playtest batch reports."],
    ),
    "quality_gate_standard_profile": PerformanceBudgetEntry(
        target_ms=3000,
        warning_ms=8000,
        blocker_ms=20000,
        measurement_method="Manual end-to-end wall-clock observation of quality_gate --profile standard.",
        known_caveats=["The benchmark suite does not time the full gate directly yet."],
    ),
}


class BenchmarkStats(BaseModel):
    p50: dict[str, float] = Field(default_factory=dict)
    p95: dict[str, float] = Field(default_factory=dict)
    max: dict[str, float] = Field(default_factory=dict)


class BenchmarkReport(BaseModel):
    benchmark_id: str = Field(default_factory=lambda: f"benchmark-{uuid4().hex}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    world_id: str
    environment_summary_safe: dict[str, Any] = Field(default_factory=dict)
    samples: list[BenchmarkSample] = Field(default_factory=list)
    p50: dict[str, float] = Field(default_factory=dict)
    p95: dict[str, float] = Field(default_factory=dict)
    max: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    budgets: dict[str, PerformanceBudgetEntry] = Field(default_factory=dict)
    regressions: list[BenchmarkRegression] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_benchmark_suite(request: BenchmarkRunRequest) -> BenchmarkReport:
    selected = [benchmark for benchmark in request.benchmarks if benchmark in BENCHMARK_TYPES]
    if not selected:
        selected = list(BENCHMARK_TYPES)
    samples: list[BenchmarkSample] = []
    with TemporaryDirectory(prefix="llm_world_benchmark_", ignore_cleanup_errors=True) as temp_dir:
        context = _BenchmarkContext(
            world_id=request.world_id,
            worlds_root=Path(request.worlds_root),
            temp_dir=Path(temp_dir),
        )
        for benchmark_type in selected:
            runner = _RUNNERS[benchmark_type]
            for _ in range(request.iterations):
                samples.append(_time_runner(benchmark_type, runner, context))
    stats = _stats(samples)
    budgets = load_performance_budget(request.budget_path) if request.use_v1_budget else {}
    regressions = _regressions(stats.max, request.thresholds_ms, budgets)
    return BenchmarkReport(
        world_id=request.world_id,
        environment_summary_safe={
            "python": "local",
            "database": "temporary sqlite",
            "llm_provider": "mock/local_stub",
            "telemetry": "not uploaded",
            "world_id": request.world_id,
            "benchmark_count": len(selected),
            "iterations": request.iterations,
        },
        samples=samples,
        p50=stats.p50,
        p95=stats.p95,
        max=stats.max,
        thresholds=request.thresholds_ms,
        budgets={name: budget for name, budget in budgets.items() if name in selected or name == "quality_gate_standard_profile"},
        regressions=regressions,
    )


def load_performance_budget(path: str | Path | None = None) -> dict[str, PerformanceBudgetEntry]:
    if path is None:
        return dict(DEFAULT_PERFORMANCE_BUDGET)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_budgets = payload.get("budgets", payload)
    if not isinstance(raw_budgets, dict):
        raise ValueError("Performance budget file must contain a mapping or a 'budgets' mapping.")
    return {
        str(name): PerformanceBudgetEntry.model_validate(raw_budget)
        for name, raw_budget in raw_budgets.items()
    }


class _BenchmarkContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    world_id: str
    worlds_root: Path
    temp_dir: Path


def _time_runner(
    benchmark_type: str,
    runner: Callable[["_BenchmarkContext"], dict[str, Any]],
    context: _BenchmarkContext,
) -> BenchmarkSample:
    started = perf_counter()
    try:
        details = runner(context)
        ok = True
        error = None
    except Exception as exc:
        details = {}
        ok = False
        error = f"{type(exc).__name__}: {exc}"
    duration_ms = round((perf_counter() - started) * 1000, 3)
    return BenchmarkSample(
        benchmark_type=benchmark_type,
        duration_ms=duration_ms,
        ok=ok,
        safe_details=_strip_sensitive(details),
        error=error,
    )


def _bench_game_loop_turn(context: _BenchmarkContext) -> dict[str, Any]:
    provider = PlaytestLLMProvider()
    game_loop = GameLoop(
        state=create_initial_state(WorldLoader(context.worlds_root), context.world_id),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
    )
    result = game_loop.step("observe")
    return {"turn": result.state.turn, "events": len(game_loop.event_log.list_events())}


def _bench_world_tick(context: _BenchmarkContext) -> dict[str, Any]:
    state = create_initial_state(WorldLoader(context.worlds_root), context.world_id)
    result = run_world_tick(state)
    return {"delta_count": len(result.state_deltas), "event_created": result.event is not None}


def _bench_save_load(context: _BenchmarkContext) -> dict[str, Any]:
    repository = SQLiteSaveRepository(context.temp_dir / f"benchmark-save-{uuid4().hex}.db")
    state = create_initial_state(WorldLoader(context.worlds_root), context.world_id)
    repository.save_snapshot("benchmark-save", state, events=[])
    loaded = repository.load_save("benchmark-save")
    return {"world_id": loaded.world_id}


def _bench_migration_dry_run(context: _BenchmarkContext) -> dict[str, Any]:
    repository = SQLiteSaveRepository(context.temp_dir / f"benchmark-migration-{uuid4().hex}.db")
    state = create_initial_state(WorldLoader(context.worlds_root), context.world_id)
    repository.save_snapshot("benchmark-save", state, events=[])
    report = MigrationService(repository).dry_run("benchmark-save")
    return {"applied_migrations": len(report.applied_migrations), "dry_run": report.dry_run}


def _bench_validate_world(context: _BenchmarkContext) -> dict[str, Any]:
    report = validate_world_pack(context.world_id, worlds_root=context.worlds_root)
    return {"ok": report.ok, "errors": len(report.errors), "warnings": len(report.warnings)}


def _bench_map_graph_build(context: _BenchmarkContext) -> dict[str, Any]:
    pack = WorldLoader(context.worlds_root).load(context.world_id)
    graph = build_authoring_map_visual_graph(pack)
    return {"nodes": len(graph.nodes), "edges": len(graph.edges)}


def _bench_quest_graph_roundtrip(context: _BenchmarkContext) -> dict[str, Any]:
    service = ContentAuthoringService(context.worlds_root)
    content = service.read_file(context.world_id, "quests.yaml")
    graph = quest_yaml_to_graph(context.world_id, content)
    yaml_content = quest_graph_to_yaml(graph)
    roundtrip_graph = quest_yaml_to_graph(context.world_id, yaml_content)
    return {"quests": len(roundtrip_graph.quests), "edges": len(roundtrip_graph.edges)}


def _bench_memory_search(context: _BenchmarkContext) -> dict[str, Any]:
    _ = context
    store = InMemoryMemoryStore(
        [
            MemoryRecord(
                id=f"memory-{index:03d}",
                content=f"safe public memory {index}",
                tags=["benchmark", "public"],
                entity_ids=["player"],
                fact_ids=["public_fact"],
                visibility=MemoryVisibility.NARRATOR_SAFE,
                importance=index % 5,
                created_turn=index,
            )
            for index in range(100)
        ]
    )
    result = store.search_memory(MemoryQuery(tags=["benchmark"], substring="public", limit=10))
    return {"matches": len(result)}


def _bench_scenario_regression_run(context: _BenchmarkContext) -> dict[str, Any]:
    scenario = PlaytestScenario(
        id="benchmark_exploration",
        world_id=context.world_id,
        name="Benchmark exploration",
        scenario_type=PlaytestScenarioType.EXPLORATION,
        agent_type="random_valid_action_agent",
        max_steps=2,
        seed=42,
    )
    report = run_playtest_scenario(scenario, worlds_root=str(context.worlds_root))
    return {"passed": report.passed, "turns_run": report.playtest_report.turns_run}


_RUNNERS: dict[str, Callable[[_BenchmarkContext], dict[str, Any]]] = {
    BenchmarkType.GAME_LOOP_TURN: _bench_game_loop_turn,
    BenchmarkType.WORLD_TICK: _bench_world_tick,
    BenchmarkType.SAVE_LOAD: _bench_save_load,
    BenchmarkType.MIGRATION_DRY_RUN: _bench_migration_dry_run,
    BenchmarkType.VALIDATE_WORLD: _bench_validate_world,
    BenchmarkType.MAP_GRAPH_BUILD: _bench_map_graph_build,
    BenchmarkType.QUEST_GRAPH_ROUNDTRIP: _bench_quest_graph_roundtrip,
    BenchmarkType.MEMORY_SEARCH: _bench_memory_search,
    BenchmarkType.SCENARIO_REGRESSION_RUN: _bench_scenario_regression_run,
}


def _stats(samples: list[BenchmarkSample]) -> BenchmarkStats:
    grouped: dict[str, list[float]] = {}
    for sample in samples:
        if not sample.ok:
            continue
        grouped.setdefault(sample.benchmark_type, []).append(sample.duration_ms)
    return BenchmarkStats(
        p50={name: round(median(values), 3) for name, values in sorted(grouped.items()) if values},
        p95={name: _percentile(values, 95) for name, values in sorted(grouped.items()) if values},
        max={name: round(max(values), 3) for name, values in sorted(grouped.items()) if values},
    )


def _percentile(values: list[float], percentile: int) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((percentile / 100) * (len(ordered) - 1))))
    return round(ordered[index], 3)


def _regressions(
    max_values: dict[str, float],
    thresholds: dict[str, float],
    budgets: dict[str, PerformanceBudgetEntry],
) -> list[BenchmarkRegression]:
    regressions: list[BenchmarkRegression] = []
    for name, budget in sorted(budgets.items()):
        observed = max_values.get(name)
        if observed is None:
            continue
        if observed > budget.blocker_ms:
            regressions.append(
                BenchmarkRegression(
                    benchmark_type=name,
                    threshold_ms=budget.blocker_ms,
                    observed_ms=observed,
                    severity="blocker",
                    budget_name="v1.0",
                )
            )
        elif observed > budget.warning_ms:
            regressions.append(
                BenchmarkRegression(
                    benchmark_type=name,
                    threshold_ms=budget.warning_ms,
                    observed_ms=observed,
                    severity="warning",
                    budget_name="v1.0",
                )
            )
    for name, threshold in sorted(thresholds.items()):
        observed = max_values.get(name)
        if observed is not None and observed > threshold:
            regressions.append(
                BenchmarkRegression(
                    benchmark_type=name,
                    threshold_ms=threshold,
                    observed_ms=observed,
                    severity="warning",
                    budget_name="custom_threshold",
                )
            )
    return regressions


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_sensitive(item)
            for key, item in value.items()
            if _safe_key_value(key, item)
        }
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if "sk-" in lowered or "api_key" in lowered or "prompt" in lowered or "hidden fact" in lowered:
            return "[redacted]"
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower()
    forbidden = ["api_key", "llm_api_key", "secret", "sk-", "prompt", "hidden fact", "fact_text", "state_json"]
    return not any(term in lowered for term in forbidden)
