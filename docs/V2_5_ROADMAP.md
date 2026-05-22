# v2.5 Roadmap: Provider Gateway Pro

## Version Theme

Provider Gateway Pro on top of the v2.1 `NarrativeProject` layer, v2.2 Novel
Studio MVP, v2.3 Tavern Studio MVP, and v2.4 Cross-Mode Bridge.

## Current Baseline

- Runtime `ProviderFactory` currently supports `mock`, `local_stub`,
  `local_http`, and `openai`.
- `ProjectProviderProfile` already includes `openai_compatible`, but runtime
  provider construction does not yet treat it as a full first-class provider
  type.
- Usage tracking, provider benchmark tools, provider capability registry, model
  compatibility matrix, and structured-output reliability tests already exist
  as foundations.
- `MemorySummarizer` currently includes serialized `state_deltas` in provider
  prompt payloads. v2.5 must treat that as a first-priority Provider Safety
  Policy issue.

## Goal

v2.5 upgrades the existing provider factory and `LLMProvider` abstraction into a
manageable, routable, testable, traceable, and safely isolated Provider Gateway.
It must serve Novel, Tavern, World, Cross-Mode, Quality, authoring, and prompt
lab workflows without changing world authority.

Provider choice may affect wording, latency, formatting, cost, reliability, and
structured-output behavior. It must not decide facts, grant hidden access,
modify `GameState`, bypass schema validation, or weaken visibility rules.

This roadmap is a development plan, not an acceptance report.

## Explicit Non-Goals

- No cloud account system.
- No online billing.
- No API resale service.
- No real API key storage in project files.
- No API key delivery to frontend code or browser storage.
- No provider profile export containing secrets.
- No provider authority to decide world facts.
- No LLM direct mutation of `GameState`.
- No fallback model bypassing schema validation.
- No prompt-full logging by default.
- No sensitive prompt logging unless explicitly debug-enabled and redacted.
- No real provider calls in automated tests.
- No binding to a specific relay or middleman service.
- No weakening of Novel/Tavern/World/Cross-Mode boundaries.

## Recommended Development Order

1. Gateway Foundation:
   - Provider Gateway Core Contract Review.
   - Provider Profile v2 Schema.
   - Provider Secrets Boundary.
   - Provider Registry / Repository.
   - Provider Safety Policy.
2. Local Authoring API / UI:
   - Provider API.
   - Provider Profile UI.
   - Provider Usage Dashboard Backend.
   - Provider Usage Dashboard Frontend.
3. Provider Implementations:
   - OpenAI Provider Hardening.
   - OpenAI-Compatible Provider Hardening.
   - Local HTTP Provider Hardening.
   - Relay / Middleman API Profile Support.
4. Routing / Capability / Reliability:
   - Provider Capability Detection.
   - Model Capability Matrix.
   - Mode-Based Routing Rules.
   - Fallback Provider Chain.
   - Cost / Token Tracking.
   - Provider Benchmark Suite.
   - Structured Output Reliability Test.
   - Provider Simulation / Mock Harness.
5. Platform Integration / Release Hardening:
   - Provider Gateway Integration with Novel/Tavern/World.
   - Provider Gateway Integration with Cross-Mode Bridge.
   - Provider Gateway Integration Tests.

## Module Plan

### 1. Provider Gateway Core Contract Review

- Goal: define the contract boundary between `LLMProvider`, provider factory,
  provider router, Provider Gateway, usage tracking, and business modules.
- Data structures: contract notes, provider call request/response envelope,
  provider error category, provider use-case enum, routing context.
- API changes: none required in this slice, but future APIs must expose only
  safe summaries and routing previews.
- Frontend changes: none required in this slice.
- Tests: static regression checks for forbidden concrete provider instantiation
  in business modules, schema validation for provider call envelopes.
- Acceptance: business modules depend on gateway/router/`LLMProvider`, not
  concrete provider classes or vendor SDKs.

### 2. Provider Profile v2 Schema

- Goal: define provider and model profile contracts that are safe to store in a
  project workspace.
- Data structures: `ProviderProfileV2`, `ProviderModelProfileV2`,
  `ProviderSecretRef`, `ProviderModeScope`, `ProviderCapabilityRef`,
  `ProviderRoutingTag`.
- API changes: profile create/update endpoints consume v2 schemas and return
  safe summaries.
- Frontend changes: editor fields for provider type, model id, mode scopes,
  capability refs, routing tags, and secret refs.
