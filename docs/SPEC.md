# Project Specification

## v2.2 Novel Studio MVP

v2.2 upgrades Novel Mode from a safe v2.1 stub into a local drafting MVP inside
`NarrativeProject`. It adds manuscripts, outlines, chapters, scenes, character
arcs, plot threads, foreshadowing, safe World Bible context, novel-scoped
prompt profiles, optional draft generation, Markdown/TXT export, EventLog to
chapter draft import, Novel-to-World draft candidates, and deterministic novel
quality checks.

Novel Mode remains a draft system:

- Novel drafts do not modify `GameState`.
- Novel timeline links do not modify `EventLog`.
- Novel -> World conversion creates `WorldContentDraft` candidates only.
- EventLog -> Novel import reads player-visible or narrator-safe summaries
  only.
- Hidden facts, NPC secrets, private notes, debug memory, raw `state_deltas`,
  API keys, provider secrets, and raw env are excluded from normal Novel
  context, prompt context, export files, and quality reports.

v2.2 does not implement a complete Tavern Studio, online publishing,
collaboration, cloud sync, DOCX/EPUB export, or LLM literary judging.

Novel Studio MVP data contracts:

- `NovelManuscript`: project-local manuscript metadata, linked outlines,
  chapters, characters, World Bible, timeline, and default prompt profile.
- `NovelOutline` / `NovelOutlineNode`: act, volume, chapter, scene, beat, and
  note nodes with stable ordering and reference validation.
- `NovelChapter` / `NovelScene`: draft text, summaries, status, linked
  timeline/character/fact refs, and authoring notes.
- `CharacterArc`, `PlotThread`, and `ForeshadowingItem`: project-local writing
  structures. They can reference shared libraries, but they do not modify World
  NPCs, quests, or facts.
- `WorldContentDraft`: Novel-to-World candidate content. It requires later
  validation before any content-pack write.
- `GeneratedNovelDraft`: optional LLM-assisted draft output. It remains a
  Novel proposal and cannot become authoritative state.

Novel APIs are local authoring/studio endpoints under
`/projects/{project_id}/novel/...`. They are controlled by the same local
authoring boundary as other project authoring tools. They must not return API
keys, raw env, hidden facts, raw `GameState`, raw `state_deltas`, provider
secrets, or debug memory.

Novel-to-World and World-to-Novel flows are intentionally asymmetric:

- `Novel -> World`: creates draft/proposal objects and optional
  `CrossModeLink` references. It does not write content packs, create world
  facts, or touch active saves.
- `World -> Novel`: reads EventLog/Timeline summaries to produce chapter draft
  proposals. Preview writes nothing; apply requires explicit confirmation and
  writes only Novel draft fields.

## v2.1 Unified Narrative Project Layer

v2.1 adds a local `NarrativeProject` layer above the v2.0 modular platform.
The project is a metadata and workspace container for Novel, Tavern, World,
Scripts/Mods, Providers, Quality Reports, and Exports. It does not replace
`GameState`, and it does not become a second fact engine.

Core v2.1 project concepts:

- `NarrativeProject`: project id, name, version, engine/schema version,
  default world, active campaign, project root, mode flags, library refs,
  local settings, safety policy, and migration history.
- Project workspace layout: `project.yaml`, `novel/`, `tavern/`, `world/`,
  `scripts/`, `providers/`, `quality/`, and `exports/`.
- Shared libraries: character profiles, World Bible, timeline, lore/fact
  entries, prompt profiles, provider profiles, and memory records.
- `CrossModeLink`: references between Novel/Tavern/World/Script/Quality
  assets. Links never apply state changes and cannot make hidden targets
  visible.
- Mode Router: safe status routing for `novel`, `tavern`, `world`, `script`,
  `quality`, and `settings`.
- Project validation and project quality gate: local reports that check
  schema, directory layout, forbidden files, provider/prompt safety, broken
  cross-mode links, world validation when configured, and export safety.

Mode boundaries:

- Novel Mode in v2.1 is a stub and draft container. Novel outlines and chapter
  drafts do not modify `GameState` and do not become world facts.
- Tavern Mode in v2.1 is a stub and RP session/proposal container. Tavern
  sessions do not modify `GameState`; relationship/fact changes remain
  proposals until explicitly validated by a later World flow.
- World Mode adapts existing world startup/state APIs into a project context.
  It still uses the World Engine, `GameState`, `StateDelta`, `EventLog`, and
  visibility rules.

Project APIs are local authoring/studio endpoints under `/projects`. They are
not public service APIs. They return safe summaries, validation reports, mode
status, and World Mode visible-state projections. They must not return API
keys, raw env, raw `GameState`, raw `state_deltas`, hidden facts, debug memory,
or provider secrets.

v2.1 does not implement a full Novel Studio, full Tavern Studio, cloud sync,
accounts, online marketplace, arbitrary-code plugins, or online project
publishing.

## v2.0 Modular Narrative RPG Platform

v2.0 formalizes the local studio as a modular narrative RPG platform. The scope
includes stable local Plugin API, Module API, Package Contract v2, Content Pack
Schema v2, Save Migration v2, Authoring Extension API, Provider Gateway v2,
workspace projects, multi-campaign metadata, timeline branches, character
transfer packages, and long-campaign summaries.

v2.0 does not introduce an online marketplace, cloud sync, accounts, multi-user
collaboration, arbitrary-code plugins by default, or LLM world authority. All
state authority remains in GameState, StateDelta, EventLog, and Visibility.

## Goal

Build a local-only LLM interactive fiction world engine. The LLM handles language-facing work: intent parsing, narrative rendering, memory summaries, and optional author-facing draft generation. The deterministic Python world engine owns canonical state, rules, causality, events, visibility, saves, social consequences, combat outcomes, authoring validation, and content-pack loading.

The project is local personal software, not a hosted multiplayer service.

