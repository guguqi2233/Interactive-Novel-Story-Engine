# v2.7 Acceptance Report: Advanced World Simulation Modules

## Verdict

Accepted.

v2.7 Advanced World Simulation Modules are accepted as a lightweight,
deterministic, local module MVP layer on top of the v2.6 Script / Mod Platform
contracts. The implementation provides module state extensions, module
migration, advanced module rule helpers, authoring/dashboard surfaces,
playtests, compatibility stress, quality gate coverage, import/export hardening,
and integration regression tests.

This acceptance does not certify v2.7 as a complete tactical board game,
complete grand-war simulation, complete global economy, full cultivation
system, arbitrary-code module runtime, online marketplace, or LLM multi-agent
simulation.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: `1662 passed in 135.72s`
- `cd frontend && npm.cmd run build`: passed
- Frontend build warning: Vite reported the existing chunk-size warning for a
  generated JS chunk larger than 500 kB. This is not a v2.7 acceptance blocker.

## Scope Accepted

### 1. Advanced Module Runtime Contract Review

Accepted. `docs/V2_7_MODULE_RUNTIME_CONTRACT_REVIEW.md` documents the current
runtime module boundary and identifies the v2.7 contract shape. The advanced
module layer remains deterministic and does not execute arbitrary code.

### 2. Module State Schema Extension Framework

Accepted. `ModuleStateExtension` and `ModuleStateField` support controlled
module state declarations under `state.modules.{module_id}`. Core `GameState`
field names are rejected, and module StateDelta validation constrains module
owned deltas to `modules.{module_id}...` paths.

### 3. Module Save Migration Framework

Accepted. `ModuleMigrationPlan`, `ModuleMigrationStep`,
`ModuleMigrationReport`, and `ModuleMigrationService` support dry-run and
confirmed apply. Dry-run does not mutate the original state, apply requires
confirmation, successful apply records `module_migration_history`, and
destructive module-state removal is rejected unless explicitly confirmed.

### 4. Tactical Combat Module Core

Accepted as MVP. `TacticalCombatState`, `CombatEncounter`, and
`CombatantTacticalState` provide encounter state, turn order, active combatant,
AP, range, cover, stance, status effects, and player-safe visible summaries.
Hidden combatants are excluded from normal tactical summaries.

### 5. Tactical Combat Actions

Accepted as lightweight rule helpers and tests. Tactical actions such as
`tactical_move`, `take_cover`, `aim`, `strike`, `defend`, `guard`, and
`flee_tactical` produce `ActionResult`, `StateDelta`, and `Event` records. AP
is consumed through StateDelta, and cover is bounded.

Note: full runtime ActionRegistry integration for every advanced helper remains
a v2.8 hardening priority.

### 6. Tactical Combat Authoring UI

Accepted. The Module Authoring Dashboard includes tactical combat config and
draft validation surfaces. These surfaces are local authoring tools and do not
modify active `GameState`.

### 7. Economy Simulation Module Core

Accepted as MVP. `EconomySimState`, `MarketRegionState`, and `CommodityState`
support regional markets, commodities, supply, demand, scarcity, and
price-index modifiers. Item `base_price` is not overwritten.

### 8. Economy Simulation Tick / Events

Accepted. `economy_sim_tick` produces StateDeltas and a module tick Event. The
price index is capped to avoid unbounded price explosion, and tests verify
determinism and no base-price overwrite.

### 9. Economy Authoring UI

Accepted. Economy simulation draft validation is exposed through the module
authoring UI/API path. It remains draft/config validation only.

### 10. Faction War Module Core

Accepted as MVP. `FactionWarState`, `RegionConflictState`, and
`FactionWarResourceState` support regional conflict data, control score,
front pressure, morale, supply, war phase, and player-known visibility.

### 11. Faction War Regional Conflict Tick

Accepted. `faction_war_tick` produces StateDeltas and module tick Events using
local rule inputs such as rumors and economy route penalties. Hidden war regions
are excluded from player-safe visible summaries.

### 12. Faction War Authoring UI

Accepted. Faction war draft validation is exposed through the module authoring
UI/API path. It does not apply active war state.

