# Desktop Studio Boundary

v1.7 introduces the Desktop Studio boundary for the local launcher and studio shell. The desktop layer is a convenience layer around the existing FastAPI backend and Vite/React frontend. It is not a second game engine, a privileged state editor, a secret store, or an LLM authority layer.

## Boundary Terms

- `desktop_shell`: the local launcher or future desktop wrapper that starts and monitors backend/frontend processes.
- `backend_process`: the FastAPI application and rule engine. It owns secret configuration, persistence, validation, and all state-changing services.
- `frontend_app`: the browser/Vite/desktop-rendered UI. It talks to backend APIs and never reads local secrets directly.
- `local_workspace`: the user-selected repository or project root containing worlds, packages, modules, docs, and local data.
- `safe_config_summary`: a backend-produced summary that may say whether a value is configured, but never returns the value if it is secret.
- `secret_config`: local-only backend configuration such as `.env`, API keys, provider credentials, and database connection details.
- `backup_bundle`: a local backup archive. Its safe default excludes `.env`, API keys, database connection config, logs, caches, and build outputs.
- `export_bundle`: a world/package/module export. Safe exports are redacted and must not contain secrets.
- `crash_report`: a local diagnostic report stored on the user's machine. It is not uploaded by default.
- `local_log`: local backend/frontend/launcher log output. Normal views must redact secrets and hidden content.

## Authority Model

1. The backend remains the only component that can validate and apply content changes.
2. The desktop shell can start processes, check readiness, open the frontend, and request backend APIs.
3. The desktop shell must not directly write `GameState`, saves, StateDelta files, EventLog entries, world packs, modules, packages, prompt profiles, or database rows.
4. The frontend app can call backend APIs and display safe summaries.
5. The frontend app must never read `.env`, API keys, raw environment variables, provider secrets, database URLs, raw logs, raw crash dumps, or raw state deltas.
6. All content or package modifications continue to flow through existing backend services, validation gates, import/export profiles, quality gates, and explicit confirmation steps.

## Secret Handling

API keys belong only to backend `secret_config`.

Allowed:

- Backend reads `LLM_API_KEY` from the local environment or ignored `.env`.
- Backend returns `api_key_configured: true|false` in safe summaries.
- Launcher warns when a real provider is selected but a key is missing.

Forbidden:

- Frontend reading `LLM_API_KEY`, `OPENAI_API_KEY`, or any provider secret.
- Desktop launcher injecting API keys into `VITE_*` variables.
- Logs, crash reports, backups, exports, packages, or help docs containing API keys.
- Settings UI showing raw secrets.

## Launcher Rules

The local launcher may:

- Set safe defaults such as `LLM_PROVIDER=mock`.
- Set `VITE_API_BASE_URL` for the frontend.
- Start backend and frontend processes.
- Write launcher logs to ignored local log files.
- Print safe local status.

The launcher must not:

- Hardcode API keys.
- Print API keys.
- Pass API keys to Vite.
- Run untrusted gameplay modules automatically.
- Modify `GameState` or content packs directly.
- Upload telemetry or crash reports.

## Frontend Rules

The frontend may use `VITE_API_BASE_URL`.

The frontend must not contain, request, persist, or display:

- API keys.
- Raw `.env`.
- Raw database URLs.
- Raw provider secrets.
- Raw prompts.
- Raw hidden facts.
- Raw state deltas.
- Module debug data in normal player UI.

## Backup and Export Rules

Safe backup/export defaults exclude:

- `.env` and `.env.*`.
- API keys or provider credentials.
- Database connection config.
- Logs.
- Caches.
- Local database files.
- `node_modules`.
- `frontend/dist`.
- Desktop build outputs.

Backup restore and package import apply operations must require explicit confirmation and must pass the relevant validation gate.

## Logs and Crash Reports

Local logs and crash reports are for local diagnostics only.

Normal views must redact:

- API keys and private keys.
- Raw environment dumps.
- Raw prompts.
- Raw state deltas.
- Hidden facts and NPC secrets.
- Full database connection strings.

Crash reports are never uploaded automatically.

## LLM Boundary

Desktop Studio features do not expand LLM authority. The LLM remains a language layer:

- It cannot modify `GameState`.
- It cannot bypass StateDelta or EventLog.
- It cannot decide rules, gameplay outcomes, package trust, or backup/restore safety.
- Desktop health checks, diagnostics, packaging checks, backups, and exports must not call real providers by default.

## Testing Requirements

v1.7.1 tests must verify:

1. Safe config summary does not contain API keys or raw database URLs.
2. Backup bundles reject `.env`, API key content, logs, caches, and database files by default.
3. Crash report normal views omit raw environment values.
4. Frontend config rejects API keys and only allows safe `VITE_*` configuration.
5. Desktop launcher scripts do not hardcode API keys or pass secrets to the frontend.

