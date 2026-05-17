# v0.6 Research Plan

## Purpose

v0.6 is a research and prioritization phase for moving the project from a local world-making platform into a more polished, testable, distributable, and author-friendly local application.

The core architecture remains unchanged:

- The world engine is the source of truth.
- The LLM is the language layer, not the world judge.
- `GameState` cannot be directly mutated by LLM output.
- Runtime state changes must go through `StateDelta`.
- Player actions, system ticks, and planning/playtesting ticks must be recorded as `Event`.
- Hidden facts, NPC secrets, hidden witnesses, debug data, and hidden/debug memory must not enter player-facing APIs or narrator prompts.
- Authoring and debug tools remain local-only unless a future version designs a stronger security boundary.

This document is a research roadmap, not an implementation plan. It does not change code or current architecture.

## Current v0.5 Baseline

v0.5 provides:

- content authoring API and frontend
- structured content validation UX
- local memory and `MemoryContextBuilder`
- advanced NPC goals and planning tick
- relationship graph
- faction conflict
- economy/trade
- procedural side quest drafts
- automated boundary evals
- content-only plugin/mod packaging
- multi-world save browser

These modules give v0.6 a strong base for improving usability, test depth, distribution, and long-term maintainability.

## Evaluation Summary

| Direction | Value | Risk | Recommended For v0.6 |
| --- | --- | --- | --- |
| Packaged desktop app | High usability | Medium packaging/config risk | Yes, after API stability check |
| Richer content authoring UI | Very high creator value | Medium UI/schema complexity | Yes, core theme |
| Visual relationship/faction graph | High debugging/authoring value | Medium visibility risk | Yes, core theme |
| Advanced combat expansion | Medium gameplay value | Medium-high rules complexity | Limited research or small slice |
| Automated playtesting agents | Very high quality value | High determinism/boundary risk | Yes, but rule/mock first |
| Narrative quality evals | High quality value | Medium subjectivity risk | Yes, deterministic first |
| Local model provider support | High local-first value | Medium dependency/runtime risk | Research/prototype only |
| Advanced mod versioning | Medium author value | Medium compatibility risk | Yes, minimal schema/tooling |
| Save migration system | Very high maintenance value | Medium data integrity risk | Yes, core infrastructure |
| Performance profiling and optimization | High reliability value | Low-medium risk | Yes, cross-cutting |

## 1. Packaged Desktop App

### Functional Value

High. A packaged app would make the local engine easier to run without juggling backend, frontend, environment variables, and browser tabs. It improves personal usability and future testing of local authoring workflows.

### Technical Risk

Medium.

- Packaging Python backend plus React frontend can be brittle.
- SQLite database location, worlds/mods paths, logs, and `.env` equivalents must be explicit.
- Desktop shell choices such as Tauri, Electron, or a minimal launcher affect build complexity.
- Packaging must not accidentally expose API keys in frontend assets.

### Architecture Impact

Should be mostly outer-shell impact. The FastAPI backend, React frontend, `WorldLoader`, repository layer, and provider factory should remain unchanged.

Recommended architecture:

- keep backend as local process
- keep frontend as bundled web UI
- add a launcher/config layer
- keep all provider credentials in local environment/config storage outside bundled source

### v0.5 Dependencies

- FastAPI game/authoring/debug APIs
- React frontend
- `.env.example` and settings model
- SQLite save/load
- authoring/debug gating
- multi-world save browser

### New Data Structures

- `DesktopAppConfig`
  - `data_dir`
  - `worlds_dir`
  - `mods_dir`
  - `database_url`
  - `backend_host`
  - `backend_port`
  - `llm_provider`
  - `debug_enabled`
  - `authoring_enabled`
- `LocalPathConfig`
  - `config_dir`
  - `saves_dir`
  - `logs_dir`
  - `cache_dir`

### StateDelta Paths

None. Packaging must not affect runtime world state.

### Event Types

No game `Event` required.

Optional local app audit events outside game `EventLog`:

- `desktop_app_started`
- `backend_process_started`
- `config_loaded`

These must never enter player timelines.

### APIs

No new player API required.

Optional local-only health/config endpoints:

- `GET /app/health`
- `GET /app/local-config-summary`

The config summary must redact secrets and local sensitive paths unless explicitly debug-only.

