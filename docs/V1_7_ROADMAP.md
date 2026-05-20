# v1.7 Roadmap: Polished Desktop Studio

v1.7 turns the local engine into a more polished desktop studio experience. The goal is not to change the world simulation model, add cloud features, or ship a public installer. The goal is to make the existing local studio easier to start, inspect, recover, back up, export, and diagnose without weakening the engine boundaries established in v1.0 through v1.6.

The desktop layer remains a convenience shell around the backend and frontend. It must not become a second game engine, a privileged state editor, or a place where secrets are exposed.

## Goals

1. Provide a reliable local desktop launcher for the backend and frontend studio.
2. Make local projects easier to select, reopen, back up, restore, and export.
3. Provide safe diagnostics for startup, health, logs, errors, crash reports, and packaging outputs.
4. Keep `.env`, API keys, databases, logs, caches, and local paths protected by default.
5. Keep all content changes behind existing backend services, validation gates, import/export checks, and quality gates.
6. Make offline documentation and local release notes available inside the studio.

## Non-Goals

v1.7 explicitly does not include:

1. Cloud sync.
2. Account systems.
3. Multi-user collaboration.
4. Online marketplace.
5. Automatic updates.
6. Code signing.
7. Formal public installer release.
8. Bundling API keys into the frontend or desktop package.
9. Frontend direct reads of `.env`.
10. Desktop shell bypassing backend APIs.
11. Desktop shell direct modification of `GameState`.
12. Backups or exports that include `.env`, API keys, database connection config, logs, or caches by default.
13. Network upload of crash reports.
14. Launcher auto-enabling untrusted gameplay modules.

## Hard Constraints

1. The desktop shell must call backend APIs; it must not modify `GameState` directly.
2. The desktop shell must not write StateDelta, EventLog, save, world, package, module, or prompt files outside existing backend service flows.
3. The frontend must never read `.env`, API keys, raw environment variables, or secret provider config.
4. Startup scripts must not hardcode API keys or provider secrets.
5. Backup/export defaults must exclude `.env`, API keys, database connection config, logs, caches, frontend build outputs, and desktop build outputs.
6. Crash reports are local-only by default and are never uploaded.
7. Health checks must return safe summaries only.
8. Settings UI may show safe config summaries, not raw secrets.
9. Local config manager must not write secrets into frontend-readable files.
10. All data modifications still go through backend services and validation gates.
11. Tests must use mock/local_stub/fake providers and must not call real APIs.
12. Desktop build outputs must be excluded by `.gitignore`.

## Recommended Development Order

1. Desktop Studio Boundary Contract.
2. Desktop Startup Diagnostics.
3. Desktop Health Check.
4. Local Config Manager.
5. Desktop Launcher Pro.
6. Project Selector.
7. Recent Projects.
8. Desktop Settings UI.
9. Log Viewer.
10. Error Recovery Wizard.
11. Backup / Restore.
12. One-click Quality Gate.
13. One-click Export World Pack.
14. Workspace Templates.
15. Offline Help Docs.
16. Local Update Notes.
17. Crash Report Local Viewer.
18. Desktop Packaging Safety Pass.

This order builds the safety boundary first, then the launch/config foundation, then user-facing workflow polish, and finally packaging and freeze checks.

## Modules

### 1. Desktop Studio Boundary Contract

**Goal:** Define the safety contract for desktop shell, launcher scripts, local config, logs, backup/restore, and packaging.

**Data Structures:** `DesktopStudioPolicy`, `DesktopSafeConfigSummary`, `DesktopOperationBoundary`, `DesktopPrivacyClass`.

**API Changes:** Add or document safe desktop summary endpoints if missing, such as `GET /desktop/boundary` or reuse existing config summary APIs.

**Frontend Changes:** Display boundary status in the desktop settings/about area without exposing secrets.

**Script Changes:** Document script responsibilities: start services, check ports, open UI, and never mutate game state.

**Tests:** Verify safe summaries exclude `.env`, API keys, raw env, database URLs, logs, caches, and debug-only data.

**Acceptance:** Desktop boundary is documented, tested, and referenced by launcher/config/backup features.

**Privacy Impact:** Establishes safe vs sensitive data classes.

**Secret/Log/DB Security:** Defines exclusion and redaction rules for all later desktop features.

**LLM Boundary:** No LLM call; desktop cannot grant LLM new state authority.

### 2. Desktop Launcher Pro

**Goal:** Provide a reliable local launcher that can start backend/frontend services, detect ports, show status, and open the studio.