- Tests: JSON serialization, secret-like value rejection, safe summary
  redaction, import/export redaction.
- Acceptance: profiles are serializable and useful for routing, but never store
  raw API keys.

### 3. Provider Secrets Boundary

- Goal: centralize rules for API keys, relay tokens, header secrets, base URL
  sensitivity, env refs, and local secret refs.
- Data structures: `ProviderSecretPolicy`, `ProviderSecretValidationReport`,
  redaction result, safe secret reference summary.
- API changes: profile and diagnostic APIs reject raw secrets and return
  redacted validation reports.
- Frontend changes: UI only accepts env var names or local secret refs; it never
  asks users to paste raw keys into project files.
- Tests: raw `sk-...`, bearer tokens, private keys, database URLs, raw env
  values, and provider secrets are rejected or redacted.
- Acceptance: API keys and provider secrets can only be resolved from
  environment variables or a future local secret store.

### 4. Provider Registry / Repository

- Goal: persist provider profiles, model profiles, routing policies, benchmark
  metadata, and non-sensitive capability metadata locally.
- Data structures: `ProviderRegistry`, `ProviderRegistryRepository`,
  provider/model index records, routing policy refs.
- API changes: repository-backed APIs for list/load/save/update/delete profile
  metadata.
- Frontend changes: provider profile list and local registry status.
- Tests: save/load/list, stable ordering, path traversal rejection, repository
  does not read `.env`, databases, logs, cache, `node_modules`, `dist`, backups,
  crash reports, or desktop outputs.
- Acceptance: provider metadata is local, deterministic, and secret-safe.

### 5. Provider API

- Goal: expose local authoring/studio provider management routes.
- Data structures: create/update requests, safe profile response, routing
  preview response, diagnostics response.
- API changes: routes for profiles, model profiles, safe summaries, capability
  queries, config validation, and routing preview.
- Frontend changes: consumes provider management APIs and handles disabled
  authoring/provider APIs safely.
- Tests: enabled/disabled behavior, missing profile errors, secret redaction,
  no raw env or API key in responses.
- Acceptance: Provider APIs are local authoring/studio APIs and are safe for
  frontend consumption.

### 6. Provider Profile UI

- Goal: provide a local UI for managing provider profiles and safe summaries.
- Data structures: frontend provider profile, model profile, safe summary,
  validation issue, routing preview.
- API changes: none beyond Provider API consumption.
- Frontend changes: provider list, create/edit form, capability/status panel,
  routing preview, safe secret ref hints.
- Tests: frontend build, empty state, disabled API state, validation issue
  display, no API key or raw env shown, no browser secret storage.
- Acceptance: users can configure provider metadata without exposing secrets.

### 7. OpenAI Provider Hardening

- Goal: harden OpenAI provider initialization, errors, timeouts, structured
  output validation, and usage metadata.
- Data structures: OpenAI provider config, safe error category, request timeout
  policy, usage metadata.
- API changes: diagnostics route can report configured/not configured status,
  not raw credentials.
- Frontend changes: safe status display only.
- Tests: missing env key fails clearly, vendor errors are redacted, JSON output
  must validate, no real API calls in default tests.
- Acceptance: OpenAI provider is reliable and secret-safe when explicitly
  configured.

### 8. OpenAI-Compatible Provider Hardening

- Goal: make `openai_compatible` a first-class runtime provider type instead of
  only a profile-level concept.
- Data structures: OpenAI-compatible config, base URL ref, optional header
  secret refs, model compatibility metadata.
- API changes: profile/routing/diagnostic APIs accept and preview
  `openai_compatible` directly.
- Frontend changes: UI can configure OpenAI-compatible endpoints without naming
  or depending on a specific relay service.
- Tests: local fake compatible server, schema validation, timeout handling,
  redacted URL/secret behavior, no external network in tests.
- Acceptance: compatible providers work through the same gateway boundary as
  first-party providers.

### 9. Local HTTP Provider Hardening

- Goal: strengthen local model endpoint support for diagnostics, timeouts,
  error reporting, and structured output.
- Data structures: local HTTP config, health check result, response parse
  result, JSON extraction diagnostics.
- API changes: local provider diagnostic and health routes return safe
  summaries.
- Frontend changes: local provider status and troubleshooting hints.
- Tests: fake local server success/failure, malformed JSON, non-JSON response,
  timeout, schema validation.
- Acceptance: local models are testable and diagnosable without weakening
  provider safety.

