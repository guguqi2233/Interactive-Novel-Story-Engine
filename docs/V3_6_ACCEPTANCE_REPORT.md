# v3.6 Acceptance Report: Local Performance & Accessibility Polish

## Verdict

Accepted with documented limitations.

v3.6 is accepted as **Local Performance & Accessibility Polish** for the
local-first AI Narrative Studio. The accepted scope is optimization and
accessibility polish over the existing v0.1-v3.5 product surface, not a new
business-system release. The implementation improves route-level loading,
frontend chunk pressure, long-list and large-report rendering, Provider model
list performance, Provider status safe caching, search/filter responsiveness,
keyboard and focus usability, accessibility semantics, reduced motion, safe
error boundaries, loading skeletons, progressive rendering, and local
backup/diagnostics progress affordances.

No high-risk v3.6 release blocker remains in the accepted scope. The latest
code review blocker around Timeline Replay normal error display was fixed:
Timeline Replay now redacts normal `error` and `dryRunError` text before
rendering, and the v3.6 performance/a11y check guards against raw error display
regression.

## Verification Date

2026-05-24

## Verification Commands

```powershell
python -m pytest
```

Result: passed, `1783 passed in 129.35s`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed. Current production chunk output includes:

- `assets/App-BTGD3Pu2.js`: 445.82 kB, gzip 107.20 kB.
- `assets/vendor-react-BnfF7MAh.js`: 192.48 kB, gzip 60.34 kB.
- `assets/studio-provider-ui-D7VMkStf.js`: 52.25 kB, gzip 14.31 kB.
- `assets/studio-api-C65PFhUQ.js`: 45.78 kB, gzip 6.83 kB.
- `assets/studio-world-ui-BXFMSfsx.js`: 30.43 kB, gzip 8.00 kB.
- `assets/studio-tavern-ui-Cts18pZZ.js`: 29.39 kB, gzip 7.91 kB.
- `assets/studio-novel-ui-DJ_zR5gm.js`: 22.37 kB, gzip 6.64 kB.
- `assets/studio-desktop-ui-B9UH0Ktb.js`: 11.23 kB, gzip 3.32 kB.

No Vite `>500 kB` chunk warning was emitted in this verification run.

```powershell
cd frontend
# all package.json check:* scripts
```

Result: passed. All 34 frontend check scripts completed successfully:

- `check:v29-ui`
- `check:v30-ux`
- `check:v31-novel-ui`
- `check:v32-tavern-ui`
- `check:v33-world-ui`
- `check:v34-authoring-ui`
- `check:v35-qa-debug-provider-ui`
- `check:v36-a11y-semantics`
- `check:v36-authoring-mod-package-performance`
- `check:v36-backup-diagnostics-progress`
- `check:v36-capability-matrix-performance`
- `check:v36-contrast-spacing`
- `check:v36-error-boundary`
- `check:v36-eventlog-windowing`
- `check:v36-focus-management`
- `check:v36-hidden-leak-windowing`
- `check:v36-integration-regression`
- `check:v36-keyboard-shortcuts`
- `check:v36-loading-progressive`
- `check:v36-novel-performance`
- `check:v36-performance-a11y`
- `check:v36-performance-accessibility`
- `check:v36-performance-dashboard-polish`
- `check:v36-provider-model-list-windowing`
- `check:v36-provider-status-cache`
- `check:v36-quality-report-windowing`
- `check:v36-reduced-motion`
- `check:v36-safe-api-cache`
- `check:v36-search-filter-performance`
- `check:v36-slow-provider-warning`
- `check:v36-statedelta-windowing`
- `check:v36-tavern-performance`
- `check:v36-timeline-windowing`
- `check:v36-world-panel-performance`

The temporary Node wrapper used to execute the check list emitted a Node
deprecation warning for `spawnSync(..., { shell: true })`; the warning concerns
the local verification wrapper, not project runtime code. Each npm script
itself passed.

## Scope Accepted

1. Performance / Accessibility Contract Review.
   `docs/V3_6_PERFORMANCE_ACCESSIBILITY_CONTRACT_REVIEW.md` exists and maps
   bundle, large-list, Provider model-list, quality report, accessibility, and
   error-boundary priorities.

2. Frontend Bundle / Chunk Review.
   The main App chunk is below the warning threshold. Route-sized chunks now
   separate Provider, Desktop, Novel, Tavern, World, API, and React vendor
   payloads.

3. Route-Level Code Splitting.
   `React.lazy`, `Suspense`, `RouteLoadingBoundary`, and route-scoped
   `AppErrorBoundary` are present. Loading and failure states remain safe and
   local-only.

