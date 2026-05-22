# v2.7 Roadmap: Advanced World Simulation Modules

## Version Theme

Advanced World Simulation Modules.

v2.7 builds on the v2.6 Script / Mod Platform Pro contracts to harden and expand
advanced world-simulation gameplay as local, deterministic, modular systems.
The goal is to support richer play loops without turning the core World Engine
into a monolith and without weakening the authority boundary around
`GameState`, `StateDelta`, `EventLog`, visibility, providers, or package safety.

## Current Baseline

- HEAD is expected to begin from the local `v2.6` tag with a clean working tree.
- v2.6 provides `PackageManifestV2`, `ModulePermissionSet`, declarative Action
  Mods, Rule Module Contract, Module Browser, Compatibility Matrix,
  Certification, Mod Quality Gate, Import/Export hardening, and Mod Audit Trail.
- Existing early or basic rule areas include combat, economy, faction, magic,
  hacking, crafting, investigation, and survival.
- Cultivation / xianxia mechanics were not found in the current baseline and
  should start in v2.7 as a minimal deterministic module.
- `mods/` and `docs/V2_7_RESEARCH_PLAN.md` are not present in the current
  baseline.

## Goal

v2.7 should introduce Advanced World Simulation Modules as optional, validated,
testable, importable, exportable, migratable, and disable-able module systems.
The modules should provide MVP gameplay frameworks for tactical combat, economy,
faction conflict, magic, hacking, crafting, investigation/deduction,
survival/travel, and cultivation.

All advanced gameplay must:

- integrate through the Script / Mod Platform contracts;
- declare module state schemas and migration implications;
- register actions through `ActionRegistry`;
- produce state changes through `StateDelta`;
- record runtime-affecting module events in `EventLog`;
- respect visibility and NPC knowledge boundaries;
- pass deterministic validation and quality gates;
- avoid real provider/API calls in tests.

## Explicit Non-Goals

v2.7 does not implement:

- arbitrary-code plugins;
- mod Python or JavaScript execution;
- a complete grand-war simulation;
- a complete complex global economy simulation;
- a complete tactical board game;
- a full LLM multi-agent social simulation;
- an online marketplace;
- account systems;
- cloud sync;
- LLM decisions for combat, economy, war, magic, hacking, crafting, deduction,
  survival, travel, or cultivation outcomes;
- direct module mutation of `GameState`;
- bypasses around `StateDelta`, `EventLog`, or visibility;
- module access to `.env`, API keys, databases, logs, caches, private user
  files, or real external network systems.

## Hard Constraints

- The World Engine remains the authoritative fact source.
- Advanced gameplay must be attached as modules rather than merged into an
  unbounded core state surface.
- Module state extensions must declare schema, namespace, version, defaults, and
  migration expectations.
- Module actions must register through `ActionRegistry`.
- All runtime state changes must be represented as `StateDelta`.
- All confirmed module runtime events must be recorded in `EventLog`.
- Every advanced module must be disable-able and quality-gate checkable.
- Modules must not execute arbitrary code.
- Modules must not bypass visibility.
- Modules must not make NPCs omniscient.
- Provider Gateway remains the only model entry.
- LLMs may help with expression, summaries, and drafts, but not with rule
  adjudication.
- Tests must use mock/local providers and must not call real APIs.

## Recommended Development Order

1. Runtime Foundation
   - Advanced Module Runtime Contract Review
   - Module State Schema Extension Framework
   - Module Save Migration Framework
   - Module Quality Gate
   - Module Import / Export / Migration Hardening

2. Existing Advanced Module Hardening
   - Tactical Combat Module Core
   - Tactical Combat Actions
   - Economy Simulation Module Core
   - Economy Simulation Tick / Events
   - Faction War Module Core
   - Faction War Regional Conflict Tick
   - Magic Module Core
   - Magic Action Pack
   - Hacking Module Core
   - Hacking Action Pack
   - Crafting Module Core
   - Investigation / Deduction Module Core
   - Survival / Travel Module Core

3. New Simulation Slice
   - Cultivation Module Core

4. Authoring / Review UI
   - Tactical Combat Authoring UI
   - Economy Authoring UI
   - Faction War Authoring UI
   - Module Authoring Dashboard

5. Release Hardening
   - Module Playtest Scenarios
   - Module Compatibility Stress Tests
   - v2.7 Integration Regression Tests

## Module Plan

