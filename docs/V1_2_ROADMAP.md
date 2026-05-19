# v1.2 Roadmap: Visual Authoring Pro

## Version Goal

v1.2 upgrades the local studio from a collection of useful authoring panels into
a coherent Visual Authoring Pro workflow for building, reviewing, validating,
and packaging local interactive-fiction worlds.

The theme is visual creation with explicit safety gates. Creators should be able
to edit maps, quests, social graphs, factions, rumors, crime consequences,
items, economy data, RP characters, dialogue scenes, group RP scenes, templates,
branches, content libraries, references, and draft history through local visual
tools. None of those tools become the world engine, and none of them can bypass
the v1.0/v1.1 authority boundary.

The rule remains:

Authoring drafts are content candidates. `GameState` remains runtime truth.

## Frozen Constraints

- LLM output must not directly modify `GameState`.
- All canonical runtime state changes must go through `StateDelta`.
- All formal player actions, system ticks, NPC planning ticks, and dialogue
  scene events must record `Event` entries.
- Authoring drafts are not active `GameState`.
- Every editor save must use preview, validation, and explicit save.
- Hidden facts must not enter player `visible_state`.
- NPCs must not receive facts outside NPC knowledge rules.
- RP private fields do not enter player-facing or ordinary prompt context by
  default.
- Authoring and debug APIs remain local-only tools.
- Import/export must not execute arbitrary code.
- Content packages must not bypass validation or Quality Gate requirements.
- `provider_factory` remains the only runtime LLM provider entry.

## Not In v1.2

- LLM world judge.
- LLM direct `GameState` mutation.
- Visual editors directly modifying active `GameState`.
- Visual editors bypassing validation.
- Arbitrary code plugin execution.
- Online marketplace.
- Cloud sync, accounts, hosted collaboration, or multi-user authoring.
- Automatic overwrite of user world packs.
- Automatic application of external character cards or templates to an active
  world.
- Prompt Profile authority expansion.
- Editor access to `.env`, API keys, database files, logs, or arbitrary system
  files.
- Remote URL import for authoring assets.
- Automatic world repair from Quality Gate output.

## Recommended Development Order

1. Authoring Pro Boundary Contract.
2. Authoring Validation Gate.
3. Authoring Undo / Draft History.
4. Content Diff Review.
5. Authoring Project Dashboard.
6. Visual Map Editor Pro.
7. Quest Graph Editor Pro.
8. NPC Relationship Graph Editing.
9. Faction Conflict Editor.
10. Rumor / Crime Consequence Graph Pro.
11. Item / Economy Visual Editor Pro.
12. RP Character Authoring UI Pro.
13. Dialogue Scene Editor.
14. Group RP Scene Authoring.
15. Character Pack Builder.
16. Template Wizard.
17. Local Content Library.
18. Visual Reference Picker System.
19. Authoring Workflow Presets.
20. World Branch Merge Assistant.

The first three modules should land before expanding editor surface area. They
define the safety contract, save gate, and draft recovery model that the rest of
v1.2 should reuse.

## Module Roadmap

### 1. Authoring Pro Boundary Contract

Goal: Document and encode the v1.2 authoring boundary so every Pro editor uses
the same draft, validation, explicit-save, and visibility assumptions.

Data structures:

- `AuthoringProPolicy`
- `AuthoringDraftScope`
- `AuthoringSurfaceKind`
- `AuthoringSaveMode`
- `AuthoringRiskLevel`
- `AuthoringBoundaryReport`

API changes:

- `GET /authoring/pro/boundary`
- `POST /authoring/pro/boundary/check`

Frontend changes:

- Add a compact boundary/status panel in Authoring Pro.
- Show whether the current operation edits content files, drafts, packages, or
  active runtime state. Active runtime state should always be false.

Tests:

- Policy defaults reject active `GameState` mutation.
- Boundary report redacts hidden fact text and local paths.
- Prompt profile fields cannot widen authoring authority.

Acceptance:

- Every v1.2 editor can reference the shared policy.
- Boundary check clearly reports local-only, validation-required, and
  no-active-state-mutation status.

Content schema impact: none.

