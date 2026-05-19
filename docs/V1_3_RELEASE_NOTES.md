# v1.3 Release Notes: Advanced NPC Simulation

## 1. Version Name

v1.3: Advanced NPC Simulation

## 2. Version Goal

v1.3 adds a bounded, deterministic NPC simulation layer to the local
interactive novel world engine / studio.

NPCs can now appear more autonomous through finite intent queues, short-term
plans, known-memory reactions, relationship and faction-driven behavior, rumor
decisions, social disposition, conflict avoidance, daily replanning, local
debugging, quality evals, and regression playtests.

This release does not turn the engine into an LLM multi-agent free simulation.
The world engine remains the only source of truth. The LLM remains a language
layer, not the world judge.

## 3. New Features

### NPC Simulation Boundary

- Added the v1.3 NPC Simulation Boundary Contract.
- Added `NPCSimulationPolicy` and scoped NPC simulation context concepts:
  `npc_known_context`, `npc_visible_context`, `npc_private_state`,
  `simulation_candidate_action`, `simulation_intent`, `simulation_plan`,
  `simulation_event`, and `debug_only_simulation_data`.
- NPC simulation is explicitly constrained to deterministic rule outputs.

### NPC Intent Queue

- Added `NPCIntent` runtime support on NPC state.
- Added finite intent queue operations for enqueue, cancel, complete, fail,
  select, and prune expired intents.
- Intent queue changes return `StateDelta` and system `Event` records.
- Intent selection is deterministic by priority, created turn, and id.

### NPC Short-Term Plans

- Added `NPCPlan` and `NPCPlanStep`.
- Added finite plan creation, validation, advancement, cancellation, and
  failure.
- Plans use whitelisted step types and deterministic rule execution.
- Plans do not directly mutate `GameState`.

### Memory-Based Reactions

- Added bounded NPC memory reaction rules.
- NPCs can react to eligible known memories and events through finite outcomes
  such as avoid, report, spread known rumor, adjust suspicion/tone, refuse talk,
  or enqueue an intent.
- Hidden and debug-only memories are filtered out of ordinary reactions.

### Relationship-Driven Behavior

- Added relationship behavior rules based on trust, fear, affinity,
  obligation, hostility, relationship tone, emotional state, known facts, and
  known rumors.
- Supported finite behaviors include help, warn, avoid, report, lie/withhold,
  share known rumor, and seek reconciliation.
- Hidden relationships remain excluded from player-visible relationship graphs.

### NPC Faction Duties

- Added `NPCFactionDuty` support on NPC state.
- Duties can represent guard, patrol, report crime to faction, protect faction
  member, refuse hostile actor, spread faction rumor, seek information, and
  enforce curfew.
- Duties produce intent/plan candidates through existing simulation paths.

### NPC Rumor Decisions

- Added `NPCRumorDecision`.
- NPCs can keep secret, share with actor, share with faction, distort, ignore,
  report, or enqueue a spread-rumor intent.
- NPCs can only spread or reason from rumors they know.
- Hidden fact truth is not copied into player-facing rumor text.

### Fear / Trust / Loyalty Models

- Added `NPCSocialDisposition`.
- Added deterministic updates and derived behavior weights for trust, fear,
  faction loyalty, NPC loyalty, moral flexibility, risk tolerance, conflict
  tolerance, and secrecy preference.
- Disposition can influence behavior and dialogue tone summaries, but does not
  grant knowledge or override authoritative relationship state.

### Conflict Avoidance

- Added bounded conflict avoidance rules.
- NPCs can avoid locations, flee from actors, avoid actors, seek guards, call
  for help, hide, refuse confrontation, or rest when injured.
- Hidden NPC actions remain non-player-visible unless normal visibility rules
  make them visible.

### Daily Goal Replanning

- Added daily and event-triggered replanning.
- Replanning can reevaluate goals, clear expired intents, enqueue daily duties,
  adjust plan priorities, and cancel impossible plans.
- Replanning is deterministic and uses `StateDelta` plus system `Event`
  records.

### Simulation Tick Orchestrator

- Added deterministic NPC simulation tick orchestration.
- Tick phases include pruning expired intents, daily replanning,
  memory reactions, relationship behavior, faction duties, rumor decisions,
  conflict avoidance, intent selection, and plan build/advance.
- Tick budgets limit NPCs, intents, plan steps, and events to prevent infinite
  loops.

### NPC Simulation Authoring Presets

- Added local NPC simulation presets for common behavior styles such as guards,
  merchants, informants, hostile actors, cautious villagers, loyal followers,
  rumor spreaders, and investigators.
- Preset apply affects authoring draft data only.
- Preset save remains under the v1.2 Authoring Validation Gate.

## 4. Behavior Changes

- NPC state can now include intent queues, short-term plans, faction duties,
  and social disposition.
- World loading and save/load support the new v1.3 NPC simulation fields.
- World tick can integrate bounded NPC simulation without making NPCs
  free-running background agents.
- Dead, incapacitated, or stunned NPCs are blocked from ordinary simulation.
- Public simulation rule entry points reject inactive NPCs before producing
  ordinary intent, plan, relationship behavior, or rumor-decision output.
- NPC actions are limited to known facts, known rumors, witnessed/known crimes,
  known memories, and visible context.

## 5. API Changes

New or expanded local/debug/authoring surfaces include:

- NPC simulation debug summary endpoints.
- Per-NPC simulation inspection endpoints for intent queue, plans, goals,
  known facts summary, faction duties, social disposition, and recent events.
- Dry-run NPC simulation tick endpoint.
- NPC behavior timeline endpoints.
- NPC simulation preset authoring endpoints.

