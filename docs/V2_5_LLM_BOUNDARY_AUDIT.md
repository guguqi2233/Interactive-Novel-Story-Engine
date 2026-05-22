# v2.5 LLM Boundary Audit: Provider Gateway Pro

## Verification Date

2026-05-22

## Scope

This audit reviews the current v2.5 Provider Gateway Pro implementation against
the LLM boundary requirements in `AGENTS.md`, `docs/LLM_PROTOCOL.md`, and
`docs/V2_5_ROADMAP.md`.

The review is code/static-inspection based. No business code was modified for
this report.

## Review Commands

```powershell
rg -n "create_llm_provider|ProviderGateway|ProviderRouter|OpenAIProvider\(|OpenAICompatibleProvider\(|LocalHTTPProvider\(|LocalStubProvider\(|MockLLMProvider\(" backend/app backend/tests
rg -n "state_deltas|state_delta|hidden fact|debug memory|private_persona|api_key|secret_ref|allow_real_provider|allow_real_connection" backend/app/llm backend/app/platform backend/tests/test_v25_provider_gateway_integration_regression.py backend/tests/test_v25_provider_gateway_pro.py
rg -n "generate_json|generate_text|apply_confirmed|CrossMode|TavernToWorldApplyService|ProviderSafetyPolicy|resolve_provider_for_use_case" backend/app/llm backend/app/platform
```

## Passed Items

