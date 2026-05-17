# v0.6 LLM Boundary Audit

## Audit Date

2026-05-18

## Scope

This audit reviews the v0.6 additions against the project rule that the world
engine remains the fact source and LLMs remain a bounded language layer.

Reviewed areas:

- save migration system and migration CLI/API
- authoring diff, preview, validation, and impact analysis
- relationship/faction graph backend and frontend data boundaries
- automated playtesting agents
- narrative quality evals
- performance instrumentation
- advanced mod versioning
- desktop packaging prototype
- local model provider support slice
- advanced combat expansion slice
- existing narrator, memory context, provider factory, and tests

## Verification Commands

Commands used during this audit:

```powershell
rg -n "OpenAIProvider|LocalHTTPProvider|LocalStubProvider|FakeLLMProvider|MockLLMProvider|create_llm_provider|generate_json|generate_text|LLMProvider|prompt|state_deltas|hidden_facts|hidden memory|debug_only|narrator_safe" backend/app backend/tests docs/LLM_PROTOCOL.md
rg -n "OpenAIProvider\(|LocalHTTPProvider\(|LocalStubProvider\(|MockLLMProvider\(|FakeLLMProvider\(" backend/app --glob "!backend/app/llm/provider_factory.py" --glob "!backend/app/llm/local_provider.py"
Get-Content backend/app/llm/provider_factory.py
Get-Content backend/app/llm/narrator.py
Get-Content backend/app/llm/context_builder.py
Get-Content backend/app/llm/local_provider.py
Get-Content backend/app/playtesting/provider.py
Get-Content backend/app/core/instrumentation.py
Get-Content backend/app/db/migrations.py
Get-Content backend/app/db/migration_service.py
Get-Content backend/app/engine/content/authoring_service.py
Get-Content backend/app/engine/rules/graphs.py
Get-Content backend/app/engine/content/side_quest_generator.py
Get-Content scripts/start_local_studio.ps1
Get-Content docs/DESKTOP_PACKAGING.md
```

Latest full verification from the current v0.6 work session before this audit:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Result: `451 passed`; frontend production build passed.

## Passed Items

1. v0.6 rule modules do not call real LLM services.
   - Save migration, authoring preview/impact, graph generation, performance instrumentation, mod versioning, and combat expansion are deterministic code paths.
   - No direct provider calls were found in these rule modules.

2. Save migration does not call LLM.
   - `backend/app/db/migrations.py` and `backend/app/db/migration_service.py` use schema/default filling and validation only.
   - Migration calls `load_game_state_payload` for validation, not provider code.
   - Migration does not generate state from natural language.

3. Authoring diff/preview/impact-analysis does not call LLM.
   - `ContentAuthoringService` uses YAML parsing, temporary draft validation, diff/id comparison, and `validate_world_pack`.
   - Draft validation does not mutate active `GameState`.

4. Graph backend does not infer hidden relationships with LLM.
   - `build_relationship_graph` and `build_faction_graph` read structured `GameState` only.
   - Player graph scope filters hidden/unknown relationships; debug graph is a separate debug-scoped route.

5. Playtesting agents do not call real LLM APIs.
   - `PlaytestLLMProvider` is deterministic and local.
   - Playtest agents act through `GameLoop`/visible-state inputs rather than direct `GameState` mutation.

6. Narrative quality evals do not use an external LLM judge.
   - Evals are deterministic rule checks against `NarrativeResult`, `ActionResult`, and forbidden/required strings.
   - CLI evals use local cases and do not call providers.

7. Performance instrumentation avoids prompt and sensitive content capture.
   - `PerformanceSample` stores names, durations, stages, and sanitized tags only.
   - Tag sanitizer rejects `api_key`, `llm_api_key`, `secret`, `sk-`, `prompt`, `game_state`, and `state_delta`.
   - Debug performance API is debug-gated and returns aggregate/local timing data.

8. Advanced mod versioning does not call LLM and does not execute code.
   - `ModLoader` parses YAML manifests, validates versions/dependencies/conflicts, reuses world validation, and rejects executable suffixes.
   - No provider calls or code execution paths were found.

9. Desktop packaging prototype does not package API keys.
   - `scripts/start_local_studio.ps1` defaults `LLM_PROVIDER=mock`.
   - The script explicitly does not set `LLM_API_KEY`.
   - `docs/DESKTOP_PACKAGING.md` states API keys must remain in local environment or ignored `.env`, not in frontend assets.

10. Local model provider remains behind `LLMProvider`.
    - `LocalStubProvider` and `LocalHTTPProvider` implement the `LLMProvider` interface.
    - `provider_factory.py` supports `mock`, `local_stub`, `local_http`, and `openai`.
    - `local_http` is a checked stub; it requires `LOCAL_LLM_BASE_URL` and does not call a local service yet.

11. Local model output cannot directly enter `GameState`.
    - Local providers only satisfy `generate_text`/`generate_json`.
    - Existing business flow still routes model output through `IntentParser`, `Narrator`, or other schema-validated language-layer modules.
    - State changes are still generated by action/rule modules as `StateDelta`.

12. Advanced combat expansion remains rule-driven.
    - Stance, guarded/stunned/bleeding, non-lethal attack, and flee risk are computed in `combat.py`/actions with deterministic RNG.
    - No LLM call decides hit, damage, death, flee, or visibility.

