# v3.4 Roadmap: Authoring / Mod UI Pro

## Version Goal

v3.4 turns Authoring Studio, Content Pack workflows, Script Pack workflows,
Mod Platform review, and Quality Gate surfaces into a daily-use local creation
workspace. The release focuses on safer and clearer local creation of world
packs, script packs, character packs, quest graphs, location maps, NPCs,
factions, relationships, items, economy/trade data, rumors, crime consequences,
Action Mods, Rule Module contracts, local module review, permissions,
compatibility, certification, import/export, Mod Quality Gate, authoring
validation, diff/preview/dry-run, audit trail, backup/restore, and safe local
apply.

v3.4 remains local-first and engine-boundary-first. Authoring output is a draft,
content-pack candidate, package candidate, or proposal until validated and
explicitly applied to local content files. Authoring UI cannot directly modify
active `GameState`, cannot bypass validation, cannot execute arbitrary code,
and cannot turn LLM output into world authority.

## Non-Goals

v3.4 explicitly does not implement:

- online marketplace;
- remote package auto-download;
- account system;
- cloud sync;
- multi-user collaborative editing;
- arbitrary code plugins;
- execution of mod Python / JavaScript;
- direct Authoring UI mutation of active `GameState`;
- Authoring UI bypass of validation, dry-run, quality gates, or explicit
  confirmation;
- Action Mod bypass of `ActionRegistry`;
- Rule Module runtime code execution;
- Provider Profile Pack storage of real API keys;
- normal authoring UI leakage of hidden facts, NPC secrets, debug memory, raw
  prompts, raw env, provider secrets, API keys, or raw `state_deltas`;
- automatic application of authoring drafts into World content;
- LLM-based content safety judgment or LLM world-fact judgment.

## Hard Constraints

- Local-first behavior is mandatory.
- Authoring outputs are drafts / content-pack candidates / package candidates /
  proposals by default.
- Applying to `worlds/`, content packs, packages, or project scripts requires
  validation, dry-run or preview, and explicit confirmation.
- Active `GameState` changes only through World Engine runtime flows,
  `StateDelta`, and `EventLog`.
- Authoring UI must not directly write active `GameState`.
- Mod UI must not execute arbitrary code.
- Action Mods remain declarative and must flow through `ActionRegistry`,
  `StateDelta`, and `EventLog` when used at runtime.
- Rule Modules are contracts and manifests only in this scope; they do not
  execute runtime code.
- Import/export must filter `.env`, API keys, provider secrets, databases, logs,
  caches, build artifacts, hidden/debug data, and unsafe paths.
- Provider Profile Packs may contain `api_key_env` / `secret_ref` only, never
  raw keys.
- Hidden/debug/private data must be filtered from normal UI.
- Dangerous operations require explicit confirmation.
- New pages must support loading, empty, error, and disabled states.
- `python -m pytest` must pass.
- `cd frontend && npm.cmd run build` must pass.

## Recommended Development Order

1. Authoring / Mod UI Contract Review.
2. Authoring Workspace Layout Pro.
3. Authoring Validation Dashboard.
4. Authoring Diff / Preview / Dry-Run UX.
5. Authoring Safe Apply / Publish-to-Local Workflow.
6. World Pack Editor Pro.
7. Script Pack Editor Pro.
8. Character Pack Editor Pro.
9. Quest Graph Editor Pro.
10. Location / Map Authoring Pro.
11. NPC / Faction / Relationship Authoring Pro.
12. Item / Economy / Trade Authoring Pro.
13. Rumor / Crime / Consequence Authoring Pro.
14. Advanced Module Authoring Panels.
15. Action Mod Editor.
16. Action Mod Test Harness UI.
17. Rule Module Contract UI.
18. Module Browser Pro.
19. Mod Permission Dashboard Pro.
20. Compatibility Matrix UI Pro.
21. Extension Certification UI Pro.
22. Import / Export Wizard Pro.
23. Mod Quality Gate UI Pro.
24. Authoring Audit Trail UI.
25. Authoring Backup / Restore UX.
26. Authoring UI Regression Tests.
27. v3.4 Integration Regression Tests.

The recommended first phase is contract review plus workspace layout and shared
validation/diff/apply surfaces. These become the spine for all later editors.

## Module Plan

### 1. Authoring / Mod UI Contract Review

Goal: audit current Authoring, Content Pack, Script Pack, Mod Platform, Module
Browser, import/export, and Quality Gate UI/API flows.

