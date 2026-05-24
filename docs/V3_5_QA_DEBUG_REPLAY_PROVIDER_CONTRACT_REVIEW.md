# v3.5 Local QA / Debug / Replay / Provider Contract Review

## Review Scope

This review covers the current local QA, Debug, Replay, Quality, Diagnostics,
and Provider Connectivity surfaces before v3.5 implementation work. It is based
on the current frontend, backend API, tests, and docs after v3.4.

Reviewed areas:

- Timeline Replay, EventLog, StateDelta, Debug API, DebugGate, and replay
  dry-run surfaces.
- Quality Gate, Playtest Dashboard, hidden leak evals, CrossMode conflict
  review, module playtests, and module stress/quality reports.
- Provider Gateway, ProviderProfileV2, ModelProfile, ProviderSecretResolver,
  Provider profile APIs, Provider Setup UI, provider usage/cost dashboards,
  and current test-connection behavior.
- Diagnostics bundle preview/create, local logs, backup/restore, safe errors,
  and frontend redaction utilities.

## Current QA / Debug / Replay Routes

Current debug/replay routes are mostly under `/debug/...` and are gated through
`require_debug_api()` in `backend/app/main.py`.

Current debug/replay API families:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/events`
- `GET /debug/saves/{save_id}/timeline`
- `POST /debug/saves/{save_id}/replay-dry-run`
- `GET /debug/sessions/{session_id}/graphs/relationships`
- `GET /debug/sessions/{session_id}/graphs/factions`
- `GET /debug/modules`
- `GET /debug/modules/{module_id}`
- `POST /debug/modules/{module_id}/actions/{action_id}/dry-run`
- `GET /debug/sessions/{session_id}/npc-simulation`
- `GET /debug/sessions/{session_id}/npcs/{npc_id}/simulation`
- `GET /debug/sessions/{session_id}/npc-simulation/ticks`
- `POST /debug/sessions/{session_id}/npc-simulation/dry-run-tick`
- `GET /debug/sessions/{session_id}/npcs/{npc_id}/behavior-timeline`
- `GET /debug/saves/{save_id}/npcs/{npc_id}/behavior-timeline`
- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

Current frontend entry points are concentrated in `frontend/src/App.tsx` and
`frontend/src/worldUi.tsx`:

- `DebugGate`, `DebugDisabledState`, and `DebugWarningBanner` in
  `worldUi.tsx`.
- Debug side panel in `App.tsx`, including refresh state, refresh timeline,
  session/save replay, replay dry-run, graphs, NPC simulation, gameplay module
  debug, crash reports, and performance.
- `TimelineReplayPanel` and EventLog timeline details in `App.tsx`.
- World normal panel entry `WorldTimelineEventLogPanel` in `worldUi.tsx`.

## Current EventLog / StateDelta / Timeline UI

Current behavior:

- Normal World UI presents safe EventLog / timeline summaries and copy stating
  that hidden events are excluded and raw `state_deltas` require DebugGate.
- Raw `event.state_deltas` JSON is rendered in the debug side panel only after
  `DebugGate debugEnabled={studioStatus?.debug_api_enabled ?? false}`.
- `TimelineReplayResponse` contains grouped timeline turns and replay summary.
  It may contain raw `state_deltas`, so it must stay debug-gated when showing
  raw details.
- `VisibleStateInspector` and normal World cards describe `visible_state` as
  the normal UI source and exclude raw `GameState`, NPC secrets, hidden facts,
  debug memory, and raw `state_deltas`.

Existing tests relevant to this boundary:

- Hidden leak eval verifies `state_deltas` do not enter player APIs and debug
  enabled responses may contain them.
- v3.3 regression tests verify normal `/game/state` output does not include
  `state_deltas`, Debug API can include them, and raw delta rendering in
  `worldUi.tsx` is not in the normal component area.

Contract finding:

- Current raw StateDelta rendering is debug-gated, but v3.5 should consolidate
  all raw delta display into a dedicated StateDelta Viewer component to reduce
  future regression risk.

## Current Quality / Playtest UI

Current backend:

- `/playtests/recent`, `/playtests/run`, `/playtests/{run_id}`,
  `/playtests/batch/run`, and `/playtests/batch/{run_id}` provide automated
  playtest reports.
- `quality_api_enabled()`, `playtest_api_enabled()`,
  `scenario_regression_api_enabled()`, and related require helpers gate local
  quality/playtest APIs.
- Hidden leak evals live under `backend/tests/evals/hidden_info_leaks`.
- Module playtests and advanced module quality exist under
  `backend/app/playtesting/module_playtest.py` and module quality tools.
- CrossMode conflicts are detected through `CrossModeConflictDetector`, with
  frontend API `detectCrossModeConflicts`.

Current frontend:

- `PlaytestingDashboard` in `App.tsx` shows recent, selected, and batch
  playtest reports and can run local playtests.
- `QualityDashboardUXPanel` in `App.tsx` shows overall quality status,
  playtest count, world health, and local next actions.
- `WorldQualityPlaytestPanel` in `worldUi.tsx` exposes World Quality /
  Playtest actions.
- Authoring/Mod UI includes Mod Quality Gate and module quality surfaces.
- Tavern and Novel have their own safe quality dashboards.

Contract finding:

- Current QA surfaces exist but are spread across World, Studio, Authoring,
  Tavern, Novel, and Prompt Lab screens. v3.5 should unify them into a single
  QA / Debug / Replay workspace while keeping per-mode entry points.

## Current Provider Connectivity UI

Current backend Provider routes:

- `GET /projects/{project_id}/providers`
- `POST /projects/{project_id}/providers`
- `GET /projects/{project_id}/providers/{provider_profile_id}`
- `PATCH /projects/{project_id}/providers/{provider_profile_id}`
- `DELETE /projects/{project_id}/providers/{provider_profile_id}`
- `POST /projects/{project_id}/providers/{provider_profile_id}/validate`
- `GET /projects/{project_id}/providers/{provider_profile_id}/status`
- `POST /projects/{project_id}/providers/{provider_profile_id}/test-connection`
- `GET /projects/{project_id}/providers/capability-matrix`
- `GET /projects/{project_id}/providers/usage/recent`
- `GET /projects/{project_id}/providers/usage/summary`
- `GET /projects/{project_id}/providers/usage/by-mode`
- `GET /projects/{project_id}/providers/usage/by-provider`

Current frontend:

- Prompt Lab / Provider Profiles panel can create provider profiles using
  provider type, model profiles, `api_key_env`, `secret_ref`, base URL metadata,
  allowed modes, and enablement status.
- Provider Setup Wizard is currently instructional and safe, but not yet a full
  connection/model-discovery workflow.
- Provider Usage Dashboard shows local estimates by recent usage, by mode, and
  by provider.
- Provider capability matrix can be loaded for existing profiles.

Current connection testing:

- `test-connection` exists but currently defaults to a dry-run response:
  `{"ok": true, "dry_run": true, ...}` with note "No real provider call was
  made."
- `allow_real_connection=true` currently returns 403 by design.

Current gaps:

- No dedicated model discovery endpoint was found with names such as
  `fetch-models`, `sync-models`, or model discovery/sync.
- No full Provider Connectivity Dashboard exists yet.
- No formal mode-assignment UI for Novel / Tavern / World / Cross-Mode /
  Quality has been centralized in v3.5 terms, although Provider routing and
  allowed modes already exist.

## Current Provider Secret Boundary

Current backend contracts:

- `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and
  `openai_api_key` fields.
