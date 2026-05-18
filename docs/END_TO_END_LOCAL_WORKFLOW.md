# End-to-End Local Workflow

This is the v1.0 Stable Local Studio workflow for one trusted local machine.
The project is local personal software, not a hosted service. The world engine
is the fact layer; the LLM is a language layer and is not the world judge.

## 0. Safety Boundaries

- `GameState`, `StateDelta`, and `EventLog` are the authoritative fact layer.
- Player APIs return filtered `visible_state`, not raw `GameState` or raw
  `state_deltas`.
- Authoring, debug, playtest, eval, performance, and quality APIs are local
  tooling APIs. Keep the backend bound to `127.0.0.1`.
- API keys stay in local shell variables or ignored `.env` files. They must not
  enter frontend code, frontend builds, content packs, saves, quality reports,
  fixtures, logs, or docs examples.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden map
  edges, hidden items, hidden/debug memory, and debug-only data must not appear
  in player-visible output.
- Mods and templates are content/data only. They do not execute arbitrary code.
- Memory summaries are not authoritative facts and cannot overwrite structured
  world state.

## 1. Install Dependencies

Create or activate the Python environment used for this repository, then make
sure backend dependencies are installed according to your local Python setup.
The launcher preflight checks that `fastapi`, `uvicorn`, `pydantic`, and
`app.main` are importable.

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Useful checks:

```powershell
python --version
npm --version
```

## 2. Configure `.env`

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Recommended offline/local defaults:

```text
DATABASE_URL=sqlite:///./world_engine.db
LLM_PROVIDER=mock
ENABLE_AUTHORING_API=false
ENABLE_DEBUG_API=true
ENABLE_PERF_LOGGING=false
ENABLE_PLAYTEST_API=false
ENABLE_EVAL_API=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use `LLM_PROVIDER=openai` only when you intentionally want real API calls and
have set `LLM_API_KEY` locally. Use `LLM_PROVIDER=local_http` only when a
compatible local model service is already running and `LOCAL_LLM_BASE_URL` is
configured.

## 3. Start Backend

Manual backend startup from the repository root:

```powershell
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "sqlite:///./world_engine.db"
$env:LLM_PROVIDER = "mock"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 4. Start Frontend

In a second terminal:

```powershell
cd frontend
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm.cmd run dev
```

Open the printed Vite URL, usually `http://127.0.0.1:5173`.

Build check:

```powershell
cd frontend
npm.cmd run build
```

## 5. Create Or Copy A World Pack

World packs live under `worlds/{world_id}`. To create a local experiment, copy
the sample world:

```powershell
Copy-Item -Recurse worlds\mist_valley worlds\my_world
```

Then update `worlds/my_world/manifest.yaml`:

```yaml
world_id: my_world
name: My World
version: 1.0.0
start_location_id: village_square
```

Do not place `.env`, API keys, database files, logs, caches, or executable
scripts inside a world pack.

## 6. Edit Content With Visual Editors

Enable authoring only on a trusted local machine:

```text
ENABLE_AUTHORING_API=true
```

Restart the backend after changing environment variables.

Use the frontend Authoring area:

- Map: edit locations, exits, coordinates, regions, tags, and visibility.
- Quests: edit quest stages, objectives, triggers, rewards, alternate/failure
  paths, and visibility.
- NPC Goals: edit deterministic NPC goals, priority, conditions, desired state,
  allowed actions, and forbidden actions.
- Items / Economy: edit items, ownership, prices, trade flags, and merchant
  inventory. The frontend does not calculate authoritative prices.
- Factions / Relationships: edit faction relations, NPC relationships, trust,
  fear, affinity, conflict level, and visibility.
- Rumors / Crime: edit rumor and crime consequence chains while keeping hidden
  fact text out of player-facing rumor text.
- Validation Graph: inspect validation issues by file, entity, reference, and
  severity.
- Templates: preview and apply local starter templates.

Every editor should follow the same flow:

1. Edit a local draft.
2. Preview.
3. Validate.
4. Review warnings/errors.
5. Save explicitly.

Visual editors edit content-pack YAML. They do not mutate active sessions or
active `GameState`.

## 7. Run `validate_world`

Validate the sample world:

```powershell
python -m backend.app.tools.validate_world worlds/mist_valley
```

Validate a copied world:

```powershell
python -m backend.app.tools.validate_world worlds/my_world
```

Fix validation errors before playtesting or packaging. Warnings can be accepted
only when they are intentional and documented.

## 8. Run Quality Gate

Run the standard v1.0 gate:

```powershell
$env:PYTHONPATH = "backend"
python -m app.tools.quality_gate --world mist_valley --profile standard
```

Profiles:

- `fast`: quick local smoke pass.
- `standard`: recommended release-candidate profile.
- `strict`: freeze-level profile; treats warnings more aggressively.

The quality gate is deterministic code. The LLM does not decide pass/fail.
Quality scores are useful local signals, not absolute design judgments.

## 9. Run Scenario Regression

Scenario regression checks repeatable story paths, visible facts, forbidden
visible facts, quest states, inventory, save/load behavior, and hidden leak
boundaries.

From the UI, use the Scenario Regression Dashboard or Scenario Regression
Authoring panel.

From the API, enable the local playtest/eval gates and use:

```text
GET  /scenarios/regression
POST /scenarios/regression/run
GET  /scenarios/regression/{run_id}
```

Regression runs use temporary sessions/saves and must not modify real user
saves.

## 10. Run Playtesting Batch

