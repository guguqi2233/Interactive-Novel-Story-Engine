# v3.0 Release Notes

## 1. Version Name

v3.0 - Local Desktop Studio Polish

## 2. Version Goal

v3.0 polishes AI Narrative Studio as a local-first desktop/studio workflow. It
improves startup visibility, project selection, local configuration, provider
setup, health checks, quality entry points, backup/restore, recovery, logs,
diagnostics, offline help, settings, and local safety messaging.

v3.0 is not an online platform release. It does not add accounts, cloud sync,
online marketplaces, remote package auto-download, telemetry upload, online
diagnostics upload, or a complete commercial installer.

## 3. New Local Desktop UX Capabilities

- Local Launcher / Startup Status panel.
- Project Picker and Recent Projects.
- Local Config Wizard.
- Provider Setup Wizard.
- Backend Health Check UI.
- One-click Quality Gate entry.
- Backup / Restore Wizard UI.
- Error Recovery Wizard UI.
- Local Log Viewer.
- Local Diagnostics Bundle UI.
- Offline Help Center.
- Desktop Settings / Preferences polish.
- Safe local path summaries.
- First-run onboarding flow.
- v3.0 desktop smoke, UX, and integration regression checks.

## 4. Behavior Changes

- Local desktop surfaces now prefer safe summaries over raw details.
- Backup and restore flows are dry-run first.
- Backup creation and restore apply require explicit confirmation.
- Diagnostics preview does not write files.
- Diagnostics bundle creation writes local redacted bundles only.
- Logs are displayed through a redacted safe-log layer.
- Recent project references store safe summaries, not secrets.
- Desktop and UI surfaces continue to avoid direct `GameState` mutation.

## 5. Frontend Changes

- Added Local Launcher / Startup Status UI.
- Added Project Picker / Recent Projects UI.
- Added Local Config Wizard and Provider Setup Wizard.
- Added Health Check and One-click Quality Gate desktop entry points.
- Added Backup / Restore Wizard and Error Recovery Wizard.
- Added Local Log Viewer and Diagnostics Bundle panels.
- Added Offline Help Center, desktop settings sections, safe path display, and
  first-run onboarding.
- Added `npm.cmd run check:v30-ux` static safety check for v3.0 local desktop
  UI surfaces.

The frontend still does not show API key values, raw env, provider secrets,
hidden facts, mature/private content, or raw `state_deltas` in normal views.

## 6. Backend API Changes

New local desktop safe-summary APIs:

```text
GET  /local-studio/status
GET  /local-studio/health
GET  /local-studio/config-summary
GET  /local-studio/startup-checks
GET  /local-studio/recent-errors
```

New local backup/restore APIs:

```text
POST /local-studio/backups/dry-run
POST /local-studio/backups
GET  /local-studio/backups
POST /local-studio/restore/dry-run
POST /local-studio/restore/apply
```

New local recovery APIs:

```text
GET  /local-studio/recovery/issues
POST /local-studio/recovery/plan
POST /local-studio/recovery/dry-run
POST /local-studio/recovery/apply
```

New local logs and diagnostics APIs:

```text
GET  /local-studio/logs
GET  /local-studio/logs/recent
POST /local-studio/diagnostics/preview
POST /local-studio/diagnostics
POST /local-studio/diagnostics/validate
```

All v3.0 local desktop APIs are local safe-summary or dry-run/confirmed-apply
surfaces. They are not cloud APIs and do not upload data.

## 7. Startup Script Changes

- Windows and shell launchers include clearer help and safety text.
- Startup scripts include dependency, `.env` presence, port, local-only, and
  frontend env guidance.
- The frontend receives only `VITE_API_BASE_URL`.
- Startup scripts do not print API keys or raw env.
- Startup scripts do not modify `GameState`, saves, databases, worlds, or
  content packs.

## 8. Project Picker / Recent Projects Changes

- Added local workspace/project picker surfaces.
- Added bounded Recent Projects service and UI summaries.
- Recent entries store safe project id/name, redacted path summary, last opened
  time, optional last world/mode hint, and health status.
- Recent entries reject secret-like content and do not store API keys, raw env,
  `.env` contents, or raw `GameState`.

## 9. Config / Provider Wizard Changes

- Local Config Wizard shows safe status for database, provider profiles, debug,
  authoring, module, and quality APIs.
- Provider Setup Wizard guides provider type, display/model/base URL metadata,
  allowed modes, and dry-run validation.
- Provider credentials are referenced through `api_key_env` or `secret_ref`.
- v3.0 does not add a plaintext API key input field.

## 10. Health Check / Quality Gate Changes

- Backend Health Check UI shows safe backend, database, project repository,
  provider gateway, quality, debug, and authoring status.
- One-click Quality Gate UI provides local quality gate entry and scope
  selection.
- Quality output remains safe-summary oriented and does not upload reports.

## 11. Backup / Restore Changes