4. Large EventLog Virtualized Rendering.
   EventLog rows use windowed rendering, filters, safe summaries, and linked
   StateDelta counts. Raw EventLog JSON and raw StateDelta payloads remain
   debug-gated.

5. Timeline Replay Virtualized Rendering.
   Timeline Replay uses turn windows, filters, jump controls, active event
   state, safe summaries, and debug-gated raw details. Replay remains read-only.

6. Long StateDelta / Debug List Optimization.
   StateDelta Viewer remains inside DebugGate and uses filtered/windowed rows,
   redacted value summaries, and no apply-delta action.

7. Large Quality Report Optimization.
   Unified Quality Gate issues use grouping, severity/source/search filters,
   collapsed categories, pagination/windowing, and safe summaries.

8. Large Hidden Leak Report Optimization.
   Hidden Leak reports use target grouping, severity/source-target filters,
   safe metadata search, and visible issue windows without printing hidden text
   bodies.

9. Provider Model List Virtualization.
   Provider model rows support search, capability filters, enabled/disabled
   filters, recommended use-case filters, memoized badges, and windowed
   rendering.

10. Provider Connection Status Cache.
    Backend cache stores only allowlisted safe fields: provider profile id,
    status, tested time, latency, safe error type, model count, and redaction
    flag. TTL/stale/manual refresh behavior is present.

11. Capability Matrix Performance Polish.
    Capability matrix views use safe summaries, provider/capability/use-case
    filters, grouped rows, memoized warning summaries, and windowing markers.

12. Search / Filter Performance Polish.
    Shared search helpers provide debounced input, safe search indexes,
    memoized result lists, and no normal search indexing of hidden text.

13. Large Manuscript / Chapter Editor Performance.
    Novel chapter, scene, snapshot, word count, and sidebar surfaces use
    targeted debouncing, pagination, memoized derived values, and safe filters.

14. Large Tavern Session / Message List Performance.
    Tavern session, message, multi-NPC, and RP memory surfaces use safe search,
    filters, visible-list limits, and jump/latest affordances without exposing
    mature/private content by default.

15. World Panel Rendering Optimization.
    World NPC, quest, inventory, visible state, and module panels use filters,
    preview limits, collapsible sections, and safe visible-state summaries.

16. Authoring / Mod Large Package UI Optimization.
    Module Browser, compatibility matrix, permission dashboard, import/export
    preview, validation, and large package surfaces use grouping, filters,
    paging/windowing, and never execute packages.

17. Backup / Restore / Diagnostics Progress UI.
    Local progress stages and exclusion summaries are visible for backup,
    restore, diagnostics, and debug export workflows.

18. Slow Provider Warning UI.
    Provider UI shows high-latency, timeout, model-list-slow, and high-error
    warnings using safe summaries only.

19. Local Performance Dashboard Polish.
    Performance Dashboard shows local large-list warnings, Provider latency,
    quality/playtest/save/diagnostics durations, event/model counts, filters,
    and optimization hints without telemetry upload.

20. Keyboard Shortcuts Foundation.
    Keyboard shortcut help and navigation shortcuts are present. Shortcuts do
    not trigger apply, import, delete, restore, migration apply, or debug
    export without existing confirmation paths.

21. Focus Management.
    Dialog, shortcut help, wizard step title, and safe error focus helpers are
    present. Destructive actions are not default-focused by custom dialogs.

22. Accessibility Labels / Semantics.
    Main navigation, icon-only buttons, badges, filter groups, form inputs,
    loading/error states, and major panels have readable labels or semantics.

23. Reduced Motion / Visual Comfort.
    Reduced-motion preference, `prefers-reduced-motion`, visual comfort
    spacing, badge readability, contrast, and focus styles are present.

24. Contrast / Font Size / Spacing Polish.
    Styles include v3.6 readability updates for dense dashboards, reports,
    badges, loading skeletons, disabled states, and error/warning copy.

25. Error Boundary Polish.
    `AppErrorBoundary` provides safe summaries, retry/go-home actions, focus
    behavior, stack redaction, secret/path/raw-env redaction, and local
    diagnostics guidance.

26. Loading Skeleton / Progressive Rendering Polish.
    Major dashboards and large lists use safe loading skeletons and
    summary-first progressive rendering; skeletons do not contain project data.

27. Safe Refresh / API Cache Strategy.
    Frontend safe API cache is in-memory only, stores safe summaries, exposes
    stale/manual refresh state, and rejects secrets, hidden/debug content, raw
    prompts, raw outputs, raw provider responses, and raw StateDelta payloads.

28. v3.6 UI Regression Tests.
    v3.6 frontend check scripts cover route splitting, long-list windowing,
    Provider model list, status cache, safe API cache, accessibility,
    reduced motion, keyboard shortcuts, ErrorBoundary, loading/progressive
    rendering, and cross-version UI safety.

