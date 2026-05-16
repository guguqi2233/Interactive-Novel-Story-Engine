# v0.3 Roadmap

## Goal

v0.3 upgrades the project from a persistent interactive novel engine into a more trustworthy simulated world with NPC behavior, advanced player actions, inventory rules, quest state, and a debug timeline.

The release must preserve the core architecture:

- The LLM does not directly modify `GameState`.
- All canonical state changes go through `StateDelta`.
- All player actions and autonomous world changes are recorded as `Event`.
- Hidden facts do not enter `visible_state` or narrator prompts.
- NPCs cannot act or speak from facts they do not know.
- Business code depends on `LLMProvider`, not concrete provider classes.

## Current Baseline

v0.2.1 has:

- Unified `state_deltas`.
- `facts.yaml` content-pack support.
- Multi-world `/game/start`.
- SQLite save/load API.
- Structured `visible_state`.
- Centralized provider factory.
- Frontend world selector and save/load controls.

## Recommended Development Order

1. Quest state machine foundation.
2. Inventory rules.
3. `search` action.
4. `lockpick` action.
5. `sneak` action.
6. NPC schedule resolver.
7. NPC autonomous event tick.
8. Debug timeline API and frontend viewer.
9. v0.3 integration tests and acceptance report.

This order builds the deterministic state/rule substrate before adding autonomous behavior and UI.

## Module 1: Quest State Machine

### Goal

Add the first structured quest state system so quests can be visible, started, progressed, completed, or failed without relying on prose.

### Data Structures

Add or extend:

- `QuestState`
  - `id: str`
  - `status: inactive | active | completed | failed`
  - `stage: str | None`
  - `known_to_player: bool`
  - `objectives: list[QuestObjectiveState]`
- `QuestObjectiveState`
  - `id: str`
  - `description: str`
  - `status: inactive | active | completed | failed`
  - `visible: bool`

Content-pack `quests.yaml` may later include initial quest definitions, but v0.3 should keep this minimal.

### Interfaces

- `backend/app/engine/rules/quests.py`
  - `get_visible_quests(state) -> list[VisibleQuestResponse]`
  - `apply_quest_progress(state, trigger) -> list[StateDelta]`
  - `quest_is_active(state, quest_id) -> bool`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/api.py`
- `backend/app/session_store.py`
- `backend/app/engine/rules/quests.py`
- `backend/tests/test_quests.py`
- `backend/tests/test_game_api.py`

### Test Requirements

- Quest starts inactive by default.
- Quest can become active through a `StateDelta`.
- Quest objective can complete through a `StateDelta`.
- Completed/failed quests cannot silently regress.
- `visible_state.quests` exposes only player-visible quests/objectives.
- Hidden quest stages do not appear in API responses.

### Acceptance Standard

The frontend receives structured quest summaries from `visible_state`, and all quest status changes are replayable through events and deltas.

### Not In v0.3

- Branching quest authoring UI.
- Complex quest scripting language.
- Automatic LLM-authored quests.

## Module 2: Inventory Rules

### Goal

Make inventory a real deterministic system instead of a placeholder list.

### Data Structures

Extend object/item state as needed:

- `WorldObjectState`
  - `portable: bool = False`
  - `locked: bool = False`
  - `key_id: str | None = None`
  - `tags: list[str]`

Inventory remains authoritative on `GameState.player.inventory`.

### Interfaces

- `backend/app/engine/rules/inventory.py`
  - `can_take_item(state, actor_id, item_id) -> RuleResult`
  - `make_take_item_deltas(state, item_id) -> list[StateDelta]`
  - `has_item(state, actor_id, item_id) -> bool`
  - `item_visible_to_player(state, item_id) -> bool`

Potential action additions:

- `take`
- `drop`

Only add these if needed to support lockpick/search flows.

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/actions/basic.py`
- `backend/app/engine/actions/schemas.py`
- `backend/app/engine/action_dispatcher.py`
- `backend/app/engine/rules/inventory.py`
- `backend/app/engine/content/world_loader.py`
- `backend/tests/test_inventory.py`

