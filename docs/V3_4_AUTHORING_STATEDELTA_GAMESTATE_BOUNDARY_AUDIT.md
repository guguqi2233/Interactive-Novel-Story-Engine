# v3.4 Authoring StateDelta / Active GameState Boundary Audit

Verification date: 2026-05-24

Scope: v3.4 Authoring / Mod UI Pro boundary between authoring drafts/content-pack writes and active runtime `GameState`, `StateDelta`, and `EventLog`.

This audit is documentation-only. It does not modify business code.

## Reviewed Areas

- `frontend/src/App.tsx`
- `backend/app/main.py`
- `backend/app/engine/content/validation_gate.py`
- `backend/app/engine/content/world_pack_wizard.py`
- `backend/app/engine/content/world_merge.py`
- `backend/app/engine/actions/declarative.py`
- `backend/app/engine/action_registry.py`
- `backend/app/engine/rule_module_contract.py`
- `backend/app/platform/mod_import_export.py`
- `backend/tests/test_v34_integration_regression.py`
- `docs/V3_4_ROADMAP.md`

## Passed Items

1. Authoring UI does not directly modify active `GameState`.
   - The v3.4 authoring UI presents drafts, previews, validation, diff, import/export, backup, audit, and safe-apply concepts as local authoring workflows.
   - The UI copy explicitly states that authoring does not modify active `GameState`.

2. World Pack preview does not write active saves.
   - `/authoring/production/world-pack/preview` returns `writes_to_disk=False` and `applied=False`.
   - v3.4 integration tests assert the draft world directory is not created by preview.

3. Quest Graph preview does not alter active quest state.
   - `/authoring/worlds/{world_id}/quests/graph/preview` builds a YAML preview and validation result from the submitted graph.
   - v3.4 integration tests mutate the quest graph draft title, call preview, and then confirm active `/game/state/{session_id}` visible state is unchanged.

4. NPC/faction/social authoring routes target authoring content graphs, not active runtime NPC/faction state.
   - NPC goal/social graph save paths operate through authoring services and local YAML/content graph writers.
   - Frontend save flows use validation and confirmation prompts before writing local content files.

5. Item/economy authoring does not directly change player inventory.
   - Item/economy editor copy and save flow are authoring-file oriented.
   - There is no observed UI path that increments/decrements player inventory or modifies active save inventory directly from item/economy authoring.

6. Economy authoring does not directly change active `economy_sim` runtime state.
   - Economy authoring is grouped with item/economy content graph editing.
   - Runtime economy changes remain in world/module rule flows, not authoring UI.

7. Safe apply/import package flow has dry-run and confirm gates.
   - `/authoring/import/packages/dry-run` performs dry-run without writing.
   - `/authoring/import/packages/apply` calls the import service with `confirm_apply`; missing confirmation returns an error.
   - v3.4 integration tests assert package import dry-run does not create imported worlds and apply without confirmation is blocked.

8. Safe apply targets local project/content/package files, not active runtime `GameState`.
   - Import/export services and authoring writers operate on package archives, project roots, modules, worlds directory files, or content YAML.
   - v3.4 tests compare active `/game/state/{session_id}` before and after authoring dry-run/import flows and assert equality.

9. Action Mod editor does not directly register actions into an active game session.
   - The editor sends drafts to preview/validate/export/test endpoints.
   - Backend Action Mod registration goes through `ActionRegistry.register_mod_action`; the editor preview/test paths report `active_game_state_modified=False`.

10. Rule Module UI does not modify module runtime state.
    - Rule Modules are represented by `RuleModuleManifest` contracts.
    - Dangerous runtime permissions such as code execution, LLM calls, filesystem access, and network access are rejected.
    - v3.4 UI marks Rule Modules as contract-only.

11. Diff/preview paths are non-writing by design.
    - World Pack preview, file preview, map preview, quest preview, NPC/social/item/rumor preview, import dry-run, and package dry-run routes return preview/validation summaries rather than applying active runtime state.

12. Restore/apply destructive changes are confirmation-gated in the main local and import flows.
    - Local backup restore has dry-run and apply-confirmed service paths.
    - Package import apply requires `confirm_apply`.
    - Frontend destructive authoring actions use `confirmDangerousAction`.

13. Active World changes still flow through World Engine / `StateDelta` / `EventLog`.
    - Runtime player/world-changing actions remain under `/game/input` and World Engine action handlers.
    - Declarative Action Mods generate `ActionResult.state_deltas` and `Event` records when used at runtime.

14. Tests cover active state unchanged for v3.4 authoring boundaries.
    - `test_v34_authoring_safe_apis_and_dry_runs_do_not_modify_active_game_state` compares active visible state before/after world pack preview, script build dry-run, character import dry-run, quest preview, validation graph, and map graph calls.
    - `test_v34_import_export_safe_apply_boundaries_and_active_state` compares active visible state before/after export/import dry-run and blocked apply.

