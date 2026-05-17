# v0.7 Release Notes

## 1. Version Name

**v0.7 - Polished Local Studio**

This release is for the local-only interactive novel world engine. It is not a hosted service, not a multiplayer platform, and not a public marketplace release.

## 2. Version Goal

v0.7 turns the v0.6 local studio from a capable collection of tools into a smoother day-to-day workspace for local world authoring, validation, migration, debugging, evaluation, playtesting, packaging, and privacy review.

The core authority model is unchanged:

- The world engine is the source of truth.
- The LLM is still a parser, narrator, summarizer, or optional draft assistant.
- The LLM is not the world judge.
- No LLM output directly mutates `GameState`.
- Runtime state changes still go through `StateDelta` and are recorded through `Event`.

## 3. New Features

### Studio Home Dashboard

- Adds a local studio home surface for backend status, world count, recent saves, API feature flags, validation summaries, provider status, and recent playtest status.
- Provides quick navigation into play, authoring, save browser, migration, mod manager, graphs, evals, performance, playtesting, import/export, and settings.
- Uses safe summaries only; it does not display API keys, raw environment variables, raw `GameState`, raw `state_deltas`, or hidden facts.

### Save Migration UI

- Exposes migration status, dry-run, apply, migration history, and migration list workflows in the local frontend.
- Dry-run is explicitly non-writing.
- Apply is confirmation-gated in the UI.
- Migration UI does not display raw hidden save payloads or raw `GameState`.

### Mod Manager UI

- Adds a local mod management view for discovered mods, versions, dependencies, conflicts, compatible worlds, content schema version, validation status, migration notes, and load order.
- Mod manager does not execute arbitrary mod code.
- Mod validation remains content/YAML validation through the backend.

### Narrative Quality Dashboard

- Adds a dashboard over deterministic narrative quality eval reports.
- Reports include totals, categories, failed cases, and safe failure reasons.
- Evals do not call a real LLM and do not use an external LLM judge.
- Hidden fixture text is redacted from failure reasons before API/UI exposure.

### Performance Dashboard

- Adds frontend views for local performance summaries and recent samples.
- Covers game loop, intent parse, action resolve, world tick, narrator, save/load, memory search, and authoring validation timing where samples exist.
- Performance instrumentation does not upload telemetry and does not record prompt text, API keys, hidden fact text, raw `GameState`, or raw `state_deltas`.

### Automated Playtesting Dashboard

- Adds local playtest APIs and UI for fixed-seed deterministic runs.
- Supports agent type, step count, seed, and save/load checks.
- Reports actions, turns, errors, invariant violations, visibility leak summaries, save/load failures, and final state summary.
- Playtesting agents act through the game loop/test harness and are not formal player AI.

### App Settings / Local Privacy Panel

- Adds a safe local settings/privacy view.
- Shows provider status, authoring/debug/perf/eval/playtest feature flags, database configuration status, and local privacy notes.
- Does not expose API keys, raw env, full sensitive paths, or allow frontend edits to `.env`.

## 4. Behavior Changes

- v0.7 emphasizes local-studio navigation and UX consistency across play, authoring, debugging, migration, mod management, evals, performance, playtesting, import/export, and settings.
- Dangerous local operations such as migration apply, save deletion, file overwrite, and similar workflows have clearer confirmation patterns.
- Narrative eval failure reasons now redact forbidden hidden terms instead of echoing the raw hidden fixture text.
- Save/export workflows are treated as sensitive local archive workflows because save bundles can contain full hidden/internal state.
- Debug and authoring data remain intentionally powerful but are visually and API-separated from player-facing surfaces.

## 5. API Changes

New or expanded local studio APIs include:

- `GET /studio/status`
- `GET /studio/config-summary`
- `GET /evals/narrative/recent`
- `POST /evals/narrative/run`
- `GET /evals/narrative/{run_id}`
- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`
- `GET /authoring/templates`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/templates/{template_id}/render`
- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`
- `GET /authoring/mods/{mod_id}`
- `GET /authoring/mods/load-order`
- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`

Existing migration APIs remain part of the v0.7 UI flow:

- `GET /saves/{save_id}/migration-status`
- `POST /saves/{save_id}/migrate-dry-run`
- `POST /saves/{save_id}/migrate`
- `GET /migrations`

Local-only controls:

- Authoring/import/export/template/quest graph/mod APIs are guarded by `ENABLE_AUTHORING_API`.
- Debug/performance graph/timeline APIs remain guarded by `ENABLE_DEBUG_API`.
- Eval APIs are local/debug-controlled.
- Playtest APIs are guarded by `ENABLE_PLAYTEST_API` or debug mode.

These APIs are for local development and authoring. They are not designed as public remote service endpoints.

## 6. Frontend Changes

- Adds Studio Home Dashboard.
- Adds Save Migration UI inside the save workflow.
- Adds Mod Manager UI.
- Adds Narrative Quality Dashboard.
- Adds Performance Dashboard.
- Adds Automated Playtesting Dashboard.
- Adds Settings / Local Privacy Panel.
- Adds Scenario Template preview/render UI.
- Adds Visual Quest Graph Editor initial slice.
- Adds import/export controls for local world, mod, and save archives.
- Improves local-only notices, disabled API states, error/empty states, confirmations, and navigation.
- Keeps debug/authoring/player surfaces separated.
- Frontend still does not store or display API keys.

## 7. Desktop Packaging Changes

- Updates `docs/DESKTOP_PACKAGING.md`.
- Improves local launcher scripts:
  - `scripts/start_local_studio.ps1`
  - `scripts/start_local_studio.sh`