### 13. Magic Module Core

Accepted as MVP. `MagicState`, `SpellDefinition`, and `CasterState` support
mana/focus, known spells, spell definitions, local effects, and public-illegal
magic consequence proposals. Spell effects are now constrained to safe
`modules.magic.casters.*` paths and bounded resource values.

### 14. Magic Action Pack

Accepted as rule helpers. Magic actions such as `cast_spell`, `prepare_spell`,
`rest_focus`, and `inspect_magic` resolve through local rules and return
StateDeltas/Events. LLMs do not decide spell success or effects.

### 15. Hacking Module Core

Accepted as MVP. `HackingState`, `HackableObjectState`, and
`DigitalAccessState` model in-world terminals, security, access state, trace,
and visible digital logs. The module does not access real filesystems or
networks.

### 16. Hacking Action Pack

Accepted as rule helpers. `scan_terminal`, `hack_terminal`, `extract_logs`,
`erase_trace`, and `disable_lock` are local deterministic/seeded outcomes.
Hidden logs are filtered from visible extraction.

### 17. Crafting Module Core

Accepted as MVP after release-blocker fix. `CraftingState`, `RecipeDefinition`,
and `CraftingJob` support recipes, material consumption, workstation checks,
and output proposals. The previous zero-input/net-positive crafting exploit is
blocked by schema validation.

### 18. Investigation / Deduction Module Core

Accepted as MVP. `DeductionState`, evidence, claims, and hypotheses support
known-fact-only deduction actions. Hidden evidence is rejected, and hypotheses
do not become world facts.

### 19. Survival / Travel Module Core

Accepted as MVP. `SurvivalTravelState`, `TravelRouteModuleState`, and
`SurvivalStatus` support travel time, fatigue, camp/rest, forage, and hidden
route danger filtering. Travel changes are represented as StateDeltas.

### 20. Cultivation Module Core

Accepted as MVP. `CultivationState`, `CultivatorState`,
`TechniqueDefinition`, and `BreakthroughRule` support realm/progress/qi,
techniques, meditation, practice, breakthrough, and pill modifiers. Breakthrough
is deterministic with a fixed seed.

### 21. Module Authoring Dashboard

Accepted. The frontend dashboard displays module list, enabled/status metadata,
state extension status, actions provided, migration requirement, validation
status, and quality status. It does not display secrets or hidden details.

### 22. Module Playtest Scenarios

Accepted. `ModulePlaytestScenario` and `ModulePlaytestReport` run deterministic
scenarios for tactical, economy, faction, magic, hacking, crafting, deduction,
survival, and cultivation paths. Reports check Event presence, StateDelta count,
hidden leak sentinels, and save/load stability.

### 23. Module Compatibility Stress Tests

Accepted. `ModuleCompatibilityStressReport` covers planned combinations such
as tactical+magic, tactical+hacking, economy+faction, crafting+economy,
survival+faction, cultivation+magic, deduction+crime/witness, and all-enabled
smoke checks.

### 24. Module Quality Gate

Accepted. `ModuleQualityGateConfig` and `ModuleQualityGateResult` aggregate
playtest, compatibility, migration, permission, hidden leak, EventLog, and
save/load checks. Dangerous permissions can block the gate.

### 25. Module Import / Export / Migration Hardening

Accepted. v2.7 builds on v2.6 import/export hardening. Dry-run checks package
manifest, module state metadata, migration requirements, zip slip,
executables, secrets, permissions, and action conflict risks. Apply requires
confirmation, and destructive state removal is rejected by default.

### 26. v2.7 Integration Regression Tests

Accepted. Focused and integration tests cover module state/migration,
tactical, economy, faction, magic, hacking, crafting, deduction, survival,
cultivation, module dashboard APIs, playtests, compatibility stress, quality
gate, import/export hardening, and no-real-provider/static boundary checks.

## Boundary Review

### World Engine Authority

Passed. World Engine remains the authoritative source of runtime facts.
Advanced modules do not replace `GameState`, do not become independent fact
authorities, and do not allow LLMs or providers to decide rule outcomes.

