# v3.3 Roadmap: World Studio UI Pro

## Version Goal

v3.3 turns World Studio from a usable local world-play entry into a daily-use
local open-world play workspace. The release focuses on World play clarity,
map/location awareness, NPC and relationship review, quest journaling,
inventory/item/trade workflows, tactical combat, economy, faction war,
deduction, survival/travel, magic, hacking, crafting, cultivation, timeline and
EventLog review, visible-state inspection, save/load, and World quality /
playtest workflows.

v3.3 remains local-first, privacy-first, and World Engine-first. The World
Engine is still the fact source. `visible_state` is the normal UI state source.
World UI can display safe state and call backend APIs, but it cannot directly
modify `GameState`, bypass validation, bypass `StateDelta`, bypass `EventLog`,
or turn LLM output into world truth.

## Non-Goals

v3.3 explicitly does not implement:

- online play platform;
- account system;
- cloud sync;
- multiplayer online play;
- online marketplace;
- remote package auto-download;
- new large gameplay modules;
- complete grand-strategy simulation;
- complete complex-economy rewrite;
- complete tactics-game rewrite;
- arbitrary code plugins;
- direct World UI mutation of `GameState`;
- frontend bypass of backend APIs, validation, `StateDelta`, or `EventLog`;
- normal UI display of hidden facts, NPC secrets, debug memory, or raw
  `state_deltas`;
- Debug UI access when `ENABLE_DEBUG_API=false`;
- API key, raw env, or provider secret display in UI;
- LLM as world judge;
- Mature Module default enablement.

## Hard Constraints

- Local-first behavior is mandatory.
- World Engine remains the authoritative fact source.
- UI only displays data and calls backend APIs.
- All world state changes must flow through `StateDelta`.
- World-changing events must record `EventLog`.
- `visible_state` is the only safe normal-state source for World normal UI.
- Hidden facts, NPC secrets, debug memory, and raw `state_deltas` must not enter
  normal UI.
- Debug UI must be gated by `ENABLE_DEBUG_API`.
- Provider Gateway remains the only model entry point.
- Narrator renders confirmed results only.
- Advanced Modules UI cannot change module rule authority.
- New pages must support loading, empty, error, and disabled states.
- Dangerous operations must require explicit confirmation.
- `python -m pytest` must pass.
- `cd frontend && npm.cmd run build` must pass.

## Recommended Development Order

1. World Studio UI Contract Review.
2. World Workspace Layout Pro.
3. World Play Main View Pro.
4. Map / Location Panel.
5. NPC / Relationship Panel.
6. Quest / Journal Panel.
7. Inventory / Item / Trade UI.
8. Tactical Combat UI Pro.
9. Economy Dashboard UI.
10. Faction War Dashboard UI.
11. Deduction Board UI.
12. Survival / Travel UI.
13. Magic / Hacking / Crafting / Cultivation Module UI.
14. World Timeline / EventLog UI Pro.
15. Visible State Inspector.
16. World Save / Load UX Pro.
17. World Quality / Playtest UI.
18. World Prompt / Provider UX Polish.
19. World Action Input / Suggested Actions UX.
20. World Debug Boundary / Safe Debug UI.
21. World UI Component Cleanup.
22. World UI Regression Tests.
23. v3.3 Integration Regression Tests.

This order starts with boundaries and layout, then normal play surfaces, then
module-specific panels, then timeline/debug/save/quality, and finally
regression hardening.

## Scope

### 1. World Studio UI Contract Review

Goal: document current World UI routes, APIs, data flow, visibility handling,
debug boundaries, Provider Gateway use, advanced-module surfaces, and risks.

Frontend changes:

- No product UI changes required.
- Review `frontend/src/App.tsx`, `frontend/src/api.ts`, and any World-related
  component extraction points.

Backend changes:

- None unless a newly discovered high-risk safety blocker requires a minimal
  fix.

Testing requirements:

- No new tests required for a documentation-only slice.
- If a safety blocker is fixed, add focused regression coverage.

