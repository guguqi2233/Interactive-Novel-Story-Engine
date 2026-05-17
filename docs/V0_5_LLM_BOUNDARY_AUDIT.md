# v0.5 LLM Boundary Audit

## Audit Date

2026-05-17

## Scope

This audit reviews the v0.5 LLM authority boundary across:

- Content Authoring API and validation.
- Local memory backends and `MemoryContextBuilder`.
- NPC goals, NPC planning, relationships, faction conflict, economy/trade, and mod packaging.
- Procedural side quest generator.
- Narrator prompt inputs and player-visible API boundaries.
- Provider factory usage and test isolation from real APIs.

The audit is source-code based. It uses targeted `rg` searches and direct file reads of the relevant modules and tests.

## Verification Commands

- `rg "LLM|provider|generate_json|generate_text|OpenAIProvider|FakeLLMProvider|MockLLMProvider|create_llm_provider" backend/app backend/tests docs/LLM_PROTOCOL.md`
- `rg "Narrator|narrator|visible_facts|narrator_safe|hidden|DEBUG_ONLY|state_deltas" backend/app/llm backend/app/core backend/app/session_store.py backend/app/main.py`
- Reviewed:
  - `backend/app/llm/provider_factory.py`
  - `backend/app/llm/narrator.py`
  - `backend/app/llm/context_builder.py`
  - `backend/app/llm/memory_store.py`
  - `backend/app/engine/content/side_quest_generator.py`
  - `backend/tests/evals/test_narrative_boundaries.py`
  - `backend/tests/test_memory_context_builder.py`
  - `backend/tests/test_llm_provider.py`
  - `backend/tests/test_v05_integration_regression.py`

Full test suite was not rerun as part of this audit document creation. The immediately preceding v0.5 integration task reported `python -m pytest` as `357 passed` and frontend build as passed.

## Passed Items

1. v0.5 deterministic modules do not call LLM providers.

   The following v0.5 modules are rule/code driven and have no `LLMProvider`, `generate_json`, or `generate_text` calls:
   - authoring service
   - content validator
   - memory store retrieval backends
   - NPC goal rules
   - NPC planning rules
   - relationship graph rules
   - faction conflict rules
   - economy/trade rules
   - mod loader

2. Runtime rule outcomes remain engine-owned.

   Authoring, validation, memory retrieval, NPC goals/planning, relationship graph, faction conflict, economy, and mod packaging are decided by local schema validation and deterministic rule modules. They do not ask an LLM to decide canonical outcomes.

3. Procedural quest LLM-assisted mode is draft-only.

   `llm_assisted_generate_side_quest` accepts an injected `LLMProvider`, calls `generate_json` into the `QuestDraft` schema, validates references with `validate_quest_draft`, and returns a draft. It does not write `quests.yaml` and does not modify active `GameState`.

4. No LLM output directly enters `GameState`.

   The reviewed LLM paths are:
   - `IntentParser`: schema-validated `PlayerIntent`; action resolution remains in `ActionDispatcher` and rule modules.
   - `Narrator`: schema-validated `NarrativeResult`; result is prose/suggestions only.
   - `MemorySummarizer`: schema-validated summary; memory is not authoritative state.
   - side quest generator: schema-validated `QuestDraft`; draft-only.

5. Narrator input remains filtered.

   `Narrator.render` builds a `safe_action_result` with only:
   - `success_level`
   - `reason`
   - `visible_facts`

   It does not pass `state_deltas`, `hidden_facts`, raw `Event`, debug timeline data, witness records, NPC secrets, or raw `GameState`.

6. Hidden facts are guarded from narrator prompt.

   `Narrator.render` ignores `ActionResult.hidden_facts`. Boundary evals assert that hidden fact ids/text and hidden witness ids do not enter narrator messages.

7. NPC secrets are not passed to player-facing narration.

   `build_visible_state` does not serialize `NPCState.secrets`, and `Narrator.render` does not receive NPC records. Boundary evals cover NPC secret exclusion from narrator prompt.

8. Debug `state_deltas` do not enter narrator.

   Debug APIs expose `state_deltas` only through debug endpoints gated by `ENABLE_DEBUG_API`. Narrator prompt construction does not consume debug APIs or raw events. Boundary evals assert raw delta paths are absent from narrator prompt and player API.

9. Hidden/debug memory is filtered before narrator context.

   `MemoryContextBuilder` excludes:
   - `MemoryVisibility.HIDDEN`
   - `MemoryVisibility.DEBUG_ONLY`
   - memories tied to hidden/discoverable facts not in `player_visible_facts`
   - memories tagged with `source_event_hidden`

   Tests cover hidden/debug memory exclusion from narrator context and v0.5 integration coverage confirms persistence plus filtering.

10. NPC memory context respects NPC knowledge.

   `MemoryContextBuilder` uses `npc_knows` for NPC-specific memory context. Memories tied to facts the NPC does not know are excluded from `npc_known_memories`.

