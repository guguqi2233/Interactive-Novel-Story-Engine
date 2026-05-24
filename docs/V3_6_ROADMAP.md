# v3.6 Roadmap: Local Performance & Accessibility Polish

## Version Goal

v3.6 focuses on making the local product feel faster, calmer, and easier to
use across large local projects. It is a polish release, not a feature
expansion release.

The main goals are:

- reduce frontend bundle and chunk pressure;
- split route-scale UI code where it lowers load cost and maintenance risk;
- improve long-list rendering for EventLog, Timeline Replay, StateDelta,
  Quality, Hidden Leak, Provider model, Module Browser, Compatibility Matrix,
  Tavern message, Novel chapter/scene, and Authoring package views;
- improve Provider status refresh, model list caching, and capability matrix
  responsiveness;
- improve search/filter performance without changing results or visibility;
- add keyboard shortcut foundations, focus management, accessible labels,
  reduced-motion support, visual comfort, and clearer error boundaries;
- improve progress UI for backup, restore, diagnostics, slow Provider checks,
  and long-running local quality operations.

v3.6 must preserve the v0.1-v3.5 architecture: World Engine remains the
authority, `StateDelta` and `EventLog` remain the world-change boundary,
`visible_state` remains the safe normal UI source, Debug / Replay remain
read-only, and Provider Gateway remains the only model entry point.

## Non-Goals

v3.6 explicitly does not implement:

- account system;
- cloud sync;
- online marketplace;
- remote package auto-download;
- new large gameplay modules;
- full new editor rewrites;
- arbitrary code plugins;
- real provider calls in automated tests or CI;
- changes to World Engine rules;
- changes to Provider Gateway semantics;
- changes to `StateDelta`, `EventLog`, or visibility boundaries;
- normal UI rendering of hidden facts, NPC secrets, debug memory, raw prompts,
  raw provider responses, raw env, API keys, provider secrets, or raw
  `state_deltas`;
- performance caches that store API keys, `transient_api_key`, raw prompts,
  raw outputs, hidden/debug content, or mature/private content;
- turning optimization work into a new feature-completion phase.

## Hard Constraints

- Local-first behavior is mandatory.
- Optimization must not change business semantics.
- UI code must not directly modify `GameState`.
- Debug / Replay surfaces may observe, compare, filter, and export safe or
  confirmed debug data only; they must not mutate runtime state.
- `visible_state` remains the safe source for normal World UI.
- API keys must not enter frontend code, caches, logs, diagnostics, backups,
  exports, docs examples, fixtures, or ProviderProfile data.
- Provider model caches may store only safe model metadata and status.
- Large-list optimization must not bypass debug gating.
- All performance strategies must have safe degraded states.
- `python -m pytest` must pass.
- `cd frontend && npm.cmd run build` must pass.
- Existing frontend check scripts must pass, including v2.9-v3.5 checks, when
  the touched area is in scope.

## Recommended Development Order

1. Performance / Accessibility Contract Review.
2. Frontend Bundle / Chunk Review.
3. Route-Level Code Splitting.
4. Shared list/performance utilities.
5. Large EventLog Virtualized Rendering.
6. Timeline Replay Virtualized Rendering.
7. Long StateDelta / Debug List Optimization.
8. Large Quality and Hidden Leak Report Optimization.
9. Provider Model List Virtualization and status cache.
10. Capability Matrix Performance Polish.
11. Cross-studio Search / Filter Performance Polish.
12. Novel, Tavern, World, and Authoring large-data rendering polish.
13. Backup / Restore / Diagnostics Progress UI.
14. Slow Provider Warning UI.
15. Local Performance Dashboard Polish.
16. Keyboard Shortcuts Foundation.
17. Focus Management.
18. Accessibility Labels / Semantics.
19. Reduced Motion / Visual Comfort.
20. Contrast / Font Size / Spacing Polish.
21. Error Boundary Polish.
22. Loading Skeleton / Progressive Rendering Polish.
23. Safe Refresh / API Cache Strategy.
24. v3.6 UI Regression Tests.
25. v3.6 Integration Regression Tests.

