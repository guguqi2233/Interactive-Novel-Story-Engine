# v3.1 Novel Accessibility / Usability Audit

Verification Date: 2026-05-23

Scope: v3.1 Novel Studio UI Pro surfaces in `frontend/src/novelUi.tsx` and
their current integration in `frontend/src/App.tsx`.

This audit is documentation-only. It does not modify business code.

## 已通过项目

1. Novel page has clear top-level labeling.

   The integrated Novel section is labeled `Novel Studio UI Pro`, and the
   workspace navigation lists the main Novel surfaces: manuscript dashboard,
   outline, chapter editor, scene board, character arcs, plot/foreshadowing,
   timeline, World Bible, export, and quality.

2. Major action buttons use mostly clear text.

   Buttons such as `Create Manuscript`, `Start Writing Session`, `End Session`,
   `Save Novel Preferences`, `Add Chapter`, `Save Draft`, `Add Scene`,
   `Create Snapshot`, `Export Markdown`, and `Export TXT` are understandable.

3. Key empty states exist.

   The manuscript list shows `No manuscripts yet` with a next step. The chapter
   editor shows `Select a chapter`. Snapshot and search result lists have empty
   text. These states prevent blank panels.

4. Error and success panels are present.

   The Novel section includes compact error/success panels for Novel API,
   message, and snapshot feedback. This gives users a visible recovery point
   when API calls fail.

5. Chapter editor save and dirty state are visible.

   `DraftSaveStatus` displays `saving...`, `unsaved changes`, or `saved
   locally`, and the editor displays word count beside the active chapter.

6. Local-first and World boundary messaging is visible.

   The Novel section states that Novel drafts do not write World `GameState`.
   The workspace status also says Novel UI does not directly modify GameState.

7. Export filtering policy is visible.

   `NovelExportWizard` states that Markdown/TXT export excludes authoring notes,
   hidden refs, mature/private content, debug data, and API keys by default.

8. World -> Novel safety wording is visible.

   The Novel area and Cross-Mode area both state that World -> Novel preview uses
   safe event summaries, excludes raw `state_deltas`, and does not modify World
   `EventLog` or `GameState`.

9. Prompt/Provider panel avoids excessive sensitive detail.

   The panel shows prompt profile, provider safe summary, and use cases without
   exposing API keys or raw prompt content. This is concise and not currently
   overloaded.

10. Plot/Foreshadowing and Timeline panels communicate safe-summary behavior.

    The panels explain that hidden truth refs, timeline links, and world events
    are represented through safe labels/summaries in normal view.

## 高风险可用性问题

No high-risk accessibility or usability issue was found that would make the
Novel UI dangerous to use or likely to cause direct data loss by itself.

The reviewed UI avoids obvious secret exposure, does not present cloud/account
flows, and repeatedly states the World boundary. The main issues are incomplete
or shallow Pro workflows rather than unsafe controls.

## 中风险可用性问题

1. Outline Tree Pro is currently a placeholder, not an understandable tree.

   `OutlineTreePro` displays explanatory text but does not render act / volume /
   chapter / scene / beat / note hierarchy, expand/collapse state, validation
   rows, or jump targets. This blocks the requested outline-tree usability goal.

2. Export Wizard does not require an explicit filtering-policy confirmation.

   The wizard explains filtering, but the current UI exposes direct `Export
   Markdown` and `Export TXT` buttons. It does not step through manuscript
   selection, chapter selection, preview, filtering review, and final confirm.

3. World -> Novel Import UX is split and partly raw.

   The Novel panel has safety copy, while the Cross-Mode area has a `Preview
   Chapter Draft` button and renders the response through `SafeJSON`. Even if
   the payload is safe, a raw JSON preview is harder for writers to understand
   than labeled source events, excluded counts, suggested title, warnings, and a
   clear apply confirmation flow.

4. Quality issues are not yet easy to locate.

   `NovelQualityDashboard` can list severity and message, but current
   integration passes an empty issue list and the component does not render
   affected chapter/scene links, suggested action, category, or jump controls.

5. Error states may not provide enough recovery guidance.

   The top-level error panel shows the error message, but Novel-specific errors
   do not consistently show next actions such as retry, select a project, enable
   API, refresh data, or open diagnostics.

6. Disabled states explain safety only indirectly.

   Buttons are disabled when project/manuscript/chapter context is missing, but
   many disabled controls do not show inline reasons. This can make first-use
   workflows feel stalled.

7. Scene/plot/timeline panels are safe but thin.

   Scene cards exist, and plot/timeline panels communicate safe summaries, but
   plot-thread status, foreshadowing payoff state, and timeline link meaning are
   not yet presented with enough structured labels for a Pro writing workflow.

## 小问题

1. Some empty states lack explicit next-step details.

   `No chapters`, `No snapshots`, and `Select a chapter` are clear but could
   better point to `Add Chapter`, `Create Snapshot`, or manuscript selection.

2. The Novel workspace navigation is a static list.

   The navigation names are helpful, but they are not active tabs or jump links
   yet. This limits keyboard/scanning ergonomics.

3. Chapter editor textarea has no visible field label.

   The surrounding toolbar identifies the editor, but the draft textarea itself
   could use an accessible label or nearby label.

4. Search has a clear label but limited filter explanation.

   The search bar explains where to search, but tag/status/character filters are
   not visible in the current UI integration.

5. `docs/V3_1_ROADMAP.md` was not present during this audit.

   This is not a UI issue, but it makes it harder to compare current usability
   status against an accepted v3.1 scope document.

## 修复建议

1. Convert `OutlineTreePro` from explanatory placeholder to a real tree view
   with node type badges, hierarchy indentation, expand/collapse, validation
   summary, and clear empty state.

2. Upgrade `NovelExportWizard` into a staged flow: select manuscript, select
   chapters, choose format, preview structure, review filtering policy, then
   confirm export.

3. Replace raw World -> Novel `SafeJSON` preview with writer-facing rows:
   source event IDs, safe summaries, excluded hidden/debug counts, suggested
   title, warnings, and an explicit apply confirmation.

4. Expand `NovelQualityDashboard` issue rows with category, affected
   chapter/scene, suggested action, and safe jump controls.

5. Add visible disabled-state reasons for context-dependent buttons, especially
   when no project, manuscript, or chapter is selected.

6. Add accessible labels for editor textareas and make Novel workspace
   navigation actionable.

7. Keep Prompt/Provider concise. If cost/token hints or capability warnings are
   added, group them behind a compact summary to avoid information overload.

## 是否阻塞 v3.1 release

Conditionally blocking.

There is no high-risk accessibility or safety usability blocker. However, if the
release bar is "Novel Studio UI Pro" as a complete writer-facing experience, the
medium issues above should block v3.1 acceptance until fixed or explicitly
documented as known limitations. The largest gaps are Outline Tree Pro,
Export Wizard confirmation flow, World -> Novel Import preview clarity, and
locatable Novel Quality issues.
