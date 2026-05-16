# v0.3 LLM Boundary Audit

Date: 2026-05-17

Scope:

- v0.3 rules and actions: NPC schedule, search, inventory, lockpick, sneak, quest state machine, world tick, debug timeline.
- LLM-facing modules: provider factory, intent parser, narrator, memory summarizer.
- API/player-visible surfaces and tests.

## Summary

v0.3 preserves the core permission boundary: LLM output is used for intent parsing, narration, and memory summaries, while world truth is still decided by deterministic Python rules and applied through `StateDelta`.

No high-risk blocker was found for v0.3 acceptance. The main non-blocking risk is that `MemorySummarizer` receives full event payloads, including `state_deltas`; it does not mutate `GameState`, but future memory storage must avoid promoting summary text into canonical facts without rule validation.

## Passed Items

1. v0.3 rule modules do not call LLM providers.

   Reviewed modules:

   - `backend/app/engine/actions/search.py`
   - `backend/app/engine/actions/lockpick.py`
   - `backend/app/engine/actions/sneak.py`
   - `backend/app/engine/rules/inventory.py`
   - `backend/app/engine/rules/quests.py`
   - `backend/app/engine/rules/schedule.py`
   - `backend/app/engine/rules/world_tick.py`

   These modules rely on `GameState`, `StateDelta`, deterministic rules, and optional seeded `Random`. They do not instantiate or call `LLMProvider`.

2. v0.3 outcomes are rule-engine decisions.

   - `search` discovers only objects/facts matching structured visibility/scope rules.
   - `inventory` ownership changes are generated as `StateDelta`.
   - `lockpick` uses target lock state, visibility, inventory tool tags, difficulty, and seeded RNG.
   - `sneak` uses location connectivity, cover/light, NPC alertness/suspicion, and seeded RNG.
   - `quest` progress is triggered by structured state changes such as fact discovery, item acquisition, NPC talk, and location visits.
   - `schedule` uses game time and content-pack schedule entries.
   - `world_tick` runs schedule, suspicion decay, delayed consequences, and quest triggers.

3. No LLM output directly writes to `GameState`.

   `GameLoop` applies only `ActionResult.state_deltas`, quest deltas, turn deltas, and world tick deltas through `apply_delta`. `Narrator` output is stored on `Event.narrative_text`, not in canonical `GameState`.

4. Narrator receives a restricted payload.

   `Narrator.render` builds `safe_action_result` with:

   - `success_level`
   - `reason`
   - `visible_facts`

   It does not pass `ActionResult.hidden_facts` to prompt construction.

5. Hidden facts and NPC secrets are covered by tests.

   Relevant checks exist in:

   - `backend/tests/test_narrator.py`
   - `backend/tests/test_knowledge.py`
   - `backend/tests/test_game_api.py`
   - `backend/tests/test_v03_integration_regression.py`
   - `backend/tests/test_lockpick.py`
   - `backend/tests/test_search.py`

6. NPC dialogue context is constrained.

   `get_npc_context_for_dialogue` merges NPC knowledge but filters facts through `_fact_allowed_for_dialogue`. Facts not visible to the player or public are not passed through dialogue context, and `npc.secrets` are excluded unless already allowed.

7. Memory summarizer does not mutate state.

   `MemorySummarizer.summarize_recent` returns `MemorySummary` through provider schema validation. It does not call `apply_delta`, does not write `GameState`, and does not write `EventLog`.

8. Provider factory remains the app-level provider entry point.

   Runtime session construction goes through `InMemorySessionStore`, which defaults to `create_llm_provider`. Business orchestration still depends on `LLMProvider` abstractions for `IntentParser` and `Narrator`.

9. Tests do not call real OpenAI APIs.

   Tests use `FakeLLMProvider`, `MockLLMProvider`, or direct `Settings` checks. OpenAI provider tests verify construction/error behavior only; no real API request is made.

10. Schema validation failures are explicit.

   - `FakeLLMProvider` raises `LLMProviderError` on Pydantic validation failure.
   - `OpenAIProvider.generate_json` raises `LLMProviderError` on JSON schema validation failure.
   - Narrator schema errors are tested to be non-silent.
   - Provider factory rejects unknown `LLM_PROVIDER` values clearly.

## Risk Items

1. `MemorySummarizer` receives full event payloads.

   It includes event `state_deltas`, which may contain hidden/debug information. This is acceptable for local-only summarization because it does not mutate state, but it should remain classified as internal memory input, not player-visible text or canonical fact input.

2. Debug timeline intentionally exposes state deltas.

   Debug endpoints may show hidden or system-only deltas. This is allowed for local development, gated by `ENABLE_DEBUG_API`, but must not be treated as player-facing API.

3. Some `ActionResult.reason` strings are sent to Narrator.

   Current reasons are rule-generated and generally non-secret. Future rules should avoid putting hidden NPC identity, secret fact text, or undiscovered causal details in `reason`, because `Narrator` receives it.

## High-Risk Issues

None found.

## Medium-Risk Issues

1. Memory summaries could become unsafe if later promoted into canonical state without validation.

   Current state: not blocking. `MemorySummary` is schema-validated and does not alter `GameState`.

   Risk: future `MemoryStore` or fact-import code might treat summary text as authoritative.

2. Debug timeline can expose hidden facts through `state_deltas`.

   Current state: not blocking. The API is explicitly debug/local and can be disabled.

   Risk: if frontend debug panel is exposed beyond local development, it bypasses normal visibility boundaries.

3. `ActionResult.reason` is part of narrator input.

   Current state: not blocking. Existing v0.3 reason strings do not include hidden facts or secrets.

   Risk: future rule implementations may accidentally encode hidden cause details in `reason`.

## Low-Risk Issues

1. Tests directly instantiate `OpenAIProvider` for constructor-level validation.

   This does not call the network and is acceptable, but it is a minor exception to the runtime “business code uses factory” pattern.

2. `FakeLLMProvider` is used directly in tests.

   This is intentional and helps guarantee no real API usage.

3. `MemorySummarizer` has no hidden-fact redaction layer.

   This is acceptable for internal memory compression, but future player-facing memory views should use a visibility filter.

## Fix Recommendations

1. Before v0.4 memory expansion, add a rule that `MemorySummary.important_facts` cannot be promoted to `GameState.facts` without deterministic validation.

2. Add a short developer note near debug endpoints or in docs stating that debug timeline may include hidden/system information and must remain local-only.

3. Add a helper for rule-facing narrator-safe reason strings, or add tests preventing known hidden fact IDs/NPC secrets from appearing in `ActionResult.reason`.

4. If debug API is ever enabled outside local use, require authentication or remove hidden delta fields from its response.

5. Keep provider construction centralized in app/session code; continue allowing direct fake providers only in tests.

## Acceptance Impact

Does this block v0.3 acceptance?

No.

Rationale:

- v0.3 deterministic systems do not call LLMs.
- LLM output does not directly modify `GameState`.
- Narrator receives visible facts, not `hidden_facts`.
- NPC secrets are filtered out of dialogue/player-visible paths.
- Memory summary remains non-authoritative and non-mutating.
- Provider factory remains the runtime provider selection entry point.
- Automated tests use fake/mock providers and do not call real APIs.

