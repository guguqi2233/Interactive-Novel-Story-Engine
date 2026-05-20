# v1.7 Release Notes: Polished Desktop Studio

## 1. Version Name

v1.7: Polished Desktop Studio

This release turns the local engine into a more comfortable desktop-style studio prototype while preserving the same world authority boundary established in v1.0 through v1.6.

It is a local personal studio prototype. It is not a formal public installer, not a signed desktop application, not an auto-updater, not a cloud-sync product, and not an account-based service.

## 2. Version Goal

The v1.7 goal is to make local startup, workspace selection, safe configuration inspection, diagnostics, crash report review, update notes, workspace templates, and packaging safety easier to use without changing the world engine model.

The desktop layer is a convenience shell around the backend API and frontend UI. It does not become a second engine, a privileged state editor, a secret store, or an LLM authority layer.

## 3. New Features

- Desktop Studio Boundary Contract in `docs/DESKTOP_STUDIO_BOUNDARY.md`.
- Desktop packaging safety checklist in `docs/DESKTOP_PACKAGING.md`.
- Safer launcher scripts:
  - `scripts/start_local_studio.ps1`
  - `scripts/start_local_studio.sh`
- Startup diagnostics CLI:
  - `python -m backend.app.tools.startup_diagnostics`
- Project selector APIs and UI for local workspaces.
- Recent projects APIs and UI.
- Local config safe summary APIs and UI.
- Local update notes index and UI.
- Desktop health check APIs and UI.
- Workspace templates for creating local starter workspaces.
- Crash report local viewer behind debug API.
- Desktop settings/status panels in the frontend.
- `.gitignore` hardening for local secrets, logs, backups, crash reports, caches, databases, frontend build output, and desktop build outputs.
- v1.7 focused and integration tests.

## 4. Behavior Changes

- Desktop startup now has clearer preflight diagnostics for Python, Node/npm, dependency availability, ports, `.env` presence, database path accessibility, workspace status, frontend build presence, and crash report count.
- Launcher scripts write local logs under ignored `logs/`.
- Launcher scripts pass only safe frontend configuration such as `VITE_API_BASE_URL`; they do not inject API keys into frontend environment variables.
- Local config summaries now expose whether secrets are configured as booleans and safe labels only.
- Workspace paths and recent project paths are redacted before reaching normal frontend views.
- Crash reports are local-only and redacted by default.
- Backup/export policy rejects secrets, generated local outputs, databases, logs, caches, executable/script files, absolute paths, and path traversal candidates.

## 5. API Changes

New or expanded local studio APIs include:

- `GET /studio/config/summary`
- `GET /studio/config/issues`
- `POST /studio/config/generate-template`
- `GET /studio/update-notes`
- `GET /studio/health`
- `POST /studio/health/check`
- `GET /studio/workspaces`
- `POST /studio/workspaces`
- `POST /studio/workspaces/select`
- `GET /studio/workspaces/current`
- `GET /studio/recent-projects`
- `DELETE /studio/recent-projects/{workspace_id}`
- `POST /studio/recent-projects/clear`
- `GET /studio/workspace-templates`
- `POST /studio/workspaces/create-from-template`
- `GET /debug/crash-reports`
- `GET /debug/crash-reports/{report_id}`
- `DELETE /debug/crash-reports/{report_id}`

The crash report APIs are debug-gated. The studio config, workspace, health, update-note, and template APIs return safe summaries and must not return API keys, raw env, raw prompts, hidden facts, or full sensitive paths.

## 6. Frontend Changes

- Added desktop studio surfaces for:
  - safe config summary
  - project/workspace selection
  - recent projects
  - update notes
  - health checks
  - crash report viewing
  - workspace template creation
  - desktop settings/status
- Frontend code uses backend safe summaries and does not read `.env`.
- Frontend config remains limited to safe Vite variables such as `VITE_API_BASE_URL`.
- The frontend build passes for v1.7.

## 7. Desktop / Launcher Changes

- Windows PowerShell and shell-style launcher scripts now support help/preflight behavior.
- Launchers can run startup diagnostics before launching local services.
- Launchers check dependency and port conditions and print safer recovery hints.
- Launchers treat PowerShell profile signing warnings as local shell policy warnings, not studio failures.
- Launchers do not hardcode API keys.
- Launchers do not pass provider secrets into frontend `VITE_*` variables.
- Launchers do not modify `GameState`, saves, worlds, modules, packages, prompt profiles, or databases.

v1.7 does not introduce a formal installer, code signing, auto-update channel, desktop marketplace, account system, or cloud sync.

## 8. Backup / Restore Changes

v1.7 strengthens the backup/export boundary and packaging rules:

- Safe backup/export policy rejects:
  - `.env` and `.env.*`
  - API keys and secret-like content previews
  - database files
  - logs
  - caches
  - `node_modules`
  - `frontend/dist`
  - desktop build outputs
  - local backup and crash-report directories
  - executable/script files
  - absolute paths
  - path traversal
- Documentation now states that backup/export defaults must not include `.env`, API keys, database connection config, logs, caches, frontend build outputs, desktop build outputs, or executables.

Current limitation: v1.7 does not yet ship a complete dedicated desktop Backup / Restore runtime with archive creation, restore dry-run, checksum validation, conflict detection, and apply confirmation. The accepted v1.7 scope is boundary/policy/documentation plus tests for the safety policy.

## 9. Local Privacy / Security Changes

- API keys remain backend-only.
- API keys do not enter frontend safe summaries.
- API keys do not enter crash reports.
- API keys do not enter safe backup/export policy outputs.
- Crash reports default to local storage and are not uploaded.
- Logs and crash reports are local debug tools, not player-facing or cloud-uploaded surfaces.
- Workspace and recent-project paths are redacted for normal frontend display.
- Local config issue fields use safe labels such as `provider_config` rather than exposing secret environment variable names.
- `.gitignore` excludes local runtime and generated artifacts such as logs, crash reports, backups, caches, database files, frontend build output, and desktop build outputs.
- Desktop tools do not change the world fact boundary and cannot bypass backend APIs.

## 10. Testing Changes

v1.7 adds or expands tests for:

- Desktop Studio boundary policy.
- Safe config summaries.
- Startup diagnostics.
- Project selector and recent projects.
- Local update notes.
- Desktop health checks.
- Crash report redaction and debug gating.
- Workspace templates.
- v1.7 desktop integration coverage.
- Launcher and packaging safety checks.

Verification for acceptance:

- `python -m pytest`: passed, `1551 passed`.
- `cd frontend && npm.cmd run build`: passed.

## 11. Known Limitations

- v1.7 is a local desktop studio prototype, not a formal public desktop app.
- No formal installer is produced.
- No code signing is included.
- No automatic update system is included.
- No cloud sync, account system, hosted collaboration, or online marketplace is included.
- Log Viewer is not yet a complete `/debug/logs` runtime with logs-only access, search, and tail UI.
- Error Recovery Wizard is not yet a full diagnostic and safe-step execution workflow.
- Backup / Restore is not yet a full desktop runtime with archive creation, restore dry-run, checksum validation, conflict detection, and apply confirmation.
- One-click Quality Gate is not yet a complete desktop aggregator over all validation, leak, scenario, module, migration, and performance checks.
- One-click World Export is not yet a complete guided desktop export workflow.
- Offline Help Docs is not yet a complete in-app indexed help browser.
- Frontend build currently emits a non-blocking chunk-size warning.
- PowerShell profile signing warnings may appear on some machines; these are treated as local shell policy warnings.

## 12. Upgrade Notes From v1.6

- Keep `.env` local and untracked. Do not copy provider secrets into frontend or desktop build outputs.
- Use `LLM_PROVIDER=mock` or `local_stub` for offline local startup unless intentionally using a configured real provider.
- Use the launcher scripts for local startup:
  - `scripts/start_local_studio.ps1`
  - `scripts/start_local_studio.sh`
- Run startup diagnostics when setup fails:
  - `python -m backend.app.tools.startup_diagnostics`
- Review `.gitignore` if you add local packaging tools; generated desktop outputs, logs, backups, crash reports, caches, and database files should remain untracked.
- Treat save exports and backups as private local data. Safe world/package export profiles should remain the default for sharing.
- Do not treat the desktop shell as a way to bypass backend APIs, validation gates, StateDelta, EventLog, package validation, or quality gates.

## 13. Recommended v2.0 Directions

- Complete the deferred desktop workflows:
  - Log Viewer
  - Error Recovery Wizard
  - Backup / Restore
  - One-click Quality Gate
  - One-click World Export
  - Offline Help Docs
- Add a repeatable packaging safety scan command for built frontend and any future desktop bundles.
- Move desktop runtime data defaults toward OS app-data directories before any formal packaging milestone.
- Define a clearer process lifecycle model for starting, stopping, and monitoring backend/frontend services.
- Add focused frontend tests for API-disabled states and redaction-heavy desktop panels.
- Continue schema and migration hardening for a v2.0 stability milestone.
- Research public-ready packaging only after local privacy, secrets, backups, crash reports, and update behavior have a complete policy and test suite.

## Final Notes

v1.7 keeps the engine local-first and rule-first. The LLM is still not the world judge. The desktop studio shell does not change the world fact boundary, does not directly modify `GameState`, and does not bypass backend APIs.

API keys must remain backend-only. Backup/export defaults must not include secrets. Crash reports remain local by default and are not uploaded.
