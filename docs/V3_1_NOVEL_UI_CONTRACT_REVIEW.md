# v3.1 Novel Studio UI Contract Review

## Current Novel Routes

Novel Studio currently uses the local Project Shell instead of a standalone router. The main frontend entry is the Novel section inside `frontend/src/App.tsx`, backed by project-scoped `/projects/{project_id}/novel/...` APIs.

## Current Novel Components

v3.1 introduces a modest Novel UI component layer in `frontend/src/novelUi.tsx`: `NovelWorkspaceShell`, card/badge/toolbar components, Outline/Chapter/Scene panels, continuity panels, Prompt/Provider, Export, Quality, World Bible, and local recovery summaries.

## Current Novel Data Flow

Novel manuscripts, chapters, scenes, outlines, arcs, plot threads, foreshadowing, exports, snapshots, sessions, preferences, and search remain project-local data. Frontend actions call backend APIs; they do not write files directly and do not modify `GameState`.

## Current Editing UX

The v3.1 editor remains plain text / markdown-oriented. Chapter draft editing includes word count, dirty/save status, local snapshots, safe linked refs, and local writing session status. No rich-text, cloud collaboration, or online publishing is introduced.

## Current Cross-Mode UX

Novel to World remains draft/proposal based. World to Novel previews use safe event summaries and explicitly exclude raw `state_deltas`. Apply flows remain backend validated and confirmed; Novel UI does not mutate World state.

## Current Export UX

Novel export supports local Markdown and TXT through the existing Novel export service. The UI states that authoring notes, hidden refs, debug data, mature/private content, and API keys are excluded by default.

## Current Quality UX

Novel quality remains deterministic and local. Normal quality views show safe issue summaries and do not print hidden text, raw prompts, API keys, or raw state deltas.

## Privacy / Visibility Risks

Normal Novel UI must not render hidden facts, NPC secrets, private authoring notes, raw prompts, raw `state_deltas`, provider secrets, or API keys. v3.1 components only accept safe summaries, IDs, counts, redacted labels, and local draft text explicitly authored by the user.

## Recommended v3.1 Novel UI Shape

Use `NovelWorkspaceShell` as the stable structure: left navigation, center authoring area, right safe context sidebar, and bottom local status. Keep Novel data local, keep Provider Gateway as the only model entry, and require proposal/validation/apply for any World-facing consequence.
