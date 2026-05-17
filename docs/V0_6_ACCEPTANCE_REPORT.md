# v0.6 Acceptance Report

## Verdict

Accepted for v0.6 with non-blocking hardening items.

The current project satisfies the v0.6 scope for Local Studio Hardening: save
migration, richer authoring, authoring preview/dry-run, graph visualization,
playtesting agents, narrative quality evals, performance instrumentation,
advanced mod versioning, desktop launcher prototype, local provider slice, and
advanced combat slice are implemented and covered by automated tests.

The previous release-blocking visibility issue in `visible_state.relationships`
was fixed before this acceptance run. Player-visible relationships now require
both relationship visibility and actor endpoint visibility.

## Verification Date

2026-05-18

## Verification Commands

```powershell
python -m pytest
```

Result: 454 passed.

```powershell
cd frontend
npm.cmd run build
```

Result: TypeScript build and Vite production build passed.

PowerShell printed a local profile signature warning during command startup.
The warning did not change command exit status.

## Scope Accepted

### 1. Save Migration

Accepted.

- `SaveGame` stores engine/schema/world/content metadata, timestamps, enabled
  mod metadata, and migration history.
- `GameState` includes `schema_version`.
- Migration registry, migration service, dry-run, backup metadata, and apply
  paths are implemented.
- Legacy-style saves migrate to the current schema.
- Dry-run does not write database state.
- Migration failure tests verify the original save is not overwritten.
- EventLog preservation and hidden/debug visibility preservation are covered
  by compatibility tests.

### 2. Migration CLI/API

Accepted.

- API endpoints exist for migration listing, status, dry-run, and apply.
- CLI supports list, status, dry-run, and apply.
- API responses return migration metadata and reports, not raw hidden
  `GameState`.
- Missing save and migration errors return clear failures.

### 3. Migration Compatibility Test Suite

Accepted.

- Fixture saves cover v0.3-like, v0.4-like, v0.5-like, corrupted, hidden-fact,
  debug-memory, and old content-pack-version cases.
- Corrupted saves fail safely.
- EventLog preservation, `migration_history`, and visibility preservation are
  tested.

### 4. Richer Authoring UI

Accepted as a local prototype.

- Frontend authoring view provides world/file tree, raw YAML editor,
  lightweight form views for common entity types, validation panel, preview
  panel, dirty state, discard, and reload.
- Authoring disabled state is handled safely.
- Authoring data remains separate from the player narrative UI.

### 5. Authoring Preview / Dry Run

Accepted.

- Preview, draft validation, and impact-analysis APIs are implemented.
- Preview writes only to temporary draft directories and does not modify active
  world files or active session `GameState`.
- Diff summary, affected references, removed-id impact, parse errors, and
  validation reports are exposed structurally.
- Path traversal and non-whitelisted file names are rejected.

### 6. Visual Relationship / Faction Graphs

Accepted.

- Player graph endpoints and debug graph endpoints are implemented.
- Player graph returns only player-visible relationships/factions.
- Debug graph is gated by `ENABLE_DEBUG_API`.
- Frontend graph panels render player graph data separately from debug graph
  data.
- Regression tests cover hidden relationship endpoints and hidden fact
  non-leakage.

### 7. Automated Playtesting

Accepted.

- Playtesting agents choose player input from visible state and act through
  `GameLoop`.
- Agents do not directly mutate `GameState`.
- Fixed seed behavior, report structure, invariant violations, visibility leak
  detection, event creation, and save/load roundtrip are tested.

### 8. Narrative Quality Evals

Accepted as deterministic test tooling.

- Evals cover contradiction with `ActionResult`, invented item/NPC/location,
  hidden fact leakage, hidden witness leakage, suggested-action legality, and
  visible consequence checks.
- Evals use deterministic data and do not call real APIs or external LLM
  judges.

### 9. Performance Instrumentation

Accepted.

- `ENABLE_PERF_LOGGING` controls local in-memory performance samples.
- Samples are structured and cover game loop phases, save/load, memory search,
  and authoring validation.
- Debug performance APIs are gated by `ENABLE_DEBUG_API`.
- Tests verify disabled behavior, enabled recording, debug API gating, and
  absence of API key/raw delta leakage in performance responses.

### 10. Advanced Mod Versioning

Accepted.

- Mod manifests support version bounds, content schema version, dependencies,
  optional dependencies, conflicts, load order hint, compatible worlds, and
  migration notes.
- Dependency, conflict, engine compatibility, content schema compatibility,
  load order, path traversal, and executable-file rejection are tested.
- Mod validation remains content-only and reuses world validation.

### 11. Desktop Packaging Prototype

Accepted as documentation/prototype only.

- `docs/DESKTOP_PACKAGING.md` exists.
- `scripts/start_local_studio.ps1` starts backend/frontend local development
  processes and opens the local frontend URL.
- The prototype does not create a formal installer, does not perform signing,
  does not implement auto-update, and does not embed `.env` or API keys into
  frontend assets.

### 12. Local Model Provider Slice

Accepted.

- `local_stub` is available through provider factory and supports deterministic
  offline/test behavior.
- `local_http` is a configuration-checked placeholder and fails clearly when
  `LOCAL_LLM_BASE_URL` is missing.
- Business modules continue to depend on `LLMProvider`.
- Local model output still cannot directly mutate `GameState`.

### 13. Advanced Combat Slice

Accepted.

