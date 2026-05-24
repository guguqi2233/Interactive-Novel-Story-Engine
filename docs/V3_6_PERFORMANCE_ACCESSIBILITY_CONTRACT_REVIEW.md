# v3.6 Performance / Accessibility Contract Review

## Review Scope

This review covers the current local UI and related safe-summary backend
surfaces before v3.6 implementation. It is based on:

- `docs/V3_6_ROADMAP.md`;
- `docs/V3_5_FULL_COMPLETENESS_REVIEW.md`;
- `docs/V3_6_OPTIMIZATION_READINESS_REPORT.md`;
- `frontend/package.json`;
- `frontend/src/App.tsx`;
- `frontend/src/api.ts`;
- `frontend/src/novelUi.tsx`;
- `frontend/src/tavernUi.tsx`;
- `frontend/src/worldUi.tsx`;
- `frontend/src/styles.css`;
- `frontend/scripts/check-*.mjs`;
- backend QA / Debug / Replay / Provider / Quality / Diagnostics code paths.

No business code was modified during this review.

## Current Bundle / Chunk Risk

Current frontend source size:

| File | Approx. size | Approx. lines | Risk |
| --- | ---: | ---: | --- |
| `frontend/src/App.tsx` | 969 KB | 23,313 | High |
| `frontend/src/api.ts` | 202 KB | 6,815 | Medium |
| `frontend/src/styles.css` | 39 KB | 2,429 | Medium |
| `frontend/src/worldUi.tsx` | 33 KB | 801 | Low to medium |
| `frontend/src/novelUi.tsx` | 25 KB | 568 | Low to medium |
| `frontend/src/tavernUi.tsx` | 24 KB | 434 | Low to medium |

The main production bundle is already known to exceed Vite's default 500 kB
warning threshold. The most recent v3.6 opening check recorded a successful
build with a main JS chunk around 828 kB minified / 206 kB gzip.

Primary risk:

- `App.tsx` contains route-level shell logic plus many large panels:
  Provider Setup, Provider Usage, Provider Connectivity, Performance,
  Playtesting, Diagnostics, Safe Debug Export, Quality dashboards, World
  Studio, Authoring / Mod Studio, Novel Studio, Tavern Studio, EventLog,
  Timeline Replay, StateDelta, Hidden Leak, and Visual Authoring tools.
- The app currently has no route-level code splitting or lazy-loaded studio
  modules.
- `api.ts` is also large and central, but its size is secondary to `App.tsx`
  because the UI components dominate render and chunk pressure.

Current mitigating factors:

- No large UI framework was introduced.
- Dependencies remain small: React, React DOM, Vite, TypeScript, and the React
  plugin.
- Several studios already have smaller helper files (`novelUi.tsx`,
  `tavernUi.tsx`, `worldUi.tsx`), proving that extraction is already an
  accepted local pattern.

Recommended contract:

- v3.6 should reduce bundle pressure by extracting route-scale UI modules and
  applying code splitting. It should not simply raise Vite's warning limit.
- Split modules must preserve loading, empty, error, disabled, local-only, and
  safety boundary states.
- Splitting must not change API behavior or introduce new backend semantics.

## Route-Level Split Candidates

High-value split candidates:

- Local Desktop / Studio Home panels.
- Provider Setup / Usage / Connectivity / Model Assignment panels.
- QA / Debug / Replay panels:
  - Timeline Replay;
  - EventLog Viewer;
  - StateDelta Viewer;
  - Hidden Leak Report;
  - Visible vs Debug Compare;
  - Safe Debug Export.
- Authoring / Mod Studio panels:
  - Module Browser;
  - Compatibility Matrix;
  - Quality Gate;
  - Validation / Diff / Safe Apply;
  - Visual Authoring editors.
- Novel Studio route and Novel UI wrappers.
- Tavern Studio route and Tavern UI wrappers.
- World Studio route and World UI wrappers.

Suggested order:

1. Extract QA / Debug / Provider panel modules first because they are the v3.5
   additions and are large, self-contained, and v3.6-critical.
2. Extract Authoring / Mod next because its visual editors and module panels
   are dense.
3. Keep Novel / Tavern / World extraction incremental because they already
   have helper UI files.

## Current Large List Risk

No virtualized list implementation was found. Searches did not find
`react-window`, `react-virtual`, `virtualized`, `IntersectionObserver`, or a
shared pagination/virtual-list component in `frontend/src`.

Existing mitigation is mostly:

- `useMemo` for derived rows;
- `slice(...)` for small previews;
- occasional backend `limit` query parameters;
- local filtering after loading complete arrays.

### EventLog

Current state:

- `EventLogViewerPanel` derives event types, actors, source modules, tags, and
  filtered rows from all loaded events.