Save migration impact: none.

RP / knowledge / visibility impact: documents that authoring may inspect local
hidden content, but ordinary player/RP prompts cannot.

LLM boundary impact: no new model authority.

Leak risk: medium if boundary reports include raw hidden text. Reports must use
ids, counts, and redacted summaries.

### 2. Authoring Validation Gate

Goal: Centralize editor save gating so visual editors cannot save invalid YAML,
unsafe imports, broken references, or Quality Gate blockers.

Data structures:

- `AuthoringValidationGateRequest`
- `AuthoringValidationGateResult`
- `GateCheck`
- `GateRequirement`
- `GateBlockingIssue`

API changes:

- `POST /authoring/worlds/{world_id}/gate/preview`
- `POST /authoring/worlds/{world_id}/gate/run`
- Add optional `gate_result` to Pro editor preview/save responses.

Frontend changes:

- Add a shared gate widget with pass/warn/block states.
- Disable final save when blockers exist.
- Link gate issues to the relevant editor, file, node, edge, or field.

Tests:

- Invalid content blocks save.
- Hidden-leak and schema blockers are surfaced safely.
- Quality Gate blockers cannot be ignored by Pro save paths.
- Gate output excludes raw `GameState`, raw `state_deltas`, API keys, and hidden
  fact text.

Acceptance:

- All Pro save APIs call the gate or prove equivalent validation.
- A blocked save writes nothing.

Content schema impact: none initially.

Save migration impact: gate can warn when edits may require save review; it
does not migrate saves.

RP / knowledge / visibility impact: gate checks RP hidden/private fields and
NPC knowledge references where relevant.

LLM boundary impact: deterministic checks only.

Leak risk: high if gate displays hidden content. Normal gate output must be
safe; debug-only details stay gated.

### 3. Authoring Undo / Draft History

Goal: Provide local draft checkpoints and undo/redo for editor changes without
touching active sessions.

Data structures:

- `AuthoringDraft`
- `AuthoringDraftRevision`
- `AuthoringDraftChange`
- `DraftHistorySummary`
- `DraftRestoreRequest`

API changes:

- `GET /authoring/worlds/{world_id}/drafts`
- `POST /authoring/worlds/{world_id}/drafts`
- `GET /authoring/worlds/{world_id}/drafts/{draft_id}`
- `POST /authoring/worlds/{world_id}/drafts/{draft_id}/restore`
- `DELETE /authoring/worlds/{world_id}/drafts/{draft_id}`

Frontend changes:

- Add undo/redo controls to Pro editors.
- Add draft history drawer with timestamps, touched files, issue counts, and
  restore preview.

Tests:

- Draft revisions are local content snapshots, not saves.
- Restore requires preview/validation before writing files.
- Draft history rejects path traversal and disallowed files.

Acceptance:

- Users can recover a previous authoring draft without modifying active
  `GameState`.

Content schema impact: none for world packs; optional local draft metadata file
must stay outside published content unless explicitly exported.

Save migration impact: none.

RP / knowledge / visibility impact: draft views may show hidden authoring
content only in authoring surfaces.

LLM boundary impact: none.

Leak risk: medium. Draft history must not be exposed through player APIs or
normal narrator context.

### 4. Content Diff Review

Goal: Make changes reviewable before save, with semantic diffs for YAML,
graphs, RP content, templates, and packages.

Data structures:

- `ContentDiffReview`
- `ContentDiffFile`
- `ContentDiffEntity`
- `ContentDiffRisk`
- `ContentDiffApproval`

API changes:

- `POST /authoring/worlds/{world_id}/diff/review`
- `POST /authoring/worlds/{world_id}/diff/approve`
- Extend editor preview responses with `diff_review_id`.

Frontend changes:

- Add side-by-side raw YAML diff.
- Add semantic entity diff by map node, quest stage, relationship edge, faction
  conflict, item, rumor, crime, RP field, and template output.

Tests:

- Diff review redacts hidden text in normal mode.
- Deleted ids and renamed-id guesses are stable.
- Approval cannot skip validation gate.

Acceptance:

- Any Pro save can show what will change before writing.

Content schema impact: none.

