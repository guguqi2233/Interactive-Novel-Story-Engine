# v0.6 Roadmap

## Theme

Local Studio Hardening: Better Authoring, Safer Migration, Stronger Evaluation, and Visual Debugging

## Goal

v0.6 hardens the v0.5 local world-making platform into a more maintainable local studio. The release should make content safer to edit, saves safer to evolve, social systems easier to inspect, regressions easier to catch, and the local app easier to run.

v0.6 is not a new authority model. The world engine remains the fact source. The LLM remains a bounded language layer for parsing, narration, summarization, and draft assistance only.

Core invariants:

- LLM does not directly modify `GameState`.
- All runtime state changes go through `StateDelta`.
- Player actions, system ticks, NPC planning ticks, and playtesting-agent game inputs are recorded as `Event`.
- Hidden facts do not enter `visible_state`.
- NPCs cannot know or act on unknown facts.
- Memory is not an authoritative fact source.
- Authoring/debug APIs are local-only and gated.
- Mods are content-only and never execute arbitrary code.
- Save migration must be testable, auditable, and reversible through backup or dry-run validation.
- Performance optimization must not bypass correctness, visibility, schema validation, `StateDelta`, or `EventLog`.

## Explicitly Not In v0.6

v0.6 will not include:

- LLM world-judge behavior.
- LLM-generated canonical `StateDelta` application.
- Arbitrary mod/plugin code execution.
- Cloud sync, accounts, hosted auth, multiplayer, or multi-user collaboration.
- Full tactical/grid combat.
- Large-scale war simulation.
- Large-scale dynamic economy simulation.
- Required external vector database or hosted LLM judge.
- Production security hardening for public deployment.
- Frontend direct filesystem access.
- Performance shortcuts that bypass `StateDelta`, `EventLog`, visibility filters, content validation, or schema checks.

## Recommended Development Order

1. Save migration foundation and version metadata.
2. Migration dry-run/reporting and backup workflow.
3. Authoring schema descriptors and reference metadata API.
4. Richer structured authoring UI for core content types.
5. Visual relationship/faction graph for authoring/debug and player-safe scopes.
6. Deterministic automated playtesting agents and scenario runner.
7. Narrative quality evals and safe prompt/input snapshots.
8. Performance profiling for validation, world tick, memory search, and frontend render hotspots.
9. Advanced mod versioning and save content signatures.
10. Desktop packaging prototype with local process/config management.
11. Local model provider support research slice.
12. Advanced combat expansion research slice.
13. v0.6 integration regression tests, audits, acceptance report, and release notes.

## Module 1: Save Migration System

### Goal

Introduce explicit save schema/version metadata, dry-run migration reporting, backup/rollback safety, and fixture-based migration tests for v0.3-v0.5 style saves.

### Data Structures

- `SaveSchemaVersion`
  - `engine_version: str`
  - `state_schema_version: str`
  - `content_signature: str | None`
  - `created_with_world_id: str`
  - `created_with_mod_ids: list[str]`
- `MigrationStep`
  - `id: str`
  - `from_version: str`
  - `to_version: str`
  - `description: str`
  - `dry_run_supported: bool`
  - `requires_backup: bool`
- `MigrationReport`
  - `save_id: str`
  - `current_version: str`
  - `target_version: str`
  - `required_steps: list[str]`
  - `warnings: list[str]`
  - `errors: list[str]`
  - `backup_save_id: str | None`
  - `success: bool`
- `SaveMigrationHistoryEntry`
  - `step_id: str`
  - `from_version: str`
  - `to_version: str`
  - `applied_at: str`

### API Changes

- `GET /game/saves/{save_id}/migration-status`
- `POST /game/saves/{save_id}/migrate-dry-run`
- `POST /game/saves/{save_id}/migrate`

Responses must avoid hidden state details in player-facing contexts. Detailed migration reports are local/debug or save-management surfaces.

### Frontend Changes

- Save browser migration badge.
- Migration status panel.
- Dry-run report display.
- Backup confirmation before applying migrations.
- Clear failure state if migration cannot proceed.

### Tests