### StateDelta / EventLog

Passed for accepted MVP scope. Module helpers return `ActionResult`,
`StateDelta` lists, and module `Event` records. Tests verify EventLog coverage
and save/load stability. Future player-facing wiring should route every module
action through a shared runtime wrapper or full ActionRegistry path to ensure
atomic apply+event behavior.

### Module State Namespace

Passed. Module extension state is scoped to `state.modules.{module_id}` and
module StateDelta validation rejects non-module paths for module-owned deltas.
Some module actions intentionally emit engine-owned consequence deltas such as
inventory, turn, or public consequence flags; these are explicit StateDeltas,
not direct mutation.

### Visibility and Hidden Information

Passed for current paths. Hidden combatants, hidden war regions, hidden logs,
hidden evidence, hidden route dangers, hidden techniques, NPC secrets, debug
memory, and raw state deltas are excluded from normal module summaries and
provider inputs. Module playtests include hidden leak sentinels.

### LLM Boundary

Passed. v2.7 module rules do not call Provider Gateway, concrete providers,
OpenAI, real APIs, `generate_text`, `generate_json`, or `call_llm`. LLMs remain
language/draft/summarization tools only.

### Provider Gateway

Passed. Provider Gateway remains the only model entry. v2.7 rules do not bypass
it because they do not use model calls for rule adjudication.

### Security

Passed. The v2.7 module runtime does not execute arbitrary code, does not read
secrets, does not access real networks, and does not write databases directly.
Tests use local/mock/fake settings and temporary state.

## Known Limitations

1. v2.7 modules are lightweight MVPs, not complete large-scale simulations.
2. Tactical Combat lacks a full tactical grid, complete AI, encounter-end
   system, and full ActionRegistry runtime integration for every helper.
3. Economy Simulation is a local price-index modifier system, not a full global
   economy.
4. Faction War is an abstract regional pressure/morale/supply MVP, not a grand
   strategy simulation.
5. Magic, Hacking, Crafting, Deduction, Survival, and Cultivation are bounded
   rule MVPs, not freeform systems.
6. Module playtests are deterministic smoke/integration tests, not long-run
   adversarial balance simulations.
7. The frontend build passes with an existing Vite chunk-size warning.
8. Some advanced module actions are direct rule helpers today; full runtime
   ActionRegistry convergence is recommended for v2.8.

## Acceptance Risks

1. Long-run balance coverage is still limited. The v2.7 balance blocker around
   crafting zero-input/net-positive recipes has been fixed, but other medium
   balance items remain as hardening tasks.
2. Same-turn idempotency for some ticks should be strengthened before longer
   campaign simulation.
3. Module consequence allowlists should be formalized for non-module paths such
   as `turn`, `player.inventory`, and public consequence flags.
4. Future prompt integration must use safe module summaries only and must not
   send raw module state to providers.

None of these risks block v2.7 MVP acceptance after the release-blocker fixes
and passing verification commands.

## Recommended v2.8 Priorities

1. Quality Studio Pro.
   - Broaden long-run module playtests.
   - Add adversarial balance checks for economy/crafting/survival/cultivation.
   - Add release dashboards for v2.1-v2.7 contract health.

2. Advanced Module Runtime Hardening.
   - Route all player-facing module actions through ActionRegistry/runtime
     wrapper.
   - Add module consequence allowlists and atomic apply+EventLog wrappers.
   - Add same-turn tick idempotency checks.

3. Module Authoring Polish.
   - Expand tactical/economy/faction authoring panels.
   - Add safe previews for magic/hacking/crafting/deduction/survival/cultivation
     module configs.

4. Balance Regression Matrix.
   - Add numerical cap tests, resource loop tests, repeated tick tests, and
     long-run save/load replay scenarios.

## Final Status

v2.7 is accepted.

Final verified state:

- Backend tests: passed, `1662 passed`.
- Frontend build: passed.
- No real provider/API calls are required for verification.
- No high-risk LLM boundary, module security/state, or balance/simulation
  blocker remains after the crafting/economy/magic release-blocker fixes.
- v2.7 may proceed to release notes and final freeze checks.
