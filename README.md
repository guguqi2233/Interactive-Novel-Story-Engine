# Local LLM Interactive Novel World Engine

A local-first interactive novel world engine. The LLM is used for intent
parsing, narration, and memory summarization, while the local engine owns
world state, rule resolution, event logs, saves, visibility, social systems,
combat, and content validation.

This project is for local personal use. It is not designed as a hosted service.

## Current Version Scope

v1.1 is the Roleplay Immersion Layer on top of the v1.0 Stable Local Studio
Edition. v1.0 freezes the local contracts built through the v0.x series, and
v1.1 adds character voice, dialogue, group RP, roleplay imports, RP-safe memory,
and RP regression checks without changing world authority:

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
- Visual Map Editor.
- Visual Quest Graph Editor full authoring slice.
- NPC Goal Editor.
- Faction / Relationship Visual Editor.
- Item / Economy Editor.
- Rumor / Crime Consequence Editor.
- Visual Validation Graph.
- Timeline Replay Visualizer.
- World Branch / Diff System.
- Scenario Regression Suite.
- Local Template Browser.
- Prompt Profile Manager.
- Advanced import/export packages for world, mod, save, template, and scenario
  bundles.
- World quality report schemas and local report aggregation.
- Expanded deterministic playtest scenarios and batch runner.
- Scenario regression authoring.
- Hidden information leak regression suite.
- Quest completion analysis and dead-end/unreachable objective detection.
- NPC behavior coverage and schedule conflict detection.
- Economy, combat, and social consequence balance/coverage sanity checks.
- Save/load/migration stress tests.
- Performance benchmark suite.
- Narrative consistency evals.
- World Health Score Dashboard and Content Coverage Dashboard.
- Branch diff regression and mod compatibility stress testing.
- Quality Gate CLI/API.
- Roleplay Boundary Contract.
- Character Card Importer.
- RP Profile / Voice Profile support.
- NPC Emotional State and Relationship Tone.
- Dialogue Mode and Multi-NPC Group RP.
- Scene Mood Presets.
- Lorebook Import / Classification.
- Example Dialogue Manager.
- RP Memory Context Builder.
- RP Prompt Profile Manager.
- RP Output Consistency Checker.
- Tavern Compatibility Import / Export.
- RP Scenario Templates.
- RP Boundary Evals and RP Regression Playtests.
- Frontend RP / Dialogue panels.

The LLM is still not the world judge. Rule outcomes are decided by local code.

## v1.0 Documentation Map

- `docs/SPEC.md`: project scope, boundaries, and known limitations.
- `docs/WORLD_ENGINE.md`: engine behavior, rules, state, events, authoring,
  quality, migration, and local studio architecture.
- `docs/LLM_PROTOCOL.md`: provider boundary, prompt/profile rules, and why LLM
  output cannot directly change `GameState`.
- `docs/ROLEPLAY_BOUNDARY.md`: v1.1 RP expression/fact boundary.
- `docs/CONTENT_PACKS.md`: content pack format and authoring notes.
- `docs/V1_0_CONTENT_SCHEMA_CONTRACT.md`: frozen v1.0 content schema contract.
- `docs/V1_0_API_CONTRACT.md`: frozen v1.0 API contract.
- `docs/V1_0_SAVE_MIGRATION_GUARANTEE.md`: migration guarantees and matrix.
- `docs/V1_0_MOD_CONTRACT.md`: content-only mod packaging contract.
- `docs/DESKTOP_PACKAGING.md`: local startup scripts and desktop prototype
  limitations.