### 1. Advanced Module Runtime Contract Review

- Goal: document and stabilize the runtime module boundary on top of v2.6.
- Data structures: `AdvancedModuleRuntimeContract`, module lifecycle state,
  module enable/disable metadata, module capability summary.
- API changes: no new runtime API is required in this slice; any discovered
  boundary gaps should become follow-up implementation tasks.
- Frontend changes: none.
- Tests: static boundary checks for no direct `GameState` mutation, no
  arbitrary code execution, and no direct provider calls from modules.
- Acceptance: one documented runtime contract governs all v2.7 modules.

### 2. Module State Schema Extension Framework

- Goal: allow modules to declare namespaced state extensions without polluting
  the core `GameState` schema.
- Data structures: `ModuleStateExtensionSpec`, `ModuleStateNamespace`,
  extension schema version, default values, validation rules, visibility hints.
- API changes: validation and module inspection endpoints can read extension
  specs and report namespace collisions.
- Frontend changes: Module Browser and authoring dashboard display declared
  module state namespaces.
- Tests: schema serialization, namespace collision detection, forbidden path
  rejection, disabled-module behavior.
- Acceptance: module state extensions are declared, validated, namespaced, and
  safe to disable.

### 3. Module Save Migration Framework

- Goal: migrate module state safely across module versions.
- Data structures: `ModuleMigrationPlan`, `ModuleMigrationStep`,
  `ModuleMigrationDryRunReport`, migration warning categories.
- API changes: module migration dry-run and apply should go through existing
  migration authority and require explicit confirmation.
- Frontend changes: module dashboard shows migration warnings, blockers, and
  dry-run results.
- Tests: dry-run no write, apply requires confirmation, rollback notes are
  present, migration errors do not corrupt active saves.
- Acceptance: module state migration is explicit, auditable, and does not bypass
  save migration rules.

### 4. Tactical Combat Module Core

- Goal: harden tactical combat as an optional module-scoped system.
- Data structures: tactical combat state, grid or zone model, cover,
  initiative, stance, tactical conditions, safe combat summaries.
- API changes: combat state preview/read endpoints may expose player-safe
  tactical state.
- Frontend changes: combat state panel can consume the safe summary.
- Tests: deterministic initiative, cover and stance validation, hidden combat
  intel filtering, disable-safe behavior.
- Acceptance: tactical combat state is module-scoped, deterministic, and safe in
  normal views.

### 5. Tactical Combat Actions

- Goal: register tactical actions through `ActionRegistry`.
- Data structures: move, attack, defend, flank, aim, suppress, and recover
  action definitions; `ActionResult`; `StateDelta` outputs; event tags.
- API changes: existing action preview/dry-run APIs may expose tactical action
  affordances if available.
- Frontend changes: tactical action affordance list for player or authoring
  surfaces.
- Tests: every tactical action returns `ActionResult`, produces valid
  `StateDelta`, records an `EventLog` event, and rejects invalid targets.
- Acceptance: tactical actions never mutate state directly.

### 6. Tactical Combat Authoring UI

- Goal: author tactical zones, cover, encounter presets, and tactical map
  annotations.
- Data structures: encounter preset draft, tactical map annotations, cover
  metadata, validation report.
- API changes: authoring endpoints for read/save draft/validate.
- Frontend changes: compact tactical authoring panel.
- Tests: frontend build, empty/error states, invalid refs, draft-only behavior.
- Acceptance: UI edits drafts or content only, never active `GameState`.

### 7. Economy Simulation Module Core

- Goal: provide module-scoped markets, prices, supply/demand, production, and
  consumption.
- Data structures: market state, commodity, producer, consumer, price rule,
  supply/demand snapshot.
- API changes: economy summary and preview endpoints.
- Frontend changes: economy overview table.
- Tests: deterministic price calculation, bounded values, invalid refs, disable
  safety.
- Acceptance: economy state is module-scoped and does not leak hidden trade
  intelligence.

### 8. Economy Simulation Tick / Events

- Goal: run deterministic economy ticks that produce `StateDelta` and
  `EventLog`.
- Data structures: economy tick result, market event, price delta, inventory
  flow summary.
- API changes: tick dry-run/summary through existing world tick tools where
  possible.
- Frontend changes: tick preview and event list.
- Tests: dry-run no write, confirmed tick through engine flow, `EventLog`
  recorded, values remain bounded.
