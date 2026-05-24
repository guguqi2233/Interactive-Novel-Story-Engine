# v3.5 StateDelta / EventLog Debug Boundary Audit

## Audit Scope

This audit reviews the v3.5 StateDelta, EventLog, Timeline Replay, debug compare,
and debug export boundaries. It focuses on whether QA / Debug UI remains
read-only, whether raw StateDelta/EventLog details are gated, and whether normal
UI keeps safe summaries only.

Reviewed areas:

- `StateDeltaViewerPanel`
- `EventLogViewerPanel`
- `TimelineReplayPanel`
- `TimelineEventCard`
- `VisibleDebugStateCompare`
- `SafeDebugExportWizard`
- shared `DebugGate`
- debug API routes in `backend/app/main.py`
- v3.5 integration and UI regression tests

## Passed Checks

1. StateDelta Viewer is debug-gated.
   - `StateDeltaViewerPanel` is rendered inside the debug-gated QA/Debug area.
   - The panel labels itself as debug-only and states `ENABLE_DEBUG_API
     required`.
   - It is explicitly read-only and contains no apply button or mutation flow.

2. EventLog Viewer normal view shows safe summaries.
   - `EventLogSafeCard` shows event id, turn/time, safe event type, actor safe
     summary, visible summary, tags, and linked StateDelta count.
   - Raw EventLog JSON and raw StateDelta details are wrapped in `DebugGate`.
   - Debug-only events show redacted/gated labels in normal rows.

3. Timeline Replay normal view does not show raw deltas.
   - Timeline Replay uses visible/system-safe summary rows.
   - Raw StateDelta details are rendered only in `TimelineEventCard` inside
     `DebugGate`.
   - Empty state copy states Replay is read-only and never writes GameState or
     EventLog.

4. Debug UI cannot modify GameState through reviewed v3.5 surfaces.
   - StateDelta Viewer is read-only.
   - EventLog Viewer is read-only.
   - Timeline Replay controls observe/jump/filter replay only.
   - Visible vs Debug Compare summarizes sections and counts; it does not
     expose state mutation actions.

5. Debug UI cannot apply StateDelta.
   - No reviewed v3.5 StateDelta/EventLog/Timeline UI exposes an apply-delta
     control.
   - Existing copy explicitly says the viewer cannot apply deltas or modify
     GameState.

6. Debug export requires confirmation.
   - Safe Debug Export Wizard states debug exports require `ENABLE_DEBUG_API`
     and explicit confirmation.
   - Raw export scopes require explicit opt-in and confirmation.
   - Debug export is local-only and does not upload.

7. Debug compare does not show hidden text full bodies by default.
   - `VisibleDebugStateCompare` uses counts, section summaries, filtered field
     counts, and redacted hidden summaries.
   - It states hidden text is summarized and redacted by default.

8. EventLog remains the authoritative event log.
   - Reviewed v3.5 UI reads EventLog/debug responses but does not replace
     EventLog authority.
   - World-changing flows remain outside these QA/debug viewers and continue to
     rely on backend action APIs, StateDelta, and EventLog.

9. UI cannot delete or modify EventLog through reviewed v3.5 surfaces.
   - EventLog Viewer has load/filter controls only.
   - No delete/edit EventLog button or API call was found in the v3.5 EventLog
     viewer path.

10. Replay UI observes only and does not write back.
    - Timeline Replay UI provides start/previous/next/jump/pause/filter-style
      controls for observation.
    - Replay dry-run is labeled as preview-only and does not mutate GameState or
      EventLog.

11. Tests cover normal raw delta exclusion.
    - `backend/tests/test_v35_integration_regression.py` asserts
      `/game/state/{session_id}` contains `visible_state` and does not contain
      `state_deltas`.
    - The same integration test verifies debug endpoints can return
      `state_deltas` only after debug is enabled.
    - `frontend/scripts/check-v35-qa-debug-provider-ui.mjs` checks sensitive
      components are clearly debug-gated and normal slices do not render raw
      StateDelta JSON.

12. `ENABLE_DEBUG_API=false` disables debug routes or shows disabled UI.
    - Backend debug routes call `require_debug_api()`.
    - Existing debug API tests assert disabled debug routes return 403.
    - v3.5 integration regression verifies session timeline/events return 403
      when debug is disabled.
    - Frontend `DebugGate` and disabled states show `ENABLE_DEBUG_API required`
      copy.

## High-Risk Boundary Problems

No high-risk StateDelta / EventLog debug boundary problem was found.

No release blocker was found for:

- raw StateDelta rendering in normal UI;
- EventLog deletion/modification from v3.5 UI;
- debug UI applying StateDelta;
- replay writing back to GameState/EventLog;
- debug API availability when `ENABLE_DEBUG_API=false`.

## Medium-Risk Boundary Problems

No medium-risk release-blocking issue was found.

Medium-risk areas to keep under regression coverage:

- Raw EventLog JSON and raw StateDelta payloads are intentionally available in
  DebugGate. Future edits must keep them inside `DebugGate` and behind backend
  `ENABLE_DEBUG_API`.
- Visible vs Debug Compare derives debug counts from event/delta data. It must
  remain redacted-summary based and must not start printing hidden text bodies.
- Replay dry-run should remain dry-run only. Any future replay apply/restore
  feature would need a separate validation, confirm, and GameState boundary
  audit.

## Low-Risk Issues

- Some StateDelta/EventLog handling still lives in the large monolithic
  `App.tsx`. v3.5 component cleanup added safety components, but v3.6 can
  further split debug-only renderers for maintainability.
- Static checks currently guard common raw delta regressions. If a frontend test
  framework is introduced later, component-level DebugGate tests would provide
  stronger coverage.
- EventLog safe tags and source-module summaries are derived from metadata;
  current code redacts/report-summarizes them, but future metadata fields should
  continue using the same redaction path.

## Fix Recommendations

No release-blocking fix is required for v3.5.

Recommended non-blocking follow-ups:

- Keep `test_v35_integration_regression.py` and
  `check:v35-qa-debug-provider-ui` in the release checklist.
- Continue centralizing raw StateDelta/EventLog rendering inside
  `StateDeltaViewerPanel` and debug-only shared components.
- Add component-level DebugGate tests if the frontend testing stack expands.
- Require a new audit before adding any replay restore, EventLog edit/delete, or
  debug StateDelta apply feature.

## Release Decision

Not blocked.

v3.5 can proceed toward release readiness from the StateDelta / EventLog debug
boundary perspective, assuming backend tests, frontend build, and v3.5 UI
regression checks remain passing.
