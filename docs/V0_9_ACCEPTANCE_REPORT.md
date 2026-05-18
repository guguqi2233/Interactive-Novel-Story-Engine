# v0.9 Acceptance Report

## Verdict

**Accepted for local v0.9 release with non-blocking cautions.**

v0.9 meets the planned "Quality & Automated Playtesting" scope. The project now
has a repeatable local quality toolchain covering structured quality reports,
expanded deterministic playtesting, scenario regression authoring, hidden-leak
regression, quest/dead-end analysis, NPC and schedule coverage, economy/combat
and social-consequence checks, save/load/migration stress, performance
benchmarks, narrative consistency evals, health and coverage dashboards, branch
diff regression, mod compatibility stress, playtest batch runs, and a quality
gate CLI/API.

The core boundary remains intact: the world engine is still the source of
truth, LLMs remain language-layer providers, quality tooling is advisory, and
quality/playtest/eval outputs do not mutate active `GameState` or active saves.

## Verification Date

2026-05-19

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: **728 passed in 28.77s**.
- `cd frontend && npm.cmd run build`: **passed** with `tsc -b && vite build`.

Note: the local PowerShell profile signing warning appears during command
execution. It is local shell noise and did not affect test or build results.

## Scope Accepted

### 1. World Quality Report

Accepted.

- `WorldQualityReport`, `QualityIssue`, `QualityMetric`, and
  `QualityRunMetadata` are structured Pydantic schemas.
- Issues and metrics carry category, severity/status, safe details, and
  optional debug-only hidden details.
- `model_dump_normal()` removes `hidden_details_debug_only` from normal report
  payloads.
- Reports are advisory artifacts and do not modify `GameState`.

### 2. Playtesting Scenarios

Accepted.

- Expanded `PlaytestScenario` supports exploration, quest, combat, stealth,
  economy, crime/social, save/load, migration, and hidden-leak probe paths.
- Fixed seeds produce deterministic runs.
- Agents act through game-loop/test-harness paths rather than directly
  mutating `GameState`.
- Playtest reports expose safe normal payloads and do not include hidden text in
  ordinary output.

### 3. Scenario Regression Authoring

Accepted.

- Local authoring APIs support listing, previewing, validating, and saving
  scenario regression cases.
- Preview does not write disk.
- `forbidden_visible_facts`, expected visible facts, quest state expectations,
  input sequences, max turns, and tags are configurable.
- Scenario authoring does not modify active `GameState` or active saves.

### 4. Hidden Leak Suite

Accepted.

- Hidden leak evals cover visible state, narrator context, memory context,
  player graph, player map, quest visible state, shop/player UI data, scenario
  reports, and quality report normal views.
- Debug/player API separation is tested.
- Failure output uses safe reasons and does not print hidden fact text in normal
  logs.

### 5. Quest / Dead-End Analysis

Accepted.

- Quest completion analysis detects missing next-stage references, missing
  trigger references, unreachable stages, circular paths, terminal-stage gaps,
  hidden-quest visibility risks, and availability issues.
- Dead-end analysis detects unreachable required items/NPCs/facts, locked paths
  without access, missing objective triggers, and hidden clue availability
  problems.
- These analyzers emit `QualityIssue`/`WorldQualityReport` output and do not
  alter content packs or runtime state.

### 6. NPC / Schedule Coverage

Accepted.

- NPC behavior coverage reports NPCs seen/talked to, goals, activated goals,
  planning actions, schedule moves, reactions, rumor spread, crime reports, and
  combat participation.
- Schedule conflict detection catches invalid locations, overlapping schedule
  blocks, missing/default schedule concerns, quest-required NPC availability,
  merchant availability, and goal/location mismatches.
- Hidden NPC details stay out of normal report payloads.

### 7. Balance Checks

Accepted.

- Economy balance checks cover negative prices, arbitrage risk, non-tradeable
  shop items, hidden shop item exposure, reward outliers, missing merchant item
  references, and extreme modifiers.
- Combat balance checks cover lethal dead ends, impossible flee paths,
  non-lethal objective gaps, critical NPC death without fallback, missing combat
  rewards, public combat consequence gaps, and hidden witness leak risks.
- Social consequence coverage detects missing rumor/faction references,
  hidden-fact leakage risk, untriggerable rules, duplicate consequence risks,
  and playtest-triggered rumor/reputation coverage.
- Balance checks are advisory and do not auto-edit world data.

### 8. Stress / Benchmark

Accepted.

- Save/load/migration stress tests cover 100+ turn playtests, repeated
  save/load cycles, migration dry-run/apply, save-bundle import/export, and
  replay dry-run.
- Performance benchmark suite covers game loop turns, world tick, save/load,
  migration dry-run, validation, map graph building, quest graph roundtrip,
  memory search, and scenario regression runs.
- Benchmark reports use safe environment summaries and do not record API keys,
  prompt text, hidden facts, raw `GameState`, or raw `state_deltas`.
- Thresholds are configurable.

### 9. Narrative Consistency

Accepted.

- Narrative consistency evals catch invented items, invented locations, hidden
  witness reveals, dead NPC speaking, unknown NPC knowledge, invented quest
  stages, and memory treated as authoritative fact.
- Evals use mock/fake narrator outputs and do not call real LLM APIs or
  external LLM judges.
- Failure reports use safe summaries.

### 10. Dashboards

Accepted.

- World Health Dashboard consumes `WorldHealthScore` summaries with category
  scores, blockers, warnings, recommended actions, and last-run metadata.
