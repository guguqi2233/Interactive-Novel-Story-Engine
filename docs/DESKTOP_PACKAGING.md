# Desktop Packaging Prototype

## Status

v0.7.7 keeps desktop packaging as a local studio launcher prototype. It improves
the v0.6 script path with dependency checks, clearer status output, an optional
built-frontend preview mode, and a Unix-like shell launcher. It is not a formal
installer, signed application, auto-updater, or public distribution package.

No Tauri or Electron dependency is introduced in v0.7.7. The current safest
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
- `frontend/dist/index.html` when `-UseBuiltFrontend` is used

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
```

The shell script is a convenience prototype. Windows PowerShell remains the
primary supported local desktop launcher for this repository.

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
- Python and pytest caches
- TypeScript build info
- common installer artifacts such as `*.msi`, `*.dmg`, `*.AppImage`

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

### Current v0.7.7 Decision

Do not add Tauri or Electron yet. The local authoring, migration, graph,
evaluation, performance, and provider flows are still changing, so a script
launcher remains easier to audit and safer for local-only development.

## Not In This Prototype

v0.7.7 does not include:

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

1. Keep using the launcher while v0.7 studio workflows stabilize.
2. Add explicit status/stop commands if long-running local processes become
   confusing.
3. Move SQLite, logs, worlds, and mods to an OS-specific app data directory
   before formal packaging.
4. Decide Tauri vs Electron only after file-dialog, process-lifecycle, and
   distribution requirements are clearer.
5. Add automated bundle scanning before any installer milestone.
