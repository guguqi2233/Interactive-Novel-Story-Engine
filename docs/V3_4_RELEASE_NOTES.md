# v3.4 Release Notes: Authoring / Mod UI Pro

## 1. Version Name

v3.4 **Authoring / Mod UI Pro**

## 2. Version Goal

v3.4 turns Authoring Studio and the local Mod Platform into a more manageable
local creation workspace. The release focuses on safer world/script/character
pack authoring, content editor polish, Action Mod authoring, Rule Module
contract review, Module Browser clarity, permission review, compatibility,
local advisory certification, import/export, Mod Quality Gate, validation,
diff/preview/dry-run, audit trail, backup/restore, and Safe Apply workflows.

v3.4 remains local-first. It is not an online marketplace, remote package
registry, remote package auto-download system, account system, cloud sync
feature, multiplayer collaboration tool, arbitrary-code plugin system, or new
World Engine authority layer.

## 3. New Authoring / Mod UI Capabilities

- Authoring Workspace Shell with local authoring navigation, central editor
  area, right validation/preview/permission/quality context, and local safety
  status copy.
- World Pack, Script Pack, and Character Pack authoring surfaces.
- Quest Graph, Location / Map, NPC / Faction / Relationship, Item / Economy /
  Trade, and Rumor / Crime / Consequence authoring panels.
- Advanced Module authoring/review panels for local module status, validation,
  action, migration, and quality summaries.
- Action Mod Editor for declarative action definitions.
- Action Mod Test Harness UI for local safe pass/fail summaries.
- Rule Module Contract UI for contract-only review.
- Module Browser Pro with filters, scan, validation, permission, compatibility,
  certification, and quality summaries.
- Mod Permission Dashboard Pro.
- Compatibility Matrix UI Pro.
- Extension Certification UI Pro for local advisory certification.
- Import / Export Wizard Pro.
- Mod Quality Gate UI Pro.
- Authoring Validation Dashboard.
- Authoring Diff / Preview / Dry-Run UX.
- Authoring Audit Trail UI.
- Authoring Backup / Restore UX.
- Authoring Safe Apply / Publish-to-Local Workflow.
- v3.4 frontend regression check: `check:v34-authoring-ui`.
- v3.4 integration regression tests.

## 4. Behavior Changes

- Authoring work is presented as draft / candidate / proposal work until it is
  validated and explicitly applied to local content/project files.
- Normal Authoring UI now uses redacted preview/report rendering for authoring
  previews, validation reports, module quality reports, and dry-run summaries.
- Import/export and Safe Apply flows are more explicit about validation,
  dry-run/preview, blockers, filtering policy, and confirmation.
- Module and package review surfaces consistently state local-only,
  no-marketplace, no-remote-download, and no-execution boundaries.
- Action Mod authoring remains declarative and includes additional code-like
  token rejection in frontend JSON helpers.
- Rule Module review remains contract-only and does not expose runtime
  execution.

## 5. Frontend Changes

- Expanded Authoring / Mod UI Pro integration in `frontend/src/App.tsx`.
- Added or enhanced authoring workspace, module browser, permission dashboard,
  compatibility, certification, quality, validation, diff, audit, backup, and
  safe-apply panels.
- Added redacted authoring preview helpers for YAML/JSON/report displays.
- Added Action Mod Test Harness UI wiring.
- Added v3.4 static frontend safety check in
  `frontend/scripts/check-v34-authoring-ui.mjs`.
- Added npm script `check:v34-authoring-ui`.
- Updated supporting UI and safety copy across Novel/Tavern/World/Authoring
  regression checks where needed to preserve prior UI Pro boundaries.

## 6. Backend API Changes

v3.4 mostly reuses existing authoring, content validation, package, module, and
quality APIs.

Backend-side changes include safe additions/hardening around:

- Action Mod validation and test reporting.
- Character pack import/export safety.
- Authoring / Mod safe API integration paths.
- v3.4 integration regression coverage.