### Test Requirements

- Player can take a visible portable item.
- Player cannot take hidden undiscovered item.
- Player cannot take non-portable item.
- Taking an item moves it through `StateDelta`.
- Inventory appears in `visible_state.inventory`.
- Failed take/drop still creates an `Event` if routed through `GameLoop`.

### Acceptance Standard

Inventory changes are deterministic, visible to the API, and fully represented by `StateDelta` and `Event`.

### Not In v0.3

- Weight, capacity, item durability, crafting, equipment slots.

## Module 3: search Action

### Goal

Add a deterministic `search` action that lets players discover hidden objects or facts in the current location.

### Data Structures

Use existing:

- `WorldObjectState.hidden`
- `WorldObjectState.discovered_by`
- `FactState.visibility`
- `GameState.player_visible_facts`

Optional content fields:

- object `search_difficulty: int`
- fact `discoverable_at: list[str]`

### Interfaces

- `PlayerActionType.SEARCH`
- `SearchActionHandler`
- `backend/app/engine/rules/search.py`
  - `resolve_search_targets(state, actor_id, location_id) -> SearchResult`
  - `make_discovery_deltas(...) -> list[StateDelta]`

### Impact Files

- `backend/app/llm/schemas.py`
- `backend/app/llm/prompts.py`
- `backend/app/engine/actions/basic.py` or `actions/search.py`
- `backend/app/engine/action_dispatcher.py`
- `backend/app/engine/rules/search.py`
- `backend/tests/test_search.py`
- `worlds/mist_valley/*`

### Test Requirements

- Searching current location can reveal hidden discoverable object.
- Searching can add discoverable fact to `player_visible_facts`.
- Searching unrelated location reveals nothing.
- Hidden facts do not appear before discovery.
- Search consumes time.
- Search result is recorded as an event through `GameLoop`.

### Acceptance Standard

Players can discover at least one hidden object or fact in `mist_valley` using `search`, and it appears afterward in structured visible state.

### Not In v0.3

- Probabilistic perception systems unless a seeded RNG is already passed through the action handler.
- LLM-generated discoveries.

## Module 4: lockpick Action

### Goal

Add a deterministic lockpicking action for locked objects/doors using inventory and rule checks.

### Data Structures

Add minimal lock fields:

- `WorldObjectState.locked: bool`
- `WorldObjectState.lock_difficulty: int | None`
- `WorldObjectState.unlocks_to: str | None`
- `PlayerState.skills: dict[str, int]` or a simple default lockpick score

If this is too broad, use object-level fixed difficulty and seeded RNG only.

### Interfaces

- `PlayerActionType.LOCKPICK`
- `LockpickActionHandler`
- `backend/app/engine/rules/lockpick.py`
  - `can_lockpick(state, actor_id, target_id) -> RuleResult`
  - `resolve_lockpick(state, intent, rng) -> ActionResult`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/llm/schemas.py`
- `backend/app/llm/prompts.py`
- `backend/app/engine/action_dispatcher.py`
- `backend/app/engine/actions/lockpick.py`
- `backend/app/engine/rules/lockpick.py`
- `backend/tests/test_lockpick.py`

### Test Requirements

- Cannot lockpick missing target.
- Cannot lockpick target not visible/reachable.
- Cannot lockpick target that is not locked.
- Success unlocks target through `StateDelta`.
- Failure does not unlock target.
- Attempt consumes time and creates an event.

### Acceptance Standard

At least one locked object in `mist_valley` can be unlocked through deterministic lockpick rules.

### Not In v0.3

- Detailed lock mini-games.
- Item durability for lockpicks.
- Complex skill progression.

## Module 5: sneak Action

### Goal

Add stealth movement/action state that NPCs can notice through deterministic rules.

### Data Structures

Potential additions:

- `PlayerState.stealth: int = 0`
- `flags["player_sneaking"]`
- `NPCState.suspicion`
- optional `LocationState.visibility_level`

### Interfaces

- `PlayerActionType.SNEAK`
- `SneakActionHandler`
- `backend/app/engine/rules/stealth.py`
  - `can_sneak(state, actor_id, location_id) -> RuleResult`
  - `resolve_detection(state, actor_id, observers, rng) -> list[StateDelta]`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/llm/schemas.py`
