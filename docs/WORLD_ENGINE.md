# World Engine

## v2.9+ Local UI / UX Direction

The roadmap after v2.8 prioritizes local UI / UX foundations and local desktop
polish rather than online architecture. UI improvements may make World, Novel,
Tavern, authoring, mod, QA, debug, and replay workflows easier to use, but they
must not change World Engine authority.

The World Engine remains the fact source. UI layers must not bypass
`StateDelta`, `EventLog`, visibility filtering, save migration, provider
boundaries, package validation, or export privacy rules. Account systems, cloud
sync, online marketplaces, remote package registries, online narrative
platforms, and online mature-content platforms are long-term optional ideas, not
near-term World Engine scope.

v2.9 implements UI surfaces such as Unified Navigation, Project Home, Local
Status Bar, mode landing sections, Provider Setup, Module Browser, Quality Gate
Dashboard, Cross-Mode Dashboard, Settings / Privacy, and Diagnostics Export.
These are safe summary and navigation layers. They do not grant the frontend
authority to directly edit `GameState`, apply proposals, bypass validation, or
write `EventLog`. Normal UI must continue to show visible/safe summaries only;
debug/replay and diagnostics debug export remain gated by `ENABLE_DEBUG_API`.

v3.0 extends this local-first direction with Local Desktop Studio Polish:
launcher/startup status, Project Picker, Recent Projects, Local Config Wizard,
Provider Setup Wizard, Health Check, One-click Quality Gate, Backup / Restore,
Error Recovery, Local Log Viewer, Diagnostics Bundle, Offline Help Center,
Desktop Settings, safe path summaries, and first-run onboarding. These desktop
tools are convenience surfaces over backend APIs. They do not become a second
World Engine, do not directly modify `GameState`, do not bypass validation or
apply flow, and do not write `EventLog` except through existing backend
world-changing paths. Backups, diagnostics, logs, and packaging must exclude
secrets, hidden/debug data, mature/private content, databases, caches, build
outputs, and raw `state_deltas` by default.

v3.1 focuses on Novel Studio UI Pro. Novel Workspace, Outline Tree Pro,
Chapter Editor Pro, Scene Cards, Character Arc, Plot/Foreshadowing, Timeline
Link, World Bible, Draft Snapshot, Writing Session, Search, Export, Import, and
Quality panels are local writing/authoring surfaces. They can display safe
World references and create Novel drafts, but they do not change World Engine
fact authority.

Novel UI rules:

- Novel UI must not directly modify `GameState`.
- Novel drafts, snapshots, writing sessions, preferences, search results,
  quality reports, and export previews are not World facts.
- Novel -> World remains draft/proposal/validation/apply and cannot write
  content packs, active saves, `GameState`, or `EventLog` directly.
- World -> Novel reads safe EventLog/timeline summaries and can create Novel
  draft data only; it must not edit the source `EventLog` or `GameState`.
- Hidden facts, NPC secrets, authoring-only private notes, debug events, raw
  prompts, raw `state_deltas`, API keys, provider secrets, and raw env must not
  enter normal Novel UI, prompt context, exports, diagnostics, or quality
  reports.

v3.2 focuses on Tavern Studio UI Pro. Tavern Workspace, Character Card Library,
Character/RP/Voice editor, Single Character Chat, Multi-NPC Scene, RP Memory,
Emotion, Relationship Tone, Scene Mood, Voice Lab, Boundary/Mature Settings,
Prompt/Provider, Cross-Mode review, RP Safety, export/backup, preferences, and
recovery panels are local RP workflow surfaces. They do not change World Engine
fact authority.

Tavern UI rules:

- Tavern UI must not directly modify `GameState`.
- Tavern sessions, messages, memory, preferences, recovery drafts, and exports
  are not World facts.
- Tavern -> World still requires proposal / validation / dry-run / explicit
  apply.
- Tavern -> Novel creates Novel draft data only and does not modify World
  `EventLog`, active saves, or `GameState`.
- World NPC -> Tavern creates Tavern draft/adapter data only and does not
  overwrite World NPC records.
- World Engine remains the fact source. NPC knowledge, hidden facts,
  `visible_state`, player-visible facts, and visibility filtering are unchanged
  by Tavern UI polish.
- Hidden facts, NPC secrets, NPC unknown facts, private persona, mature memory,
  debug memory, raw prompts, raw `state_deltas`, API keys, provider secrets,
  and raw env must not enter normal Tavern UI, Tavern prompt context, export,
  backup, logs, or quality/safety reports.

v3.3 focuses on World Studio UI Pro. World Workspace, World Play Main View,
Map/Location, NPC/Relationship, Quest/Journal, Inventory/Trade, Tactical
Combat, Economy, Faction War, Deduction, Survival/Travel, Magic/Hacking/
Crafting/Cultivation, Timeline/EventLog, Visible State Inspector, Save/Load,
World Quality/Playtest, Prompt/Provider, Action Input, and Safe Debug panels
are local World play workflow surfaces. They do not change World Engine fact
authority.

World UI rules:

- World UI must not directly modify `GameState`.
- World UI must not directly apply `StateDelta`.
- World UI action submit must go through `/game/input` or an equivalent backend
  action API.
- World state changes still go through backend rule/action resolution,
  `StateDelta`, and `EventLog`.
- `visible_state` is the normal World UI safe source.
- Normal World UI must not display hidden facts, NPC secrets, `npc_knowledge`,
  debug memory, raw prompts, raw `state_deltas`, API keys, provider secrets, or
  raw env.
- Debug/raw EventLog details, raw StateDelta, debug timeline, and module debug
  summaries require `ENABLE_DEBUG_API` and a clearly marked debug-gated view.
- Tactical combat, economy, faction war, deduction, survival/travel, magic,
  hacking, crafting, and cultivation UI panels can show safe visible summaries
  and suggest backend actions only. They do not decide hits, damage, prices,
  war state, truth, route risk, spells, hacks, crafting, or breakthroughs.
- Save / Load UI shows safe save-slot summaries and must not directly read or
  write database files.

v3.4 focuses on Authoring / Mod UI Pro. Authoring Workspace, World Pack Editor,
Script Pack Editor, Character Pack Editor, Quest Graph, Location/Map,
NPC/Faction/Relationship, Item/Economy/Trade, Rumor/Crime/Consequence,
Advanced Module Authoring, Action Mod Editor, Rule Module Contract UI, Module
Browser, Permission Dashboard, Compatibility Matrix, Certification, Import /
Export, Mod Quality Gate, Validation Dashboard, Diff/Preview/Dry-Run, Audit,
Backup/Restore, and Safe Apply panels are local content/package authoring
surfaces. They do not change World Engine fact authority.

Authoring / Mod UI rules:

- Authoring UI must not directly modify active `GameState`, active saves,
  runtime module state, `StateDelta`, or `EventLog`.
- Authoring outputs are drafts, content-pack candidates, package candidates,
  validation reports, previews, dry-run summaries, or proposals until a local
  apply path accepts them.
- Safe Apply writes local project/content-pack/package files only after the
  applicable validation, preview/dry-run, and explicit confirmation gates. It
  must not bypass World Engine runtime rules.
- Applying authoring content to local files does not itself create World facts
  in an active session. Active World changes still require World Engine runtime
  flows, `StateDelta`, and `EventLog`.
- Action Mods remain declarative and must go through `ActionRegistry` when
  enabled/used at runtime. The editor/test harness must not register drafts
  into an active game without validation.
- Rule Modules are contract-only in v3.4 and cannot execute runtime code,
  access the network/filesystem, call providers, or modify game state directly.
- Normal authoring UI must not show hidden facts, NPC secrets, debug memory,
  raw prompts, raw `state_deltas`, provider secrets, API keys, or raw env.
- Import/export and backup/restore must filter secrets, debug data,
  mature/private content, executable payloads, path traversal, and zip slip by
  default.

v3.5 focuses on Local QA / Debug / Replay & Provider Connectivity UI Pro.
Timeline Replay, EventLog Viewer, StateDelta Viewer, Visible vs Debug Compare,
Hidden Leak Report, Playtest, Quality Gate, Performance, Save Migration,
Diagnostics, Safe Debug Export, and Provider Connectivity panels are local
observation/configuration surfaces. They do not change World Engine fact
authority.

QA / Debug / Replay rules:

- Replay UI is read-only. It may select saves/sessions, filter events, and step
  through safe replay summaries, but it must not write `GameState`, rewrite
  `EventLog`, or apply `StateDelta`.
- EventLog Viewer normal view shows safe event summaries and linked delta
  counts only. Raw event JSON and raw StateDelta payloads require a
  debug-gated view.
- StateDelta Viewer and Visible vs Debug State Compare are debug-sensitive
  tools. They require `ENABLE_DEBUG_API`, must redact sensitive values, and
  must never offer an apply-delta or edit-state action.
- Hidden Leak, Quality, Playtest, CrossMode Conflict, Module Stress,
  Performance, Diagnostics, and Debug Export reports are analysis surfaces.
  They may produce blockers/warnings/safe suggestions, but they do not become
  World facts and do not alter active saves.
- Safe Debug Export defaults to safe summaries, requires explicit confirmation
  for raw debug selections, excludes API keys/provider secrets/raw env, and
  does not upload debug material.
- Provider Connectivity, Model Discovery, Model Assignment, and Provider Usage
  configure or summarize Provider Gateway metadata only. They do not let a
  provider decide facts, action success, StateDelta application, EventLog
  writes, or visibility.

v3.6 focuses on Local Performance & Accessibility Polish. Route-level lazy
loading, large-list windowing, report pagination, safe API caches, provider
status caches, keyboard shortcuts, focus helpers, accessibility labels,
reduced motion, loading skeletons, and ErrorBoundary polish are presentation
and local workflow optimizations. They do not change World Engine fact
authority.

Performance / accessibility optimization rules:

- Optimization must not directly modify `GameState`, active saves, module
  runtime state, `StateDelta`, or `EventLog`.
- Large EventLog, Timeline, StateDelta, Quality, Hidden Leak, Provider model,
  Module Browser, Novel, Tavern, World, and Authoring views may window,
  paginate, memoize, debounce, cache safe summaries, or show stale indicators,
  but they must not alter the underlying records or rule outcomes.
- Normal UI remains based on `visible_state` and safe summaries. Hidden facts,
  NPC secrets, debug memory, raw prompts, raw `state_deltas`, raw EventLog
  JSON, raw provider responses, API keys, provider secrets, raw env, and
  mature/private bodies must not be rendered or cached in normal views.
- Debug-sensitive views remain gated by `ENABLE_DEBUG_API`; code splitting or
  lazy loading must not expose StateDelta, debug compare, or raw debug export
  routes as normal UI.
- Provider connection status and safe API caches are local safe-metadata
  caches only. They do not store credentials, do not change Provider Gateway
  routing semantics, and do not let providers decide World facts.
- Keyboard shortcuts and focus improvements must not trigger destructive
  actions such as apply, import, delete, restore, migration apply, or debug
  export without the existing confirmation gates.

v3.7 focuses on Local Playable Complete Product CN closure. The default UI is
Chinese and player/creator-oriented: open/create a local project, configure
models, write novels, run Tavern RP, and play the open world. Product
Readiness, workflow checklists, Provider setup checklist, local project
lifecycle, Novel/Tavern/World/Cross-Mode/Authoring/QA/Backup/Export readiness,
privacy review, product guide, navigation, settings, status, and acceptance
checklist surfaces remain available, but Debug / QA / Authoring / Diagnostics
are advanced tools rather than default Home panels. These product changes do
not change World Engine fact authority.

Local Playable Complete Product CN rules:

- Users can write novels, run Tavern RP, and play the open world locally, but
  each mode keeps its original authority boundary.
- World Studio remains the only runtime World play surface, and World changes
  still go through backend action resolution, `StateDelta`, and `EventLog`.
- Novel and Tavern Cross-Mode work remains draft/proposal/validation/explicit
  apply. Drafts do not directly mutate `GameState`.
- Provider setup, connection testing, model discovery, `ModelProfile` sync,
  and mode assignment configure Provider Gateway only. Providers and LLMs do
  not become world arbiters.
- Real LLM providers may be configured and manually tested by a local user, but
  tests/CI remain fake-provider only. Real provider calls are not made at
  startup and must not be automatic background checks.
- Authoring and Mod workflows operate on local drafts, packages, validation
  reports, dry-runs, and confirmed safe apply. They do not execute arbitrary
  code and do not edit active `GameState`.
- Quality, Debug, Replay, Diagnostics, and Safe Debug Export are local
  observation/review surfaces. Debug/raw views remain gated by
  `ENABLE_DEBUG_API`.
- Backup, Restore, Export, and Diagnostics stay preview/confirm/redacted local
  workflows and exclude API keys, provider secrets, hidden/debug data,
  mature/private content, raw prompts/outputs, raw `state_deltas`, databases,
  logs, caches, and build outputs by default.
- v3.7 does not introduce accounts, cloud sync, online marketplace, remote
  package download, online writing/RP/play, multiplayer collaboration, API
  resale, or arbitrary-code plugins.

## v2.8 Roleplay Immersion & Mature Module Integration

v2.8 strengthens Tavern/RP immersion and adds default-off mature safety policy
infrastructure without changing World Engine authority. The World Engine
remains the fact source for runtime World Mode.

RP integration rules:

- Advanced RP memory, emotion arcs, relationship tone, scene mood, voice lab
  data, boundary profiles, and mature policy data are project/Tavern metadata.
- RP metadata can influence expression, prompt context, and proposal drafting.
- RP metadata does not modify `GameState`, apply `StateDelta`, append
  `EventLog`, or become a World fact.
- Multi-NPC scene generation stores Tavern messages only. Per-NPC prompt
  context must be filtered to that NPC's known and visible facts.
- Dead/incapacitated NPC consistency, NPC unknown facts, nonexistent items,
  quest-claim contradictions, and hidden leaks are reported as
  warnings/errors/proposals, not applied as facts.

Mature boundary rules:

- Mature content is disabled by default through `MatureContentPolicy`.
- Consent, adult-character eligibility, boundary checks, fade-to-black, mature
  memory partitioning, provider routing, export filtering, and mature mod policy
  are deterministic local checks.
- Mature memory and boundary private notes do not enter normal Tavern, Novel,
  World, export, or quality-report contexts.
- Mature content must not be written into World facts. Any RP-to-World effect
  remains a proposal until validation and explicit apply.

Tavern -> World continues to use proposal / validation / explicit apply. A
valid World-changing apply must still use the normal World Engine
`StateDelta` / `EventLog` path. LLM output, Tavern messages, RP memory, mature
memory, and boundary notes cannot bypass that path.

## v2.7 Advanced World Simulation Modules

v2.7 adds optional Advanced World Simulation Modules while preserving World
Engine authority. Modules enrich local play, but they do not become a second
fact source and they do not bypass `GameState`, `StateDelta`, `EventLog`, or
visibility.

### Module State Extension

`ModuleStateExtension` declares controlled module state under:

```text
state.modules.{module_id}
```

Each extension declares module id, namespace, fields, default values,
migration requirement, visibility policy, and save policy. Core `GameState`
fields cannot be redefined by module extensions. Module StateDelta validation
allows module paths such as `modules.tactical_combat...` and rejects attempts
to write unrelated core paths through a module-state helper.

### Module Migration

`ModuleMigrationPlan` and `ModuleMigrationStep` support module save migration
for:

- adding module defaults;
- upgrading module schema;
- disabling a module while preserving state;
- destructive module-state removal only with explicit dangerous confirmation.

Migration dry-run does not write saves. Apply must be confirmed and records
`module_migration_history`. Failure paths should leave the original save
intact.

