# v1.6 Roadmap: Advanced Gameplay Modules

## Version Goal

v1.6 adds Advanced Gameplay Modules on top of the stable world engine. The goal
is to support pluggable, local, validated gameplay modules and declarative
Action Mods for domains such as magic, hacking, crafting, investigation,
travel, stealth, combat, social manipulation, faction missions, and base
management.

Gameplay modules extend what the deterministic rules engine can adjudicate.
They do not become scripts, plugins, or LLM agents. Every gameplay action still
flows through the same authority chain:

`ActionRegistry -> rule module -> structured ActionResult -> StateDelta ->
EventLog -> Visibility/NPC Knowledge filtering`.

LLM output may describe an already-adjudicated action result. It may not decide
success, failure, damage, magic effects, hacking outcomes, deduction truth,
crafting output, stealth detection, combat consequences, or any canonical
state change.

## Not In v1.6

- Arbitrary code plugin execution.
- LLM world adjudication.
- LLM-decided gameplay results.
- LLM direct `GameState` mutation.
- Action Mods writing databases, files, `.env`, API keys, or local sensitive
  files.
- Action Mods bypassing `StateDelta`, `EventLog`, `Visibility`, or NPC
  Knowledge.
- Gameplay modules bypassing the unified `ActionRegistry`.
- Online mod marketplace, remote module download, cloud sync, accounts, or
  multiplayer collaboration.
- Large-scale war simulation.
- Full tactical board-game combat.
- MMO-scale economy simulation.
- Default enablement of untrusted modules.
- Automatic module application to active saves without compatibility and
  migration checks.

## Frozen Constraints

- All gameplay modules register through `ActionRegistry` or explicit rule
  module registration.
- All state changes use `StateDelta`.
- Every action records an `Event`.
- Every action result is structured and schema validated.
- LLMs cannot decide action success/failure or write canonical effects.
- LLMs cannot directly modify `GameState`.
- Action Mods are declarative by default and do not execute arbitrary code.
- Module import must run validation before install or enable.
- Module enablement must check save compatibility and migration impact.
- Hidden facts cannot enter `player_visible_state`.
- NPCs can only use information allowed by NPC Knowledge.
- Module debug data is debug-only and gated by `ENABLE_DEBUG_API`.
- Gameplay module tests use mock/fake/local_stub providers by default.
- The Gameplay Module Quality Gate must run for module packages and enabled
  module sets.

## Recommended Development Order

1. Gameplay Module Boundary Contract.
2. Gameplay Module Manifest.
3. Declarative Action Mod System.
4. Action Registry Extension.
5. Action DSL Preconditions / Checks / Effects.
6. Action Mod Validation.
7. Gameplay Module Import / Export.
8. Gameplay Module Quality Gate.
9. Gameplay Module Regression Playtests.
10. Gameplay Module Debugger.
11. Action Mod Authoring UI.
12. Magic System.
13. Hacking System.
14. Crafting System.
15. Investigation / Deduction System.
16. Travel / Survival System.
17. Stealth Expansion.
18. Combat Expansion.
19. Social Manipulation System.
20. Faction Mission System.
21. Domain / Base Management.

The first phase should start with the shared boundary, manifest, registry, DSL,
validation, and package safety. Domain modules should only land after the
Action Mod path can prove that a module cannot execute code, bypass
`StateDelta`, leak hidden data, or mutate active saves without explicit checks.

## Module Roadmap

### 1. Gameplay Module Boundary Contract

Goal: Define the formal boundary for gameplay modules, declarative action mods,
module packages, runtime action execution, active saves, debug data, and LLM
authority.

Data structures:

- `GameplayModulePolicy`
- `GameplayModuleBoundaryDecision`
- `GameplayModuleOperation`
- `ModuleRuntimeScope`
- `ModuleDebugData`
- `ModuleVisibilityRisk`

API changes:

- `GET /gameplay/modules/boundary`
- `POST /gameplay/modules/boundary/check`

Frontend changes:

- Add a local module boundary/status panel.
- Show module trust level, validation state, save compatibility, and whether
  debug data is enabled.

Tests:

- Module preview/import does not modify active `GameState`.
- Module action candidates cannot execute arbitrary code.
- Module actions require `StateDelta` and `Event`.
- LLM output cannot be accepted as gameplay adjudication.

Acceptance:

- Boundary document and policy are implemented.
- Tests prove module operations are draft/package/runtime-rule only.
- Debug-only data is never returned through player APIs.

Impact:

- `GameState`: no direct mutation.
- `StateDelta`/`EventLog`: required for all runtime effects.
- Content/mod package: establishes the module package boundary.
- Save migration: module enablement must declare compatibility.
- LLM: no new authority.
- Hidden data: must be redacted outside debug APIs.

### 2. Gameplay Module Manifest

Goal: Define metadata and declared capabilities for installable local gameplay
modules.

Data structures:

- `GameplayModuleManifest`
- `GameplayModuleDependency`
- `GameplayModuleCapability`
- `GameplayModuleCompatibility`
- `GameplayModuleTrustLevel`

API changes:

- `GET /gameplay/modules`
- `GET /gameplay/modules/{module_id}`
- `POST /gameplay/modules/{module_id}/validate`

Frontend changes:

- Module library list with dependency, compatibility, trust, and validation
  status.

Tests:

- Valid manifests load.
- Missing dependencies fail validation.
- Unsupported engine/schema versions are rejected.
- Manifest cannot include secrets or executable entrypoints.

Acceptance:

- Manifest is schema-validated.
- Module metadata is safe to display in normal UI.
- Enablement is impossible without compatibility metadata.

Impact:

- `GameState`: none until module action execution.
- Packages: adds module manifest format.
- Migration: manifest declares target schema and save requirements.
- LLM: no provider configuration or prompt secrets in manifest.
- Hidden data: normal manifest cannot contain hidden fact text.

### 3. Declarative Action Mod System

Goal: Allow local content packs to define new actions through declarative
schemas instead of executable code.

Data structures:

- `DeclarativeActionMod`
- `ActionModDefinition`
- `ActionModParameter`
- `ActionModResultTemplate`
- `ActionModVisibilityPolicy`

API changes:

- `POST /gameplay/action-mods/preview`
- `POST /gameplay/action-mods/validate`
- `POST /gameplay/action-mods/register-draft`

Frontend changes:

- Action mod preview showing parameters, allowed targets, result templates, and
  validation issues.

Tests:

- Action mods are parsed without code execution.
- Invalid schemas are rejected.
- Unsafe effects cannot be registered.
- Registration does not modify active saves.

Acceptance:

- A simple declarative action can be previewed and validated.
- No Python/JS/script execution path exists.
- Every effect must map to a permitted `StateDelta` template.

Impact:

- `GameState`: action definitions only; no active mutation at import.
- `StateDelta`/`EventLog`: runtime effects use declared delta templates.
- Packages: action mod definitions added to module packs.
- Migration: registered action IDs require save compatibility checks.
- LLM: may parse player intent into action ID only; cannot decide effects.
- Hidden data: target selectors must respect visibility and NPC knowledge.

### 4. Action Registry Extension

Goal: Extend the existing action dispatcher/registry to discover and resolve
core actions plus validated module actions through one path.

Data structures:

- `ActionRegistryEntry`
- `RegisteredActionHandler`
- `ActionResolutionContext`
- `ActionRegistryReport`

API changes:

- `GET /gameplay/actions`
- `POST /gameplay/actions/resolve-preview`

Frontend changes:

- Action registry inspector for debug/local authoring.

Tests:

- Core actions still resolve.
- Module actions cannot override protected core actions unless explicitly
  allowed.
- Disabled modules cannot provide runtime actions.
- Resolution still returns structured `ActionResult`.

Acceptance:

- All gameplay actions use a single registry surface.
- Registry records source module and trust state.
- Unknown or disabled actions fail safely.

Impact:

- `GameState`: no direct mutation.
- `StateDelta`/`EventLog`: registry requires structured result path.
- Packages: module-provided action IDs are namespaced.
- Migration: namespace collisions are blockers.
- LLM: intent parser can select action IDs, not adjudicate outcomes.
- Hidden data: registry metadata is player-safe by default.