### Frontend UI

- first-run setup screen
- local data directory status
- backend connection status
- provider configuration guidance without storing API keys in frontend
- open worlds/mods folder buttons if the desktop shell supports it

### Tests

- packaged build smoke test
- backend starts from packaged environment
- frontend can reach local backend
- no `LLM_API_KEY` or `sk-...` string in bundled frontend assets
- SQLite path is outside source tree by default
- authoring/debug gates still work

### Hidden Facts Leakage Risk

Low for player APIs, medium for app-level logs.

Packaged logs must not capture raw debug timelines, hidden content, or authoring YAML unless explicitly local-debug and user-visible.

### LLM Boundary Impact

Low if packaging only launches existing provider factory. High if desktop UI starts storing provider keys. v0.6 should not put provider secrets into frontend state or bundled config.

### Recommendation

Enter v0.6 as a prototype after save migration and config path design. Keep it local-only and avoid auto-updaters, installers, or cloud sync in v0.6.

## 2. Richer Content Authoring UI

### Functional Value

Very high. v0.5 authoring is textarea-based. Structured forms for locations, NPCs, items, facts, quests, factions, relationships, rumors, and mods would make world creation safer and less YAML-error-prone.

### Technical Risk

Medium.

- The UI must stay schema-driven and not duplicate backend validation logic.
- Editing hidden content must remain authoring-only.
- Complex forms can drift from YAML schemas.

### Architecture Impact

Moderate frontend expansion, limited backend impact if APIs stay file/validation based.

Preferred approach:

- add schema metadata endpoints or static frontend field descriptors
- keep backend validation authoritative
- keep authoring writes through existing authoring API
- avoid direct frontend filesystem access

### v0.5 Dependencies

- authoring API
- structured validation report
- content schemas in `WorldLoader`
- mod validation
- frontend authoring mode

### New Data Structures

- `AuthoringSchemaDescriptor`
  - `file_name`
  - `entity_type`
  - `fields`
  - `references`
  - `required_fields`
  - `enum_values`
- `AuthoringEntityDraft`
  - `file_name`
  - `entity_id`
  - `data`
  - `validation_status`
- `ReferenceOption`
  - `id`
  - `label`
  - `kind`
  - `visible_to_author`

### StateDelta Paths

None. Authoring edits content files, not active `GameState`.

### Event Types

No game events.

Optional authoring audit entries outside `EventLog`:

- `authoring_entity_created`
- `authoring_entity_updated`
- `authoring_validation_run`

### APIs

- `GET /authoring/worlds/{world_id}/schema`
- `GET /authoring/worlds/{world_id}/references`
- `POST /authoring/worlds/{world_id}/entities/{file_name}`
- `PUT /authoring/worlds/{world_id}/entities/{file_name}/{entity_id}`
- `POST /authoring/worlds/{world_id}/preview`

All routes must stay gated by `ENABLE_AUTHORING_API`.

### Frontend UI

- structured forms per YAML file
- reference pickers
- validation badges per field
- safe hidden-content labels in authoring mode
- quest trigger editor
- NPC goal editor
- relationship editor
- mod manifest editor

### Tests

- schema descriptor shape tests
- field form serialization round trip
- invalid references surface validation issues
- authoring disabled state
- hidden content appears only in authoring mode, not play mode
- frontend build and TypeScript coverage

### Hidden Facts Leakage Risk

Medium. Authoring UI intentionally displays hidden content. The main risk is accidental mixing into play UI or save summaries.

### LLM Boundary Impact

Low if no LLM authoring assistant is included. If future LLM assistance is added, it must produce drafts only and pass validation.

### Recommendation

Enter v0.6 as a core theme.

## 3. Visual Relationship / Faction Graph

### Functional Value

High. A graph view would make NPC relationships, faction conflict, rumor paths, and social consequences understandable. It is especially useful for debugging hidden leaks and authoring social worlds.

### Technical Risk

Medium.

- Graphs can reveal hidden relationships/factions if reused in player UI.
- Large graphs can degrade frontend performance.
- Adding a visualization library may increase build size.

### Architecture Impact

Mostly frontend and debug/authoring API expansion. Player-visible graph must use filtered data only.

### v0.5 Dependencies