### 10. Relay / Middleman API Profile Support

- Goal: support relay-style APIs through OpenAI-compatible profiles without
  becoming an API resale service.
- Data structures: relay profile metadata, header secret refs, base URL ref,
  provider display label, relay safety notes.
- API changes: profile validation recognizes relay-compatible configuration
  but stores only refs and safe metadata.
- Frontend changes: relay profile form uses generic OpenAI-compatible fields.
- Tests: raw relay token rejection, secret ref acceptance, safe export, no
  provider-specific hardcoding.
- Acceptance: relay support is generic, local, secret-safe, and not tied to a
  specific middleman service.

### 11. Provider Capability Detection

- Goal: detect or declare model/provider capabilities that affect routing and
  reliability.
- Data structures: `ProviderCapabilityDetectionRequest`,
  `ProviderCapabilityDetectionResult`, capability confidence, detection source.
- API changes: capability detection endpoint with fake/local-only default.
- Frontend changes: capability status panel with detected/manual labels.
- Tests: detection success/failure, safe fallback, no real provider calls by
  default.
- Acceptance: capabilities inform routing but do not grant new security
  authority.

### 12. Model Capability Matrix

- Goal: unify declared capabilities, detection results, benchmark results,
  structured-output reliability, and usage metadata.
- Data structures: model capability matrix row, compatibility score,
  reliability score, cost estimate, advisory warnings.
- API changes: matrix endpoint and filtered views by mode/use-case.
- Frontend changes: matrix table for provider/model comparison.
- Tests: matrix aggregation, missing data behavior, advisory-only semantics.
- Acceptance: the matrix helps selection but never decides world facts or
  bypasses validation.

### 13. Mode-Based Routing Rules

- Goal: route provider calls by mode and use case: Novel, Tavern, World,
  Cross-Mode, Quality, authoring, prompt lab, diagnostics.
- Data structures: `ProviderRoutingRuleV2`, `ProviderRoutingContext`,
  `ProviderRouteDecision`, priority and fallback refs.
- API changes: routing preview endpoint and route decision summaries.
- Frontend changes: routing rule editor and preview.
- Tests: correct provider selected by mode/use-case, disabled/missing providers
  produce clear failure, no direct provider construction by business modules.
- Acceptance: Novel/Tavern/World/Cross-Mode calls obtain providers through
  Gateway routing.

### 14. Fallback Provider Chain

- Goal: define safe fallback behavior for provider failures without relaxing
  schema, prompt, visibility, or mode boundaries.
- Data structures: fallback chain, failure category, fallback decision,
  fallback audit record.
- API changes: routing preview and usage APIs include fallback metadata.
- Frontend changes: visible fallback chain status and recent fallback reasons.
- Tests: primary failure uses fallback, fallback schema failure still fails,
  fallback does not receive hidden/raw forbidden context.
- Acceptance: fallback improves reliability but cannot bypass validation or
  safety policy.

### 15. Cost / Token Tracking

- Goal: track usage metadata without storing secrets or sensitive prompt text.
- Data structures: provider usage record v2, token estimate, cost estimate,
  latency, mode/use-case, error category, redaction marker.
- API changes: usage summary/recent/by-mode/by-provider endpoints.
- Frontend changes: usage dashboard consumes safe usage summaries.
- Tests: usage records exclude API key, raw env, full sensitive prompt, hidden
  text, raw `state_deltas`, and debug memory.
- Acceptance: usage logging is useful for local authoring and safe by default.

### 16. Provider Usage Dashboard Backend

- Goal: provide backend summary services for provider usage, costs, latency,
  failures, fallback rates, and structured-output reliability.
- Data structures: usage dashboard summary, provider breakdown, mode breakdown,
  error/fallback breakdown.
- API changes: dashboard endpoints gated by debug/usage configuration.
- Frontend changes: none required in this slice.
- Tests: API disabled behavior, safe summaries, filtering, no prompt/key leaks.
- Acceptance: usage dashboard data is safe, local, and configurable.

### 17. Provider Usage Dashboard Frontend

- Goal: display provider usage and reliability without exposing sensitive
  prompts or secrets.
- Data structures: frontend usage summary, provider row, mode row, error row.
- API changes: none beyond dashboard backend.
- Frontend changes: charts/tables for calls, latency, cost estimate, errors,
  fallback, and mode distribution.
- Tests: frontend build, empty state, disabled API state, no secret/raw prompt
  display.