- `docs/END_TO_END_LOCAL_WORKFLOW.md`: start-to-finish local workflow.
- `docs/UPGRADE_GUIDE_V0_TO_V1.md`: upgrade notes from v0.x to v1.0.
- `docs/V1_0_RELEASE_CRITERIA.md`: release blockers and tag checklist.

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
TEMPLATE_ROOT=templates
PACKAGE_IMPORT_ROOT=imports
```

`LLM_PROVIDER=mock` is the local development default. `local_stub` is a
deterministic offline local-provider placeholder. `local_http` posts to
`LOCAL_LLM_BASE_URL/chat/completions` with an OpenAI-compatible chat payload and
uses `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT_SECONDS`, and
`LOCAL_LLM_JSON_MODE`. It is configurable for local model services but still
does not make the model a world judge. Use `openai` only when you explicitly
want real API calls and have set the API key through the environment. API keys
must never be committed, logged, or placed in frontend code.

`AUTHORING_ROOT`, `MODS_ROOT`, `TEMPLATE_ROOT`, `PACKAGE_IMPORT_ROOT`, and
`MEMORY_BACKEND` document the intended local configuration surface. Some
runtime paths still use the current repository defaults.

There is currently no separate `ENABLE_QUALITY_API` setting. v0.9 quality
tools reuse local-only debug/eval/playtest/performance gates where implemented;
some analyzer endpoints are local-only and should not be exposed outside a
trusted localhost setup.

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

v1.0 keeps the desktop app shell as a local launcher prototype. The scripts
check Python and Node/npm dependencies, verify backend imports, check installed
frontend dependencies, warn if `.env` is missing, check `DATABASE_URL`, fail
early when backend/frontend ports are occupied, start the backend, start the
frontend in dev mode or built-preview mode, run local health checks, print safe
status, and open the local frontend URL:

```powershell
.\scripts\start_local_studio.ps1
```

```bash
bash scripts/start_local_studio.sh
```

The launcher reads local environment variables and applies safe defaults for
`DATABASE_URL`, `LLM_PROVIDER`, `ENABLE_DEBUG_API`, `ENABLE_AUTHORING_API`,
`ENABLE_PERF_LOGGING`, and `VITE_API_BASE_URL`. It does not set, print, or
embed `LLM_API_KEY`. If `.env` is missing, it continues with safe defaults and
suggests copying `.env.example` for local customization.

Common startup checks and fixes:

- Port occupied: stop the existing process or pass `-BackendPort` /
  `-FrontendPort` on PowerShell, or `--backend-port` / `--frontend-port` on
  the shell launcher.
- Missing `.env`: copy `.env.example` to `.env`; keep `.env` untracked.
- Missing frontend dependencies: run `cd frontend && npm install`.
- Missing API key: use `LLM_PROVIDER=mock` or `local_stub` for offline startup;
  only set `LLM_API_KEY` locally when intentionally using `openai`.
- Local model unavailable: with `LLM_PROVIDER=local_http`, set
  `LOCAL_LLM_BASE_URL` and start your local model service yourself.

Built frontend preview:

```powershell
cd frontend
npm run build
cd ..
.\scripts\start_local_studio.ps1 -UseBuiltFrontend
```

Use `.\scripts\start_local_studio.ps1 -PreflightOnly` to check configuration
without starting backend/frontend processes. After launch, the scripts check:

- `GET /health`
- `GET /studio/status`
- frontend URL availability

Windows PowerShell is the primary launcher path. The shell launcher is a
convenience prototype for macOS/Linux-style shells; macOS uses `open` and Linux
usually uses `xdg-open` to launch a browser automatically. Neither script
creates a formal installer, signs code, enables auto-update, syncs to cloud, or
packages secrets.

See `docs/DESKTOP_PACKAGING.md` for the Tauri/Electron/local-launcher review
and packaging safety notes.

## Scenario Templates

v1.0 includes stable starter templates under `templates/`. They are YAML data
files used to preview reusable world, quest, location, NPC, faction, mystery,
trade, rumor, or combat encounter drafts. Templates do simple variable
substitution, validate rendered output through the existing world validator,
and never modify active sessions or saves.

Starter templates:

- `basic_village_world`
- `mystery_quest`
- `faction_conflict_seed`
- `small_dungeon`
- `merchant_and_trade`
- `rumor_chain`
- `NPC_goal_set`
- `combat_encounter_light`

Template preview endpoints are behind `ENABLE_AUTHORING_API`:

```powershell
Invoke-RestMethod -Method Get http://127.0.0.1:8000/authoring/templates
```

The Local Template Browser can list templates, show variables/tags,
preview rendered YAML, display validation output, and apply templates through
authoring-gated explicit save flows. Rendered files must still pass validation
and must not modify active sessions or saves.

## Visual Map Editor

When `ENABLE_AUTHORING_API=true`, the Authoring workspace includes a Map Editor
for `locations.yaml`. It reads and writes map graphs through:

- `GET /authoring/worlds/{world_id}/map`
- `POST /authoring/worlds/{world_id}/map/preview`
- `POST /authoring/worlds/{world_id}/map/validate`
- `PUT /authoring/worlds/{world_id}/map`

The editor can show location nodes, exits, positions, regions, labels, and
visual tags. Preview and validate do not write files. Save converts the graph
back to `locations.yaml` and runs validation. Hidden map data is authoring-only
and does not enter the player map.

## Quest Graph Editor

When editing `quests.yaml`, the Authoring panel includes a Quest Graph section.
It shows quests, stages, objectives, triggers, rewards, failure/alternate
paths, and `next_stages` edges. The v0.8 editor supports structured edits and
converts the graph back to YAML through backend preview/validate/save
endpoints:

```powershell
Invoke-RestMethod -Method Get http://127.0.0.1:8000/authoring/worlds/mist_valley/quests/graph
```

Graph preview does not write files or modify active `GameState`. Saving still
goes through normal authoring validation. Hidden quests remain authoring-only
until rules make them player-visible.

## NPC Goal Editor

The Authoring workspace includes an NPC Goal Editor for `npcs.yaml` goals:

- `GET /authoring/worlds/{world_id}/npcs/goals`
- `POST /authoring/worlds/{world_id}/npcs/goals/preview`
- `POST /authoring/worlds/{world_id}/npcs/goals/validate`
- `PUT /authoring/worlds/{world_id}/npcs/goals`

It can edit goal id, description, priority, conditions, desired state,
allowed actions, and forbidden actions. Validation checks references and
supported planning actions. It does not create LLM NPC planners or modify
active runtime state.

## Faction / Relationship Editor

The Faction / Relationship Visual Editor reads `factions.yaml`,
`relationships.yaml`, and related NPC metadata:

- `GET /authoring/worlds/{world_id}/social/graph`
- `POST /authoring/worlds/{world_id}/social/graph/preview`
- `POST /authoring/worlds/{world_id}/social/graph/validate`
- `PUT /authoring/worlds/{world_id}/social/graph`

It can edit relation type, trust, fear, affinity, obligation, faction conflict
values, and visibility. Player relationship/faction graphs remain separate and
filtered.

## Item / Economy Editor

The Item / Economy Editor reads `items.yaml` and NPC merchant fields:

- `GET /authoring/worlds/{world_id}/economy`
- `POST /authoring/worlds/{world_id}/economy/preview`
- `POST /authoring/worlds/{world_id}/economy/validate`
- `PUT /authoring/worlds/{world_id}/economy`

It can edit item ownership, hidden state, tags, base price, rarity,
tradeability, portability, and merchant shop inventory. Backend rules remain
the authority for actual buy/sell prices.

## Rumor / Crime Editor

The Rumor / Crime Consequence Editor reads rumor, fact, faction, quest, and
consequence-like content:

- `GET /authoring/worlds/{world_id}/rumor-crime`
- `POST /authoring/worlds/{world_id}/rumor-crime/preview`
- `POST /authoring/worlds/{world_id}/rumor-crime/validate`
- `PUT /authoring/worlds/{world_id}/rumor-crime`

Validation catches invalid fact ids, hidden fact text in player-facing rumor
text, duplicate consequence ids, and simple loop risks. Runtime social
consequences are still rule-engine decisions.

## Validation Graph

The Visual Validation Graph turns validation reports into a file/entity/issue
graph:

- `GET /authoring/worlds/{world_id}/validation-graph`
- `POST /authoring/worlds/{world_id}/validation-graph`

It is an authoring diagnostic only. It does not auto-fix YAML or call the LLM.

## World Branch / Diff

v0.8 adds lightweight local world branches and structured diff:

- `GET /authoring/worlds/{world_id}/branches`
- `POST /authoring/worlds/{world_id}/branches`
- `GET /authoring/worlds/{world_id}/diff?other=BRANCH_OR_WORLD`
- `POST /authoring/worlds/{world_id}/diff-draft`

Branches copy only whitelisted world YAML under `worlds/.branches/...`.
Diff reports added/removed/changed entities, broken references, migration
impacts, and visibility risks. It does not modify active sessions or saves.

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

The Save Browser includes a migration UI for status, dry-run, apply, and
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
- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/timeline`
- `POST /debug/saves/{save_id}/replay-dry-run`

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