These endpoints are local tools. Debug APIs are gated by `ENABLE_DEBUG_API`.
Authoring preset flows remain authoring/draft flows and do not modify active
`GameState`.

Player APIs do not expose NPC simulation debug data, intent queues, plan
internals, debug reasons, raw state deltas, hidden memory, or hidden fact text.

## 6. Frontend Changes

- Added local NPC Simulation Debugger UI.
- Added NPC Behavior Timeline UI.
- Added debug-disabled safe states.
- Added display areas for current goals, intent queue, active plan, current
  plan step, emotional state, social disposition, relationship behavior
  summary, faction duties, and recent simulation events.
- Added dry-run tick controls for local debug use.
- Added NPC simulation preset selection/preview in authoring flows.
- Hidden fact text remains redacted by default.
- Debug UI is not mixed into player UI.

## 7. NPC Simulation Changes

v1.3 NPC simulation is finite and rule-driven:

- NPCs may queue finite intents.
- NPCs may build finite plans from those intents.
- NPCs may react to known memories and witnessed/known events.
- NPCs may choose behavior influenced by relationship, faction duty, rumor
  knowledge, emotional state, and social disposition.
- NPCs may avoid known or visible danger.
- NPCs may replan on new day or significant rule events.

NPC simulation cannot:

- know unknown facts
- read unknown hidden facts
- use hidden/debug memory for ordinary reactions
- directly modify `GameState`
- bypass `StateDelta`
- skip `Event` records for simulation behavior
- ask an LLM to decide behavior
- call external tools or networks
- run unbounded background thinking loops

All NPC simulation state changes still flow through `StateDelta`. All NPC
simulation behavior still records `Event`.

## 8. Debug / Timeline Changes

- Added debug-only NPC simulation inspection.
- Added dry-run tick support that does not write active state.
- Added behavior timeline entries for NPC behavior over turns.
- Timeline/debug output uses safe summaries and redacted hidden fact text by
  default.
- Debugger data is for local debugging only and must not enter narrator prompts
  or player APIs.

## 9. Testing / Evals Changes

- Added NPC simulation unit tests for boundary policy, intent queue, plans,
  memory reactions, relationship behavior, faction duties, rumor decisions,
  social disposition, conflict avoidance, daily replanning, tick orchestration,
  presets, quality evals, and regression playtests.
- Added v1.3 integration regression tests across v1.0 world engine, v1.1 RP
  boundaries, v1.2 authoring, Visibility, NPC Knowledge, StateDelta, EventLog,
  Quality Gate, debug APIs, and frontend build.
- Added quality eval checks for:
  - NPC unknown fact usage
  - hidden fact leak
  - repeated intent loop
  - blocked plan loop
  - dead NPC acted
  - invalid target
  - missing event record
  - excessive intents
  - plan budget exceeded
  - low behavior coverage
- Added deterministic NPC simulation regression scenarios.
- NPC simulation quality evals and regression playtests do not call real LLMs
  or real OpenAI APIs.

Accepted verification:

- `python -m pytest`: passed, `1114 passed`.
- `cd frontend && npm.cmd run build`: passed.

## 10. Known Limitations

- v1.3 is not full social AI.
- v1.3 is not a city-scale society simulation.
- v1.3 is not a war simulator.
- v1.3 is not an economic simulator.
- v1.3 does not include complex GOAP planning.
- v1.3 does not include large-scale pathfinding or a full chase system.
- NPCs do not run infinite background thoughts.
- NPCs do not call external tools or networks.
- LLMs do not generate authoritative NPC plans or behavior choices.
- Debug views are local tools and should not be reused in player UI.
- Plan execution currently uses the deterministic NPC planning rule resolver
  and whitelisted planning actions. This is accepted for v1.3, but v1.4 should
  consider centralizing and naming this as an explicit plan action registry.
- Quality evals are deterministic safety/coverage checks, not an absolute
  measure of narrative quality.

## 11. Upgrade Notes From v1.2

- Existing v1.2 content packs remain focused on authoring/draft workflows.
- NPC content may now include optional simulation fields such as faction duties
  and social disposition.
- Saves may now preserve NPC intent queues and plans.
- Existing worlds do not need to become fully simulated. The new fields are
  additive and can be introduced gradually.
- Authoring presets affect drafts, not active runtime state.
- Debug APIs must remain explicitly enabled with `ENABLE_DEBUG_API`.
- Eval/playtest APIs remain local testing tools and should use mock/local-stub
  providers.
- Frontend debug panels are local studio/debug tools, not player-facing
  features.

Migration expectations:

- Do not treat missing v1.3 NPC simulation fields as invalid old content.
- Do not copy debug simulation data into player-facing content.
- Do not promote hidden facts, hidden memories, or debug reasons into narrator
  prompts.
- Keep provider selection through the existing provider factory.

## 12. Recommended v1.4 Directions

- Centralize and document a formal plan action registry for all future NPC plan
  step types.
- Add deterministic mystery/case simulation with evidence chains and suspect
  behavior.
- Improve player-facing journal, rumor board, and discovered-behavior
  summaries.
- Expand timeline replay with safer player/debug side-by-side redaction.
- Add stronger authoring validation for simulated-world balance and long-running
  schedule interactions.
- Improve save/content migration support for worlds that heavily use NPC
  simulation.
- Explore optional draft-only LLM authoring assistants behind strict validation
  gates, without runtime NPC behavior authority.

## Final Notes

v1.3 keeps the project identity intact: a local self-use engine and studio where
rules own the world and the LLM speaks only within bounded language surfaces.

NPCs are now more reactive and legible, but they are still finite,
knowledge-scoped, deterministic rule actors. Hidden facts are redacted by
default, debug data stays local, and `GameState` remains protected by
`StateDelta` and `EventLog`.
