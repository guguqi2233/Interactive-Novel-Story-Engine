# v1.3 Roadmap: Advanced NPC Simulation

## Version Goal

v1.3 upgrades NPC behavior from simple deterministic planning into a richer
advanced simulation layer while preserving the core engine boundary.

NPCs should appear more autonomous through finite intent queues, short-term
plans, memory-aware reactions, relationship and faction-driven choices, rumor
decisions, fear/trust/loyalty scoring, conflict avoidance, daily replanning,
debug tooling, and regression playtests.

The theme is bounded autonomy:

NPCs may choose from finite rule-defined actions. They do not become LLM agents.

The rule remains:

NPC simulation proposes deterministic `StateDelta` and `Event` output. It never
directly mutates `GameState`.

## Frozen Constraints

- NPCs cannot know unknown facts.
- NPC simulation cannot directly modify `GameState`.
- All NPC simulation state changes must use `StateDelta`.
- All NPC simulation behavior must record `Event`.
- NPC planning can produce only finite candidate actions.
- NPC action results are judged by deterministic rules, not by an LLM.
- The LLM may express NPC behavior or dialogue, but cannot decide NPC behavior.
- Dead or incapacitated NPCs cannot run ordinary simulation.
- Hidden NPC behavior cannot leak to player APIs or narrator prompts.
- Debug APIs may show simulation details only behind `ENABLE_DEBUG_API`.
- Simulation ticks must be deterministic.
- Simulation must enforce max steps and max actions to avoid infinite loops.

## Not In v1.3

- LLM multi-agent free simulation.
- LLM direct NPC behavior decisions.
- Omniscient NPCs.
- NPC direct `GameState` mutation.
- NPC bypass of Visibility, Knowledge, `StateDelta`, or `EventLog`.
- Large-scale city simulation.
- Large-scale war simulation.
- Large-scale economy simulation.
- Background infinite NPC thinking loops.
- NPC calls to external network services or tools.
- Arbitrary-code plugins driving NPC behavior.
- Realtime always-on simulation independent of player/system ticks.
- Automatic retcon of facts, relationships, quests, or memories.

## Recommended Development Order

1. NPC Simulation Boundary Contract.
2. NPC Simulation Tick Orchestrator.
3. NPC Intent Queue.
4. NPC Short-Term Plan System.
5. NPC Memory-Based Reactions.
6. NPC Relationship-Driven Behavior.
7. NPC Fear / Trust / Loyalty Models.
8. NPC Conflict Avoidance.
9. NPC Faction Duties.
10. NPC Rumor Decision System.
11. NPC Daily Goal Replanning.
12. NPC Simulation Debugger Backend.
13. NPC Behavior Timeline Visualizer.
14. NPC Simulation Debugger Frontend.
15. NPC Simulation Authoring Presets.
16. NPC Simulation Quality Evals.
17. NPC Simulation Regression Playtests.

The first two modules should land before adding new behavior. They define the
simulation contract and bounded tick execution model that every later behavior
must reuse.

## Module Roadmap

### 1. NPC Simulation Boundary Contract

Goal: Document and encode the v1.3 boundary for bounded NPC autonomy.

Data structures:

- `NPCSimulationPolicy`
- `NPCSimulationScope`
- `NPCActionAuthority`
- `NPCSimulationRiskLevel`
- `NPCSimulationBoundaryReport`
- `NPCSimulationCapability`

API changes:

- `GET /debug/npc-simulation/boundary`
- `POST /debug/npc-simulation/boundary/check`

Frontend changes:

- Add a debug-only simulation boundary panel.
- Show whether simulation is deterministic, knowledge-scoped, StateDelta-only,
  event-logged, and max-step bounded.

Tests:

- Policy rejects direct `GameState` mutation.
- Policy rejects LLM behavior authority.
- Boundary report redacts hidden fact text and debug-only payloads in normal
  views.
- Dead/incapacitated NPC policy blocks ordinary simulation.

Acceptance:

- Every v1.3 simulation module can reference the shared policy.
- Boundary check clearly reports no-LLM-authority, no-omniscience,
  StateDelta-only, and Event-required status.

NPC Knowledge / Visibility impact: establishes that each NPC can only reason
from `npc_known_facts`, public facts, visible local state, and explicitly known
rumors/crimes.

GameState / StateDelta / EventLog impact: no schema mutation required at first;
all behavior must emit deltas and events.

LLM boundary impact: no new model authority.

