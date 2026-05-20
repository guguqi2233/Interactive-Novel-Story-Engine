# v1.6 LLM Boundary Audit

Verification Date: 2026-05-20

Scope:

- v1.6 gameplay module policy, manifest, loader, package import/export,
  debugger, quality gate, regression playtests, declarative actions, Action DSL,
  ActionRegistry extension, and domain modules.
- Domain modules reviewed: Magic, Hacking, Crafting, Investigation /
  Deduction, Travel / Survival, Stealth Expansion, Combat Expansion, Social
  Manipulation, Faction Mission, Domain / Base Management.
- Supporting tests reviewed for real-provider exposure.

Commands / Evidence:

- `rg "LLM|llm|provider|generate_text|generate_json|create_llm_provider|ProviderRouter|PromptProfile|prompt" backend\app\engine backend\app\core backend\app\quality backend\app\playtesting backend\app\tools ...`
- `rg "GameState|state\.|apply_delta|StateDelta|state_deltas|resolve_with_event|Event" backend\app\engine\rules\*.py backend\app\engine\actions\declarative.py`
- Reviewed `docs/V1_6_ROADMAP.md`
- Reviewed `docs/GAMEPLAY_MODULE_BOUNDARY.md`

## Passed Items

1. v1.6 gameplay modules do not call LLM providers for adjudication.
   - `magic.py`, `hacking.py`, `crafting.py`, `investigation.py`,
     `survival.py`, `stealth.py`, `combat.py`, `social_manipulation.py`,
     `faction_missions.py`, and `domain.py` import `PlayerIntent` schemas but
     do not import provider factory, concrete providers, or call
     `generate_text` / `generate_json`.

2. Declarative Action Mod does not call LLM to judge results.
   - `DeclarativeActionHandler` evaluates target, preconditions, checks, and
     outcomes from declarative schemas and returns structured `ActionResult`,
     `StateDelta`, and `Event`.

3. Magic System does not let LLM decide spell effects.
   - Spell success and effects are based on `SpellDefinition`, Action DSL
     checks/effects, resources, visibility, and crime/witness rules.

4. Hacking System does not let LLM decide intrusion results.
   - Hacking outcomes are deterministic/rule based using difficulty, tool
     power, seed/RNG, target state, and monitoring rules.

5. Crafting System does not let LLM decide recipe results.
   - Crafting resolves against `RecipeDefinition`, inventory, station tags,
     materials, and failure policy.

6. Investigation System does not let LLM decide truth.
   - Evidence, testimony, hypothesis, accusation, and quest progress are
     derived from structured facts/evidence/hypothesis state.

7. Survival System does not let LLM decide travel risk.
   - Travel/rest/consume/forage/camp actions use declared route/weather/state
     rules and seeded deterministic risk checks.

8. Stealth Expansion does not let LLM decide detection.
   - Detection is computed from rule inputs such as light, cover, noise,
     stealth modifier, NPC alertness, and hidden observer policy.

9. Combat Expansion does not let LLM decide hit, damage, death, or non-lethal
   outcome.
   - Combat resolution uses combat stats, stance, weapon tags, status effects,
     life-state rules, RNG, and structured deltas.

10. Social Manipulation does not let LLM decide persuasion/deception outcomes.
    - Social moves use relationship, emotion, reputation, known facts,
      leverage, currency, and deterministic checks.

11. Faction Mission does not let LLM decide mission availability or completion.
    - Availability, accept, complete, fail, reward, reputation, and quest state
      changes are rule functions returning `StateDelta` and `Event`.

12. Domain System does not let LLM decide income/upkeep/risk.
    - Base/facility/staff/inventory/income/upkeep/risk behavior is rule based
      and bounded.

13. No v1.6 gameplay module output directly enters `GameState`.
    - Reviewed module actions generate `StateDelta`; tests assert original
      state remains unchanged until deltas are applied.

14. Provider factory remains the intended Provider entry point.
    - v1.6 gameplay modules do not directly instantiate concrete providers.
      Existing provider usage in broader app remains in LLM/Prompt Lab,
      playtesting, or GameLoop surfaces.

15. Tests do not call real external APIs.
    - v1.6 tests use direct handlers, `Random` seeds, local schemas, or fake
      providers in legacy GameLoop combat tests.

16. Module import does not enable LLM permissions.
    - `GameplayModulePermissions.call_llm` defaults to false and validation
      rejects forbidden permissions, including LLM calls.

17. Prompt/Profile cannot change module adjudication boundary.
    - Gameplay module boundary and roadmap state that Prompt Profiles may
      affect expression only; module success/failure/effects are rule outputs.

## Risk Items

- Some non-v1.6 quality/playtest tooling imports fake/playtest providers for
  benchmark and GameLoop coverage. This is expected and local/fake by default,
  but should remain separated from module adjudication.
- v1.6 handlers commonly import `PlayerIntent` from the LLM schema package.
  This is a schema dependency, not a provider call. The naming can look risky
  in grep-based audits.
- Combat tests use `FakeLLMProvider` through `GameLoop` to exercise narrator
  and intent parser integration. This is safe because action outcome is still
  resolved by combat rules, but future real-provider tests must remain
  explicitly gated.

## High-Risk Issues

None found.

No evidence was found that v1.6 modules call LLM providers, accept LLM output
as authoritative gameplay results, or write LLM output directly into
`GameState`.

## Medium-Risk Issues

None blocking.

The only medium-watch area is naming and dependency clarity: gameplay rule
modules import `PlayerIntent` from `app.llm.schemas`. This does not create LLM
authority, but future maintainers may misread it as permission to call
providers from gameplay rules.

## Minor Issues

- Grep output is noisy because broader `backend/app` contains v1.5 Prompt Lab
  and quality benchmark provider code. Future audits would benefit from a
  scripted v1.6 module-only LLM boundary check.
- Legacy combat GameLoop tests rely on `FakeLLMProvider` to produce intents and
  narration. This is acceptable, but the test names should continue making
  clear that fake provider output does not adjudicate combat.

## Fix Recommendations

1. Keep gameplay rule modules provider-free. Do not import provider factory,
   concrete providers, or `ProviderRouter` into v1.6 gameplay modules.
2. Consider adding a small release-check assertion that v1.6 module paths do
   not contain `generate_text`, `generate_json`, `create_llm_provider`, or
   concrete provider instantiation.
3. If schema ownership is refactored later, consider moving `PlayerIntent` to a
   neutral action-schema module to reduce audit noise.
4. Keep all real-provider tests under explicit `allow_real_provider` gates and
   out of gameplay module regression by default.
5. Continue blocking `call_llm=true` in module manifests and package import
   dry-run.

## Acceptance Blocking Status

Not blocking v1.6 acceptance.

Final assessment: v1.6 preserves the engine boundary. LLMs remain language and
presentation tools; gameplay modules adjudicate results through deterministic
rules, structured `ActionResult`, `StateDelta`, `EventLog`, Visibility, and NPC
Knowledge.