- relationship graph
- faction conflict layer
- reputation/factions
- rumors/crimes/witnesses
- frontend social/debug panels
- debug API gating

### New Data Structures

- `GraphNode`
  - `id`
  - `kind: npc | faction | location | rumor | crime | quest`
  - `label`
  - `visibility: player_visible | authoring | debug`
- `GraphEdge`
  - `source_id`
  - `target_id`
  - `kind`
  - `weight`
  - `label`
  - `visibility`
- `SocialGraphResponse`
  - `nodes`
  - `edges`
  - `scope`

### StateDelta Paths

None for graph visualization. Existing relationship/faction paths remain authoritative:

- `relationships.{id}.*`
- `factions.{id}.relationships_to_other_factions.*`
- `factions.{id}.alert_level`
- `factions.{id}.conflict_level`

### Event Types

No new runtime events for viewing.

Existing events to visualize:

- `relationship_changed`
- `faction_conflict_changed`
- `rumor_propagated`
- `crime_reported`
- `npc_planning_tick`

### APIs

- `GET /game/state/{session_id}` continues to serve player-visible summaries.
- `GET /debug/sessions/{session_id}/social-graph`
- `GET /authoring/worlds/{world_id}/social-graph`

Debug/authoring graph endpoints must be gated.

### Frontend UI

- social graph panel
- faction relation view
- filters by NPC/faction/rumor/crime
- player-safe graph mode
- debug/authoring graph mode with clear local-only labeling

### Tests

- hidden relationships absent from player graph
- hidden factions absent from player graph
- debug graph disabled when debug API disabled
- authoring graph disabled when authoring API disabled
- large graph render smoke test
- frontend build

### Hidden Facts Leakage Risk

High if graphs are not scoped by audience. Graph APIs must require explicit audience/scope and reuse existing visibility filters.

### LLM Boundary Impact

Low. Graph layout and filtering are deterministic. The LLM must not infer relationships or faction conflicts into state.

### Recommendation

Enter v0.6 as a core authoring/debug feature, with strict player/debug separation.

## 4. Advanced Combat Expansion

### Functional Value

Medium. Combat is useful for RPG depth, but the project is primarily a narrative world engine. Expanding combat too far can pull focus away from authoring, testing, and world reliability.

### Technical Risk

Medium-high.

- More combat state increases save/replay complexity.
- Injuries, equipment, initiative, and AI actions can conflict with NPC planning.
- Combat outcomes can trigger crimes, witnesses, rumors, reputation, quests, and death state.

### Architecture Impact

Moderate to high. Combat rules touch action dispatch, life state, inventory, crime, world tick, NPC planning, visible state, and narrator inputs.

### v0.5 Dependencies

- combat core
- life state
- inventory/economy
- crime/witness
- NPC reactions
- NPC planning
- event log

### New Data Structures

- `CombatRoundState`
  - `combat_id`
  - `round_number`
  - `active_actor_id`
  - `turn_order`
- `CombatManeuver`
  - `id`
  - `name`
  - `stamina_cost`
  - `damage_profile`
  - `allowed_weapon_tags`
- `InjuryState`
  - `id`
  - `actor_id`
  - `severity`
  - `effect_tags`
  - `created_turn`

### StateDelta Paths

- `combats.{combat_id}.round_number`
- `combats.{combat_id}.turn_order`
- `combats.{combat_id}.active_actor_id`
- `combats.{combat_id}.combatants.{actor_id}.stance`
- `actors.{actor_id}.injuries.{injury_id}`
- `npcs.{npc_id}.condition`
- `player.condition`

### Event Types

- `combat_round_started`
- `combat_maneuver_used`
- `injury_inflicted`
- `combatant_retreated`
- `combat_ended`

### APIs

- extend `POST /game/input` through parsed intents/actions
- optional `GET /game/combat/{session_id}` for player-visible combat summary
- debug endpoint for raw combat state

### Frontend UI

- active combat summary
- available combat actions
- visible combatants and conditions
- debug combat timeline

### Tests

- deterministic initiative
- damage/injury deltas
- dead/incapacitated restrictions
- crime/witness integration
- save/load/replay combat state
- hidden combatant filtering

### Hidden Facts Leakage Risk

