# v3.6 Accessibility / Usability Audit

Verification date: 2026-05-24

## Scope

This audit reviews the v3.6 Local Performance & Accessibility Polish work for
accessibility, keyboard operation, focus management, safe error handling,
visual comfort, loading and empty states, disabled-state guidance, dense report
usability, Provider model list readability, debug-disabled copy, and Safe Debug
Export risk communication.

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
- Current build emits no Vite `>500 kB` chunk warning.
- Current main App chunk: `assets/App-BBc0cBc4.js` 445.81 kB, gzip
  107.20 kB.

Additional source checks reviewed:

- `frontend/scripts/check-v36-a11y-semantics.mjs`
- `frontend/scripts/check-v36-focus-management.mjs`
- `frontend/scripts/check-v36-keyboard-shortcuts.mjs`
- `frontend/scripts/check-v36-reduced-motion.mjs`
- `frontend/scripts/check-v36-contrast-spacing.mjs`
- `frontend/scripts/check-v36-error-boundary.mjs`
- `frontend/scripts/check-v36-loading-progressive.mjs`

## Passed Items

1. Major pages have clear headings and section titles.
   Route fallback UI, workspace panels, dashboards, report browsers, and
   provider surfaces use visible titles and section headings. Static checks
   verify shared page/header and section-card semantics.

2. Main navigation has accessible labeling.
   The local workspace has an accessible landmark label, the primary
   navigation exposes `aria-label="Local studio navigation"`, active navigation
   uses `aria-current`, and navigation buttons use sanitized accessible names.

3. Icon-only buttons have accessible labels where required.
   The keyboard shortcut launcher and debug drawer controls include readable
   labels and control relationships such as `aria-controls`.

4. Form inputs have labels.
   Provider setup, model filters, local settings toggles, report filters,
   authoring forms, and search controls use visible labels or grouped filter
   semantics.

5. Status, risk, severity, leak, and capability badges are readable.
   Shared badge helpers expose readable text such as `Status:`, `Risk level:`,
   `Validation status:`, `Quality severity:`, `Leak risk severity:`, and
   `Model capability`.

6. Keyboard shortcuts are available.
   `KeyboardShortcutsProvider`, `ShortcutHelpDialog`, shortcut status live
   region, local preference storage, and shortcut help UI are present.

7. Keyboard shortcuts do not trigger dangerous actions.
   The shortcut handler avoids confirm-gated operations. The dangerous action
   blocklist includes apply, import, delete, restore, and debug export.

8. `Ctrl/Cmd+S` does not bypass confirm or apply flows.
   Shortcut copy explicitly reserves save behavior for safe draft contexts and
   does not call dangerous handlers such as apply, import, restore, delete, or
   debug export.

9. `Esc` closes supported modal/drawer surfaces.
   Shortcut help supports Escape close behavior, and the global handler also
   closes shortcut help or the debug drawer without mutating project data.

10. Modal/dialog focus management is present.
    The UI includes `focusElementSafely`, `focusElementImmediately`,
    `focusableElementsIn`, `handleDialogFocusTrap`, and
    `useManagedDialogFocus`.

11. Dialog close focus return is implemented.
    `useManagedDialogFocus` records the previously active element and restores
    focus after close when possible.

12. Dangerous confirm does not default-focus a custom destructive button.
    Dangerous confirmation uses the native keyboard-accessible confirm path,
    with no custom destructive default focus detected in the checked source.

13. Wizard step focus support is present.
    `useStepTitleFocus` focuses step titles after step changes, and checked
    wizard title targets use `tabIndex={-1}`.

14. Reduced motion is available.
    The UI has a local reduced-motion preference key, root reduced-motion data
    state, settings toggle, motion-safe scroll helper, and reduced-motion
    styling.

15. `prefers-reduced-motion` is respected.
    The initial reduced-motion state reads the system preference, and CSS
    includes `@media (prefers-reduced-motion: reduce)`.

