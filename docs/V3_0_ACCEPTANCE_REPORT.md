# v3.0 Acceptance Report

## Verdict

Accepted with non-blocking documentation and hardening follow-ups.

v3.0 Local Desktop Studio Polish is accepted as a local-first desktop/studio
polish release. The implementation adds safe local launcher/status APIs,
Project Picker and Recent Projects, local config/provider setup surfaces,
health and quality entry points, backup/restore dry-run and confirmed apply,
error recovery suggestions, redacted log viewing, diagnostics bundle
preview/create/validate, offline help, settings polish, safe path summaries,
first-run onboarding, and v3.0 desktop/local regression coverage.

No high-risk blocker was found in the v3.0 code review, Desktop / Local Privacy
Audit, Desktop Security / Secrets Audit, or Backup / Restore / Diagnostics
Audit.

## Verification Date

2026-05-23

## Verification Commands

```powershell
python -m pytest
```

Result: passed, `1711 passed`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed. Vite reported the existing large chunk warning only.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_local_studio.ps1 -Help
```

Result: passed. The launcher help prints safe usage and safety text without
starting backend/frontend processes or printing secrets.

Additional v3.0-focused checks available in the tree:

```powershell
python -m pytest backend/tests/test_v30_local_studio_services.py
python -m pytest backend/tests/test_v30_integration_regression.py
cd frontend
npm.cmd run check:v30-ux
```

## Scope Accepted

Accepted v3.0 scope:

1. Desktop Studio Contract Review
   - `docs/V3_0_DESKTOP_STUDIO_CONTRACT_REVIEW.md` documents startup,
     launcher, project path, config, provider secret, logs/diagnostics,
     backup/restore, packaging, and recommended v3.0 desktop contract.

2. Local Launcher UX Backend
   - Safe-summary local studio APIs are implemented:
     `/local-studio/status`, `/local-studio/health`,
     `/local-studio/config-summary`, `/local-studio/startup-checks`, and
     `/local-studio/recent-errors`.

3. Local Launcher UX Frontend
   - The frontend includes Local Launcher / Startup Status surfaces using safe
     summaries and no secret values.

4. Project Picker
   - Project/workspace selection UI and API surfaces are available with safe
     project summaries and redacted paths.

5. Recent Projects
   - `RecentProjectEntry` and `RecentProjectsService` provide bounded local
     recent-project summaries without secrets.

6. Local Config Wizard
   - Local configuration status is exposed through safe booleans and redacted
     path hints, not raw env.

7. Provider Setup Wizard
   - Provider setup uses provider type, display/model/base URL metadata,
     `api_key_env`, and `secret_ref`. There is no plaintext API key field.

8. Backend Health Check UI
   - Health check UI/API surfaces provide safe backend, database, project,
     provider, quality, debug, and authoring status.

9. One-Click Quality Gate
   - Quality Gate entry and scope selection are available from the local UI
     as safe status/summary surfaces.

10. Backup / Restore Core
    - `BackupManifest`, `BackupPlan`, `BackupService`, and `RestoreService`
      implement dry-run-first local backup and restore with explicit
      confirmation.

11. Backup / Restore Wizard UI
    - The frontend includes backup/restore wizard surfaces with filtering
      policy, dry-run preview, conflict warning, and confirmation copy.

12. Error Recovery Core
    - `RecoveryIssue`, `RecoveryPlan`, and `RecoveryService` provide local
      deterministic recovery suggestions. Destructive recovery remains blocked.

13. Error Recovery Wizard UI
    - The frontend includes safe issue/plan/dry-run recovery UI.

14. Local Log Viewer
    - `SafeLogEntry` and `LocalLogService` read only the allowed local `logs/`
      directory and redact secrets, Authorization headers, DB URLs, raw env,
      hidden/debug/mature/private markers, and raw state-delta markers.

15. Local Diagnostics Bundle
    - `DiagnosticsBundleManifest` and `DiagnosticsBundleService` support
      preview, create, and validate for local redacted diagnostics bundles.

16. Offline Help Center
    - The frontend includes local help/onboarding topics for getting started,
      local-first workflow, modes, provider setup, mods, quality, backup,
      diagnostics/logs, privacy/secrets, and mature default-off behavior.

17. Startup Script Polish
    - Windows and shell launchers include dependency/preflight hints,
      `.env` presence hints, port guidance, local-only reminders, and safe
      frontend env behavior.

18. Desktop Packaging Docs
    - `docs/DESKTOP_PACKAGING.md` documents local-first positioning, package
      contents, exclusions, `.env`/API key/provider/log/database/build-output
      handling, backup/restore, diagnostics, and release checklist.

19. Local First Privacy Review
    - `docs/V3_0_DESKTOP_LOCAL_PRIVACY_AUDIT.md` was generated and reports no
      v3.0 release blocker.

20. Desktop Settings / Preferences Polish
    - Settings sections cover General, Local Privacy, Providers, Export,
      Debug, Backup / Restore, Diagnostics, Mature Module, UI Preferences, and
      Quality Gate without account/cloud/marketplace entries.

21. Safe Local File Path UX
    - Safe path summaries are used in workspace, recent-project, backup,
      diagnostics, and frontend local desktop surfaces.

22. First-Run Onboarding Flow
    - The frontend includes a local-only first-run onboarding flow with project
      selection, optional provider setup, and privacy/secrets explanation.

23. Desktop Shell Integration Smoke Tests
    - `backend/tests/test_v30_desktop_shell_smoke.py` covers launcher/scripts,
      packaging docs, no account/cloud/marketplace requirement, and safety
      boundaries.

24. Local Studio UX Regression Tests
    - `backend/tests/test_v30_local_studio_ux_regression.py` and
      `frontend/scripts/check-v30-local-studio-ux.mjs` cover v3.0 UI entries
      and safety copy.

25. v3.0 Integration Regression Tests
    - `backend/tests/test_v30_integration_regression.py` verifies local studio
      safe APIs, backup/restore, diagnostics/logs, Recent Projects, Recovery,
      frontend static safety, scripts/docs, and World boundary preservation.

## Boundary Review

Local-first:

- v3.0 does not add account login, cloud sync, online marketplace, remote
  package auto-download, telemetry upload, online diagnostics upload, or a
  signed desktop installer.
- Launcher, backup, restore, diagnostics, logs, recent projects, and recovery
  remain local-only workflows.

Secrets:

- API keys are not displayed in frontend values.
- Provider setup uses `api_key_env` and `secret_ref`, not plaintext key input.
- Startup scripts state that `LLM_API_KEY` is not read or injected into
  frontend env; the frontend receives only `VITE_API_BASE_URL`.
- Backup, diagnostics, logs, crash reports, exports, and desktop packaging
  exclude or redact `.env`, API keys, provider secrets, Authorization headers,
  raw env, database connection secrets, and sensitive local paths by default.

Backup / Restore / Diagnostics:

- Backup dry-run does not write files.
- Backup creation requires `explicit_confirm=true`.
- Restore dry-run does not write projects.
- Restore apply requires explicit confirmation.
- Existing target restore conflicts block apply unless overwrite is explicitly
  allowed.
- Corrupted backup without manifest is rejected.
- Diagnostics preview does not write files.
- Diagnostics bundle creation writes local redacted zip files under
  `exports/diagnostics/`.
- Diagnostics does not upload.

World Engine:

- Desktop/UI features are convenience surfaces over backend APIs.
- UI does not directly modify `GameState`.
- World-changing flows remain governed by backend validation,
  `StateDelta`, and `EventLog`.
- Provider Gateway remains the only model entry point.
- v3.0 tests do not call real providers.

Visibility:

- Normal UI and desktop summaries exclude hidden facts, NPC secrets, debug
  memory, raw prompts, raw `state_deltas`, mature/private content, API keys,
  provider secrets, and raw env.
- Debug/log/diagnostics debug behavior remains gated and redacted.

## Known Limitations

1. `docs/V3_0_ROADMAP.md` is not present in the current tree.
   - v3.0 implementation and acceptance are based on AGENTS.md, README,
     SPEC/WORLD_ENGINE/LLM_PROTOCOL, the implementation plan, current code,
     v3.0 contract review, v3.0 audits, and v3.0 tests.
   - This is a documentation completeness risk, not a runtime blocker.

2. v3.0 is not a formal desktop installer.
   - There is no signed installer, Tauri/Electron shell, auto-updater, or
     platform-specific distribution bundle.

3. Backup / Restore and Diagnostics are safe-summary first.
   - Current backup payloads are intentionally narrow and redacted.
   - Future richer backup of real project content should add manifest-level
     content inventory, checksums, privacy classification, and expanded tests.

4. Restore overwrite hardening can improve.
   - Current restore requires `explicit_confirm` and `allow_overwrite` for
     conflicts.
   - Future full restore should add overwrite-specific confirmation phrases.

5. PowerShell launcher command construction can be hardened.
   - `DATABASE_URL` is not printed and is not passed to frontend, but it is
     interpolated into the backend child process command string.
   - Future launcher polish should prefer process environment passing that
     avoids command-line exposure on the local machine.

6. Safe file picker is not a formal native desktop picker.
   - Restore and diagnostics validation can inspect user-provided zip paths.
   - Current validation checks zip extension, manifest, archive paths, and
     secret content; future desktop shell work should add a safe picker /
     validate API.

7. `workspace_id` is path-derived.
   - Display uses redacted paths and Recent Projects rejects secret-like
     entries, but future share/sync features should use random local ids.

## Acceptance Risks

No high-risk release blocker remains.

Non-blocking risks:

- Missing `docs/V3_0_ROADMAP.md`.
- Vite build reports a chunk size warning.
- Launcher, restore, diagnostics, and recent-project path handling have
  hardening opportunities listed above.

These risks do not block v3.0 acceptance because they do not leak secrets by
default, do not introduce online behavior, do not call real providers in tests,
and do not weaken World Engine fact authority.

## Recommended v3.1 Priorities

1. Novel Studio UI Pro.
   - Improve manuscript, outline, chapter, scene, arc, plot-thread,
     foreshadowing, export, and World -> Novel draft workflows on top of the
     stable local UI/desktop foundation.

2. Desktop hardening carryover.
   - Add overwrite-specific restore confirmation.
   - Harden launcher environment passing.
   - Add safe native file picker / path validation for formal desktop shell
     work.
   - Consider random local workspace ids.

3. Continue local-first release hygiene.
   - Keep account/cloud/marketplace/remote package download out of v3.1 scope.
   - Preserve Provider Gateway, visibility, export, backup, diagnostics, and
     `StateDelta` / `EventLog` boundaries.

## Final Status

v3.0 Local Desktop Studio Polish is accepted.

Final verification:

- Backend tests: passed, `1711 passed`.
- Frontend build: passed.
- Startup script safety/help check: passed.
- v3.0 audits: generated and non-blocking.
- v3.0 acceptance status: accepted with non-blocking follow-ups.