**Data Structures:** `DesktopLaunchConfig`, `DesktopLaunchStatus`, `DesktopServiceStatus`.

**API Changes:** Optional `GET /desktop/launch-status` safe endpoint if the backend can report its own readiness.

**Frontend Changes:** Launcher status panel with backend/frontend readiness, port, and error summaries.

**Script Changes:** Improve local launcher scripts for Windows and optional POSIX shells; no hardcoded secrets.

**Tests:** Script dry-run checks, port conflict handling, missing dependency messages, and no secret output.

**Acceptance:** User can start the local studio with clear status and recoverable errors.

**Privacy Impact:** Shows only safe local status.

**Secret/Log/DB Security:** Must not print raw `.env`, API keys, or full database URLs.

**LLM Boundary:** No provider calls during launch unless explicitly configured by backend health checks in safe mode.

### 3. Project Selector

**Goal:** Let users choose a local project/workspace/world root without manually editing paths.

**Data Structures:** `DesktopProjectRef`, `ProjectSelectionRequest`, `ProjectSelectionResult`.

**API Changes:** `GET /desktop/projects`, `POST /desktop/projects/select` behind local authoring/desktop controls.

**Frontend Changes:** Project selector screen with safe names, sanitized paths, and validation status.

**Script Changes:** Optional launcher parameter for project root; path normalization and validation.

**Tests:** Path traversal rejection, root boundary enforcement, missing project handling, safe display of local paths.

**Acceptance:** Only validated local projects can be selected; selection does not mutate active `GameState`.

**Privacy Impact:** Displays minimal local path information.

**Secret/Log/DB Security:** Must not scan or expose `.env`, databases, logs, or caches as selectable content.

**LLM Boundary:** No LLM involvement.

### 4. Recent Projects

**Goal:** Track recently opened local projects for convenience.

**Data Structures:** `RecentProjectEntry`, `RecentProjectsStore`.

**API Changes:** `GET /desktop/recent-projects`, `POST /desktop/recent-projects`, `DELETE /desktop/recent-projects/{id}`.

**Frontend Changes:** Recent project list on launcher/home screen.

**Script Changes:** Optional local recent-project file managed by backend or launcher, not by frontend secrets.

**Tests:** Redaction, max history, stale project handling, no secret or raw env storage.

**Acceptance:** Recent projects are useful, bounded, and safe to display.

**Privacy Impact:** Stores local project references; must support clear/delete.

**Secret/Log/DB Security:** No API keys, raw env, database connection strings, or logs.

**LLM Boundary:** No LLM involvement.

### 5. Local Config Manager

**Goal:** Manage safe local studio configuration, including ports, roots, feature flags, and provider selection summaries.

**Data Structures:** `LocalStudioConfig`, `SafeConfigSummary`, `ConfigValidationReport`.

**API Changes:** `GET /desktop/config/summary`, `POST /desktop/config/validate`, optionally `POST /desktop/config/update-safe`.

**Frontend Changes:** Config summary and validation UI.

**Script Changes:** Read safe config defaults; do not write secrets into frontend-readable files.

**Tests:** Secret redaction, invalid config detection, feature flag summary, no frontend API key exposure.

**Acceptance:** Users can inspect and adjust safe config without seeing or storing secrets in unsafe places.

**Privacy Impact:** Separates safe config from secret config.

**Secret/Log/DB Security:** Raw `.env`, API keys, database URLs, and provider secrets are never returned to frontend.

**LLM Boundary:** Provider selection remains through backend provider factory/router.

### 6. Log Viewer

**Goal:** Provide a local log viewer with redaction, filtering, and safe summaries.

**Data Structures:** `LogFileSummary`, `LogEntryView`, `LogRedactionReport`.

**API Changes:** `GET /desktop/logs`, `GET /desktop/logs/{id}` with safe redaction and local-only controls.

**Frontend Changes:** Log viewer page with severity filters and copy-safe snippets.

**Script Changes:** Standardize launcher log paths and rotation hints.

**Tests:** API key redaction, hidden fact redaction, path traversal rejection, log file allowlist.

**Acceptance:** Logs are inspectable without leaking secrets or hidden content.

**Privacy Impact:** Logs may contain sensitive local details; normal view must redact.

**Secret/Log/DB Security:** No `.env`, API keys, raw prompt, hidden facts, raw state deltas, or full DB URLs.

**LLM Boundary:** Logs must not be sent to LLM.

### 7. Error Recovery Wizard

