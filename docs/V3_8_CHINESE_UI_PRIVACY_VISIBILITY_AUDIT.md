# v3.8 Chinese UI Privacy / Visibility Audit

Verification date: 2026-05-25

Scope: v3.8 Chinese Product UX Polish UI surfaces, with focus on the Chinese Home, Provider UI, backend-unavailable recovery state, safe error states, Debug / Replay visibility, search/filter safety, mature/private defaults, and Backup / Diagnostics copy.

## Passed Items

1. Chinese Home does not render API keys.
   - The v3.8 Home is product-facing and uses safe project/provider summaries.
   - Static checks cover the Home surface and reject secret-looking `sk-*` tokens and Authorization values.
   - Provider setup copy explicitly says API keys are not shown or saved in project/frontend storage/logs/backup/diagnostics/export.

2. Chinese Home does not render hidden facts.
   - Home copy is limited to mode cards, next steps, local safety summaries, project/demo summaries, and Provider status.
   - No hidden fact text or NPC secret token is rendered by the Home checks.

3. Chinese Home does not render raw `state_deltas`.
   - Home checks explicitly reject `StateDeltaViewerPanel`, raw `state_deltas` JSON rendering, and debug panel surfaces.
   - StateDelta details remain in debug-only surfaces.

4. Provider UI does not display API keys.
   - Provider setup supports env/secret/local secret references and transient test keys, but saved secrets are not displayed.
   - The UI copy warns that API keys do not enter project files, frontend storage, logs, backups, diagnostics, or exports.
   - Model list and capability matrix surfaces display safe metadata only, not raw provider responses.

5. Backend unavailable state does not display raw env.
   - `BackendUnavailableState` presents a Chinese recovery flow with reconnect/start guide/diagnostics/settings actions.
   - The state uses a safe API base URL summary and states that raw env/API keys/hidden facts/raw deltas are not shown.

6. Error states do not show stack traces, secrets, or sensitive paths in normal UI.
   - `AppErrorBoundary` and safe error formatters redact stack traces, raw env, API-key-like content, hidden facts, state deltas, and sensitive path patterns.
   - Normal error UI shows a safe summary plus retry/home/diagnostics guidance.

7. Chinese aria-label text does not contain secrets.
   - Current Chinese labels are descriptive labels for navigation, local safety, provider setup, pagination, and help regions.
   - Static scans did not find real-looking secret values in frontend UI labels.

8. Search/filter does not cache hidden text in normal views.
   - Safe search and filtering use safe summaries/metadata for normal UI surfaces.
   - The safe API cache rejects secrets, hidden facts, NPC secrets, raw prompts/outputs, raw provider responses, raw env, debug data, and mature/private content.
   - Hidden leak report search is limited to safe metadata and does not search hidden text full content.

9. Debug is hidden by default.
   - Home does not default to Debug / Replay / EventLog / StateDelta panels.
   - QA, Debug, Replay, Diagnostics, and authoring/debug surfaces are grouped under Advanced Tools.

10. Debug remains gated.
    - StateDelta Viewer and visible-vs-debug compare are checked to remain inside `DebugGate`.
    - Debug disabled copy references `ENABLE_DEBUG_API`.
    - Normal Home does not expose raw debug panels.

11. Mature/private remains hidden by default.
    - UI copy and settings summaries state mature/private content is default-off and excluded from normal prompts, exports, backups, and diagnostics unless explicitly opted in.
    - Backup/Diagnostics filtering copy includes mature/private exclusion.

12. Backup/Diagnostics Chinese copy correctly describes filtering policy.
    - Backup and diagnostics UI states that API Key, `.env`, Provider secrets, debug raw data, raw `state_deltas`, mature/private content, databases/logs/caches/build outputs are excluded by default.
    - The UI also states local-only/no upload behavior.

13. No account/cloud/marketplace remains negative local-first copy.
    - Chinese local-first copy states no account required, no cloud sync, no online marketplace, and no project upload.
    - The audit did not find account/cloud/marketplace entry points in the checked v3.8 UI surfaces.

## High-risk Issues

None found.

No release-blocking privacy or visibility regression was found for v3.8 Chinese UI surfaces.

## Medium-risk Issues

None blocking.

Residual medium-risk area: this pass used static source inspection and existing regression scripts. It did not include a fresh browser-rendered screenshot audit of every route state. The current automated checks cover the known high-risk surfaces, but a final release freeze can still add a browser smoke pass for the rendered Home, Provider, Backup, Diagnostics, and Debug-disabled states.

## Non-blocking Follow-ups

1. Add a dedicated aria-label scanner that extracts JSX `aria-label` values and checks for key-like strings, hidden fact markers, and sensitive path patterns.
2. Add a rendered browser smoke check for the Chinese Home with backend unavailable and no-project states.
3. Keep v3.8 product UX scripts aligned when component extraction changes Home, Provider, or Advanced Tools markup.
4. Consider a small fixture-based check for normal search indexes to confirm hidden text is not indexed outside authoring/debug contexts.

## Verification Commands and Results

Commands run:

```powershell
cd frontend
npm.cmd run check:v38-product-ux
npm.cmd run check:v38-integration-regression
npm.cmd run check:v38-backend-unavailable
npm.cmd run check:v38-backup-diagnostics-ux
```

Results:

- `check:v38-product-ux`: passed.
- `check:v38-integration-regression`: passed.
- `check:v38-backend-unavailable`: passed.
- `check:v38-backup-diagnostics-ux`: passed.

Previously verified in the v3.8 regression pass:

- `python -m pytest`: passed, `1825 passed`.
- `cd frontend && npm.cmd run build`: passed.
- Frontend check scripts: passed.

## Release Decision

Ready for v3.8 release from the Chinese UI privacy / visibility perspective.

The checked v3.8 Chinese UI surfaces preserve the local-first boundaries: no API key rendering, no hidden fact rendering in normal Home, no raw `state_deltas` in normal UI, Debug remains gated and hidden by default, mature/private remains default-hidden, backup/diagnostics filtering is clearly described in Chinese, and no account/cloud/marketplace entry point was found.
