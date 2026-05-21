# v2.1 Roadmap: Unified Narrative Project Layer

v2.1 upgrades the local modular narrative RPG platform from a world/campaign
centered model into a `NarrativeProject` centered model. A NarrativeProject is a
local project container that can organize Novel drafts, Tavern/RP sessions,
World play, scripts, mods, provider profiles, shared libraries, quality reports,
exports, and compatibility metadata without replacing the World Engine as the
source of truth.

This roadmap is a development plan, not an acceptance report. It does not claim
that complete Novel Studio or Tavern Studio functionality already exists.

## v2.1 Goals

- Define a stable `NarrativeProject` contract for local project metadata,
  workspace layout, mode references, shared libraries, validation status, quality
  status, import/export policy, and migration metadata.
- Introduce project-level APIs and a frontend Project Shell that can route
  between Novel, Tavern, and World mode stubs.
- Add shared libraries for characters, world bible entries, timelines, lore,
  facts, prompt profiles, provider profiles, and memory references.
- Add `CrossModeLink` references so Novel/Tavern/World assets can refer to one
  another without directly applying world state changes.
- Adapt existing v2.0 WorkspaceProject, Campaign, World, Module, Provider,
  Package, and Quality Gate services into a project-level workflow.
- Preserve all v2.0 safety boundaries: local-first operation, Provider Gateway
  as the model entrypoint, no API keys in exports, no hidden leaks, and no
  direct GameState mutation outside World Engine rules.

## Explicit Non-Goals

- No complete Novel Studio.
- No complete Tavern Studio.
- No online accounts.
- No cloud sync.
- No online marketplace.
- No arbitrary-code plugins.
- No change to World Engine fact authority.
- No direct `GameState` mutation from Novel or Tavern modes.
- No real API keys in Provider Profile data.
- No weakening of v2.0 compatibility, package, plugin, module, or export
  security.

## Recommended Development Order

1. NarrativeProject Foundation:
   - NarrativeProject Core Schema.
   - Project Workspace Layout.
   - Project Repository / Storage.
   - Project API.
   - Project Frontend Shell.
2. Shared Libraries:
   - Shared Character Library.
   - Shared World Bible.
   - Shared Timeline Library.
   - Shared Lore / Fact Library.
   - Shared Prompt Profile Library.
   - Shared Provider Profile Library.
   - Shared Memory Library.
3. Mode Integration:
   - CrossModeLink System.
   - Mode Router.
   - Novel Mode Project Stub.
   - Tavern Mode Project Stub.
   - World Mode Project Adapter.
4. Portability and Safety:
   - Project Import / Export.
   - Project Migration from v2.0.
   - Project Validation.
   - Project Quality Gate Integration.

## Module Plan

### 1. NarrativeProject Core Schema

- Goal: introduce the top-level project object that groups all mode-specific and
  shared project data.
- Data structures: `NarrativeProject`, `NarrativeProjectMetadata`,
  `NarrativeProjectModeRefs`, `NarrativeProjectLibraryRefs`,
  `NarrativeProjectCompatibility`, `NarrativeProjectSafeSummary`.
- API changes: project create/read/update/list endpoints should return safe
  summaries by default and full local metadata only through trusted local APIs.
- Frontend changes: Project Shell header shows project name, active mode,
  validation state, quality state, and local-only status.
- Tests: schema validation, deterministic JSON serialization, safe summary no
  secrets, unknown experimental fields handled safely.
- Acceptance: a project can be created, loaded, summarized, and validated without
  touching active `GameState`.

### 2. Project Workspace Layout

- Goal: define the local directory layout for a NarrativeProject.
- Data structures: `ProjectLayout`, `ProjectLayoutPath`, `ProjectLayoutReport`.
- API changes: layout init/validate endpoints should reject path traversal and
  unsafe absolute references outside the project root.
- Frontend changes: Project Settings shows redacted local paths and layout
  validation status.
- Tests: valid layout passes, traversal fails, `.env`/database/log/cache folders
  are excluded from exportable layout.
- Acceptance: project directories can be initialized or detected safely without
  copying secrets or executable scripts.

### 3. Project Repository / Storage

- Goal: provide local persistence for project manifests and shared library
  indexes.
- Data structures: `NarrativeProjectRepository`, `ProjectStorageRecord`,
  `ProjectStorageReport`.
- API changes: repository-backed read/write should be explicit; read APIs should
  never expose raw env or full sensitive paths.
- Frontend changes: save/load project metadata actions and clear error states.
- Tests: temp workspace storage, round-trip save/load, corrupted manifest safe
  failure, no writes during preview/validate.
- Acceptance: repository operations are deterministic and do not modify active
  saves or world runtime state.

### 4. Project API

