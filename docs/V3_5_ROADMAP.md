# v3.5 Roadmap: Local QA / Debug / Replay & Provider Connectivity UI Pro

## Version Goal

v3.5 turns local QA, Debug, Replay, Quality, Diagnostics, and Provider
connectivity into a daily-use local inspection workspace. Users should be able
to review Timeline Replay, EventLog, StateDelta, visible-vs-debug state,
hidden leak reports, playtests, quality gates, performance, Provider usage,
Provider connection status, local model discovery, model assignment,
Cross-Mode conflicts, module stress results, save migration, diagnostics
bundles, local test runs, and safe debug exports from one coherent UI.

v3.5 remains local-first and boundary-first. Debug and replay surfaces observe
and analyze only; they do not modify `GameState`. Normal UI uses
`visible_state` and safe summaries. Raw `state_deltas`, raw EventLog details,
debug memory, raw provider responses, and raw debug payloads require explicit
debug-gated UI. Provider Connection & Model Discovery is local configuration
for Provider Gateway, not an online platform or API resale service.

## Non-Goals

v3.5 explicitly does not implement:

- account system;
- cloud sync;
- online marketplace;
- remote package auto-download;
- online QA platform;
- real provider CI connection tests;
- API resale service;
- binding to any specific relay provider;
- Debug UI mutation of `GameState`;
- normal UI display of hidden facts, NPC secrets, debug memory, raw prompts,
  raw env, provider secrets, API keys, or raw `state_deltas`;
- Provider UI persistence of real API keys to project files;
- persistence of `transient_api_key`;
- writing `transient_api_key` to logs, diagnostics, backups, exports, prompt
  profiles, provider profiles, usage records, call traces, crash reports, or
  frontend state;
- changes to World Engine, `StateDelta`, `EventLog`, visibility, validation,
  save migration, import/export, or Provider Gateway authority.

## Hard Constraints

- Local-first behavior is mandatory.
- Debug / Replay views observe and analyze only; they must not modify
  `GameState`, saves, content packs, or EventLog.
- Raw `state_deltas` are visible only in debug-gated UI.
- `visible_state` is the safe source for normal World UI.
- Provider Gateway remains the only model entry point.
- `ProviderProfile` can store only provider metadata, `api_key_env`, and
  `secret_ref`; it must not store raw API keys.
- `transient_api_key` may be used only for one test/fetch request and must not
  be persisted.
- Provider connection and model discovery tests must use fake providers or
  fake clients in automated tests.
- CI must not call real OpenAI, OpenAI-compatible, relay, `local_http`, or
  custom provider endpoints.
- Diagnostics, logs, backup, export, quality, and debug export default to
  filtering secrets, hidden/debug data, mature/private content, raw prompts,
  raw env, raw provider responses, and raw `state_deltas`.
- All new pages must handle loading, empty, error, and disabled states.
- Dangerous operations and export/create actions require explicit confirm.
- `python -m pytest` must pass.
- `cd frontend && npm.cmd run build` must pass.

## Recommended Development Order

1. Local QA / Debug / Replay Contract Review.
2. QA / Debug Workspace Layout and shared components.
3. Timeline Replay UI Pro.
4. EventLog Viewer Pro.
5. StateDelta Viewer Pro.
6. Visible vs Debug State Compare.
7. Hidden Leak Report UI Pro.
8. Playtest Dashboard Pro.
9. Quality Gate Unified Dashboard Pro.
10. Performance Dashboard Pro.
11. Provider Connectivity Dashboard.
12. Provider Connection Test Backend.
13. Provider Model Discovery / Sync.
14. Provider Model Assignment by Mode.
15. Provider Connectivity Diagnostics / Secret Redaction.
16. Provider Usage / Cost Dashboard Pro.
17. CrossMode Conflict Review Pro.
18. Module Playtest / Stress UI Pro.
19. Save Migration Visualizer.
20. Diagnostics Bundle Review UI.
21. Local Test Run Dashboard.
22. Safe Debug Export Wizard.
23. QA / Debug UI Component Cleanup.
24. v3.5 UI Regression Tests.
25. v3.5 Integration Regression Tests.

The recommended first phase is contract review plus a shared QA / Debug /
Replay workspace shell. Provider Connectivity should begin immediately after
the review because connection testing and model discovery need explicit secret
handling contracts before UI polish.

## Module Plan

### 1. Local QA / Debug / Replay Contract Review

