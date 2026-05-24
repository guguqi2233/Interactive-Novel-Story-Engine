# v3.6 StateDelta / EventLog / Debug Boundary Audit

Verification date: 2026-05-24

## Verdict

v3.6 StateDelta / EventLog / Debug boundary audit is **not blocked**.

The reviewed v3.6 performance work uses windowing, pagination, safe summaries,
redaction helpers, and debug gates. It does not add a UI or API path that
modifies `GameState`, applies `StateDelta`, rewrites `EventLog`, or exposes raw
StateDelta payloads in normal UI.

## Verification Commands

```powershell
python -m pytest
```

Result: `1783 passed in 116.72s`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed. Main App chunk: `445.81 kB`, gzip `107.20 kB`; no Vite
`>500 kB` warning.

```powershell
cd frontend
npm.cmd run check:v36-performance-a11y
```

Result: passed.

Reviewed implementation and test evidence:

- `docs/WORLD_ENGINE.md`
- `docs/V3_6_ROADMAP.md`
- `backend/app/core/state_delta.py`
- `backend/app/core/event_log.py`
- `backend/app/core/game_loop.py`
- `backend/app/core/timeline_replay.py`
- `backend/app/main.py`
- `frontend/src/App.tsx`
- `frontend/src/worldUi.tsx`
- `frontend/scripts/check-v36-performance-a11y.mjs`
- `frontend/scripts/check-v36-integration-regression.mjs`
- `frontend/scripts/check-v36-eventlog-windowing.mjs`
- `frontend/scripts/check-v36-timeline-windowing.mjs`
- `frontend/scripts/check-v36-statedelta-windowing.mjs`
- `backend/tests/test_debug_api.py`
- `backend/tests/test_event_log.py`
- `backend/tests/test_state_delta.py`
- `backend/tests/test_timeline_replay.py`
- `backend/tests/test_v35_integration_regression.py`
- `backend/tests/test_v36_integration_regression.py`

## Passed Items

1. StateDelta Viewer is debug-gated.
   `StateDeltaViewerPanel` is rendered inside `DebugGate`, and v3.6 static
   checks assert that placement. The panel labels itself debug-only and states
   that it cannot apply deltas or modify `GameState`.

2. EventLog Viewer normal view shows safe summaries only.
   `EventLogViewerPanel` renders `visibleEvents` through `EventLogSafeCard`.
   Normal rows show event id, turn/time, type, actor safe summary, source
   module, visible summary, tags, and linked StateDelta count. Raw event JSON
   and raw StateDelta payloads are inside `DebugGate`.

3. Timeline Replay normal view does not show raw deltas.
   `TimelineReplayPanel` filters to visible/system-safe replay rows and renders
   `TimelineEventCard` summaries. Raw StateDelta JSON is displayed only in the
   `Timeline Replay Debug Details` area wrapped by `DebugGate`.

4. Debug UI cannot modify `GameState`.
   The reviewed debug UI actions refresh state, load timelines/events, load
   replay views, run debug dry-runs, or inspect summaries. They do not expose a
   direct state edit or apply-delta button.

5. Debug UI cannot apply StateDelta.
   No `/debug/.../apply-delta` route or frontend apply-delta action was found.
   `StateDeltaViewerPanel` only displays recorded rows and redacted values.

6. Debug export requires confirmation.
   `SafeDebugExportWizard` is disabled when `ENABLE_DEBUG_API` is false. Raw
   debug scopes require explicit confirmation before preview/create.

7. Visible vs Debug Compare does not show hidden text full content.
   `VisibleDebugStateCompare` shows counts, safe examples, filtered counts, and
   redacted summaries. Hidden facts, NPC secrets, hidden item properties, quest
   hidden truth, and module internals are summarized rather than printed.

8. EventLog remains the authoritative event record.
   `GameLoop.step` applies deltas through `apply_delta`, then appends the player
   event and system events to `EventLog`. `EventLog` remains append/list/recent
   oriented and enforces monotonic turn ordering.

9. UI cannot delete or modify EventLog.
   No frontend EventLog delete/edit control and no `/debug/.../events` delete,
   patch, or rewrite endpoint were found. The debug UI can delete crash reports,
   which are separate local diagnostic artifacts, not EventLog entries.

10. Replay UI is observe-only.
    Timeline replay controls can start, pause, step, filter, and jump to turns.
    Backend `replay_dry_run` applies deltas to a copied initial state for
    analysis and tests assert the saved timeline is unchanged before/after.

11. Virtualized rendering does not bypass redaction.
    EventLog, Timeline Replay, and StateDelta views render only visible windows:
    `visibleEvents`, `windowedTurns`, and `visibleRows`. Redaction and DebugGate
    wrapping are applied at the row/card layer, not only at the full list layer.

12. Search/filter does not expose hidden/debug data in normal UI.
    EventLog filters use safe event type/actor/module/tag helpers. StateDelta
    search indexes redacted path/event/source metadata and is debug-gated.
    Timeline filters may classify events internally, but normal rendering uses
    safe summary functions.

