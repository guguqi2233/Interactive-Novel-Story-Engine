# v0.8 Roadmap

## Theme

Visual World Authoring

## Goal

v0.8 turns the polished local studio into a more visual world-authoring environment. The release should let a local creator inspect, edit, validate, preview, diff, branch, and regress-test world content through structured visual tools instead of relying mainly on raw YAML.

v0.8 does not change the authority model. The world engine remains the only fact source. The LLM remains a bounded language layer for intent parsing, narration, summarization, local-provider language output, and optional author-facing draft assistance. Visual tools are editor surfaces for content packs and drafts; they do not directly mutate active runtime `GameState`.

Core invariants:

- LLM does not directly modify `GameState`.
- All runtime state changes go through `StateDelta`.
- Player actions, system ticks, NPC planning ticks, and playtesting-agent game inputs are recorded as `Event`.
- Hidden facts do not enter `visible_state`.
- NPCs cannot know or act on unknown facts.
- Memory is not an authoritative fact source.
- Authoring/debug/perf/eval/playtest APIs remain local-only and gated.
- Mods are content-only and never execute arbitrary code.
- Save migration remains dry-run capable and testable.
- Desktop packaging must never include API keys or a real `.env`.
- Local model providers must go through `LLMProvider`.
- Visual editors must go through preview, validation, explicit save, and content-pack schemas.
- Authoring UI must not edit active session `GameState`.

## Explicitly Not In v0.8

v0.8 will not include:

- LLM world-judge behavior.
- LLM-generated canonical `StateDelta` application.
- Cloud sync, hosted accounts, online auth, marketplace publishing, or multi-user collaboration.
- Arbitrary mod/plugin code execution.
- Full tactical/grid combat.
- Large-scale war simulation.
- Large-scale dynamic economy simulation.
- Online marketplace workflows.
- Frontend direct filesystem access.
- Performance shortcuts that bypass `StateDelta`, `EventLog`, visibility filters, save migration, schema validation, or content validation.
- Visual editors that directly modify active session `GameState`.
- Local model output written directly into `GameState`.
- Automatic publishing or automatic overwriting of user world packs.

## Recommended Development Order

1. Visual authoring schema descriptors shared by editors.
2. Visual Map Editor.
3. Visual Quest Graph Editor full version.
4. NPC Goal Editor.
5. Item / Economy Editor.
6. Faction / Relationship Visual Editor.
7. Rumor / Crime Consequence Editor.
8. Visual Validation Graph.
9. Timeline Replay Visualizer.
10. World Branch / Diff System.
11. Scenario Regression Suite UI.
12. Local Template Browser.
13. Local Model Prompt Profile Manager.
14. Advanced Import / Export Packages.
15. Desktop App Shell Polish.
16. Authoring UX Integration Pass.
17. v0.8 integration regression tests, audits, acceptance report, and release notes.

## Module 1: Visual Map Editor

### Goal

Provide a visual editor for locations, exits, map clusters, and location metadata while preserving `locations.yaml` as the content source.

### Data Structures

- `MapGraph`
  - `nodes: list[MapLocationNode]`
  - `edges: list[MapExitEdge]`
  - `layout: dict[str, MapNodeLayout]`
- `MapLocationNode`
  - `id: str`
  - `name: str`
  - `description: str`
  - `tags: list[str]`
  - `visibility: public | hidden | discoverable`
  - `light_level: str | None`
  - `cover_level: int | None`
- `MapExitEdge`
  - `source_location_id: str`
  - `target_location_id: str`
  - `direction: str`
  - `locked: bool`
  - `requirements: list[str]`
- `MapNodeLayout`
  - `x: float`
  - `y: float`
  - `group_id: str | None`

### API Changes

- `GET /authoring/worlds/{world_id}/map/graph`
- `POST /authoring/worlds/{world_id}/map/preview`
- `PUT /authoring/worlds/{world_id}/map`

All endpoints are gated by `ENABLE_AUTHORING_API`, reject path traversal, and save only after validation.

### Frontend Changes

- Add Map Editor panel inside Authoring.
- Show locations as nodes and exits as edges.
- Support node detail forms for name, description, tags, light, cover, and visibility.
- Support edge editing for exits and locked-door metadata.
- Show diff, validation, and impact analysis before save.