- `ProviderSecretResolver` resolves `api_key_env` and `secret_ref` on the
  backend side.
- `FakeProviderSecretResolver` exists for tests.
- `ProviderProfileRepository` stores profile YAML under project provider
  profile directories and returns safe summaries.
- Provider Profile Packs are validated to allow `api_key_env` / `secret_ref`
  and reject raw keys.

Current frontend contracts:

- Provider Setup and Prompt Lab use `api_key_env` and `secret_ref` fields.
- No plaintext API key input field was found in the current Provider setup UI.
- Frontend API client redacts `sk-*`, Authorization headers, `api_key`,
  secret/token/password values, sensitive local paths, hidden facts, raw
  prompts, and state delta text in errors.

Current tests:

- Provider Gateway tests assert raw API key fields are rejected.
- Provider usage tests assert secret-like text and hidden fact text do not
  appear in usage payloads.
- v2.5, v2.6, v3.0, v3.3, and v3.4 tests cover provider-secret redaction in
  project profiles, exports, diagnostics, and frontend surfaces.

Contract finding:

- The existing provider secret boundary is solid for persisted profiles.
- v3.5 must add a stricter contract for `transient_api_key`: one request only,
  never stored, never logged, never exported, never included in frontend state
  beyond the submitted request lifecycle.