Frontend changes:
- document current authoring routes, panels, API calls, disabled states, and
  safety copy;
- identify places where authoring-only, debug-only, hidden, and normal-safe
  views are mixed.

Backend changes:
- none by default.

Tests:
- no required code tests unless a blocker is fixed.

Acceptance:
- `docs/V3_4_AUTHORING_MOD_UI_CONTRACT_REVIEW.md` exists;
- report lists current UI surfaces, data flow, apply flow, import/export flow,
  package/mod flow, privacy risks, and recommended v3.4 UI shape.

### 2. Authoring Workspace Layout Pro

Goal: create a unified local authoring workspace with clear navigation, working
area, safety/context sidebar, and bottom status.

Frontend changes:
- add `AuthoringWorkspaceShell`;
- left navigation for World Pack, Script Pack, Character Pack, Quest, Map, NPC,
  Faction, Item/Economy, Rumor/Crime, Modules, Mods, Import/Export, Quality,
  Audit, Backup;
- right sidebar for validation, diff, permissions, package summary, hidden-data
  policy, and safe apply state;
- bottom status for local-only, authoring API, quality gate, dirty state, and
  apply safety.

Backend changes:
- none unless a safe summary endpoint is needed.

Tests:
- frontend build;
- static check that workspace text includes local-only and no direct
  `GameState` mutation copy.

Acceptance:
- empty/disabled states are friendly;
- no hidden facts, raw `state_deltas`, API keys, raw env, or provider secrets
  are shown in normal workspace.

### 3. World Pack Editor Pro

Goal: make world pack editing safer and easier for manifest, facts, locations,
NPCs, quests, items, factions, relationships, schedules, and module config.

Frontend changes:
- safe file tree grouped by content type;
- structured editor summary where schemas exist;
- YAML/preview view remains local;
- validation summary and impact summary are always visible.

Backend changes:
- optional safe file summary endpoint if current authoring file API lacks
  enough metadata.

Tests:
- preview does not write files;
- save requires validation and confirmation for warnings/impact;
- hidden/debug fields are labeled authoring-only or excluded from normal
  preview.

Acceptance:
- editing a world pack never modifies active `GameState`;
- invalid pack cannot be applied without validation failure being visible.

### 4. Script Pack Editor Pro

Goal: polish local script/scenario/template package authoring without executable
code.

Frontend changes:
- Script Pack form for manifest, files, scenario/template refs, compatibility,
  validation gates, and export preview;
- dry-run, validate, build, and export states clearly separated.

Backend changes:
- reuse existing script package builder; add safe summaries only if needed.

Tests:
- dry-run does not write package output;
- `.env`, secrets, executable payloads, path traversal, databases, logs, and
  build artifacts are rejected.

Acceptance:
- package export requires validation;
- UI states clearly say script packs are content packages, not executable code.

### 5. Character Pack Editor Pro

Goal: provide local character pack authoring for shared character profiles,
Tavern-compatible drafts, RP/voice references, and World NPC draft candidates.

Frontend changes:
- character list/cards;
- import/preview/edit safe fields;
- private/persona/authoring-only fields collapsed and labeled;
- World NPC draft conversion status.

Backend changes:
- reuse character pack builder/importer; optional safe summary endpoint.

Tests:
- private notes and NPC secrets are excluded from normal export;
- character pack import does not auto-create World NPCs;
- no scripts are executed.

Acceptance:
- character pack UI supports create/edit/validate/export safe flow.

### 6. Quest Graph Editor Pro

Goal: polish quest graph authoring with nodes, objectives, dependencies,
visibility, and validation issues.

Frontend changes:
- improved quest node list and detail panel;
- objective/status/visibility controls;
- dependency and blocker summaries;
- safe link to validation graph.

Backend changes:
- none unless safe graph summary is missing.

Tests:
- preview validates quest refs;
- save requires confirmation when warnings or impact risks exist;
- hidden objectives are authoring-only and not shown in player preview.

Acceptance:
- quest graph edits are local content changes only and do not complete active
  quests.

### 7. Location / Map Authoring Pro

Goal: polish location map editing, exits, tags, map coordinates, and visibility.

Frontend changes:
- location list, selected location editor, exits editor, map coordinate summary;
- map preview with safe labels and validation issue overlay;
- hidden exits/locations clearly marked authoring-only.

Backend changes:
- reuse map authoring APIs.

Tests:
- invalid exits and missing locations are reported;
- preview does not move player or alter active session.

Acceptance:
- map authoring cannot alter active player location.