- Acceptance: local users can inspect provider health and usage safely.

### 18. Provider Benchmark Suite

- Goal: run deterministic provider benchmarks for latency, reliability, JSON
  compliance, and redaction behavior.
- Data structures: benchmark case, benchmark run, benchmark result,
  provider/model score.
- API changes: optional local benchmark API or CLI, gated and fake/local by
  default.
- Frontend changes: benchmark results may feed usage/capability dashboard.
- Tests: fake/local_stub benchmark runs, real provider tests skipped unless
  explicitly opted in.
- Acceptance: benchmark suite is deterministic and does not call real APIs in
  normal CI.

### 19. Structured Output Reliability Test

- Goal: harden `generate_json` behavior across providers, retries, fallback,
  invalid JSON, schema mismatch, and hidden leak sentinel cases.
- Data structures: structured-output test case, retry result, schema validation
  issue, reliability summary.
- API changes: reliability report endpoint or CLI summary.
- Frontend changes: optional report panel in provider dashboard.
- Tests: invalid JSON rejected, schema mismatch rejected, fallback revalidates,
  hidden sentinel output fails safely.
- Acceptance: every `generate_json` result is schema-validated before use.

### 20. Provider Safety Policy

- Goal: enforce prompt and payload safety before any provider call.
- Data structures: `ProviderPromptSafetyPolicy`, `ProviderPromptSafetyReport`,
  forbidden content category, redacted prompt summary.
- API changes: route decision and diagnostic APIs can return safe policy
  failures.
- Frontend changes: user-visible safe error messages for blocked provider calls.
- Tests: hidden facts, raw `state_deltas`, debug memory, API keys, raw env, and
  provider secrets are blocked from provider payloads.
- Acceptance: `MemorySummarizer` and other provider paths no longer send raw
  `state_deltas` to providers.

### 21. Provider Simulation / Mock Harness

- Goal: standardize fake/mock/local_stub provider testing across all modes.
- Data structures: simulation scenario, fake response queue, forced error,
  latency simulation, leak simulation.
- API changes: no production API required; test harness may expose helpers.
- Frontend changes: none required.
- Tests: Novel/Tavern/World/Cross-Mode can run with fake/local providers,
  including failure and fallback simulations.
- Acceptance: integration tests do not depend on real providers or network.

### 22. Provider Gateway Integration with Novel/Tavern/World

- Goal: connect Novel draft generation, Tavern response generation, World
  narrator/intent parsing, and memory summarization to mode-based Gateway
  routing.
- Data structures: mode-specific provider use-case constants, route decision
  records, safe prompt summaries.
- API changes: mode services may accept routing context instead of concrete
  provider instances.
- Frontend changes: mode UIs may show safe selected provider summaries.
- Tests: each mode uses Gateway routing, no direct concrete provider
  instantiation, no `GameState` authority expansion.
- Acceptance: Provider Gateway becomes the model entrypoint for the three-mode
  platform.

### 23. Provider Gateway Integration with Cross-Mode Bridge

- Goal: ensure cross-mode draft/proposal generation, validation assistance,
  quality checks, and summaries use Provider Gateway safely when they need an
  LLM.
- Data structures: cross-mode provider routing context, proposal generation
  use-case, safe source-context summary.
- API changes: cross-mode services request providers by mode/use-case through
  Gateway.
- Frontend changes: cross-mode review panels may show safe selected provider
  summaries.
- Tests: LLM can only generate draft/proposal text, cannot decide apply, cannot
  access hidden/raw forbidden payloads.
- Acceptance: cross-mode LLM use remains language-layer only.

### 24. Provider Gateway Integration Tests

- Goal: verify Provider Gateway Pro works across profile storage, routing,
  fallback, usage, safety, frontend, and mode integration.
- Data structures: integration fixtures, fake provider scenarios, profile
  fixtures, routing fixtures.
- API changes: none beyond implemented APIs.
- Frontend changes: build verification for Provider Profile UI and Usage
  Dashboard.
- Tests: full backend suite, frontend build, no real API calls, no secret
  leaks, no forbidden prompt payloads.
- Acceptance: `python -m pytest` and `cd frontend && npm.cmd run build` pass.

## Impact On Novel Studio

- Novel draft generation must obtain providers through mode-based Gateway
  routing.
- Novel prompt contexts must pass Provider Safety Policy before generation.
- Fallback providers must not receive hidden facts, private notes, raw
  `state_deltas`, or provider secrets.
