# v2.6 Roadmap: Script / Mod Platform Pro

## Version Theme

Script / Mod Platform Pro on top of the v2.1 `NarrativeProject` layer, v2.2
Novel Studio MVP, v2.3 Tavern Studio MVP, v2.4 Cross-Mode Bridge, and v2.5
Provider Gateway Pro.

## Current Baseline

- HEAD is expected to start from the `v2.5` tag with a clean working tree.
- Existing foundations include content-only `ModLoader`, manifest-only
  `PluginLoader`, declarative `GameplayModuleLoader`, `ActionRegistry`, script
  package builder, ProjectPackage import/export, and package security helpers.
- `mods/` does not yet exist as a stable v2.6 project workspace directory.
- `docs/V2_6_RESEARCH_PLAN.md` does not exist in the current baseline.
- Current mod and package systems are local, declarative, and non-executable.

## Goal

v2.6 unifies script packs, world extension packs, character packs, prompt profile
packs, provider profile packs, narrative style mods, RP profile mods,
declarative action mods, and rule module contracts into one local extension
platform.

The platform must be safe, manifest-driven, validation-first, auditable, and
compatible with `NarrativeProject`, Novel Studio, Tavern Studio, World Mode,
Cross-Mode Bridge, and Provider Gateway. Mods may add content, configuration,
templates, profiles, style metadata, and controlled declarative action/rule
definitions. They must not execute arbitrary code or bypass World Engine
authority.

This roadmap is a development plan, not an acceptance report.

## Explicit Non-Goals

- No arbitrary-code plugins.
- No Python, JavaScript, shell, PowerShell, binary, or native-code execution
  from mods.
- No mod access to `.env`, API keys, databases, logs, caches, user private
  files, or arbitrary filesystem paths.
- No Action Mod bypass of `ActionRegistry`.
- No Action Mod direct mutation of `GameState`.
- No Action Mod bypass of `StateDelta` or `EventLog`.
- No Rule Module direct database access.
- No Provider Profile Pack storage of real API keys.
- No online marketplace.
- No account system.
- No cloud sync.
- No automatic remote package download and execution.
- No sandbox code runtime in v2.6; sandboxed code execution may be considered
  for a later v2.9 direction only after a separate security design.
- No LLM-based safety certification.
- No LLM-as-world-judge behavior.
- No weakening of Provider Gateway as the only model entry.

## Recommended Development Order

1. Platform Foundation:
   - Script / Mod Platform Contract Review.
   - Package Manifest v2 Schema.
   - Module Permission Model.
   - Mod Import / Export Hardening.
   - Mod Audit Trail.
2. Pack Types:
   - Script Pack v2.
   - World Pack Extension Pack.
   - Character Pack.
   - Prompt Profile Pack.
   - Provider Profile Pack.
   - Narrative Style Mod.
   - RP Profile Mod.
3. Declarative Action / Rule Modules:
   - Declarative Action Mod Core Schema.
   - Action Registry Mod Integration.
   - Declarative Action Preconditions / Checks / Outcomes DSL.
   - Action Mod Test Harness.
   - Rule Module Contract.
4. Studio / Review / Quality:
   - Module Browser Backend.
   - Module Browser Frontend.
   - Mod Compatibility Matrix.
   - Extension Certification Tool.
   - Mod Quality Gate.
   - Mod Permission Dashboard.
5. Release Hardening:
   - v2.6 Integration Regression Tests.

## Module Plan

### 1. Script / Mod Platform Contract Review

- Goal: define one contract boundary for local extension packages, mod records,
  manifests, permissions, validation reports, compatibility status, audit
  records, and quality gate results.
- Data structures: `ExtensionPackageKind`, `ExtensionPackageRef`,
  `ExtensionManifestBase`, `ExtensionValidationReport`,
  `ExtensionCompatibilityStatus`, `ExtensionSafeSummary`.
- API changes: none required in this slice; future APIs must expose only safe
  summaries and validation results.
- Frontend changes: none required in this slice.
- Tests: static contract checks for no executable permissions, no raw secrets,
  and no direct `GameState` mutation fields in package contracts.
- Acceptance: v2.6 has one documented extension boundary that existing mod,
  plugin, gameplay module, script package, and package import/export code can
  align with.

### 2. Package Manifest v2 Schema

- Goal: define the common manifest layer for all extension package types.
- Data structures: `PackageManifestV2`, package id, display name, version,
  package kind, contract version, engine version range, dependencies,
  conflicts, included sections, checksums, permissions, redaction policy,
  compatibility metadata.
