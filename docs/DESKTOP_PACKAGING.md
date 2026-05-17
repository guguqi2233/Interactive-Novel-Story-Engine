# Desktop Packaging Prototype

## Status

v0.6.12 is a local desktop packaging prototype, not a formal installer. It adds
a documented launch path for running the FastAPI backend and Vite frontend as a
local studio without changing backend API semantics.

The project currently has no Tauri or Electron foundation. To avoid adding a
large runtime dependency before the local studio workflows settle, v0.6 uses a
small PowerShell launcher first.

## Option Review

### Tauri

Value:
- Small desktop shell and good long-term fit for local-first tooling.
- Can wrap the React frontend and launch a sidecar backend later.

Risks:
- Requires Rust toolchain and sidecar process packaging decisions.
- Needs careful local data directory handling for SQLite, worlds, mods, and
  logs.
- Requires a deliberate secret-handling design so `LLM_API_KEY` is never baked
  into frontend assets.

Recommendation:
- Good candidate after v0.6, once migration, authoring, graph, and eval flows
  stabilize.

### Electron

Value:
- Mature desktop app ecosystem and straightforward Node process management.
- Easier to bundle a local web UI and spawn backend helpers.

Risks:
- Larger dependency and bundle footprint.
- More surface area for local security mistakes.
- Still needs the same secret, database, and local path policy.

Recommendation:
- Viable, but not the first prototype unless Node-based desktop integration
  becomes necessary.

### Local Launcher Script

Value:
- Zero new packaging dependency.
- Transparent and easy to audit.
- Works with the current FastAPI + Vite development model.
- Keeps API keys in the caller's environment, not in frontend bundles.

Risks:
- Not a polished desktop installer.
- Windows-focused initial script.
- Process lifecycle is manual; closing browser does not stop background
  backend/frontend processes.

Recommendation:
- Use for v0.6. It is the safest small slice for local studio hardening.

## Added Prototype Script

Run from the repository root:

```powershell
.\scripts\start_local_studio.ps1
```

Useful options:

```powershell
.\scripts\start_local_studio.ps1 -NoBrowser
.\scripts\start_local_studio.ps1 -BackendPort 8000 -FrontendPort 5173
```

The script starts:

- backend: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- frontend: `npm run dev -- --host 127.0.0.1 --port 5173`
- browser: `http://127.0.0.1:5173`

Logs are written to `logs/`, which is ignored by git.

## Environment Variables

The launcher reads or sets safe local defaults:

- `DATABASE_URL`
  - default: `sqlite:///./world_engine.db`
  - local SQLite files are ignored by git.
- `LLM_PROVIDER`
  - default: `mock`
  - use real providers only when explicitly configured in the shell.
- `LLM_API_KEY`
  - not set by the script.
  - not embedded into frontend code.
  - must stay in local environment or local untracked `.env`.
- `ENABLE_DEBUG_API`
  - default: `true` for local development.
- `ENABLE_AUTHORING_API`
  - default: `false`.
- `VITE_API_BASE_URL`
  - default: `http://127.0.0.1:8000`.

## Secret Handling

The prototype must not:

- commit `.env`;
- write API keys to source, docs examples, frontend assets, logs, or saves;
- pass `LLM_API_KEY` into Vite as a `VITE_` variable;
- store credentials in `frontend/dist`;
- upload telemetry.

The launcher intentionally does not mention or assign an API key. If a user
sets `LLM_PROVIDER=openai`, they must provide `LLM_API_KEY` through their own
local shell or ignored `.env` workflow.

## Git Ignore Expectations

The repository should continue ignoring:

- `.env`
- `*.db`
- `logs/`
- `node_modules/`
- `dist/`
- `frontend/dist`
- Python and pytest caches

The current `.gitignore` already covers these categories through `.env`,
`*.db`, `logs/`, `node_modules/`, `dist/`, `__pycache__/`, `.pytest_cache/`,
and `*.tsbuildinfo`.

## Not In This Prototype

v0.6.12 does not include:

- formal installer generation;
- code signing;
- auto-update;
- account login;
- cloud sync;
- Tauri or Electron dependency setup;
- frontend storage of provider keys;
- backend API semantic changes.

## Future Path

Recommended next steps:

1. Keep using the launcher while v0.6 local studio features settle.
2. Add explicit process shutdown/status commands if needed.
3. Decide Tauri vs Electron based on local file/dialog needs and distribution
   expectations.
4. Move SQLite and logs to an OS-specific app data directory before formal
   packaging.
5. Add bundle scanning before any installer milestone to confirm no secrets are
   included.
