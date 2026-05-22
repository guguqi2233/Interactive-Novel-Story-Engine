# Project Overview

This repository is a local-first AI narrative creation, roleplay, and open-world
play platform. As of v2.0, it has moved from a local interactive-novel prototype
into a local modular narrative RPG platform.

The project direction includes:

1. World Engine: authoritative world state, rules, visibility, saves, migration,
   EventLog, and deterministic gameplay.
2. Narrative / Novel: prose drafting, chapter-like summaries, and narrative
   rendering based on confirmed structured facts.
3. Roleplay / Tavern: character cards, RP profiles, voices, dialogue, group RP,
   emotional tone, and scene mood.
4. Script / Mod Platform: world packs, script packages, templates, prompt
   profiles, gameplay modules, action mods, and v2.0 plugin/package manifests.
5. Provider Gateway: OpenAI, OpenAI-compatible APIs, local models, mock providers,
   and relay-style provider configurations behind a safe routing boundary.
6. Authoring Studio: visual map, quest, NPC, faction, relationship, item,
   economy, rumor, crime, template, package, and validation tools.
7. Quality Gate: deterministic tests, playtesting, hidden-leak checks, migration
   checks, performance budgets, compatibility gates, and release checklists.
8. Desktop / Local Studio: local launcher, project/workspace tools, logs,
   crash reports, health checks, backup/restore, and offline help/update notes.

AI Narrative Studio is a local-first three-mode platform for writing novels,
Tavern-style roleplay, and interactive open-world play. After v2.8, the
near-term direction is local UI / UX improvement, not online architecture.

Near-term roadmap:

- v2.9 Local UI / UX Foundation.
- v3.0 Local Desktop Studio Polish.
- v3.1 Novel Studio UI Pro.
- v3.2 Tavern Studio UI Pro.
- v3.3 World Studio UI Pro.
- v3.4 Authoring / Mod UI Pro.
- v3.5 Local QA / Debug / Replay UI Pro.
- v3.6 Local Performance & Accessibility Polish.

Explicitly deferred from v2.9-v3.6 primary scope:

- account system;
- cloud sync;
- online marketplace;
- online package registry;
- remote package auto-download;
- online narrative platform;
- API resale service;
- online mature content platform;
- multi-user collaboration;
- real-time online publishing.

These may remain long-term optional directions, but they must not be treated as
near-term goals or described as implemented unless a future version explicitly
requests, implements, tests, documents, and audits them.

This is local-first software. LLMs are provided by API or local providers, but
the world state, rules, EventLog, save/load, migration, visibility, NPC knowledge,
import/export, package validation, and quality gates are local engine
responsibilities.

API keys may only be read through environment variables or local safe
configuration. Real API keys must never enter frontend code, logs, crash reports,
exports, backups, mods, tests, fixtures, package manifests, prompt profiles, or
documentation examples.

# Local-First Rules

1. All core features must be runnable locally.
2. API keys may only be read through environment variables or a local secret
   resolver.
3. API keys must never enter frontend code.
4. API keys must never enter project exports.
5. API keys must never enter logs, diagnostics, crash reports, quality reports,
   backups, mods, package manifests, prompt profiles, or documentation examples.
6. Project data is not uploaded by default.
7. The app does not make network calls by default except to user-configured LLM
   providers.
8. Mature/private content is not exported or synchronized by default.
9. Local package management takes priority over online marketplaces.
10. UI code may call local backend APIs, but it must not directly read or write
    arbitrary files.

# Core Architecture Principles

1. The LLM is the language layer, not the world judge.
2. The World Engine is the authoritative source of facts.
3. `GameState` must not be directly modified by LLM output.
4. All world state changes must go through `StateDelta`.
5. Player actions, system ticks, NPC planning, module actions, and migration
   events must be recorded as `Event` entries when they affect runtime state.
6. `EventLog` must support replay, debug, save/load, migration, quality analysis,
   and timeline inspection.
7. Important facts must be structured data; they cannot exist only in natural
   language narration.
8. NPCs may only know facts in `npc_knowledge` or equivalent structured known
   facts.
9. Players may only see `visible_state`, `player_visible_facts`, and safe public
   summaries.
10. Hidden facts, NPC secrets, hidden witnesses, debug memory, raw prompts, and
    raw `state_deltas` must not enter player APIs or narrator prompts.
11. Prompts cannot replace code rules.
12. Memory summaries are not an authoritative fact source and cannot override
    `GameState` or `EventLog`.