- Acceptance: economy ticks do not write database or `GameState` directly.

### 9. Economy Authoring UI

- Goal: author commodities, markets, trade routes, producers, and consumers.
- Data structures: draft market config, trade route draft, producer/consumer
  draft, validation report.
- API changes: safe draft save and validation endpoints.
- Frontend changes: economy editor with validation messages.
- Tests: frontend build, invalid refs, empty/error states, no secret rendering.
- Acceptance: authoring data validates before save and does not mutate runtime
  state.

### 10. Faction War Module Core

- Goal: provide an abstract module-scoped regional conflict model.
- Data structures: region control, war objective, faction front, army or force
  abstract score, conflict visibility summary.
- API changes: faction war summary endpoint.
- Frontend changes: conflict overview.
- Tests: schema validation, control refs, disabled module behavior, hidden intel
  filtering.
- Acceptance: MVP is abstract regional conflict, not full grand strategy.

### 11. Faction War Regional Conflict Tick

- Goal: run deterministic regional conflict ticks.
- Data structures: conflict tick result, control delta, casualty/resource
  summary, hidden intelligence notes.
- API changes: dry-run and confirmed tick through engine flow.
- Frontend changes: event and timeline display.
- Tests: `EventLog` recorded, hidden intel excluded from normal view, NPC
  knowledge remains scoped.
- Acceptance: ticks do not make NPCs omniscient and do not bypass
  `StateDelta`.

### 12. Faction War Authoring UI

- Goal: edit conflict regions, objectives, faction war presets, and abstract
  force setups.
- Data structures: war preset draft, region objective draft, validation report.
- API changes: authoring draft and validation endpoints.
- Frontend changes: region conflict editor.
- Tests: invalid region/faction refs, frontend build, empty/error states.
- Acceptance: UI cannot mutate active world state.

### 13. Magic Module Core

- Goal: harden existing magic rules as an optional module.
- Data structures: spell, mana or resource pool, school, cooldown, casting
  condition, visibility policy.
- API changes: magic summary and action list endpoints.
- Frontend changes: spell/module panel.
- Tests: existing magic tests plus module enable/disable, cooldown validation,
  hidden effect filtering.
- Acceptance: spells resolve through deterministic rules and `StateDelta`.

### 14. Magic Action Pack

- Goal: package magic actions as declarative or registered actions.
- Data structures: cast, channel, ward, dispel, ritual action specs; target
  specs; event tags.
- API changes: action preview and validation where available.
- Frontend changes: magic action affordances.
- Tests: invalid targets, hidden effect leak checks, `EventLog`, no LLM
  adjudication.
- Acceptance: LLMs cannot decide spell success.

### 15. Hacking Module Core

- Goal: harden hacking as an optional cyber/tech in-world module.
- Data structures: device, network node, access level, trace risk, local
  in-world network graph.
- API changes: hacking target summary.
- Frontend changes: hacking panel.
- Tests: no filesystem/network access, target visibility, trace risk
  determinism.
- Acceptance: hacking module never touches real network, files, or external
  services.

### 16. Hacking Action Pack

- Goal: register scan, intrude, disable, spoof, and exfiltrate-style in-world
  actions.
- Data structures: action specs, trace outcomes, target visibility, state delta
  specs.
- API changes: action preview and validation.
- Frontend changes: hacking action list.
- Tests: deterministic checks, hidden logs not player-visible unless revealed,
  no real external API calls.
- Acceptance: all hacking results are in-world model changes only.

### 17. Crafting Module Core

- Goal: harden crafting as an optional production module.
- Data structures: recipe, station, ingredient, output, quality tier, failure
  risk, crafting state summary.
- API changes: crafting summary and validation endpoints.
- Frontend changes: crafting recipe/station panel or editor.
- Tests: consumes/produces via `StateDelta`, invalid refs, undeclared key item
  rejection.
- Acceptance: crafting cannot create undeclared key facts or items without
  validation.

### 18. Investigation / Deduction Module Core

- Goal: harden deduction and evidence reasoning as a deterministic rule module.
- Data structures: clue, evidence, hypothesis, deduction check, reveal policy,
  safe evidence summary.
- API changes: evidence and deduction safe-summary endpoints.
- Frontend changes: deduction board MVP.
- Tests: hidden clues filtered, reveal only through local rules, invalid
  hypothesis refs.
- Acceptance: deduction output is not an LLM judgment.

### 19. Survival / Travel Module Core