### v2.7 Module Families

- `tactical_combat`: encounter state, combatants, turn order, active
  combatant, action points, range bands, cover, stance, status effects, and
  player-safe tactical summaries.
- `economy_sim`: regional markets, commodities, supply/demand, scarcity,
  price-index modifiers, trade route status, and deterministic economy ticks.
  It does not overwrite item `base_price`.
- `faction_war`: regional control/conflict state, front pressure, morale,
  supply, war phase, and player-known conflict summaries.
- `magic`: caster mana/focus, known spells, spell definitions, spell effects,
  visibility policy, and public-illegal magic consequence proposals.
- `hacking`: in-world hackable objects, security level, access state,
  trace level, visible digital logs, and alert-style consequences. It never
  touches real networks.
- `crafting`: recipes, materials, workstation checks, crafting time metadata,
  deterministic success/failure, material consumption, and output proposals.
- `deduction`: evidence, claims, hypotheses, contradiction checks, and
  known-fact-only hypothesis testing.
- `survival_travel`: fatigue/hunger/thirst state, travel routes, time/fatigue
  costs, route risk, camp/rest, forage, and hidden-danger filtering.
- `cultivation`: cultivator realm/stage/progress/qi, techniques,
  breakthrough rules, meditation, practice, breakthrough, and pill modifiers.

### Runtime Boundary

- All module runtime changes must be emitted as `StateDelta`.
- All module events that affect runtime state must be recorded as `EventLog`
  events.
- Module actions do not directly modify `GameState`.
- LLMs do not decide module outcomes.
- Hidden combatants, hidden markets, hidden war status, hidden logs, hidden
  evidence, hidden route danger, and hidden techniques must not enter normal
  player-visible summaries.
- Authoring UI/API endpoints validate or edit draft/config data only. They do
  not apply active world state.

Known v2.7 balance note: crafting recipe validation hardening is covered by
v2.7 tests, the balance/simulation audit, and acceptance checks. Zero-input
recipes and obvious net-positive duplication recipes are blocked. Crafting
remains a lightweight MVP, not a complete production-chain simulation.

## v2.6 Script / Mod Platform Pro Integration

v2.6 adds local Script / Mod Platform Pro services around the World Engine. It
does not change World Engine authority.

World Engine rules remain unchanged:

- `GameState` is still the authoritative runtime state.
- Runtime state changes still go through `StateDelta`.
- Runtime World consequences still record `EventLog`.
- Player-facing state still comes from visibility-filtered projections.
- Mods, packages, prompt profiles, RP profiles, style metadata, and provider
  profile packs cannot create authoritative facts.

Action Mod rules:

- Declarative Action Mods must register through `ActionRegistry`.
- Action IDs and aliases are checked for core-action and mod-action conflicts.
- `ModActionHandler` / `ModActionEvaluator` interprets declarative definitions
  only. It does not execute arbitrary code.
- Preconditions, checks, and outcomes are restricted DSL records, not Python,
  JavaScript, or shell code.
- State changes are emitted as `StateDelta` proposals through `ActionResult`;
  the engine apply flow remains responsible for applying valid deltas.
- Mod action events must be recorded through the engine/EventLog flow when a
  runtime action changes state.

Rule Module rules:

- `RuleModuleManifest` is a contract and permission declaration.
- v2.6 Rule Modules do not execute runtime code.
- Rule Modules may declare state schema extensions, but those require
  validation and migration review before runtime use.
- Rule Modules cannot directly access databases, filesystem, network,
  secrets, provider credentials, or `GameState`.

Package and import/export rules:

- Script packs, world extension packs, character packs, prompt/provider
  profile packs, narrative style mods, RP profile mods, action mods, and rule
  modules are local extension packages with manifests and validation.
- Imports and exports must reject zip slip, path traversal, executables,
  `.env`, API keys, provider secrets, databases, logs, caches, build outputs,
  and hidden/debug payloads in normal package paths.
- Package import/export and Module Browser operations are authoring/studio
  services. They do not modify active runtime `GameState`.

## v2.5 Provider Gateway Pro Integration

v2.5 Provider Gateway Pro changes provider management, routing, fallback,
capability metadata, usage estimates, and provider diagnostics. It does not
change World Engine authority.

World Engine rules remain unchanged:

- `GameState` is still the authoritative runtime state.
- Runtime state changes still go through `StateDelta`.
- Runtime World consequences still record `EventLog`.
- Player-facing state still comes from visibility-filtered projections.
- Hidden facts, NPC secrets, debug memory, raw `GameState`, and raw
  `state_deltas` remain outside player APIs and narrator/provider prompts.

Provider routing boundaries:

- Provider choice may change wording, latency, failure behavior, cost
  estimates, or structured-output reliability.
- Provider choice cannot change action rules, visibility rules, quest rules,
  NPC knowledge, relationship authority, or state mutation authority.
- `IntentParser` may use a JSON-capable provider route to parse player input,
  but the parsed intent is still resolved by deterministic engine rules.
- `Narrator` may use a provider route to render visible outcomes, but it may
  receive only confirmed action results and narrator-safe visible facts.
- `MemorySummarizer` may use a provider route to create non-authoritative
  summaries and must not receive raw `state_deltas`.
- Fallback providers must follow the same schema validation, visibility, and
  safety policy as the primary provider.

Provider Gateway Pro data such as `ProviderProfileV2`, `ModelProfile`,
`ProviderRoutingRule`, fallback metadata, `ProviderCallTrace`, and
`ProviderUsageRecord` is local observability/configuration metadata. It is not
World state and cannot apply deltas or create facts.

## v2.4 Cross-Mode Bridge Integration

v2.4 adds Cross-Mode Bridge services around Novel, Tavern, and World, but it
does not change World Engine authority. The World Engine remains the fact
source for World Mode.

Cross-mode bridge rules:

- Novel and Tavern artifacts are drafts/proposals until validated and
  explicitly applied through an allowed World path.
- `CrossModeDraft`, `CrossModeProposal`, `CrossModeReview`, and
  `CrossModeApplyPlan` are project-local authoring/review data. They are not
  runtime facts.
- `CrossModeLink` records references and review state only. It does not apply
  deltas, create facts, or make hidden targets visible.
- World -> Novel reads only player-visible or narrator-safe summaries and does
  not modify EventLog or `GameState`.
- Tavern -> World apply must pass validation, require explicit confirmation,
  apply through `StateDelta`, and record `EventLog` when it performs an actual
  World runtime change.
- Novel/Tavern -> World draft/proposal flows do not write content packs,
  `facts.yaml`, active saves, or `GameState` directly.
- CrossMode audit records complement EventLog for authoring review; they do
  not replace EventLog for World runtime changes.

The current public Tavern -> World apply-confirmed API records an explicit
CrossMode audit confirmation. A full runtime World apply is valid only through
the service path that receives runtime `GameState`, `EventLog`, and validated
StateDeltas together.

Normal CrossMode reports, timeline views, validation output, quality-gate
output, and import/export exclude hidden facts, NPC secrets, debug memory, raw
`state_deltas`, raw env, API keys, and provider secrets.

## v2.3 Tavern Studio Integration

v2.3 adds a local Tavern Studio MVP around the existing World Engine. Tavern
Studio can reference world-facing concepts through safe summaries, proposals,
and `CrossModeLink`, but it does not become the world fact engine.

Tavern integration points are deliberately non-authoritative:

- Tavern characters, RP profiles, voice profiles, sessions, messages, scene
  mood presets, relationship tone, lore context, and RP memory are project-local
  RP/authoring data.
- Tavern Mode does not modify `GameState`.
- Tavern Mode does not apply `StateDelta`.
- Tavern Mode does not append or rewrite `EventLog`.
- Tavern messages do not become world facts.
- Tavern memory is not authoritative and cannot override facts, NPC knowledge,
  relationships, saves, or EventLog.
- `TavernWorldProposal` records possible world effects such as relationship
  changes, fact discoveries, quest hints, promises/deals, NPC mood changes,
  memory-to-world-fact candidates, or scene-to-timeline-event candidates.
  Proposals must be validated and v2.3 does not implement an apply-to-World
  path.
- `WorldNpcToTavernAdapterService` creates Tavern character/RP/voice drafts and
  optional `CrossModeLink` references from safe NPC data. It does not overwrite
  NPCs and excludes NPC secrets or unknown facts in `player_safe` mode.

The World Engine remains the only runtime fact source for World Mode. Any future
Tavern proposal application must go through explicit validation and the normal
World Engine `StateDelta` / `EventLog` path.

## v2.2 Novel Studio Integration

v2.2 adds a Novel Studio MVP around the existing World Engine. Novel Studio can
reference World Bible entries, timeline summaries, and player-visible EventLog
summaries, but it does not become a world fact source.

- Novel manuscripts, outlines, chapters, scenes, arcs, plot threads, and
  foreshadowing are authoring drafts.
- Novel-to-World conversion produces `WorldContentDraft` candidates only.
- EventLog-to-Novel import is one-way and read-only against the EventLog.
- Novel export and prompt context exclude hidden facts, debug data, raw
  `state_deltas`, API keys, raw env, and provider secrets.
- World Mode actions continue to be resolved by deterministic rules,
  `StateDelta`, `GameState`, and `EventLog`.

Novel Studio integration points are read-only or proposal-only from the World
Engine perspective:

- `CrossModeLink` can record that a world event, fact, NPC, or timeline entry
  is related to a novel scene, outline node, or chapter draft. The link does
  not dereference hidden targets into normal views and does not apply deltas.
- `WorldContentDraft` is a candidate object for authoring review. It is not a
  content-pack write, not a save migration, and not a `GameState` mutation.
- EventLog-to-chapter import uses player-visible or narrator-safe event
  summaries. It never imports raw `state_deltas`, debug events, hidden events,
  or raw `GameState`.
- Novel consistency and quality checks can report potential world-reference
  issues, but they do not repair or rewrite World Mode state.

The World Engine remains the only runtime fact engine. Novel manuscripts,
outlines, chapters, scenes, character arcs, plot threads, foreshadowing items,
and generated drafts are authoring artifacts until a separate future
content-validation flow explicitly accepts candidate content.

## v2.1 NarrativeProject Integration

v2.1 introduces `NarrativeProject` as a local project container above the
existing world engine. A project can organize Novel drafts, Tavern session
drafts, World content/saves/campaigns, script/mod metadata, provider profile
references, quality reports, and exports under one workspace. This project
layer does not change world authority.

World Engine remains the fact source for World Mode:

- `GameState` is still authoritative.
- World state changes still go through `StateDelta`.
- Player actions and system consequences still append `EventLog` entries.
- Player-facing responses still use `visible_state`.
- Hidden facts, NPC secrets, debug memory, raw `GameState`, and raw
  `state_deltas` remain out of player and narrator contexts.

Novel and Tavern project data are not world facts:

- Novel outlines and chapter drafts are authoring drafts.
- Tavern sessions, messages, and RP proposals are RP draft/proposal records.
- Neither mode can directly modify active `GameState`.
- `CrossModeLink` records references between modes only; it does not convert
  drafts into facts, reveal hidden targets, or apply deltas.

The v2.1 World Mode adapter exposes project-aware routes such as
`POST /projects/{project_id}/world/start` and
`GET /projects/{project_id}/world/state/{session_id}`. These use the existing
world loader/session/game-loop path and return visible-state projections. The
legacy `/game/start` flow remains supported.

## v2.0 Platform Integration

v2.0 adds platform services around the world engine without changing the engine
authority model. Plugins, modules, packages, workspace projects, campaigns,
timeline branches, and transfer packages are metadata and compatibility layers.
They cannot directly mutate active GameState.

Campaign and timeline services preserve EventLog lineage and keep hidden facts
inside the active campaign/branch visibility boundary. Character transfer uses
redacted packages and target-world mapping warnings. Package v2 import/export
must pass checksum, compatibility, zip slip, executable, and secret checks.

This document describes the local world engine as of v1.7 Polished Desktop
Studio on top of v1.6 Advanced Gameplay Modules, v1.5 Local Model & Prompt
Lab, v1.4 Content Production Pipeline, v1.3 Advanced NPC Simulation, v1.2
Visual Authoring Pro, the v1.1 Roleplay Immersion Layer, and v1.0 Stable Local
Studio Edition. The engine is the only source of truth for world state, rules,
consequences, persistence, and visibility. The LLM layer may parse intent,
render narration, and summarize memory, but it does not decide rule outcomes
or mutate `GameState`.

## Core Boundary

- `GameState` is authoritative.
- All state changes are represented as `StateDelta` entries.
- Player actions and system ticks are recorded as `Event` records.
- Rule systems never call the LLM.
- Narration receives only player-visible facts and narrator-safe memory.
- Hidden facts, NPC secrets, hidden witnesses, debug data, and hidden memory do
  not enter player API responses or narrator prompts.

## Main Flow

1. The API or CLI receives player input.
2. `IntentParser` turns text into a structured intent through `LLMProvider`.
3. `ActionDispatcher` routes the intent to a deterministic action handler.
4. The handler returns `ActionResult` with `state_deltas`.
5. `apply_delta` updates `GameState`.
6. `EventLog` records the player event.
7. `WorldTick` runs deterministic system rules and records system events.
8. `Narrator` renders the visible result as text.
9. APIs return `narrative_text`, suggested actions, and structured
   `visible_state`.

## GameState Areas

The current state model includes:

- Player: location, inventory ownership through item state, currency, health,
  and stealth-related fields.
- Locations: exits, visible objects, cover/light fields, and metadata.
- NPCs: location, mood, relationship to player, knowledge, secrets, life state,
  schedule, goals, plan state, merchant data, faction id, alertness, and
  suspicion.
- Items: location/owner/container ownership, portability, hidden/discovered
  state, tags, price, rarity, and trade flags.
- Facts: public, hidden, or discoverable structured facts with known-by data.
- Quests: stages, objectives, visibility, triggers, and runtime state.
- Social systems: factions, reputation, rumors, crimes, witnesses,
  relationships, faction conflict, social flags, and consequence dedupe data.
- Combat and life state: combatants, hp, condition, stance, and status effects.
- Memory: memory records are persisted separately and are not authoritative
  facts.
- Gameplay module state: optional v1.6 fields for magic resources, hacking
  targets/tools/network nodes, crafting stations, investigation evidence and
  hypotheses, survival/travel/weather/camps, stealth/noise/cover, faction
  missions, domain/base management, and combat/social extensions. These fields
  are still ordinary `GameState` data and may only change through
  `StateDelta`.

Old save JSON is loaded through Pydantic defaults, compatibility-friendly
model fields, and the v0.6+ save migration system. Missing v0.3-v0.6 fields
should default or migrate rather than crash.

## StateDelta Rules

`StateDelta` supports structured operations such as `set`, `inc`, `add`, and
`remove` over dot paths. Core paths used by the current engine include:

- `player.location_id`
- `player.currency`
- `items.{item_id}.owner_id`
- `items.{item_id}.location_id`
- `npcs.{npc_id}.location_id`
- `npcs.{npc_id}.goals`
- `npcs.{npc_id}.plan_state`
- `relationships.{relationship_id}.trust`
- `factions.{faction_id}.reputation`
- `factions.{faction_id}.alert_level`
- `rumors.{rumor_id}.known_by_npcs`
- `crimes.{crime_id}.status`
- `witnesses.{witness_id}`
- `combats.{combat_id}.combatants.{actor_id}.hp`
- `quests.{quest_id}.current_stage`

Rules may prepare deltas, but they must not directly mutate `GameState`.

## Event Log

Every player action and system consequence is represented as an `Event`.
Events include:

- `event_id`
- `turn`
- `actor_id`
- `action_type`
- `target_id`
- `input_text`
- `result`
- `state_deltas`
- `visible_to_player`
- `narrative_text`
- `created_at`

Debug timeline APIs expose events only when debug mode is enabled. Player APIs
do not expose raw `state_deltas`.

## Content Packs

World content lives under `worlds/{world_id}`. The loader validates YAML
schemas and reference integrity before creating runtime state. Current content
files include:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`

The engine must not hardcode content from `mist_valley` or any other world.

## Visibility

Player-visible state is produced by explicit visibility rules. It may include:

- current location
- formatted game time
- inventory
- visible objects
- visible NPCs
- known facts
- visible quests
- known factions and reputation bands
- known rumors
- known crimes or public consequences
- known relationships
- visible faction conflicts

It must not include:

- hidden facts not discovered by the player
- hidden objects or NPCs not discovered by the player
- NPC secrets
- hidden witnesses
- hidden faction details
- hidden/debug memory
- raw event `state_deltas`
- API keys, environment variables, or local paths

Known limitation: visible faction conflict summaries include
`conflict_tags` for player-known factions. Authors should avoid using those
tags for secret-only content until a stricter public-label field is added.

Known v0.7 hardening note: authoring/debug views may intentionally show full
local content, raw debug events, or raw deltas. They must stay visually and API
separated from player views and narrator payloads.

Known v0.8 authoring note: visual editors are authoring tools over content-pack
YAML. They do not change active session `GameState`, and saved edits must pass
preview/validation/explicit save flows.

## Time, Schedule, and World Tick

Game time is a simple day plus minutes-of-day structure. Actions advance time
through deltas. After player action resolution, `WorldTick` runs deterministic
system rules. The intended order is:

1. Time advancement from the action result.
2. NPC schedule resolution.
3. Quest triggers.
4. Crime witness/report handling.
5. Rumor propagation.
6. Reputation and faction consequences.
7. NPC reactions.
8. NPC planning.
9. Delayed consequences.

System changes are recorded as system events. Hidden system events may affect
the world, but they do not become narration unless later visible through normal
rules.

## NPC Schedule

NPC schedules are loaded from `npcs.yaml`. A schedule entry contains:

- `time_of_day`
- `location_id`
- `activity`

The resolver moves or updates NPCs using `StateDelta`. Dead or incapacitated
NPCs do not follow schedules.

## Search

`search` is a deterministic action for discovering objects or facts near the
current location, a visible object, or a visible NPC. Success can reveal
discoverable objects/facts by updating discovered state through `StateDelta`.
Failure consumes time but does not leak hidden content.

## Inventory and Economy

Inventory is derived from item ownership in `GameState`, not from frontend
state. Items may have:

- `location_id`
- `owner_id`
- `container_id`
- `portable`
- `hidden`
- `discovered_by`
- `base_price`
- `tradeable`
- `rarity`
- `tags`

Only one ownership location should be active at a time. Pickup, drop, use,
buy, and sell actions produce `StateDelta` entries and events. Trade prices are
rule-based and may consider merchant modifiers and reputation bands. The LLM
does not price items.

The current engine does not implement a dynamic supply/demand economy, auctions, equipment
slots, or full stolen-goods simulation.

## Lockpick and Sneak

`lockpick` supports locked doors and containers with structured lock state.
Success, partial success, failure, and invalid results are rule outcomes.
Failure can leave traces or create social consequences.

`sneak` supports movement or approach attempts influenced by cover, light,
NPC alertness, and player stealth fields. Hidden observers may affect the rule
result, but their identity is not exposed to the narrator or player API.

## Quest State Machine

Quests are loaded from `quests.yaml` with stages, objectives, visibility, and
triggers. Triggers may reference facts, items, NPC conversations, locations,
reputation, crimes, or other structured state. Quest state changes go through
`StateDelta` and are visible only when the quest is known or active.

## Social Systems

### Factions and Reputation

`factions.yaml` defines factions, default player reputation, visibility, tags,
and conflict metadata. Reputation bands include hostile, suspicious,
neutral, friendly, and trusted. Reputation changes are rule-driven and are not
decided by the LLM.

### Rumors

Rumors are structured records with known-by NPCs/factions, player visibility,
truth status, spread level, and safe player-facing text. A rumor linked to a
hidden fact must not reveal the hidden fact text unless the fact is legitimately
known to the player.

### Crime and Witnesses

Crime records and witness records represent theft, assault, murder,
lockpicking, trespass, vandalism, and reserved crime types. Witness detection
uses location, visibility, life state, light/cover, and sneak/combat context.
Hidden witnesses may affect rules without being exposed to player APIs.

### NPC Reactions

NPC reactions include suspicion changes, refusing talk, fleeing, spreading
rumors, calling for help, friendliness, and hostility. Reactions require
structured inputs such as known crimes, known rumors, relationship state,
faction reputation, combat status, or quest state. Dead or incapacitated NPCs
do not react.

### Faction Conflict

Faction conflict tracks faction-to-faction relations, alert level, conflict
level, resources, and conflict tags. Incidents can come from crimes, public
combat, rumors, quest stages, or reputation bands. Conflict changes are
deduped by source/consequence ids where supported and are visible only for
player-known factions/conflicts.

The current engine does not simulate armies, diplomacy AI, territorial war, or complex
conflict escalation.

## Combat and Life State

Combat is lightweight and rules-first. Actions include:

- `attack`
- `defend`
- `flee`

Damage, hit/miss, hp, condition, stance, incapacitation, and death are decided
by deterministic rules. Public assault or killing can feed crime, witness,
rumor, reputation, quest, and reaction systems.

v0.6+ includes a small combat expansion:

- stances: `aggressive`, `defensive`, `cautious`, `fleeing`
- status effects: `guarded`, `stunned`, `bleeding`
- defend grants a guarded/defensive consequence through `StateDelta`
- guarded can reduce damage and be consumed
- stunned actors cannot act
- heavy damage can mark bleeding for future consequences
- flee has deterministic risk and failure consequences
- non-lethal attack can incapacitate without directly killing
- `visible_state.active_combat` exposes only player-visible combatants

This is not tactical combat. There is no grid movement, equipment system,
magic combat, or multi-round AI combat planner.

Life state prevents contradictions:

- Dead NPCs do not move by schedule.
- Dead NPCs do not talk.
- Dead NPCs do not spread rumors.
- Dead NPCs do not become new witnesses.
- Incapacitated NPCs have restricted action.

## Memory

Memory is not authoritative state. It summarizes or indexes events for
retrieval, but it does not replace `GameState`, facts, quests, or event logs.

### MemoryStore Backends

The current engine supports:

- `InMemoryMemoryStore`
- `SQLiteMemoryStore`
- `LocalVectorMemoryStore` / optional vector-style interface with deterministic
  substring and metadata fallback

Search supports tags, entities, facts, turn ranges, substring, recency, and
semantic query only when a backend supports it. No external vector database is
required.

### MemoryContextBuilder

`MemoryContextBuilder` builds safe memory context for narrator and NPC dialogue.
It filters by:

- memory visibility
- player-known facts
- NPC knowledge
- location/entity/fact relevance
- recent turns
- importance

`hidden` and `debug_only` memories do not enter narrator context. NPC dialogue
does not receive memories tied to facts or rumors the NPC does not know.

## Procedural Side Quest Drafts

The side quest generator creates `QuestDraft` candidates. It has:

- a rule-based mode that does not call the LLM
- an optional LLM-assisted mode through `LLMProvider`

Generated quests are drafts, not runtime quest state. They do not modify
`GameState`, active saves, or `quests.yaml`. A creator must explicitly review
and save content through authoring tools, and validation must pass before the
pack is treated as valid.

LLM-assisted drafts must be schema-validated and may only reference existing
content unless new content is marked as proposed.

## Studio Home Dashboard

v0.7 adds a local Studio Home panel backed by `GET /studio/status`. It is a
safe summary surface for the local project. It can show:

- engine version and backend health
- available worlds count
- recent safe save summaries
- authoring/debug/performance API status
- current `LLM_PROVIDER` and local provider status labels
- recent validation and playtest summaries when available
- shortcuts to Play, Authoring, Save Browser, Migration, Mod Manager, Graphs,
  Narrative Evals, Performance, Playtesting, and Settings

Studio Home is not a debug dump. It must not return API keys, raw environment
variables, raw `GameState`, raw `state_deltas`, hidden facts, NPC secrets, or
debug memory.

## Settings and Local Privacy Panel

v0.7 adds `GET /studio/config-summary` and a Settings / Local Privacy panel.
The endpoint returns safe booleans and labels for:

- `LLM_PROVIDER`
- provider configured/status text
- whether the configured provider may receive prompts
- authoring/debug/performance/playtest/eval API status
- whether a database is configured
- a redacted database hint
- whether an API key is configured, without returning the key

The panel explains that saves, `GameState`, memory records, content packs, and
mods stay local; only configured LLM providers may receive prompts; API keys
are not exposed to the frontend; and local mods are validated as content-only
packages.

## Authoring API and Validation UX

The local authoring API is controlled by `ENABLE_AUTHORING_API`. It is intended
for local development only. It can list worlds, read whitelisted YAML files,
write whitelisted YAML after YAML parsing, create world pack skeletons, and run
structured validation.

Allowed world files are:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`

The API rejects path traversal and non-whitelisted file names. It must not read
`.env`, database files, logs, source files, or arbitrary local paths. It must
not mutate active session `GameState`.

Validation reports contain structured `errors`, `warnings`, and `suggestions`
with file, path, code, message, severity, and optional reference ids. CLI
validation still returns a non-zero exit code when errors are present.

## Authoring Diff, Preview, and Dry Run

v0.6+ adds local authoring dry-run support:

- `preview-file-change` parses proposed YAML, validates a draft in a temporary
  copy, returns normalized YAML when possible, and reports a diff summary.
- `validate-draft` validates proposed file content without writing it.
- `impact-analysis` reports removed ids, renamed-id guesses, changed exits,
  and whether existing saves may require review.

These APIs do not modify active `GameState`, active sessions, or saves. They
are local authoring tools only and must stay behind `ENABLE_AUTHORING_API`.

## v1.2 Visual Authoring Pro

v1.2 adds Visual Authoring Pro: a broader local authoring workflow for maps,
quests, social data, economy, RP scenes, reusable packs, templates, branch
merge, content review, reference picking, and draft history. These are content
pack tools. They do not modify active session `GameState`, do not call the LLM
to generate authoritative content, and do not execute imported code.

### Authoring Pro Boundary

`docs/AUTHORING_BOUNDARY.md` defines the v1.2 boundary terms:

- `authoring_draft`
- `preview_result`
- `validation_report`
- `explicit_save`
- `active_world_pack`
- `active_game_state`
- `migration_impact`
- `hidden_authoring_field`
- `player_visible_content`

Preview and validation do not write disk. Save writes content-pack files only.
Apply-to-active-session is not part of the default v1.2 workflow. Warnings
require confirmation, and validation errors block save. Hidden authoring fields
must not enter player UI or ordinary narrator/RP prompts.

### Authoring Validation Gate

`AuthoringValidationGate` is the shared save/import/merge/export/apply gate.
It receives draft content, target world, operation type, affected files, and an
optional validation report. It returns validation, quality warnings, migration
impact, hidden leak risks, `allowed_to_save`, and `confirmation_required`.

All v1.2 editor save paths should route through this gate directly or through
`ContentAuthoringService.write_file(s)`. Hidden leak risks are blocked by
default unless an explicit debug override is designed for a local-only flow.

### Visual Map Editor Pro

Map authoring extends `MapVisualGraph` with regions, layers, conditional edges,
locked edges, hidden edges, travel costs, and discovery rules. Backend APIs:

- `GET /authoring/worlds/{world_id}/map`
- `POST /authoring/worlds/{world_id}/map/preview`
- `POST /authoring/worlds/{world_id}/map/validate`
- `PUT /authoring/worlds/{world_id}/map`

The editor supports node coordinates, location add/remove, exit edge edits, and
edge types such as exit, locked, hidden, conditional, and one-way. Player map
builders filter hidden nodes and hidden edges.

### Quest Graph Editor Pro

Quest authoring represents quests, stages, objectives, triggers, rewards,
consequences, optional paths, failure paths, and hidden objective fields. APIs:

- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`
- `POST /authoring/worlds/{world_id}/quests/graph/validate`
- `PUT /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/scenario-draft`

Graph preview and scenario-draft generation are deterministic. Hidden
objectives do not enter player quest UI unless normal visibility rules expose
them.

### NPC Relationship Graph Editing And Faction Conflict Editor

The social authoring graph reads and writes `relationships.yaml`,
`factions.yaml`, and NPC metadata. APIs:

- `GET /authoring/worlds/{world_id}/social/graph`
- `POST /authoring/worlds/{world_id}/social/graph/preview`
- `POST /authoring/worlds/{world_id}/social/graph/validate`
- `PUT /authoring/worlds/{world_id}/social/graph`

It supports NPC relationship edges, trust/fear/affinity/obligation, hidden
relationships, RP tone presets, faction nodes, faction relation edges, alert
levels, visibility, and conflict tags. Player relationship and faction graphs
remain separate filtered runtime views.

### Rumor / Crime Consequence Graph Pro

Rumor/crime consequence authoring models triggers, witnesses, crimes, rumors,
reputation effects, NPC reactions, quest effects, delay/cooldown, and dedupe
keys. APIs:

- `GET /authoring/worlds/{world_id}/rumor-crime`
- `POST /authoring/worlds/{world_id}/rumor-crime/preview`
- `POST /authoring/worlds/{world_id}/rumor-crime/validate`
- `PUT /authoring/worlds/{world_id}/rumor-crime`

Validation checks missing fact/faction/NPC/quest refs, hidden fact text leakage,
loops, and dedupe warnings. Runtime consequences are still decided by code.

### Item / Economy Editor Pro

Item/economy authoring covers items, merchants, shop inventory edges, price
modifiers, stolen item policy, and quest reward links. APIs:

- `GET /authoring/worlds/{world_id}/economy`
- `POST /authoring/worlds/{world_id}/economy/preview`
- `POST /authoring/worlds/{world_id}/economy/validate`
- `POST /authoring/worlds/{world_id}/economy/balance-check`
- `PUT /authoring/worlds/{world_id}/economy`

The frontend offers table and graph-style editing surfaces. Backend rules remain
authoritative for real trade prices, and hidden items cannot enter player shop
inventory.

### RP Character Authoring UI Pro

RP character authoring reads NPC base fields, `rp_profile`, `voice_profile`,
default emotional state, example dialogue refs, lorebook links, scene mood
preferences, import safety reports, and safe export data. APIs:

- `GET /authoring/worlds/{world_id}/rp/characters/pro`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/import-preview`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/preview`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/validate`
- `PUT /authoring/worlds/{world_id}/rp/characters/pro`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/safe-export`

Unsafe imported prompt text is rejected or quarantined. Safe export excludes
private summaries, hidden facts, NPC secrets, debug state, and unsafe examples.

### Dialogue Scene Editor And Group RP Scene Authoring

Dialogue scene templates describe participants, focus NPC, location, dialogue
mode, scene mood, opening context, allowed/forbidden topics, required visible
facts, and possible outcomes. Group RP scene templates add scene type, required
roles, turn order policy, speaker selection policy, tension, and exit
conditions. APIs:

- `GET /authoring/worlds/{world_id}/dialogue-scenes`
- `POST /authoring/worlds/{world_id}/dialogue-scenes/preview`
- `POST /authoring/worlds/{world_id}/dialogue-scenes/validate`
- `PUT /authoring/worlds/{world_id}/dialogue-scenes`
- `GET /authoring/worlds/{world_id}/group-rp-scenes`
- `POST /authoring/worlds/{world_id}/group-rp-scenes/preview`
- `POST /authoring/worlds/{world_id}/group-rp-scenes/validate`
- `PUT /authoring/worlds/{world_id}/group-rp-scenes`

These tools save templates. They do not start active dialogue sessions, do not
generate model text, and do not create hidden facts.

### Character Pack Builder

Character packs bundle NPCs, RP profiles, voice profiles, prompt-safe examples,
dialogue/group scene templates, flavor lore, and optional fact candidates.
APIs:

- `POST /authoring/character-packs/export`
- `POST /authoring/character-packs/import-dry-run`
- `POST /authoring/character-packs/import-apply`

Import apply requires explicit confirmation and validation. Character packs
reject API keys, executable files, path traversal, remote URLs, and script-like
payloads. Safe export does not include hidden facts by default.

### Template Wizard

Template Wizard creates deterministic drafts for world, location cluster,
questline, NPC set, character pack, dialogue scene, group RP scene, faction
conflict, and mystery case templates. APIs:

- `POST /authoring/template-wizard/preview`
- `POST /authoring/template-wizard/validate`
- `POST /authoring/template-wizard/apply`

Preview does not write disk. Apply requires validation and explicit save/apply
semantics. Templates are YAML/data only and do not execute scripts.

### World Branch Merge Assistant And Content Diff Review

Merge Assistant compares world branches, detects conflicts, accepts explicit
base/ours/theirs/custom resolutions, validates merge drafts, and saves only
after confirmation and validation. APIs:

- `POST /authoring/worlds/{world_id}/merge/preview`
- `POST /authoring/worlds/{world_id}/merge/validate`
- `POST /authoring/worlds/{world_id}/merge/save`

Content Diff Review provides file/entity/graph/package/schema/visibility/RP
profile diff summaries:

- `POST /authoring/diff/review`

These tools do not auto-merge with an LLM and do not modify active sessions.
Normal views should continue to redact hidden details; full conflict payloads
are local authoring/debug data.

### Authoring Workflow Presets, Local Content Library, Reference Picker, And Draft History

Workflow presets are a lightweight launcher, not a workflow engine:

- `GET /authoring/workflow-presets`

Local Content Library lists, inspects, validates, imports, exports, archives,
and duplicates local worlds, packs, scenarios, prompt/RP profiles, and mods:

- `GET /library/items`
- `GET /library/items/{id}`
- `POST /library/items/{id}/validate`
- `POST /library/import`
- `POST /library/export`
- `POST /library/duplicate`

ReferenceIndex powers the common Reference Picker:

- `GET /authoring/worlds/{world_id}/references`

It returns authoring-safe metadata and marks hidden refs. It is not a player
API.

Draft History stores local authoring draft snapshots, not active `GameState`:

- `GET /authoring/drafts`
- `POST /authoring/drafts/snapshot`
- `POST /authoring/drafts/compare`
- `POST /authoring/drafts/{draft_id}/restore`
- `DELETE /authoring/drafts/{draft_id}`

Restored drafts still require validation before save. Draft history rejects API
keys and raw env/config-like content.

## Visual Map Data Model and Editor

v0.8 adds a map visualization layer for `locations.yaml`. Location definitions
may include an optional `visual` field:

- `x`
- `y`
- `region_id`
- `icon`
- `color_tag`
- `display_group`
- `tags`
- `visibility`
- `notes` for authoring/debug use only

The backend exposes authoring map graph data as `MapVisualGraph` with
`MapVisualNode` and `MapVisualEdge`. Edges are derived from location exits.
When visual fields are missing, the graph builder supplies deterministic
authoring defaults without writing files.

Authoring map APIs are behind `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds/{world_id}/map`
- `POST /authoring/worlds/{world_id}/map/preview`
- `POST /authoring/worlds/{world_id}/map/validate`
- `PUT /authoring/worlds/{world_id}/map`

`PUT` converts graph edits back to `locations.yaml` and runs world validation
before saving. Validation errors reject the save. Player-visible map graphs
filter hidden nodes and hidden edges; authoring maps may show complete local
content in authoring-only panels.

The frontend Map Editor provides a simple SVG/form editor for node positions,
labels, regions, tags, and exit edges. It does not implement automatic layout,
does not call the LLM, and does not change player movement rules.

## Scenario Template System and Local Template Browser

v0.7 added local `ScenarioTemplate` support for reusable authoring drafts.
Templates live under `templates/` and are YAML data, not executable scripts.
v0.8 adds a Local Template Browser that can list, inspect, preview, validate,
and apply templates through authoring-gated APIs.

`ScenarioTemplate` fields:

- `id`
- `name`
- `description`
- `template_type`: `world`, `quest`, `location_cluster`, `npc_set`,
  `faction_set`, `mystery`, or `combat_encounter`
- `required_variables`
- `optional_variables`
- `output_files`
- `validation_rules`
- `tags`

The template renderer supports:

- `list_templates`
- `preview_template`
- `render_template`
- `validate_rendered_content`

Rendering performs simple `{{variable}}` substitution. Variable names and
values are checked for unsafe path traversal patterns, and output files must be
normal authoring YAML files. Preview and render do not write disk, do not
modify active `GameState`, and do not call the LLM.

Rendered world templates are validated in a temporary world root with
`validate_world_pack`. Non-world templates can be validated against a temporary
copy of a target world. Applying rendered content is intentionally separate:
creators must use the authoring API or another explicit save step, and the
validator remains the gate.

Template APIs:

- `GET /authoring/templates`
- `GET /authoring/templates/{template_id}`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/templates/{template_id}/apply`

Templates cannot execute scripts, cannot write active saves, and cannot bypass
validation.

## Import / Export Workflow and Advanced Packages

v0.7 added local authoring-gated archive import/export for worlds, mods, and
saves. v0.8 extends this into local packages with manifests, checksums,
compatibility checks, dry-run, and explicit apply. Archives are zip files
represented by the API as base64 payloads.

Import/export endpoints:

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

Legacy archive manifests are stored in `export_manifest.json` and include:

- `export_type`: `world`, `mod`, or `save`
- `id`
- `schema_version`
- optional content/mod version fields
- included file list

The importer rejects zip slip/path traversal, executable files, `.env`,
secret files, local database files, and logs. World imports run world
validation, mod imports run mod validation, and save imports check migration
status. Import/export does not call the LLM and does not modify active session
`GameState`.

v0.8 package archives also include `local_package_manifest.json` with:

- `package_id`
- `package_type`: `world`, `mod`, `save_bundle`, `template_pack`, or
  `scenario_suite`
- `version`
- `engine_version_min`
- `schema_version`
- `content_pack_version`
- `included_files`
- `checksums`
- `dependencies`
- `conflicts`
- `created_at`
- `notes`

Dry-run validates manifests, file paths, disallowed file types, checksums,
compatibility, overwrite conflicts, world/mod validation, and save migration
status. Apply requires explicit confirmation and a passing dry-run.

Save export can include full hidden save state by design. It is therefore a
local authoring/backup workflow only and must stay behind
`ENABLE_AUTHORING_API`.

## Visual Quest Graph Editor

v0.7 added an initial authoring-only quest graph layer for `quests.yaml`. v0.8
expands it into a fuller visual quest editor. It parses quests into:

- quest nodes
- stage nodes
- objective nodes
- trigger nodes
- reward nodes
- `next_stages` edges
- trigger-to-stage edges
- failure/alternate path edges where content provides them

The UI supports viewing and editing quest title/description, stage
title/description, objectives, triggers, `next_stages`, rewards, and visibility
fields. The frontend sends the edited graph to backend preview/validate/save
endpoints, which convert it back to `quests.yaml` and run draft validation.
Saving still uses the normal authoring validation path, so validation remains
the gate and active `GameState` is not modified.

Quest graph APIs are local authoring endpoints behind `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`
- `POST /authoring/worlds/{world_id}/quests/graph/validate`
- `PUT /authoring/worlds/{world_id}/quests/graph`

Hidden quests can appear in the authoring UI because authoring is a local
creator tool, but they must not enter player `visible_state`.

Validation catches invalid `next_stage` references and missing trigger
references. Unreachable stages and missing terminal stages are warnings.

## NPC Goal Editor

v0.8 adds authoring support for NPC goals in `npcs.yaml`. The editor reads,
previews, validates, and saves structured goal data. The backend represents
the graph as NPC goal authoring DTOs and validates:

- unique goal ids per NPC
- valid priority values
- valid goal status
- condition references to facts/items/NPCs/locations/quests
- supported planning actions in `allowed_actions`
- legal `forbidden_actions`
- safe `desired_state` references

APIs:

- `GET /authoring/worlds/{world_id}/npcs/goals`
- `POST /authoring/worlds/{world_id}/npcs/goals/preview`
- `POST /authoring/worlds/{world_id}/npcs/goals/validate`
- `PUT /authoring/worlds/{world_id}/npcs/goals`

NPC goals remain deterministic planning inputs. The editor does not call the
LLM, does not grant NPCs unknown facts, and does not modify active runtime
state.

## Faction / Relationship Visual Editor

v0.8 adds authoring graph support for factions and NPC relationships. It reads
`factions.yaml`, `relationships.yaml`, and related NPC metadata, then exposes
authoring-only graph nodes and edges for:

- faction nodes
- NPC nodes
- relationship edges
- conflict/relation edges
- trust, fear, affinity, obligation, visibility, and conflict values

APIs:

- `GET /authoring/worlds/{world_id}/social/graph`
- `POST /authoring/worlds/{world_id}/social/graph/preview`
- `POST /authoring/worlds/{world_id}/social/graph/validate`
- `PUT /authoring/worlds/{world_id}/social/graph`

Player graph endpoints remain filtered separately. Hidden relationships and
hidden faction conflicts may appear in authoring views but must not enter
player graph or player visible state.

## Item / Economy Editor

v0.8 adds an Item / Economy authoring editor over `items.yaml` and merchant
fields in `npcs.yaml`. It supports item ids, names, descriptions, ownership,
visibility, tags, base prices, rarity, trade flags, portability, and merchant
shop inventory.

APIs:

- `GET /authoring/worlds/{world_id}/economy`
- `POST /authoring/worlds/{world_id}/economy/preview`
- `POST /authoring/worlds/{world_id}/economy/validate`
- `PUT /authoring/worlds/{world_id}/economy`

Validation checks item id uniqueness, ownership conflicts, non-negative
prices, valid trade flags, valid shop inventory item ids, and hidden shop item
warnings. Trade authority remains in backend economy rules; the frontend does
not calculate authoritative prices.

## Rumor / Crime Consequence Editor

v0.8 adds authoring support for social consequence graphs around rumors,
crimes, witnesses, reputation effects, and quest triggers. The editor reads
`rumors.yaml`, facts, factions, quests, and related consequence content where
available.

APIs:

- `GET /authoring/worlds/{world_id}/rumor-crime`
- `POST /authoring/worlds/{world_id}/rumor-crime/preview`
- `POST /authoring/worlds/{world_id}/rumor-crime/validate`
- `PUT /authoring/worlds/{world_id}/rumor-crime`

Validation checks rumor fact references, hidden fact text leakage in
player-facing rumor text, valid crime types, faction ids, quest trigger
references, duplicate consequence ids, and simple consequence-loop risks.
Runtime crime and social consequences remain rule-engine decisions.

## Visual Validation Graph

v0.8 can turn a structured validation report into a local authoring
`ValidationGraph`. It includes file, entity, reference, schema, and issue
nodes, with edges such as contains, references, missing_reference,
invalid_value, visibility_risk, and cycle.

APIs:

- `GET /authoring/worlds/{world_id}/validation-graph`
- `POST /authoring/worlds/{world_id}/validation-graph`

The graph is an authoring diagnostic. It does not auto-fix YAML, does not call
the LLM, and should avoid local absolute paths or sensitive configuration.

## Timeline Replay Visualizer

v0.8 adds debug-only timeline replay data for sessions and saves:

- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/timeline`
- `POST /debug/saves/{save_id}/replay-dry-run`

Timeline replay groups events by turn and can include event kind, actor,
action type, result, visible-to-player flag, raw `state_deltas`, visible
changes, and replay dry-run summaries. Replay dry-run applies event deltas to
a fresh loaded initial state and reports checksums and invariant violations
without writing the database.

This is debug data only, gated by `ENABLE_DEBUG_API`. It must never enter
player APIs or narrator prompts.

## World Branch / Diff System

v0.8 adds lightweight local world branching and structured diff. Branches are
copies of whitelisted world YAML under `worlds/.branches/{world_id}/{branch}`.
They do not copy `.env`, databases, logs, caches, or arbitrary files.

APIs:

- `GET /authoring/worlds/{world_id}/branches`
- `POST /authoring/worlds/{world_id}/branches`
- `GET /authoring/worlds/{world_id}/diff?other=...`
- `POST /authoring/worlds/{world_id}/diff-draft`

`WorldDiff` reports added, removed, changed, and potential renamed entities,
broken references, migration impacts, and visibility risks. Diff is
authoring-only and deterministic; it does not modify active `GameState`, does
not migrate active saves, and does not call the LLM.

## Scenario Regression Suite

v0.8 adds scenario regression cases and run reports for local regression
testing. A case contains a world id, input sequence, expected visible facts,
forbidden visible facts, expected quest states, expected inventory, max turns,
and tags.

APIs:

- `GET /scenarios/regression`
- `POST /scenarios/regression/run`
- `GET /scenarios/regression/{run_id}`

The API is gated by playtest/eval/debug configuration. Runs use mock/local
providers through the normal game loop or test harness, do not modify real
user saves, and redact hidden fact text from reports.

## Prompt Profile Manager

v0.8 documents and exposes prompt profile management for local provider/model
preferences. `PromptProfile` can configure provider/model filters, narrator
style, prompt variants, temperature overrides, and optional output token
limits.

Prompt profiles cannot widen LLM authority. Validation rejects profiles that
try to request hidden facts, NPC secrets, raw `GameState`, raw `state_deltas`,
or direct `GameState` writes. Profiles may adjust style and variants only;
they do not change visible facts, narrator-safe memory filtering, provider
factory boundaries, or rule outcomes.

## Save Migration System

v0.6+ formalizes save migration. Save metadata includes engine/schema/content
version fields and migration history. `GameState` also carries a
`schema_version`.

Migration APIs and CLI support:

- list available migrations
- migration status
- dry-run migration
- apply migration with backup

Migration is deterministic, does not call the LLM, does not drop `EventLog`,
and must not change hidden/debug visibility classifications. Failed migration
rolls back rather than overwriting the original save.

## Save Migration UI

v0.7 exposes migration status, dry-run, apply, and history in the Save Browser.
The UI uses existing migration APIs and does not return or display raw hidden
save payloads. Applying migration requires confirmation. Dry-run is clearly
marked as non-writing.

## Visual Relationship and Faction Graphs

v0.6+ adds graph response schemas and APIs for relationship/faction inspection:

- player graph endpoints return player-visible nodes/edges only
- debug graph endpoints return fuller graph data only when debug API is enabled
- graph generation is deterministic and does not infer hidden relationships

The frontend renders these as lightweight lists/SVG summaries. Debug graphs
must remain in the debug panel.

## Mod Manager UI

v0.7 adds a local Mod Manager panel backed by authoring-gated mod endpoints.
It can list discovered content-only mods, show manifest fields, validate a
mod, display dependency/conflict/version status, show deterministic load order,
and display migration notes. It does not enable online downloads, does not
execute scripts, and does not hot-reload active saves.

## Automated Playtesting Agents

v0.6+ adds local playtesting agents:

- `random_valid_action_agent`
- `explore_agent`
- `quest_following_agent`
- `stress_agent`

Agents receive `VisibleStateResponse` and return player input text. The runner
sends that text through `GameLoop`, records events, checks invariants, and can
exercise save/load. Agents do not directly mutate `GameState` and do not call
real LLM APIs.

## Automated Playtesting Dashboard

v0.7 adds playtest APIs and a local dashboard:

- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`