The recommended first implementation phase is contract review plus bundle and
large-list proof-of-pattern work. That gives later modules a shared safe
performance pattern instead of one-off optimizations.

## Module Plan

### 1. Performance / Accessibility Contract Review

Goal: audit current performance and accessibility risks before changing code.

Frontend changes:
- document bundle size, high-density files, large list views, filtering hot
  paths, current ARIA coverage, focus behavior, reduced-motion gaps, and error
  boundaries;
- identify components that are safe to split without changing data flow.

Backend changes:
- none by default.

Tests:
- no code test required unless a blocker is found and fixed.

Acceptance:
- `docs/V3_6_PERFORMANCE_ACCESSIBILITY_CONTRACT_REVIEW.md` exists;
- review clearly marks performance-only work versus behavior-changing work;
- no privacy, visibility, Provider, or debug boundary regression is proposed.

### 2. Frontend Bundle / Chunk Review

Goal: understand and reduce the production bundle warning without hiding it by
raising limits.

Frontend changes:
- inspect `frontend/src/App.tsx`, `frontend/src/api.ts`, shared UI modules, and
  Vite output;
- identify route-sized extraction candidates;
- document chunk budget targets for v3.6.

Backend changes:
- none.

Tests:
- `cd frontend && npm.cmd run build`;
- compare chunk output before and after changes.

Acceptance:
- main chunk risk is measured;
- recommended split points are documented;
- no large UI dependency is introduced solely to satisfy chunk size.

### 3. Route-Level Code Splitting

Goal: split high-density studios and dashboards into route-scale modules where
that lowers initial load cost.

Frontend changes:
- move large Novel, Tavern, World, Authoring/Mod, QA/Debug, Provider, Desktop,
  and shared panel groups out of monolithic `App.tsx` where practical;
- use React lazy/dynamic import only for safe route or panel boundaries;
- keep loading, empty, error, and disabled states visible.

Backend changes:
- none.

Tests:
- frontend build;
- v2.9-v3.5 frontend check scripts for touched studios;
- smoke import checks for split modules.

Acceptance:
- initial chunk size is reduced or split into meaningful chunks;
- lazy-load fallback states are understandable;
- no UI route loses local-first or visibility boundary copy.

### 4. Large EventLog Virtualized Rendering

Goal: make large EventLog inspection responsive.

Frontend changes:
- add a safe virtualized or paged list pattern for EventLog rows;
- keep normal rows limited to event id, turn/time, type, actor safe summary,
  visible safe summary, tags, and linked StateDelta count;
- keep raw details inside DebugGate.

Backend changes:
- optional safe pagination parameters if current endpoints load too much data.

Tests:
- EventLog viewer smoke tests;
- normal view must not render raw event JSON or raw StateDelta payloads;
- debug disabled state must remain clear.

Acceptance:
- large EventLog samples remain scrollable;
- filters do not freeze the UI on representative large data;
- normal UI still shows safe summaries only.

### 5. Timeline Replay Virtualized Rendering

Goal: improve large replay browsing without changing replay semantics.

Frontend changes:
- virtualize or page turn groups and event rows;
- preserve replay controls: start, previous, next, jump to turn, pause;
- add safe reduced-motion behavior for replay playback.

Backend changes:
- optional safe replay summary pagination if needed.

Tests:
- replay UI smoke tests;
- hidden/debug events stay out of normal replay;
- raw StateDelta details remain debug-gated.

Acceptance:
- large replay views remain responsive;
- replay is still read-only and never writes `GameState` or `EventLog`.

### 6. Long StateDelta / Debug List Optimization

Goal: make debug-only StateDelta and debug list views usable for long sessions.

Frontend changes:
- keep StateDelta Viewer fully DebugGate protected;
- use paged/virtualized rows for long StateDelta lists;
- optimize path search and prefix filtering.

Backend changes:
- optional debug-only safe summary endpoint or paged delta endpoint, gated by
  `ENABLE_DEBUG_API`, if frontend-only filtering is insufficient.

