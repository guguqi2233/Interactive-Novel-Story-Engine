# v2.6 Acceptance Report: Script / Mod Platform Pro

## Verdict

Accepted with known limitations.

v2.6 Script / Mod Platform Pro is accepted as a local, declarative, manifest-led,
validation-first, and auditable extension platform for script packs, world
extension packs, character packs, prompt/profile packs, provider profile packs,
narrative/RP style mods, declarative action mods, and rule module contracts.

The release preserves the core project boundary: mods do not execute arbitrary
code, do not read secrets, do not directly mutate `GameState`, do not bypass
`ActionRegistry`, `StateDelta`, `EventLog`, Provider Gateway, visibility rules,
or quality gates, and do not use LLMs as safety judges or world judges.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Verification results:

- Backend: `1649 passed in 102.95s`
- Frontend: `npm.cmd run build` passed
- Frontend note: Vite reported the existing chunk-size warning for the main JS
  bundle. This is not a functional failure.

## Scope Accepted

Accepted v2.6 modules:

1. Script / Mod Platform Contract Review.
2. Package Manifest v2 Schema.
3. Script Pack v2.
4. World Pack Extension Pack.
5. Character Pack.
6. Prompt Profile Pack.
7. Provider Profile Pack.
8. Narrative Style Mod.
9. RP Profile Mod.
10. Declarative Action Mod Core Schema.
11. Action Registry Mod Integration.
12. Declarative Action Preconditions / Checks / Outcomes DSL.
13. Action Mod Test Harness.
14. Rule Module Contract.
15. Module Permission Model.
16. Module Browser Backend.
17. Module Browser Frontend.
18. Mod Compatibility Matrix.
19. Extension Certification Tool.
20. Mod Quality Gate.
21. Mod Import / Export Hardening.
22. Mod Permission Dashboard.
23. Mod Audit Trail.
24. v2.6 integration regression tests.

Accepted public surfaces:

- Local Module Browser APIs under `/projects/{project_id}/modules...`.
- Local module scan, detail, validation, permission, compatibility, quality gate,
  certification, permission summary, and audit APIs.
- `PackageManifestV2` and v2.6 package schemas for supported extension types.
- `ModulePermissionSet` and deterministic permission validation.
- Declarative Action Mod schema, registry integration, evaluator, and test
  harness.
- Rule Module manifest contract. Runtime execution remains out of scope.
- Mod import/export dry-run and confirmed import hardening.
- CLI tools:
  - `python -m backend.app.tools.test_action_mod <mod_path> --json`
  - `python -m backend.app.tools.certify_extension <package_path> --json`
  - `python -m backend.app.tools.mod_quality_gate <package_path> --json`
- Frontend Module Browser and Mod Permission Dashboard.

## Boundary Review

### Package Contracts

- `PackageManifestV2` is the common v2.6 manifest contract.
- Package types cover `script_pack`, `world_extension_pack`, `character_pack`,
  `prompt_profile_pack`, `provider_profile_pack`, `narrative_style_mod`,
  `rp_profile_mod`, `action_mod`, `rule_module`, and `template_pack`.
- Executable entry points and executable payloads are rejected.
- Permissions are structured through `ModulePermissionSet`.
- Dangerous permissions are blockers in v2.6, including `execute_code`,
  `access_filesystem`, `access_network`, `read_secrets`, `write_database`,
  `modify_game_state_directly`, `bypass_visibility`, and `call_llm`.

### Pack Types

- Script Pack v2 validates reusable scenarios, quest drafts, Novel/Tavern/
  Cross-Mode templates, and quality-check metadata as package data.
- World Extension Packs support additive and reviewed patch candidates, but do
  not automatically apply to active worlds.
- Character Packs package character profiles, Tavern drafts, RP/Voice profiles,
  character cards, and World NPC draft candidates without directly creating or
  overwriting World NPCs.
- Prompt Profile Packs cannot grant hidden fact access, state modification,
  action override, or visibility bypass.
- Provider Profile Packs allow `api_key_env` / `secret_ref` references but reject
  raw API keys and authorization headers.
- Narrative Style Mods are expression-only and cannot alter world facts, action
  results, quests, or key items.
- RP Profile Mods can adjust presentation fields but cannot patch NPC knowledge
  or hidden fact access.

### Action Mod

- Action Mods define declarative actions and register through `ActionRegistry`.
- The registry rejects core action ID conflicts and detects alias conflicts.
- The evaluator supports controlled declarative preconditions, checks, outcomes,
  and `StateDelta` proposal templates.
- Mod action execution returns `ActionResult` plus event metadata. Active world
  changes remain engine-owned.
- State changes must flow through `StateDelta`; mod action events are recorded
  through `EventLog`.
- The implementation and tests reject `eval`, `exec`, arbitrary code,
  `call_llm`, filesystem, network, and direct database behavior.