The API is controlled by `ENABLE_PLAYTEST_API` or debug mode. Reports include
turns run, actions taken, errors, invariant violations, visibility leak
summaries, save/load failures, and safe final state summaries. Reports are
studio/debug artifacts and must not enter player narration.

## Narrative Quality Evals

Narrative quality evals are deterministic test/eval utilities. They check
whether a `NarrativeResult` contradicts the `ActionResult`, invents key content,
leaks hidden facts/witnesses, becomes too long, omits visible consequences, or
suggests illegal actions. They do not use an external LLM judge.

## Narrative Quality Dashboard

v0.7 adds local eval report APIs and a dashboard:

- `GET /evals/narrative/recent`
- `POST /evals/narrative/run`
- `GET /evals/narrative/{run_id}`

The current routes are debug-gated. Reports include run ids, timestamps, pass
counts, failure reasons, categories, and safe case summaries. They do not
modify `GameState`, do not call real model APIs, and must not display hidden
fixture text in ordinary UI.

## Performance Instrumentation

v0.6+ adds local performance samples for game loop stages, save/load,
memory search, and authoring validation. Samples are in-memory, controlled by
`ENABLE_PERF_LOGGING`, and exposed only through debug performance APIs gated by
`ENABLE_DEBUG_API`.

Performance data must not include prompt text, API keys, hidden fact text, raw
`GameState`, or raw `state_deltas`. Performance work must never bypass
`StateDelta`, `EventLog`, visibility, schema validation, or rule correctness.

## Performance Dashboard

v0.7 exposes the local performance samples in a dashboard. It shows recent
samples and summaries for game loop, intent parsing, action resolution, world
tick, narrator, save/load, memory search, and authoring validation when data is
available. The dashboard is debug-gated, local-only, and must not display
prompt text, hidden content, API keys, raw `GameState`, or raw
`state_deltas`.

## Plugin / Mod Packaging

The engine includes a content-only mod packaging layer. A v0.6+ mod manifest can
describe:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `content_schema_version`
- `dependencies`
- `optional_dependencies`
- `conflicts`
- `load_order_hint`
- `compatible_worlds`
- `migration_notes`
- `entry_worlds`
- `content_paths`
- `author`
- `description`

Mods may contain YAML content packs only. The loader does not execute Python,
JavaScript, shell scripts, or arbitrary code. It rejects paths outside the mod
directory and validates entry worlds through the same content validation path.

Dependency, conflict, engine-version, content-schema, and load-order checks are
simple and deterministic in v0.7. There is no online download, SAT solver, hot
reload of active saves, or arbitrary script execution.

Known limitation: some invalid mod manifest errors may include local file
paths in diagnostics. Keep mod validation local until path sanitization is
tightened further.

## Desktop Packaging Prototype

v1.0 keeps desktop packaging as a local launcher prototype and hardens the
launcher scripts. The Windows and shell scripts check dependencies, ports,
`DATABASE_URL`, `.env` guidance,
start the FastAPI backend and Vite frontend or built preview, print safe local
status, run `/health` and `/studio/status` checks, and open the browser. This
is not a formal installer, does not sign code, does not auto-update, does not
sync to cloud, and does not embed `.env` or API keys into frontend assets.

## Local Model Provider Full Integration

v1.0 keeps the configurable local provider integration:

- `local_stub`: deterministic test/offline provider
- `local_http`: OpenAI-compatible local HTTP chat endpoint integration

`local_http` uses `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`,
`LOCAL_LLM_TIMEOUT_SECONDS`, and `LOCAL_LLM_JSON_MODE`. It still goes through
`LLMProvider`; outputs are schema-validated for JSON calls and have no new
authority. Local model output cannot directly modify `GameState`.

## Multi-world Save Browser

Save listing supports world filtering, updated-time ordering, deletion, and
safe summaries. A save summary may include:

- save id
- world id
- world name
- turn
- current location name
- formatted time
- created and updated timestamps
- optional player summary

Save summaries must not include raw `GameState`, hidden facts, raw
`state_deltas`, debug memory, or API keys.

## Debug Timeline

Debug timeline APIs are controlled by `ENABLE_DEBUG_API` and are for local
development only. They expose event timelines and `state_deltas` for debugging.
This data must remain separated from player APIs and narrator prompts.

## v1.0 Quality And Automated Playtesting Layer

v1.0 stabilizes the local quality-analysis layer on top of the visual authoring
studio. These tools inspect content packs, event timelines, playtest reports,
scenario regression output, save/migration behavior, and performance samples.
They produce safe reports for authors; they do not modify active `GameState`,
active saves, or world-pack YAML unless a separate authoring save flow is used.

The common report format is `WorldQualityReport`:

- `run_id`, `world_id`, `created_at`
- engine, schema, and content-pack version metadata
- `categories`
- `metrics` as structured `QualityMetric` records
- `issues` as structured `QualityIssue` records
- `summary`
- `recommended_actions`

`QualityIssue` supports `info`, `warning`, `error`, and `blocker` severities.
Normal reports use `safe_details`; hidden or sensitive diagnostic material must
stay in `hidden_details_debug_only` and must only be exposed through explicitly
debug/local-only surfaces. Normal quality reports must not include hidden fact
text, NPC secrets, hidden witnesses, raw `GameState`, raw `state_deltas`, API
keys, raw environment variables, or local sensitive paths.

Current v1.0 quality modules include:

- Automated Playtesting Scenario Expansion: deterministic scenarios for
  exploration, quest paths, combat, stealth, economy, crime/social behavior,
  save/load, migration, and hidden-leak probes.
- Scenario Regression Authoring UI: local authoring of regression cases stored
  in controlled scenario files, with preview/validate/save flows.
- Hidden Information Leak Regression Suite: pytest evals for player API,
  narrator context, memory context, graphs, maps, shops, quest state, reports,
  and quality output.
- Quest Completion Analysis: static and scenario/playtest-assisted analysis of
  missing stage refs, missing trigger refs, unreachable stages, completion
  paths, circular paths, and hidden quest visibility risks.
- Dead-End / Unreachable Objective Detector: pragmatic checks for unreachable
  required items/NPCs/facts, locked paths without access, undiscoverable clues,
  and quest blockers.
- NPC Behavior Coverage Report and NPC Schedule Conflict Detector: coverage and
  conflict analysis for NPC goals, schedules, planning actions, reactions,
  rumor/crime participation, and quest-required availability.
- Economy Balance Sanity Checks: non-authoritative checks for negative prices,
  arbitrage risk, shop references, hidden shop inventory, reward outliers, and
  extreme price modifiers.
- Combat Balance Sanity Checks: non-authoritative checks for lethal dead ends,
  missing non-lethal paths, critical NPC death without fallback, public combat
  consequence gaps, and unresolved status effects.
- Faction / Rumor / Crime Consequence Coverage: checks for missing references,
  untriggerable consequences, dedupe risks, faction effects, and hidden fact
  leakage in social systems.
- Save / Load / Migration Stress Tests: deterministic temporary-DB scenarios
  for many turns, save/load cycles, migration dry-run/apply, save-bundle
  import/export, replay dry-run, and hidden-safe reporting.
- Performance Benchmark Suite: local benchmarks for game loop, world tick,
  save/load, migration dry-run, validation, map/quest graph conversion, memory
  search, and scenario regression.
- Narrative Consistency Evals: deterministic evals for contradictions with
  `ActionResult`, `visible_state`, timeline, NPC knowledge, quest state, and
  memory authority.
- World Health Score Dashboard: a heuristic dashboard that aggregates quality
  reports into structure, reachability, secrecy, continuity, balance, coverage,
  performance, and migration-safety dimensions. It is not an absolute quality
  judgment.
- Content Coverage Dashboard: safe coverage summaries for locations, NPCs,
  items, quests, facts, factions, rumors, crimes, combat, and trade.
- Branch Diff Regression Testing: selects relevant regression cases from a
  `WorldDiff` and runs them in temporary sessions.
- Mod Compatibility Stress Testing: checks mod combinations without executing
  code or modifying original world/mod files.
- Automated Playtest Batch Runner: deterministic batch execution across
  scenarios, agents, and seeds, with aggregate safe reports.
- Quality Gate CLI / API: runs a configured local gate over validation,
  hidden-leak checks, quest/dead-end/NPC/economy/combat/social analyses,
  stress tests, benchmarks, scenario regression, and mod compatibility smoke
  checks.

Quality tools are local development tools. They must not call real LLM APIs by
default, must use mock/local-stub providers in tests, and must not make the LLM
the pass/fail judge. The quality gate uses deterministic code, thresholds, and
report severities.

## v1.1 Roleplay Immersion Layer

v1.1 adds a Roleplay Immersion Layer for character voice, dialogue continuity,
group scenes, local Tavern-like imports, and RP-specific regression checks. It
does not change the core authority model: `GameState`, `StateDelta`, `EventLog`,
visibility, NPC knowledge, and deterministic rules remain the fact layer. RP
features may change expression style, tone, scene mood, and safe dialogue
context; they must not create facts, complete quests, decide combat, reveal
hidden information, or let model output directly mutate state.

### Roleplay Boundary

`docs/ROLEPLAY_BOUNDARY.md` defines the v1.1 RP boundary terms:

- `authoritative_fact`
- `visible_fact`
- `npc_known_fact`
- `narrator_safe_memory`
- `rp_flavor`
- `emotional_expression`
- `prohibited_fact_creation`
- `debug_only_context`

`RoleplayContextPolicy` is the shared policy object used by RP context builders
and consistency checks. It permits voice, sentence style, emotional expression,
relationship atmosphere, and scene mood. It prohibits critical item/NPC/location
creation, task completion, knowledge changes, relationship-value changes,
dead-character contradiction, hidden fact leakage, and `ActionResult` override.

### Character Card Importer

Character card import is local authoring only. APIs:

- `POST /authoring/characters/import/preview`
- `POST /authoring/characters/import/validate`
- `POST /authoring/characters/import/apply`

The importer accepts JSON, YAML, simple text cards, and Tavern-like fields such
as `name`, `description`, `personality`, `scenario`, `first_message`,
`example_dialogue`, `creator_notes`, and `system_prompt`. It returns candidates:

- `rp_profile_candidate`
- `voice_profile_candidate`
- `example_dialogue_candidate`
- `flavor_lore_candidate`
- `structured_fact_candidate`
- `hidden_fact_candidate`
- `unsafe_or_unsupported_entries`

Preview and validation do not write disk. Apply requires `confirm_save=true`,
uses authoring validation, and writes content only through the authoring
service. The importer rejects remote URLs and script-like payloads. External
`system_prompt` and `creator_notes` are treated as untrusted and unsafe when
they attempt to override world or prompt authority.

### RP Profile And Voice Profile

NPCs may now include `rp_profile`, `voice_profile`, `dialogue_style`,
`speech_habits`, `taboo_topics`, `emotional_mask`, and
`example_dialogue_refs`. Safe voice fields can enter dialogue context. Hidden or
authoring-only profile fields, especially `private_self_summary`, do not enter
player-facing prompts by default.

`RPProfile` controls persona and expression preferences. `VoiceProfile` controls
tone, sentence length, vocabulary style, catchphrases, speech habits, silence
style, and emotional tells. These profiles are expression data only. They do
not change NPC knowledge, relationship values, `ActionResult`, quest state, or
visibility.

### NPC Emotional State

`EmotionalState` tracks a small structured emotional layer on NPC state:

- `primary_emotion`
- `intensity`
- `stability`
- `stress`
- `trust_tone`
- `fear_tone`
- `affection_tone`
- `last_emotional_event_id`
- optional `expires_turn`

Emotion rule helpers can derive shifts from events, apply shifts, decay emotion,
and summarize emotion for dialogue. Emotional changes are rule outcomes and
must go through `StateDelta` and events. The LLM may express emotion in text but
cannot write `emotional_state`.

### Relationship Tone

`RelationshipTone` derives an expression layer from existing relationship
values, faction reputation, emotional state, and recent event tags. It includes
address style, formality, warmth, tension, intimacy, respect, resentment, fear,
avoidance, and trust expression.

Relationship tone only affects prompt style summaries. It does not directly
modify `RelationshipState`; relationship value changes still require normal
rules and `StateDelta`. Hidden relationships must not enter player-visible
graphs or dialogue prompts.

### Dialogue Mode

Dialogue Mode adds structured `DialogueSession` records and a `DialogueManager`.
APIs:

- `POST /game/dialogue/start`
- `POST /game/dialogue/continue`
- `POST /game/dialogue/end`

A dialogue session stores participants, focus NPC, turn range, dialogue mode,
active topics, safe context summary, and status. Dialogue context is built from
player-visible facts, NPC-known facts, safe voice/profile fields, relationship
tone, emotional state, prompt-safe example dialogue, scene mood, and safe RP
memory. NPCs cannot receive facts they do not know.

Dialogue may produce rule-authorized consequences such as relationship deltas,
emotional shifts, quest triggers, fact reveals, or rumor hearing. Those changes
are decided by code, emitted as `StateDelta`, and recorded as events. LLM text
cannot directly decide them.

### Multi-NPC Scene / Group RP

Group RP uses `GroupDialogueScene` and `GroupDialogueManager`. APIs:

- `POST /game/group-dialogue/start`
- `POST /game/group-dialogue/next-speaker`
- `POST /game/group-dialogue/end`

Each participant gets an independent context based on that NPC's knowledge,
emotion, relationship tone, and visibility. Group scenes record events and use a
deterministic next-speaker rule. Dead or incapacitated NPCs do not participate
in ordinary group chat. Group RP is not an autonomous multi-agent simulator and
does not let NPC contexts share hidden facts.

### Scene Mood Presets

Content packs may define `scene_moods.yaml` with `SceneMoodPreset` entries.
Mood presets can influence tone, pacing, sensory focus, metaphor style,
dialogue pressure, and intensity range. They are style controls only: they do
not modify `GameState`, `ActionResult`, hidden fact filtering, or prompt safety.

Dialogue Mode and Group RP can select a mood preset, and prompt profiles may
reference safe mood settings. Invalid presets are caught by validation.

### Lorebook Import / Classification

Lorebook import is local authoring only. APIs:

- `POST /authoring/lorebook/import/preview`
- `POST /authoring/lorebook/import/validate`
- `POST /authoring/lorebook/import/apply`

`LorebookClassifier` parses JSON, YAML, or text entries and classifies them as:

- `flavor_lore`
- `structured_fact_candidate`
- `hidden_fact_candidate`
- `unsafe_entry`

Flavor lore can become safe style/context. Structured facts must be written to
content packs before becoming authoritative. Hidden fact candidates remain under
visibility control. Unsafe prompt/control entries are quarantined and cannot
enter prompts. The importer does not execute instructions, read remote URLs, or
modify active `GameState`.

### Example Dialogue Manager

Example dialogue entries are authoring content used to guide voice. They do not
become `GameState` facts and do not add NPC knowledge. APIs:

- `GET /authoring/worlds/{world_id}/example-dialogue`
- `POST /authoring/worlds/{world_id}/example-dialogue/preview`
- `POST /authoring/worlds/{world_id}/example-dialogue/validate`
- `PUT /authoring/worlds/{world_id}/example-dialogue`