Tests:
- debug disabled blocks StateDelta details;
- redacted value summaries remain redacted;
- no viewer can apply deltas.

Acceptance:
- long delta lists do not lock the UI;
- raw values and hidden text are not exposed outside debug-gated contexts.

### 7. Large Quality Report Optimization

Goal: make large quality reports easier to scan.

Frontend changes:
- add grouped counts, severity tabs, search, and incremental rendering for
  large report rows;
- preserve safe summaries and suggested actions.

Backend changes:
- optional report summary counts if needed.

Tests:
- quality dashboard tests;
- hidden text must not appear in normal report rows.

Acceptance:
- large reports are navigable by category and severity;
- blockers remain easy to locate.

### 8. Large Hidden Leak Report Optimization

Goal: scale hidden leak report UI without printing sensitive details.

Frontend changes:
- virtualize or page leak issue rows;
- keep safe summary, source, target, severity, and suggested action;
- add category counts and quick filters.

Backend changes:
- optional safe aggregate counts if needed.

Tests:
- hidden leak report tests;
- hidden text, NPC secrets, mature/private content, and API keys are redacted.

Acceptance:
- large leak reports remain responsive;
- all rows remain safe-summary only.

### 9. Provider Model List Virtualization

Goal: keep Provider Connectivity usable with large local model lists.

Frontend changes:
- virtualize or page provider/model rows;
- add provider, capability, enabled, use-case, and status filters;
- avoid rendering all model details at once.

Backend changes:
- optional safe model list pagination if current metadata payloads grow too
  large.

Tests:
- Provider UI tests;
- no API keys, Authorization headers, raw env, or `transient_api_key` rendered.

Acceptance:
- large local model lists remain responsive;
- model cache displays metadata only.

### 10. Provider Connection Status Cache

Goal: prevent repeated unnecessary local status refreshes.

Frontend changes:
- cache provider connection status and last-tested metadata in memory or safe
  local project metadata as appropriate;
- add refresh cooldown or explicit refresh controls;
- show stale, refreshing, failed, and missing-secret states.

Backend changes:
- optional safe status timestamp or cache metadata endpoint.

Tests:
- cache must not contain API keys, `transient_api_key`, raw provider errors, or
  Authorization headers;
- stale status warning is understandable.

Acceptance:
- repeated navigation does not trigger needless refresh storms;
- explicit refresh remains available.

### 11. Capability Matrix Performance Polish

Goal: keep model and module compatibility matrices responsive.

Frontend changes:
- compute matrix rows from indexed data instead of repeated nested scans;
- add filters for provider, model, mode, risk, package type, and capability;
- avoid rendering full matrix details by default.

Backend changes:
- optional safe precomputed counts if needed.

Tests:
- matrix tests;
- no hidden facts, secrets, or provider raw responses in rows.

Acceptance:
- large capability matrices render and filter smoothly;
- warnings remain visible and actionable.

### 12. Search / Filter Performance Polish

Goal: improve search/filter behavior across large local projects.

Frontend changes:
- debounce expensive text searches;
- memoize normalized indexes for Novel, Tavern, World, Authoring, QA, and
  Provider views;
- keep filters deterministic and safe.

Backend changes:
- optional safe search endpoints only if local frontend search becomes too
  costly.

Tests:
- filters return expected rows;
- search indexes do not store hidden/debug/secrets in normal UI caches.

Acceptance:
- typing in filters remains responsive;
- search does not broaden visibility.

### 13. Large Manuscript / Chapter Editor Performance

Goal: make Novel Studio comfortable with large manuscripts.

Frontend changes:
- avoid rerendering all chapters/scenes when editing one chapter;
- add lightweight chapter/scene list rendering;
- preserve draft dirty state and recovery UX.

Backend changes:
- none by default.

Tests:
- Novel UI smoke checks;
- Novel UI still does not modify World `GameState`.

Acceptance:
- large chapter/scene sets remain navigable;
- World Bible and timeline references remain safe summaries.

### 14. Large Tavern Session / Message List Performance

Goal: improve Tavern session and message navigation.