## Core Responsibilities

### LLM Responsibilities

- Parse player natural language into schema-validated `PlayerIntent`.
- Render accepted world outcomes into player-facing prose.
- Summarize recent events into internal memory summaries.
- Optionally generate author-facing side quest drafts through `LLMProvider`.
- Operate only through `LLMProvider`.

### World Engine Responsibilities

- Store canonical `GameState`.
- Evaluate player intent with deterministic rules.
- Produce and apply `StateDelta` objects.
- Record player and system events.
- Persist and load saves through SQLite.
- Enforce visibility boundaries.
- Keep important facts, quests, items, NPC state, social state, combat state, time, memory records, and content-pack definitions in structured data.
- Validate content packs and local mods before loading or saving authoring edits.

## Architecture Boundary

The LLM is a narrator, parser, summarizer, and optional draft assistant. It is not the world judge.

The world engine is authoritative. It decides whether an action succeeds, what changes, what is visible, what is remembered, what gets saved, and what content is loadable.

No LLM output may directly mutate `GameState`.

All canonical changes must go through `StateDelta`.

All handled player actions, system ticks, NPC planning ticks, and system consequences must be recorded as `Event` entries.

Authoring APIs edit content-pack YAML, not active `GameState`. Procedural
quest generation and v1.4 content production generate drafts, candidates,
packages, previews, and reports only. v1.5 Prompt Lab generates diagnostics,
benchmark reports, prompt diffs, usage summaries, context snapshots,
compatibility matrices, and prompt experiment packages only. v1.6 gameplay
modules add rule-driven actions and optional state fields through
`ActionRegistry`, declarative definitions, validation, and module packages;
they still cannot bypass `StateDelta`, `EventLog`, Visibility, NPC Knowledge,
or the LLM boundary. v1.7 desktop studio tools add local launcher,
workspace/config/health/crash/update-note convenience around the backend API;
they do not become a second engine, secret store, or direct state editor.

## Current v1.0 Gameplay Loop

1. Player submits text through API or frontend.
2. `IntentParser` returns schema-validated `PlayerIntent`.
3. `ActionDispatcher` selects an action handler.
4. The action handler resolves deterministic `ActionResult`.
5. Action deltas are applied with `apply_delta`.
6. Quest triggers caused by the action are resolved.
7. Turn advances for successful/partial actions.
8. World tick runs schedule, quest triggers, social consequences, NPC reactions, NPC planning, suspicion decay, delayed consequences, and post-delayed quest triggers.
9. Player event and system events are recorded.
10. Crime/witness consequences can be generated from the player event.
11. Narrator receives visible action facts and returns `NarrativeResult`.
12. API returns narration plus filtered `visible_state`.

## v1.0 Stable Scope

v1.0 is the Stable Local Studio Edition. It freezes the core local contracts
around `GameState`, `StateDelta`, `EventLog`, content packs, mod manifests,
save migration, `LLMProvider`, player APIs, local authoring APIs, debug APIs,
and quality tooling. The goal is long-term local reliability rather than major
new gameplay expansion.

Backend:

- FastAPI API with health, game start/input/state, save/load/delete/list, debug timeline, and local authoring endpoints.
- SQLite save/load for state snapshots, event history, and memory records.
- Multi-world content-pack loading from `worlds/{world_id}`.
- Content-pack validation CLI and structured validation report.
- Local authoring API for whitelisted YAML files.
- Content-only mod manifest discovery and validation.
- Save migration status, dry-run, apply, backup metadata, and CLI.
- Save migration UI in the frontend Save Browser.
- Authoring diff/preview/dry-run and content impact analysis.
- Relationship/faction graph APIs in player-safe and debug scopes.
- Debug performance APIs for local timing samples.
- Studio Home and Settings / Local Privacy safe summary endpoints.
- Narrative eval, playtest, import/export, scenario template, quest graph, and
  mod manager local studio endpoints.
- Visual map, quest graph, NPC goal, social graph, economy, rumor/crime,
  validation graph, timeline replay, world branch/diff, template browser,
  prompt profile, scenario regression, and advanced package endpoints.
- World quality report schemas, quality issue/metric/run metadata, and safe
  normal/debug report separation.
- Expanded automated playtesting scenarios and deterministic batch runner.
- Scenario regression authoring APIs.
- Hidden information leak regression suite.
- Quest completion analysis, dead-end detector, NPC behavior coverage, NPC
  schedule conflict detector, economy balance checks, combat balance checks,
  and faction/rumor/crime consequence coverage.
- Save/load/migration stress tests and import/export save-bundle stress paths.
- Performance benchmark suite.
- Narrative consistency evals.
- World health score and content coverage APIs/dashboards.
- Branch diff regression and mod compatibility stress testing.
- Quality gate CLI/API.
- Multi-world save browser summaries.
- LLM provider factory using `LLM_PROVIDER`.

World engine:

- `GameState`, `StateDelta`, `EventLog`.
- Time system.
- NPC schedule resolver.
- Search action.
- Inventory rule functions.
- Lockpick action.
- Sneak action.
- Quest state machine.
- Faction reputation.
- Rumor propagation.
- Crime and witness system.
- Social consequence tick.
- Combat core: attack, defend, flee.
- Advanced combat slice: guarded/stunned/bleeding, cautious/fleeing stances,
  non-lethal attack, flee risk, and visible combat summary.
- Injury, death, and incapacitation rules.
- NPC reaction rules.
- NPC goals and deterministic NPC planning tick.
- NPC relationship graph.
- Faction conflict layer.
- Economy/trade rules and buy/sell actions.
- Advanced local memory retrieval with in-memory and SQLite stores plus a local-vector-ready fallback interface.
- `MemoryContextBuilder` for safe narrator/player/NPC memory context.
- Procedural side quest draft generation.

Frontend:

- React/Vite local prototype.
- World selection.
- Start/input flow.
- Save/load/delete browser.
- Visible state panels.
- Player-visible social/status panels.
- Local debug timeline and classified debug panels.
- Authoring panel for reading/editing/saving/validating content-pack YAML.
- Lightweight graph panels for player-visible and debug relationship/faction
  graph data.
- Local studio launcher prototype documented for Windows PowerShell.
- Studio Home Dashboard.
- Save Migration UI.
- Mod Manager UI.
- Narrative Quality Dashboard.
- Performance Dashboard.
- Automated Playtesting Dashboard.
- Scenario Template preview UI.
- Visual Map Editor.
- Visual Quest Graph Editor full authoring slice.
- NPC Goal Editor.
- Faction / Relationship Visual Editor.
- Item / Economy Editor.
- Rumor / Crime Consequence Editor.
- Visual Validation Graph.
- Timeline Replay Visualizer.
- World Branch / Diff panels.
- Scenario Regression Suite UI.
- Local Template Browser.
- Prompt Profile Manager.
- Import/export controls for local world, mod, save, template, and scenario
  packages.
- Settings / Local Privacy panel.
- World Health Score Dashboard.
- Content Coverage Dashboard.
- Scenario Regression Authoring panel.
- Quality, playtest batch, benchmark, and regression report surfaces where
  implemented by the local studio UI.

Testing:

- Unit tests for core rules and actions.
- FastAPI tests.
- SQLite save/load tests with temporary databases.
- Boundary eval tests for narrative visibility leaks.
- v0.3, v0.4, v0.5, v0.6, v0.7, v0.8, and v0.9 integration regression tests.
- Migration compatibility fixtures.
- Deterministic playtesting agents and narrative quality evals.
- Hidden information leak evals and narrative consistency evals.
- Deterministic quality gate, benchmark, stress, coverage, and analyzer tests.
- Fake/mock LLM providers in automated tests.

## v1.0 Quality Verification Model

v1.0 keeps local quality verification as an authoring and regression
toolchain. Quality reports can aggregate validation issues, playtest results,
scenario regression output, hidden-leak checks, quest reachability analysis,
dead-end detection, NPC/schedule coverage, economy/combat/social sanity
checks, save/load/migration stress tests, benchmarks, and mod compatibility
smoke tests.

Quality output is advisory. `WorldHealthScore` and dashboard scores are
explainable heuristics, not absolute quality judgments and not canonical game
facts. Quality reports do not mutate `GameState`, write active saves, or
change content packs. The quality gate is a deterministic threshold/severity
gate; LLM output cannot decide pass/fail.

Normal quality, playtest, benchmark, and scenario reports must not contain
hidden fact text, NPC secrets, hidden witnesses, raw `GameState`, raw
`state_deltas`, API keys, raw environment variables, or sensitive local paths.
Debug-only diagnostic details must be explicitly marked and kept on
debug/local-only surfaces.

Current implementation note: the main playtest, eval, benchmark, and quality
gate routes use existing local feature flags such as `ENABLE_PLAYTEST_API`,
`ENABLE_EVAL_API`, `ENABLE_DEBUG_API`, and `ENABLE_PERF_LOGGING`. There is no
separate `ENABLE_QUALITY_API` setting yet, and some analyzer endpoints remain
local-only without an independent quality flag. The backend should remain
bound to localhost for local studio use.

## v1.1 Roleplay Immersion Scope

v1.1 is the Roleplay Immersion Layer. It brings Tavern-style roleplay
convenience into the local studio while preserving the v1.0 fact boundary.

Included scope:

- Roleplay boundary contract and policy objects.
- Character card import preview/validate/apply as authoring candidates.
- Lorebook/world-info import with deterministic classification.
- Tavern-like local import/export for character cards, lorebooks, example
  dialogue, and prompt presets.
- NPC `RPProfile` and `VoiceProfile`.
- NPC `EmotionalState` as structured rule-managed state.
- `RelationshipTone` as an expression layer derived from relationships,
  faction reputation, emotion, and recent events.
- Dialogue Mode for focused continuous NPC conversation.
- Multi-NPC scene / Group RP with participant-specific context.
- Scene mood presets loaded from content packs.
- Example dialogue management for prompt-safe style examples.
- RP memory context builder with hidden/debug filtering.
- RP prompt profile settings that can adjust style but cannot widen authority.
- RP output consistency checker.
- RP scenario templates, RP boundary evals, and RP regression playtests.
- Frontend RP / Dialogue panels for safe dialogue controls and summaries.

RP features are allowed to change expression, voice, mood, pacing, safe memory
selection, and prompt style. They are not allowed to change authoritative
facts, bypass visibility, grant NPCs unknown knowledge, decide quest/combat
outcomes, or write `GameState` from model text.

Principle: expression is flexible; facts are controlled.

## v1.2 Visual Authoring Pro Scope

v1.2 is Visual Authoring Pro. It expands the local studio from individual
authoring panels into a broader visual content workflow while preserving the
same world authority boundary.

Included scope:

- Authoring Pro Boundary Contract and policy checks.
- Shared Authoring Validation Gate for save/import/merge/export/apply flows.
- Visual Map Editor Pro with regions, layers, locked/hidden/conditional edges,
  travel cost, discovery rules, validation, impact, and diff preview.
- Quest Graph Editor Pro with quest/stage/objective/trigger/reward/consequence
  nodes, optional/failure paths, hidden objective fields, and deterministic
  scenario regression draft generation.
- NPC Relationship Graph Editing with trust, fear, affinity, obligation,
  hidden relationships, relationship type, and RP tone preview fields.
- Faction Conflict Editor with faction nodes, alliance/hostility/conflict
  edges, alert levels, visibility fields, and conflict tags.
- Rumor / Crime Consequence Graph Pro with trigger, witness, crime, rumor,
  reputation effect, NPC reaction, quest effect, delay/cooldown, and dedupe
  fields.
