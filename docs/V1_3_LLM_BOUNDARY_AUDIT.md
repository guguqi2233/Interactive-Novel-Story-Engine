# v1.3 LLM Boundary Audit

Verification Date: 2026-05-19

Scope: v1.3 Advanced NPC Simulation modules, v1.3 debug/timeline APIs, simulation authoring presets, quality evals, regression playtests, LLM provider entry points, narrator/dialogue prompt context, and relevant tests.

## Verification Inputs

- Reviewed `docs/V1_3_ROADMAP.md`, `docs/LLM_PROTOCOL.md`, `docs/NPC_SIMULATION_BOUNDARY.md`, `docs/WORLD_ENGINE.md`, and roleplay boundary documentation.
- Inspected v1.3 rule modules under `backend/app/engine/rules`, especially NPC simulation boundary, intents, plans, memory reactions, relationship behavior, faction duties, rumor decisions, social disposition, conflict avoidance, daily replanning, and simulation tick orchestration.
- Inspected debug and timeline API paths in `backend/app/main.py`.
- Inspected v1.3 authoring presets, quality evals, and regression playtests.
- Searched for LLM/provider/prompt usage in v1.3 modules and related tests.
- Latest known verification before this audit: `python -m pytest` passed with 1110 tests, and `cd frontend && npm.cmd run build` passed.

## Passed Items

1. **v1.3 modules do not call LLM providers directly.**  
   The NPC simulation modules reviewed do not instantiate OpenAI/local HTTP providers, do not call `generate_text` / `generate_json`, and do not import provider factory APIs.

2. **NPC Intent Queue does not call LLM.**  
   Intent creation, selection, pruning, completion, failure, and cancellation are deterministic rule functions. Intent changes are represented as `StateDelta` plus system `Event`.

3. **NPC Plan System does not use free-form LLM planning.**  
   Plans are built from finite intent types and whitelisted step types. Plan validation rejects invalid or unknown prerequisites, and plan execution routes through rule/action resolution with `StateDelta` output.

4. **Memory-Based Reactions do not call LLM for reaction judgment.**  
   Memory reaction logic uses structured known memories, known rumors, witnessed crimes, relationship history, and explicit rules. It does not invoke a model to infer or invent reactions.

5. **Relationship-Driven Behavior does not call LLM to decide behavior.**  
   Behavior is derived from structured relationship state, tone presets, known facts, rumors, emotional state, and faction data. Outputs remain bounded to intents, plan candidates, deltas, and events.

6. **Faction Duties do not call LLM to decide duties.**  
   Duty activation and conversion to intent/plan are rule-based and checked against NPC life state and knowledge.

7. **Rumor Decision does not call LLM to rewrite or propagate rumors.**  
   Rumor decisions are deterministic and based on structured rumor knowledge, trust, faction alignment, secrecy, source credibility, and disposition fields. Hidden fact text is not used as player-facing rumor text.

8. **Fear / Trust / Loyalty models are not directly written by LLM.**  
   Social disposition updates are rule-based and use `StateDelta` / `Event`. The LLM may express tone through existing dialogue/narration paths, but does not own disposition values.

9. **Conflict Avoidance is not LLM-decided.**  
   Avoid/flee/rest/help behavior is derived from structured life state, fear, visible hostile actors, known crimes, safety tags, and duties.

10. **Daily Replanning does not call LLM.**  
    Replanning is deterministic, event/time driven, bounded, and produces structured intent/plan changes.

11. **Simulation Tick does not call LLM.**  
    Tick orchestration has fixed subsystem order, budgets, deterministic processing, and no provider invocation.

12. **Debugger does not send debug data to narrator.**  
    Simulation debug APIs are under debug routes and controlled by `ENABLE_DEBUG_API`. Reviewed player/narrator-facing paths do not consume debug-only simulation summaries.

13. **No v1.3 LLM output directly enters GameState.**  
    v1.3 simulation state changes are represented as `StateDelta` and applied through the engine path. The reviewed simulation code does not accept model output as authoritative state.

14. **NPC dialogue context remains knowledge-filtered.**  
    Dialogue context construction continues to expose `npc_known_facts` rather than raw world state or all hidden facts. RP prompt profile handling remains expression-only and does not expand state authority.