Leak risk: high if boundary reports include hidden fact text or debug plans.
Reports must use ids, counts, and redacted summaries.

### 2. NPC Simulation Tick Orchestrator

Goal: Provide one deterministic orchestration layer for v1.3 NPC simulation
steps.

Data structures:

- `NPCSimulationTickRequest`
- `NPCSimulationTickResult`
- `NPCSimulationStep`
- `NPCSimulationBudget`
- `NPCSimulationDecisionTrace`
- `NPCSimulationEventSummary`

API changes:

- `POST /debug/npc-simulation/tick-preview`
- `POST /debug/npc-simulation/tick-run`
- Optional debug-only `GET /debug/npc-simulation/last-tick`

Frontend changes:

- Debug-only tick preview/run controls.
- Show max NPCs, max actions, deterministic seed, skipped NPCs, produced
  `StateDelta` count, and produced `Event` count.

Tests:

- Tick is deterministic for the same state and budget.
- Max step/action budget is enforced.
- Dead/incapacitated NPCs are skipped.
- Tick preview does not mutate active `GameState`.
- Tick run applies only through `StateDelta`.
- Every behavior action records an event.

Acceptance:

- All v1.3 behavior systems plug into the orchestrator.
- No direct state mutation or unbounded loop is possible.

NPC Knowledge / Visibility impact: orchestrator passes only per-NPC scoped
context to behavior modules.

GameState / StateDelta / EventLog impact: centralizes simulation deltas and
events; can reuse existing world tick event flow.

LLM boundary impact: no provider calls.

Leak risk: medium. Debug traces can include hidden simulation details and must
stay debug-gated.

### 3. NPC Intent Queue

Goal: Give NPCs a finite queue of rule-derived intents that can be consumed by
the simulation orchestrator.

Data structures:

- `NPCIntent`
- `NPCIntentQueue`
- `NPCIntentPriority`
- `NPCIntentSource`
- `NPCIntentStatus`
- `NPCIntentResolution`

API changes:

- `GET /debug/npc-simulation/npcs/{npc_id}/intent-queue`
- `POST /debug/npc-simulation/npcs/{npc_id}/intent-queue/preview`
- Authoring validation for allowed intent types in NPC presets.

Frontend changes:

- Debug panel for queued intents, priority, source, age, status, and rejection
  reason.

Tests:

- Queue ordering is deterministic.
- Unknown fact references are rejected.
- Dead/incapacitated NPC queues do not execute ordinary intents.
- Queue execution emits `StateDelta` and `Event`.
- Queue capacity is enforced.

Acceptance:

- NPCs can hold finite pending intents without background free-thinking.
- Invalid or knowledge-illegal intents are skipped with traceable reasons.

NPC Knowledge / Visibility impact: every intent records required facts and is
filtered against the NPC's knowledge before execution.

GameState / StateDelta / EventLog impact: queue status changes use
`StateDelta`; execution records events.

LLM boundary impact: LLM cannot enqueue authoritative intents.

Leak risk: medium. Intent debug reasons may mention hidden ids; player surfaces
must not receive them.

### 4. NPC Short-Term Plan System

Goal: Upgrade existing one-step NPC planning into bounded short-term plans with
finite actions and stop conditions.

Data structures:

- `NPCShortTermPlan`
- `NPCPlanStep`
- `NPCPlanStatus`
- `NPCPlanConstraint`
- `NPCPlanStopReason`

API changes:

- `GET /debug/npc-simulation/npcs/{npc_id}/plans`
- `POST /debug/npc-simulation/npcs/{npc_id}/plans/preview`

Frontend changes:

- Plan list and step timeline in the debug UI.
- Show current step, next eligible step, blockers, and stop reason.

Tests:

- Plans choose only allowed actions.
- Missing references block plan steps.
- Inaccessible locations block movement.
- Max step budget stops long plans.
- Plans do not execute for dead/incapacitated NPCs.

Acceptance:

- NPCs can pursue short plans without free-form reasoning or infinite loops.

NPC Knowledge / Visibility impact: plan preconditions must be scoped to NPC
knowledge and local visibility.

GameState / StateDelta / EventLog impact: plan creation/status/step execution
uses deltas and events.

LLM boundary impact: deterministic plan selection only.

Leak risk: medium for debug plan details.

### 5. NPC Memory-Based Reactions

Goal: Let NPCs react to recent memories and events they are allowed to know.

Data structures:

- `NPCMemorySignal`
- `NPCReactionCandidate`
- `NPCMemoryReactionRule`
- `NPCReactionCooldown`

