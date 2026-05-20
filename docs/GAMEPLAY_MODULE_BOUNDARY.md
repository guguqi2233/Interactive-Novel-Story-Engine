# Gameplay Module Boundary

v1.6 introduces Advanced Gameplay Modules: local, validated gameplay
extensions that add new rule-driven actions and optional state fields without
turning the engine into an arbitrary plugin host.

The existing world-engine contract remains the root authority:

`ActionRegistry -> ActionHandler/rule module -> ActionResult -> StateDelta ->
EventLog -> Visibility / NPC Knowledge filtering -> narrator/player API`.

Gameplay modules extend the deterministic rule layer. They do not execute
untrusted code, call the LLM as judge, directly modify `GameState`, write the
database, or bypass visibility.

## Concepts

- `gameplay_module`: A local gameplay extension package that declares actions,
  affordances, state extensions, event types, migration defaults, and quality
  tests.
- `action_mod`: A declarative module contribution that adds or configures a
  gameplay action.
- `declarative_action`: A schema-defined action with parameters,
  preconditions, checks, effects, event type, and visibility policy. It is data,
  not executable code.
- `rule_module`: Trusted engine code that evaluates checks and turns declared
  effects into `StateDelta` values.
- `module_state_extension`: Optional save/runtime state fields declared by a
  module and guarded by migration compatibility.
- `module_event_type`: A module-defined event category used for structured
  logging and replay.
- `module_debug_data`: Debug-only traces, reasons, roll details, or effect
  previews. These are never player-visible by default.
- `action_affordance`: A player/NPC-visible possibility such as "cast",
  "hack", "craft", "deduce", or "repair", filtered through visibility and
  knowledge.
- `module_permission`: A declared capability. Safe permissions include
  registering actions, declaring checks/effects, StateDelta templates, event
  types, save migration defaults, affordances, and quality tests. Unsafe
  permissions such as arbitrary code execution are rejected.

## Allowed

Gameplay modules may:

- Register new actions through `ActionRegistry`.
- Register object/NPC/location affordances.
- Declare preconditions, checks, and effects.
- Declare `StateDelta` templates for rule-approved paths.
- Declare module event types.
- Declare save migration defaults and compatibility metadata.
- Declare quality tests and regression fixtures.
- Provide debug-only traces for local debugging.
- Provide player-facing affordances only after `Visibility` and NPC Knowledge
  filters allow them.

## Forbidden

Gameplay modules must not:

- Execute arbitrary Python, JavaScript, shell, WASM, or package scripts.
- Directly mutate active `GameState`.
- Write directly to the database or save files.
- Read `.env`, API keys, provider secrets, database files, logs, caches, or
  arbitrary local files.
- Access the network.
- Call an LLM to decide action success, damage, spell effects, hacking
  results, deduction truth, crafting output, combat outcomes, or other
  canonical gameplay results.
- Bypass `StateDelta`.
- Skip `EventLog`.
- Bypass `Visibility`, player-visible fact filtering, or NPC Knowledge.
- Expose hidden facts, NPC secrets, hidden relationship data, hidden gameplay
  state, or module debug reasons to player APIs or normal UI.

## Runtime Rules

1. A module action must resolve through the unified `ActionRegistry`.
2. A module action must return a structured `ActionResult`.
3. A successful or consequential module action must return `StateDelta`
   effects.
4. A module action must record an `Event`; the event must include the relevant
   state deltas unless it is an explicit no-op event.
5. Hidden module outputs must be stored as hidden/debug data and redacted from
   normal reports.
6. NPC module actions can only use facts, rumors, relationships, locations, and
   targets known or visible to that NPC.
7. Player-facing affordances can only include visible objects, locations, NPCs,
   facts, and module state.
8. Debug traces are local-only and gated by `ENABLE_DEBUG_API`.

## Import / Enable Rules

Module import is not module enablement.

- Import performs schema validation, package safety checks, hidden leak checks,
  dependency checks, and executable-file rejection.
- Enablement requires explicit user confirmation, validation success, quality
  gate success when configured, and save compatibility/migration review.
- Untrusted modules are disabled by default.
- Module packages cannot contain executable entrypoints, provider secrets, API
  keys, `.env`, databases, logs, caches, or raw hidden fact text in safe export
  mode.

## LLM Boundary

LLMs remain language-layer tools. They may:

- Parse user text into a candidate intent.
- Narrate a module action after the rule engine adjudicates it.
- Help draft module content in authoring mode, subject to validation.

LLMs may not:

- Decide whether a module action succeeds.
- Generate canonical effects without validation.
- Write directly to `GameState`.
- Expand Prompt Profile permissions.
- See hidden facts or debug traces in normal prompts.

## Policy Enforcement

The initial v1.6 policy module is `app.engine.gameplay_modules`. It provides:

- `GameplayModulePolicy`
- `GameplayModule`
- `ActionMod`
- `DeclarativeAction`
- `ModuleStateExtension`
- `ModuleEventType`
- `ModuleDebugData`
- `ActionAffordance`
- `ModulePermission`
- `check_gameplay_module_boundary`

The policy blocks direct `GameState` mutation, missing `StateDelta`, missing
`Event`, forbidden permissions, LLM adjudication, visibility bypass, secret
access, and network access.

## Acceptance Criteria

- Module preview/import/validate do not modify active `GameState`.
- Module action effects must be `StateDelta` values.
- Module actions must record `Event` entries.
- Hidden module output is redacted from normal/player-facing views.
- Permissions for arbitrary code, direct writes, secrets, network, LLM
  adjudication, and visibility bypass are rejected.
- Tests use mock/fake/local_stub providers and do not call real LLM APIs.
