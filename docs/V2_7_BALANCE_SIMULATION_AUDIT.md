# v2.7 Balance / Simulation Audit

## Verification Date

2026-05-22

## Scope

This audit reviews the v2.7 Advanced World Simulation Modules balance and simulation behavior. It focuses on deterministic rules, bounded resources, repeated tick safety, infinite resource risks, visibility boundaries, playtest coverage, and compatibility stress coverage.

Reviewed implementation areas:

- `backend/app/engine/advanced_modules.py`
- `backend/app/playtesting/module_playtest.py`
- `backend/app/quality/module_compatibility_stress.py`
- `backend/app/quality/module_quality_gate.py`
- `backend/tests/test_v27_advanced_modules.py`
- `backend/tests/test_v27_advanced_module_integration_regression.py`

No business code was modified for this audit.

## Passed Items

1. Tactical Combat AP is guarded in the resolver.
   - `resolve_tactical_action` rejects actions when `action_points <= 0`.
   - Normal tactical actions consume exactly one AP through a `StateDelta`.
   - `take_cover` clamps cover to `0..5`.

2. Tactical Combat does not currently create a guaranteed death loop.
   - The v2.7 tactical slice records `last_strike_result` only.
   - It does not resolve damage, death, or life-state transitions.
   - Death/unconsciousness remains outside tactical hit text and is still expected to be handled by life-state rules.

3. Economy Simulation does not overwrite item base prices.
   - `economy_sim_tick` writes module-scoped `price_index` and `scarcity`.
   - `economy_price_modifier` reads the module price modifier.
   - Tests assert that `WorldObjectState.base_price` is not overwritten.

4. Economy ticks are deterministic for a fixed state.
   - The tick formula derives scarcity and price from current supply, demand, and route status.
   - It does not call LLMs or random functions.

5. Faction War core values are schema-bounded.
   - `control_score`, `front_pressure`, `morale`, and `supply_level` use `0..100` schema bounds.
   - `faction_war_tick` clamps morale, supply, and pressure into `0..100`.

6. Magic cast cost cannot make mana negative through the normal cast path.
   - `cast_spell` checks `mana >= cost` before producing the mana delta.
   - Spell costs are schema-limited to non-negative values.

7. Hacking does not access real networks and is deterministic with a fixed seed.
   - `resolve_hacking_action` uses in-world `HackableObjectState` only.
   - Success/failure is based on seeded local random plus in-world tool state.
   - Hidden logs are filtered from `extract_logs`.

8. Deduction does not directly leak hidden truth in the reviewed paths.
   - Hidden evidence inspection returns invalid.
   - `test_hypothesis` counts only public or player-known facts.
   - Hypotheses are module records and do not write world facts.

9. Survival fatigue is bounded in the normal travel/rest paths.
   - Travel clamps fatigue to max `100`.
   - Camp/rest clamps fatigue to min `0`.
   - Hidden route danger is not included in visible event text.

10. Cultivation breakthrough is deterministic with a fixed seed.
    - `attempt_breakthrough` uses seeded local random.
    - Hidden techniques are rejected unless known and non-hidden.
    - LLMs do not decide breakthrough success.

11. Module playtests cover one smoke path for each v2.7 module.
    - Tactical, economy, faction, magic, hacking, crafting, deduction, survival, and cultivation scenarios exist.
    - Reports check Event presence, StateDelta count, save/load stability, and hidden leak sentinels.

12. Compatibility stress covers the planned module combinations.
    - `tactical_combat + magic`
    - `tactical_combat + hacking`
    - `economy_sim + faction_war`
    - `crafting + economy_sim`
    - `survival_travel + faction_war`
    - `cultivation + magic`
    - `deduction + crime_witness`
    - all-enabled smoke set

## High-Risk Balance Issues

### 1. Crafting can mint unlimited items if a package defines zero-input or net-positive recipes

`RecipeDefinition.input_items` defaults to an empty dict, and `resolve_craft_item` does not reject recipes with no inputs. If a module/package defines a recipe with empty `input_items` and non-empty `output_items`, repeated `craft_item` calls can generate unlimited items.

The same class of issue can occur with net-positive recipes, for example consuming one item and outputting two of the same item, unless that is explicitly intended and quality-gated.

Risk:

- Infinite item creation.
- Economy destabilization when paired with `economy_sim`.
- Quest/item progression bypass if crafted outputs include important items.

Recommended fix:

- Add recipe validation before v2.7 release acceptance:
  - Reject output-producing recipes with empty `input_items` unless an explicit `allow_free_recipe=true` authoring flag exists and the recipe is marked non-economy/non-quest.
  - Reject or warn on same-item net-positive recipes.
  - Require either material cost, time cost, workstation, or explicit limited-use source for production recipes.
  - Add tests for zero-input recipes, net-positive recipes, and important-item outputs.

Blocking assessment:

- This is a v2.7 balance blocker if the crafting module is shipped as player-facing or enabled by default.
- It is not a platform security blocker if crafting remains disabled/draft-only, but it should be fixed before claiming final v2.7 gameplay balance acceptance.

## Medium-Risk Balance Issues

### 1. Economy price index is not capped

`price_index = 1.0 + scarcity / 100`, with scarcity derived from demand minus supply. The value is not recursive, so it does not compound by itself. However, very large authored demand/supply values can produce very large price modifiers.

Recommended fix:

- Add module validation bounds for supply and demand.
- Add a configurable max `price_index`, such as `10.0`, unless a world explicitly opts into extreme prices.
- Add tests for extreme supply/demand values.

### 2. Faction War can emit repeated same-shape tick events

`faction_war_tick` is deterministic and bounded, but it does not record a `last_updated_turn` per region. Calling the tick repeatedly for the same turn can emit repeated module tick events and repeated identical deltas.