Only `prompt_safe` entries with safe fact policy can enter dialogue context.
Entries marked `authoring_only`, `debug_only`, or `unsafe` stay out of runtime
prompts. Hidden fact references are filtered unless the relevant facts are
visible and known according to normal rules.

### RP Memory Context Builder

`RPMemoryContextBuilder` builds RP-safe memory lists for a speaker and player:

- `speaker_safe_memories`
- `player_visible_shared_memories`
- `relationship_memories`
- `recent_dialogue_memories`
- debug-only `excluded_memory_reasons`

It filters hidden memory, debug-only memory, memory tied to unknown facts, and
memory tied to currently invisible hidden facts. Memory remains non-authoritative
and cannot override `GameState`.

### RP Prompt Profile Manager

v1.1 extends `PromptProfile` with `RPPromptProfile` fields for RP style:
dialogue depth, emotional intensity, prose density, response length,
perspective, inner thought policy, and optional sensuality style policy. The
boundary fields are fixed:

- `hidden_fact_policy=deny`
- `state_modification_policy=deny`

Validation rejects profiles that try to widen authority. RP prompt profiles may
change style only; they cannot change visible facts, NPC knowledge,
`ActionResult`, `StateDelta`, or quest state.

### RP Output Consistency Checker

`RPOutputConsistencyChecker` checks generated RP text against the safe dialogue
context. It can flag hidden fact leakage, NPC unknown-fact mentions, invented
key items/NPCs/locations, dead NPCs speaking, contradictions with
`ActionResult`, unauthorized relationship change, unauthorized quest completion,
and raw debug/state-delta leakage.

The checker does not use an external LLM judge and does not modify state. On
serious violations it can reject output, request retry, or fall back to a safe
summary.

### Tavern Compatibility Import / Export

Tavern-like compatibility APIs:

- `POST /authoring/tavern/import/preview`
- `POST /authoring/tavern/import/apply`
- `POST /authoring/tavern/export`

Supported import resources are character cards, lorebook/world info, example
dialogue, and prompt presets. Import always goes through parse, classification,
unsafe detection, preview, explicit apply, and validation. It rejects path
traversal in source names, remote URL references, and script-like payloads.

Safe export supports character-like cards, safe lorebook export, and prompt
profile export. Safe mode excludes API keys, raw `GameState`, save data, and
hidden facts. Authoring/debug export modes must remain local and warned.
Compatibility is practical and best-effort; it is not a promise that every
external Tavern format is fully supported.

### RP Scenario Templates

RP scenario templates live under `templates/rp/` and create dialogue or group
scene drafts. APIs:

- `GET /authoring/rp-scenario-templates`
- `GET /authoring/rp-scenario-templates/{template_id}`
- `POST /authoring/rp-scenario-templates/{template_id}/preview`
- `POST /authoring/rp-scenario-templates/{template_id}/apply`

Templates can specify scene type, required/optional participants, suggested
mood, suggested dialogue mode, opening context, allowed/forbidden topics,
required visible facts, and safety notes. They do not call the LLM, do not
modify active saves, and cannot expand NPC knowledge or hidden fact access.

## v1.3 Advanced NPC Simulation

v1.3 adds bounded NPC autonomy under the same local world-engine authority
model. NPC simulation is deterministic rule code, not LLM multi-agent
simulation. NPCs can choose from finite rule-defined behavior, but they cannot
read unknown facts, cannot directly mutate `GameState`, cannot call external
network services, and cannot bypass `StateDelta` or `EventLog`.

### NPC Simulation Boundary

`docs/NPC_SIMULATION_BOUNDARY.md` defines the contract and
`backend/app/engine/rules/npc_simulation_boundary.py` implements
`NPCSimulationPolicy`. The main concepts are:

- `npc_known_context`: public facts plus facts, rumors, and crimes actually
  known by that NPC.
- `npc_visible_context`: local visible entities from visibility rules, not raw
  state.
- `npc_private_state`: mood, condition, current goal/activity, and plan-state
  keys.
- `simulation_candidate_action`, `simulation_intent`, `simulation_plan`, and
  `simulation_event`.
- `debug_only_simulation_data`: local diagnostics that must stay behind debug
  APIs.

The policy checks inactive/dead NPCs, allowed action types, unknown required
facts, finite plan size, and event/delta requirements. It is read-only: it
does not apply deltas, write disk, or call the LLM.

### NPC Intent Queue

`NPCIntent` entries live on `NPCState.intent_queue`. They contain id, NPC id,
intent type, priority, status, optional source event/goal, optional target,
created/expiry turn, preconditions, and a debug-only reason.

`npc_intents` provides enqueue, cancel, complete, fail, select, and prune
helpers. Queue changes return `StateDelta` entries and system events.
Selection is deterministic by priority and turn, and ordinary selection returns
no intent for dead, incapacitated, or stunned NPCs. Fact, rumor, and crime
preconditions are checked against the NPC's scoped knowledge.

### NPC Short-Term Plans

`NPCPlan` entries live on `NPCState.plans`. A plan links to a source intent,
has a status, finite `NPCPlanStep` list, current step index, creation turn, and
optional expiry turn.

`npc_plans` converts intents into whitelisted steps such as move, talk, report,
spread rumor, rest, guard, avoid, and seek item. Plans are validated against
targets and NPC knowledge. Advancing a plan delegates executable effects to the
existing rule/action resolver and returns `StateDelta` plus events; plans do
not directly write state.

### NPC Memory-Based Reactions

`npc_memory_reactions` accepts candidate `MemoryRecord` values and
`NPCMemoryReactionRule` rules. It can remember events, avoid/seek actors,
report known crimes, spread known rumors, increase suspicion, soften tone,
refuse talk, or enqueue an intent.

Hidden and debug-only memory is filtered out. Memories tied to facts, rumors,
or crimes unknown to the NPC are skipped. Reactions produce finite deltas and
events, and dedupe markers in `social_flags` prevent infinite repeat firing.

### NPC Relationship-Driven Behavior

`npc_relationship_behavior` uses `RelationshipState`, relationship tone,
known facts, known rumors, emotional state, and faction-duty inputs to produce
bounded behavior such as help, warn, avoid, report, lie, withhold information,
share known rumor, or seek reconciliation.

Outputs are intents, plan candidates, `StateDelta`, and events. Hidden
relationships remain filtered from player graphs, and unknown facts/rumors do
not become behavior inputs.

### NPC Faction Duties

`NPCFactionDuty` entries live on `NPCState.faction_duties`. Supported duty
types include guard location, patrol route, report crime to faction, protect
faction member, refuse hostile actor, spread faction rumor, seek information,
and enforce curfew.

`npc_faction_duties` filters duties by life state, faction membership, target
validity, known facts, known rumors, and known/witnessed crimes. Duties produce
intents or plan candidates through existing systems and record events; they do
not run large-scale war or diplomacy simulation.

### NPC Rumor Decisions

`npc_rumor_decisions` defines `NPCRumorDecision` and deterministic decisions:
keep secret, share with actor, share with faction, distort, ignore, report, or
enqueue a spread-rumor intent.

The NPC must already know the rumor. Decision inputs include relationship
trust, faction alignment, secrecy tags, source credibility, and emotional
intensity. The system does not call the LLM to rewrite rumors and does not
expose hidden fact truth text as player-facing rumor text.

### NPC Fear / Trust / Loyalty Models

`NPCSocialDisposition` lives on `NPCState` and tracks lightweight values such
as `trust_player`, `fear_player`, `loyalty_to_faction`,
`loyalty_to_npcs`, `moral_flexibility`, `risk_tolerance`,
`conflict_tolerance`, and `secrecy_preference`.

`npc_social_disposition` can derive values from relationships, update from
events through `StateDelta`, convert disposition into behavior weights, and
summarize it for dialogue tone. Disposition does not grant knowledge, override
relationship authority, or let LLMs write NPC psychology.

### NPC Conflict Avoidance

`npc_conflict_avoidance` creates finite avoid/flee/rest/help/hide/refuse
behavior based on emotional state, social disposition, combat/life state,
known crimes, visible hostile actors, location safety tags, and duties.

Hidden NPC avoidance stays system/debug-only unless the NPC is visible by
normal rules. Avoidance outputs intents or plans and relies on later rule
resolution for actual state changes.

### NPC Daily Goal Replanning

`npc_daily_replanning` runs bounded replanning on new day, major event, goal
completion/failure, schedule change, faction duty update, or injury/recovery.
It can reevaluate goals, clear expired intents, enqueue daily duties, adjust
priorities, and cancel impossible plans.

Replanning is deterministic, uses `StateDelta` and events, and skips ordinary
replanning for inactive NPCs.

### NPC Simulation Tick Orchestrator

`npc_simulation_tick` centralizes tick order:

1. prune expired intents
2. daily replanning
3. memory reactions
4. relationship behavior
5. faction duties
6. rumor decisions
7. conflict avoidance
8. select intent
9. build or advance plan

`NPCSimulationTickBudget` limits NPCs per tick, intents per NPC, plan steps,
and event count. `run_npc_simulation_tick` applies returned deltas only to an
internal working copy during orchestration, returns the final deltas/events to
the caller, and prevents unbounded loops.

### NPC Simulation Debugger And Behavior Timeline

Debug APIs are local-only and gated by `ENABLE_DEBUG_API`:

- `GET /debug/sessions/{session_id}/npc-simulation`
- `GET /debug/sessions/{session_id}/npcs/{npc_id}/simulation`
- `GET /debug/sessions/{session_id}/npc-simulation/ticks`
- `POST /debug/sessions/{session_id}/npc-simulation/dry-run-tick`
- `GET /debug/sessions/{session_id}/npcs/{npc_id}/behavior-timeline`
- `GET /debug/saves/{save_id}/npcs/{npc_id}/behavior-timeline`

The debugger can show intent/plan counts, known ids, hidden fact ids, goals,
emotional/social state, faction duties, known rumors/crimes, and redacted
debug reasons. Dry-run tick does not write the database or mutate active
state. Behavior timeline is debug-only and returns safe summaries plus
redacted debug reasons; it must not be used as narrator input.

### NPC Simulation Authoring Presets

NPC simulation presets are authoring-draft helpers. APIs:

- `GET /authoring/npc-simulation-presets`
- `POST /authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/preview`
- `POST /authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/apply-draft`

Built-in presets include guard, merchant, informant, hostile actor, timid
villager, loyal subordinate, rumor spreader, and investigator. Presets can
apply goals, intent priorities, faction duties, relationship behavior metadata,
rumor tendencies, social disposition defaults, and conflict avoidance defaults
to an NPC authoring draft. They go through validation and do not modify active
`GameState`, execute scripts, or grant unknown facts.

### NPC Simulation Quality Evals

`npc_simulation_quality` produces `NPCSimulationQualityReport` and integrates
with the Quality Gate / World Health source report path. It checks unknown
fact usage, hidden fact leaks, repeated intent loops, blocked plan loops, dead
NPC actions, invalid targets, missing events, too many intents, plan budget
overruns, and low behavior coverage.

Reports are deterministic diagnostics. They do not modify saves, do not call
LLMs, and normal report dumps strip debug-only hidden details.

### NPC Simulation Regression Playtests

`npc_simulation_regression` defines deterministic regression scenarios such as
guard patrol, report crime, spread rumor, avoid player, seek help, daily
replan, relationship response, faction duty, and injured rest.

Runs use temporary SQLite storage and synthetic fixtures. They check expected
intents/events, forbidden intents/facts, plan failure limits, save/load
continuity, and quality reports. They do not call real LLM APIs and do not
modify real user saves.

## v1.4 Content Production Pipeline

v1.4 adds a local Content Production Pipeline for producing world packs, NPC
packs, quest packs, location clusters, mystery cases, faction templates,
script packages, campaign starter kits, batch imports, coverage plans, and
batch quality reports. These tools operate on production drafts, candidates,
packages, previews, and reports. They do not directly modify active
`GameState`.

### Content Production Boundary

`docs/CONTENT_PRODUCTION_BOUNDARY.md` defines the v1.4 boundary terms:

- `production_draft`
- `generated_content_candidate`
- `batch_import_candidate`
- `production_package`
- `package_manifest`
- `explicit_apply`
- `validation_required`
- `quality_required`
- `active_world_pack`
- `active_game_state`

Preview and validate operations do not write disk. Apply/build operations
require explicit confirmation and must pass validation; release/package flows
use the relevant Quality Gate or Batch Quality Gate. Batch import defaults to
dry-run review. Packages are data only and must not execute scripts, fetch
remote URLs, read `.env`/API keys/databases/logs/system files, or overwrite
user worlds automatically.

The shared policy module is
`backend/app/engine/content/content_production_boundary.py`.

### World Pack Wizard

`WorldPackWizardDraft` creates a local world-pack draft from basic metadata,
genre/tone, starting location, seed counts, enabled systems, prompt profile,
and quality profile. It can preview generated files, validate them, and apply
to the worlds directory only after confirmation and validation gate approval.

Generated draft files include `manifest.yaml`, `locations.yaml`, `npcs.yaml`,
`items.yaml`, `quests.yaml`, `facts.yaml`, and optional faction/rumor content.
The wizard does not modify active sessions and defaults to deterministic local
generation; `llm_assisted` is reserved metadata and is not a real-provider call
path in the current implementation.

### NPC Pack Generator

`NPCPackGeneratorDraft` produces NPC candidates, RP profile drafts, voice
profile drafts, relationship candidates, goal candidates, and schedule
candidates for a target world. Inputs include pack id, theme, faction ids,
location ids, NPC count, archetypes, RP style, simulation preset ids,
relationship density, and hidden-secret ratio.

Preview and validation are dry-run. Apply writes candidate content only through
the authoring service after confirmation and validation. Hidden secrets are
marked hidden and are not player-facing fields. Character pack export uses the
safe package path and must not include API keys.

### Quest Pack Generator

`QuestPackGeneratorDraft` produces quest candidates, fact candidates, optional
rumor/consequence candidates, scenario regression candidates, and a quest graph
draft. It validates referenced NPCs, locations, factions, and facts before
producing YAML. Hidden fact candidates remain hidden and player-facing quest
text is checked for hidden leaks.

The generator does not publish quests to active saves and does not call an LLM
by default. Generated quest quality is structural rather than literary.

### Location Cluster Templates

`LocationClusterTemplate` defines reusable local map fragments with required
variables, location nodes, exit edges, optional hidden edges, default visual
layout, and tags. APIs list templates, preview a rendered `MapVisualGraph`,
and apply the rendered cluster to a world draft after validation.

Hidden edges are marked hidden and do not become player map exits unless later
revealed by normal map/visibility rules. The system does not attempt complex
automatic layout.

### Mystery Template System

`MysteryTemplate` produces structured mystery drafts: hidden truth fact,
suspects, clues, red herrings, witness statements, reveal/failure conditions,
required locations/NPCs, fact drafts, NPC knowledge drafts, questline drafts,
rumor drafts, evidence item drafts, and scenario regression drafts.

The truth fact must be hidden. Red herrings are explicitly marked. Normal
preview/report fields avoid revealing hidden truth text. The implementation is
deterministic and focuses on safe structure, not literary quality.

### Faction Template System

`FactionTemplate` produces faction drafts, relation drafts, NPC faction duty
candidates, relationship candidates, and quest hook candidates. It supports
default reputation, relations, duties, ranks, archetypes, rumor policies, crime
policies, quest hooks, hidden flag, and tags.

Hidden factions and hidden relations are authoring data and must not enter the
player-visible faction graph until revealed by normal rules. The template
system does not implement war simulation or diplomacy AI.

### Content Batch Validator

