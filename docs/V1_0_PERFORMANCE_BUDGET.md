# v1.0 Performance Budget

## Goal

v1.0 defines local performance budgets for the stable local studio edition.
These budgets are release-readiness guardrails, not permission to bypass
correctness. No performance optimization may skip `StateDelta`, `EventLog`,
visibility filtering, validation, migration safety, or hidden/debug data
boundaries.

Benchmark and quality-gate reports are local-only. They must not upload
telemetry and must not record prompt text, API keys, hidden fact text, raw
`GameState`, raw `state_deltas`, or raw environment variables.

## Measurement Rules

- Use the local benchmark suite:

```powershell
python -m app.tools.benchmark --world mist_valley
```

- Use v1.0 quality gate standard profile:

```powershell
python -m app.tools.quality_gate --world mist_valley --profile standard
```

- Benchmark reports compare observed local `max` timings against the v1.0
  warning/blocker budgets.
- `p50` and `p95` are informational; current budget enforcement uses max timing
  in the smoke benchmark to avoid hiding rare slow samples.
- Hardware, antivirus, filesystem cache, and development logging can affect
  short-running local timing.

## Budget Matrix

| Area | Target | Warning threshold | Blocker threshold | Measurement method | Known caveats |
| --- | ---: | ---: | ---: | --- | --- |
| game_loop single turn | 150 ms | 300 ms | 1000 ms | `game_loop_turn`: one mock-provider `game_loop.step("observe")`. | Local CPU and debug logging can affect short runs. |
| world_tick | 50 ms | 150 ms | 500 ms | `world_tick`: one deterministic world tick. | Larger worlds may need documented budget updates. |
| save/load | 80 ms | 200 ms | 750 ms | `save_load`: temporary SQLite save snapshot plus load. | Disk and filesystem cache differences can shift timing. |
| migration dry-run | 80 ms | 200 ms | 750 ms | `migration_dry_run`: temporary SQLite migration status/dry-run. | Current-schema saves should normally be no-op dry-runs. |
| validate_world | 150 ms | 500 ms | 1500 ms | `validate_world`: content validator over `mist_valley`. | Content-heavy worlds may need larger per-world budgets. |
| map graph build | 80 ms | 250 ms | 1000 ms | `map_graph_build`: load world and build authoring map graph. | Very large maps should get a documented budget. |
| quest graph roundtrip | 100 ms | 350 ms | 1200 ms | `quest_graph_roundtrip`: YAML -> graph -> YAML -> graph. | Complex quest packs may need larger authoring budgets. |
| memory search | 20 ms | 80 ms | 250 ms | `memory_search`: local search across 100 safe records. | External vector backends are not part of this smoke budget. |
| scenario regression smoke | 250 ms | 750 ms | 2500 ms | `scenario_regression_run`: two-step deterministic scenario smoke. | Full scenario suites are measured separately by batch reports. |
| quality gate standard profile | 3000 ms | 8000 ms | 20000 ms | Manual end-to-end wall-clock observation of `quality_gate --profile standard`. | Current benchmark suite does not time the full gate directly. |
| frontend build size warning | advisory | 512 KB JS gzip | 1024 KB JS gzip | `cd frontend && npm.cmd run build`, inspect Vite output. | This is advisory until a frontend build-size parser is added. |

## Benchmark Integration

The benchmark suite now carries a `PerformanceBudgetEntry` schema:

- `target_ms`
- `warning_ms`
- `blocker_ms`
- `measurement_method`
- `known_caveats`

`BenchmarkRunRequest` supports:

- `use_v1_budget`: defaults to `true`
- `budget_path`: optional local JSON file for test or local override budgets
- `thresholds_ms`: existing custom warning thresholds

Budget file shape:

```json
{
  "budgets": {
    "memory_search": {
      "target_ms": 20,
      "warning_ms": 80,
      "blocker_ms": 250,
      "measurement_method": "Local memory search smoke benchmark.",
      "known_caveats": ["External vector backends are out of scope."]
    }
  }
}
```

Observed values above `warning_ms` produce warning regressions. Observed values
above `blocker_ms` produce blocker regressions. Custom `thresholds_ms` still
produce warning regressions for local experiments.

## Quality Gate Integration

The v1.0 quality gate consumes benchmark regressions:

- benchmark warning regressions enter `QualityGateResult.warnings`
- benchmark blocker regressions enter `QualityGateResult.blockers`
- pass/fail remains deterministic threshold logic
- LLM output never decides pass/fail

The gate also keeps the older `max_performance_p95_ms` override for callers
that want a single broad p95 cap.

## Safety Rules

Performance budget work must not:

- bypass `StateDelta`
- skip `EventLog`
- expose hidden facts
- expose raw `state_deltas` to player APIs
- remove validation to make authoring faster
- skip migration dry-run/apply safety
- log prompt text, API keys, hidden fact text, raw env, raw state JSON, or raw
  debug memory
- upload benchmark telemetry

## Known Limitations

- The quality gate standard profile budget is documented but not directly timed
  as a benchmark type yet.
- Frontend build size warning is advisory and not enforced by pytest yet.
- Budgets are calibrated for the bundled sample world and local smoke tests,
  not for very large custom worlds.
- Benchmark samples are short-running local checks; use them to catch obvious
  regressions, not as full production profiling.
