# v3.6 Performance Regression Audit

Verification date: 2026-05-24

## Scope

This audit verifies the v3.6 Local Performance & Accessibility Polish work
against the current frontend implementation. It focuses on build health,
chunking, route-level code splitting, long-list rendering, large report
rendering, Provider model list performance, safe cache behavior, search/filter
performance, backup/diagnostics progress UI, slow Provider warnings, and
whether performance work introduced functional or boundary regressions.

The audit is read-only for business code. The only repository change made for
this task is this report.

## Verification Commands

```powershell
cd frontend
npm.cmd run build
npm.cmd run check:v36-performance-a11y
```

Results:

- `npm.cmd run build`: passed.
- `npm.cmd run check:v36-performance-a11y`: passed.
- No Vite chunk-size warning was emitted in the current build.

Current production chunk output:

| Chunk | Size | Gzip |
| --- | ---: | ---: |
| `assets/index-k78Alurj.js` | 2.45 kB | 1.26 kB |
| `assets/studio-desktop-ui-B9UH0Ktb.js` | 11.23 kB | 3.32 kB |
| `assets/studio-novel-ui-DJ_zR5gm.js` | 22.37 kB | 6.64 kB |
| `assets/studio-tavern-ui-Cts18pZZ.js` | 29.39 kB | 7.91 kB |
| `assets/studio-world-ui-BXFMSfsx.js` | 30.43 kB | 8.00 kB |
| `assets/studio-api-C65PFhUQ.js` | 45.78 kB | 6.83 kB |
| `assets/studio-provider-ui-D7VMkStf.js` | 52.25 kB | 14.31 kB |
| `assets/vendor-react-BnfF7MAh.js` | 192.48 kB | 60.34 kB |
| `assets/App-BTGD3Pu2.js` | 445.82 kB | about 107 kB |

Known chunk baseline:

- User-reported pre-specialized split warning: `App-CorS9wLp.js` 634.56 kB,
  gzip 152.46 kB.
- Previously measured pre-specialized split warning: `App-DjxbYrRc.js`
  635.37 kB, gzip 152.61 kB.
- Final main App chunk after the v3.6 splitting pass:
  `App-BTGD3Pu2.js` 445.82 kB, gzip about 107 kB.
- Main chunk reduction versus the measured warning baseline: 189.55 kB raw and
  about 45.4 kB gzip.
- The Vite `>500 kB` chunk warning was removed.

## Passed Items

1. Frontend build passes.
   `tsc -b && vite build` completed successfully.

2. Main App chunk warning is resolved in the current build.
   The main App chunk is now below the Vite 500 kB warning threshold.

3. Route-level code splitting exists.
   `frontend/src/App.tsx` uses `lazyNamed`, `Suspense`, and
   `RouteLoadingBoundary`. `frontend/vite.config.ts` defines manual chunks for
   React, API, Novel, Tavern, World, Provider, and Desktop UI modules.

4. Large EventLog rendering is optimized.
   EventLog UI includes `data-windowed-eventlog`, visible-window rendering,
   filters, and normal safe summary rows. Raw event JSON and raw StateDelta
   payloads remain excluded from normal view.

5. Timeline Replay large-list rendering is optimized.
   Timeline Replay includes `data-windowed-timeline`, turn filtering, jump
   controls, and visible turn windows. Replay remains read-only.

6. StateDelta debug-list rendering is optimized.
   StateDelta Viewer includes `data-windowed-statedelta`, path/op/event
   filtering, and visible row windows. The viewer remains DebugGate protected.

7. Quality large report rendering is optimized.
   Unified Quality Gate issue browsing includes `data-windowed-quality-report`,
   severity/source/search filters, safe summaries, and visible issue windows.

8. Hidden Leak large report rendering is optimized.
   Hidden Leak reports include `data-windowed-hidden-leak-report`, target
   grouping, severity/source-target filters, safe-metadata search, and visible
   issue windows. Hidden text is not searched or rendered in normal view.

9. Provider model list rendering is optimized.
   Provider model rows include search, capability filters, enabled/disabled
   filters, recommended use-case filters, memoized row derivation, and
   `data-windowed-provider-model-list`.

