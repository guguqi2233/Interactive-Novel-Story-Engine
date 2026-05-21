# v2.2 Release Notes

## 1. 版本名称

v2.2 Novel Studio MVP

## 2. 版本目标

v2.2 turns the v2.1 Novel Mode stub into a usable local Novel Studio MVP inside `NarrativeProject`. It adds project-local manuscript, outline, chapter, scene, character arc, plot thread, foreshadowing, context, export, and quality workflows while keeping Novel output as draft/authoring material.

Novel Mode remains separate from World Mode authority:

- Novel drafts are not World facts.
- Novel Mode does not directly modify World `GameState`.
- Novel-to-World creates draft/proposal candidates only.
- EventLog-to-chapter import reads safe summaries and does not modify `EventLog`.
- LLM remains a language layer, not the world referee.

## 3. 新增功能

- Novel core schemas for manuscripts, outlines, outline nodes, chapters, scenes, character arcs, plot threads, foreshadowing items, and draft status.
- Local `NovelRepository` storage under `project/novel/`.
- Local authoring APIs under `/projects/{project_id}/novel/...`.
- Novel frontend shell in the Project Shell.
- Outline tree editing backend and basic frontend.
- Chapter and scene draft management.
- Character arc, plot thread, and foreshadowing management services.
- Novel timeline integration with project timeline and World EventLog references.
- Safe World Bible / Lore context builder for Novel writing.
- Novel-scoped Prompt Profile integration.
- Optional `NovelDraftGenerationService` using injected `LLMProvider`.
- Chapter consistency checks and Novel quality evals.
- Markdown and TXT export.
- Novel-to-World `WorldContentDraft` proposals.
- EventLog-to-chapter draft preview/apply workflow.
- v2.2 focused and integration regression tests.

## 4. 行为变更

- Novel Mode is no longer only a placeholder. It now stores and edits project-local draft data.
- Novel data remains authoring data and is not automatically imported into World Mode.
- Project Quality Gate can include Novel checks.
- EventLog-to-Novel import is one-way and read-only against World EventLog.
- Novel export writes local Markdown/TXT files only under the project Novel exports directory.

## 5. API 变更

New local authoring APIs include:

```text
GET  /projects/{project_id}/novel/manuscripts
POST /projects/{project_id}/novel/manuscripts
GET  /projects/{project_id}/novel/manuscripts/{manuscript_id}
PATCH /projects/{project_id}/novel/manuscripts/{manuscript_id}
GET  /projects/{project_id}/novel/chapters
POST /projects/{project_id}/novel/chapters
GET  /projects/{project_id}/novel/chapters/{chapter_id}
PATCH /projects/{project_id}/novel/chapters/{chapter_id}
POST /projects/{project_id}/novel/chapters/reorder
GET  /projects/{project_id}/novel/scenes
POST /projects/{project_id}/novel/scenes
PATCH /projects/{project_id}/novel/scenes/{scene_id}
POST /projects/{project_id}/novel/scenes/{scene_id}/move
GET  /projects/{project_id}/novel/outline
PUT  /projects/{project_id}/novel/outline
GET  /projects/{project_id}/novel/outlines/{outline_id}/tree
POST /projects/{project_id}/novel/outlines/{outline_id}/nodes
PATCH /projects/{project_id}/novel/outlines/{outline_id}/nodes/{node_id}
DELETE /projects/{project_id}/novel/outlines/{outline_id}/nodes/{node_id}
POST /projects/{project_id}/novel/outlines/{outline_id}/validate
GET  /projects/{project_id}/novel/arcs
POST /projects/{project_id}/novel/arcs
GET  /projects/{project_id}/novel/plot-threads
POST /projects/{project_id}/novel/plot-threads
GET  /projects/{project_id}/novel/foreshadowing
POST /projects/{project_id}/novel/foreshadowing
POST /projects/{project_id}/novel/consistency/check
POST /projects/{project_id}/novel/quality/run
POST /projects/{project_id}/novel/export
GET  /projects/{project_id}/novel/exports
```

These APIs are local authoring/studio APIs. They are not player APIs and must remain gated by local authoring/quality configuration.

## 6. Frontend 变更

- Project Shell Novel mode now shows a Novel Studio MVP surface.
- Users can create/select manuscripts.
- The UI includes outline, chapter, scene, character arc, plot thread, foreshadowing, quality, and export entry points.
- Basic outline and chapter/scene editing use simple local controls and textareas.
- API-disabled states degrade safely.
- The UI does not display API keys, raw env, hidden facts, provider secrets, or debug details in the Novel normal surface.

## 7. Novel schema 变更

New v2.2 draft contracts:

- `NovelManuscript`
- `NovelOutline`
- `NovelOutlineNode`
- `NovelChapter`
- `NovelScene`
- `CharacterArc`
- `PlotThread`
- `ForeshadowingItem`
- `NovelDraftStatus`
- `NovelPromptContext`
- `NovelWorldBibleContext`
- `GeneratedNovelDraft`
- `WorldContentDraft`
- `ChapterDraftImportProposal`
- `NovelConsistencyReport`
- `NovelQualityReport`

These schemas do not depend on `GameState` and do not create authoritative World facts.

## 8. Novel Repository / Storage 变更

Novel files live under the project-local Novel section:

```text
project/
  novel/
    manuscripts/
    outlines/
    chapters/
    scenes/
    arcs/
    plot_threads/
    foreshadowing/
    exports/
```

`NovelRepository` supports create/load/save/list operations and rejects path traversal. It does not read `.env`, databases, logs, caches, node modules, or frontend build outputs.

## 9. Cross-mode 变更

- Novel scenes can link to timeline events.
- World EventLog events can be referenced through safe summaries.
- `CrossModeLink` may record provenance between World and Novel records.
- Novel-to-World creates `WorldContentDraft` candidates only.
- EventLog-to-chapter import preview writes nothing.
- EventLog-to-chapter apply requires explicit confirmation and writes only Novel chapter draft fields.

Cross-mode links and drafts do not bypass validation and do not modify active World state.

## 10. LLM / Prompt Profile 变更

- Novel draft generation is optional.
- `NovelDraftGenerationService` accepts an injected `LLMProvider` and produces `GeneratedNovelDraft`.
- Tests use fake/mock/local provider paths and do not call real APIs.
- `NovelPromptContext` contains only safe chapter/scene summaries, safe character summaries, safe World Bible context, safe timeline summaries, and style instructions.
- Prompt Profiles may adjust Novel style and generation preferences only.
- Prompt Profiles cannot enable hidden fact access, state modification, action-result override, or visibility bypass.
- Provider Gateway / `LLMProvider` remains the model access boundary.

## 11. Export 变更

- Markdown export is supported.
- TXT export is supported.
- Export writes to `project/novel/exports/`.
- Export excludes authoring notes, hidden refs, debug memory, raw `state_deltas`, API keys, provider profiles, provider secrets, and raw env.
- Export checks rendered output for secret-like content and `state_delta` markers.

## 12. Quality / eval 变更

- `NovelConsistencyChecker` adds local deterministic checks for chapter ordering, missing refs, foreshadowing issues, hidden-reference risk, duplicate order, and authoring notes in export candidates.
- `NovelQualityEvaluator` wraps deterministic checks into a Novel quality report.
- Novel Quality Eval does not use an external LLM judge.
- Reports use safe details and do not print hidden text in full.
- Project Quality Gate can include Novel checks.

## 13. 已知限制

- Novel Studio is an MVP, not a complete publishing system.
- No DOCX, EPUB, or PDF export.
- No rich-text editor.
- No online publishing, cloud sync, accounts, or collaboration.
- No full Tavern Studio in v2.2.
- Novel-to-World does not apply content to world YAML.
- `WorldContentDraft` candidates require future schema validation before any content-pack write.
- Hidden-content detection is deterministic and rule-based; arbitrary author-written hidden truth in normal prose cannot be semantically guaranteed.
- Frontend build still has a non-blocking Vite chunk-size warning.

## 14. 从 v2.1 升级注意事项

- Existing v2.1 `NarrativeProject` workspaces remain valid.
- Novel Mode now creates additional files under `project/novel/`.
- Enable `ENABLE_AUTHORING_API=true` only on a trusted local machine to use Novel authoring APIs.
- No new real API key is required for v2.2.
- Keep `LLM_PROVIDER=mock` or `local_stub` for tests.
- If using optional real provider-backed drafting locally, credentials must remain in environment/local secret config and must not be stored in project files, exports, prompt profiles, provider profiles, or frontend env.
- Novel exports are local draft artifacts. Review them before sharing.

## 15. 推荐 v2.3 方向

Recommended v2.3 theme: Tavern Studio MVP.

Suggested priorities:

1. Tavern session drafts and local RP transcript management.
2. Character card / RP profile workflows connected to the Shared Character Library.
3. Tavern memory and relationship proposals that remain non-authoritative until validated.
4. Group RP draft support with NPC knowledge boundaries.
5. Tavern-to-World proposal validation.
6. Stronger cross-mode quality checks across Novel, Tavern, and World.

v2.3 should continue the same boundaries: LLM is not the world judge, Provider Gateway remains the model entry point, Tavern output is proposal/draft material, and World Mode facts remain under the World Engine.
