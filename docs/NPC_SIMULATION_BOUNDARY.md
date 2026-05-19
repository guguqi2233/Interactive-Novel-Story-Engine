# NPC Simulation Boundary Contract

## Purpose

v1.3 introduces Advanced NPC Simulation: richer bounded NPC behavior under the
same local world-engine authority model.

NPC simulation is deterministic rule logic. It can choose goals, queue finite
intents, build short plans, react to known information, spread known rumors,
avoid conflict, and execute faction duties. It is not an LLM multi-agent
system, not an always-on background thinker, and not an alternate fact source.

The core rule remains:

NPC simulation may propose `StateDelta` and `Event` output. It must not directly
mutate `GameState`.

## Boundary Concepts

### npc_known_context

The set of facts, rumors, crimes, and structured signals a specific NPC is
allowed to use for simulation. It may include public facts and facts explicitly
known by that NPC through `NPCState.knowledge`, `GameState.npc_knowledge`, or
content `known_by` metadata.

It must not include hidden facts unknown to the NPC.

### npc_visible_context

The local, perceivable scene for one NPC, built through visibility rules. It can
include the NPC's current location, visible local objects, visible local NPCs,
and player-visible facts. It is not a license to read raw `GameState`.

### npc_private_state

The NPC's own rule-side state that may inform bounded behavior, such as mood,
condition, current goal id, current activity, and plan-state keys.

Private state is not player-visible by default and must not be copied into
narrator or player APIs unless a safe summary is explicitly produced.

### simulation_candidate_action

A finite rule-defined action candidate such as move, talk, report a known
crime, spread a known rumor, flee, guard, rest, avoid conflict, or execute a
faction duty.

A candidate action is a proposal. It must not mutate `GameState` by itself.
If selected and resolved, its effect must be represented as `StateDelta`.

### simulation_intent

A queued or prioritized desire to attempt one candidate action. An intent may
record source, priority, required facts, and target id. It is not authoritative
until resolved by deterministic rules.

v1.3.2 stores finite runtime intents as `NPCIntent` entries on
`NPCState.intent_queue`. Each intent includes id, NPC id, type, priority,
status, optional source event/goal, optional target, created/expiry turns,
preconditions, and a debug-only reason field.

### simulation_plan

A bounded list of intents or candidate steps for one NPC. A plan must have a
maximum step budget and must reject actions that require facts outside the NPC's
known context.

v1.3.3 stores short-term plans as `NPCPlan` entries on `NPCState.plans`. A plan
links back to a source intent, optional goal id, status, finite steps, current
step index, and creation/expiry turns. `NPCPlanStep` is a structured step with
a whitelisted type, optional target, preconditions, expected result, and status.

### simulation_event

The `Event` record for NPC simulation behavior. Any behavior that changes
state must include the produced `StateDelta` entries. Pure debug-only previews
must remain separate from runtime event history.

### debug_only_simulation_data

Local developer diagnostics such as rejected candidates, blocked reason codes,
plan traces, hidden fact ids, or budget usage. Debug data must stay behind debug
APIs/UI and must not enter player APIs, narrator prompts, ordinary RP prompts,
or normal authoring reports.

## NPC Simulation May Do

- Choose a goal from rule-defined candidates.
- Queue finite intents.
- Generate bounded short-term plans.
- React to information already known by the NPC.
- Spread rumors already known by the NPC.
- Avoid conflict based on known or visible threats.
- Execute faction duties through deterministic rules.
- Produce `StateDelta` entries for selected effects.
- Record `Event` entries for simulation behavior.

## NPC Simulation Must Not Do

- Read unknown hidden facts.
- Directly modify `GameState`.
- Bypass `StateDelta`.
- Change state without an `Event`.
- Call an LLM for free planning or behavior decisions.
- Call external network services or tools.
- Run unbounded or infinite planning loops.
- Let dead, incapacitated, or stunned NPCs perform ordinary simulation.
- Leak hidden NPC behavior to player APIs or narrator prompts.
- Treat debug traces as player-visible timeline entries.

## Policy Implementation

The shared policy module is:

`backend/app/engine/rules/npc_simulation_boundary.py`

It defines:

- `NPCSimulationPolicy`
- `NPCKnownContext`
- `NPCVisibleContext`
- `NPCPrivateState`
- `NPCSimulationContext`
- `SimulationCandidateAction`
- `SimulationIntent`
- `SimulationPlan`
- `SimulationEvent`
- `DebugOnlySimulationData`
- `NPCSimulationCheckResult`

`NPCSimulationPolicy` is read-only. It builds per-NPC simulation context,
checks lifecycle eligibility, validates candidate actions and plans against the
NPC's known facts, enforces finite plan size, and validates that simulation
events record state-changing deltas.

The policy does not call an LLM, does not execute external tools, does not write
disk, and does not apply deltas.

## Knowledge And Visibility Rules

Simulation context must be scoped per NPC:

- Public facts may be considered by any NPC.
- NPC-known hidden or discoverable facts may be considered only by that NPC.
- Unknown hidden facts are excluded from context and rejected if referenced by
  a candidate action or plan.
- Rumor candidates require the NPC to be in `rumor.known_by_npcs`.
- Crime candidates require witnessed crime state or explicit NPC knowledge.
- Visibility context is built through `get_visible_facts`, not raw state dumps.

