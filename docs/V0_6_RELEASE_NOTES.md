# v0.6 Release Notes

## 1. Version Name

v0.6 - Local Studio Hardening

## 2. Version Goal

v0.6 turns the local interactive novel engine into a safer and more inspectable
local studio prototype. The focus is not larger simulation scope; it is safer
save evolution, better authoring workflows, stronger local evaluation, visual
debugging, lightweight instrumentation, and packaging research.

This remains a local self-use engine. It is not a hosted service, not a
multiplayer platform, and not a cloud product.

The LLM is still not the world judge. The world engine remains the source of
truth. LLM providers may parse intent, render narration, summarize memory, or
draft author-facing candidates, but rule outcomes, migrations, graph
visibility, combat results, mod validation, and playtesting reports are
determined by local code.

## 3. New Features

### Save Migration System

- Added explicit save/schema version metadata.
- Added `GameState.schema_version`.
- Added migration registry, deterministic migration service, dry-run support,
  backup metadata, migration history, and legacy save migration paths.
- Added compatibility fixture tests for v0.3-like, v0.4-like, v0.5-like,
  corrupted, hidden-fact, debug-memory, and old content-pack-version saves.

### Migration CLI/API

- Added local migration status, dry-run, apply, and migration list surfaces.
- CLI supports listing migrations and inspecting/applying migration for a save.
- Migration API returns reports and metadata, not raw hidden `GameState`.

Always dry-run migration before applying it.

### Richer Authoring UI

- Added a more useful local authoring interface:
  - world/file tree
  - raw YAML editor
  - lightweight form views for common content types
  - validation panel
  - preview panel
  - dirty state tracking
  - discard and reload
- Authoring remains local-only and gated by `ENABLE_AUTHORING_API`.

### Authoring Diff / Preview / Dry Run

- Added authoring preview/draft/impact APIs.
- Draft validation uses temporary files and does not write active world files.
- Impact analysis detects removed ids, changed exits, and possible save-impact
  risks.
- Path traversal and non-whitelisted files are rejected.

### Visual Relationship / Faction Graphs

- Added player-safe graph APIs for relationships and factions.
- Added debug graph APIs gated by `ENABLE_DEBUG_API`.
- Added frontend graph panels for player-visible graph data and debug graph
  data.
- Fixed player visible relationship filtering so hidden relationship endpoints
  do not enter `visible_state.relationships`.

### Automated Playtesting Agents

- Added local deterministic playtesting agents:
  - random valid action agent
  - explore agent
  - quest-following agent
  - stress agent
- Agents act through the normal `GameLoop`/test harness and do not directly
  modify `GameState`.
- Playtesting agents are testing tools, not formal player AI.

### Narrative Quality Evals

- Added deterministic narrative quality evals for:
  - contradiction with `ActionResult`
  - invented key item/NPC/location
  - hidden fact leakage
  - hidden witness leakage
  - illegal suggested actions
  - visible consequence checks
- Evals do not use an external LLM judge and do not call real model APIs in
  automated tests.

### Performance Instrumentation

- Added local in-memory performance samples controlled by
  `ENABLE_PERF_LOGGING`.
- Added debug performance APIs gated by `ENABLE_DEBUG_API`.
- Current sampling covers game loop stages, save/load, memory search, and
  authoring validation.
- No telemetry is uploaded.
- Performance instrumentation must not record API keys, prompt text, hidden
  fact text, raw `GameState`, or raw `state_deltas`.

### Advanced Mod Versioning

- Expanded content-only mod validation with:
  - engine version bounds
  - content schema version
  - dependencies
  - optional dependencies
  - conflicts
  - deterministic load order hints
  - compatible worlds
  - migration notes
- Mod system still does not execute arbitrary code.

### Desktop Packaging Prototype

- Added `docs/DESKTOP_PACKAGING.md`.
- Added Windows PowerShell local launcher prototype:
  - starts backend
  - starts frontend
  - opens local frontend URL