- Item / Economy Editor Pro with item nodes, merchants, shop inventory edges,
  price modifier fields, stolen item policy, quest reward links, and balance
  warnings.
- RP Character Authoring UI Pro with character-card import preview,
  RP/voice/profile editing, default emotion, example dialogue management, safe
  export, and hidden/private field checks.
- Dialogue Scene Editor and Group RP Scene Authoring for reusable scene
  templates.
- Character Pack Builder with safe local export, dry-run import, explicit
  apply, validation, path traversal rejection, script rejection, and hidden fact
  exclusion by default.
- Template Wizard for deterministic world/location/quest/NPC/RP/faction/mystery
  template drafts.
- World Branch Merge Assistant and Content Diff Review.
- Authoring Workflow Presets.
- Local Content Library.
- Reference Picker / ReferenceIndex.
- Authoring Undo / Draft History.
- v1.2 integration regression tests and boundary/security audit docs.

v1.2 authoring tools are content-pack editors. Preview and validate do not write
disk. Save writes world-pack or package files only after validation and explicit
save. Restore from draft history returns draft content and still requires
validation before save. None of these tools modifies active `GameState`, active
dialogue sessions, or active saves.

v1.2 does not add LLM authority. Visual editors do not call an LLM to generate
maps, quests, relationships, faction conflict, rumors, crime consequences,
prices, dialogue scene facts, hidden facts, merge resolutions, diff summaries,
or templates. RP authoring does not allow imported prompt text, prompt profiles,
or RP profiles to widen hidden-fact or state-write permissions.

## v1.3 Advanced NPC Simulation Scope

v1.3 adds bounded NPC simulation on top of the existing world engine. The goal
is to make NPCs appear more autonomous while preserving deterministic rule
authority.

Included:

- NPC Simulation Boundary Contract.
- NPC Intent Queue.
- NPC Short-Term Plans.
- NPC Memory-Based Reactions.
- NPC Relationship-Driven Behavior.
- NPC Faction Duties.
- NPC Rumor Decisions.
- NPC Fear / Trust / Loyalty models.
- NPC Conflict Avoidance.
- NPC Daily Goal Replanning.
- NPC Simulation Tick Orchestrator.
- NPC Simulation Debugger and NPC Behavior Timeline.
- NPC Simulation Authoring Presets.
- NPC Simulation Quality Evals.
- NPC Simulation Regression Playtests.

NPC simulation is not a second world authority. It can produce finite
candidate actions, intents, plans, `StateDelta` entries, and `Event` records.
It cannot directly mutate `GameState`, cannot know unknown facts, cannot call
the LLM or external tools, and cannot run unbounded background thinking loops.

NPC behavior outcomes are decided by local rules. The LLM may express selected
behavior or dialogue in safe prose, but it cannot choose actions, create
authoritative plans, decide rumor/faction/social outcomes, or write NPC state.

Debug simulation APIs are local tools behind `ENABLE_DEBUG_API`. Debug traces,
hidden fact ids, intent queues, plans, and behavior timelines must not enter
player APIs or narrator prompts.

## v1.4 Content Production Pipeline Scope

v1.4 adds local content-production tooling on top of the existing world engine,
RP layer, visual authoring, and NPC simulation systems. The goal is to help a
local creator produce, review, validate, package, and export structured content
at a larger batch scale without changing runtime authority.

Included:

- Content Production Boundary Contract and policy checks.
- World Pack Wizard for draft world-pack generation.
- NPC Pack Generator for NPC/RP/voice/relationship/goal/schedule candidates.
- Quest Pack Generator with quest graph and scenario regression candidates.
- Location Cluster Templates for reusable map fragments.
- Mystery Template System for hidden-truth clue structures.
- Faction Template System for faction/relation/duty/quest-hook drafts.
- Content Batch Validator.
- Content Coverage Planner.
- Export / Import Profiles.
- Local Content Library Pro.
- Batch Character Card Import.
- Batch Lorebook Classification.
- Script Package Builder.
- Campaign Starter Kit Builder.
- Production Pipeline Dashboard.
- Content Production CLI.
- Batch Quality Gate.
- v1.4 integration tests and LLM/visibility/security audit docs.

Production drafts are not active runtime state. Preview and validate do not
write disk. Apply/build operations require explicit confirmation and validation
gate approval, and release/package operations use the relevant quality gate.
Production tools write content-pack or package files only after those gates
pass; they do not modify active sessions or active `GameState`.

Generated content is schema-checked structure, not trusted world truth. Hidden
facts, NPC secrets, private RP fields, unsafe imported prompts, and production
debug data must remain out of normal reports, player-visible state, narrator
prompts, and player UI unless revealed through normal rule/visibility flows.

v1.4 does not add LLM authority. Generators default to deterministic local
logic. Reserved `llm_assisted` fields are metadata only in the current
implementation and must remain draft/candidate-only if a future assisted path
is added.

## v1.5 Local Model & Prompt Lab Scope

v1.5 adds local Model & Prompt Lab tooling for comparing and debugging
providers, models, Prompt Profiles, structured output, context building, token
budgets, provider routing metadata, usage metrics, prompt regression, and
prompt experiment packages.

Included:

- Model & Prompt Lab Boundary Contract.
- Provider Capability Registry.
- Provider Benchmark Harness.
- Prompt Profile A/B Test.
- Narrator Style Lab.
- NPC Voice Style Lab.
- Structured Output Reliability Test.
- Cost / Latency Tracker and Model Usage Dashboard.
- Context Builder Inspector.
- Prompt Diff Tool.
- Model Compatibility Matrix.
- Provider Routing Rule Editor.
- Prompt Regression Suite.
- Local Model Diagnostics.
- Token Budget Manager Pro.
- Prompt Experiment Package.
- Prompt Lab Frontend and CLI.

