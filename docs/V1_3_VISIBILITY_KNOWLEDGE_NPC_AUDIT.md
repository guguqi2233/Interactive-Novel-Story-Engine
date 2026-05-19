# v1.3 Visibility / NPC Knowledge / NPC Simulation Audit

Verification Date: 2026-05-19

Scope: v1.3 Advanced NPC Simulation, NPC knowledge filtering, player-visible APIs, RP/dialogue context builders, debug simulation APIs, NPC behavior timeline, relationship/faction graphs, and v1.3 integration tests.

## Verification Inputs

- Reviewed `docs/V1_3_ROADMAP.md` and `docs/NPC_SIMULATION_BOUNDARY.md`.
- Inspected `backend/app/engine/rules/npc_simulation_boundary.py`.
- Inspected v1.3 simulation modules for intents, plans, memory reactions, relationship behavior, faction duties, rumor decisions, conflict avoidance, daily replanning, and tick orchestration.
- Inspected `backend/app/session_store.py` for player `visible_state` construction.
- Inspected `backend/app/main.py` for debug NPC simulation APIs, behavior timeline, relationship/faction graph endpoints, and redaction helpers.
- Inspected `backend/app/llm/context_builder.py` for narrator, RP, and NPC memory filtering.
- Inspected `backend/app/engine/rules/graphs.py`, `relationships.py`, `factions.py`, and faction conflict visibility helpers.
- Inspected `backend/tests/test_v13_npc_simulation_integration.py`.
- Latest known full verification before this audit: `python -m pytest` passed with 1110 tests, and `cd frontend && npm.cmd run build` passed.

## Passed Items

1. **NPC unknown facts do not enter simulation context.**  
   `NPCSimulationPolicy.build_context` includes public facts and facts explicitly known through NPC knowledge fields. Candidate actions and plans are rejected when they reference facts outside `npc_known_context`.

2. **Hidden facts do not enter accepted NPC plans unless known by that NPC.**  
   `npc_plans.validate_plan` checks `fact:`, `rumor:`, and `crime:` preconditions against the scoped context. Unknown hidden fact references become `npc_unknown_fact` rather than plan authority.

3. **Hidden memory does not trigger NPC reactions.**  
   `npc_memory_reactions._memory_allowed_for_npc` rejects `MemoryVisibility.HIDDEN`.

4. **Debug memory does not trigger NPC reactions.**  
   The same memory filter rejects `MemoryVisibility.DEBUG_ONLY`, and v1.3 integration tests assert debug-only memory produces no reaction event.

5. **NPCs only spread known rumors.**  
   `npc_rumor_decisions.decide_npc_rumor_action` requires `npc_id in rumor.known_by_npcs`. Intent enqueue paths also validate `rumor:` preconditions against known rumor ids.

6. **Hidden rumor truth is not used as player-facing rumor text.**  
   Player-visible rumors are built through `get_visible_rumors` / `build_visible_state` using `text_for_player`, not raw hidden fact text. Existing validation/tests cover hidden fact leakage in rumor player text.

7. **Hidden NPC action does not enter player `visible_state` by default.**  
   `build_visible_state` filters NPCs by location, visibility, hidden flag, and discovery. v1.3 integration tests assert hidden NPC ids and hidden fact text are absent from player state.

8. **Dead/incapacitated NPCs do not execute ordinary simulation.**  
   `NPCSimulationPolicy.can_simulate_npc`, `select_next_intent`, `advance_plan`, and `run_npc_simulation_tick` use life-state checks. The tick skips inactive NPCs and records debug skip output only.

9. **Group RP and NPC simulation contexts remain separate.**  
   Dialogue/group RP responses build participant dialogue context through RP/dialogue managers and `build_visible_state`; NPC simulation debug/tick context is not mixed into group RP responses.

10. **Debug simulation data is exposed only through debug APIs.**  
    NPC simulation summary/detail, dry-run tick, tick event list, and behavior timeline are under `/debug/...` endpoints and call `require_debug_api()`.

11. **Player API does not return intent queue or plan debug data.**  
    Player `visible_state` does not include `intent_queue`, `plans`, `debug_output`, debug reasons, or behavior timeline entries. v1.3 integration tests assert debug output is absent from player state.

12. **NPC behavior timeline redacts sensitive text and is debug-only.**  
    Timeline endpoints are `/debug/...`, require debug API, produce `safe_summary`, and use `debug_reason_redacted`. Existing v1.3 tests assert hidden fact text is absent from timeline output.

13. **Hidden relationship fields do not enter player graph.**  
    `build_relationship_graph(debug=False)` skips relationships not known by player and skips relationships involving actors not visible to player.