- It renders all `filteredEvents` with `.map(...)`.
- Normal rows use safe summaries and raw details are behind `DebugGate`.

Risk:

- Large EventLog payloads can cause expensive filter recalculation and large
  DOM output.

Optimization priority: High.

Required boundary:

- Normal rows must continue to show only event id, turn/time, type, actor safe
  summary, visible safe summary, tags, and linked StateDelta count.
- Raw EventLog JSON and raw StateDelta payloads must remain debug-gated.

### Timeline Replay

Current state:

- `TimelineReplayPanel` filters turn groups with `filterTimelineTurns`.
- It renders all filtered turn groups and nested events with `.map(...)`.
- It uses local replay controls and `setInterval` for play mode.
- API supports turn range and event filter parameters, but the frontend can
  still hold and render large result sets.

Risk:

- Long campaigns can make replay filtering and nested rendering expensive.
- Auto-play does not currently appear to respect reduced-motion preferences.

Optimization priority: High.

Required boundary:

- Replay remains read-only and must not write `GameState` or `EventLog`.
- Hidden/debug events stay out of normal replay.
- Raw StateDelta details stay behind `DebugGate`.

### StateDelta

Current state:

- `StateDeltaViewerPanel` uses `flattenStateDeltaRows(events)` to build all
  delta rows from all loaded events.
- It then filters rows in memory and renders all filtered rows.
- The viewer is placed inside debug-gated UI and uses redacted value summaries.

Risk:

- Long debug timelines can create a large flat row array and heavy DOM output.

Optimization priority: High.

Required boundary:

- StateDelta Viewer remains debug-only.
- The viewer must not gain any apply/edit/delete action.
- Redaction must be applied before display.

### Quality Issues

Current state:

- Unified Quality Gate rows are built with `useMemo`.
- Quality panels display blockers, warnings, and suggested actions as safe
  summaries.
- Some reports can still render whole row groups at once.

Risk:

- Large quality reports can overload the DOM and make filtering slow.

Optimization priority: Medium to high.

Required boundary:

- Hidden text, NPC secrets, raw prompts, raw outputs, and raw state deltas must
  not enter normal report rows.

### Hidden Leak Issues

Current state:

- Hidden Leak Report builds issues from visible state, events, world health,
  narrative eval reports, diagnostics preview, and backup plan.
- It uses redaction helpers and category filtering.
- It scans nested values to find leak markers, then renders all filtered rows.

Risk:

- Large diagnostics/quality payloads can make marker collection expensive.

Optimization priority: Medium to high.

Required boundary:

- Leak report must never print hidden text in full.
- The report should keep source, target, severity, safe summary, and suggested
  action only.

### Provider Models

Current state:

- Provider Connectivity rows are derived from all provider profiles plus matrix
  rows.
- Provider model assignment and model options are built from loaded profile and
  capability arrays.
- Provider model discovery/sync uses safe backend metadata and fake clients in
  tests.

Risk:

- Large model lists can make repeated filtering and matrix derivation costly.
- There is no visible shared provider model cache, virtual model list, or
  refresh throttling pattern.

Optimization priority: High.

Required boundary:

- Model caches may contain safe metadata only.
- They must not store API keys, `transient_api_key`, raw provider responses,
  Authorization headers, raw env, or raw error payloads.

### Compatibility Matrix

Current state:

- Model compatibility matrix UI renders a sliced preview in one area.
- Module Compatibility Matrix Pro renders matrix rows/details from loaded
  matrix data.
- No shared large-matrix pagination or indexed filtering was found.

Risk:

- Large provider/model or package compatibility matrices can become expensive,
  especially if row derivation repeats nested scans.

Optimization priority: Medium to high.

Required boundary:

- Matrix rows remain safe summary metadata and must not expose secrets or
  hidden target details.

### Module Browser

Current state:

- Module Browser Pro renders local modules, validation, permission risk,
  compatibility, certification, and quality status.
- It is local-only and explicitly says no marketplace, no remote download, and
  no arbitrary code execution.

Risk:

- Large package sets can make package filtering and detail rendering slow.

Optimization priority: Medium.

Required boundary:

- Browser must never execute package contents.
- No online marketplace or remote package download wording should appear.

### Tavern Messages

Current state:

- Tavern message list renders loaded messages directly.
- RP memory and emotion panels use slices for some summaries.
- Mature/private and hidden safety copy remains present.

Risk:

- Long local RP sessions can produce heavy message rendering.

Optimization priority: Medium.

Required boundary:

- Mature/private content remains default hidden/filtered.
- NPC secrets and private persona do not enter normal prompt/context/export.

### Novel Scenes / Chapters

Current state:

- Novel outline and scene boards map over all loaded chapters/scenes.
- Quality and arc panels derive issues from loaded chapter/scene arrays.