16. Contrast, font size, and spacing polish is present.
    Styles include v3.6 visual-comfort updates for route loading, skeletons,
    badges, disabled states, empty states, report rows, and dense dashboards.

17. ErrorBoundary shows safe errors and next steps.
    `AppErrorBoundary` provides safe summaries, retry, go-home recovery, and a
    local diagnostics hint. Normal UI avoids raw stack traces, raw env, API
    keys, hidden facts, and sensitive local paths.

18. Loading skeletons and progressive rendering are available.
    `LoadingSkeletonPanel` and `ProgressiveLoadNote` provide summary-first
    loading states. Skeleton rows are explicitly safe and contain no project
    data, hidden facts, raw debug payloads, or secrets.

19. Empty states provide next-step guidance.
    EventLog, Timeline, StateDelta, Hidden Leak, Provider model list, Quality,
    World, Novel, Tavern, Authoring, Backup, Diagnostics, and Performance
    surfaces include empty copy that tells the user how to proceed.

20. Disabled states explain why an action is unavailable.
    Debug disabled copy references `ENABLE_DEBUG_API`, API-disabled notices
    explain local enablement, and disabled buttons are paired with safe state
    copy where the surrounding panel is blocked.

21. Large reports and large lists reduce information overload.
    EventLog, Timeline Replay, StateDelta, Quality, Hidden Leak, Provider
    model list, Module Browser, and compatibility matrix views use grouping,
    filters, paging/windowing, rendered-count copy, and safe summaries.

22. Provider model list is understandable.
    Provider model rows expose provider, model, enabled state, capability
    badges, recommended use cases, stale/cache status, search, capability
    filters, enabled/disabled filter, and use-case filter. API keys and raw
    provider responses are excluded.

23. Debug disabled state is clear.
    Debug panels show `ENABLE_DEBUG_API required` or `debug disabled` copy,
    and raw StateDelta/debug details remain behind DebugGate.

24. Safe Debug Export risk copy is clear.
    Safe Debug Export and Diagnostics surfaces explain local-only operation,
    explicit confirm for debug/raw exports, redaction policy, default
    exclusions, and no upload behavior.

## Accessibility Improvements

- Added route-level loading states with safe skeletons and live-region status
  text.
- Added route-scoped ErrorBoundary coverage with safe retry/go-home recovery.
- Added keyboard shortcut help, local shortcut enable/disable setting, and
  status announcements.
- Added focus helpers for dialogs, wizard step titles, and safe error states.
- Added readable ARIA/status labels for navigation, status badges, risk
  badges, severity badges, leak badges, and model capability badges.
- Added reduced-motion preference handling and CSS support for
  `prefers-reduced-motion`.
- Added visible focus styling for programmatically focused headings.
- Added safer accessible-name sanitization through `safeAriaText`.

## Usability Improvements

- Large reports are easier to scan through grouping, filters, pagination, and
  windowed rendering.
- Provider model lists are easier to navigate through search, capability
  filters, enabled-state filters, use-case filters, memoized capability
  badges, and rendered-count copy.
- Backup, restore, diagnostics, and safe debug export flows communicate
  long-running progress through explicit stages and exclusion summaries.
- Error states provide next steps instead of raw failure payloads.
- Empty states tell the user how to load data, run a local check, start a
  session, or refresh a safe summary.
- Disabled debug states explain local enablement requirements instead of
  silently hiding debug-dependent controls.
- Keyboard shortcuts improve navigation while preserving confirm boundaries.
- Reduced motion and visual comfort settings make long local sessions calmer.

## High-risk Accessibility Blockers

No screen-reader, keyboard-only, focus-management, or visual-comfort blocker was
confirmed by the static checks and source review.

However, there is one **high-risk usability / release blocker** that affects
core operation confidence:

1. Route-level lazy splitting may have changed active route feature coverage
   for Desktop and Provider/Settings surfaces.

   Evidence:

   - `App.tsx` routes `studio` to lazy `DesktopStudioHome` from
     `desktopUi.tsx`.
   - `App.tsx` routes `prompt_lab` to lazy `ProviderPromptLabPage` from
     `providerUi.tsx`.
   - Older, more complete `StudioHome`, `PromptLabPage`, and
     `SettingsPrivacyPanel` implementations still remain in `App.tsx`.
   - The older `StudioHome` includes detailed World Health, Content Coverage,
     Narrative Quality, Performance, Playtesting, Scenario Regression,
     Provider Settings / Privacy, Desktop Health, and Local Update Notes
     panels.
   - The new lazy Desktop component appears narrower and may not be a
     feature-equivalent extraction.

   Accessibility / usability impact:

   - Even if labels, focus, and loading states pass, users may lose access to
     expected panels or next-step actions on the active route.
   - Static checks can pass because old unused code still exists in `App.tsx`.

   Release requirement:

   - Before final v3.6 release, verify active-route parity for `studio`,
     `prompt_lab`, and settings-related routes, or move the full old
     implementations into the lazy modules.

## Medium-risk Usability Issues

1. Accessibility validation is mostly static.
   The current checks verify source markers and safe patterns, but do not run
   browser-level tab-order, screen-reader, zoom, mobile viewport, or reduced
   motion walkthroughs.

2. Focus coverage is strongest for shared dialogs and shortcut help.
   Some older authoring or dashboard subpanels may still rely on native focus
   flow rather than explicit focus restoration.

3. Large dashboards remain dense.
   Windowing and grouping help, but QA/Debug, Authoring/Mod, Provider, and
   Quality views can still present many controls at once.

4. Keyboard shortcuts are intentionally minimal.
   This is safer for v3.6, but the shortcut framework is not yet a full command
   palette or task launcher.

5. Native confirm is safe but limited.
   Native confirm avoids custom destructive auto-focus problems, but complex
   destructive operations could benefit from richer accessible confirm dialogs
   in a future version.

6. Provider model list usability depends on upstream metadata quality.
   Filters and badges help, but poorly labeled or huge model catalogs may need
   stronger grouping and pinned recommendations before v3.7.

7. Safe Debug Export risk copy is clear, but debug-heavy workflows still need
   a manual keyboard-only pass.
   The source shows risk copy and confirm requirements, but this audit did not
   run an interactive browser walkthrough.

## Non-blocking Follow-ups

- Add browser-level keyboard-only smoke tests for Studio, Novel, Tavern, World,
  Authoring, QA/Debug, Provider, Backup/Diagnostics, and Settings.
- Add active-route runtime smoke checks that assert lazy routes show the
  expected panels and actions.
- Add screen-reader notes for navigation, live regions, status badges, report
  rows, and Provider model filters.
- Add high-zoom and narrow viewport checks for dense dashboards.
- Add skip links or quick-jump navigation for long dashboard pages.
- Expand progressive disclosure for QA/Debug and Authoring/Mod dashboards.
- Improve Provider model grouping for very large compatible model lists.
- Consider a custom accessible confirm dialog for complex destructive actions,
  while preserving no-default-focus on destructive buttons.
- Expand shortcut help into a searchable local command reference without
  allowing shortcuts to bypass confirm.

## Release Decision

The v3.6 accessibility foundations are materially improved: build passes,
`check:v36-performance-a11y` passes, and the source includes keyboard shortcut,
focus, reduced-motion, ErrorBoundary, semantic label, skeleton, empty-state,
disabled-state, and large-list usability improvements.

This audit does **not** find a pure accessibility blocker. It does find the same
high-risk active-route parity issue recorded in the v3.6 Performance
Regression Audit. Because v3.6 must not change core operations while optimizing
the UI, final v3.6 release should be treated as **blocked until lazy route
feature parity is verified or restored**.

Recommended next step:

- Verify or restore active-route parity for `studio`, `prompt_lab`, and
  settings-related routes.
- Then rerun:
  - `cd frontend && npm.cmd run build`
  - `cd frontend && npm.cmd run check:v36-performance-a11y`
  - the v2.9-v3.5 frontend checks that cover affected pages.
