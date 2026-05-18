# v0.9 Roadmap: Quality & Automated Playtesting

## Goal

v0.9 turns the local studio into a repeatable quality and automated
playtesting toolchain. It helps authors find broken references, unreachable
quest paths, hidden information leaks, coverage gaps, balance outliers,
save/load/migration instability, benchmark regressions, and mod compatibility
risks.

The world engine remains the source of truth. The LLM remains a language layer.
Quality tools are local reports and gates, not automatic world repair.

## Not In v0.9

- LLM world judge.
- Cloud sync, accounts, multiplayer, or hosted quality service.
- Arbitrary mod code execution.
- Full tactical combat, large-scale war, or large-scale economy simulation.
- Automatic rewriting of user world packs.
- Performance shortcuts that bypass `StateDelta`, `EventLog`, validation, or
  visibility boundaries.
- Writing eval/playtest/quality results into active `GameState`.
- Treating playtest results as formal story events.

## Development Order

1. World quality baseline schema.
2. Expanded playtest scenarios and scenario regression authoring.
3. Hidden information leak regression suite.
4. Quest completion and dead-end analysis.
5. NPC behavior coverage and schedule conflict detection.
6. Economy, combat, and social consequence sanity checks.
7. Save/load/migration stress tests and performance benchmarks.
8. Narrative consistency evals.
9. Health score and content coverage dashboards.
10. Branch diff regression and mod compatibility stress testing.
11. Playtest batch runner.
12. Quality gate CLI/API.
13. v0.9 integration regression tests and audits.

## Module Summary

### WorldQualityReport

Defines `WorldQualityReport`, `QualityIssue`, `QualityMetric`, and
`QualityRunMetadata`. Reports carry safe summaries and debug-only hidden
details. Normal report views must not include hidden fact text, secrets, raw
state, raw deltas, API keys, or raw env.

### Automated Playtesting Scenario Expansion

Adds structured scenario types for exploration, quest, combat, stealth,
economy, crime/social, save/load, migration, and hidden-leak probes. Agents act
through the game loop or test harness only.

### Hidden Leak Regression Suite

Tests hidden facts, NPC secrets, hidden witnesses, relationships, faction
conflict, memory, raw deltas, hidden quests, items, map edges, and rumor truth
across player APIs, narrator context, memory context, graphs, maps, shops, and
normal quality reports.

### Quest, Dead-End, NPC, Schedule, Economy, Combat, And Social Analysis

Adds deterministic analyzers that emit quality issues and metrics. They do not
auto-fix content, call LLMs, or modify active saves.

### Stress And Benchmark Suites

Save/load/migration stress tests use temporary local databases and mock/local
providers. Benchmarks record safe timing samples only and do not upload
telemetry.

### Narrative Consistency Evals

Checks mock/fake narrator outputs against `ActionResult`, visible state,
timeline, NPC knowledge, quest state, and the rule that memory is not
authoritative fact. No external LLM judge is used.

### Health And Coverage Dashboards

Health scores aggregate quality reports into explainable categories. Scores are
heuristics, not absolute creative judgments. Coverage reports summarize covered
and uncovered content with hidden entities redacted from normal views.

### Branch Diff And Mod Compatibility Regression

Branch diff regression selects relevant local scenarios based on changed
content. Mod compatibility stress tests dependency/conflict/load-order and
validation behavior without executing mod code.

### Quality Gate

The quality gate combines validation, hidden leak checks, quest/dead-end/NPC
analysis, economy/combat/social checks, stress tests, benchmarks, scenario
regression, and mod compatibility smoke tests. It uses deterministic code,
thresholds, and severities for pass/fail.

## API And CLI

Representative CLI commands:

```powershell
python -m app.tools.quality_gate --world mist_valley
python -m app.tools.playtest_batch --world mist_valley --seeds 1,2,3
python -m app.tools.benchmark --world mist_valley
```

Representative API routes:

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

## Security And Visibility

- Quality reports normal views must use safe summaries only.
- Debug-only details must be explicitly marked.
- Evals, playtests, benchmarks, and quality gates must not call real LLM APIs
  in automated tests.
- Quality tooling must not modify active `GameState` or active saves.
- Current implementation has no standalone `ENABLE_QUALITY_API`; quality flows
  use existing local flags where implemented. Keep the backend local-only.

## Acceptance Criteria

- `python -m pytest` passes.
- `cd frontend && npm run build` passes.
- Quality reports serialize safely.
- Hidden leak suites do not print hidden text in normal output.
- Quality gate can pass a valid world and fail a blocker world.
- No LLM output becomes canonical state.
- No quality report is treated as an absolute creative judgment.
