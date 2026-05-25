# Desktop Packaging Safety Pass

## v3.0 Local Desktop Studio Positioning

v3.0 focuses on **Local Desktop Studio Polish**. The desktop surface is a
local launcher plus local backend/frontend UX, not a formal installer, signed
app, account client, cloud sync client, marketplace client, telemetry uploader,
or auto-updater. Packages, backups, exports, diagnostics bundles, logs, and
crash reports must not include `.env`, API keys, provider secrets, databases,
caches, mature/private content, or build outputs by default.

## Status

v3.0 keeps desktop packaging as a local-only studio prototype. The supported
workflow is still a transparent launcher that starts the FastAPI backend and
the Vite frontend. There is no formal installer, code signing, automatic
update channel, cloud sync, account system, marketplace, or telemetry upload.

The desktop layer is a convenience shell around the backend API. It must not
modify `GameState`, write saves, apply content, or enable gameplay modules
outside the existing backend services and validation gates.

## Supported Local Launcher

Use the local launcher scripts from the repository root:

- Windows: `scripts/start_local_studio.ps1`
- macOS/Linux-style shells: `scripts/start_local_studio.sh`

The launchers can run safe startup diagnostics before starting services:

```powershell
python -m backend.app.tools.startup_diagnostics
.\scripts\start_local_studio.ps1 -PreflightOnly
```

```bash
python -m backend.app.tools.startup_diagnostics
bash scripts/start_local_studio.sh --preflight-only
```

The scripts start the backend, the frontend dev server or built preview, write
local logs under `logs/`, and optionally open `http://127.0.0.1:5173`.

## Packaging Safety Checklist

Before any local desktop bundle or handoff archive is created, verify:

1. `python -m pytest` passes.
2. `cd frontend && npm.cmd run build` passes on Windows, or the platform
   equivalent `npm run build` passes.
3. `git ls-files` does not include local secrets or generated outputs:
   `.env`, database files, logs, crash reports, backups, caches,
   `node_modules`, `frontend/dist`, `desktop-dist`, `desktop_build`,
   `desktop-build`, `desktop-release`, or `release`.
4. Scripts do not contain real `sk-...` API keys or provider secrets.
5. Frontend build artifacts do not contain `.env` contents, `LLM_API_KEY`,
   `OPENAI_API_KEY`, `Authorization` headers, raw prompts, or raw env dumps.
6. Exported bundles use safe export profiles and exclude `.env`, API keys,
   database connection config, logs, cache directories, and executable files.
7. Crash reports and log views are local-only and redacted.
8. Backups exclude `.env`, API keys, raw env, logs, caches, frontend build
   outputs, and desktop build outputs by default.
9. The launcher only passes `VITE_API_BASE_URL` to the frontend; it never
   injects API keys into `VITE_` variables.
10. No desktop workflow calls a real LLM provider unless the user explicitly
    configures the backend provider for normal local use.

## Git Ignore Expectations

`.gitignore` must exclude local secrets, runtime files, and desktop build
outputs:

- `.env`
- `frontend/.env`
- `*.db`, `*.sqlite`, `*.sqlite3`, and journal files
- `*.log`
- `logs/`
- `crash-reports/`
- `backups/`
- `.cache/`, `cache/`, and `caches/`
- `node_modules/`
- `dist/`
- `frontend/dist/`
- `desktop-dist/`
- `desktop_build/`
- `desktop-build/`
- `desktop-release/`
- `electron-dist/`
- `tauri-dist/`
- `release/`
- `installers/`
- `src-tauri/target/`
- `src-tauri/gen/`
- common installer artifacts such as `*.msi`, `*.dmg`, `*.AppImage`, `*.deb`,
  `*.rpm`, `*.pkg`, and `*.exe`

The repository should not track generated desktop outputs. If a future formal
packaging milestone needs checked-in metadata, add a narrow exception for that
metadata only, not for produced bundles.

## Frontend Build Safety

The Vite frontend only receives `VITE_API_BASE_URL` from the launcher. API keys,
provider secrets, raw env values, database URLs, prompt text, hidden facts,
debug memory, and raw `state_deltas` must not be written to frontend source or
`frontend/dist`.

Recommended local scan after a build:

```powershell
rg -n "sk-|LLM_API_KEY|OPENAI_API_KEY|Authorization|DATABASE_URL|raw env" frontend/dist scripts README.md docs/DESKTOP_PACKAGING.md
```

Fake test keys that are explicitly named as fake test fixtures may appear in
tests, but real-looking keys must block release.

## Launcher Safety

