# v2.7 LLM Boundary Audit

## Verdict

v2.7 Advanced World Simulation Modules are **not blocked** for acceptance on
LLM authority grounds in the current code. The implemented advanced module MVPs
resolve combat, economy, faction war, magic, hacking, crafting, deduction,
survival/travel, and cultivation through local deterministic or seeded-rule
helpers. The audited v2.7 module code does not call Provider Gateway, concrete
providers, OpenAI, `generate_text`, `generate_json`, or `call_llm`.

Verification date: 2026-05-22.

## Audited Files

- `backend/app/engine/advanced_modules.py`
- `backend/app/engine/module_state.py`
- `backend/app/playtesting/module_playtest.py`
- `backend/app/quality/module_quality_gate.py`
- `backend/app/quality/module_compatibility_stress.py`
- `backend/tests/test_v27_advanced_modules.py`
- `backend/tests/test_v27_advanced_module_integration_regression.py`
- `docs/V2_7_ROADMAP.md`
- `docs/LLM_PROTOCOL.md`

## Checks Performed

- Searched v2.7 module code and tests for `call_llm`, `ProviderGateway`,
  `OpenAI`, `openai`, `generate_text`, `generate_json`, provider references,
  prompts, raw `state_deltas`, and hidden leak sentinels.
- Reviewed v2.7 advanced module rule helpers for outcome authority.
- Reviewed module playtest and quality gate code for LLM-based pass/fail.
- Reviewed v2.7 tests for real provider/API usage.
- Reviewed LLM protocol and roadmap boundaries for provider gateway and
  world-authority language.

## Passed Items

1. **Tactical Combat**
   - `resolve_tactical_action` uses local AP, stance, cover, and seeded/random
     strike logic.
   - No LLM decides hit, damage, death, stance, AP consumption, or encounter
     state.
   - Death and incapacitation remain outside the tactical MVP and are not
     delegated to an LLM.

2. **Economy Simulation**
   - `economy_sim_tick` computes `price_index` from supply, demand, scarcity,
     and route status.
   - It does not call an LLM for pricing and does not overwrite item
     `base_price`.

3. **Faction War**
   - `faction_war_tick` computes morale, supply, and pressure from local state,
     known rumor pressure, and optional economy route penalty.
   - It does not call an LLM to decide control, victory, morale, supply, or war
     phase.

4. **Magic**
   - `resolve_magic_action` checks known spell, mana, target/action validity,
     and declared spell effects.
   - Spell effects are declared data and filtered to module paths beginning
     with `modules.magic.` unless an explicit engine-owned consequence flag is
     used for public illegal magic.
   - No LLM freely generates spell effects.

5. **Hacking**
   - `resolve_hacking_action` uses local object state, tool/inventory checks,
     security level, and seeded randomness.
   - It does not access real networks and does not call an LLM to decide hack
     success or extracted logs.

6. **Crafting**
   - `resolve_craft_item` validates recipe, materials, workstation tags, and
     seeded success/failure.
   - Outputs come from `RecipeDefinition`; no LLM generates products.

7. **Deduction**
   - `resolve_deduction_action` rejects hidden evidence and counts/tests known
     facts only.
   - Hypotheses are drafts/proposals and do not become world facts.
   - No LLM judges truth or solves cases.

8. **Survival / Travel**
   - `resolve_survival_action` uses route time, fatigue, supplies/forage rules,
     and seeded risk.
   - Hidden route danger is not included in visible event summaries.
   - No LLM judges route risk.

9. **Cultivation**
   - `resolve_cultivation_action` uses known techniques, progress, pill/status
     modifiers, and seeded breakthrough rules.
   - Hidden techniques are rejected.
   - No LLM decides breakthrough success.

10. **Module Actions**
    - v2.7 module helpers do not contain `call_llm`.
    - Advanced module tests include static checks for no `eval`, no `exec`, no
      Provider Gateway reference, and no OpenAI reference in the advanced module
      implementation.

11. **Provider Gateway Boundary**
    - Provider Gateway remains the documented only model entry for text/JSON
      generation.
    - v2.7 rule modules do not bypass Provider Gateway because they do not call
      models at all for rule adjudication.

12. **Prompt / Hidden Data Boundary**
    - v2.7 advanced modules do not construct provider prompts.
    - Hidden combatants, markets, war regions, hacking logs, evidence, route
      dangers, and cultivation techniques are filtered or rejected in visible
      summaries/tests.
    - No reviewed v2.7 path sends hidden facts or raw `state_deltas` to a
      provider prompt.

