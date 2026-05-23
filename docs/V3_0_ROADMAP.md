# v3.0 Roadmap - Local Desktop Studio Polish

## 1. Version Goal

v3.0 focuses on **Local Desktop Studio Polish**. The goal is to make AI
Narrative Studio easier to start, inspect, configure, back up, diagnose, and
recover as a local-first studio application.

The release priorities are:

- local-first operation;
- privacy-first defaults;
- clearer desktop and UI/UX workflows;
- safe launcher, project, provider, diagnostics, logs, backup, restore, and
  settings surfaces;
- deterministic local checks rather than online services.

v3.0 does not add account systems, cloud sync, online marketplaces, remote
package auto-download, telemetry upload, online publishing, or any hosted
platform behavior.

## 2. Scope

v3.0 covers the following accepted desktop polish areas:

1. Desktop Studio Contract Review
   - Document current launcher, desktop, project path, config, provider secret,
     logging, diagnostics, backup, restore, and packaging boundaries.

2. Local Launcher UX Backend
   - Add safe local studio status, health, config summary, startup checks, and
     recent error summaries.

3. Local Launcher UX Frontend
   - Add Local Launcher / Startup Status surfaces that display only safe
     summaries.

4. Project Picker
   - Provide local project/workspace selection, creation, open, validate, and
     refresh flows using safe path summaries.

5. Recent Projects
   - Store local recent-project summaries without secrets, raw env, API keys,
     or raw project data.

6. Local Config Wizard
   - Show safe configuration status for database, provider profiles, debug,
     authoring, module, and quality APIs without showing raw env.

7. Provider Setup Wizard
   - Guide provider type, display/model/base URL metadata, `api_key_env`,
     `secret_ref`, allowed modes, capability summary, and dry-run validation.

8. Backend Health Check UI
   - Show backend, API version, database, project repository, provider gateway,
     quality gate, debug, and authoring status without secrets.

9. One-Click Quality Gate
   - Provide local Quality Gate entry points, scope selection, running state,
     and safe result summaries.

10. Backup / Restore Core
    - Add backup manifest, backup plan, dry-run, create, list, validate,
      restore dry-run, and confirmed restore apply.

11. Backup / Restore Wizard UI
    - Add backup and restore flows with filtering policy, dry-run preview,
      conflict warnings, and explicit confirmation.

12. Error Recovery Core
    - Add deterministic recovery issue and recovery plan detection with
      dry-run and confirmed safe apply only.

13. Error Recovery Wizard UI
    - Display recovery issues, plan summaries, dry-run results, manual-only
      items, and destructive blocked states.

14. Local Log Viewer
    - Provide redacted local log summaries from allowed log directories only.

15. Local Diagnostics Bundle
    - Provide local diagnostics preview, create, and validate flows with safe
      summaries and redacted logs.

16. Offline Help Center
    - Add local static help topics for startup, local-first workflow, modes,
      provider setup, mods, quality, backup, diagnostics/logs, privacy, and
      mature default-off behavior.

17. Startup Script Polish
    - Improve Windows and shell launchers with dependency checks, `.env`
      presence hints, port hints, local-only reminders, and safe frontend env
      behavior.

18. Desktop Packaging Docs
    - Document local desktop positioning, packaging contents, exclusions,
      `.env`/API key/provider/log/database/build-output handling, backup,
      diagnostics, and release checklist.

19. Local First Privacy Review
    - Audit that v3.0 remains local-first and does not introduce account,
      cloud, marketplace, telemetry, or default secret export behavior.

20. Desktop Settings / Preferences Polish
    - Organize settings around General, Local Privacy, Providers, Export,
      Debug, Backup / Restore, Diagnostics, Mature Module, UI Preferences, and
      Quality Gate.

21. Safe Local File Path UX
    - Use safe path summaries and backend validation for local path display and
      file-related flows.

22. First-Run Onboarding Flow
    - Add local-only onboarding for welcome, project create/open, optional
      provider setup, privacy/secrets explanation, and Project Home entry.

23. Desktop Shell Integration Smoke Tests
    - Add script/docs/packaging safety checks without building a real
      installer.

24. Local Studio UX Regression Tests
    - Add local studio UI safety checks for launcher, picker, recent projects,
      config, provider, health, quality, backup, recovery, logs, diagnostics,
      help, and settings surfaces.

25. v3.0 Integration Regression Tests
    - Cover local studio APIs, backup/restore, diagnostics/logs, recent
      projects, recovery, frontend static safety, scripts/docs, and World
      boundary preservation.

## 3. Non-Goals

v3.0 explicitly does not implement:

- account system;
- cloud sync;
- online marketplace;
- remote package auto-download;
- online narrative platform;
- telemetry upload;
- API resale service;
- arbitrary code plugins;
- new large gameplay systems;
- formal signed commercial installer;
- automatic updater;
- changing World Engine fact authority;
- frontend or desktop-side direct `GameState` mutation;
- bypassing `StateDelta`, `EventLog`, visibility, validation, export, backup,
  diagnostics, or Provider Gateway boundaries.

Online, account, cloud, marketplace, and hosted platform concepts remain
long-term optional directions only. They are not v3.0 features.

## 4. Architecture Boundaries

v3.0 desktop and UI surfaces are convenience layers over local backend APIs.
They are not a second runtime authority.

Required boundaries:

- UI and desktop shell must not directly modify `GameState`.
- World-changing flows still go through backend APIs, validation,
  `StateDelta`, and `EventLog`.
