# v3.5 QA / Debug Privacy / Visibility Audit

## Audit Scope

This audit reviews v3.5 Local QA / Debug / Replay & Provider Connectivity UI Pro
privacy and visibility boundaries. It covers:

- Normal QA surfaces in `frontend/src/App.tsx`.
- Timeline Replay UI Pro.
- EventLog Viewer Pro.
- StateDelta Viewer Pro.
- Visible vs Debug State Compare.
- Hidden Leak Report UI Pro.
- Playtest Dashboard Pro.
- Quality Gate Unified Dashboard Pro.
- Diagnostics Bundle Review UI.
- Safe Debug Export Wizard.
- Shared DebugGate and QA/debug safety components.
- v3.5 provider/debug/privacy regression tests and static check script.

The audit is read-only with respect to business code. It verifies that normal
UI surfaces remain safe-summary based, while raw debug details remain gated by
`ENABLE_DEBUG_API`.

## Passed Checks

1. Normal QA UI does not display hidden facts.
   - Normal QA, quality, playtest, diagnostics, and provider panels use safe
     summaries and explicit copy stating hidden facts are excluded.
   - Hidden leak report issue rows use safe summaries and suggested actions
     rather than hidden text bodies.

2. Normal QA UI does not display NPC secrets.
   - Visible-state and QA copy explicitly excludes NPC secrets and
     `npc_knowledge`.
   - Cross-mode and hidden leak review panels describe hidden target details as
     redacted.

3. Normal QA UI does not display debug memory.
   - Diagnostics, export, and quality panels list debug memory in excluded or
     gated categories.
   - Debug memory is not surfaced as a normal QA report payload.

4. Normal QA UI does not display raw `state_deltas`.
   - Normal surfaces show counts, safe summaries, or risk labels.
   - Raw delta JSON rendering is kept in debug-oriented components and
     DebugGate-wrapped details.

5. StateDelta Viewer is debug-gated.
   - `StateDeltaViewerPanel` is rendered inside the debug area and includes
     `ENABLE_DEBUG_API required` copy.
   - It is read-only and does not expose an apply path.

6. Visible vs Debug Compare is debug-gated.
   - `VisibleDebugStateCompare` is in the debug tab area and marks the compare
     as a debug-gated boundary check.
   - Hidden text is summarized/redacted rather than printed by default.

7. Timeline Replay normal view does not display hidden/debug events by default.
   - Timeline replay cards show safe summary, type, actor, turn/time, and counts.
   - Debug StateDelta details are inside `DebugGate`.

8. EventLog Viewer normal view does not display raw JSON.
   - Event rows show event id, turn/time, type, actor safe summary, visible
     summary, and linked StateDelta count.
   - Raw event JSON and StateDelta details are under DebugGate.

9. Hidden Leak Report does not print hidden text full bodies.
   - Report rows are safe summaries with severity, source, target, and suggested
     action.
   - Sensitive marker detection is used to identify risk without rendering the
     hidden source text.

10. Quality Dashboard does not print hidden text full bodies.
    - Unified quality rows show blocker/error/warning counts and safe next
      actions.
    - Hidden facts are referenced as excluded/redacted, not printed.

11. Playtest reports do not display hidden details in normal view.
    - Playtest dashboard uses pass/fail, duration, coverage, failed step, and
      safe replay summary style fields.
    - Raw debug-only details remain excluded from normal report surfaces.

12. Diagnostics preview does not display secrets.
    - Diagnostics Bundle Review UI lists included safe sections and excluded
      sections such as `.env`, API keys, provider secrets, raw env, raw
      prompt/output, hidden facts, NPC secrets, debug memory, raw
      `state_deltas`, mature/private content, and database files.
    - Backend diagnostics redaction tests cover provider raw response and
      Authorization-like data.

13. Debug export defaults are safe.
    - Safe Debug Export Wizard starts from safe summaries and requires explicit
      confirmation for debug/raw export scopes.
    - It states that API keys, raw env, and provider secrets are excluded.

14. Debug UI is controlled by `ENABLE_DEBUG_API`.
    - `DebugGate` and disabled states clearly state `ENABLE_DEBUG_API required`.
    - Debug API endpoints are backend-gated through `require_debug_api()`.
    - v3.5 integration regression verifies debug endpoints return 403 when
      debug is disabled.

15. ErrorState avoids sensitive path exposure.
    - Existing frontend error handling redacts secret-like values and sensitive
      local path shapes.
    - Safe path summaries are used for user-facing local path display.

## High-Risk UI Leaks

No high-risk QA / Debug privacy or visibility leak was found.

No blocker was found for:

- hidden facts in normal QA UI;
- NPC secrets in normal QA UI;
- debug memory in normal QA UI;
- raw `state_deltas` outside DebugGate;
- API keys or provider secrets in diagnostics/debug export UI;
- debug UI bypassing `ENABLE_DEBUG_API`.

## Medium-Risk UI Leaks

No medium-risk release-blocking leak was found.

Medium-risk areas to keep under regression coverage:

- Raw EventLog / StateDelta JSON is intentionally available in debug views.
  This is acceptable only while those render paths remain under DebugGate and
  backend `ENABLE_DEBUG_API`.
- Visible vs Debug Compare uses debug event/delta counts and redacted summaries.
  Future edits must not turn those summaries into full hidden text output.
- Diagnostics and debug export are powerful local tools. Future raw-debug
  export additions must preserve explicit confirm and secret filtering.

## Low-Risk Issues

- Some QA/Debug safety copy is distributed across large monolithic frontend
  sections. The v3.5 component cleanup and static check reduce this risk, but a
  future v3.6 pass should continue extracting shared safe report components.
- Frontend build still reports a large chunk warning. This is a performance
  polish item, not a privacy or visibility blocker.
- EventLog and Timeline surfaces rely on static checks plus tests to keep raw
  details gated. This is acceptable for v3.5 but should remain part of release
  checks.

## Fix Recommendations

No release-blocking fix is required for v3.5.

Recommended non-blocking follow-ups:

- Keep `frontend/scripts/check-v35-qa-debug-provider-ui.mjs` in the release
  checklist.
- Add future component-level tests if the frontend test stack grows beyond
  static smoke checks.
- Continue consolidating raw debug rendering into `StateDeltaViewerPanel` and
  shared debug-only components.
- Keep diagnostics and safe debug export redaction tests updated whenever new
  debug scopes are introduced.

## Release Decision

Not blocked.

v3.5 can proceed toward release readiness from the QA / Debug privacy and
visibility perspective, assuming `python -m pytest`, frontend build, and the
v3.5 QA/Debug/Provider UI regression check remain passing.
