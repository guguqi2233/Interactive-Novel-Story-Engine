# v1.7 Acceptance Report: Polished Desktop Studio

## Verdict

Accepted with documented limitations.

v1.7 is acceptable as a local-only Polished Desktop Studio prototype layer. The implemented scope strengthens desktop startup, safe configuration summaries, workspace selection, recent projects, local update notes, health checks, crash report viewing, startup diagnostics, launcher scripts, workspace templates, frontend desktop panels, and packaging safety documentation without weakening the v1.0-v1.6 world-engine authority boundary.

The release is not accepted as a complete desktop product, installer, online updater, cloud workspace, or complete implementation of every roadmap-named desktop workflow. The current code and docs correctly mark Log Viewer, Error Recovery Wizard, full Backup / Restore runtime, One-click Quality Gate, One-click World Export, and Offline Help runtime flows as partial or boundary-level surfaces.

## Verification Date

2026-05-20

## Verification Commands

```powershell
python -m pytest
cd frontend; npm.cmd run build
```

Results:

- `python -m pytest`: passed, `1551 passed in 110.96s`.
- `cd frontend; npm.cmd run build`: passed.

Notes:

- The frontend build emitted a Vite chunk-size warning for a bundle above 500 kB. This is non-blocking for v1.7 acceptance.
- PowerShell printed a local profile signing warning after commands. This is a local shell policy warning and did not fail either verification command.

## Scope Accepted

Accepted v1.7 scope:

1. Desktop Studio Boundary Contract is documented in `docs/DESKTOP_STUDIO_BOUNDARY.md` and enforced by `DesktopStudioPolicy`.
2. Desktop Launcher Pro scripts exist for PowerShell and shell-style environments, include help/preflight behavior, avoid API-key injection into frontend env, and write logs to ignored local paths.
3. Project Selector is implemented through safe workspace schemas and `/studio/workspaces` APIs.
4. Recent Projects are implemented with local-only safe summaries, redacted paths, remove, and clear behavior.
5. Local Config Manager exposes safe config summaries, issues, and `.env.example`-style template generation without returning secrets.
6. Local Update Notes are implemented as offline local release-note indexing.
7. Desktop Health Check is implemented with safe local status summaries.
8. Workspace Templates can create safe local starter workspaces without copying `.env` or API keys.
9. Crash Report Local Viewer is implemented behind debug APIs with secret and hidden-content redaction.
10. Desktop Startup Diagnostics is implemented as a CLI and launcher preflight support.
11. Desktop Settings UI and related frontend panels build successfully and consume safe summaries.
12. Desktop Packaging Safety Pass is documented, and `.gitignore` excludes local secrets, logs, crash reports, backups, caches, databases, frontend build output, and desktop build output patterns.
13. v1.7 integration and focused tests cover boundary, launcher diagnostics, workspace/recent project flows, config summaries, update notes, health checks, crash reports, templates, and packaging safety.

Partially accepted as boundary/policy/documented constraints, not complete runtime workflow implementations:

- Log Viewer: redaction policy exists, but dedicated `/debug/logs` runtime service is not complete.
- Error Recovery Wizard: safe recovery concepts are documented, but a full wizard service/UI is not complete.
- Backup / Restore: bundle policy and packaging rules are implemented/documented, but a dedicated desktop backup/restore runtime is not complete.
- One-click Quality Gate: existing quality systems remain available, but the v1.7 one-click desktop aggregator is not complete.
- One-click World Export: existing export/profile systems remain available, but the v1.7 one-click desktop flow is not complete.
- Offline Help Docs: local docs exist and are documented, but a dedicated offline help runtime index/page is not complete.

## Boundary Review

Desktop boundary:

- API keys remain backend-only secret config. Frontend-facing config uses safe booleans and labels, not secret values.
- Frontend config is limited to safe `VITE_API_BASE_URL` style usage and does not read `.env`.
- Launcher scripts do not hardcode API keys and do not inject provider secrets into frontend environment variables.
- Desktop tools do not directly mutate `GameState`, saves, content packs, prompt profiles, modules, or databases.
- Workspace and recent project APIs expose redacted paths and reject path traversal.
- Crash report APIs are debug-gated and redact API keys, Authorization headers, raw prompts, raw env, hidden fact text, and sensitive database details.
- Backup/export policy rejects `.env`, secret-like content previews, logs, caches, databases, desktop/frontend build outputs, local backup/crash directories, path traversal, absolute paths, and executable/script files.

LLM boundary:

- v1.7 desktop modules do not call LLM providers for launch, diagnostics, config, workspace selection, update notes, health checks, crash reports, templates, or packaging safety.
- Provider construction remains behind the existing provider factory/provider abstraction.
- LLM output still cannot modify `GameState`, decide rules, or act as a desktop recovery/packaging judge.

World-engine boundary:

- The world engine remains the only fact source.
- Runtime state changes remain governed by `StateDelta`, `EventLog`, validation, visibility, and existing backend services.
- Desktop Studio is a convenience surface around backend APIs, not a second engine or privileged state editor.

## Known Limitations

1. Log Viewer is not yet a complete `/debug/logs` runtime with logs-only file access and search/tail UI.
2. Error Recovery Wizard is not yet a full diagnostic and safe-step execution workflow.
3. Backup / Restore is not yet a full desktop runtime with archive creation, restore dry-run, checksum validation, conflict detection, and apply confirmation.
4. One-click Quality Gate is not yet a complete desktop aggregator over all validation, leak, scenario, module, migration, and performance checks.
5. One-click World Export is not yet a complete guided desktop export flow.
6. Offline Help Docs is not yet a complete in-app indexed help browser.
7. Desktop packaging remains a local launcher prototype, not a signed installer or public desktop release.
8. Frontend bundle size has a non-blocking Vite warning; code-splitting can be considered later.
9. PowerShell profile signing warnings can appear before/after commands on this machine; launcher docs treat this as non-blocking local shell configuration.

## Acceptance Risks

No high-risk blocker remains for v1.7 as a local-only desktop prototype.

Residual risks:

1. Future completion of Log Viewer and Backup / Restore must reuse `DesktopStudioPolicy` redaction, forbidden path, executable rejection, and secret scanning logic.
2. Future one-click workflows must be careful not to bypass existing validation gates, export profiles, quality gates, or import/export safety checks.
3. Desktop path handling should continue to minimize full path exposure in ordinary frontend views.
4. Any future packaged desktop shell must preserve the current rule that the shell calls backend APIs and never edits `GameState` directly.
5. A formal installer, code signing, auto-update, app-data directory policy, and bundle scanning are explicitly deferred beyond v1.7.

## Recommended v2.0 Priorities

1. Complete the deferred desktop runtime workflows: Log Viewer, Error Recovery Wizard, Backup / Restore, One-click Quality Gate, One-click World Export, and Offline Help.
2. Add a repeatable packaging scan command that inspects built frontend and desktop bundles for `.env`, API keys, raw env, logs, caches, databases, crash reports, and executable plugin content.
3. Move desktop runtime data defaults toward OS app-data directories before any formal packaging milestone.
4. Add dedicated frontend tests for API-disabled states and redaction-heavy desktop panels.
5. Define a formal desktop process lifecycle model for starting, stopping, and monitoring backend/frontend processes.
6. Keep investigating public-ready packaging only after secrets, backups, crash reports, and update behavior have formal local-only policies.
7. Continue schema/migration hardening for long-term v2.0 stability.

## Final Status

v1.7 is accepted for freeze as a local-only Polished Desktop Studio prototype with the limitations above.

The verified build and test status is green:

- Backend: `1551 passed`.
- Frontend: build passed.

Recommendation: proceed to v1.7 release notes and final freeze checks, while preserving the documented limitation that several roadmap-named desktop workflows remain partial/boundary-level rather than complete runtime features.