## Timeline Replay

When debug API is enabled, Timeline Replay shows turn groups, events,
state-delta summaries, system tick events, migration events, and replay dry-run
checksums/invariant violations. It is a debug panel only. Replay dry-run does
not write the database and the timeline must not be used as narrator/player
content.

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
- use v0.8 visual editors for map, quests, NPC goals, social graph, economy,
  rumor/crime consequences, templates, and validation graph

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

The frontend includes a Mod Manager panel when the authoring API is
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

When `ENABLE_DEBUG_API=true`, the Narrative Quality Dashboard can run and
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

With `ENABLE_PLAYTEST_API=true` or debug enabled, the Playtesting
Dashboard can run deterministic playtests through:

- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`

The dashboard is a local testing tool, not a player AI. Agents act through the
game loop/test harness and do not directly modify `GameState`.

v0.9 expands playtesting with scenario types for exploration, quest paths,
combat, stealth, economy, crime/social behavior, save/load, migration, and
hidden-leak probes. Batch playtests run multiple scenarios and seeds
deterministically:

```powershell
python -m app.tools.playtest_batch --world mist_valley --seeds 1,2,3
```

Reports are local quality artifacts. They should not contain hidden fact text
in normal views and must not be treated as player AI or canonical story events.

## Scenario Regression Suite

v0.8 adds scenario regression APIs for repeatable local story/path checks:

- `GET /scenarios/regression`
- `POST /scenarios/regression/run`
- `GET /scenarios/regression/{run_id}`

Cases run scripted input through the game loop or test harness with mock/local
providers. Reports include pass/fail status, failed steps, safe expected-vs-
actual summaries, hidden leak summaries, and save/load failures. Reports must
not show hidden fact text.

Scenario regression cases can also be authored locally through the authoring
API/UI when authoring is enabled. Preview does not write disk, save requires
validation, and scenario output does not modify active saves.

## v1.0 Quality Gate

Run the local quality gate from the repository root after setting
`PYTHONPATH=backend` or installing the backend package:

```powershell
python -m app.tools.quality_gate --world mist_valley --profile standard
python -m app.tools.quality_gate --world mist_valley --profile standard --json
```

The gate combines validation, hidden-leak checks, quest analysis, dead-end
detection, NPC coverage, schedule conflict detection, economy/combat/social
sanity checks, save/load stress, benchmarks, scenario regression, and mod
compatibility smoke checks. It is a deterministic threshold/severity gate; the
LLM does not decide pass/fail.

v1.0 gate profiles:

- `standard`: default release-candidate profile. Warnings are allowed; errors
  and blockers fail.
- `strict`: stricter release freeze profile. Warnings, errors, and blockers
  fail, with a higher health-score target and broader smoke coverage.
- `fast`: local quick-check profile. It keeps the same check categories but
  uses smaller smoke parameters for faster iteration.

The API entry point is local-only and gated through the eval/playtest/debug
gate path:

```text
POST /quality/worlds/{world_id}/gate/run
```

## v1.0 Quality Analysis APIs

The quality analyzers provide safe local reports for authoring and regression:

```text
GET  /quality/worlds/{world_id}/quests
POST /quality/worlds/{world_id}/quests/analyze
POST /quality/worlds/{world_id}/dead-ends/analyze
GET  /quality/worlds/{world_id}/npc-coverage
POST /quality/worlds/{world_id}/npc-coverage/analyze
POST /quality/worlds/{world_id}/schedules/analyze
POST /quality/worlds/{world_id}/economy/analyze
POST /quality/worlds/{world_id}/combat/analyze
POST /quality/worlds/{world_id}/social-consequences/analyze
GET  /quality/worlds/{world_id}/health
POST /quality/worlds/{world_id}/health/run
GET  /quality/worlds/{world_id}/coverage
POST /quality/worlds/{world_id}/coverage/run
POST /quality/worlds/{world_id}/branch-regression/run
POST /quality/mods/compatibility-stress/run
```

These APIs do not call the LLM and do not modify active `GameState`. Normal
report views must not include hidden fact text, raw state, raw deltas, API
keys, or raw environment values. Current v1.0 has no independent
`ENABLE_QUALITY_API`; keep these endpoints local.

## Hidden Leak And Narrative Consistency Evals

Run the hidden information leak suite:

```powershell
python -m pytest backend/tests/evals/hidden_info_leaks
```

Run narrative consistency evals:

```powershell
python -m pytest backend/tests/evals/narrative_consistency
```

These evals use deterministic fixtures and mock/fake narrator outputs. They do
not call external LLM judges and should not print hidden text in normal failure
output.

## Quest, Dead-End, And Balance Analysis

Quest completion analysis checks missing next stages, missing trigger refs,
unreachable stages, completion-path gaps, circular paths, and hidden quest
visibility risks. Dead-end detection looks for blocked required items, NPCs,
facts, locked paths, merchant availability, undiscoverable clues, and schedule
availability issues. Economy, combat, and social consequence analyzers provide
sanity checks and coverage, not automatic fixes.

These reports are authoring aids. They do not prove a world is creatively
perfect, and they do not modify world files or active saves.

## Save / Load / Migration Stress Tests

v0.9 includes deterministic stress coverage for many turns, repeated
save/load cycles, migration dry-run/apply, save-bundle import/export, replay
dry-run, and hidden-safe report output. These tests use temporary SQLite
databases and mock/local providers; they do not use real user saves.

## Performance Benchmarks

Run local benchmarks:

```powershell
python -m app.tools.benchmark --world mist_valley
```

Benchmark reports cover game loop turns, world tick, save/load, migration
dry-run, validation, map graph build, quest graph roundtrip, memory search,
and scenario regression. They record timings and safe environment summaries
only. They do not upload telemetry, record prompt text, or store API keys.

v1.0 benchmark reports include local performance budget metadata and warning or
blocker regressions for sample-world smoke checks. The quality gate consumes
those regressions in its pass/fail decision. See
`docs/V1_0_PERFORMANCE_BUDGET.md` for the current budget table and caveats.

## Prompt Profiles

Prompt profiles are local style/configuration records for provider/model
preferences:

- `GET /studio/prompt-profiles`
- `POST /studio/prompt-profiles/select`

Profiles can adjust narrator style, prompt variant, temperature overrides, and
optional token preferences. They cannot add hidden facts, raw `GameState`, raw
`state_deltas`, NPC secrets, or direct state-write authority. Provider
selection still goes through `LLMProvider`.

## v1.1 Roleplay / Dialogue Layer

v1.1 adds a local Roleplay Immersion Layer. It is built for character voice and
continuous dialogue, not for changing world authority. The LLM remains a
language layer. Dialogue, group scenes, imported character cards, lorebooks,
example dialogue, scene moods, and RP prompt profiles cannot directly modify
`GameState`, reveal hidden facts, or make NPCs know unknown information.

See `docs/ROLEPLAY_BOUNDARY.md` for the formal boundary contract.

### Import Character Cards

Character card import is authoring-only and disabled unless
`ENABLE_AUTHORING_API=true`.

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/authoring/characters/import/preview `
  -ContentType "application/json" `
  -Body '{"raw_content":"name: Mira\ndescription: A careful speaker.","input_format":"yaml"}'
```