API changes:

- `GET /debug/npc-simulation/npcs/{npc_id}/memory-signals`
- Extend debug tick trace with memory-based reaction candidates.

Frontend changes:

- Debug view showing memory signal id, visibility class, reaction candidate,
  cooldown, and selected/blocked status.

Tests:

- Hidden/debug-only memory is not considered unless the NPC is allowed to know
  it.
- Reaction cooldown is deterministic.
- Reactions produce `StateDelta` and `Event`.
- Player API and narrator do not receive hidden memory details.

Acceptance:

- NPC reactions can reference allowed memory without making memory authoritative
  facts.

NPC Knowledge / Visibility impact: memory signals are filtered by
`RoleplayContextPolicy`, NPC knowledge, and memory visibility.

GameState / StateDelta / EventLog impact: reaction effects are deltas; reaction
occurrences are events.

LLM boundary impact: no LLM memory interpretation for action decisions.

Leak risk: high if hidden memory text enters normal output. Use ids/summaries
and debug gates.

### 6. NPC Relationship-Driven Behavior

Goal: Let relationships influence finite NPC choices such as approach, avoid,
help, warn, report, refuse, or seek ally.

Data structures:

- `NPCRelationshipBehaviorRule`
- `NPCRelationshipDecisionInput`
- `NPCRelationshipDecisionScore`
- `NPCRelationshipActionCandidate`

API changes:

- Debug candidate endpoint within simulation trace.
- Optional authoring preset fields for relationship behavior thresholds.

Frontend changes:

- Debug scoring panel for trust, fear, affinity, obligation, hostility, and
  selected finite action.

Tests:

- Relationship scores change candidate ordering but not hidden knowledge.
- Hidden relationships do not leak to player views.
- Behavior output remains finite and deterministic.
- Relationship value changes still require rule deltas.

Acceptance:

- NPC social behavior is visibly affected by relationship state without LLM
  arbitration.

NPC Knowledge / Visibility impact: relationship data may influence private NPC
behavior, but player-visible summaries remain filtered.

GameState / StateDelta / EventLog impact: any relationship changes use deltas;
behavior decisions record events.

LLM boundary impact: LLM may describe a chosen behavior, not choose it.

Leak risk: medium for hidden relationships in debug traces.

### 7. NPC Fear / Trust / Loyalty Models

Goal: Add deterministic scoring models that summarize NPC risk and attachment
without creating a full psychology simulator.

Data structures:

- `NPCSocialMotivation`
- `NPCFearModel`
- `NPCTrustModel`
- `NPCLoyaltyModel`
- `NPCMotivationScore`

API changes:

- `GET /debug/npc-simulation/npcs/{npc_id}/motivation`
- Include motivation scores in simulation debug traces.

Frontend changes:

- Compact motivation score panel for debug use.

Tests:

- Scores are deterministic and bounded.
- Scores do not grant facts.
- Dead/incapacitated NPCs do not produce ordinary motivation actions.
- Hidden score inputs are redacted from player and normal authoring views.

Acceptance:

- Scores can inform candidate ranking but cannot bypass rules or knowledge.

NPC Knowledge / Visibility impact: model inputs must be available to the NPC or
safe derived runtime state.

GameState / StateDelta / EventLog impact: scores can be derived or stored; any
stored updates use deltas.

LLM boundary impact: no LLM scoring.

Leak risk: medium for debug score inputs.

### 8. NPC Conflict Avoidance

Goal: Let NPCs avoid danger, hostile actors, crime scenes, or feared locations
when deterministic rules indicate risk.

Data structures:

- `NPCThreatSignal`
- `NPCAvoidanceCandidate`
- `NPCAvoidanceRule`
- `NPCAvoidanceCooldown`

API changes:

- Include avoidance candidates in simulation tick preview.

Frontend changes:

- Debug visualization of threat source, known/visible status, selected avoidance
  action, and blocked reason.

Tests:

- NPC cannot avoid threats it does not know or perceive.
- Hidden NPC movement does not leak to player API.
- Avoidance movement uses legal exits and `StateDelta`.
- Max action limits prevent repeated flee loops.

Acceptance:

- NPCs can avoid danger in bounded, knowledge-scoped ways.

NPC Knowledge / Visibility impact: threat signals require local perception or
known facts.

GameState / StateDelta / EventLog impact: movement/activity changes use deltas;
avoidance records events.

LLM boundary impact: no LLM threat assessment.

