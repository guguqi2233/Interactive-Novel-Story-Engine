# v1.6 Release Notes

## Version Name

v1.6 Advanced Gameplay Modules

## Version Goal

v1.6 adds local, rule-driven gameplay modules and declarative Action Mods to
the interactive novel world engine. It expands the kinds of gameplay the
engine can adjudicate while preserving the original authority boundary:

- This remains a local personal engine / studio.
- The world engine remains the source of truth.
- The LLM remains a parser, narrator, summarizer, style layer, and optional
  draft assistant. It is not the world referee.
- Gameplay modules cannot directly modify `GameState`.
- All module action consequences still flow through structured `ActionResult`,
  `StateDelta`, and `EventLog`.

v1.6 is not an arbitrary-code plugin system, not a full tactical combat game,
not a complex economy simulator, and not a large-scale war simulator.

## New Features

### Gameplay Module Boundary

v1.6 introduces `docs/GAMEPLAY_MODULE_BOUNDARY.md` and a policy layer for
advanced gameplay modules. The boundary defines:

- `gameplay_module`
- `action_mod`
- `declarative_action`
- `rule_module`
- `module_state_extension`
- `module_event_type`
- `module_debug_data`
- `action_affordance`
- `module_permission`

Modules may register actions, declare affordances, define preconditions,
checks, effects, event types, migration defaults, and quality tests. They may
not execute arbitrary code, call an LLM as judge, write the database, access
network/files/secrets, bypass visibility, or mutate `GameState` directly.

### Gameplay Module Manifest

`GameplayModuleManifest` lets local module packages declare:

- id, name, version, module type, engine/schema compatibility
- dependencies and conflicts
- provided actions, rules, state extensions, and event types
- permissions
- save compatibility and migration defaults
- quality tests

Dangerous permissions default to false, including `execute_code`,
`access_network`, `access_filesystem`, `call_llm`, and direct GameState
mutation.

### Declarative Action Mod System

Declarative Action Mods are data, not scripts. `DeclarativeActionDefinition`
supports action ids, labels, aliases, categories, target specs, affordance
requirements, time cost, preconditions, checks, outcomes, StateDelta templates,
event type, visibility policy, and narrator hints.

`DeclarativeActionHandler` resolves these actions without executing code or
calling the LLM.

### Action Registry Extension

`ActionRegistry` now supports core and module actions through a unified
surface:

- register core actions
- register module actions
- unregister module actions
- list available actions
- fetch action metadata
- detect alias conflicts

Intent parsing and suggested actions can discover enabled module actions, but
disabled module actions cannot be invoked. Suggested actions still depend on
visible affordances.

### Action DSL

v1.6 adds a constrained Action DSL for declarative preconditions, checks, and
effects.

Supported preconditions include actor location, target existence, target
visibility, inventory/status requirements, target tags, combat state, NPC
knowledge, and fact visibility.

Supported checks include skill, reputation, relationship, item, deterministic
random threshold, and fixed success checks.

Supported effects include StateDelta templates, fact discovery, status
changes, item consumption, time advancement, and event markers. Effects
generate `StateDelta`; they do not apply it directly.

The final v1.6 acceptance fix ensures generic fact discovery cannot promote
hidden or unknown facts into `player_visible_facts`.

### Gameplay Systems

v1.6 adds lightweight, rule-driven modules:

- Magic System: spells, mana/focus, spell targets, effects, failure effects,
  visibility policy, and crime/witness consequences.
- Hacking System: terminals, security doors, cameras, logs, traces, alarms,
  cyber-crime consequences, and hidden log filtering.
- Crafting System: recipes, required/consumed materials, tools, stations,
  repair/dismantle support, time cost, and failure policy.
- Investigation / Deduction System: evidence, testimony, hypotheses,
  accusation, timeline reconstruction, hidden truth safety, and social/quest
  consequences.
- Travel / Survival System: route travel, fatigue, hunger, thirst, weather,
  camping, rest, forage, food/water use, and seeded risks.
- Stealth Expansion: hiding, sneaking, distraction, noise, decoys, shadowing,
  detection checks, suspicion, hidden observers, witness and combat
  consequences.
- Combat Expansion: weapon tags, stances, status effects, non-lethal attacks,
  flee risk, public-combat consequences, and hidden witness redaction.
- Social Manipulation System: persuade, threaten, bribe, deceive, provoke,
  comfort, blackmail, and extract information through relationship,
  emotional-state, reputation, known-fact, and leverage rules.
- Faction Mission System: faction mission availability, accept, complete,
  fail, rewards, reputation gates, quest integration, and hidden mission
  filtering.
- Domain / Base Management: base claiming, facility building, staff
  assignment, upgrades, storage, withdrawal, income, upkeep, and bounded domain
  tick behavior.

These systems are intentionally lightweight gameplay slices. They are not
full-scale simulations.

### Module Quality, Regression, Debugger, Import / Export

v1.6 adds:

- Gameplay Module Quality Gate
- Gameplay Module Regression Playtests
- Gameplay Module Debugger
- Gameplay Module Import / Export

The quality gate checks manifest validity, permissions, action validation,
state schema extensions, save compatibility, hidden leak risks, regression
metadata, forbidden paths, and executable-code rejection. It reports problems;
it does not automatically repair modules.

Regression playtests run deterministic scenarios with temporary state and
mock/fake/local-stub-style providers.

The debugger is local-only and gated by `ENABLE_DEBUG_API`. Dry-run does not
modify `GameState`.

Module import/export packages are local data packages. They do not execute
code.

## Behavior Changes

- The action system now has a unified registry for core actions and enabled
  module actions.
- Suggested actions may include module actions when their affordances are
  visible and the module action is enabled.
