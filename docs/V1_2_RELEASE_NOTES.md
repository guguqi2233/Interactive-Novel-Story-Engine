# v1.2 Release Notes: Visual Authoring Pro

## Version Name

v1.2 Visual Authoring Pro

## Version Goal

v1.2 turns the local interactive-fiction engine's authoring surface into a more
complete local studio workflow. It adds visual and structured tools for editing
world content packs, reviewing drafts, validating changes, packaging reusable
content, and managing local authoring projects.

This remains a local self-use engine and studio. The LLM is still a language
layer, not the world judge. The world engine remains the fact source, and
runtime state changes still go through deterministic rules, `StateDelta`, and
`Event`.

Visual Authoring Pro edits content packs and authoring drafts. It does not
directly modify active `GameState` or live sessions.

## New Features

### Authoring Boundary And Validation

- Added the Authoring Pro Boundary Contract in `docs/AUTHORING_BOUNDARY.md`.
- Added `AuthoringValidationGate` for shared save/import/merge/apply checks.
- Added clear concepts for authoring drafts, preview results, validation
  reports, explicit save, active world pack, active `GameState`, migration
  impact, hidden authoring fields, and player-visible content.
- Added validation-gated save behavior across primary v1.2 editor paths.
- Added hidden leak risk detection that blocks or requires explicit handling
  before save.

### Visual Editors

- Visual Map Editor Pro:
  regions, layers, node coordinates, locked/hidden/conditional/one-way edges,
  travel cost, discovery rules, validation, player-visible map projection, and
  diff/impact preview.
- Quest Graph Editor Pro:
  quest/stage/objective/trigger/reward/consequence nodes, failure and optional
  paths, hidden objective fields, stable graph/YAML roundtrip, validation, and
  scenario regression draft generation.
- NPC Relationship Graph Editing:
  NPC nodes, relationship edges, trust/fear/affinity/obligation/hostility
  fields, hidden relationship flags, tone presets, and RP tone previews.
- Faction Conflict Editor:
  faction metadata, alliance/hostility/conflict edges, alert/conflict levels,
  visibility fields, and conflict tags.
- Rumor / Crime Consequence Graph Pro:
  trigger, witness, crime, rumor, reputation effect, NPC reaction, quest effect,
  delay/cooldown, dedupe keys, loop checks, and hidden fact leak checks.
- Item / Economy Visual Editor Pro:
  items, merchants, shop inventory links, price modifiers, stolen item policy,
  quest reward links, price preview, and balance warnings.

### RP Authoring

- RP Character Authoring UI Pro:
  NPC base fields, RP profile, voice profile, default emotional state, example
  dialogue refs, lore links, mood preferences, import preview, validation, and
  safe export behavior.
- Dialogue Scene Editor:
  dialogue scene templates with participants, focus NPC, location, dialogue
  mode, scene mood, opening context, allowed/forbidden topics, required visible
  facts, prompt profile, and possible outcomes.
- Group RP Scene Authoring:
  group scene templates with participants, required roles, turn order, speaker
  policy, mood, tension, topics, and exit conditions.
- Character Pack Builder:
  local export/import dry-run/import apply for reusable character packs.

RP authoring does not expand LLM authority. Imported prompt-like material is
classified and filtered; `private_self_summary`, hidden facts, unsafe examples,
and other private fields do not enter player-facing context by default.

### Content Workflow

- Template Wizard for deterministic starter drafts:
  world, location cluster, questline, NPC set, character pack, dialogue scene,
  group RP scene, faction conflict, and mystery case templates.
- World Branch Merge Assistant:
  conflict detection, explicit resolution choices, preview, validate, and
  validation-gated save.
- Content Diff Review:
  file/entity/graph/package/schema/visibility/RP profile summaries with
  migration impact and validation issue codes.
- Authoring Workflow Presets:
  reusable local flows for new worlds, questlines, character packs, RP scenes,
  mystery cases, pre-release checks, import review, and branch merge review.
- Local Content Library:
  list, inspect, validate, import, export, archive, and duplicate local content
  types.
- Authoring Project Dashboard:
  active world/branch, recent edits, validation status, quality gate summary,
  content counts, open warnings, migration impact, and package status.
- Visual Reference Picker System:
  shared reference index and picker for locations, NPCs, items, facts, quests,
  quest stages, factions, relationships, rumors, crime types, RP profiles,
  scene moods, and prompt profiles.
- Authoring Undo / Draft History:
  local draft snapshots, list, restore, discard, and compare.

Draft History is a local recovery aid. It is not a Git replacement and does not
provide branching, commits, remote history, or collaboration.

## Behavior Changes