### 8. NPC / Faction / Relationship Authoring Pro

Goal: unify NPC, faction, relationship, goals, schedules, and social graph
editing.

Frontend changes:
- NPC list/detail editor;
- faction/relationship graph panel;
- relationship visibility controls;
- NPC knowledge/secrets shown only in explicit authoring-only sections.

Backend changes:
- reuse social graph, NPC goal, and content validation APIs.

Tests:
- authoring-only private/secret fields do not appear in normal preview;
- save requires validation;
- relationship edits do not modify active runtime relationship state.

Acceptance:
- authoring UI can draft NPC/social changes without changing active
  `GameState`.

### 9. Item / Economy / Trade Authoring Pro

Goal: polish item schema, merchant inventory, prices, tags, economy references,
and trade authoring.

Frontend changes:
- item list/detail editor;
- merchant/trade panel;
- economy modifier summary;
- validation and impact preview.

Backend changes:
- reuse item/economy authoring APIs.

Tests:
- hidden item properties are authoring-only;
- UI does not calculate authoritative runtime trade outcomes;
- save requires validation.

Acceptance:
- item/economy edits remain content-pack edits only.

### 10. Rumor / Crime / Consequence Authoring Pro

Goal: polish rumor chains, witness/crime consequences, reputation effects, and
quest links.

Frontend changes:
- rumor/crime graph overview;
- witness/NPC knowledge refs;
- consequence preview and validation;
- safe player-facing preview.

Backend changes:
- reuse rumor/crime authoring APIs.

Tests:
- hidden witnesses and unrevealed truths are not shown in normal preview;
- validation catches missing refs;
- save cannot bypass warnings without confirmation.

Acceptance:
- consequence authoring remains deterministic content data, not runtime event
  mutation.

### 11. Advanced Module Authoring Panels

Goal: expose safe authoring panels for tactical combat, economy simulation,
faction war, magic, hacking, crafting, deduction, survival/travel, and
cultivation module configuration.

Frontend changes:
- module dashboard with enabled/disabled state, migration status, quality
  status, and safe draft validators;
- per-module lightweight draft validation panels.

Backend changes:
- reuse module draft validation and module quality gate APIs.

Tests:
- module drafts validate without changing active module state;
- hidden module data is filtered from normal preview.

Acceptance:
- module authoring UI cannot adjudicate module outcomes or mutate runtime
  module state.

### 12. Action Mod Editor

Goal: improve declarative Action Mod editing.

Frontend changes:
- manifest editor;
- action definition editor;
- precondition/effect/result preview;
- normalized YAML preview;
- validation issues next to fields.

Backend changes:
- reuse Action Mod preview/validate/export APIs.

Tests:
- `execute_code`, network, secret reads, and unsafe paths are rejected;
- Action Mod cannot bypass `ActionRegistry`;
- export contains no API keys or hidden debug material.

Acceptance:
- Action Mod UI exports declarative packages only.

### 13. Action Mod Test Harness UI

Goal: let authors run local deterministic test cases for action mods.

Frontend changes:
- test case list/editor;
- dry-run result summary;
- expected vs actual safe output;
- no real provider calls.

Backend changes:
- optional API wrapper for existing action mod test harness if missing.

Tests:
- test harness uses local fixtures;
- no active `GameState` mutation;
- no LLM/provider calls.

Acceptance:
- authors can verify action definitions before package export.

### 14. Rule Module Contract UI

Goal: display and validate Rule Module manifests and permissions as contracts,
not executable code.

Frontend changes:
- manifest viewer/editor;
- permission summary;
- lifecycle compatibility summary;
- warning that runtime code execution is unsupported.

Backend changes:
- optional safe contract validation endpoint if current tooling is CLI-only.

Tests:
- `can_execute_code` and network access are blocked;
- manifest validation reports clear errors.

Acceptance:
- Rule Module UI cannot execute or load runtime code.

### 15. Module Browser Pro

Goal: polish local Module Browser for package scan, details, validation, and
safe install/readiness review.

Frontend changes:
- module cards, detail panel, validation summary, package contents summary,
  compatibility summary, permission risk, and local-only status;
- no remote package download or online marketplace entry.

Backend changes:
- reuse module browser APIs.

Tests:
- scanning rejects secret-like package content;
- path traversal and unsafe files are rejected;
- no online calls.

Acceptance:
- module browser supports daily local review without executing packages.

### 16. Mod Permission Dashboard Pro

Goal: make permissions understandable and enforce default-deny risky categories.