### 5. Action DSL Preconditions / Checks / Effects

Goal: Provide a constrained DSL for action availability, rule checks, and
effects.

Data structures:

- `ActionDSL`
- `ActionPrecondition`
- `ActionCheck`
- `ActionEffect`
- `ActionTargetSelector`
- `ActionEffectTemplate`

API changes:

- `POST /gameplay/action-dsl/validate`
- `POST /gameplay/action-dsl/evaluate-preview`

Frontend changes:

- DSL issue viewer and effect preview in action mod authoring.

Tests:

- Preconditions evaluate deterministically.
- Checks cannot read hidden facts unless allowed by scope.
- Effects compile only to allowed `StateDelta` operations.
- Invalid paths are rejected.

Acceptance:

- DSL has no loops, imports, IO, reflection, or dynamic execution.
- Evaluation is deterministic and bounded.
- Effects are structured and auditable.

Impact:

- `GameState`: read-only during checks; write via deltas only.
- `StateDelta`/`EventLog`: each effect must map to evented deltas.
- Packages: DSL version included.
- Migration: DSL version changes require compatibility notes.
- LLM: cannot authoritatively evaluate checks.
- Hidden data: selectors must state visibility scope.

### 6. Action Mod Validation

Goal: Validate declarative action mods before registration, package export, or
module enablement.

Data structures:

- `ActionModValidationRequest`
- `ActionModValidationReport`
- `ActionModIssue`
- `ActionModSafetyFinding`

API changes:

- `POST /gameplay/action-mods/validate`
- `POST /gameplay/modules/{module_id}/action-mods/validate`

Frontend changes:

- Validation report with blockers, warnings, hidden-risk findings, migration
  impact, and suggested fixes.

Tests:

- Invalid target selectors fail.
- Hidden leak risk is blocked or debug-only.
- Effects outside allowed paths fail.
- Validation does not write disk or active state.

Acceptance:

- No module action can be enabled without validation.
- Validation blockers stop save/enable/export.
- Reports are redacted for normal UI.

Impact:

- `GameState`: none.
- Packages: validation report can be included as safe metadata.
- Migration: validation computes affected save fields.
- LLM: no LLM judge.
- Hidden data: normal reports redact sensitive values.

### 7. Action Mod Authoring UI

Goal: Provide a local visual authoring surface for declarative action mods.

Data structures:

- Uses `DeclarativeActionMod`, `ActionDSL`, and validation reports.

API changes:

- Uses action mod preview/validate/register-draft endpoints.

Frontend changes:

- Form and graph-style editor for action parameters, target selectors,
  preconditions, checks, effects, visibility policy, and debug notes.
- Diff and validation preview before explicit save.

Tests:

- Frontend build passes.
- Disabled authoring API degrades safely.
- Hidden/debug fields are not displayed in normal player UI.

Acceptance:

- Users can author a simple local action mod draft.
- Save requires validation.
- No active session mutation occurs.

Impact:

- `GameState`: authoring draft only.
- Packages: action mods can be exported/imported through module packages.
- Migration: UI displays compatibility impact.
- LLM: no generation required.
- Hidden data: hidden fields are visually marked and redacted in normal views.

### 8. Magic System

Goal: Add a deterministic magic gameplay module for spells, mana/costs,
resistances, conditions, and visible/hidden magical effects.

Data structures:

- `MagicModuleConfig`
- `SpellDefinition`
- `SpellCost`
- `SpellCheck`
- `MagicEffect`
- `MagicResistance`

API changes:

- `GET /gameplay/magic/spells`
- `POST /gameplay/magic/cast-preview`

Frontend changes:

- Spell list, target selector, cost preview, and debug effect preview.

Tests:

- Spell success/failure is rule-determined.
- Mana/cost/status effects use `StateDelta`.
- Hidden magical marks do not enter player visible state.
- NPC spell knowledge obeys NPC Knowledge.

Acceptance:

- Basic spell action path works through `ActionRegistry`.
- Every spell creates structured `ActionResult` and `Event`.
- No LLM-decided magic effects.

Impact:

- `GameState`: may add magic resources, effects, cooldowns.
- Packages: spell definitions in module packs.
- Migration: save compatibility for new actor/resource fields.
- LLM: narration only.
- Hidden data: secret spell effects are redacted unless discovered.

### 9. Hacking System

Goal: Add a deterministic cyber/hacking module for devices, access levels,
traces, alarms, lockouts, and data discovery.

Data structures:

- `HackingModuleConfig`
- `HackableDevice`
- `AccessLevel`
- `HackCheck`
- `TraceState`
- `HackingEffect`

API changes:

- `GET /gameplay/hacking/devices`
- `POST /gameplay/hacking/action-preview`

Frontend changes:

- Device/action preview, access status, risk, and trace visualization.

Tests:

- Hack results are rule-based.
- Unauthorized data remains hidden.
- Trace/alarm updates use `StateDelta` and `Event`.
- LLM cannot invent access.

Acceptance:

- Hacking actions register through `ActionRegistry`.
- Hidden data is revealed only via explicit discover deltas.
- Debug traces are debug API only.

Impact:

- `GameState`: device/access/trace fields may be added.
- Packages: hackable device content.
- Migration: save compatibility for devices.
- LLM: expression only.
- Hidden data: protected files/secrets stay hidden until discovered.

### 10. Crafting System

Goal: Add deterministic crafting recipes, tools, stations, quality tiers,
failure consequences, and inventory effects.

Data structures:

- `CraftingModuleConfig`
- `RecipeDefinition`
- `CraftingIngredient`
- `CraftingStation`
- `CraftingOutcome`
- `ItemQuality`

API changes:

- `GET /gameplay/crafting/recipes`
- `POST /gameplay/crafting/preview`

Frontend changes:

- Recipe browser, ingredient availability, station requirements, and output
  preview.

Tests:

- Recipe validation catches missing items.
- Inventory changes use `StateDelta`.
- Hidden recipes do not appear in player UI.
- Crafting failure is rule-driven.

Acceptance:

- Crafting actions produce structured results.
- No automatic economy rebalance.
- No LLM-generated authoritative item output.

Impact:

- `GameState`: inventory/item quality/crafting state.
- Packages: recipes and stations.
- Migration: recipe and item schema additions.
- LLM: can describe result after rules.
- Hidden data: secret recipes are gated by discovery/knowledge.

### 11. Investigation / Deduction System

Goal: Add structured investigation tools for clues, hypotheses, evidence,
deduction checks, and case conclusions without letting LLM decide truth.

Data structures:

- `InvestigationModuleConfig`
- `EvidenceState`
- `Hypothesis`
- `DeductionRule`
- `CaseConclusion`
- `ClueVisibility`

API changes:

- `GET /gameplay/investigation/cases`
- `POST /gameplay/investigation/deduce-preview`

Frontend changes:

- Evidence board, hypothesis checklist, known/unknown clue separation, and
  deduction validation issues.

Tests:

- Player cannot conclude from unknown evidence.
- Hidden truth facts remain hidden.
- Deduction outcome is rule-based.
- Events record evidence discovery and conclusions.

Acceptance:

- Deduction actions use ActionRegistry and structured results.
- Hidden truth never appears in normal UI before discovery.
- LLM cannot assert canonical culprit/truth.

Impact:

- `GameState`: evidence, hypothesis, case progress fields.
- Packages: case modules and evidence data.
- Migration: case state compatibility.
- LLM: narration only.
- Hidden data: truth facts are debug/hidden until revealed by rules.

### 12. Travel / Survival System

Goal: Add travel cost, weather/exposure, fatigue, provisions, hazards, and
survival checks.

Data structures:

- `TravelSurvivalConfig`
- `TravelRouteRule`
- `SurvivalResource`
- `HazardCheck`
- `ExposureState`
- `RestOutcome`

API changes:

- `GET /gameplay/travel/routes`
- `POST /gameplay/travel/preview`
- `POST /gameplay/survival/check-preview`

Frontend changes:

- Route cost preview, resource warning, hazard visibility, and survival status.

Tests:

- Route/hazard checks are deterministic.
- Resource changes use `StateDelta`.
- Hidden routes remain hidden.
- NPC travel knowledge respects NPC Knowledge.

