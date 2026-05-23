# v3.0 Desktop Security / Secrets Audit

Verification date: 2026-05-23

Scope reviewed:

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v30-local-studio-ux.mjs`
- `backend/app/desktop/studio_policy.py`
- `backend/app/desktop/local_studio.py`
- `backend/app/desktop/local_config.py`
- `backend/app/desktop/workspaces.py`
- `backend/app/desktop/backup_restore.py`
- `backend/app/desktop/diagnostics_bundle.py`
- `backend/app/desktop/local_logs.py`
- `backend/app/desktop/recovery.py`
- `backend/app/desktop/startup_diagnostics.py`
- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`
- `.gitignore`
- `docs/DESKTOP_PACKAGING.md`
- v3.0 desktop/local studio tests and regression checks

## Passed Items

1. Frontend does not display API key values.
   - Provider and settings UI display `configured`, `not shown`, `api_key_env`, or `secret_ref`.
   - The Provider Setup Wizard copy explicitly says there is no plaintext API key field.
   - Static v3.0 UI checks reject `<input name="api_key">` style fields.

2. Desktop launcher does not inject API keys into frontend env.
   - Windows and shell launchers pass only `VITE_API_BASE_URL` to the frontend process.
   - `docs/DESKTOP_PACKAGING.md` requires that frontend build artifacts do not contain `.env`, `LLM_API_KEY`, `OPENAI_API_KEY`, Authorization headers, raw prompts, or raw env dumps.

3. Startup scripts do not print raw env.
   - Scripts print `DATABASE_URL configured` rather than the value.
   - Scripts state that `LLM_API_KEY` is not read, printed, logged, or injected into frontend env.
   - Scripts print local-only reminders and no account/cloud/marketplace/telemetry copy.

4. Config wizard does not display raw env.
   - `LocalConfigManager` returns safe booleans, status entries, and redacted path hints.
   - UI copy states raw env, API keys, and database connection strings are not shown.

5. Provider wizard does not allow plaintext `api_key` input.
   - Frontend provider draft supports `api_key_env` and `secret_ref`.
   - The wizard does not provide a raw `api_key` field.
   - Placeholder `OPENAI_API_KEY` is an env var name, not a key value.

6. Backup does not include `.env` or API keys by default.
   - Backup plan exclusions include `.env`, `API key`, provider secrets, logs, cache, `node_modules`, `frontend/dist`, desktop build outputs, databases, debug-only data, and mature/private content.
   - Created backups currently contain only `manifest.json`, `project_safe_summary.json`, and `quality_safe_summary.json`.
   - Backup validation rejects forbidden file names, forbidden suffixes, executable payloads, forbidden directories, unsafe paths, and sensitive manifest text.

7. Restore does not restore secrets from current backup format.
   - Restore validates backup manifest first.
   - Restore apply requires `explicit_confirm`.
   - Current restore writes a safe marker file into a local restored-project folder rather than importing raw project secrets.

8. Diagnostics bundle does not include secrets by default.
   - Diagnostics manifest excludes `.env`, API key, provider secrets, raw env, raw prompt/output, hidden facts, NPC secrets, debug memory, raw `state_deltas`, mature/private content, database files, and full save files.
   - Created diagnostics bundle is validated with export bundle policy and redaction checks.

9. Logs are redacted.
   - `LocalLogService` reads only `.log` files immediately under the allowed `logs/` directory.
   - Redaction covers `sk-...` style keys, `LLM_API_KEY`, `OPENAI_API_KEY`, generic API key/secret/token/password values, Authorization headers, database URLs, raw env, raw prompt/output, hidden facts, NPC secrets, debug memory, raw `state_deltas`, and mature/private markers.
   - Debug logs require debug-enabled mode.

10. Error Recovery does not display sensitive paths or secrets.
    - Recovery issues are deterministic safe summaries.
    - Recovery plan summaries pass through `redact_desktop_secret_text`.
    - Recovery apply requires explicit confirmation and destructive recovery remains blocked.

11. Desktop packaging docs exclude `.env`.
    - `.env` is listed in git ignore expectations, packaging safety checklist, backup/diagnostics/log/crash report boundaries, and final packaging gate.

12. Desktop packaging docs exclude db/log/cache/node_modules/dist outputs.
    - `docs/DESKTOP_PACKAGING.md` excludes database files, logs, crash reports, backups, caches, `node_modules`, `frontend/dist`, desktop build outputs, installer outputs, and common desktop target directories.

