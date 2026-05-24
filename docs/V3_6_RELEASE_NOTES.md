# v3.6 Release Notes: Local Performance & Accessibility Polish

## 1. Version Name

v3.6 **Local Performance & Accessibility Polish**

## 2. Version Goal

v3.6 makes the local AI Narrative Studio faster, calmer, and easier to use
across larger local projects. It is an optimization and accessibility release
over the existing v0.1-v3.5 product surface, not a new large feature release.

v3.6 explicitly does not add:

- account system;
- cloud sync;
- online marketplace;
- remote package auto-download;
- online platform;
- arbitrary-code plugin runtime;
- real-provider CI checks;
- new World Engine rules;
- new Provider Gateway semantics.

World Engine remains the authority, `StateDelta` and `EventLog` remain the
state-change boundary, `visible_state` remains the normal UI safety source, and
Provider Gateway remains the only model entry point.

## 3. Performance Optimizations

- Added v3.6 performance/accessibility contract review and regression audits.
- Reduced main App chunk pressure through route-level splitting and Vite manual
  chunks.
- Added long-list windowing / pagination patterns for EventLog, Timeline
  Replay, StateDelta, Quality reports, Hidden Leak reports, Provider model
  lists, Module Browser, Compatibility Matrix, Novel, Tavern, World, and
  Authoring / Mod surfaces.
- Added debounced search and memoized safe search indexes for large local
  lists.
- Added local performance dashboard polish for large-list warnings, provider
  latency, quality/playtest/save/diagnostics durations, event counts, model
  counts, filters, and optimization hints.
- Added backup/restore/diagnostics progress affordances for long-running local
  operations.
- Added slow Provider warning UI for high latency, repeated timeout, slow model
  list reads, and high error rates.

These optimizations do not change business results, validation criteria, replay
semantics, provider routing decisions, quality-gate pass/fail results, or World
Engine authority.

## 4. Accessibility Optimizations

- Added keyboard shortcut foundation and shortcut help.
- Added focus helpers for shortcut help, dialogs, wizard step titles, and safe
  error states.
- Improved main navigation labels, icon-button labels, form labels, badge text,
  filter group semantics, and report-list readability.
- Added reduced-motion preference support and `prefers-reduced-motion`
  handling.
- Improved contrast, font sizing, spacing, badge sizing, report density, and
  warning/error copy readability.
- Kept dangerous operations out of direct shortcuts. Apply, import, delete,
  restore, migration apply, debug export, backup creation, and diagnostics
  creation still require visible UI flows and confirmation gates.

## 5. Frontend Chunk / Route Splitting Changes

- Added route/panel lazy loading with `React.lazy`, `Suspense`,
  `RouteLoadingBoundary`, and route-scoped `AppErrorBoundary`.
- Added safe loading fallback and safe route error fallback.
- Added Vite manual chunks for:
  - React vendor code;
  - frontend API helpers;
  - Novel Studio UI;
  - Tavern Studio UI;
  - World Studio UI;
  - Provider UI;
  - Desktop UI.
- Current accepted build emits no Vite `>500 kB` chunk warning.

Accepted build snapshot:

| Chunk | Size | Gzip |
| --- | ---: | ---: |
| `assets/App-BTGD3Pu2.js` | 445.82 kB | 107.20 kB |
| `assets/vendor-react-BnfF7MAh.js` | 192.48 kB | 60.34 kB |
| `assets/studio-provider-ui-D7VMkStf.js` | 52.25 kB | 14.31 kB |
| `assets/studio-api-C65PFhUQ.js` | 45.78 kB | 6.83 kB |
| `assets/studio-world-ui-BXFMSfsx.js` | 30.43 kB | 8.00 kB |
| `assets/studio-tavern-ui-Cts18pZZ.js` | 29.39 kB | 7.91 kB |
| `assets/studio-novel-ui-DJ_zR5gm.js` | 22.37 kB | 6.64 kB |
| `assets/studio-desktop-ui-B9UH0Ktb.js` | 11.23 kB | 3.32 kB |

## 6. Large List / Large Report Optimizations

- EventLog Viewer uses windowed rows, filters, safe summaries, and linked
  StateDelta counts. Raw EventLog JSON and raw StateDelta payloads remain
  debug-gated.
- Timeline Replay uses turn windows, event filters, jump controls, active event
  state, safe summaries, and debug-gated raw details. Replay remains read-only.
- StateDelta Viewer remains DebugGate-only and uses filtered/windowed rows with
  redacted value summaries.
- Unified Quality Gate report browsing uses category grouping, severity/source
  filters, search, collapsed categories, and visible issue windows.
- Hidden Leak reports use target grouping, severity/source-target filters, safe
  metadata search, and visible issue windows without rendering hidden text
  bodies.
- Module Browser, Compatibility Matrix, and Authoring / Mod package views use
  grouping, filters, pagination/windowing, and safe preview rows.
- Novel, Tavern, and World panels use targeted limits, filters, memoized
  derived values, and large-list friendly presentation.

## 7. Provider Model List / Status Cache Optimizations

- Provider model lists support search, capability filters, enabled/disabled
  filters, recommended-use-case filters, memoized capability badges, and
  windowed rendering.