Goal: audit current QA, Debug, Replay, Timeline, EventLog, StateDelta,
Diagnostics, Quality, Playtest, Provider Setup, Provider usage, and performance
UI/API flows.

Frontend changes:
- document current routes, panels, component boundaries, disabled states, and
  debug-gated sections;
- identify raw debug rendering points and normal-safe rendering points;
- identify Provider setup gaps for test connection, model discovery, sync, and
  mode assignment.

Backend changes:
- none by default.

Tests:
- no required test changes unless a blocker is found and fixed.

Acceptance:
- `docs/V3_5_QA_DEBUG_REPLAY_PROVIDER_CONTRACT_REVIEW.md` exists;
- report maps current API/data flow and privacy boundaries;
- high-risk leaks or authority bypasses are either absent or tracked as
  release blockers.

### 2. Timeline Replay UI Pro

Goal: provide a clearer replay surface for turns, checkpoints, visible events,
safe replay summaries, and replay dry-run status.

Frontend changes:
- turn/time grouped replay list;
- filters by turn, event type, actor, location, and visibility category;
- safe replay summary cards;
- empty/error/disabled states for missing debug API or missing save/session.

Backend changes:
- reuse existing timeline replay APIs where possible;
- add safe-only replay summary fields only if current responses are too raw.

Tests:
- frontend build/import smoke;
- pytest for replay API safe summaries if backend changes are made.

Acceptance:
- normal replay view does not show raw `state_deltas` or hidden events;
- debug details require DebugGate and `ENABLE_DEBUG_API`;
- replay is read-only.

### 3. EventLog Viewer Pro

Goal: make EventLog review usable without exposing hidden/debug details in
normal mode.

Frontend changes:
- event list with event id, turn/time, actor, event type, safe summary, related
  quest/NPC/location/module refs;
- filters and search over safe summaries;
- jump links to World panels where safe refs exist.

Backend changes:
- optional safe EventLog summary endpoint if current debug endpoint is too raw.

Tests:
- normal view excludes hidden event text and raw delta payloads;
- debug view is gated.

Acceptance:
- player/narrator-safe events are visible;
- raw EventLog details are debug-gated;
- viewer cannot write EventLog.

### 4. StateDelta Viewer Pro

Goal: provide a debug-only StateDelta inspection surface for understanding
state changes without making raw deltas part of normal UI.

Frontend changes:
- DebugGate-wrapped StateDelta list;
- grouped by event, path, operation, module, and risk;
- safe normal summary counts outside DebugGate.

Backend changes:
- none by default; reuse debug/timeline replay response.

Tests:
- static check that raw delta rendering appears only inside DebugGate;
- pytest only if API changes.

Acceptance:
- raw deltas are not in normal UI;
- StateDelta viewer is read-only;
- debug disabled state explains `ENABLE_DEBUG_API`.

### 5. Visible vs Debug State Compare

Goal: help users understand what normal UI can see versus what debug-only data
contains.

Frontend changes:
- side-by-side safe sections for `visible_state` and debug availability;
- normal side shows player, location, visible NPCs, inventory, quests, known
  facts, and module safe summaries;
- debug side is gated and labeled internal.

Backend changes:
- optional safe compare endpoint returning counts/status rather than raw debug
  data when debug is disabled.

Tests:
- normal compare excludes raw `GameState`, hidden facts, NPC secrets, and raw
  `state_deltas`;
- debug disabled state is clear.

Acceptance:
- users can see the boundary without leaking secrets;
- no state mutation path is introduced.

### 6. Hidden Leak Report UI Pro

Goal: consolidate hidden leak reports into clear safe issue rows.

Frontend changes:
- issue table with severity, category, affected run/session/module, safe
  summary, suggested action, and jump target;
- no full hidden text rendering.

Backend changes:
- reuse existing hidden leak eval/report outputs;
- add redacted safe row adapters if needed.

Tests:
- hidden text full bodies are absent;
- no API keys or debug memory in reports.

Acceptance:
- blockers are clear and actionable;
- reports are local-only and not uploaded.

### 7. Playtest Dashboard Pro

Goal: improve automated playtest review for deterministic local runs.

Frontend changes:
- recent runs, selected report, batch report, action traces, final safe state,
  hidden leak/save-load status, and failure summaries;
- run controls for local default playtest and batch playtest.

Backend changes:
- reuse `/playtests/*` APIs;
- no real provider calls.