- Combat stance/status fields are structured.
- `defend`, flee risk, guarded, stunned, bleeding, non-lethal attack, and
  visible combat summary are implemented.
- Combat results are deterministic rule outcomes and do not call the LLM.
- Visible combat summary filters hidden NPCs/witnesses.

### 14. v0.6 Integration Tests

Accepted.

- v0.6 integration regression coverage verifies migration, authoring preview,
  graph APIs, playtesting, narrative evals, performance, mod versioning,
  provider slice, combat slice, and key visibility boundaries.

## Boundary Review

### LLM Boundary

Passed.

- LLM remains parser, narrator, summarizer, and optional author-facing draft
  assistant.
- v0.6 migration, authoring preview, graph generation, playtesting, evals,
  performance, mod versioning, desktop launcher, local provider selection, and
  combat expansion do not grant LLM world-judge authority.
- Provider factory remains the central runtime provider selection path.
- `local_stub` and `local_http` remain behind `LLMProvider`.
- Automated tests use mock/fake/local providers and do not call real OpenAI or
  external LLM judge services.

### World-State Boundary

Passed.

- Player actions, system ticks, NPC planning ticks, and playtesting-driven
  inputs are recorded as events through existing game loop/test harness paths.
- Canonical state changes are represented through `StateDelta`.
- Migration and authoring flows do not give LLM or frontend code authority to
  directly mutate active `GameState`.

### Visibility / Memory / Debug Boundary

Passed after blocker fix.

- Hidden facts, NPC secrets, hidden witnesses, hidden NPCs, hidden/debug
  memory, and hidden relationships are tested against player API/narrator
  leakage paths.
- `visible_state.relationships` now filters relationship endpoints by actor
  visibility.
- Debug timeline, debug graph, and performance data remain debug-gated and do
  not enter narrator input.
- MemoryContextBuilder keeps hidden/debug memory out of narrator-safe context.

### Authoring / Security Boundary

Passed for local-only scope.

- Authoring API is gated by `ENABLE_AUTHORING_API`.
- Debug and performance debug APIs are gated by `ENABLE_DEBUG_API`.
- Authoring file access is whitelisted and rejects path traversal.
- Authoring preview/dry-run does not write real world files or active saves.
- Mod loader rejects executable files and path traversal.
- Desktop prototype does not package `.env` or API keys.

### Correctness Over Performance

Passed.

- Performance instrumentation is observational and local.
- No performance path bypasses `StateDelta`, `EventLog`, schema validation,
  migration validation, provider abstraction, or visibility filtering.

## Known Limitations

- Desktop packaging is a launcher/documentation prototype, not a formal
  installer, signed app, auto-updater, or production packaging workflow.
- `local_http` is a provider interface stub and does not yet call a real local
  model server.
- Narrative quality evals are deterministic checks, not a replacement for
  human writing review.
- Performance instrumentation is in-memory/local only and not a production APM
  system.
- Authoring UI is useful for local editing but is not a full IDE, graphical
  quest graph editor, or collaborative editor.
- Mod versioning uses simple deterministic checks, not a complex SAT solver.
- No cloud sync, account system, multi-user collaboration, online mod registry,
  or online mod download.
- Economy, faction conflict, combat, and NPC planning remain lightweight
  rule-based systems, not full simulations.
- Some non-blocking hardening items remain: mod manifest error messages can be
  further sanitized, performance tag filtering can move from blacklist to
  allowlist, migration backup id reporting can be made more precise under
  backup-name collision, debug panel can default closed, and mojibake text in
  eval/local stub fixtures can be cleaned.

## Acceptance Risks

- Low: authoring/debug/performance APIs are intentionally local-only but should
  not be exposed outside localhost without additional controls.
- Low: mod validation remains content-only and blocks executable suffixes, but
  formal packaging should continue to avoid arbitrary code execution.
- Low: performance tag sanitization is adequate for current call sites but
  should be hardened with an allowlist before broader instrumentation.
- Low: migration compatibility covers current fixture set; future schema
  changes must add new fixtures before release.
- Low: debug panel defaults and UX should continue to be treated as local
  development tooling, not player-facing content.

No high-risk or release-blocking acceptance risk remains after the relationship
visibility fix.

## Recommended v0.7 Priorities

1. Formalize desktop packaging path: local data directories, process lifecycle,
   installer decision, and secret handling.
2. Harden diagnostics: sanitize mod manifest paths and use allowlisted
   performance tags.
3. Expand migration discipline with versioned fixture generation and migration
   rollback/diff tooling.
4. Improve authoring UX for nested quest stages, NPC schedules, goals, and
   relationship/faction graph editing.
5. Add optional real local HTTP provider implementation while preserving
   `LLMProvider` schema validation and world-boundary rules.
6. Expand playtesting scenarios for long-run content packs, save migration
   chains, and mod combinations.
7. Improve narrative quality eval fixture readability and add curated JSONL
   cases for manual model evaluation.
8. Add stricter public/debug field separation for faction reputation raw values
   and faction conflict tags.

## Final Status

v0.6 is accepted for release preparation.

Verification completed with:

- `python -m pytest`: 454 passed
- `cd frontend && npm.cmd run build`: passed

The project remains aligned with the core architecture: the world engine is the
source of truth, LLMs are language-layer providers, all canonical changes use
`StateDelta`, all handled actions/ticks are evented, and player-facing APIs are
filtered through visibility boundaries.