10. Capability matrix rendering is optimized.
    Capability matrix UI uses safe summaries, provider/capability/use-case
    filtering, collapsed grouping, memoized warning summaries, and
    `data-windowed-compatibility-matrix`.

11. Search and filter hot paths are debounced or memoized.
    `useDebouncedValue`, `buildSafeSearchIndex`, `safeSearchMatches`, and
    `useMemo` are used across Novel, Tavern, World, Authoring/Mod,
    Provider, EventLog, Timeline, StateDelta, Quality, and Hidden Leak views.

12. Large manuscript / chapter editor surfaces have targeted optimizations.
    Novel scenes, chapters, snapshots, word count, and sidebars use debounced
    input, memoized derived values, filtering, and paged/preview lists.

13. Large Tavern session / message surfaces have targeted optimizations.
    Tavern session, message, multi-NPC scene, and RP memory lists use
    debounced search, safe search indexes, filtering, and visible-list limits.

14. World panels have targeted optimizations.
    World NPC, quest, inventory, visible state, and module panels use safe
    preview limits, filters, memoized derived rows, and collapsible sections.

15. Authoring / Mod large package UI has targeted optimizations.
    Module Browser, compatibility matrix, permission dashboard, import/export
    previews, and validation issues include grouping, filters, pagination or
    window markers, and safe summaries.

16. Backup / diagnostics progress UI is available.
    Backup, restore, diagnostics, and safe debug export surfaces expose staged
    progress and exclusion summaries for `.env`, API keys, provider secrets,
    debug data, mature/private data, databases, logs/cache, and build outputs.

17. Slow Provider warning UI is available.
    Provider UI includes slow Provider warnings for high latency, repeated
    timeout, model-list slow paths, and high error rates without rendering raw
    Provider errors, prompts, outputs, or secrets.

18. Performance dashboard is available.
    The local performance dashboard summarizes large-list warnings, Provider
    latency, quality/playtest/save diagnostics durations, event counts, model
    counts, category filters, and optimization hints without telemetry upload.

19. No large new dependency was introduced.
    `frontend/package.json` still contains React, React DOM, Vite, TypeScript,
    and type packages only. No large virtualization, charting, routing, or
    accessibility framework was added for v3.6.

20. v3.6 static regression check passes.
    `check:v36-performance-a11y` confirms route split markers, windowed list
    markers, DebugGate expectations, keyboard shortcut safety markers, reduced
    motion markers, ErrorBoundary redaction markers, and safe API cache
    rejection markers.

## Performance Improvements

- Main App chunk pressure is materially improved. The current App chunk is
  445.82 kB, down from the 635.37 kB measured warning baseline.
- Vite no longer emits a `chunk size limit` warning in the current build.
- Route-sized chunks now separate `studio-provider-ui`,
  `studio-desktop-ui`, `studio-novel-ui`, `studio-tavern-ui`,
  `studio-world-ui`, `studio-api`, and `vendor-react`.
- Long EventLog, Timeline Replay, StateDelta, Quality, Hidden Leak, Provider
  model, Module Browser, and compatibility matrix views no longer rely only on
  rendering every row into the DOM.
- Search/filter paths use debounced input and memoized safe search indexes
  instead of recomputing every large list on each keystroke.
- Provider model and status refresh paths use safe summaries, stale indicators,
  and manual refresh affordances instead of encouraging repeated blind refresh.
- Backup/restore/diagnostics and safe debug export flows now expose staged
  progress, which reduces the apparent blank or frozen state for long local
  operations.

## Remaining Chunk / Bundle Warnings

No Vite `>500 kB` chunk warning remains in the current build.

Remaining bundle considerations:

- The main `App` chunk is still large at 445.82 kB. It is below the warning
  threshold, but still dense enough to merit continued extraction before v3.7.
- The Provider chunk is 52.25 kB and contains both Provider Connectivity and
  Prompt Lab surfaces. This is acceptable for v3.6, but it should be monitored
  if model discovery and assignment UI grows.