- Launcher workflow checks local dependencies, starts backend/frontend, opens local URLs, and reports local feature flag status where applicable.
- Desktop packaging remains a local prototype/enhanced launcher workflow.
- It is not a signed installer, not an auto-updater, not a cloud client, and not a public distribution package.
- `.env` and API keys must not be bundled into frontend or desktop artifacts.

## 8. Local Model Provider Changes

- Expands local provider support through `LLM_PROVIDER`.
- Supported local options:
  - `local_stub`: deterministic offline placeholder.
  - `local_http`: configurable HTTP provider for local model service experiments.
- `local_http` configuration:
  - `LOCAL_LLM_BASE_URL`
  - `LOCAL_LLM_MODEL`
  - `LOCAL_LLM_TIMEOUT_SECONDS`
  - `LOCAL_LLM_JSON_MODE`
- Provider construction still goes through `LLMProvider` and the provider factory.
- `generate_json` remains Pydantic schema-validated.
- Tests use fake transports and do not call real local model services.
- Local model output still cannot directly write `GameState`, apply `StateDelta`, decide combat, decide validation, or become world authority.

## 9. Authoring / Templates / Quest Graph Changes

### Scenario Templates

- Adds data-only scenario template support.
- Templates support list, preview, render, and validate flows.
- Preview does not write disk.
- Templates do not call LLM.
- Templates do not execute scripts.
- Templates do not directly modify running saves or active `GameState`.
- Rendered content must pass validation before use.

### Visual Quest Graph Editor

- Adds `quests.yaml` to graph conversion.
- Adds graph preview back to YAML.
- Invalid stage edges are caught by validation.
- Preview does not write disk or active saves.
- Saving still goes through the authoring validation path.
- Quest graph editor does not call LLM and does not bypass `validate_world`.

### Authoring Boundary

- Authoring UI may show full local YAML content to the creator, including hidden world content.
- That content must remain separate from player UI and narrator payloads.
- Authoring APIs remain local-only and gated.

## 10. Testing / Evals Changes

- Backend suite collected 502 tests.
- Final full run passed: **502 passed**.
- Frontend build passed: `tsc -b && vite build`.
- Adds/updates tests for:
  - Studio status/config summaries
  - Narrative eval safety and hidden fixture redaction
  - Playtesting reports and invariants
  - Local provider fake transport behavior
  - Mod manager/versioning behavior
  - Scenario templates
  - Quest graph authoring
  - Import/export safety
  - v0.7 integration regression
  - Migration/mod UI integration
- Narrative quality evals are deterministic rule checks and do not use external LLM judges.
- One first-pass full pytest run showed a transient v0.4 save/load comparison failure. The specific test passed on direct rerun, and the second full suite passed. This is tracked as a non-blocking hardening item.

## 11. Import / Export Changes

- Adds local archive import/export for:
  - world packs
  - mod packages
  - save bundles
- Archive format is zip-based.
- Import rejects:
  - zip slip / path traversal
  - executable files
  - `.env`
  - secrets files
  - database files
  - log files
  - disallowed code/script suffixes
- Imports run validation.
- Save bundle import checks migration status.
- Import/export does not execute arbitrary code.
- Save bundle exports can contain full internal save state by design and should be treated as sensitive local archives.

## 12. Known Limitations

- v0.7 is still local self-use software, not a hardened public SaaS or multiplayer product.
- Desktop packaging remains a prototype/enhanced launcher, not a formal installer.
- Save bundles can contain hidden/internal state and should not be shared casually.
- Debug APIs expose internal events and `state_deltas` when enabled; keep them local-only.
- Authoring UI intentionally exposes hidden content to the local creator.
- Narrative quality evals are deterministic guardrails, not authoritative literary judgments.
- Performance instrumentation is local timing telemetry only and does not optimize the engine by itself.
- Local HTTP provider support is configurable but not guaranteed to work with every local model server.
- Some older prompt/eval/provider fixture strings still show encoding artifacts; this does not affect the authority boundary but should be cleaned.
- The initial transient save/load comparison failure suggests a future deterministic serialization cleanup is worthwhile.

## 13. Upgrade Notes From v0.6

1. Review `.env.example` for new or expanded local studio options:
   - `ENABLE_EVAL_API`
   - `ENABLE_PLAYTEST_API`
   - `ENABLE_PERF_LOGGING`
   - `LOCAL_LLM_BASE_URL`
   - `LOCAL_LLM_MODEL`
   - `LOCAL_LLM_TIMEOUT_SECONDS`
   - `LOCAL_LLM_JSON_MODE`
2. Keep authoring/debug/perf/eval/playtest APIs bound to local use.
3. Run save migration status before relying on older saves:
   - use the UI or migration API/CLI.
4. Treat exported save bundles as sensitive local archives.
5. Validate imported worlds/mods before use.
6. Do not commit `.env`, local databases, logs, `frontend/dist`, desktop build outputs, or generated archives.
7. If using `local_http`, understand that prompts are sent to the configured local endpoint, and the endpoint may have its own logging behavior.
8. Scenario template output and quest graph edits should be previewed and validated before saving.

## 14. Recommended v0.8 Direction

1. Stronger export/import UX with explicit sensitive archive warnings and safer file download/upload flows.
2. Dedicated `ENABLE_EVAL_API` gate independent of full debug mode.
3. Deterministic serialization helpers for set/list fields in save/load equality tests.
4. More frontend component-level tests for disabled API states and debug/player separation.
5. Better desktop packaging prototype while still excluding secrets.
6. Cleanup of corrupted/mojibake fixture and prompt text.
7. Richer authoring previews for hidden-content risk and migration impact.
8. More local model provider compatibility tests using fake transports only.
9. Continued Studio UX polish for long sessions, empty states, and local safety messaging.

## Final Notes

v0.7 is accepted as a local self-use release. It improves the studio workflow without changing the fundamental rule:

**The world engine decides what is true. The LLM only helps with language.**