No backend change turns Authoring UI into active `GameState` mutation. No API
change introduces arbitrary code execution, remote package download, online
marketplace behavior, account sync, or cloud sync.

## 7. Content Editor Changes

- World Pack authoring supports local draft/preview/validation workflow for
  generated world content and content-pack candidates.
- Script Pack authoring supports local package build/export review as data
  package workflow, not executable scripts.
- Character Pack authoring supports safe character/RP/Tavern-oriented import
  and export surfaces without automatically overwriting World NPCs.
- Quest Graph editor supports stage/objective editing, validation issue display,
  scenario draft generation, and confirmed save behavior.
- Location / Map authoring supports generated location previews and validation.
- NPC / Faction / Relationship authoring supports content graph editing and
  validation-oriented local workflows.
- Item / Economy / Trade authoring supports item/economy content graph editing,
  preview, validation, and balance checks.
- Rumor / Crime / Consequence authoring supports rumor and consequence graph
  editing with safe validation and preview.

All editor flows are content-authoring flows. They do not directly modify active
runtime `GameState`, complete active quests, move players, alter active NPC
state, change active economy state, or change player inventory.

## 8. Mod UI Changes

- Action Mod Editor now presents declarative action metadata, targets,
  preconditions/checks/outcomes, event type, visibility policy, and preview/test
  entry points.
- Action Mod Test Harness UI shows local safe test report summaries:
  pass/fail, expected/actual result type, StateDelta safe summary, EventLog
  tags, and hidden-leak warnings.
- Rule Module Contract UI reviews module id, version, provided systems, state
  schema extensions, actions/rules, permissions, compatibility notes, and
  migration warnings as contract data only.
- Module Browser Pro clarifies local package review, validation, permission
  risk, compatibility, certification, and quality status.
- Mod Quality Gate UI shows manifest, permissions, compatibility, secrets,
  executable files, action tests, hidden leaks, and migration impact categories.

v3.4 does not execute module packages, run Rule Module code, run package Python
or JavaScript, or enable arbitrary-code plugins.

## 9. Permission / Compatibility / Certification Changes

- Permission Dashboard shows dangerous permissions:
  `execute_code`, `access_filesystem`, `access_network`, `read_secrets`,
  `write_database`, `modify_game_state_directly`, `bypass_visibility`, and
  `call_llm`.
- Dangerous permissions are displayed as blocked by default. The UI does not
  provide a runtime override or "enable dangerous permission" control.
- Compatibility Matrix shows engine/schema/dependency/conflict/target
  world/permission/action/state namespace compatibility summaries and load
  order draft information.
- Extension Certification is local advisory certification only. It does not
  upload packages, perform online signing, claim marketplace trust, or provide
  an absolute safety guarantee.

## 10. Import / Export / Safe Apply Changes

- Import Wizard shows local package selection, manifest validation, permission
  review, compatibility review, quality status, dry-run preview, and confirm
  import flow.
- Export Wizard shows package type/content selection, filtering policy, manifest
  preview, and confirm export flow.
- Default import/export filtering excludes `.env`, API keys, provider secrets,
  database files, logs/cache, `node_modules`, `dist`, debug reports, executable
  payloads, mature/private content, and unsafe paths.
- Provider Profile Pack export/import is restricted to `api_key_env` /
  `secret_ref` style references and rejects plaintext provider keys.
- Safe Apply Workflow presents select draft/package, validate, quality gate,
  diff preview, dry-run, explicit confirm, local apply, and audit steps.
- Safe Apply writes only local content/project/package files after confirmation;
  it does not write active saves or directly modify active `GameState`.

## 11. Validation / Quality / Audit Changes

- Authoring Validation Dashboard aggregates issue categories across world pack,
  script pack, character pack, quest graph, locations, NPC/factions/
  relationships, items/economy, rumors/crime/consequences, action mods, rule
  modules, and import/export.
- Validation and quality issue text is redacted before normal UI display.
- Authoring Diff / Preview / Dry-Run UX separates safe summaries from
  authoring-only redacted preview content.
