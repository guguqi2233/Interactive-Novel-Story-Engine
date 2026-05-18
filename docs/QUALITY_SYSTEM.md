# v0.9 Quality System

v0.9 adds a local quality and automated playtesting layer. It is an authoring
and regression toolchain, not a player-facing world system. Quality reports do
not modify active `GameState`, active saves, or content-pack files, and they do
not call real LLM APIs in automated tests.

## WorldQualityReport Schema

`WorldQualityReport` is the common safe report envelope used by v0.9 analyzers.

Core fields:

- `run_id`
- `world_id`
- `created_at`
- `engine_version`
- `schema_version`
- `content_pack_version`
- `categories`
- `metrics`
- `issues`
- `summary`
- `recommended_actions`

`QualityRunMetadata` carries run identity and version context for the tool that
produced the report.

`QualityIssue` fields:

- `id`
- `severity`: `info`, `warning`, `error`, or `blocker`
- `category`
- `file`, optional and path-sanitized for normal views
- `path`, optional structured YAML/schema path
- `entity_id`, optional
- `message`
- `safe_details`
- `hidden_details_debug_only`, optional and never included in normal report
  summaries

`QualityMetric` fields:

- `name`
- `value`
- `unit`, optional
- `category`
- `threshold`, optional
- `status`: `ok`, `info`, `warning`, `error`, `blocker`, or `unknown`

Normal report serialization must strip `hidden_details_debug_only`. Reports
must not contain hidden fact text, NPC secrets, hidden witness details, raw
`GameState`, raw `state_deltas`, API keys, raw environment variables, prompt
text, or sensitive local paths.

## Quality Gate Config

`QualityGateConfig` controls release-style local checks:

- `allow_warnings`
- `fail_on_error`
- `fail_on_blocker`
- `max_performance_p95_ms`
- `min_health_score`
- `benchmark_iterations`
- `playtest_seeds`
- `playtest_steps`
- `mod_max_combinations`

`QualityGateResult` includes:

- `gate_id`
- `created_at`
- `world_id`
- `passed`
- `blockers`
- `errors`
- `warnings`
- `report_links`
- `health_score`
- `summary`
- `local_only`

The gate is deterministic. It combines validation, hidden-leak regression,
quest/dead-end/NPC/economy/combat/social reports, save/load/migration stress,
benchmarks, scenario regression, and mod compatibility smoke checks. The LLM
does not decide pass/fail.

CLI:

```powershell
python -m app.tools.quality_gate --world mist_valley
python -m app.tools.quality_gate --world mist_valley --json
```

API:

```text
POST /quality/worlds/{world_id}/gate/run
```

## PlaytestScenario Schema

Expanded playtest scenarios support:

- `exploration`
- `quest_path`
- `combat_path`
- `stealth_path`
- `economy_path`
- `crime_social_path`
- `save_load_path`
- `migration_path`
- `hidden_leak_probe`

Fields:

- `id`
- `world_id`
- `name`
- `description`
- `scenario_type`
- `initial_conditions`
- `agent_type`
- `max_steps`
- `seed`
- `expected_outcomes`
- `forbidden_outcomes`
- `invariants`
- `tags`

Agents act through the normal game loop or test harness and must not directly
modify `GameState`. Tests use mock/local-stub providers.

Batch runner:

```powershell
python -m app.tools.playtest_batch --world mist_valley --seeds 1,2,3
```

## BenchmarkReport Schema

Benchmark types:

- `game_loop_turn`
- `world_tick`
- `save_load`
- `migration_dry_run`
- `validate_world`
- `map_graph_build`
- `quest_graph_roundtrip`
- `memory_search`
- `scenario_regression_run`

`BenchmarkReport` fields:

- `benchmark_id`
- `created_at`
- `world_id`
- `environment_summary_safe`
- `samples`
- `p50`
- `p95`
- `max`
- `thresholds`
- `regressions`

Benchmarks are local and do not upload telemetry. They must not record prompt
text, API keys, hidden fact text, raw state, or raw deltas.

CLI:

```powershell
python -m app.tools.benchmark --world mist_valley
```

API:

```text
POST /quality/benchmarks/run
GET /quality/benchmarks/recent
```

## Health Score Categories

`WorldHealthScore` aggregates quality reports into explainable dimensions:

- `structure`
- `reachability`
- `secrecy`
- `continuity`
- `balance`
- `coverage`
- `performance`
- `migration_safety`

Blocker issues significantly reduce scores. The health score is a heuristic
authoring aid, not an absolute quality judgment and not a canonical world fact.

API:

```text
GET /quality/worlds/{world_id}/health
POST /quality/worlds/{world_id}/health/run
```

## Coverage Report Categories

`ContentCoverageReport` summarizes coverage from event logs, timelines,
playtest reports, and scenario regression reports.

Covered entity groups:

- locations
- NPCs
- items
- quests
- facts
- factions
- rumors
- crimes
- combat encounters
- shops/trade

Normal coverage reports show totals, covered/uncovered counts, percentages,
and safe summaries. Hidden entities must not appear in normal details. Debug
reports may expose debug ids only through debug/local-only surfaces.

API:

```text
GET /quality/worlds/{world_id}/coverage
POST /quality/worlds/{world_id}/coverage/run
```

## Local-Only API Boundary

Current v0.9 quality tooling uses existing local flags:

- `ENABLE_PLAYTEST_API`
- `ENABLE_EVAL_API`
- `ENABLE_DEBUG_API`
- `ENABLE_PERF_LOGGING`

There is no separate `ENABLE_QUALITY_API` setting yet. The main quality gate is
gated through the eval/playtest/debug path, benchmark routes use debug/perf
gating, and some analyzer endpoints are local-only without an independent
quality flag. Keep the backend bound to localhost and do not expose quality
routes as a hosted service.

## Known Limits

- Quality reports do not auto-fix content.
- Quality scores are not absolute judgments.
- Evals do not use an external LLM judge.
- Playtest agents are testing tools, not formal player AI.
- Stress tests use temporary local data, not real user saves.
- Mod compatibility stress does not execute mod code or solve complex SAT
  version constraints.