- Added `BackupManifest`, `BackupPlan`, `BackupService`, and `RestoreService`.
- Backup dry-run does not write files.
- Backup creation requires explicit confirmation.
- Backup defaults exclude `.env`, API keys, provider secrets, logs, cache,
  `node_modules`, `frontend/dist`, desktop build outputs, databases,
  debug-only data, and mature/private content.
- Restore dry-run does not write project folders.
- Restore apply requires explicit confirmation.
- Existing target conflicts block restore apply unless overwrite is explicitly
  allowed.
- Corrupted backup files without a manifest are rejected.

## 12. Error Recovery / Logs / Diagnostics Changes

- Added `RecoveryIssue`, `RecoveryPlan`, and `RecoveryService` for local
  deterministic recovery suggestions.
- Destructive recovery remains blocked.
- Added `SafeLogEntry` and `LocalLogService` for redacted local log viewing.
- Added `DiagnosticsBundleManifest` and `DiagnosticsBundleService` for local
  diagnostics preview/create/validate.
- Diagnostics default exclusions include `.env`, API keys, provider secrets,
  raw env, raw prompt/output, hidden facts, NPC secrets, debug memory, raw
  `state_deltas`, mature/private content, database files, and full save files.
- Diagnostics bundles are local files under `exports/diagnostics/`; they are
  not uploaded.

## 13. Offline Help / Settings Changes

- Added local Offline Help Center topics for getting started, local-first
  workflow, modes, Cross-Mode, Provider setup, Mods, Quality Gate,
  Backup/Restore, Diagnostics/Logs, Privacy/Secrets, and Mature default-off
  behavior.
- Settings / Preferences now organize General, Local Privacy, Providers,
  Export, Debug, Backup / Restore, Diagnostics, Mature Module, UI Preferences,
  and Quality Gate.
- Settings do not include account, cloud sync, or online marketplace sections.

## 14. Desktop Packaging Docs Changes

- `docs/DESKTOP_PACKAGING.md` now documents v3.0 local desktop positioning.
- The docs clarify what is packaged and what must not be packaged.
- Required exclusions include `.env`, API keys, local secret store material,
  database files unless explicitly intended, logs, caches, `node_modules`,
  `frontend/dist`, desktop build outputs, debug reports, mature/private
  content, backups unless explicit, and crash reports unless redacted.
- The docs explicitly state that v3.0 does not provide a formal installer,
  code signing, automatic updates, account login, cloud sync, online
  marketplace, telemetry upload, or online platform behavior.

## 15. Known Limitations

- `docs/V3_0_ROADMAP.md` is not present in the current tree. v3.0 acceptance is
  based on AGENTS.md, README, SPEC/WORLD_ENGINE/LLM_PROTOCOL, the
  implementation plan, current code, v3.0 contract review, v3.0 audits, and
  v3.0 tests.
- v3.0 is not a complete commercial desktop installer.
- No signed installer, Tauri/Electron shell, auto-updater, or platform-specific
  packaged app is included.
- Backup / Restore and Diagnostics are safe-summary first; future richer
  project backup formats need expanded manifests, checksums, and tests.
- Restore overwrite currently uses `allow_overwrite` plus `explicit_confirm`;
  future full restore should add overwrite-specific confirmation.
- PowerShell launcher command construction can be further hardened so
  `DATABASE_URL` is not interpolated into a child command string.
- Restore and diagnostics validation can inspect user-provided zip paths;
  future desktop shells should add a safe native file picker / path validation
  flow.
- `workspace_id` is currently path-derived, though display uses redacted path
  summaries.

## 16. Upgrade Notes From v2.9

- Run backend tests and frontend build after pulling v3.0 changes:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

- Optional v3.0-focused checks:

```powershell
python -m pytest backend/tests/test_v30_local_studio_services.py
python -m pytest backend/tests/test_v30_integration_regression.py
cd frontend
npm.cmd run check:v30-ux
```

- Review `.env.example` for v3.0 local desktop comments. Do not put real API
  keys in committed files.
- Keep generated `logs/`, `backups/`, `exports/diagnostics/`, crash reports,
  databases, caches, `node_modules`, `frontend/dist`, and desktop build outputs
  ignored and out of release bundles.
- Continue using `api_key_env` or `secret_ref` for provider profiles.
- v3.0 does not require account setup, cloud sync, online marketplace access,
  or remote package download.

## 17. Recommended v3.1 Direction

Recommended v3.1 direction: Novel Studio UI Pro.

Suggested priorities:

- Improve manuscript, outline, chapter, scene, character arc, plot thread,
  foreshadowing, export, and World -> Novel draft workflows.
- Preserve v3.0 local desktop safety boundaries.
- Continue avoiding account, cloud sync, online marketplace, remote package
  auto-download, and online platform scope.
- Keep Provider Gateway, visibility, backup, diagnostics, export, `StateDelta`,
  and `EventLog` boundaries intact.
