# v3.0 Desktop Studio Contract Review

## Current Startup Flow

The current Local Desktop Studio startup flow is based on the local launcher
scripts:

- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`

Both launchers are local convenience wrappers around the existing backend and
frontend. They do not introduce a new runtime authority, account system, cloud
sync path, online marketplace, or desktop-side `GameState` mutation path.

The startup flow is:

1. Resolve repository, backend, frontend, and log directories.
2. Apply safe local defaults for backend host/port, frontend port, provider,
   authoring/debug/perf flags, and SQLite `DATABASE_URL` when not configured.
3. Optionally run safe startup diagnostics through
   `python -m backend.app.tools.startup_diagnostics`.
4. Check required local paths and dependencies, including Python project files,
   frontend dependencies, and optionally `frontend/dist` when built frontend
   mode is requested.
5. Start backend and frontend local processes unless `PreflightOnly` /
   equivalent dry-run mode is used.
6. Write stdout/stderr logs to ignored local `logs/` files.

The launcher preflight currently checks Python, Node/npm, backend imports,
frontend dependencies, ports, `.env` presence, SQLite database parent path,
workspace status, optional built frontend output, and previous crash report
status. In the v3.0 preparation check, PowerShell `-PreflightOnly` completed
successfully with safe local defaults and did not start processes.

The launcher passes only `VITE_API_BASE_URL` to the frontend process. It
explicitly states that `LLM_API_KEY` is not read by the script and is never
written to launcher logs.

## Current Desktop / Launcher Support

Desktop support is currently a local launcher and local-studio convenience
surface, not a formal installer or signed desktop distribution.

Current support includes:

- local PowerShell and shell launchers;
- safe startup diagnostics;
- local health checks;
- local config summaries;
- workspace / recent-project management;
- update-note surfaces;
- crash report storage and review APIs;
- desktop packaging guidance in `docs/DESKTOP_PACKAGING.md`;
- v2.9 local UI surfaces for diagnostics, settings/privacy, provider setup,
  Project Home, and mode entry points.

`docs/DESKTOP_PACKAGING.md` exists and defines local packaging safety checks. It
states that bundles, logs, diagnostics, crash reports, backups, and package
outputs must not include `.env`, API keys, databases, logs, caches,
`node_modules`, frontend build output, desktop build output, backups, crash
reports, or executable payloads unless an explicit future policy safely allows
them.

`docs/V3_0_ROADMAP.md` and `docs/V3_0_RESEARCH_PLAN.md` were not present during
this review. That is a planning gap for the next roadmap step, not a release
blocker for this contract review.

## Current Project Path Handling

Project path handling is provided through local workspace services and Studio
UI panels rather than through a cloud account or remote project registry.

Current project selection support includes:

- `GET /studio/workspaces`
- `POST /studio/workspaces`
- `POST /studio/workspaces/select`
- `GET /studio/workspaces/current`
- `DELETE /studio/recent-projects/{workspace_id}`

The frontend contains Project Selector and Recent Projects panels. Adding a
workspace stores a local reference; it does not import arbitrary files into the
project and does not modify active `GameState`.

Workspace creation from templates is also local. Template creation is designed
to reject unsafe paths and avoid copying `.env`, `node_modules`, `dist`, logs,
cache, or secret-like material. Recent project operations are local-only
navigation and bookkeeping operations.

Path display is expected to use safe summaries. Sensitive local paths should be
redacted in UI errors, diagnostics, quality reports, crash reports, and export
previews.

## Current Config Handling

Runtime configuration is still backend-owned and local.

Current behavior:

- `.env` is optional; absence is handled as a warning with safe defaults.
- `.env.example` may be used as a template but contains placeholders only.
- launcher scripts can set safe defaults such as local SQLite `DATABASE_URL`,
  `LLM_PROVIDER=mock`, and `VITE_API_BASE_URL`.
- frontend configuration receives only `VITE_API_BASE_URL`.
- local config summaries expose booleans and safe hints such as provider type,
  API key configured/not configured, and redacted database hints.

The frontend must not edit `.env`, read raw environment values, or display
provider secrets. The existing Settings / Privacy UI communicates that secrets
remain backend/local-resolver concerns.

## Current Provider Secret Boundary

Provider secrets remain behind backend-only provider configuration and secret
resolution.

Current boundary:

- Provider UI uses `api_key_env` and `secret_ref` references.
- The frontend does not expose a plaintext `api_key` field as the normal setup
  path.
- Provider status summaries expose configured/not configured booleans rather
  than secret values.
- Provider Profile Packs may carry `api_key_env` or `secret_ref` metadata, but
  must not contain real API keys.
- `ProviderSecretResolver` is documented as a backend-only resolver.
- The launcher explicitly avoids reading, printing, or injecting `LLM_API_KEY`
  into frontend environment variables.

Reviewed risk: search hits for `api_key`, `secret`, `LLM_API_KEY`, and
`OPENAI_API_KEY` are primarily schema fields, redaction code, validation rules,
docs, launch warnings, or safe references. No high-risk path was identified that
injects API keys into frontend code or desktop build output.

## Current Logs / Diagnostics

Logs and diagnostics are local-only and should be redacted by default.

Current support includes:

- launcher stdout/stderr logs in ignored local `logs/`;
- startup diagnostics through `backend.app.tools.startup_diagnostics`;
- desktop health checks;
- local config summaries;
- crash report APIs under debug routes;
- frontend diagnostics safe-preview/export from v2.9;
- API client error redaction for API-key-like text, Authorization headers,
  raw environment markers, sensitive paths, hidden facts, raw prompts, and raw
  `state_deltas`.

Crash reports are stored locally and redacted. Debug and crash report APIs are
expected to remain gated by debug configuration. Normal diagnostics must not
include raw prompts, hidden facts, NPC secrets, provider secrets, raw env, raw
`GameState`, raw `state_deltas`, or full sensitive local paths.

The current v2.9 Diagnostics Export is frontend-side safe summary by default.
If v3.0 adds backend diagnostics export endpoints, the backend must repeat the
same filtering server-side rather than relying on frontend filtering alone.

## Current Backup / Restore

Backup and restore support currently exists mainly through save migration,
project import/export safety policies, and documented desktop backup
boundaries. A complete one-click desktop Backup / Restore runtime is not yet
implemented.

Current capabilities:

- save migration can create pre-migration backups;
- restore of pre-migration backup requires explicit confirmation;
- migration recovery reports expose backup ids and restore availability;
- export/import profiles and package policies reject secrets and unsafe paths;
- desktop policy validates backup bundles against forbidden names, suffixes,
  directories, and secret-like content.

Current gaps:

- no complete desktop-wide Backup / Restore wizard is present;
- no dedicated v3.0 backup manifest/checksum UX exists yet;
- restore is available for migration recovery, but not a full local project
  restore product experience.

v3.0 should treat Backup / Restore as a first-class desktop polish area, but
must keep it dry-run first, explicit-confirm, path-safe, checksum/manifest
validated, and secret-filtered by default.

## Current Packaging Risks

No high-risk packaging blocker was found in the reviewed baseline. The main
risks are future implementation risks:

- accidentally bundling `.env` or local provider secrets;
- accidentally including local databases, logs, caches, backups, crash reports,
  `node_modules`, `frontend/dist`, or desktop build outputs in shareable
  artifacts;
- relying on frontend-only filtering for future diagnostics export;
- displaying full local paths in UI, diagnostics, or crash reports;
- adding a remote package downloader or online marketplace entry while v3.0 is
  intended to remain local-first;
- treating the desktop shell as a second authority that can bypass backend
  validation, `StateDelta`, `EventLog`, visibility, or provider boundaries.

Existing mitigations:

- `docs/DESKTOP_PACKAGING.md` lists packaging safety checks and forbidden
  artifacts;
- `DesktopStudioPolicy` blocks secret-like env exposure, unsafe frontend env
  names, forbidden backup names, database/log/cache-like suffixes, build output
  directories, and secret-like content previews;
- launcher scripts only pass `VITE_API_BASE_URL` to the frontend;
- frontend and backend redaction helpers already cover common secret and
  sensitive-path patterns;
- git-tracked forbidden artifact scans during v3.0 preparation did not report
  tracked `.env`, database, log, cache, `node_modules`, `frontend/dist`,
  desktop output, backup, or crash-report files.

## Recommended v3.0 Desktop Contract

v3.0 should define Local Desktop Studio Polish around these rules:

1. Desktop shell is a convenience surface over local backend APIs, not a second
   source of world authority.
2. Desktop UI must not directly mutate `GameState`.
3. Any world-changing operation must continue to use backend validation and the
   existing `StateDelta` / `EventLog` boundary.
4. Startup, diagnostics, logs, crash reports, backup, restore, and packaging
   must remain local-first and secret-redacted.
5. Launcher scripts may pass only safe frontend variables such as
   `VITE_API_BASE_URL`.
6. Provider API keys must remain in env/local secret resolver paths and must not
   enter frontend code, logs, diagnostics, crash reports, backups, package
   manifests, or desktop artifacts.
7. Project Picker and Recent Projects should manage local workspace references
   only; they must not import arbitrary files or read secrets.
8. Backup / Restore must be dry-run first, explicit-confirm on apply,
   path-safe, checksum/manifest-validated, and secret-filtered by default.
9. Diagnostics Export must be safe-summary-only by default. Debug export must be
   explicit, gated, and redacted.
10. Log Viewer and Crash Report Viewer must redact secrets, raw env, prompts,
    hidden facts, raw `state_deltas`, and sensitive local paths.
11. Packaging must reject `.env`, API keys, databases, logs, caches,
    `node_modules`, `frontend/dist`, desktop build outputs, backups, crash
    reports, executables, path traversal, and secret-like content by default.
12. Offline help and local update notes must be bundled/static/local and must
    not load remote content by default.
13. v3.0 must not add an account system, cloud sync, online marketplace, online
    platform, telemetry upload, remote package registry, or remote package
    auto-download.

Recommended first v3.0 implementation slices:

- Desktop Studio Roadmap and acceptance criteria.
- Launcher preflight and error-recovery UX polish.
- Project Picker / Recent Projects polish.
- Backup / Restore contract and dry-run UX.
- Diagnostics / Log Viewer / Crash Report polish.
- Packaging safety checklist automation.
- Local Desktop Studio acceptance report and security/privacy audit.