- Visual editor save paths now require validation before writing content pack
  files.
- Validation errors block save. Validation warnings require explicit
  confirmation.
- Hidden leak risks are blocked by the authoring validation gate unless handled
  through explicit debug-only behavior.
- Preview and validate operations remain read-only and do not write disk.
- Authoring save writes content pack files only; it does not mutate active
  `GameState`, active saves, event logs, active dialogue sessions, or active
  group RP scenes.
- Merge previews are read-only. Merge save requires explicit confirmation and
  validation gate approval.
- Template Wizard apply requires explicit confirmation and validation. New
  world apply goes through the validation gate before writing files.
- Normal authoring views now use redacted or structural summaries for
  hidden/private merge, diff, reference, dashboard, and gate data.
- Hidden authoring fields default to authoring-only behavior and do not enter
  player UI.

## API Changes

v1.2 adds or extends local authoring APIs behind `ENABLE_AUTHORING_API`.
Representative endpoints include:

- `GET /authoring/pro/boundary`
- `POST /authoring/pro/boundary/check`
- `GET /authoring/worlds/{world_id}/map-graph`
- `POST /authoring/worlds/{world_id}/map-graph/preview`
- `POST /authoring/worlds/{world_id}/map-graph/validate`
- `POST /authoring/worlds/{world_id}/map-graph/save`
- `GET /authoring/worlds/{world_id}/quest-graph`
- `POST /authoring/worlds/{world_id}/quest-graph/preview`
- `POST /authoring/worlds/{world_id}/quest-graph/validate`
- `POST /authoring/worlds/{world_id}/quest-graph/save`
- Social graph endpoints for relationships and faction conflicts.
- Item/economy, rumor/crime, RP character, dialogue scene, and group RP scene
  preview/validate/save endpoints.
- `POST /authoring/character-packs/export`
- `POST /authoring/character-packs/import-dry-run`
- `POST /authoring/character-packs/import-apply`
- `POST /authoring/template-wizard/preview`
- `POST /authoring/template-wizard/validate`
- `POST /authoring/template-wizard/apply`
- `POST /authoring/worlds/{world_id}/merge/preview`
- `POST /authoring/worlds/{world_id}/merge/validate`
- `POST /authoring/worlds/{world_id}/merge/save`
- `POST /authoring/diff/review`
- `GET /authoring/worlds/{world_id}/references`
- `GET /authoring/drafts`
- `POST /authoring/drafts/snapshot`
- `POST /authoring/drafts/compare`
- `POST /authoring/drafts/{draft_id}/restore`
- `DELETE /authoring/drafts/{draft_id}`
- `GET /authoring/project-summary`
- `GET /library/items`
- `GET /library/items/{id}`
- `POST /library/items/{id}/validate`
- `POST /library/import`
- `POST /library/export`
- `POST /library/duplicate`

Authoring and library APIs are local tools. Player APIs do not expose
ReferenceIndex, draft history, authoring graph payloads, raw state deltas, or
hidden authoring fields.

## Frontend Changes

- Added/expanded Authoring Project Dashboard.
- Added Visual Map Editor Pro UI with node/edge editing, edge type controls,
  validation output, hidden path indicators, and diff/impact preview.
- Added Quest Graph Editor Pro UI with graph editing, hidden/optional/failure
  path markers, validation issue location, and scenario draft generation.
- Added social graph UI for NPC relationships and faction conflicts.
- Added Rumor / Crime Consequence Graph Pro panel.
- Added Item / Economy Pro panel with table and graph-oriented workflows,
  merchant inventory editing, price preview, and balance warnings.
- Added RP Character Editor, Dialogue Scene Editor, and Group RP Scene
  Authoring panels.
- Added Character Pack Builder, Template Wizard, Merge Assistant, Diff Review,
  Local Content Library, Workflow Launcher, ReferencePicker, and Draft History
  UI.
- Disabled authoring API states are handled safely.
- Player UI remains separate from authoring-only hidden content.

## Content Pack / Package Format Changes

v1.2 extends content authoring support for:

- Map visual graph metadata:
  regions, layers, conditional edges, locked edges, hidden edges, travel cost,
  discovery rules, and coordinates.
- Quest graph authoring metadata:
  richer node/edge types, hidden objective fields, rewards, consequences,
  failure paths, and optional paths.
- Relationship and faction conflict data:
  hidden relationship flags, tone presets, faction visibility, alert/conflict
  levels, and conflict tags.
- Rumor/crime consequence graph data:
  triggers, witnesses, crimes, rumors, reputation effects, NPC reactions, quest
  effects, delay/cooldown, and dedupe keys.