### Rule Module

- `RuleModuleManifest` is available as a contract-only manifest for future rule
  systems such as magic, hacking, crafting, deduction, or similar modules.
- Dangerous permissions are denied by default and rejected when enabled.
- Rule Modules do not execute runtime code in v2.6.
- State schema extension declarations trigger migration/review warnings instead
  of mutating state.

### Module Browser / Compatibility / Certification

- Module Browser backend scans local allowed directories and returns safe
  summaries only.
- Module Browser frontend displays local package details, validation status,
  compatibility status, permission risk, and safety notes.
- Module Browser does not execute package contents and does not read forbidden
  local payloads such as `.env`, database, log, or cache files.
- Compatibility Matrix detects engine/schema mismatch, missing dependencies,
  conflicts, target mode/world mismatch, dangerous permissions, executable
  payloads, and secret risks.
- Extension Certification classifies packages into local advisory levels such
  as `safe_content`, `safe_style`, `verified_action`,
  `experimental_rule_module`, or `unsafe_blocked`.
- Unsafe packages are blocked by certification and quality gate paths.

### Quality / Import Export / Audit

- Mod Quality Gate validates manifest safety, permissions, compatibility,
  executable files, secrets, package-specific safety, action tests, and migration
  impact warnings.
- Import dry-run validates manifests, checksums, zip slip, executable payloads,
  forbidden paths, duplicate package IDs, permissions, compatibility, and
  secrets without writing package files.
- Import apply requires explicit confirmation and does not auto-enable
  high-risk modules.
- Export filters `.env`, API keys, provider secrets, database files, logs,
  caches, `node_modules`, frontend `dist`, desktop outputs, and executable
  payloads.
- Provider Profile Pack export preserves only safe references such as
  `api_key_env` and `secret_ref`, not resolved secrets.
- Mod Audit Trail records scan, validate, certify, quality gate, import/export,
  and reject-style operations with safe summaries and without secrets.

### Core Boundaries

- LLMs remain the language layer only.
- World Engine remains the authoritative fact source.
- Mods cannot directly modify `GameState`.
- Action Mods must go through `ActionRegistry`.
- `StateDelta` / `EventLog` remain the world-change boundary.
- Provider Gateway remains the only model entry.
- API keys do not enter frontend, export packages, project files, provider
  profiles, mod packages, logs, or audit summaries.
- Tests use local deterministic fixtures, mock/local-stub provider behavior, and
  do not call real APIs.
- No arbitrary-code plugin execution path is accepted in v2.6.

## Known Limitations

1. v2.6 is not an online marketplace, cloud sync platform, account system,
   remote package downloader, or arbitrary-code plugin runtime.
2. Rule Modules are manifest/contract-only. They do not execute runtime rule
   code in v2.6.
3. Action Mod DSL is intentionally limited to deterministic declarative
   preconditions, checks, outcomes, and `StateDelta` proposals.
4. Certification is local and advisory. It is not a cryptographic trust system
   or external review service.
5. Hidden leak checks are deterministic marker/schema checks, not semantic
   classifiers.
6. Import/export hardening rejects unsafe package shapes but does not implement
   complex package signing or supply-chain provenance.
7. Confirmed import writes package files into the local project module area, but
   does not auto-enable high-risk modules.
8. Frontend build still emits the existing Vite chunk-size warning.

## Acceptance Risks

No high-risk release blocker remains after the final security hardening pass.

Residual non-blocking risks:

- Audit redaction should continue to be hardened for future generic
  authorization/header-like secret strings, even though current audit paths use
  controlled safe summaries.
- Future runtime Rule Module support would require a new sandbox design,
  permission model review, security audit, and acceptance boundary.
- Future richer Action Mod DSL features must keep the no-code-execution and
  no-direct-GameState-mutation boundary.
- Future install/enable flows must keep the validation, compatibility,
  certification, quality gate, explicit confirmation, and audit sequence intact.

## Recommended v2.7 Priorities

1. Quality Studio Pro: unified quality dashboard for World, Novel, Tavern,
   Cross-Mode, Provider Gateway, and Script/Mod Platform checks.
2. Release readiness automation that aggregates acceptance reports, audits,
   quality gates, compatibility reports, and frontend/backend verification.
3. Stronger package provenance and optional signing/checksum workflows.
4. Deeper mod quality visualization for dependency graphs, permission risk,
   action test coverage, and migration impact.
5. Expanded deterministic leak detection fixtures for prompt/style/RP/provider
   package content.

## Final Status

v2.6 is accepted for release preparation.

The verified implementation satisfies the Script / Mod Platform Pro goals while
preserving the project boundaries: no arbitrary code execution, no secret access,
no direct `GameState` mutation, no ActionRegistry bypass, no StateDelta/EventLog
bypass, no Provider Gateway bypass, no real API calls in tests, and no LLM-based
world or safety authority.