Preview parses JSON, YAML, or simple text cards and returns candidates for RP
profile, voice profile, example dialogue, flavor lore, structured facts, hidden
facts, and unsafe entries. Apply requires explicit confirmation and validation:

```text
POST /authoring/characters/import/apply
```

External `system_prompt` and `creator_notes` are not trusted. Remote URLs and
script-like payloads are rejected. Import does not modify active `GameState`.

### Import Lorebook / World Info

Lorebook import classifies entries instead of pushing them straight into
prompts:

- `flavor_lore`
- `structured_fact_candidate`
- `hidden_fact_candidate`
- `unsafe_entry`

APIs:

```text
POST /authoring/lorebook/import/preview
POST /authoring/lorebook/import/validate
POST /authoring/lorebook/import/apply
```

Hidden fact candidates stay under visibility control. Structured fact
candidates must be saved as content-pack facts before becoming authoritative.
Unsafe prompt/control entries are quarantined.

### Configure RP Profile / Voice Profile

NPCs can define roleplay and voice fields in `npcs.yaml`:

```yaml
rp_profile:
  public_persona: "A careful archivist."
  private_self_summary: "Hidden by default."
  attachment_style: "slow trust"
voice_profile:
  tone: "measured"
  sentence_length: "mixed"
  vocabulary_style: "plain but exact"
  catchphrases:
    - "Carefully, now."
```