Frontend changes:
- virtualize or page long message lists;
- keep per-character knowledge-safe summaries;
- keep mature/private content default hidden and filtered.

Backend changes:
- optional safe message pagination if needed.

Tests:
- Tavern UI checks;
- mature/private and NPC secrets stay out of normal prompts and exports.

Acceptance:
- long local RP sessions remain scrollable and searchable;
- no online RP or multiplayer affordance is introduced.

### 15. World Panel Rendering Optimization

Goal: reduce rerender cost in World Studio panels.

Frontend changes:
- memoize visible Map, NPC, Quest, Inventory, Timeline, Module, Save, Quality,
  and Provider panel props;
- split heavy panel groups where practical;
- preserve action submission through backend APIs only.

Backend changes:
- none by default.

Tests:
- v3.3 World UI checks;
- actions still route through `/game/input` or equivalent backend API.

Acceptance:
- World Studio feels responsive under larger visible states;
- UI still cannot directly mutate `GameState`.

### 16. Authoring / Mod Large Package UI Optimization

Goal: improve large local package navigation.

Frontend changes:
- page or virtualize package/module lists;
- optimize compatibility, permission, quality, validation, and audit rows;
- keep Safe Apply validation/dry-run/confirm visible.

Backend changes:
- optional safe summary pagination for large package sets.

Tests:
- v3.4 Authoring UI checks;
- Mod UI still does not execute packages or arbitrary code.

Acceptance:
- large package sets remain manageable;
- no online marketplace or remote download wording is introduced.

### 17. Backup / Restore / Diagnostics Progress UI

Goal: make long local operations understandable.

Frontend changes:
- add progress summaries for backup, restore, diagnostics, dry-run, and export;
- show included/excluded sections and current stage;
- keep explicit confirm for writes and raw debug exports.

Backend changes:
- optional safe progress/status endpoints if existing operations cannot expose
  stage summaries.

Tests:
- backup/restore/diagnostics tests;
- secrets, logs/cache, databases, debug-only data, and mature/private content
  remain excluded by default.

Acceptance:
- long operations have clear status and cancel/disabled affordances where safe;
- no upload or cloud backup behavior appears.

### 18. Slow Provider Warning UI

Goal: clarify slow or failing local Provider checks.

Frontend changes:
- show slow, timeout, missing-secret, auth-failed, model-list-failed, and stale
  statuses with safe next steps;
- show that tests use fake/local providers in CI.

Backend changes:
- optional latency/status fields if missing.

Tests:
- Provider connectivity tests;
- raw provider errors remain redacted.

Acceptance:
- slow Provider states are understandable;
- no UI stores or displays real API keys.

### 19. Local Performance Dashboard Polish

Goal: make local performance metrics more actionable.

Frontend changes:
- group backend API duration, save/load duration, EventLog size, replay
  duration, provider call duration, quality duration, playtest duration, and
  build/chunk warnings;
- add time range filters and safe metric summaries.

Backend changes:
- optional safe aggregate metrics if needed.

Tests:
- performance dashboard tests;
- prompt/output text and hidden facts stay excluded.

Acceptance:
- metrics guide optimization work without becoming telemetry upload.

### 20. Keyboard Shortcuts Foundation

Goal: add a safe, discoverable shortcut layer for local workflows.

Frontend changes:
- define scoped shortcuts for navigation, search focus, close panel, run safe
  refresh, and replay controls;
- avoid destructive shortcuts or require confirm for dangerous actions;
- add a local shortcuts reference.

Backend changes:
- none.

Tests:
- shortcut smoke tests for scoped behavior;
- shortcuts must not bypass validation, confirm, or DebugGate.

Acceptance:
- keyboard users can navigate core views more efficiently;
- dangerous operations remain protected.

### 21. Focus Management

Goal: make dialogs, wizards, side panels, debug gates, Safe Apply, backup,
restore, Provider setup, and export flows easier to use.

Frontend changes:
- set initial focus on modal/wizard entry;
- restore focus on close;
- keep focus within active modal-like flows where appropriate;
- make disabled reasons reachable.

Backend changes:
- none.

