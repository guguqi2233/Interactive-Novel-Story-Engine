# v3.0 Desktop / Local Privacy Audit

Verification date: 2026-05-23

Scope reviewed:

- `backend/app/desktop/local_studio.py`
- `backend/app/desktop/backup_restore.py`
- `backend/app/desktop/diagnostics_bundle.py`
- `backend/app/desktop/local_logs.py`
- `backend/app/desktop/workspaces.py`
- `backend/app/desktop/studio_policy.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`
- `docs/DESKTOP_PACKAGING.md`
- `README.md`
- v3.0 local studio regression tests

## Passed Items

1. Local-first remains the default direction.
   - The v3.0 desktop surface is described as Local Desktop Studio Polish.
   - `LocalStudioStatus`, backup/restore, logs, diagnostics, and recent projects all expose `local_only=true` style safe summaries.

2. No account system was found.
   - Frontend and packaging docs explicitly state no account is required.
   - No account login or account settings entry appears in the v3.0 desktop UI scope.

3. No cloud sync was found.
   - Startup scripts and UI copy state no cloud sync.
   - Backup/restore and diagnostics are local workflows, not sync workflows.

4. No online marketplace was found.
   - Module/browser and desktop copy state no online marketplace and no remote package auto-download.
   - No marketplace download flow is introduced by the v3.0 desktop polish.

5. No remote package auto-download was found.
   - Desktop docs and UI keep package handling local.
   - No remote registry or auto-download endpoint appears in the reviewed desktop code.

6. No telemetry upload was found.
   - Startup scripts print `no telemetry upload`.
   - Diagnostics bundle generation writes local files under `exports/diagnostics/` and does not upload.

7. API keys remain env/local-secret-resolver only.
   - Provider setup UI uses `api_key_env` and `secret_ref`.
   - Local studio status/config summaries expose only configured counts or booleans.

8. API keys do not enter the frontend as values.
   - The launcher only passes `VITE_API_BASE_URL`.
   - Frontend UI shows `configured`, `not shown`, `api_key_env`, or `secret_ref`, not raw key values.

9. API keys do not enter backup by default.
   - `BackupService` writes only `manifest.json`, `project_safe_summary.json`, and `quality_safe_summary.json`.
   - Backup plan exclusions include `.env`, `API key`, `provider secrets`, logs, cache, build outputs, databases, debug-only data, and mature/private content.
   - Backup validation rejects forbidden files and sensitive manifest text.

10. API keys do not enter diagnostics by default.
    - `DiagnosticsBundleService` includes safe summaries and redacted logs only.
    - Diagnostics excluded sections include `.env`, API key, provider secrets, raw env, raw prompt/output, hidden facts, NPC secrets, debug memory, raw `state_deltas`, mature/private content, database files, and full save files.

11. API keys do not enter log viewer output.
    - `LocalLogService` reads only the allowed local `logs/` directory and applies `redact_desktop_secret_text`.
    - Redaction covers API-key-like strings, Authorization headers, database URLs, raw env, raw prompt/output, hidden/debug/raw state delta markers, and mature/private markers.

12. Mature/private content is excluded by default.
    - Backup default exclusions include mature/private content.
    - Diagnostics default exclusions include mature/private content.
    - Packaging docs state mature/private content must not be packaged by default.

13. Hidden/debug data is excluded by default.
    - Backup excludes debug-only data unless explicitly requested.
    - Diagnostics excludes hidden facts, NPC secrets, debug memory, and raw `state_deltas`.
    - Debug logs require debug-enabled mode.

14. Desktop packaging docs exclude secrets.
    - `docs/DESKTOP_PACKAGING.md` excludes `.env`, API keys, provider secrets, databases, logs, caches, `node_modules`, frontend build output, desktop build output, backups, crash reports, and mature/private content by default.

15. Startup scripts do not print secrets.
    - Scripts state that `LLM_API_KEY` is not read or injected into frontend env.
    - Scripts print `DATABASE_URL configured` rather than the database URL value.
    - Scripts print only `VITE_API_BASE_URL` as frontend configuration.

16. Recent Projects does not store secrets.
    - `RecentProjectEntry` stores workspace id, display name, redacted path, timestamp, optional world id, and status only.
    - `_ensure_safe_recent_entry` rejects entries containing `api_key`, `llm_api_key`, `openai_api_key`, `raw_env`, `sk-`, or `.env`.

17. Local paths are summarized rather than fully exposed in most desktop APIs.
    - Project workspaces expose `path_redacted`.
    - Backup and diagnostics responses use short path summaries.

## High-Risk Privacy Issues

None found.

No reviewed v3.0 desktop path currently uploads data, introduces account/cloud/marketplace behavior, sends secrets to frontend values, or includes secrets in backup/diagnostics/log safe outputs by default.

## Medium-Risk Privacy Issues

None currently blocking.

The reviewed privacy boundaries are covered by deterministic redaction and v3.0 regression tests. The current implementation remains a local polish layer rather than a formal packaged desktop installer, so release hardening should continue to include packaging scans before any distributable bundle is produced.

## Minor Issues

1. Launcher console output shows the local `logs/` directory path.
   - This is acceptable for a local launcher but may reveal a user directory in screenshots or copied console output.
   - It is not a release blocker because logs are local-only and not uploaded.

2. `workspace_id` is derived from a normalized path.
   - `path_redacted` is used for display, and recent project entries reject secret-like tokens, but the id can still encode some path shape.
   - This is acceptable for local-only state but should be revisited before any future share/export/sync surface.

3. Diagnostics bundle creation writes local files under `exports/diagnostics/`.
   - The bundle is redacted and local-only, but generated diagnostic artifacts should remain ignored by git and excluded from desktop bundles.

4. `docs/V3_0_ROADMAP.md` is not present in the current tree.
   - This is a planning/documentation completeness gap, not a privacy blocker for the reviewed implementation.

## Recommendations

1. Keep `exports/diagnostics/`, `logs/`, `backups/`, crash reports, databases, caches, `frontend/dist`, and desktop build outputs ignored and excluded from packaging.
2. Before v3.0 release, run `git ls-files` scans for `.env`, database files, logs, backups, diagnostics bundles, crash reports, `node_modules`, `frontend/dist`, and desktop build outputs.
3. Consider shortening launcher console path output further in a future UI polish slice if users often share terminal screenshots.
4. Consider replacing path-derived `workspace_id` with a random local id in a future persistence-focused slice, especially before any future share/export/sync feature.
5. Keep diagnostics and debug exports explicit-confirm only, debug-gated, and redacted.
6. Keep provider setup limited to `api_key_env` / `secret_ref`; do not add plaintext API key fields to frontend forms.

## v3.0 Release Blocking Status

Not blocked.

The reviewed v3.0 Desktop / Local Privacy surface satisfies the local-first privacy requirements: no account, no cloud sync, no online marketplace, no remote package auto-download, no telemetry upload, no secret values in frontend/backup/diagnostics/log safe views, and mature/private/hidden/debug data excluded by default.