Acceptance:

- `docs/V3_3_WORLD_UI_CONTRACT_REVIEW.md` exists.
- It identifies normal World UI, authoring UI, debug UI, save/load, quality,
  playtest, advanced modules, and Provider Gateway boundaries.

### 2. World Workspace Layout Pro

Goal: establish a unified World workspace with left navigation, central play or
panel area, right safe context sidebar, and bottom local status bar.

Frontend changes:

- Add a `WorldWorkspaceShell` or equivalent shared layout.
- Left nav: Play, Map, NPCs, Quests, Inventory, Combat, Economy, Factions,
  Deduction, Survival, Modules, Timeline, Saves, Quality.
- Right sidebar: visible location, visible NPCs, active quest summary, provider
  status, local-only status, debug-gated status.
- Bottom status: save state, turn, local-only, debug disabled/enabled, provider
  safe summary.

Backend changes:

- Prefer existing `/game/*`, save, local-studio status, quality, and debug
  APIs.
- Add only safe-summary endpoints if existing data cannot support the layout
  without leaking debug/raw state.

Testing requirements:

- Frontend build.
- UI smoke check that imports the World workspace.
- Verify no hidden facts, API keys, raw env, or raw `state_deltas` in normal
  shell text.

Acceptance:

- Works with no active session, active session, API disabled, and debug disabled
  states.
- Normal layout uses `visible_state` and safe summaries only.

### 3. World Play Main View Pro

Goal: improve the main local play experience: narrative feed, visible state
summary, action input, suggested actions, recent results, and local status.

Frontend changes:

- Redesign play view around visible location, narrative feed, action input, and
  suggested actions.
- Add loading, empty, error, and disabled states for no session / backend
  unavailable.
- Keep dialogue/group RP surfaces separate from World normal play if shown.

Backend changes:

- Reuse `POST /game/start`, `POST /game/input`, and
  `GET /game/state/{session_id}`.
- Do not add direct state-write endpoints.

Testing requirements:

- Existing World API tests remain passing.
- Frontend build.
- Regression check that play view does not render raw `GameState` or
  `state_deltas`.

Acceptance:

- Player actions call backend APIs only.
- Updated play result shows confirmed visible outcome and updated
  `visible_state`.

### 4. Map / Location Panel

Goal: provide a player-safe map/location panel for visible locations, exits,
known routes, location tags, and local map context.

Frontend changes:

- Display current location, visible exits, known/visible connected locations,
  and safe location notes.
- Show hidden/unknown routes only as counts or redacted labels if backend
  provides safe summaries.
- Include navigation affordances that fill action input rather than directly
  mutating state.

Backend changes:

- Prefer `visible_state.location`, visible objects, and visible exits.
- If needed, add a safe map-summary API that filters hidden locations/routes.

Testing requirements:

- Hidden locations/routes do not appear in normal map panel.
- Frontend build.

Acceptance:

- Map panel reflects visible state and never reveals hidden location facts.

### 5. NPC / Relationship Panel

Goal: show visible NPCs, player-known relationship summaries, dialogue entry
points, and safe social context.

Frontend changes:

- Visible NPC list with disposition/status summaries where available.
- Relationship/faction graph normal view uses player-safe graph APIs.
- Actions such as talk, inspect, or follow fill action input or call safe
  backend APIs.

Backend changes:

- Reuse visible NPCs and player-safe graph APIs.
- Add safe relationship summary only if needed.

Testing requirements:

- Hidden NPCs and NPC secrets do not appear in normal panel.
- Debug graph data remains debug-gated.

Acceptance:

- Normal panel shows only visible/known NPC information.

### 6. Quest / Journal Panel

Goal: provide a clearer quest journal for active, completed, failed, and
discoverable player-known quest information.

Frontend changes:

- Quest cards with stage, known objectives, rewards if visible, and next action
  hints.
- Filter active/completed/blocked.
- Link to map/NPC panels where safe refs exist.

