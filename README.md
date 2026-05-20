# Local LLM Interactive Novel World Engine

A local-first interactive novel world engine. The LLM is used for intent
parsing, narration, and memory summarization, while the local engine owns
world state, rule resolution, event logs, saves, visibility, social systems,
combat, and content validation.

This project is for local personal use. It is not designed as a hosted service.

## Current Version Scope

v1.8 is Stable Contracts & Compatibility on top of v1.7 Polished Desktop
Studio, v1.6 Advanced Gameplay Modules, v1.5 Local Model & Prompt Lab, v1.4
Content Production Pipeline, v1.3 Advanced NPC Simulation, v1.2 Visual
Authoring Pro, the v1.1 Roleplay Immersion Layer, and the v1.0 Stable Local
Studio Edition. v1.0 freezes the local contracts built through the v0.x
series, v1.1 adds character voice and RP-safe dialogue, v1.2 expands local
visual authoring, v1.3 adds bounded rule-driven NPC autonomy, v1.4 adds local
batch content production, v1.5 adds local provider/prompt diagnostics, v1.6
adds local declarative gameplay modules, v1.7 improves local desktop startup,
project selection, diagnostics, update notes, crash reports, and packaging
safety, and v1.8 freezes pre-v2.0 contract and compatibility behavior without
changing world authority:

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
- Local Model & Prompt Lab for provider capability metadata, fake/default
  benchmarks, Prompt A/B, style labs, structured-output reliability, usage
  summaries, context inspection, prompt diff, model compatibility, provider
  routing, prompt regression, local diagnostics, token budgets, and experiment
  packages.
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
- Authoring Pro Boundary Contract.
- Authoring Validation Gate.
- Visual Map Editor Pro and Quest Graph Editor Pro.
- NPC Relationship Graph Editing and Faction Conflict Editor.
- Rumor / Crime Consequence Graph Pro.
- Item / Economy Editor Pro.
- RP Character Authoring UI Pro.
- Dialogue Scene Editor and Group RP Scene Authoring.
- Character Pack Builder.
- Template Wizard.
- World Branch Merge Assistant and Content Diff Review.
- Authoring Workflow Presets.
- Local Content Library.
- Reference Picker / ReferenceIndex.
- Authoring Draft History.
- NPC Simulation Boundary Contract.
- NPC Intent Queue and Short-Term Plans.
- NPC Memory-Based Reactions.
- NPC Relationship-Driven Behavior.
- NPC Faction Duties.
- NPC Rumor Decisions.
- NPC Fear / Trust / Loyalty models.
- NPC Conflict Avoidance.
- NPC Daily Goal Replanning.
- NPC Simulation Tick Orchestrator.
- NPC Simulation Debugger and Behavior Timeline.
- NPC Simulation Authoring Presets.
- NPC Simulation Quality Evals.
- NPC Simulation Regression Playtests.
- Content Production Boundary Contract.
- World Pack Wizard.
- NPC Pack Generator and Quest Pack Generator.
- Location Cluster Templates.
- Mystery Template System and Faction Template System.
- Content Batch Validator and Content Coverage Planner.
- Export / Import Profiles.
- Local Content Library Pro.
- Batch Character Card Import.
- Batch Lorebook Classification.
- Script Package Builder.
- Campaign Starter Kit Builder.
- Production Pipeline Dashboard.
- Content Production CLI.
- Batch Quality Gate.
- Gameplay Module Boundary Contract.
- Gameplay Module Manifest and safe module loader.
- Declarative Action Mod System.
- Action Registry Extension.
- Action DSL Preconditions / Checks / Effects.
- Action Mod Validation and Action Mod Editor.
- Magic, Hacking, Crafting, Investigation / Deduction, Travel / Survival,
  Stealth, Combat, Social Manipulation, Faction Mission, and Domain / Base
  Management modules.
- Gameplay Module Quality Gate.
- Gameplay Module Regression Playtests.
- Gameplay Module Debugger.
- Gameplay Module Import / Export.
- Desktop Studio Boundary Contract.
- Desktop Launcher Pro scripts.
- Project Selector and Recent Projects.
- Local Config Manager safe summaries.
- Local Update Notes.
- Desktop Health Check.
- Workspace Templates.
- Crash Report Local Viewer.
- Desktop Startup Diagnostics.
- Desktop Packaging Safety Pass.
- Compatibility Boundary Contract.
- Stable GameState, StateDelta, and EventLog contracts.
- Stable Content Pack, Save Migration, Module Manifest, Action Mod, Prompt
  Profile, Provider Gateway, Package, Authoring API, Debug API, and Quality
  Gate contracts.
- Schema Version Compatibility Matrix.
- Compatibility Test Suite.
- Migration Failure Recovery.
- Deprecated Field Policy and Backward Compatibility Shims.
- Contract Docs Generator and v2.0 Compatibility Checklist.

The LLM is still not the world judge. Rule outcomes are decided by local code.
NPC simulation is deterministic, finite, knowledge-scoped, and applied through
`StateDelta` plus `Event`; it is not an LLM multi-agent simulator. v1.4
production tools generate drafts, candidates, packages, previews, and reports;
they do not directly modify active `GameState`. v1.6 gameplay modules resolve
through `ActionRegistry` and deterministic rule handlers; Action Mods are
declarative data and cannot execute arbitrary code. v1.7 desktop tools are
local convenience layers around backend APIs; they do not directly write
`GameState`, read frontend secrets, or turn the desktop shell into a second
engine. v1.8 is not a new gameplay release; it stabilizes versioned contracts,
compatibility gates, migration recovery, and package validation ahead of v2.0.

## v1.8 Documentation Map

- `docs/COMPATIBILITY_BOUNDARY.md`: v1.8 contract/version compatibility
  boundary, migration rules, deprecated-field rules, shim limits, and package
  compatibility requirements.
- `docs/GAMESTATE_CONTRACT.md`, `docs/STATEDELTA_CONTRACT.md`, and
  `docs/EVENTLOG_CONTRACT.md`: stable core runtime contracts.
- `docs/CONTENT_PACK_SCHEMA_CONTRACT.md` and
  `docs/SAVE_MIGRATION_CONTRACT.md`: stable content pack and save migration
  contracts.
- `docs/MODULE_MANIFEST_CONTRACT.md` and `docs/ACTION_MOD_CONTRACT.md`:
  gameplay module and declarative action contracts.
