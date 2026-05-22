# v2.5 Release Notes: Provider Gateway Pro

## 1. Version Name

v2.5 Provider Gateway Pro

## 2. Version Goal

v2.5 upgrades the local provider layer into Provider Gateway Pro: a
manageable, routable, testable, traceable, and secret-safe model access
boundary for Novel, Tavern, World, Cross-Mode, Quality, and authoring
workflows.

Provider Gateway Pro does not change world authority. Providers remain the
language/JSON layer. The World Engine remains the source of facts, and LLM
output cannot directly modify `GameState`, apply `StateDelta`, append
`EventLog`, bypass visibility, or decide Cross-Mode apply results.

## 3. New Features

- Added Provider Profile v2 schemas for provider profiles, model profiles,
  safety policy, retry metadata, fallback ids, cost hints, and mode scopes.
- Added backend-only provider secret resolution for `api_key_env` and
  `secret_ref`.
- Added local provider profile repository under project provider metadata.
- Added Provider APIs for profile management, safe validation/status,
  capability matrix, and usage summaries.
- Added Provider Profile UI, capability matrix UI, routing controls, and local
  usage dashboard.
- Added OpenAI-compatible provider support and relay-style profile support as
  generic compatible API configuration.
- Hardened local HTTP and provider factory paths for v2.5 profile/factory
  behavior.
- Added declarative capability detection and model capability matrix.
- Added mode-based routing for Novel, Tavern, World, Cross-Mode, Quality,
  structured JSON, memory summary, and cheap summary use cases.
- Added fallback chain handling with schema and safety enforcement.
- Added local token/cost estimate tracking and safe usage summaries.
- Added provider benchmark and structured-output reliability surfaces that
  default to fake/mock/local providers.
- Added provider simulation/mock harness for success, invalid JSON, schema
  mismatch, timeout, rate limit, provider error, safety rejection, and slow
  response behavior.
- Integrated routed providers with key Novel/Tavern/World/Cross-Mode paths and
  regression tests.

## 4. Behavior Changes

- Provider routing is now use-case aware.
- JSON-required use cases require JSON-capable models and fail closed if no
  valid model is available.
- Fallback providers must satisfy the same capability and safety policy checks
  as primary providers.
- `MemorySummarizer` no longer serializes raw `state_deltas` into provider
  prompt payloads; it records a `state_delta_count` instead.
- World session defaults now use a routed provider wrapper for
  `world_intent_parse` and `world_narration`.
- Tavern chat now routes default provider calls through the `tavern_reply`
  use case.

## 5. API Changes

New local project Provider APIs:

- `GET /projects/{project_id}/providers`
- `POST /projects/{project_id}/providers`
- `GET /projects/{project_id}/providers/{provider_profile_id}`
- `PATCH /projects/{project_id}/providers/{provider_profile_id}`
- `DELETE /projects/{project_id}/providers/{provider_profile_id}`
- `POST /projects/{project_id}/providers/{provider_profile_id}/validate`
- `GET /projects/{project_id}/providers/{provider_profile_id}/status`
- `POST /projects/{project_id}/providers/{provider_profile_id}/test-connection`
- `GET /projects/{project_id}/providers/capability-matrix`
- `GET /projects/{project_id}/providers/usage/recent`
- `GET /projects/{project_id}/providers/usage/summary`
- `GET /projects/{project_id}/providers/usage/by-mode`
- `GET /projects/{project_id}/providers/usage/by-provider`

Provider APIs are local authoring/studio APIs. They return safe summaries and
must not return raw API keys, authorization headers, raw env, full prompts,
full outputs, hidden facts, or provider secrets.

## 6. Frontend Changes

- Added Provider Profile management UI.
- Added provider capability matrix display.
- Added provider routing controls and routing preview surfaces.
- Added Provider Usage Dashboard with recent calls, usage by mode, usage by
  provider, estimated tokens, estimated cost, and error counts.
- Provider UI uses `api_key_env` and `secret_ref` references. It does not
  include a plaintext API key field.
- Usage dashboard displays metadata only and does not display full prompt text,
  model output text, API keys, hidden facts, raw env, or raw `state_deltas`.

## 7. ProviderProfileV2 Changes

`ProviderProfileV2` supports:

- `provider_profile_id`
- `display_name`
- `provider_type`: `openai`, `openai_compatible`, `local_http`, `relay`,
  `mock`, `local_stub`
- `base_url` / `base_url_env`
- `api_key_env` / `secret_ref`
- `model_profiles`
- `capabilities`
- `allowed_modes`
- timeout and retry settings
- fallback profile ids
- cost tracking metadata
- safety policy
- enabled/disabled state

Raw `api_key`, `llm_api_key`, and `openai_api_key` fields are rejected. Project
provider profiles must not store real API keys.

