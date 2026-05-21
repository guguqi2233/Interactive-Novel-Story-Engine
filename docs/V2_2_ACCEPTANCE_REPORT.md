# v2.2 Acceptance Report

## Verdict

PASS_WITH_WARNINGS

v2.2 Novel Studio MVP is accepted as a local drafting and authoring milestone on top of the v2.1 `NarrativeProject` layer. The implementation provides Novel schemas, storage, APIs, frontend shell/editor surfaces, local consistency/quality checks, Markdown/TXT export, safe World Bible / Timeline / Prompt Profile integration, optional provider-backed draft generation, Novel-to-World draft candidates, and EventLog-to-chapter draft import.

No high-risk acceptance blocker was found. Remaining warnings are documented MVP limitations rather than release blockers.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: PASS, `1594 passed in 124.12s`
- `cd frontend && npm.cmd run build`: PASS
- Frontend build warning: Vite reported an existing chunk-size warning for a bundled asset larger than 500 kB. This is non-blocking for v2.2.

## Scope Accepted

Accepted v2.2 scope:

1. Novel Core Schema
   - `NovelManuscript`, `NovelOutline`, `NovelOutlineNode`, `NovelChapter`, `NovelScene`, `CharacterArc`, `PlotThread`, `ForeshadowingItem`, and `NovelDraftStatus`.
   - Novel schemas are Pydantic models and do not depend on `GameState`.

2. Novel Repository / Storage
   - `NovelRepository` stores Novel data under `project/novel/`.
   - Repository supports create/load/save/list flows for manuscripts, outlines, chapters, scenes, arcs, plot threads, and foreshadowing items.
   - Path traversal is rejected through safe id and relative path validation.

3. Novel API
   - Local authoring APIs exist under `/projects/{project_id}/novel/...`.
   - APIs support manuscripts, chapters, scenes, outline tree/nodes, arcs, plot threads, foreshadowing, consistency checks, quality eval, exports, and export listing.
   - APIs are local authoring/studio endpoints and do not expose API keys, raw env, raw `GameState`, raw `state_deltas`, or provider secrets.

4. Novel Frontend Shell
   - Project Shell includes a Novel mode surface.
   - Novel UI can show manuscript list/create, outline entry, chapter/scene lists, character arc, plot thread, foreshadowing, quality/export entry points, and disabled/coming-soon states.
   - Frontend build passes.

5. Outline Editor Backend / Frontend
   - `OutlineService` supports tree building, add/update/delete/reorder, and validation.
   - Frontend includes a simple outline editor surface without a large tree-editor dependency.

6. Chapter / Scene Draft Manager and Editor
   - `ChapterSceneService` supports chapter creation/update/delete guards/reorder and scene creation/update/delete/move/list.
   - Frontend includes basic chapter and scene draft editing with textarea-based MVP behavior.

7. Character Arc / Plot Thread / Foreshadowing
   - `CharacterArcService`, `PlotThreadService`, and `ForeshadowingService` support local authoring operations and validation.
   - Hidden truth refs and private notes are not exposed in safe summaries.

8. Timeline / World Bible / Prompt Integration
   - `NovelTimelineService` links scenes to timeline events and can summarize Novel timelines without modifying `EventLog`.
   - `NovelWorldBibleContextBuilder` filters hidden and authoring-only entries from normal Novel context.
   - `NovelPromptContext` and `NovelPromptContextBuilder` support novel-scoped prompt profile selection while preserving LLM authority limits.

9. Novel Draft Generation Service
   - `NovelDraftGenerationService` accepts an injected `LLMProvider`.
   - Generated output is validated as `GeneratedNovelDraft`.
   - Generated drafts do not modify `GameState`, do not append `EventLog`, and do not overwrite existing text unless explicitly confirmed.
   - Tests use fake/mock/local provider paths and do not call real APIs.

10. Chapter Consistency Checks / Novel Quality Evals
    - `NovelConsistencyChecker` detects missing refs, foreshadowing order issues, unresolved foreshadowing warnings, hidden reference risks, duplicate/order issues, and authoring note export risks.
    - `NovelQualityEvaluator` provides local deterministic quality reports without external LLM judging.
    - Reports use safe details and do not print hidden text in full.

11. Novel Export Markdown / TXT
    - `NovelExportService` exports Markdown and TXT under `project/novel/exports/`.
    - Export filters authoring notes, hidden refs, debug memory, raw `state_deltas`, API keys, provider profiles, provider secrets, and raw env.