The launcher scripts may:

- check Python, Node/npm, dependencies, ports, `.env` presence, database path,
  workspace status, build output presence, and prior crash report count;
- start backend and frontend local processes;
- write stdout/stderr logs to ignored local `logs/`;
- print safe status summaries and recovery hints.

The launcher scripts must not:

- hardcode API keys;
- print API keys or raw env;
- pass `LLM_API_KEY` into the frontend;
- modify `GameState`, saves, world packs, content packs, modules, or packages;
- install dependencies unless a future explicit user-confirmed option is added;
- upload telemetry or crash reports;
- start a real LLM service.

## Backup, Restore, Diagnostics, Logs, And Crash Reports

Backups, restores, diagnostics bundles, log views, and world exports are local
workflows, not cloud sync. They must default to safe profiles and exclude
`.env`, API keys, provider secrets, raw env, logs, caches, database connection
secrets, database files, frontend build outputs, desktop build outputs,
debug-only data, mature/private content, backups, crash reports, and executable
files unless a future explicit safe policy says otherwise.

Crash reports are local-only. They may store redacted exception type, component,
safe message, redacted stack, and safe context summary. They must not include
API keys, raw prompts, hidden fact text, raw env, or database passwords.

Current v3.0 implementation note: desktop boundary policy, crash report viewer,
health check, startup diagnostics, workspace selector, recent projects, local
config summaries, redacted log viewer, diagnostics bundle preview/create,
backup/restore dry-run/apply-confirmed boundary, recovery suggestions, offline
help UI, and launcher scripts are local-only surfaces. They remain safety-first
desktop polish, not cloud backup, online diagnostics, or a signed installer.

Additional v3.0 implementation note: Local Studio safe-summary endpoints
(`/local-studio/status`, `/local-studio/health`,
`/local-studio/config-summary`, `/local-studio/startup-checks`,
`/local-studio/recent-errors`) are desktop convenience APIs. Backup,
diagnostics, recovery, and log APIs are local-only and redacted by default.
They must not be treated as a cloud diagnostics channel, remote support upload,
or installer packaging mechanism.

## v3.5 Provider Connectivity Packaging Boundary

v3.5 adds local Provider Connectivity, connection testing, model discovery,
model assignment, usage summaries, and diagnostics review surfaces. These are
local Provider Gateway configuration and observability workflows, not API
resale, online accounts, cloud sync, an online provider platform, or real
provider CI checks.

Desktop bundles, diagnostics bundles, backups, exports, logs, crash reports,
and frontend builds must not contain:

- `transient_api_key` values used for a one-time connection test or model-list
  fetch;
- API key values resolved from `api_key_env`;
- `secret_ref` values or backend-only secret resolver output;
- Authorization headers, relay tokens, token-like base URL query/path segments,
  raw provider errors, or raw provider responses;
- provider prompt/output bodies, hidden facts, NPC secrets, debug memory, raw
  `GameState`, or raw `state_deltas`.

Provider tests and CI packaging checks must use fake provider/fake client
paths. A packaged local desktop build may let a user configure local provider
profiles at runtime, but it must not ship real provider credentials or assume a
real network connection during verification.

## v3.6 Performance / Accessibility Packaging Boundary

v3.6 adds local performance and accessibility polish for route-level lazy
loading, large-list windowing, safe cache summaries, Provider status/model-list
performance, keyboard shortcuts, focus management, reduced motion, loading
skeletons, and ErrorBoundary handling. These changes do not relax desktop
packaging exclusions and do not introduce online services.

Desktop bundles, diagnostics, backups, exports, logs, crash reports, and
frontend builds must continue to exclude:

- `.env`, raw env, API keys, provider secrets, Authorization headers, and
  `transient_api_key` values;
- raw provider responses, raw provider errors, raw prompts, raw outputs, token-
  like base URL secrets, and secret resolver output;
- hidden facts, NPC secrets, debug memory, raw `GameState`, raw
  `state_deltas`, mature/private content, database files, logs, caches,
  `node_modules`, `frontend/dist` as a source-controlled artifact, desktop
  build outputs, backups, crash reports, diagnostics bundles, and executable
  package payloads.

Provider connection status caches and frontend safe API caches are local safe
metadata caches only. They may contain status, timestamps, latency, model
counts, safe report summaries, and stale flags, but they must not contain
secrets or raw provider/debug payloads. No v3.6 performance cache should be
treated as a credential store, cloud sync mechanism, telemetry uploader, or
provider availability monitor that runs real network checks during packaging.

## v3.7 Local Playable Complete Product CN Packaging Boundary