Risk:

- Large manuscripts can cause rerenders while editing one chapter.

Optimization priority: Medium.

Required boundary:

- Novel UI remains draft/authoring mode and must not modify World
  `GameState`.
- World Bible and Timeline references remain safe-summary only.

## Current Provider Model List Risk

Provider connection and model discovery are safe from a secret-boundary
perspective, but performance polish is still needed.

Current backend facts:

- `ProviderModelDiscoveryReport` and `ProviderModelSyncReport` return lists of
  `ModelProfile` metadata.
- `sync_provider_models_safe` merges discovered models into
  `ProviderProfileV2.model_profiles`.
- Fake discovery client is deterministic and does not perform network I/O.
- No API key or Authorization header is returned by the safe reports.

Current frontend facts:

- Provider connectivity rows are derived with `useMemo`.
- Provider status and warnings are rendered per provider.
- Model assignment options are derived from loaded profile/model/capability
  arrays.

Performance risks:

- no visible virtualized model list;
- no visible refresh cooldown;
- no visible stale-status cache policy;
- repeated provider/matrix filtering may become costly with hundreds or
  thousands of local models.

Recommended v3.6 direction:

- introduce safe provider metadata cache with stale markers;
- virtualize or page model rows;
- index capability rows by provider id and model id;
- add explicit refresh/cooldown UI;
- never persist secrets or raw provider output in performance caches.

## Current Quality Report Rendering Risk

Quality and playtest surfaces are safe-summary oriented, but large reports
currently rely on normal React rendering of mapped arrays.

Risk areas:

- World health blockers/warnings;
- Unified Quality Gate rows;
- Mod Quality Gate blockers/warnings;
- Module playtest/stress rows;
- Hidden Leak report rows;
- Playtest reports and failed steps;
- CrossMode conflict rows;
- Diagnostics and backup excluded/included sections.

Recommended v3.6 direction:

- add category/severity counts before full row rendering;
- page or virtualize issue rows;
- memoize redacted row models;
- add progressive rendering for large reports;
- keep all report text redacted and safe-summary only.

## Current Accessibility Gaps

Existing positive signs:

- Some navigation regions have `aria-label`.
- Error and success panels use `role="alert"` and `role="status"`.
- Some graph previews use `role="img"` with `aria-label`.
- Replay controls have an `aria-label`.
- Native buttons and selects are generally used for actions and filters.

Gaps:

- No global keyboard shortcut layer was found.
- No systematic `onKeyDown` shortcut handling was found for major workflows.
- No general focus management pattern was found for wizard-like or modal-like
  flows.
- No focus restoration pattern was found for side panels, debug gates, safe
  apply, backup/restore, Provider setup, or export flows.
- No `prefers-reduced-motion` CSS rule was found.
- Replay auto-play uses timed progression but does not appear to check reduced
  motion preferences.
- ARIA labels are present in some areas but not systematic across badges,
  filter toolbars, status chips, icon-like controls, graph controls, and
  dense dashboards.
- Contrast and spacing are mostly handled with design tokens, but muted text,
  badge colors, dense cards, and long rows need v3.6 review.
- Font sizing is mostly static, which is good; large dense panels need
  readability polish rather than viewport-scaled type.

High-priority accessibility issues:

- missing focus management for wizard/dialog-like flows;
- missing reduced-motion handling for replay and dashboard transitions;
- incomplete accessible names for dense controls and status badges.

No release-blocking accessibility bug was found in this review, but these are
high-priority v3.6 polish items.

## Current Error Boundary Gaps

Current state:

- `ErrorPanel` exists and redacts errors before display in many flows.
- Many panels provide empty/error/disabled states.
- No React `ErrorBoundary`, `componentDidCatch`, or
  `getDerivedStateFromError` implementation was found.

Risk:

- A rendering error in one large report, debug view, provider matrix, or visual
  authoring panel can break the entire React tree.

Recommended v3.6 direction:

- add local ErrorBoundary wrappers around high-risk panels:
  - QA / Debug / Replay;
  - Provider Connectivity / Model Assignment;
  - Authoring / Mod visual editors;
  - Novel large manuscript views;
  - Tavern large session views;
  - diagnostics/backup/export wizards;
- error fallback must show safe redacted text only;
- fallback must not print raw paths, raw env, raw provider errors, raw
  `GameState`, raw `state_deltas`, API keys, or hidden/debug data.

## Current Backend/API Performance Notes

Current safe backend surfaces already include some useful controls:

- timeline replay frontend API accepts turn range and event filter parameters;
- local logs and recent usage APIs accept limits;
- provider model discovery and sync return safe metadata only;
- performance samples have a recent-summary model;
- quality and diagnostics use safe summaries and redaction.

Potential API polish:

- add safe pagination for EventLog and StateDelta debug lists if frontend-only
  virtualization is insufficient;
- add safe aggregate counts for large quality and hidden leak reports;
- add provider model list pagination or filtered fetch for very large model
  sets;
- add stale timestamp metadata for Provider connection status cache;
- keep any new endpoint safe-summary only and avoid changing engine semantics.

## Security / Visibility Boundary Review

No obvious security UI bug was found during this contract review.

v3.6 optimization must preserve:

- `visible_state` as normal World UI source;
- DebugGate for raw `StateDelta`, raw EventLog, debug memory, and raw debug
  payloads;
- Provider Gateway as the only model entry point;
- no API keys, `transient_api_key`, Authorization headers, raw env, provider
  secrets, raw prompts, raw outputs, hidden/debug data, or mature/private
  content in caches, frontend storage, logs, diagnostics, backups, exports, or
  reports;
- no online marketplace, remote package download, account, cloud sync, or
  arbitrary code plugin behavior;
- no UI direct mutation of `GameState`.

Optimization must not broaden what any panel can see. Virtualization,
pagination, caching, and code splitting must operate on the same safe data each
view already receives.

## Optimization Priorities

### Highest Priority

1. Split `App.tsx` by route/studio boundary.
2. Add a shared safe large-list pattern for EventLog, Timeline Replay, and
   StateDelta.
3. Add Provider model list virtualization or pagination plus safe status cache.
4. Add ErrorBoundary wrappers for QA / Debug / Provider / Authoring high-risk
   panels.
5. Add reduced-motion handling for replay and animated/progressive UI.

### Medium Priority

1. Optimize Quality and Hidden Leak report rendering.
2. Optimize Compatibility Matrix and Module Browser filtering.
3. Debounce and memoize cross-studio search/filter indexes.
4. Improve focus management in Safe Apply, backup/restore, diagnostics,
   Provider setup, and debug export flows.
5. Add accessible names for dense controls and status chips.

### Lower Priority

1. Fine-tune contrast, spacing, and font size in dense report panels.
2. Add loading skeletons and staged loading where operations already have
   meaningful progress states.
3. Improve large backup/diagnostics progress presentation.

## Non-goals

This review does not recommend:

- rewriting all frontend UI;
- adding a large UI framework;
- changing backend business semantics;
- changing `GameState`, `StateDelta`, `EventLog`, visibility, Provider
  Gateway, save migration, import/export, or quality gate authority;
- adding accounts, cloud sync, online marketplace, remote package download, or
  online QA;
- calling real providers in tests;
- caching secrets or raw debug content;
- making Debug / Replay write state;
- exposing hidden facts, NPC secrets, raw prompts, raw outputs, raw provider
  responses, raw EventLog JSON, or raw `state_deltas` in normal UI.

## Recommended v3.6 Implementation Order

1. Add v3.6 frontend smoke/check script that asserts:
   - split modules import;
   - DebugGate remains present for raw debug panels;
   - no online/account/cloud/marketplace wording appears as implemented;
   - reduced-motion CSS exists once implemented;
   - ErrorBoundary exists once implemented.
2. Extract QA / Debug / Provider panels from `App.tsx` into route-level
   modules.
3. Add shared safe list primitives:
   - paged list;
   - virtual-like windowed list;
   - filter toolbar with debounced text input;
   - safe empty/error/loading states.
4. Apply list primitive to EventLog Viewer.
5. Apply list primitive to Timeline Replay.
6. Apply list primitive to StateDelta Viewer while preserving DebugGate.
7. Apply list primitive to Provider model list and status rows.
8. Add Provider status stale cache with explicit refresh and cooldown.
9. Optimize Capability Matrix row derivation with indexed data.
10. Optimize Quality and Hidden Leak reports with category counts and paged
    rows.
11. Add ErrorBoundary wrappers around high-risk panels.
12. Add focus management and keyboard shortcut foundation.
13. Add reduced-motion and visual comfort CSS.
14. Extend v3.6 UI regression tests.
15. Run full `python -m pytest`, frontend build, and relevant v2.9-v3.5/v3.6
    frontend check scripts.

## Acceptance Criteria for v3.6.1

- This review document exists.
- It distinguishes optimization risks from release blockers.
- It identifies bundle/chunk, large-list, Provider model, Quality report,
  accessibility, and ErrorBoundary risks.
- It preserves local-first, Provider secret, DebugGate, visibility, and
  StateDelta/EventLog boundaries.
- No business code changes are required for this review.

## Verification

Commands run for this review:

- `git status --short`
- `Get-ChildItem frontend/src -File`
- `rg` scans over frontend source, scripts, and backend dashboard/report/list
  paths

Full test/build commands were not run because this change only adds a review
document and does not modify business code, frontend code, or tests.