### Tests

- Parse `locations.yaml` into `MapGraph`.
- Convert `MapGraph` back to valid YAML.
- Invalid exit is rejected.
- Hidden locations are not shown in player map surfaces.
- Preview does not write disk.
- Save goes through validator.

### Acceptance

- A creator can visually inspect and edit map topology.
- Invalid exits cannot be saved.
- Active sessions are not modified by map editing.

### Save Migration Impact

- Removing or renaming locations must produce impact warnings for existing saves.
- Changes that affect current player/NPC location ids must be migration-aware.

### Content Pack / Mod Version Impact

- Adds optional map layout metadata.
- Requires content schema version bump if layout files become first-class content.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Authoring can show hidden locations to the local creator.
- Player map views must show only player-visible locations.

## Module 2: Visual Quest Graph Editor Full Version

### Goal

Upgrade the v0.7 quest graph slice into a fuller visual editor for quest stages, objectives, triggers, visibility, and next-stage transitions.

### Data Structures

- `QuestGraph`
  - `quests: list[QuestGraphQuest]`
  - `stages: list[QuestGraphStage]`
  - `objectives: list[QuestGraphObjective]`
  - `triggers: list[QuestGraphTrigger]`
  - `edges: list[QuestGraphEdge]`
- `QuestGraphEdge`
  - `source_stage_id: str`
  - `target_stage_id: str`
  - `condition: dict[str, str] | None`
- `QuestGraphValidationIssue`
  - `quest_id: str`
  - `stage_id: str | None`
  - `path: str`
  - `message: str`
  - `severity: error | warning | suggestion`

### API Changes

- Extend:
  - `GET /authoring/worlds/{world_id}/quests/graph`
  - `POST /authoring/worlds/{world_id}/quests/graph/preview`
- Add:
  - `PUT /authoring/worlds/{world_id}/quests/graph`

### Frontend Changes

- Visual quest graph with stage nodes and transition edges.
- Forms for objectives, triggers, visibility, and rewards.
- Validation panel grouped by quest/stage/path.
- Diff and impact analysis before save.

### Tests

- Quest graph roundtrip preserves semantic content.
- Invalid `next_stages` edge is rejected.
- Invalid trigger references are rejected.
- Hidden quests do not enter `visible_state`.
- Save requires successful validation.

### Acceptance

- A creator can edit multi-stage quests visually without hand-editing every YAML field.
- The editor cannot bypass quest validation.

### Save Migration Impact

- Removed quest/stage ids must warn about existing saves with active quest state.

### Content Pack / Mod Version Impact

- May require clearer quest graph schema version metadata.

### LLM Boundary

- No automatic LLM quest graph editing.
- Optional future draft assistance must remain draft-only.

### Visibility Risk

- Hidden quest authoring details stay inside authoring UI.
- Player UI continues to show only visible or active quest state.

## Module 3: NPC Goal Editor

### Goal

Provide structured editing for NPC goals, priorities, constraints, allowed actions, and plan state defaults.

### Data Structures

- `NPCGoalEditorModel`
  - `npc_id: str`
  - `goals: list[GoalDefinition]`
  - `priorities: dict[str, int]`
  - `constraints: list[GoalConstraint]`
- `GoalConstraint`
  - `id: str`
  - `type: fact_known | rumor_known | location | relationship | life_state`
  - `reference_id: str`
  - `required_value: str | int | bool | None`

### API Changes

- `GET /authoring/worlds/{world_id}/npcs/{npc_id}/goals`
- `POST /authoring/worlds/{world_id}/npcs/{npc_id}/goals/preview`
- `PUT /authoring/worlds/{world_id}/npcs/{npc_id}/goals`

### Frontend Changes

- Goal editor inside NPC authoring view.
- Priority controls, allowed-action checklists, and condition reference pickers.
- Validation for unknown fact/rumor/location references.

### Tests

- Goal YAML roundtrip.
- Unknown fact condition rejected.
- Dead/incapacitated action constraints remain enforced by runtime rules.
- Preview does not mutate active `GameState`.

### Acceptance

- NPC goals are easier to author and remain deterministic rule inputs.

### Save Migration Impact

- Changed goal ids warn if active saves reference old goal ids.

### Content Pack / Mod Version Impact

- NPC goal schema should be versioned and validated.