Safe public voice/profile fields can enter dialogue context. Private summaries,
taboo topics, secrets, and hidden facts do not enter player-facing prompts by
default.

### Dialogue Mode

Dialogue Mode creates a focused `DialogueSession` through the game API:

```text
POST /game/dialogue/start
POST /game/dialogue/continue
POST /game/dialogue/end
```

The frontend RP / Dialogue panel can start, continue, and end dialogue; choose
focus NPC, dialogue mode, scene mood, and RP prompt profile; and display safe
emotion/tone/topic summaries. Dialogue context includes only player-visible and
NPC-known information. If dialogue produces state changes, they must be
rule-authorized `StateDelta` entries and recorded events.

### Group RP

Group scenes use:

```text
POST /game/group-dialogue/start
POST /game/group-dialogue/next-speaker
POST /game/group-dialogue/end
```

Each NPC receives a separate context. One NPC's hidden knowledge does not leak
into another NPC's prompt. Dead or incapacitated NPCs do not join ordinary group
scenes.

### Scene Mood

Scene mood presets can be authored in `scene_moods.yaml` and selected in
Dialogue Mode or Group RP. A mood changes tone, pacing, sensory focus, metaphor
style, and dialogue pressure. It does not change facts, `ActionResult`, hidden
fact filtering, or rule outcomes.

