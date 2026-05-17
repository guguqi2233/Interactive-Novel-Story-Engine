# v0.5 Visibility, Memory, and Debug Data Audit

## Audit Date

2026-05-17

## Scope

This audit reviews player-facing visibility, memory filtering, debug-data separation, authoring isolation, and mod-validation output for v0.5.

Reviewed areas:

- `build_visible_state` and player API responses.
- Visibility rules for facts, objects, NPCs, witnesses, crimes, rumors, relationships, faction conflicts, and trade inventory.
- `MemoryContextBuilder` and memory visibility flags.
- Procedural side quest draft validation.
- Debug API and frontend debug panel separation.
- Authoring UI separation from play UI.
- Mod validation path and configuration exposure.

## Verification Commands

- `Get-Content backend/app/session_store.py`
- `Get-Content backend/app/engine/rules/visibility.py`
- `Get-Content backend/app/engine/rules/rumors.py`
- `Get-Content backend/app/engine/rules/crime.py`
- `Get-Content backend/app/engine/rules/relationships.py`
- `Get-Content backend/app/engine/rules/faction_conflict.py`
- `Get-Content backend/app/engine/rules/economy.py`
- `Get-Content backend/app/llm/context_builder.py`
- `Get-Content backend/app/engine/content/side_quest_generator.py`
- `Get-Content backend/app/engine/content/mod_loader.py`
- `Get-Content backend/app/main.py`
- `Get-Content frontend/src/App.tsx`

Full tests were not rerun during this audit document creation. The immediately preceding v0.5 integration task reported `python -m pytest` as `357 passed` and frontend build as passed.

## Passed Items

1. Hidden facts do not enter `visible_state`.

   `build_visible_state` serializes `known_facts` only from `state.player_visible_facts`. Hidden facts remain in `state.facts` but are not exposed unless deliberately added to `player_visible_facts` by a rule.

2. Hidden objects are not visible before discovery.

   `_object_visible_to_player` requires:

   - object location equals current player location;
   - `visible=True`;
   - either `hidden=False` or `player.id in discovered_by`.

3. Discoverable facts only enter `known_facts` after discovery.

   Discoverable facts are not automatically serialized. They must first be added to `player_visible_facts`, normally by rule-driven discovery/search deltas.

4. NPC secrets do not enter player context by default.

   `VisibleNPCResponse` includes id, mood, relationship, and condition. It does not include `NPCState.secrets`, `knowledge`, goals, schedule, faction internals, or plan state.

5. Hidden NPCs do not enter `visible_npcs`.

   `_npc_visible_to_player` requires `visible=True` and either `hidden=False` or the player has discovered the NPC.

6. Hidden witnesses do not enter player API.

   `build_visible_state` does not serialize `witnesses`. `known_crimes` use `get_player_known_crimes`, which returns crime summaries without witness ids.

7. Rumors do not reveal hidden fact text by default.

   `get_visible_rumors` returns only `known_by_player` rumors. `_safe_rumor_text` uses `text_for_player` when present; otherwise it only uses fact text if the fact id is in `player_visible_facts`. If not, it returns a vague fallback.

8. Crime records are filtered.

   `get_player_known_crimes` exposes only crimes with `known_to_player=True` or status `reported/resolved`. Player-facing crime summaries omit witness ids and raw witness records.

9. Hidden relationships are filtered.

   `get_visible_relationships` returns only relationships with `known_by_player=True`.

10. Economy/trade hides hidden shop inventory.

   `get_shop_inventory` filters items to `visible`, `not hidden`, and `tradeable`. `can_buy` also rejects hidden items.

11. `MemoryContextBuilder` filters hidden/debug memory.

   Narrator context excludes `MemoryVisibility.HIDDEN`, `MemoryVisibility.DEBUG_ONLY`, hidden/discoverable facts not known to the player, and `source_event_hidden` memories.

12. NPC memory context respects knowledge.

   `MemoryContextBuilder` checks `npc_knows` for fact-linked NPC memory. NPCs do not receive memory tied to facts they do not know.

13. Procedural quest draft validation rejects hidden fact text leaks.

   `validate_quest_draft` scans player-facing draft title, premise, and stage text for hidden fact text. Hidden fact id references are warnings, not automatic player-facing leaks.

14. Authoring UI is separated from player UI.

   The frontend has explicit `mode: "play" | "authoring"`. Authoring surfaces are shown in the story panel only when authoring mode is selected. Player play UI uses `visible_state`, not authoring file content.

15. Debug API is separated from player API.

   Debug endpoints are separate paths:

   - `/debug/sessions/{session_id}/events`
   - `/debug/saves/{save_id}/events`

   They require `ENABLE_DEBUG_API`. Player APIs do not return raw `state_deltas`.

16. Frontend debug panel is separate from the main narrative area.

   Debug timeline, raw `state_deltas`, social debug event summaries, and raw reputation deltas are rendered only inside the debug panel. The main story panel displays `narrative_text`, suggested actions, and player-visible state panels.

17. Narrator cannot see raw `state_deltas`.

   `Narrator.render` constructs `safe_action_result` from success level, reason, and visible facts only. It does not include `state_deltas`, hidden facts, raw events, debug timelines, or witness records.