- v0.3, v0.4, and v0.5 fixture saves load or report migration needs.
- Dry-run does not mutate saves.
- Migration creates a backup before mutating.
- Failed migration leaves original save intact.
- Migrated save can be loaded and continued.
- Hidden facts, NPC secrets, hidden witnesses, hidden memory, and hidden relationships remain filtered after migration.
- Migration report does not enter narrator context.

### Acceptance Standard

A user can inspect an old save, run a dry-run migration, apply migration with backup, load the migrated save, and continue play without losing turn/event consistency.

### Save/Load Impact

High. Repository and save metadata must persist schema version, content signature, and migration history. Existing save/load behavior must remain compatible.

### Content Pack / Mod Version Impact

Migration should read world version and mod content signatures when available. It must not silently load an incompatible mod set as if it were safe.

### LLM Boundary Impact

None. Migrations are deterministic code. LLM must not produce migration steps or apply migration state.

### Visibility Risk

Medium. Migration reports may mention hidden ids or content mismatches. Player UI should show generic compatibility status; detailed reports remain local/debug.

## Module 2: Richer Authoring UI

### Goal

Move beyond raw YAML textarea editing by adding structured forms, reference pickers, validation badges, and safe entity editing for common content pack files.

### Data Structures

- `AuthoringSchemaDescriptor`
  - `file_name: str`
  - `entity_type: str`
  - `fields: list[AuthoringFieldDescriptor]`
  - `required_fields: list[str]`
  - `reference_fields: list[str]`
  - `enum_values: dict[str, list[str]]`
- `AuthoringFieldDescriptor`
  - `name: str`
  - `field_type: str`
  - `required: bool`
  - `description: str`
  - `reference_kind: str | None`
- `AuthoringEntityDraft`
  - `file_name: str`
  - `entity_id: str`
  - `data: dict`
  - `validation_status: str`
- `ReferenceOption`
  - `id: str`
  - `label: str`
  - `kind: str`
  - `visibility: str`

### API Changes

- `GET /authoring/worlds/{world_id}/schema`
- `GET /authoring/worlds/{world_id}/references`
- `GET /authoring/worlds/{world_id}/entities/{file_name}`
- `POST /authoring/worlds/{world_id}/entities/{file_name}`
- `PUT /authoring/worlds/{world_id}/entities/{file_name}/{entity_id}`
- `POST /authoring/worlds/{world_id}/preview`

All routes stay behind `ENABLE_AUTHORING_API`. Backend validation remains authoritative.

### Frontend Changes

- Entity list and structured editor.
- Forms for locations, NPCs, items, facts, quests, factions, rumors, relationships, and mod manifests.
- Reference picker for ids.
- Field-level validation messages.
- Toggle between structured form and raw YAML view.
- Strong local-authoring visual label.

### Tests

- Schema descriptor response shape.
- Entity form serialization round trip to YAML.
- Invalid references produce structured validation issues.
- Authoring API disabled state.
- Hidden content appears only in authoring mode.
- Player mode does not render authoring content.
- Frontend TypeScript/build checks.

### Acceptance Standard

A local author can edit key entity types through forms, validate changes, and save through the authoring API without bypassing backend validation.

### Save/Load Impact

None for active saves. Authoring edits content packs only and must not mutate active `GameState`.

### Content Pack / Mod Version Impact

Moderate. Structured forms should reflect current content schemas and mod manifest fields. Schema descriptors should help prevent docs/UI drift.

### LLM Boundary Impact

Low. No LLM is required. Any future LLM authoring assistant remains draft-only and validation-gated.

### Visibility Risk

Medium. Authoring mode displays hidden content by design. It must stay visually and technically separate from play mode.

## Module 3: Visual Relationship / Faction Graph

### Goal

Provide player-safe, authoring, and debug graph views for NPC relationships, faction relations, faction conflict, rumors, crimes, and social consequences.

### Data Structures

- `GraphNode`
  - `id: str`
  - `kind: npc | faction | location | rumor | crime | quest | item`
  - `label: str`
  - `visibility: player_visible | authoring | debug`
  - `metadata: dict[str, str]`
- `GraphEdge`
  - `source_id: str`
  - `target_id: str`
  - `kind: relationship | faction_relation | rumor_path | crime_report | quest_link`
  - `weight: int | None`
  - `label: str`
  - `visibility: player_visible | authoring | debug`