Tests:
- playtest dashboard builds;
- playtest reports use safe summaries and fake/local providers.

Acceptance:
- run and review are clear;
- no upload, no real provider call, no hidden leak body display.

### 8. Quality Gate Unified Dashboard Pro

Goal: unify world, project, mod, module, RP/mature, cross-mode, migration, and
release checklist statuses.

Frontend changes:
- overall status, blockers, warnings, categories, last run, affected entity,
  suggested action, and jump targets;
- no hidden text full bodies.

Backend changes:
- optional aggregation endpoint if current reports require too many UI calls.

Tests:
- no-report state is friendly;
- blocker state is clear;
- hidden/mature/debug text remains redacted.

Acceptance:
- users can decide what to fix next without reading raw reports.

### 9. Performance Dashboard Pro

Goal: expose local performance instrumentation for debug/release readiness.

Frontend changes:
- recent samples, p50/p95 summaries, component filters, local warning bands,
  and performance budget status;
- clear disabled state when instrumentation is off.

Backend changes:
- reuse existing debug performance APIs;
- add safe summaries only if needed.

Tests:
- no sensitive paths or raw debug payloads in normal performance view;
- debug disabled state is clear.

Acceptance:
- performance view is local-only and read-only.

### 10. Provider Connectivity Dashboard

Goal: provide the main local provider connection/status dashboard.

Frontend changes:
- provider list with type, base URL source, configured/missing secret status,
  enabled state, model count, last test status, last discovery status, routing
  warnings, and local-only copy;
- supports `openai`, `openai_compatible`, `relay`, `local_http`, and `custom`
  profile types;
- no plaintext API key field.

Backend changes:
- extend provider safe summaries with connection/discovery metadata if needed.

Tests:
- no API key rendered;
- relay copy states OpenAI-compatible/custom base URL only and not API resale.

Acceptance:
- users can see provider readiness without exposing secrets.

### 11. Provider Connection Test Backend

Goal: provide a safe backend path for provider connection tests.

Frontend changes:
- connection test button and result panel;
- optional one-time `transient_api_key` field only if backend explicitly
  supports it and never stores it;
- clear fake/offline test mode for CI.

Backend changes:
- `POST /projects/{project_id}/providers/{provider_profile_id}/test-connection`
  should support fake-client tests by default;
- real provider tests require explicit local opt-in outside CI;
- `transient_api_key` must be memory-only for a single request and redacted
  from all reports/logs/errors.

Tests:
- fake provider connection success/failure;
- transient key is not persisted and not logged;
- CI does not call real providers.

Acceptance:
- connection test returns safe status and redacted errors only;
- Provider Gateway remains the only model path.

### 12. Provider Model Discovery / Sync

Goal: read provider model lists and store safe model metadata as
`ModelProfile`.

Frontend changes:
- discover models action;
- model list preview;
- sync selected/all models;
- discovery errors with redacted messages.

Backend changes:
- safe-only model discovery endpoint using fake client in tests;
- safe model sync endpoint that writes `ModelProfile` metadata only;
- raw provider responses are normalized/redacted before storage.

Tests:
- fake model discovery;
- sync writes model ids/capabilities only;
- no secret or raw provider response stored.

Acceptance:
- users can update model profiles without pasting keys into project files.

### 13. Provider Model Assignment by Mode

Goal: assign discovered or manually configured models to Novel, Tavern, World,
Cross-Mode, and Quality use cases.

Frontend changes:
- mode/use-case assignment table;
- capability warnings for JSON, context length, local-only, mature policy, and
  quality use cases;
- fallback assignment preview.

Backend changes:
- reuse or extend Provider routing rule storage;
- validation endpoint for capability/policy mismatches.

Tests:
- assignment validation catches missing JSON support for structured use cases;
- assignments do not call providers and do not store secrets.

Acceptance:
- routing metadata is clear and safe;
- no authority or visibility boundary changes.

### 14. Provider Connectivity Diagnostics / Secret Redaction

Goal: ensure Provider test/discovery diagnostics are safe.

Frontend changes:
- redacted diagnostics panel for connection/discovery failures;
- copy safe summary button;
- explicit "no secrets stored" status.

Backend changes:
- central redaction for Authorization headers, raw env, API keys,
  `transient_api_key`, provider secrets, raw request/response bodies, prompts,
  and outputs.

Tests:
- fake `sk-test-*` and Authorization-like values are redacted;
- diagnostics preview does not write.