14. **Hidden faction data does not enter player UI/graph.**  
    `build_faction_graph(debug=False)` includes only factions known to the player or with player-known reputation, and only visible NPC membership edges.

15. **Narrator cannot see raw `state_deltas` or simulation debug reasons through normal player state.**  
    Player-facing state construction omits raw events and state deltas. Memory/RP context builders filter hidden/debug memories and exclude hidden or unknown facts from narrator/RP/NPC context.

## Possible Leak Paths

1. **Debug detail response includes raw-ish debug reason fields behind `ENABLE_DEBUG_API`.**  
   `_debug_npc_simulation_detail` exposes `debug_decision_reasons` for local debugging. It is correctly debug-gated, but future debug reasons must not contain hidden text or secrets.

2. **Behavior timeline redaction is generic, not fact-aware.**  
   `_redact_sensitive_text` redacts API-key-like strings, while hidden fact text safety currently depends on v1.3 events using structured ids/statuses rather than embedding hidden fact prose in `event.result` or delta metadata.

3. **Relationship debug summary naming is broader than player visibility.**  
   Debug NPC simulation detail uses a key named `visible_relationship_ids` but includes all relationships involving the NPC. This is behind debug API, so not a player leak, but the field name could mislead future UI code.

4. **Group RP and simulation both use NPC state and relationship tone.**  
   The current paths are separate, but future frontend reuse of debug simulation components inside RP panels would be a leak risk unless gated and redacted.

5. **Hidden rumor truth remains dependent on authoring/validation discipline.**  
   Runtime player rumor views use `text_for_player`, but if content authors write hidden truth into `text_for_player`, validation must catch it before release.

## High-Risk Leaks

None found.

No current player-facing API path was found that returns hidden facts, hidden memory, debug memory, intent queues, NPC plans, simulation debug output, raw state deltas, hidden relationship graph data, hidden faction graph data, or hidden NPC behavior timeline entries.

## Medium-Risk Leaks

1. **Timeline/debug redaction is not semantic hidden-fact redaction.**  
   The behavior timeline redacts obvious sensitive tokens and truncates debug reasons, but it does not compare text against hidden fact bodies. If a future simulation event stores hidden prose in `event.result`, `StateDelta.reason`, or debug metadata, the timeline could echo it in debug output. This is currently debug-only and covered by tests for the known hidden text fixture, so it is not a release blocker.

2. **Debug APIs expose hidden ids by design.**  
   Debug simulation summaries may return hidden fact ids and known fact ids. This is acceptable for local debug mode, but it must remain strictly behind `ENABLE_DEBUG_API` and out of ordinary authoring/player UI.

3. **Field naming in debug relationship summary could cause UI misuse.**  
   `relationship_behavior_summary.visible_relationship_ids` contains relationship ids involving the NPC in debug detail, not necessarily player-visible relationship ids. A future UI should treat it as debug-only.

## Low-Risk Issues

1. Broad text searches are noisy because normal docs/tests contain words such as `hidden`, `debug`, `prompt`, and `visible`. Manual inspection did not confirm those noisy matches as leaks.

2. Some older playtest and eval paths include placeholder or fake narrative text, but they are not v1.3 NPC simulation visibility authority paths.

3. Debug event response intentionally returns raw `state_deltas` under debug API. This is expected for local debugging but should not be reused in normal UI components.

## Fix Recommendations

1. Add a semantic redaction helper for debug/timeline output that can optionally compare output strings against hidden fact text and replace matches with `[hidden text redacted]`.

2. Rename debug-only `visible_relationship_ids` to `related_relationship_ids_debug_only` or add a response comment/type marker so frontend code cannot mistake it for player-visible graph data.

3. Add a static or integration test asserting `/sessions/{id}/state`, `/game/state/{id}`, relationship graph, faction graph, and dialogue/group RP responses do not contain `intent_queue`, `plans`, `debug_output`, `debug_reason`, `state_deltas`, or hidden fixture text.

4. Keep all NPC Simulation Debugger frontend routes/components under a debug-only boundary, and do not mount them inside player UI.

5. Continue requiring validation gates for rumor/content authoring so `text_for_player` cannot carry full hidden fact truth.

6. If future simulation events need richer explanations, split them into `safe_summary` and `debug_reason_debug_only`, and never derive narrator text from debug reasons.

## v1.3 Blocker Assessment

**Not blocking v1.3.**

The reviewed implementation preserves the required boundaries: NPC simulation is scoped by NPC knowledge, hidden/debug memory is excluded from reactions, rumor spread requires known rumors, hidden NPC/relationship/faction data is filtered from player surfaces, debug simulation data is debug-gated, and narrator/player APIs do not receive raw simulation debug data or raw state deltas.
