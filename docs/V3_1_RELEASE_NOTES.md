# v3.1 Release Notes: Novel Studio UI Pro

## Version Name

**v3.1 Novel Studio UI Pro**

## Version Goal

v3.1 upgrades the local Novel Studio authoring experience. The release focuses
on a safer, clearer local writing workspace for manuscripts, outlines, chapters,
scenes, continuity panels, draft snapshots, writing sessions, search, export,
World -> Novel import, and Novel quality review.

The main project direction remains **local-first**. v3.1 is not an online
writing platform, account system, cloud sync feature, online publishing service,
multiplayer collaboration system, or full commercial publishing suite.

Novel Mode remains a **draft and authoring mode**. It does not directly modify
World `GameState`. The World Engine remains the authoritative fact source, and
Provider Gateway remains the only model-entry boundary.

## New Novel UI Capabilities

- Novel workspace shell with local Novel navigation, main workspace, safe
  context sidebar, and status surfaces.
- Manuscript dashboard for chapter/scene counts, local word-count summaries,
  quality status, recent work, and quick actions.
- Outline Tree Pro foundation for structured outline views.
- Chapter Editor Pro foundation using plain text / markdown-style editing.
- Scene Cards Board for safe scene summaries.
- Character Arc Panel.
- Plot Thread / Foreshadowing Board.
- Timeline Link Panel.
- World Bible Sidebar with safe summaries only.
- Draft Version Compare through local draft snapshots.
- Writing Session Dashboard through local writing-session state.
- Novel Search / Tags / Filters through lightweight local search.
- Novel Prompt / Provider panel with safe prompt/provider summaries.
- Novel Export Wizard Pro for local Markdown/TXT-oriented export workflows.
- World -> Novel Import UX for safe EventLog/timeline draft previews.
- Novel Quality Dashboard Pro with safe issue summaries.
- Novel local preferences and unsaved/recovery UX.
- Novel UI component cleanup and static Novel UI regression checks.

## Behavior Changes

- Novel export now filters non-normal chapters by default.
- Novel export excludes authoring notes, hidden refs, mature/private content,
  debug data, and secrets by default.
- Draft snapshots reject hidden/authoring targets and store only user draft text
  plus safe metadata.
- Novel search skips hidden/private normal-view content by default.
- Novel quality issue display uses safe excerpts instead of raw hidden text.
- World -> Novel preview displays safe event summaries and does not expose raw
  `state_deltas`.
- Novel export requires explicit local confirmation from the frontend.

## Frontend Changes

- Added Novel UI Pro surfaces in `frontend/src/novelUi.tsx`.
- Integrated Novel workspace and Novel Pro panels into `frontend/src/App.tsx`.
- Added v3.1 frontend API types and client functions in `frontend/src/api.ts`.
- Added Novel UI styles in `frontend/src/styles.css`.
- Added `check:v31-novel-ui` to `frontend/package.json`.
- Added `frontend/scripts/check-v31-novel-ui.mjs` for lightweight Novel UI
  regression/safety checks.

## Backend API Changes

v3.1 extends local Novel APIs and services while preserving existing project,
World Engine, Cross-Mode, and Provider boundaries.

New or expanded backend surfaces include:

- Draft snapshot create/list/compare/confirmed restore.
- Writing session start/update/end/current session.
- Novel search across safe Novel entities.
- Novel preferences load/save.
- Safe Novel chapter/scene response projections for normal UI usage.
- Novel export filtering updates.
- World -> Novel and Novel -> World safe bridge support through existing
  Cross-Mode patterns.

These APIs do not expose API keys, raw env, provider secrets, hidden facts, raw
prompts, raw `GameState`, or raw `state_deltas` in normal responses.

## Novel Workspace Changes

- The Novel workspace is organized around manuscripts, outline, chapters,
  scenes, characters, plot, timeline, export, and quality.
- The right-side context area is reserved for safe World Bible, character,
  timeline, quality, and prompt/provider context.
- The workspace displays local-first and provider-safe status copy.
- Empty, disabled, and missing-data states are handled as local setup states
  rather than online onboarding or cloud prompts.

## Outline / Chapter / Scene UI Changes

- Outline Tree Pro provides a local structured outline foundation for acts,
  volumes, chapters, scenes, beats, and notes.
- Chapter Editor Pro keeps the editor lightweight and local, using existing
  plain text / markdown-style draft editing rather than a heavy rich-text
  dependency.
- Chapter editing displays save/dirty/recovery status and word-count context.
- Scene Cards Board displays safe scene cards and summaries without hidden fact
  text.

## Character Arc / Plot / Foreshadowing Changes