## High-Risk Issues

No direct active `GameState` mutation path was found in the reviewed v3.4 Authoring / Mod UI Pro surfaces.

No path was found where World Pack, Quest Graph, NPC/Faction, Item/Economy, Rule Module, Diff/Preview, or Import dry-run directly applies `StateDelta` or writes runtime session state.

## Medium-Risk Issues

1. Some legacy authoring content-file save endpoints are validation-gated but not uniformly dry-run-plus-explicit-confirm enforced by the backend for clean writes.
   - Examples include direct authoring file/map/quest/social/item/rumor save routes that can write local content files when validation passes. Several return `confirmation_required` only when warnings exist.
   - The frontend generally wraps these saves with `confirmDangerousAction`, and these routes write content pack files rather than active runtime `GameState`.
   - Risk: if v3.4 acceptance interprets Safe Apply as "all local content file writes must be backend-enforced validation + dry-run + explicit confirm," these older authoring save APIs are not yet fully aligned.
   - Impact: not an active `GameState` safety violation, but it is a Safe Apply workflow consistency gap.

2. `/authoring/import/saves` exists as a save import route.
   - This route is part of broader authoring/import-export tooling, not the v3.4 Safe Apply package flow.
   - Risk: save import is closer to runtime/save data than content-pack authoring. It should remain clearly separated from Authoring Safe Apply and require strong confirmation/validation in any UI path.
   - Impact: no reviewed v3.4 UI evidence shows it as a primary Authoring Safe Apply path, but it deserves release-review attention.

3. Action Mod tests validate draft boundaries but do not execute a full active runtime action in a session.
   - Existing tests prove safe registration through `ActionRegistry`, invalid StateDelta path rejection, and active state unchanged for authoring preview/dry-run flows.
   - Risk: a future runtime module enable path needs separate coverage showing mod action execution still records `EventLog` and applies only validated `StateDelta`.
   - Impact: not a v3.4 Authoring UI blocker because v3.4 does not enable arbitrary runtime module execution from the editor.

## Low-Risk Issues

1. Frontend confirmation is stronger than backend confirmation in some editor-specific save flows.
   - This is acceptable for local content editing, but backend enforcement is more robust for release-critical Safe Apply paths.

2. Diff/preview UI is still partly summary-oriented.
   - It communicates non-writing behavior and destructive-risk warnings, but field-level before/after summaries are not uniformly populated for every editor.

3. Audit records cover module scan/certify/quality gate in tests.
   - Apply/import/export audit coverage exists at a high level, but broader end-to-end audit assertions could be expanded for every authoring editor.

## Recommendations

1. Introduce a shared backend `AuthoringSafeApplyRequest` for all Pro apply/publish flows.
   - Require `validation_id` or validation result, dry-run result id, `explicit_confirm=True`, and optional quality gate status.
   - Use it for world pack, script pack, character pack, quest graph, location/map, NPC/faction, item/economy, rumor/crime, import, and package apply paths.

2. Keep legacy direct content-file save APIs available only as low-level authoring APIs, or add a `confirm_save` field.
   - If v3.4 acceptance demands strict Safe Apply semantics, clean writes should still require explicit backend confirmation.

3. Add focused tests for editor-specific write endpoints.
   - Assert they write only content files and never alter an active `GameState` session.
   - Assert confirmation is required for destructive, warning-bearing, overwrite, restore, and apply paths.

4. Separate save import from Authoring Safe Apply in UI and docs.
   - Save import/restore is a runtime save management concept, not a content-pack authoring publish path.

5. Extend audit-trail tests.
   - Cover import/export/apply/reject/restore records, not only scan/certify/quality gate.

6. Preserve the runtime boundary for Action Mods.
   - Editor preview/test/export must not register to active sessions.
   - Runtime use must continue through `ActionRegistry`, `ActionResult`, `StateDelta`, and `EventLog`.

## v3.4 Acceptance Blocker Status

This audit does not find a high-risk active `GameState` boundary blocker.

The main acceptance risk is medium severity: Safe Apply is not uniformly backend-enforced across all older authoring content-file save endpoints. If v3.4 acceptance requires every local content write to pass a backend-enforced validation + dry-run + explicit confirm sequence, this should be fixed before acceptance. If the release scope treats those older endpoints as low-level content editors and the Pro Safe Apply/import flows as the release-critical apply paths, this audit is pass with hardening recommendations.

Final status for this audit: **No direct active `GameState` blocker found; Safe Apply backend-confirm consistency should be resolved or explicitly scoped before v3.4 acceptance.**