- Goal: expose local project APIs for project CRUD, selection, validation, and
  safe summaries.
- Data structures: request/response schemas for create, update, select, validate,
  safe summary, and status.
- API changes: freeze project endpoints in the first v2.1 implementation slice,
  preferably under a single local project namespace.
- Frontend changes: Project Shell consumes these APIs and handles disabled/error
  states.
- Tests: disabled API behavior if gated, stable error schema, no secrets, no
  hidden data, path traversal rejected.
- Acceptance: project APIs are deterministic, local-only, and do not bypass
  World Engine state boundaries.

### 5. Project Frontend Shell

- Goal: add a lightweight shell for switching project modes and viewing shared
  project status.
- Data structures: frontend types matching project safe summaries and mode
  status.
- API changes: none beyond Project API consumption.
- Frontend changes: mode tabs for Novel, Tavern, World, Libraries, Quality, and
  Export; only stub content for incomplete modes.
- Tests: `npm.cmd run build`, disabled API state, no debug/hidden data in normal
  UI, project summary renders.
- Acceptance: users can select a project and see mode/library/validation status
  without full Novel/Tavern feature implementation.

### 6. Shared Character Library

- Goal: unify reusable character identities across Novel, Tavern, and World
  modes.
- Data structures: `SharedCharacter`, `CharacterLibraryIndex`,
  `CharacterModeBinding`.
- API changes: list/read/validate character library entries and mode bindings.
- Frontend changes: character list with safe public profile, linked modes, and
  validation warnings.
- Tests: hidden/private fields redacted, Character Card to NPC conversion remains
  schema-gated, duplicate ids detected.
- Acceptance: shared characters can be referenced by modes without leaking NPC
  secrets or directly changing world NPC state.

### 7. Shared World Bible

- Goal: store project-level world bible entries used by Novel/Tavern/World
  workflows.
- Data structures: `WorldBibleEntry`, `WorldBibleIndex`,
  `WorldBibleVisibility`.
- API changes: list/read/validate bible entries; world import remains explicit.
- Frontend changes: world bible panel with category, visibility, and link status.
- Tests: hidden entries excluded from normal context, invalid refs warned,
  export safe profile redacts hidden text.
- Acceptance: bible entries are reusable references, not authoritative World
  facts until imported and validated.

### 8. Shared Timeline Library

- Goal: provide project-level timeline artifacts separate from runtime EventLog.
- Data structures: `SharedTimeline`, `TimelineEntryRef`, `TimelineLibraryIndex`.
- API changes: list/read timeline drafts and links to campaigns/EventLog.
- Frontend changes: timeline library panel with mode/source filters.
- Tests: runtime EventLog preserved, timeline drafts do not mutate saves, hidden
  entries redacted in normal view.
- Acceptance: project timelines can reference World EventLog but cannot rewrite
  it.

### 9. Shared Lore / Fact Library

- Goal: centralize lore and fact candidates across modes.
- Data structures: `SharedFact`, `SharedLoreEntry`, `FactLibraryIndex`,
  `FactVisibilityPolicy`.
- API changes: validate fact candidates and show safe summaries.
- Frontend changes: lore/fact library with visible/hidden/debug classification.
- Tests: hidden facts do not enter visible state, normal Novel/Tavern contexts,
  or exports; duplicate/conflicting facts warn.
- Acceptance: facts remain candidates until World Engine validation promotes
  them into world content or runtime state.

### 10. Shared Prompt Profile Library

- Goal: organize prompt profiles for modes without expanding LLM authority.
- Data structures: `ProjectPromptProfileRef`, `PromptProfileLibraryIndex`.
- API changes: list/read/validate profile refs and compatibility.
- Frontend changes: profile selector with mode compatibility and safety status.
- Tests: missing contract version rejected, unsafe hidden/state policy rejected,
  export safe.
- Acceptance: prompt profiles can change expression style only and cannot alter
  visibility or facts.

### 11. Shared Provider Profile Library

- Goal: organize provider profile metadata and routing refs at project level.
- Data structures: `ProjectProviderProfileRef`, `ProviderProfileSafeSummary`,
  `ProviderRoutingRef`.
- API changes: list/read safe provider summaries and routing compatibility.
- Frontend changes: provider profile panel shows provider type, capabilities, and
  missing-config warnings without secrets.
- Tests: API keys/raw env never serialized, env var refs only, missing config
  produces stable safe errors.
- Acceptance: Provider Gateway remains the only model entrypoint; profiles never
  contain real API keys.

### 12. Shared Memory Library

- Goal: hold reusable, redacted memory references for project modes.
- Data structures: `SharedMemoryRef`, `MemoryLibraryIndex`,
  `MemoryVisibilityPolicy`.
- API changes: list/read safe memory summaries and mode bindings.
- Frontend changes: memory panel with source mode, visibility, and redaction
  status.