### LLM Boundary

- No LLM planning.
- Goals produce finite rule candidates only.

### Visibility Risk

- NPC secrets and hidden goals may be visible in authoring UI but never player UI.

## Module 4: Faction / Relationship Visual Editor

### Goal

Let creators visually inspect and edit faction relations, NPC relationships, trust/fear/affinity, and known-by-player flags.

### Data Structures

- `RelationshipEditorGraph`
  - `nodes: list[GraphNode]`
  - `edges: list[RelationshipEditorEdge]`
- `RelationshipEditorEdge`
  - `source_id: str`
  - `target_id: str`
  - `relation_type: str`
  - `trust: int`
  - `fear: int`
  - `affinity: int`
  - `obligation: int`
  - `known_by_player: bool`
- `FactionConflictEditorEdge`
  - `source_faction_id: str`
  - `target_faction_id: str`
  - `relation: str`
  - `conflict_level: int`
  - `alert_level: int`

### API Changes

- `GET /authoring/worlds/{world_id}/relationships/graph`
- `PUT /authoring/worlds/{world_id}/relationships/graph`
- `GET /authoring/worlds/{world_id}/factions/graph`
- `PUT /authoring/worlds/{world_id}/factions/graph`

### Frontend Changes

- Visual relationship/faction graph editor.
- Safe list/SVG graph first; no heavy graph framework required.
- Relationship edge forms and faction conflict forms.

### Tests

- Relationship graph roundtrip.
- Invalid NPC/faction ids rejected.
- Hidden relationships remain absent from player graph.
- Runtime relationship changes still use `StateDelta`.

### Acceptance

- Creator can edit relationship and faction graph data visually.
- Player graph remains filtered.

### Save Migration Impact

- Removed relationship/faction ids warn for saves with relationship/faction state.

### Content Pack / Mod Version Impact

- Relationships and faction conflict files should carry content schema compatibility.

### LLM Boundary

- No LLM social-graph inference.

### Visibility Risk

- Hidden relationships and hidden faction conflicts must not cross from authoring/debug graph to player graph.

## Module 5: Item / Economy Editor

### Goal

Provide structured editing for items, prices, trade flags, merchant inventory, rarity, ownership, and economy defaults.

### Data Structures

- `ItemEconomyEditorModel`
  - `items: list[ItemDefinition]`
  - `merchants: list[MerchantDefinition]`
  - `currency_defaults: dict[str, int]`
- `MerchantInventoryEntry`
  - `merchant_id: str`
  - `item_id: str`
  - `quantity: int`
  - `price_override: int | None`

### API Changes

- `GET /authoring/worlds/{world_id}/economy`
- `POST /authoring/worlds/{world_id}/economy/preview`
- `PUT /authoring/worlds/{world_id}/economy`

### Frontend Changes

- Item table with filters for tradeable, hidden, stolen/default, rarity, and tags.
- Merchant inventory editor.
- Price preview based on deterministic economy rules.

### Tests

- Negative prices rejected.
- Hidden shop inventory not exposed to player UI.
- Invalid owner/location/container conflicts rejected.
- Preview does not write disk or active state.

### Acceptance

- Economy authoring is visual and validation-backed.
- Frontend does not calculate authoritative trade outcomes.

### Save Migration Impact

- Removed item ids warn for saves with inventory/shop references.

### Content Pack / Mod Version Impact

- Item/economy schema may require version bump if inventory files are split.

### LLM Boundary

- No LLM pricing or trade authority.

### Visibility Risk

- Hidden items can appear in authoring UI but not player inventory/shop surfaces until visible.

## Module 6: Rumor / Crime Consequence Editor

### Goal

Provide a visual editor for rumor seeds, crime classifications, witness consequences, reputation effects, and social tick consequence rules.

### Data Structures

- `ConsequenceRuleGraph`
  - `triggers: list[ConsequenceTriggerNode]`
  - `effects: list[ConsequenceEffectNode]`
  - `edges: list[ConsequenceEdge]`
- `ConsequenceTriggerNode`
  - `id: str`
  - `type: crime | rumor | reputation | quest | combat | item`
  - `reference_id: str | None`
- `ConsequenceEffectNode`
  - `id: str`
  - `type: create_rumor | change_reputation | add_witness | set_flag | quest_trigger`
  - `parameters: dict[str, str | int | bool]`