- This is not a formal desktop installer, signed application, or release
  package.
- `.env` and API keys are not bundled into frontend assets.

### Local Model Provider Slice

- Added `LLM_PROVIDER=local_stub`.
- Added `LLM_PROVIDER=local_http` as a configuration-checked placeholder.
- `local_http` requires `LOCAL_LLM_BASE_URL`, but it is not a full local model
  integration and does not guarantee compatibility with any specific local
  model product.
- Local providers remain behind `LLMProvider`.

### Advanced Combat Slice

- Added lightweight combat stance/status expansion:
  - stances: `aggressive`, `defensive`, `cautious`, `fleeing`
  - status effects: `guarded`, `stunned`, `bleeding`
  - non-lethal attack marker
  - flee risk
  - visible combat summary
- Combat outcomes remain rule-engine decisions. The LLM does not judge hit,
  damage, flee, death, or incapacitation.

## 4. Behavior Changes

- Player-visible relationships now require both:
  - the relationship is known by player, and
  - both relationship endpoints are visible to the player.
- Save/load now carries schema/content/mod metadata for migration-aware
  workflows.
- Authoring save now has stronger preview/dry-run support before writing.
- Debug graph and performance views are explicitly debug-gated local tools.
- Frontend includes richer authoring, graph panels, and local studio flows.
- Combat visible state can include a player-safe active combat summary.

## 5. API Changes

### Migration

- `GET /migrations`
- `GET /saves/{save_id}/migration-status`
- `POST /saves/{save_id}/migrate-dry-run`
- `POST /saves/{save_id}/migrate`

### Authoring Preview / Dry Run

- `POST /authoring/worlds/{world_id}/preview-file-change`
- `POST /authoring/worlds/{world_id}/validate-draft`
- `POST /authoring/worlds/{world_id}/impact-analysis`

These require `ENABLE_AUTHORING_API=true`.

### Graphs

Player-safe:

- `GET /game/{session_id}/graphs/relationships`
- `GET /game/{session_id}/graphs/factions`

Debug-only:

- `GET /debug/sessions/{session_id}/graphs/relationships`
- `GET /debug/sessions/{session_id}/graphs/factions`

Debug graph APIs require `ENABLE_DEBUG_API=true`.

### Performance

- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

These require `ENABLE_DEBUG_API=true`. Recording requires
`ENABLE_PERF_LOGGING=true`.

## 6. Content Pack / Mod Format Changes

### Content Pack

- Save metadata now tracks content-pack version data where available.
- Content docs now describe `schema_version`, `content_pack_version`, graph
  visibility expectations, and combat/life fields.
- Existing content pack files remain YAML data; no arbitrary code execution is
  introduced.

### Mod Manifest

Mod manifests can now include:

- `content_schema_version`
- `optional_dependencies`
- `load_order_hint`
- `compatible_worlds`
- `migration_notes`

Existing fields remain:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `dependencies`
- `conflicts`
- `entry_worlds`
- `content_paths`
- `author`
- `description`

Mods remain content-only. The mod loader rejects executable code and path
traversal.

## 7. Save Migration Changes

- New saves include richer version metadata.
- Legacy saves can be migrated to the current schema through registry-backed
  deterministic migrations.
- Dry-run is supported and should be used before apply.
- Apply creates backup metadata and records `migration_history`.
- Migration failure must not overwrite the original save.
- Hidden facts, debug memory, hidden relationships, and visibility
  classifications must remain protected across migration.

## 8. Frontend Changes

- Authoring view now supports multiple panels, raw/form editing, validation,
  preview, dirty state, discard, reload, and save confirmation flow.
- Player-visible relationship and faction graph panels were added.
- Debug graph panels were added under the debug area.
- Save browser and local studio UX reflect v0.6 migration/authoring workflows.
- Frontend continues not to store API keys and does not directly access the
  local filesystem.

## 9. Testing / Evals Changes