## Current Diagnostics / Logs Boundary

Current backend:

- Local log viewer and diagnostics bundle services are under the desktop/local
  studio services.
- Diagnostics preview/create APIs are local-only and redacted by default.
- Backup/restore uses dry-run first and explicit confirm for writes.
- Local log service rejects unsafe paths and redacts Authorization, database
  URLs, API keys, secret-like values, and sensitive paths.

Current frontend:

- Diagnostics Bundle UI previews local diagnostics and states default
  exclusions for `.env`, API keys, provider secrets, raw env, raw prompts,
  hidden facts, raw `state_deltas`, debug memory, mature/private content,
  databases, and full saves.
- Local Log Viewer states it shows redacted logs from allowed log directories.
- Backup / Restore UI uses dry-run and explicit confirm.

Current tests:

- v3.0 local studio service tests verify logs and diagnostics do not leak
  fake API keys or Authorization headers.
- Diagnostics preview does not write; create writes local redacted bundles.
- Backups exclude sensitive content by default.

Contract finding:

- Diagnostics/log boundaries already match v3.5 needs for baseline local QA.
- Provider connection/model discovery diagnostics must be added to the same
  redaction policy before real UI is introduced.

## Current Debug Gating

Backend:

- `debug_api_enabled()` reads `ENABLE_DEBUG_API`.
- `require_debug_api()` calls `sync_runtime_settings()` and raises 403 when
  debug is disabled.
- Debug routes for sessions, saves, graphs, modules, replay, NPC simulation,
  crash reports, and performance call `require_debug_api()`.
- Usage API can be enabled by `ENABLE_DEBUG_API` or `ENABLE_USAGE_TRACKING`.
- Quality/playtest APIs have their own gates and can also become available
  through debug/eval/playtest/performance flags depending on the surface.

Frontend:

- `DebugGate` displays `DebugDisabledState` when debug is disabled.
- Debug warning copy states debug data may include internal state, raw EventLog
  details, raw StateDelta, debug timeline, and module debug summaries.
- World normal components state raw `state_deltas` require DebugGate and
  `ENABLE_DEBUG_API`.

Contract finding:

- Gating exists, but v3.5 should make the distinction clearer by extracting a
  common QA/Debug shell and putting all raw EventLog/StateDelta/debug export
  renderers behind the same component boundary.

## Privacy / Visibility Risks

High-risk issues:

- No high-risk release blocker was found during this review.

Medium-risk issues:

1. **Raw StateDelta rendering is debug-gated but not centralized.**
   - Current raw JSON rendering is inside the debug panel's `DebugGate`, but
     v3.5 should move it into a dedicated `StateDeltaViewer` / `DebugRawPanel`
     to make static checks easier.

2. **Provider test-connection exists but is only a dry-run skeleton.**
   - This is safe, but v3.5 must avoid bolting real connection logic directly
     onto the current endpoint without a fake-client test harness, transient
     key lifecycle, and redacted diagnostics.

