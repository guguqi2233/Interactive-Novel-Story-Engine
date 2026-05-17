# v0.4 LLM Boundary Audit

## Verdict

v0.4 LLM boundary is acceptable for v0.4 acceptance.

No high-risk blocker was found. The new v0.4 systems for faction reputation, rumor propagation, crime/witness, social tick, combat, life state, NPC reactions, content validation, and memory retrieval are deterministic rule-engine paths and do not call the LLM.

## Verification Date

2026-05-17

## Review Scope

Reviewed:

- `backend/app/core/game_loop.py`
- `backend/app/core/event_log.py`
- `backend/app/core/state_delta.py`
- `backend/app/core/world_state.py`
- `backend/app/engine/actions/*`
- `backend/app/engine/rules/*`
- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/content/validator.py`
- `backend/app/llm/*`
- `backend/app/session_store.py`
- `backend/app/main.py`
- v0.4 related tests

Searches performed:

- Provider and LLM call sites:
  - `LLMProvider`
  - `generate_json`
  - `generate_text`
  - `OpenAIProvider`
  - `MockLLMProvider`
  - `FakeLLMProvider`
  - `create_llm_provider`
- Visibility and prompt paths:
  - `hidden_facts`
  - `secrets`
  - `narrator`
  - `visible_facts`
  - `MemoryStore`
  - `filter_narrator`
  - `debug`
  - `state_deltas`
- v0.4 rule modules:
  - `factions`
  - `rumor`
  - `crime`
  - `witness`
  - `social_tick`
  - `combat`
  - `life_state`
  - `npc_reaction`

Latest full backend verification available during this phase:

```powershell
python -m pytest
```

Result before this audit:

```text
255 passed
```

## Passed Items

### v0.4 Rule Modules Do Not Call LLM

Passed.

The following v0.4 modules are deterministic rule paths:

- `backend/app/engine/rules/factions.py`
- `backend/app/engine/rules/rumors.py`
- `backend/app/engine/rules/crime.py`
- `backend/app/engine/rules/social_tick.py`
- `backend/app/engine/rules/combat.py`
- `backend/app/engine/rules/life_state.py`
- `backend/app/engine/rules/npc_reactions.py`
- `backend/app/engine/content/validator.py`

No direct `LLMProvider`, `generate_json`, `generate_text`, `OpenAIProvider`, or provider factory calls were found in these modules.

### Rule Engine Decides v0.4 Outcomes

Passed.

The following outcomes are decided by Python rules:

- faction reputation band and reputation delta
- rumor creation and propagation
- crime classification
- witness detection
- crime reporting
- social consequence tick
- combat hit/miss/damage
- injury, incapacitation, death state
- NPC reaction
- content pack validation
- memory retrieval ranking/filtering

LLM output is not used to decide these outcomes.

### LLM Output Does Not Directly Enter GameState

Passed.

The current LLM outputs are:

- `PlayerIntent` from `IntentParser`
- `NarrativeResult` from `Narrator`
- `MemorySummary` from `MemorySummarizer`

`PlayerIntent` is passed to deterministic handlers. It does not mutate `GameState`.

`NarrativeResult` is returned as prose and suggested actions. It is not applied as `StateDelta`.

`MemorySummary` is a summary object and is not applied to `GameState`.

### Narrator Receives Filtered Player Context

Passed with a minor caution.

`GameLoop` calls:

```python
self.narrator.render(
    player_input=player_input,
    action_result=action_result,
    visible_facts=action_result.visible_facts,
    current_location=next_state.player.location_id,
    tone=tone,
)
```

`Narrator` builds a safe action payload containing:

- `success_level`
- `reason`
- `visible_facts`

It does not pass:

- `ActionResult.hidden_facts`
- raw `GameState`
- raw debug events
- raw system tick `state_deltas`
- NPC secrets

Tests include `test_narrator_does_not_send_hidden_facts_to_provider`.

### Hidden Facts and NPC Secrets Are Not Normal Player API Output

Passed.

`build_visible_state` uses:

- `state.player_visible_facts`
- visible object rules
- visible NPC rules
- visible faction rules
- visible rumor rules
- player-known/reported crime filtering

NPC secrets are not included in `visible_state`.

Relevant tests exist across:

- `test_visibility.py`
- `test_knowledge.py`
- `test_social_state.py`
- `test_rumors.py`
- `test_crime.py`
- `test_combat.py`
- `test_v04_integration_regression.py`

### Debug StateDeltas Do Not Enter Narrator

Passed.

Debug timeline APIs are separate endpoints:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They are guarded by `ENABLE_DEBUG_API` through `require_debug_api`.

No path was found where debug event payloads or raw debug `state_deltas` are passed to `Narrator`.

### MemorySummarizer Remains Summary-Only

Passed with a medium caution.

`MemorySummarizer` receives recent `Event` records and calls `LLMProvider.generate_json` with `MemorySummary`.

It does not:

- mutate `GameState`
- apply `StateDelta`
- append `Event`
- write canonical facts
- replace `EventLog`

Tests include:

- schema validation error path
- no silent invalid schema
- no `GameState` mutation

### Advanced Memory Retrieval Has Safe Filters

Passed.

`MemoryRecord.visibility` supports:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

Narrator-safe filtering is explicit:

```python
filter_narrator_safe_memories(...)
```

Allowed narrator memory visibilities:

- `player_visible`
- `narrator_safe`

Disallowed:

- `debug_only`
- `hidden`

Tests cover hidden/debug memory exclusion from narrator or player-facing context.

Current `Narrator` does not yet consume memory records directly, so this is a prepared safe interface rather than an active prompt path.

### Provider Factory Remains Runtime Composition Entry

Passed.

Runtime provider composition occurs in:

- `backend/app/llm/provider_factory.py`
- `backend/app/session_store.py`

Business modules depend on `LLMProvider` abstraction:

- `IntentParser`
- `Narrator`
- `MemorySummarizer`

Concrete provider construction found in application code is limited to `provider_factory`.

Tests instantiate `FakeLLMProvider`, `MockLLMProvider`, and `OpenAIProvider` directly as test doubles or provider unit tests. This is acceptable.

### Tests Do Not Call Real API

Passed.

Tests use `FakeLLMProvider` or `MockLLMProvider`.

OpenAI tests validate construction/error behavior and do not perform real API calls.

### Schema Validation Failure Has Controlled Behavior

Passed.

Observed behavior:

- `FakeLLMProvider` raises `LLMProviderError` on schema validation failure.
- `OpenAIProvider` raises `LLMProviderError` on schema validation failure.
- `IntentParser` catches `LLMProviderError` and falls back to a clarification/unknown intent.
- `Narrator` schema failure is not silent; it propagates `LLMProviderError`.
- `GameLoop` has a test proving narrator failure does not commit state or event.
- `MemorySummarizer` invalid schema raises `LLMProviderError`.

## Risk Items

### Medium Risk: Narrator Receives `ActionResult.reason`

`Narrator` passes `action_result.reason` to the LLM. Current rule modules appear to use player-safe reason strings and tests cover major hidden witness/hidden fact cases.

Residual risk: future rule authors may place debug-only details, hidden witness ids, hidden faction motives, or NPC secrets into `ActionResult.reason`.

This is not currently blocking, but it is the highest-priority boundary to harden before v0.5.

Recommended mitigation:

- Add separate fields:
  - `player_reason`
  - `debug_reason`
- Pass only `player_reason` to `Narrator`.
- Add a lint/test rule that `ActionResult.reason` or future `player_reason` does not contain hidden ids from `hidden_facts`, `witnesses`, or hidden NPCs.

### Medium Risk: MemorySummarizer Receives Raw Event StateDeltas

`MemorySummarizer` includes event `state_deltas` in the LLM prompt payload. This is acceptable for internal summarization, but raw deltas can contain hidden witness ids, hidden facts, crime records, faction internals, or debug-like details.

Current protection:

- `MemorySummarizer` does not mutate `GameState`.
- Its output is schema-validated.
- Memory retrieval has visibility filters.

Residual risk:

- A generated `MemorySummary` could summarize hidden details unless the caller classifies resulting `MemoryRecord` as `hidden` or `debug_only`.
- Legacy `MemorySummary` coercion in `MemoryStore.add_memory` defaults to `narrator_safe`.

Recommended mitigation:

- When summarizing events that include non-player-visible `state_deltas`, default the resulting `MemoryRecord.visibility` to `debug_only` or `hidden`.
- Add a helper such as `memory_visibility_for_events(events)`.
- Avoid exposing raw `state_deltas` to summarizer when preparing narrator-facing memories.

### Low Risk: Prompt Text Encoding Appears Corrupted In Some Files

`backend/app/llm/prompts.py` contains mojibake in narrator prompt text. This is not directly an LLM authority problem because schema and code boundaries still hold.

Risk:

- Prompt safety instructions may be less readable or less reliable to a live model.

Recommended mitigation:

- Rewrite narrator prompt text in clear UTF-8 Chinese or English.
- Preserve existing boundary instructions:
  - Narrator is not world judge.
  - No hidden facts.
  - No NPC secrets.
  - No creating canonical items/NPCs/locations.
  - No changing rule outcome.

### Low Risk: `MemoryStore.add_memory(MemorySummary)` Defaults To `narrator_safe`

Legacy compatibility converts `MemorySummary` into a `MemoryRecord` with `visibility=narrator_safe`.

Risk:

- If a summary was generated from hidden/debug events, it may become narrator-safe by default.

Recommended mitigation:

- Prefer explicit `MemoryRecord` creation for v0.4+ callers.
- Deprecate direct `MemorySummary` insertion or require a `visibility` argument.

## High-Risk Problems

None found.

## Medium-Risk Problems

1. Narrator receives `ActionResult.reason`; future rule code could accidentally include hidden/debug details there.
2. MemorySummarizer receives raw event `state_deltas`; generated summaries must be classified carefully before retrieval.

## Low-Risk Problems

1. Narrator prompt text appears mojibake/corrupted.
2. Legacy `MemorySummary` to `MemoryRecord` conversion defaults to `narrator_safe`.

## Fix Recommendations

Recommended before or during v0.4 final hardening:

1. Add a player-safe/debug split for action reasons.
2. Add tests ensuring narrator prompt excludes:
   - hidden witness ids
   - hidden NPC ids
   - hidden faction ids
   - raw `state_deltas`
   - NPC secrets
3. Add memory visibility classification for summaries generated from debug or hidden events.
4. Rewrite narrator prompt text to clean UTF-8.
5. Add a regression test that `MemorySummary` from an event containing non-player-visible deltas is not added as `narrator_safe` without explicit override.

## Acceptance Blocking Status

Not blocking v0.4 acceptance.

The current implementation preserves the core LLM boundary:

- LLM does not directly modify `GameState`.
- v0.4 rule outcomes are deterministic and code-owned.
- All canonical state changes remain `StateDelta` based.
- Player-facing state remains filtered through `visible_state`.
- Debug timeline data is isolated from Narrator.
- Provider selection remains centralized for runtime composition.

The medium risks should be addressed as hardening work before expanding memory-to-narrator integration or adding richer NPC/social prose.