- Tests: debug/private memories redacted, memory cannot override GameState,
  exports exclude raw/private text by default.
- Acceptance: memory is context material only, not an authoritative fact source.

### 13. CrossModeLink System

- Goal: connect Novel/Tavern/World assets by reference without applying changes.
- Data structures: `CrossModeLink`, `CrossModeLinkType`,
  `CrossModeLinkValidationReport`.
- API changes: create/list/delete/validate links between project assets.
- Frontend changes: link inspector showing source, target, mode, warnings, and
  broken refs.
- Tests: broken refs warn, hidden targets redacted, no direct `GameState`
  mutation, import/export preserves links safely.
- Acceptance: links are references only and cannot bypass validation or
  visibility.

### 14. Mode Router

- Goal: route project actions to Novel, Tavern, or World mode services with
  explicit boundaries.
- Data structures: `ProjectMode`, `ModeRouteRequest`, `ModeRouteResult`,
  `ModeCapabilitySummary`.
- API changes: project mode status and route endpoints for local shell use.
- Frontend changes: mode navigation and disabled-state messaging.
- Tests: unsupported mode fails safely, Novel/Tavern cannot call World mutation
  APIs directly, World mode adapter still uses existing runtime APIs.
- Acceptance: routing clarifies mode ownership and prevents cross-mode authority
  escalation.

### 15. Novel Mode Project Stub

- Goal: provide a minimal project-scoped Novel mode placeholder.
- Data structures: `NovelDraft`, `NovelOutlineRef`, `NovelModeProjectState`.
- API changes: create/list/read draft metadata and safe export preview.
- Frontend changes: Novel tab with draft list/status only; no full editor.
- Tests: drafts are not World facts, no hidden facts in normal draft context,
  no LLM call by default.
- Acceptance: Novel mode can store project drafts without modifying World
  `GameState`.

### 16. Tavern Mode Project Stub

- Goal: provide a minimal project-scoped Tavern/RP mode placeholder.
- Data structures: `TavernSessionRef`, `RPProposal`, `TavernModeProjectState`.
- API changes: list/read RP sessions and proposal metadata.
- Frontend changes: Tavern tab with session/proposal status only; no full Tavern
  UI.
- Tests: RP outputs are memory/proposals, not runtime facts; hidden/private RP
  fields redacted; no direct GameState mutation.
- Acceptance: Tavern mode can reference RP material without changing World
  state until a proposal is validated.

### 17. World Mode Project Adapter

- Goal: connect NarrativeProject to existing World/Campaign services.
- Data structures: `WorldModeProjectBinding`, `CampaignBinding`,
  `WorldModeStatus`.
- API changes: bind project to world/campaign/save/module/profile refs; expose
  safe status.
- Frontend changes: World tab shows linked world/campaign/save/module status and
  entry points to existing Studio panels.
- Tests: World actions still use `StateDelta` and `EventLog`; player APIs remain
  current-campaign scoped; hidden data isolated.
- Acceptance: v2.0 World/Campaign behavior remains compatible under project
  ownership.

### 18. Project Import / Export

- Goal: package project metadata and shared libraries safely.
- Data structures: `NarrativeProjectPackageManifest`,
  `ProjectExportProfile`, `ProjectImportDryRunReport`.
- API changes: export, inspect, import-dry-run, and explicit import-apply
  endpoints.
- Frontend changes: export/import panel with profile confirmation and warnings.
- Tests: zip slip rejected, executables rejected, checksums required, dry-run no
  write, `.env`/API keys/logs/cache/databases/raw prompts/hidden facts excluded
  by default.
- Acceptance: project packages are local, safe, deterministic, and compatible
  with package v2 security rules.

### 19. Project Migration from v2.0

- Goal: migrate existing v2.0 workspace/campaign metadata into NarrativeProject
  form.
- Data structures: `ProjectMigrationPlan`, `ProjectMigrationReport`,
  `ProjectMigrationBackupRef`.
- API changes: migration inspect, dry-run, apply with explicit confirmation, and
  recovery endpoints if needed.
- Frontend changes: migration panel with dry-run summary, blockers, warnings, and
  backup status.
- Tests: v2.0 workspace -> NarrativeProject, campaign refs preserved, dry-run no
  write, backup before apply, failure preserves source metadata.
- Acceptance: migration does not alter active saves or runtime world state and
  fails safely.

### 20. Project Validation

- Goal: validate project schema, layout, links, libraries, mode bindings, and
  export safety.
- Data structures: `NarrativeProjectValidationReport`,
  `ProjectValidationIssue`, `ProjectValidationProfile`.