- `SocialGraphResponse`
  - `scope: player | authoring | debug`
  - `nodes: list[GraphNode]`
  - `edges: list[GraphEdge]`

### API Changes

- `GET /debug/sessions/{session_id}/social-graph`
- `GET /authoring/worlds/{world_id}/social-graph`
- Optional player-safe subset through `GET /game/state/{session_id}` extension only if filtered and useful.

Debug and authoring graph endpoints must be gated by existing environment controls.

### Frontend Changes

- Graph panel in debug/authoring mode.
- Player-safe relationship/faction summary remains separate.
- Filters for NPC, faction, rumor, crime, quest.
- Expand node details without exposing hidden data in play mode.

### Tests

- Hidden relationships excluded from player graph.
- Hidden factions excluded from player graph.
- Hidden witnesses excluded from player graph.
- Debug graph disabled when debug API disabled.
- Authoring graph disabled when authoring API disabled.
- Large graph fixture renders without crashing.
- Frontend build passes.

### Acceptance Standard

The UI can visualize social structures in debug/authoring mode while player-visible graph data remains filtered.

### Save/Load Impact

None directly. Graphs read current state or content pack data.

### Content Pack / Mod Version Impact

Moderate. Graph should include mod-origin metadata in authoring/debug mode only, useful for version conflicts.

### LLM Boundary Impact

None. Graph generation is deterministic and must not infer new relationships.

### Visibility Risk

High if scopes are mixed. Graph data must be explicitly audience-scoped.

## Module 4: Automated Playtesting Agents

### Goal

Add deterministic playtesting agents and scenario runners that exercise the public game API or test harness without directly mutating `GameState`.

### Data Structures

- `PlaytestScenario`
  - `id: str`
  - `world_id: str`
  - `max_turns: int`
  - `agent_policy: scripted | deterministic_explorer | llm_suggested_research`
  - `steps: list[PlaytestStep]`
  - `assertions: list[PlaytestAssertion]`
- `PlaytestStep`
  - `input_text: str`
  - `expected_action_type: str | None`
  - `save_after: bool`
  - `load_after: bool`
- `PlaytestAssertion`
  - `kind: visible_contains | visible_not_contains | event_exists | no_hidden_leak | state_path_equals`
  - `value: str`
- `PlaytestReport`
  - `scenario_id: str`
  - `passed: bool`
  - `turns_run: int`
  - `events_checked: int`
  - `violations: list[str]`

### API Changes

Prefer CLI/test harness first:

- `python -m backend.app.tools.run_playtest <scenario_id>`

Optional debug-only APIs:

- `POST /debug/playtests`
- `GET /debug/playtests/{run_id}`

### Frontend Changes

Optional debug panel:

- scenario list
- run button
- playtest report
- failed assertion details
- link to event timeline

### Tests

- Scripted scenario is deterministic.
- Agent inputs go through `GameLoop` or public API, not direct state mutation.
- Every agent game input records `Event`.
- Save/load mid-scenario works.
- Hidden facts/secrets/witnesses/memory forbidden strings are not visible.
- Mock provider only.
- No real LLM calls.

### Acceptance Standard

A deterministic playtest scenario can run from start to finish, produce a report, validate no hidden leaks, and preserve save/load consistency.

### Save/Load Impact

Moderate. Playtests should explicitly exercise save/load and migration paths.

### Content Pack / Mod Version Impact

Moderate. Scenarios should declare world id, content signature, and optional mod set to avoid stale playtest results.

### LLM Boundary Impact

Medium. v0.6 agents should be scripted/rule-based. LLM-assisted playtesting, if researched, may propose player text only and must not inspect hidden state or mutate `GameState`.

### Visibility Risk

Medium. Playtest reports can contain forbidden hidden strings. Reports are debug/test-only and must not enter player APIs.

## Module 5: Narrative Quality Evals

### Goal

Expand boundary evals into deterministic quality checks for narration consistency, Chinese output, visible fact grounding, suggested actions, and summary quality.

### Data Structures