- API changes: package validation APIs consume and return v2 manifest reports.
- Frontend changes: package detail views can render v2 manifest metadata and
  validation status.
- Tests: schema serialization, required fields, unsupported contract version
  rejection, checksum field validation, unsafe permission rejection.
- Acceptance: every v2.6 extension package has a manifest and can be validated
  before import.

### 3. Script Pack v2

- Goal: formalize script packs as local data packages, not executable scripts.
- Data structures: `ScriptPackManifestV2`, script nodes, scenario templates,
  regression refs, quality config refs, authoring notes, safe file list.
- API changes: script pack build, validate, import, export, and safe summary
  endpoints align with `PackageManifestV2`.
- Frontend changes: script pack detail panel with validation issues and included
  data sections.
- Tests: executable file rejection, `.env` and secret rejection, zip slip
  rejection, safe summary redaction, import dry-run no writes.
- Acceptance: script packs can package narrative/project data safely without
  code execution.

### 4. World Pack Extension Pack

- Goal: allow local packages to extend world content through validated content
  candidates.
- Data structures: `WorldExtensionPackManifest`, world refs, content pack refs,
  fact/location/NPC/quest/item/faction candidate refs, compatibility notes.
- API changes: preview and validation APIs create extension candidates, not
  active world writes.
- Frontend changes: review panel for world extension pack content and warnings.
- Tests: content validation, hidden fact handling, no active `GameState` write,
  no content pack write unless a future explicit apply flow validates it.
- Acceptance: world extension packs are validation-ready content candidates,
  not runtime mutations.

### 5. Character Pack

- Goal: package character profiles, Tavern character drafts, RP/voice profile
  metadata, and optional world NPC draft refs safely.
- Data structures: `CharacterPackManifest`, character profile refs,
  TavernCharacter refs, RP/Voice profile refs, visibility mode, authoring-only
  fields.
- API changes: import/export/validate endpoints return safe character summaries.
- Frontend changes: character pack browser and validation issue display.
- Tests: NPC secrets and private notes excluded from normal export, no API key
  material, no direct World NPC overwrite.
- Acceptance: character packs can move character material between projects
  without leaking secrets or modifying world facts.

### 6. Prompt Profile Pack

- Goal: package prompt profiles, mode scopes, style metadata, and safety flags
  without expanding LLM authority.
- Data structures: `PromptProfilePackManifest`, prompt profile refs, mode
  scopes, permission summary, safety policy, compatibility metadata.
- API changes: prompt profile pack validation checks forbidden permissions.
- Frontend changes: prompt pack safe summary and warning list.
- Tests: `can_modify_state`, `can_access_hidden_facts`, raw prompt secrets, and
  provider secrets rejected.
- Acceptance: prompt profile packs are style/config packages only.

### 7. Provider Profile Pack

- Goal: package provider profile metadata without raw provider secrets.
- Data structures: `ProviderProfilePackManifest`, `ProviderProfileV2` refs,
  model profile refs, capability refs, `api_key_env`, `secret_ref`, safe
  routing metadata.
- API changes: provider profile import/export validates secret boundary.
- Frontend changes: provider pack panel shows safe profile summaries only.
- Tests: raw API key rejection, `api_key_env` accepted, `secret_ref` displayed
  as reference only, export contains no key values.
- Acceptance: provider profile packs never store or expose real API keys.

### 8. Narrative Style Mod

- Goal: package Novel/World narration style metadata that affects expression
  only.
- Data structures: `NarrativeStyleModManifest`, style presets, prose tone,
  pacing, formatting hints, allowed mode scopes, safety flags.
- API changes: style mod validation checks mode scope and fact-boundary rules.
- Frontend changes: style mod preview and enabled/disabled state.
- Tests: style-only behavior, no facts added, no hidden fact access, no prompt
  permission escalation.
- Acceptance: narrative style mods can alter wording and presentation, not
  facts or state.

### 9. RP Profile Mod

- Goal: package Tavern RP profile and voice/tone metadata safely.
- Data structures: `RPProfileModManifest`, RP profile refs, voice profile refs,
  relationship tone presets, scene mood refs, authoring-only fields.
- API changes: RP profile mod import/export and validation endpoints.
- Frontend changes: RP mod browser entry with safe summaries.
- Tests: private persona and authoring notes excluded from normal export,
  hidden/debug memory excluded, no World state write.