- Goal: harden travel, hunger, thirst, fatigue, route risk, weather, and camps.
- Data structures: route, survival state, weather/risk summary, travel event,
  resource consumption plan.
- API changes: route and survival summary endpoints.
- Frontend changes: survival/travel panel.
- Tests: deterministic travel, hidden route filtering, `EventLog`, invalid
  route refs.
- Acceptance: travel changes happen through `StateDelta`.

### 20. Cultivation Module Core

- Goal: introduce a minimal cultivation/xianxia MVP as a new deterministic
  module.
- Data structures: cultivation realm, qi/resource pool, technique,
  breakthrough attempt, sect/reputation refs, tribulation or risk summary.
- API changes: cultivation state and action summary endpoints.
- Frontend changes: cultivation panel MVP.
- Tests: deterministic breakthrough rules, module disabled state, no LLM judge,
  hidden technique filtering.
- Acceptance: MVP supports progression mechanics without claiming full genre
  simulation.

### 21. Module Authoring Dashboard

- Goal: provide a unified authoring surface for advanced modules.
- Data structures: module summary, validation status, enable/disable status,
  migration status, quality status.
- API changes: dashboard summary endpoint.
- Frontend changes: module cards, blockers, warnings, and validation links.
- Tests: frontend build, disabled/empty/error states, no active state mutation.
- Acceptance: dashboard reviews and edits drafts/configs only.

### 22. Module Playtest Scenarios

- Goal: add deterministic scenarios for each advanced module.
- Data structures: scenario fixtures, expected outcomes, hidden leak sentinels,
  expected events.
- API changes: reuse existing playtest or scenario runner patterns.
- Frontend changes: optional dashboard display for scenario status.
- Tests: module scenarios pass with mock/local providers, no real APIs, no
  arbitrary code.
- Acceptance: every advanced module has at least one deterministic regression
  path.

### 23. Module Compatibility Stress Tests

- Goal: detect cross-module conflicts and disabled-module safety issues.
- Data structures: compatibility matrix extensions, selected module set,
  load-order draft, conflict summary.
- API changes: compatibility checks extend v2.6 module matrix behavior.
- Frontend changes: compatibility warnings in the module dashboard.
- Tests: combinations of combat/economy/faction/magic/hacking/crafting/
  investigation/survival/cultivation, deterministic load order, disabled-module
  fallbacks.
- Acceptance: conflict blockers are deterministic and visible before runtime.

### 24. Module Quality Gate

- Goal: extend quality gate coverage for advanced modules.
- Data structures: `AdvancedModuleQualityGateResult`, blocker categories,
  warnings, per-module status, migration status.
- API changes: quality gate can include advanced modules with an explicit flag.
- Frontend changes: dashboard quality status.
- Tests: blockers for direct mutation, missing migration, hidden leak, no
  `EventLog`, invalid state namespace.
- Acceptance: quality gate can block unsafe advanced modules.

### 25. Module Import / Export / Migration Hardening

- Goal: extend v2.6 package hardening for module state, module packages, and
  migration metadata.
- Data structures: export manifest sections, module migration metadata,
  import dry-run report.
- API changes: import dry-run/apply remains explicit-confirm and must not enable
  unsafe modules automatically.
- Frontend changes: import warnings and migration review.
- Tests: zip slip, executable rejection, secret filtering, migration dry-run no
  write, provider/profile safety.
- Acceptance: module packages import/export safely without mutating active
  `GameState`.

### 26. v2.7 Integration Regression Tests

- Goal: cover end-to-end advanced module boundaries.
- Data structures: regression fixtures, scenario packages, expected event/state
  summaries.
- API changes: none beyond verifying public surfaces added during v2.7.
- Frontend changes: verify dashboard and module panels build.
- Tests: full `python -m pytest` and `cd frontend && npm.cmd run build`.
- Acceptance: all v2.7 modules pass without real APIs, arbitrary code, secret
  leakage, or boundary bypasses.

## Cross-Cutting Impact

### NarrativeProject

NarrativeProject may gain module enable/disable metadata and references to
module state namespaces. It should not absorb module-specific fields directly
into its core schema unless a migration and compatibility policy explicitly
requires it.

### Novel Studio

Novel Studio may reference safe module events, summaries, and timelines for
prose drafts. It cannot apply module outcomes, decide rule results, or turn
module draft text into world facts without validation.

### Tavern Studio