### API Changes

- `GET /authoring/worlds/{world_id}/consequences/graph`
- `POST /authoring/worlds/{world_id}/consequences/preview`
- `PUT /authoring/worlds/{world_id}/consequences/graph`

### Frontend Changes

- Rule graph for rumor/crime/social consequences.
- Reference pickers for facts, factions, NPCs, crimes, and quests.
- Warnings when hidden fact text appears in player-facing rumor text.

### Tests

- Unknown referenced ids rejected.
- Hidden fact text warning/error is surfaced.
- Consequence graph roundtrip.
- Runtime consequences still go through `StateDelta` and `Event`.

### Acceptance

- Social consequence rules become inspectable and safer to author.

### Save Migration Impact

- Consequence id changes may affect deduplication ids in saves; impact analysis must warn.

### Content Pack / Mod Version Impact

- New consequence authoring schema likely needs explicit content schema version.

### LLM Boundary

- No LLM consequence judgment.

### Visibility Risk

- Rumor player-facing text must not reveal hidden facts unless explicitly safe.

## Module 7: Visual Validation Graph

### Goal

Show validation issues as a graph of broken references, affected files, and suggested repair paths.

### Data Structures

- `ValidationGraph`
  - `nodes: list[ValidationGraphNode]`
  - `edges: list[ValidationGraphEdge]`
  - `issues: list[ValidationIssue]`
- `ValidationGraphNode`
  - `id: str`
  - `type: file | entity | issue | reference`
  - `label: str`
- `ValidationGraphEdge`
  - `source: str`
  - `target: str`
  - `type: references | missing | conflicts | blocks_save`

### API Changes

- `POST /authoring/worlds/{world_id}/validate-graph`
- Reuse structured validation report from v0.5/v0.6.

### Frontend Changes

- Validation graph panel grouped by file, entity, and severity.
- Clicking a node opens the relevant authoring file/path when available.

### Tests

- Invalid references create graph nodes/edges.
- Warnings do not block save unless configured.
- Errors block save.
- No sensitive local paths are exposed.

### Acceptance

- Creators can understand broken content relationships visually.

### Save Migration Impact

- Validation graph can include save-impact warnings from removed/renamed ids.

### Content Pack / Mod Version Impact

- Helps validate content/mod schema compatibility.

### LLM Boundary

- No LLM validation.

### Visibility Risk

- Authoring graph can show hidden content to local creator; player UI must not consume it.

## Module 8: Timeline Replay Visualizer

### Goal

Visualize `EventLog`, `state_deltas`, system ticks, quest transitions, NPC movements, and social consequences for local debugging.

### Data Structures

- `ReplayTimeline`
  - `events: list[ReplayTimelineEvent]`
  - `snapshots: list[ReplaySnapshotSummary]`
  - `branches: list[ReplayBranchSummary]`
- `ReplayTimelineEvent`
  - `turn: int`
  - `event_id: str`
  - `actor_id: str`
  - `action_type: str`
  - `visible_to_player: bool`
  - `delta_count: int`
  - `summary: str`

### API Changes

- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/timeline`
- Optional `POST /debug/saves/{save_id}/replay-dry-run`

All debug endpoints remain gated by `ENABLE_DEBUG_API`.

### Frontend Changes

- Timeline replay view in debug area.
- Turn scrubber, event filters, and delta summaries.
- Debug-only label and local-only warning.

### Tests

- Debug disabled blocks timeline.
- Timeline event order deterministic.
- Player UI does not receive raw debug timeline.
- Replay dry-run does not mutate save.

### Acceptance

- Developers can inspect what happened without exposing debug state to player narrative.

### Save Migration Impact

- Timeline must work for migrated saves and expose migration event summaries safely.

### Content Pack / Mod Version Impact

- Mod/content version changes should be visible as safe metadata.

### LLM Boundary

- No LLM replay interpretation.

### Visibility Risk

- Raw `state_deltas` remain debug-only and never enter narrator/player surfaces.

## Module 9: World Branch / Diff System

### Goal

Let creators create local branches of content packs, compare branches, preview merges, and avoid accidental overwrite.

### Data Structures

- `WorldBranch`
  - `id: str`
  - `world_id: str`
  - `base_content_pack_version: str`
  - `created_at: str`
  - `description: str | None`
- `WorldDiffReport`
  - `base_branch_id: str`
  - `compare_branch_id: str`
  - `changed_files: list[FileDiffSummary]`
  - `added_ids: list[EntityRef]`
  - `removed_ids: list[EntityRef]`
  - `renamed_candidates: list[RenameCandidate]`
  - `migration_warnings: list[str]`

### API Changes

- `GET /authoring/worlds/{world_id}/branches`
- `POST /authoring/worlds/{world_id}/branches`
- `POST /authoring/worlds/{world_id}/branches/{branch_id}/diff`
- `POST /authoring/worlds/{world_id}/branches/{branch_id}/merge-preview`

### Frontend Changes

- Branch selector in Authoring.
- Diff viewer with changed files and reference impact.
- Explicit save/merge confirmation.

### Tests

- Branch creation does not modify active content.
- Diff detects added/removed ids.
- Merge preview does not write disk.
- Path traversal rejected.

### Acceptance

- Creators can safely explore changes before committing them to world content.

### Save Migration Impact

- Branch diffs should produce migration-impact warnings for removed/renamed ids.

### Content Pack / Mod Version Impact

- Branch metadata must not confuse mod package versioning.

### LLM Boundary

- No LLM merge authority.

### Visibility Risk

- Branch diff is authoring-only and can include hidden content; player UI does not consume it.

## Module 10: Scenario Regression Suite UI

### Goal

Expose deterministic scenario and playtest regression runs through a local UI.

### Data Structures

- `ScenarioRegressionSuite`
  - `id: str`
  - `name: str`
  - `world_id: str`
  - `scenarios: list[ScenarioRegressionCase]`
- `ScenarioRegressionRun`
  - `run_id: str`
  - `suite_id: str`
  - `created_at: str`
  - `passed: int`
  - `failed: int`
  - `failures: list[ScenarioFailureSummary]`

### API Changes

- `GET /playtests/scenario-suites`
- `POST /playtests/scenario-suites/{suite_id}/run`
- `GET /playtests/scenario-runs/{run_id}`

Endpoints gated by `ENABLE_PLAYTEST_API` or debug configuration.

### Frontend Changes

- Scenario regression dashboard.
- Run fixed-seed suites and inspect safe failure summaries.
- Link failures to validation/timeline where possible.

### Tests

- Suite run deterministic.
- Hidden facts not included in ordinary failure summaries.
- Agent actions go through game loop/test harness.
- No direct `GameState` mutation by test agents.

### Acceptance

- Local creator can detect regressions after visual edits.

### Save Migration Impact

- Suites should run against migrated saves or fresh worlds with migration warnings.

### Content Pack / Mod Version Impact

- Suites include world/mod version metadata.

### LLM Boundary

- No real LLM calls; use mock/local_stub providers.

### Visibility Risk

- Reports must be sanitized unless explicitly debug-only.

## Module 11: Local Template Browser

### Goal

Make scenario templates discoverable, previewable, and safely applyable from the authoring UI.

### Data Structures

- `TemplateCatalog`
  - `templates: list[ScenarioTemplateSummary]`
- `TemplatePreviewResult`
  - `template_id: str`
  - `variables: dict[str, str]`
  - `rendered_files: list[RenderedTemplateFile]`
  - `validation_report: ValidationReport`
  - `writes_disk: bool`

### API Changes

- `GET /authoring/templates`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/worlds/{world_id}/templates/{template_id}/apply-preview`
- Optional explicit apply endpoint that writes only after validation and confirmation.

### Frontend Changes

- Template browser in Authoring.
- Variable form, preview, validation report, and diff before save.

### Tests

- Template preview does not write disk.
- Invalid variables rejected.
- Path traversal rejected.
- Rendered content passes validation before save.

### Acceptance

- Templates help creators start content without becoming script execution.

### Save Migration Impact

- Applying templates may add ids; removing/overwriting existing ids requires impact warnings.

### Content Pack / Mod Version Impact

- Template schema and content schema compatibility must be explicit.

### LLM Boundary

- No LLM template rendering in v0.8.

### Visibility Risk

- Templates must not mark hidden facts as player-visible by default.

## Module 12: Local Model Prompt Profile Manager