- Acceptance: RP profile mods affect character presentation only.

### 10. Declarative Action Mod Core Schema

- Goal: stabilize declarative action mod schema around controlled inputs,
  preconditions, checks, outcomes, and StateDelta templates.
- Data structures: `DeclarativeActionModManifest`,
  `DeclarativeActionDefinitionV2`, target specs, affordance requirements,
  visibility policy, outcome definitions, StateDelta proposal templates.
- API changes: action mod validation and preview endpoints accept v2 schema.
- Frontend changes: action mod detail and schema validation issue display.
- Tests: safe id validation, forbidden path rejection, visibility write
  rejection, direct `GameState` mutation fields rejected.
- Acceptance: action mods are declarative and cannot execute code.

### 11. Action Registry Mod Integration

- Goal: register validated action mods through `ActionRegistry` only.
- Data structures: registry source metadata, module/action refs, enabled state,
  risk level, target type metadata, registration audit record.
- API changes: enable/disable action mod endpoints route through registry
  services.
- Frontend changes: action registry mod panel with available actions and
  conflicts.
- Tests: module action registration, unregister, alias conflicts, disabled
  action unavailable, no direct handler bypass.
- Acceptance: Action Mods cannot enter runtime outside `ActionRegistry`.

### 12. Declarative Action Preconditions / Checks / Outcomes DSL

- Goal: provide a controlled DSL for action preconditions, checks, outcomes,
  visibility, and StateDelta proposals.
- Data structures: condition enum, check enum, outcome enum, allowed path
  policy, placeholder policy, visibility policy, deterministic randomness
  policy.
- API changes: DSL validation endpoint and action preview endpoint.
- Frontend changes: compact DSL inspector and validation issue display.
- Tests: allowed conditions pass, unknown operations fail, unsafe paths fail,
  hidden facts not exposed, deterministic preview.
- Acceptance: the DSL is expressive enough for common Action Mods but cannot
  bypass engine rules.

### 13. Action Mod Test Harness

- Goal: let authors test declarative actions against fixture states without
  mutating active saves.
- Data structures: `ActionModTestCase`, `ActionModTestResult`, fixture state
  ref, expected deltas, expected event metadata, hidden leak report.
- API changes: run-test endpoint for action mod fixtures.
- Frontend changes: action test panel with pass/fail and safe diff.
- Tests: success/failure cases, fixture isolation, no active save mutation,
  no hidden text in normal result.
- Acceptance: Action Mods can be tested deterministically before enable/apply.

### 14. Rule Module Contract

- Goal: define safe contracts for deterministic rule modules and their declared
  state/event extensions.
- Data structures: `RuleModuleManifest`, rule type refs, lifecycle hooks,
  state schema extensions, event type declarations, compatibility metadata.
- API changes: rule module validate/list endpoints.
- Frontend changes: rule module summary and permission/compatibility warnings.
- Tests: unsafe lifecycle hooks rejected, direct DB access permissions rejected,
  state extension prefix validation, event type validation.
- Acceptance: Rule Modules are declarative contracts, not executable runtime
  code plugins.

### 15. Module Permission Model

- Goal: centralize extension permissions and enforce safe defaults.
- Data structures: `ModulePermissionPolicy`, `ExtensionPermissionSet`,
  permission review issue, permission risk level, allow/deny reason.
- API changes: permission validation APIs return blockers/warnings.
- Frontend changes: permission dashboard consumes permission summaries.
- Tests: dangerous permissions rejected, safe read-only metadata accepted,
  provider/LLM permissions blocked unless routed through Provider Gateway.
- Acceptance: no extension can request unsafe permissions silently.

### 16. Module Browser Backend

- Goal: provide local APIs for discovering, listing, validating, enabling, and
  reviewing extension packages.
- Data structures: module browser index, package summary, validation summary,
  compatibility summary, enabled state, source path ref.
- API changes: local authoring/studio routes for list/detail/validate/enable/
  disable/review.
- Frontend changes: consumed by Module Browser UI.
- Tests: enabled/disabled API behavior, empty root behavior, path traversal
  rejection, no `.env` read, no secrets in responses.
- Acceptance: backend can safely manage local extension metadata.

### 17. Module Browser Frontend

- Goal: provide a local studio view for extension packages and module safety.
- Data structures: frontend package summary, validation issue, permission
  summary, compatibility status, audit event summary.