- `NarrativeEvalCase`
  - `id: str`
  - `world_id: str`
  - `input_context: dict`
  - `quality_rules: list[str]`
  - `forbidden_patterns: list[str]`
  - `required_patterns: list[str]`
- `NarrativeQualityRule`
  - `code: str`
  - `description: str`
  - `severity: error | warning`
- `NarrativeEvalResult`
  - `case_id: str`
  - `passed: bool`
  - `violations: list[str]`
  - `warnings: list[str]`

### API Changes

No runtime API required.

Optional local CLI:

- `python -m backend.app.tools.run_narrative_evals`

### Frontend Changes

Optional authoring/debug report view:

- eval case list
- pass/fail status
- prompt/input snapshot with redactions
- violation list

### Tests

- Hidden facts absent from prompt snapshots.
- NPC secrets absent.
- Raw `state_deltas` absent.
- Chinese output required for narrator fake/golden cases.
- Suggested actions schema valid.
- `short_summary` present.
- No real LLM judge required.

### Acceptance Standard

Narrative evals run locally and catch both boundary leaks and deterministic quality regressions without external LLM calls.

### Save/Load Impact

None directly.

### Content Pack / Mod Version Impact

Low. Eval fixtures should include content signature so golden cases are not accidentally reused against incompatible content.

### LLM Boundary Impact

Low if deterministic. LLM-as-judge is not in v0.6.

### Visibility Risk

Medium. Prompt snapshots can contain sensitive test fixtures and must remain test/debug-only.

## Module 6: Performance Profiling and Optimization

### Goal

Add debug-only instrumentation for validation, world tick, NPC planning, memory search, mod resolution, save load, and frontend graph rendering.

### Data Structures

- `PerformanceMetric`
  - `name: str`
  - `scope: str`
  - `duration_ms: float`
  - `count: int`
  - `created_at: str`
- `ProfilingReport`
  - `scenario_id: str | None`
  - `metrics: list[PerformanceMetric]`
  - `slow_steps: list[str]`
  - `warnings: list[str]`

### API Changes

Debug-only:

- `GET /debug/performance`
- `POST /debug/performance/run-scenario`

These routes must not expose hidden payloads, prompt contents, API keys, or raw local paths.

### Frontend Changes

- Debug performance panel.
- Validation timing.
- World tick timing.
- Memory search timing.
- Frontend graph render timing/warnings.

### Tests

- Profiling disabled or gated outside debug.
- Profiling does not mutate `GameState`.
- Profiling report omits hidden content and raw deltas.
- Performance budgets for sample world validation and world tick.
- Frontend build.

### Acceptance Standard

Developers can identify slow v0.6 workflows without changing rule outcomes or leaking hidden data.

### Save/Load Impact

Low. Profiling may time save/load but must not alter persisted data.

### Content Pack / Mod Version Impact

Low to moderate. Profiling should include world/mod validation timings but avoid exposing hidden content text in reports.

### LLM Boundary Impact

None. Profiling must not call LLM.

### Visibility Risk

Low if metrics remain aggregate. Medium if slow-step details include content ids; keep detailed traces debug-only.

## Module 7: Advanced Mod Versioning

### Goal

Add deterministic mod dependency/version resolution, content signatures, load-order checks, and save compatibility indicators.

### Data Structures

- `ModVersionConstraint`
  - `mod_id: str`
  - `min_version: str | None`
  - `max_version: str | None`
- `ResolvedModSet`
  - `mods: list[str]`
  - `load_order: list[str]`
  - `content_hash: str`
  - `validation_report: dict`
- `SaveContentSignature`
  - `world_id: str`
  - `world_version: str`
  - `mod_ids: list[str]`
  - `content_hash: str`
- `ModCompatibilityReport`
  - `compatible: bool`
  - `errors: list[str]`
  - `warnings: list[str]`

### API Changes

- `POST /authoring/mods/resolve`
- `POST /authoring/worlds/{world_id}/validate-with-mods`
- `GET /game/saves/{save_id}/content-signature`
- optional `GET /authoring/worlds/{world_id}/mod-compatibility`

### Frontend Changes

- Mod list with versions.
- Dependency/conflict warnings.
- Load-order preview.
- Save compatibility badge.
- Content signature display in authoring/debug mode.