Frontend changes:
- grouped permission categories for filesystem, network, secrets, execution,
  content writes, and runtime hooks;
- risk badges and remediation copy.

Backend changes:
- reuse module permissions model.

Tests:
- dangerous permissions surface as blocked/warning;
- UI does not offer an execute-code override.

Acceptance:
- permission dashboard is safe, readable, and local-only.

### 17. Compatibility Matrix UI Pro

Goal: improve local dependency/conflict/version/permission compatibility review.

Frontend changes:
- matrix table;
- conflicts summary;
- version mismatch and permission conflict rows;
- package selection controls.

Backend changes:
- reuse compatibility matrix APIs/tools.

Tests:
- matrix can be built from local package IDs;
- no package download;
- hidden/secrets not shown.

Acceptance:
- compatibility blockers are visible before import/apply.

### 18. Extension Certification UI Pro

Goal: polish local advisory certification for packages/extensions.

Frontend changes:
- certification status, level, checks, warnings, local-only explanation;
- clear distinction from online certification.

Backend changes:
- reuse extension certification services.

Tests:
- certification runs locally;
- unsafe permissions, secrets, executable payloads, and compatibility blockers
  affect result.

Acceptance:
- certification is advisory and cannot bypass quality/validation gates.

### 19. Import / Export Wizard Pro

Goal: unify local package import/export with preview, filtering, validation,
conflict review, and explicit apply.

Frontend changes:
- steps for choose package/source, scan, preview, validate, conflict review,
  filtering policy, confirm import/export;
- explicit local-only and no-remote-download copy.

Backend changes:
- optional safe preview additions if current import/export response lacks
  filtering detail.

Tests:
- preview does not write;
- import rejects zip slip/path traversal/secrets/executables;
- export filters `.env`, API keys, provider secrets, logs, databases, caches,
  build outputs, hidden/debug/private data by default.

Acceptance:
- no import/export path can bypass validation and confirmation.

### 20. Mod Quality Gate UI Pro

Goal: centralize package/mod quality checks for manifest, permissions,
compatibility, hidden leaks, executable payloads, action tests, and docs.

Frontend changes:
- quality gate dashboard;
- blocker/warning/suggestion grouping;
- affected package links;
- run button and safe report.

Backend changes:
- reuse mod quality gate tools/APIs.

Tests:
- no real provider calls;
- secret/executable/permission blockers are surfaced;
- report contains safe summaries only.

Acceptance:
- mod quality gate is a required visible step before safe apply/export.

### 21. Authoring Validation Dashboard

Goal: provide one local dashboard for validation status across world files,
packs, modules, imports, exports, and authoring drafts.

Frontend changes:
- validation health cards;
- grouped errors/warnings/suggestions;
- file/entity links;
- recent validation runs.

Backend changes:
- optional aggregate safe summary endpoint.

Tests:
- validation dashboard does not show hidden text or raw local paths;
- stale/missing validation states are clear.

Acceptance:
- authors can find blockers without searching individual editors.

### 22. Authoring Diff / Preview / Dry-Run UX

Goal: make every authoring write easy to preview before it writes.

Frontend changes:
- shared diff viewer;
- added/changed/removed files;
- impact summary;
- dry-run status;
- confirmation readiness.

Backend changes:
- reuse diff/preview services; optional safe diff summary if missing.

Tests:
- dry-run does not write;
- diff output filters secrets and sensitive local paths;
- warnings require confirmation.

Acceptance:
- no write flow lacks a preview/dry-run explanation.

### 23. Authoring Audit Trail UI

Goal: show local authoring/mod operations as safe audit records.

Frontend changes:
- audit list for scan, preview, validate, certify, quality gate, import,
  export, save, apply;
- local timestamps and safe actor/source labels;
- no hidden content or secrets.

Backend changes:
- optional audit summary endpoint if current records are scattered.

Tests:
- audit records redact secrets and paths;
- audit does not replace `EventLog`.

Acceptance:
- authoring audit trail is local-only and cannot modify runtime world state.

### 24. Authoring Backup / Restore UX

Goal: adapt local backup/restore patterns to authoring and package work.

Frontend changes:
- authoring backup dry-run;
- changed files summary;
- default exclusions;
- restore preview, conflict warning, and explicit confirm.

Backend changes:
- optional authoring-scoped backup plan using existing backup service.

Tests:
- backup dry-run does not write;
- backups exclude `.env`, API keys, provider secrets, logs, caches, databases,
  build outputs, hidden/debug/private data by default;
- restore apply requires confirmation.