- API changes: none beyond Module Browser Backend consumption.
- Frontend changes: package list, filters by kind/status/risk, details,
  validate button, enable/disable with confirmation, safe empty/disabled states.
- Tests: frontend build, no secret display, disabled API state, validation
  issues shown clearly.
- Acceptance: users can inspect extension packages without exposing hidden or
  debug data.

### 18. Mod Compatibility Matrix

- Goal: report compatibility across engine version, content schema, project
  mode, dependencies, conflicts, permissions, and package kind.
- Data structures: `ModCompatibilityMatrix`, package row, compatibility issue,
  blocker/warning category.
- API changes: compatibility matrix endpoint and CLI output.
- Frontend changes: matrix table in Module Browser.
- Tests: dependency missing, conflict active, engine version mismatch, schema
  mismatch, safe package passes.
- Acceptance: compatibility blockers are visible before enable/import.

### 19. Extension Certification Tool

- Goal: provide deterministic certification checks for extension packages.
- Data structures: `ExtensionCertificationReport`, certification profile,
  checklist item, failure reason, safe summary.
- API changes: certification endpoint and CLI command.
- Frontend changes: certification status badge and report detail.
- Tests: certified package passes, secret/executable/unsafe permission package
  fails, no LLM judge usage.
- Acceptance: certification is deterministic, local, and safe-summary only.

### 20. Mod Quality Gate

- Goal: integrate mod/package checks into the project quality gate.
- Data structures: quality category `mods`, mod quality issue, blocker
  definition, package coverage summary.
- API changes: Project Quality Gate can include mod checks.
- Frontend changes: quality dashboard shows mod blockers/warnings.
- Tests: unsafe permission blocker, executable blocker, secret blocker,
  invalid manifest blocker, compatibility blocker, safe package pass.
- Acceptance: unsafe extensions block release readiness.

### 21. Mod Import / Export Hardening

- Goal: harden extension import/export with explicit modes and strict file
  filtering.
- Data structures: import dry-run report, export mode, included section list,
  checksum map, rejected file report, duplicate id report.
- API changes: import/export endpoints for extension packages with dry-run and
  explicit confirm.
- Frontend changes: import/export review panel.
- Tests: zip slip rejected, executable rejected, `.env` rejected, database/log/
  cache/build outputs rejected, raw `state_deltas` rejected, import dry-run no
  writes.
- Acceptance: extension portability does not leak secrets or execute code.

### 22. Mod Permission Dashboard

- Goal: make extension permissions visible and reviewable before enable/apply.
- Data structures: permission dashboard summary, permission issue, package risk
  score, review state.
- API changes: permission summary endpoint.
- Frontend changes: dashboard by package, permission, risk, mode, and status.
- Tests: unsafe permissions displayed as blockers, safe permissions displayed
  clearly, no hidden/debug detail leakage.
- Acceptance: users can understand extension permissions without reading raw
  manifests.

### 23. Mod Audit Trail

- Goal: record local extension operations without storing secrets or hidden
  text.
- Data structures: `ModAuditRecord`, action type, actor, package ref, timestamp,
  safe summary, result, debug ref.
- API changes: audit list/detail endpoints for extension operations.
- Frontend changes: audit trail panel in Module Browser.
- Tests: discover/validate/import/export/enable/disable/certify/quality-gate
  audit records, append-only behavior, normal summary redaction.
- Acceptance: extension operations are traceable without replacing EventLog or
  leaking secrets.

### 24. v2.6 Integration Regression Tests

- Goal: verify Script / Mod Platform Pro works across Novel, Tavern, World,
  Cross-Mode, Provider Gateway, import/export, and quality gate boundaries.
- Data structures: integration fixtures for safe and unsafe packages,
  compatibility fixtures, action mod fixtures, audit fixtures.
- API changes: none beyond tested public APIs.
- Frontend changes: build verification for Module Browser and dashboards.
- Tests: full v2.6 integration matrix, no arbitrary code execution, no direct
  `GameState` mutation, no real provider calls, no secret leakage.
- Acceptance: `python -m pytest` and `cd frontend && npm.cmd run build` pass.

## Impact and Boundaries

### NarrativeProject

`NarrativeProject` gains a stable extension-package workspace concept and safe
references to imported packages, validation reports, compatibility status, and
audit records. Project exports must continue to exclude secrets, databases,
logs, caches, build outputs, raw prompts, raw `state_deltas`, and executable
payloads.