18. Save browser summaries are player-safe.

   Save summaries include world id/name, turn, location name, formatted time, timestamps, and player summary. They do not include raw `GameState`, facts, witnesses, memory, or `state_deltas`.

19. Mod validation rejects executable code and path traversal.

   `ModLoader` rejects absolute paths, `..` path traversal, and executable-code-like file suffixes. Validation reuses world validation.

## Possible Leak Paths

1. Faction conflict tags can expose thematic hidden information.

   `get_visible_faction_conflicts` filters target faction relations to known factions, but it returns `conflict_tags` from the visible faction unchanged. In `mist_valley`, the visible `village_council` faction has a tag like `law_vs_smuggling`, which may hint at hidden smuggler content even if the hidden faction id is filtered.

2. Mod manifest errors may include local filesystem paths.

   `ModLoader._read_manifest` raises `ModLoaderError(f"Invalid mod manifest {path}: {exc}")`. If surfaced through authoring APIs, invalid mod manifest errors can include an absolute or local mod path. This is not a player API leak, but it is a local path disclosure in authoring/debug surfaces.

3. Authoring UI intentionally displays hidden world content.

   This is expected for a local authoring tool, but it means authoring mode must remain gated and clearly separated from player mode.

4. Debug panel intentionally displays raw `state_deltas`.

   This is expected for local debugging. The current separation is UI-based plus backend debug route gating. It must not be used as player narrative input.

5. Memory summarization may ingest raw event details.

   This is not directly player-facing, but summaries derived from hidden/debug events must be classified as hidden/debug unless explicitly safe. `MemoryContextBuilder` currently provides the narrator/player filter.

## High Risk Leaks

None found.

No reviewed player API path returns hidden facts, NPC secrets, hidden witnesses, raw debug memory, or raw `state_deltas`.

## Medium Risk Leaks

1. Faction conflict `conflict_tags` can hint at hidden factions or hidden social structure.

   Severity: Medium.

   Current implementation filters hidden faction ids in `relationships_to_other_factions`, but leaves `conflict_tags` unchanged. Tags are low-structure but player-visible through `visible_state.faction_conflicts`.

   Impact: A player may infer hidden social content from a known faction's tags.

2. Mod manifest validation errors can expose local paths in authoring API responses.

   Severity: Medium.

   Current invalid manifest error includes the manifest `Path`. Authoring APIs are local/gated, but the audit target includes avoiding local sensitive path/config exposure. This should be sanitized before v0.5 freeze if security audit treats local path disclosure as blocking.

## Low Risk Issues

1. Authoring mode and debug panel are frontend-separated, but not visually impossible to confuse.

   The UI uses different mode and panel areas. A stronger visual local-only/debug-only label would reduce operator mistakes.

2. `MemoryContextBuilder` exists but is not yet fully wired into the runtime `GameLoop`.

   This currently reduces leak risk because memory is not passed to Narrator. When runtime memory is integrated, all paths must use `MemoryContextBuilder`.

3. Authoring validation reports can show hidden content ids.

   This is acceptable in authoring mode, but it must remain authoring-only and should not be linked into player play mode.

4. Debug event `visible_to_player` is not a redaction mechanism.

   Debug endpoints return raw debug event contents when enabled. This is acceptable for local debug, but player APIs must continue not to consume debug responses.

## Fix Recommendations

1. Sanitize `visible_state.faction_conflicts.conflict_tags`.

   Recommended options:

   - return only tags explicitly marked player-safe;
   - omit conflict tags from player API and keep them debug-only;
   - map internal tags to authored player-safe labels.

2. Sanitize mod loader manifest errors.

   Replace absolute/local path text in API-facing `ModLoaderError` messages with file names or relative mod ids, for example `Invalid mod manifest mod.yaml`.

3. Add regression tests for faction conflict tag visibility.

   Test that hidden faction ids and hidden-theme tags do not appear in `visible_state` unless explicitly player-known.

4. Add regression tests for mod loader error sanitization.

   Test invalid manifest responses do not include temp directory paths, database paths, `.env`, or full local roots.

5. Keep authoring and debug APIs gated.

   Authoring and debug surfaces are allowed to display hidden content for local development, but they must stay separate from player APIs and player narrative.

6. When integrating memory into runtime narration, pass only:

   - `MemoryContextBuilder.narrator_safe_memories`;
   - no `hidden`, `debug_only`, or source-hidden memories;
   - no raw event log or raw `state_deltas`.

## Blocking Assessment

No high-risk visibility or memory leak was found.

The audit does not block v0.5 acceptance, provided the medium risks are accepted as local-authoring/debug risks or addressed before freeze. The most important pre-freeze hardening recommendation is sanitizing mod manifest path errors and filtering or remapping player-visible faction conflict tags.

## Final Verdict

v0.5 visibility, memory, and debug-data boundaries are broadly intact.

Player APIs continue to expose structured `visible_state` only, debug data remains on debug endpoints/panels, hidden/debug memory is filtered by `MemoryContextBuilder`, and procedural quest drafts are validated against hidden text leaks. The remaining risks are medium or lower and mostly concern player-safe labeling of faction conflict tags and local path exposure in authoring/mod validation errors.
