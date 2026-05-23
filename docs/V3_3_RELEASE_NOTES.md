# v3.3 Release Notes: World Studio UI Pro

## 1. Version Name

v3.3 **World Studio UI Pro**

## 2. Version Goal

v3.3 turns World Studio into a more usable local open-world play workspace. The
release focuses on World play clarity, visible-state review, map/location
context, NPC and quest review, inventory/trade workflows, advanced module
panels, timeline/EventLog summaries, save/load UX, World quality/playtest
entry points, provider/action status, and safe debug boundaries.

v3.3 remains local-first. It is not an online play platform, account system,
cloud sync feature, multiplayer service, online marketplace, remote package
downloader, or new World Engine authority layer.

## 3. New World UI Capabilities

- World Workspace with World navigation, central story/action workspace, safe
  context sidebar, and local/provider/debug status.
- World Play Main View with narrative log, visible location state, action
  input, suggested actions, recent actions, and safe no-session/loading states.
- Map / Location Panel, NPC / Relationship Panel, Quest / Journal Panel, and
  Inventory / Trade UI.
- Tactical Combat, Economy, Faction War, Deduction, Survival / Travel, and
  Magic / Hacking / Crafting / Cultivation panels.
- Timeline / EventLog UI for player-visible event summaries.
- Visible State Inspector for `visible_state` sections only.
- World Save / Load UX with safe save slot summaries.
- World Quality / Playtest UI.
- World Prompt / Provider UX.
- World Action Input / Suggested Actions UX.
- Safe Debug UI through `DebugGate`.
- v3.3 frontend regression check: `check:v33-world-ui`.
- v3.3 integration regression tests.

## 4. Behavior Changes

- World mode now presents a dedicated World Studio workspace rather than only
  scattered play/debug sections.
- Suggested actions and module action chips fill the normal action flow instead
  of directly applying results.
- Normal World UI is explicitly framed around `visible_state` and safe
  summaries.
- Raw debug/EventLog/StateDelta details are explicitly debug-gated.
- Provider/status copy clarifies that Provider Gateway remains the only model
  entry and that the LLM is not the world judge.

## 5. Frontend Changes

- Added reusable World UI components in `frontend/src/worldUi.tsx`.
- Integrated World UI Pro panels into `frontend/src/App.tsx`.
- Added World workspace, status, card, action, visible-state, save, timeline,
  module, provider, quality, and debug-gate styling in `frontend/src/styles.css`.
- Added `frontend/scripts/check-v33-world-ui.mjs`.
- Added npm script `check:v33-world-ui`.

## 6. Backend API Changes

No major backend API expansion was required for v3.3.

v3.3 reuses existing World and local APIs, including:

- `/game/start`
- `/game/input`
- `/game/state/{session_id}`
- save/load APIs
- debug-gated EventLog / timeline APIs
- local studio config/status summaries
- quality/playtest APIs

Backend behavior remains authoritative. The frontend does not apply
`StateDelta`, write `EventLog`, read database files directly, or calculate
world outcomes.

## 7. World Workspace Changes

- Added `WorldWorkspaceShell`.
- Added local status footer for local-only, World Engine authority, provider,
  and debug-gated status.
- Added left workspace navigation area, central play/action area, and right
  safe context sidebar.
- Added no-session, loading, empty, disabled, and debug-disabled states.

## 8. Map / NPC / Quest / Inventory UI Changes

- Map / Location Panel shows current location, location ref, and visible exits.
- NPC / Relationship Panel shows visible NPCs, mood, relationship safe bands,
  conditions, and talk actions.
- Quest / Journal Panel shows known quest summaries, status, stage, and known
  objectives.
- Inventory / Trade UI shows visible inventory and backend-validated use/trade
  affordances.

These panels use `visible_state` and safe summaries. Hidden locations, hidden
exits, NPC secrets, `npc_knowledge`, hidden quest truth, hidden objectives, and
hidden item properties are not shown in normal UI.

## 9. Advanced Modules UI Changes

- Tactical Combat UI shows encounter safe summary, visible combatants, player
  stance/condition, and tactical action suggestions.
- Economy Dashboard shows safe/degraded market information when no safe normal
  endpoint exists.
- Faction War Dashboard shows known conflict summaries only.
- Deduction Board shows known facts and safe hypothesis actions.
- Survival / Travel UI shows safe travel/rest/camp/forage action entries.
- Magic / Hacking / Crafting / Cultivation panels show safe action surfaces.