Backend changes:

- Reuse `visible_state.quests`.
- Add safe quest journal summary only if current visible state is insufficient.

Testing requirements:

- Hidden quest triggers, hidden witnesses, and secret outcomes do not render.
- Frontend build.

Acceptance:

- Journal is useful for player-known progress and does not reveal hidden quest
  facts.

### 7. Inventory / Item / Trade UI

Goal: polish visible inventory, item details, use/equip/drop suggestions, and
safe trade/shop summaries.

Frontend changes:

- Inventory item list with visible item metadata.
- Item detail panel with safe action suggestions.
- Trade/shop panel for visible merchants and public prices.

Backend changes:

- Reuse visible inventory and shop/trade APIs if present.
- Add safe trade summary only if needed.

Testing requirements:

- Hidden item ownership, hidden contraband metadata, and secret prices do not
  leak.
- Trade actions use backend validation.

Acceptance:

- Inventory/trade UI cannot bypass item rules or mutate state directly.

### 8. Tactical Combat UI Pro

Goal: present tactical combat state clearly without rewriting combat rules or
turn resolution.

Frontend changes:

- Combat summary, visible combatants, turn/initiative, HP/status summaries,
  available combat actions, and recent combat result.
- Hidden combatants are omitted or counted as redacted if backend supplies a
  safe count.

Backend changes:

- Reuse tactical visible summaries and action result data.
- Add safe combat summary only if required.

Testing requirements:

- Hidden combatants do not appear in normal UI.
- Combat action buttons fill action input or call backend action APIs.

Acceptance:

- Combat UI improves clarity but does not become a tactics engine rewrite.

### 9. Economy Dashboard UI

Goal: show player-safe economy and market summaries for known regions,
commodities, shops, and trade opportunities.

Frontend changes:

- Known market cards, visible price modifiers, local scarcity hints, merchant
  summaries.
- Warnings when economy data is unavailable or hidden.

Backend changes:

- Reuse economy safe summaries or add read-only safe economy summary.

Testing requirements:

- Hidden supply/demand, secret faction manipulation, and debug economy data stay
  out of normal UI.

Acceptance:

- Dashboard is informational and does not alter economy simulation rules.

### 10. Faction War Dashboard UI

Goal: expose player-known faction-war state, visible control, conflict pressure,
front summaries, and public events.

Frontend changes:

- Faction cards, known region control, public conflict status, safe rumors.
- Links to quest/NPC/location panels where safe.

Backend changes:

- Reuse faction-war visible summaries or add safe read-only summary.

Testing requirements:

- Hidden faction plans, secret agents, undiscovered conflicts, and debug plans
  do not render.

Acceptance:

- Faction war UI shows known consequences only and cannot decide outcomes.

### 11. Deduction Board UI

Goal: provide a player-known board for evidence, claims, hypotheses, and
contradictions without revealing the hidden truth.

Frontend changes:

- Evidence cards, testimony/claim list, hypothesis board, contradiction
  warnings.
- User notes may be local UI state or project-local authoring data if already
  supported.

Backend changes:

- Reuse deduction module safe summaries.
- Add safe deduction summary only if needed.

Testing requirements:

- Hidden truth refs and unrevealed evidence do not appear.
- Hypothesis changes do not write World facts.

Acceptance:

- Deduction UI helps reason from known evidence only.

### 12. Survival / Travel UI

Goal: clarify fatigue, hunger, thirst, weather, route risk, camp status, and
travel choices from player-visible data.

Frontend changes:

- Survival status panel.
- Known route cards with visible cost/risk summaries.
- Travel/rest/camp/forage actions as backend-validated suggestions.

Backend changes:

- Reuse survival visible summaries or add read-only safe travel summary.

Testing requirements:

- Hidden routes and hidden observers do not appear.
- Travel actions still resolve through backend rules.

Acceptance:

- Survival UI does not bypass travel, stealth, visibility, or resource rules.

### 13. Magic / Hacking / Crafting / Cultivation Module UI