Save migration impact: diff review flags changed/deleted ids that may affect
existing saves.

RP / knowledge / visibility impact: private RP fields are marked authoring-only
in diff metadata.

LLM boundary impact: no LLM decision required.

Leak risk: high in normal authoring review if hidden facts are copied into
shareable reports. Keep hidden text local and mark exports explicitly.

### 5. Authoring Project Dashboard

Goal: Provide a single Pro dashboard for world health, changed drafts, Quality
Gate, schema status, content coverage, RP safety, and package readiness.

Data structures:

- `AuthoringProjectStatus`
- `AuthoringProjectMetric`
- `AuthoringProjectTask`
- `AuthoringReadinessSummary`

API changes:

- `GET /authoring/worlds/{world_id}/project-status`
- `POST /authoring/worlds/{world_id}/project-status/refresh`

Frontend changes:

- Add project dashboard tab.
- Show active world, draft state, validation status, gate status, recent diffs,
  coverage, health score, RP warnings, package/export readiness.

Tests:

- Dashboard does not return raw hidden text, raw `GameState`, raw
  `state_deltas`, API keys, or local absolute paths.
- Dashboard remains local authoring, not player API.

Acceptance:

- A creator can see whether the world is ready to edit, test, package, or
  release.

Content schema impact: none.

Save migration impact: shows migration risk summaries only.

RP / knowledge / visibility impact: RP warnings are counts/safe summaries.

LLM boundary impact: none.

Leak risk: medium. Summary aggregation must not promote debug details into
normal dashboard fields.

### 6. Visual Map Editor Pro

Goal: Improve the map editor with richer regions, layout tools, node grouping,
visibility diagnostics, locked/hidden exits, and reference picker integration.

Data structures:

- Extend `LocationVisualDef` only if needed:
  - `region_id`
  - `layer`
  - `display_group`
  - `pin_style`
  - `authoring_notes`
- `MapEditorProGraph`
- `MapEditorProLayoutHint`

API changes:

- `GET /authoring/worlds/{world_id}/map/pro`
- `POST /authoring/worlds/{world_id}/map/pro/preview`
- `POST /authoring/worlds/{world_id}/map/pro/validate`
- `PUT /authoring/worlds/{world_id}/map/pro`

Frontend changes:

- Add pan/zoom, region filters, visibility filters, node inspector, edge
  inspector, locked/hidden exit badges, and semantic diff preview.

Tests:

- Hidden locations and hidden exits remain absent from player map APIs.
- Save path writes `locations.yaml` only after validation.
- No active session movement rules are changed by editor layout data.

Acceptance:

- Visual map edits produce valid `locations.yaml` and pass the gate.

Content schema impact: additive optional visual fields.

Save migration impact: none for active saves unless location ids are changed or
deleted; gate warns on those changes.

RP / knowledge / visibility impact: map visibility must not reveal hidden
locations to player or NPC prompts.

LLM boundary impact: none.

Leak risk: high around hidden exits and authoring notes. Player map and
narrator context must never use authoring notes.

### 7. Quest Graph Editor Pro

Goal: Upgrade quest graph editing with stage-node editing, trigger/reward
inspectors, reachability hints, visibility diagnostics, and completion-path
analysis.

Data structures:

- `QuestGraphPro`
- `QuestStageEditorNode`
- `QuestTriggerEditorNode`
- `QuestRewardEditorNode`
- `QuestReachabilityHint`

API changes:

- `GET /authoring/worlds/{world_id}/quests/graph/pro`
- `POST /authoring/worlds/{world_id}/quests/graph/pro/preview`
- `POST /authoring/worlds/{world_id}/quests/graph/pro/validate`
- `PUT /authoring/worlds/{world_id}/quests/graph/pro`

Frontend changes:

- Add node-level forms for stages/triggers/rewards.
- Show missing refs, unreachable stages, hidden quest visibility risks, and
  completion paths.

Tests:

- Invalid stage refs block save.
- Hidden quests do not appear in player visible quest state until rules reveal
  them.
- Quest edits do not complete or activate runtime quests.

Acceptance:

- Quest graph edits round-trip to valid `quests.yaml` and pass quest analysis.

Content schema impact: likely none; optional editor layout metadata can be
stored separately or in authoring-only visual fields.

Save migration impact: deleted/renamed quest ids or stage ids require migration
risk warnings.

RP / knowledge / visibility impact: RP scenes may reference quest topics only
when visible/known.

LLM boundary impact: no quest outcome can be LLM-decided.

Leak risk: high if hidden quest descriptions enter player summaries or RP
prompts. Editor diagnostics must stay authoring-only.

### 8. NPC Relationship Graph Editing

Goal: Provide visual editing for NPC/player/NPC relationship edges, tone
metadata, visibility, and authoring diagnostics.

Data structures:

- `RelationshipGraphPro`
- `RelationshipEditorNode`
- `RelationshipEditorEdge`
- `RelationshipTonePreview`

API changes:

- `GET /authoring/worlds/{world_id}/relationships/pro`
- `POST /authoring/worlds/{world_id}/relationships/pro/preview`
- `POST /authoring/worlds/{world_id}/relationships/pro/validate`
- `PUT /authoring/worlds/{world_id}/relationships/pro`

Frontend changes:

- Add relationship graph editor with node filters, edge forms, tone preview,
  hidden-edge warnings, and RP dialogue impact preview.

Tests:

- Hidden relationships remain absent from player relationship APIs.
- Relationship save validates NPC refs and visibility.
- Editor changes do not modify runtime relationship values in active sessions.

Acceptance:

- Relationship YAML round-trips and player graph filtering remains correct.

Content schema impact: additive optional tone hints only if needed; canonical
relationship numbers remain existing schema.

Save migration impact: warn when relationship ids are deleted/renamed.

RP / knowledge / visibility impact: tone previews must use safe summaries and
not disclose hidden relationship details.

LLM boundary impact: no LLM relationship updates.

Leak risk: high for hidden relationships and private RP context. Keep player
graphs filtered.

### 9. Faction Conflict Editor

Goal: Add a dedicated visual editor for faction relationships, conflict levels,
alert levels, resources, visibility, and consequence links.

Data structures:

- `FactionConflictGraphPro`
- `FactionConflictNode`
- `FactionConflictEdge`
- `FactionConflictIncidentDraft`

API changes:

- `GET /authoring/worlds/{world_id}/factions/conflicts/pro`
- `POST /authoring/worlds/{world_id}/factions/conflicts/pro/preview`
- `POST /authoring/worlds/{world_id}/factions/conflicts/pro/validate`
- `PUT /authoring/worlds/{world_id}/factions/conflicts/pro`

Frontend changes:

- Add faction conflict graph with public/debug visibility mode, edge severity,
  conflict tags, reputation bands, and incident preview.

Tests:

- Hidden factions/conflicts stay out of player faction graph.
- Conflict tags in player outputs remain safe or are redacted if marked hidden.
- Save validates faction refs.

Acceptance:

- Faction conflict edits pass validation and do not mutate active runtime
  faction state.

Content schema impact: may add `public_label` or `player_safe_conflict_label`
to reduce tag leakage risk.

Save migration impact: warn on deleted/renamed faction ids.

RP / knowledge / visibility impact: NPC dialogue can mention faction conflict
only if known by NPC and visible to player context.

LLM boundary impact: no LLM-decided diplomacy or conflict outcomes.

Leak risk: high due `conflict_tags`; v1.2 should prefer player-safe labels.

### 10. Rumor / Crime Consequence Graph Pro

Goal: Expand social consequence graph editing for rumor spread, crimes,
witnesses, faction effects, quest triggers, and safe public text.

Data structures:

- `RumorCrimeGraphPro`
- `RumorEditorNode`
- `CrimeConsequenceEditorNode`
- `WitnessRulePreview`
- `SocialConsequenceEdge`

API changes:

- `GET /authoring/worlds/{world_id}/rumor-crime/pro`
- `POST /authoring/worlds/{world_id}/rumor-crime/pro/preview`
- `POST /authoring/worlds/{world_id}/rumor-crime/pro/validate`
- `PUT /authoring/worlds/{world_id}/rumor-crime/pro`