Acceptance:
- authoring backups protect local work without leaking secrets.

### 25. Authoring Safe Apply / Publish-to-Local Workflow

Goal: make local apply/publish explicit and safe without implying online
publishing.

Frontend changes:
- shared safe apply checklist;
- validation status, quality gate status, diff status, backup status,
  permission status, compatibility status, and confirm;
- output target is local content/package only.

Backend changes:
- optional apply readiness safe summary.

Tests:
- apply blocked when validation fails;
- confirm required;
- apply never targets active `GameState`;
- publish-to-local does not upload or call remote services.

Acceptance:
- users can safely promote drafts into local content/package files.

### 26. Authoring UI Regression Tests

Goal: ensure Authoring / Mod UI Pro compiles and preserves safety copy.

Frontend changes:
- add `frontend/scripts/check-v34-authoring-ui.mjs`;
- add npm script `check:v34-authoring-ui`.

Backend changes:
- none.

Tests:
- import/check components and required tokens;
- check no online marketplace, no package download, no plaintext API key field,
  no direct `GameState` mutation copy, and validation/dry-run/confirm copy.

Acceptance:
- `cd frontend && npm.cmd run build`;
- `cd frontend && npm.cmd run check:v34-authoring-ui`.

### 27. v3.4 Integration Regression Tests

Goal: verify v3.4 does not break v2.1-v3.3 capabilities or authoring/mod
security boundaries.

Frontend changes:
- none beyond checks.

Backend changes:
- add focused pytest coverage for authoring/mod boundaries.

Tests:
- authoring preview does not write active runtime state;
- save/apply requires validation/confirm;
- Action Mod and Rule Module cannot execute code;
- Provider Profile Pack rejects raw API keys;
- import/export rejects secrets and unsafe paths;
- Mod Quality Gate reports blockers;
- no real API calls;
- `python -m pytest`;
- frontend build.

Acceptance:
- all tests pass and no release blocker remains.

## Cross-Area Impact

### Authoring Studio Impact

Authoring Studio becomes a cohesive local workspace rather than a collection of
separate dense panels. Draft, preview, validation, dry-run, diff, backup, audit,
and safe apply become shared concepts across editors.

### Mod Platform Impact

Mod Platform gets clearer local package review: Module Browser, permissions,
compatibility, certification, Action Mod editor/test harness, Rule Module
contract review, import/export, and Mod Quality Gate become visible and
repeatable. v3.4 does not expand module authority or add executable plugins.

### World Studio / Active GameState Impact

World Studio runtime authority is unchanged. Authoring can edit local world
content files or package candidates after validation and confirmation, but it
cannot directly alter active `GameState`, active saves, active sessions,
`StateDelta`, or `EventLog`.

### Novel / Tavern / Cross-Mode Impact

Novel and Tavern outputs may remain sources of drafts/proposals for content
authoring, but they do not automatically become World facts. Cross-mode
artifacts still require draft/proposal/review/validation/explicit apply.
Authoring UI may surface these links only as safe summaries.

### Provider Gateway Impact

Provider Gateway remains the only model entry point. v3.4 UI does not add LLM
judgment for content safety, package certification, quality gates, or world
facts. Provider Profile Packs may reference environment variables or local
secret refs only; raw API keys are forbidden.

### Quality Gate Impact

Quality Gate becomes more visible in authoring workflows. v3.4 should connect
validation, compatibility, certification, Mod Quality Gate, and release
readiness into clear safe reports, without making the UI an authority that can
override blockers.

### Import / Export / Security Impact

Import/export remains local and dry-run-first. Packages must reject path
traversal, zip slip, executable payloads, `.env`, API keys, provider secrets,
databases, logs, caches, build outputs, hidden/debug/private content, and
unsafe permissions by default. Export previews and manifests must remain safe
summaries.

## v3.5 Candidate Direction

Recommended v3.5 theme: Local QA / Debug / Replay UI Pro.

Candidate priorities:

- Unified QA workspace;
- Scenario regression dashboard;
- Playtest replay UI;
- Debug timeline Pro;
- EventLog replay inspector;
- Save migration stress UI;
- Hidden leak dashboard;
- Performance budget dashboard;
- Provider prompt regression dashboard;
- Module regression runner UI;
- Release checklist UI Pro;
- Safe debug bundle review;
- Local-only QA audit trail.

v3.5 should continue the local-first route and must not add accounts, cloud
sync, online marketplaces, remote package download, arbitrary-code plugins, or
LLM-as-judge authority.
