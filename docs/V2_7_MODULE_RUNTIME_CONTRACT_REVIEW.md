# v2.7 Module Runtime Contract Review

## Existing Module Contracts

- v2.6 provides `PackageManifestV2`, `ModulePermissionSet`, declarative Action Mods, `RuleModuleManifest`, Module Browser, compatibility checks, certification, quality gate, import/export hardening, and audit trail.
- Existing runtime rule slices include combat, magic, hacking, crafting, investigation, survival/travel, economy, faction/social rules, and world tick helpers.
- `ActionRegistry` supports core, module, and mod action metadata. Declarative actions resolve through local handlers and return `ActionResult` plus `StateDelta` proposals.
- `StateDelta` remains the write boundary for runtime state, and `EventLog` records state-affecting actions/ticks.

## Existing Runtime Behavior

- Rule handlers resolve deterministic or seeded-random outcomes in Python engine code already trusted by the app.
- v2.6 modules do not execute package-provided Python or JavaScript.
- Rule modules are manifest/contract declarations; they are not runtime code plugins.
- Provider Gateway remains the only model entry, and no module quality/certification pass-fail uses an LLM.

## Existing Permission Model

- `ModulePermissionSet` defaults to safe declarative permissions.
- Dangerous permissions such as `execute_code`, `access_filesystem`, `access_network`, `read_secrets`, `write_database`, `modify_game_state_directly`, `bypass_visibility`, and `call_llm` are blockers.
- Provider Profile Packs may contain only `api_key_env` or `secret_ref`, never raw keys.

## Existing Action Registration

- Core actions are registered by default.
- Module actions can be registered through `ActionRegistry.register_module_action`.
- Mod actions go through `ActionRegistry.register_mod_action`, which rejects core-action id conflicts and mod alias conflicts.
- v2.7 advanced module actions must continue to register through the registry or be exposed as deterministic module handlers that produce the same `ActionResult`/`StateDelta`/`Event` contract.

## Existing State Extension Support

- Before v2.7, several gameplay systems had top-level legacy fields such as `magic_resources`, `hackables`, `crafting_stations`, `evidence`, `survival`, and `travel_routes`.
- v2.7 introduces the controlled `state.modules.{module_id}` namespace for new advanced simulation state. Modules must declare a `ModuleStateExtension`; they may not add arbitrary root `GameState` fields.
- Module `StateDelta` paths must remain inside `modules.{module_id}` unless they are explicit engine-approved consequences such as inventory consumption, time passage, or public consequence flags.

## Existing Migration Support

- The save repository already stores migration history for saves/projects.
- v2.7 adds module migration planning with dry-run and explicit apply semantics.
- `remove_module_state` is destructive and remains blocked unless explicitly confirmed.

## Existing Quality Gate Support

- v2.6 Mod Quality Gate checks manifests, permissions, compatibility, secrets, executable payloads, action tests, hidden leaks, and import/export blockers.
- v2.7 adds an advanced module quality gate that aggregates state schema checks, migration plans, playtest reports, compatibility stress, EventLog coverage, save/load coverage, hidden leak checks, and dangerous permission blockers.

## Gaps Before Advanced Modules

- Legacy gameplay slices were not uniformly namespaced under module state.
- Economy/faction/cultivation needed deterministic MVP state/tick/action contracts.
- The frontend lacked a unified advanced module authoring dashboard.
- Module import/export needed v2.7-specific state schema and migration warnings.

## Security Risks

- Any future package-provided runtime code would need a separate sandbox design and remains out of scope.
- Hidden tactical actors, war intelligence, digital logs, route dangers, and cultivation techniques must not enter normal UI, prompts, exports, reports, or visible event summaries.
- Advanced modules must not make NPCs omniscient; visibility and known-fact filtering remain mandatory.
- LLMs must not decide outcomes for combat, economy, war, magic, hacking, crafting, deduction, survival, travel, or cultivation.

## Recommended v2.7 Runtime Contract

- Use `ModuleStateExtension` to declare `state.modules.{module_id}` fields and defaults.
- Use `ModuleMigrationService` for dry-run/apply migration, append migration history, and preserve state when modules are disabled.
- Use `ActionRegistry` for module actions where actions are exposed to the player/action parser.
- Resolve all module outcomes through deterministic rules or seeded randomness.
- Emit `StateDelta` proposals for every state change and `Event` records for every state-affecting module action/tick.
- Keep normal summaries secret-free and hidden-filtered.
- Run module playtests, compatibility stress, quality gate, and import/export checks before release.
