# Local LLM Interactive Novel World Engine

A local-first interactive novel world engine. The LLM is used for intent
parsing, narration, and memory summarization, while the local engine owns
world state, rule resolution, event logs, saves, visibility, social systems,
combat, and content validation.

This project is for local personal use. It is not designed as a hosted service.

## Current Version Scope

v0.7 polishes the local studio layer on top of the v0.6 hardening work:

- Multi-world content packs.
- Structured `GameState`, `StateDelta`, `EventLog`, and SQLite save/load.
- Structured `visible_state` for frontend use.
- NPC schedule, search, inventory, lockpick, sneak, quest state machine, and
  world tick.
- Faction reputation, rumors, crime/witness, social consequences, combat,
  life state, NPC reactions, and debug timeline.
- Content authoring API and frontend authoring UI.
- Structured world validation reports.
- Local memory backends and safe `MemoryContextBuilder`.
- NPC goals, planning tick, relationship graph, and faction conflict.
- Economy/trade rules.
- Procedural side quest drafts.
- Content-only mod packaging and validation.
- Multi-world save browser.
- Automated narrative boundary evals.
- Save migration system with status, dry-run, apply, backup metadata, and CLI.
- Authoring preview/diff/dry-run plus content impact analysis.
- Player-safe and debug relationship/faction graph APIs and frontend panels.
- Deterministic playtesting agents.
- Narrative quality evals without an external LLM judge.
- Local performance instrumentation and debug performance summaries.
- Advanced mod versioning checks.
- Desktop launcher prototype documentation and script.
- Local provider support with `local_stub` and configurable `local_http`.
- Advanced combat slice with stance, status effects, non-lethal attacks, flee
  risk, and visible combat summaries.
- Studio Home Dashboard and Settings / Local Privacy panel.
- Save Migration UI.
- Mod Manager UI.
- Narrative Quality Dashboard.
- Performance Dashboard.
- Automated Playtesting Dashboard.
- Scenario Template System.
- Visual Quest Graph Editor initial slice.
- Import/export workflow for local world, mod, and save archives.

The LLM is still not the world judge. Rule outcomes are decided by local code.

## Requirements

- Python 3.11+
- Node.js 18+
- npm

## Setup

Install backend dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install frontend dependencies:

```powershell
cd frontend
npm install
```

## Configuration

Copy `.env.example` to a local `.env` if desired. Do not commit `.env`.

Important variables:

```env
DATABASE_URL=sqlite:///./world_engine.db
LLM_PROVIDER=mock
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=
LOCAL_LLM_BASE_URL=
LOCAL_LLM_MODEL=local-model
LOCAL_LLM_TIMEOUT_SECONDS=30
LOCAL_LLM_JSON_MODE=true
ENABLE_DEBUG_API=true
ENABLE_AUTHORING_API=false
ENABLE_PERF_LOGGING=false
ENABLE_PLAYTEST_API=false
ENABLE_EVAL_API=false
VITE_API_BASE_URL=http://127.0.0.1:8000
MEMORY_BACKEND=sqlite
AUTHORING_ROOT=worlds
MODS_ROOT=mods
```

`LLM_PROVIDER=mock` is the local development default. `local_stub` is a
deterministic offline local-provider placeholder. `local_http` posts to
`LOCAL_LLM_BASE_URL/chat/completions` with an OpenAI-compatible chat payload and
uses `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT_SECONDS`, and
`LOCAL_LLM_JSON_MODE`. It is configurable for local model services but still
does not make the model a world judge. Use `openai` only when you explicitly
want real API calls and have set the API key through the environment. API keys
must never be committed, logged, or placed in frontend code.

`AUTHORING_ROOT`, `MODS_ROOT`, and `MEMORY_BACKEND` document the intended
local configuration surface. Some runtime paths still use the current
repository defaults.

## Start the Backend

From the repository root:

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

## Start the Frontend