**Goal:** Help users recover from common local failures such as port conflicts, missing dependencies, failed migrations, broken config, or invalid content packs.

**Data Structures:** `RecoveryIssue`, `RecoveryPlan`, `RecoveryStep`, `RecoveryResult`.

**API Changes:** `POST /desktop/recovery/diagnose`, `POST /desktop/recovery/run-safe-step` for non-destructive steps only.

**Frontend Changes:** Wizard with diagnosis, safe steps, confirmation for any file-affecting operation.

**Script Changes:** Optional repair helpers for cache cleanup or dependency checks; no destructive default.

**Tests:** Recovery plans do not mutate game state, destructive steps require confirmation, secret redaction.

**Acceptance:** Common failures produce actionable local recovery steps.

**Privacy Impact:** Diagnosis uses safe summaries.

**Secret/Log/DB Security:** Does not expose raw env, database content, API keys, or hidden facts.

**LLM Boundary:** No LLM diagnosis by default.

### 8. Backup / Restore

**Goal:** Provide local backup and restore for safe project data with explicit exclusions.

**Data Structures:** `BackupManifest`, `BackupProfile`, `RestoreDryRunReport`, `RestoreApplyReport`.

**API Changes:** `POST /desktop/backups/create`, `POST /desktop/backups/restore-dry-run`, `POST /desktop/backups/restore-apply`.

**Frontend Changes:** Backup/restore page with manifest preview, exclusions, validation, and confirmation.

**Script Changes:** Optional CLI/script wrapper for local backup creation and verification.

**Tests:** Default backup excludes `.env`, API keys, database connection config, logs, caches, build outputs; restore dry-run writes nothing; apply requires confirmation.

**Acceptance:** Safe local backups can be created and restored without leaking secrets or bypassing validation.

**Privacy Impact:** Backups contain user content; safe defaults and manifests are mandatory.

**Secret/Log/DB Security:** No secrets by default; explicit secret backup is not a v1.7 feature.

**LLM Boundary:** No LLM involvement.

### 9. One-click Quality Gate

**Goal:** Run existing validation, quality gate, hidden leak, module gate, prompt regression, and package checks from one desktop action.

**Data Structures:** `DesktopQualityGateRequest`, `DesktopQualityGateSummary`.

**API Changes:** `POST /desktop/quality-gate/run`, optionally composing existing quality APIs.

**Frontend Changes:** One-click button and report summary with blockers, warnings, and links to detailed tools.

**Script Changes:** Optional desktop quality script that calls backend APIs.

**Tests:** No direct content mutation, no real API calls, hidden details redacted, failures reported clearly.

**Acceptance:** A local user can run a broad readiness check before export/release.

**Privacy Impact:** Normal report redacts hidden facts and debug data.

**Secret/Log/DB Security:** No API keys or raw env in reports.

**LLM Boundary:** Uses mock/fake providers unless explicit existing eval settings allow local safe tests.

### 10. One-click Export World Pack

**Goal:** Provide a guided export path for world packs using existing validation gate, package profiles, and safe export rules.

**Data Structures:** `DesktopWorldExportRequest`, `DesktopWorldExportReport`.

**API Changes:** `POST /desktop/worlds/{world_id}/export-safe` or compose existing export APIs.

**Frontend Changes:** Export button with profile selection, dry-run, validation, and safe manifest preview.

**Script Changes:** Optional export CLI wrapper.

**Tests:** Export excludes API keys, `.env`, hidden facts in safe mode, logs, caches, database connection config; validation gate required.

**Acceptance:** A safe world pack export can be produced with one guided flow.

**Privacy Impact:** Export is redacted by default.

**Secret/Log/DB Security:** No secrets or operational logs in export.

**LLM Boundary:** No LLM involvement.

### 11. Offline Help Docs

**Goal:** Make key local documentation available in the studio without internet access.

**Data Structures:** `OfflineHelpIndex`, `OfflineHelpArticle`.

**API Changes:** `GET /desktop/help`, `GET /desktop/help/{slug}` serving bundled docs or generated safe indexes.

**Frontend Changes:** Help browser with sections for setup, authoring, modules, prompt lab, backups, and troubleshooting.

**Script Changes:** Optional docs index generation script.

**Tests:** Help index builds, broken links caught, no secrets in indexed docs.

**Acceptance:** Users can find local instructions without external websites.

**Privacy Impact:** No user content required.

**Secret/Log/DB Security:** Docs index must not include `.env`, logs, local DB data, or generated secrets.

