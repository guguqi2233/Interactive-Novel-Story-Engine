# v0.9 Release Notes

## Version Name

**v0.9: Quality & Automated Playtesting**

## Version Goal

v0.9 turns the local studio into a repeatable quality and automated
playtesting toolchain. It helps local authors find broken references,
unreachable quest paths, hidden information leaks, coverage gaps, balance
outliers, save/load/migration instability, benchmark regressions, and mod
compatibility risks.

This remains a **local self-use engine**. The LLM is still a parser, narrator,
summarizer, or draft assistant. It is not the world judge, and it does not
decide quality gate pass/fail.

## New Features

### World Quality Baseline

- Added `WorldQualityReport`, `QualityIssue`, `QualityMetric`, and
  `QualityRunMetadata`.
- Quality issues support severity, category, file/path/entity references,
  player-safe details, and explicitly marked debug-only hidden details.
- Normal report serialization strips debug-only hidden details.

### Automated Playtesting Expansion

- Expanded playtest scenarios for:
  - exploration
  - quest paths
  - combat paths
  - stealth paths
  - economy paths
  - crime/social paths
  - save/load paths
  - migration paths
  - hidden-leak probes
- Added deterministic batch playtest runs across scenarios, agents, and seeds.
- Playtesting agents remain test harnesses. They are not real player AI and do
  not become NPC cognition.

### Scenario Regression Authoring

- Added local authoring APIs and UI surfaces for scenario regression cases.
- Scenario drafts support input sequences, expected visible facts, forbidden
  visible facts, expected quest states, max turns, and tags.
- Preview does not write disk, and save requires validation.

### Hidden Information Leak Regression

- Added hidden leak eval coverage for player visible state, narrator context,
  memory context, player graph, player map, quest visible state, shop data,
  scenario reports, and quality report normal views.
- Hidden leak suite must not print hidden text in ordinary logs or normal
  report output.

### Quest, Dead-End, NPC, Schedule, Economy, Combat, and Social Analysis

- Added quest completion analysis for unreachable stages, missing triggers,
  circular paths, terminal-stage gaps, and hidden quest visibility risks.
- Added dead-end detection for unreachable required items/NPCs/facts, locked
  paths without access, missing objective triggers, and hidden clue availability
  risks.
- Added NPC behavior coverage and schedule conflict detection.
- Added economy balance sanity checks.
- Added combat balance sanity checks.
- Added faction/rumor/crime consequence coverage.

### Stress, Benchmark, and Narrative Consistency

- Added save/load/migration stress tests for long deterministic runs, repeated
  save/load, migration dry-run/apply, save bundle import/export, and replay
  dry-run.
- Added performance benchmark suite for core local operations.
- Added narrative consistency evals for invented items/locations, dead NPC
  speech, hidden witness reveals, NPC unknown facts, invented quest stages, and
  memory treated as authoritative fact.
- Narrative consistency evals do not use an external LLM judge.

### Dashboards and Quality Gate

- Added World Health Score dashboard data.
- Added Content Coverage dashboard data.
- Added Quality Gate CLI/API.
- Quality score is an explainable local heuristic, not an absolute quality
  judgment.
- Quality gate pass/fail is determined by deterministic severities and
  thresholds, not by an LLM.

## Behavior Changes

- Quality, playtesting, eval, and benchmark outputs are treated as advisory
  local tooling artifacts.
- Quality reports do not automatically modify world packs.
- Quality reports do not write to active `GameState` or active saves.
- Quality API normal responses strip debug-only hidden details.
- `/quality/...` endpoints are gated behind local eval/playtest/perf/debug
  flags.
- Benchmarks produce local timing reports only and do not upload telemetry.

## API Changes

New or expanded local API surfaces include:

- `POST /quality/worlds/{world_id}/gate/run`
- `GET /quality/worlds/{world_id}/quests`
- `POST /quality/worlds/{world_id}/quests/analyze`
- `POST /quality/worlds/{world_id}/dead-ends/analyze`
- `GET /quality/worlds/{world_id}/npc-coverage`
- `POST /quality/worlds/{world_id}/npc-coverage/analyze`
- `POST /quality/worlds/{world_id}/schedules/analyze`
- `POST /quality/worlds/{world_id}/economy/analyze`
- `POST /quality/worlds/{world_id}/combat/analyze`
- `POST /quality/worlds/{world_id}/social-consequences/analyze`
- `GET /quality/worlds/{world_id}/health`
- `POST /quality/worlds/{world_id}/health/run`
- `GET /quality/worlds/{world_id}/coverage`
- `POST /quality/worlds/{world_id}/coverage/run`
- `POST /quality/worlds/{world_id}/branch-regression/run`
- `POST /quality/mods/compatibility-stress/run`
- `POST /quality/benchmarks/run`
- `GET /quality/benchmarks/recent`
- `POST /playtests/batch/run`
- `GET /playtests/batch/{run_id}`
- Scenario regression authoring endpoints under `/authoring/scenarios`

