# v2.4 Visibility / Cross-Mode Leak Audit

Verification Date: 2026-05-22

Scope: v2.4 Cross-Mode Bridge visibility and leak boundaries across Novel, Tavern, World, CrossMode reports, import/export, audit trail, and frontend normal views.

Verdict: Pass with non-blocking medium risks. No high-risk hidden-content leak was found in the current v2.4 implementation. The remaining risks are mostly future-maintenance hazards where callers must continue to provide safe summaries rather than hidden raw text.

## 已通过项目

1. Hidden facts do not enter Novel normal context through the v2.2 Novel context builders and prompt/export rules. Novel draft and export paths are designed around safe summaries and do not write World facts.
2. Hidden facts do not enter Tavern normal context through v2.3 Tavern prompt, lore, memory, and response-generation filtering. Tavern memory remains non-authoritative and hidden/debug memory is excluded from normal prompt context.
3. CrossMode normal reports use safe/normal summaries. `CrossModeDraft.safe_summary()`, `CrossModeProposal.safe_summary()`, `CrossModeApplyPlan.safe_summary()`, `CrossModeAuditRecord.normal_summary()`, `CrossModeValidationReport.normal_copy()`, and `CrossModeConflictReport.normal_summary()` are the intended normal-view surfaces.
4. NPC secrets are not expected to enter Tavern prompts or Novel drafts. The World NPC adapter and Tavern prompt context use player-safe / authoring modes, and player-safe mode excludes NPC secrets and unknown facts.
5. WorldBible and Lorebook hidden entries are filtered by the Novel/Tavern context builders from v2.2/v2.3, and v2.4 CrossMode services consume safe summaries rather than raw hidden text.
6. Character private notes and private persona fields are not normal prompt/export fields. Novel-to-Tavern and World-to-Tavern paths distinguish safe vs authoring output.
7. Timeline hidden / authoring-only entries are filtered from normal CrossMode timeline output. `CrossModeTimelineService.build_project_timeline()` excludes `hidden`, `debug_only`, and `authoring_only` entries unless `include_debug=True`.
8. EventLog raw `state_deltas` are excluded from World-to-Novel and Tavern/Novel draft surfaces. Tests cover raw `state_delta` text exclusion from World-to-Novel preview and draft payloads.
9. CrossModeLink review does not expose hidden target details. Hidden links are reported by link id/risk count, while `CrossModeLink.safe_summary()` suppresses hidden link content.
10. CrossModeConflict normal reports do not include debug-only conflicts and use `safe_summary` rather than raw hidden detail fields.
11. CrossModeValidation normal reports clear `debug_details` and redact messages/safe details with the project redaction helper.
12. Project Quality Gate normal output uses redacted validation/link/conflict summaries and does not include hidden text bodies.
13. Project import/export normal mode filters secret-like content and cross-mode raw debug material such as raw `state_delta` markers and debug memory.
14. AuditTrail normal summary redacts `safe_summary` and stores only references/result metadata by default.
15. Frontend Cross-Mode UI displays backend-provided safe fields, counts, statuses, and summaries. It does not render raw `state_deltas`, API keys, hidden target bodies, or debug memory in normal panels.
16. World Mode `visible_state` remains governed by the existing World Engine visible-state path. v2.4 bridge services do not change `visible_state` construction.

## 可能泄露路径

1. `CrossModeConflict.safe_summary` is trusted as safe. If future conflict detector rules place hidden fact text directly into `safe_summary`, normal conflict reports and frontend conflict lists could display it.
2. `CrossModeValidationIssue.safe_details` is redacted syntactically, but it can still carry semantically sensitive labels if a future validator puts hidden prose or secret names there.
3. `WorldToNovelPipeline.preview()` accepts caller-provided safe event summaries. The current implementation filters obvious raw `state_delta` text and hidden/debug events, but the endpoint cannot independently prove a client-provided summary is narrator-safe.
4. `CrossModeTimelineService._add_yaml_entries()` reads `summary` fields before normal visibility filtering. The normal result filters hidden/debug/authoring entries, but any future debug-enabled API must keep `include_debug` gated.
5. `CrossModeAuditRecord.debug_details_ref` is returned in normal audit summary. It is currently only a reference, not raw hidden text, but future callers must keep it opaque and avoid descriptive secret-bearing paths.
6. Frontend `World -> Novel` preview renders JSON returned by the backend. This is acceptable with current backend filtering, but the UI does not perform a second redaction pass.
7. Normal project export excludes secret-like text and obvious raw debug markers. It is not a semantic hidden-lore classifier, so export safety still depends on artifacts using hidden/debug fields rather than embedding hidden prose in normal fields.

## 高风险泄露

None found.

No current code path was found that directly exposes hidden facts, NPC secrets, debug memory, raw `state_deltas`, API keys, or provider secrets in v2.4 normal CrossMode reports or frontend CrossMode panels.

## 中风险泄露

1. Safe-summary trust boundary. Several normal views depend on the convention that `safe_summary` is already sanitized. This is acceptable for v2.4, but it is the main future regression risk.
2. Client-supplied World-to-Novel safe summaries. The API can filter forbidden markers, but cannot verify external text is genuinely player-visible/narrator-safe without binding preview input to server-side EventLog retrieval.
3. Audit `debug_details_ref` normal exposure. The field should remain an opaque id. If future code stores local paths, hidden labels, or descriptive debug names there, normal audit output could reveal metadata.
4. Export normal mode is marker/secret based, not a full visibility graph proof. Artifacts that misuse normal fields for hidden prose could be exported.

## 小问题

1. Frontend CrossMode preview uses raw JSON display for safe backend payloads. It is useful for MVP review, but a typed, field-by-field renderer would reduce accidental future leaks.
2. CrossMode link review reports hidden target risk by link id. This does not leak hidden text, but link ids should remain non-semantic.
3. CrossMode validation currently checks cross-mode artifact safety at a shallow level. It catches forbidden material in normal summaries and missing confirmation, but deeper semantic visibility checks should be expanded later.
4. Debug export requires an explicit flag, but authoring/debug export policies should be re-reviewed before any broader package distribution workflow.

## 修复建议

1. Add a strict `SafeText` or `NormalViewPayload` helper for v2.5 so normal reports can only be built from sanitized primitives.
2. Add regression tests that intentionally place hidden prose in `CrossModeConflict.safe_summary`, `CrossModeValidationIssue.safe_details`, timeline summaries, and audit refs, then assert normal views redact or reject them.
3. Bind World-to-Novel preview to server-side EventLog/session lookup where possible, instead of accepting caller-supplied summaries as the primary safety source.
4. Add frontend-side defensive redaction before rendering generic JSON preview blocks.
5. Keep `include_debug` disabled for normal CrossMode timeline APIs and require `ENABLE_DEBUG_API` before any debug view is exposed.
6. Keep cross-mode export modes explicit, with `debug` requiring a second confirmation flag and normal export rejecting raw hidden/debug markers.

## 是否阻塞 v2.4

Not blocking.

The current v2.4 implementation preserves the expected visibility boundary for normal CrossMode reports, exports, audit summaries, and frontend panels. The identified issues should be tracked as hardening work, but they do not block v2.4 acceptance because no active high-risk leak path was found.
