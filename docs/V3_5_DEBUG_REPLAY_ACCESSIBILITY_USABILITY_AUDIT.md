# v3.5 Debug / Replay Accessibility / Usability Audit

## Audit Scope

This audit reviews the usability and accessibility readiness of v3.5 Local QA /
Debug / Replay & Provider Connectivity UI Pro. It focuses on whether local
debug/replay/provider surfaces are understandable, navigable, and actionable
without weakening privacy or debug boundaries.

Reviewed surfaces:

- Timeline Replay UI Pro
- EventLog Viewer Pro
- StateDelta Viewer Pro
- Hidden Leak Report UI Pro
- Quality Gate Unified Dashboard Pro
- Provider Connectivity Dashboard
- Provider Model Assignment by Mode
- Debug disabled states and DebugGate copy
- Safe Debug Export Wizard
- Performance Dashboard Pro
- CrossMode Conflict Review Pro
- Module Playtest / Stress UI Pro
- shared error, empty, disabled, badge, and safe report components

## Passed Checks

1. Timeline Replay has a clear title.
   - The panel title is `Timeline Replay UI Pro`.
   - Supporting copy explains that visible replay uses player-safe summaries
     and raw StateDelta details are debug-gated and read-only.
   - Replay controls are labeled: start, previous, next, jump turn, pause,
     session replay, save replay, and replay dry-run.

2. EventLog Viewer event types are understandable.
   - `EventLog Viewer Pro` uses `EventTypeBadge` and filters by event type,
     actor, source module, tags, and turn.
   - Normal rows show event id, turn/time, type, actor, source module, visible
     summary, linked StateDelta count, and tags.

3. StateDelta Viewer is clearly marked debug-sensitive.
   - `StateDelta Viewer Pro` states it is debug-only, read-only, and cannot
     apply deltas or modify GameState.
   - The panel includes `ENABLE_DEBUG_API required` copy.

4. Hidden Leak Report can locate issues.
   - Issues include category, severity, source, target, safe summary, and
     suggested action.
   - The panel supports category filtering and shows blocker/warning counts.

5. Quality Gate Dashboard can locate blockers.
   - Unified dashboard shows overall state, category rows, blocker/error/
     warning counts, last run time, and suggested next actions.
   - Categories include Project, World, Novel, Tavern, Cross-Mode, Provider,
     Mods, Modules, RP/Mature, and Backup/Diagnostics.

6. Provider Connectivity status is understandable.
   - Provider rows show display name, provider type, connection status, model
     count, last tested time, allowed modes, default model, warnings, and
     local-only boundary copy.
   - Missing secret and missing model metadata warnings are visible in safe
     language.

7. Provider model assignment warnings are understandable.
   - Provider Model Assignment by Mode lists use cases and capability warnings.
   - Routing preview shows validation errors/warnings and fallback chains.
   - JSON capability requirements are surfaced as validation feedback rather
     than hidden failures.

8. Debug disabled state is clear.
   - `DebugGate`, diagnostics, and safe debug export panels explicitly state
     `ENABLE_DEBUG_API required` or `ENABLE_DEBUG_API is false`.
   - Disabled states explain that normal safe summaries remain available while
     raw debug views are unavailable.

9. Error states provide safe next-step context.
   - Error panels redact sensitive text.
   - Debug-related errors are paired with copy pointing to `ENABLE_DEBUG_API`.
   - Provider/config errors direct users toward safe setup and validation
     rather than exposing raw provider responses.

10. Empty states provide next steps.
    - Timeline Replay: load session replay or save replay.
    - EventLog: load a session or save EventLog.
    - StateDelta: load a session or save EventLog first.
    - Hidden Leak Report: run local leak check or load quality reports.
    - Provider Connectivity: load or create local provider profiles.
    - Performance: enable debug/perf APIs locally to inspect timing data.

11. Safe Debug Export risk explanation is clear.
    - The wizard states debug exports require `ENABLE_DEBUG_API` and explicit
      confirmation.
    - It distinguishes safe summary scopes from raw debug scopes.
    - It lists excluded sensitive categories and emphasizes local-only/no
      upload.

12. Performance Dashboard avoids serious information overload.
    - Metrics are grouped by backend API duration, save/load duration,
      EventLog size, timeline replay duration, provider call duration, quality
      gate duration, playtest duration, and frontend build/chunk warnings.
    - Missing metrics have friendly empty states.
    - Prompt/output/secrets are explicitly excluded.

13. CrossMode Conflict Review is understandable.
    - Conflicts are categorized by character identity, timeline order,
      relationship, fact visibility, stale link, broken link, and proposal
      validation.
    - Each conflict row includes severity, affected refs, safe summary,
      suggested action, and jump/fix draft affordances.

14. Module Playtest failures are locatable.
    - Module stress/playtest rows include module id, failed step, action
      coverage, state namespace conflicts, migration conflicts, hidden leak
      warnings, and pass/fail status.
    - Hidden details remain redacted, but failure summaries stay actionable.

15. No obvious release-blocking information overload was found.
    - v3.5 adds many panels, but major surfaces use filters, cards, badges,
      safe summary rows, and empty/error/disabled states.
    - The largest remaining issue is maintainability/information density in the
      monolithic frontend, not a release-blocking usability failure.

## High-Risk Usability Issues

No high-risk accessibility or usability blocker was found.

No release blocker was found for:

- unclear debug disabled states;
- unsafe or confusing debug export flow;
- inability to locate hidden leak or quality blockers;
- Provider connection/model assignment state being incomprehensible;
- Replay/EventLog/StateDelta surfaces lacking titles or basic next steps.

## Medium-Risk Usability Issues

No medium-risk release-blocking issue was found.

Medium-risk non-blocking concerns:

- The v3.5 QA/Debug/Provider UI is still implemented largely in a monolithic
  `App.tsx`, which increases cognitive load for future maintainers and makes
  component-level accessibility testing harder.
- Provider Connectivity and Prompt Lab are close together. The boundary is
  documented and visible, but future polish should split Provider Connectivity
  into a dedicated route/panel group.
- Performance Dashboard and Unified Quality Dashboard can become dense when
  many reports are loaded. Filters and grouping help, but v3.6 should consider
  virtualization or progressive disclosure for large reports.

## Low-Risk Issues

- Replay controls are text-labeled and clear, but icon buttons/tooltips could
  improve scan speed in a future UI polish pass.
- StateDelta paths are searchable/filterable but may still be technical for
  non-developer users. Additional inline explanations would help.
- Provider model assignment warning strings are accurate but somewhat
  developer-oriented. A future pass can map common warnings to friendlier
  explanations.
- Current static checks validate important strings and gates, but component
  keyboard/focus tests are not yet present.

## Fix Recommendations

No release-blocking fix is required for v3.5.

Recommended non-blocking follow-ups:

- Split v3.5 QA/Debug/Provider panels into smaller files/components for easier
  review and accessibility tests.
- Add keyboard/focus checks for replay controls, filter toolbars, provider
  assignment selectors, and debug export confirmations.
- Add friendlier descriptions for common Provider assignment warnings.
- Add progressive disclosure or virtualization for very large EventLog,
  Timeline Replay, Quality, and Performance reports.
- Keep disabled/empty/error states in the v3.5 UI regression check.

## Release Decision

Not blocked.

v3.5 can proceed toward release readiness from the Debug / Replay accessibility
and usability perspective, assuming backend tests, frontend build, and v3.5 UI
regression checks remain passing.