13. Provider choice can change wording, latency, cost, or formatting; it cannot
    change world authority.
14. Mods and plugins may extend content, actions, style, templates, packages, and
    authoring metadata, but cannot bypass `StateDelta`, `EventLog`, visibility
    checks, compatibility checks, or quality gates.
15. Performance optimizations must never bypass correctness, visibility,
    migration safety, or package security.

# Version Milestones v0.1-v2.0

This section summarizes the documented architecture evolution. When a document
is missing for a sub-detail, treat the capability as unconfirmed rather than
inventing proof.

## v0.1 Minimal Playable Prototype

Documented in `docs/V0_1_ACCEPTANCE_REPORT.md`.

- FastAPI backend loop with `GET /health`, `POST /game/start`,
  `POST /game/input`, and `GET /game/state/{session_id}`.
- Structured `GameState`, `StateDelta`, and `EventLog`.
- Main loop: input -> intent -> action -> result -> `StateDelta` -> narrative
  -> `Event`.
- Initial actions: `observe`, `move`, `talk`, `use_item`, and `wait`.
- `LLMProvider` abstraction and fake/mock provider tests.
- SQLite save repository.
- WorldLoader and content pack loading.
- Initial visibility and NPC-knowledge boundaries.
- Memory summary is non-authoritative.
- React/Vite frontend prototype.
- Documented verification: `73 passed`; frontend build succeeded.

## v0.2 World Consistency & Persistence

Documented in `docs/V0_2_ACCEPTANCE_REPORT.md`.

- Unified `state_deltas`.
- `facts.yaml` loading.
- Multi-world start by `world_id`.
- SQLite save/load API.
- Structured typed `visible_state`.
- Provider factory.
- Frontend world selector and save/load controls.
- Documented verification includes `88 passed` and a later `92 passed`;
  frontend build succeeded.

## v0.3 NPC Behavior & Advanced Actions

Documented in `docs/V0_3_ACCEPTANCE_REPORT.md`.

- NPC schedule resolver.
- Search, inventory rules, lockpick, sneak, quest state machine, and world tick.
- Debug timeline.
- Deterministic serialization fixes for sets and dicts containing sets to avoid
  flaky snapshots.
- Frontend debug timeline support.
- Documented verification: `157 passed`; frontend build succeeded.

## v0.4 Social Consequences & Conflict Systems

Documented in `docs/V0_4_ACCEPTANCE_REPORT.md`.

- Social schema, faction reputation, rumor propagation, crime/witness system,
  social tick, combat core, life state, NPC reactions, advanced memory retrieval,
  and content validation.
- Frontend social/debug panels.
- Documented verification: `257 passed`; frontend build succeeded.

## v0.5 Authoring Tools, Advanced NPCs & Local Memory

Documented in `docs/V0_5_ACCEPTANCE_REPORT.md`.

- Authoring API and frontend authoring mode.
- Validation UX and content validation flow.
- Memory backend and safe `MemoryContextBuilder`.
- NPC goals/planning, relationship graph, faction conflict, economy/trade,
  procedural side quest drafts, automated evals, mod packaging, and multi-world
  save browser.
- Documented verification: `360 passed`; frontend production build succeeded.

## v0.6 Local Studio Hardening

Documented in `docs/V0_6_ACCEPTANCE_REPORT.md`.

- Save migration system with list/status/dry-run/apply paths.
- Authoring diff, preview, and dry-run.
- Player-safe/debug relationship and faction graph APIs.
- Automated playtesting agents, narrative quality evals, performance
  instrumentation, advanced mod version checks, desktop packaging prototype,
  local model provider support slice, and advanced combat slice.
- Documented verification: `454 passed`; frontend build succeeded.

## v0.7 Polished Local Studio

Documented in `docs/V0_7_ACCEPTANCE_REPORT.md`.

- Studio Home, Save Migration UI, Mod Manager UI, Narrative Quality Dashboard,
  Performance Dashboard, Local Model Provider integration, Scenario Template
  System, Quest Graph Editor, Playtesting Dashboard, Import/Export, and
  Settings/Privacy Panel.
- Documented verification: final full backend suite `502 passed`; frontend
  build is documented as passed.

## v0.8 Visual World Authoring

Documented in `docs/V0_8_ACCEPTANCE_REPORT.md`.