```powershell
cd frontend
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

The frontend includes a play view, debug panel, authoring view, and save
browser. It does not store API keys.

## Studio Home

The first studio screen summarizes safe local project status from
`GET /studio/status`: backend health, engine version, available worlds, recent
save summaries, authoring/debug/performance API status, current
`LLM_PROVIDER`, and recent validation/playtest summaries when available.

Studio Home does not return API keys, raw environment variables, raw
`GameState`, raw `state_deltas`, hidden facts, NPC secrets, or debug memory.
It is a launcher and status surface, not a new source of truth.

## Settings / Local Privacy

The Settings / Local Privacy panel reads:

```text
GET /studio/config-summary
```

It shows provider type/status, local API toggles, whether an API key is
configured, a redacted database hint, and local privacy notes. It does not show
the API key, raw `.env`, full sensitive paths, or raw state. The frontend does
not edit `.env`.

## Local Studio Launcher Prototype

v0.7 includes local studio launcher scripts. They check basic dependencies,
start the backend, start the frontend in dev mode or built-preview mode, print
safe local status, and open the local frontend URL:

```powershell
.\scripts\start_local_studio.ps1
```

```bash
bash scripts/start_local_studio.sh
```

The launcher reads local environment variables and applies safe defaults for
`DATABASE_URL`, `LLM_PROVIDER`, `ENABLE_DEBUG_API`, `ENABLE_AUTHORING_API`,
`ENABLE_PERF_LOGGING`, and `VITE_API_BASE_URL`. It does not set, print, or
embed `LLM_API_KEY`.

Built frontend preview:

```powershell
cd frontend
npm run build
cd ..
.\scripts\start_local_studio.ps1 -UseBuiltFrontend
```

Use `.\scripts\start_local_studio.ps1 -PreflightOnly` to check configuration
without starting backend/frontend processes.

See `docs/DESKTOP_PACKAGING.md` for the Tauri/Electron/local-launcher review
and packaging safety notes.

## Scenario Templates

v0.7 includes local authoring templates under `templates/`. They are YAML data
files used to preview reusable world, quest, location, NPC, faction, mystery,
or combat encounter drafts. Templates do simple variable substitution, validate
rendered output through the existing world validator, and never modify active
sessions or saves.

Template preview endpoints are behind `ENABLE_AUTHORING_API`:

```powershell
Invoke-RestMethod -Method Get http://127.0.0.1:8000/authoring/templates
```

The frontend Authoring panel includes a Scenario Templates section for preview
only. Rendered files must still be explicitly saved through normal authoring
file flows.

## Quest Graph Authoring

When editing `quests.yaml`, the Authoring panel includes a Quest Graph section.
It shows quests, stages, objectives, triggers, and `next_stages` edges. The
initial editor supports small stage-level edits and converts the graph back to
YAML through the backend preview endpoint:

```powershell
Invoke-RestMethod -Method Get http://127.0.0.1:8000/authoring/worlds/mist_valley/quests/graph
```

The graph preview does not write files or modify active `GameState`. Saving
still goes through normal authoring validation.

## Choose a World

Start a game with the default world:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/start
```

Start a specific world:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/start `
  -ContentType "application/json" `
  -Body '{"world_id":"mist_valley"}'
```

The frontend world selector uses the same `world_id` flow.

## Send Player Input

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/input `
  -ContentType "application/json" `
  -Body '{"session_id":"SESSION_ID","player_input":"观察四周"}'
```

The response includes narration, suggested actions, current turn, and
structured `visible_state`. Player APIs do not return raw `state_deltas`,
hidden facts, NPC secrets, hidden witnesses, or debug memory.

## Save and Load

List saves, optionally filtered by world:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/game/saves
Invoke-RestMethod "http://127.0.0.1:8000/game/saves?world_id=mist_valley"
```

Save an active session:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/SESSION_ID/save
```

Load a save into an active session:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/load/SAVE_ID
```

Delete a save:

```powershell
Invoke-RestMethod -Method Delete http://127.0.0.1:8000/game/saves/SAVE_ID
```

Save summaries are safe summaries. They do not expose raw `GameState`, hidden
facts, raw event deltas, or debug memory.

## Save Migration

v0.6+ adds local save migration checks for schema upgrades. Migrations are
deterministic, do not call the LLM, and create a backup before applying changes.

API:

- `GET /migrations`
- `GET /saves/{save_id}/migration-status`
- `POST /saves/{save_id}/migrate-dry-run`
- `POST /saves/{save_id}/migrate`

CLI:

```powershell
python -m app.tools.migrate_save --list
python -m app.tools.migrate_save --save-id SAVE_ID --status
python -m app.tools.migrate_save --save-id SAVE_ID --dry-run
python -m app.tools.migrate_save --save-id SAVE_ID --apply
```

When running from the repository root without installing the backend package,
set `PYTHONPATH=backend` first. The CLI uses `DATABASE_URL` by default and also
accepts `--database-url`.

The v0.7 Save Browser includes a migration UI for status, dry-run, apply, and
history. Dry-run is non-writing. Apply requires confirmation. The UI displays
safe summaries only and does not show raw hidden save payloads.

## Debug API

Debug APIs are local-development tools only. Enable them with:

```powershell
$env:ENABLE_DEBUG_API = "true"
```

Endpoints:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`
- `GET /debug/sessions/{session_id}/graphs/relationships`
- `GET /debug/sessions/{session_id}/graphs/factions`
- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