Tests:
- focused frontend smoke checks where practical.

Acceptance:
- keyboard navigation is predictable;
- focus changes do not hide safety warnings or confirmations.

### 22. Accessibility Labels / Semantics

Goal: improve screen-reader and keyboard clarity.

Frontend changes:
- add accessible names for icon-like buttons, status badges, graph previews,
  replay controls, filter toolbars, and provider status chips;
- use semantic headings and landmarks consistently.

Backend changes:
- none.

Tests:
- frontend static check script for required labels in v3.6 surfaces.

Acceptance:
- core actions have understandable accessible names;
- status-only UI has readable text equivalents.

### 23. Reduced Motion / Visual Comfort

Goal: respect motion preferences and reduce visual strain.

Frontend changes:
- add `prefers-reduced-motion` CSS handling;
- pause or simplify replay/animated affordances when reduced motion is set;
- avoid flashing progress or aggressive transitions.

Backend changes:
- none.

Tests:
- CSS/static check for reduced-motion rules.

Acceptance:
- reduced-motion users can use replay and dashboards comfortably.

### 24. Contrast / Font Size / Spacing Polish

Goal: improve readability without changing information architecture.

Frontend changes:
- review contrast for muted text, badges, danger/warning states, and dense
  panels;
- tune compact list spacing and table-like rows;
- avoid viewport-based font scaling.

Backend changes:
- none.

Tests:
- build and visual/manual checks.

Acceptance:
- dense panels remain readable on desktop and mobile widths;
- no text overlaps or truncates critical safety labels.

### 25. Error Boundary Polish

Goal: prevent a single large report or panel from breaking the whole app.

Frontend changes:
- add local ErrorBoundary components around high-risk panels;
- show redacted, safe recovery options;
- avoid exposing sensitive paths, raw env, secrets, raw prompts, or raw debug
  payloads in errors.

Backend changes:
- none by default.

Tests:
- smoke tests for safe error rendering;
- redaction checks for error strings.

Acceptance:
- panel failures degrade safely;
- users get next steps without sensitive detail leakage.

### 26. Loading Skeleton / Progressive Rendering Polish

Goal: make slow local operations feel stable.

Frontend changes:
- add lightweight skeleton or staged loading states for large dashboards;
- progressively render counts before full rows where useful;
- preserve empty/error/disabled states.

Backend changes:
- optional safe summary endpoints if needed.

Tests:
- frontend build and smoke checks.

Acceptance:
- large screens communicate progress without pretending work is complete.

### 27. Safe Refresh / API Cache Strategy

Goal: reduce duplicate local API calls while preserving freshness and safety.

Frontend changes:
- introduce safe cache keys for non-secret summaries;
- add explicit refresh and stale indicators;
- never cache raw debug payloads outside DebugGate state or Provider secrets in
  frontend storage.

Backend changes:
- optional cache-control metadata for safe summary endpoints.

Tests:
- cache behavior tests for Provider summaries, QA summaries, and report rows;
- verify no cache stores API keys, `transient_api_key`, raw prompt/output,
  hidden/debug data, or mature/private content.

Acceptance:
- navigation and refresh feel faster;
- privacy and visibility boundaries remain unchanged.

### 28. v3.6 UI Regression Tests

Goal: keep polish from breaking existing UI.

Frontend changes:
- add or extend static/smoke checks for code-split imports, virtualization
  wrappers, accessibility labels, reduced motion, ErrorBoundary, no online
  entries, no secret rendering, and debug gating.

Backend changes:
- none unless adding safe summary endpoints.

Tests:
- `cd frontend && npm.cmd run build`;
- existing v2.9-v3.5 frontend check scripts;
- new v3.6 frontend check script.

Acceptance:
- UI checks pass;
- split modules compile;
- normal UI safety boundaries remain enforced.

### 29. v3.6 Integration Regression Tests

Goal: ensure performance/accessibility polish does not regress v0.1-v3.5
capabilities.

Frontend changes:
- no direct changes beyond test fixtures/checks.

Backend changes:
- add focused tests only for new safe summary/cache/progress endpoints.

