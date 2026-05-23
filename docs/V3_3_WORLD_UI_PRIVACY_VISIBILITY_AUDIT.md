# v3.3 World UI Privacy / Visibility Audit

Verification date: 2026-05-24

Scope: v3.3 World Studio UI Pro normal UI, visible-state inspector, map/location, NPC, quest, inventory/trade, advanced module panels, timeline/EventLog, debug gating, provider panel, and related v3.3 regression checks.

Reviewed evidence:

- `AGENTS.md`
- `docs/V3_3_ROADMAP.md`
- `frontend/src/worldUi.tsx`
- `frontend/src/App.tsx`
- `frontend/scripts/check-v33-world-ui.mjs`
- `backend/tests/test_v33_integration_regression.py`

## Audit Summary

Verdict: Pass with non-blocking follow-up items.

The v3.3 World UI Pro implementation keeps normal World UI tied to `visible_state` and safe summaries. The new World workspace components explicitly separate normal views from debug views, and raw `state_deltas` rendering is placed behind `DebugGate` / `ENABLE_DEBUG_API` surfaces. The v3.3 regression tests verify that `/game/state` does not expose raw `state_deltas`, debug memory, NPC secrets, or fake API-key material, while debug event details require the debug API gate.

No high-risk World normal UI privacy or visibility leak was found in the reviewed v3.3 surfaces.

## 已通过项目

1. World normal UI does not intentionally render hidden facts.
   - `WorldWorkspaceShell` and related copy state that normal World UI uses `visible_state` only.
   - `backend/tests/test_v33_integration_regression.py` checks `/game/state` output for absence of hidden/debug/secrets markers.

2. World normal UI does not intentionally render NPC secrets.
   - `NPCRelationshipPanel` reads visible NPC summaries and includes explicit safe-boundary copy.
   - The v3.3 regression test asserts NPC secret fixture text is absent from normal state output.

3. World normal UI does not intentionally render `npc_knowledge`.
   - The new normal World UI components consume `VisibleState` fields rather than raw NPC state.
   - No normal v3.3 panel renders `npc_knowledge` directly.

4. World normal UI does not intentionally render debug memory.
   - `VisibleStateInspector` and World workspace copy mark debug memory as excluded.
   - The backend regression test asserts debug-memory marker text is absent from `/game/state`.

5. World normal UI does not render raw `state_deltas`.
   - Normal `worldUi.tsx` components avoid `JSON.stringify(event.state_deltas)`.
   - Raw delta rendering in `App.tsx` is in debug-oriented surfaces, including the v3.3 `DebugGate` panel.
   - The v3.3 static regression check verifies raw `state_deltas` rendering is not present in the normal component section.

6. Visible State Inspector only displays `visible_state`-based sections.
   - `VisibleStateInspector` accepts `VisibleState | null` and renders player, location, visible NPC, inventory, quest, known-fact, and module-safe summary sections.
   - It explicitly labels itself as not raw `GameState`.

7. Map / Location Panel does not display hidden locations or hidden exits.
   - `LocationCard` / `MapLocationPanel` renders the current visible location and visible exits from `visible_state`.
   - There is no full world graph or raw location table rendering in the v3.3 normal panel.

8. NPC / Relationship Panel does not display hidden NPCs or NPC secrets.
   - `NPCRelationshipPanel` displays visible NPC summaries and relationship safe bands.
   - It does not render raw NPC records or hidden knowledge fields.

9. Quest / Journal Panel does not display hidden objectives or hidden truth.
   - `QuestJournalPanel` renders visible quest summaries from `visible_state`.
   - It does not render raw quest state machine internals.

10. Inventory / Item / Trade UI does not display hidden item properties.
    - `InventoryTradePanel` uses visible inventory item summaries.
    - It does not calculate authoritative trade results or render hidden properties.

11. Economy UI does not display hidden market state.
    - `EconomyDashboardPanel` renders safe/degraded market status from visible data only.
    - No raw economy state is displayed in normal UI.