- Provider Gateway remains the only model entry point.
- Provider choice can affect wording, latency, cost, or routing; it cannot
  change world authority.
- API keys may only be read through environment variables or a local secret
  resolver.
- API keys must not enter frontend code, frontend state, backups,
  diagnostics, logs, exports, packages, crash reports, or desktop bundles.
- Provider setup must use `api_key_env` or `secret_ref`, not plaintext API key
  values.
- Debug data remains controlled by `ENABLE_DEBUG_API`.
- Normal UI, backups, diagnostics, logs, reports, and exports must not include
  hidden facts, NPC secrets, debug memory, raw prompts, raw outputs, raw
  `state_deltas`, mature/private content, API keys, provider secrets, or raw
  env.
- Mature/private content remains disabled or excluded by default from backup,
  export, diagnostics, and normal reports.

## 5. Security / Privacy Requirements

Backup defaults:

- Backup dry-run must not write files.
- Backup creation must require explicit confirmation.
- Backup must exclude `.env`, API keys, provider secrets, logs, cache,
  `node_modules`, `frontend/dist`, desktop build outputs, databases,
  debug-only data, and mature/private content by default.
- Backup must not upload or cloud-sync data.

Restore defaults:

- Restore dry-run must not write projects.
- Restore apply must require `explicit_confirm`.
- Existing project overwrite must be blocked unless explicitly allowed and
  confirmed.
- Corrupted backups must be rejected.

Diagnostics defaults:

- Diagnostics preview must not write files.
- Diagnostics bundles must be local files only.
- Diagnostics must exclude `.env`, API keys, provider secrets, raw env, raw
  prompt/output, hidden facts, NPC secrets, debug memory, raw `state_deltas`,
  mature/private content, database files, and full save files by default.
- Debug diagnostics must require both explicit confirmation and debug enablement.
- Diagnostics must not upload data.

Logs:

- Local Log Viewer must read only allowed local log directories.
- Log output must be redacted.
- Redaction must cover API-key-like strings, Authorization headers, raw env,
  database connection strings, provider secrets, hidden facts, NPC secrets,
  debug memory, raw `state_deltas`, mature/private markers, and sensitive
  prompt/output markers.

Recent projects and paths:

- Recent Projects must store safe summaries only.
- Recent Projects must not store secrets, raw env, API keys, `.env` contents,
  raw `GameState`, or raw local sensitive paths.
- Path display should prefer project name, folder name, and redacted/short
  path summaries.

Startup scripts:

- Startup scripts must not print raw env.
- Startup scripts must not print API keys.
- Startup scripts must not inject API keys into frontend env.
- The frontend may receive safe configuration such as `VITE_API_BASE_URL`.

Packaging:

- Desktop packaging must exclude `.env`, API keys, local secret store
  material, databases unless explicitly intended, logs, caches,
  `node_modules`, `frontend/dist`, desktop build outputs, debug reports,
  mature/private content, backups unless explicit, and crash reports unless
  redacted.

## 6. Testing / Verification

Required v3.0 release verification commands:

```powershell
python -m pytest
```

```powershell
cd frontend
npm.cmd run build
```

Startup script safe/syntax checks should be run when available, for example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_local_studio.ps1 -Help
```

Recommended v3.0-focused checks:

```powershell
python -m pytest backend/tests/test_v30_local_studio_services.py
python -m pytest backend/tests/test_v30_integration_regression.py
python -m pytest backend/tests/test_v30_desktop_shell_smoke.py
python -m pytest backend/tests/test_v30_local_studio_ux_regression.py
cd frontend
npm.cmd run check:v30-ux
```

Release readiness should also include:

- scan for tracked `.env`, databases, logs, caches, `node_modules`,
  `frontend/dist`, desktop build outputs, backups, crash reports, and
  diagnostics bundles;
- scan for real API keys or sensitive configuration;
- verify no account/cloud/marketplace/remote auto-download entry is presented
  as a current feature;
- verify backup, restore, diagnostics, logs, startup scripts, and packaging
  remain secret-safe.

## 7. Known Limitations

- v3.0 is not a complete commercial desktop installer.
- v3.0 does not include a signed installer, automatic updater, platform app
  shell, account login, cloud sync, online marketplace, telemetry upload, or
  online platform.
- v3.0 does not implement cloud backup.
- v3.0 does not implement a remote package registry.
- Backup and diagnostics are local safe-summary-first flows.
- Future richer backup formats need expanded manifests, content inventory,
  checksums, privacy classification, and renewed tests.
- Future full restore workflows should add stronger overwrite-specific
  confirmation before replacing real project data.
- Diagnostics and backup output directories must remain ignored and excluded
  from desktop bundles.
- Local path display is intentionally conservative; future native desktop file
  picker integration should continue to validate paths through backend rules.

## 8. Recommended v3.1 Priorities

Recommended v3.1 direction: **Novel Studio UI Pro**.

Candidate v3.1 priorities:

- Outline Tree Pro;
- Chapter Editor Pro;
- Scene Cards;
- Character Arc Panel;
- Plot Thread / Foreshadowing Board;
- Timeline Link Panel;
- World Bible Sidebar;
- Draft Version Compare;
- Novel Export Wizard Pro.

v3.1 should preserve v3.0 local desktop safety boundaries. Novel UI polish must
not change World Engine fact authority, Provider Gateway boundaries, visibility
rules, export filtering, backup/diagnostics redaction, or `StateDelta` /
`EventLog` requirements.