Medium-high. Hidden observers, hidden attackers, traps, or unseen combatants must not be exposed in player summaries or narration.

### LLM Boundary Impact

Medium. Narrator can render combat, but must not decide hit/miss, damage, morale, injury, death, or enemy actions.

### Recommendation

Do not make this the main v0.6 theme. Consider one small research slice: player-visible combat summary and deterministic round state only.

## 5. Automated Playtesting Agents

### Functional Value

Very high. Automated playtesting can stress content packs, save/load, visibility, quest triggers, NPC planning, economy, and combat without manual clicking.

### Technical Risk

High.

- LLM-driven agents could accidentally become world judges if not constrained.
- Random exploration can create flaky tests.
- Full game loops can be slow.

### Architecture Impact

Moderate. Add a test harness around existing APIs and `GameLoop`; avoid changing runtime rules.

### v0.5 Dependencies

- authoring validation
- multi-world save browser
- event log
- boundary evals
- mock provider
- scenario-style integration tests
- MemoryContextBuilder

### New Data Structures

- `PlaytestScenario`
  - `id`
  - `world_id`
  - `initial_actions`
  - `agent_policy`
  - `max_turns`
  - `assertions`
- `PlaytestStep`
  - `turn`
  - `input_text`
  - `expected_visible_contains`
  - `forbidden_visible_contains`
- `PlaytestReport`
  - `scenario_id`
  - `passed`
  - `events_checked`
  - `violations`
  - `final_turn`

### StateDelta Paths

None for harness itself. It verifies existing deltas.

### Event Types

Optional debug/test-only events outside player game logs:

- `playtest_started`
- `playtest_step_executed`
- `playtest_failed`

Game runtime should still record normal player/system events.

### APIs

Prefer CLI/test runner first:

- `python -m backend.app.tools.run_playtest scenario_id`

Optional local debug API later:

- `POST /debug/playtests`
- `GET /debug/playtests/{run_id}`

### Frontend UI

Optional debug-only panel:

- scenario list
- run report
- failed assertion details
- event timeline link

### Tests

- deterministic scripted scenario
- hidden fact forbidden-string assertions
- save/load mid-scenario
- mock provider only
- no real LLM calls
- replay/final-state consistency check

### Hidden Facts Leakage Risk

Medium. Playtest reports may include hidden strings in forbidden assertions. Reports must be debug/test-only.

### LLM Boundary Impact

High if LLM agents are introduced. v0.6 should start with scripted or rule-based agents. If LLM-assisted playtesting is researched, it must only propose player input text and must never modify state or assert facts.

### Recommendation

Enter v0.6 as a core quality theme, but begin with deterministic scripted agents and mock provider only.

## 6. Narrative Quality Evals

### Functional Value

High. Boundary evals prevent leaks; quality evals can catch repetition, tone drift, missing consequences, broken Chinese output, and narrative contradictions.

### Technical Risk

Medium.

- Quality is subjective.
- LLM-as-judge would add cost and instability.
- Golden text tests can be brittle.

### Architecture Impact

Low to moderate. Add eval fixtures and scoring tools without changing runtime.

### v0.5 Dependencies

- automated boundary evals
- Narrator
- MemoryContextBuilder
- mock provider
- event logs
- scenario integration tests

### New Data Structures

- `NarrativeEvalCase`
  - `id`
  - `world_id`
  - `turn_context`
  - `expected_quality_rules`
  - `forbidden_patterns`
- `NarrativeEvalResult`
  - `case_id`
  - `passed`
  - `scores`
  - `violations`
- `NarrativeQualityRule`
  - `code`
  - `description`
  - `severity`

### StateDelta Paths

None.

### Event Types

None for runtime. Optional test report entries only.

### APIs

Prefer CLI/tests:

- `python -m pytest backend/tests/evals`
- optional `python -m backend.app.tools.run_narrative_evals`

### Frontend UI

Optional debug/authoring report:

- eval list
- pass/fail
- forbidden string hits
- prompt snapshot preview with redactions

### Tests

- no hidden facts
- no raw deltas
- Chinese output required where narrator is used
- action result consistency
- short summary present
- suggested actions schema valid
- deterministic fake provider snapshots

### Hidden Facts Leakage Risk

Medium. Eval snapshots can contain hidden fixtures. Store them only in test/debug paths and never expose through player APIs.

