# v2.7 Release Notes: Advanced World Simulation Modules

## Version Name

v2.7 Advanced World Simulation Modules.

## Version Goal

v2.7 adds lightweight, deterministic advanced simulation modules on top of the
v2.6 Script / Mod Platform Pro contracts. The release focuses on making richer
World Mode systems modular, testable, migratable, disable-able, and
quality-gate checkable while preserving the core authority boundary:

- World Engine remains the fact source.
- Module state changes go through `StateDelta`.
- Module events are represented as `EventLog` events.
- LLMs remain language/draft/summarization tools, not world judges.
- Provider Gateway remains the only model entry.
- Modules do not execute arbitrary code or read secrets.

## New Features

- Added v2.7 module runtime contract review:
  `docs/V2_7_MODULE_RUNTIME_CONTRACT_REVIEW.md`.
- Added module state extension support with `ModuleStateExtension` and
  `ModuleStateField`.
- Added module migration support with `ModuleMigrationPlan`,
  `ModuleMigrationStep`, `ModuleMigrationReport`, and `ModuleMigrationService`.
- Added lightweight advanced module MVPs:
  - `tactical_combat`
  - `economy_sim`
  - `faction_war`
  - `magic`
  - `hacking`
  - `crafting`
  - `deduction`
  - `survival_travel`
  - `cultivation`
- Added deterministic module playtest scenarios and reports.
- Added module compatibility stress reports for planned module combinations.
- Added advanced module quality gate coverage.
- Added v2.7 module authoring/dashboard frontend surfaces.
- Added v2.7 audits and acceptance report.

## Behavior Changes

- Advanced gameplay state is modeled as module state under
  `GameState.modules`, not as unbounded additions to core `GameState`.
- Module-owned state paths are validated under `modules.{module_id}...`.
- Module migrations are dry-run capable and require explicit confirmation for
  apply.
- Destructive module-state removal is rejected by default.
- Economy price modifiers are capped to avoid unbounded price explosion.
- Crafting recipes now reject zero-input output recipes and same-item
  net-positive recipes.
- Magic spell effects are constrained to safe `modules.magic.casters.*` paths
  and bounded resource values.

## API Changes

New or extended local authoring / module endpoints include:

```text
GET  /authoring/worlds/{world_id}/modules/dashboard
GET  /authoring/worlds/{world_id}/modules/tactical-combat/config
POST /authoring/worlds/{world_id}/modules/tactical-combat/validate-draft
POST /authoring/worlds/{world_id}/modules/economy-sim/validate-draft
POST /authoring/worlds/{world_id}/modules/faction-war/validate-draft
POST /projects/{project_id}/modules/quality-gate
```

These endpoints are local authoring/review surfaces. They return safe summaries
and draft validation results. They do not apply active runtime `GameState`,
display secrets, expose hidden module details, or call LLMs.

CLI:

```powershell
python -m app.tools.module_quality_gate_v27 . --json
python -m app.tools.module_quality_gate . --advanced --json
```

## Frontend Changes

- Added Module Authoring Dashboard for advanced modules.
- Dashboard shows:
  - module id;
  - enabled/status metadata;
  - state extension status;
  - actions provided;
  - migration requirement;
  - validation status;
  - quality gate status.
- Added tactical/economy/faction draft validation flows.
- UI remains local-only and does not display secrets, hidden details, raw
  module state, raw `state_deltas`, API keys, or provider secrets.

## Module State / Migration Changes

- `ModuleStateExtension` declares module id, namespace, fields, default values,
  migration requirement, visibility policy, and save policy.
- Valid module state namespaces must be:

```text
state.modules.{module_id}
```

- Core `GameState` field names cannot be declared as module fields.
- Module deltas are validated against `modules.{module_id}...`.
- `ModuleMigrationService` supports:
  - add module defaults;
  - upgrade module schema;
  - disable module while preserving state;
  - destructive removal only with explicit destructive confirmation.
- Successful migration apply records `module_migration_history`.

## Tactical Combat Changes

- Added `TacticalCombatState`, `CombatEncounter`, and
  `CombatantTacticalState`.
- Supports encounter ids, combatants, turn order, active combatant,
  action points, range bands, cover, stance, status effects, and hidden
  combatant filtering.
- Added lightweight tactical actions:
  - `tactical_move`
  - `take_cover`
  - `aim`
  - `strike`
  - `defend`
  - `guard`
  - `flee_tactical`
- Tactical actions produce `ActionResult`, `StateDelta`, and module `Event`
  records. They do not directly mutate `GameState`.

## Economy Simulation Changes

- Added `EconomySimState`, `MarketRegionState`, and `CommodityState`.
- Supports regional markets, commodities, supply, demand, scarcity,
  price-index modifiers, trade route status, and deterministic economy ticks.
- `economy_sim_tick` produces StateDeltas and a module tick Event.
- Item `base_price` is not overwritten.
- Price index is capped for v2.7 MVP stability.

## Faction War Changes

- Added `FactionWarState`, `RegionConflictState`, and
  `FactionWarResourceState`.
- Supports regional control/conflict state, contested factions, control score,
  front pressure, morale, supply, war phase, and player-known visibility.
- `faction_war_tick` produces StateDeltas and a module tick Event.
- War changes are local rule outcomes, not LLM judgments.
- Hidden war regions are excluded from player-safe summaries.

## Magic / Hacking / Crafting Changes

### Magic

- Added `MagicState`, `SpellDefinition`, and `CasterState`.
- Supports caster mana/focus, known spells, spell costs, local effects,
  visibility policy, and public-illegal magic consequence proposals.
- Spell effects are declared data and constrained to safe module paths.
- LLMs do not invent spell effects or decide spell success.

### Hacking

