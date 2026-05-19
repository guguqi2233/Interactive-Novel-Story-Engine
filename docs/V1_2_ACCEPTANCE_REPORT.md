# v1.2 Acceptance Report: Visual Authoring Pro

## Verdict

Accepted for v1.2 release candidate.

v1.2 Visual Authoring Pro is accepted as a local, validation-gated authoring
layer on top of the v1.0 world engine and v1.1 RP layer. The implementation adds
visual authoring workflows for maps, quests, NPC relationships, faction
conflicts, rumor/crime consequences, item/economy data, RP characters, dialogue
scenes, group RP scenes, character packs, templates, branch merging, diff
review, workflow presets, local content library, project dashboard, reference
picker, draft history, and the shared Authoring Validation Gate.

The release preserves the core boundary:

Authoring drafts are content candidates. `GameState` remains runtime truth.

No v1.2 release blocker remains after fixing Template Wizard world-apply gate
coverage and normal-view redaction for merge/diff/reference/draft/library
surfaces.

## Verification Date

2026-05-19

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: passed, 998 tests.
- `cd frontend && npm.cmd run build`: passed, TypeScript build and Vite
  production build completed.

## Scope Accepted

### 1. Authoring Pro Boundary Contract

Accepted.

- `docs/AUTHORING_BOUNDARY.md` defines `authoring_draft`,
  `preview_result`, `validation_report`, `explicit_save`,
  `active_world_pack`, `active_game_state`, `migration_impact`,
  `hidden_authoring_field`, and `player_visible_content`.
- Preview and validate are documented and tested as read-only draft checks.
- Save writes content-pack files only and does not mutate active sessions.
- Applying authoring output to an active session is explicitly out of v1.2.

### 2. Authoring Validation Gate

Accepted.

- `AuthoringValidationGate` centralizes save/import/merge/apply checks.
- `ContentAuthoringService.write_file` and `write_files` call the gate before
  persisted content writes.
- Visual editor saves, merge save, import apply, template apply, and local
  duplicate paths are covered by gate tests.
- Validation errors block saves. Warnings require explicit confirmation. Hidden
  leak risks are blocked unless an explicit debug override is used.

### 3. Visual Map Editor Pro

Accepted.

- Map visual schema supports regions, layers, conditional/locked/hidden edges,
  travel cost, discovery rules, coordinates, and player-visible filtering.
- API supports graph read, preview, validate, save, impact analysis, and player
  map projection.
- Tests cover roundtrip, hidden edge filtering, locked-edge warnings, preview
  read-only behavior, invalid save blocking, and active `GameState` isolation.
- Frontend Map Editor supports node/edge editing, coordinates, edge types,
  validation issues, diff/impact preview, and hidden path markers.

### 4. Quest Graph Editor Pro

Accepted.

- Quest graph schema covers quest, stage, objective, trigger, reward,
  consequence, failure/optional edges, and hidden objective fields.
- Graph/YAML roundtrip is stable.
- API supports preview, validate, save, impact analysis, and scenario draft
  generation.
- Tests cover invalid triggers, unreachable stages, hidden objective filtering,
  scenario draft validity, preview read-only behavior, and active state
  isolation.

### 5. NPC Relationship Graph Editing

Accepted.

- Relationship authoring graph supports NPC nodes, relationship edges, hidden
  relationship fields, tone presets, and RP tone previews.
- Relationship and faction conflict editing are exposed through the social graph
  authoring flow.
- Tests cover roundtrip, invalid NPC refs, hidden relationship filtering, tone
  preview not mutating numeric relationship values, and validation-gated save.

### 6. Faction Conflict Editor

Accepted.

- Faction conflict graph supports faction metadata, alliance/hostility/conflict
  relations, alert/conflict levels, visibility fields, and conflict tags.
- Player-visible faction graph filters hidden faction conflicts.
- Tests cover invalid faction refs, duplicate relation handling, alert level
  validation, hidden conflict filtering, preview read-only behavior, and save
  gate behavior.

### 7. Rumor / Crime Consequence Graph Pro

Accepted.

- Consequence authoring graph supports trigger, witness, crime, rumor,
  reputation effect, NPC reaction, quest effect, delay/cooldown, and dedupe
  fields.
- Validation checks fact/faction/NPC/quest refs, hidden fact text leakage,
  loops, and missing dedupe warnings.
- Tests cover roundtrip, hidden leakage detection, missing refs, loop warnings,
  preview read-only behavior, and active `GameState` isolation.

### 8. Item / Economy Visual Editor Pro

Accepted.

- Item/economy authoring supports item nodes, merchant nodes, shop inventory
  edges, price modifiers, stolen item policy, quest reward links, price preview,
  and balance warnings.
- Tests cover graph roundtrip, invalid shop refs, hidden shop filtering,
  negative price validation, arbitrage warnings, preview read-only behavior, and
  frontend build compatibility.

### 9. RP Character Authoring UI Pro

Accepted.