Provider / Prompt Lab boundary:

- All real provider construction remains behind `LLMProvider` /
  `create_llm_provider`.
- `ProviderRouter` may select provider/model ids and fallbacks, but cannot
  store secrets or expand model authority.
- Prompt Profiles may tune style, prompt variants, temperature, output hints,
  and RP expression fields, but cannot enable hidden facts or state writes.
- Benchmarks and prompt regressions default to fake/mock/local providers.
- Real provider benchmarks require explicit `allow_real_provider=true`.
- Local HTTP diagnostics require explicit `allow_real_local_check=true` when
  using a real endpoint.
- Structured output reliability records schema failures and metrics; it does
  not create authoritative state.
- Context snapshots classify normal, narrator-safe, NPC-known, debug-only, and
  hidden-redacted sections.
- Cost/latency usage records store metadata and token estimates only, not raw
  prompts.
- Prompt experiment packages reject API keys, raw env, hidden fact text, raw
  `GameState`, raw `state_delta`, sensitive prompt snapshots, executables, and
  path traversal.

v1.5 does not change the gameplay loop. Prompt Lab reports are advisory local
studio data and are never applied automatically to active saves or worlds.

## v1.6 Advanced Gameplay Modules Scope

v1.6 adds local, validated gameplay modules and declarative Action Mods for
extending the deterministic rule layer. Modules can add actions and optional
state schema extensions, but they do not execute arbitrary code and do not
turn the LLM into a gameplay referee.

Included:

- Gameplay Module Boundary Contract.
- Gameplay Module Manifest and safe manifest-only loader.
- Declarative Action Mod System.
- Action Registry Extension for core and module actions.
- Action DSL Preconditions / Checks / Effects.
- Action Mod Validation.
- Action Mod Authoring UI.
- Magic System.
- Hacking System.
- Crafting System.
- Investigation / Deduction System.
- Travel / Survival System.
- Stealth Expansion.
- Combat Expansion.
- Social Manipulation System.
- Faction Mission System.
- Domain / Base Management.
- Gameplay Module Quality Gate.
- Gameplay Module Regression Playtests.
- Gameplay Module Debugger.
- Gameplay Module Import / Export.

Module / Action Mod safety boundary:

- All gameplay actions resolve through `ActionRegistry` or trusted rule
  handlers.
- Action Mods are declarative YAML/JSON-like data, not code plugins.
- Preconditions, checks, and effects are schema-limited and path-whitelisted.
- Effects compile to `StateDelta` values and are not applied directly by
  module definitions.
- Every consequential module action records an `Event`.
- Module import/export rejects zip slip, executable files, unsafe
  permissions, sensitive files, API keys, logs, databases, and caches.
- Module debug dry-runs are gated by `ENABLE_DEBUG_API` and do not mutate
  state.
- Module quality gate and regression playtests are deterministic and do not
  call real LLM APIs.

Current v1.6 module state areas include magic resources, hackable targets,
hacking tools, network nodes, crafting stations, evidence/testimony/hypothesis
state, survival/travel/weather/camps, stealth/noise/cover, combat stance and
status expansion, social leverage, faction missions, and domain/base
management.

Known v1.6 limitation: declarative fact-discovery effects are powerful and
must remain guarded by action mod validation and hidden-leak tests so a module
cannot expose hidden facts to `player_visible_facts` unless discovery is
explicitly allowed by rules.

## v1.7 Polished Desktop Studio Scope

v1.7 adds a local desktop-studio polish layer around the existing backend and
frontend. The goal is safer local startup, project navigation, configuration
visibility, health diagnostics, update notes, crash report inspection, and
packaging safety without changing world authority.

Included in the current implementation:

- Desktop Studio Boundary Contract.
- Desktop Launcher Pro scripts for PowerShell and shell environments.
- Startup Diagnostics CLI.
- Project Selector and Recent Projects.
- Local Config Manager safe summaries and `.env.example`-style template
  generation.
- Local Update Notes index.
- Desktop Health Check.
- Workspace Templates.
- Crash Report Local Viewer.
- Desktop packaging safety documentation and `.gitignore` hardening.
- Frontend studio panels for the implemented v1.7 local surfaces.
- v1.7 LLM, local data/privacy, and security/packaging audit docs.

Current partial or boundary-only surfaces:

- Log Viewer: policy-level redaction exists, but full runtime log viewer API
  is not complete in the current code.
- Error Recovery Wizard: recovery concepts remain roadmap/boundary level in
  the current code.
- Backup / Restore: desktop boundary and packaging rules define exclusions and
  restore requirements, but full v1.7 backup/restore runtime is not complete.
- One-click Quality Gate and One-click World Export: existing quality/export
  systems remain available, but dedicated v1.7 one-click desktop workflows are
  not complete.
- Offline Help Docs: local docs exist and update notes are indexed, but a full
  searchable offline help index is not complete.

Desktop local-only boundary:

- The desktop shell and launcher must use backend APIs and scripts only.
- The desktop layer must not directly mutate `GameState`, saves, databases,
  world packs, modules, prompt profiles, or content packs.
- Frontend code must not read `.env`, API keys, raw env, provider secrets,
  database passwords, raw prompts, raw logs, raw crash dumps, or hidden facts.
- Config summaries may show safe booleans and labels only.
- Logs and crash reports are local-only and redacted.
- Backups and exports must default to excluding `.env`, API keys, logs,
  caches, database connection config, frontend build outputs, desktop build
  outputs, and executable files.
- Desktop packaging remains a local prototype. v1.7 does not produce a formal
  installer, signed application, automatic updater, cloud sync, account
  system, marketplace, telemetry pipeline, or online docs updater.

## RP And World Engine Boundary

The RP layer is above the world engine. It reads safe context from structured
state and can request rule-mediated actions, but it is not itself the fact
source.

Dialogue and group-scene consequences that affect the world must still follow:

1. deterministic rule decision
2. `StateDelta`
3. `Event`
4. filtered player-visible response

LLM output may be rejected, retried, or replaced with a safe summary by the RP
consistency checker. It cannot be applied as a state patch.

Character card import, lorebook import, Tavern compatibility, example dialogue,
scene mood presets, RP profiles, and prompt profiles are authoring/style data.
They can produce candidates or drafts. They do not directly modify active
session `GameState` and do not become authoritative facts until explicitly
saved as validated content-pack data.

## Persistence Model

SQLite stores:

- `SaveGame` with current `GameState` JSON snapshot.
- `StoredEvent` with full event JSON.
- `StoredMemory` with memory record JSON when explicitly saved.

Event history is suitable for debugging and scoped replay. `StateDelta` values are type-validated when reapplied.

## Visibility Model

Player-visible API responses must be derived from `visible_state`.

`visible_state` includes:

- world id
- turn
- formatted game time
- current location
- inventory
- visible objects
- visible NPC summaries
- known facts
- visible/known quests
- known factions
- known rumors
- known/reported/resolved crimes
- known relationships
- visible faction conflicts

It must not include:

- hidden facts not in `player_visible_facts`
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- hidden witnesses
- debug-only event details
- hidden inactive quests
- hidden factions
- hidden relationships
- hidden/debug memory records
- raw `state_deltas`

Known caveats:

- Current visible faction responses still include raw numeric reputation as well as a band. The frontend displays the band; moving raw reputation to debug-only remains a hardening recommendation.
- Current visible faction conflict responses include `conflict_tags`, which may hint at hidden social structure if authored incautiously.

## Debug Model

Debug timeline endpoints are local-development tools:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They can show raw `state_deltas`, including hidden/system-only information. They are controlled by `ENABLE_DEBUG_API` and must not be treated as player-facing narrative output.

The frontend shows debug data only in the debug panel.

Performance debug endpoints are also controlled by `ENABLE_DEBUG_API`.
Performance recording is controlled by `ENABLE_PERF_LOGGING`, stores samples in
memory, and must not record prompt text, API keys, hidden fact text, raw
`GameState`, or raw `state_deltas`.

## Authoring Model

Authoring endpoints are local-development tools controlled by `ENABLE_AUTHORING_API`.

They can list, read, save, and validate whitelisted YAML files in content packs. They are not player APIs and may show hidden world content to the local author.

Authoring saves YAML files and runs validation. It does not write active session `GameState`.

v0.6 authoring preview/dry-run endpoints parse proposed YAML, validate it in a
temporary draft, calculate diff/impact summaries, and report possible save
migration risk without writing disk or active saves.

v0.7 extended authoring with scenario templates, quest graph preview, mod
manager views, and import/export. v0.8 extends authoring with visual map,
fuller quest graph, NPC goal, faction/relationship, item/economy,
rumor/crime, validation graph, branch/diff, template browser, and advanced
package workflows. These tools are still local-only, gated by
`ENABLE_AUTHORING_API`, and must not write active session `GameState`.
Authoring UI may show hidden world content to the local creator, but that data
must remain isolated from player UI and narrator inputs.

## Local Studio Model

The v0.8 local studio is a collection of trusted-local tools around the world
engine. It includes Studio Home, Save Migration UI, Mod Manager UI, narrative
eval and performance dashboards, playtesting dashboard, settings/privacy
panel, import/export, scenario templates, visual authoring editors, validation
graph, timeline replay, world branch/diff, prompt profiles, and desktop
launcher scripts.

These tools improve convenience but do not change authority:

- They do not make the frontend a source of truth.
- They do not let authoring tools edit active `GameState`.
- They do not let dashboards feed debug data into narration.
- They do not make local model output canonical.
- They do not execute mod or template scripts.

## Import / Export Model

World, mod, and save archives are local zip bundles with a manifest. Import
rejects path traversal, zip slip, executable files, `.env`, local database
files, logs, and secret files. World and mod imports run validation. Save
imports check migration status.

Save archives can contain full save state and event history, including hidden
state by design. They are authoring/backup data, not player-facing output.

v0.8 advanced packages add `local_package_manifest.json`, checksums,
compatibility checks, dry-run, and explicit apply. Supported package types are
world, mod, save bundle, template pack, and scenario suite. Package import
must not execute code, auto-overwrite content, or bypass validation/migration.

v1.2 adds character-pack import/export and local library import/export surfaces.
These remain local authoring flows. They must reject path traversal, executable
files, remote URLs, API keys, secret configuration, and arbitrary code. They do
not automatically write imported character cards, templates, or packages into
the active world without dry-run/validation/explicit apply.

## Save Migration Model

Saves carry engine/schema/world/content metadata and migration history. The
v0.6 migration system can report status, dry-run, and apply migration with a
backup. Migrations are deterministic code, do not call LLMs, must preserve
EventLog, and must not reclassify hidden/debug data as player-visible.

## Correctness Over Convenience And Performance

Performance instrumentation and future optimizations must not bypass
`StateDelta`, `EventLog`, Pydantic/schema validation, content validation,
visibility filtering, provider abstraction, or migration validation. A faster
path that weakens rule correctness or privacy is invalid.

The same principle applies to local studio convenience. A nicer visual editor,
faster import path, easier template flow, branch/diff workflow, prompt profile,
or desktop launcher must not bypass validation, visibility, migration dry-run,
event logging, provider abstraction, or content-only mod restrictions.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for handled player actions, system ticks, NPC planning ticks, or system consequences.
- Do not store API keys in source, docs, fixtures, logs, database rows, or saves.
- Do not write provider-specific model calls inside world engine modules.
- Do not make canonical state changes without `StateDelta`.
- Do not expose hidden facts, NPC secrets, hidden witnesses, hidden NPCs, hidden objects, hidden relationships, or hidden/debug memory through player APIs.
- Do not put game rules only in prompts.
- Do not let combat, crime, rumor, faction, trade, NPC planning, relationship, or quest outcomes be decided by LLM output.
- Do not let authoring or mod packaging execute arbitrary code.
- Do not let procedural side quest generation write active saves or content files without explicit authoring review/export.
- Do not let scenario templates execute scripts or write active saves.
- Do not let quest graph editing bypass `quests.yaml` validation.
- Do not let visual map, NPC goal, social graph, item/economy, rumor/crime, or
  validation graph tools bypass content validation.