### Goal

Allow local users to define safe prompt/profile settings for providers while preserving provider factory boundaries and schema validation.

### Data Structures

- `PromptProfile`
  - `id: str`
  - `name: str`
  - `provider: mock | openai | local_http | local_stub`
  - `model: str | None`
  - `temperature_defaults: dict[str, float]`
  - `json_mode: bool`
  - `enabled_for: list[intent_parser | narrator | memory_summarizer | quest_draft]`
  - `redaction_policy_id: str`
- `PromptProfileValidationReport`
  - `errors: list[str]`
  - `warnings: list[str]`

### API Changes

- `GET /studio/prompt-profiles`
- `POST /studio/prompt-profiles/validate`
- `PUT /studio/prompt-profiles/{profile_id}`

Profiles are local settings and must not expose API keys.

### Frontend Changes

- Prompt profile manager in Settings.
- Shows provider status and safe configurable fields.
- Does not show raw prompt secrets or API keys.

### Tests

- Profile validation rejects unsupported provider ids.
- API key never returned.
- Business modules still use provider factory.
- Schema validation errors remain clear.

### Acceptance

- Users can configure local provider behavior without changing world authority.

### Save Migration Impact

- None for `GameState`; profile ids may be stored as local studio config only.

### Content Pack / Mod Version Impact

- Prompt profiles are not content pack facts.

### LLM Boundary

- Profiles configure bounded LLM calls; they do not grant state authority.

### Visibility Risk

- Prompt profile UI must not include hidden facts, raw prompts from sessions, or debug memory.

## Module 13: Advanced Import / Export Packages

### Goal

Improve v0.7 import/export with package manifests, dry-run import, dependency checks, checksums, and migration warnings.

### Data Structures

- `PackageManifest`
  - `id: str`
  - `package_type: world | mod | save_bundle | template_bundle`
  - `version: str`
  - `engine_version_min: str`
  - `content_schema_version: str`
  - `files: list[PackageFileEntry]`
  - `checksums: dict[str, str]`
- `PackageImportDryRunReport`
  - `parsed_ok: bool`
  - `validation_report: ValidationReport`
  - `conflicts: list[str]`
  - `migration_required: bool`
  - `blocked_files: list[str]`

### API Changes

- `POST /authoring/packages/import-dry-run`
- `POST /authoring/packages/import`
- `POST /authoring/packages/export`
- `GET /authoring/packages/recent`

All endpoints remain gated by `ENABLE_AUTHORING_API`.

### Frontend Changes

- Import/export wizard.
- Dry-run report, conflict resolution prompt, and explicit overwrite confirmation.

### Tests

- Zip slip rejected.
- Executable files rejected.
- `.env`, DB files, logs, and secrets rejected.
- Checksums verified.
- Import dry-run does not write disk.

### Acceptance

- Packages are safer to exchange locally without becoming online publishing.

### Save Migration Impact

- Save bundles must show migration status before import is finalized.

### Content Pack / Mod Version Impact

- Package manifests include content/mod schema metadata.

### LLM Boundary

- No LLM package inspection.

### Visibility Risk

- Import reports must not expose local absolute paths or secret file contents.

## Module 14: Desktop App Shell Polish

### Goal

Improve the local desktop-like startup and shell experience without claiming a public production installer.

### Data Structures

- `DesktopLaunchStatus`
  - `backend_ready: bool`
  - `frontend_ready: bool`
  - `database_configured: bool`
  - `authoring_enabled: bool`
  - `debug_enabled: bool`
  - `perf_enabled: bool`
  - `warnings: list[str]`

### API Changes

- Reuse `/studio/status` and `/studio/config-summary`.
- No public remote management endpoints.

### Frontend Changes

- Better shell loading/error states.
- Desktop/local-only notices.
- Links to local logs without exposing sensitive paths in normal UI.

### Tests

- Build output does not include `.env` or API keys.
- Startup scripts contain no real secrets.
- `.gitignore` excludes desktop build outputs.

### Acceptance

- Local launch is clearer and safer.
- Desktop shell remains prototype/local packaging, not public distribution.

### Save Migration Impact

- Startup can show migration warnings; it does not auto-migrate.

### Content Pack / Mod Version Impact

- Startup can show content/mod version warnings.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Shell must not show hidden content or debug dumps on startup.