- Visual Map Editor, Quest Graph Editor, NPC Goal Editor, faction/relationship
  editor, item/economy editor, rumor/crime consequence editor, visual validation
  graph, timeline replay visualizer, world branch/diff, scenario regression UI,
  local template browser, prompt profile manager, advanced import/export, and
  desktop shell polish.
- Documented verification: `596 passed`; frontend build succeeded.

## v0.9 Quality & Automated Playtesting

Documented in `docs/V0_9_ACCEPTANCE_REPORT.md`.

- `WorldQualityReport`, expanded automated playtesting, scenario regression,
  hidden information leak regression, quest completion analysis, dead-end and
  unreachable detection, NPC behavior coverage, schedule conflict detection,
  economy/combat/social sanity checks, save/load/migration stress tests,
  performance benchmark, narrative consistency evals, world health score,
  content coverage, branch diff regression, mod compatibility stress, batch
  playtesting, and Quality Gate CLI/API.
- Documented verification: `728 passed`; frontend build succeeded.

## v1.0 Stable Local Studio Edition

Documented in `docs/V1_0_ACCEPTANCE_REPORT.md`.

- v1.0 is the first stable local studio edition.
- It stabilizes core local APIs, schemas, content workflow, save migration,
  quality gate, sample world/starter workflow, and provider boundaries for
  longer local play, authoring, testing, and migration.
- Documented verification: 763 tests passed; frontend build succeeded.

## v1.1-v1.7 Platform Expansion

Documented in `docs/V1_1_ACCEPTANCE_REPORT.md` through
`docs/V1_7_ACCEPTANCE_REPORT.md`.

- v1.1 Roleplay Immersion Layer: RP boundary, character card import, RP/voice
  profiles, emotional state, relationship tone, dialogue mode, group RP, scene
  mood, lorebook classification, example dialogue, RP memory context, RP prompt
  profiles, consistency checks, Tavern compatibility import/export, RP evals,
  and RP regression playtests. Documented verification: 890 tests.
- v1.2 Visual Authoring Pro: authoring boundary, visual map and quest graph
  editors, relationship/faction/rumor/crime/item/economy editors, RP character
  authoring, dialogue scene editor, group RP scene authoring, character pack
  builder, template wizard, branch merge assistant, content diff review,
  workflow presets, local content library, reference picker, draft history, and
  authoring validation gate. Documented verification: 998 tests.
- v1.3 Advanced NPC Simulation: NPC simulation boundary, intent queue,
  short-term plans, memory-based reactions, relationship-driven behavior,
  faction duties, rumor decisions, fear/trust/loyalty, conflict avoidance, daily
  replanning, simulation tick orchestrator, debugger, behavior timeline,
  presets, quality evals, and regression playtests. Documented verification:
  `1114 passed`.
- v1.4 Content Production Pipeline: production boundary, world/NPC/quest pack
  generators, location/faction/mystery templates, batch validator, coverage
  planner, import/export profiles, local content library pro, batch character
  card import, lorebook classification, script package builder, campaign starter
  kit builder, production dashboard/CLI, and batch quality gate. Documented
  verification: `1239 passed`.
- v1.5 Local Model & Prompt Lab: provider capability registry, provider
  benchmark, Prompt A/B, narrator/NPC voice style labs, structured output
  reliability, cost/latency tracker, context inspector, prompt diff, model
  compatibility matrix, provider routing rules, prompt regression, local model
  diagnostics, token budget manager, usage dashboard, prompt experiment package,
  frontend, and CLI. Documented verification: `1341 passed`.
- v1.6 Advanced Gameplay Modules: gameplay module boundary, manifest, safe
  loader, declarative Action Mod system, ActionRegistry extension, action DSL,
  validation/authoring UI, magic/hacking/crafting/investigation/travel/stealth/
  combat/social/faction/domain modules, module quality gate, regression
  playtests, debugger, and import/export. Documented verification: `1503
  passed`.
- v1.7 Polished Desktop Studio: desktop boundary, launcher scripts, project
  selector, recent projects, local config manager, log viewer, error recovery,
  backup/restore, one-click quality gate, one-click world export, offline help,
  local update notes, desktop health check, workspace templates, crash report
  viewer, settings UI, startup diagnostics, and packaging safety pass.
  Documented verification: `1551 passed`; frontend build succeeded.

## v1.8-v2.0 Modular Platform Transition

