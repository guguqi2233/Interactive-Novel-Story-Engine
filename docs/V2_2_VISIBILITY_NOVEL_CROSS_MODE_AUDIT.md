# v2.2 Visibility / Novel / Cross-Mode Audit

Verification date: 2026-05-22

Scope: v2.2 Novel Studio MVP visibility, Novel context, exports, EventLog import, Novel-to-World draft conversion, CrossModeLink behavior, frontend Novel UI safety, and World Mode isolation.

This audit is read-only for business code. It reviews the current implementation and tests around `backend/app/platform/novel_studio.py`, shared project libraries, Project/Novel APIs, frontend Novel UI, and v2.2 regression tests.

## 已通过项目

1. Hidden facts do not enter Novel normal context.
   - `NovelWorldBibleContextBuilder` excludes hidden World Bible entries and hidden Lore/Fact entries from normal context.
   - Debug exclusion records use ids/reasons rather than hidden text.

2. Hidden facts do not enter Novel export by default.
   - `NovelExportService` renders manuscript and chapter/scene draft text only.
   - Authoring notes, hidden refs, provider profiles, debug memory, and raw state deltas are not rendered.
   - Export output is checked for secret-like text and `state_delta` markers.

3. WorldBible hidden entries are filtered.
   - Hidden and non-safe entries are excluded from normal Novel context.
   - Authoring notes require explicit authoring/debug view.

4. LoreFactLibrary hidden entries are filtered.
   - Hidden and authoring-only lore is excluded from Novel-safe context.
   - Hidden/debug exclusion details are recorded without printing hidden content.

5. Character private notes do not enter export or prompt context.
   - Character prompt context uses safe summaries.
   - `private_notes_authoring_only` is omitted from safe summaries and normal export paths.

6. Timeline hidden and authoring-only events do not enter normal draft context.
   - Timeline safe summaries exclude hidden and authoring-only entries.
   - Novel timeline summaries use safe event summaries only.

7. EventLog raw state deltas do not enter chapter drafts.
   - EventLog-to-chapter import builds drafts from player-visible or narrator-safe summaries.
   - Raw `state_deltas` are not rendered into draft text.

8. EventLog hidden/debug events do not enter normal import.
   - Import preview excludes non-player-visible and debug/hidden events.
   - Excluded hidden/debug counts are reported without exposing event internals.

9. Novel-to-World Draft does not bypass validation.
   - Conversion produces `WorldContentDraft` candidates and warnings.
   - It does not write content packs, active saves, or active `GameState`.

10. Novel draft does not become a World fact.
    - Novel manuscripts, chapters, scenes, outlines, arcs, plot threads, and foreshadowing stay in Novel storage.
    - World Mode continues to use the existing World Engine, `StateDelta`, and `EventLog` boundaries.

11. CrossModeLink does not expose hidden targets in safe context.
    - Hidden links return no normal safe summary.
    - Link safe summaries redact notes and do not dereference hidden targets.

12. Novel Quality Report normal view does not print hidden text in full.
    - Hidden-reference findings use safe labels such as `[hidden-ref]`.
    - Quality checks are local deterministic rules, not external LLM judging.

13. Export does not include API keys, provider secrets, or debug memory.
    - Provider profiles are not rendered into novel exports.
    - Secret-like text checks block unsafe export output.

14. Frontend Novel UI does not display hidden/debug details.
    - The Novel UI consumes project/novel APIs and does not directly read local files or secrets.
    - Static regression coverage checks that frontend source does not include hidden test content.

15. World Mode `visible_state` is not affected by Novel Mode.
    - Novel services do not mutate `GameState`.
    - World Mode state remains built through the existing visible-state path.

## 可能泄露路径

1. Author-entered hidden truth in normal `draft_text`.
   - If a human manually types hidden information into a normal chapter or scene, deterministic checks can only catch known hidden labels, explicit hidden refs, secret-like strings, and raw state-delta markers.
   - This is a known limitation of local rule-based detection, not an observed leak in automated flows.

2. Authoring/debug context misuse.
   - World Bible authoring notes can be included only when explicitly requested with authoring/debug view.
   - Future UI surfaces must keep these views clearly labeled and excluded from normal export.

3. Novel API authoring responses.
   - Novel APIs are local authoring APIs and may return authoring fields to Studio clients.
   - They must not be reused as player/public APIs without an additional normal-view projection.

4. Future Novel-to-World apply flow.
   - v2.2 creates draft candidates only.
   - Any future apply/import feature must require schema validation, compatibility checks, and explicit confirmation before writing world content.

## 高风险泄露

None found.

No reviewed v2.2 path shows hidden facts, NPC secrets, debug memory, raw state deltas, provider secrets, or API keys entering Novel normal context, Novel export, EventLog-to-chapter import, CrossModeLink safe summaries, or World Mode player-visible state.

## 中风险泄露

1. Manual hidden-content authoring in normal Novel drafts.
   - Impact: A human author could paste hidden content into chapter text, and the system may not semantically recognize it unless it matches known hidden refs/labels or secret markers.
   - Current mitigation: consistency checks, quality evals, export safety checks, and redacted hidden refs.
   - Status: Non-blocking for v2.2 because this is an authoring limitation, not an automatic leak path.

2. Authoring API surface must remain local/studio-only.
   - Impact: Raw authoring objects are appropriate for local Studio use but not for player/public consumption.
   - Current mitigation: Project and Novel APIs are local authoring/studio surfaces, while player state remains separate.
   - Status: Non-blocking, but must be preserved in future routing.

## 小问题

1. The earlier `docs/V2_2_VISIBILITY_NOVEL_AUDIT.md` remains a narrower audit. This document supersedes it for Novel plus cross-mode visibility review.

2. This audit is based on code and test inspection. It does not include a fresh browser screenshot pass of the Novel UI.

3. Novel-to-World draft validation is intentionally candidate-level in v2.2. Full write/apply semantics remain out of scope and must not be inferred as implemented.

## 修复建议

1. Keep all Novel APIs gated as local authoring/studio APIs and avoid exposing raw Novel models through player routes.

2. Add a future export preflight that checks chapter and scene text against known hidden fact ids, hidden labels, NPC secret ids, and authoring-only refs from project libraries.

3. When a future Novel-to-World apply flow is introduced, require explicit confirmation, content schema validation, compatibility checks, and hidden-field filtering before any content pack write.

4. Keep authoring/debug notes visually labeled in the UI and excluded from normal Novel context, prompt context, and export.

5. Continue requiring fake/mock/local_stub providers in Novel generation tests so provider prompts can be inspected for hidden content.

## 是否阻塞 v2.2

Not blocking.

Verdict: PASS_WITH_WARNINGS.

The warnings are authoring-surface and future-hardening items. No high-risk visibility, Novel, or cross-mode leak blocker was found for v2.2 acceptance.