- RP character authoring supports NPC base fields, RP profiles, voice profiles,
  default emotional state, example dialogue refs, lore links, mood preferences,
  import preview, validation, and safe export behavior.
- `private_self_summary`, unsafe imported prompt text, hidden facts, and unsafe
  example dialogue are excluded from player-facing context and safe exports.
- Tests cover roundtrip, private field filtering, unsafe prompt rejection,
  example dialogue filtering, safe export redaction, and preview read-only
  behavior.

### 10. Dialogue Scene Editor

Accepted.

- Dialogue scene templates support participants, focus NPC, location, dialogue
  mode, scene mood, opening context, allowed/forbidden topics, required visible
  facts, prompt profile selection, and possible outcomes.
- Validation catches missing participants/locations/facts, hidden forbidden
  topic promptability, and disallowed `StateDelta` outcome templates.
- Saves write template content only and do not start or mutate active
  `DialogueSession`.

### 11. Group RP Scene Authoring

Accepted.

- Group scene templates support scene type, participants, required roles,
  location, turn-order policy, speaker selection policy, mood, tension, topics,
  and exit conditions.
- Validation catches missing participants, dead-participant policy violations,
  missing required roles, hidden opening context leakage, and invalid turn order.
- Saves do not start active group scenes or modify runtime dialogue state.

### 12. Character Pack Builder

Accepted.

- Character packs include characters, RP profiles, voice profiles, example
  dialogue, dialogue scene templates, group scene templates, flavor lore, and
  optional fact candidates.
- Export includes a manifest. Import dry-run is read-only. Import apply requires
  explicit confirmation and validation.
- Safe export excludes hidden facts and API keys. Executable files, path
  traversal, scripts, remote URLs, and hidden-fact default import are rejected.

### 13. Template Wizard

Accepted.

- Template Wizard supports world, location cluster, questline, NPC set,
  character pack, dialogue scene, group RP scene, faction conflict, and mystery
  case draft types.
- Preview and validate do not write disk.
- Apply requires explicit confirmation and validation.
- New world apply now goes through `AuthoringValidationGate` before writing
  content, and failed gated apply writes nothing.
- Template generation is deterministic and does not call an LLM or execute
  scripts.

### 14. World Branch Merge Assistant

Accepted.

- Merge Assistant detects same-entity changes, delete/change conflicts, id
  collisions, hidden visibility mismatches, quest graph conflicts, relationship
  conflicts, and RP profile conflicts.
- Preview is read-only. Save requires explicit confirmation, validation, and
  gate approval.
- Normal conflict payloads are redacted so hidden/private entity details do not
  appear in ordinary authoring views.
- Active `GameState` is not modified by merge preview or save.

### 15. Content Diff Review

Accepted.

- Diff Review supports file, entity, graph, package, schema, visibility, and RP
  profile diff summaries.
- Output includes added/removed/changed entities, rename candidates, visibility
  risks, migration impact, and validation issue codes.
- Normal view redacts hidden entity details and avoids arbitrary validation
  messages that could carry hidden text.
- Path traversal is rejected, temporary materialization is cleaned up, and no
  active state is modified.

### 16. Authoring Workflow Presets

Accepted.

- Workflow presets cover new world, new questline, new character pack, new RP
  scene, new mystery case, pre-release check, import review, and branch merge
  review.
- Presets contain steps, required tools, validation gates, suggested templates,
  and quality checks.
- Workflow steps invoke existing editors/APIs and do not implement a new
  privileged workflow engine.

### 17. Local Content Library

Accepted.

- Local Content Library lists, inspects, validates, imports, exports, archives,
  and duplicates supported local content categories.
- Path traversal is rejected. Sensitive paths are not shown in frontend
  metadata. `.env`, API keys, scripts, and root-outside reads are not allowed.
- Import does not modify active `GameState`.
- Duplicate world operations are validation-gated and roll back on gate block.

### 18. Authoring Project Dashboard

Accepted.

- Project summary API reports active world, active branch, recent edits,
  validation status, quality gate status, content counts, open warnings,
  migration impact, and package status.
- The summary does not return raw env, API keys, hidden fact text, or debug-only
  details.
- Frontend dashboard provides entry points to the v1.2 editor set.

### 19. Visual Reference Picker System

Accepted.

- ReferenceIndex supports location, NPC, item, fact, quest, quest stage,
  faction, relationship, rumor, crime type, RP profile, scene mood, and prompt
  profile references.
- Hidden references are marked and hidden labels are redacted by default.
- ReferenceIndex is authoring-only and is not exposed as a player API.
- Main editors use the shared `ReferencePicker` where appropriate.

### 20. Authoring Undo / Draft History

Accepted.

- Draft history supports snapshot creation, listing, restore, discard, and
  comparison.
- Snapshots store authoring draft content only, not active `GameState`.
- Restore does not write active content and still requires validation before
  save.
- Draft history rejects disallowed files and sensitive config/API-key markers.

### 21. v1.2 Integration Tests

Accepted.