Goal: give each advanced module a safe, compact panel that explains current
player-known state and available actions.

Frontend changes:

- Magic: visible resources, known spells, safe effects.
- Hacking: visible targets, tools, access status, safe risks.
- Crafting: known recipes, materials, station status.
- Cultivation: visible realm/stage/progress summaries, known techniques.
- Shared disabled state when a module is unavailable.

Backend changes:

- Reuse advanced module safe summaries.
- Add safe module summary endpoints only if existing APIs expose too much debug
  data.

Testing requirements:

- Hidden spells, secret networks, hidden recipe outcomes, and debug module data
  do not enter normal UI.
- Module actions still use ActionRegistry / StateDelta / EventLog.

Acceptance:

- Module UI improves discoverability without changing module rule authority.

### 14. World Timeline / EventLog UI Pro

Goal: split normal event history from debug raw EventLog / Timeline Replay.

Frontend changes:

- Normal history: safe event summaries, visible changes, turn grouping, filters.
- Debug timeline: raw `state_deltas` and replay details only when
  `ENABLE_DEBUG_API=true`.
- Add clear debug disabled state.

Backend changes:

- Prefer existing debug timeline routes for debug view.
- If normal history needs data, add a safe EventLog summary endpoint that
  excludes raw deltas and hidden/debug events.

Testing requirements:

- Normal timeline does not render raw `state_deltas`.
- Debug timeline returns 403 or disabled copy when debug API is off.

Acceptance:

- Users can review visible history safely while debug details remain gated.

### 15. Visible State Inspector

Goal: provide a transparent normal-state inspector based only on
`visible_state`.

Frontend changes:

- Show current location, visible NPCs, visible objects, known facts, quests,
  inventory, public social/combat/survival summaries.
- Explain that this is not raw `GameState`.

Backend changes:

- Reuse `GET /game/state/{session_id}`.

Testing requirements:

- Inspector has no raw `GameState`, hidden facts, NPC secrets, debug memory, or
  raw `state_deltas`.

Acceptance:

- Inspector is a normal UI debugging aid without debug-only data.

### 16. World Save / Load UX Pro

Goal: improve save browser, load confirmation, migration status, export/import
safe policy, and recovery guidance.

Frontend changes:

- Save list with world id, turn, created/updated time, migration status, safe
  summary.
- Load/delete/export/import confirmation flows.
- Migration dry-run/apply states.

Backend changes:

- Reuse save repository, migration, import/export APIs.
- Add safe save summary fields only if necessary.

Testing requirements:

- Dangerous operations require confirmation.
- Save summaries exclude raw `GameState`, hidden facts, raw deltas, and
  secrets.

Acceptance:

- Save/load is clear, local, and privacy-safe.

### 17. World Quality / Playtest UI

Goal: make World quality, hidden leak checks, playtests, health score,
coverage, migration stress, and performance summaries easier to run and read.

Frontend changes:

- World Quality dashboard with blockers, warnings, category summaries, recent
  playtests, and next actions.
- Playtest launcher with local-only/mock-provider reminders.
- Safe report rows with jump targets where possible.

Backend changes:

- Reuse project/world quality, playtest, and report APIs.
- Add safe report summary only if current reports expose debug/raw data.

Testing requirements:

- Quality reports do not print hidden text in full in normal UI.
- Playtests do not call real providers.

Acceptance:

- Quality UI supports release confidence without uploading data or using LLM
  judges.

### 18. World Prompt / Provider UX Polish

Goal: show which provider/prompt context is used for World intent parsing and
narration without exposing secrets or hidden facts.

Frontend changes:

- Panel showing selected provider safe summary, model id, world intent parse
  use case, world narration use case, capability warnings, and safe context
  policy.
- Link to Provider Setup Wizard.

Backend changes:

- Optional safe prompt-context preview for World intent/narration if existing
  provider summaries are insufficient.
- Preview must exclude hidden facts, raw prompts, raw env, API keys, and raw
  `state_deltas`.

