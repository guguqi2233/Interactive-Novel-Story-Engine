# v1.3 Acceptance Report: Advanced NPC Simulation

## Verdict

Accepted for v1.3.

v1.3 delivers the Advanced NPC Simulation layer as bounded deterministic rule
systems, not LLM multi-agent simulation. The implementation provides NPC
simulation boundary policy, intent queues, short-term plans, memory reactions,
relationship behavior, faction duties, rumor decisions, social disposition,
conflict avoidance, daily replanning, tick orchestration, debug/timeline
inspection, authoring presets, quality evals, regression playtests, and v1.3
integration coverage.

No high-risk acceptance blocker remains after the final inactive-NPC rule entry
hardening.

## Verification Date

2026-05-19 20:46:50 +08:00

## Verification Commands

- `python -m pytest`
- `cd frontend && npm.cmd run build`

## Verification Results

- Backend tests: passed, `1114 passed in 48.40s`.
- Frontend build: passed, `tsc -b && vite build` completed successfully.
- Non-blocking shell noise: Windows PowerShell reported an unsigned user
  profile warning while starting commands. The commands still completed
  successfully and this did not affect test/build results.

## Scope Accepted

Accepted v1.3 scope:

- NPC Simulation Boundary Contract.
- NPC Intent Queue.
- NPC Short-Term Plan System.
- NPC Memory-Based Reactions.
- NPC Relationship-Driven Behavior.
- NPC Faction Duties.
- NPC Rumor Decision System.
- NPC Fear / Trust / Loyalty Models.
- NPC Conflict Avoidance.
- NPC Daily Goal Replanning.
- NPC Simulation Tick Orchestrator.
- NPC Simulation Debugger Backend.
- NPC Simulation Debugger Frontend.
- NPC Behavior Timeline Visualizer.
- NPC Simulation Authoring Presets.
- NPC Simulation Quality Evals.
- NPC Simulation Regression Playtests.
- v1.3 integration regression tests.

The accepted scope remains local-first. It does not add online services,
external tools, arbitrary code plugins, cloud sync, or free-running background
NPC agents.

## Boundary Review

### NPC Simulation Boundary

Accepted.

- `docs/NPC_SIMULATION_BOUNDARY.md` defines `npc_known_context`,
  `npc_visible_context`, `npc_private_state`, `simulation_candidate_action`,
  `simulation_intent`, `simulation_plan`, `simulation_event`, and
  `debug_only_simulation_data`.
- `NPCSimulationPolicy` builds scoped NPC context, rejects unknown hidden facts
  in candidate actions/plans, validates finite plans, and checks simulation
  events.
- NPC simulation is explicitly prohibited from reading unknown hidden facts,
  mutating `GameState` directly, bypassing `StateDelta`, skipping `Event`
  records for state-changing actions, calling LLMs for behavior selection,
  using external network/tools, or running unbounded planning loops.
- Dead, incapacitated, or stunned NPCs are blocked from ordinary simulation by
  policy and runtime rule entry points.

### Intent / Plan

Accepted.

- `NPCIntent` and `NPCState.intent_queue` support finite queued intents with
  priority, lifecycle status, source ids, targets, preconditions, created turn,
  expiry, and debug-only reason.
- Intent queue mutations return `StateDelta` and system `Event` output.
- `select_next_intent` is deterministic by priority, created turn, and id.
- Unknown fact/rumor/crime preconditions are rejected.
- Inactive NPCs cannot enqueue or select ordinary intents.
- `NPCPlan` and `NPCPlanStep` support bounded short-term plans with whitelisted
  step types.
- Plan build/status/advance use `StateDelta` and `Event`; active state changes
  still require normal delta application.
- Plan execution delegates step effects to deterministic NPC planning rules
  rather than free-form text.
- Save/load preserves intent and plan state.

### Memory / Relationship / Faction

Accepted.

- Memory reactions operate only on eligible known/visible memory records.
- Hidden and debug-only memories are filtered and do not trigger ordinary NPC
  reactions.
- Reactions that create future activity use the intent queue and record events.
- Relationship behavior uses existing relationship state, relationship tone,
  known facts/rumors, emotional state, and bounded rules to produce intents,
  plan candidates, deltas, and events.
- Hidden relationships remain filtered from player-visible graphs.
- Faction duties are NPC-owned bounded responsibilities. They validate faction
  membership, target references, known facts/rumors/crimes, lifecycle state,
  and produce intent/plan candidates without direct `GameState` mutation.
- NPCs do not act on unknown facts.

### Rumor / Social Disposition / Avoidance

Accepted.

- Rumor decisions require the NPC to already know the rumor.
- Secret rumor truth and hidden fact text are not copied into player-facing
  rumor text.
- Rumor decisions are deterministic and use dedupe markers.
- `NPCSocialDisposition` stores lightweight trust/fear/loyalty/risk/secrecy
  signals and updates through `StateDelta` plus events.
- Disposition influences behavior weights and dialogue tone summaries; it does
  not grant knowledge or override authoritative relationship state.
- Conflict avoidance uses known/visible threats, life state, emotional state,
  social disposition, and faction duties to enqueue finite intents.
- Hidden NPC avoidance remains non-player-visible unless normal visibility
  rules make the NPC/action visible.

### Daily Replanning / Tick

Accepted.