- `test_v12_visual_authoring_pro_integration.py` verifies boundary behavior,
  visual editor roundtrips, RP authoring redaction, template/diff/merge/import
  flows, reference picker behavior, draft history, disabled API handling, and
  player API hidden-content isolation.
- Full regression coverage includes v1.0/v1.1 runtime, RP boundary evals,
  hidden info leak evals, save/load/migration tests, package import/export, and
  quality gate checks.

## Boundary Review

### Authoring Boundary

Accepted.

- `draft`, `preview`, `validate`, `save`, `apply`, active world pack, and active
  `GameState` boundaries are clear in docs and implementation.
- Preview and validation use temporary copies or in-memory drafts and are
  tested not to write disk.
- Saves use validation gate paths or equivalent explicit validation before
  writing content-pack files.
- Existing active sessions keep their current `GameState`; authoring edits do
  not mutate runtime state.

### Runtime World Authority

Accepted.

- The world engine remains the source of truth.
- Runtime state changes continue to use deterministic rules and `StateDelta`.
- Player actions, dialogue events, planning/tick systems, and save/load flows
  retain event logging and replay-oriented structure.
- v1.2 does not add an LLM world judge or any LLM direct state mutation path.

### LLM Boundary

Accepted.

- v1.2 visual authoring modules do not call LLM providers to generate
  authoritative maps, quests, relationships, faction conflicts, consequences,
  prices, templates, merges, or diffs.
- Prompt/RP profiles do not widen LLM authority.
- Provider selection remains centralized through provider factory usage in
  runtime paths.
- Tests use mock, local stub, or fake providers and do not call real APIs.

### Visibility / RP Boundary

Accepted.

- Hidden facts, NPC secrets, hidden witnesses, debug memory, hidden
  relationships, hidden faction conflicts, hidden map edges, hidden shop items,
  raw `state_deltas`, and RP private fields are filtered from player APIs and
  ordinary narrator/RP prompts.
- RP `private_self_summary` and unsafe imported prompt text remain
  authoring/private data.
- Normal authoring reports for merge, diff, reference index, dashboard, and
  gate output use redacted or structural summaries for hidden/private data.

### Security / Import / Package Boundary

Accepted.

- Authoring APIs are controlled by `ENABLE_AUTHORING_API`; debug APIs are
  controlled by `ENABLE_DEBUG_API`.
- Import/export rejects path traversal and executable content.
- Templates and packages do not execute arbitrary code or read remote URLs.
- Character pack safe export excludes hidden facts and API keys.
- Local content library operations use safe IDs/root checks and do not read
  outside configured roots.

## Known Limitations

- v1.2 is local single-user authoring only. It does not include cloud sync,
  accounts, hosted collaboration, or online marketplace behavior.
- Applying authoring changes into an already-running active session is not part
  of v1.2 and remains blocked by design.
- Template Wizard uses deterministic starter templates; it does not provide LLM
  content generation or automatic world repair.
- Visual editors do not implement complex automatic layout, full Git semantics,
  large-scale simulation, or multi-user conflict resolution.
- Save archives can contain full runtime state by design and should be treated
  as sensitive local backup artifacts.
- `ENABLE_DEBUG_API` remains suitable for local development/self-hosted use, but
  should be disabled in any shared or exposed environment.

## Acceptance Risks

- Normal authoring/debug views remain powerful local tools. They are gated, but
  future UI additions must preserve the redacted normal-view contract.
- The older side quest generator can use an injected `LLMProvider` for assisted
  drafts. It is not part of v1.2 Visual Authoring Pro save paths; any future
  wiring must keep it draft-only and validation-gated.
- Content schema growth increases migration surface. v1.2 reports migration
  impact but does not automatically migrate old saves after content edits.
- The frontend currently relies on build-level verification and backend
  integration tests rather than a broad component-test suite.

## Recommended v1.3 Priorities

1. Formalize spoiler-safe normal authoring response models separately from
   debug authoring response models.
2. Add more frontend component and interaction tests for disabled API states,
   ReferencePicker behavior, validation issue navigation, and hidden-content
   badges.
3. Design an explicit, deterministic active-session apply workflow if runtime
   application of authoring changes is desired; it must use `StateDelta` and
   `Event`.
4. Improve save/content migration tooling for worlds edited heavily through
   Visual Authoring Pro.
5. Expand Quality Gate integration with editor-specific issue navigation and
   release checklist automation.
6. Keep LLM-assisted authoring, if added later, strictly draft-only with no
   direct save or `GameState` authority.

## Final Status

v1.2 Visual Authoring Pro is accepted for release candidate status.

All required v1.2 modules are implemented and covered by deterministic tests.
The backend regression suite and frontend production build pass. The release
preserves the v1.0/v1.1 authority model: the LLM remains a language layer, the
world engine remains the fact source, all runtime state changes remain governed
by rules and `StateDelta`, authoring drafts do not modify active `GameState`,
and hidden/private content remains filtered from player-facing APIs and ordinary
RP/narrator prompts.