### Novel Studio

Novel Studio may consume prompt packs, narrative style mods, character packs,
and script packs. These packages can change drafting style, templates, and
authoring metadata only. They cannot turn Novel drafts into World facts without
Cross-Mode draft/proposal validation.

### Tavern Studio

Tavern Studio may consume character packs, RP profile mods, voice/style
metadata, scene mood presets, and prompt packs. These affect RP presentation
only. Tavern memories remain non-authoritative, and RP mods cannot modify World
state.

### World Mode / GameState

World Engine remains the fact source. Action Mods must flow through
`ActionRegistry`, return structured `ActionResult` / `StateDelta` proposals,
and rely on engine apply/event logic. Rule Modules declare schema and permissions
only. No mod may directly mutate `GameState` or bypass `EventLog`.

### Cross-Mode Bridge

Cross-Mode Bridge may reference extension packages as sources or targets for
draft/proposal review, but `CrossModeLink` remains a reference/review structure.
It cannot create authoritative facts or apply package changes by itself.

### Provider Gateway

Provider Gateway remains the only model entry. Provider Profile Packs may carry
non-secret provider metadata, model profiles, capability refs, routing tags, and
`api_key_env` / `secret_ref` references. They must never contain raw API keys,
header secrets, raw env, or provider tokens.

### LLM Boundary

LLMs may draft text, suggestions, package descriptions, validation summaries,
or authoring hints only through Provider Gateway. They cannot certify packages,
decide mod safety, execute package code, apply actions, mutate state, or act as
world judge.

### API Key / Provider Secret / Mod Package Security

Extension packages must reject `.env`, API keys, provider secrets, private keys,
database URLs, logs, caches, desktop outputs, raw prompts, raw `state_deltas`,
hidden/debug payloads in normal export, and executable files. Normal APIs,
frontend views, exports, quality reports, and audit trails must return safe
summaries only.

## v2.6 Integration Test Requirements

- Package manifest schema serialization/defaults and unsafe field rejection.
- Package repository/import/export path traversal and zip slip rejection.
- `.env`, API keys, provider secrets, databases, logs, caches, `node_modules`,
  `dist`, executable files, raw prompts, raw `state_deltas`, hidden/debug
  payload rejection.
- Script Pack, World Extension Pack, Character Pack, Prompt Profile Pack,
  Provider Profile Pack, Narrative Style Mod, and RP Profile Mod validation.
- Provider Profile Pack accepts `api_key_env` and `secret_ref` only.
- Action Mod registration through `ActionRegistry`.
- Action Mod output remains `ActionResult` / `StateDelta` and EventLog records
  are produced only through engine flow.
- Rule Module permission and schema checks.
- Module Browser backend/frontend disabled, empty, and error states.
- Compatibility matrix and certification reports.
- Mod Quality Gate blockers.
- Audit Trail append-only safe summaries.
- No real provider calls in tests.
- No arbitrary code execution in tests.
- Full validation:
  - `python -m pytest`
  - `cd frontend && npm.cmd run build`

## v2.6 Final Acceptance Criteria

- All 24 v2.6 modules are implemented or explicitly documented as out of scope
  for the release.
- Extension packages require manifests, validation, compatibility checks, and
  safe summaries.
- Action Mods can only register through `ActionRegistry`.
- Action Mods cannot directly modify `GameState` or bypass `StateDelta` /
  `EventLog`.
- Rule Modules declare permissions and schema; unsafe permissions are blocked.
- Provider Profile Packs do not store raw secrets.
- Import/export rejects zip slip, path traversal, executable files, `.env`,
  API keys, provider secrets, databases, logs, caches, `node_modules`, `dist`,
  raw prompts, and raw `state_deltas`.
- Module Browser backend/frontend are safe and build cleanly.
- Mod Quality Gate blocks unsafe extension packages.
- Audit Trail records extension operations with redacted normal summaries.
- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.

## v2.7 Candidate Directions

- Quality Studio Pro: unified quality dashboards, long-run regression matrices,
  release automation, package certification history, and cross-mode quality
  reporting.
- Desktop Packaging Pro: stronger local desktop distribution, backup/restore
  hardening, local update notes, workspace health automation, and crash/report
  UX.
- Default recommendation: if v2.6 lands the extension platform safely, v2.7
  should prioritize **Quality Studio Pro** so the growing Novel/Tavern/World/
  Cross-Mode/Provider/Mod surface has a unified release-quality layer.