13. No LLM output was found directly entering `GameState`.
    - `GameLoop` still takes `PlayerIntent`, dispatches to rule handlers, applies `StateDelta`, records `Event`, and only then asks `Narrator` to render.

14. Narrator still receives only sanitized action result payload.
    - `Narrator.render` builds `safe_action_result` with `success_level`, `reason`, and `visible_facts`.
    - It does not pass `state_deltas`, `hidden_facts`, raw events, raw `GameState`, debug graph, or debug timeline.

15. Memory context filtering is explicit.
    - `MemoryContextBuilder` filters hidden/debug-only memory through `filter_narrator_safe_memories` and hidden/discoverable fact checks.
    - NPC context checks `npc_knows` before including fact-bound memories.

16. Provider factory remains the centralized provider selection point.
    - Runtime/session code uses `create_llm_provider`.
    - Direct provider instantiation found in `backend/app` outside factory is limited to provider class definitions themselves.
    - Tests instantiate fake/local providers directly as test doubles, which is acceptable.

17. Tests do not call real APIs by default.
    - Provider tests cover OpenAI construction and local HTTP config errors without making real network calls.
    - Playtesting uses `PlaytestLLMProvider`.
    - Narrative quality evals use deterministic local checks.

18. Schema validation failures are explicit.
    - `FakeLLMProvider`, `LocalStubProvider`, `OpenAIProvider`, and side quest LLM-assisted generation raise clear errors on schema validation failure.
    - `local_http` missing base URL raises `LLMProviderError`.

## Risk Items

1. `MemorySummarizer` serializes event `state_deltas` into its summarization input.
   - This is not a new v0.6 issue, and it is for memory summarization rather than narrator prompts.
   - Risk remains if hidden/debug events are summarized into memories with too-permissive visibility.
   - Existing protocol documentation warns summaries derived from hidden/debug events should be `debug_only` or `hidden`.

2. `ActionResult.reason` can enter narrator prompt.
   - `Narrator.render` passes the rule-generated reason.
   - Rule modules must continue avoiding hidden witness names, NPC secrets, hidden fact text, or raw debug details in `reason`.
   - v0.6 combat flee failure appears generic and does not identify hidden observers.

3. Graph player visibility helper is stricter/different from some other visibility helpers.
   - `graphs.py` treats hidden NPCs as invisible regardless of `discovered_by`.
   - This is conservative for leak prevention but may under-display discovered hidden NPC relationships.
   - This is a product consistency risk, not an LLM authority risk.

4. Desktop launcher writes backend/frontend logs.
   - The launcher itself does not write keys, but backend logs could contain future application output.
   - Current audit found no prompt/API-key logging in instrumentation, but future logging changes need review.

## High Risk Issues

None found.

No v0.6 module reviewed gives LLM output authority to directly mutate
`GameState`, decide combat, decide migration, infer hidden graph edges, or bypass
`StateDelta`/`EventLog`.

## Medium Risk Issues

1. Memory summarization input includes raw event `state_deltas`.
   - Severity: medium.
   - Reason: if summarized into `narrator_safe` memory without sanitization, hidden/debug event details could later reach narrator context.
   - Current mitigations: memory visibility enum, `MemoryContextBuilder`, boundary evals, and protocol warnings.
   - Recommended follow-up: add a dedicated test that `MemorySummarizer` outputs from hidden/debug events are stored as `debug_only` or require an explicit sanitizer before `MemoryStore.add_memory`.

2. Rule-generated `ActionResult.reason` remains part of narrator prompt.
   - Severity: medium.
   - Reason: hidden information leakage could happen if a future rule puts hidden fact text or hidden witness id in `reason`.
   - Current mitigations: targeted evals for hidden facts, hidden witnesses, and raw `state_deltas`.
   - Recommended follow-up: add a shared helper or lint/eval fixture that scans `ActionResult.reason` for hidden ids/text before narrator rendering in tests.

## Low Risk Issues

1. `LocalStubProvider` returns mojibake placeholder text.
   - This does not affect authority boundaries.
   - It may reduce readability of test snapshots and docs.
   - Recommended follow-up: replace stub strings with clean UTF-8 Chinese placeholders.

2. `LocalHTTPProvider` is a stub and does not perform HTTP calls.
   - This is intentionally limited for v0.6.
   - Future implementation must add transport tests, timeout handling, schema validation, and prompt logging redaction.

3. Desktop launcher defaults `ENABLE_DEBUG_API=true`.
   - This matches local development intent.
   - It must remain clearly documented as local-only and not suitable for public deployment.

## Fix Recommendations

Before v0.6 acceptance:

- No blocking fixes required for LLM authority boundaries.

Recommended non-blocking hardening:

1. Add a sanitizer/storage policy test for memory summaries derived from hidden/debug events.
2. Add a small test helper to assert narrator prompt payloads never include `ActionResult.hidden_facts`, `state_deltas`, hidden witness ids, or hidden fact text.
3. Replace mojibake test/stub narration strings with clean UTF-8 Chinese text.
4. In future `LocalHTTPProvider` implementation, keep prompt logging disabled/redacted by default and preserve schema validation.
5. Keep desktop/debug APIs explicitly local-only in docs and acceptance checks.

## Blocking Status

This audit does not find any high-risk or release-blocking LLM boundary issue.

`v0.6` is not blocked on LLM boundary grounds, assuming existing visibility,
security, and acceptance audits do not uncover separate blockers.
