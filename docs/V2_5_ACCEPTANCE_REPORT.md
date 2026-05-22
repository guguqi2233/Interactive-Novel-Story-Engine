# v2.5 Acceptance Report: Provider Gateway Pro

## Verdict

Accepted with known limitations.

v2.5 Provider Gateway Pro is accepted as a local provider management, routing,
fallback, capability, usage-estimate, benchmark, reliability, and safety layer
for Novel, Tavern, World, Cross-Mode, Quality, and authoring workflows.

The release preserves the project boundary: providers remain a language/JSON
layer only. They do not decide world facts, apply proposals, modify
`GameState`, append `EventLog`, bypass visibility, or receive hidden facts, raw
`state_deltas`, debug memory, API keys, raw env, or provider secrets in normal
contexts.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Verification results:

- Backend: `1633 passed in 95.77s`
- Frontend: `npm.cmd run build` passed
- Frontend note: Vite reported the existing chunk-size warning for the main JS
  bundle. This is not a functional failure.

## Scope Accepted

Accepted v2.5 modules:

1. Provider Gateway Core Contract Review.
2. Provider Profile v2 Schema.
3. Provider Secrets Boundary.
4. Provider Registry / Repository.
5. Provider API.
6. Provider Profile UI.
7. OpenAI Provider Hardening.
8. OpenAI-Compatible Provider Hardening.
9. Local HTTP Provider Hardening.
10. Relay / Middleman API Profile Support.
11. Provider Capability Detection.
12. Model Capability Matrix.
13. Mode-Based Routing Rules.
14. Fallback Provider Chain.
15. Cost / Token Tracking.
16. Provider Usage Dashboard Backend.
17. Provider Usage Dashboard Frontend.
18. Provider Benchmark Suite.
19. Structured Output Reliability Test.
20. Provider Safety Policy.
21. Provider Simulation / Mock Harness.
22. Provider Gateway Integration with Novel/Tavern/World.
23. Provider Gateway Integration with Cross-Mode Bridge.
24. Provider Gateway Integration Tests.

Accepted public surfaces:

- Provider profile APIs under `/projects/{project_id}/providers...`.
- Provider capability matrix API.
- Provider usage recent/summary/by-mode/by-provider APIs.
- Provider Profile UI, capability matrix UI, routing controls, and usage
  dashboard.
- Mock-only provider benchmark CLI:
  `python -m app.tools.provider_benchmark --mock-only` with
  `PYTHONPATH=backend`.
- Structured output reliability CLI:
  `python -m app.tools.structured_output_reliability --provider fake` with
  `PYTHONPATH=backend`.

## Boundary Review

### Provider Contract

- `LLMProvider` remains the common text/JSON provider contract.
- `generate_json` output is schema-validated before use.
- Provider errors are normalized into clear `LLMProviderError` categories in
  provider/gateway paths.
- Concrete provider construction remains behind provider factory/gateway
  boundaries. Tests may instantiate concrete providers for contract coverage.

### Provider Profile / Secrets