Documented in `docs/V1_8_ACCEPTANCE_REPORT.md`,
`docs/V1_9_ACCEPTANCE_REPORT.md`, `docs/V2_0_ACCEPTANCE_REPORT.md`, and v2.0
contract/release notes.

- v1.8 Stable Contracts & Compatibility: compatibility boundary, stable
  `GameState`/`StateDelta`/`EventLog`, content pack contract, save migration
  contract, module/action/prompt/provider/package contracts, authoring/debug/
  quality contracts, compatibility matrix, compatibility test suite, migration
  failure recovery, deprecated field policy, backward compatibility shims,
  contract docs generator, and v2.0 compatibility checklist. Documented
  verification: `1558 passed`; frontend build succeeded.
- v1.9 Release Candidate Hardening: release candidate boundary, full quality
  gate hardening, long-run playtest, save/load/migration stress, module
  compatibility stress, prompt regression hardening, hidden leak regression,
  performance budget, sample world/starter templates polish, desktop startup
  polish, error recovery polish, documentation finalization, release checklist
  automation, final security audit, and v2.0 RC checklist. The acceptance
  report lists required commands but does not record a test count in the current
  document.
- v2.0 Modular Narrative RPG Platform: platform boundary, Stable Plugin API,
  Stable Module API, Content Pack Schema v2, Save Migration Contract v2,
  Authoring Extension API, Provider Gateway v2, Package Contract v2, Local
  Module Browser, Local Script Package Browser, Multi-Campaign, Cross-World
  Character Transfer, Advanced Timeline Branching, Long Campaign Management,
  Workspace-level Project System, v2 compatibility tests, v2 release checklist
  automation, v2 audits, acceptance report, and release notes. The acceptance
  report lists required commands but does not record a test count in the current
  document.

# Repository Structure

- `backend/app/core`: `GameState`, `StateDelta`, `EventLog`, game loop, replay,
  visibility, and core state contracts.
- `backend/app/engine`: action parsing/resolution, rules, world simulation,
  content loading, validation, gameplay modules, and deterministic systems.
- `backend/app/llm`: provider abstractions, intent parsing, narration, memory
  summarization, Prompt Lab, provider routing, and local/mock provider support.
- `backend/app/db`: database models, session handling, repositories, save/load,
  and migration persistence.
- `backend/app/platform`: v2.0 plugin/module/package/content/save/provider/
  authoring/campaign/timeline/workspace platform services.
- `backend/app/tools`: CLI tools for validation, migration, quality gates,
  playtesting, compatibility, release checks, diagnostics, and package flows.
- `backend/tests`: pytest suite, including compatibility and v2 platform tests.
- `frontend`: local React/Vite Studio frontend.
- `worlds`: local world packs. Current documented sample: `mist_valley`.
- `templates`: local starter templates and RP templates.
- `scripts`: local launcher, diagnostics, and helper scripts.
- `docs`: specs, boundary docs, contract docs, audits, acceptance reports, and
  release notes.
- `logs`, `backups`, and `crash-reports`: local-only runtime directories that
  must remain ignored by git.

# Required Commands

Run commands from the repository root unless a command explicitly changes
directory.

Backend tests:

```powershell
python -m pytest
```

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

World validation:

```powershell
$env:PYTHONPATH='backend'
python -m app.tools.validate_world mist_valley
```

Quality gate:

```powershell
python -m backend.app.tools.quality_gate --world mist_valley
```

Deterministic playtest:

```powershell
$env:PYTHONPATH='backend'
python -m app.tools.playtest --world mist_valley --steps 100 --seed 123
```

Compatibility and contract tools:

```powershell
$env:PYTHONPATH='backend'
python -m app.tools.compatibility_matrix --json
python -m app.tools.generate_contract_docs --check
python -m backend.app.tools.v2_compatibility_checklist --json
python -m backend.app.tools.v2_release_candidate_checklist --json
python -m backend.app.tools.v2_release_checklist --json
```

