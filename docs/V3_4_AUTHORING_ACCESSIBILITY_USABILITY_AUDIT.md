# v3.4 Authoring Accessibility / Usability Audit

Verification date: 2026-05-24

This audit reviews the v3.4 Authoring / Mod UI Pro user experience after the
v3.4 privacy, mod security, StateDelta/GameState boundary, acceptance, and
release notes passes. It is documentation-only and does not modify business
code or tests.

## 1. Audit Scope

Reviewed v3.4 Authoring / Mod UI areas:

- Authoring Workspace
- World Pack Editor
- Script Pack Editor
- Character Pack Editor
- Quest Graph Editor
- Location / Map Authoring
- NPC / Faction / Relationship Authoring
- Item / Economy / Trade Authoring
- Rumor / Crime / Consequence Authoring
- Advanced Module Authoring Panels
- Action Mod Editor
- Action Mod Test Harness UI
- Rule Module Contract UI
- Module Browser Pro
- Permission Dashboard
- Compatibility Matrix
- Certification UI
- Import / Export Wizard
- Mod Quality Gate UI
- Authoring Validation Dashboard
- Diff / Preview / Dry-Run UX
- Audit Trail UI
- Backup / Restore UX
- Safe Apply Workflow

Reviewed supporting artifacts:

- `README.md`
- `docs/SPEC.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `docs/CONTENT_PACKS.md`
- `docs/CONTRACT_INDEX.md`
- `docs/V3_4_ROADMAP.md`
- `docs/V3_4_ACCEPTANCE_REPORT.md`
- `docs/V3_4_RELEASE_NOTES.md`
- `docs/V3_4_AUTHORING_MOD_UI_CONTRACT_REVIEW.md`
- `docs/V3_4_AUTHORING_UI_PRIVACY_VISIBILITY_AUDIT.md`
- `docs/V3_4_MOD_PERMISSION_SECURITY_AUDIT.md`
- `docs/V3_4_AUTHORING_STATEDELTA_GAMESTATE_BOUNDARY_AUDIT.md`
- `frontend/src/App.tsx`
- `frontend/scripts/check-v34-authoring-ui.mjs`
- `backend/tests/test_v34_integration_regression.py`

## 2. Passed Checks

### Page Titles And Navigation

- Authoring Workspace surfaces use clear labels such as Authoring Workspace,
  World Pack, Script Pack, Character Pack, Quest Graph, Locations, NPC/Faction,
  Items/Economy, Rumors/Crime, Modules, Import/Export, Quality, Audit, Backup,
  and Safe Apply.
- Module Browser Pro, Permission Dashboard, Compatibility Matrix, Certification
  UI, Mod Quality Gate UI, Authoring Validation Dashboard, Audit Trail, Backup /
  Restore, and Safe Apply Workflow are discoverable from the Authoring / Mod
  workspace area.

### Primary Actions

- Main action labels are understandable: Scan local modules, Validate package,
  Run Tests, Run Gate, Import Dry-run, Explicit Import, Export, Preview,
  Validate, Save, Apply, and Safe Apply.
- Dangerous or writing actions use confirmation language and are framed as local
  content/project/package operations, not active world-session operations.

### Empty, Error, And Disabled States

- Empty states consistently provide next steps such as scan local modules, run
  validation, select a package, load an editor, adjust filters, or generate a
  preview.
- Error states use safe display helpers and avoid raw stack traces, raw env,
  provider secrets, full sensitive paths, hidden facts, and raw `state_deltas`.
- Disabled states explain local API availability, missing package/module
  selection, not-run validation state, missing test report, blocked package
  state, or debug/API gating where relevant.

### Validation And Quality Usability

- Validation errors are shown with severity, code/path/entity-oriented context,
  and redacted safe summaries.
- Authoring Validation Dashboard groups issues by useful authoring categories:
  world pack, script pack, character pack, quest graph, locations,
  NPC/factions/relationships, items/economy, rumors/crime/consequences, action
  mods, rule modules, and import/export.
- Quality gate blockers and warnings are visible in Mod Quality Gate and module
  package review surfaces.
- Quality and validation reports are now passed through redaction before normal
  UI display, following the v3.4 privacy blocker fix.

### Dry-Run, Preview, Confirm, And Safe Apply

- Import, apply, export, backup, restore, merge, template apply, and package
  flows communicate dry-run or preview before write behavior.
- Safe Apply Workflow explicitly lists select draft/package, validate, quality
  gate, diff preview, dry-run, explicit confirm, local apply, and audit record.
- Destructive or writing actions are presented with confirm requirements.
- Safe Apply is described as writing local content/project/package files only;
  it does not directly modify active `GameState`.

### Visibility Labels

- Hidden, authoring-only, and player-visible concepts are separated in copy.
- Authoring-only preview details are redacted and labeled so users do not
  confuse draft/internal review with player-safe preview.
- Player-facing preview language avoids claiming that hidden facts, NPC secrets,
  hidden objectives/truth, hidden witness data, hidden item properties, debug
  memory, raw prompts, or raw `state_deltas` are visible.

### Permission, Compatibility, And Certification Clarity

- Permission risk is understandable through allowed/blocked state, risk level,
  reason, and affected package summary.
- Dangerous permissions are fixed and named: `execute_code`,
  `access_filesystem`, `access_network`, `read_secrets`, `write_database`,
  `modify_game_state_directly`, `bypass_visibility`, and `call_llm`.
- Compatibility Matrix presents package compatibility, blockers/warnings, and
  load-order draft summaries without executing packages.
- Certification UI presents local advisory levels such as `safe_content`,
  `safe_style`, `verified_action`, `experimental_rule_module`, and
  `unsafe_blocked`, without claiming online trust or absolute safety.

### Local-First And Security Copy

- The UI repeatedly states local-only, no online marketplace, no remote
  download, and no arbitrary code execution.
- Provider profile flows direct users to `api_key_env` / `secret_ref` instead
  of plaintext API keys.
- Import/export copy clearly states filtering for `.env`, API keys, provider
  secrets, database files, logs/cache, build outputs, debug reports,
  executable payloads, and mature/private content.

## 3. Risks / Issues

### High-Risk Usability Issues

No high-risk usability issue was found that blocks v3.4 release.

The major privacy/usability confusion identified earlier, raw authoring preview
and validation report text being displayed too directly, has been fixed by
redacted authoring preview helpers, redacted report rendering, the updated
`check:v34-authoring-ui` script, and v3.4 integration-regression assertions.

### Medium-Risk Usability Issues

1. Older authoring save endpoints are not all unified under one shared Safe
   Apply backend contract.
   - The UI communicates validation and confirmation, and these paths write
     content files rather than active `GameState`.
   - A future shared backend Safe Apply request would make the mental model
     simpler and harder to misuse.

2. Action Mod Editor still includes some JSON-oriented structured fields.
   - The UI and backend keep these declarative and non-executing.
   - Users would benefit from fully field-level rows for conditions/checks to
     reduce confusion and paste errors.

3. Large package navigation can become dense.
   - Module Browser filters and workspace navigation help, but very large local
     package sets may still require better section search, pinned items, and
     entity-level breadcrumbs.

### Low-Risk Usability Issues

1. Some panels are summary-heavy.
   - The v3.4 scope prioritizes safety and manageability over rich visual
     editors. More inline help and progressive disclosure would improve comfort
     without changing release readiness.

2. Keyboard workflows are basic.
   - Major actions are visible, but editor-level keyboard shortcuts, focus
     management, and command palette style navigation are future polish items.

3. Certification remains advisory.
   - The UI uses correct language, but users may still need repeated reminders
     that local certification is not online signing, marketplace trust, or an
     absolute guarantee.

4. Frontend build reports a chunk-size warning.
   - This does not affect usability correctness, but route/component splitting
     would improve load performance and maintainability later.

## 4. Required Fixes

No release-blocking accessibility or usability issue remains for v3.4.

The current v3.4 UI is sufficiently understandable for the accepted scope:
local authoring drafts, local package review, validation, dry-run/preview,
explicit confirmation, safe import/export, permission review, compatibility,
local advisory certification, quality gate, audit, backup/restore, and Safe
Apply.

## 5. Non-Blocking Follow-Ups

The following follow-ups are recommended but not required for v3.4 release:

- Unify older authoring save APIs under a shared Safe Apply backend contract.
- Add editor-level keyboard shortcuts for frequent authoring actions.
- Add richer inline validation hints next to individual editor fields.
- Improve navigation for large packages with breadcrumbs, pinned sections, and
  faster entity search.
- Replace remaining Action Mod JSON-oriented condition/check fields with fully
  structured row editors.
- Continue improving progressive disclosure for authoring-only, player-visible,
  and debug-only concepts.
- Split the frontend bundle to address the Vite chunk-size warning.

## 6. Release Decision

Release decision: Not blocked.

No release-blocking accessibility or usability issue remains for v3.4. v3.4 can
proceed to final freeze once this audit exists and tests/build remain passing.

The release remains local-first. It does not add an online marketplace, remote
package download, account system, cloud sync, arbitrary-code plugin runtime, or
Authoring UI direct mutation of active `GameState`. Authoring outputs remain
drafts, content-pack candidates, package candidates, or proposals until
validation, dry-run/preview, and explicit confirmation complete.