- Added `HackingState`, `HackableObjectState`, and `DigitalAccessState`.
- Supports in-world terminals, security levels, access state, trace level,
  visible digital logs, and locked functions.
- Hacking is strictly in-world simulation. It does not access real networks,
  filesystems, or external services.

### Crafting

- Added `CraftingState`, `RecipeDefinition`, and `CraftingJob`.
- Supports recipe definitions, material consumption, workstation checks,
  deterministic success/failure, and output proposals.
- Release-blocker fix: zero-input output recipes and same-item net-positive
  recipes are rejected to prevent item duplication loops.
- LLMs do not generate authoritative crafted outputs.

## Deduction / Survival / Cultivation Changes

### Deduction

- Added `DeductionState`, evidence records, claims, and hypotheses.
- Deduction actions inspect visible evidence, compare known claims, form
  hypotheses, and test against known facts only.
- Hidden evidence and hidden truth are not exposed to the player.
- Hypotheses do not become world facts.

### Survival / Travel

- Added `SurvivalTravelState`, `SurvivalStatus`, and
  `TravelRouteModuleState`.
- Supports route time cost, fatigue changes, camp/rest, forage, route risk,
  and hidden-danger filtering.
- Travel changes are represented as StateDeltas.

### Cultivation

- Added `CultivationState`, `CultivatorState`, `TechniqueDefinition`, and
  `BreakthroughRule`.
- Supports realm/stage/progress/qi, known techniques, meditation, practice,
  breakthrough attempts, and pill modifiers.
- Breakthrough resolution is deterministic with a fixed seed.
- Hidden techniques are rejected unless properly revealed/known.

## Module Quality / Playtest / Compatibility Changes

- Added `ModulePlaytestScenario` and `ModulePlaytestReport`.
- Default playtests cover:
  - tactical combat path;
  - economy market tick path;
  - faction war tick path;
  - magic cast path;
  - hacking terminal path;
  - crafting recipe path;
  - deduction case path;
  - survival travel path;
  - cultivation progress path.
- Added `ModuleCompatibilityStressReport`.
- Compatibility stress covers planned module combinations, including
  tactical+magic, economy+faction, crafting+economy, survival+faction,
  cultivation+magic, deduction+crime/witness, and all-enabled smoke checks.
- Added `ModuleQualityGateConfig` and `ModuleQualityGateResult`.
- Quality gate checks playtest results, EventLog coverage, save/load stability,
  hidden leak flags, compatibility reports, migration errors, and dangerous
  permissions.

## Import / Export / Migration Hardening Changes

- v2.7 extends v2.6 import/export safety for advanced module metadata.
- Import dry-run checks module state metadata, migration requirements,
  executable files, secrets, zip slip/path traversal, permissions, and action
  conflict risks.
- Import apply requires explicit confirmation.
- High-risk modules are not automatically enabled.
- Destructive module-state removal is rejected by default.
- Module packages must filter `.env`, API keys, provider secrets, databases,
  logs, caches, `node_modules`, `dist`, build artifacts, debug reports,
  executables, and secret-like content.

## Known Limitations

v2.7 is intentionally an MVP-scale module release.

It does not support:

- a complete large-scale war system;
- a complete complex/global economy simulation;
- a complete complex tactical board game;
- a full LLM multi-agent social simulation;
- arbitrary-code plugins;
- mod Python/JavaScript execution;
- online marketplace, account system, or cloud sync;
- LLM adjudication of combat, economy, war, magic, hacking, crafting,
  deduction, survival, travel, or cultivation results.

Additional limitations:

- Some advanced module actions are direct rule helpers today; full
  player-facing runtime integration through `ActionRegistry` / shared module
  runner remains a hardening priority.
- Tactical Combat does not include a full grid, AI, or complete encounter end
  system.
- Economy and Faction War are abstract local simulations, not full strategic
  simulations.
- Module playtests are deterministic smoke/integration tests, not long-run
  adversarial balance simulations.
- Frontend build currently passes with the existing Vite chunk-size warning.

## Upgrade Notes From v2.6

- Existing v2.6 Script / Mod Platform packages remain local declarative
  packages. v2.7 does not turn them into executable plugins.
- New module state should be declared under `state.modules.{module_id}`.
- Module migrations should dry-run before apply.
- Any module package import/export path must continue to filter secrets and
  unsafe artifacts.
- Provider Profile Packs still cannot contain raw API keys.
- Prompt/Profile/Style modules still cannot expand LLM authority.
- Provider Gateway remains the only model entry.
- If enabling crafting content from external packages, validate recipes against
  the new no-zero-input and no-net-positive same-item rules.

## Recommended v2.8 Direction

Recommended v2.8 direction: **Quality Studio Pro**.

Rationale: v2.1-v2.7 now cover Novel, Tavern, World, Provider Gateway, Script /
Mod Platform, and Advanced Simulation Modules. The next useful layer is a
stronger release/quality surface that can run long-run module playtests,
balance checks, hidden-leak regression, provider regressions, compatibility
stress, migration stress, and release readiness from one local dashboard.

Alternative v2.8 candidates:

- Roleplay Immersion & Mature Module, if the next priority is richer Tavern/RP
  style, consent-aware mature-content policy, and character relationship depth.
- Online-Ready Architecture, if the next priority is preparing local-first
  workspace boundaries for future sync/collaboration without shipping cloud
  accounts or marketplace features yet.

## Verification Summary

From `docs/V2_7_ACCEPTANCE_REPORT.md`:

- `python -m pytest`: `1662 passed in 135.72s`
- `cd frontend && npm.cmd run build`: passed
- No high-risk LLM boundary, module security/state, or balance/simulation
  blocker remains after release-blocker fixes.