### RP Prompt Profiles

Prompt profiles now include an optional RP style section. It can tune dialogue
depth, emotional intensity, prose density, response length, perspective, and
inner-thought policy. It cannot enable hidden facts or state writes:

```text
hidden_fact_policy = deny
state_modification_policy = deny
```

Use the Settings / Privacy panel or prompt profile APIs:

```text
GET /studio/prompt-profiles
POST /studio/prompt-profiles/select
```

### Example Dialogue

Example dialogue helps voice consistency but is not a fact source:

```text
GET  /authoring/worlds/{world_id}/example-dialogue
POST /authoring/worlds/{world_id}/example-dialogue/preview
POST /authoring/worlds/{world_id}/example-dialogue/validate
PUT  /authoring/worlds/{world_id}/example-dialogue
```

Only `prompt_safe` examples with safe fact policy can enter dialogue context.
Unsafe, debug-only, or hidden-fact examples stay out of runtime prompts.

### Tavern-like Import / Export

Tavern compatibility is local and best-effort. It supports preview/apply for
character cards, lorebooks/world info, example dialogue, and prompt presets,
plus safe export of NPC RP profiles, lorebook-style public facts, and prompt
profiles:

```text
POST /authoring/tavern/import/preview
POST /authoring/tavern/import/apply
POST /authoring/tavern/export
```

Import requires parse, classification, unsafe detection, preview, explicit
apply, and validation. It does not fetch remote URLs, execute scripts, trust
external system prompts, or automatically modify active worlds/saves. Safe
export does not include API keys, raw `GameState`, save data, or hidden facts.
It does not claim full compatibility with every external Tavern format.

### RP Boundary Evals

Run RP boundary evals:

```powershell
python -m pytest backend/tests/evals/rp_boundary
```

These tests use fake outputs and do not call real LLM APIs. They cover hidden
fact leakage, unknown fact mentions, example-dialogue-as-fact mistakes, group
context crossover, and scene mood fact override.

### RP Regression Playtests

RP regression playtests exercise friendly talk, interrogation, negotiation,
conflict, trust-building, group meeting, secret probing, and rumor discussion
through the dialogue manager/test harness with mock/local providers:

```powershell
python -m pytest backend/tests/test_rp_regression_playtests.py
```

Reports are safe summaries. They should not print hidden text and should not be
treated as canonical story events.

## Import / Export

v0.7 added local archive import/export for worlds, mods, and saves. v0.8 adds
advanced package dry-run/apply with manifests and checksums. These endpoints
are gated by `ENABLE_AUTHORING_API`:

- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`
- `GET /authoring/export/templates`
- `GET /authoring/export/scenarios`
- `POST /authoring/import/packages/dry-run`
- `POST /authoring/import/packages/apply`

Archives are zip bundles returned as base64 in the API response. Imports reject
zip slip/path traversal, executable files, `.env`, database files, logs, and
secret files. World and mod imports run validation. Save imports check
migration status. Save export can contain hidden state and event history by
design, so treat save bundles as local private backup data.

Advanced packages include `local_package_manifest.json` with package id, type,
version, schema/content version, included files, checksums, dependencies,
conflicts, created time, and notes. Apply requires explicit confirmation and a
passing dry-run.

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
See `docs/QUALITY_SYSTEM.md` for v0.9 quality report, quality gate,
playtest scenario, benchmark, health score, and coverage schemas.

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
- v0.8 visual editors are useful structured editors, not a full visual IDE or
  collaborative authoring system.
- Visual editor saves always go through backend validation; they do not modify
  active sessions or active saves.
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
- World branch/diff is a lightweight local authoring helper, not a Git
  replacement and not a merge system.
- v0.9 quality reports and health scores are heuristic local authoring aids,
  not absolute quality judgments.
- Quality, playtest, eval, benchmark, and stress APIs are local-only tools and
  should not be exposed as hosted endpoints.
- There is no dedicated `ENABLE_QUALITY_API` yet; some quality analyzer routes
  rely on the local-only deployment boundary rather than a separate flag.
