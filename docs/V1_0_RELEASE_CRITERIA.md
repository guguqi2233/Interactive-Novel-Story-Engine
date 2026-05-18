# v1.0 Release Criteria

## Release Goal

v1.0 is the **Stable Local Studio Edition** of the local interactive novel world
engine. The release goal is stability, compatibility, documentation, and
repeatable local acceptance rather than new gameplay expansion.

v1.0 is ready to freeze only when the project can demonstrate that:

- The world engine remains the single source of truth.
- LLMs remain language-layer providers and never become world judges.
- Core schemas and local API contracts are stable enough for long-term local
  world authoring.
- Existing v0.9 saves, content packs, quality tools, and local studio workflows
  remain compatible.
- Release checks are deterministic, local, and safe to run without real API
  calls.

## Required Verification Commands

The following commands must pass before v1.0 can be tagged:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

The following local quality commands or equivalent test/API coverage must also
pass:

```powershell
python -m app.tools.quality_gate --world mist_valley
python -m app.tools.benchmark --world mist_valley
```

Additional required suites:

- Quality gate.
- Hidden information leak regression suite.
- Save/load/migration stress tests.
- Scenario regression suite.
- Performance benchmark suite.

These checks must use mock, fake, or local stub providers. They must not call
real OpenAI APIs or real local model services during CI-style verification.

## Required Documents

The following documents must exist and be current before v1.0 freeze:

- `docs/SPEC.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `docs/CONTENT_PACKS.md`
- `docs/DESKTOP_PACKAGING.md`
- `README.md`
- `docs/UPGRADE_GUIDE_V0_TO_V1.md`
- `docs/END_TO_END_LOCAL_WORKFLOW.md`
- `docs/V1_0_ROADMAP.md`
- `docs/V1_0_ACCEPTANCE_REPORT.md`
- `docs/V1_0_RELEASE_NOTES.md`
- `docs/V1_0_RELEASE_CRITERIA.md`

The documentation must clearly state that this is a local self-use engine, not
a hosted multi-user platform.

## Interface Freeze Scope

The following contracts are considered v1.0 freeze candidates. Changes after
v1.0 should require migration notes, compatibility tests, and release-note
entries.

### Core GameState Schema

Freeze scope:

- `GameState` top-level fields.
- Player, NPC, location, quest, fact, faction, relationship, economy, memory,
  combat, and visibility-related state shapes.
- `schema_version` semantics.

Acceptance:

- Existing v0.9 saves load or migrate.
- Hidden/debug fields do not become player-visible.
- Memory remains advisory and never becomes authoritative fact state.

### StateDelta

Freeze scope:

- StateDelta operation names.
- Path format.
- Validation/error semantics.
- Apply behavior.

Acceptance:

- All canonical runtime mutations still go through `StateDelta`.
- Direct `GameState` mutation remains limited to construction, loading,
  migration, or test fixture setup.
- Replay and save/load remain deterministic.

### Event

Freeze scope:

- Event identity and ordering fields.
- Actor/action/result/tick/event-type semantics.
- EventLog replay expectations.

Acceptance:

- Player actions, system ticks, NPC planning ticks, and playtesting agent
  actions produce Events.
- EventLog can support debug timeline, replay dry-run, save recovery, and
  regression analysis.

### Content Pack Schema

Freeze scope:

- World pack file layout and whitelisted YAML files.
- Location visual fields.
- Quest graph fields.
- NPC goal fields.
- Relationship/faction fields.
- Economy/item fields.
- Rumor/crime/consequence fields.
- Scenario/template/package metadata fields.

Acceptance:

- `validate_world` produces structured reports.
- Visual editors cannot bypass validation.
- Authoring preview/dry-run does not write disk.
- Hidden authoring data does not enter player APIs.

### Save Migration Contract

Freeze scope:

- Save metadata fields.
- `schema_version`, engine version, world/content-pack version semantics.
- Migration registry behavior.
- Dry-run/apply semantics.
- `migration_history` shape.

Acceptance:

- Migration is deterministic.
- Dry-run never writes database state.
- Apply preserves EventLog and does not destroy the original save on failure.
- Migration does not change visibility classification.

### Mod Manifest Contract

Freeze scope:

- Mod manifest fields.
- Version comparison rules.
- Dependency/conflict/load-order behavior.
- Compatible worlds and schema version fields.

Acceptance:

- Mod validation does not execute code.
- Path traversal is rejected.
- Mod compatibility stress can run without modifying original worlds or mods.

### LLMProvider Interface

Freeze scope:

- Provider factory as the only runtime provider selection entry.
- `generate_text` and `generate_json` interface behavior.
- Schema validation for structured output.
- Mock/local stub/local HTTP/OpenAI provider configuration boundaries.

Acceptance:

- Business rules do not directly instantiate provider implementations.
- Missing provider configuration fails clearly.
- LLM output never directly mutates `GameState`.
- Prompt profiles cannot enable hidden facts or debug state in narrator input.

### Player API

Freeze scope:

- Player-facing visible state response shape.
- Game action request/response shape.
- Save/load browser safe summary shape.
- Player-visible graph/map/shop/quest fields.

Acceptance:

- No hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden
  map edges, hidden quests, hidden items, hidden memory, or raw
  `state_deltas` appear in player API payloads.

### Authoring API

Freeze scope:

- Local authoring enable flag behavior.
- World pack read/write endpoints.
- Preview/validate/save semantics.
- Visual editor graph endpoints.
- Template, import/export, branch/diff, scenario authoring endpoints.

Acceptance:

- `ENABLE_AUTHORING_API` controls access.
- Authoring APIs only access whitelisted local content roots.
- Path traversal is rejected.
- Save operations run validation first.
- Authoring never modifies active session `GameState`.

### Debug API

Freeze scope:

- Local debug enable flag behavior.
- Timeline, graph, performance, replay, and debug summary response shape.

Acceptance:

- `ENABLE_DEBUG_API` controls access.
- Debug APIs do not return API keys, raw env, database URLs, or sensitive local
  paths.
- Debug data never enters narrator prompts or player API responses.

## Required Security Boundaries

v1.0 must satisfy all of the following:

- No API keys are tracked in git.
- No `.env`, database, log, cache, `node_modules`, `frontend/dist`, or desktop
  build outputs are tracked.
- No hidden facts appear in player API payloads.
- No raw `state_deltas` appear in player API payloads.
- No LLM output directly mutates `GameState`.
- No arbitrary mod code is executed.
- No authoring path traversal is possible.
- Import/export rejects zip slip and executable payloads.
- Template rendering does not execute scripts.
- Performance and benchmark reports do not include prompt text, API keys, hidden
  fact text, raw env, raw `GameState`, or raw `state_deltas`.
- Quality reports normal view does not include hidden fact text, NPC secrets, or
  debug-only details.

## Release Blockers

Any of the following blocks v1.0 freeze:

- `python -m pytest` fails.
- `cd frontend && npm.cmd run build` fails.
- Quality gate fails under the v1.0 release profile.
- Hidden leak suite detects player-facing or narrator-facing hidden data.
- Save/load/migration stress detects data loss, EventLog loss, migration
  corruption, or nondeterministic replay.
- Scenario regression suite fails on required starter-world paths.
- Performance benchmark exceeds the accepted v1.0 budget without an explicit
  documented exception.
- A real API key or sensitive local config is tracked or staged.
- `.env`, database, logs, caches, `node_modules`, `frontend/dist`, or desktop
  build outputs are tracked or staged.
- Any business/runtime module bypasses provider factory for real provider
  selection.
- Any rule module delegates rule judgment to LLM output.
- Any active gameplay state mutation bypasses `StateDelta`.
- Player API returns hidden facts, NPC secrets, hidden witnesses, hidden
  relationships, hidden map edges, hidden quests, hidden shop items, hidden
  memory, debug memory, or raw `state_deltas`.
- Authoring, template, mod, branch/diff, or import/export APIs allow path
  traversal.
- Mod loading, template rendering, or package import executes arbitrary code.
- v0.9 saves cannot load or migrate without a documented, tested migration
  path.
- Required v1.0 documents are missing.

## Non-Blocking Known Limitations

A limitation may be non-blocking only if it is documented, does not violate a
security/visibility/state boundary, and has a clear v1.1 or later follow-up.

Examples of acceptable non-blocking limitations:

- Quality scores are heuristic and not absolute creative judgments.
- Static analyzers are practical checks, not formal proofs of every possible
  path.
- Playtesting agents are test harnesses, not real player AI.
- Debug APIs expose debug data only when explicitly enabled for local use.
- Desktop packaging remains a local startup shell rather than a signed public
  installer.
- Some large-world performance budgets may be advisory if documented with local
  machine context.

Examples that are not non-blocking:

- Hidden data leakage to player/narrator surfaces.
- Real API keys in tracked files.
- Failed migrations that can corrupt user saves.
- Rule decisions delegated to an LLM.
- Mod/package/template arbitrary code execution.

## v1.0 Tag Checklist

Before creating `v1.0`, complete this checklist:

### Repository State

- [ ] `git status --short` is clean or contains only expected v1.0 files.
- [ ] No `.env`, database, logs, cache, `node_modules`, `frontend/dist`, or
      desktop build outputs are tracked or staged.
- [ ] Secret scan finds no real API keys.
- [ ] Fake test keys are documented and clearly non-real.

### Tests and Builds

- [ ] `python -m pytest` passes.
- [ ] `cd frontend && npm.cmd run build` passes.
- [ ] Quality gate passes under the v1.0 release profile.
- [ ] Hidden leak regression suite passes.
- [ ] Save/load/migration stress passes.
- [ ] Scenario regression suite passes.
- [ ] Performance benchmark passes or documented exceptions are approved.

### API and Schema Freeze

- [ ] Core `GameState` schema freeze reviewed.
- [ ] `StateDelta` freeze reviewed.
- [ ] `Event` and EventLog freeze reviewed.
- [ ] Content pack schema freeze reviewed.
- [ ] Save migration contract freeze reviewed.
- [ ] Mod manifest contract freeze reviewed.
- [ ] `LLMProvider` interface freeze reviewed.
- [ ] Player API freeze reviewed.
- [ ] Authoring API freeze reviewed.
- [ ] Debug API freeze reviewed.

### Boundary Review

- [ ] LLM boundary audit passed.
- [ ] Visibility/privacy/debug audit passed.
- [ ] Security/local data audit passed.
- [ ] Player API does not return hidden/debug/raw state.
- [ ] Narrator only receives visible facts and narrator-safe memory.
- [ ] Quality normal reports strip hidden/debug details.

### Documentation

- [ ] `docs/SPEC.md` updated.
- [ ] `docs/WORLD_ENGINE.md` updated.
- [ ] `docs/LLM_PROTOCOL.md` updated.
- [ ] `docs/CONTENT_PACKS.md` updated.
- [ ] `docs/DESKTOP_PACKAGING.md` updated.
- [ ] `README.md` updated.
- [ ] `docs/UPGRADE_GUIDE_V0_TO_V1.md` exists and covers v0.x to v1.0.
- [ ] `docs/V1_0_ROADMAP.md` exists.
- [ ] `docs/V1_0_ACCEPTANCE_REPORT.md` exists.
- [ ] `docs/V1_0_RELEASE_NOTES.md` exists.
- [ ] `docs/V1_0_RELEASE_CRITERIA.md` exists.

### Release Artifacts

- [ ] v1.0 acceptance report records verification date and commands.
- [ ] v1.0 release notes describe new stability/freeze behavior and known
      limitations.
- [ ] Upgrade guide describes migration expectations from v0.x to v1.0.
- [ ] Final freeze check recommends tagging.
- [ ] Pre-commit review recommends commit/tag.

### Tagging

- [ ] Commit message uses a release-style summary, for example:
      `chore: freeze v1.0 stable local studio`.
- [ ] Create annotated or lightweight tag according to project convention:
      `git tag v1.0`.
- [ ] Push branch and tag:
      `git push origin main`
      `git push origin v1.0`.

## Final v1.0 Acceptance Standard

v1.0 can be accepted only when all release blockers are cleared, all required
documents exist, all required tests/builds/quality checks pass, and the project
maintains the core boundary:

**The world engine is the fact source. LLMs are language-layer providers. All
runtime state changes flow through StateDelta and EventLog. Hidden/debug data
does not enter player or narrator surfaces.**