- `backend/app/engine/actions/sneak.py`
- `backend/app/engine/rules/stealth.py`
- `backend/app/engine/action_dispatcher.py`
- `backend/tests/test_sneak.py`

### Test Requirements

- Sneak sets structured stealth/sneaking state through `StateDelta`.
- Nearby NPC suspicion can increase on detection.
- No NPC outside location detects the player.
- Sneak consumes time.
- Sneak result does not reveal NPC secrets.

### Acceptance Standard

Sneak can affect player state and NPC suspicion while staying fully deterministic and event-recorded.

### Not In v0.3

- Combat integration.
- Complex lighting/noise simulation.
- LLM-driven detection decisions.

## Module 6: NPC Schedule Resolver

### Goal

Let NPCs move or change state based on time and structured schedules.

### Data Structures

Content-pack addition:

- `schedules.yaml` or NPC schedule field
  - `npc_id`
  - `entries`
    - `day_pattern`
    - `start_minute`
    - `end_minute`
    - `location_id`
    - `activity`

Runtime additions:

- `NPCState.current_activity: str | None`

### Interfaces

- `backend/app/engine/rules/schedule.py`
  - `resolve_npc_schedule(state, npc_id) -> list[StateDelta]`
  - `resolve_all_schedules(state) -> list[StateDelta]`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/rules/schedule.py`
- `backend/tests/test_schedule.py`
- `worlds/mist_valley/schedules.yaml`

### Test Requirements

- NPC moves to scheduled location at the right time.
- NPC does not move outside schedule window.
- Schedule target location must exist.
- Schedule deltas are idempotent when NPC already matches schedule.
- Schedule changes do not leak hidden facts.

### Acceptance Standard

At least one `mist_valley` NPC changes location/activity based on game time.

### Not In v0.3

- Pathfinding.
- Calendar exceptions and holidays.
- LLM-generated schedules.

## Module 7: NPC Autonomous Event Tick

### Goal

Add a world tick after player actions so NPC schedules or simple autonomous rules can emit events and deltas.

### Data Structures

Use existing:

- `Event`
- `StateDelta`
- `GameState`

Optional:

- `Event.actor_id = npc_id | system`
- `action_type = npc_tick | schedule_update | autonomous_action`

### Interfaces

- `backend/app/core/world_tick.py`
  - `run_world_tick(state, rng) -> WorldTickResult`
- `WorldTickResult`
  - `state_deltas: list[StateDelta]`
  - `events: list[EventDraft]`
  - `visible_facts: list[str]`

Game loop extension:

1. Player action resolves.
2. Player deltas apply.
3. Turn advances.
4. NPC/world tick runs.
5. Tick deltas apply.
6. Tick events append.
7. Narrator receives only player-visible tick facts.

### Impact Files

- `backend/app/core/game_loop.py`
- `backend/app/core/event_log.py`
- `backend/app/core/world_tick.py`
- `backend/app/engine/rules/schedule.py`
- `backend/tests/test_world_tick.py`
- `backend/tests/test_game_loop.py`

### Test Requirements

- Tick emits events for autonomous changes.
- Tick deltas apply through `apply_delta`.
- Tick does not run on clarification or unknown intent.
- Tick does not expose hidden facts.
- Event order remains stable and replayable.

### Acceptance Standard

After a qualifying player action, at least one NPC/system event can be generated deterministically and persisted in EventLog.

### Not In v0.3

- Complex AI planning.
- NPCs calling the LLM to decide actions.
- Background async simulation.

## Module 8: Debug Timeline Viewer

### Goal

Expose and display a debug timeline of events, deltas, turns, and save/load activity for local development.

### Data Structures

API response:

- `TimelineEventResponse`
  - `event_id`
  - `turn`
  - `actor_id`
  - `action_type`
  - `result`
  - `visible_to_player`
  - `state_deltas`
  - `created_at`

Debug-only field filtering must still avoid secrets in normal player API. Timeline may show technical deltas but should not include raw hidden narrative text unless explicitly marked debug.

### Interfaces

- `GET /game/{session_id}/timeline`
- optional query:
  - `since_turn`
  - `limit`

Frontend:

- Add collapsible debug timeline panel.
- Show event order, actor, action, result, and delta paths.

### Impact Files

- `backend/app/api.py`
- `backend/app/main.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `backend/tests/test_game_api.py`