Leak risk: medium when avoidance reveals hidden threat existence.

### 9. NPC Faction Duties

Goal: Let faction membership produce finite duties such as patrol, report,
guard, warn ally, avoid enemy, or spread faction rumor.

Data structures:

- `NPCFactionDuty`
- `FactionDutyRule`
- `FactionDutyPriority`
- `FactionDutyAssignment`
- `FactionDutyCooldown`

API changes:

- `GET /debug/npc-simulation/factions/{faction_id}/duties`
- Include duty candidates in NPC simulation traces.

Frontend changes:

- Debug faction duty panel by NPC and faction.

Tests:

- Missing faction refs are rejected.
- Hidden faction conflicts do not enter player graph.
- Duties select finite legal actions.
- Duties do not run for dead/incapacitated NPCs.

Acceptance:

- Faction affiliation can influence NPC actions without large-scale war
  simulation.

NPC Knowledge / Visibility impact: faction conflict inputs are scoped by NPC
faction membership and known conflict status.

GameState / StateDelta / EventLog impact: duty status and effects use deltas
and events.

LLM boundary impact: no LLM faction command system.

Leak risk: medium for hidden faction conflicts in debug views.

### 10. NPC Rumor Decision System

Goal: Improve rumor spread from simple known-rumor propagation into finite,
relationship-aware, knowledge-safe decisions.

Data structures:

- `NPCRumorDecision`
- `NPCRumorCandidate`
- `NPCRumorAudienceScore`
- `NPCRumorSafetyCheck`
- `NPCRumorDedupeKey`

API changes:

- Include rumor candidates and blocked reasons in simulation debug traces.

Frontend changes:

- Debug rumor decision panel with source NPC, target NPC, trust/fear score,
  known-by status, dedupe status, and leak-risk status.

Tests:

- NPC only spreads rumors it knows.
- Hidden fact text is not exposed to player or narrator.
- Rumor target selection is deterministic.
- Dedupe/cooldown prevents repeated loops.

Acceptance:

- Rumor decisions feel more social while staying knowledge-safe.

NPC Knowledge / Visibility impact: rumor candidates require `known_by_npcs`.

GameState / StateDelta / EventLog impact: known-by and spread-level changes use
deltas; rumor events are recorded.

LLM boundary impact: no LLM rumor choice.

Leak risk: high if hidden fact text is copied into player-facing rumor text.

### 11. NPC Daily Goal Replanning

Goal: Let NPCs periodically reconsider goals based on schedule, faction duties,
memory signals, relationship state, and local conditions.

Data structures:

- `NPCDailyGoalPlan`
- `NPCGoalReplanRequest`
- `NPCGoalReplanResult`
- `NPCGoalCandidateScore`
- `NPCGoalReplanCooldown`

API changes:

- `POST /debug/npc-simulation/npcs/{npc_id}/replan-preview`
- Include daily replanning summary in tick traces.

Frontend changes:

- Debug replanning panel showing goal candidates, scores, selected goal, and
  blocked reasons.

Tests:

- Replanning is deterministic.
- Replanning respects allowed actions and NPC knowledge.
- Replanning has cooldown/max frequency.
- Replanning uses deltas and events.

Acceptance:

- NPCs can update goals without free-form cognition or LLM decisions.

NPC Knowledge / Visibility impact: candidate goals must be derived from known
or safely perceivable state.

GameState / StateDelta / EventLog impact: goal changes use deltas and events.

LLM boundary impact: no LLM goal selection.

Leak risk: medium for debug goal reasons.

### 12. NPC Simulation Debugger Backend

Goal: Provide debug-only APIs for inspecting simulation decisions, traces,
budgets, skipped actions, and produced events.

Data structures:

- `NPCSimulationDebugTrace`
- `NPCSimulationDebugStep`
- `NPCSimulationDebugBlocker`
- `NPCSimulationDebugSnapshot`

API changes:

- `GET /debug/npc-simulation/traces`
- `GET /debug/npc-simulation/traces/{trace_id}`
- `GET /debug/npc-simulation/npcs/{npc_id}/summary`

Frontend changes:

- Backend only for this module; frontend consumes it in later modules.

Tests:

- Endpoints require `ENABLE_DEBUG_API`.
- Debug output does not include API keys or raw env.
- Player APIs do not expose debug traces.
- Hidden text redaction is enforced outside explicit debug detail views.

Acceptance:

- Developers can inspect why NPC simulation did or did not act.