Advanced module panels do not judge outcomes. The frontend does not calculate
hits, damage, prices, war outcomes, deduction truth, travel risk, spell results,
hacking results, crafting results, or cultivation breakthroughs.

## 10. Timeline / EventLog / Visible State Changes

- Timeline / EventLog normal view shows player-visible safe event summaries.
- Raw `state_deltas` are not shown in normal view.
- `VisibleStateInspector` shows player, location, visible NPCs, inventory,
  quests, known facts, and module safe summaries from `visible_state`.
- Debug/raw details require `DebugGate` and `ENABLE_DEBUG_API`.

## 11. Save / Load / Quality / Playtest Changes

- Save / Load UX shows safe save slot summaries: world/session/location/time,
  turn, schema, migration status, and updated time.
- Save summaries do not show raw `GameState`, hidden facts, API keys, or raw
  `state_deltas`.
- World Quality / Playtest UI shows local safe report summaries and entry
  points for world quality and playtest workflows.
- Quality/playtest panels do not upload reports and do not call real providers
  by default.

## 12. Provider / Actions / Debug UI Changes

- World Prompt / Provider panel shows safe provider/profile summaries for
  intent parser, narrator, memory summary, and quality eval use cases.
- Action Input supports free text, suggested actions, recent actions, and
  category filtering.
- Action submit still routes through `/game/input`.
- `DebugGate`, `DebugDisabledState`, and debug warning copy clarify that debug
  data requires `ENABLE_DEBUG_API` and is never player-facing.

## 13. Privacy / Visibility / Boundary Changes

Accepted v3.3 boundaries:

- World Engine remains the fact source.
- World UI does not directly modify `GameState`.
- World UI does not directly apply `StateDelta`.
- World state changes still flow through backend action resolution,
  `StateDelta`, and `EventLog`.
- `visible_state` is the normal UI safe source.
- Normal World UI does not show hidden facts, NPC secrets, `npc_knowledge`,
  debug memory, raw prompts, raw `state_deltas`, raw env, provider secrets, or
  API keys.
- Provider Gateway remains the only model entry.
- IntentParser parses input; Narrator renders confirmed visible results. LLMs
  do not judge world outcomes.
- No account, cloud sync, online play, online marketplace, remote package
  auto-download, or multiplayer entry was added.

## 14. Known Limitations

- v3.3 is not a new World Engine rule release.
- v3.3 is not an online play platform.
- v3.3 does not add account support.
- v3.3 does not add cloud sync.
- v3.3 does not add multiplayer online play.
- Tactical Combat UI is not a full tactical grid or complete tactics-game
  rewrite.
- Economy Dashboard is not a full market simulator UI.
- Faction War Dashboard is not a grand-strategy interface.
- Deduction Board does not solve cases or reveal hidden truth.
- Magic / Hacking / Crafting / Cultivation panels expose safe action surfaces;
  backend rules still decide outcomes.
- Some action labels remain command-like and can be improved in a future polish
  pass.
- Frontend build currently emits a Vite chunk-size warning, but the production
  build succeeds.

## 15. Upgrade Notes from v3.2

- v3.2 Tavern Studio UI Pro remains intact.
- v3.3 adds World UI Pro surfaces without changing Novel/Tavern authority
  boundaries.
- Existing World APIs remain compatible; the v3.3 UI reuses the existing
  backend action, state, save/load, debug, quality, and local status APIs.
- Existing provider configuration remains valid. Provider Gateway remains the
  model boundary and API keys still stay backend/local-secret only.
- Projects do not need cloud accounts, online sync, or remote package access to
  use v3.3.
- Debug users should keep `ENABLE_DEBUG_API` disabled unless they intentionally
  need local debug views.

## 16. Recommended v3.4 Direction

Recommended v3.4 theme: **Authoring / Mod UI Pro**.

Suggested priorities:

- Authoring Workspace Layout Pro.
- Visual Map / Location Editor Pro.
- Quest Graph Editor Pro.
- NPC / Relationship / Faction Authoring Pro.
- Item / Economy Authoring Pro.
- Module Authoring Dashboard Pro.
- Content Pack Browser / Validation UX Pro.
- Script / Mod Package Review UX Pro.
- Action Mod Editor Pro.
- Rule Module Permission / Compatibility Dashboard.
- Authoring Quality Gate Dashboard.
- Safer raw-debug component isolation for future QA/debug polish.

## Verification

v3.3 acceptance verification:

```powershell
python -m pytest
```

Result: passed, `1730 passed`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed with the existing Vite chunk-size warning.