- `docs/PROMPT_PROFILE_CONTRACT.md` and
  `docs/PROVIDER_GATEWAY_CONTRACT.md`: prompt/profile and provider gateway
  contracts. Prompt profiles cannot expand LLM authority.
- `docs/PACKAGE_CONTRACT.md`, `docs/AUTHORING_API_CONTRACT.md`,
  `docs/DEBUG_API_CONTRACT.md`, and `docs/QUALITY_GATE_CONTRACT.md`: package,
  local API, and quality report contracts.
- `docs/DEPRECATION_POLICY.md`, `docs/DEPRECATED_FIELDS.md`,
  `docs/CONTRACT_INDEX.md`, and `docs/SCHEMA_VERSION_MATRIX.md`: generated and
  policy-level compatibility references.
- `docs/V1_8_LLM_BOUNDARY_AUDIT.md`,
  `docs/V1_8_VISIBILITY_COMPATIBILITY_AUDIT.md`, and
  `docs/V1_8_SECURITY_AUDIT.md`: release-freeze audits.
- `docs/V1_8_ACCEPTANCE_REPORT.md` and `docs/V1_8_RELEASE_NOTES.md`: v1.8
  acceptance and release summary.

## v1.8 Compatibility Workflows

Run the compatibility matrix:

```powershell
python -m backend.app.tools.compatibility_matrix
```

Generate contract docs:

```powershell
python -m backend.app.tools.generate_contract_docs
```

Run the v2 compatibility checklist:

```powershell
python -m backend.app.tools.v2_compatibility_checklist
```

Run compatibility tests:

```powershell
python -m pytest backend/tests/compatibility
```

Deprecated fields are warning-backed compatibility metadata. They are not
removed immediately, and removal requires a replacement, migration strategy,
and contract review. Compatibility shims may fill safe defaults or rename known
legacy fields, but they must not change hidden/visible classification or hide
unsupported breaking changes.

Migration failure recovery creates a pre-migration backup and checksum before
apply, preserves the original save on failure, records a failed attempt, and
offers an explicit restore path. It is not an automatic repair system for every
corrupted save.

Package import/export still requires validation, compatibility checks,
checksum verification, zip-slip protection, executable rejection, and secret
exclusion. Safe packages must not contain `.env`, API keys, logs, caches,
databases, raw env, or hidden text by default.

The LLM remains a narrator/parser/summarizer layer. v1.8 compatibility tools,
migration recovery, shims, contract docs generation, and checklists do not call
an LLM and do not let model output directly modify `GameState`.

## v1.7 Documentation Map

- `docs/DESKTOP_STUDIO_BOUNDARY.md`: v1.7 desktop shell, backend, frontend,
  local config, backup/export, log, crash, and secret boundary.
- `docs/DESKTOP_PACKAGING.md`: local launcher, packaging safety checklist,
  `.gitignore` expectations, and prototype limits.
- `docs/V1_7_ROADMAP.md`: v1.7 Polished Desktop Studio roadmap.
- `docs/V1_7_LLM_BOUNDARY_AUDIT.md`: v1.7 LLM permission boundary audit.
- `docs/V1_7_LOCAL_DATA_PRIVACY_AUDIT.md`: v1.7 local data/privacy audit.
- `docs/V1_7_SECURITY_AUDIT.md`: v1.7 security and desktop packaging audit.

## v1.6 Documentation Map

- `docs/GAMEPLAY_MODULE_BOUNDARY.md`: v1.6 gameplay module, Action Mod,
  StateDelta, EventLog, Visibility, import/export, and no-code boundary.
- `docs/V1_6_ROADMAP.md`: v1.6 Advanced Gameplay Modules roadmap.
- `docs/V1_6_LLM_BOUNDARY_AUDIT.md`: v1.6 LLM permission boundary audit.
- `docs/V1_6_VISIBILITY_GAMEPLAY_MOD_AUDIT.md`: v1.6 visibility, gameplay,
  and module audit.
- `docs/V1_6_SECURITY_AUDIT.md`: v1.6 security, module, and import audit.

## v1.5 Documentation Map

- `docs/MODEL_PROMPT_LAB_BOUNDARY.md`: v1.5 Model & Prompt Lab provider,
  prompt profile, context, benchmark, and experiment boundary.
- `docs/V1_5_ROADMAP.md`: v1.5 Local Model & Prompt Lab roadmap.
- `docs/V1_5_LLM_BOUNDARY_AUDIT.md`: v1.5 LLM permission boundary audit.
- `docs/V1_5_VISIBILITY_PROMPT_CONTEXT_AUDIT.md`: v1.5 visibility, prompt,
  and context audit.
- `docs/V1_5_SECURITY_AUDIT.md`: v1.5 security, provider, and API key audit.

## v1.4 Documentation Map

- `docs/SPEC.md`: project scope, boundaries, and known limitations.
- `docs/WORLD_ENGINE.md`: engine behavior, rules, state, events, authoring,
  quality, migration, and local studio architecture.
- `docs/LLM_PROTOCOL.md`: provider boundary, prompt/profile rules, and why LLM
  output cannot directly change `GameState`.
- `docs/ROLEPLAY_BOUNDARY.md`: v1.1 RP expression/fact boundary.
- `docs/AUTHORING_BOUNDARY.md`: v1.2 authoring draft/preview/validate/save
  boundary.
- `docs/NPC_SIMULATION_BOUNDARY.md`: v1.3 NPC simulation knowledge,
  visibility, StateDelta, EventLog, and no-LLM-agent boundary.
- `docs/CONTENT_PRODUCTION_BOUNDARY.md`: v1.4 production draft, batch import,
  package, validation, quality, and active-GameState boundary.
- `docs/CONTENT_PACKS.md`: content pack format and authoring notes.
- `docs/V1_4_ROADMAP.md`: v1.4 Content Production Pipeline roadmap.
- `docs/V1_4_LLM_BOUNDARY_AUDIT.md`: v1.4 LLM permission audit.
- `docs/V1_4_VISIBILITY_CONTENT_PACKAGE_AUDIT.md`: v1.4 visibility/content
  package audit.