Use the Playtesting Dashboard for batch runs across scenarios, agents, and
seeds. Normal reports must not show hidden fact text.

CLI:

```powershell
python -m backend.app.tools.playtest_batch --world mist_valley --seeds 1,2,3
```

Playtesting agents are not formal player AI. They use the game loop or test
harness and do not directly modify `GameState`.

## 11. View World Health Dashboard

Use the World Health Dashboard to inspect:

- overall score
- category scores
- blockers
- warnings
- recommended actions
- latest run time

Health scores aggregate validation, quest analysis, hidden leak checks,
coverage, balance checks, stress tests, benchmark signals, and scenario
regression. They are not absolute quality judgments and do not rewrite content.

## 12. Create A Save

Start a local game from the frontend or API:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/start -ContentType "application/json" -Body '{"world_id":"mist_valley"}'
```

Use the Save Browser to create, list, load, export, or delete saves. Save
summaries omit hidden facts, raw `GameState`, raw `state_deltas`, debug memory,
and API keys.

## 13. Run Save Migration Dry-Run

Always check and dry-run before applying:

```powershell
python -m backend.app.tools.migrate_save --list
python -m backend.app.tools.migrate_save --save-id <id> --status
python -m backend.app.tools.migrate_save --save-id <id> --dry-run
```

Apply only after reviewing the dry-run:

```powershell
python -m backend.app.tools.migrate_save --save-id <id> --apply
```

Migration apply records history and must not destroy the original save on
failure. Migration must preserve EventLog and hidden/debug visibility
classification.

## 14. Import / Export World Packages

Use Authoring Import / Export UI or local APIs to export and import world,
mod, save, template, and scenario packages. Packages are local zip archives
with manifests and checksums.

Import dry-run/apply must reject:

- zip slip / path traversal
- executable files
- `.env`
- API keys
- database connection configuration
- invalid manifests
- checksum mismatches

Package import does not execute code and should not automatically overwrite
existing worlds or mods without explicit confirmation.

## 15. Validate Mods With Mod Manager

Use Mod Manager to list and inspect local content-only mods:

- manifest fields
- engine/content schema compatibility
- dependencies
- optional dependencies
- conflicts
- load order
- migration notes
- validation status

Mods do not execute Python, JavaScript, shell scripts, binaries, or arbitrary
entry points. Mod validation must stay local and must not access files outside
the mod directory.

## 16. Use Desktop Startup Script

For a single-command local launch:

```powershell
.\scripts\start_local_studio.ps1
```

macOS/Linux-style shells:

```bash
bash scripts/start_local_studio.sh
```

Preflight without starting processes:

```powershell
.\scripts\start_local_studio.ps1 -PreflightOnly
```

The launcher checks Python, npm, installed dependencies, `.env` guidance,
`DATABASE_URL`, backend/frontend port availability, backend `/health`, studio
status, and frontend availability. It does not inject `LLM_API_KEY` into the
frontend and does not create a formal desktop installer.

## 17. Common Troubleshooting

### Port Occupied

Stop the existing backend/frontend process or choose different ports:

```powershell
.\scripts\start_local_studio.ps1 -BackendPort 8010 -FrontendPort 5174
```

### Missing `.env`

The launcher can run with safe defaults, but persistent local settings should
go in ignored `.env`:

```powershell
Copy-Item .env.example .env
```

### Missing Frontend Dependencies

```bash
cd frontend
npm install
```

### API Key Missing

Use `LLM_PROVIDER=mock` or `local_stub` for offline work. If using
`LLM_PROVIDER=openai`, set `LLM_API_KEY` locally and never commit it.

### Local Model Unavailable

If `LLM_PROVIDER=local_http`, set `LOCAL_LLM_BASE_URL` and start your local
model server. The launcher does not start model services.

### Authoring API Disabled

Set `ENABLE_AUTHORING_API=true`, restart the backend, and keep it on localhost.

### Quality / Playtest API Disabled

Enable `ENABLE_PLAYTEST_API=true` and/or `ENABLE_EVAL_API=true` for local
dashboards. Some v1.0 quality endpoints are local-only and reuse debug/eval/
playtest/performance gates where implemented.

### Build Or Health Check Fails

Check:

- `logs/desktop-backend.err.log`
- `logs/desktop-frontend.err.log`
- `python -m pytest`
- `cd frontend && npm.cmd run build`

## 18. Security Notes

### API Key

API keys belong only in local shell variables or ignored `.env`. They must not
be printed, committed, bundled into frontend builds, stored in saves, or written
to quality reports.

### Local-Only Data

Saves, SQLite databases, logs, caches, packages, templates, mods, and authored
worlds are local files. Do not commit `.env`, database files, logs, caches,
`node_modules`, `frontend/dist`, or desktop build outputs.

### LLM Provider Data Boundary

LLM providers may receive prompts only through `LLMProvider`. The engine sends
language-layer context, not raw authoritative state. Local model providers and
OpenAI providers cannot directly write `GameState`; structured outputs still go
through schemas and deterministic rules.

### Debug API

Debug, authoring, eval, playtest, performance, and quality APIs are trusted
local tools. They can expose more diagnostic information than player APIs and
must remain bound to localhost. Debug data must not enter narrator prompts or
player-visible output.

## Final Local Verification

Before a v1.0 freeze:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Then run the quality gate, hidden leak suite, save/load/migration stress,
scenario regression suite, and benchmark smoke checks listed in
`docs/V1_0_RELEASE_CRITERIA.md`.