### Tests

- Dependency resolution.
- Conflict detection.
- Version constraint parsing.
- Duplicate id detection.
- Content hash stability.
- Save detects incompatible content signature.
- Path traversal still rejected.
- Executable files still rejected.

### Acceptance Standard

The engine can resolve a content-only mod set, validate it, compute a signature, and warn if a save was created with incompatible content.

### Save/Load Impact

High. Saves should record content signature and mod set metadata. Loading should warn or require migration/confirmation on mismatch.

### Content Pack / Mod Version Impact

High. Manifest schemas and validation expand to version constraints and load-order compatibility.

### LLM Boundary Impact

None. Versioning is deterministic.

### Visibility Risk

Medium. Mod metadata may reveal hidden content names. Player APIs should not expose raw mod internals.

## Module 8: Desktop Packaging Prototype

### Goal

Prototype a local desktop launcher that starts the backend and serves the frontend with clear local data/config directories.

### Data Structures

- `DesktopAppConfig`
  - `data_dir: str`
  - `worlds_dir: str`
  - `mods_dir: str`
  - `database_url: str`
  - `backend_host: str`
  - `backend_port: int`
  - `llm_provider: str`
  - `debug_enabled: bool`
  - `authoring_enabled: bool`
- `LocalPathConfig`
  - `config_dir: str`
  - `saves_dir: str`
  - `logs_dir: str`
  - `cache_dir: str`

### API Changes

No player API required.

Optional local-only app endpoints:

- `GET /app/health`
- `GET /app/local-config-summary`

Secrets and sensitive paths must be redacted unless explicitly debug-only.

### Frontend Changes

- First-run local setup status.
- Backend connection status.
- Data directory summary.
- Provider configuration guidance without storing API keys in frontend.

### Tests

- Backend launches with packaged config.
- Frontend reaches packaged backend.
- Bundle scan contains no `LLM_API_KEY` or `sk-...` value.
- SQLite path defaults outside source tree.
- Authoring/debug gates remain respected.

### Acceptance Standard

A developer can run a prototype desktop build locally without manually starting backend and frontend in separate shells.

### Save/Load Impact

Moderate. Desktop app must choose a stable local data directory and avoid writing real DB files into source control.

### Content Pack / Mod Version Impact

Moderate. Desktop config must locate worlds and mods predictably.

### LLM Boundary Impact

Low if provider factory remains unchanged. Do not store provider keys in frontend bundle.

### Visibility Risk

Medium for logs. Desktop logs must not include hidden content, raw debug events, prompts, or API keys by default.

## Module 9: Local Model Provider Support Research Slice

### Goal

Research a local provider option behind `LLMProvider`, without making it a required runtime dependency or changing LLM authority.

### Data Structures

- `LocalModelProviderConfig`
  - `base_url: str`
  - `model: str`
  - `timeout_seconds: int`
  - `json_mode_strategy: str`
  - `max_retries: int`
- `ProviderCapability`
  - `supports_json: bool`
  - `supports_streaming: bool`
  - `supports_embeddings: bool`

### API Changes

- Add config option research for `LLM_PROVIDER=local`.
- Optional debug-only provider status:
  - `GET /debug/provider`

### Frontend Changes

- Debug/settings provider status only.
- No frontend API key storage.

### Tests

- Factory can construct fake local provider.
- Schema failure raises clear error.
- Timeout/retry path tested with fake transport.
- No real local model server required.
- Provider output still cannot mutate `GameState`.

### Acceptance Standard

Research prototype demonstrates local provider compatibility behind the same provider boundary, with tests and no mandatory external service.

### Save/Load Impact

None.

### Content Pack / Mod Version Impact

None.

### LLM Boundary Impact

Medium. More providers increase failure modes, but authority remains unchanged.

### Visibility Risk

Medium if provider logging records prompts. Logs must be redacted or disabled.

## Module 10: Advanced Combat Expansion Research Slice

### Goal

Research one limited combat improvement without building a full tactical combat system.

Recommended slice:

- player-visible combat summary
- deterministic combat round metadata
- no complex enemy AI
- no grid movement

