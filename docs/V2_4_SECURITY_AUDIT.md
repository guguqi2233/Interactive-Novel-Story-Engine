# v2.4 Security / Apply Flow Audit

Verification Date: 2026-05-22

Scope: v2.4 Cross-Mode Bridge repository safety, import/export safety, apply-flow confirmation, StateDelta/EventLog boundaries, API gating, frontend secret handling, tracked-file hygiene, API key scanning, and provider-secret rejection.

Verdict: Pass with non-blocking medium risks. No high-risk security blocker was found for v2.4 release. The current implementation preserves the core boundary that CrossMode artifacts cannot store provider secrets, normal exports omit secret-like content, and service-level World apply requires explicit confirmation and StateDelta/EventLog inputs.

## 已通过项目

1. CrossModeRepository path traversal protection is present. It resolves `project_root`, keeps all files under `project/cross_mode/`, validates section paths, validates item ids with `safe_identifier`, and rejects paths escaping the project root.
2. CrossMode import/export inherits ProjectPackage zip safety. Import dry-run validates archive paths with `validate_relative_package_path`, rejects unsafe paths/zip slip attempts, validates checksums, and checks included file presence.
3. CrossMode export filters secrets. Text files containing secret-like material are skipped, and cross-mode files containing raw `state_delta` debug markers or debug memory are excluded from normal export.
4. `ProjectPackageManifest` supports `export_mode`, and `debug` export requires `include_debug=True`.
5. `CrossModeApplyPlan.requires_confirmation` defaults to `true`. Validation reports a blocker when an apply plan disables confirmation.
6. Tavern to World service-level confirmed apply requires `explicit_confirm=True`.
7. Tavern to World service-level confirmed apply uses `apply_delta()` when runtime `state`, `event_log`, and `state_deltas` are supplied.
8. Tavern to World service-level confirmed apply appends a World `Event` with normalized StateDeltas when runtime state/EventLog inputs are supplied.
9. Partial World apply inputs are rejected. The service requires `state`, `event_log`, and non-empty `state_deltas` together for a runtime World apply.
10. Dry-run does not mutate World state. The dry-run result records `writes: 0` for world writes.
11. Project and CrossMode HTTP APIs are authoring-gated through `require_authoring_api()` for cross-mode routes and project authoring operations.
12. Debug-only APIs remain controlled through existing debug API gating patterns and `ENABLE_DEBUG_API`.
13. Frontend does not store or display API key values. UI surfaces show configured/not configured status and redaction messages rather than key material.
14. Settings/config summaries do not return raw env. Existing config UI and backend summary code expose safe summaries only.
15. Player API surfaces continue to avoid raw `state_deltas` in normal player views. Debug panels may show deltas only in debug-oriented surfaces.
16. `.gitignore` excludes `.env`, frontend env files, `node_modules/`, and `frontend/dist/`.
17. Git tracked-file scan did not find tracked `.env`, database, log/cache, `node_modules`, `frontend/dist`, desktop build output, backup, or crash-report files.
18. Secret scan found `sk-...` strings only in tests and historical security documents as fake redaction fixtures, not production secrets.
19. Tests use mock/local/fake providers and redaction fixtures. No v2.4 tests call a real external API.
20. CrossMode artifacts reject provider secrets at model validation/storage boundaries via `contains_secret_text`.

## 高风险问题

None found.

No active v2.4 path was found that writes a provider secret into a CrossMode artifact, exports `.env` or API keys, bypasses explicit confirmation, or applies World state changes outside the StateDelta/EventLog service path.

## 中风险问题

1. Public Tavern to World `apply-confirmed` endpoint is audit-only in the current wiring.
   - The endpoint calls `TavernToWorldApplyService.apply_confirmed()` with `explicit_confirm`, but does not provide runtime `state`, `event_log`, or `state_deltas`.
   - Security impact: low-to-medium. It does not mutate World state and therefore cannot bypass StateDelta/EventLog. However, the route name can imply a full World apply while the current behavior records an audit confirmation only.
   - Release impact: not blocking, but the UI/docs should keep describing this as review/audit unless a real runtime apply path is wired.
2. Dry-run writes CrossMode metadata.
   - `dry_run_apply()` saves the updated apply plan and appends an audit record. It does not write active World state or database state, but it does write project-local CrossMode files.
   - Security impact: medium only if “dry-run does not write” is interpreted as no filesystem writes at all. Current behavior is acceptable as an audit trail, but the semantics should be documented as “no World writes”.
3. Apply failure atomicity depends on `apply_delta()` purity before final state update.
   - The service applies deltas into `next_state` and updates the original state only after processing deltas. This appears safe if `apply_delta()` is pure/returns a copied state.
   - Security impact: medium. A future in-place `apply_delta()` implementation could weaken rollback safety.
4. Import/export filtering is marker/secret based rather than full semantic classification.
   - Normal export rejects obvious secrets and raw debug markers, but a malformed artifact could still misuse normal fields for sensitive prose that does not match secret markers.
   - Security impact: medium, aligned with the visibility audit. Validation and tests reduce the risk but do not prove semantic secrecy for all future artifacts.
5. CrossModeRepository writes audit records with `debug_details_ref` available in normal summaries.
   - Current use is a reference, not raw secret content.
   - Security impact: medium if future callers put sensitive paths or descriptive secret names into this field.

## 小问题

1. The frontend has generic JSON preview blocks for safe backend payloads. This is acceptable for MVP, but typed field renderers would reduce accidental future exposure.
2. The `apply-confirmed` HTTP route does not currently expose a runtime StateDelta/EventLog apply request shape. This avoids unsafe mutation but may confuse reviewers expecting a complete apply path.
3. Security scans identify many fake `sk-*` strings in tests/docs. These are deliberate redaction fixtures and should remain clearly named as fake/test values.
4. CrossMode export mode `authoring` exists but should receive another targeted review before any broad sharing workflow.
5. CrossMode validation catches provider secrets in artifacts, but deeper semantic checks for secret-like authoring labels should be expanded later.

## 修复建议

1. Rename or document the public Tavern to World `apply-confirmed` endpoint as audit-only until it is wired to a real runtime state/EventLog context.
2. If v2.4 requires a true runtime apply endpoint, add an explicit request model that loads the target World session/save, validates the proposal, applies StateDeltas through the World Engine, records EventLog, and adds rollback/transaction tests.
3. Clarify dry-run semantics as “no active World/database writes” or change dry-run to return an unsaved plan when strict no-write behavior is required.
4. Add a regression test that injects an invalid second StateDelta and verifies the original state remains unchanged after failure.
5. Add repository-level tests for `debug_details_ref` and audit safe summaries to reject or redact sensitive-looking local paths and secret labels.
6. Add frontend defensive redaction for generic JSON preview panels.
7. Keep all CrossMode APIs under authoring/studio local gating and do not expose apply routes as public/player APIs.
8. Keep `debug` export behind explicit `include_debug=True`, and require a release checklist item before enabling debug export in any UI.

## 是否阻塞 v2.4 release

Not blocking.

The v2.4 security/apply-flow boundary is acceptable for release as a Cross-Mode Bridge MVP. The main caveat is that the public Tavern to World apply route currently behaves as an explicit audit confirmation unless service callers supply runtime World state/EventLog/StateDelta objects. This is safer than an unsafe apply, but should be documented and hardened before advertising full World apply from the API/UI.