13. `.gitignore` covers generated and sensitive artifacts.
    - `.env`, `frontend/.env`, database files, SQLite files, logs, caches, crash reports, backups, `node_modules`, `dist`, `frontend/dist`, desktop build outputs, installers, and common installer artifacts are ignored.

14. Tests/docs `sk-...` hits are fake or redaction fixtures.
    - Search hits are concentrated in tests and security/audit docs with explicit fake fixture language such as `sk-test-*`, `sk-real-looking-*`, `sk-real-not-allowed-*`, and deliberate redaction/import rejection cases.
    - No production source path reviewed contains a real API key value.

15. Debug export requires explicit confirmation.
    - Diagnostics debug bundle only becomes active when `include_debug`, `explicit_confirm_debug`, and `debug_enabled` are all true.
    - Logs also require debug-enabled mode for debug inclusion.

16. Local file path validation rejects obvious traversal and unsafe targets.
    - Workspace paths reject `..`, `.env`, and `node_modules`.
    - New workspace paths also reject `dist`, logs, cache, and `__pycache__`.
    - Backup target directory must stay inside the local workspace and rejects `.env`, `node_modules`, frontend/dist, logs, and cache components.
    - Bundle validation rejects archive paths containing `..` or absolute paths.

## High-Risk Issues

None found.

No reviewed v3.0 desktop path exposes API keys in frontend values, injects API keys into `VITE_` env, packages `.env`, stores secrets in Recent Projects, writes secrets to backup/diagnostics/log safe outputs, or introduces account/cloud/marketplace/telemetry behavior.

## Medium-Risk Issues

1. PowerShell launcher embeds `DATABASE_URL` in the backend child command string.
   - The script does not print the value and does not pass it to the frontend.
   - However, command-line process inspection on the local machine may reveal a database URL/path while the backend process is running.
   - This is not an API key leak and is local-only, but it is a desktop hardening candidate.

2. Restore and diagnostics validation accept user-provided absolute zip paths.
   - Backup restore validation and diagnostics validation inspect zip files selected by path.
   - They validate extension, manifest, forbidden archive paths, and sensitive content, and they do not upload data.
   - Still, future desktop file picker integration should constrain paths through a safe picker/validate API to reduce accidental broad local reads.

## Minor Issues

1. Startup scripts print the full local `logs/` directory path.
   - This can reveal user directory structure in terminal screenshots.
   - It is local-only and not uploaded, so it is not a release blocker.

2. `workspace_id` is derived from a normalized path.
   - Display uses `path_redacted`, and recent project entries reject secret-like content.
   - Before any future sync/share feature, consider switching to random local ids.

3. README and historical audit docs contain many security-key keywords.
   - These are placeholders, empty `.env.example` style values, or historical fake redaction fixtures.
   - Release scans should continue distinguishing fake fixtures from real secrets.

4. `docs/V3_0_ROADMAP.md` is absent in the current tree.
   - This is a planning/documentation gap, not a secrets blocker for the reviewed code.

## Recommendations

1. In a future launcher hardening slice, prefer setting backend environment variables through process environment rather than interpolating `DATABASE_URL` into a PowerShell command string.
2. Add a safe local file picker / validate endpoint before allowing broad restore or diagnostics bundle path selection in a formal desktop shell.
3. Keep `frontend/scripts/check-v30-local-studio-ux.mjs` in the release checklist and extend it if additional desktop pages are added.
4. Keep `python -m pytest`, `npm.cmd run build`, and `npm.cmd run check:v30-ux` as mandatory v3.0 release checks.
5. Before tagging v3.0, run `git ls-files` and secret scans for `.env`, database files, logs, caches, backups, diagnostics bundles, crash reports, `node_modules`, `frontend/dist`, desktop build outputs, and real-looking API keys.
6. Keep debug bundle generation gated by both `ENABLE_DEBUG_API` and explicit user confirmation.
7. Keep provider setup limited to env references and local secret references; do not add plaintext key entry fields.

## v3.0 Release Blocking Status

Not blocked.

The reviewed v3.0 Desktop Security / Secrets posture is acceptable for release: no high-risk secret exposure was found, default backup/diagnostics/log/recent-project flows are secret-safe, desktop packaging docs exclude generated and sensitive artifacts, debug export is explicit-confirm and gated, and path traversal protections exist for workspaces, backup targets, and archive contents. The medium-risk items are local hardening follow-ups, not release blockers.