Acceptance:
- no provider secret appears in frontend, logs, diagnostics, backup, or export.

### 15. Provider Usage / Cost Dashboard Pro

Goal: improve local provider usage and cost-estimate review.

Frontend changes:
- usage by provider, model, mode, use case, time range, success/error category,
  estimated tokens, estimated cost, and latency;
- safe empty state when usage tracking is disabled.

Backend changes:
- reuse existing usage endpoints;
- optional aggregation improvements only.

Tests:
- usage reports exclude prompts, outputs, API keys, hidden facts, and raw env.

Acceptance:
- usage is local observability only, not billing-grade and not uploaded.

### 16. CrossMode Conflict Review Pro

Goal: make Cross-Mode conflicts easier to review and fix safely.

Frontend changes:
- conflict list by direction, severity, affected refs, safe summary, suggested
  action, and jump target;
- create draft fix proposal only, no automatic apply.

Backend changes:
- reuse CrossMode conflict detection APIs.

Tests:
- hidden target details remain redacted;
- no World mutation from review.

Acceptance:
- conflicts are actionable and remain proposal-based.

### 17. Module Playtest / Stress UI Pro

Goal: review advanced module playtest and compatibility stress status.

Frontend changes:
- module scenario status for tactical, economy, faction, magic, hacking,
  crafting, deduction, survival, and cultivation;
- stress blockers/warnings by namespace/action/migration/permission/hidden
  leak category.

Backend changes:
- reuse module playtest/stress quality APIs;
- optional safe aggregation endpoint.

Tests:
- reports do not execute arbitrary code or call real providers;
- hidden leak report is redacted.

Acceptance:
- module quality status is clear before release/import.

### 18. Save Migration Visualizer

Goal: make migration dry-runs and migration warnings easier to inspect.

Frontend changes:
- migration plan list, affected saves, schema version, warnings, blockers, and
  before/after safe summary;
- apply remains explicit-confirm and backend-controlled.

Backend changes:
- reuse save migration dry-run/status/apply endpoints.

Tests:
- dry-run does not write;
- apply requires confirm;
- raw save JSON and hidden state are not shown.

Acceptance:
- users can understand migration impact without reading raw saves.

### 19. Diagnostics Bundle Review UI

Goal: improve diagnostics preview and bundle review.

Frontend changes:
- preview-first bundle manifest;
- default exclusion policy;
- redaction summary;
- explicit confirm before bundle creation.

Backend changes:
- reuse diagnostics preview/create services;
- ensure Provider test/discovery artifacts follow exclusions.

Tests:
- preview does not write;
- bundle excludes `.env`, API keys, provider secrets, logs/cache/build outputs
  when configured, raw env, hidden/debug/mature/private data, raw prompts, and
  raw provider responses by default.

Acceptance:
- diagnostics are local-only and redacted.

### 20. Local Test Run Dashboard

Goal: show local pytest/frontend/check command status in a UI-friendly
dashboard without running arbitrary commands from the browser.

Frontend changes:
- displays recent local test run summaries, configured checks, last pass/fail,
  duration, and safe failure summary;
- manual "record result" or backend-managed allowlisted runner only.

Backend changes:
- optional allowlisted test-run summary service;
- no arbitrary command execution.

Tests:
- no arbitrary shell command UI;
- no logs with secrets.

Acceptance:
- dashboard is informational and safe.

### 21. Safe Debug Export Wizard

Goal: export local debug/replay/QA bundles safely.

Frontend changes:
- select scopes, preview exclusions, redaction summary, risk warnings, and
  explicit confirm;
- debug raw scopes require `ENABLE_DEBUG_API` and explicit opt-in.

Backend changes:
- safe debug export preview/create endpoints if existing diagnostics bundles
  are insufficient.

Tests:
- preview does not write;
- export filters secrets by default;
- raw debug export requires confirm.

Acceptance:
- debug export is local-only, redacted by default, and never uploaded.

### 22. QA / Debug UI Component Cleanup

Goal: extract reusable UI components for QA/debug/replay/provider surfaces.

Frontend changes:
- components such as `QAIssueRow`, `DebugGate`, `ReplayEventCard`,
  `StateDeltaSummary`, `ProviderStatusCard`, `ModelProfileCard`,
  `QualityStatusBadge`, `PerformanceMetricCard`, and `SafeExportPolicyPanel`;
- no business logic changes.

Backend changes:
- none.

