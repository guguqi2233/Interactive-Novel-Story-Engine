# v2.9 UI Privacy / Visibility Audit

## Verdict

Pass with no release-blocking UI privacy or visibility leak found.

This audit reviewed the v2.9 Local UI / UX Foundation frontend surfaces, API client hardening, static UI safety checks, and v2.9 regression tests. The reviewed implementation keeps the UI local-first, does not introduce account/cloud/marketplace entry points, and does not expand frontend authority over `GameState`, provider secrets, hidden facts, mature/private memory, or debug payloads.

## Scope Reviewed

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v29-ui-safety.mjs`
- `backend/tests/test_v29_ui_regression.py`
- `docs/V2_9_ROADMAP.md`
- `docs/V2_9_LOCAL_APP_SHELL_REVIEW.md`

## Passed Items

1. **Frontend API key display**
   - Provider setup uses `api_key_env` and `secret_ref`.
   - No plaintext `api_key` input field is present.
   - UI status cards show configured/not configured states, not key values.
   - `check:v29-ui` and `test_v29_provider_setup_has_no_plaintext_api_key_field` cover this.

2. **Raw env display**
   - Settings, Provider, and Prompt Lab copy explicitly state raw env is not displayed.
   - `SafeJSON` redacts keys containing `raw_env`.
   - `sanitizeDisplayError` and API client redaction cover raw env style error text.

3. **Provider secrets**
   - Provider status is rendered through `SafeJSON`.
   - `redactDebugText` redacts keys containing `api_key` or `secret`.
   - `api.ts` redacts `Authorization`, key-like, token-like, password-like, and secret-like error fragments.

4. **Sensitive paths in error states**
   - `ErrorPanel` uses `sanitizeDisplayError`.
   - `api.ts` uses `getErrorMessageSafe` and redacts Windows local paths plus common sensitive Unix-style paths.
   - v2.9 regression tests assert path and stack redaction support.

5. **Hidden facts in normal UI**
   - Normal Novel, Tavern, Project Home, World, Quality, and Cross-Mode surfaces use safe summary copy.
   - UI text explicitly says hidden facts are excluded from normal views.
   - No normal landing page renders hidden fact bodies.

6. **NPC secrets in normal UI**
   - Tavern and Multi-NPC UI copy states NPC secrets are not shown.
   - World landing only displays visible location, visible NPC count, visible quest count, and safe summaries.

7. **Debug memory in normal UI**
   - Diagnostics export defaults to safe summaries and lists debug memory as filtered.
   - Debug export requires explicit confirmation and `ENABLE_DEBUG_API`.

8. **Raw `state_deltas` in normal UI**
   - Normal Project Home, Cross-Mode Dashboard, World landing, Quality Dashboard, Diagnostics export, and Prompt Lab copy exclude raw `state_deltas`.
   - Raw `state_deltas` renderings remain in debug/replay-oriented sections.
   - `check:v29-ui` ties raw `state_deltas` copy to Debug / Replay guidance.

9. **Mature/private content default hidden**
   - Mature settings display disabled/default-off behavior.
   - Diagnostics export and privacy notices list mature/private content as filtered by default.
   - v2.9 tests assert mature/private default hiding text.

10. **Diagnostics export filtering**
    - `DiagnosticsExportPanel` builds a frontend-only safe JSON preview.
    - Default filters include API key, `.env`, provider secrets, hidden facts, mature/private content, debug memory, and raw `state_deltas`.
    - Debug export requires explicit confirmation and debug API enabled.

11. **Export UI filtering strategy**
    - Settings / Privacy and diagnostics panels explain export filtering.
    - Existing export surfaces continue using safe local summaries and do not add online upload behavior.

12. **Debug / Replay gating**
    - Unified navigation shows Debug / Replay as enabled or gated.
    - Debug export explains `ENABLE_DEBUG_API`.
    - Debug data remains dependent on debug API availability.

13. **Provider UI safe references**
    - Provider setup supports `openai`, `openai_compatible`, `local_http`, `relay`, `mock`, and `local_stub`.
    - Key handling is limited to `api_key_env` / `secret_ref`.
    - The UI explicitly states it has no plaintext API key field.

14. **Module Browser permissions**
    - Module Browser displays dangerous permission summaries and risk badges.
    - It preserves local-only/no-marketplace/no-download/no-code-execution messaging.
    - It does not render provider secrets or package execution output.

15. **Quality Dashboard normal view**
    - Quality Dashboard shows overall status, blocker/warning counts, category summaries, and safe issue guidance.
    - It explicitly avoids hidden facts, NPC secrets, debug memory, raw env, API keys, and raw `state_deltas`.

16. **Cross-Mode Dashboard normal view**
    - Dashboard shows draft/proposal/conflict/link counts and safe lanes.
    - Hidden target risks are displayed as counts, not hidden target details.
    - World-to-Novel preview uses `SafeJSON`.

## High-Risk UI Leaks

None found.

No evidence was found that v2.9 normal frontend surfaces display API keys, provider secrets, raw env values, hidden facts, NPC secrets, mature/private memory, debug memory, or raw `state_deltas`.

## Medium-Risk UI Leaks

None blocking.

The following are residual design risks rather than confirmed leaks:

- Some debug/replay panels can display raw `state_deltas` once debug data is available. This is acceptable under the existing debug model, but future UI polish should continue making the gated/debug-only nature visually unmistakable.
- `safe_path_hint` may appear in Module Browser summaries. The field is intended to be safe, but future hardening should continue ensuring the backend never sends full sensitive local paths through this field.
- `SafeJSON` redacts common secret/text keys, but it is still a generic renderer. Normal UI should keep using purpose-built summaries where possible instead of growing new generic JSON previews.

## Low-Risk Issues

- Debug panel defaults and placement can still feel prominent for a local UX foundation. This is a usability concern, not a privacy blocker, because debug API access is gated by backend configuration.
- Some normal UI copy mentions hidden facts and raw `state_deltas` as exclusions. This is useful safety messaging, but future copy should avoid making debug concepts noisy for non-technical users.
- The frontend remains monolithic. That does not create a direct privacy leak, but it makes future privacy review harder unless shared safe components keep expanding.

## Recommendations

1. Keep `npm.cmd run check:v29-ui` in the v2.9 release checklist.
2. Keep `backend/tests/test_v29_ui_regression.py` as the regression anchor for UI privacy/visibility boundaries.
3. Prefer purpose-built safe summary cards over raw JSON previews in all new normal UI.
4. Consider default-collapsing debug-heavy panels in a later UI polish slice while preserving explicit debug access.
5. Add future static checks for full local path patterns in module browser/display strings if more path-like fields are surfaced.

## Release Blocking Assessment

Not blocking v2.9 release.

The reviewed UI changes preserve the local-first privacy model, keep normal views safe, keep Provider secrets out of frontend display, gate debug/replay, and keep mature/private content default-hidden. No high-risk privacy or visibility blocker was found.