13. `ENABLE_DEBUG_API=false` disables debug routes or shows disabled state.
    Backend `require_debug_api()` returns `403` when debug is disabled.
    Frontend `DebugGate` shows `ENABLE_DEBUG_API required` and does not render
    children when disabled.

14. Tests cover normal raw delta exclusion.
    `test_timeline_replay.py`, `test_v35_integration_regression.py`, and
    `test_v36_integration_regression.py` assert normal player APIs do not
    return `state_deltas`, debug endpoints are disabled when debug API is off,
    and debug reads do not modify normal state.

## StateDelta Boundary Review

- `StateDelta` remains a typed contract with operation, path, value,
  `caused_by_event_id`, reason, source, metadata, and contract version.
- `apply_delta` clones `GameState` before applying changes and validates model
  field values.
- Stable delta validation rejects forbidden paths such as `debug`,
  `debug_memory`, `raw_env`, `api_key`, and `secrets`, and rejects hidden facts
  being written to `player_visible_facts`.
- v3.6 `StateDeltaViewerPanel` is read-only. It supports op filter, path prefix,
  event filter, turn range, debounced path search, and paged/windowed rows.
- StateDelta values in the UI are summarized by type/shape and rendered through
  `redactDebugText`; raw detail remains within the debug-gated panel.
- No UI action was found that applies, edits, deletes, replays into, or writes
  StateDelta records.

## EventLog Boundary Review

- `Event` still requires `state_deltas` unless `allow_empty_delta` is explicit.
- Player-visible events validate against obvious secret/raw-env markers.
- `EventLog.append` rejects backward turn movement, and list/read helpers return
  copies or filtered views.
- `GameLoop.step` records world-affecting runtime changes as `Event` entries
  after backend rule resolution and `apply_delta`.
- EventLog Viewer normal view shows safe summaries and linked delta counts.
  Raw event JSON is available only through `EventLog Debug Details` inside
  `DebugGate`.
- v3.6 EventLog windowing renders current pages/windows only and does not
  change EventLog persistence semantics.
- No EventLog delete/edit/rewrite route was found in the reviewed debug API.

## Debug Gating Review

- Backend debug endpoints for session events, save events, timeline, graphs,
  modules, NPC simulation, behavior timeline, replay dry-run, and performance
  all call `require_debug_api()`.
- Frontend `DebugGate` suppresses children and shows a disabled state when
  `debugEnabled` is false.
- StateDelta Viewer and Visible vs Debug Compare are inside the main debug gate.
- EventLog and Timeline normal sections are visible as safe-summary tools, but
  their raw details are individually wrapped in `DebugGate`.
- Safe Debug Export is disabled when debug API is off and requires explicit
  confirmation for raw-risk scopes.
- v3.6 route-level lazy loading does not remove the DebugGate checks observed
  in the active QA/Debug UI source and regression checks.

## High-risk Boundary Issues

None found.

No high-risk StateDelta / EventLog / Debug boundary issue blocks v3.6 release.

## Medium-risk Boundary Issues

1. `DebugEventSummary` relies on an outer `DebugGate`.
   The helper renders raw `event.state_deltas`, but reviewed usage places it
   inside the main debug-gated block. This is not a current leak, but future
   reuse should either keep it debug-only or add an internal `DebugGate`.

2. Timeline classification reads debug event metadata internally.
   Combat/social/system filters inspect action types and some StateDelta paths
   for classification. Display remains redacted and safe, but future filters
   should avoid adding hidden text or delta values to normal search indexes.

3. Debug API intentionally returns raw StateDelta when enabled.
   This is expected for debug tools, but it means all new debug consumers must
   keep `ENABLE_DEBUG_API` and UI redaction boundaries intact.

4. Crash report deletion exists under debug UI.
   This does not affect EventLog, StateDelta, or `GameState`, but final release
   checks should continue to distinguish crash-report maintenance from World
   event history mutation.

## Non-blocking Follow-ups

- Rename `DebugEventSummary` or wrap it internally so its debug-only status is
  obvious at the component boundary.
- Add a focused frontend check that verifies every `DebugEventSummary` usage is
  inside an active `DebugGate`.
- Add a browser-level smoke test for debug disabled state after route-level lazy
  loading.
- Add a large fake EventLog fixture to confirm windowed rows still redact raw
  StateDelta details in rendered output, not only by source checks.
- Consider a debug API route inventory check that fails if `/debug/.../events`
  delete/patch/rewrite or `/debug/.../apply-delta` endpoints are introduced
  without an explicit security review.

## Release Decision

v3.6 release is **not blocked** by StateDelta / EventLog / Debug boundary
issues.

Proceed with v3.6 release preparation if the broader performance,
accessibility, privacy/visibility, Provider secret, code review, final freeze,
and release readiness checks remain passing.