12. Novel to World Draft Conversion
    - `NovelToWorldDraftService` creates `WorldContentDraft` candidates.
    - Drafts are proposals only and do not write content packs, saves, or active `GameState`.

13. EventLog to Chapter Draft Import
    - `EventLogToNovelDraftService` previews player-visible or narrator-safe event summaries.
    - Preview writes nothing.
    - Apply requires explicit confirmation and writes only Novel chapter draft fields.
    - EventLog and GameState are not modified.

14. v2.2 Integration Regression Tests
    - v2.2 focused and integration regression tests are present in `backend/tests/test_v22_novel_studio_mvp.py` and `backend/tests/test_v22_integration_regression.py`.
    - Full pytest suite passes.

## Boundary Review

LLM boundary:

- LLM remains a language layer.
- Novel draft generation uses an injected `LLMProvider` abstraction and test paths use fake/mock providers.
- `NovelPromptContext` excludes hidden facts, private notes, raw debug memory, raw `state_deltas`, API keys, provider secrets, and raw env.
- Prompt profiles cannot enable hidden fact access or state modification.
- Generated Novel drafts are not world facts and cannot mutate `GameState`.

World Engine boundary:

- World Engine remains the World Mode fact source.
- `GameState` changes continue to require `StateDelta`.
- World events remain recorded through `EventLog`.
- Novel Mode produces draft/proposal artifacts only.
- Novel-to-World conversion produces `WorldContentDraft` candidates and does not write world YAML.
- EventLog-to-Novel import reads safe summaries and does not modify EventLog.

Visibility and privacy boundary:

- Hidden World Bible entries do not enter normal Novel context.
- Lore/Fact hidden entries are filtered from Novel-safe context.
- Character private notes are excluded from safe summaries, prompt context, and export.
- Hidden/debug timeline events are excluded from normal summaries.
- Raw `state_deltas` do not enter Novel drafts or exports.
- Novel Quality normal reports use safe details rather than hidden text.

Security/export boundary:

- Novel APIs are gated as local authoring/studio APIs.
- NovelRepository rejects traversal and confines storage to `project/novel/`.
- Novel export rejects secret-like output and `state_delta` markers.
- Provider profiles store env-var references only, not real API keys.
- Frontend does not store API keys or raw env.

## Known Limitations

1. Novel Studio is an MVP, not a complete publishing suite.
   - No DOCX/EPUB/PDF export.
   - No rich-text editor.
   - No online publishing, collaboration, accounts, or cloud sync.

2. Novel-to-World remains proposal-only.
   - v2.2 does not implement a final apply path into content packs.
   - Candidate validation is warning/proposal level; future apply must require schema validation and explicit confirmation.

3. Hidden-content detection is deterministic and rule-based.
   - Known hidden refs, secret-like strings, and raw state-delta markers are blocked or flagged.
   - Arbitrary author-written hidden truth in normal prose cannot be semantically guaranteed without future richer validation.

4. Novel Draft Generation is optional and provider-backed.
   - Current tests use fake/mock providers.
   - Real provider use remains an explicit local configuration choice and is not part of default tests.

5. Frontend MVP is functional but compact.
   - It favors simple controls and textareas over a full professional manuscript editor.
   - Vite still emits a non-blocking chunk-size warning.

## Acceptance Risks

Low to medium, non-blocking:

- Future export formats must reuse current secret/hidden filtering.
- Future public/player views must not reuse raw authoring Novel API responses.
- Future Novel-to-World apply must enforce schema validation, visibility checks, and explicit confirmation.
- Future LLM-assisted extraction from unstructured text must remain schema-validated, provider-gated, and hidden-safe.

No high-risk release blocker remains for v2.2 acceptance.

## Recommended v2.3 Priorities

1. Tavern Studio MVP
   - Tavern sessions, character chat drafts, relationship proposals, RP memory, and safe character card workflows.

2. Stronger Novel export pipeline
   - Export preflight against known hidden fact ids, NPC secret ids, and private-note labels.
   - Consider DOCX/EPUB only after reusing current redaction and secret checks.

3. Novel-to-World apply review
   - Add explicit validation reports, diff review, and authoring-gate confirmation before any content-pack write.

4. Richer Novel UI
   - Better outline navigation, scene management, draft status filters, and manuscript-level review.

5. Project Quality Gate deepening
   - More complete Novel quality aggregation, hidden leak probes, and cross-mode reference checks.

## Final Status

v2.2 is accepted as Novel Studio MVP with warnings.

Release recommendation: proceed to v2.2 release notes and final freeze checks if no new blockers appear.
