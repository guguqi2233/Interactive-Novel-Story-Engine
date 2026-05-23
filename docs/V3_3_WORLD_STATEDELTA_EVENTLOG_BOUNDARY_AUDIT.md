# v3.3 World StateDelta / EventLog Boundary Audit

Verification date: 2026-05-24

Scope: v3.3 World Studio UI Pro action flow, advanced module panels, save/load,
debug UI, Provider/Narrator boundary, and integration tests related to
`GameState`, `StateDelta`, and `EventLog`.

Reviewed evidence:

- `AGENTS.md`
- `docs/V3_3_ROADMAP.md`
- `frontend/src/worldUi.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v33-world-ui.mjs`
- `backend/tests/test_v33_integration_regression.py`
- targeted source search for `apply_delta`, `StateDelta`, `state_deltas`,
  `/game/input`, `GameState`, tactical/economy/deduction/survival terms, and
  provider / narrator routing

## Audit Summary

Verdict: Pass with non-blocking hardening notes.

The v3.3 World UI Pro implementation does not introduce a frontend authority
path for mutating `GameState`, applying `StateDelta`, deciding advanced-module
outcomes, or writing `EventLog`. World-changing interaction remains routed
through the backend `/game/input` flow via `submitPlayerInput`. The backend
regression test verifies that successful world actions record `EventLog`
entries and carry `StateDelta` entries, while normal `/game/state` responses do
not expose raw `state_deltas`.

No high-risk `GameState` / `StateDelta` / `EventLog` boundary issue was found.

## 已通过项目

1. World UI does not directly modify `GameState`.
   - `frontend/src/App.tsx` v3.3 static regression asserts `apply_delta(` and
     `StateDelta(` do not appear in the frontend app source.
   - v3.3 UI copy states that World UI does not directly modify `GameState`.

2. World UI does not directly apply `StateDelta`.
   - `WorldActionInputPanel` states that actions submit through `/game/input`
     and that UI does not apply `StateDelta`.
   - No frontend v3.3 World panel creates or applies `StateDelta` objects.

3. World UI action submit does not bypass `/game/input` or backend action API.
   - `frontend/src/api.ts` exposes `submitPlayerInput`, which posts to
     `/game/input`.
   - `frontend/src/App.tsx` `handleSubmit` calls
     `submitPlayerInput(sessionId, trimmedInput)`.
   - Suggested action cards and module action chips only fill/select action
     strings and feed the same input/submit path.

4. Tactical UI does not calculate hit or damage.
   - `TacticalCombatPanel` displays visible combat summaries and action
     suggestions only.
   - The panel states hidden combatants and debug rolls are excluded and combat
     results are backend-authoritative.

5. Economy UI does not calculate authoritative prices.
   - `InventoryTradePanel` states that no authoritative prices are calculated
     in the frontend.
   - `EconomyDashboardPanel` uses safe/degraded summaries and does not expose
     raw economy state.

6. Faction War UI does not decide war outcomes.
   - `FactionWarDashboardPanel` displays known faction conflict summaries only.
   - It does not contain controls or logic to resolve conflict state.

7. Deduction UI does not judge hidden truth.
   - `DeductionBoardPanel` displays known facts and offers safe action strings
     such as `form_hypothesis` and `test_hypothesis`.
   - It explicitly excludes hidden truth and debug solution from normal view.

8. Survival UI does not judge travel risk.
   - `SurvivalTravelPanel` displays safe route/action summaries only.
   - Travel-related actions are submitted as backend action strings and hidden
     route danger is not shown.

9. Magic / Hacking / Crafting / Cultivation UI does not decide results.
   - `WorldAdvancedModulePanels` provides safe summaries and action chips only.
   - It does not compute spell, hack, crafting, or cultivation outcomes.

10. Save / Load UI does not directly read or write the database.
    - `WorldSaveLoadPanel` displays `SaveSummary` / migration status data
      provided through existing API state.
    - It does not access SQLite files or local database paths directly.

