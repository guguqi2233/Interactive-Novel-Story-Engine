# Desktop Startup Reliability

## Status

v1.0 keeps desktop packaging as a local studio launcher prototype and focuses
on startup reliability. The launcher scripts check Python, Node/npm, installed
dependencies, `.env` guidance, `DATABASE_URL`, occupied ports, backend and
frontend health, studio status, and safe local feature flags. They are not a
formal installer, signed application, auto-updater, or public distribution
package.

No Tauri or Electron dependency is introduced in v1.0. The current safest
path is still a transparent local launcher that starts the existing FastAPI
backend and Vite frontend without changing backend API semantics.

## Recommended Scheme

Use the local launcher scripts:

- Windows: `scripts/start_local_studio.ps1`
- macOS/Linux-style shells: `scripts/start_local_studio.sh`

The scripts start:

- backend: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- frontend dev mode: `npm run dev -- --host 127.0.0.1 --port 5173`
- frontend built preview mode: `npm run preview -- --host 127.0.0.1 --port 5173`
- browser: `http://127.0.0.1:5173`, unless disabled

Logs are written to `logs/`, which is ignored by git.

## Windows Launcher

Run from the repository root:

```powershell
.\scripts\start_local_studio.ps1
```

Useful options:

```powershell
.\scripts\start_local_studio.ps1 -NoBrowser
.\scripts\start_local_studio.ps1 -BackendPort 8000 -FrontendPort 5173
.\scripts\start_local_studio.ps1 -UseBuiltFrontend
.\scripts\start_local_studio.ps1 -SkipDependencyCheck
.\scripts\start_local_studio.ps1 -PreflightOnly
```

`-UseBuiltFrontend` requires:

```powershell
cd frontend
npm run build
```

The Windows script checks for:

- `python`
- `npm`
- repository `pyproject.toml`
- `frontend/package.json`
- `frontend/node_modules`
- importable backend dependencies: `fastapi`, `uvicorn`, `pydantic`, and
  `app.main`
- `.env` presence, with a safe prompt to copy `.env.example` if missing
- non-empty `DATABASE_URL`, defaulting to `sqlite:///./world_engine.db`
- backend and frontend port availability before startup
- `frontend/dist/index.html` when `-UseBuiltFrontend` is used

After launch it checks:

- backend `/health`
- backend `/studio/status`
- frontend URL availability

The checks are readiness hints, not formal process supervision. If a check times
out, inspect `logs/desktop-backend.err.log` or `logs/desktop-frontend.err.log`.

## Shell Launcher

For macOS/Linux-style shells:

```bash
bash scripts/start_local_studio.sh
```

Useful options:

```bash
bash scripts/start_local_studio.sh --no-browser
bash scripts/start_local_studio.sh --backend-port 8000 --frontend-port 5173
bash scripts/start_local_studio.sh --use-built-frontend
bash scripts/start_local_studio.sh --skip-dependency-check
bash scripts/start_local_studio.sh --preflight-only
bash scripts/start_local_studio.sh --health-timeout-seconds 45
```

The shell script is a convenience prototype. Windows PowerShell remains the
primary supported local desktop launcher for this repository. On macOS and
Linux, browser opening depends on `open` or `xdg-open`; if neither is present,
the script prints the URL for manual opening.

The shell script performs the same preflight class as the Windows script:
Python, npm, dependency folders, backend imports, `DATABASE_URL`, port
availability, `.env` guidance, built frontend presence when requested, and
post-launch health checks.

## Runtime Status Output

The launchers print safe local status:

- backend URL
- frontend URL
- frontend mode
- log directory
- `LLM_PROVIDER`
- `ENABLE_AUTHORING_API`
- `ENABLE_DEBUG_API`
- `ENABLE_PERF_LOGGING`
- `VITE_API_BASE_URL`
- backend `/health` status
- backend `/studio/status` reachability
- frontend availability
- database URL configured, without printing secret environment dumps
- warnings for `LLM_PROVIDER=openai` without `LLM_API_KEY`
- warnings for `LLM_PROVIDER=local_http` without `LOCAL_LLM_BASE_URL`

They do not print `LLM_API_KEY`, environment dumps, database contents, prompts,
raw `GameState`, or raw `state_deltas`.

## Environment Variables

The launchers read or set safe local defaults:

- `DATABASE_URL`
  - default: `sqlite:///./world_engine.db`
  - local SQLite files are ignored by git.
- `LLM_PROVIDER`
  - default: `mock`
  - use real providers only when explicitly configured in the shell.
- `LLM_API_KEY`
  - not set by the scripts.
  - not embedded into frontend code.
  - must stay in a local shell environment or ignored `.env`.