Frontend changes:

- Add consequence chain visualization.
- Show hidden fact linkage warnings and player-safe rumor text preview.

Tests:

- Rumor text linked to hidden facts is blocked or warned when it reveals hidden
  fact text.
- Hidden witnesses stay out of player API and narrator prompt.
- Saves write only content YAML after gate pass.

Acceptance:

- Social consequence graph edits validate and pass hidden-leak checks.

Content schema impact: may add explicit `player_safe_summary` for consequence
nodes.

Save migration impact: warn on deleted rumor/crime/faction/quest refs.

RP / knowledge / visibility impact: NPCs may discuss rumors only if they know
them; player-facing text must use safe rumor fields.

LLM boundary impact: no LLM-decided crime/witness/social consequences.

Leak risk: very high around hidden witnesses and hidden fact-linked rumors.

### 11. Item / Economy Visual Editor Pro

Goal: Improve item, container, merchant, shop inventory, price, rarity, and
trade flag editing with economy sanity checks.

Data structures:

- `ItemEconomyGraphPro`
- `ItemEditorNode`
- `MerchantEditorNode`
- `ContainerEdge`
- `EconomyBalancePreview`

API changes:

- `GET /authoring/worlds/{world_id}/economy/pro`
- `POST /authoring/worlds/{world_id}/economy/pro/preview`
- `POST /authoring/worlds/{world_id}/economy/pro/validate`
- `PUT /authoring/worlds/{world_id}/economy/pro`

Frontend changes:

- Add item graph by location/owner/container.
- Add merchant inventory editor, price warnings, hidden item badges, and
  balance summary.

Tests:

- Hidden items remain absent from player visible state until discovered.
- Invalid ownership cycles block save.
- Economy balance blockers cannot be ignored.

Acceptance:

- Economy edits round-trip and pass validation/balance sanity checks.

Content schema impact: likely additive optional authoring metadata only.

Save migration impact: warn on deleted/renamed item ids and merchant refs.

RP / knowledge / visibility impact: NPCs cannot mention hidden inventory unless
knowledge and visibility rules allow it.

LLM boundary impact: no LLM pricing or trade outcomes.

Leak risk: medium/high for hidden shop inventory and secret items.

### 12. RP Character Authoring UI Pro

Goal: Provide a visual RP character editor for public persona, voice profile,
safe example dialogue refs, emotional defaults, boundaries, and private fields.

Data structures:

- `RPCharacterAuthoringProfile`
- `RPCharacterFieldVisibility`
- `VoiceProfileEditor`
- `RPPrivateFieldReview`

API changes:

- `GET /authoring/worlds/{world_id}/rp/characters/pro`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/preview`
- `POST /authoring/worlds/{world_id}/rp/characters/pro/validate`
- `PUT /authoring/worlds/{world_id}/rp/characters/pro`

Frontend changes:

- Add character profile editor with public/private/debug field separation.
- Add safe prompt preview that omits `private_self_summary`.
- Add example dialogue picker.

Tests:

- Private RP fields do not enter player-facing context.
- Unsafe prompt-control text is rejected or quarantined.
- Character profile saves validate content pack schema.

Acceptance:

- Creator can edit RP profile/voice data safely and preview prompt-safe fields.

Content schema impact: additive RP fields already exist; v1.2 may add
authoring-only labels or field visibility metadata.

Save migration impact: none unless NPC ids change.

RP / knowledge / visibility impact: direct impact; must preserve private-field
and NPC knowledge boundaries.

LLM boundary impact: profiles can change style only.

Leak risk: very high around `private_self_summary`, taboo topics, and imported
prompt text.

### 13. Dialogue Scene Editor

Goal: Let creators author reusable dialogue scene drafts, topics, allowed
participants, visible fact requirements, mood presets, and safety notes.

Data structures:

- `DialogueSceneTemplate`
- `DialogueSceneDraft`
- `DialogueTopicRule`
- `DialogueSceneRequirement`
- `DialogueSceneSafetyPolicy`

API changes:

- `GET /authoring/worlds/{world_id}/dialogue-scenes`
- `POST /authoring/worlds/{world_id}/dialogue-scenes/preview`
- `POST /authoring/worlds/{world_id}/dialogue-scenes/validate`
- `PUT /authoring/worlds/{world_id}/dialogue-scenes`

Frontend changes:

- Add dialogue scene editor with topic list, participant selector, mood selector,
  required visible facts, and prompt-safe preview.

Tests:

- Scene drafts do not start active dialogue sessions unless explicitly invoked
  through game APIs.
- Required hidden facts cannot be required for player-facing scenes unless
  visibility rules allow discovery.
- Dialogue scene events at runtime still record `Event`.

Acceptance:

- Dialogue scene content can be authored and validated without runtime mutation.

Content schema impact: new optional `dialogue_scenes.yaml` or templates under
`templates/rp`.

Save migration impact: none for runtime saves.

RP / knowledge / visibility impact: scene requirements must respect player and
NPC knowledge.

LLM boundary impact: scene templates do not generate authoritative facts.

Leak risk: high around topic names and required hidden facts.

### 14. Group RP Scene Authoring

Goal: Add authoring support for group scene drafts, participant roles, turn
order hints, conflict/tension cues, shared topics, and per-NPC context checks.

Data structures:

- `GroupRPSceneTemplate`
- `GroupRPParticipantRole`
- `GroupRPSceneDraft`
- `ParticipantKnowledgePreview`

API changes:

- `GET /authoring/worlds/{world_id}/group-rp-scenes`
- `POST /authoring/worlds/{world_id}/group-rp-scenes/preview`
- `POST /authoring/worlds/{world_id}/group-rp-scenes/validate`
- `PUT /authoring/worlds/{world_id}/group-rp-scenes`

Frontend changes:

- Add group scene canvas with participant lanes, role badges, scene mood, and
  per-participant knowledge preview.

Tests:

- Participant contexts remain isolated.
- NPC A's hidden knowledge cannot appear in NPC B's prompt.
- Dead/incapacitated NPCs cannot be marked ordinary participants without an
  explicit validation warning/blocker.

Acceptance:

- Group scene drafts validate and can be applied only through runtime rules.

Content schema impact: new optional group scene template content.

Save migration impact: none.

RP / knowledge / visibility impact: direct high impact; per-NPC knowledge
filtering is mandatory.

LLM boundary impact: no autonomous LLM multi-agent state changes.

Leak risk: very high due cross-NPC context contamination.

### 15. Character Pack Builder

Goal: Package NPC RP profiles, voice profiles, example dialogue, lorebook
flavor, safe character exports, and metadata into local character packs.

Data structures:

- `CharacterPackManifest`
- `CharacterPackEntry`
- `CharacterPackExportMode`
- `CharacterPackImportPreview`

API changes:

- `POST /authoring/character-packs/preview`
- `POST /authoring/character-packs/export`
- `POST /authoring/character-packs/import/preview`
- `POST /authoring/character-packs/import/apply`

Frontend changes:

- Add pack builder wizard with safe export mode, private-field review, and
  import classification report.

Tests:

- Safe export excludes credentials, save data, runtime state, hidden facts, NPC
  secrets, private summaries, and raw debug data.
- Import does not auto-write active worlds.
- Archive validation rejects executable files and path traversal.

Acceptance:

- Creator can build a local safe character pack and import it only through
  preview/validation/explicit apply.

Content schema impact: package manifest schema, not core world schema.

Save migration impact: none.

RP / knowledge / visibility impact: imported fields remain candidates until
saved as validated content.

LLM boundary impact: no imported prompt can widen authority.

Leak risk: high for private RP fields and hidden lore.

### 16. Template Wizard

Goal: Provide a guided UI for using world, quest, location, NPC, faction,
economy, mystery, combat, and RP templates.

Data structures:

- `TemplateWizardSession`
- `TemplateWizardStep`
- `TemplateVariableBinding`
- `TemplateRenderPreview`

API changes:

- `GET /authoring/templates/wizard`
- `POST /authoring/templates/wizard/preview`
- `POST /authoring/templates/wizard/validate`
- `POST /authoring/templates/wizard/apply`

Frontend changes:

- Add step-based wizard for selecting templates, variables, target world, diff
  review, and validation gate.

Tests:

- Template variables reject path traversal and unsafe output files.
- Apply requires confirmation and validation.
- Templates never execute scripts.

Acceptance:

- Users can apply templates safely to content files through explicit save flow.

Content schema impact: none unless new template types are introduced.

Save migration impact: warn on ids that conflict with existing saves.

RP / knowledge / visibility impact: RP templates must preserve visibility and
NPC knowledge requirements.

LLM boundary impact: no LLM required; optional future draft generation must be
authoring-only and schema-validated.

Leak risk: medium for templates containing hidden topics in public fields.

### 17. Local Content Library

Goal: Add a local library for reusable worlds, snippets, characters, templates,
scene drafts, icons, references, and packs.

Data structures:

- `LocalContentLibraryItem`
- `LibraryItemType`
- `LibraryItemManifest`
- `LibraryImportPreview`

API changes:

- `GET /authoring/library`
- `POST /authoring/library/import/preview`
- `POST /authoring/library/import/apply`
- `POST /authoring/library/export`
- `DELETE /authoring/library/{item_id}`

Frontend changes:

- Add library browser with filters, safe preview, import/export actions, and
  validation status.

Tests:

- Library cannot read arbitrary system files.
- Disallowed files are rejected.
- Library import cannot auto-overwrite worlds.

Acceptance:

- Local content can be reused without weakening import/export safety.

Content schema impact: library manifests outside core world packs.

Save migration impact: none.

RP / knowledge / visibility impact: library preview marks hidden/private fields
clearly.

LLM boundary impact: none.

Leak risk: high if library previews expose private/hidden data in shareable
exports.

### 18. Visual Reference Picker System

Goal: Provide safe pickers for locations, NPCs, items, quests, facts, factions,
relationships, rumors, scene moods, example dialogue, templates, and packages.

Data structures:

- `ReferencePickerIndex`
- `ReferencePickerItem`
- `ReferenceScope`
- `ReferenceVisibility`

API changes:

- `GET /authoring/worlds/{world_id}/references`
- `GET /authoring/worlds/{world_id}/references/{kind}`

Frontend changes:

- Replace free-text refs in editors with searchable pickers.
- Show safe labels, visibility badges, and broken-ref status.

Tests:

- Player-safe picker mode does not include hidden-only labels.
- Authoring picker rejects arbitrary file/path refs.
- Broken refs are surfaced safely.

Acceptance:

- Pro editors share one reference picker with visibility-aware results.

Content schema impact: none.

Save migration impact: none.

RP / knowledge / visibility impact: pickers can show authoring-hidden data only
inside authoring tools.

LLM boundary impact: none.

Leak risk: medium/high depending on picker mode. Player-safe labels must be
separate from authoring labels.

### 19. Authoring Workflow Presets

Goal: Add reusable local workflows such as "new village quest", "add faction
conflict", "import character safely", "review hidden leaks", and "package for
backup".

Data structures:

- `AuthoringWorkflowPreset`
- `WorkflowStep`
- `WorkflowRequirement`
- `WorkflowRunSummary`

API changes:

- `GET /authoring/workflows`
- `POST /authoring/workflows/{workflow_id}/start`
- `POST /authoring/workflows/{workflow_id}/step`

Frontend changes:

- Add workflow sidebar with guided steps and progress.

Tests:

- Workflow steps cannot bypass validation or confirmation.
- Workflow output is safe summary only.
- Import/package workflows reject executable content.

Acceptance:

- Presets guide creators through common tasks without adding hidden authority.

Content schema impact: workflow definitions live outside core world packs unless
exported as local templates.

Save migration impact: none.

RP / knowledge / visibility impact: workflow steps preserve existing RP and
visibility boundaries.

LLM boundary impact: no provider calls required.

Leak risk: medium if workflow summaries include hidden details.

### 20. World Branch Merge Assistant

Goal: Help compare, review, and merge local world branches with conflict
classification, semantic diffs, validation, and explicit apply.

Data structures:

- `WorldMergeRequest`
- `WorldMergePreview`
- `WorldMergeConflict`
- `WorldMergeResolution`
- `WorldMergeApplyResult`

API changes:

- `POST /authoring/worlds/{world_id}/branches/merge/preview`
- `POST /authoring/worlds/{world_id}/branches/merge/validate`
- `POST /authoring/worlds/{world_id}/branches/merge/apply`

Frontend changes:

- Add merge assistant with branch selection, conflict list, semantic diff,
  resolution editor, gate result, and explicit apply.

Tests:

- Merge never auto-overwrites current world without confirmation.
- Merge output validates before writing.
- Conflicts involving hidden content are redacted in normal summaries.

Acceptance:

- Local branch merges are reviewable, validation-gated, and reversible through
  draft history.

Content schema impact: none.

Save migration impact: merge preview flags deleted/renamed ids that may affect
saves.

RP / knowledge / visibility impact: merge conflict summaries must keep private
RP fields and hidden facts local/authoring-only.

LLM boundary impact: no LLM merge decisions in v1.2. A future LLM assistant may
suggest text only as authoring draft.

Leak risk: high if merge reports expose hidden/private content.

## v1.2 Integration Test Requirements

The v1.2 integration suite should include:

- Pro boundary contract regression.
- Validation Gate blocks invalid visual saves.
- Draft history restore requires validation and does not touch active sessions.
- Content Diff Review redacts hidden text in normal reports.
- Project Dashboard omits raw `GameState`, raw `state_deltas`, API keys, local
  paths, and hidden text.
- Map Pro hidden locations/exits remain filtered from player APIs.
- Quest Pro edits do not activate or complete runtime quests.
- Relationship and faction Pro hidden edges remain filtered from player graphs.
- Rumor/crime Pro does not leak hidden witnesses or hidden fact text.
- Item/economy Pro hidden inventory stays hidden from player API.
- RP character Pro private fields stay out of player-facing context.
- Dialogue and Group RP authoring preserve NPC knowledge boundaries.
- Character Pack Builder safe export excludes private/hidden/runtime data.
- Template Wizard rejects unsafe variables and script-like outputs.
- Local Library rejects path traversal, executable files, `.env`, DB files, and
  logs.
- Reference Picker has separate authoring and player-safe modes.
- Workflow Presets cannot skip preview/validate/explicit save.
- Branch Merge Assistant writes only after validation and confirmation.
- Full `python -m pytest` passes.
- Frontend `npm.cmd run build` passes.

## v1.2 Final Acceptance Standards

v1.2 can be accepted when:

1. All implemented Pro editors use shared preview, validation, explicit save,
   and gate behavior.
2. No visual editor mutates active `GameState`.
3. Runtime state changes still use `StateDelta`.
4. Player actions, system ticks, NPC planning, and dialogue scene events still
   record `Event`.
5. Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden
   memory, raw `state_deltas`, private RP fields, API keys, local paths, and raw
   environment data stay out of player APIs, ordinary authoring summaries, and
   narrator/RP prompts.
6. Authoring/debug APIs remain local-only and clearly separated from player
   surfaces.
7. Import/export and local library flows reject executable content, path
   traversal, `.env`, DB files, logs, and secret files.
8. Content packages cannot bypass validation or Quality Gate.
9. Provider construction still goes through `provider_factory`.
10. `python -m pytest` passes.
11. `cd frontend && npm.cmd run build` passes.
12. v1.2 release notes, acceptance report, and boundary audit are created.

## v1.3 Candidate Directions

- Provider-backed NPC dialogue generation with mandatory RP consistency checks.
- Visual scene director tools for pacing, tension, and camera-like narrative
  structure without world authority.
- Stronger semantic classifiers for imported character/lorebook content.
- Memory-ingest validation for hidden fact bindings.
- Optional local image/reference asset management with safe local-only
  manifests.
- More sample worlds and Pro authoring tutorials.
- Component-level frontend tests for complex visual editors.
- Read-only local analytics for authoring productivity and world complexity.
- More advanced branch comparison and release packaging workflows.
- Optional LLM-assisted authoring suggestions that remain draft-only,
  schema-validated, and validation-gated.
