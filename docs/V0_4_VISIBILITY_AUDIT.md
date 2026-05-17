# v0.4 Visibility, Secrecy, and Debug Data Audit

## Verdict

v0.4 visibility boundary is acceptable for v0.4 acceptance, with medium-risk hardening items.

No high-risk player-facing leak was found in the reviewed code paths. The main player API continues to use `visible_state`, while debug APIs are separate and controlled by `ENABLE_DEBUG_API`.

## Verification Date

2026-05-17

## Review Scope

Reviewed:

- `backend/app/session_store.py`
- `backend/app/main.py`
- `backend/app/api.py`
- `backend/app/core/game_loop.py`
- `backend/app/core/world_state.py`
- `backend/app/engine/actions/*`
- `backend/app/engine/rules/visibility.py`
- `backend/app/engine/rules/knowledge.py`
- `backend/app/engine/rules/rumors.py`
- `backend/app/engine/rules/crime.py`
- `backend/app/engine/rules/factions.py`
- `backend/app/engine/rules/combat.py`
- `backend/app/engine/rules/social_tick.py`
- `backend/app/engine/rules/npc_reactions.py`
- `backend/app/llm/narrator.py`
- `backend/app/llm/memory_store.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- related tests

Search focus:

- hidden facts
- hidden objects
- discoverable facts
- NPC secrets
- hidden NPCs
- hidden witnesses
- visible state
- narrator prompt input
- raw `state_deltas`
- debug APIs
- frontend debug panel

Latest full backend verification available before this audit:

```powershell
python -m pytest
```

Result:

```text
255 passed
```

## Passed Items

### 1. Hidden Facts Do Not Enter `visible_state`

Passed.

`build_visible_state` only includes facts from:

```python
state.player_visible_facts
```

`WorldLoader` only seeds public facts into `player_visible_facts`.

Tests cover:

- hidden facts do not enter initial visible state
- hidden fact ids/text are absent from game API responses
- hidden social data is absent from visible state

### 2. Hidden Objects Are Invisible Until Discovered

Passed.

Object filtering in `build_visible_state` requires:

- object is in current location
- object is `visible`
- object is not hidden, or player id is in `discovered_by`

`visibility.get_visible_facts` uses equivalent logic for action/narrator-visible fact ids.

Tests cover:

- hidden item cannot be picked up before discovery
- hidden object is not visible by default
- discovered hidden object becomes visible
- search can reveal discoverable objects through `StateDelta`

### 3. Discoverable Facts Enter `known_facts` Only After Discovery

Passed.

Discoverable facts are not automatically player-visible. Search and other rule paths add them through `StateDelta` to `player_visible_facts`.

Tests cover:

- discoverable fact enters `known_facts` after successful search
- search failure does not reveal hidden fact
- `facts.yaml` hidden/discoverable/public behavior

### 4. NPC Secrets Are Hidden From Player Context By Default

Passed.

Dialogue context is built by `get_npc_context_for_dialogue`.

Facts are allowed only when:

- already in `player_visible_facts`
- marked public
- not present as an NPC secret for unknown custom fact ids

Tests cover:

- secrets are hidden by default
- hidden fact in knowledge does not enter dialogue context
- talk does not leak hidden facts

### 5. Hidden NPCs Do Not Enter `visible_npcs`

Passed.

NPC filtering in `build_visible_state` requires:

- same location as player
- `visible=True`
- not hidden, or player id in `discovered_by`

Tests cover schedule, sneak, world tick, crime, combat, and integration cases where hidden NPCs do not appear in `visible_state`.

### 6. Hidden NPC Witness Behavior Does Not Directly Enter Narrator

Passed.

Hidden NPCs may affect deterministic rules as observers, but `Narrator` is not given raw witness records or debug `state_deltas`.

Narrator receives:

- player input
- action result success level
- action result reason
- action result visible facts
- current location id
- tone

It does not receive:

- `witnesses`
- `crimes.*.witness_ids`
- hidden NPC records
- raw debug timeline

Tests include hidden witness / hidden NPC cases for crime, combat, social tick, and v0.4 integration.

### 7. Hidden Witnesses Do Not Appear In Player API

Passed.

Player API only includes `known_crimes`, and `VisibleCrimeResponse` contains:

- `id`
- `crime_type`
- `location_id`
- `severity`
- `status`
- `created_turn`

It does not include:

- `witness_ids`
- `witnessed_by`
- `WitnessRecord`
- `reported_to`

Hidden witnesses are present in debug/event state deltas only.

### 8. Rumors Do Not Automatically Reveal Hidden Fact Text

Passed with a medium-risk authoring caveat.

`get_visible_rumors` only returns rumors where `known_by_player=True`.

`_safe_rumor_text` returns:

1. `rumor.text_for_player` if provided
2. fact text only if the linked fact is already in `player_visible_facts`
3. otherwise a vague fallback

Tests cover hidden fact text fallback behavior.

Content validation warns when a player-known rumor appears to include the full hidden fact text.

### 9. Crime Records Expose Only Player-Known/Public Subset

Passed.

`get_player_known_crimes` returns crimes only when:

- `known_to_player=True`
- status is `reported`
- status is `resolved`

The player-visible crime response omits witness and report internals.

### 10. Hidden Faction State Is Filtered

Passed with a medium-risk data-shape caveat.

`get_visible_factions` returns only factions where reputation state is known to player.

Tests confirm hidden faction id/name do not enter visible state.

Medium caveat: `VisibleFactionResponse` currently includes raw `reputation` value in addition to `band`. The current frontend displays only `name` and `band`, but the player API still exposes the raw number.

### 11. Combat Does Not Expose Hidden Observers Or Hidden Enemies

Passed.

Combat target validation rejects hidden targets unless discovered. Hidden observers can generate witness/crime consequences, but visible state excludes hidden witness ids.

Tests cover:

- cannot attack invisible hidden target
- hidden witness after combat crime does not enter visible state
- v0.4 integration excludes hidden witness from visible payload

### 12. Advanced Memory Retrieval Filters Hidden/Debug-Only Memory

Passed.

`MemoryRecord.visibility` supports:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

`filter_narrator_safe_memories` allows only:

- `player_visible`
- `narrator_safe`

`filter_player_visible_memories` allows only:

- `player_visible`

Tests cover hidden/debug memory exclusion from narrator/player context.

### 13. Debug API Is Separate From Player API

Passed.

Debug endpoints:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They are separate from `/game/*` endpoints and require `ENABLE_DEBUG_API`.

Tests cover:

- debug enabled reads events
- debug disabled returns forbidden
- debug response does not include API key
- event order is stable

### 14. Frontend Keeps Debug Data In Debug Panel

Passed.

Frontend player-visible area uses `visible_state` for:

- location
- time
- inventory
- quests
- known factions
- known rumors
- known crimes
- visible status

Raw debug timeline and `state_deltas` are rendered only inside:

- `debug-panel`
- `timeline`
- `debug-group`

No code path copies debug event text into story entries.

### 15. Narrator Cannot See Raw `state_deltas`

Passed.

`GameLoop` does not pass event log, debug timeline, or raw `state_deltas` to `Narrator`.

`Narrator` also explicitly removes `ActionResult.hidden_facts` from the safe action payload.

Tests cover hidden facts not being sent to provider.

## Possible Leak Paths

### ActionResult Reason To Narrator

`Narrator` receives `ActionResult.reason`. Current reasons appear player-safe, but this field is not structurally separated from debug reasons.

Potential leak:

- a future rule adds hidden witness id or hidden motive to `reason`
- that reason enters narrator prompt

### Player API Raw Reputation Value

`VisibleFactionResponse` exposes:

```python
reputation: int
band: str
```

Frontend displays only band, but API clients can see raw numeric reputation.

Potential leak:

- raw numbers may be considered internal mechanical state
- future hidden social math may be inferable if raw values are exposed

### Rumor `text_for_player` Is Trusted

`_safe_rumor_text` returns `rumor.text_for_player` if provided. This is intended as authored safe text, but it depends on author discipline.

Potential leak:

- content author writes hidden fact text directly into `text_for_player`
- rumor becomes known by player and exposes it

Mitigation exists:

- content validator warns on exact hidden fact text inclusion

Residual risk:

- paraphrased hidden facts are not reliably detected by deterministic validation

### Memory Summary Classification

`MemorySummarizer` can summarize events containing raw `state_deltas`. If a caller stores that summary as `narrator_safe`, hidden/debug information could become retrievable for future narrator context.

Potential leak:

- hidden witness id or hidden fact appears in generated memory
- memory is stored as `narrator_safe`

Current state:

- retrieval filters are correct
- classification responsibility remains with caller

### Debug Panel Default Open

Frontend `debugOpen` defaults to `true`.

This is acceptable for local development, but it means raw event deltas are visible immediately when debug API is enabled.

Potential issue:

- user-facing playtesting on the same local app may see debug internals by default

## High-Risk Leaks

None found.

## Medium-Risk Leaks

1. `ActionResult.reason` is passed to Narrator and is not structurally separated from debug/internal reasons.
2. `VisibleFactionResponse` includes raw `reputation` numeric value in player API.
3. Rumor safety relies on authored `text_for_player`; deterministic validation only catches exact full hidden fact text.
4. Memory summaries from raw events need explicit hidden/debug/narrator-safe classification.

## Low-Risk Issues

1. Debug panel defaults open in the frontend.
2. Frontend `Debug Snapshot` includes `lastResponse`; currently this is player API data plus saves, but it should stay debug-only.
3. Narrator prompt text appears mojibake/corrupted in `prompts.py`, which may reduce clarity of visibility instructions to a live model.
4. `visible_state.known_crimes` includes `location_id` and `severity`; this is probably acceptable for reported/known crimes, but may be too detailed for some narrative designs.

## Fix Recommendations

Recommended before v0.4 final acceptance if time allows:

1. Split action result reason fields:
   - `player_reason`
   - `debug_reason`
   Pass only `player_reason` to Narrator.
2. Remove or gate raw numeric faction reputation from player API:
   - keep `band`
   - optionally expose raw value only in debug API
3. Add stronger tests for rumor authoring:
   - hidden fact paraphrase cannot be automatically detected, so require `text_for_player` for hidden-linked rumors to pass an explicit `safe_for_player: true` or similar author flag.
4. Add memory visibility classification helper:
   - memories derived from non-player-visible events default to `debug_only` or `hidden`
5. Set frontend debug panel default to closed for safer local playtesting.
6. Rewrite narrator prompt text in clean UTF-8 and keep explicit visibility rules.
7. Add regression tests proving:
   - narrator prompt excludes hidden witness ids after crime/combat
   - player API does not include witness ids
   - player API does not include raw faction reputation if that becomes policy

## Acceptance Blocking Status

Not blocking v0.4.

Current v0.4 implementation preserves the key visibility boundary:

- hidden facts do not enter `visible_state`
- hidden objects/NPCs stay hidden until discovered
- NPC secrets are filtered from dialogue context
- hidden witnesses are debug/system state only
- player crime view omits witness internals
- debug state deltas are isolated behind debug endpoints and frontend debug panel
- narrator does not receive raw `state_deltas`
- memory retrieval has explicit narrator/player safety filters

The medium risks are important hardening work, especially before making memory retrieval an active narrator input or expanding public/social API detail.
