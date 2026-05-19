# v1.3 Security / Debug Audit

Verification Date: 2026-05-19

Scope: v1.3 Advanced NPC Simulation debug APIs, behavior timeline, dry-run tick, performance logging, provider configuration failure paths, NPC simulation presets, regression fixtures, tracked-file hygiene, and sensitive string scans.

## Verification Inputs

- Searched backend, tests, docs, `.env.example`, and frontend references for debug gates, API keys, provider usage, external network calls, script execution, performance logging, and NPC simulation routes.
- Reviewed `backend/app/main.py` debug endpoints and redaction helpers.
- Reviewed `backend/app/core/instrumentation.py`.
- Reviewed `backend/app/llm/provider_factory.py`, `backend/app/llm/openai_provider.py`, and `backend/app/llm/local_provider.py`.
- Reviewed `backend/app/engine/content/npc_simulation_presets.py`.
- Reviewed `backend/app/playtesting/npc_simulation_regression.py`.
- Checked `git status --short`.
- Checked tracked files for `.env`, databases, logs, caches, `node_modules`, `frontend/dist`, and desktop build outputs.
- Searched for real-looking `sk-...` keys and sensitive configuration strings.

## Passed Items

1. **Debug API is controlled by `ENABLE_DEBUG_API`.**  
   NPC simulation debug routes, behavior timeline routes, event/timeline debug routes, graph debug routes, and performance debug routes call `require_debug_api()` or the shared debug gate before returning debug data.

2. **NPC Simulation Debugger API does not return API keys or raw env by design.**  
   Debug NPC simulation detail goes through `_redact_debug_payload`, which redacts `llm_api_key`, `api_key`, `raw_env`, `env`, and keys containing `secret`. Tests assert the NPC simulation debug response does not contain API key or raw env strings.

3. **Dry-run tick does not write database or mutate active `GameState`.**  
   `/debug/sessions/{session_id}/npc-simulation/dry-run-tick` snapshots the current state, runs `run_npc_simulation_tick(game_loop.state)`, returns redacted result data, and reports whether the in-memory state stayed unchanged. It does not call the save repository. v1.3 integration tests assert the session state remains unchanged.

4. **Player API does not return NPC simulation debug data.**  
   Player state responses are built with `build_visible_state`, which omits intent queues, plans, debug output, debug reasons, raw events, and state deltas. v1.3 integration tests assert `debug_output` is absent from player state.

5. **Debug timeline does not enter narrator paths.**  
   Behavior timeline APIs are under `/debug/...` and return `NPCBehaviorTimelineResponse`. No inspected narrator or dialogue response path consumes timeline/debug output.

6. **Performance logging strips high-risk tags.**  
   `PerformanceRecorder` sanitizes tags containing `api_key`, `llm_api_key`, `secret`, `sk-`, `prompt`, `game_state`, or `state_delta`. Performance samples store timing/stage metadata rather than content text.

7. **Real `.env` is not git-tracked.**  
   The tracked-file scan found only `.env.example` and `frontend/.env.example`, which are expected safe templates. No real `.env` file was reported as tracked.

8. **Database, log, cache, `node_modules`, `frontend/dist`, and desktop build outputs are not tracked.**  
   The tracked forbidden-file scan did not report tracked DB/log/cache/build/dependency outputs.

9. **No real `sk-...` key was found.**  
   The search found documentation references and test fixtures such as `sk-test-fake` and `sk-real-looking-but-local`, but no production real API key was identified.

10. **Test fake keys are distinguishable from real leaks.**  
    Fake keys are named as test/local placeholders and are covered by prior release-check logic that recognizes fake markers. They are not used as real provider credentials.

11. **Provider factory and providers fail clearly when required config is missing.**  
    `OpenAIProvider` raises `LLMProviderError("LLM_API_KEY is required for OpenAIProvider")` when configured without a key. `LocalHTTPProvider` raises `LLMProviderError("LOCAL_LLM_BASE_URL is required when LLM_PROVIDER=local_http")` when the local endpoint is missing.