13. **GameState Authority**
    - v2.7 module helpers return `ActionResult` and `StateDelta`; tests apply
      deltas explicitly.
    - Module playtests check EventLog and save/load coverage.
    - LLM output is not used as a source of `StateDelta`.

14. **Tests / Real APIs**
    - v2.7 integration tests use local rule helpers, temporary state, temporary
      SQLite through TestClient setup, and mock provider settings.
    - No real OpenAI, relay, local HTTP model, or provider API call is made by
      v2.7 tests.

15. **Quality Gate**
    - `run_module_quality_gate` aggregates local playtest reports,
      compatibility stress reports, migration/permission/action checks, and
      hidden leak flags.
    - It does not call an LLM to judge safety or pass/fail.

## Risk Items

1. **ActionRegistry exposure is still mixed**
   - Some v2.7 module MVP helpers are direct resolver functions rather than
     fully registered action handlers in the runtime `ActionRegistry`.
   - This is not an LLM authority issue, but future player-facing module
     actions should be wired through `ActionRegistry` consistently so the same
     action discovery, conflict, and audit boundaries apply.

2. **Magic declared effects need continued schema review**
   - Current magic effects are only applied if their path starts with
     `modules.magic.`. This blocks broad GameState writes from spell effect
     data in the MVP.
   - Future richer spell DSLs should keep this whitelist and route non-module
     consequences through explicit engine-owned proposal rules.

3. **No prompt construction today means no module-prompt leak today**
   - The current v2.7 module layer does not build prompts. If future Novel,
     Tavern, or World narration uses module summaries as prompt input, that
     prompt builder must use safe summaries only and continue excluding hidden
     facts, debug data, and raw `state_deltas`.

4. **Quality Gate is MVP-level**
   - The module quality gate checks reports and blockers but is not a complete
     formal proof of no LLM authority misuse in all future modules.
   - This is acceptable for v2.7 MVP but should be expanded as module runtime
     registration deepens.

## High-Risk Issues

None found in the current v2.7 implementation.

## Medium-Risk Issues

1. **Incomplete runtime ActionRegistry integration for every advanced helper**
   - Severity: medium.
   - Reason: Direct helper invocation in tests is safe and deterministic, but
     runtime player-facing use should converge on `ActionRegistry`.
   - Impact: Not an LLM boundary blocker, but it affects consistency of action
     metadata, conflict checks, and auditability.

2. **Future prompt use of module summaries needs explicit safe-summary contract**
   - Severity: medium.
   - Reason: v2.7 currently avoids prompts entirely. Future narrative use could
     accidentally include hidden module data if it consumes raw module state.
   - Impact: Not a current blocker; document and test before any provider prompt
     integration.

## Minor Issues

1. The v2.7 modules are MVP rule slices, not full tactical/economic/war/magic
   engines. Documentation should continue to describe them as deterministic MVP
   modules.
2. Static tests check absence of obvious provider and arbitrary-code strings in
   `advanced_modules.py`; broader static enforcement across future module files
   should be added as the module surface grows.

## Recommendations

1. For the next v2.7 hardening slice, register each advanced module action
   through `ActionRegistry` in a shared bootstrap function and test action id /
   alias conflicts there.
2. Add a `build_module_prompt_safe_summary` contract only when modules are used
   in narration prompts. It should exclude hidden data, debug data, raw module
   state, and raw `StateDelta`.
3. Keep magic, hacking, deduction, survival, and cultivation effects limited to
   declared DSL/state paths and explicit engine-owned consequence proposals.
4. Extend quality gate static checks to scan all future `advanced_modules/*`
   files for provider calls, `eval`, `exec`, network/file access, and prompt
   construction that includes hidden fields.
5. Keep tests configured with mock/local providers only and continue requiring
   no real API calls in CI/default test runs.

## Acceptance Impact

This audit does **not block v2.7 acceptance**.

Current v2.7 code preserves the LLM boundary:

- LLMs do not judge combat, economy, war, magic, hacking, crafting, deduction,
  survival/travel, or cultivation outcomes.
- Module actions do not call LLMs.
- Provider Gateway remains the only model-entry boundary for language tasks.
- Hidden facts and raw `state_deltas` are not sent to module prompts because
  modules do not build prompts.
- LLM output cannot directly modify `GameState`.
- Quality Gate is local and deterministic, not LLM-judged.