Tavern Studio may use safe module context for RP flavor and character-facing
dialogue. It cannot alter module state directly, reveal hidden module facts, or
grant NPCs knowledge outside structured visibility and knowledge rules.

### World Mode / GameState

World Mode remains the fact authority. Module state extensions must be
namespaced, schema-declared, migration-aware, and changed only through
`StateDelta`. Confirmed runtime changes must be recorded in `EventLog`.

### Cross-Mode Bridge

Novel or Tavern inputs to advanced modules remain drafts or proposals. Cross-mode
flows cannot apply module state changes or decide advanced module results without
World Engine validation.

### Provider Gateway

Provider Gateway remains the only model entry. Providers can summarize, draft,
or render expression around confirmed module events, but cannot decide tactical,
economic, faction, magic, hacking, crafting, deduction, survival, travel, or
cultivation outcomes.

### Script / Mod Platform

v2.7 modules build on v2.6 manifests, permissions, certification, quality gate,
import/export hardening, and audit. Advanced modules should not introduce a
parallel plugin system or runtime code execution path.

### LLM Permission Boundary

LLMs remain the language layer. They must not adjudicate advanced mechanics,
write `GameState`, bypass schema validation, bypass visibility, or replace local
rules.

### Visibility, Secrets, Debug Data, and Memory Risk

Hidden facts, NPC secrets, hidden intelligence, debug data, raw `state_deltas`,
and debug memory must be filtered from normal UI, player APIs, prompts, exports,
reports, module packages, and quality gate normal views. Debug views must remain
explicitly gated and must not leak provider secrets or local paths.

## v2.7 Integration Test Requirements

The v2.7 integration suite should cover:

- module state extension schema serialization, validation, namespace collision,
  and forbidden paths;
- module save migration dry-run and explicit-confirm apply;
- enable/disable behavior for every advanced module;
- ActionRegistry registration for module actions;
- `ActionResult`, `StateDelta`, and `EventLog` coverage for module actions and
  ticks;
- visibility and hidden-leak regression for combat, faction intel, evidence,
  hacking logs, travel risks, and cultivation secrets;
- deterministic per-module scenarios for tactical combat, economy, faction war,
  magic, hacking, crafting, deduction, survival/travel, and cultivation;
- cross-module compatibility stress checks;
- import/export rejection for zip slip, executables, secrets, forbidden paths,
  and unsafe migration metadata;
- module quality gate blockers for direct mutation, missing `EventLog`, hidden
  leak risk, missing migration, and unsafe permissions;
- frontend build and empty/error/disabled states for authoring dashboard and
  module panels;
- no arbitrary code execution;
- no real API/provider calls.

Final validation commands:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

## v2.7 Final Acceptance Criteria

v2.7 is accepted only when:

- advanced module runtime contracts are documented and enforced by tests;
- module state extensions are namespaced, validated, and migration-aware;
- module save migration supports dry-run and explicit confirmation;
- tactical combat, economy, faction war, magic, hacking, crafting,
  investigation/deduction, survival/travel, and cultivation have deterministic
  MVP coverage;
- module actions go through `ActionRegistry`;
- module state changes go through `StateDelta`;
- confirmed module runtime events write `EventLog`;
- module UI surfaces do not mutate active state directly;
- import/export filters secrets and rejects unsafe package content;
- module quality gate can block unsafe advanced modules;
- normal views do not leak hidden facts, NPC secrets, debug data, or raw
  `state_deltas`;
- tests do not call real providers or external APIs;
- `python -m pytest` passes;
- `cd frontend && npm.cmd run build` passes;
- acceptance report, audits, release notes, and final freeze checks exist before
  tagging.

## v2.8 Candidate Directions

Recommended v2.8 direction: Quality Studio Pro.

Rationale: v2.1-v2.7 expands the project into Novel, Tavern, World,
Cross-Mode, Provider Gateway, Script/Mod Platform, and Advanced Simulation
Modules. A stronger Quality Studio would help validate the larger platform with
release matrices, scenario dashboards, quality trends, compatibility analysis,
performance budgets, hidden-leak monitoring, and safer acceptance automation.

Alternative v2.8 candidates:

- Desktop Packaging Pro, if local distribution and project lifecycle polish
  becomes the release bottleneck.
- Advanced Authoring Studio Pro, if module authoring workflows need deeper map,
  timeline, graph, and validation UX before expanding quality automation.