## StateDelta And Event Rules

Candidate actions and plans are proposals only.

The selection/resolution layer may produce deltas, but the active state changes
only when those deltas are applied through `apply_delta` by the normal engine
flow. Runtime simulation behavior that changes state must be recorded as an
`Event` with the relevant `state_deltas`.

Intent queue changes follow the same rule. `enqueue_intent`, `cancel_intent`,
`complete_intent`, `fail_intent`, and `prune_expired_intents` return
`StateDelta` entries for `npcs.{npc_id}.intent_queue` plus system `Event`
records. `select_next_intent` is read-only and returns no intent for dead,
incapacitated, or stunned NPCs. Intents whose fact, rumor, or crime
preconditions are outside the NPC known context are rejected instead of queued
or selected.

Short-term plan changes also return `StateDelta` entries for
`npcs.{npc_id}.plans` plus system `Event` records. `build_plan_from_intent`
converts a known finite intent into whitelisted steps, `validate_plan` checks
targets and preconditions, and `advance_plan` delegates executable step effects
to the existing NPC planning rule resolver. Plans do not directly write
`GameState`; callers still apply returned deltas through the normal engine
flow.

Memory-based reactions follow the same boundary. `npc_memory_reactions` accepts
candidate `MemoryRecord` entries and `NPCMemoryReactionRule` rules, filters out
hidden/debug memories and unknown fact/crime/rumor references, and returns
finite `StateDelta` plus `Event` output. Reactions that create follow-up action
use `NPCIntentQueue`; they do not directly execute plans. Dedupe markers are
stored in `social_flags` using npc, reaction type, memory id, and rule id, so
the same memory reaction cannot fire forever.

Relationship-driven behavior is also finite and rule-scoped.
`npc_relationship_behavior` reads existing `RelationshipState`, derived
`RelationshipTone`, NPC-known facts, NPC-known rumors, emotional state, and
future faction-duty inputs. `RelationshipBehaviorRule` can produce help, warn,
avoid, report, lie/withhold, share-rumor, or reconciliation candidates. Action
outputs are intents, plan candidates, state deltas, and events. Hidden
relationships remain filtered from player-visible relationship graphs, and
rules requiring unknown facts or rumors are skipped.

Faction duties are bounded NPC-owned responsibilities. `NPCFactionDuty` entries
live on `NPCState.faction_duties` and can represent guard, patrol,
crime-reporting, member protection, hostile-player refusal, faction-rumor
spreading, information seeking, or curfew enforcement. `npc_faction_duties`
filters by life state, faction membership, target validity, known facts,
known rumors, and witnessed/known crimes. Duties produce intents or plan
candidates through the existing queue/plan systems and record system events;
they do not directly mutate `GameState`.

Rumor decisions are bounded and structural. `npc_rumor_decisions` produces an
`NPCRumorDecision` such as keep secret, share with actor/faction, distort,
ignore, report, or enqueue a spread-rumor intent. The decision system requires
the NPC to already know the rumor, uses relationship trust, faction alignment,
fear/loyalty-like relationship inputs, rumor tags, secrecy level, credibility,
and emotional intensity, and records an event. It never rewrites rumor text with
LLM output, never exposes hidden fact text, and uses `social_flags` markers to
avoid repeating the same rumor decision indefinitely.

Fear, trust, and loyalty are lightweight disposition signals.
`NPCSocialDisposition` lives on `NPCState` with trust/fear toward the player,
faction and NPC loyalty, moral flexibility, risk/conflict tolerance, and secrecy
preference. `npc_social_disposition` can derive values from relationships,
faction state, and emotional state, update values from deterministic events via
`StateDelta`, convert them into behavior weights, and summarize them for
dialogue tone. Disposition does not override relationship state, grant facts,
or let an LLM modify NPC psychology directly.

Conflict avoidance is a bounded simulation rule, not a chase system or
free-form survival AI. `npc_conflict_avoidance` may inspect visible hostile
actors, known danger context, injury/life state, emotional state, active faction
duties, and `NPCSocialDisposition` to enqueue finite intents such as
`avoid_actor`, `flee_from_actor`, `rest`, `call_for_help`, `hide`, or
`avoid_location`. It must not directly mutate `GameState`; any flee, hide, or
rest outcome is handled later through intent, plan, and action rules with
`StateDelta`. Hidden NPC avoidance remains system/debug-only unless the NPC is
actually visible to the player.

## LLM Boundary

NPC simulation has no provider authority.

The LLM may later express an already selected NPC behavior in narration or
dialogue if the prompt context is visibility-safe. It must not choose NPC
actions, score candidates, create hidden facts, grant NPC knowledge, or write
state.

## Debug Boundary

Debug traces may include blocked reason codes, hidden fact ids, scoped context
ids, and budget information. They must be exposed only through debug APIs gated
by `ENABLE_DEBUG_API` and must not be reused in player UI, narrator prompt
builders, or normal authoring reports.

## Acceptance Requirements

- Unknown hidden facts do not enter `npc_known_context`.
- Hidden facts outside NPC knowledge cannot appear in accepted plans.
- Candidate action validation does not mutate `GameState`.
- State-changing simulation behavior is represented by `Event` plus
  `StateDelta`.
- Dead, incapacitated, or stunned NPCs cannot run ordinary simulation.
- No real LLM provider is called by simulation policy or tests.