15. **Hidden facts are not used as NPC simulation prompt input.**  
    v1.3 simulation has no NPC simulation prompt path. NPC simulation context is built from public facts, explicitly known facts, known rumors, witnessed crimes, and visibility checks.

16. **Provider factory remains the provider selection boundary.**  
    Concrete provider selection is still centralized in `backend/app/llm/provider_factory.py`. v1.3 simulation modules do not instantiate concrete providers.

17. **Tests do not call real APIs.**  
    v1.3 tests and regression playtests use deterministic local/mock providers or no provider at all. No real OpenAI API path is required for v1.3 simulation tests.

## Risk Items

1. **Debug APIs intentionally expose more simulation structure.**  
   Debug routes can expose intent queues, known fact ids, hidden fact ids, redacted reasons, and tick details. This is acceptable for local debugging only while `ENABLE_DEBUG_API` remains enforced and hidden text remains redacted by default.

2. **Existing playtest/benchmark infrastructure uses LLM-shaped interfaces.**  
   Some older playtesting paths instantiate `IntentParser`, `Narrator`, or `PlaytestLLMProvider`. These are not v1.3 simulation authority paths, and `PlaytestLLMProvider` is deterministic/local, but their names can look risky during broad grep-based audits.

3. **Narrator safety depends on context filtering staying centralized.**  
   Existing narrator paths are designed to receive visible/action-safe context rather than raw GameState. Future NPC simulation summaries must continue to enter narration only through explicit visibility-filtered summaries.

4. **RP/social expression fields can be mistaken for authority.**  
   Relationship tone, RP prompt profile, and social disposition may influence language style. They must remain expression inputs and must not become a way for prompts to grant new world-state permissions.

## High-Risk Issues

None found.

No evidence was found that v1.3 simulation modules call LLMs, allow LLM output to directly modify `GameState`, bypass `StateDelta`, or let LLMs decide NPC behavior.

## Medium-Risk Issues

1. **Debug redaction must remain covered as fields expand.**  
   v1.3 debug/timeline APIs currently redact hidden fact text by default. Any new debug field should receive a test asserting it is not returned by player APIs or normal UI routes.

2. **Broad playtesting provider usage should stay isolated from simulation authority.**  
   The deterministic `PlaytestLLMProvider` is acceptable for scenario/playtest narration, but NPC simulation regression should continue to avoid real provider configuration and should not let parser/narrator output become NPC decisions.

3. **Narrator `ActionResult.reason` remains a boundary-sensitive field.**  
   Existing LLM protocol guidance notes narrator input must stay action-safe. If future simulation events include debug reasons, they should be split from player-safe summaries before reaching narrator context.

## Low-Risk Issues

1. Some fake playtest output strings appear to be placeholder or mojibake text. This is cosmetic and not an LLM boundary issue.

2. Grep-based scans produce noisy matches because words such as `prompt`, `generate`, and `provider` appear in documentation, test names, and deterministic fake providers. Manual review found no v1.3 authority violation.

## Fix Recommendations

1. Add or keep a static regression test that forbids v1.3 simulation modules from importing concrete LLM providers, `Narrator`, `IntentParser`, `OpenAI`, or calling `generate_text` / `generate_json`.

2. Keep `ENABLE_DEBUG_API` disabled by default outside local development, and add focused tests whenever new debug fields are added.

3. Continue routing all player/narrator/RP prompt context through visibility and knowledge builders. Do not pass raw simulation debug output to narration.

4. If social disposition or relationship behavior is later surfaced in dialogue prompts, expose only expression-safe summaries, not hidden relationship values or debug reasons.

5. Consider separating future event fields into `safe_summary` and `debug_reason` consistently so narrator and player APIs cannot accidentally consume debug-only reasons.

## Acceptance Impact

**Not blocking v1.3 acceptance.**

Based on this audit, v1.3 preserves the intended LLM boundary: the LLM remains a language and presentation layer, while NPC simulation decisions are deterministic, rule-based, knowledge-filtered, and applied only through `StateDelta` / `EventLog`.