**LLM Boundary:** No LLM involvement.

### 12. Local Update Notes

**Goal:** Show local release notes and migration notes for installed project versions.

**Data Structures:** `LocalUpdateNote`, `LocalVersionSummary`.

**API Changes:** `GET /desktop/update-notes`.

**Frontend Changes:** Release notes panel showing v1.x docs and local migration warnings.

**Script Changes:** Optional release-note index generation.

**Tests:** Notes load offline, missing docs handled, no network request required.

**Acceptance:** Users can inspect local version changes safely.

**Privacy Impact:** No user data.

**Secret/Log/DB Security:** No secrets.

**LLM Boundary:** No LLM involvement.

### 13. Desktop Health Check

**Goal:** Summarize local studio health: backend, frontend, database reachability, content roots, package roots, provider safe status, feature flags, and disk path readiness.

**Data Structures:** `DesktopHealthCheckReport`, `DesktopHealthItem`.

**API Changes:** `GET /desktop/health`.

**Frontend Changes:** Health dashboard with pass/warn/fail cards and recovery links.

**Script Changes:** Launcher can call health check after startup.

**Tests:** No secret leakage, missing root warnings, provider config summarized safely, disabled APIs safe.

**Acceptance:** User can understand whether the studio is ready without seeing secrets.

**Privacy Impact:** Local path summaries should be minimized or redacted.

**Secret/Log/DB Security:** No raw env, API keys, full DB URLs, or logs.

**LLM Boundary:** Health check does not call real providers by default.

### 14. Workspace Templates

**Goal:** Provide safe local workspace templates for new projects without copying secrets.

**Data Structures:** `WorkspaceTemplate`, `WorkspaceTemplateApplyRequest`, `WorkspaceTemplateApplyReport`.

**API Changes:** `GET /desktop/workspace-templates`, `POST /desktop/workspace-templates/{id}/apply-dry-run`, `POST /desktop/workspace-templates/{id}/apply`.

**Frontend Changes:** Template picker with preview and validation.

**Script Changes:** Optional template scaffolding script.

**Tests:** Apply dry-run writes nothing, apply requires confirmation, templates exclude secrets and build outputs.

**Acceptance:** New local workspaces can be scaffolded safely.

**Privacy Impact:** New templates contain no user secrets.

**Secret/Log/DB Security:** No `.env`, API keys, DB files, logs, caches, or build outputs.

**LLM Boundary:** No LLM involvement.

### 15. Crash Report Local Viewer

**Goal:** Display local crash/error snapshots for backend/frontend/launcher without uploading anything.

**Data Structures:** `LocalCrashReport`, `CrashReportSummary`, `CrashReportRedactionReport`.

**API Changes:** `GET /desktop/crash-reports`, `GET /desktop/crash-reports/{id}`.

**Frontend Changes:** Crash report viewer with redacted stack traces and local-only export option.

**Script Changes:** Launcher can write local crash report files to an ignored directory.

**Tests:** Reports are local-only, redacted, bounded, and do not include API keys/raw env.

**Acceptance:** Users can inspect crash details locally and decide what to share manually.

**Privacy Impact:** Crash reports may contain paths and snippets; normal view redacts sensitive values.

**Secret/Log/DB Security:** No `.env`, API keys, raw prompt, hidden facts, or database contents.

**LLM Boundary:** Crash reports are not sent to LLM.

### 16. Desktop Settings UI

**Goal:** Provide a safe settings page for feature flags, local roots, launch options, provider summaries, and UI preferences.

**Data Structures:** `DesktopSettingsSummary`, `DesktopSettingsUpdateRequest`, `DesktopSettingsValidationReport`.

**API Changes:** `GET /desktop/settings`, `POST /desktop/settings/validate`, `POST /desktop/settings/update-safe`.

**Frontend Changes:** Settings page with safe fields only; secrets show as configured/not configured.

**Script Changes:** Launcher reads safe settings for ports and roots.

**Tests:** API keys cannot be read or written through settings UI; invalid roots rejected; path traversal rejected.

**Acceptance:** Settings are useful without becoming a secret editor.

**Privacy Impact:** Some local paths may be displayed in redacted or user-approved form.

**Secret/Log/DB Security:** No secret values are returned or stored in frontend-readable files.

**LLM Boundary:** Provider configuration still belongs to backend environment/provider factory.

### 17. Desktop Startup Diagnostics

**Goal:** Detect startup problems before the user hits a blank page: dependency missing, port conflict, backend failed, frontend build missing, invalid config, migration issue.