Acceptance:

- Travel/survival actions register through ActionRegistry.
- Existing map visibility is preserved.
- No unbounded background simulation.

Impact:

- `GameState`: fatigue, provisions, exposure, route state.
- Packages: route/hazard definitions.
- Migration: optional survival fields.
- LLM: describes adjudicated travel.
- Hidden data: undiscovered routes/hazards do not leak.

### 13. Stealth Expansion

Goal: Extend stealth with detection levels, cover, noise, suspicion, patrol
awareness, and stealth consequences.

Data structures:

- `StealthModuleConfig`
- `DetectionState`
- `NoiseEvent`
- `CoverState`
- `SuspicionChange`
- `StealthCheck`

API changes:

- `GET /gameplay/stealth/status`
- `POST /gameplay/stealth/preview`

Frontend changes:

- Local debug stealth inspector and player-safe stealth status.

Tests:

- Hidden NPCs do not leak through stealth UI.
- Detection changes use deltas and events.
- NPC awareness uses visible/known context.
- Results are deterministic.

Acceptance:

- Stealth expands existing sneak/search without breaking old actions.
- Debug-only detection reasons stay debug-only.

Impact:

- `GameState`: suspicion/detection/cover fields.
- Packages: stealth tags and patrol hints.
- Migration: backwards-compatible optional fields.
- LLM: cannot decide detection.
- Hidden data: hidden actors remain redacted unless detected.

### 14. Combat Expansion

Goal: Extend lightweight combat with abilities, non-lethal options, conditions,
resistances, armor, reactions, and encounter safety checks.

Data structures:

- `CombatModuleConfig`
- `CombatAbility`
- `DamageProfile`
- `ArmorProfile`
- `CombatCondition`
- `CombatReaction`

API changes:

- `GET /gameplay/combat/abilities`
- `POST /gameplay/combat/action-preview`

Frontend changes:

- Combat ability browser, risk preview, non-lethal indicators, and debug roll
  trace.

Tests:

- Combat outcomes remain rule-based.
- HP/status changes use `StateDelta`.
- Dead/incapacitated actors are handled safely.
- Hidden combatants are not player-visible.

Acceptance:

- Combat actions remain structured and evented.
- No tactical grid or large war simulation.
- LLM cannot determine damage or victory.

Impact:

- `GameState`: expanded combat fields and conditions.
- Packages: ability definitions and encounter metadata.
- Migration: combat field compatibility.
- LLM: narration only.
- Hidden data: hidden combatants/reasons stay redacted.

### 15. Social Manipulation System

Goal: Add structured persuasion, intimidation, bribery, deception, reputation
pressure, favors, and social consequences.

Data structures:

- `SocialManipulationConfig`
- `SocialActionDefinition`
- `SocialCheck`
- `FavorState`
- `LeverageState`
- `SocialConsequence`

API changes:

- `GET /gameplay/social/actions`
- `POST /gameplay/social/preview`

Frontend changes:

- Social action preview with known leverage, visible risks, and relationship
  impact.

Tests:

- NPC cannot react to unknown leverage.
- Relationship/faction effects use deltas/events.
- Hidden relationships do not leak.
- LLM cannot decide persuasion success.

Acceptance:

- Social actions are deterministic and bounded.
- Relationship/RP tone systems remain expression layers, not authority.

Impact:

- `GameState`: favors/leverage/social cooldowns.
- Packages: social action definitions.
- Migration: optional social state fields.
- LLM: dialogue style only.
- Hidden data: secret leverage is gated by knowledge/visibility.

### 16. Faction Mission System

Goal: Add faction-issued mission templates, ranks, reputation gates, rewards,
and failure consequences.

Data structures:

- `FactionMissionConfig`
- `FactionMissionDefinition`
- `FactionMissionState`
- `FactionRewardPolicy`
- `FactionFailureConsequence`

API changes:

- `GET /gameplay/factions/{faction_id}/missions`
- `POST /gameplay/faction-missions/preview`

Frontend changes:

- Mission board with player-visible missions and debug-only hidden hooks.

Tests:

- Hidden faction missions do not appear to the player.
- Mission rewards/consequences use deltas and events.
- Reputation gates are rule-based.
- NPC/faction knowledge boundaries hold.

Acceptance:

- Faction missions integrate with quests/reputation without replacing them.
- No large-scale war simulation.

Impact:

- `GameState`: mission state and faction progress.
- Packages: mission definitions.
- Migration: mission state compatibility.
- LLM: can narrate assigned missions only.
- Hidden data: secret missions remain hidden.

### 17. Domain / Base Management

Goal: Add lightweight base/domain management for rooms, facilities, upkeep,
staff, storage, production queues, and local events.

Data structures:

- `DomainModuleConfig`
- `BaseState`
- `FacilityDefinition`
- `FacilityState`
- `UpkeepRule`
- `DomainAction`

API changes:

- `GET /gameplay/domain/status`
- `POST /gameplay/domain/action-preview`

Frontend changes:

- Base overview, facility list, upkeep warnings, and action preview.

Tests:

- Facility changes use `StateDelta`.
- Production queues are bounded and deterministic.
- Hidden staff/facilities do not leak.
- Save/load preserves base state.

Acceptance:

- Lightweight base management works without MMO economy complexity.
- No background infinite simulation.

Impact:

- `GameState`: base/facility/storage/queue fields.
- Packages: facility definitions and starter bases.
- Migration: base state compatibility.
- LLM: narration only.
- Hidden data: hidden facilities and debug upkeep reasons are redacted.

### 18. Gameplay Module Quality Gate

Goal: Add quality checks for module manifests, action mods, DSL effects,
hidden leaks, compatibility, validation coverage, and regression coverage.

Data structures:

- `GameplayModuleQualityRequest`
- `GameplayModuleQualityReport`
- `GameplayModuleQualityIssue`
- `GameplayModuleCoverageSummary`

API changes:

- `POST /gameplay/modules/quality-gate`

Frontend changes:

- Quality gate report in module library and authoring UI.

Tests:

- Unsafe module fails.
- Missing validation coverage warns.
- Hidden leak risk blocks or warns according to severity.
- Report redacts hidden details.

Acceptance:

- Quality gate can run on one module or module set.
- Export/enable paths can require a passing gate.

Impact:

- `GameState`: none.
- Packages: quality report metadata.
- Migration: compatibility blockers are surfaced.
- LLM: no LLM judge.
- Hidden data: report is normal-safe by default.

### 19. Gameplay Module Regression Playtests

Goal: Add deterministic playtests for module action flows and boundary
invariants.

Data structures:

- `GameplayModuleRegressionScenario`
- `GameplayModuleRegressionRun`
- `GameplayModuleRegressionReport`

API/CLI changes:

- `POST /gameplay/modules/regression/run`
- `python -m backend.app.tools.gameplay_module_regression`

Frontend changes:

- Regression run summary in module debugger/quality panel.

Tests:

- Magic/hacking/crafting/investigation sample scenarios pass.
- Hidden leak scenarios are caught.
- No real LLM calls.
- Active saves are not modified.

Acceptance:

- Regression suite covers boundary, StateDelta/Event, visibility, and package
  safety.
- Results are deterministic.

Impact:

- `GameState`: temp saves only.
- Packages: optional regression fixtures.
- Migration: regression can exercise migration impact.
- LLM: mock/fake only by default.
- Hidden data: forbidden visible facts are asserted.

### 20. Gameplay Module Debugger

Goal: Provide local debug APIs and UI for module registry, action resolution,
DSL evaluation, generated deltas, events, and hidden/debug reasons.

Data structures:

- `GameplayModuleDebugSummary`
- `ActionResolutionTrace`
- `ActionDSLTrace`
- `ModuleEventTrace`

API changes:

- `GET /debug/gameplay/modules`
- `POST /debug/gameplay/actions/trace`

Frontend changes:

- Debug-only module inspector and action trace panel.

Tests:

- Debug API disabled returns unavailable.
- Player API never returns debug traces.
- Hidden text is redacted unless explicit debug policy allows.
- Trace does not modify state.

Acceptance:

- Debugger is local/debug-only.
- It can explain why an action is available, blocked, or unsafe.

Impact:

- `GameState`: read-only/dry-run.
- Packages: no package changes.
- Migration: debugger displays compatibility impact.
- LLM: no calls.
- Hidden data: debug API only; normal UI redacted.

### 21. Gameplay Module Import / Export

Goal: Safely import/export local gameplay module packages, action mods,
domain configs, quality reports, and regression fixtures.

Data structures:

- `GameplayModulePackageManifest`
- `GameplayModuleImportDryRun`
- `GameplayModuleImportReport`
- `GameplayModuleExportProfile`

API changes:

- `POST /gameplay/modules/export`
- `POST /gameplay/modules/import-dry-run`
- `POST /gameplay/modules/import-apply`

Frontend changes:

- Module package import/export UI with validation, compatibility, quality, and
  explicit enablement flow.

Tests:

- Zip slip/path traversal is rejected.
- Executable files are rejected.
- Import dry-run writes nothing.
- Apply requires validation and explicit confirmation.
- Safe export excludes secrets and hidden text by default.

Acceptance:

- Module packages are local, declarative, and non-executable.
- Import does not enable untrusted modules by default.
- Save compatibility must be checked before enablement.

Impact:

- `GameState`: no active mutation at import.
- Packages: module package manifest and profiles.
- Migration: enablement includes migration impact.
- LLM: no provider config/secrets in package.
- Hidden data: safe export redacts hidden content.

## v1.6 Integration Test Requirements

- Boundary tests prove module preview/import/validate do not write active
  `GameState`.
- Action registry tests prove core and module actions resolve through the same
  structured path.
- DSL tests prove no arbitrary code, IO, loops, dynamic imports, or unsafe
  paths are allowed.
- Runtime tests prove every module action returns structured `ActionResult`,
  `StateDelta`, and `Event`.
- Visibility tests prove hidden facts, NPC secrets, hidden actors, hidden
  relationships, hidden gameplay state, and debug data do not enter player
  APIs or narrator prompts.
- NPC Knowledge tests prove NPCs cannot use unknown facts for module actions.
- Domain module tests cover magic, hacking, crafting, investigation, travel,
  stealth, combat, social manipulation, faction missions, and base management
  at smoke/regression level.
- Package tests cover module import/export, zip slip, executable rejection,
  sensitive file rejection, manifest validation, checksum, dry-run, and save
  compatibility.
- Quality gate tests prove unsafe modules are blocked and safe modules pass.
- Regression playtests are deterministic and use mock/fake/local_stub providers.
- Frontend build passes and disabled APIs degrade safely.
- No tests call real external LLM APIs by default.

## Final Acceptance Standard

v1.6 is accepted when:

- The Gameplay Module Boundary is documented and enforced by policy/tests.
- Module manifests, declarative Action Mods, ActionRegistry extension, DSL,
  validation, import/export, quality gate, regression playtests, and debugger
  are implemented.
- At least representative gameplay modules are available for magic, hacking,
  crafting, investigation/deduction, travel/survival, stealth, combat, social
  manipulation, faction missions, and domain/base management.
- Every gameplay action produces structured `ActionResult`.
- Every runtime state change is a `StateDelta`.
- Every gameplay action records an `Event`.
- No module executes arbitrary code.
- No module bypasses Visibility, NPC Knowledge, EventLog, or save migration
  checks.
- LLMs remain language-layer only and never decide canonical gameplay results.
- Hidden facts, NPC secrets, gameplay hidden state, module debug traces, and
  raw state deltas are not exposed to player APIs or normal UI.
- `python -m pytest` and `cd frontend && npm.cmd run build` pass.

## v1.7 Candidate Directions

- Advanced world simulation orchestration across multiple enabled modules.
- Lightweight encounter director and pacing tools, still rule-based.
- Visual module dependency graph and save migration assistant.
- More domain-specific authoring packs for genre modules.
- Expanded deterministic playtest generation for gameplay modules.
- Module performance profiling and budget visualization.
- Optional local-only LLM-assisted module draft generation with strict
  validation and fake-provider default.
- Desktop packaging hardening for local studio workflows.