Desktop startup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_local_studio.ps1
```

Only add new commands here after verifying that the module exists and the
documented invocation works.

# Coding Standards

1. Python code must use type annotations.
2. Pydantic, SQLModel, or the current project schema pattern must be explicit.
3. All LLM JSON output must be validated against a schema before use.
4. Tests must not call real external APIs by default.
5. Never hardcode API keys.
6. Never delete or weaken existing tests merely to make the suite pass.
7. Never bypass `StateDelta` to mutate `GameState`.
8. Never allow LLM output to directly enter `GameState`.
9. New core modules require focused pytest coverage.
10. New frontend functionality must pass `npm.cmd run build`.
11. New content packs, mods, templates, and packages must go through validation.
12. New save schema fields require migration and compatibility consideration.
13. New providers must go through provider factory/router abstractions.
14. New actions must go through `ActionRegistry`.
15. New mods, modules, plugins, and rule modules must declare permissions,
    contract versions, and compatibility metadata.
16. New import/export/backup paths must reject zip slip, path traversal,
    executable payloads, secrets, databases, logs, caches, and build artifacts
    unless a future explicit safe policy says otherwise.

# UI Development Rules

1. UI improvements must not change World Engine fact authority.
2. UI code must not directly modify `GameState`.
3. All world-changing UI actions must go through backend APIs, `StateDelta`, and
   `EventLog`.
4. Normal UI views must not display hidden facts, NPC secrets, debug memory, raw
   prompts, raw `state_deltas`, provider secrets, or API keys.
5. Debug views must be explicitly gated by `ENABLE_DEBUG_API`.
6. Provider UI must not display API keys.
7. Export UI must filter secrets and mature/private content by default.
8. New UI pages must handle loading, empty, error, and disabled states.
9. Frontend changes must pass `cd frontend && npm.cmd run build`.
10. Do not introduce large UI dependencies unless there is a clear, documented
    reason and the existing UI patterns cannot reasonably solve the problem.

# LLM Boundary Rules

- `IntentParser` only parses player intent.
- `Narrator` only renders confirmed rule results and visible facts.
- `MemorySummarizer` summarizes; it does not create authoritative facts.
- RP layers can change emotion, tone, voice, and format; they cannot change
  fact authority.
- Novel mode may draft prose, outlines, chapters, and summaries; anything that
  enters World mode must be structured and validated.
- Tavern mode may roleplay characters, but world-changing consequences must
  become proposals and be validated by the World Engine.
- Provider Gateway, local provider support, relay APIs, and model routing cannot
  expand LLM authority.
- Local models have the same boundary as remote models: they cannot directly
  write `GameState`.
- Prompt/profile/module/provider/package compatibility checks must not use an
  LLM as a judge for pass/fail.

# Visibility and Secrecy Rules

1. Hidden facts must not enter `visible_state`.
2. NPC secrets must not enter player APIs.
3. Hidden witnesses must not enter player narrative unless revealed by local
   rules.
4. Debug memory must not enter narrator prompts.
5. Raw `state_deltas` must not enter player APIs.
6. Debug APIs must be gated by `ENABLE_DEBUG_API`.
7. Authoring, debug, quality, prompt-lab, desktop, and production reports must
   separate normal safe views from debug views.
8. Safe exports, backups, packages, crash reports, logs, and normal quality
   reports must redact hidden text and secrets.
9. Mature/adult content, if introduced, must be optional, disabled by default,
   limited to adult characters and consensual contexts, clearly categorized,
   and isolated in exports/packages. It must not weaken visibility, consent,
   or safety boundaries.

# Mod / Extension Rules

1. Mods, plugins, and authoring extensions do not execute arbitrary code by
   default.
2. Content mods may add structured content.
3. Patch mods must declare target, path, operation, compatibility, and
   migration implications.
4. Narrative style mods only change expression style, not facts.
5. RP Profile mods only change character presentation and cannot bypass
   knowledge or visibility.
6. Action Mods must go through `ActionRegistry`.
7. Action Mods may produce `ActionResult` plus `StateDelta` proposals; local
   engine validation decides what is applied.
8. Rule modules must declare permissions, lifecycle, compatibility, and quality
   tests.
9. Provider profiles must never contain real API keys.
10. Mods, modules, plugins, packages, prompt profiles, and templates must pass
    validation, compatibility checks, and relevant quality gates.
11. Mods/plugins must not read `.env`, API keys, databases, logs, crash reports,
    backups, or arbitrary user files.
12. If future code plugins are supported, they require an explicit sandbox
    design and must remain disabled until that design exists and is tested.

# Three-Mode Platform Direction

The v2.1+ direction is a three-mode platform: Novel Studio + Tavern Studio +
World Studio, with Script / Mod Platform, Provider Gateway, and Quality Studio
as shared infrastructure.

1. Novel Studio: novels, outlines, chapters, character arcs, foreshadowing,
   continuity notes, and exports.
2. Tavern Studio: character cards, RP profiles, group chats, emotional state,
   relationship tone, and scene mood.
3. World Studio: open-world play, NPCs, quests, maps, combat, economy,
   factions, simulation, and EventLog timeline.
4. Script / Mod Platform: world packs, script packages, character packs, prompt
   profiles, action mods, templates, and plugin/package manifests.
5. Provider Gateway: multiple APIs, multiple models, local models, relay APIs,
   routing rules, safe summaries, and capability metadata.
6. Quality Studio: deterministic tests, hidden leak regression, quality gates,
   compatibility checks, performance budgets, release checklists, and audits.

Cross-mode rules:

- Novel -> World must go through draft and validation.
- Tavern -> World must go through proposal and validation.
- World -> Novel may generate chapter drafts from EventLog, timeline, and
  structured state.
- Character Card -> NPC must go through `CharacterProfile` / NPC schema
  conversion and validation.
- RP sessions cannot directly modify active `GameState`.

# Security and Repo Hygiene

1. Do not track `.env`.
2. Do not track `*.db`, `*.sqlite`, or `*.sqlite3`.
3. Do not track `logs/` or `*.log`.
4. Do not track `__pycache__/` or `.pytest_cache/`.
5. Do not track `node_modules/` or `frontend/dist/`.
6. Do not track desktop build outputs such as `desktop-dist/`, `desktop_build/`,
   or `release/`.
7. Do not track `backups/` or `crash-reports/`.
8. `.env.example` may be committed, but it must contain only empty values or
   obvious placeholders.
9. Test fake keys must be clearly fake, such as `sk-test-...` or documented
   redaction fixtures.
10. Documentation examples must not contain real keys.
11. Import/export packages must not include `.env`, API keys, database
    connection secrets, databases, logs, caches, or local build outputs by
    default.
12. Provider profiles, prompt profiles, mods, templates, plugin manifests, and
    package manifests must not leak secrets.

# Workflows Codex Must Follow

For every development task:

1. Read `AGENTS.md` and the relevant docs before editing.
2. State the likely impact area when the work is non-trivial.
3. Make small, scoped changes.
4. Prefer existing project patterns over new abstractions.
5. Run focused tests for the changed area.
6. Run `python -m pytest` and frontend build when the change is broad, touches
   contracts, affects release readiness, or modifies frontend code.
7. Summarize changed files, tests, remaining risks, and any commands that could
   not be run.

For every release:

1. Run `python -m pytest`.
2. Run `cd frontend && npm.cmd run build`.
3. Run the relevant quality, compatibility, migration, and release checklists.
4. Confirm acceptance report, release notes, and required audits exist.
5. Scan for secrets and tracked artifacts.
6. Check `git status --short`.
7. Confirm there is no high-risk blocker.
8. Only then commit, tag, and push.

# Do Not Do

1. Do not let the LLM act as world judge.
2. Do not put game rules only in prompts.
3. Do not bypass `StateDelta`.
4. Do not let mods/plugins directly write `GameState`.
5. Do not let providers, profiles, prompts, or modules change security
   boundaries.
6. Do not call real APIs in tests.
7. Do not commit real `.env` files, databases, logs, caches, build outputs,
   backups, or crash reports.
8. Do not return hidden/debug/raw state information in player APIs.
9. Do not delete tests to hide a problem.
10. Do not describe online marketplace, cloud sync, accounts, arbitrary-code
    plugins, or multiplayer collaboration as stable unless code, tests, docs,
    and security boundaries actually support them.
11. Do not implement online account, cloud sync, or marketplace features unless
    explicitly requested in a future version.
12. Do not introduce remote package download or remote package execution.
13. Do not add network services beyond user-configured LLM providers unless a
    future version explicitly requests and audits them.
14. Do not present planned online features as implemented.
15. Do not weaken local privacy constraints for UI convenience.

# Documentation Maintenance

When adding or changing a module that affects facts, state, visibility,
migration, packages, providers, authoring, debug APIs, desktop tools, or release
readiness, update the relevant docs:

- `docs/SPEC.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `docs/CONTENT_PACKS.md`
- `docs/COMPATIBILITY_BOUNDARY.md`
- `docs/PLATFORM_BOUNDARY.md`
- the corresponding boundary or contract doc
- release notes, acceptance reports, and audits when preparing a release

Do not invent test counts. If a version document does not record a result, say
that the result is not confirmed in the current document.