**Data Structures:** `StartupDiagnosticReport`, `StartupDiagnosticIssue`, `StartupDiagnosticSuggestion`.

**API Changes:** `GET /desktop/startup-diagnostics` when backend is available; launcher-side fallback report if not.

**Frontend Changes:** Startup diagnostics page and retry/recovery actions.

**Script Changes:** Preflight checks before launching services.

**Tests:** Missing dependency and port conflict are reported; no secrets printed; backend unavailable still yields local diagnostics.

**Acceptance:** Startup failures are explainable and recoverable.

**Privacy Impact:** Reports local environment status only.

**Secret/Log/DB Security:** No raw env, API keys, or full database URL.

**LLM Boundary:** No LLM involvement.

### 18. Desktop Packaging Safety Pass

**Goal:** Add a final packaging safety checklist for ignored outputs, secret scanning, bundled files, local-only behavior, and desktop build artifacts.

**Data Structures:** `DesktopPackagingSafetyReport`, `DesktopPackagingFinding`.

**API Changes:** Optional `POST /desktop/packaging/safety-check` or CLI-only tool.

**Frontend Changes:** Packaging safety summary in local tools area.

**Script Changes:** Safety script for `.gitignore`, dist outputs, secret scan, bundle manifest, and safe export checks.

**Tests:** Detect tracked build outputs, `.env`, database/log/cache files, suspicious real API keys, and executable files in unsafe package areas.

**Acceptance:** v1.7 can be frozen with a repeatable local packaging safety check.

**Privacy Impact:** Prevents accidental inclusion of local user data.

**Secret/Log/DB Security:** Explicitly checks for `.env`, API keys, DB files, logs, caches, and build outputs.

**LLM Boundary:** No LLM involvement.

## Integration Test Requirements

v1.7 integration tests should verify:

1. Desktop APIs return safe summaries and never raw secrets.
2. Launcher/status/diagnostic flows do not mutate `GameState`.
3. Project selection rejects path traversal and project roots outside allowed workspaces.
4. Recent projects do not store API keys, raw env, or database URLs.
5. Local config manager does not write secrets to frontend-readable files.
6. Log viewer and crash viewer redact API keys, hidden facts, raw prompts, raw state deltas, and full DB URLs.
7. Backup/export default profiles exclude `.env`, API keys, database connection config, logs, caches, frontend build outputs, and desktop build outputs.
8. Restore dry-run writes nothing; restore apply requires explicit confirmation.
9. One-click quality gate composes existing gates and does not bypass validation.
10. One-click world export uses safe export profiles and validation gate.
11. Offline help and update notes load without network access.
12. Desktop health check and startup diagnostics do not call real providers by default.
13. Settings UI displays only safe config summaries.
14. Packaging safety pass catches tracked/generated forbidden artifacts.
15. Frontend build passes.
16. `python -m pytest` passes.
17. Tests use mock/local_stub/fake provider and never call real APIs.

## Final Acceptance Criteria

v1.7 is accepted when:

1. `docs/DESKTOP_STUDIO_BOUNDARY.md` or equivalent boundary documentation exists and is reflected in `WORLD_ENGINE`, `LLM_PROTOCOL`, `SPEC`, and `README`.
2. Desktop launcher, project selection, recent projects, config summary, settings, diagnostics, health check, logs, backup/restore, quality gate, export, help, update notes, crash viewer, workspace templates, and packaging safety have focused tests.
3. Frontend desktop studio surfaces build successfully and degrade safely when APIs are disabled.
4. No desktop feature bypasses backend APIs, validation gates, StateDelta, EventLog, or existing package security.
5. No desktop feature exposes `.env`, API keys, raw env, raw database URLs, logs, caches, hidden facts, raw prompts, or debug-only state in normal UI.
6. Backup/export/packaging defaults are safe and redacted.
7. Crash reports remain local-only.
8. Desktop build outputs remain ignored by Git.
9. `python -m pytest` passes.
10. `cd frontend && npm.cmd run build` passes.

## v2.0 Candidate Directions

1. Stable save/world schema consolidation and long-term migration hardening.
2. Public-ready packaging research without code signing commitments.
3. Optional plugin marketplace research with strict no-code-execution sandboxing.
4. Richer replay/debug time-travel UI.
5. Larger content authoring workflows built on the desktop studio shell.
6. Accessibility and keyboard-first UX pass.
7. Performance profiling and large-world scalability pass.
8. Optional local-only collaboration research without cloud sync.