- Audit Trail UI shows local authoring audit records as safe summaries. It does
  not replace World `EventLog`.
- Backup / Restore UX states local-only backup policy, default exclusions,
  dry-run requirement, conflict warning, and confirm-required restore behavior.

## 12. Privacy / Visibility / Boundary Changes

Accepted v3.4 boundaries:

- Authoring UI does not directly modify active `GameState`.
- Apply/import workflows require validation, dry-run or preview, and explicit
  confirmation before writing local project/content/package files.
- World Engine remains the fact source.
- Active world changes still flow through backend World Engine actions,
  `StateDelta`, and `EventLog`.
- Action Mods remain declarative and continue through `ActionRegistry`,
  `ActionResult`, `StateDelta`, and `EventLog` at runtime.
- Rule Modules remain contract-only.
- Mod UI does not execute arbitrary code.
- Module Browser and Import Wizard scan/validate metadata/packages without
  executing package contents.
- API keys do not enter frontend code, exports, logs, packages, provider
  profile packs, or documentation examples.
- Normal Authoring UI does not render hidden facts, NPC secrets, debug memory,
  raw prompts, raw env, provider secrets, API keys, or raw `state_deltas`.
- Authoring previews are redacted and labeled authoring-only where full draft
  context may exist.
- No online marketplace, remote package auto-download, account system, cloud
  sync, multi-user collaboration, arbitrary-code plugin workflow, or online
  publishing entry was added.
- Tests use local/mock paths and do not call real provider APIs or execute
  unknown mod code.

## 13. Known Limitations

- v3.4 is not a new World Engine, save system, provider, or runtime mod
  execution release.
- v3.4 does not implement online marketplace, remote package registry, remote
  package auto-download, account system, cloud sync, or multiplayer
  collaboration.
- Rule Modules remain contract-only; no sandbox runtime exists.
- Action Mod editing still includes some JSON-oriented structured fields.
  Obvious code-like tokens are blocked in UI helpers and backend validation
  keeps runtime action handling declarative, but future polish should replace
  the remaining JSON fields with full field-level controls.
- Some older low-level authoring save APIs can write local content files when
  validation passes and are not all normalized into one shared Safe Apply
  backend contract. They do not mutate active `GameState`, but should be
  unified in a future release.
- `docs/V3_4_AUTHORING_ACCESSIBILITY_USABILITY_AUDIT.md` was not present during
  acceptance. Usability acceptance is based on roadmap criteria, visible UI
  states, and regression/build results.
- Frontend production build emits a Vite chunk-size warning. The build succeeds;
  code-splitting remains future polish.

## 14. Upgrade Notes from v3.3

- v3.3 focused on World Studio UI Pro. v3.4 adds Authoring / Mod UI Pro on top
  of that without changing World Engine fact authority.
- Existing World, Novel, and Tavern workflows remain local-first and keep their
  prior boundaries.
- Use the new Authoring / Mod workspace for content-pack and package review
  rather than expecting authoring edits to alter an active world session.
- Review v3.4 import/export filtering before sharing packages. Provider
  profiles should contain only `api_key_env` or `secret_ref`, never real keys.
- Run v3.4 checks before release or packaging:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v34-authoring-ui
```

## 15. Recommended v3.5 Direction

Recommended v3.5 theme: **Local QA / Debug / Replay UI Pro**.

Suggested priorities:

- Consolidate local QA, debug, replay, timeline, diagnostics, and quality
  surfaces into a clearer workspace.
- Add a shared backend Safe Apply contract for all authoring editor writes.
- Complete the missing v3.4 Authoring Accessibility / Usability audit and fold
  findings into v3.5/v3.6 polish.
- Move more redaction/report-safety guarantees into backend validator contracts.
- Replace remaining Action Mod JSON textareas with fully field-level condition
  and check editors.
- Continue tightening normal/debug separation for raw state, raw deltas, and
  sensitive reports.
- Address the frontend chunk-size warning through route/component splitting.