11. Debug UI does not modify `GameState`.
    - `DebugGate` is a display gate with warning/disabled states.
    - The reviewed v3.3 debug panel renders raw debug details only when gated;
      no debug write/apply controls were found in v3.3 World UI.

12. `EventLog` still records world actions.
    - `backend/tests/test_v33_integration_regression.py` starts a world, submits
      `/game/input`, reads the session `event_log`, and asserts events exist.
    - The same test asserts at least one successful world action carries
      `StateDelta` entries.

13. UI does not display raw `state_deltas` in normal view.
    - `WorldTimelineEventLogPanel` filters normal events and only shows safe
      summaries.
    - Raw `state_deltas` rendering in `App.tsx` is inside debug-oriented
      surfaces, including the v3.3 `DebugGate` panel.
    - The backend regression test verifies `/game/state` text does not include
      `state_deltas`.

14. Tests do not call real APIs.
    - v3.3 integration tests configure `llm_provider="mock"` and use local
      temporary SQLite paths.
    - No real OpenAI/provider API call is required by the v3.3 regression tests.

15. Provider / Narrator remains outside world authority.
    - v3.3 regression checks confirm `session_store.py` still routes world
      providers through `world_routed_provider_from_settings`,
      `IntentParser(provider...)`, and `Narrator(provider...)`.
    - World UI provider panels display safe routing summaries and do not make
      the provider or narrator a world judge.

## 高风险问题

None found.

No reviewed v3.3 World UI surface directly mutates `GameState`, directly applies
`StateDelta`, bypasses `/game/input`, computes authoritative module outcomes, or
lets debug UI write world state.

## 中风险问题

1. Legacy debug/timeline rendering remains close to normal app code.
   - `frontend/src/App.tsx` still contains raw `state_deltas` rendering in
     debug-oriented timeline/event components.
   - Current v3.3 workspace gates raw details behind `DebugGate`, and tests
     verify normal `/game/state` excludes raw deltas.
   - Risk: future UI refactors could accidentally reuse a debug component in a
     normal route if the debug boundary is not kept explicit.

2. Suggested action labels are plain strings.
   - Module and suggested action chips pass text such as `strike`,
     `travel_route`, `hack_terminal`, or `test_hypothesis` into the input flow.
   - This is acceptable because the backend remains authoritative, but future
     UI improvements should avoid making those labels look like guaranteed
     outcomes.

## 小问题

1. Some advanced module panels are safe but intentionally shallow.
   - They render action options and safe/degraded summaries rather than rich
     backend-calculated previews.
   - This avoids boundary risk but limits usability until dedicated safe
     summary APIs exist.

2. Static frontend checks catch direct frontend `StateDelta` use and normal raw
   delta rendering, but they are not semantic UI tests.
   - This is acceptable for v3.3 because the project intentionally avoids a
     large E2E dependency for UI smoke checks.

3. Save/load UI currently focuses on safe summaries.
   - Delete/archive confirmation and richer migration previews should remain
     backend-mediated if expanded later.

## 修复建议

1. Keep all world-changing controls routed through `/game/input` or explicit
   backend world APIs. Do not add frontend state mutation helpers.

2. Keep raw `state_deltas`, raw EventLog details, and debug module state inside
   `DebugGate` and behind `ENABLE_DEBUG_API`.

3. Add a future static check that any `JSON.stringify(event.state_deltas...)`
   usage must appear only in approved debug components.

4. When advanced module panels become richer, add backend safe-summary APIs for
   combat, economy, faction war, deduction, survival, magic, hacking, crafting,
   and cultivation instead of duplicating rule logic in frontend.

5. Keep Provider / Narrator panels framed as routing and rendering summaries.
   They must not expose controls that decide action success, world facts, or
   proposal apply.

## 是否阻塞 v3.3 acceptance

Not blocking.

The audit found no high-risk `GameState`, `StateDelta`, or `EventLog` boundary
issue. v3.3 acceptance can proceed if the standard verification remains green:

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- `cd frontend && npm.cmd run check:v33-world-ui`