## Module 15: Authoring UX Integration Pass

### Goal

Unify visual editors, validation, preview, diff, save confirmation, and local-only safety copy across the authoring workspace.

### Data Structures

- `AuthoringWorkspaceState`
  - `world_id: str`
  - `active_editor: str`
  - `dirty_files: list[str]`
  - `validation_report: ValidationReport | None`
  - `impact_report: ImpactAnalysisReport | None`
  - `last_preview_at: str | None`

### API Changes

- Prefer reusing existing preview/validation/diff APIs.
- Add only small schema-description endpoints if editors need stable metadata.

### Frontend Changes

- Consistent navigation between map, quests, NPC goals, economy, relationships, consequences, templates, validation graph, and diffs.
- Consistent empty/loading/error states.
- Consistent local-only and explicit-save notices.
- Dangerous operations require confirmation.

### Tests

- Disabled authoring API degrades gracefully.
- Dirty-state prompts protect unsaved edits.
- Save is blocked on validation errors.
- Player UI does not show authoring/debug-only data.

### Acceptance

- Visual authoring feels like one coherent local studio rather than isolated panels.

### Save Migration Impact

- Workspace shows migration-impact warnings before save when ids are removed/renamed.

### Content Pack / Mod Version Impact

- Editors show schema and mod compatibility warnings consistently.

### LLM Boundary

- No new LLM authority.

### Visibility Risk

- Main risk is accidentally rendering authoring content in player UI. Shared components must keep authoring/debug/player scopes explicit.

## v0.8 Integration Test Requirements

v0.8 must add or extend regression tests covering:

1. Visual map graph roundtrip and invalid-exit rejection.
2. Quest graph full editor roundtrip and invalid transition rejection.
3. NPC goal editor validation and active-session isolation.
4. Relationship/faction editor filtering between authoring/debug/player scopes.
5. Item/economy editor validation, including ownership conflicts and hidden shop inventory filtering.
6. Rumor/crime consequence editor validation and hidden fact text warnings.
7. Visual validation graph issue generation.
8. Timeline replay visualizer ordering and debug gating.
9. World branch/diff preview without disk writes.
10. Scenario regression UI running deterministic playtests without real LLM calls.
11. Template browser preview without disk writes.
12. Prompt profile manager redacting keys and preserving provider factory boundaries.
13. Package import dry-run rejecting zip slip, executable files, `.env`, secrets, DB files, and logs.
14. Desktop shell build/startup scripts excluding `.env` and API keys.
15. Authoring UX disabled-state, dirty-state, and explicit-save behavior.

All test suites must remain deterministic and use mock/local_stub providers unless a test is specifically a fake local HTTP harness. Tests must not call real OpenAI or real local model services.

## v0.8 Final Acceptance Standard

v0.8 can be accepted when:

- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.
- Visual editors cannot bypass validator, preview, explicit save, or content schema checks.
- Authoring changes do not mutate active session `GameState`.
- Player API and player UI do not expose hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden mod metadata, debug memory, raw `state_deltas`, or raw `GameState`.
- Debug/authoring/perf/eval/playtest APIs remain local-only and gated.
- Import/export and branch/diff workflows reject path traversal, executable files, secrets, and unsafe overwrites.
- Local model prompt profiles still route through `LLMProvider` and cannot grant world-state authority.
- Save migration warnings are shown before potentially breaking content edits.
- Desktop shell polish does not package `.env`, API keys, databases, logs, caches, or build artifacts that should remain local.
- Documentation, audits, acceptance report, release notes, and final freeze checks are updated.

## Recommended v0.9 Directions

Potential v0.9 themes:

- Visual narrative timeline and chapter planner.
- Richer map layout tooling with optional coordinates, regions, and route constraints.
- Advanced content refactor tools for safe id rename and migration generation.
- Offline documentation browser for content schemas and rule references.
- More complete desktop shell if v0.8 startup polish proves stable.
- Accessibility and keyboard workflow pass for the authoring studio.
- Optional local-only asset manager for images/audio references, with no cloud upload.
- Stronger property-based content validation and replay invariants.
- More advanced but still rule-bound combat encounter authoring.

v0.9 should continue preserving the core boundary: the world engine is the fact source, and the LLM is a language layer.