- Novel exports and reports must continue excluding provider secrets and hidden
  content.

## Impact On Tavern Studio

- Tavern response generation must use Gateway routing and safe provider
  summaries.
- Tavern prompt contexts must exclude NPC unknown facts, private persona,
  hidden lore, debug memory, raw `state_deltas`, API keys, and provider secrets.
- Relationship tone, scene mood, RP profile, and voice profile remain
  style/context inputs only; providers cannot turn them into world authority.

## Impact On World Mode / GameState

- World Mode remains the only runtime fact engine.
- Provider Gateway does not change the rule that all state changes go through
  `StateDelta` and relevant `EventLog` entries.
- Intent parsing, narration, and memory summarization may use providers, but
  outputs must remain schema-validated language-layer artifacts.
- Provider selection, fallback, model capabilities, and costs cannot alter
  action resolution or visibility.

## Impact On Cross-Mode Bridge

- Cross-mode LLM use remains limited to summaries, suggestions, drafts, and
  proposal candidates.
- Gateway routing may choose different models by cross-mode use case, but apply
  decisions remain validation + explicit confirmation + World Engine logic.
- Cross-mode artifacts must not store provider secrets, raw prompts, hidden
  text, or raw `state_deltas`.

## LLM Boundary Impact

- Provider Gateway is the only model entrypoint.
- Business modules must not instantiate concrete providers directly.
- All `generate_json` outputs must pass schema validation before use.
- Fallback providers must enforce the same schema, prompt safety, visibility,
  and mode boundaries as primary providers.
- Providers cannot grant hidden fact access, modify state, decide proposal
  apply, or bypass quality gates.

## API Key / Provider Secret / Usage Logging Risks

- API keys must only come from env vars or future local secret refs.
- Provider profiles may store `api_key_env` or `secret_ref`, never raw key
  values.
- Base URLs for private relays may be sensitive metadata; normal summaries and
  exports should redact them or use refs where appropriate.
- Usage records must not store raw env, API keys, provider secrets, hidden
  facts, debug memory, raw `state_deltas`, or full sensitive prompts.
- Debug prompt capture, if ever enabled, must be explicit, local, gated,
  redacted, and excluded from normal exports.

## v2.5 Integration Test Requirements

- Provider profile schema accepts safe refs and rejects raw secrets.
- Provider repository rejects path traversal and forbidden files.
- Provider API disabled state is safe and clear.
- Provider Profile UI and Usage Dashboard build successfully.
- OpenAI, OpenAI-compatible, local HTTP, mock, and local_stub paths are covered
  with fake/local tests.
- Mode-based routing works for Novel, Tavern, World, Cross-Mode, Quality, and
  prompt lab use cases.
- Fallback chains re-run schema validation and safety checks.
- Hidden facts, raw `state_deltas`, debug memory, raw env, API keys, and
  provider secrets do not enter provider prompts or usage logs.
- Usage summaries include safe metadata only.
- Benchmark and structured-output reliability tests do not call real APIs by
  default.
- Final commands:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

## v2.5 Final Acceptance Criteria

- Provider Gateway is the documented and tested model entrypoint for the local
  three-mode platform.
- Runtime provider support includes a coherent story for `mock`, `local_stub`,
  `local_http`, `openai`, and `openai_compatible`.
- Provider profiles, APIs, frontend, import/export, logs, usage records, and
  tests do not leak API keys or provider secrets.
- Novel/Tavern/World/Cross-Mode provider calls use mode-based routing.
- All JSON provider outputs are schema-validated.
- Fallback providers do not bypass schema validation, visibility, prompt safety,
  or mode boundaries.
- Provider Safety Policy prevents hidden facts, raw `state_deltas`, debug
  memory, API keys, and provider secrets from entering provider prompts.
- No automated test calls a real external provider.
- Full backend test suite and frontend build pass.

## v2.6 Candidate Directions

- Script / Mod Platform Pro: safer script package contracts, declarative plugin
  metadata, Action Mod authoring, and sandbox policy foundations.
- Quality Studio Pro: unified quality dashboards across Novel, Tavern, World,
  Provider Gateway, Cross-Mode Bridge, compatibility, and release automation.

Recommended default: after Provider Gateway Pro, prioritize Script / Mod
Platform Pro because provider routing, prompt safety, capability metadata, and
cross-mode boundaries are prerequisites for a safer extension platform.
