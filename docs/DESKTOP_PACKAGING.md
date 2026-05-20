# Desktop Packaging Safety Pass

## Status

v1.7 keeps desktop packaging as a local-only studio prototype. The supported
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

## Backup, Export, And Crash Reports

Backups and world exports are local bundle workflows, not cloud sync. They must
default to safe profiles and exclude `.env`, API keys, raw env, logs, caches,
database connection secrets, frontend build outputs, desktop build outputs,
and executable files.

Crash reports are local-only. They may store redacted exception type, component,
safe message, redacted stack, and safe context summary. They must not include
API keys, raw prompts, hidden fact text, raw env, or database passwords.

Current v1.7 implementation note: the desktop boundary policy, crash report
viewer, health check, startup diagnostics, workspace selector, update notes,
and launcher scripts are implemented. Dedicated desktop Backup / Restore,
Log Viewer, Error Recovery Wizard, One-click Quality Gate, One-click World
Export, and Offline Help runtime flows are still partial or boundary-level in
the current code. Do not describe those flows as complete desktop runtime
features until their APIs/CLI/UI are implemented and tested.

## Tauri / Electron Review

Tauri and Electron remain future options only. v1.7 does not add either runtime
or produce an installer. A future desktop shell must preserve the same boundary:
the shell calls backend APIs and cannot become a second engine, a privileged
state editor, or a secret store exposed to frontend code.

## Not In v1.7

v1.7 does not include:

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

A v1.7 desktop packaging safety pass is acceptable only when:

- tests and frontend build pass;
- `.gitignore` covers all local secret/runtime/build outputs listed above;
- `git ls-files` confirms excluded outputs are not tracked;
- script and repository scans find no real API keys;
- documentation states the local-only prototype limits clearly;
- no generated bundle contains `.env`, API keys, logs, caches, database files,
  raw prompts, raw env, hidden facts, or executable plugin code.
