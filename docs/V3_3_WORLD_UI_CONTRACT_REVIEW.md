# v3.3 World Studio UI Contract Review

Verification date: 2026-05-24

## Current World Routes

- Normal play uses `POST /game/start`, `POST /game/input`, and
  `GET /game/state/{session_id}`.
- Save/load uses `/game/saves`, `/game/{session_id}/save`,
  `/game/load/{save_id}`, save deletion, save import/export, and save migration
  APIs.
- Player-safe graphs use `/game/{session_id}/graphs/relationships` and
  `/game/{session_id}/graphs/factions`.
- Debug and replay routes are under `/debug/...` and remain controlled by
  `ENABLE_DEBUG_API`.
- Quality and playtest surfaces reuse existing local quality/playtest APIs.

## Current World Components

- `frontend/src/App.tsx` contains the main World shell, `WorldStudioLanding`,
  `SaveBrowser`, dialogue panels, social/status panels, debug timeline,
  timeline replay, NPC simulation debugger, gameplay module debugger, and
  crash report viewer.
- v3.3 adds `frontend/src/worldUi.tsx` for reusable World UI Pro presentation
  components: `WorldWorkspaceShell`, visible-state cards, suggested action
  cards, module panels, safe timeline cards, save slot cards, and `DebugGate`.

## Current World Data Flow

- The normal World UI receives `VisibleState` from backend game APIs.
- Player actions are submitted as text to `/game/input`; the frontend does not
  construct or apply `StateDelta`.
- Backend game loop remains responsible for intent parsing, action resolution,
  rules, `StateDelta`, narration, and `EventLog`.
- Save/load and migration stay backend mediated.

## Current visible_state Usage

- Normal World panels render current location, exits, visible NPCs, inventory,
  known facts, quests, social summaries, and active combat only from
  `visible_state`.
- v3.3 panels degrade to empty/disabled states when no player-safe summary
  exists instead of reading raw module state.
- `Visible State Inspector` explicitly labels the displayed data as
  player-visible state, not raw `GameState`.

## Current Debug / EventLog / Timeline UX

- Raw debug events and timeline replay can include raw `state_deltas`.
- v3.3 requires raw EventLog details, raw `StateDelta`, debug timeline, module
  debug summaries, and replay internals to be rendered only inside `DebugGate`.
- Normal timeline/event cards show safe summaries and state that raw
  `state_deltas` are debug-gated.

## Current Advanced Module UX

- Existing normal APIs do not expose rich safe summaries for every advanced
  module.
- v3.3 module panels are therefore informational and action-suggestion based:
  tactical combat can use `visible_state.active_combat`; economy, faction war,
  deduction, survival, magic, hacking, crafting, and cultivation show safe
  available/unavailable states unless a player-safe summary is already present.
- Module actions still flow through backend action handling and
  `ActionRegistry`.

## Current Save / Load UX

- Save cards display safe save metadata: world id/name, turn, visible location,
  formatted time, updated time, and migration status.
- Save UI does not display raw save JSON, raw `GameState`, hidden facts, or raw
  `state_deltas`.
- Destructive save operations continue to require explicit confirmation through
  existing flows.

## Current Quality / Playtest UX

- World quality/playtest panels reuse existing safe reports and local-only
  controls.
- Reports must not print hidden text, raw `state_deltas`, API keys, raw env, or
  provider secrets in normal UI.
- Playtest and quality UI do not call real providers by default and do not
  upload reports.

## Privacy / Visibility Risks

- Raw `state_deltas` already exist in debug/replay components and must remain
  clearly gated.
- Some advanced module internals are only available through debug APIs; normal
  v3.3 panels must not use those APIs as player-facing data.
- Prompt/provider UI must show only safe summaries. It must not reveal raw
  prompts, hidden facts, provider secrets, raw env, or API keys.

## Recommended v3.3 World UI Shape

- Keep `WorldWorkspaceShell` as a presentation shell over existing backend
  APIs.
- Use `visible_state` as the only normal World data source.
- Use empty/disabled states for missing safe module summaries.
- Keep all debug raw details inside `DebugGate`.
- Keep all world-changing actions behind `/game/input` or existing backend
  flows.
- Continue documenting local-first boundaries: no account, no cloud sync, no
  online play platform, no online marketplace, no remote package auto-download.