Debug events may include raw `state_deltas`. They are intentionally separated
from player APIs and narrator input.

Performance sampling is controlled separately with `ENABLE_PERF_LOGGING=true`.
It records local timing samples for game loop phases, save/load, memory search,
and authoring validation. Samples stay in memory and must not include prompts,
API keys, hidden fact text, raw `GameState`, or raw `state_deltas`.

## Performance Dashboard

When `ENABLE_DEBUG_API=true`, the frontend Performance Dashboard reads:

- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

It displays recent local samples and summaries for game loop phases, narrator,
world tick, save/load, memory search, and authoring validation when available.
It does not record or show prompt text, hidden facts, API keys, raw
`GameState`, or raw `state_deltas`.

## Relationship and Faction Graphs

Player-safe graph APIs:

- `GET /game/{session_id}/graphs/relationships`
- `GET /game/{session_id}/graphs/factions`

Debug graph APIs are available only when `ENABLE_DEBUG_API=true`:

- `GET /debug/sessions/{session_id}/graphs/relationships`
- `GET /debug/sessions/{session_id}/graphs/factions`

Player graphs return only player-known relationships and factions. Hidden
relationships, hidden factions, hidden NPCs, hidden facts, raw `GameState`, and
raw `state_deltas` stay out of player graph responses. The frontend graph
panels render this API data as lightweight lists/SVG summaries and do not infer
hidden relationships client-side.

## Authoring API

The authoring API is disabled by default. Enable it only for local editing:

```powershell
$env:ENABLE_AUTHORING_API = "true"
```

Endpoints:

- `GET /authoring/worlds`
- `POST /authoring/worlds`
- `GET /authoring/worlds/{world_id}`
- `GET /authoring/worlds/{world_id}/files`
- `GET /authoring/worlds/{world_id}/files/{file_name}`
- `PUT /authoring/worlds/{world_id}/files/{file_name}`
- `POST /authoring/worlds/{world_id}/preview-file-change`
- `POST /authoring/worlds/{world_id}/validate-draft`
- `POST /authoring/worlds/{world_id}/impact-analysis`
- `POST /authoring/worlds/{world_id}/validate`
- `GET /authoring/mods`
- `POST /authoring/mods/{mod_id}/validate`

The API can read/write only whitelisted YAML content files and rejects path
traversal. It does not mutate active session `GameState` and does not call the
LLM.

Example authoring dry-run preview:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/authoring/worlds/mist_valley/preview-file-change `
  -ContentType "application/json" `
  -Body '{"file_name":"locations.yaml","proposed_content":"[]"}'
```

`preview-file-change`, `validate-draft`, and `impact-analysis` parse and
validate proposed content without writing disk or active saves. Use
`PUT /authoring/worlds/{world_id}/files/{file_name}` only after reviewing
validation errors, warnings, and impact output.

## Authoring UI

The frontend includes a local authoring view. It can:

- list world packs
- select a world
- select whitelisted YAML files
- browse files in a categorized world/file tree
- edit raw YAML
- edit common entity types through lightweight forms for locations, NPCs, items,
  facts, and quests
- preview selected entities and file-level validation status
- track dirty state, discard local edits, and reload from disk
- preview diff and impact before saving
- save YAML through the authoring API
- run validation
- show structured errors, warnings, and suggestions grouped by file

Before saving, the UI can run a dry-run preview. Validation errors block save;
warnings and possible save-impact risks require local confirmation.

If the authoring API is disabled, the UI shows an unavailable state. The
authoring view is separate from the player narrative view.

## Studio Home Shortcuts

The Studio Home page links to Play, Authoring, Save Browser, Migration, Mod
Manager, Graphs, Narrative Evals, Performance, Playtesting, and Settings. Some
panels require `ENABLE_AUTHORING_API`, `ENABLE_DEBUG_API`,
`ENABLE_PLAYTEST_API`, or `ENABLE_EVAL_API`/debug mode.

## World Validation

Run validation from the repository root:

```powershell
python scripts\validate_world.py mist_valley
```

JSON output:

```powershell
python scripts\validate_world.py mist_valley --json
```

Validation checks include schema fields, references, exits, NPC locations,
schedule locations, faction ids, item ownership conflicts, quest triggers,
fact known-by references, rumor fact ids, hidden fact leakage warnings, life
fields, economy fields, and reserved plugin manifest checks.

The CLI exits non-zero when errors are present.

## Mod Validation

The current engine supports content-only local mods. Mods may contain YAML content packs but
must not execute Python, JavaScript, shell scripts, or arbitrary code.

When the authoring API is enabled:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/authoring/mods
Invoke-RestMethod -Method Post http://127.0.0.1:8000/authoring/mods/MOD_ID/validate
```