Tests:
- frontend build;
- static UI check import coverage.

Acceptance:
- repeated QA/debug UI patterns use shared components and keep redaction copy.

### 23. v3.5 UI Regression Tests

Goal: prevent UI regressions in QA/debug/replay/provider connectivity.

Frontend changes:
- add `frontend/scripts/check-v35-qa-provider-ui.mjs`;
- add npm script `check:v35-qa-provider-ui`.

Backend changes:
- none unless test fixtures require safe API outputs.

Tests:
- imports for Timeline Replay, EventLog, StateDelta, Hidden Leak, Playtest,
  Quality, Performance, Provider Connectivity, Model Discovery, Model
  Assignment, Diagnostics, and Debug Export UI;
- static checks for no plaintext API key, no normal raw state deltas, DebugGate
  copy, fake-provider CI copy, and no account/cloud/marketplace/API resale.

Acceptance:
- `npm.cmd run check:v35-qa-provider-ui` passes.

### 24. v3.5 Integration Regression Tests

Goal: verify v3.5 does not break v2.1-v3.4 capabilities or safety boundaries.

Frontend changes:
- none directly.

Backend changes:
- focused pytest coverage for provider test/discovery/sync, debug export,
  diagnostics redaction, quality aggregation, and migration dry-run if changed.

Tests:
- `/game/start`, `/game/input`, `/game/state`, save/load, timeline, debug,
  playtest, quality, provider profile, provider test-connection, model
  discovery/sync, and routing assignment flows still work;
- active `GameState` remains unchanged by debug/replay/provider UI;
- no real provider calls in CI;
- `python -m pytest` and frontend build pass.

Acceptance:
- v3.5 integration regression suite passes with fake providers and local temp
  data only.

## Impact

### World Studio

World Studio gains clearer replay, EventLog, StateDelta, visible-state compare,
save migration, quality, playtest, performance, and debug export workflows. It
does not gain any direct GameState mutation path. Normal World UI remains
`visible_state`-based.

### Novel Studio

Novel Studio benefits from Provider mode assignment, Provider usage summaries,
Quality Gate aggregation, Cross-Mode conflict review, and diagnostics. Novel
drafting remains local draft/authoring mode and does not modify World state.

### Tavern Studio

Tavern Studio benefits from Provider connection status, model assignment for
Tavern replies, RP/hidden leak quality review, and diagnostics. Tavern remains
RP session / memory / proposal mode and does not directly modify World
`GameState`.

### Authoring / Mod Studio

Authoring / Mod Studio benefits from unified quality/debug reports, module
stress review, diagnostics, local test run summaries, and safe debug export.
Authoring drafts remain candidates/proposals until validation, dry-run, and
explicit confirm.

### Provider Gateway

v3.5 adds local provider connection testing, model discovery/sync, model
assignment, and provider diagnostics around Provider Gateway. It does not add
a second model entry point. Provider profiles continue to store only
`api_key_env` / `secret_ref`; `transient_api_key` is one-request-only and never
persisted.

### Quality Gate / Debug / Replay

Quality Gate, Debug, and Replay become first-class local workbench surfaces.
Debug raw details are explicitly gated. Quality reports remain deterministic
and safe-summary based. Replay and debug views are read-only.

### Privacy / Security / Visibility

v3.5 must strengthen, not weaken, privacy boundaries:

- no API key in frontend, project files, logs, diagnostics, backups, exports,
  provider profiles, prompt profiles, package manifests, usage records, or
  call traces;
- no hidden facts, NPC secrets, debug memory, mature/private content, raw env,
  raw prompts, raw provider responses, or raw `state_deltas` in normal UI;
- debug raw data requires `ENABLE_DEBUG_API` and explicit debug UI;
- fake providers/fake clients are mandatory for CI and automated tests.

## v3.6 Candidate Direction

Recommended v3.6 theme: **Local Performance & Accessibility Polish**.

Candidate v3.6 priorities:

- frontend code splitting and bundle-size reduction;
- Provider model list performance and caching UX;
- Provider capability matrix performance and accessibility;
- large report virtualization for Timeline, EventLog, Quality, and Playtest;
- keyboard navigation and focus management across all Studio modes;
- contrast, screen-reader labels, reduced-motion behavior, and responsive
  layout polish;
- safe error UX consistency across Novel, Tavern, World, Authoring, QA, Debug,
  and Provider screens;
- non-blocking observability polish without weakening local-first boundaries.