- Provider status cache stores only safe local status metadata:
  provider profile id, status, tested time, latency, safe error type, model
  count, and redaction flag.
- Provider status cache supports TTL/stale state and manual refresh.
- Provider model list and status cache do not store API keys,
  `transient_api_key`, Authorization headers, raw env, raw provider responses,
  raw provider errors, raw prompts, or raw outputs.
- Capability Matrix performance polish keeps provider/model warnings visible
  while using safe summaries and filtered/grouped rows.

## 8. Search / Filter Optimizations

- Added shared debounced input and safe search helpers.
- Added memoized safe search indexes for large local list surfaces.
- Normal search/filter paths are expected to use safe metadata only.
- Hidden facts, NPC secrets, raw prompts, raw outputs, raw StateDelta values,
  mature/private bodies, and provider secrets must not be indexed in normal
  UI search.

## 9. Keyboard Shortcuts / Focus / Reduced Motion Changes

- Added keyboard shortcut help and local shortcut preference.
- Added navigation shortcuts for major local workspaces.
- `Ctrl/Cmd+S` remains safe/reserved and does not bypass confirm-gated flows.
- `Esc` closes supported local modal/drawer/help surfaces.
- Added focus helpers for route errors, shortcut help, dialog-like panels, and
  wizard step titles.
- Added reduced-motion preference state and CSS support for
  `prefers-reduced-motion`.

## 10. ErrorBoundary / Loading Skeleton Changes

- Added `AppErrorBoundary` with safe error summaries, retry, go-home recovery,
  focus behavior, and local diagnostics guidance.
- Normal ErrorBoundary output redacts stack traces, API keys, Authorization
  headers, raw env, sensitive local paths, hidden facts, NPC secrets, raw
  prompts, raw StateDelta markers, debug memory, and private notes.
- Added loading skeleton and progressive rendering helpers for major large
  dashboards and list surfaces.
- Skeleton rows use static safe text and do not contain project data, hidden
  facts, debug payloads, provider data, or secrets.

## 11. Privacy / Cache / Secret Safety Changes

- Frontend safe API cache is in-memory only.
- Safe API cache rejects payloads containing API keys, `transient_api_key`,
  Authorization headers, provider secrets, raw env, raw provider responses,
  raw provider errors, raw prompts, raw outputs, hidden facts, NPC secrets,
  raw StateDelta payloads, raw GameState, debug memory, or mature/private
  markers.
- Provider connection status cache uses a backend allowlisted schema and does
  not cache `safe_message`, raw provider error bodies, Authorization headers,
  API keys, transient keys, raw env, or raw provider responses.
- Timeline Replay normal errors are redacted before display.
- Debug and raw StateDelta details remain behind DebugGate /
  `ENABLE_DEBUG_API`.
- v3.6 does not introduce telemetry upload, cloud cache, service worker cache,
  account flows, cloud sync, online marketplace, or remote package download.

## 12. Known Limitations

- `App.tsx` remains large even though the main chunk is now below the Vite
  warning threshold.
- Some legacy detailed Desktop/Provider components still remain in `App.tsx`
  while active lazy modules provide summary-first route implementations.
  Current checks pass, but v3.7 should do a route parity and dead-code cleanup
  pass.
- v3.6 frontend checks are mostly static/source-level checks, not full browser
  performance benchmarks with thousands of rendered rows.
- Provider-supplied model ids and display names remain user-visible metadata;
  v3.7 can add stricter truncation/normalization if needed.
- Safe API cache is an in-memory session helper, not a persistent offline cache.
- Accessibility checks cover broad semantics, labels, reduced motion, focus
  helpers, and visual comfort, but not full screen-reader certification.

## 13. Upgrade Notes from v3.5

- No database migration is required solely for v3.6 UI polish.
- Re-run frontend install only if local dependencies are stale; no large UI
  dependency was added.
- Run the standard verification commands after upgrading:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v36-performance-a11y
```

- Provider connection status may show stale/fresh local cache state. Manual
  refresh remains explicit and does not perform background provider polling.
- Existing Provider profiles still store only `api_key_env` / `secret_ref`.
  Do not move API keys into projects, frontend state, exports, backups, logs,
  diagnostics, fixtures, or docs.
- Debug / Replay views remain observational. They do not gain permission to
  apply StateDelta, rewrite EventLog, or modify GameState.
- Existing v2.9-v3.5 frontend checks remain part of the release verification
  chain and should continue to pass.

## 14. Recommended v3.7 Direction

v3.7 should be **Local Complete Product**.

Recommended v3.7 priorities:

- complete route parity review for active lazy-loaded Desktop, Provider,
  Settings, Novel, Tavern, World, Authoring, and QA surfaces;
- remove or extract remaining legacy duplicate UI from `App.tsx`;
- add browser-level smoke checks for lazy routes, debug-disabled routes,
  large EventLog/Timeline/StateDelta windows, Provider model lists, and
  Quality / Hidden Leak reports;
- add large local fixture projects for performance validation;
- improve Provider model display normalization and truncation;
- expand keyboard-only and screen-reader manual QA;
- keep local-first privacy and safety boundaries intact;
- avoid accounts, cloud sync, online marketplace, remote package downloads,
  arbitrary-code plugins, and online platform claims.