1. `LLMProvider` remains the common runtime contract for text and schema-validated JSON generation.
2. Concrete provider construction is centralized in `backend/app/llm/provider_factory.py`; direct concrete provider construction found in app code is inside the factory.
3. `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and `openai_api_key` fields.
4. Provider profiles store `api_key_env` / `secret_ref` references rather than raw key values.
5. `ProviderSecretResolver` resolves secrets server-side only; safe summaries do not include secret values.
6. `OpenAICompatibleProvider` and relay-style profiles use the OpenAI-compatible protocol without binding to a specific relay service.
7. `ProviderRouter` validates required JSON capability for `structured_json`, `world_intent_parse`, `cross_mode_draft`, and `quality_eval`.
8. Runtime fallback through `ProviderGateway` keeps the same message payload and still calls `generate_json` with Pydantic schema validation.
9. `ProviderSafetyPolicy` supports mode allow/deny, sensitive prompt, debug prompt, prompt/output logging, redaction, and local-only checks.
10. Provider profile API responses return safe summaries and do not expose raw secrets.
11. Provider usage records store metadata only; they do not store prompt text, model output text, API keys, raw env, or hidden facts.
12. Provider benchmark and structured-output reliability flows default to fake/mock providers and require explicit real-provider opt-in.
13. `MemorySummarizer` no longer serializes raw `state_deltas` into provider prompt payloads; it records only `state_delta_count`.
14. Novel and Tavern prompt contexts validate against secret-like text and `state_delta` markers before provider calls.
15. Cross-Mode apply remains deterministic: `TavernToWorldApplyService.apply_confirmed` requires explicit confirmation, uses supplied `StateDelta` objects, and records `EventLog`; no LLM call decides apply.
16. v2.5 integration regression tests cover profile secrets, Provider API, routing, fallback, usage, benchmark/reliability, safety policy, Novel/Tavern/World/Cross-Mode routed calls, and no-LLM apply.

## Risk Items

1. Provider Gateway is not yet the sole practical LLM entry point across all runtime paths.
2. Several legacy business/helper modules still obtain providers by calling `create_llm_provider` directly rather than resolving through `ProviderRouter` and `ProviderGateway`.
3. Novel, Tavern, World, and Cross-Mode services can be exercised through routed providers in tests, but their production constructors still primarily accept a plain injected `LLMProvider`.
4. `ProviderSafetyPolicy` is enforced in `ProviderRouter.resolve_provider_for_use_case`, but paths that call `create_llm_provider` directly do not automatically pass through that policy.
5. Prompt-lab and diagnostics modules allow explicit real-provider opt-in. This is gated by policy and not used in tests, but it remains an operational boundary requiring careful configuration.

## High-Risk Issues

### H1. Provider Gateway Is Not Yet The Unique Runtime LLM Entry

Evidence:

- `backend/app/session_store.py` still defaults to `create_llm_provider`.
- `backend/app/main.py` Tavern chat endpoint still uses `create_llm_provider` if no injected `tavern_llm_provider` exists.
- Prompt Lab helpers such as `prompt_ab_test.py`, `narrator_style_lab.py`, `npc_voice_style_lab.py`, `local_model_diagnostics.py`, `provider_benchmark.py`, and `structured_output_reliability.py` call `create_llm_provider`.

Impact:

- These paths still use the factory boundary, so they do not instantiate concrete providers directly, but they do not consistently enforce `ProviderRouter` use-case selection or `ProviderSafetyPolicy`.
- This partially misses the v2.5 goal that Novel/Tavern/World/Cross-Mode/Quality obtain providers through mode-based routing.

Recommendation:

- Introduce one shared `ProviderGateway` construction path for runtime services.
- Replace direct `create_llm_provider` calls in business/helper modules with gateway/router resolution or an explicitly injected routed provider.
- Keep `create_llm_provider` as a low-level factory used by the gateway only.

Acceptance impact:

- Blocks a strict interpretation of v2.5 Provider Gateway acceptance.
- Does not currently show a direct GameState or hidden-fact leak, but it is an architecture blocker for “Provider Gateway is the only LLM entry.”

## Medium-Risk Issues

### M1. Provider Safety Policy Is Not Applied To All Factory-Based Calls

Evidence:

- `ProviderSafetyPolicy` is enforced by `ProviderRouter.resolve_provider_for_use_case`.
- Legacy direct factory paths bypass `ProviderRouter`.

Impact:

- A cloud provider could be selected by settings in a path that does not check project `local_only`, sensitive prompt flags, or mode allow/deny policy.

Recommendation:

- Require every LLM call site to provide a `ProviderRoutingContext`.
- Add regression tests that fail when production modules call `create_llm_provider` outside the gateway/factory layer.

### M2. Mode Integration Is Demonstrated But Not Fully Wired

Evidence:

- v2.5 integration tests route Novel/Tavern/World/Cross-Mode calls through `ProviderGateway.provider_for(...)`.
- Existing service constructors still accept `LLMProvider` directly and do not know their own `use_case`.

Impact:

- Correct routing depends on callers choosing the right routed provider.
- Future call sites could accidentally pass a non-routed provider.

Recommendation:

- Add thin mode-specific factory helpers, for example `gateway.provider_for_novel_draft(...)`, `gateway.provider_for_tavern_reply(...)`, `gateway.provider_for_world_intent_parse(...)`.
- Use these helpers in service construction from API/session entry points.

### M3. Explicit Real-Provider Paths Need Continued Guarding

Evidence:

- Prompt Lab benchmark/reliability/diagnostic flows contain `allow_real_provider` or equivalent opt-in flags.
- Current tests use fake/mock/local_stub and validate no real API calls.

Impact:

- This is acceptable for local authoring, but release checks must continue verifying real-provider tests are not enabled by default.

Recommendation:

- Keep real-provider calls disabled in CI and default tests.
- Add release-check assertions for `allow_real_provider=false` defaults and no real network calls.

## Low-Risk Issues

### L1. ProviderCallTrace Is Safe But Sparse

`ProviderCallTrace` records provider id, model id, use case, behavior, success, error type, and duration. It does not store prompts or outputs, which is correct. It currently does not record a normalized fallback reason enum separate from error type.

Recommendation:

- Add a safe fallback reason field later if dashboard or audit UX needs it.

### L2. Structured Output Failure Messages Are Clear But Coarse

Schema validation failures return clear categories such as `schema_validation_failed` in gateway traces. Some provider-specific errors still collapse to class names.

Recommendation:

- Add a small provider error category enum if v2.5 final acceptance wants more precise reporting.

## Specific Checks

### 1. Provider Gateway as Unique LLM Entry

Status: **Partial**

The contract and `ProviderGateway` exist, but direct factory usage remains in app modules. Concrete provider instantiation remains centralized in factory app code.

### 2. Direct Business Instantiation of Concrete Providers

Status: **Pass with test exceptions**

No app business module directly constructs `OpenAIProvider`, `OpenAICompatibleProvider`, `LocalHTTPProvider`, `LocalStubProvider`, or `MockLLMProvider` outside `provider_factory.py`. Tests instantiate concrete providers for contract coverage.

### 3. Novel/Tavern/World/CrossMode Through ProviderRouter

Status: **Partial**

Routed-provider integration is covered in v2.5 regression tests. Production entry points are not fully switched to mandatory router resolution.

### 4. Fallback Schema Validation

Status: **Pass**

`ProviderGateway.generate_json` calls `provider.generate_json(..., schema=...)` for each attempt. Fallback providers cannot bypass Pydantic schema validation through the gateway.

### 5. Fallback Prompt Safety Context

Status: **Pass in gateway path**

The gateway reuses the same `messages` payload for primary and fallback attempts. It does not rebuild or expand prompts.

### 6. Structured JSON Routing

Status: **Pass**

`ProviderRouter` marks `world_intent_parse`, `structured_json`, `cross_mode_draft`, and `quality_eval` as JSON-required and selects fallback or errors when the primary lacks JSON support.

### 7. Provider Safety Policy

Status: **Partial**

Effective in `ProviderRouter.resolve_provider_for_use_case`; not guaranteed in direct factory paths.

### 8. Provider Profiles Expanding LLM Authority

Status: **Pass**

`ProviderProfileV2` controls provider type, model metadata, routing, fallback, cost tracking, and safety policy. It does not add hidden fact access or GameState mutation authority.

### 9. PromptProfile Hidden Fact Access

Status: **Pass based on existing guards**

Prompt/profile safety checks still reject hidden fact access and state modification markers in relevant prompt-profile and prompt-lab policy code.

### 10. Hidden Facts in Provider Input

Status: **No current high-risk path found**

Novel/Tavern contexts validate safe payloads; prompt-lab tools include redaction and hidden-leak checks. The main residual risk is un-routed legacy factory paths rather than a confirmed hidden fact leak.

### 11. raw `state_deltas` in Provider Input

Status: **Pass for known v2.5 blocker**

`MemorySummarizer` now passes `state_delta_count`, not raw serialized deltas. Novel/Tavern/Cross-Mode prompt builders reject `state_delta` markers in normal prompt contexts.

### 12. Debug Memory in Provider Input

Status: **No confirmed leak found**

Tavern memory and Cross-Mode export/validation paths filter debug markers. Provider usage and benchmark reports avoid prompt logging.

### 13. LLM Output Directly Into GameState

Status: **Pass**

No inspected provider path directly applies LLM output to `GameState`. World apply remains through `StateDelta` and `EventLog`.

### 14. CrossMode Apply Calling LLM

Status: **Pass**

`TavernToWorldApplyService.apply_confirmed` is deterministic and does not call an LLM.

### 15. usage / benchmark / reliability Real API Calls

Status: **Pass for default tests**

Default tests use fake/mock/local_stub. Real-provider runs require explicit opt-in and are not used by automated tests.

### 16. Schema Failure Clarity / Fallback

Status: **Pass**

Provider and gateway paths surface clear errors for invalid JSON/schema failures, and fallback can recover where configured.

## Fix Recommendations

1. Make `ProviderGateway` the only production entry above the low-level factory.
2. Replace direct `create_llm_provider` calls in runtime modules with routed gateway helpers.
3. Require `ProviderRoutingContext` at every LLM call boundary.
4. Add a static regression test that fails on app-code `create_llm_provider` imports outside allowlisted gateway/factory modules.
5. Add release-check coverage that `allow_real_provider` defaults stay false.
6. Add safe fallback reason enum to `ProviderCallTrace` for observability.

## Acceptance Blocker Assessment

**Blocks strict v2.5 acceptance: Yes.**

Reason: v2.5 requires Provider Gateway / ProviderRouter to be the unified model
entry across Novel, Tavern, World, Cross-Mode, and Quality. The current code has
strong provider safety foundations and passing regression tests, but several
production/helper paths still call `create_llm_provider` directly and therefore
do not uniformly enforce mode-based routing and `ProviderSafetyPolicy`.

**Does this indicate immediate hidden fact or GameState mutation leakage? No.**

The audit did not find a current path where LLM output directly mutates
`GameState`, where Cross-Mode apply calls an LLM, or where raw `state_deltas`
are currently sent by the known `MemorySummarizer` path. The blocker is
architectural: routing and policy enforcement are not yet universal.