- Item/economy data:
  merchant inventory, price modifiers, stolen item policy, quest reward links,
  and balance-check metadata.
- RP character authoring data:
  RP profile, voice profile, emotional defaults, example dialogue refs, lore
  links, and mood preferences.
- Dialogue and group RP scene template files.
- Character Pack manifests.
- Template Wizard generated content.
- Local draft history metadata outside published content.

Content packages cannot bypass validation or Quality Gate expectations.
Character Pack, Template, Import, and Package flows do not execute arbitrary
code and do not read remote URLs as authoring assets.

## Authoring Workflow Changes

- Authoring now follows a unified flow:
  draft -> preview -> validate -> explicit save.
- Preview does not write disk.
- Validate does not write disk.
- Save writes validated content pack files only.
- Warnings require confirmation.
- Hidden leak risks block or require explicit debug handling.
- Merge Assistant helps detect and present conflicts, but it does not
  automatically solve every conflict.
- Local Content Library operations remain local and explicit.
- Draft History provides local snapshot/restore for drafts, but it is not a Git
  substitute.

## Testing / Validation Changes

- Added v1.2 integration regression tests covering authoring boundary, visual
  editor roundtrips, RP authoring redaction, template/diff/merge/import flows,
  reference picker, draft history, disabled authoring API, and player API hidden
  content isolation.
- Added targeted tests for Map, Quest, Social/Faction, Rumor/Crime,
  Item/Economy, RP Character, Dialogue Scene, Group RP Scene, Character Pack,
  Template Wizard, Merge, Diff Review, Workflow Presets, Local Content Library,
  Project Dashboard, ReferenceIndex, Draft History, and Validation Gate.
- Full backend regression status at acceptance:
  `python -m pytest` passed with 998 tests.
- Frontend acceptance status:
  `cd frontend && npm.cmd run build` passed.
- Tests use mock/local/fake providers and do not call real APIs.

## Known Limitations

- v1.2 is local single-user authoring only.
- No online marketplace, cloud sync, accounts, hosted collaboration, or
  multi-user authoring.
- Visual editors do not realtime-modify a running world or active session.
- Applying authoring changes directly into an active session is out of scope.
- Template Wizard uses deterministic starter templates and does not call an LLM
  to generate content.
- Visual editors do not include complex automatic layout, full Git semantics,
  large-scale simulation, or automatic world repair.
- Merge Assistant detects conflicts and supports explicit choices, but it does
  not automatically resolve all conflicts.
- Draft History is local snapshot recovery, not Git.
- Save archives can contain full runtime state by design and should be treated
  as sensitive local backup artifacts.
- `ENABLE_DEBUG_API` is intended for local development/self-hosted use and
  should be disabled in shared or exposed environments.

## Upgrade Notes From v1.1

- Existing v1.1 worlds remain compatible with the runtime model.
- New v1.2 authoring fields are content-pack/editor metadata and should be
  introduced through preview, validate, and explicit save.
- Existing active sessions do not automatically pick up authoring edits. Restart
  or reload through normal runtime flows to use changed content.
- Authoring APIs are disabled unless `ENABLE_AUTHORING_API` is enabled.
- Debug APIs remain controlled by `ENABLE_DEBUG_API`.
- Review `.env.example` for new local studio paths and flags:
  `ENABLE_AUTHORING_API`, `ENABLE_DEBUG_API`, `ENABLE_EVAL_API`,
  `ENABLE_PLAYTEST_API`, `LLM_PROVIDER`, `LOCAL_LLM_BASE_URL`, `DATABASE_URL`,
  `VITE_API_BASE_URL`, `AUTHORING_ROOT`, `TEMPLATE_ROOT`, and
  `PACKAGE_IMPORT_ROOT`.
- Content pack changes that delete or rename ids can affect old saves. v1.2
  reports migration impact but does not automatically migrate saves after every
  content edit.
- Character packs and templates are imported as local authoring content. They do
  not execute scripts and do not automatically overwrite active worlds.

## Recommended v1.3 Direction

1. Separate spoiler-safe normal authoring response models from debug authoring
   response models more formally.
2. Add broader frontend component and interaction tests for disabled API states,
   ReferencePicker behavior, validation navigation, and hidden-content badges.
3. Design an explicit active-session apply workflow, if desired, using
   deterministic rules, `StateDelta`, and `Event`.
4. Improve save/content migration tooling for worlds edited heavily through
   Visual Authoring Pro.
5. Expand Quality Gate integration with editor-specific issue navigation and
   release checklist automation.
6. Keep any future LLM-assisted authoring draft-only, provider-factory based,
   validation-gated, and unable to directly save or mutate `GameState`.