### LLM Boundary Impact

Low for deterministic checks. Medium if LLM-as-judge is added; v0.6 should avoid real LLM judges.

### Recommendation

Enter v0.6 as a core quality theme using deterministic and snapshot-based evals.

## 7. Local Model Provider Support

### Functional Value

High for local self-use. Supporting local model runtimes would reduce dependence on remote APIs and better match the project’s local-first philosophy.

### Technical Risk

Medium.

- Local runtimes differ in API shape, JSON reliability, tool support, streaming, and model quality.
- Structured JSON validation may fail more often.
- Installation burden can be high.

### Architecture Impact

Moderate but contained if added through provider factory.

### v0.5 Dependencies

- `LLMProvider`
- provider factory
- schema validation
- fake/mock provider tests
- prompt boundary tests
- `.env.example` settings

### New Data Structures

- `LocalModelProviderConfig`
  - `base_url`
  - `model`
  - `timeout_seconds`
  - `json_mode_strategy`
  - `max_retries`
- `ProviderCapability`
  - `supports_json`
  - `supports_streaming`
  - `supports_embeddings`

### StateDelta Paths

None. Provider selection must not alter world state.

### Event Types

None. Optional local diagnostics outside game `EventLog`:

- `provider_health_check_failed`
- `provider_schema_retry`

### APIs

- extend config/env with `LLM_PROVIDER=local`
- optional local debug endpoint:
  - `GET /debug/provider`

Must redact secrets and avoid returning prompt payloads.

### Frontend UI

- local provider status in settings/debug panel
- no API key entry in frontend unless a future secure local config design exists

### Tests

- factory returns local provider when configured
- no real local server required in tests
- schema failure is clear
- timeout/retry behavior
- fake local provider for tests
- no provider output can mutate `GameState`

### Hidden Facts Leakage Risk

Low to medium. Local model prompts still contain visible/narrator-safe context only. If logs capture prompts, hidden data risks increase.

### LLM Boundary Impact

Medium. More providers mean more failure modes, but not more authority if `LLMProvider` boundary is preserved.

### Recommendation

Research/prototype in v0.6, not required for acceptance unless scoped tightly.

## 8. Advanced Mod Versioning

### Functional Value

Medium. Useful for long-term content reuse and save compatibility, especially as content packs and mods evolve.

### Technical Risk

Medium.

- Version resolution can become complex.
- Mod load order affects ids, references, and save compatibility.
- Incompatible content changes can break saves.

### Architecture Impact

Moderate. It touches mod loader, world loader, validation, save metadata, and migration planning.

### v0.5 Dependencies

- content-only mod packaging
- world validation
- multi-world saves
- save repository
- content pack manifest

### New Data Structures

- `ModVersionConstraint`
  - `mod_id`
  - `min_version`
  - `max_version`
- `ResolvedModSet`
  - `mods`
  - `load_order`
  - `content_hash`
  - `validation_report`
- `SaveContentSignature`
  - `world_id`
  - `world_version`
  - `mod_ids`
  - `content_hash`

### StateDelta Paths

None for loading/validation. Runtime effects still use normal rules and deltas.

### Event Types

No game events.

Optional save metadata/audit:

- `mod_set_validated`
- `save_content_mismatch_detected`

### APIs

- `GET /authoring/mods`
- `POST /authoring/mods/resolve`
- `POST /authoring/worlds/{world_id}/validate-with-mods`
- `GET /game/saves/{save_id}/content-signature`

### Frontend UI

- mod list
- dependency/conflict warnings
- load order preview
- save compatibility indicator

### Tests

- version constraint parsing
- dependency/conflict resolution
- duplicate ids
- content hash stability
- save detects incompatible mod set
- path traversal still rejected
- no code execution

### Hidden Facts Leakage Risk

Medium in authoring/debug UI, low in player UI. Mod metadata can reveal hidden content names if surfaced to players.

### LLM Boundary Impact

Low. Versioning is deterministic tooling.

### Recommendation

Enter v0.6 as a minimal compatibility layer, paired with save migration.

## 9. Save Migration System

### Functional Value

Very high. As schemas evolve, v0.6 needs a safe way to load old saves, inspect migration status, and apply explicit migration steps.

### Technical Risk