Testing requirements:

- Provider summary contains no API key.
- Prompt context preview excludes hidden facts and raw state.

Acceptance:

- Provider UX informs users without widening LLM authority.

### 19. World Action Input / Suggested Actions UX

Goal: polish action entry with clear affordances, command hints, disabled
states, and backend-validated suggested actions.

Frontend changes:

- Action input toolbar.
- Suggested actions grouped by movement, talk, inspect, inventory, combat,
  module actions where safe.
- Clear errors and retry states.

Backend changes:

- Prefer existing suggested actions from narration and ActionRegistry.
- Add safe suggested-action endpoint only if needed.

Testing requirements:

- Suggested actions do not include hidden targets.
- Submitting still calls backend `/game/input`.

Acceptance:

- Action UX is clearer but remains backend-authoritative.

### 20. World Debug Boundary / Safe Debug UI

Goal: make Debug UI boundaries explicit and safer.

Frontend changes:

- Debug landing/disabled state when `ENABLE_DEBUG_API=false`.
- Clear separation between normal World UI, authoring UI, and debug UI.
- Raw `state_deltas` and debug memory labels must only appear in debug-gated
  surfaces.

Backend changes:

- Reuse `require_debug_api()`.
- No weakening of debug gate.

Testing requirements:

- Debug APIs unavailable when disabled.
- Normal UI check rejects raw delta/debug strings.

Acceptance:

- Debug UI cannot be mistaken for normal player UI.

### 21. World UI Component Cleanup

Goal: extract reusable World UI components without changing business logic.

Frontend changes:

- Candidate components: `WorldWorkspaceShell`, `WorldStatusBadge`,
  `VisibleStateCard`, `LocationCard`, `NPCSummaryCard`, `QuestJournalCard`,
  `InventoryItemCard`, `CombatantCard`, `TimelineEventSummaryCard`,
  `SaveSummaryCard`, `WorldSafeSummaryPanel`, `WorldToolbar`.
- Keep extraction scoped and avoid large UI dependencies.

Backend changes:

- None.

Testing requirements:

- Frontend build.
- Existing World pages compile.

Acceptance:

- UI code is easier to maintain without changing APIs or boundaries.

### 22. World UI Regression Tests

Goal: add lightweight frontend/static checks for v3.3 World UI.

Frontend changes:

- Add a script such as `frontend/scripts/check-v33-world-ui.mjs`.
- Add npm script `check:v33-world-ui`.

Backend changes:

- None.

Testing requirements:

- Check World components are importable.
- Check no API key/plain secret UI.
- Check normal UI does not include raw `state_deltas`, hidden facts, NPC
  secrets, or debug memory outside explicitly debug-gated copy.
- Check no account/cloud/online play/marketplace primary entry.

Acceptance:

- `npm.cmd run check:v33-world-ui` passes.

### 23. v3.3 Integration Regression Tests

Goal: verify v3.3 does not break v2.1-v3.2 features and preserves World fact
boundaries.

Backend changes:

- Add focused pytest coverage where new safe-summary APIs or services are
  introduced.

Testing requirements:

- `/game/start`, `/game/input`, `/game/state/{session_id}` remain compatible.
- World UI/API paths do not directly mutate `GameState`.
- World state changes still pass through `StateDelta` and record `EventLog`.
- Debug APIs remain gated.
- Advanced module summaries do not leak hidden/debug data.
- Save/load summaries do not leak raw state or secrets.
- No real provider calls.
- No uploads.
- Full `python -m pytest` passes.
- Frontend build passes.

Acceptance:

- v3.3 integration regression tests pass with the full suite.

## Impact Review

### World Studio Impact

World Studio gains the main product value in v3.3: a clearer daily-use local
World workspace, better normal play state, safer timeline/debug separation,
better save/load, and more understandable advanced module panels.

### Novel Studio Impact