Mod validation reuses world validation for entry worlds and checks
dependencies, conflicts, content paths, engine version bounds, and executable
file restrictions.

v0.6 mod manifests can also declare `content_schema_version`,
`optional_dependencies`, `load_order_hint`, `compatible_worlds`, and
`migration_notes`. Version checks are deterministic and intentionally simple;
there is no online registry, code execution, or complex SAT-style resolver.

## Mod Manager

The v0.7 frontend includes a Mod Manager panel when the authoring API is
enabled. It can list discovered local content-only mods, show manifest fields,
validate selected mods, display dependency/conflict/version status, show load
order, and display migration notes.

It does not execute mod scripts, download online mods, hot-reload active saves,
or bypass validation. Any local paths shown by diagnostics should be treated as
local authoring/debug information only.

## Narrative Boundary Evals

Run the automated boundary evals:

```powershell
python -m pytest backend/tests/evals
```

The evals cover hidden facts, NPC secrets, hidden witnesses, debug deltas,
hidden/debug memory, rumor safety, and procedural quest draft safety. They use
mock providers and do not call real APIs.

## Narrative Quality Evals

Run deterministic narrative quality evals:

```powershell
python -m app.tools.eval_narrative_quality
python -m app.tools.eval_narrative_quality --json
```

When running from the repository root without installing the backend package,
set `PYTHONPATH=backend` first. These evals use deterministic cases and do not
call an external LLM judge.

When `ENABLE_DEBUG_API=true`, the v0.7 Narrative Quality Dashboard can run and
display eval reports through:

- `GET /evals/narrative/recent`
- `POST /evals/narrative/run`
- `GET /evals/narrative/{run_id}`

Reports are local test artifacts. They do not modify `GameState` and should
not display hidden fixture text in ordinary UI.

## Playtesting Agents

Run deterministic local playtesting:

```powershell
python -m app.tools.playtest --world mist_valley --steps 100 --seed 123
python -m app.tools.playtest --world mist_valley --steps 100 --seed 123 --json
```

The playtesting agents use the normal `GameLoop`/test harness and mock
providers. They must not directly mutate `GameState`. Reports include actions,
errors, invariant violations, visibility leaks, save/load failures, and final
state summaries.

With `ENABLE_PLAYTEST_API=true` or debug enabled, the v0.7 Playtesting
Dashboard can run deterministic playtests through:

- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`

The dashboard is a local testing tool, not a player AI. Agents act through the
game loop/test harness and do not directly modify `GameState`.

## Import / Export

v0.7 adds local archive import/export for worlds, mods, and saves. These
endpoints are gated by `ENABLE_AUTHORING_API`:

- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`

Archives are zip bundles returned as base64 in the API response. Imports reject
zip slip/path traversal, executable files, `.env`, database files, logs, and
secret files. World and mod imports run validation. Save imports check
migration status. Save export can contain hidden state and event history by
design, so treat save bundles as local private backup data.

## Full Verification

Backend tests:

```powershell
python -m pytest
```

Frontend build:

```powershell
cd frontend
npm run build
```

## Content Pack Files

World packs live under `worlds/{world_id}`. The current schema supports:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`

See `docs/CONTENT_PACKS.md` for file-level details.

## Known Limits

- Authoring and debug APIs are local-only tools, not production features.
- No accounts, cloud sync, or online mod publishing.
- The authoring UI is a local structured editor, not a full IDE. Complex nested
  content such as quest stages, NPC schedules, and goals should still be edited
  in raw YAML.
- Validation reports identify issues but do not auto-fix YAML.
- The local vector memory layer currently has deterministic fallback behavior;
  no external vector database is required.
- `local_http` is an OpenAI-compatible local HTTP integration slice; individual
  local model servers may still need adapter work if their API shape differs.
- Memory is not authoritative and cannot overwrite `GameState` or `EventLog`.
- Procedural side quest generation produces drafts only.
- NPC planning is deterministic and limited to predefined action types.
- Economy is lightweight and does not model dynamic supply/demand.
- Faction conflict does not simulate war or diplomacy AI.
- Desktop packaging is currently a local launcher prototype and documentation,
  not a formal installer, signed application, or auto-updater.
- Narrative quality evals are deterministic test checks, not a substitute for
  human writing review.
- Import/export archive APIs are local authoring tools. Save archives can
  contain hidden state by design and should be handled as private local data.
- Narrative eval APIs are currently debug-gated; a future cleanup may add a
  dedicated `ENABLE_EVAL_API` route gate separate from broad debug access.