Medium.

- Bad migrations can corrupt saves.
- Migration must not invent canonical facts.
- Need backup/rollback.

### Architecture Impact

High but infrastructural. It touches repository, `GameState` parsing, content signatures, save APIs, and tests.

### v0.5 Dependencies

- SQLite save/load
- Pydantic defaults
- world/content version metadata
- multi-world save browser
- mod versioning
- EventLog replay expectations

### New Data Structures

- `SaveSchemaVersion`
  - `engine_version`
  - `state_schema_version`
  - `content_signature`
- `MigrationStep`
  - `id`
  - `from_version`
  - `to_version`
  - `description`
  - `dry_run_supported`
- `MigrationReport`
  - `save_id`
  - `required_steps`
  - `warnings`
  - `backup_save_id`
  - `success`

### StateDelta Paths

Migrations may alter serialized save state, but should not be normal gameplay deltas.

If migrations affect runtime state after load, prefer explicit migration records:

- `metadata.schema_version`
- `metadata.migration_history`
- `metadata.content_signature`

Avoid gameplay-looking deltas unless replay semantics are designed.

### Event Types

Do not use normal player `EventLog` for save migration by default.

Optional system/audit metadata:

- `save_migration_started`
- `save_migration_completed`
- `save_migration_failed`

These should live in save metadata or a migration audit table, not player narrative events.

### APIs

- `GET /game/saves/{save_id}/migration-status`
- `POST /game/saves/{save_id}/migrate`
- `POST /game/saves/{save_id}/migrate-dry-run`

### Frontend UI

- save browser migration badge
- dry-run report
- backup confirmation
- migration result details

### Tests

- v0.3/v0.4/v0.5 save fixtures load
- missing fields default safely
- migration dry run does not alter save
- migration creates backup
- failed migration leaves original intact
- post-migration save can continue play
- hidden facts remain hidden after migration

### Hidden Facts Leakage Risk

Medium. Migration reports may mention hidden ids or content differences. Player UI should show only generic compatibility status; details are debug/authoring-only.

### LLM Boundary Impact

Low. Migrations must be deterministic code. LLM must not generate or apply migration state changes.

### Recommendation

Enter v0.6 as a core infrastructure theme.

## 10. Performance Profiling and Optimization

### Functional Value

High. The project now has many rule systems, validation passes, memory searches, and frontend panels. Profiling will prevent slow ticks and sluggish authoring as worlds grow.

### Technical Risk

Low-medium.

- Premature optimization can obscure code.
- Profiling data can include local paths or hidden content if logged carelessly.

### Architecture Impact

Low if implemented as instrumentation and tests. Avoid changing rule semantics.

### v0.5 Dependencies

- world tick
- NPC planning
- validation
- memory store
- mod loader
- frontend graph/debug panels
- integration tests

### New Data Structures

- `PerformanceMetric`
  - `name`
  - `duration_ms`
  - `count`
  - `scope`
  - `created_at`
- `ProfilingReport`
  - `scenario_id`
  - `metrics`
  - `slow_steps`
  - `recommendations`

### StateDelta Paths

None. Profiling must not affect `GameState`.

### Event Types

No game events.

Optional debug-only metrics:

- `profile_sample_recorded`
- `slow_tick_detected`

### APIs

- `GET /debug/performance`
- `POST /debug/performance/run-scenario`

Debug-only and gated.

### Frontend UI

- debug performance panel
- validation timing
- world tick timing
- memory search timing
- frontend render warning badges

### Tests

- profiling disabled by default unless debug mode
- deterministic benchmark scenario
- no hidden data in performance report
- no state changes from profiling
- performance budgets for validation and world tick on sample world

### Hidden Facts Leakage Risk

Low if reports contain metric names only. Medium if reports include raw slow event payloads or content ids.

### LLM Boundary Impact

Low. Profiling should not call LLM.

### Recommendation

Enter v0.6 as cross-cutting work, especially around validation, world tick, memory search, and frontend graph rendering.

## Recommended v0.6 Development Theme

Recommended theme:

**Local Studio Hardening: Better Authoring, Safer Migration, Stronger Evaluation, and Visual Debugging**

This theme fits the current maturity of the project better than jumping into larger gameplay simulation. v0.5 already added many world systems; v0.6 should make them easier to inspect, validate, migrate, package, and test.