`ContentBatchValidationRequest` and `ContentBatchValidationReport` validate
multiple local targets: world packs, character packs, quest packs, template
packs, mod packages, and script packages. Reports aggregate total, passed,
warning, failed, blockers, per-package reports, and aggregate issues.

The validator does not execute package code, does not call LLMs, rejects path
traversal, and keeps hidden details redacted in normal reports.

### Content Coverage Planner

`ContentCoveragePlan` is a rule-based planning report for missing location
types, NPC archetypes, quest types, clue paths, faction hooks, RP scenes,
scenario regressions, and playtest paths. It uses current coverage input and
safe world summaries to recommend authoring work. It does not generate or
write content.

### Export / Import Profiles

`ExportProfile` controls whether exports include worlds, characters,
templates, scenarios, prompt profiles, hidden authoring data, quality reports,
and test fixtures. Safe export defaults redact hidden text and forbid API
keys.

`ImportProfile` controls overwrite policy, hidden authoring data, validation,
quality gate, migration check, executable rejection, and unknown schema
rejection. Import profiles must require validation, reject executables, and
forbid API keys.

### Local Content Library Pro

Local Content Library Pro extends local content management with search,
filtering, tags, inspection, validation, batch validation, export/import with
profiles, dependency summaries, quality summaries, duplicate/archive helpers,
and editor links. Supported content types include worlds, character packs,
quest packs, NPC packs, template packs, scenario suites, prompt profiles, RP
profiles, mods, script packages, and campaign starters.

Normal library responses avoid sensitive absolute paths and hidden details.
The library does not download remote content or execute packages.

### Batch Character Card Import

Batch character card import accepts multiple local cards, safe zip inputs, or
pasted JSON/YAML text. Each entry uses the existing Character Card Importer
and reports parsed, failed, unsafe, duplicate names, candidate characters,
unsafe entries, and a character pack draft.

It rejects zip slip/path traversal, does not fetch remote URLs, does not
execute card content, and does not write active worlds automatically.

### Batch Lorebook Classification

Batch lorebook classification accepts one or more local lorebooks or safe zip
inputs and classifies entries as flavor lore, structured fact candidates,
hidden fact candidates, or unsafe entries. It reports duplicate keys and
prompt-injection warnings.

Hidden fact text stays out of normal reports unless an explicitly local debug
view is used. Applying entries requires explicit selection and validation.

### Script Package Builder

`ScriptPackageManifest` describes local script packages with package id, name,
version, target engine/schema versions, included worlds/quests/characters/
templates/scenarios, quality profile, dependencies, conflicts, checksums,
created time, and normal-manifest mode.

Despite the name, script packages are data packages. The builder supports
dry-run, validation, build/apply, and zip export; it rejects executable files,
`.env`, API keys, databases, logs, and hidden fact text in normal manifests.

### Campaign Starter Kit Builder

`CampaignStarterKitDraft` composes a small playable starter from a world-pack
draft, NPC pack draft, quest pack draft, faction draft, optional mystery draft,
scenario regression suite, quality gate config, and script package draft.

Preview does not write disk. Build requires validation and quality dry-run.
The builder does not create a complete long campaign, call a real LLM by
default, execute scripts, or modify active `GameState`.

### Production Pipeline Dashboard

`ProductionPipelineSummary` powers the local dashboard for active production
drafts, recent generated packages, batch validation status, content coverage
plan, quality gate summary, import/export profile status, script package build
status, and campaign starter status.

The API is local authoring-only, guarded by `ENABLE_AUTHORING_API`, and returns
redacted summaries rather than raw hidden facts or secrets.

### Content Production CLI

`python -m backend.app.tools.production` exposes local commands for:

- `world-wizard`
- `npc-pack`
- `quest-pack`
- `batch-validate`
- `build-script-package`
- `campaign-starter`
- `coverage-plan`
- `batch-quality-gate`

The CLI reuses service-layer code. Preview is the default safe path. Apply/build
requires explicit flags. Output can be human-readable or JSON and redacts API
keys, raw environment values, hidden/private fields, and package archive
payloads.

### Batch Quality Gate

`BatchQualityGateRequest` and `BatchQualityGateReport` run deterministic
release/export checks across multiple worlds or packages. Reports include
pass/fail, blockers, warnings, per-item results, aggregate summary, and
recommended actions. The gate does not modify content, call real LLMs, upload
reports, or expose hidden fact text in normal output.

Known v1.0 implementation note: `ENABLE_PLAYTEST_API`, `ENABLE_EVAL_API`,
`ENABLE_DEBUG_API`, and `ENABLE_PERF_LOGGING` gate the main playtest, eval,
debug, benchmark, and quality-gate flows. There is currently no separate
`ENABLE_QUALITY_API` setting. Some analyzer endpoints are local-only but not
all have an independent feature flag yet; keep the backend bound to localhost
and do not expose quality APIs as a hosted service.

## Current Limits

- No account system, cloud sync, or remote publishing.
- No formal desktop installer.
- No complex drag/drop IDE or multiplayer authoring workflow.
- No automatic YAML repair.
- No arbitrary mod code execution.
- No online mod download or complex mod version solver.
- No large-scale social simulation, diplomacy AI, or war simulation.
- No external vector database requirement.
- No external LLM judge in evals.
- No production APM/telemetry; performance samples remain local.
- Quality reports and health scores are heuristic authoring aids, not absolute
  design judgments and not canonical world facts.
- Quality, eval, benchmark, and playtest APIs are local-only tools, not
  production or hosted-service endpoints.
- NPC planning is limited to deterministic candidate actions.
- Procedural side quests are drafts only.
- Content production generators are drafts/packages only.
- Batch import and package build require dry-run/validation/explicit apply
  semantics and must not modify active runtime sessions.
- v1.4 does not provide online marketplace, remote download, script execution,
  background production jobs, or automatic long-form campaign writing.
- Memory retrieval is context support, not canonical truth.

## v1.5 Local Model & Prompt Lab

v1.5 adds a local Model & Prompt Lab for comparing and debugging providers,
models, prompt profiles, context construction, structured output reliability,
token budgets, latency, cost estimates, routing rules, and prompt experiment
packages.

The lab is diagnostic and evaluative. It produces reports, matrices,
diagnostics, usage summaries, diffs, and packages. It does not modify active
`GameState`, active saves, active content packs, or world facts.

The boundary contract lives in `docs/MODEL_PROMPT_LAB_BOUNDARY.md`.

### Provider Capability Registry

`ProviderCapabilityRegistry` records declared provider/model metadata:

- provider id and type
- text/JSON/streaming/tool/embedding support flags
- context window and max output hints
- recommended use cases
- local-only / requires-key flags
- cost and reliability metadata where known

The registry is metadata only. It does not call providers, probe networks,
validate real model availability, or expose API key values. Frontend summaries
may show booleans such as `api_key_configured`, but not secrets.

API:

- `GET /prompt-lab/provider-capabilities`

### Provider Benchmark Harness

`ProviderBenchmarkRun`, `ProviderBenchmarkCase`, and
`ProviderBenchmarkReport` compare provider behavior for safe local cases:

- text smoke
- JSON schema
- intent parser schema
- narrator style
- RP dialogue style
- memory summary schema
- hidden fact refusal
- latency smoke

Benchmarks default to fake/mock/local providers. Real provider runs require
explicit `allow_real_provider=true`. Reports use redacted prompt previews and
safe output summaries; they do not become world facts.

API / CLI:

- `POST /prompt-lab/providers/benchmark`
- `GET /prompt-lab/providers/benchmark/{run_id}`
- `python -m app.tools.prompt_lab benchmark-provider`
- `python -m app.tools.provider_benchmark`

### Prompt Profile A/B Test

`PromptABTestRun` compares two prompt profiles for narrator, RP dialogue,
intent parser, or memory summary use cases. It reports style metrics, schema
reliability, hidden leak flags, consistency flags, and latency/cost summaries.

Prompt profiles remain style/configuration only. They cannot set
`hidden_fact_policy` or `state_modification_policy` to anything other than
`deny`, cannot add facts, and cannot modify `GameState`.

API:

- `POST /prompt-lab/prompt-profiles/ab-test`
- `GET /prompt-lab/prompt-profiles/ab-test/{run_id}`

### Narrator Style Lab

`NarratorStyleExperiment` tests narrator style parameters such as prompt
profile, scene mood, perspective, prose density, response length, sensory
focus, and genre tone. Findings check hidden leaks, invented key items,
contradictions with the resolved `ActionResult`, concise output, style match,
and suggested action validity.

The lab does not change `ActionResult`, does not apply state changes, and does
not write narration into active play.

API:

- `POST /prompt-lab/narrator-style/run`
- `GET /prompt-lab/narrator-style/{run_id}`

### NPC Voice Style Lab

`NPCVoiceStyleExperiment` compares voice profile variants, RP prompt profiles,
and example dialogue sets for NPC voice consistency. Findings cover voice
consistency, catchphrases, emotional tone, unknown facts, hidden leaks,
relationship value invention, and quest completion invention.

Example dialogue remains style-only. The lab does not add NPC knowledge,
modify NPC state, or write dialogue into active sessions.

API:

- `POST /prompt-lab/npc-voice-style/run`
- `GET /prompt-lab/npc-voice-style/{run_id}`

### Structured Output Reliability Test

`StructuredOutputReliabilityRun` tests model JSON/schema reliability for
schemas such as `PlayerIntent`, `NarrativeResult`, `MemorySummary`,
`QuestDraft`, character card import, lorebook classification, and RP
consistency reports.

Metrics include valid JSON rate, schema valid rate, retry success rate,
invalid field rate, refusal/empty rate, and hidden-policy violation rate.
Failures produce safe reports and do not modify state.

API / CLI:

- `POST /prompt-lab/structured-output/run`
- `python -m app.tools.prompt_lab structured-output`
- `python -m app.tools.structured_output_reliability`

### Cost / Latency Tracker and Model Usage Dashboard

`ModelUsageRecord` and `CostLatencySummary` record safe usage metadata:

- provider/model/use case
- start time and duration
- estimated input/output tokens
- estimated cost
- success/failure and error type

Usage tracking is controlled by `ENABLE_USAGE_TRACKING`. It does not store raw
prompts, hidden fact text, raw `GameState`, raw `state_deltas`, or API keys.

APIs:

- `GET /prompt-lab/usage/recent`
- `GET /prompt-lab/usage/summary`
- `GET /prompt-lab/usage/by-use-case`

The frontend Model Usage Dashboard displays provider/use-case distribution,
latency p50/p95, estimated token/cost totals, error rate, and recent failure
metadata.

### Context Builder Inspector

`ContextSnapshot` and `ContextSection` show how narrator, dialogue, group RP,
intent parser, memory summary, and character import context is assembled.
Sections are classified as:

- `normal`
- `narrator_safe`
- `npc_known`
- `debug_only`
- `hidden_redacted`

Hidden facts and unknown NPC facts are shown as redacted/excluded sections.
Raw prompt output is disabled by default and, when explicitly requested for
local debug, is still redacted.

API:

- `POST /prompt-lab/context/inspect`

### Prompt Diff Tool

`PromptDiffRequest` and `PromptDiffReport` compare prompt profiles, RP prompt
profiles, context snapshots, or prompt templates. Reports include added,
removed, and changed sections, token delta, safety policy changes,
hidden-access policy changes, and state-modification policy changes.

Relaxing `hidden_fact_policy` or `state_modification_policy` is a blocker.
Reports do not show raw hidden text or API keys.

API:

- `POST /prompt-lab/prompt-diff/review`

### Model Compatibility Matrix

`ModelCompatibilityMatrix` combines declared capabilities, benchmark reports,
structured-output reliability, usage summaries, and hidden-leak findings to
mark provider/model/use-case pairs as supported, recommended, caution, or
unsupported.

The matrix is advisory. It does not call real APIs by itself, does not switch
models automatically, and does not expose hidden prompt cases.

APIs:

- `GET /prompt-lab/model-compatibility`
- `POST /prompt-lab/model-compatibility/recompute`

### Provider Routing Rule Editor

`ProviderRoutingRule` configures which provider/model to use for a use case,
plus fallback and constraints such as JSON support, local-only requirements,
latency/cost hints, and enabled state.

Routing rules do not contain API keys and do not expand model authority.
Business code still uses `LLMProvider` / provider factory paths. Routing is
configuration, not a world-rule authority.

APIs:

- `GET /prompt-lab/provider-routing`
- `POST /prompt-lab/provider-routing/validate`
- `POST /prompt-lab/provider-routing/preview`
- `POST /prompt-lab/provider-routing/save`

### Prompt Regression Suite

`PromptRegressionRun` compares baseline and candidate prompt/provider/model
settings for intent parser schema, narrator consistency, RP dialogue boundary,
NPC voice consistency, memory summary schema, hidden leak cases, and structured
JSON reliability.

Pass/fail is computed by deterministic checks and schema/eval results, not by
an LLM judge. Results are reports only and are not applied automatically.

API / CLI:

- `POST /prompt-lab/regression/run`
- `python -m app.tools.prompt_lab prompt-regression`
- `python -m app.tools.prompt_regression`

### Local Model Diagnostics

`LocalModelDiagnosticRequest` and `LocalModelDiagnosticReport` diagnose
`local_stub` or `local_http` providers for base URL configuration, optional
health check, text smoke, JSON smoke, timeout behavior, error parsing,
latency, and declared context window.

Diagnostics default to fake/local behavior. Real local checks require explicit
`allow_real_local_check=true`. Safe diagnostic prompts do not include world
facts or hidden facts.

API / CLI:

- `POST /prompt-lab/local-model/diagnose`
- `python -m app.tools.prompt_lab local-diagnostics`

### Token Budget Manager Pro

`TokenBudgetProfile`, `TokenBudgetRequest`, and `BudgetReport` estimate token
usage, allocate per-use-case budgets, trim low-priority context, and report
trimmed or dropped sections.

Safety/boundary/policy sections are protected. Hidden-redacted sections are
dropped rather than added to context. The manager is deterministic and does
not call an LLM.

APIs / CLI:

- `GET /prompt-lab/token-budget/profiles`
- `POST /prompt-lab/token-budget/estimate`
- `python -m app.tools.prompt_lab token-budget-report`

### Prompt Experiment Package

`PromptExperimentPackageManifest` packages prompt profiles, RP prompt
profiles, test cases, benchmark configs, regression configs, provider
requirements, and redaction policy for local reproducible experiments.

Exports reject API keys, raw env, hidden facts, raw `GameState`, raw
`state_delta`, sensitive prompt snapshots, executable files, and path
traversal. Imports validate first, dry-run by default, do not auto-enable
profiles, and do not modify active `GameState`.

APIs:

- `POST /prompt-lab/experiment-packages/export`
- `POST /prompt-lab/experiment-packages/import-dry-run`
- `POST /prompt-lab/experiment-packages/import-apply`

## v1.6 Advanced Gameplay Modules

v1.6 adds a local, declarative gameplay module layer. Modules can add
rule-driven actions and optional state fields, but they do not become trusted
code plugins. The runtime chain remains:

`ActionRegistry -> ActionHandler/rule module -> ActionResult -> StateDelta -> EventLog -> Visibility / NPC Knowledge`

The LLM may narrate an already resolved result. It does not decide action
success, damage, spell effects, hacking outcomes, crafting output,
deduction truth, social manipulation results, faction mission completion, or
domain income.

### Gameplay Module Boundary

`docs/GAMEPLAY_MODULE_BOUNDARY.md` defines the v1.6 boundary. The policy layer
in `app.engine.gameplay_modules` defines gameplay modules, action mods,
declarative actions, module state extensions, module event types, debug data,
affordances, and permissions.