12. Faction War UI does not display hidden war state.
    - `FactionWarDashboardPanel` renders known faction conflict summaries from visible data.
    - Hidden conflict state is not rendered.

13. Deduction UI does not display hidden truth.
    - `DeductionBoardPanel` uses known facts / safe hypothesis actions.
    - It does not render solution/debug truth.

14. Module UI does not display hidden spells, logs, recipes, or techniques.
    - `WorldAdvancedModulePanels` provides safe action/status surfaces and disabled states.
    - It does not render raw module state.

15. Timeline UI excludes hidden/debug events from normal view.
    - `WorldTimelineEventLogPanel` filters events with `visible_to_player`.
    - Raw `state_deltas` require debug-gated rendering.

16. Debug UI is gated.
    - `DebugGate` clearly states `ENABLE_DEBUG_API` is required and debug data is not player-facing.
    - Backend regression verifies debug event access returns `403` when debug API is disabled.

17. Provider UI does not display API keys.
    - `WorldPromptProviderPanel` displays provider safe summaries and capability/routing information only.
    - v3.3 static regression checks include API-key exclusion tokens and no plaintext key field.

18. ErrorState / safe summaries do not introduce a new sensitive-path leak in v3.3.
    - v3.3 surfaces reuse existing safe/degraded error patterns.
    - No new v3.3 World UI component renders arbitrary local paths.

## 高风险 UI 泄露

None found.

No reviewed v3.3 normal World UI surface was found rendering hidden facts, NPC secrets, `npc_knowledge`, debug memory, raw `state_deltas`, API keys, raw env, provider secrets, or sensitive local paths.

## 中风险 UI 泄露

1. Legacy debug-oriented event components remain in `frontend/src/App.tsx`.
   - `App.tsx` still contains older debug/timeline components that can render raw `state_deltas`.
   - Current v3.3 workspace places raw delta rendering behind `DebugGate`, and backend debug APIs are gated, so this is not a release blocker.
   - Risk: future refactors could accidentally mount a legacy debug component in a normal route.

2. Some normal UI text explicitly names sensitive categories as exclusions.
   - Normal UI copy mentions phrases such as hidden facts, NPC secrets, raw `state_deltas`, API keys, and debug memory.
   - This does not leak actual sensitive content, but it can add noise for player-facing UX.
   - Risk: low operational risk, moderate polish concern.

## 小问题

1. Advanced module panels are safe but mostly summary/degraded UI.
   - This is preferable to leaking raw module state.
   - Richer module-specific safe summaries may be useful in v3.4+.

2. Static frontend checks are strong enough for v3.3 scope but are not a full DOM rendering test.
   - The project intentionally avoids adding a large E2E framework for this slice.
   - Current static checks and backend integration tests cover the critical privacy boundaries.

3. Debug boundary relies on continued discipline around `DebugGate`.
   - The current implementation and tests are acceptable.
   - A future lint/check could specifically assert all raw delta renders are gated.

## 修复建议

1. Keep all raw `state_deltas`, raw EventLog details, raw `GameState`, and module debug data behind `DebugGate`.

2. Add a future static check that flags `JSON.stringify(event.state_deltas` unless it appears inside an approved debug-only component.

3. If richer economy, faction-war, deduction, magic, hacking, crafting, or cultivation UI is needed, add backend safe-summary APIs rather than reading raw module state in frontend.

4. Keep `/game/state` as the normal UI state source and avoid passing raw debug API responses into normal panels.

5. Consider reducing player-facing exclusion copy after release, while preserving boundary language in Settings, Help, audits, and debug-gated panels.

## 是否阻塞 v3.3 release

Not blocking.

The audit found no high-risk World normal UI privacy or visibility leak. The remaining issues are non-blocking hardening and polish items. v3.3 release can proceed if the standard release checks still pass:

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- `cd frontend && npm.cmd run check:v33-world-ui`