- `docs/V1_4_SECURITY_AUDIT.md`: v1.4 security/import/batch audit.
- `docs/V1_3_ROADMAP.md`: v1.3 Advanced NPC Simulation roadmap.
- `docs/V1_3_LLM_BOUNDARY_AUDIT.md`: v1.3 LLM permission audit.
- `docs/V1_3_VISIBILITY_KNOWLEDGE_NPC_AUDIT.md`: v1.3 visibility,
  NPC-knowledge, and simulation audit.
- `docs/V1_3_SECURITY_AUDIT.md`: v1.3 security/debug audit.
- `docs/V1_2_ROADMAP.md`: v1.2 Visual Authoring Pro roadmap.
- `docs/V1_2_LLM_BOUNDARY_AUDIT.md`: v1.2 LLM permission audit.
- `docs/V1_2_VISIBILITY_AUTHORING_RP_AUDIT.md`: v1.2 visibility/RP audit.
- `docs/V1_2_SECURITY_AUDIT.md`: v1.2 security/import/package audit.
- `docs/V1_0_CONTENT_SCHEMA_CONTRACT.md`: frozen v1.0 content schema contract.
- `docs/V1_0_API_CONTRACT.md`: frozen v1.0 API contract.
- `docs/V1_0_SAVE_MIGRATION_GUARANTEE.md`: migration guarantees and matrix.
- `docs/V1_0_MOD_CONTRACT.md`: content-only mod packaging contract.
- `docs/DESKTOP_PACKAGING.md`: local startup scripts, startup diagnostics,
  desktop prototype limits, and packaging safety checklist.
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
ENABLE_USAGE_TRACKING=false
ENABLE_PLAYTEST_API=false
ENABLE_EVAL_API=false
VITE_API_BASE_URL=http://127.0.0.1:8000
MEMORY_BACKEND=sqlite
AUTHORING_ROOT=worlds
MODS_ROOT=mods
MODULE_ROOT=gameplay_modules
TEMPLATE_ROOT=templates
PACKAGE_IMPORT_ROOT=imports
CONTENT_LIBRARY_ROOT=
WORKSPACE_ROOT=
LOG_DIR=logs
BACKUP_DIR=backups
```

`LLM_PROVIDER=mock` is the local development default. `local_stub` is a
deterministic offline local-provider placeholder. `local_http` posts to
`LOCAL_LLM_BASE_URL/chat/completions` with an OpenAI-compatible chat payload and
uses `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT_SECONDS`, and
`LOCAL_LLM_JSON_MODE`. It is configurable for local model services but still
does not make the model a world judge. Use `openai` only when you explicitly
want real API calls and have set the API key through the environment. API keys
must never be committed, logged, or placed in frontend code.

`AUTHORING_ROOT`, `MODS_ROOT`, `MODULE_ROOT`, `TEMPLATE_ROOT`, `PACKAGE_IMPORT_ROOT`,
`CONTENT_LIBRARY_ROOT`, and `MEMORY_BACKEND` document the intended local
configuration surface. Some runtime paths still use the current repository
defaults; v1.4 Local Content Library Pro currently derives its roots from the
local import/export service rather than a dedicated `CONTENT_LIBRARY_ROOT`
runtime setting.

There is currently no separate `ENABLE_QUALITY_API` setting. v0.9-v1.6 quality
tools reuse local-only debug/eval/playtest/performance/authoring gates where
implemented; some analyzer endpoints are local-only and should not be exposed
outside a trusted localhost setup.

`WORKSPACE_ROOT`, `LOG_DIR`, and `BACKUP_DIR` document v1.7 Desktop Studio
local path intentions. Current services still default to the current
workspace/repository and ignored local `logs/` unless a specific script or
future settings integration uses these values. Do not put secrets in these
paths, and do not expose them as frontend `VITE_*` variables.

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

## Local Studio Launcher Pro

v1.7 keeps the desktop app shell local and upgrades the launcher into a more
reliable local startup surface. It is still not a formal installer. The scripts
run safe startup diagnostics, check Python 3.11+, Node/npm, backend imports,
installed frontend dependencies, `.env` presence, `DATABASE_URL`, workspace
status, frontend build presence, previous crash reports, and backend/frontend
port availability. They then start the backend, start the frontend in dev mode
or built-preview mode, run local health checks, print safe status, and open the
local frontend URL:

```powershell
.\scripts\start_local_studio.ps1
```

```bash
bash scripts/start_local_studio.sh
```

Help:

```powershell
.\scripts\start_local_studio.ps1 -Help
```

```bash
bash scripts/start_local_studio.sh --help
```

Safe startup diagnostics can also run directly:

```powershell
python -m backend.app.tools.startup_diagnostics
python -m backend.app.tools.startup_diagnostics --json
```

The launcher reads local environment variables and applies safe defaults for
`DATABASE_URL`, `LLM_PROVIDER`, `ENABLE_DEBUG_API`, `ENABLE_AUTHORING_API`,
`ENABLE_PERF_LOGGING`, and `VITE_API_BASE_URL`. It does not set, print, or
embed `LLM_API_KEY`, and it only passes `VITE_API_BASE_URL` to the frontend
process. If `.env` is missing, it continues with safe defaults and suggests
copying `.env.example` for local customization.

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
without starting backend/frontend processes. Use `-SkipStartupDiagnostics` or
`--skip-startup-diagnostics` only when you want the older launcher checks
without the v1.7 diagnostics report. After launch, the scripts check:

- `GET /health`
- `GET /studio/status`
- frontend URL availability

Windows PowerShell is the primary launcher path. The shell launcher is a
convenience prototype for macOS/Linux-style shells; macOS uses `open` and Linux
usually uses `xdg-open` to launch a browser automatically. Neither script
creates a formal installer, signs code, enables auto-update, syncs to cloud, or
packages secrets.

If Windows PowerShell prints a profile signing warning before the launcher
output appears, treat it as a local PowerShell profile policy warning rather
than a studio failure. Run with `powershell -NoProfile -ExecutionPolicy Bypass`
if you need to suppress profile loading.

Launcher logs go to `logs/`, which is ignored by git. The launcher does not
modify `GameState`, saves, databases, worlds, modules, prompt profiles, or
content packs.

Desktop packaging remains a local prototype. Before sharing any local bundle,
run `python -m pytest`, `cd frontend && npm.cmd run build`, confirm
`git ls-files` does not include `.env`, databases, logs, crash reports,
backups, caches, `frontend/dist`, or desktop build outputs, and scan scripts
and built assets for real API keys. See `docs/DESKTOP_PACKAGING.md` for the
full packaging safety checklist and Tauri/Electron/local-launcher review.

## v1.7 Desktop Studio Workflows

v1.7 desktop workflows are local-only convenience features around backend APIs.
They do not replace validation gates, do not write active `GameState`, do not
upload data, and do not expose API keys to the frontend.

### Select A Project

Use the Project Selector in the Studio UI, or call:

```text
GET  /studio/workspaces
POST /studio/workspaces
POST /studio/workspaces/select
GET  /studio/workspaces/current
```

Workspace paths are validated and returned to the frontend as redacted path
summaries. Adding a workspace stores a reference only; it does not import
unknown content or modify active saves.

### Recent Projects

The Studio Home page can show recent project summaries:

```text
GET    /studio/recent-projects
DELETE /studio/recent-projects/{workspace_id}
POST   /studio/recent-projects/clear
```

Recent entries contain display name, redacted path, last-opened time, optional
last world id, and safe status. They do not store API keys, raw env, or full
sensitive paths.

### Local Config Manager

Use Settings / Local Config to inspect safe configuration:

```text
GET  /studio/config/summary
GET  /studio/config/issues
POST /studio/config/generate-template
```

The summary shows provider type/model, local feature flags, database
configured yes/no, redacted path hints, and whether an API key is configured
as a boolean. It never returns the key value or raw `.env`. The template
endpoint returns an `.env.example`-style template and does not write secrets.

### Logs And Error Recovery

v1.7 defines the Log Viewer and Error Recovery Wizard boundaries, but the
current runtime implementation is not a complete log/recovery workflow yet.
The required boundary is:

- log views must be debug-gated, read only local `logs/`, reject path
  traversal, and redact API keys, raw prompts, Authorization headers, and
  hidden facts;
- recovery steps must default to safe recommendations and require explicit
  confirmation before any risky local operation.

Use the launcher logs in ignored `logs/` for now and keep recovery actions
manual unless a future backend endpoint makes the operation explicit.

### Backup / Restore

v1.7 documents and tests the desktop backup/restore safety boundary, but the
dedicated desktop Backup / Restore runtime is not complete in the current
code. The required safe behavior is:

- backup defaults exclude `.env`, API keys, logs, caches, databases, frontend
  build outputs, desktop build outputs, and executable files;
- restore must dry-run first, validate manifest/checksums, reject zip slip and
  executable files, detect conflicts, and require explicit confirmation.

Existing save and package import/export tools still apply their own validation
and migration checks.

### One-click Quality Gate And World Export

Dedicated v1.7 one-click desktop workflows are not complete yet. Use the
existing quality and export tooling:

```powershell
python -m app.tools.quality_gate
python -m app.tools.validate_world worlds/mist_valley
```

World export must use safe profiles and validation. Safe exports must not
include `.env`, API keys, logs, caches, database connection config, hidden
authoring text by default, or executable files.

### Offline Help And Update Notes

Release/update notes are indexed locally:

```text
GET /studio/update-notes
```

This reads local docs only. It does not check the network, download patches,
or run update scripts. A complete searchable Offline Help Docs page is still a
future polish item; use local `docs/` and this README as the source of truth.

### Desktop Health Check

Run health checks from the Studio UI or through:

```text
GET  /studio/health
POST /studio/health/check
```

Health checks report backend status, optional frontend reachability, database
configured/reachable status, safe config status, workspace/world directory
status, authoring/debug API state, provider safe summary, and recent-error
placeholder status. They do not call real providers and do not return secrets.

### Workspace Templates

Create local workspaces from templates:

```text
GET  /studio/workspace-templates
POST /studio/workspaces/create-from-template
```

Templates can create folder structures and safe starter files. They do not
copy `.env`, write API keys, execute scripts, download remote templates, or
overwrite existing non-empty workspaces.

### Crash Report Local Viewer

Crash reports are local and debug-gated:

```text
GET    /debug/crash-reports
GET    /debug/crash-reports/{id}
DELETE /debug/crash-reports/{id}
```

Reports include safe message, redacted stack, component, error type, and safe
context summary. API keys, Authorization headers, raw env, raw prompts,
hidden fact text, and database passwords are redacted or omitted.

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

## v1.2 Visual Authoring Pro Workflow

Enable authoring locally:

```powershell
$env:ENABLE_AUTHORING_API = "true"
```

All v1.2 editors are local content-pack tools. Preview and validate do not
write disk. Save writes YAML/package files only after validation and explicit
save. Editors do not modify active `GameState`, active sessions, active saves,
or prompt permissions.

### Visual Map Editor Pro

Use the frontend Authoring workspace Map Editor, or call:

```text
GET  /authoring/worlds/{world_id}/map
POST /authoring/worlds/{world_id}/map/preview
POST /authoring/worlds/{world_id}/map/validate
PUT  /authoring/worlds/{world_id}/map
```

It supports regions, layers, node coordinates, location nodes, exits, locked,
hidden, conditional, one-way edges, travel cost, discovery rules, validation
issues, and diff/impact preview. Hidden path data stays out of player maps.

### Quest Graph Editor Pro

Use the frontend Quest Graph panel, or call:

```text
GET  /authoring/worlds/{world_id}/quests/graph
POST /authoring/worlds/{world_id}/quests/graph/preview
POST /authoring/worlds/{world_id}/quests/graph/validate
PUT  /authoring/worlds/{world_id}/quests/graph
POST /authoring/worlds/{world_id}/quests/graph/scenario-draft
```

It edits quest, stage, objective, trigger, reward, consequence, optional path,
failure path, and hidden objective data. Scenario drafts are deterministic
testing drafts, not active quest state.

### NPC Relationship Editor And Faction Conflict Editor

Use the Social Graph editor:

```text
GET  /authoring/worlds/{world_id}/social/graph
POST /authoring/worlds/{world_id}/social/graph/preview
POST /authoring/worlds/{world_id}/social/graph/validate
PUT  /authoring/worlds/{world_id}/social/graph
```

It edits NPC relationship values, hidden relationships, relation type, RP tone
presets, faction visibility, alert levels, conflict levels, relation edges, and
conflict tags. Player social graphs remain filtered.

### RP Character Authoring UI Pro

Use the RP Character Editor panel, or call:

```text
GET  /authoring/worlds/{world_id}/rp/characters/pro
POST /authoring/worlds/{world_id}/rp/characters/pro/import-preview
POST /authoring/worlds/{world_id}/rp/characters/pro/preview
POST /authoring/worlds/{world_id}/rp/characters/pro/validate
PUT  /authoring/worlds/{world_id}/rp/characters/pro
POST /authoring/worlds/{world_id}/rp/characters/pro/safe-export
```

It edits NPC base fields, RP Profile, Voice Profile, default emotional state,
example dialogue refs, lorebook links, scene mood preferences, import reports,
and safe exports. Unsafe external prompt text is rejected or quarantined.

### Dialogue Scene Editor And Group RP Scene Authoring

Use the scene authoring panels, or call:

```text
GET  /authoring/worlds/{world_id}/dialogue-scenes
POST /authoring/worlds/{world_id}/dialogue-scenes/preview
POST /authoring/worlds/{world_id}/dialogue-scenes/validate
PUT  /authoring/worlds/{world_id}/dialogue-scenes
GET  /authoring/worlds/{world_id}/group-rp-scenes
POST /authoring/worlds/{world_id}/group-rp-scenes/preview
POST /authoring/worlds/{world_id}/group-rp-scenes/validate
PUT  /authoring/worlds/{world_id}/group-rp-scenes
```

These save reusable templates. They do not start active dialogue/group sessions
and do not call the LLM to generate scene facts.

### Character Pack Builder

Character packs bundle reusable NPC/RP/voice/example/dialogue/group-scene/lore
content:

```text
POST /authoring/character-packs/export
POST /authoring/character-packs/import-dry-run
POST /authoring/character-packs/import-apply
```

Import apply requires explicit confirmation and validation. Packs reject path
traversal, executable files, API keys, remote URLs, and script-like payloads.

### Template Wizard

Template Wizard creates deterministic drafts:

```text
POST /authoring/template-wizard/preview
POST /authoring/template-wizard/validate
POST /authoring/template-wizard/apply
```

Supported draft types include world, location cluster, questline, NPC set,
character pack, dialogue scene, group RP scene, faction conflict, and mystery
case. Templates are data only; they do not execute scripts.

### Merge Assistant / Diff Review

Use Merge Assistant for local branch conflict review:

```text
POST /authoring/worlds/{world_id}/merge/preview
POST /authoring/worlds/{world_id}/merge/validate
POST /authoring/worlds/{world_id}/merge/save
```

Use Diff Review for unified content diff summaries:

```text
POST /authoring/diff/review
```

These tools do not auto-resolve conflicts with an LLM. Save requires explicit
confirmation and validation.

### Local Content Library

Use the Local Content Library page, or call:

```text
GET  /library/items
GET  /library/items/{id}
POST /library/items/{id}/validate
POST /library/import
POST /library/export
POST /library/duplicate
```

It manages local worlds, character packs, template packs, scenario suites,
prompt profiles, RP profiles, and mods. It rejects path traversal and does not
execute package code.

### Reference Picker

The common Reference Picker is backed by:

```text
GET /authoring/worlds/{world_id}/references
```

It returns authoring-safe metadata for locations, NPCs, items, facts, quests,
quest stages, factions, relationships, rumors, crime types, RP profiles, scene
moods, and prompt profiles. Hidden refs are marked and are not exposed through
player APIs.

### Draft History

Draft History stores local authoring snapshots only:

```text
GET    /authoring/drafts
POST   /authoring/drafts/snapshot
POST   /authoring/drafts/compare
POST   /authoring/drafts/{draft_id}/restore
DELETE /authoring/drafts/{draft_id}
```

Restored drafts still require validation before save. Draft history rejects API
keys and raw env/config-like content.

### Authoring Validation Gate

The Authoring Validation Gate is a backend service used by visual editor saves,
world export/import, package apply, and merge save flows. There is no separate
manual CLI command for the gate; run it through normal authoring save/import
paths, or use validation-oriented tests:

```powershell
python -m pytest backend/tests/test_authoring_validation_gate.py
python -m pytest backend/tests/test_v12_visual_authoring_pro_integration.py
```

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

## v1.3 NPC Simulation

v1.3 adds bounded NPC simulation. It is part of the backend rule layer; there
is no separate runtime feature flag for ordinary simulation helpers. Debug
inspection still requires local debug mode:

```powershell
$env:ENABLE_DEBUG_API = "true"
```

NPC simulation remains deterministic local code. It can queue finite intents,
build short plans, react to known memories, use relationships and faction
duties, decide whether to spread known rumors, avoid conflict, and replan daily
goals. It cannot call the LLM, cannot know unknown facts, cannot run forever,
and cannot directly modify active `GameState`. State changes are returned as
`StateDelta` and recorded as `Event`.

### NPC Simulation Debugger

Debug endpoints are available only when `ENABLE_DEBUG_API=true`:

```text
GET  /debug/sessions/{session_id}/npc-simulation
GET  /debug/sessions/{session_id}/npcs/{npc_id}/simulation
GET  /debug/sessions/{session_id}/npc-simulation/ticks
POST /debug/sessions/{session_id}/npc-simulation/dry-run-tick
GET  /debug/sessions/{session_id}/npcs/{npc_id}/behavior-timeline
GET  /debug/saves/{save_id}/npcs/{npc_id}/behavior-timeline
```

The debugger shows intent counts, plan counts, known fact ids, hidden fact ids,
goals, emotional/social state, faction duties, known rumors/crimes, redacted
debug reasons, and dry-run tick results. Dry-run tick does not write the
database or mutate active state. Hidden fact text and API keys are redacted by
default.

### NPC Simulation Quality Evals

NPC simulation quality checks are integrated into the quality pipeline and
World Health source reports. Run focused tests:

```powershell
python -m pytest backend/tests/test_npc_simulation_quality.py
python -m pytest backend/tests/test_v13_npc_simulation_integration.py
```

The evals detect unknown fact usage, hidden fact leaks, repeated intent loops,
blocked plan loops, dead NPC actions, invalid targets, missing events, too many
intents, plan budget overruns, and low behavior coverage. Reports are local
diagnostics and do not modify `GameState`.

### NPC Simulation Regression Playtests

Run deterministic v1.3 regression tests:

```powershell
python -m pytest backend/tests/test_npc_simulation_regression.py
python -m pytest backend/tests/test_v13_npc_simulation_integration.py
```

Regression scenarios use temporary SQLite storage and synthetic fixtures for
guard patrol, crime reporting, rumor spread, avoid-player behavior, seek-help,
daily replanning, relationship response, faction duty, and injured-rest cases.
They do not call real LLM APIs and do not modify real saves.

### NPC Simulation Presets

NPC simulation presets are authoring-draft helpers. Enable authoring locally:

```powershell
$env:ENABLE_AUTHORING_API = "true"
```

Available endpoints:

```text
GET  /authoring/npc-simulation-presets
POST /authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/preview
POST /authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/apply-draft
```

Built-in presets include guard, merchant, informant, hostile actor, timid
villager, loyal subordinate, rumor spreader, and investigator. Applying a
preset returns an NPC draft preview and validation-gate result. It does not
modify active `GameState`, does not execute scripts, and does not grant NPCs
unknown facts.

## v1.4 Content Production Pipeline

v1.4 production tools are local studio tools. They create drafts, candidates,
packages, previews, reports, and quality decisions. They do not directly modify
active `GameState`, do not execute scripts, do not download remote content, and
do not call a real LLM by default. Enable authoring APIs only on a trusted
local machine:

```powershell
$env:ENABLE_AUTHORING_API = "true"
```

### World Pack Wizard

```text
POST /authoring/production/world-pack/create-draft
POST /authoring/production/world-pack/preview
POST /authoring/production/world-pack/validate
POST /authoring/production/world-pack/apply
```

The wizard writes generated world-pack files only after validation and explicit
apply.

### NPC Pack Generator

```text
POST /production/npc-pack/preview
POST /production/npc-pack/validate
POST /production/npc-pack/apply
POST /production/npc-pack/export
```

Generated NPCs, RP profiles, voice profiles, relationships, goals, and
schedules are candidates. Hidden secrets stay hidden.

### Quest Pack Generator

```text
POST /production/quest-pack/preview
POST /production/quest-pack/validate
POST /production/quest-pack/apply
```

Quest drafts include quest graph and scenario regression candidates. They do
not publish quests to active saves.

### Location Cluster Templates

```text
GET  /production/location-clusters
POST /production/location-clusters/{id}/preview
POST /production/location-clusters/{id}/apply-draft
```

Preview renders a `MapVisualGraph`; hidden edges stay hidden.

### Mystery Template System

```text
GET  /production/mystery-templates
POST /production/mystery-templates/{id}/preview
POST /production/mystery-templates/{id}/apply-draft
```

Truth facts are hidden, red herrings are marked, and normal previews avoid
revealing hidden truth text.

### Faction Template System

```text
GET  /production/faction-templates
POST /production/faction-templates/{id}/preview
POST /production/faction-templates/{id}/apply-draft
```

Faction templates produce drafts for factions, relations, duties, and hooks;
they are not a war simulator.

### Batch Validator

```text
POST /production/batch-validate
```

CLI:

```powershell
python -m backend.app.tools.production batch-validate --target world:mist_valley
```

Batch validation aggregates pass/warning/fail/blocker status and does not
execute package content.

### Coverage Planner

```text
POST /production/content-coverage-plan
```

The planner recommends missing content coverage without writing content.

### Export / Import Profiles

```text
GET /authoring/import-export-profiles
```

Safe export redacts hidden text and forbids API keys. Import profiles require
validation and reject executables.

### Local Content Library Pro

```text
GET  /library/items
POST /library/items/search
GET  /library/items/{id}
POST /library/items/{id}/validate
POST /library/items/batch-validate
POST /library/import
POST /library/items/{id}/export
```

Normal library views avoid sensitive absolute paths and hidden details.

### Batch Character Card Import

```text
POST /production/characters/batch-import/preview
POST /production/characters/batch-import/apply-draft
POST /production/characters/batch-import/export-pack
```

Unsafe prompt text is flagged. Import does not automatically overwrite NPCs or
write active worlds.

### Batch Lorebook Classification

```text
POST /production/lorebooks/batch-classify/preview
POST /production/lorebooks/batch-classify/apply-draft
```

Hidden entries stay redacted in normal reports and require explicit selection
before apply.

### Script Package Builder

```text
POST /production/script-packages/build-dry-run
POST /production/script-packages/build
POST /production/script-packages/validate
POST /production/script-packages/export
```

Script packages are data packages. The builder rejects executables, `.env`,
API keys, databases, and logs.

### Campaign Starter Kit Builder

```text
POST /production/campaign-starter/preview
POST /production/campaign-starter/build
POST /production/campaign-starter/export-script
```

Starter kits compose world, NPC, quest, faction, optional mystery, scenario,
quality, and package drafts. They are not automatic full campaign writers.

### Production Pipeline Dashboard

```text
GET /production/pipeline-summary
```

The dashboard summarizes active drafts, generated packages, batch validation,
coverage plans, quality status, profiles, script packages, and campaign
starter status.

### Production CLI

```powershell
python -m backend.app.tools.production world-wizard --world-id demo --name "Demo" --preview --json
python -m backend.app.tools.production npc-pack --world-id mist_valley --pack-id villagers --preview
python -m backend.app.tools.production quest-pack --world-id mist_valley --pack-id starter --preview
python -m backend.app.tools.production batch-validate --target world:mist_valley
python -m backend.app.tools.production build-script-package --package-id starter --name "Starter" --validate
python -m backend.app.tools.production campaign-starter --campaign-id starter --name "Starter" --preview
python -m backend.app.tools.production coverage-plan --world-id mist_valley
python -m backend.app.tools.production batch-quality-gate --world mist_valley
```

Use `--apply` only when you intentionally want a write/build operation. The CLI
redacts hidden/private/API-key-like output and can emit `--json`.

### Batch Quality Gate

```text
POST /production/batch-quality-gate
```

CLI:

```powershell
python -m backend.app.tools.production batch-quality-gate --world mist_valley --profile standard
```

The gate reports pass/fail, blockers, warnings, per-item results, and
recommended actions. It does not modify content or call a real LLM.

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

## v1.5 Local Model & Prompt Lab

v1.5 Prompt Lab is a local workbench for comparing providers, models, prompt
profiles, context builders, structured JSON reliability, token budgets, usage
metadata, and prompt regression. It produces reports only. It does not change
world facts, active `GameState`, active saves, or content packs.

Prompt Lab endpoints are local studio tools. In the current implementation
they reuse the benchmark/usage gates:

- benchmark-style APIs require `ENABLE_DEBUG_API=true`,
  `ENABLE_PERF_LOGGING=true`, or `ENABLE_USAGE_TRACKING=true`
- usage APIs require `ENABLE_DEBUG_API=true` or `ENABLE_USAGE_TRACKING=true`
- there is no separate `ENABLE_PROMPT_LAB_API` setting yet

### Provider Capability

Open the Prompt Lab page in the frontend and click **Load Capabilities**, or
call:

```text
GET /prompt-lab/provider-capabilities
```

The registry shows provider/model metadata such as JSON support, local-only
status, recommended use cases, and whether a key is configured as a boolean.
It does not call a provider and does not return API keys.

### Provider Benchmark

Run local fake/default benchmark from the frontend **Prompt Lab** page, or use:

```powershell
cd backend
python -m app.tools.prompt_lab benchmark-provider --provider fake
```

Real provider benchmarks are not default. They require explicit
`--allow-real-provider` / `allow_real_provider=true` and should be used only
with safe, redacted eval cases.

API:

```text
POST /prompt-lab/providers/benchmark
GET  /prompt-lab/providers/benchmark/{run_id}
```

### Prompt A/B Test

Use the Prompt Lab A/B panel to select two profiles and a use case
(`narrator`, `RP_dialogue`, `intent_parser`, or `memory_summary`), then run the
local fake-provider comparison.

API:

```text
POST /prompt-lab/prompt-profiles/ab-test
GET  /prompt-lab/prompt-profiles/ab-test/{run_id}
```

Prompt Profiles can change style and variants only. They cannot enable hidden
facts or state modification.

### Narrator Style Lab

Use **Narrator Style Lab** to compare prompt profile, genre tone, sensory focus,
response length, prose density, perspective, and scene mood effects. Checks
include hidden leak, invented key item, contradiction with `ActionResult`,
style match, and suggested action validity.

```text
POST /prompt-lab/narrator-style/run
GET  /prompt-lab/narrator-style/{run_id}
```

Style experiments do not write output into active play.

### NPC Voice Style Lab

Use **NPC Voice Style Lab** to compare an NPC id, RP prompt profile, voice
profile variant, catchphrases, and example dialogue. The report checks voice
consistency, unknown fact mentions, hidden leaks, relationship invention, and
quest completion invention.

```text
POST /prompt-lab/npc-voice-style/run
GET  /prompt-lab/npc-voice-style/{run_id}
```

Example dialogue remains style-only and does not add NPC knowledge.

### Structured Output Reliability Test

Run structured JSON checks with fake provider by default:

```powershell
cd backend
python -m app.tools.prompt_lab structured-output --provider fake --schema PlayerIntent
```

API:

```text
POST /prompt-lab/structured-output/run
```

Reports include valid JSON rate, schema valid rate, retry success rate,
invalid field rate, refusal/empty rate, and hidden-policy violation rate. They
do not modify `GameState`.

### Cost / Latency Tracker

Enable local usage tracking when you want safe metadata:

```powershell
$env:ENABLE_USAGE_TRACKING="true"
```

Usage records contain provider/model/use case, duration, estimated tokens,
estimated cost, success/failure, and error type. They do not store raw prompts,
API keys, hidden fact text, raw `GameState`, or raw `state_deltas`.

APIs:

```text
GET /prompt-lab/usage/summary
GET /prompt-lab/usage/recent
GET /prompt-lab/usage/by-use-case
```

### Context Builder Inspector

Use the **Context Builder Inspector** panel to inspect context composition,
token estimates, visibility partitions, and exclusion reasons.

```text
POST /prompt-lab/context/inspect
```

Context sections are classified as normal, narrator-safe, NPC-known,
debug-only, or hidden-redacted. Raw prompt output is off by default and remains
redacted when explicitly enabled for local debug.

### Prompt Diff Tool

Use **Prompt Diff** to compare prompt profiles, RP prompt profiles, context
snapshots, or prompt templates.

```text
POST /prompt-lab/prompt-diff/review
```

If `hidden_fact_policy` or `state_modification_policy` is relaxed, the report
marks a blocker. Hidden text and API keys are redacted.

### Model Compatibility Matrix

Load the matrix from the Prompt Lab page or call:

```text
GET  /prompt-lab/model-compatibility
POST /prompt-lab/model-compatibility/recompute
```

The matrix combines declared capabilities, benchmark reports, structured
output reliability, usage summaries, and hidden leak findings. It is advisory
and does not automatically switch providers or models.

CLI:

```powershell
cd backend
python -m app.tools.prompt_lab compatibility-matrix
```

### Provider Routing

Use the Routing Rule Editor in Prompt Lab to choose provider/model/fallback per
use case. Rules can require JSON support or local-only models.

```text
GET  /prompt-lab/provider-routing
POST /prompt-lab/provider-routing/validate
POST /prompt-lab/provider-routing/preview
POST /prompt-lab/provider-routing/save
```

Routing rules contain provider/model ids and constraints only. They do not
store API keys and do not bypass `LLMProvider`.

### Prompt Regression

Run local prompt regression with fake providers:

```powershell
cd backend
python -m app.tools.prompt_lab prompt-regression
```

API:

```text
POST /prompt-lab/regression/run
```

Regression covers intent parser schema, narrator consistency, RP dialogue
boundary, NPC voice consistency, memory summary schema, hidden leak cases, and
structured JSON reliability. Pass/fail is deterministic; an LLM does not judge
the result.

### Local Model Diagnostics

Run local stub diagnostics:

```powershell
cd backend
python -m app.tools.prompt_lab local-diagnostics --provider local_stub
```

For a real local HTTP endpoint, pass `--allow-real-local-check` explicitly.
Diagnostics use safe smoke prompts and do not send world facts.

API:

```text
POST /prompt-lab/local-model/diagnose
```

### Token Budget

Load or estimate token budgets in the Prompt Lab page, or run:

```powershell
cd backend
python -m app.tools.prompt_lab token-budget-report --profile narrator_balanced
```

APIs:

```text
GET  /prompt-lab/token-budget/profiles
POST /prompt-lab/token-budget/estimate
```

Token budgets protect safety constraints, trim low-priority context, and drop
hidden-redacted sections rather than adding hidden facts.

### Model Usage Dashboard

The Prompt Lab page shows calls by provider/use case, latency p50/p95,
estimated token usage, estimated cost, error rate, and recent failures. It does
not display prompt text or API keys.

### Prompt Experiment Package

Prompt experiment packages bundle Prompt Profiles, RP prompt profiles, test
cases, benchmark configs, regression configs, provider requirements, and a
redaction policy for local reproduction.

```text
POST /prompt-lab/experiment-packages/export
POST /prompt-lab/experiment-packages/import-dry-run
POST /prompt-lab/experiment-packages/import-apply
```

Packages reject API keys, raw env, hidden fact text, raw `GameState`, raw
`state_delta`, sensitive prompt snapshots, executables, and path traversal.
Import validates first and does not auto-enable profiles.

## v1.6 Advanced Gameplay Modules

v1.6 gameplay modules are local, declarative, and rule-driven. They extend the
engine through `ActionRegistry`, structured `ActionResult`, `StateDelta`, and
`EventLog`. They do not execute arbitrary code, call the LLM as a referee, or
modify active `GameState` directly.

### Action Mod Editor

Enable local authoring APIs on a trusted machine:

```env
ENABLE_AUTHORING_API=true
```

Open the local Studio frontend and use the Action Mod Editor to create or edit
declarative actions. The editor supports action id, label, aliases, category,
target specs, affordance requirements, time cost, preconditions, checks,
outcomes, StateDelta templates, event type, and visibility policy.

Validation/export APIs:

```text
POST /authoring/action-mods/preview
POST /authoring/action-mods/validate
POST /authoring/action-mods/export
```

The editor is not a code editor. It cannot enable `execute_code`, access
network resources, read `.env`, or write active saves.

### Import Gameplay Module

Gameplay module packages are local zip/base64 packages with a package
manifest, module manifest, declarative actions, rule configs, quality tests,
docs, example content, and checksums.

API:

```text
POST /modules/import-dry-run
POST /modules/import-apply
POST /modules/export
```

CLI:

```powershell
cd backend
python -m app.tools.module_package import-dry-run --archive ..\module_package.b64
python -m app.tools.module_package import-apply --archive ..\module_package.b64 --confirm-apply
python -m app.tools.module_package export --module-id sample_magic --output ..\sample_magic.b64
```

Import dry-run writes nothing. Apply requires explicit confirmation and a
passing validation/quality path. Package import rejects zip slip, executable
files, unsafe permissions, `.env`, API keys, databases, logs, caches, and
checksum mismatches.

### Module Quality Gate

Run the quality gate before exporting or enabling a module:

```powershell
cd backend
python -m app.tools.module_quality_gate --module-id sample_magic
```

API:

```text
POST /quality/modules/{module_id}/gate/run
```

The gate checks manifest validity, safe permissions, action validation,
state-schema extensions, save compatibility, hidden leak risk, regression
metadata, forbidden paths, and executable-code rejection. It is advisory/gating
tooling; it does not auto-fix or modify active saves.

### Debug Module Action

Enable debug APIs only for local trusted debugging:

```env
ENABLE_DEBUG_API=true
```

Debug APIs:

```text
GET  /debug/modules
GET  /debug/modules/{module_id}
POST /debug/modules/{module_id}/actions/{action_id}/dry-run
```

Dry-run returns precondition results, check results, selected outcome,
StateDelta preview, Event preview, and visibility summary. It does not apply
deltas, append events, or send debug data to narrator/player APIs.

### Gameplay Module Families

Current v1.6 modules are lightweight rule systems:

- Magic: `cast_spell`, mana/focus, spell targets, effects, failure effects,
  visibility policy, and crime policy.
- Hacking: terminals, security doors, cameras, logs, traces, alarms, and
  cyber-crime consequences.
- Crafting: recipes, materials, tools, stations, time cost, repair, and
  dismantle.
- Investigation / Deduction: evidence, testimony, hypotheses, accusations,
  contradictions, and rule-driven conclusions.
- Travel / Survival: travel routes, fatigue, hunger, thirst, exposure, camps,
  forage, food, water, and weather effects.
- Stealth: hiding, shadowing, distraction, noise, decoys, cover, light, and
  detection checks.
- Combat: weapon tags, combat stance, bleeding/stunned/guarded status,
  non-lethal attack, flee risk, and public assault consequences.
- Social Manipulation: persuade, threaten, bribe, deceive, provoke, comfort,
  blackmail, and extract-information, bounded by NPC knowledge.
- Faction Missions: reputation-gated missions, accept/complete/fail,
  rewards, consequences, and quest integration.
- Domain / Base Management: claim base, facilities, staff, storage, upgrades,
  income, upkeep, and bounded risk events.

These systems are intentionally lightweight. They do not implement arbitrary
scripts, tactical-grid combat, real network simulation, complex industry, a
full city/base sim, or LLM-decided outcomes.

### Module Regression Playtests

Module regression playtests run deterministic scenarios for action success,
action failure, invalid targets, hidden targets, save/load, replay, and quality
gate coverage. They use temporary state and mock/fake/local defaults.

Representative tests are included in:

```text
backend/tests/test_gameplay_module_regression.py
backend/tests/test_v16_gameplay_modules_integration.py
```

Run all tests with:

```powershell
python -m pytest
```

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
- v1.4 content production generates drafts, candidates, packages, and reports
  only; it does not directly edit active `GameState`.
- Batch import/export/build tools do not execute scripts, download remote
  content, or automatically overwrite worlds.
- Production generators do not guarantee literary quality and do not call real
  LLMs by default.
- v1.5 Prompt Lab is a local diagnostics/evaluation surface. It does not
  change world facts, active saves, active sessions, or content packs.
- Prompt Lab benchmarks, A/B tests, style labs, structured-output tests, and
  regressions use fake/mock/local defaults. Real provider calls require
  explicit opt-in.
- Prompt Lab reports and packages must not contain API keys, raw prompts,
  hidden fact text, raw `GameState`, or raw `state_deltas`.
- Model Compatibility Matrix and Provider Routing are advisory/configuration
  surfaces; they do not automatically switch production providers or expand
  LLM authority.
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