12. **Tests do not call real API by default.**  
    v1.3 tests and regression playtests use mock/local deterministic paths or no provider. The simulation regression runner constructs local temporary state and SQLite storage rather than a real external API client.

13. **NPC simulation cannot call external network services.**  
    v1.3 simulation modules do not import `urllib`, `requests`, `httpx`, provider classes, or external tool clients. External HTTP code exists only in `LocalHTTPProvider`, which is still outside NPC simulation authority.

14. **NPC simulation presets do not execute scripts.**  
    `NPCSimulationPreset` validates against script/command/url/executable fields and uses `yaml.safe_load` / `yaml.safe_dump`. Preset apply returns a draft preview and relies on the authoring validation gate; it does not execute code.

15. **Regression fixtures do not contain real user data.**  
    `npc_simulation_regression.py` uses synthetic fixture worlds, temporary directories, temporary SQLite files, fake NPCs/facts, and redacted hidden-text summaries.

## High-Risk Issues

None found.

No current v1.3 path was found that exposes API keys/raw env through NPC simulation debug APIs, writes dry-run tick output to the database, allows NPC simulation to call external network services, executes preset scripts, or tracks real `.env` / DB / log / build artifacts.

## Medium-Risk Issues

1. **Performance tag sanitizer is keyword-based.**  
   It blocks common risky terms such as `secret`, `prompt`, `game_state`, and `state_delta`, but does not compare tag values against hidden fact bodies. Current instrumentation appears to use safe operational tags, so this is not a release blocker.

2. **Debug endpoints can return raw `state_deltas` by design.**  
   Debug event/tick APIs intentionally expose deltas for local debugging. This is acceptable behind `ENABLE_DEBUG_API`, but those response models must not be reused in player or narrator UI.

3. **`local_http` provider contains external HTTP capability.**  
   This is expected and documented as an explicit LLM provider option. It is not used by NPC simulation modules, but tests and local runs should keep `LLM_PROVIDER=mock` or `local_stub` unless intentionally testing local model integration.

4. **Sensitive string scan is noisy.**  
   The scan returns many documentation examples, test placeholders, and historical audit text. This increases review cost but did not identify a real credential.

## Low-Risk Issues

1. **`.env.example` and `frontend/.env.example` appear in tracked-file scans.**  
   These are expected safe templates. Release checks should continue allowing example env files while blocking real `.env`.

2. **PowerShell profile loading warning appears in command output.**  
   The local shell emits a signed-profile warning before commands. It does not affect repository security, but it makes audit logs noisier.

3. **Local stub/playtest fixture text includes placeholder narrative content.**  
   This is not real user data and is not part of NPC simulation security authority.

## Fix Recommendations

1. Add a v1.3 static guard test that fails if NPC simulation modules import `urllib`, `requests`, `httpx`, `subprocess`, provider classes, or call `exec` / `eval`.

2. Add a debug response regression test for every NPC simulation debug endpoint asserting absence of `LLM_API_KEY`, `OPENAI_API_KEY`, `raw_env`, `api_key`, `sk-`, and representative hidden fixture text.

3. Keep performance sample tags limited to ids, counts, phase names, and durations. Do not add prompt text, hidden fact text, event result prose, raw deltas, or local paths as performance tags.

4. Keep `ENABLE_DEBUG_API` disabled by default for non-development runs, and ensure frontend debug panels degrade safely when disabled.

5. Continue treating `local_http` as explicit opt-in local model integration, not a simulation dependency. NPC simulation tests should remain provider-free or mock/local-stub only.

6. Extend release-check allowlists so `.env.example` files are clearly distinguished from real `.env` files, while `.db`, `.sqlite`, `.log`, caches, `frontend/dist`, desktop build outputs, and `node_modules` stay blocked.

## v1.3 Release Blocker Assessment

**Not blocking v1.3 release.**

The reviewed v1.3 implementation keeps debug APIs gated, redacts API-key/raw-env fields in NPC simulation debug responses, keeps dry-run tick read-only, keeps player/narrator paths separate from debug timelines, avoids external network/script execution in NPC simulation and presets, and does not track forbidden local artifacts.