- Do not let v1.2 visual editors bypass the Authoring Validation Gate.
- Do not treat an authoring draft, restored draft history snapshot, merge draft,
  diff review, template preview, or character-pack dry run as active
  `GameState`.
- Do not let ReferenceIndex or authoring normal views leak hidden details into
  player UI or ordinary RP/narrator prompts.
- Do not let import/export install archives without path, type, manifest, and
  validation checks.
- Do not let advanced packages skip checksum validation before apply.
- Do not expose provider secrets, raw env, raw `GameState`, or raw
  `state_deltas` through Studio Home, Settings, dashboards, or player APIs.
- Do not let RP profile, voice profile, scene mood, example dialogue, lorebook
  text, or imported Tavern prompts expand LLM authority.
- Do not let Dialogue Mode or Group RP give NPCs hidden facts outside their
  `npc_knowledge`.
- Do not let RP model output directly update emotional state, relationship
  values, quest state, inventory, combat state, or facts.
- Do not treat example dialogue or memory as authoritative world fact.
- Do not execute scripts, links, or remote content from character cards,
  lorebooks, Tavern resources, templates, or mods.

## Not In v1.0

- Hosted service security, auth, accounts, cloud sync, or multiplayer.
- Tactical grid combat or multi-round combat AI.
- Guard pursuit, arrest, trial, or full legal system.
- Dynamic supply/demand economy, crafting, equipment progression, durability, or weight systems.
- Complex drag/drop IDE, multiplayer authoring, or automatic content repair.
- LLM-driven autonomous NPC agents.
- Pathfinding and large-scale world simulation.
- Arbitrary plugin code execution or online mod download.
- Full vector database or embedding pipeline as a hard dependency.
- Automatic content repair.
- Formal desktop installer, code signing, or auto-update.
- External LLM judge for narrative quality.
- Required local model server or mandatory local LLM integration.
- Production APM, telemetry upload, or hosted monitoring.
- Complex mod version SAT solving or online mod download.
- Any performance optimization that bypasses correctness boundaries.
- Online marketplace, upload/download sync, or account-based collaboration.
- Frontend direct filesystem access.
- Authoring UI direct edits to active runtime sessions.
- Arbitrary template or mod script execution.
- A local model provider that can directly write `GameState`.
- Automatic publishing or automatic overwrite of user world packs.
- LLM-generated map/quest/NPC/social/economy/consequence content that bypasses
  explicit preview, validation, and save.
- Automatic world repair from quality reports.
- Treating health scores as definitive creative judgments.
- Writing eval/playtest/quality results into active `GameState` or active
  saves.
- Hosted quality service, telemetry upload, or cloud report storage.

## Not In v1.1

- LLM world judge or LLM-decided rule outcomes.
- LLM direct `GameState` mutation.
- LLM-decided combat, quest completion, trade, crime, or relationship values.
- NPC omniscience or RP prompts containing hidden facts outside visibility and
  NPC knowledge rules.
- Online character/lorebook marketplace.
- Remote URL import for character cards or lorebooks.
- Arbitrary script execution from imported roleplay resources.
- Automatic trust of external `system_prompt` or creator prompt text.
- Full compatibility with every Tavern ecosystem variant.
- Cloud sync, accounts, multiplayer roleplay, or hosted RP service.
- Automatic application of untrusted external content to active worlds or
  active saves.

## Not In v1.2

- LLM world judge or LLM-generated authoritative content for maps, quests,
  relationships, factions, economy, consequences, templates, merge decisions, or
  diffs.
- LLM direct `GameState` mutation.
- Visual editor direct edits to active `GameState`, active dialogue sessions,
  or active saves.
- Visual editor save that bypasses validation or the Authoring Validation Gate.
- Arbitrary code plugins, template scripts, package scripts, or executable
  imported content.
- Online marketplace, cloud sync, accounts, remote publishing, or multiplayer
  collaboration.
- Automatic overwrite of user world packs or active worlds.
- Automatic import of external character cards/templates into active worlds.
- Prompt Profile or RP Profile expansion of LLM authority.
- Editor access to `.env`, API keys, databases, logs, or arbitrary system
  files.
- Complex automatic layout, full Git replacement, full conflict auto-resolution,
  large-scale social/war simulation, or automatic content repair.

## Not In v1.3

- LLM multi-agent free simulation.
- LLM-decided NPC behavior, plans, rumor decisions, social decisions, faction
  duties, fear/trust/loyalty values, or conflict avoidance.
- NPC omniscience or NPC access to hidden facts outside `npc_knowledge`.
- NPC direct `GameState` mutation.
- NPC bypass of Visibility, Knowledge, `StateDelta`, or `EventLog`.
- Large-scale city simulation, war simulation, or economy simulation.
- Background infinite NPC thinking loops.
- NPC calls to external networks, tools, scripts, or arbitrary code plugins.
- Player or narrator access to simulation debug traces, raw state deltas,
  hidden NPC actions, hidden fact text, or behavior timeline debug reasons.
- Debugger frontend editing of NPC runtime state.
- Simulation presets that directly modify active NPC state or grant unknown
  facts.

## Not In v1.4

- LLM world judge or LLM-decided canonical content acceptance.
- LLM direct `GameState` mutation.
- Generators directly modifying active `GameState`, active sessions, or active
  saves.
