# v0.3 Visibility Audit

Date: 2026-05-17

Scope:

- Player-facing API: `/game/start`, `/game/input`, `/game/state/{session_id}`, save/load responses.
- Debug API and frontend debug panel.
- v0.3 systems: search, inventory, lockpick, sneak, quest state, NPC schedule, world tick.
- Narrator inputs and NPC dialogue context.

## Summary

v0.3 preserves the intended visibility boundary for normal player-facing flows. Hidden facts, hidden objects, hidden NPCs, and NPC secrets are not included in `visible_state`, and Narrator receives `ActionResult.visible_facts` rather than `hidden_facts` or raw system events.

No blocker was found for v0.3 acceptance. The main risk is intentional: debug timeline endpoints and the frontend debug panel can expose raw `state_deltas`, including hidden/system-only information. This is acceptable for local development, but it must remain clearly separated from player-facing UI/API.

## Passed Items

1. Hidden facts do not enter `visible_state`.

   `build_visible_state` constructs `known_facts` only from `state.player_visible_facts`. Content-pack hidden facts are loaded into `GameState.facts`, but are not added to `player_visible_facts`.

   Covered by tests:

   - `test_hidden_fact_does_not_enter_player_visible_facts`
   - `test_visible_state_exposes_only_visible_objects_npcs_and_known_facts`
   - `test_save_load_api_does_not_leak_hidden_facts`
   - `test_v03_full_system_regression_flow`

2. Hidden objects are invisible until discovered.

   Player-visible object filtering checks:

   - same location
   - `visible == true`
   - not hidden, or player is in `discovered_by`

   Search, inventory, lockpick, and sneak also check hidden/discovered state before allowing targeted interaction.

3. Discoverable facts enter `known_facts` only after discovery.

   `SearchActionHandler` only adds facts to `player_visible_facts` when:

   - `fact.visibility == discoverable`
   - fact scope matches the searched location/object/NPC
   - search produces discovery deltas

   `visible_state.known_facts` then derives from `player_visible_facts`.

4. NPC secrets are hidden by default.

   `get_npc_context_for_dialogue` filters NPC knowledge through `_fact_allowed_for_dialogue`. Secrets and hidden facts do not enter dialogue context unless already player-visible/public.

   Covered by:

   - `test_secrets_are_hidden_by_default`
   - `test_talk_does_not_leak_hidden_facts`
   - v0.3 integration regression narrator checks

5. Hidden NPCs do not appear in `visible_npcs`.

   `build_visible_state` includes NPCs only when:

   - same location
   - `visible == true`
   - not hidden, or player is in `discovered_by`

   Covered by schedule, sneak, world tick, and integration tests.

6. Hidden NPC actions do not enter Narrator directly.

   `GameLoop` runs `world_tick` before narration, but Narrator receives only the player action result:

   - `player_input`
   - `action_result`
   - `action_result.visible_facts`
   - current location
   - tone

   System tick events and raw tick deltas are appended to `EventLog`, not sent to Narrator.

7. Debug API is separated from player API.

   Debug endpoints are separate:

   - `GET /debug/sessions/{session_id}/events`
   - `GET /debug/saves/{save_id}/events`

   They are gated by `ENABLE_DEBUG_API` and return `403` when disabled. Normal player APIs return `visible_state`, not raw events.

8. Frontend debug information stays in the debug panel.

   Timeline rendering is inside `<aside className="debug-panel">`. The story panel renders only narrative text and suggested actions. Debug timeline state is not mixed into the main fiction output.

9. Search reveals discoverable information only through success.

   Search returns discovery deltas only when matching hidden/discoverable objects or discoverable facts are in scope. Failure returns existing visible facts only and does not reveal hidden facts.

10. Sneak does not reveal unseen observer identity to Narrator.

   Sneak may use hidden NPCs as observers for rule difficulty and suspicion deltas. Player-facing `visible_facts` are generic, such as `suspicion:raised` or `sneak_failed`, not hidden NPC IDs.

11. Lockpick does not reveal unknown hidden targets.

   Lockpick rejects missing, invisible, hidden-undiscovered, or inaccessible targets. Lockpick-created visible facts describe the visible target lock; hidden target IDs are not returned to `visible_facts` for invalid hidden targets.

12. Hidden quests do not appear in `visible_state`.

   `get_visible_quests` returns quests only when `known_to_player == true` and status is not `inactive`. Hidden inactive quests are excluded from `visible_state.quests`.

## Possible Leak Paths

1. Debug timeline exposes raw `state_deltas`.

   Debug events can contain NPC IDs, hidden object IDs, quest activation deltas, and delayed consequence deltas. This is intentional for local debugging but would be a leak if exposed as player-facing UI.

2. Debug panel defaults open in the frontend.

   The panel is visually separate from story text, but `debugOpen` currently defaults to `true`. In local development this is useful; for a non-debug build it would make hidden/debug information more prominent.

3. `ActionResult.reason` is sent to Narrator.

   Current v0.3 reason strings are rule-generated and do not appear to contain hidden fact text or hidden NPC identity. Future rules could accidentally include secret causal details in `reason`, which would reach the Narrator prompt.

4. `MemorySummarizer` receives full event payloads.

   This is outside player-visible API and does not mutate `GameState`, but event payloads include `state_deltas`. If memory summaries are later displayed to the player, they must be filtered.

5. Hidden quest activation can reveal quest title/description once a trigger fires.

   This is expected behavior for `known_to_player=True`, but content authors should avoid putting unrevealed hidden facts directly in quest titles/descriptions that become visible through broad triggers like item acquisition.

## Fix Recommendations

1. Keep debug timeline local-only.

   Maintain `ENABLE_DEBUG_API` gating. If the project is ever run outside trusted local development, default `ENABLE_DEBUG_API=false` and hide the frontend timeline unless enabled.

2. Consider defaulting the frontend debug panel to closed.

   This would reduce accidental exposure during demos while preserving local debug access.

3. Add a helper or convention for narrator-safe action reasons.

   Rule code should keep `ActionResult.reason` player-safe. Hidden diagnostics should stay in `hidden_facts`, event metadata, or debug-only logs.

4. Add a regression test for hidden observer identity in sneak narrator input.

   Current integration tests cover this broadly; a focused unit test would make the guarantee more obvious.

5. Add content authoring guidance for hidden quests.

   Hidden quest `title`, `description`, and stage text should be written as player-visible once activated; unrevealed secrets should remain facts with visibility rules.

6. Before exposing memory summaries, filter them through player-visible facts.

   Memory summaries are currently internal. Any future player-facing memory UI should not display facts that are absent from `player_visible_facts`.

## v0.3 Blocking Status

Does this block v0.3?

No.

Rationale:

- Normal player APIs use `build_visible_state`, which filters hidden facts, hidden objects, hidden NPCs, NPC secrets, and hidden inactive quests.
- Narrator does not receive raw system tick events, debug timeline events, or `ActionResult.hidden_facts`.
- v0.3 action/rule systems use deterministic visibility checks before revealing discoverable information.
- Debug exposure is isolated to explicit debug endpoints and frontend debug panel.

The identified risks are acceptable for a local development release, provided debug surfaces remain local-only.