Tests:
- `python -m pytest`;
- frontend build;
- relevant quality/release checklists when touched;
- provider tests must use fake/mock/local clients only.

Acceptance:
- v0.1-v3.5 boundary tests continue to pass;
- optimization does not alter game, provider, mod, authoring, debug, or
  visibility semantics.

## Studio Impact

### Novel Studio

v3.6 should improve large manuscript, outline, chapter, scene, search, and
quality views. It must not change Novel draft semantics, World Bible reference
boundaries, export filtering, or World -> Novel import safety.

### Tavern Studio

v3.6 should improve long session/message rendering, character library filters,
RP memory scanning, and accessibility. Mature/private content remains disabled
or hidden by default, and Tavern UI must not modify World `GameState`.

### World Studio

v3.6 should improve map/NPC/quest/inventory/module/timeline rendering and
action-input responsiveness. World actions still go through backend APIs and
the World Engine remains the fact source.

### Authoring / Mod Studio

v3.6 should improve large package lists, validation rows, diff previews,
compatibility matrices, permission dashboards, and Safe Apply UX. Authoring
drafts remain draft/candidate/proposal data until validation, dry-run, and
explicit confirm.

### QA / Debug / Replay

v3.6 should make EventLog, Timeline Replay, StateDelta, Hidden Leak, Quality,
Playtest, diagnostics, debug export, and local test run panels scale to larger
local projects. Debug raw data remains debug-gated and read-only.

### Provider Connectivity

v3.6 should improve large model list rendering, provider status cache,
capability matrix responsiveness, slow Provider warnings, and safe diagnostics.
Provider Connection & Model Discovery remains local configuration, not an API
resale service or online platform.

## Privacy / Security / Visibility Impact

v3.6 optimization must preserve every existing privacy and visibility boundary:

- no API key, provider secret, Authorization header, raw env, or
  `transient_api_key` in frontend caches, logs, diagnostics, backups, exports,
  fixtures, docs, or ProviderProfile data;
- no hidden facts, NPC secrets, npc_knowledge, mature/private content, debug
  memory, raw prompts, raw outputs, raw `GameState`, or raw `state_deltas` in
  normal UI;
- raw StateDelta/EventLog/debug payloads remain behind DebugGate and
  `ENABLE_DEBUG_API`;
- performance caches store only safe summaries, counts, metadata, status, and
  redacted messages;
- virtualization, pagination, and lazy loading must not accidentally expand
  what a view can see.

## Preparation for v3.7 Local Complete Product

v3.6 prepares v3.7 by making the full local product reliable at realistic
project sizes. The desired v3.7 readiness outcomes are:

- production build has manageable chunks or an accepted documented split plan;
- large local datasets are navigable without UI freezes;
- Provider model discovery and assignment remain responsive with many models;
- QA/Debug/Replay views scale to long campaigns;
- Novel, Tavern, World, Authoring/Mod, Provider, Desktop, and QA surfaces have
  consistent keyboard and focus behavior;
- reduced motion, labels, contrast, font sizing, spacing, and error recovery
  are good enough for final product acceptance;
- local-first, no onlineization, no arbitrary code plugin, and no secret
  leakage boundaries are easier to verify before v3.7.

## Verification Commands

Required during v3.6 implementation:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v29-ui
npm.cmd run check:v30-ux
npm.cmd run check:v31-novel-ui
npm.cmd run check:v32-tavern-ui
npm.cmd run check:v33-world-ui
npm.cmd run check:v34-authoring-ui
npm.cmd run check:v35-qa-debug-provider-ui
```

Add `check:v36-performance-accessibility` once the v3.6 frontend regression
script exists.

Provider connectivity, model discovery, and model assignment tests must use
fake/mock/local clients only. CI must not call real providers.

## Final Recommendation

Start v3.6 with Performance / Accessibility Contract Review and Frontend
Bundle / Chunk Review. Then land one shared large-list pattern and one route
splitting pattern before applying them across EventLog, Timeline Replay,
StateDelta, Provider model lists, Quality reports, Hidden Leak reports, and
large studio panels.