- Backend suite now includes 454 passing tests at acceptance.
- Added migration compatibility fixtures and tests.
- Added authoring preview/dry-run tests.
- Added graph API tests.
- Added playtesting agent tests.
- Added narrative quality eval tests.
- Added performance instrumentation tests.
- Added advanced mod versioning tests.
- Added local provider and combat expansion tests.
- Added v0.6 integration regression tests.

Narrative evals are deterministic and do not use an external LLM judge.

## 10. Performance / Instrumentation Changes

- Added `PerformanceSample` and in-memory recorder.
- Added local stage timing for selected backend flows.
- Added debug performance recent/summary APIs.
- Added `ENABLE_PERF_LOGGING`.
- No telemetry upload is implemented.
- Performance work is observational only and must not bypass correctness
  boundaries.

## 11. Desktop Packaging Prototype Status

v0.6 includes a desktop packaging prototype, not a production desktop release.

Current status:

- documented in `docs/DESKTOP_PACKAGING.md`
- Windows PowerShell launcher script exists
- starts backend/frontend local processes
- opens local browser URL
- no installer
- no code signing
- no auto-update
- no cloud sync
- no API key embedding

## 12. Known Limitations

- Desktop packaging is prototype-only.
- `local_http` is a placeholder and is not a completed local model provider.
- Authoring UI is not a full IDE or graphical quest graph editor.
- Narrative quality evals are not a substitute for human writing review.
- Performance instrumentation is local/in-memory and not production APM.
- Mod versioning is deterministic and simple; no SAT resolver or online mod
  registry exists.
- Playtesting agents are deterministic testing helpers, not player-facing AI.
- Combat expansion remains lightweight and not tactical/grid combat.
- Economy, faction conflict, and NPC planning remain lightweight rule systems.
- Authoring/debug/performance APIs are local development tools and should not
  be exposed publicly.
- Non-blocking hardening remains:
  - sanitize mod manifest error paths further
  - move performance tag filtering from blacklist to allowlist
  - improve backup id reporting when migration backup names collide
  - default debug panel closed
  - clean mojibake text in eval/local stub fixtures

## 13. Upgrade Notes From v0.5

1. Run the full test suite after pulling v0.6.
2. Back up local SQLite saves before migration.
3. Use migration dry-run before apply:

```powershell
python -m app.tools.migrate_save --save-id SAVE_ID --dry-run
```

4. Apply migration only after reviewing the dry-run report:

```powershell
python -m app.tools.migrate_save --save-id SAVE_ID --apply
```

5. Review content-only mod manifests for new version fields if using mods.
6. Keep authoring/debug/performance APIs local-only.
7. Use `LLM_PROVIDER=mock` or `local_stub` for tests and offline development.
8. Do not place API keys in frontend `.env`, source files, docs, saves, logs,
   fixtures, or desktop launcher scripts.

## 14. Recommended v0.7 Direction

1. Formalize desktop packaging path:
   - local data directories
   - process lifecycle
   - installer decision
   - secret handling
2. Harden diagnostics:
   - sanitize mod manifest paths
   - use allowlisted performance tags
3. Expand migration discipline:
   - richer fixture generation
   - migration rollback/diff tooling
   - content/mod compatibility reports
4. Improve authoring UX:
   - nested quest stages
   - NPC schedules
   - NPC goals
   - relationship/faction graph editing
5. Implement optional real local HTTP provider while preserving `LLMProvider`
   schema validation and world boundaries.
6. Expand deterministic playtesting:
   - long-run worlds
   - save migration chains
   - mod combinations
7. Clean and expand narrative quality eval fixtures.
8. Split more public/debug fields, especially raw reputation values and
   faction conflict tags.

## Final Notes

v0.6 is accepted for release preparation based on:

- `python -m pytest`: 454 passed
- `cd frontend && npm.cmd run build`: passed

The architecture remains intact: world engine is truth, LLM is language layer,
canonical changes use `StateDelta`, actions and ticks record `Event`, and
player-facing surfaces are filtered by visibility rules.