- Character Arc Panel provides a safe place to review character arc metadata and
  linked chapter/scene context.
- Plot Thread / Foreshadowing Board adds a local continuity surface for plot
  lines, unresolved items, setup/payoff status, and safe hint labels.
- Private authoring notes and hidden truth refs are not shown in normal UI.

## Timeline / World Bible Sidebar Changes

- Timeline Link Panel displays safe timeline and Cross-Mode link summaries.
- World -> Novel previews use safe EventLog/timeline summaries and do not modify
  EventLog or `GameState`.
- World Bible Sidebar shows flavor lore and safe structured summaries for
  characters, locations, factions, tags, and safe references.
- Hidden World Bible entries, NPC secrets, debug events, and raw `state_deltas`
  are excluded from normal Novel UI.

## Draft Version / Writing Session Changes

- `NovelDraftSnapshot` and `DraftVersionService` support local snapshot,
  listing, comparison, loading, and confirmed restore flows.
- Snapshots do not store provider prompts, provider secrets, API keys, hidden
  context, or raw debug data.
- `WritingSessionState` and `WritingSessionService` support local writing
  progress tracking.
- Writing sessions are local only and do not upload telemetry.

## Export / Import / Quality Changes

- Novel Export Wizard Pro focuses on local Markdown/TXT export.
- Export defaults filter authoring notes, hidden refs, mature/private content,
  debug data, and secrets.
- World -> Novel Import UX shows safe source summaries, excluded hidden/debug
  counts, target manuscript/chapter context, warnings, and confirmation copy.
- Novel Quality Dashboard Pro shows categories such as chapter structure, scene
  links, character refs, timeline refs, plot threads, foreshadowing, hidden leak
  risk, and export readiness.
- Quality reports show safe summaries and do not print hidden text in normal
  view.

## Privacy / Boundary Changes

- Novel Mode remains draft/authoring only.
- Novel UI does not directly modify World `GameState`.
- World changes still require backend validation, `StateDelta`, and `EventLog`.
- Novel -> World remains draft/proposal/validation/apply.
- World -> Novel reads safe summaries and does not rewrite EventLog or World
  facts.
- Provider Gateway remains the only model-entry boundary.
- API keys are not displayed in Novel UI or included in exports, logs,
  diagnostics, snapshots, tests, or docs.
- Hidden facts, NPC secrets, debug memory, raw prompts, raw `GameState`, and raw
  `state_deltas` are excluded from normal Novel UI.
- v3.1 does not add account, cloud sync, online writing, online publishing,
  multiplayer collaboration, online marketplace, or remote package download
  features.

## Known Limitations

- `docs/V3_1_ROADMAP.md` was not present during acceptance and should be added
  before final v3.1 freeze/tag.
- v3.1 is not a rich-text editor, cloud writing product, online publishing
  platform, multiplayer collaboration system, DOCX/EPUB export suite, or full
  commercial novel publishing application.
- Outline Tree Pro is a lightweight local UI foundation, not a full drag/drop
  IDE-grade outliner.
- Scene Cards Board does not implement complex kanban drag/drop.
- World Bible Sidebar and Timeline Link Panel expose safe summaries and links,
  not full world-editing tools.
- Export Wizard Pro is focused on local Markdown/TXT workflows.
- Novel Quality Dashboard does not auto-fix issues and does not use an external
  LLM judge.
- The frontend build still reports a non-blocking chunk-size warning.

## Upgrade Notes from v3.0

- Existing v3.0 local desktop workflows remain local-first and continue to use
  the same privacy and provider-secret boundaries.
- v3.1 adds Novel-specific local APIs and UI panels but does not change World
  Engine fact authority.
- Existing projects should continue to work with the new Novel UI surfaces.
- Novel draft snapshots, writing sessions, preferences, and search are local
  authoring data; they are not World facts.
- Provider setup continues to use `api_key_env` / `secret_ref` patterns and must
  not store plaintext keys in project data.
- Run the usual verification after upgrade:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v31-novel-ui
```

## Recommended v3.2 Direction

Recommended v3.2 direction: **Tavern Studio UI Pro**.

Suggested priorities:

- Tavern workspace shell and session navigation.
- Character card, session, and multi-NPC scene entry polish.
- RP memory, emotion, relationship tone, scene mood, and voice profile panels.
- Boundary profile and mature-module settings clarity, with mature disabled by
  default.
- Tavern quality/safety dashboard and RP leak checks.
- Tavern export/privacy polish.
- Cross-mode Tavern -> World and World -> Tavern review UX.
- Tavern UI regression checks for no secrets, no hidden facts, and no direct
  `GameState` mutation.