- `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT_SECONDS`,
  `LOCAL_LLM_JSON_MODE`
  - passed through for local model provider experiments.
  - not secret by default, but still not exposed as frontend `VITE_` variables.
- `ENABLE_DEBUG_API`
  - default: `true` for local development.
- `ENABLE_AUTHORING_API`
  - default: `false`.
- `ENABLE_PERF_LOGGING`
  - default: `false`.
- `VITE_API_BASE_URL`
  - default: `http://127.0.0.1:8000`.

## Secret Handling

The prototype must not:

- commit `.env`;
- write API keys to source, docs examples, frontend assets, logs, or saves;
- pass `LLM_API_KEY` into Vite as a `VITE_` variable;
- store credentials in `frontend/dist`;
- include `.env` in any desktop build output;
- upload telemetry.

If a user sets `LLM_PROVIDER=openai`, they must provide `LLM_API_KEY` through
their own local shell or ignored `.env` workflow. The launcher does not assign
or print it.

## Common Startup Problems

### Port Occupied

If the backend or frontend port is already in use, the launcher exits before
starting a second copy. Stop the existing process or choose different ports:

```powershell
.\scripts\start_local_studio.ps1 -BackendPort 8010 -FrontendPort 5174
```

```bash
bash scripts/start_local_studio.sh --backend-port 8010 --frontend-port 5174
```

### Missing Environment

The launcher can run with safe defaults, but `.env` is the expected local place
for durable configuration. Create it from the example and keep it untracked:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

### Missing npm Install

If `frontend/node_modules` is missing, install frontend dependencies:

```bash
cd frontend
npm install
```

### Missing API Key

`LLM_PROVIDER=mock` and `local_stub` need no API key. If
`LLM_PROVIDER=openai`, provide `LLM_API_KEY` in your local shell or ignored
`.env`; do not add it to frontend files, docs, commits, or logs.

### Local Model Unavailable

If `LLM_PROVIDER=local_http`, set `LOCAL_LLM_BASE_URL` and make sure the local
model service is running before using LLM-backed flows. The launcher warns when
the URL is missing but does not start any model service.

### Health Check Timeout

If `/health`, `/studio/status`, or the frontend URL times out, inspect:

- `logs/desktop-backend.err.log`
- `logs/desktop-frontend.err.log`

The scripts are startup helpers, not process supervisors. Close the spawned
backend/frontend terminals or processes manually when finished.

## Platform Notes

- Windows: PowerShell is the primary launcher path for v1.0. Use
  `-PreflightOnly` to check dependencies without starting processes.
- macOS: use `bash scripts/start_local_studio.sh`; browser opening depends on
  the `open` command.
- Linux: use `bash scripts/start_local_studio.sh`; browser opening depends on
  `xdg-open`.
- All platforms: this is a local-only prototype. It does not create a signed
  app, installer, auto-update channel, account system, or cloud sync.

## Git Ignore Expectations

The repository ignores local and desktop build artifacts:

- `.env`
- `*.db`
- `logs/`
- `node_modules/`
- `dist/`
- `frontend/dist/`
- `desktop-dist/`
- `release/`
- `src-tauri/target/`
- `src-tauri/gen/`
- `desktop-build/`
- `desktop-release/`
- `electron-dist/`
- `tauri-dist/`
- `installers/`
- Python and pytest caches
- TypeScript build info
- common installer artifacts such as `*.msi`, `*.dmg`, `*.AppImage`, `*.deb`,
  `*.rpm`, and `*.pkg`

Before any future formal installer milestone, run a bundle scan to confirm no
secret files or API keys are included.

## Tauri / Electron Review

### Tauri

Tauri remains the preferred candidate for a future smaller desktop shell. It
would require Rust tooling, sidecar backend packaging, local data directory
rules, and an explicit secret handling design.

### Electron

Electron remains viable if Node-based process management becomes more valuable
than bundle size. It would still need the same local data and secret policies.

### Current v1.0 Decision

Do not add Tauri or Electron yet. The local authoring, migration, graph,
evaluation, performance, and provider flows are still changing, so a script
launcher remains easier to audit and safer for local-only development.

## Not In This Prototype

v1.0 does not include:

- formal installer generation;
- code signing;
- auto-update;
- account login;
- cloud sync;
- Tauri or Electron dependency setup;
- frontend storage of provider keys;
- backend API semantic changes;
- automatic process shutdown when the browser closes.

## Future Path

Recommended next steps:

1. Keep using the launcher while v1.0 local studio workflows stabilize.
2. Add explicit status/stop commands if long-running local processes become
   confusing.
3. Move SQLite, logs, worlds, and mods to an OS-specific app data directory
   before formal packaging.
4. Decide Tauri vs Electron only after file-dialog, process-lifecycle, and
   distribution requirements are clearer.
5. Add automated bundle scanning before any installer milestone.