- `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and
  `openai_api_key` fields.
- Profiles store `api_key_env` / `secret_ref` references rather than raw keys.
- `ProviderSecretResolver` resolves secrets server-side only.
- Provider APIs and frontend views return safe summaries and do not return raw
  API keys, authorization headers, raw env, or provider secrets.
- Project export safety checks cover provider secret leakage. Remaining
  caution: token-like `base_url` values should prefer `base_url_env`.

### Provider API / UI

- Provider API supports profile list/create/get/patch/delete, validation,
  status, dry-run test connection, capability matrix, and safe usage summaries.
- Provider UI supports safe profile management, `api_key_env` / `secret_ref`
  fields, capability matrix, routing controls, and usage dashboard.
- No plaintext API key field is part of the frontend provider UI.

### Provider Implementations

- OpenAI provider remains behind the provider factory boundary and fails
  clearly when a key is missing.
- OpenAI-compatible provider supports `base_url` / `base_url_env`,
  `api_key_env` / `secret_ref`, fake transport tests, text generation, and
  schema-validated JSON.
- Local HTTP provider supports fake transport tests and does not require a real
  local model service in automated tests.
- Relay is a generic OpenAI-compatible profile variant. It does not bind to a
  specific relay vendor, include third-party keys, resell APIs, or implement
  billing.

### Capabilities / Routing / Fallback

- Capability detection and model capability matrix are metadata-only and do
  not call providers.
- Mode-based routing covers Novel, Tavern, World, Cross-Mode, Quality,
  structured JSON, memory summary, and cheap summary use cases.
- JSON-required use cases require JSON-capable providers. Default routing
  fails closed if no JSON-capable model is available.
- Fallback chains reuse the same safe prompt payload and schema validation.
- Fallback providers must satisfy the same capability and safety policy checks
  as the primary provider.

### Usage / Cost / Privacy

- Usage records are metadata-only: provider/model ids, mode, use case, token
  estimates, cost estimates, duration, success, and error type.
- Usage records do not store full prompts, full outputs, API keys, raw env,
  hidden facts, debug memory, or raw `state_deltas`.
- Cost values are approximate local estimates, not billing records.
- Usage dashboard displays safe summaries only.
- No telemetry upload or cloud sync of provider usage data was identified.

### Benchmark / Reliability / Safety

- Provider benchmark defaults to fake/mock/local-safe execution.
- Structured-output reliability runs with fake/mock providers by default.
- Real provider tests are explicit opt-in and are not default test behavior.
- Provider safety policy enforces mode allow/deny, sensitive prompt, debug
  prompt, logging defaults, redaction, and local-only constraints.
- Local-only project routing rejects cloud providers unless an explicit
  external override path is supplied.

### Mode Integration

- Novel draft generation can be routed through `ProviderGateway` with
  `novel_draft`.
- Tavern response generation is routed through `ProviderGateway` with
  `tavern_reply`.
- World session defaults now use a routed provider for `world_intent_parse`
  and `world_narration`.
- Cross-Mode draft/proposal helpers can use `cross_mode_draft` or
  `structured_json`; apply, validation, import/export, conflict detection, and
  quality gates remain deterministic and LLM-free.
- CrossMode apply does not call an LLM to decide results.

### World Boundary

- World Engine remains the fact source.
- Providers cannot apply `StateDelta`.
- Providers cannot append `EventLog`.
- Providers cannot directly mutate `GameState`.
- Provider selection changes expression, latency, reliability, and cost
  metadata only.
- Hidden facts, debug memory, and raw `state_deltas` are excluded from normal
  provider prompts.

## Known Limitations

1. Provider Gateway Pro is local-first. It does not implement cloud accounts,
   online billing, API resale, hosted provider management, or online provider
   telemetry.
2. Cost/token tracking is approximate and local. It is not billing-grade and
   should not be used as a financial source of truth.
3. `base_url` can be stored in provider profiles for local/compatible
   endpoints. Sensitive relay URLs should use `base_url_env`; future validation
   should reject more token-like URL patterns.
4. Prompt Lab and diagnostic tools retain explicit real-provider opt-in flags.
   Defaults and tests remain fake/mock/local, but release checks should keep
   verifying that real providers are never called by default.
5. Benchmark and structured reliability reports may include redacted prompt
   previews. They do not store full prompts, but stricter privacy policies may
   choose to make previews debug-only.
6. OpenAI provider still supports legacy `Settings.llm_api_key` configuration
   behind the factory boundary. ProviderProfileV2 / `ProviderSecretResolver`
   is the preferred v2.5 project profile path.

## Acceptance Risks

- No high-risk acceptance blocker remains after the v2.5 blocker fixes.
- Medium residual risk: token-like `base_url` values in project provider
  profile files need stronger validation in a future hardening pass.
- Medium residual risk: explicit real-provider opt-in paths must stay out of
  CI/default tests.
- Low residual risk: usage dashboard displays estimates and should continue to
  label them as estimates rather than bills.

## Recommended v2.6 Priorities

Recommended theme: Script / Mod Platform Pro.

Suggested priorities:

1. Safe script/mod package contracts with explicit permissions.
2. Declarative plugin/module capabilities without arbitrary code execution by
   default.
3. Stronger import/export policy for scripts, provider profiles, and
   cross-mode artifacts.
4. Sandbox design for any future executable plugin support, disabled until
   validated.
5. Unified release-quality matrix across World, Novel, Tavern, Cross-Mode,
   Provider Gateway, and Script/Mod packages.
6. Optional follow-up hardening for Provider Gateway: stricter token-like
   `base_url` validation, debug-only prompt previews, and richer safe provider
   error categories.

## Final Status

v2.5 Provider Gateway Pro is accepted.

Final status:

- Backend tests: passed.
- Frontend build: passed.
- Provider secrets: no raw key storage or frontend exposure found in accepted
  paths.
- Provider routing/fallback: accepted with schema and safety enforcement.
- Usage/cost privacy: accepted as local metadata-only observability.
- World authority: unchanged; providers remain language/JSON assistants only.
