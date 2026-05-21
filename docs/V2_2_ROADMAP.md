# v2.2 Roadmap: Novel Studio MVP

## Version Theme

Novel Studio MVP on top of the v2.1 Unified Narrative Project Layer.

## Goal

v2.2 turns Novel Mode from a safe project stub into a usable local drafting
workspace. It supports manuscripts, outlines, chapters, scenes, character arcs,
plot threads, foreshadowing, safe World Bible context, novel-scoped prompt
profiles, optional draft generation, Markdown/TXT export, and deterministic
quality checks.

Novel output remains draft material. It is not World Mode fact, does not modify
`GameState`, does not append `EventLog`, and does not bypass content
validation.

## Explicit Non-Goals

- No complete Tavern Studio.
- No World Engine rewrite.
- No online collaboration, cloud sync, online marketplace, or online publishing.
- No direct Novel draft mutation of `GameState`.
- No LLM-created authoritative world facts.
- No bypass of World validation when converting Novel drafts to World drafts.
- No DOCX/EPUB export in v2.2.
- No external LLM judge for quality.

## Implemented Modules

1. Novel Core Schema: `NovelManuscript`, `NovelOutline`, `NovelChapter`,
   `NovelScene`, `CharacterArc`, `PlotThread`, `ForeshadowingItem`, and
   `NovelDraftStatus`.
2. Novel Repository / Storage: local YAML storage under `project/novel/`.
3. Novel API: local authoring endpoints under `/projects/{project_id}/novel`.
4. Novel Frontend Shell: manuscript, chapter, scene, structure, and export
   entry points.
5. Outline Editor Backend / Frontend: tree/node CRUD and validation.
6. Chapter / Scene Draft Manager and Chapter Editor Frontend.
7. Character Arc, Plot Thread, and Foreshadowing managers.
8. Novel Timeline Integration.
9. World Bible Integration for safe Novel context.
10. Novel Prompt Profile Integration.
11. Novel Draft Generation Service using injected `LLMProvider`.
12. Chapter Consistency Checks and Novel Quality Evals.
13. Markdown / TXT export.
14. Novel to World Draft Conversion.
15. EventLog to Chapter Draft Import.

## Safety Constraints

- Novel drafts are always drafts.
- Novel -> World produces `WorldContentDraft` candidates only.
- EventLog -> Novel imports read visible/narrator-safe event summaries only.
- Hidden facts, private notes, debug memory, raw `state_deltas`, API keys, raw
  env, and provider secrets are excluded from normal Novel context, exports,
  prompt context, and reports.
- LLM calls are optional and must use `LLMProvider` / Provider Gateway.
- Tests use fake/mock/local providers only.

## Testing Requirements

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- Focused tests for schema/repository/API/context/export/quality boundaries.
- Regression coverage for no `GameState` mutation, no EventLog mutation, and no
  hidden/secret leakage.

## v2.3 Candidate Direction

Tavern Studio MVP, including safe RP session editing, character cards, group RP
drafts, and Tavern-to-World proposal validation.
