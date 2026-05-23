# v3.2 Tavern Accessibility / Usability Audit

Verification date: 2026-05-23

Scope reviewed:

- `frontend/src/App.tsx`
- `frontend/src/tavernUi.tsx`
- `frontend/src/styles.css`
- `docs/V3_2_ROADMAP.md`
- `docs/V3_2_TAVERN_UI_CONTRACT_REVIEW.md`
- `docs/V3_2_TAVERN_UI_PRIVACY_VISIBILITY_AUDIT.md`
- `docs/V3_2_TAVERN_LLM_BOUNDARY_AUDIT.md`

This is a documentation-only audit. No code was changed.

## Passed Items

1. **Tavern page has clear titles.**
   - The main Tavern section is titled `Tavern Studio UI Pro`.
   - The workspace and panels expose clear local RP labels such as `Single Character Chat Pro`, `Character Card Library`, `World NPC to Tavern Character UX Pro`, `RP Safety Dashboard`, `Tavern Session Export / Backup UX`, `Tavern Local Preferences`, and `Tavern Recovery / Unsaved Session UX`.

2. **Primary action buttons have clear labels.**
   - Major actions use direct verbs: `Send`, `Create Recovery Draft`, `Preview`, `Apply to Tavern Draft`, `Run RP Safety Eval`, `Preview Export`, `Confirm Export`, `Save Tavern Preferences`, `Create Character`, `Import Draft`, `Create Session`, `Create Preset`, `Create Scene`, and `Generate Next Reply`.

3. **Empty states provide basic next-step guidance.**
   - Character, session, message, preset, and multi-NPC lists use empty text such as `No Tavern characters`, `No Tavern sessions`, `No messages`, `No scene presets`, and `No multi-NPC scenes`.
   - Multi-NPC empty text gives a next step when there are too few characters: `Create at least two Tavern characters first.`

4. **Error state is visible and redacted through shared error handling.**
   - Tavern mode renders `ErrorPanel message={tavernError}` near the top of the Tavern section.
   - Backend/API error messages are routed through existing safe frontend formatting.

5. **Disabled state is generally understandable from context.**
   - Send requires a selected session, selected character, and non-empty message.
   - Multi-NPC creation requires enough characters.
   - World NPC preview/apply requires a selected NPC.
   - Export, preferences, and safety actions require a selected project.

6. **Chat input / send / draft state is understandable.**
   - The chat textarea has the placeholder `Write a local RP message...`.
   - `ChatSaveStatus` displays `unsaved message draft`, `saving...`, or `saved locally`.
   - `Safety notes` are collapsible.
   - `Create Recovery Draft` is available near the chat area.

7. **Multi-NPC turn order is understandable at summary level.**
   - Multi-NPC cards show participant count and current turn number.
   - The UI says multi-character scenes store Tavern messages only and do not modify World `GameState`, `EventLog`, hidden facts, NPC secrets, or provider secrets.

8. **Character editor distinguishes public / private / authoring-only.**
   - The editor panel states public character, RP, voice, example dialogue, and boundary refs can be edited locally.
   - Private persona is explicitly labeled authoring-only.

9. **RP Memory visibility is understandable.**
   - RP Memory Panel states relationship, promise, preference, mood, and boundary memory are shown as safe summaries.
   - It states mature-only memory is hidden by default.

10. **Emotion / Relationship states are understandable.**
    - Emotion Arc Panel states emotion affects Tavern prompt context only and does not modify World NPCs.
    - Relationship Tone Panel states relationship tone is proposal-only for World changes and shows safe summaries.

11. **Boundary / Mature settings clearly state default-off behavior.**
    - Boundary / Mature Settings UI states Mature Module is disabled by default.
    - It also states consent is required, unknown/minor scenes are blocked, and mature export is default off.
    - The Tavern workspace status repeats Mature Module default-disabled status.

12. **Proposal Review explains it will not directly modify World.**
    - Tavern section states Tavern data never writes World `GameState` or `EventLog`.
    - Cross-Mode Bridge states apply to World requires backend validation and explicit confirmation.
    - Tavern -> World Apply Review states apply plans require explicit confirmation and the UI does not mutate World state directly.

13. **Export filtering is understandable.**
    - Tavern export panel lists excluded categories: API keys, hidden facts, NPC secrets, mature/private memory, debug data, raw prompts, and raw `state_deltas`.
    - Export preview displays session count, safe message count, and filtering policy.

14. **RP Safety issues are locatable at summary level.**
    - RP Safety Dashboard displays overall status and safe issue-row wording.
    - Backend report schema supports affected session/character fields where available.
    - The UI includes a direct `Run RP Safety Eval` action.

15. **No severe information overload was found.**
    - The Tavern workspace uses a left navigation, central chat/scene area, right context sidebar, and bottom status bar.
    - Additional Pro panels are grouped as cards. The page is dense, but still scannable.

## High-Risk Usability Issues

None found.

## Medium-Risk Usability Issues

None found that block v3.2 release.

## Minor Issues

1. **Some Pro panels are still safe-summary surfaces rather than deep editors.**
   - RP Memory, Emotion, Relationship, Scene Mood, Voice Lab, Boundary/Mature, Prompt/Provider, and RP Safety panels communicate boundaries clearly but do not yet expose full artifact editing workflows.

2. **Disabled controls could explain their exact unmet prerequisite inline.**
   - Current context is usually enough, but inline helper text would improve usability for `Send`, `Create Scene`, `Generate Next Reply`, and export actions.

3. **Multi-NPC turn order is text-only.**
   - Participant count and turn number are shown, but a visual turn lane or active-speaker highlight would be clearer for repeated RP use.

4. **RP Safety drill-down is summary-level.**
   - The dashboard can show safe issue rows, but richer links to affected session/character panels would improve triage.

5. **Legacy Tavern MVP controls remain below Pro panels.**
   - Keeping them preserves existing functionality, but the page is visually dense. Future cleanup can fold those controls into `TavernWorkspaceShell`.

## Recommended Fixes

1. Add inline disabled reasons:
   - `Select a session and character first.`
   - `Create at least two Tavern characters first.`
   - `Select a project first.`

2. Improve Multi-NPC scene usability:
   - turn order lane;
   - participant badges;
   - active speaker highlight;
   - next speaker preview.

3. Expand RP Safety navigation:
   - category filters;
   - affected session links;
   - affected character links;
   - suggested action shortcuts.

4. Gradually migrate old Tavern MVP controls into the v3.2 workspace shell to reduce page density.

5. Keep future richer controls within the same boundary copy:
   - mature default off;
   - public vs authoring-only distinction;
   - proposal-only World changes;
   - safe summaries in normal UI.

## Release Blocking Assessment

This audit does **not** identify a v3.2 release blocker.

Final accessibility / usability verdict: **Pass with minor non-blocking usability follow-ups**.