Novel Studio should not receive direct feature changes. World -> Novel import
and shared timeline summaries may benefit from clearer World safe summaries, but
Novel drafts remain non-authoritative and Novel UI must continue to avoid
hidden/debug/raw World data.

### Tavern Studio Impact

Tavern Studio should not receive direct feature changes. Tavern -> World
proposal review may benefit from clearer World safe summaries, but Tavern
sessions remain RP data and cannot directly modify World state.

### Cross-Mode Bridge Impact

Cross-Mode Bridge remains proposal/draft/review infrastructure. v3.3 may expose
clearer World-side context for proposals, but it must not allow Novel or Tavern
artifacts to bypass validation or explicit apply.

### Provider Gateway Impact

Provider Gateway remains the only model entry point. World Prompt / Provider UI
may display safe summaries for intent parsing and narration, but it cannot show
API keys, raw prompts, hidden facts, raw `GameState`, or raw `state_deltas`.

### Advanced World Modules Impact

Advanced modules receive UI polish and safe summaries only. v3.3 does not add
new large modules, rewrite module rules, or let UI decide module outcomes.
Module actions still require ActionRegistry, backend validation,
`StateDelta`, `EventLog`, visibility, and quality gates.

### Quality Gate Impact

World Quality / Playtest UI should make deterministic quality reports easier to
run and read. Quality Gate remains local and deterministic. It should not upload
reports, call external LLM judges for pass/fail, or print hidden text in normal
reports.

### Privacy / Security / Visibility Impact

v3.3 must strengthen normal/debug separation:

- normal World UI uses `visible_state` and safe summaries;
- debug raw deltas and replay details require `ENABLE_DEBUG_API`;
- hidden facts, NPC secrets, debug memory, raw prompts, raw env, provider
  secrets, API keys, and raw `state_deltas` do not enter normal UI;
- save/load/export/quality surfaces remain redacted by default;
- no account, cloud sync, online play, online marketplace, remote package
  download, or telemetry upload is introduced.

## Testing / Verification

Required v3.3 verification commands:

```powershell
python -m pytest
```

```powershell
cd frontend
npm.cmd run build
```

Recommended additional checks:

```powershell
cd frontend
npm.cmd run check:v33-world-ui
```

If safe-summary APIs or module panels are added, add focused pytest coverage
for:

- visible-state-only normal summaries;
- hidden/NPC-secret redaction;
- debug API disabled behavior;
- save/load safe summaries;
- advanced module safe summaries;
- Provider Gateway-only world LLM routing;
- no real provider calls;
- no uploads.

## Known Limitations

- v3.3 is not an online play platform.
- v3.3 does not add account login, cloud sync, or multiplayer online play.
- v3.3 does not add new large gameplay modules.
- v3.3 does not implement a complete grand-strategy, full economy simulator, or
  full tactics-game rewrite.
- v3.3 does not replace authoring tools with a full standalone world editor.
- Debug timeline and raw delta details remain local debug tools, not normal UI.
- Some advanced module panels may initially show safe summaries or disabled
  states when deeper backend data is unavailable.
- The frontend bundle may continue to emit a non-blocking chunk-size warning
  until future code-splitting work.

## Recommended v3.4 Candidate Direction

Recommended v3.4 direction: **Authoring / Mod UI Pro**.

Candidate priorities:

- Authoring Workspace Layout Pro.
- Map Editor Pro.
- Quest Graph Editor Pro.
- NPC / Faction / Relationship Authoring Pro.
- Item / Economy / Rumor / Crime Authoring Pro.
- Script / Mod Package Builder Pro.
- Module Browser / Certification UX Pro.
- Action Mod DSL Editor Pro.
- Package Import / Export Review Pro.
- Compatibility Matrix UI Pro.
- Authoring Validation / Diff / Apply UX Pro.

v3.4 should keep the same local-first posture: authoring UI may edit local
content files after validation and confirmation, but it must not directly
modify active `GameState`, bypass package validation, execute arbitrary code,
or weaken Provider Gateway / visibility / export boundaries.