v3.7 packages the local product experience as a Chinese Local Playable
Complete Product. The default packaged frontend should open to a Chinese
player/creator Home for Project, Provider/model setup, Novel, Tavern RP, and
World play. Debug / QA / Authoring / Mods / Diagnostics / Product Readiness
remain advanced tools; packaging must not turn them into default first-screen
debug surfaces. It is still local-first software, not an account client, cloud
sync client, online marketplace, remote package downloader, online writing/RP/
play platform, API resale service, or telemetry uploader.

Desktop bundles, handoff archives, backups, exports, diagnostics, logs, crash
reports, and frontend build artifacts must not contain:

- `.env`, raw env, API keys, provider secrets, Authorization headers,
  one-time provider test keys, `api_key_env` resolved values, or `secret_ref`
  resolved values;
- raw provider responses, raw provider errors, raw prompts, raw outputs, token-
  like base URL path/query values, or secret resolver output;
- hidden facts, NPC secrets, debug memory, raw `GameState`, raw
  `state_deltas`, mature/private content, database files, local logs, caches,
  build outputs, backups, crash reports, diagnostics bundles, or executable
  package payloads.

v3.7 product readiness, workflow checker, Provider checklist, privacy/safety
review, acceptance checklist, and demo project assets are safe-summary local
advanced surfaces. They must use fake/local_stub providers in tests and CI,
must not call real providers during packaging verification, and must not upload
project data. Local users may manually configure and test real providers from
the Provider UI, but packaged smoke tests must stay fake-provider only. The
demo project is a local sample only; it must not ship real
credentials, `.env`, databases, logs, caches, mature/private content,
debug/raw state deltas, or executable plugin code.

## v3.8 Chinese Product UX Packaging Boundary

v3.8 packages the same local-first application with a more polished Chinese
product experience. The default packaged UI should open to a Chinese
player/creator Home that highlights writing novels, Tavern RP, open-world
play, opening/creating projects, Demo project, Provider/model-service setup,
local safety, and next-step guidance. Debug, QA, Authoring / Mods,
Diagnostics, Product Readiness, EventLog, StateDelta, and Hidden Leak reports
remain Advanced Tools and must not become default first-screen panels.

Packaging and handoff rules for v3.8:

- Backend-unavailable recovery may show reconnect/startup-guide/diagnostics/
  settings actions, but it must not print raw env, API keys, Authorization
  headers, stack traces, sensitive paths, hidden facts, or raw `state_deltas`.
- Provider setup may allow a local user to manually configure and test real
  providers, but packaged smoke tests, CI, and release verification must use
  fake providers, `mock`, `local_stub`, or injected fake clients.
- Desktop bundles, archives, diagnostics, backups, exports, logs, crash
  reports, and frontend build artifacts must not contain API keys,
  `transient_api_key`, `.env`, raw env, provider secrets, Authorization
  headers, raw provider responses, raw provider errors, raw prompts, raw
  outputs, hidden facts, NPC secrets, mature/private content, raw
  `state_deltas`, databases, logs, caches, `node_modules`, `frontend/dist` as a
  source-controlled artifact, backups, crash reports, or executable plugin
  payloads.
- v3.8 does not add accounts, cloud sync, online marketplace, remote package
  download, online writing/RP/play, API resale, telemetry upload, or
  arbitrary-code plugins.
- v3.8 does not change World Engine, Provider Gateway, StateDelta/EventLog,
  visibility, backup/diagnostics filtering, or debug-gating boundaries.

## Tauri / Electron Review

Tauri and Electron remain future options only. v3.0 does not add either runtime
or produce an installer. A future desktop shell must preserve the same boundary:
the shell calls backend APIs and cannot become a second engine, a privileged
state editor, or a secret store exposed to frontend code.

## Not In v3.0

v3.0 does not include:

- formal installer generation;
- code signing;
- automatic updates;
- online marketplace;
- account login;
- cloud sync;
- telemetry upload;
- bundling `.env` or API keys;
- frontend direct reads of `.env`;
- desktop shell direct `GameState` writes.

## Final Packaging Gate

A v3.0 desktop packaging safety pass is acceptable only when:

- tests and frontend build pass;
- `.gitignore` covers all local secret/runtime/build outputs listed above;
- `git ls-files` confirms excluded outputs are not tracked;
- script and repository scans find no real API keys;
- documentation states the local-only prototype limits clearly;
- no generated bundle contains `.env`, API keys, logs, caches, database files,
  raw prompts, raw env, hidden facts, or executable plugin code.