## 8. Provider Routing Changes

- Added routing use cases including `novel_draft`, `novel_rewrite`,
  `tavern_reply`, `world_intent_parse`, `world_narration`, `memory_summary`,
  `cross_mode_draft`, `quality_eval`, `structured_json`, and
  `cheap_summary`.
- Added `ProviderRoutingContext` for mode/use-case routing decisions.
- Added JSON capability enforcement for structured routes.
- Added local-only and sensitive/debug prompt policy checks.
- Added fallback selection that cannot bypass schema validation, capability
  checks, or safety policy.

## 9. Provider Safety / Secrets Changes

- API keys can only be resolved through environment variables or backend local
  secret resolver paths.
- `ProviderSecretResolver` is backend-only.
- Provider safe summaries expose configuration metadata, not secret values.
- Provider profile repository rejects raw secret-like values.
- Relay profiles are generic OpenAI-compatible profiles. They do not bind to a
  specific relay vendor, include built-in keys, implement accounts, resell API
  access, or provide online billing.
- Prompt/profile/provider settings cannot grant hidden fact access, modify
  state, override action results, or bypass visibility.

## 10. Usage / Cost Tracking Changes

- Added safe provider usage records with provider/model ids, mode, use case,
  estimated input/output/total tokens, estimated cost, duration, success, and
  error type.
- Added usage aggregation by project, mode, use case, provider, and model.
- Usage/cost tracking is local-only observability.
- Cost/token values are approximate estimates, not official bills or financial
  records.
- Usage records do not store full prompts, full outputs, API keys, raw env,
  hidden fact text, debug memory, or raw `state_deltas`.
- No telemetry upload or cloud sync is part of v2.5.

## 11. Benchmark / Reliability Changes

- Added provider benchmark CLI/API surfaces for mock/fake/local-safe checks.
- Added structured-output reliability tests for common JSON schemas.
- Added provider simulation profile behavior for success, invalid JSON, schema
  mismatch, timeout, rate limit, provider error, safety rejection, and slow
  response.
- Benchmark and structured-output reliability default to fake/mock providers.
- Real provider checks are explicit opt-in and are not CI/default test
  behavior.

Useful local commands:

```powershell
$env:PYTHONPATH="backend"
python -m app.tools.provider_benchmark --mock-only
python -m app.tools.structured_output_reliability --provider fake
```

## 12. Known Limitations

- v2.5 is not a cloud provider operations platform.
- v2.5 does not implement cloud accounts, online billing, API resale, hosted
  telemetry, or online provider sync.
- Cost/token estimates are approximate and local, not billing-grade.
- Sensitive relay URLs should prefer `base_url_env`; future hardening should
  reject more token-like `base_url` patterns.
- Prompt Lab and diagnostics keep explicit real-provider opt-in flags, but
  default tests remain fake/mock/local.
- Benchmark and structured reliability reports may include redacted prompt
  previews. They do not store full prompts, but stricter privacy deployments
  may choose to make previews debug-only.
- OpenAI provider still supports legacy `Settings.llm_api_key` behind the
  factory boundary. `ProviderProfileV2` with `api_key_env` / `secret_ref` is
  the preferred project profile path.

## 13. Upgrade Notes From v2.4

- Existing Novel, Tavern, World, and Cross-Mode data remains compatible.
- Provider profiles should use `api_key_env` or `secret_ref`, not raw API key
  values.
- Existing `LLM_PROVIDER=mock` / `local_stub` development flows remain valid.
- OpenAI-compatible and relay configurations should be modeled as provider
  profiles and should not include real key values in project files.
- Provider benchmark/reliability tests should use fake/mock/local providers by
  default.
- Usage tracking is opt-in local metadata and should be treated as estimates.
- World authority is unchanged: World facts still require deterministic World
  Engine rules, `StateDelta`, and `EventLog`.

## 14. Recommended v2.6 Direction

Recommended v2.6 theme: Script / Mod Platform Pro.

Provider Gateway Pro, Cross-Mode Bridge, Tavern Studio, Novel Studio, and the
World Engine now provide the boundaries needed for a safer script/mod layer.
Recommended v2.6 priorities:

- Safe script/mod package contracts with explicit permissions.
- Declarative plugin/module capabilities without arbitrary code execution by
  default.
- Stronger import/export policy for scripts, provider profiles, and cross-mode
  artifacts.
- Sandbox design for any future executable plugin support, disabled until
  validated.
- Unified quality/release matrix across World, Novel, Tavern, Cross-Mode,
  Provider Gateway, and Script/Mod packages.

## Verification

Release validation for v2.5:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Accepted verification:

- Backend: `1633 passed`
- Frontend build: passed
- Existing frontend build warning: Vite reports the main JS chunk is larger
  than 500 kB after minification. This is a known non-blocking warning.