- `App.tsx` remains a large coordination file, and static check coverage may
  still be satisfied by code that remains in `App.tsx` but is no longer routed.

## High-risk Performance Regressions

None found.

No release-blocking performance regression remains for v3.6. Final freeze and
submit-readiness checks confirmed that `python -m pytest` passed, the frontend
build passed, all frontend `check:*` scripts passed, the main App chunk is below
the Vite warning threshold, and no high-risk acceptance blocker remains.

The earlier route-level splitting parity concern is retained below as a
medium-risk follow-up because it is still worth active-route runtime coverage
before v3.7, but it is no longer classified as a v3.6 release blocker.

## Medium-risk Performance Issues

1. Route-level lazy modules should still receive active-route parity smoke
   coverage before v3.7.
   The chunk-size goal is achieved, and final v3.6 checks passed. However,
   `App.tsx` still contains legacy route-adjacent implementations while active
   routes now use lazy Desktop and Provider modules. This is a non-blocking
   verification gap: add runtime smoke checks for the lazy `studio`,
   `prompt_lab`, Provider, Settings, and diagnostics surfaces so future
   cleanups cannot accidentally narrow a route while static source-token checks
   remain green.

2. Static checks do not measure runtime performance.
   The v3.6 check scripts verify markers and source patterns, but they do not
   measure frame time, scroll latency, input latency, hydration cost, or
   browser memory under synthetic large datasets.

3. Several optimizations remain frontend windowing rather than backend
   pagination.
   EventLog, Timeline, StateDelta, Quality, Hidden Leak, Provider model,
   Module Browser, and compatibility matrix views can avoid rendering every
   row, but several still filter in-memory arrays. Very large projects may need
   backend safe pagination or indexed summary endpoints before v3.7.

4. `App.tsx` remains very large.
   The main chunk is now below warning threshold, but the file still contains
   many legacy components and orchestration logic. That raises maintenance risk
   and makes static checks more likely to miss active-route parity issues.

5. Provider capability matrix and model list may still need measured stress
   tests.
   The UI uses memoization and windowing, but a Provider returning hundreds or
   thousands of models should be validated in a browser-level local stress
   check before v3.7.

6. Performance cache safety is mostly static-checked.
   The safe API cache rejects obvious unsafe payloads and stays in memory, but
   broader integration tests should continue to assert that no API key,
   `transient_api_key`, raw prompt/output, hidden facts, NPC secrets, or raw
   StateDelta payloads enter cache-like structures.

## Non-blocking Optimization Backlog

- Add active-route smoke checks for lazy `studio`, `prompt_lab`, Provider, QA,
  Authoring, Novel, Tavern, and World pages, not only source-token checks.
- Continue extracting `App.tsx` into feature-equivalent lazy modules while
  removing or quarantining dead legacy components.
- Add a bundle-budget check that records chunk sizes and fails only on agreed
  thresholds, instead of relying solely on Vite warnings.
- Add browser-level synthetic large-list performance checks for EventLog,
  Timeline Replay, StateDelta, Quality, Hidden Leak, Provider model list, and
  Module Browser.
- Add backend safe pagination or safe summary endpoints for very large reports
  and logs.
- Add Provider model list incremental loading for compatible endpoints that
  return very large model catalogs.
- Add measured filter latency checks for Novel, Tavern, World, Authoring,
  Provider, and QA views.
- Track Provider capability matrix safe-summary generation time and stale
  refresh behavior.

## Release Decision

Performance improvements are real and measurable: the frontend build passes,
the v3.6 performance/a11y check passes, and the main App chunk warning is gone.

No high-risk performance regression or release-blocking performance issue
remains for v3.6. The earlier route-level splitting parity concern is now
tracked as a medium-risk, non-blocking follow-up for v3.7 hardening.

Recommended decision:

- v3.6 can proceed with final freeze/tag readiness if the already recorded
  pytest, frontend build, and frontend check results remain current.
- Keep active-route runtime smoke checks, large-report stress checks, and
  further `App.tsx` extraction on the v3.7 non-blocking optimization backlog.