### Data Structures

- `CombatRoundState`
  - `combat_id: str`
  - `round_number: int`
  - `active_actor_id: str | None`
  - `turn_order: list[str]`
- `CombatSummary`
  - `combat_id: str`
  - `visible_combatants: list[str]`
  - `round_number: int`
  - `player_status: str`

### API Changes

- Optional player-safe `active_combat` field in `visible_state`.
- Optional debug-only raw combat endpoint.

### Frontend Changes

- Compact active combat summary.
- Visible combatants and player condition.
- Debug combat round info.

### Tests

- Hidden combatants not visible.
- Round metadata changes through `StateDelta`.
- Combat events recorded.
- Save/load preserves combat round state.
- Narrator does not receive hidden observers or raw combat internals.

### Acceptance Standard

One combat visibility/rounding slice is researched and tested without changing the broader v0.6 focus.

### Save/Load Impact

Low to moderate if round state is persisted.

### Content Pack / Mod Version Impact

Low unless new maneuver definitions are added. Avoid maneuver content in v0.6 unless time remains.

### LLM Boundary Impact

Medium. Narrator can render combat text but cannot decide hit, damage, injury, initiative, or death.

### Visibility Risk

Medium-high. Hidden enemies, observers, traps, and witnesses must stay hidden.

## v0.6 Integration Test Requirements

v0.6 integration regression should cover:

1. Load v0.5 save fixture, dry-run migration, migrate with backup, continue play.
2. Load migrated save and verify hidden facts, hidden NPCs, hidden relationships, and hidden memory remain filtered.
3. Edit content through structured authoring form, validate, and preview load.
4. Ensure authoring disabled mode blocks all authoring APIs/UI actions.
5. Build relationship/faction graph in player-safe and debug scopes; verify hidden data is scoped correctly.
6. Run deterministic playtest scenario through public API or `GameLoop` harness; verify every input records an event.
7. Run playtest with save/load mid-scenario.
8. Run narrative quality evals and boundary evals with mock providers only.
9. Run performance profiling in debug mode and verify it does not mutate state.
10. Resolve mod versions, compute content signature, validate save compatibility.
11. Desktop prototype smoke test if included in release scope.
12. Optional local provider and combat research slices do not affect default test behavior.

## v0.6 Final Acceptance Standard

v0.6 is acceptable only when:

- `python -m pytest` passes.
- Frontend build passes.
- No tests call real LLM APIs.
- Save migration supports dry-run, backup, failure safety, and fixture coverage.
- Save/load remains stable after migration.
- Structured authoring UI edits content only through gated backend APIs.
- Backend validation remains authoritative for content and mods.
- Relationship/faction graph keeps player-safe, authoring, and debug scopes separate.
- Automated playtesting agents cannot directly mutate `GameState`.
- Playtesting-agent game inputs record events.
- Narrative quality evals and boundary evals run deterministically.
- Performance profiling is debug-only and does not alter state.
- Mod versioning remains content-only and executes no code.
- Desktop prototype, if included, does not bundle secrets.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden mod metadata, debug deltas, and hidden/debug memory remain filtered from player APIs and narrator prompts.
- LLM remains parser/narrator/summarizer/draft assistant only.
- v0.6 acceptance, LLM boundary, visibility, security, migration, and release notes documents are produced.

## v0.7 Candidate Directions

Likely v0.7 candidates:

- Full schema-aware content studio with quest graph editor.
- More complete desktop app distribution and installer.
- Stable local model provider support if v0.6 research succeeds.
- Richer combat, equipment, injury, and maneuver systems.
- Expanded economy/trade simulation.
- Larger scenario simulation runner with golden transcript regression.
- LLM-assisted authoring assistant with strict draft/review/export boundaries.
- Mod load-order UI and composed-world previews.
- Save import/export and local sharing tools.
- Relationship/faction graph history over time.
- More robust local semantic memory backend.

## First Phase Recommendation

Start v0.6 with the save migration system.

Reason:

- It protects all later changes.
- It clarifies version metadata needed by mod versioning and desktop packaging.
- It creates fixture discipline for playtesting and evals.
- It is the highest leverage infrastructure before adding more UI and visualization.