These APIs are local studio tools. They are not intended as public hosted API
surfaces.

## Frontend Changes

- Added or expanded local studio surfaces for:
  - world health score
  - content coverage
  - scenario regression authoring
  - playtest batch reports
  - benchmark and quality report summaries
- Normal dashboard output avoids hidden details.
- Disabled API states are expected to degrade safely.

## Quality / Eval / Playtesting Changes

- Added deterministic quality analyzers and report schemas.
- Added expanded playtest scenario types.
- Added playtest batch runner.
- Added hidden information leak regression suite.
- Added narrative consistency evals.
- Added quality gate CLI/API.
- Tests use mock, fake, local stub, or deterministic harness providers. They do
  not call real OpenAI or local model services.

## Performance / Benchmark Changes

- Added `BenchmarkReport` output for repeatable local benchmarks.
- Benchmark types include game loop turn, world tick, save/load, migration
  dry-run, world validation, map graph build, quest graph roundtrip, memory
  search, and scenario regression run.
- Benchmark reports avoid API keys, prompt text, hidden fact text, raw
  `GameState`, and raw `state_deltas`.
- No telemetry is uploaded.

## Content Analysis Changes

- Added practical static/dynamic checks for quest reachability, dead ends, NPC
  coverage, schedules, economy, combat, and social consequences.
- These analyzers report warnings/errors/blockers but do not auto-fix content.
- Analyzer output should keep hidden prose out of normal fields and reserve raw
  hidden details for debug-only fields.

## Stress Testing Changes

- Added save/load/migration stress tests with temporary SQLite data.
- Added replay dry-run and import/export save-bundle stress coverage.
- Stress tests do not use real user saves.
- Stress results are reports, not canonical game events.

## Known Limitations

- `ActionResult.reason` remains narrator-visible and must stay player-safe.
  Future hardening should split `player_reason` and `debug_reason`.
- Quality score is a heuristic and should not be treated as an absolute measure
  of creative quality.
- Static analyzers are practical checks, not formal proofs of every possible
  play path.
- There is no standalone `ENABLE_QUALITY_API`; quality routes currently use
  existing local eval/playtest/perf/debug flags.
- Playtesting agents are not real player AI.
- Benchmarking is local lightweight instrumentation, not a full APM or telemetry
  system.
- Debug APIs can expose raw debug data when enabled and should remain
  local-only.

## Upgrade Notes from v0.8

- Existing v0.8 worlds should continue to load.
- Quality and benchmark APIs may require enabling the appropriate local flags:
  `ENABLE_EVAL_API`, `ENABLE_PLAYTEST_API`, `ENABLE_PERF_LOGGING`, or
  `ENABLE_DEBUG_API`.
- Quality reports are advisory and should be reviewed by the local author before
  changing content.
- Hidden leak and narrative consistency evals should be run before treating a
  world as release-ready.
- Benchmark reports are local-only and should not be compared across very
  different machines without context.
- If integrating new analyzers, keep hidden text out of `message` and
  `safe_details`; use debug-only fields for raw hidden context.

## Recommended v1.0 Direction

- Split `ActionResult.reason` into player-safe and debug-only reason fields.
- Add a central hidden-content sanitizer that scans normal reports against
  hidden facts and NPC secrets.
- Introduce explicit `ENABLE_QUALITY_API`.
- Add frontend contract tests for keeping debug-only content out of ordinary UI.
- Define quality gate profiles such as authoring draft, release candidate, and
  strict regression.
- Improve analyzer precision for large worlds and heavily modded setups.
- Expand package/release secret scanning while allowlisting known fake test
  keys.

## Verification Summary

From `docs/V0_9_ACCEPTANCE_REPORT.md`:

- `python -m pytest`: **728 passed in 28.77s**
- `cd frontend && npm.cmd run build`: **passed**

Final status: **v0.9 accepted for local release.**