3. **Provider model discovery/sync is not implemented.**
   - This is a capability gap rather than a leak. v3.5 must add safe-only
     endpoints that store `ModelProfile` metadata only.

4. **QA surfaces are scattered across mode-specific screens.**
   - This makes it easier for future changes to accidentally mix normal and
     debug views. A shared QA/Debug workspace and shared components should
     reduce that risk.

Low-risk issues:

- Vite bundle-size warning remains a v3.6 performance polish item.
- Provider Usage Dashboard is local and safe but could use clearer disabled
  states when `ENABLE_USAGE_TRACKING=false`.
- CrossMode conflict review exists but should become easier to locate from the
  unified QA dashboard.

Specific checks:

- Raw `state_deltas` in normal UI: not found as an active normal-view render;
  current raw JSON render is in the DebugGate-wrapped debug panel.
- Hidden facts / NPC secrets in normal QA reports: existing tests cover
  redaction, and no current normal QA report path was found displaying full
  hidden text by design.
- API key into frontend/logs/diagnostics/backup/export: existing redaction and
  tests cover these paths. v3.5 must extend the same policy to provider
  connection/model discovery diagnostics.
- Real provider network tests: not found in CI defaults. Real provider/lab
  paths remain explicit opt-in, while `test-connection` currently rejects real
  connection by default.
- Online platform/account/cloud/marketplace/remote package entry: not found as
  implemented capability; current copy is negative/local-first.

## Recommended v3.5 UI Shape

Recommended v3.5 workspace:

- Left navigation:
  - Timeline Replay
  - EventLog
  - StateDelta
  - Visible vs Debug
  - Hidden Leaks
  - Playtests
  - Quality Gate
  - Performance
  - Providers
  - Provider Usage
  - CrossMode Conflicts
  - Module Stress
  - Save Migration
  - Diagnostics
  - Local Test Runs
  - Debug Export

- Main panel:
  - current selected QA/debug/provider surface;
  - loading, empty, error, and disabled states;
  - safe rows by default;
  - raw debug only inside `DebugGate`.

- Right sidebar:
  - current project/session/save/provider context;
  - redaction policy;
  - debug/API gate status;
  - latest blockers/warnings;
  - safe jump links.

- Footer:
  - local-only status;
  - debug API status;
  - usage tracking status;
  - provider gateway status;
  - no account / no cloud / no marketplace / no API resale.

Recommended Provider Connectivity implementation shape:

- Provider Connectivity Dashboard should list local provider profiles,
  configured/missing secret status, model count, last test status, last
  discovery status, local-only/relay-not-resale copy, and routing warnings.
- Provider Connection Test should use fake provider/fake client in tests. A
  `transient_api_key` may exist only for one request and must never be saved or
  logged.
- Provider Model Discovery / Sync should normalize provider model lists into
  safe `ModelProfile` records and discard raw provider responses.
- Provider Model Assignment by Mode should write Provider Gateway routing
  metadata only; it must not allow UI code to call providers directly.

Recommended static checks:

- raw `JSON.stringify(event.state_deltas` appears only inside DebugGate or the
  dedicated StateDelta debug component;
- no `<input name="api_key">` or plaintext API key field;
- Provider test/discovery code includes fake-client paths for automated tests;
- no account/cloud/online marketplace/API resale/remote package download
  primary entry;
- diagnostics/export text includes default secret and debug-data filtering.

## v3.5 Entry Recommendation

Proceed with v3.5 implementation. The existing architecture has enough
foundation for Timeline Replay, EventLog, DebugGate, Playtest, Quality, usage,
Provider profiles, diagnostics, and redaction. The first implementation step
should be a shared Local QA / Debug / Replay workspace and component cleanup,
followed by Provider Connectivity Dashboard and fake-client connection/model
discovery contracts.
