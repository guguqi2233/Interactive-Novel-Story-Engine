# v2.6 Release Notes: Script / Mod Platform Pro

## 1. Version Name

v2.6 Script / Mod Platform Pro.

## 2. Version Goal

v2.6 turns the existing local script, package, gameplay module, and mod
foundations into a unified Script / Mod Platform Pro layer.

The release focuses on local, declarative, manifest-led, validation-first, and
auditable extension packages. It supports script packs, world extension packs,
character packs, prompt/profile packs, provider profile packs, narrative/RP
style mods, declarative action mods, and rule module contracts without changing
World Engine authority.

v2.6 is not an online market, cloud plugin platform, arbitrary-code plugin
system, or sandbox runtime.

## 3. New Features

- Added `PackageManifestV2` as the shared manifest contract for v2.6 extension
  packages.
- Added package schemas and validators for:
  - Script Pack v2.
  - World Extension Pack.
  - Character Pack.
  - Prompt Profile Pack.
  - Provider Profile Pack.
  - Narrative Style Mod.
  - RP Profile Mod.
  - Declarative Action Mod.
  - Rule Module manifest contract.
- Added `ModulePermissionSet` with default-deny dangerous permissions.
- Added local Module Browser backend APIs.
- Added Module Browser and Permission Dashboard frontend surfaces.
- Added Mod Compatibility Matrix.
- Added local Extension Certification Tool.
- Added Mod Quality Gate.
- Added Mod Import / Export hardening.
- Added Mod Audit Trail.
- Added Action Mod Test Harness and CLI.
- Added v2.6 integration regression tests.

## 4. Behavior Changes

- Extension packages are treated as local package data, templates, profiles,
  style metadata, or controlled declarative DSL. They are not executable code.
- Dangerous permissions are blockers by default:
  - `execute_code`
  - `access_filesystem`
  - `access_network`
  - `read_secrets`
  - `write_database`
  - `modify_game_state_directly`
  - `bypass_visibility`
  - `call_llm`
- Import dry-run validates package shape without writing files.
- Import apply requires explicit confirmation and does not auto-enable
  high-risk modules.
- Module scanning reports unsafe packages without executing package contents.
- Forbidden local payloads such as `.env`, database files, logs, caches, and
  build outputs are rejected before their contents are read.

## 5. API Changes

New local module APIs under `/projects/{project_id}/modules...`:

- `GET /projects/{project_id}/modules`
- `GET /projects/{project_id}/modules/{package_id}`
- `POST /projects/{project_id}/modules/scan`
- `POST /projects/{project_id}/modules/{package_id}/validate`
- `GET /projects/{project_id}/modules/{package_id}/permissions`
- `GET /projects/{project_id}/modules/{package_id}/compatibility`
- `POST /projects/{project_id}/modules/compatibility-matrix`
- `POST /projects/{project_id}/modules/check-selection`
- `POST /projects/{project_id}/modules/{package_id}/certify`
- `POST /projects/{project_id}/modules/{package_id}/quality-gate`
- `GET /projects/{project_id}/modules/permissions-summary`
- `GET /projects/{project_id}/modules/audit`
- `GET /projects/{project_id}/modules/audit/{audit_id}`

The APIs return safe summaries, validation results, compatibility status,
permission risk, certification level, quality gate status, and audit records.
They do not execute packages or return secrets.

## 6. Frontend Changes

- Added a local Module Browser view.
- Added module list, scan, details, validation, permission, compatibility, and
  quality/certification status presentation.
- Added Mod Permission Dashboard with dangerous permission indicators.
- Added clear local-only messaging:
  - no online marketplace,
  - no arbitrary code execution,
  - no secret display,
  - no sensitive local path display.

Frontend build passed during v2.6 acceptance. Vite still emits the existing
chunk-size warning for the main JS bundle.

## 7. PackageManifestV2 Changes

`PackageManifestV2` is the common package contract for v2.6.

Supported package types:

- `script_pack`
- `world_extension_pack`
- `character_pack`
- `prompt_profile_pack`
- `provider_profile_pack`
- `narrative_style_mod`
- `rp_profile_mod`
- `action_mod`
- `rule_module`
- `template_pack`

The manifest includes structured package identity, versioning, engine version
range, target modes/worlds, dependencies, optional dependencies, conflicts,
permissions, included files, checksums, entry points, compatibility notes,
migration notes, and creation metadata.

Executable entry points are rejected. Entry points are metadata references, not
Python/JavaScript/shell execution hooks.

## 8. Script / World / Character / Prompt / Provider Pack Changes

Script Pack v2:

- Packages reusable scenarios, quest drafts, Novel/Tavern/Cross-Mode templates,
  and quality-check metadata.
- Validates manifest, refs, executable payloads, secrets, and hidden leak
  markers.
- Imports as drafts/templates only.

World Extension Pack:

- Supports additive content candidates and reviewed patch candidates.
- Covers locations, NPCs, items, quests, facts, factions, rumors, relationships,
  and optional patch declarations.
- Does not automatically apply to active worlds or mutate `GameState`.

Character Pack:

- Packages character profiles, Tavern character drafts, RP/Voice profiles,
  character cards, and World NPC draft candidates.
- Does not directly create or overwrite World NPCs.
- Keeps private notes out of public summaries.

Prompt Profile Pack:

- Packages mode-scoped prompt profiles and style presets.
- Cannot enable hidden fact access, state modification, action override, or
  visibility bypass.

Provider Profile Pack:

- Packages provider profile templates, model profiles, optional routing
  templates, and capability metadata.
- Allows `api_key_env` and `secret_ref` references.
- Rejects raw API keys, authorization headers, and secret literals.

## 9. Narrative / RP Style Mod Changes

Narrative Style Mod:

- Adds expression-only style metadata for Novel, Tavern, World narration, and
  Cross-Mode drafting.
- Can affect tone, pacing, perspective, sensory focus, sentence style, and
  length hints.
- Cannot alter world facts, override action results, create key items, complete
  quests, or access hidden facts.

RP Profile Mod:

- Adds or patches RP/Voice presentation profiles.
- Supports safe soft RP and voice profile changes.
- Cannot patch World NPC knowledge, hidden fact access, `GameState`, or hard
  character facts. Hard fact changes remain draft/proposal work.

Prompt, Narrative, and RP mods cannot expand LLM authority.

## 10. Action Mod / Rule Module Changes

Action Mod:

- Action Mods are declarative.
- They do not execute arbitrary code.
- They do not execute mod Python, JavaScript, shell scripts, binaries, or native
  code.
- They must register through `ActionRegistry`.
- They are evaluated through controlled preconditions, checks, outcomes, and
  `StateDelta` proposal templates.
- Action Mod state changes must flow through `ActionRegistry`, `StateDelta`, and
  `EventLog`.
- Action Mods cannot call LLMs, access the filesystem, access the network,
  access databases, or directly modify `GameState`.

Rule Module:

- `RuleModuleManifest` defines a contract for future rule systems.
- Rule Module is manifest-only in v2.6.
- It is not a runtime execution system.
- State schema extensions require validation and migration review.
- Runtime rule-module code execution and sandbox runtime are not implemented in
  v2.6.

## 11. Permission / Certification / Quality Gate Changes

- Added `ModulePermissionSet`.
- Dangerous permissions are rejected by default.
- Added Mod Compatibility Matrix for engine/schema compatibility, dependencies,
  conflicts, target worlds, target modes, permission risks, executables, and
  secrets.
- Added local Extension Certification levels:
  - `safe_content`
  - `safe_style`
  - `verified_action`
  - `experimental_rule_module`
  - `unsafe_blocked`
- Added Mod Quality Gate for manifest validation, permission validation,
  compatibility, executable rejection, secret rejection, action tests, pack
  safety, hidden leak risk, and migration impact warnings.
- Certification and Quality Gate are deterministic. They do not use LLMs as
  judges.

## 12. Import / Export Hardening Changes

- Import dry-run validates packages without writing files.
- Import apply requires explicit confirmation.
- Zip slip and path traversal are rejected.
- Executable payloads are rejected.
- Secrets are rejected.
- Duplicate package IDs are reported.
- Checksums are supported and validated.
- Export filters:
  - `.env`
  - API keys
  - provider secrets
  - database files
  - logs
  - caches
  - `node_modules`
  - frontend `dist`
  - desktop build outputs
  - executable payloads
- Provider Profile Pack export includes only safe references such as
  `api_key_env` and `secret_ref`, not resolved secret values.
- Mod audit records store safe summaries and do not include secrets.

## 13. Known Limitations

- v2.6 does not support arbitrary-code plugins.
- v2.6 does not execute mod Python or JavaScript.
- v2.6 does not implement a sandbox runtime.
- v2.6 does not implement an online marketplace, account system, cloud sync, or
  remote package download/execution.
- Rule Modules are contracts only, not executable runtime modules.
- Action Mod DSL is intentionally limited and declarative.
- Certification is local and advisory, not a third-party trust service.
- Hidden leak detection is deterministic and marker/schema based, not semantic
  classification.
- Import/export hardening does not implement package signing or full supply
  chain provenance.

## 14. Upgrade Notes from v2.5

- v2.5 projects can continue using Provider Gateway Pro unchanged.
- v2.6 adds module/package APIs and frontend module views, but does not require
  users to enable mods.
- Existing provider profiles must continue to store only `api_key_env` or
  `secret_ref`, not raw API keys.
- Existing content, Novel, Tavern, World, and Cross-Mode workflows remain under
  their previous authority boundaries.
- New v2.6 packages should use `PackageManifestV2` and pass validation before
  import.
- Action extensions should be migrated to declarative Action Mod definitions
  and registered through `ActionRegistry`.
- Rule-module-like ideas should be represented as `RuleModuleManifest` metadata
  only until a future runtime design exists.

## 15. Recommended v2.7 Direction

Recommended v2.7 direction: Quality Studio Pro.

Suggested priorities:

1. Unified quality dashboard across World, Novel, Tavern, Cross-Mode, Provider
   Gateway, and Script / Mod Platform checks.
2. Release readiness automation that aggregates acceptance reports, audits,
   compatibility reports, quality gates, and verification commands.
3. Deeper mod quality visualization for dependency graphs, permissions, action
   test coverage, migration impact, and certification status.
4. Stronger package provenance and optional signing/checksum workflows.
5. Expanded deterministic leak regression fixtures for prompt/style/RP/provider
   packages.

Advanced World Simulation Modules remain a viable later direction, but v2.7
should first make the expanded v2.1-v2.6 platform easier to validate, review,
and release safely.