Allowed module behavior:

- register actions through `ActionRegistry`
- declare affordances, preconditions, checks, effects, event types, and
  save-migration defaults
- return structured `ActionResult`, `StateDelta`, and `Event` values
- expose debug traces only through debug-gated APIs

Forbidden module behavior:

- arbitrary code execution
- direct `GameState` mutation
- direct database writes
- `.env`, API key, network, or arbitrary filesystem access
- LLM adjudication
- Visibility, NPC Knowledge, StateDelta, or EventLog bypass

### Gameplay Module Manifest

`GameplayModuleManifest` is loaded by `GameplayModuleLoader` from local
`gameplay_modules/{module_id}/module.yaml` style directories. It declares:

- id, name, version, module type, engine minimum, and schema version
- dependencies, conflicts, required systems
- provided actions and rules
- state schema extensions and event types
- permissions, all dangerous permissions defaulting to false
- save compatibility and migration defaults
- declared quality tests

The loader validates dependencies, conflicts, permissions, save compatibility,
safe identifiers, state schema extensions, executable-file rejection, and path
boundaries. Loading manifests does not execute module code.

### Declarative Action Mod System

`DeclarativeActionDefinition` describes new actions as data:

- id, label, aliases, category
- target specs and affordance requirements
- time cost
- preconditions and checks
- outcomes, state delta templates, event type
- visibility policy and narrator hints

`DeclarativeActionHandler` validates targets, evaluates conditions/checks,
selects an outcome, builds `StateDelta` values, and returns a structured
`ActionResult` plus `Event`. It never mutates `GameState` directly and never
calls the LLM.

### Action Registry Extension

The action registry now supports core and module actions through one surface:

- `register_core_action`
- `register_module_action`
- `unregister_module_action`
- `list_available_actions`
- `get_action_definition`
- alias conflict detection

Intent parsing and suggested actions can discover enabled module actions, but
disabled module actions cannot be invoked. Suggested module actions must still
be based on player-visible affordances.

### Action DSL Preconditions / Checks / Effects

The v1.6 Action DSL is a constrained schema, not an expression language. It
supports whitelisted preconditions such as actor location, target existence,
target visibility, item/status possession, tags, combat status, NPC known
facts, and fact visibility.

Checks include skill, reputation, relationship, item, deterministic random
threshold, and fixed success checks.

Effects compile to `StateDelta` values only. Supported effects include
state-delta templates, fact discovery, status changes, item consumption,
time advancement, and event markers. Path templates are validated against a
whitelist. The DSL performs no IO, imports, loops, reflection, script
execution, or LLM calls.

Known v1.6 audit note: `ADD_FACT_DISCOVERY` is powerful and must remain
covered by validation and hidden-leak tests so action mods cannot expose
hidden facts through `player_visible_facts` unless rules explicitly allow the
discovery.

### Action Mod Validation

`action_mod_validator` validates action ids, aliases, categories, target
specs, preconditions, checks, effects, StateDelta paths, event types,
visibility policies, hidden-output handling, dangerous permissions, and save
compatibility. It is called from module validation, authoring APIs, package
flows, and the module quality gate.

### Action Mod Authoring UI

The frontend Action Mod Editor is a local authoring tool for declarative
actions. It edits action fields, target specs, affordance requirements,
preconditions, checks, outcomes, StateDelta templates, event type, and
visibility policy. It uses validation before export and does not expose an
arbitrary code editor.

APIs:

- `POST /authoring/action-mods/preview`
- `POST /authoring/action-mods/validate`
- `POST /authoring/action-mods/export`

These routes are gated by `ENABLE_AUTHORING_API`.

### Magic System

The magic module defines `SpellDefinition`, `MagicResourceState`,
`SpellCastResult`, and `MagicModuleConfig`. The `cast_spell` action checks
spell targets, preconditions, resource cost, deterministic checks, effects,
failure effects, visibility policy, and optional crime policy.

Spell effects and resource consumption are returned as `StateDelta` values.
Public illegal casts can create crime/witness/faction consequences. Hidden
magic effects stay hidden unless visibility rules reveal them.

### Hacking System

The hacking module defines `HackableState`, `HackingToolState`,
`NetworkNodeState`, and `HackingAttemptResult`. Supported actions include
terminal hacking, security door bypass, camera disabling, log access, and
trace planting.

Failures can create intrusion traces, alarms, or cyber-crime consequences.
Hidden logs and hidden devices remain subject to Visibility.

### Crafting System

The crafting module defines `RecipeDefinition`, `CraftingStationState`, and
`CraftingAttemptResult`. Supported actions include `craft_item`,
`repair_item`, and `dismantle_item`.

Crafting consumes materials, preserves non-consumed tools, requires station
tags when configured, advances time, and creates outputs through
`StateDelta`. Recipe failure is rule-driven.

### Investigation / Deduction System

The investigation module defines `EvidenceState`, `TestimonyState`,
`HypothesisState`, and `DeductionAttemptResult`. Actions cover evidence
examination, testimony comparison, hypothesis formation, suspect accusation,
and timeline reconstruction.

Players can only form valid hypotheses from known evidence/facts. Accusation
results are rule-driven; hidden truth facts do not leak before discovery.

### Travel / Survival System

The survival module defines `SurvivalState`, `TravelRouteState`,
`WeatherState`, and `CampState`. Actions include route travel, rest, camp,
forage, food consumption, and water consumption.

Actions consume time and update fatigue, hunger, thirst, exposure, location,
and inventory through `StateDelta`. Weather and route risks are deterministic
or seeded.

### Stealth Expansion

The stealth module defines `StealthState`, `NoiseEvent`, `CoverState`, and
`DetectionCheckResult`. Actions include hide, sneak-follow, distract,
create-noise, set-decoy, and shadow-NPC.

Detection is rule-based using stealth score, light, cover, noise, alertness,
and suspicion. Hidden observers are redacted from player narration unless
discovered.

### Combat Expansion

The combat expansion adds `WeaponProfile`, `CombatEncounterDefinition`,
`CombatStatusEffect`, and `CombatStance` support. It covers weapon tags,
aggressive/defensive/cautious/fleeing stances, bleeding/stunned/guarded
status effects, non-lethal attacks, flee risk, and public combat
consequences.

Combat results are deterministic rule outcomes, not LLM judgments.

### Social Manipulation System

The social manipulation module defines `SocialMoveDefinition`,
`SocialMoveResult`, and `LeverageState`. Actions include persuade, threaten,
bribe, deceive, provoke, comfort, blackmail, and extract-information.

Rules depend on relationships, emotional state, known facts, leverage,
evidence, and faction reputation. NPCs cannot reveal unknown facts.

### Faction Mission System

`FactionMissionDefinition`, `FactionMissionState`, and
`FactionMissionReward` support local faction missions such as courier,
sabotage, investigation, protection, negotiation, bounty, and infiltration.

Mission availability is rule-driven by faction reputation, faction conflict,
known facts, prior missions, and player crime status. Accept, complete, and
fail operations create StateDeltas and Events and can integrate with quests.

### Domain / Base Management

Domain/base management uses `DomainState`, `FacilityState`,
`BaseInventoryState`, `StaffAssignmentState`, and `DomainUpgradeDefinition`.
Actions include claim-base, build-facility, assign-staff, upgrade-facility,
store-item, withdraw-item, and collect-income.

Domain ticks can handle income, upkeep, staff status, and bounded risk events.
The system remains lightweight and does not implement city-scale simulation.

### Gameplay Module Quality Gate

`GameplayModuleQualityGateReport` checks manifest validity, permissions,
action validation, state schema extensions, save compatibility, action tests,
hidden leak coverage, regression metadata, forbidden paths, and executable
code rejection.

API / CLI:

- `POST /quality/modules/{module_id}/gate/run`
- `python -m app.tools.module_quality_gate --module-id <module_id>`

The quality route is local-only and gated by the existing quality/debug/eval
configuration. Reports use normal-safe redaction.

### Gameplay Module Regression Playtests

`GameplayModuleRegressionScenario` and `GameplayModuleRegressionReport` run
deterministic module playtests for action success, action failure, invalid
target, hidden target, save/load, replay, and quality gate scenarios. Current
sample coverage includes magic, hacking, and crafting flows.

Regression tests use temporary state and mock/fake/local_stub-style
dependencies. They do not modify real user saves and do not call real LLM APIs.

### Gameplay Module Debugger

The module debugger exposes local debug-only summaries and dry-runs:

- `GET /debug/modules`
- `GET /debug/modules/{module_id}`
- `POST /debug/modules/{module_id}/actions/{action_id}/dry-run`

Dry-runs return precondition/check results, selected outcome, StateDelta
preview, Event preview, and visibility summary. They do not modify
`GameState`. Hidden facts are redacted by default, and player APIs never
return module debug data.

### Gameplay Module Import / Export

`GameplayModulePackageManifest` packages a module manifest, action
definitions, rule configs, quality tests, example content, docs, and
checksums. Export excludes `.env`, API keys, databases, logs, caches, and
executable files. Import dry-run validates manifest, actions, permissions,
checksums, save compatibility, executable rejection, zip-slip protection, and
the module quality gate.

APIs / CLI:

- `POST /modules/export`
- `POST /modules/import-dry-run`
- `POST /modules/import-apply`
- `python -m app.tools.module_package export --module-id <module_id>`
- `python -m app.tools.module_package import-dry-run --archive <package.b64>`
- `python -m app.tools.module_package import-apply --archive <package.b64> --confirm-apply`

Import apply requires explicit confirmation and does not auto-enable untrusted
modules.

## v1.7 Polished Desktop Studio

v1.7 improves the local desktop-style studio experience around the existing
backend API and React frontend. It is a local prototype layer, not a formal
installer or public desktop release. It does not add cloud sync, accounts,
auto-update, code signing, marketplace features, or direct desktop-shell access
to `GameState`.

The desktop boundary is defined in `docs/DESKTOP_STUDIO_BOUNDARY.md` and the
packaging checklist is in `docs/DESKTOP_PACKAGING.md`. The core rule remains:
desktop tools are convenience surfaces around existing backend services. They
cannot bypass `StateDelta`, `EventLog`, validation gates, visibility, provider
factory boundaries, or package safety checks.

### Desktop Studio Boundary

The v1.7 desktop boundary separates:

- `desktop_shell`
- `backend_process`
- `frontend_app`
- `local_workspace`
- `safe_config_summary`
- `secret_config`
- `backup_bundle`
- `export_bundle`
- `crash_report`
- `local_log`

API keys and provider credentials belong only to backend secret config such as
ignored local environment variables or `.env`. The frontend must never read or
receive API keys, raw env, raw provider secrets, database passwords, raw
prompts, hidden facts, or raw crash/log dumps.

### Desktop Launcher Pro

The launcher scripts are:

- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`

They check Python, Node/npm, dependencies, ports, `.env` presence, database
configuration, workspace status, optional built frontend output, and previous
crash-report count. They can run preflight-only diagnostics, start backend and
frontend local processes, write local logs under ignored `logs/`, and open the
local frontend URL.

The scripts do not hardcode API keys, do not print API keys, do not inject
`LLM_API_KEY` into frontend env, and do not modify `GameState`, saves, content
packs, modules, databases, or prompt profiles. Windows PowerShell profile
signature warnings are treated as non-blocking local shell policy warnings.

### Project Selector And Recent Projects

`ProjectWorkspace` and `RecentProjectEntry` provide safe summaries for local
workspace selection and recent-project navigation. APIs currently include:

- `GET /studio/workspaces`
- `POST /studio/workspaces`
- `POST /studio/workspaces/select`
- `GET /studio/workspaces/current`
- `GET /studio/recent-projects`
- `DELETE /studio/recent-projects/{workspace_id}`
- `POST /studio/recent-projects/clear`

Workspace paths are validated against path traversal and unsafe path
components, then exposed to the frontend only as `path_redacted`. The service
stores references and summaries only; it does not import unknown content,
read `.env`, or modify active saves.

### Local Config Manager

`LocalConfigManager` exposes safe configuration summaries through:

- `GET /studio/config/summary`
- `GET /studio/config/issues`
- `POST /studio/config/generate-template`

Safe summaries may show provider type, model id, local API flags, database
configured yes/no, redacted path hints, and whether an API key is configured
as a boolean. They do not show API key values, raw env, database passwords, or
full sensitive paths. Generated templates are `.env.example`-style output and
do not write real secrets.

### Local Update Notes

`LocalUpdateNotesIndex` reads local release-note documents and exposes:

- `GET /studio/update-notes`

This is an offline local index. It does not fetch remote URLs, check online
versions, download patches, or execute scripts.

### Desktop Health Check

`DesktopHealthCheckReport` is available through:

- `GET /studio/health`
- `POST /studio/health/check`

It reports backend availability, optional frontend reachability, database
configured/reachable status, safe config status, current workspace status,
world directory status, authoring/debug API flags, provider safe summary, and
recent-error placeholder status. It does not call providers, reveal secrets,
return hidden facts, or mutate state.

### Workspace Templates

`WorkspaceTemplate` supports local workspace creation from safe templates:

- `GET /studio/workspace-templates`
- `POST /studio/workspaces/create-from-template`

Templates create local folders and safe starter files such as
`config.template.env`. They do not copy `.env`, write API keys, execute
scripts, download remote templates, or overwrite existing non-empty
workspaces.

### Crash Report Local Viewer

`CrashReportService` stores local redacted crash reports behind debug-gated
APIs:

- `GET /debug/crash-reports`
- `GET /debug/crash-reports/{id}`
- `DELETE /debug/crash-reports/{id}`

Reports contain timestamp, component, error type, safe message, redacted stack,
and safe context summary. API keys, Authorization headers, raw env, raw
prompts, hidden fact text, and database passwords are redacted or excluded.
Reports are not uploaded.

### Startup Diagnostics

`StartupDiagnosticReport` is available through:

- `python -m backend.app.tools.startup_diagnostics`

The diagnostics check Python, Node/npm, backend imports, frontend dependency
folder presence, port availability, `.env` presence, database path
accessibility, current workspace status, optional built frontend output, and
previous crash reports. The report is a local safe summary and does not read
or print API key values.

### Desktop Settings UI

The frontend has v1.7 studio panels for safe local desktop settings/status:
config summaries, workspace/recent project summaries, update notes, health
checks, crash reports, and workspace templates. The UI must not store API
keys, raw env, raw prompts, or full sensitive paths. It does not write `.env`
or provider secrets.

### Planned Or Partial v1.7 Surfaces

The v1.7 roadmap also names Log Viewer, Error Recovery Wizard, Backup /
Restore, One-click Quality Gate, One-click Export World Pack, and Offline Help
Docs. Current code and policy establish the boundaries for these flows, but
their full runtime APIs are not all complete in the current implementation.

Current boundary expectations for these partial surfaces:

- Log views must be debug-gated, read only local `logs/`, reject path
  traversal, and redact secrets, raw prompts, and hidden facts.
- Error recovery plans must default to safe recommendations and not
  automatically modify saves, worlds, databases, or `.env`.
- Backups must default to excluding `.env`, API keys, logs, caches, databases,
  frontend build outputs, desktop build outputs, and executables.
- Restore must dry-run first, validate manifest/checksums, reject zip slip and
  executables, detect conflicts, and require explicit confirmation.
- One-click Quality Gate is a local aggregation concept over existing quality
  gates and must not call real LLMs or auto-fix content.
- One-click World Export must run validation and safe export profiles before
  packaging, and must not include secrets or hidden authoring text by default.
- Offline Help must read local docs only and must not load remote content.

These are intentionally described as local-only tools. They are not cloud
sync, account-based collaboration, online help, or automatic publishing
features.