- Content Coverage Dashboard consumes `ContentCoverageReport` summaries for
  locations, NPCs, items, quests, facts, factions, rumors, crimes, combat, and
  trade coverage.
- Quality API endpoints are gated by local eval/playtest/perf/debug flags.
- Normal UI/report payloads do not display hidden details.

### 11. Branch / Mod Regression

Accepted.

- Branch diff regression selects relevant regression subsets for changed
  quests, maps, items/economy, NPCs, and hidden-fact changes.
- Mod compatibility stress checks dependency resolution, conflicts, load order,
  validation, broken references, migration risk, and hidden leak subsets.
- Mod stress does not execute mod code and does not access files outside the
  mod root.

### 12. Quality Gate

Accepted.

- `python -m app.tools.quality_gate --world mist_valley` CLI is implemented and
  tested.
- `POST /quality/worlds/{world_id}/gate/run` is implemented and gated.
- Blocker issues fail the gate; warning-only behavior is configurable.
- Pass/fail is determined by deterministic severity/threshold logic, not by
  LLM output.
- Normal quality gate result does not leak hidden details.

### 13. v0.9 Integration Tests

Accepted.

- v0.9 integration regression tests cover quality report aggregation,
  playtesting scenarios, hidden leak probes, quest/dead-end checks, NPC and
  schedule checks, balance checks, stress/benchmark paths, narrative
  consistency, and quality gate behavior.
- Full backend suite passed: **728 tests**.
- Frontend build passed.

## Boundary Review

### LLM Boundary

Passed.

- v0.9 quality analyzers, playtest scenarios, leak suites, quest/dead-end
  analysis, NPC/schedule coverage, balance checks, stress tests, benchmarks,
  branch/mod regression, and quality gate are deterministic local code paths.
- Narrative consistency evals do not use an external LLM judge.
- Quality gate pass/fail is not delegated to an LLM.
- LLM output does not directly enter `GameState`.
- Provider selection remains centralized through `LLMProvider` and provider
  factory for runtime configurable providers.

### StateDelta / Event Boundary

Passed.

- Runtime state changes remain routed through `StateDelta` and `apply_delta`.
- Player actions, system ticks, NPC planning ticks, and playtesting actions are
  event-producing flows.
- Quality reports, evals, benchmarks, and regression outputs do not become
  canonical world events or active save data.
- Stress and replay dry-run paths use temporary/local in-memory execution where
  appropriate and do not overwrite real user saves.

### Visibility / Leak / Debug Boundary

Passed.

- Hidden facts, NPC secrets, hidden witnesses, hidden memory, hidden
  relationships, hidden faction conflict, hidden map edges, hidden quests, and
  hidden shop items are excluded from player-facing normal surfaces.
- Normal quality, playtest, scenario, benchmark, health, coverage, and gate
  payloads strip debug-only hidden details.
- Raw `state_deltas` remain debug-only and are not returned by player APIs or
  narrator prompts.
- Debug APIs remain separate from player APIs.

### Security / Test Data Boundary

Passed for local self-use release.

- Quality APIs are now gated by local eval/playtest/perf/debug feature flags.
- Playtesting and stress tests use mock/local-stub providers and temporary data.
- Benchmarks do not record prompt text, API keys, hidden facts, raw env, or raw
  state JSON.
- Mod compatibility stress does not execute code.
- Import/export protections from earlier releases remain covered by tests.

## Known Limitations

- `ActionResult.reason` is still included in narrator input and relies on rule
  code keeping that field player-safe. A future release should split
  `player_reason` and `debug_reason`.
- Quality scores and coverage percentages are heuristics. They are useful local
  signals, not absolute judgments of creative quality.
- Static quest/dead-end/schedule/balance analyzers are intentionally practical,
  not formal proofs of every possible play path.
- No standalone `ENABLE_QUALITY_API` setting exists yet; v0.9 quality routes
  use the existing local eval/playtest/perf/debug flags.
- Debug APIs can intentionally expose raw timeline/delta data when enabled and
  should stay local-only.
- Playtesting agents are test harnesses, not player AI or autonomous NPC
  cognition.
- Benchmarks are local smoke/performance checks and are not a full profiling or
  telemetry system.

## Acceptance Risks

- Future analyzers must keep hidden prose out of `message` and `safe_details`;
  raw hidden detail belongs only in debug-only fields.
- If debug APIs are enabled in a shared environment, raw debug data could be
  exposed outside the intended local workflow.
- If rule code puts hidden details into `ActionResult.reason`, narrator prompts
  could receive unsafe content despite current tests and conventions.
- Large or heavily modded worlds may require more sophisticated regression
  selection, benchmark thresholds, and analyzer tuning.

## Recommended v1.0 Priorities

1. Split player-safe and debug-only action reasons.
2. Add a central hidden-content sanitizer that can scan all normal reports
   against loaded hidden fact texts and NPC secrets.
3. Introduce an explicit `ENABLE_QUALITY_API` setting for clearer local studio
   control.
4. Add frontend contract tests to keep debug-only data confined to debug panels.
5. Expand quality gate profiles for "authoring draft", "release candidate", and
   "strict regression" modes.
6. Improve analyzer precision for large worlds, especially quest reachability,
   schedule availability, and branch/mod regression selection.
7. Add stronger package/release secret scanning with allowlisted fake test keys.

## Final Status

**v0.9 is accepted for local release.**

The release satisfies the planned Quality & Automated Playtesting goals, passes
the full backend test suite and frontend build, and preserves the core project
boundaries: world engine as fact source, LLM as language layer, StateDelta/Event
authority, local-only quality tooling, and hidden/debug data separation.
