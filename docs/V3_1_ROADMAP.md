# v3.1 Roadmap: Novel Studio UI Pro

## Version Goal

v3.1 turns Novel Studio from an MVP surface into a local writing workspace that
is practical for everyday drafting, review, continuity work, and safe local
export.

The priorities are:

- local-first writing workflows;
- writing experience and UI clarity;
- privacy-first handling of drafts, prompt context, exports, and recovery data;
- preservation of World Engine, `StateDelta`, `EventLog`, Visibility, and
  Provider Gateway boundaries.

v3.1 does not build an online writing platform, account system, cloud sync,
multi-user collaboration system, or online publishing product.

## Scope

v3.1 covers the following implemented or accepted work:

- Novel Studio UI Contract Review.
- Novel Workspace Layout Polish.
- Outline Tree Pro.
- Chapter Editor Pro.
- Scene Cards Board.
- Manuscript Dashboard.
- Character Arc Panel.
- Plot Thread / Foreshadowing Board.
- Timeline Link Panel.
- World Bible Sidebar.
- Draft Version Compare.
- Writing Session Dashboard.
- Novel Search / Tags / Filters.
- Novel Prompt / Provider UX Polish.
- Novel Export Wizard Pro.
- World -> Novel Import UX Pro.
- Novel Quality Dashboard Pro.
- Novel Local Preferences.
- Novel Recovery / Unsaved Draft UX.
- Novel UI Component Cleanup.
- Novel UI Regression Tests.
- v3.1 Integration Regression Tests.

## Non-Goals

v3.1 explicitly does not implement:

- account system;
- cloud sync;
- online writing platform;
- online publishing;
- multi-user collaboration;
- remote template marketplace;
- new large gameplay systems;
- arbitrary code plugins;
- direct Novel-to-`GameState` mutation;
- automatic conversion of Novel drafts into World facts;
- DOCX/EPUB publishing suite unless a future version separately implements,
  tests, documents, and audits it.

## Architecture Boundaries

- Novel Mode is a draft / authoring mode.
- Novel UI does not directly modify `GameState`.
- Novel -> World still requires draft / proposal / validation / explicit apply.
- World -> Novel creates chapter or scene drafts only. It does not modify
  `EventLog` or `GameState`.
- World Engine remains the authoritative source of World facts.
- Provider Gateway remains the only model-entry boundary.
- Novel LLM calls must use safe `NovelPromptContext`.
- `NovelPromptContext` may include safe manuscript, chapter, scene, style,
  World Bible, and timeline summaries only.
- Hidden facts, NPC secrets, private notes, raw prompts, raw `GameState`, and
  raw `state_deltas` must not enter normal Novel UI.
- Hidden facts, NPC secrets, private notes, raw prompts, raw `GameState`, and
  raw `state_deltas` must not enter normal Novel prompt context.
- Novel draft snapshots store user draft text plus safe metadata only. They
  must not store provider prompts, provider secrets, API keys, hidden context,
  or debug memory.
- Writing sessions are local progress metadata only. They do not upload
  telemetry and do not become World facts.
- Novel export defaults filter authoring notes, hidden refs, mature/private
  content, debug data, provider secrets, API keys, raw prompts, raw
  `GameState`, and raw `state_deltas`.

## UI / UX Requirements

- All new Novel pages and panels must handle loading, empty, error, and disabled
  states.
- Chapter and Scene editors must show dirty, save, and recovery status clearly.
- Draft restore and destructive actions must require explicit confirmation.
- Export Wizard must show the filtering policy before export.
- World -> Novel Import must clearly state that it does not modify World
  `EventLog` or `GameState`.
- Novel Quality Dashboard must use safe summaries and must not print hidden text
  in full.
- Provider / Prompt panels must not display API keys, raw env, provider secrets,
  full sensitive prompts, hidden facts, or raw `state_deltas`.
- World Bible Sidebar must show safe summaries only in normal UI.
- Timeline Link Panel must not display hidden/debug events or raw
  `state_deltas`.
- Search must not search or return hidden/private notes in normal mode.
- Export, backup, diagnostics, and logs must continue to filter secrets and
  hidden/debug/mature/private content by default.
- No v3.1 UI should present account, cloud sync, online writing, online
  publishing, online marketplace, or remote package download as a current
  feature.

## Testing / Verification

Required v3.1 verification commands:

```powershell
python -m pytest
```

```powershell
cd frontend
npm.cmd run build
```

Recommended v3.1 UI safety check:

```powershell
cd frontend
npm.cmd run check:v31-novel-ui
```

Verification should confirm:

- Novel UI compiles.
- Novel backend/API tests pass.
- World Engine, Provider Gateway, Cross-Mode, export, and visibility regression
  tests still pass.
- No test calls a real provider by default.
- No test uploads data.
- Normal Novel UI does not expose API keys, hidden facts, NPC secrets, private
  notes, raw prompts, raw `GameState`, or raw `state_deltas`.

## Known Limitations

- v3.1 is not complete commercial publishing software.
- v3.1 does not support online writing, cloud sync, multi-user collaboration, or
  online publishing.
- v3.1 does not add new large World gameplay modules.
- Novel -> World still requires user review, validation, and explicit apply.
- Novel UI Pro focuses on the local writing experience; it does not change World
  Engine rules.
- Outline Tree Pro is a local UI foundation, not a full drag/drop IDE-grade
  outliner.
- Scene Cards Board is a lightweight card surface, not a complex kanban system.
- Novel Export Wizard Pro focuses on local Markdown/TXT workflows.
- Novel Quality Dashboard provides safe summaries and next-step guidance; it
  does not auto-fix issues and does not use an external LLM judge.
- The frontend bundle may still emit a non-blocking chunk-size warning until
  future UI polish/code-splitting work.

## Recommended v3.2 Priorities

Recommended v3.2 direction: **Tavern Studio UI Pro**.

Candidate priorities:

- Tavern Workspace Layout.
- Character Card Library UI.
- Single Character Chat Pro.
- Multi-NPC Scene UI Pro.
- RP Memory Panel.
- Emotion Arc Panel.
- Relationship Tone Panel.
- Scene Mood Preset UI.
- Character Voice Lab UI.
- Tavern -> World Proposal Review UX Pro.
- RP Safety Dashboard.

v3.2 should keep the same local-first and boundary-preserving posture: Tavern
sessions and RP messages must not directly modify `GameState`, provider calls
must remain behind Provider Gateway, mature module controls must remain
default-off, and normal Tavern UI must not expose hidden facts, NPC secrets,
debug memory, raw prompts, raw `state_deltas`, or API keys.