- Gameplay module state extensions are part of `GameState`, but remain subject
  to normal save/load, migration, StateDelta, and visibility rules.
- Hidden facts cannot be discovered through generic Action DSL fact-discovery
  effects unless they are already visible, public, or discoverable.
- Declarative action visible facts are filtered at runtime so hidden facts do
  not enter player-visible action results.
- LLM narration can describe module outcomes after the rule engine resolves
  them, but cannot decide those outcomes.

## API Changes

New or expanded local APIs include:

- `POST /authoring/action-mods/preview`
- `POST /authoring/action-mods/validate`
- `POST /authoring/action-mods/export`
- `POST /quality/modules/{module_id}/gate/run`
- `GET /debug/modules`
- `GET /debug/modules/{module_id}`
- `POST /debug/modules/{module_id}/actions/{action_id}/dry-run`
- `POST /modules/export`
- `POST /modules/import-dry-run`
- `POST /modules/import-apply`

Authoring routes are gated by `ENABLE_AUTHORING_API`. Debug routes are gated
by `ENABLE_DEBUG_API`. Quality routes use the local quality/eval gate.

## Frontend Changes

The Studio frontend now includes:

- Action Mod Editor for declarative local actions.
- Module Debugger panel under debug surfaces.
- Module package and quality-gate related API bindings.
- UI support for v1.6 schemas and StateDelta/action preview fields.
- Safe disabled-API states for authoring/debug routes.

The frontend does not provide an arbitrary code editor for Action Mods and
does not store API keys.

## Gameplay Module Changes

Gameplay modules are local declarative or trusted rule-code extensions. They:

- register through `ActionRegistry`
- return structured `ActionResult`
- generate `StateDelta`
- record `Event`
- obey `Visibility` and NPC Knowledge
- declare save compatibility
- run through validation and quality checks before package/import flows

They cannot:

- execute arbitrary code
- access network or local sensitive files
- read `.env` or API keys
- directly write `GameState`
- call the LLM to decide gameplay results
- bypass player-visible fact filtering

## Action Mod Changes

Action Mods are declarative by default. They define schemas for actions,
targets, preconditions, checks, outcomes, deltas, and visibility policy.

Important safety behavior:

- StateDelta templates are path-validated.
- Dangerous paths such as direct visibility/NPC knowledge mutation are
  rejected in module templates.
- `ADD_FACT_DISCOVERY` is guarded against hidden/unknown facts.
- Hidden outcomes must not be player-visible.
- Action Mod validation checks aliases, target specs, effects, event type,
  visibility policy, dangerous permissions, and save compatibility.

## Import / Export Changes

Gameplay Module packages include manifest data, action definitions, rule
configs, quality tests, example content, docs, and checksums.

Import dry-run validates:

- manifest schema
- action definitions
- permissions
- checksums
- save compatibility
- executable-file rejection
- zip slip / path traversal rejection
- module quality gate

Export rejects:

- API keys
- `.env`
- databases
- logs
- caches
- executable files
- secret-like content

Import apply requires explicit confirmation and does not automatically enable
untrusted modules.

## Testing / Quality Gate Changes

v1.6 adds tests for:

- module boundary policy
- manifest loader and dependency/conflict checks
- declarative action handler
- ActionRegistry module actions
- Action DSL preconditions/checks/effects
- Action Mod validation
- Action Mod authoring API
- magic, hacking, crafting, investigation, survival, stealth, combat, social
  manipulation, faction mission, and domain modules
- module quality gate
- module regression playtests
- module debugger
- module package import/export
- v1.6 integration boundaries

Final acceptance commands:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Observed acceptance result:

- `python -m pytest`: 1503 passed.
- `cd frontend && npm.cmd run build`: passed.
- Vite reported the existing chunk-size warning; this is not a release
  blocker.

## Known Limitations

- v1.6 is not a complete tactical combat system.
- v1.6 is not a complex MMO-style economy.
- v1.6 is not a large-scale war simulator.
- Module Quality Gate does not automatically repair modules.
- Module Quality Gate currently relies on some declared regression metadata;
  future releases should make gate-level regression execution stricter.
- Action alias conflicts are detected and surfaced, but registry registration
  does not hard-fail every conflict at insertion time.
- Module Debugger StateDelta previews are debug-gated, but future releases
  should add deeper recursive redaction for preview values and metadata.
- Action Mod Authoring UI allows local authors to type declarative paths; the
  backend remains the authority for validation and rejection.
- Frontend bundle size still triggers Vite's 500 kB chunk-size warning.

## Upgrade Notes From v1.5

- Existing worlds and saves should continue loading through optional/default
  v1.6 fields and the existing save migration model.
- New gameplay module state fields are optional. Existing content packs do not
  need to define magic, hacking, crafting, survival, domain, or other module
  data unless they want to use those systems.
- Module packages are local and must pass validation before import/apply.
- Action Mods should use declarative schemas and safe StateDelta paths.
- Existing Prompt Lab and provider settings are unchanged. v1.6 does not grant
  LLMs gameplay authority.
- If a world enables modules later, review module save compatibility and
  migration defaults before applying to active saves.

## Recommended v1.7 Direction

Recommended v1.7 priorities:

1. Harden Module Debugger redaction for StateDelta preview values and metadata.
2. Execute referenced module regression scenarios directly inside the quality
   gate or require verifiable regression artifacts.
3. Make alias conflicts mandatory blockers during package enablement.
4. Add a gameplay module dependency graph and save migration assistant.
5. Split player-facing action reasons from debug reasons.
6. Add frontend code-splitting for large Studio panels.
7. Expand cross-module regression scenarios, especially stealth + combat,
   hacking + faction missions, and investigation + social manipulation.

## Final Status

v1.6 is accepted for freeze.

Final release status: PASS.