29. v3.6 Integration Regression Tests.
    Backend integration tests cover v3.6 safe cache/provider status behavior,
    no direct `GameState` mutation, hidden/debug exclusion, fake provider
    usage, and preservation of v0.1-v3.5 boundaries.

## Boundary Review

- World Engine remains the authoritative fact source. v3.6 changes are UI,
  cache, rendering, and accessibility optimizations only.
- UI code still cannot directly modify `GameState`, active saves, module
  runtime state, `StateDelta`, or `EventLog`.
- Replay and debug views remain observational. No debug apply-delta or
  EventLog rewrite path was accepted.
- StateDelta Viewer and Visible vs Debug Compare remain debug-gated.
- EventLog and Timeline normal views show safe summaries and counts only.
  Raw StateDelta JSON remains inside DebugGate.
- `visible_state` and safe summaries remain the normal UI source. Hidden facts,
  NPC secrets, debug memory, raw prompts, raw outputs, raw provider responses,
  raw env, API keys, and mature/private bodies are excluded from normal UI.
- Provider Gateway remains the only model entry point. Provider caches and UI
  optimizations do not change routing semantics or world authority.
- `ProviderProfile` still stores only metadata plus `api_key_env` or
  `secret_ref`; no raw API key persistence was accepted.
- `transient_api_key` is not persisted and does not enter logs, diagnostics,
  backup/export, frontend state, or cache.
- Frontend safe API cache and Provider status cache store safe metadata only.
- Keyboard shortcuts do not bypass explicit confirmation for dangerous actions.
- No account system, cloud sync, online marketplace, remote package download,
  online QA platform, API resale service, or arbitrary-code plugin system was
  introduced.
- Tests use fake/mock/local provider paths and do not require real provider
  networking.

## Known Limitations

- `App.tsx` remains large even after route-level splitting. The main chunk is
  under the warning threshold, but further extraction should continue in v3.7.
- Some legacy detailed Desktop/Provider components still remain in `App.tsx`
  while active lazy modules provide summary-first equivalents. Current checks
  pass and no release blocker remains, but dead-code cleanup and route parity
  smoke tests are recommended before v3.7 finalization.
- v3.6 frontend checks are mostly static/source-level checks. They strongly
  guard known privacy and performance patterns, but they are not a full browser
  performance benchmark with thousands of rendered rows.
- Provider-supplied model ids/display names remain visible safe metadata. They
  are not treated as secrets by default; v3.7 can add stronger truncation and
  normalization.
- Accessibility checks cover core semantics, labels, focus helpers, and visual
  comfort, but not full screen-reader QA across every route.
- Safe API cache is in-memory only. It improves repeated local refreshes within
  a session but is not a persistent offline cache.

## Acceptance Risks

- Route-level lazy loading must continue to be checked when moving old panels
  out of `App.tsx`; static token checks can otherwise pass against unused code.
- Future search/filter expansions must pass only safe metadata into normal
  search indexes and must not index hidden/private text.
- Future cache fields must remain explicitly allowlisted and reviewed for
  secrets, raw prompts, raw provider responses, hidden/debug content, and
  routing semantics.
- Future debug UI additions must remain behind `ENABLE_DEBUG_API` and must not
  gain apply/delete/rewrite authority over `GameState`, `StateDelta`, or
  `EventLog`.
- Long-list performance validation should eventually include browser-level
  smoke/performance fixtures, not only source checks.

## Recommended v3.7 Priorities

1. Local Complete Product route parity pass: ensure Desktop, Provider,
   Settings, Novel, Tavern, World, Authoring, and QA routes expose the expected
   final panels through active lazy modules.
2. Continue reducing `App.tsx` by moving legacy detailed panels into route
   modules or removing unreachable duplicate implementations.
3. Add browser-level smoke checks for lazy routes, debug-disabled routes, large
   EventLog/Timeline/StateDelta windows, Provider model lists, and Quality /
   Hidden Leak reports.
4. Add large local fixture projects for long-list and large-report performance
   validation.
5. Improve Provider model name normalization, truncation, and display safety
   for unusual provider-supplied metadata.
6. Expand keyboard shortcut and focus QA with manual screen-reader and
   keyboard-only review.
7. Keep v3.7 focused on Local Complete Product polish without introducing
   accounts, cloud sync, online marketplace, remote package downloads, or
   arbitrary-code plugins.

## Final Status

v3.6 is accepted for release as **Local Performance & Accessibility Polish**.

Final status: **Accepted with documented limitations; no high-risk release
blocker remains.**

Recommended next step: prepare v3.6 release notes and final freeze checks,
then proceed toward v3.7 Local Complete Product once the release checklist is
clean.
