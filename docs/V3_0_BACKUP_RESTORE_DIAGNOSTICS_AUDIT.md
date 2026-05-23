# v3.0 Backup / Restore / Diagnostics Audit

Verification date: 2026-05-23

Scope reviewed:

- `backend/app/desktop/backup_restore.py`
- `backend/app/desktop/diagnostics_bundle.py`
- `backend/app/desktop/local_logs.py`
- `backend/app/desktop/studio_policy.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `docs/DESKTOP_PACKAGING.md`
- `backend/tests/test_v30_local_studio_services.py`
- `backend/tests/test_v30_integration_regression.py`

## Passed Items

1. Backup dry-run does not write files.
   - `BackupService.create_backup_dry_run` delegates to `create_backup_plan`.
   - The plan lists `would_write_files` and exclusions but does not create the backup directory or zip file.
   - Covered by v3.0 tests that assert the backup directory is absent after dry-run.

2. Backup excludes `.env`.
   - `_default_exclusions` includes `.env`.
   - `DesktopStudioPolicy.validate_backup_bundle` rejects `.env`, `.env.local`, `.env.production`, and unsafe bundle paths.
   - Integration tests create a local `.env` fixture and verify it is not present in the created backup zip.

3. Backup excludes API keys.
   - `_default_exclusions` includes `API key`.
   - Backup validation rejects secret-like content in the manifest.
   - Integration tests assert fake API key fixtures do not appear in backup payloads.

4. Backup excludes provider secrets.
   - `_default_exclusions` includes `provider secrets`.
   - Created backups currently include only manifest and safe summaries, not provider profile bodies or secret stores.

5. Backup excludes mature/private content by default.
   - `BackupCreateRequest.include_mature_private` defaults to `false`.
   - `_default_exclusions` adds `mature/private content` unless explicitly requested.
   - Current backup payload contains safe summaries only.

6. Backup excludes debug-only data by default.
   - `BackupCreateRequest.include_debug` defaults to `false`.
   - `_default_exclusions` adds `debug-only data` unless explicitly requested.

7. Restore dry-run does not write projects.
   - `RestoreService.restore_dry_run` validates the backup and computes conflicts without creating the target folder.
   - Tests assert the target restore folder is absent after dry-run.

8. Restore apply requires confirmation.
   - `RestoreApplyRequest.explicit_confirm` defaults to `false`.
   - `restore_apply_confirmed` raises unless `explicit_confirm=true`.
   - Covered by focused and integration tests.

9. Restore does not overwrite existing projects unless confirmed/allowed.
   - `restore_dry_run` reports `target_project_exists` when the target folder already exists and `allow_overwrite=false`.
   - `restore_apply_confirmed` blocks conflicts unless `allow_overwrite=true`, and still requires `explicit_confirm=true`.

10. Corrupted backup is rejected.
    - Backup validation requires `.zip` extension, an existing file, no forbidden archive members, and `manifest.json`.
    - Integration tests create a zip without `manifest.json` and assert validation fails.

11. Diagnostics preview does not write files.
    - `DiagnosticsBundleService.preview_bundle` builds a manifest and safe payload in memory only.
    - Tests assert `exports/` does not exist after preview.

12. Diagnostics bundle filters secrets.
    - Diagnostics manifest excludes `.env`, API key, provider secrets, raw env, raw prompt/output, database files, and full save files.
    - Created bundle validation runs export bundle policy and redaction detection.
    - Logs included in diagnostics are produced through `LocalLogService` redaction.

13. Diagnostics bundle filters hidden/debug/mature/private by default.
    - Diagnostics manifest excludes hidden facts, NPC secrets, debug memory, raw `state_deltas`, and mature/private content.
    - Debug bundle inclusion requires `include_debug=true`, `explicit_confirm_debug=true`, and `debug_enabled=true`.

14. Log viewer redacts sensitive content.
    - `LocalLogService` reads only `.log` files directly under the allowed local `logs/` directory.
    - `redact_desktop_secret_text` covers API-key-like strings, Authorization headers, raw env, database URLs, raw prompts/outputs, hidden facts, NPC secrets, debug memory, raw `state_deltas`, and mature/private markers.
    - Tests assert fake API keys, database URL credentials, Authorization values, hidden text, and mature/private text do not appear in output.

15. Diagnostics does not upload.
    - Diagnostics bundle creation writes local zip files under `exports/diagnostics/`.
    - No `requests`, `httpx`, remote upload, cloud sync, or telemetry call exists in the diagnostics service.

16. Backup does not cloud sync.
    - Backup creation writes local zip files under the local backup directory.
    - No network upload, cloud provider, account, or sync code is involved.

## High-Risk Issues

None found.

No reviewed backup, restore, diagnostics, or log path uploads data, includes secrets by default, writes during dry-run, or bypasses confirmation for data-changing operations.

## Medium-Risk Issues

1. Restore overwrite has a single confirmation flag plus `allow_overwrite`.
   - Current behavior blocks existing target projects unless `allow_overwrite=true` and `explicit_confirm=true`.
   - This satisfies the current requirement, but a future full restore implementation should use an additional overwrite-specific confirmation token or phrase to prevent accidental destructive restore.

2. Backup and diagnostics are safe-summary prototypes, not full project backup/diagnostic implementations.
   - Current payloads are intentionally narrow and safe.
   - Future expansion to include real project data, saves, or selected mature/private/debug content will need renewed filtering tests and manifest checks.

## Minor Issues

1. Diagnostics bundle validation accepts a caller-provided zip path.
   - It validates zip extension, manifest, forbidden archive paths, and secret content.
   - A formal desktop shell should route file selection through a safe local picker/validate API.

2. Backup/diagnostics output directories are generated locally.
   - `backups/` is ignored, and desktop docs say diagnostics/export outputs must be excluded.
   - Continue verifying `exports/diagnostics/` and any future diagnostics output directory are not staged for release.

3. Backup manifest currently has `contains_mature_private` reflecting the request flag.
   - This is fine for current safe-summary bundles, but future richer backups should also compute this from actual included content.

4. `docs/V3_0_ROADMAP.md` is absent in the current tree.
   - This does not affect backup/restore/diagnostics safety, but it is a planning-document completeness gap.

## Recommendations

1. Before any richer backup format, add manifest-level content inventory, checksums, and per-section privacy classification.
2. Add an overwrite-specific confirmation phrase for future restore flows that can replace or overwrite real project data.
3. Keep diagnostics debug bundle generation behind both `ENABLE_DEBUG_API` and explicit confirmation.
4. Keep backup and diagnostics generated artifacts ignored and excluded from desktop packaging.
5. Add safe local file picker/validator integration before a formal desktop shell exposes arbitrary backup/diagnostics file selection.
6. Continue running:
   - `python -m pytest backend/tests/test_v30_local_studio_services.py backend/tests/test_v30_integration_regression.py`
   - `python -m pytest`
   - `cd frontend && npm.cmd run build`
   - `cd frontend && npm.cmd run check:v30-ux`

## v3.0 Release Blocking Status

Not blocked.

The reviewed v3.0 Backup / Restore / Diagnostics implementation satisfies the current release requirements: dry-runs do not write, backup/diagnostics default to safe redacted summaries, `.env`/API keys/provider secrets/debug-only/mature-private data are excluded by default, restore apply requires confirmation, corrupted backups are rejected, logs are redacted, and there is no upload or cloud sync behavior.