11. Provider factory remains centralized for runtime provider selection.

   `InMemorySessionStore` defaults to `create_llm_provider`. `provider_factory.py` chooses only `mock` or `openai` from settings/environment and raises clear `LLMProviderError` for unknown providers.

12. Tests do not call real APIs.

   Tests use `FakeLLMProvider`, `MockLLMProvider`, or explicit `Settings(llm_provider="mock")`. OpenAI provider tests instantiate configuration paths but do not perform network calls.

13. Schema validation failures are explicit.

   `FakeLLMProvider` and `OpenAIProvider` raise `LLMProviderError` on schema validation failure. `IntentParser` catches provider errors into controlled unknown/clarification behavior. Side quest generator invalid schema is covered by tests.

14. Authoring API does not call LLM or auto-rewrite YAML.

   Authoring reads/writes whitelisted YAML files, parses YAML, and invokes validator. It does not call `LLMProvider` and does not generate or rewrite content with LLM assistance.

## Risk Items

1. LLM-assisted side quest generator is a sanctioned LLM entry point.

   Current behavior is draft-only and validated. The risk is future integration: if authoring UI/API later exposes this function, it must preserve explicit review, validator enforcement, and no active-save mutation.

2. `MemoryContextBuilder` is safe, but not yet the only possible future narrator-context path.

   Current `GameLoop` calls `Narrator.render` directly with `visible_facts` and no memory. This is safer than passing memory, but future memory-to-narrator integration should route through `MemoryContextBuilder` only.

3. `MemorySummarizer` includes event `state_deltas` in its summarization input.

   This is an LLM summarization path, not a player/narrator path, and summaries are not authoritative state. Still, it is a sensitive input surface because raw deltas can contain hidden/debug details. Any summarized memory intended for narrator/player use must remain filtered by memory visibility and fact checks.

4. Test code directly instantiates `OpenAIProvider` for constructor/error coverage.

   This is confined to `backend/tests/test_llm_provider.py` and does not call the API. It is acceptable test-only behavior, but runtime business modules should continue using the provider factory.

## High Risk Issues

None found.

No reviewed v0.5 runtime module lets LLM output directly modify `GameState`, emit `StateDelta`, decide rules, or bypass schema validation.

## Medium Risk Issues

None blocking.

The side quest generator and memory summarizer remain areas to keep under audit because both intentionally process LLM output. Current controls are adequate for v0.5:

- side quest output is `QuestDraft`, not runtime state;
- memory summary is non-authoritative;
- both use schema validation;
- hidden/debug memory is filtered before narrator context.

## Low Risk Issues

1. Narrator prompt system text appears mojibake in `backend/app/llm/prompts.py`.

   This is not an authority leak by itself because the code-level filtering is still enforced, and tests assert prompt inputs exclude hidden data. It is a maintainability issue: future reviewers may find the boundary text hard to read.

2. Memory context is implemented but not yet integrated into `GameLoop` narrator calls.

   This prevents memory leaks today, but it also means v0.5 memory context is not yet a single enforced narrator path in runtime. When integrated, tests should assert only `narrator_safe_memories` are passed.

3. LLM-assisted quest generator can reference hidden fact ids.

   The prompt allows hidden facts by id only, and validation rejects hidden text leaks. This is acceptable for authoring-only draft workflows, but authoring UI should label such drafts as author-facing, not player-facing.

## Fix Recommendations

1. Before exposing LLM-assisted quest generation via API/UI, require:
   - authoring-only route gating;
   - `QuestDraft` schema validation;
   - `validate_quest_draft`;
   - explicit user save/export action;
   - no active `GameState` mutation.

2. When memory is wired into Narrator runtime, introduce or enforce a single context assembly path:
   - `MemoryContextBuilder.build(...)`;
   - pass only `narrator_safe_memories`;
   - add a regression test that hidden/debug/source-event-hidden memory cannot reach provider messages.

3. Keep `MemorySummarizer` outputs non-authoritative:
   - never apply summary facts as `StateDelta`;
   - tag any debug-derived or hidden-derived memory as `debug_only` or `hidden`;
   - require context filtering before use in narration.

4. Restore readable narrator boundary prompt text in a later non-blocking cleanup, while keeping existing tests.

5. Preserve provider factory discipline:
   - runtime modules should depend on `LLMProvider`;
   - only factory should instantiate concrete production providers;
   - test-only `FakeLLMProvider`/`OpenAIProvider` constructor checks are acceptable.

## Blocking Assessment

No release-blocking LLM boundary issue was found.

v0.5 acceptance is not blocked by this audit.

## Final Verdict

v0.5 LLM boundary audit passed.

The project continues to enforce the central rule: LLMs may parse, narrate, summarize, or generate authoring drafts, but they do not decide canonical world outcomes and do not directly modify `GameState`. Runtime v0.5 systems remain rule-engine driven, `MemoryContextBuilder` filters hidden/debug memory, and provider selection remains centralized through the provider factory.