### Test Requirements

- Timeline returns session events in order.
- Unknown session returns 404.
- Limit works.
- Timeline does not appear in normal `visible_state`.
- Timeline does not expose narrator hidden facts.

### Acceptance Standard

Developer can inspect event history from the frontend debug panel after several actions.

### Not In v0.3

- Full replay UI.
- Branching timeline editor.
- Save diff viewer.

## Module 9: v0.3 Integration Tests and Acceptance Report

### Goal

Prove the v0.3 systems work together without weakening the core boundaries.

### Integration Scenarios

1. Search discovers a hidden object/fact.
2. Inventory action takes discovered item.
3. Lockpick uses deterministic rules and updates locked state.
4. Sneak changes player/NPC suspicion state.
5. Time advances and NPC schedule resolver moves NPC.
6. Autonomous tick records NPC/system event.
7. Quest state updates after structured trigger.
8. Save/load preserves quests, inventory, NPC state, schedule state, and events.
9. Debug timeline shows player and autonomous events.
10. `visible_state` still excludes hidden facts, hidden objects, and secrets.

### Test Requirements

- Add focused unit tests per module.
- Add one or more full API integration tests.
- Keep tests deterministic with seeded RNG or no RNG.
- Do not call real LLM APIs.
- Ensure `python -m pytest` passes.
- Ensure frontend build passes.

### Acceptance Report

Create:

- `docs/V0_3_ACCEPTANCE_REPORT.md`

It must include:

- Verification commands and results.
- Scope accepted.
- Boundary review.
- Known limitations.
- Recommended v0.4 priorities.

## Features Explicitly Not In v0.3

- Combat system.
- Economy/shop system.
- Crafting.
- Pathfinding.
- Complex NPC AI planning.
- LLM-driven NPC autonomous decisions.
- Multiplayer/accounts/cloud sync.
- World editor UI.
- Vector database memory.
- Full replay/branching timeline editor.
- Complex quest scripting language.
- Frontend visual polish beyond debug usability.

## Final v0.3 Acceptance Standards

v0.3 is accepted only if all of the following are true:

1. `python -m pytest` passes.
2. Frontend build passes.
3. All new state changes use `StateDelta`.
4. All player actions create `Event`.
5. Autonomous NPC/system changes create `Event`.
6. Save/load preserves v0.3 state: inventory, quests, NPC schedule/activity, discovered facts/objects, and event history.
7. `visible_state` contains only player-visible facts, objects, NPC summaries, inventory, quests, location, and time.
8. Narrator prompt does not receive `hidden_facts`, NPC secrets, or undiscovered facts.
9. NPC dialogue/action context does not include facts outside NPC knowledge.
10. Business code continues to depend on `LLMProvider` abstraction.
11. No real LLM API calls happen in automated tests.
12. `docs/V0_3_ACCEPTANCE_REPORT.md` is generated and matches the implemented behavior.
