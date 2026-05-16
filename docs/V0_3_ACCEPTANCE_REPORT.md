# v0.3 Acceptance Report

## Verdict

Accepted for v0.3.

v0.3 meets the stated goal of upgrading the project from a persistent interactive novel engine into a deterministic local world with NPC schedules, advanced actions, quest state, autonomous system tick, debug timeline, and integration regression coverage.

No release-blocking issue remains after fixing stable SQLite event ordering with per-save event `sequence`.

## Verification Date

2026-05-17

## Verification Commands

```powershell
python -m pytest
```

Result:

```text
157 passed
```

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
tsc -b && vite build
built successfully
```

## Scope Accepted

### NPC Schedule

Accepted.

- Schedule entries are loaded from content-pack NPC definitions.
- NPCs can change `location_id` and `current_activity` based on `time_of_day`.
- Schedule changes are emitted as `StateDelta`.
- Schedule changes run through world tick and are recorded as `system` `Event` entries with `action_type="world_tick"`.
- Hidden NPCs are filtered from `visible_state.visible_npcs`.

Primary coverage:

- `backend/tests/test_schedule.py`
- `backend/tests/test_world_tick.py`
- `backend/tests/test_v03_integration_regression.py`

### Search

Accepted.

- Search can discover discoverable objects and facts in the current location, object scope, or NPC scope.
- Discoveries are represented through `StateDelta`.
- Discoverable facts enter `known_facts` only after being added to `player_visible_facts`.
- Failure consumes time and does not expose hidden facts.
- Search through `GameLoop` records a player `Event`.

Primary coverage:

- `backend/tests/test_search.py`
- `backend/tests/test_v03_integration_regression.py`

### Inventory

Accepted as first-version rules.

- Item ownership is structured through `location_id`, `owner_id`, and `container_id`.
- Pydantic validation prevents multiple simultaneous placements for `WorldObjectState`.
- `pick_up_item` and `drop_item` produce `StateDelta` lists.
- `use_item` checks ownership/accessibility.
- `visible_state.inventory` is derived from authoritative item ownership.
- Hidden items cannot be picked up or used before discovery.

Primary coverage:

- `backend/tests/test_inventory.py`
- `backend/tests/test_v03_integration_regression.py`

Note: pickup/drop are rule functions in v0.3, not full natural-language action handlers.

### Lockpick

Accepted.

- Locked targets are structured with `locked`, `lock_difficulty`, and `lock_state`.
- Success, partial success, failure, and invalid paths are represented.
- Failure/partial outcomes can alter lock state or create visible lock-mark facts.
- Lockpick is deterministic under seeded RNG and does not call LLM.
- Lockpick through `GameLoop` records player events.

Primary coverage:

- `backend/tests/test_lockpick.py`
- `backend/tests/test_v03_integration_regression.py`

### Sneak

Accepted.

- Sneak considers target validity, location connectivity, cover/light, NPC alertness, and NPC suspicion.
- Sneak can move the player or modify NPC suspicion through `StateDelta`.
- Hidden observers may affect rule outcomes but their identities are not included in player-visible facts.
- Sneak records player events through `GameLoop`.

Primary coverage:

- `backend/tests/test_sneak.py`
- `backend/tests/test_v03_integration_regression.py`

### Quest State Machine

Accepted.

- `quests.yaml` is loaded into structured `QuestState`.
- Quest state is persisted as part of `GameState`.
- Triggers can react to fact discovery, item acquisition, NPC talk, and location visits.
- Quest progress is represented by `StateDelta`.
- Hidden inactive quests are excluded from `visible_state.quests`.

Primary coverage:

- `backend/tests/test_quest_rules.py`
- `backend/tests/test_v03_integration_regression.py`

### World Tick

Accepted.

- Tick runs after successful or partially successful player actions, after action/quest/turn changes.
- Tick handles schedule resolution, suspicion decay, delayed consequences, and tick-induced quest triggers.
- Tick changes are deterministic under controlled RNG.
- Tick emits a `system` Event when it produces deltas.
- Tick does not call LLM and does not enter narrator prompts.

Primary coverage:

- `backend/tests/test_world_tick.py`
- `backend/tests/test_schedule.py`
- `backend/tests/test_v03_integration_regression.py`

### Debug Timeline

Accepted for local development.

- Debug endpoints are implemented:
  - `GET /debug/sessions/{session_id}/events`
  - `GET /debug/saves/{save_id}/events`
- Debug API is gated by `ENABLE_DEBUG_API`.
- Timeline returns Event fields and `state_deltas`.
- Debug data is not passed to Narrator.
- Frontend debug panel displays timeline entries with expandable deltas.
- Frontend build passes.

Primary coverage:

- `backend/tests/test_debug_api.py`
- frontend TypeScript/Vite build

### v0.3 Integration Tests

Accepted.

Integration regression validates a combined flow across:

- observe
- search
- inventory pickup rule
- move
- wait
- NPC schedule tick
- lockpick
- sneak
- talk
- quest progression
- save/load
- event replay
- debug timeline
- memory summary non-mutation

Primary coverage:

- `backend/tests/test_v03_integration_regression.py`

## Boundary Review

### LLM Boundary

Accepted.

- v0.3 rule modules do not call LLM providers.
- LLM output does not directly modify `GameState`.
- `IntentParser`, `Narrator`, and `MemorySummarizer` continue to depend on `LLMProvider`.
- Provider selection remains centralized through `create_llm_provider` and `LLM_PROVIDER`.
- Automated tests use fake/mock providers and do not call real OpenAI APIs.

Reference:

- `docs/V0_3_LLM_BOUNDARY_AUDIT.md`

### State and Event Boundary

Accepted.

- Canonical changes flow through `StateDelta`.
- Player actions handled by `GameLoop` record player `Event` entries.
- World tick records system `Event` entries when autonomous changes occur.
- SQLite event storage now preserves event-log order using per-save `sequence`.
- Save/load and replay are covered by regression tests.

### Visibility Boundary

Accepted.

- `visible_state` filters hidden facts, hidden objects, hidden NPCs, NPC secrets, and hidden inactive quests.
- Narrator receives visible facts, not `hidden_facts` or raw system tick/debug deltas.
- Debug timeline is separated from player API and controlled by `ENABLE_DEBUG_API`.

Reference:

- `docs/V0_3_VISIBILITY_AUDIT.md`

## Known Limitations

- Inventory pickup/drop are rule functions, not complete natural-language action handlers.
- No combat system.
- No economy, shop, crafting, equipment, or weight systems.
- No pathfinding.
- No complex NPC planning or LLM-driven autonomous NPC agents.
- No complex quest scripting language or quest editor.
- No vector database memory.
- Debug API is local-development only and has no production authentication.
- Debug timeline intentionally exposes raw `state_deltas`; it must not be treated as player-facing output.
- `ActionResult.reason` is currently sent to Narrator and should remain player-safe by convention.
- Memory summaries receive full event payloads but do not mutate `GameState`; future player-visible memory views will need visibility filtering.

## Acceptance Risks

No blocking risks remain.

Non-blocking risks to track:

1. Debug timeline can expose hidden/system details if enabled outside trusted local development.
2. Future rule code could accidentally put hidden causal information in `ActionResult.reason`.
3. Future memory systems could incorrectly promote summary text into canonical facts.
4. Quest triggers are currently simple and mostly idempotent; more complex quest graphs may require trigger execution tracking.

## Recommended v0.4 Priorities

1. Promote inventory pickup/drop to first-class player action handlers.
2. Add narrator-safe reason conventions or tests.
3. Add trigger execution history for more complex quest graphs.
4. Add player-visible memory view only after applying visibility filters.
5. Decide whether debug panel should default closed in non-development builds.
6. Add content-author documentation for hidden quests, facts, and discoverable objects.
7. Start v0.4 design for either combat/conflict, richer NPC routines, or a quest/content authoring workflow.

## Final Status

v0.3 is accepted.

The implementation satisfies the release goals:

- NPC schedule resolver: accepted.
- Search action: accepted.
- Inventory rules: accepted as first-version rules.
- Lockpick action: accepted.
- Sneak action: accepted.
- Quest state machine: accepted.
- NPC autonomous event tick: accepted.
- Debug timeline viewer: accepted for local development.
- v0.3 integration tests: accepted.

Verification commands passed on 2026-05-17.