- Batch import or package apply that bypasses validation gate or quality gate.
- Automatic overwrite of user world packs.
- Arbitrary package/script/template/plugin execution.
- Online marketplace, cloud sync, hosted collaboration, remote publishing, or
  remote URL auto-download.
- Applying untrusted character cards, lorebooks, templates, or generated packs
  directly to active worlds.
- Default real-LLM generation.
- Generated content bypassing Quality Gate.
- Batch tools reading `.env`, API keys, databases, logs, caches, build
  outputs, or system files as content.
- Hidden facts, NPC secrets, RP private fields, or package debug data in normal
  production reports, player APIs, narrator prompts, or player UI.
- Large-scale automatic campaign writing, literary-quality guarantees,
  automatic content repair, or full production task queue orchestration.

## Not In v1.5

- LLM world judge or benchmark-driven world adjudication.
- LLM direct `GameState` mutation.
- Prompt Lab output applied to active saves, active sessions, or active content
  packs.
- Prompt Profiles that grant hidden facts, NPC secrets, raw `GameState`, raw
  `state_deltas`, or state-write authority.
- Provider calls that bypass `LLMProvider`, `create_llm_provider`, or approved
  provider routing.
- Default benchmark/regression runs against real external APIs.
- Logging or exporting full sensitive prompts.
- API keys in frontend state, usage logs, Prompt Profiles, routing rules,
  Prompt Experiment Packages, or exported packages.
- Context Inspector hidden/debug content in normal UI, player UI, or narrator
  prompts.
- Compatibility Matrix automatically switching models or provider settings.
- LLM judge deciding prompt regression pass/fail.
- Local diagnostics sending world hidden facts or allowing local model output
  to modify state.
- Token Budget Manager removing safety/boundary instructions or adding hidden
  facts.
- Online model marketplace, cloud benchmark sharing, hosted telemetry, or
  automatic model downloads.

## Not In v1.6

- Arbitrary code plugin execution.
- LLM world judge or LLM-decided gameplay results.
- LLM direct `GameState` mutation.
- Action Mod direct database writes, save writes, filesystem reads, `.env`
  reads, API key reads, or network access.
- Action Mod bypass of `ActionRegistry`, `StateDelta`, `EventLog`,
  Visibility, NPC Knowledge, validation, or quality gate checks.
- Magic, hacking, crafting, investigation, survival, stealth, combat, social,
  faction, or domain modules bypassing deterministic rule adjudication.
- Online mod marketplace, remote module download, cloud sync, accounts, or
  multiplayer module collaboration.
- Automatic enablement of untrusted modules.
- Automatic application of modules to active saves without compatibility and
  migration review.
- Large-scale war simulation, full tactical combat, MMO economy, or complex
  city/base simulation.
- Module debug traces, dry-run output, raw StateDelta previews, hidden facts,
  hidden witnesses, hidden NPCs, or module secrets in player APIs, narrator
  prompts, or ordinary UI.

## Not In v1.7

- Formal desktop installer, code signing, or automatic update channel.
- Cloud sync, accounts, multiplayer collaboration, online marketplace,
  telemetry upload, hosted crash reporting, or remote help/update fetching.
- Desktop shell direct `GameState` writes.
- Frontend direct `.env`, API key, raw env, database password, or provider
  secret access.
- Launcher scripts that hardcode API keys or inject provider secrets into
  frontend `VITE_*` variables.
- Backup/export defaults that include `.env`, API keys, database connection
  config, logs, caches, frontend build outputs, desktop build outputs, or
  executable files.
- Crash reports or logs uploaded to a network service.
- Health/config/settings APIs returning raw env, API key values, hidden facts,
  raw prompts, raw `GameState`, raw `state_deltas`, or full sensitive paths.
- Workspace templates that copy `.env`, execute scripts, download remote
  content, or overwrite existing non-empty workspaces.
- Error recovery steps that automatically delete, overwrite, migrate, or
  repair user data without explicit confirmation and validation.
- Log Viewer, Backup / Restore, One-click Quality Gate, One-click Export, and
  Offline Help being described as complete runtime features until their
  dedicated services are fully implemented and tested.

## v1.0 Known Limitations

- Split `ActionResult.reason` into player-safe and debug-only reason fields.
- Move raw faction reputation out of player API.
- Sanitize or remap player-visible faction conflict tags.
- Sanitize invalid mod manifest errors so authoring APIs do not return local absolute paths.
- Classify LLM-generated memory summaries from hidden/debug event sources as `debug_only` or `hidden` by default.
- Keep frontend debug panel closed by default if used for non-debug playtesting.
- Rewrite any mojibake prompt text into clean UTF-8.
- Fix `visible_state.relationships` so player API filters relationship
  endpoints by actor visibility, matching player graph behavior.
- Normalize invalid mod manifest errors so authoring/debug APIs do not expose
  absolute local paths.
- Keep desktop DB/log defaults out of source control and move them to OS app
  data directories before any formal packaging milestone.
- Consider a dedicated `require_eval_api()` so `ENABLE_EVAL_API` can enable
  narrative eval endpoints without enabling all debug endpoints.
- Add stronger frontend warnings around save bundle export, because save
  archives can include hidden state and full event history by design.
- Keep desktop packaging as a prototype until bundle scanning, app data
  directory policy, process lifecycle, and secret handling are formalized.
- Continue adding component-level frontend tests for visual authoring panels.
- Keep debug timeline/replay data out of player/narrator routes.
- Consider stricter allowlists for prompt profile free-text fields if profiles
  expand beyond the current local style controls.
- Add a dedicated `ENABLE_QUALITY_API` / `require_quality_api()` if quality
  analyzer APIs need to be exposed separately from local debug/eval/playtest
  flags.
- Keep quality report `safe_details` concise and audited so hidden text cannot
  migrate from debug-only fields into normal dashboards.