Recommended fix:

- Add per-region `last_updated_turn` or have the world tick orchestrator enforce one faction-war tick per turn.
- Add tests for idempotency within the same turn.

### 3. Magic focus has no maximum, and spell effects can set arbitrary `modules.magic.*` values

`rest_focus` increments focus without a cap. `SpellDefinition.effects` accepts any `modules.magic.*` path and value. This keeps effects module-scoped, but does not deeply validate caster resource bounds or list/value shapes.

Recommended fix:

- Add optional `max_mana` / `max_focus` or module-level resource caps.
- Validate spell effect paths against allowed magic subpaths.
- Re-validate resulting `MagicState` after generated spell deltas in tests.

### 4. Hacking trace can grow without a cap and access states are free-form strings

Failures increase `trace_level` without a maximum. `access_state` is a string rather than a constrained enum, which can allow inconsistent states across content.

Recommended fix:

- Cap `trace_level` or define escalation thresholds.
- Replace free-form access state with a documented enum such as `locked`, `scanned`, `access_granted`, `disabled`, `alerted`.
- Add repeated failure tests.

### 5. Survival forage can generate supplies without time, fatigue, or location limits

`forage` can add `supplies` on repeated successes. It does not currently consume time, increase fatigue, check biome/location resources, or apply a cooldown.

Recommended fix:

- Make `forage` consume time and/or fatigue.
- Add route/location forage limits or a depletion marker.
- Add tests for repeated forage and supply growth.

### 6. Cultivation progress is unbounded before breakthrough

`meditate` and `practice_technique` increase progress without a cap. Breakthrough difficulty is non-negative but not bounded to the random roll range, so difficulty `0` is always successful and difficulty above `9` is impossible.

Recommended fix:

- Clamp progress to the current breakthrough threshold or a documented overflow limit.
- Validate `difficulty` within `0..9`, or document and test impossible/automatic cases.
- Add realm graph validation so invalid or cyclic realm transitions are reported.

### 7. Tactical Combat has no turn advancement or encounter end condition in the reviewed helper

AP prevents infinite same-turn actions through the normal resolver, but there is no reviewed rule for ending a turn, refreshing AP, advancing `active_combatant_id`, or ending an encounter.

Recommended fix:

- Add a minimal deterministic turn-advance action/rule.
- Add encounter end conditions and tests.
- Keep death/KO delegation to life-state rules.

## Minor Issues

1. Module event IDs can collide for repeated same action, same turn, same delta count.
   - `_module_event` uses `f"{action_id}:{state.turn}:{len(deltas)}"`.
   - This is mostly an audit/replay hygiene issue, but repeated same-turn actions can produce identical IDs.

2. Economy hidden market filtering is tested through event text, but no dedicated `economy_visible_summary` helper was reviewed.
   - The event summary is safe, but a future UI should avoid rendering hidden market module state directly.

3. Faction War `control_score` is bounded but not currently changed by `faction_war_tick`.
   - This is acceptable for an MVP regional-pressure slice, but v2.7 docs should avoid implying full control simulation until a control delta rule exists.

4. Survival hunger/thirst schemas are bounded but the v2.7 helper does not yet advance hunger/thirst.
   - This is a scope limitation, not an active runaway risk.

5. Playtest scenarios are smoke tests rather than adversarial balance tests.
   - They cover happy paths and hidden leak sentinels, but not extreme values, repeat abuse, resource loops, or tick idempotency.

6. Compatibility stress is structural, not numerical.
   - It catches namespace/action/permission/migration/hidden-leak conflicts.
   - It does not currently detect economy/crafting inflation loops, repeated forage supply loops, or repeated tick duplication.

## Recommendations

1. Fix crafting recipe validation first.
   - Block zero-input output recipes by default.
   - Detect same-item net-positive recipes.
   - Gate important-item crafting through explicit content validation.

2. Add resource and price caps.
   - Economy `price_index` max.
   - Magic focus/mana caps.
   - Hacking trace max.
   - Cultivation progress and breakthrough difficulty bounds.

3. Add tick idempotency checks.
   - `economy_sim_tick` and `faction_war_tick` should either record/update `last_updated_turn` or be called only once per world tick by an orchestrator with tests.

4. Expand playtests into adversarial balance tests.
   - Repeated crafting.
   - Repeated forage.
   - Extreme economy supply/demand.
   - Repeated faction tick same turn.
   - Breakthrough impossible/automatic boundaries.

5. Extend Module Quality Gate with balance checks.
   - Recipe minting.
   - Price index cap violations.
   - Resource cap violations.
   - Unbounded trace/progress warnings.
   - Missing turn/end condition warnings for tactical encounters.

6. Keep UI and docs precise.
   - Describe v2.7 as lightweight deterministic module MVPs.
   - Do not claim full tactical, economic, war, crafting, survival, or cultivation balance until adversarial tests pass.

## Is This Blocking v2.7?

Conditional yes.

The reviewed v2.7 modules pass the core authority boundary: deterministic local rules, `StateDelta`, `EventLog`, visibility filtering, no real API calls, and no LLM rule judging. However, the crafting zero-input/net-positive recipe issue is a high-risk balance blocker for a player-facing v2.7 release if `craft_item` is enabled with arbitrary package recipes.

Recommended release position:

- v2.7 can continue toward acceptance if crafting remains draft/disabled or recipe validation is fixed before release.
- v2.7 should not claim final player-facing crafting balance until zero-input/net-positive recipes are rejected or explicitly gated.
- The remaining medium and minor issues are not standalone release blockers, but should become v2.7 hardening tasks or v2.8 Quality Studio checks.