Recommended core scope:

1. Save migration system.
2. Richer content authoring UI.
3. Visual relationship/faction graph.
4. Automated playtesting agents.
5. Narrative quality evals.
6. Performance profiling.
7. Advanced mod versioning.
8. Packaged desktop app prototype.

Recommended research/prototype-only scope:

- local model provider support
- advanced combat expansion

## Recommended Development Order

1. Define version metadata and save migration design.
2. Implement migration dry-run/reporting for existing v0.3-v0.5 save shapes.
3. Add content/schema descriptors for richer authoring UI.
4. Build structured authoring forms for high-value entities: locations, NPCs, facts, quests, relationships.
5. Add visual relationship/faction graph in authoring/debug mode.
6. Add deterministic automated playtesting scenario runner.
7. Expand narrative quality evals and golden prompt/input snapshots.
8. Add performance profiling for validation, world tick, memory search, and frontend graph rendering.
9. Add advanced mod versioning: constraints, content signatures, save compatibility checks.
10. Prototype packaged desktop app with local backend/frontend process management.
11. Research local provider support behind `LLMProvider`.
12. Research one small advanced combat slice only if previous work is stable.

## What v0.6 Should Not Do

v0.6 should not:

- turn the LLM into a world judge
- let LLM output directly modify `GameState`
- let authoring tools mutate active saves without validation
- execute arbitrary mod/plugin code
- add cloud sync, user accounts, multiplayer, or hosted auth
- build a full tactical combat system
- build large-scale faction war simulation
- introduce a required external vector database
- rely on real LLM calls for tests or evals
- expose debug timelines, hidden facts, hidden relationships, hidden witnesses, or hidden memory in player APIs
- package provider API keys into frontend or desktop bundles
- optimize by bypassing `StateDelta`, `EventLog`, visibility, or schema validation

## v0.6 Acceptance Standards

v0.6 should be accepted only if:

1. Backend tests pass with no real API calls.
2. Frontend build passes.
3. Save migration can dry-run and migrate supported old save fixtures with backups.
4. Migration reports do not expose hidden content through player APIs.
5. Authoring UI supports structured editing for key content types and still writes through backend authoring APIs.
6. Authoring validation remains backend-authoritative.
7. Relationship/faction graph has distinct player-safe and debug/authoring scopes.
8. Automated playtesting runs deterministic scenarios with mock providers.
9. Narrative quality evals run locally and do not require external LLM judges.
10. Performance profiling produces debug-only reports without changing state.
11. Mod versioning detects dependency/conflict/content-signature issues.
12. Packaged desktop prototype, if included, does not bundle secrets and can start backend/frontend locally.
13. All runtime state changes still go through `StateDelta`.
14. All player actions, system ticks, NPC planning ticks, and playtesting-driven game inputs are recorded as events.
15. Hidden facts, NPC secrets, hidden witnesses, debug data, and hidden/debug memory remain filtered.
16. Provider selection still goes through `LLMProvider`/provider factory.
17. v0.6 LLM boundary, visibility, security, and acceptance reports find no release blocker.

## v0.7 Candidate Directions

Possible v0.7 themes after v0.6 hardening:

- Full schema-aware content studio with quest graph editor.
- More complete packaged desktop distribution and installer.
- Optional local model provider integration if v0.6 prototype is stable.
- Richer combat, equipment, and injury systems.
- Expanded economy and trade simulation.
- Scenario simulation runner for large regression playthroughs.
- LLM-assisted authoring assistant with strict draft/review/export boundaries.
- Mod load-order UI and composed-world previews.
- Save import/export and world pack publishing tools for local sharing.
- Relationship/faction visualization with time-series history.
- More robust local semantic memory backend.
- Golden transcript narrative regression suite.

## Final Recommendation

v0.6 should prioritize infrastructure and creator experience over adding large new simulation systems. The safest and highest-leverage path is:

1. save migration,
2. structured authoring,
3. visual social debugging,
4. automated playtesting/evals,
5. performance profiling,
6. mod versioning,
7. packaging prototype.

This keeps the project moving toward a sustainable local world-building platform while preserving the core contract: the world engine is the fact source, and the LLM remains a bounded language layer.