NPC Knowledge / Visibility impact: debug traces can show scoped knowledge ids,
but player APIs cannot.

GameState / StateDelta / EventLog impact: read-only inspection; no mutation.

LLM boundary impact: no provider calls.

Leak risk: high if debug traces are exposed through normal/player APIs.

### 13. NPC Behavior Timeline Visualizer

Goal: Show NPC simulation behavior over time as a debug timeline tied to
events, deltas, plans, and blockers.

Data structures:

- `NPCBehaviorTimeline`
- `NPCBehaviorTimelineEntry`
- `NPCBehaviorDeltaSummary`
- `NPCBehaviorVisibilityMarker`

API changes:

- `GET /debug/npc-simulation/timeline`
- Optional filters: `npc_id`, `turn_from`, `turn_to`, `action_type`.

Frontend changes:

- Timeline view grouped by turn and NPC.
- Mark visible-to-player vs debug-only entries.
- Link entries to raw debug traces when debug mode is enabled.

Tests:

- Timeline derives from events/traces without mutating state.
- Hidden/debug entries are not visible in player UI.
- Filters are deterministic and stable.

Acceptance:

- NPC simulation can be audited turn-by-turn in debug tools.

NPC Knowledge / Visibility impact: timeline must distinguish player-visible
from debug-only behavior.

GameState / StateDelta / EventLog impact: read-only view over events/traces.

LLM boundary impact: no provider calls.

Leak risk: high if hidden NPC behavior appears in player timeline.

### 14. NPC Simulation Debugger Frontend

Goal: Add frontend tools for inspecting v1.3 simulation safely in local debug
mode.

Data structures:

- Frontend mirrors for debug trace, timeline, queue, plan, and motivation
  response models.

API changes:

- No new backend endpoints required beyond debugger/timeline APIs.

Frontend changes:

- NPC Simulation Dashboard.
- Per-NPC intent queue view.
- Plan and motivation panels.
- Tick preview/run controls.
- Behavior timeline.
- Hidden/debug-only badges.

Tests:

- Frontend build passes.
- Disabled debug API state does not crash.
- Player UI does not display simulation debug content.
- Hidden data badges do not show raw hidden text in normal panels.

Acceptance:

- Local creator can inspect bounded NPC autonomy without exposing details to
  player UI.

NPC Knowledge / Visibility impact: UI should surface scoped knowledge ids only
in debug mode.

GameState / StateDelta / EventLog impact: UI preview is read-only; run calls
backend tick execution.

LLM boundary impact: no frontend LLM behavior control.

Leak risk: high if debug widgets are reused in player UI.

### 15. NPC Simulation Authoring Presets

Goal: Provide local authoring presets for common bounded NPC behavior patterns.

Data structures:

- `NPCSimulationPreset`
- `NPCSimulationPresetRule`
- `NPCSimulationPresetThreshold`
- `NPCSimulationPresetValidation`

API changes:

- `GET /authoring/npc-simulation/presets`
- `POST /authoring/npc-simulation/presets/preview`
- `POST /authoring/npc-simulation/presets/validate`
- `POST /authoring/npc-simulation/presets/save`

Frontend changes:

- Authoring panel for presets such as cautious villager, loyal guard,
  rumor-monger, fearful witness, faction patrol, and conflict avoider.

Tests:

- Presets validate allowed actions only.
- Presets cannot include script execution or network calls.
- Presets cannot grant hidden facts.
- Save goes through Authoring Validation Gate.

Acceptance:

- Creators can configure bounded behavior styles without code plugins.

NPC Knowledge / Visibility impact: presets define thresholds/actions, not
knowledge grants.

GameState / StateDelta / EventLog impact: preset saves are content-pack edits;
runtime effects still use deltas/events.

LLM boundary impact: no prompt authority expansion.

Leak risk: medium if hidden preset notes appear in player UI.

### 16. NPC Simulation Quality Evals

Goal: Add deterministic evaluation checks for v1.3 simulation safety and
believability.

Data structures:

- `NPCSimulationEvalCase`
- `NPCSimulationEvalResult`
- `NPCSimulationBoundaryViolation`
- `NPCSimulationCoverageMetric`

API changes:

- Optional debug/eval endpoint behind `ENABLE_EVAL_API`.
- CLI entry for NPC simulation evals.

Frontend changes:

- Optional Quality dashboard section for NPC simulation coverage and boundary
  failures.

Tests:

- Eval catches unknown hidden fact usage.
- Eval catches missing `Event`.
- Eval catches direct state mutation if detectable.
- Eval catches unbounded action loops.
- Eval catches LLM provider calls in simulation paths.

Acceptance:

- NPC simulation has automated guardrails before acceptance.

NPC Knowledge / Visibility impact: evals focus heavily on knowledge and hidden
fact boundaries.

GameState / StateDelta / EventLog impact: evals assert StateDelta/Event
discipline.

LLM boundary impact: evals assert no LLM simulation decisions.

Leak risk: low if reports stay structural; medium if debug evidence embeds
hidden text.

### 17. NPC Simulation Regression Playtests

Goal: Add scenario-level playtests that exercise NPC simulation across multiple
turns without real LLM calls.

Data structures:

- `NPCSimulationPlaytestScenario`
- `NPCSimulationPlaytestStep`
- `NPCSimulationPlaytestExpectation`
- `NPCSimulationPlaytestReport`

API changes:

- Extend scenario/playtest runners with NPC simulation expectations.
- Optional endpoint behind `ENABLE_PLAYTEST_API` or debug gate.

Frontend changes:

- Playtest dashboard entries for NPC simulation regressions.

Tests:

- Repeated runs are deterministic.
- NPCs do not act when dead/incapacitated.
- NPCs do not learn unknown hidden facts.
- NPC actions use StateDelta and Event.
- Hidden NPC behavior does not enter player-visible output.
- No real API calls are made.

Acceptance:

- v1.3 simulation behavior is regression-tested end-to-end.

NPC Knowledge / Visibility impact: playtests include knowledge leak probes.

GameState / StateDelta / EventLog impact: playtests assert runtime contract.

LLM boundary impact: tests use mock/local/fake providers only.

Leak risk: low if reports redact hidden text.

## v1.3 Integration Test Requirements

1. Simulation Boundary:
   - NPC simulation cannot directly mutate `GameState`.
   - All simulation effects are `StateDelta`.
   - All simulation actions produce `Event`.
   - Dead/incapacitated NPCs are skipped.

2. Tick Orchestration:
   - Tick preview is read-only.
   - Tick run is deterministic.
   - Max step/action limits are enforced.
   - Simulation cannot enter an infinite loop.

3. Knowledge / Visibility:
   - NPCs cannot act on unknown facts.
   - NPCs cannot spread rumors they do not know.
   - Hidden facts do not enter player API, narrator prompt, or normal timeline.
   - Hidden NPC behavior remains debug-only unless player-visible by rules.

4. Behavior Systems:
   - Intent queue ordering is stable.
   - Short-term plans use finite actions.
   - Relationship/fear/trust/loyalty scores affect ranking only.
   - Faction duties do not become war simulation.
   - Conflict avoidance does not reveal unknown threats.
   - Daily replanning has cooldown and max frequency.

5. Debug / Frontend:
   - Debug APIs require `ENABLE_DEBUG_API`.
   - Eval APIs require `ENABLE_EVAL_API`.
   - Playtest APIs require `ENABLE_PLAYTEST_API` or debug mode.
   - Frontend build passes.
   - Disabled debug/API states do not crash.

6. LLM / Security:
   - Simulation paths do not instantiate concrete providers.
   - Simulation paths do not call `generate_json` or `generate_text`.
   - Tests use mock/local/fake providers only.
   - No scripts, external tools, or network calls drive NPC behavior.

## v1.3 Final Acceptance Standards

- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.
- v1.3 acceptance report exists.
- v1.3 release notes exist.
- LLM boundary audit confirms no LLM NPC behavior authority.
- Visibility audit confirms no hidden fact, NPC secret, hidden memory, hidden
  relationship, hidden faction, or debug trace leaks to player surfaces.
- Security audit confirms no arbitrary code, tool, network, or provider
  escalation in NPC simulation.
- Simulation tick is deterministic and bounded.
- NPC behavior is richer but finite, explainable, and debuggable.
- Active runtime state remains governed by `StateDelta` and `Event`.
- No high-risk release blocker remains.

## v1.4 Candidate Directions

- Save/content migration assistant for heavily simulated worlds.
- Scenario Director Pro for deterministic multi-scene pacing.
- Advanced mystery/case simulation with evidence chains and suspect behavior.
- Bounded settlement schedule and occupation modeling.
- Local-only cinematic replay tools for event/timeline visualization.
- Player-facing journal and rumor board improvements.
- More granular authoring/debug normal-view redaction models.
- Optional draft-only LLM authoring assistants with strict validation gates.
