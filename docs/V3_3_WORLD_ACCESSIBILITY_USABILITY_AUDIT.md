# v3.3 World Accessibility / Usability Audit

Verification date: 2026-05-24

Scope: v3.3 World Studio UI Pro workspace, action input, suggested actions,
empty/error/disabled states, debug disabled state, map/location, NPC, quest,
inventory, tactical combat, economy, faction war, deduction, save/load, and
quality/playtest panels.

Reviewed evidence:

- `AGENTS.md`
- `docs/V3_3_ROADMAP.md`
- `frontend/src/worldUi.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/scripts/check-v33-world-ui.mjs`
- `backend/tests/test_v33_integration_regression.py`

## Audit Summary

Verdict: Pass with non-blocking usability follow-ups.

The v3.3 World UI Pro surfaces have clear panel titles, visible local status,
safe empty states, an understandable action input area, category-filtered
suggested actions, and explicit debug-disabled messaging. The UI generally
favours safe summaries over over-detailed raw state, which protects visibility
boundaries and keeps most panels scannable.

No high-risk accessibility or usability issue was found that should block v3.3.
The main usability limitation is that some advanced module panels are currently
safe/degraded summaries rather than rich, task-specific dashboards.

## 已通过项目

1. World pages have clear titles.
   - `WorldWorkspaceShell` uses the title `World Studio UI Pro`.
   - Each v3.3 panel has a specific title, including Map / Location, NPC /
     Relationship, Quest / Journal, Inventory / Trade, Tactical Combat, Economy,
     Faction War, Deduction, Timeline / EventLog, Save / Load, Quality /
     Playtest, and Debug Boundary.

2. Action input is clear.
   - `WorldActionInputPanel` is titled `World Action Input / Suggested Actions
     UX`.
   - It includes a free text input, category filter, suggested actions, recent
     actions, and a clear `Send` button.
   - It states that actions submit through `/game/input`.

3. Suggested actions are understandable.
   - `SuggestedActionCard` displays the action label, category, target, backend
     validated time, and safe requirement summary.
   - Category filters separate core, movement, social, inventory, stealth,
     combat, module, and other actions.

4. Empty states provide next steps.
   - `VisibleStateSection` renders `No active visible state` plus panel-specific
     next steps such as `Start a session to inspect known locations`.
   - Panels for NPCs, quests, inventory, saves, combat, faction conflicts, and
     deduction provide clear empty text.

5. Error states use existing safe error patterns.
   - v3.3 World UI reuses existing app-level error handling via safe error
     conversion.
   - No v3.3 panel introduces raw technical stack traces in normal World UI.

6. Disabled states explain the reason.
   - Suggested action cards and recent action chips are disabled when no session
     is active or the UI is loading.
   - Status badges show enabled/disabled module states.

7. Debug disabled state is clear.
   - `DebugDisabledState` explicitly says `ENABLE_DEBUG_API required`.
   - It explains that debug UI is disabled and normal UI remains player-facing
     safe.

8. Map / Location information is clear.
   - `LocationCard` displays current location, location ref, and visible exits.
   - Exit chips fill movement actions rather than silently changing state.

9. NPC / Quest / Inventory information is clear.
   - NPC cards show visible NPC id, mood, relationship band, condition, and a
     `Talk` action.
   - Quest cards show title, known summary, status, stage, and known objectives.
   - Inventory cards show visible item ref and a `Use item` action, with trade
     clearly labelled as backend validated.

10. Tactical Combat UI is understandable at the current scope.
    - `TacticalCombatPanel` shows encounter id/status, location, player stance,
      player condition, visible combatants, and available tactical action cards.
    - It states that combat results are backend-authoritative.

11. Economy / Faction War UI avoids information overload.
    - Economy currently shows a compact safe/degraded summary instead of raw
      economy data.
    - Faction War displays concise known conflict rows and excludes hidden war
      state.

12. Deduction Board distinguishes known evidence from hidden truth.
    - The panel displays `known_facts` and safe hypothesis actions.
    - It explicitly states hidden evidence, hidden truth, and debug solution are
      excluded.

13. Save / Load UI explains save slots.
    - `SaveSlotCard` shows world name/id, visible location, formatted time,
      turn, schema/migration status, and updated time.
    - `WorldSaveLoadPanel` states that save summaries exclude raw `GameState`,
      hidden facts, API keys, and raw `state_deltas`.

14. Quality issues are safely surfaced.
    - `WorldQualityPlaytestPanel` shows world quality status, recent playtest
      count, and clear actions to run the world quality gate or open the quality
      dashboard.
    - It states reports are safe, local-only, and not uploaded.

15. No obvious severe information overload was found.
    - The v3.3 World workspace uses card grids, compact lists, badges, and panel
      headers.
    - More complex/debug data is kept outside normal panels.

## 高风险可用性问题

None found.

No reviewed v3.3 World UI surface was so unclear, overloaded, or misleading that
it should block v3.3 release.

## 中风险可用性问题

1. Tactical Combat UI does not yet show full turn-order detail.
   - It shows encounter status, player stance, visible combatants, and action
     cards.
   - The current display is understandable but not yet a full tactical turn
     dashboard with active combatant, AP, cover, range, and status effects per
     combatant.
   - This is a usability gap, not a boundary blocker.

2. Economy Dashboard is intentionally degraded.
   - It shows `Safe summary unavailable` when no normal economy safe endpoint is
     available.
   - This avoids leaking hidden market state, but users get limited actionable
     information.

3. Advanced module panels are action-oriented but shallow.
   - Magic, hacking, crafting, and cultivation panels show safe summaries and
     action chips.
   - Users may need richer backend-provided safe summaries to understand why an
     action is unavailable or risky.

4. Error recovery guidance is mostly inherited from global app patterns.
   - v3.3 panels avoid unsafe errors, but not every panel has bespoke repair
     suggestions.
   - This is acceptable for v3.3 but should be improved in a later polish pass.

## 小问题

1. Some labels are internal/action-code-like.
   - Examples: `travel_route`, `form_hypothesis`, `test_hypothesis`,
     `scan_terminal`, `consume_pill`.
   - They are understandable to power users but could be friendlier with display
     labels while keeping command text available.

2. Save/load selection is visually represented, but destructive save operations
   are not yet part of the v3.3 safe panel.
   - Current save slot summaries are clear.
   - Future delete/archive flows should add explicit confirmation and clearer
     selected-save review.

3. Suggested action requirement summaries are generic.
   - They correctly avoid hidden requirements.
   - Richer safe requirement reasons would improve usability.

4. Normal UI boundary copy appears often.
   - The repeated safe-boundary text is useful for release confidence.
   - After v3.3, some of it could move to help/tooltips to reduce visual noise.

## 修复建议

1. Add richer backend safe summaries for tactical combat:
   - active combatant;
   - turn order;
   - AP;
   - stance;
   - cover;
   - range band;
   - status effects.

2. Add safe economy and module status endpoints before making those panels more
   detailed.

3. Add friendly display labels for action-code strings while keeping submitted
   backend commands explicit and inspectable.

4. Add panel-specific error guidance for no session, backend unavailable,
   module disabled, debug disabled, and quality/playtest unavailable states.

5. Keep debug and raw state details out of normal panels; use tooltips/help text
   for boundary explanations once the release hardening phase is complete.

## 是否阻塞 v3.3 release

Not blocking.

The audit found no high-risk accessibility or usability blocker. v3.3 can
proceed if the standard verification remains green:

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- `cd frontend && npm.cmd run check:v33-world-ui`