- Daily replanning handles new day, major events, goal completion/failure,
  schedule changes, faction duty updates, and injury/recovery through bounded
  rule logic.
- Replanning clears expired intents, enqueues daily duties, adjusts priorities,
  and cancels impossible plans through `StateDelta` and system events.
- `npc_simulation_tick` provides deterministic phase ordering and budget limits
  for NPCs, intents, plan steps, and events.
- Tick orchestration skips inactive NPCs, respects max budgets, prevents
  infinite loops, and records system events.
- Hidden NPC actions do not enter player narrative surfaces.

### Debug / Timeline

Accepted.

- NPC simulation debug endpoints are gated by `ENABLE_DEBUG_API`.
- Dry-run tick is read-only and does not mutate the active `GameState` or
  database state.
- Player APIs do not return intent queues, plan internals, debug reasons, or
  simulation traces.
- Behavior timeline endpoints are debug-only and support turn-range behavior
  inspection.
- Hidden fact text is redacted by default; debug output may use ids and safe
  summaries, not raw secrets.
- Debug timeline data is not sent to narrator prompts.

### Authoring / Presets

Accepted.

- NPC simulation presets are local authoring data for common bounded behavior
  patterns.
- Preset preview/apply affects authoring drafts, not active `GameState`.
- Preset save remains under the v1.2 Authoring Validation Gate.
- Presets cannot grant hidden facts, execute scripts, or call LLMs.

### Quality / Regression

Accepted.

- NPC simulation quality evals detect unknown fact usage, hidden leaks,
  repeated intent loops, blocked plan loops, dead NPC actions, invalid targets,
  missing events, excess intents, budget overruns, and low behavior coverage.
- Reports avoid hidden fact text in normal output.
- Regression scenarios cover guard patrol, report crime, spread rumor,
  avoid player, seek help, daily replan, relationship response, faction duty,
  and injured rest patterns.
- Regression playtests use mock/local-stub style fixtures and temporary state,
  not real API calls or real user saves.
- v1.3 integration tests verify cooperation with v1.2 authoring, v1.1 RP,
  v1.0 world engine, Visibility, NPC Knowledge, EventLog, StateDelta, and
  Quality Gate.

### Frontend

Accepted.

- NPC Simulation Debugger UI is present in the local debug/studio surface.
- Behavior Timeline UI is present for local debug inspection.
- Debug-disabled states are handled safely.
- Player UI is kept separate from debug simulation data.
- Production frontend build passes.

### LLM / Authority

Accepted.

- LLM remains a language layer: parser, narrator, summarizer, RP expression, or
  draft assistant where explicitly allowed by earlier boundaries.
- NPC behavior is selected by deterministic rule code, not LLM output.
- Simulation modules do not instantiate concrete providers and do not call
  `generate_text` / `generate_json` for behavior decisions.
- Provider factory remains the provider construction boundary.
- NPC dialogue context remains scoped to NPC-known facts, player-visible facts,
  safe RP/voice fields, relationship tone, emotional summaries, scene mood, and
  filtered memory.
- No LLM output directly enters `GameState`.

## Known Limitations

- This is bounded local NPC simulation, not full social AI, city simulation,
  war simulation, or economic simulation.
- Plan execution currently uses a deterministic NPC planning rule resolver and
  whitelisted planning actions. This is acceptable for v1.3, but v1.4 should
  consider naming and centralizing this more explicitly as the plan action
  registry.
- Debug views are local tools. They can expose structural ids and redacted
  summaries for inspection, but should not be reused in player UI.
- Behavior quality evals are deterministic safety/coverage checks, not an
  absolute measure of dramatic quality.
- Draft/preset authoring remains content-pack/draft oriented and does not
  modify active runtime state.
- No large-scale pathfinding, chase system, or complex GOAP planner is included.
- No LLM-driven NPC free planning is included.

## Acceptance Risks

- Low risk: future debug/timeline UI changes could accidentally reuse debug
  payloads in player-facing surfaces. Existing tests cover the current API/UI
  boundary; future work should keep redaction regression tests close to debug
  changes.
- Low risk: future behavior modules could bypass the centralized tick or
  lifecycle guards. The final v1.3 hardening added direct inactive-NPC guards to
  public intent, plan, relationship, and rumor-decision entry points.
- Low risk: future plan step expansion could blur the action-registry boundary.
  Keep step types whitelisted, deterministic, and rule-resolved.
- Low risk: future LLM-assisted authoring features must remain draft-only and
  must not become runtime NPC behavior authority.

No known high-risk release blocker remains.

## Recommended v1.4 Priorities

- Centralize and document the plan action registry for all future plan step
  types.
- Add richer but still deterministic evidence/case simulation for mystery
  worlds.
- Improve player-facing journal, rumor board, and discovered-behavior summaries.
- Expand local timeline replay with safer redaction controls and side-by-side
  player/debug views.
- Add more authoring validation for simulated-world balance and long-running
  schedule interactions.
- Explore optional draft-only LLM authoring assistants behind validation gates,
  without runtime state authority.
- Add more granular save/content migration support for heavily simulated worlds.

## Final Status

v1.3 is accepted.

The project is ready to proceed to v1.3 release notes and final freeze checks,
subject to normal repository hygiene checks for tracked temporary files,
sensitive data, and expected working-tree contents.