- API changes: project validate endpoint and optional JSON report output.
- Frontend changes: validation dashboard in Project Shell.
- Tests: invalid schema fails, missing refs warn/error, hidden leak checks,
  provider secret checks, path traversal checks.
- Acceptance: validation blocks unsafe imports/exports and warns about
  incomplete mode links without modifying project data.

### 21. Project Quality Gate Integration

- Goal: aggregate existing quality gates at project level.
- Data structures: `ProjectQualityGateConfig`, `ProjectQualityGateReport`,
  `ProjectQualityGateRef`.
- API changes: run/recent project quality gate endpoints, with safe report
  summaries.
- Frontend changes: quality panel showing project validation, world quality,
  package safety, hidden leak, migration, and compatibility summaries.
- Tests: valid project pass, hidden leak blocker fail, provider secret fail,
  migration blocker fail, report redacted.
- Acceptance: high-risk blockers fail project quality gate and cannot be ignored
  by default.

## Save Migration Impact

- v2.1 must not change the runtime save format merely to introduce
  NarrativeProject.
- Project migration may create project metadata that references existing saves,
  campaigns, worlds, modules, and profiles.
- Any future save schema changes require dry-run, backup before apply,
  validation after migration, EventLog preservation, hidden visibility
  preservation, and recovery on failure.

## Content Pack / Mod / Provider Profile Impact

- Content packs remain world/content artifacts and must keep schema and
  compatibility checks.
- Mods, modules, action mods, and plugins remain declarative unless a future
  sandboxed code-plugin design is explicitly added.
- NarrativeProject may reference module/package/profile ids but cannot weaken
  their contract versions, permissions, or compatibility checks.
- Provider profiles in a project store safe metadata and env-var references only;
  real API keys remain outside project files and exports.

## LLM Boundary Impact

- LLMs can help render prose, draft summaries, and assist RP expression only
  through Provider Gateway.
- Novel mode drafts are not world facts.
- Tavern mode RP memory/proposals are not world facts.
- World mode remains the only runtime fact engine and all state changes still
  flow through local rules, `StateDelta`, and `EventLog`.
- No project-level tool may use an LLM to decide validation, compatibility,
  migration, quality gate, or release pass/fail.

## Hidden / Secret / Memory Visibility Risks

- Hidden facts must not enter normal Novel, Tavern, World, project dashboard,
  export, or quality report views.
- NPC secrets and private RP fields must remain redacted unless explicitly shown
  in a gated debug/authoring context.
- Debug data, raw prompts, raw state deltas, raw env, and provider secrets must
  not enter project safe summaries or exports.
- Shared Memory Library entries must preserve source visibility classification
  and cannot become authoritative facts by being linked.
- CrossModeLink must not turn a hidden source asset into visible target context.

## v2.1 Integration Test Requirements

- Deterministic NarrativeProject schema and serialization tests.
- Project workspace layout and path traversal tests.
- Repository round-trip tests using temporary project roots.
- Project API safe summary and stable error tests.
- Shared library visibility and duplicate/conflict tests.
- CrossModeLink validation and no-direct-mutation tests.
- Novel/Tavern stub tests proving drafts/proposals do not modify GameState.
- World adapter tests proving `StateDelta` and `EventLog` boundaries remain.
- Import/export tests for checksum, zip slip, executable rejection, secrets
  filtering, and dry-run no write.
- v2.0 migration tests with backup/failure safety.
- Project validation and project quality gate aggregation tests.
- Frontend build verification with project shell UI.

Required release commands:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Additional project validation and project quality gate CLI/API commands should
be added once the corresponding v2.1 implementation exists.

## v2.1 Final Acceptance Standard

v2.1 is acceptable only when:

- NarrativeProject schema, repository, API, frontend shell, shared libraries,
  CrossModeLink, mode router, Novel/Tavern stubs, World adapter, import/export,
  migration, validation, and project quality gate have deterministic tests.
- Full pytest and frontend build pass.
- No high-risk LLM, visibility, migration, provider secret, package security, or
  project export blocker remains.
- Project exports exclude `.env`, API keys, databases, logs, caches, build
  outputs, crash reports, raw prompts, hidden facts, NPC secrets, and debug data
  by default.
- Documentation, audits, acceptance report, and release notes accurately state
  that v2.1 is a project layer, not a complete Novel/Tavern platform.

## v2.2 Candidate Direction

- Full Novel Studio: outline editor, chapter drafting, revision history,
  continuity checks, and safe exports.
- Full Tavern Studio: character chat UX, group RP workflows, RP session memory,
  emotion/relationship dashboards, and proposal review.
- Deeper World-to-Novel chronicle export from EventLog and Timeline.
- Richer CrossModeLink visualization and conflict review.
- Broader project templates and package ecosystem polish.
- More compatibility fixtures for real local projects, without online sync or
  marketplace assumptions.
