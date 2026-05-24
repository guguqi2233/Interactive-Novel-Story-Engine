# v3.6 Provider Performance / Secret Safety Audit

Verification date: 2026-05-24

## Verdict

v3.6 Provider Performance / Secret Safety audit is **not blocked**.

Provider performance work remains safe-summary based. Provider model list
windowing renders local `ModelProfile` metadata, connection status cache stores
only allowlisted status fields, capability matrix optimization uses safe
provider/model summaries, and Provider Gateway routing semantics are unchanged.
No API key, transient key, Authorization header, raw provider response, raw
prompt, or raw output storage path was found in the reviewed Provider
performance changes.

## Verification Commands

```powershell
python -m pytest
```

Result: `1783 passed in 114.40s`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed. Relevant build output:

- `assets/studio-provider-ui-D7VMkStf.js`: `52.25 kB`, gzip `14.31 kB`.
- `assets/App-BBc0cBc4.js`: `445.81 kB`, gzip `107.20 kB`.
- No Vite `>500 kB` chunk warning was emitted.

Reviewed implementation and test evidence:

- `backend/app/llm/provider_profiles.py`
- `backend/app/llm/provider_connection_test.py`
- `backend/app/llm/provider_connection_cache.py`
- `backend/app/llm/provider_model_discovery.py`
- `backend/app/llm/provider_model_assignment.py`
- `backend/app/llm/provider_gateway.py`
- `backend/app/llm/provider_redaction.py`
- `frontend/src/providerUi.tsx`
- `frontend/src/safeApiCache.ts`
- `backend/tests/test_v35_provider_connection_test_backend.py`
- `backend/tests/test_v35_provider_model_discovery_sync.py`
- `backend/tests/test_v35_provider_redaction.py`
- `backend/tests/test_v35_provider_model_assignment.py`
- `backend/tests/test_v36_provider_connection_status_cache.py`
- `backend/tests/test_v36_integration_regression.py`

## Passed Items

1. Provider model list virtualization does not save secrets.
   The Provider Connectivity UI renders windowed `ModelProfile` metadata via
   `data-windowed-provider-model-list`, search/filter controls, and capability
   badges. It does not render raw provider responses, Authorization headers, or
   API key values.

2. Provider connection status cache does not save API keys.
   `ProviderConnectionStatusCacheEntry` only allows `provider_profile_id`,
   `status`, `tested_at`, `latency_ms`, `safe_error_type`, `model_count`, and
   `redaction_applied`.

3. `transient_api_key` does not enter cache.
   `ProviderConnectionStatusCache` excludes transient key payload fields and
   tests assert transient fake keys are absent from API responses and cache
   files after manual refresh.

4. `transient_api_key` does not enter logs.
   Provider redaction tests cover log entries containing transient key markers,
   Authorization headers, provider raw responses, and fake key-shaped strings;
   safe log output redacts them.

5. `transient_api_key` does not enter diagnostics.
   Diagnostics tests cover provider raw response and Authorization-like content
   in local logs and verify diagnostics output excludes those values.

6. `transient_api_key` does not enter backup/export.
   Reviewed Provider persistence paths save `ProviderProfileV2`,
   `ModelProfile`, routing config, and safe connection cache metadata only. No
   backup/export path reviewed stores transient key fields, and diagnostics /
   export exclusion policy continues to reject provider secrets by default.

7. Model list cache does not save raw provider response.
   Model discovery converts provider payloads into `ModelProfile` metadata.
   `frontend/src/safeApiCache.ts` rejects `raw_provider_response`,
   `raw_provider_error`, Authorization, raw prompt/output, hidden facts, NPC
   secrets, and state-delta-like payloads before storage.

8. Provider error cache is redacted.
   `ProviderRedactionService` covers OpenAI-style keys, Authorization Bearer
   headers, relay tokens, `secret_ref`, `transient_api_key`, token-like
   query/path segments, and raw provider response/error text.

9. Slow provider warning does not show raw error.
   Slow-provider UI is driven by latency, timeout, error-rate, model-list-slow,
   and safe usage/status summaries. It explicitly avoids raw provider errors,
   prompts, outputs, API keys, and Authorization headers.

10. Capability matrix does not display provider secrets.
    Capability matrix rendering is based on local provider/model capability
    safe summaries, filters, grouped rows, and warnings. It does not render raw
    provider metadata or secret fields.

11. Model assignment UI does not display API keys.
    Model assignment uses provider ids, model ids, fallback chains, and
    capability warnings. It validates routing through `ProviderRouter` /
    `ProviderRoutingConfig` and does not expose plaintext key fields.

12. `ProviderProfileV2` only saves `api_key_env` / `secret_ref`.
    Validators reject raw API key fields and secret-looking values. Safe
    summaries show `secret_ref` as `[configured]` rather than the stored local
    reference value.

13. Tests do not call real providers.
    Connection tests and model discovery use fake clients. CI-facing tests use
    `mock`, `local_stub`, or deterministic fake provider clients and do not
    perform real provider networking.

14. Fake provider tests cover model list and status cache.
    v3.5 provider model discovery tests cover fake OpenAI-compatible model
    lists, unsupported model-list status, sync to `ModelProfile`, manual model
    add, and transient key exclusion. v3.6 cache tests cover save/load, stale
    status, allowed fields, manual refresh, and transient key exclusion.

15. Provider performance optimization does not change routing semantics.
    v3.6 adds UI windowing, safe cache display, stale indicators, and manual
    refresh behavior. Provider Gateway, ProviderRouter, fallback chain
    resolution, and model assignment validation semantics are not changed.

16. Relay/custom provider remains local configuration, not API resale.
    Reviewed docs and UI wording describe relay/custom as OpenAI-compatible or
    custom base URL configuration. No API resale service, account flow, cloud
    service, or specific relay vendor entry point was found in this audit.

17. CI has no real networking test requirement.
    The full pytest run passed using local/fake provider paths. No test in the
    reviewed Provider connection/model discovery/cache set requires a real
    OpenAI, relay, custom, or local_http network endpoint.

## Provider Performance Improvements

- Provider UI is split into `studio-provider-ui` and no longer inflates the
  main App chunk beyond the Vite warning threshold.
- Provider model lists use search, capability filters, enabled/disabled
  filters, recommended-use-case filters, memoized capability badges, and
  windowed rendering.
- Provider connection status uses safe local cache metadata with TTL/stale
  display and manual refresh, avoiding automatic repeated connection tests when
  opening the UI.
- Capability matrix uses safe summaries, filters, grouping/windowing, and
  memoized capability warning calculations.
- Slow provider warnings rely on safe latency/timeout/error-rate summaries
  rather than raw provider response text.
- Provider usage / cost dashboard remains local and uses estimated token/cost
  summaries without prompt/output full text.

## Secret Redaction Review

- `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and
  `openai_api_key` fields.
- `api_key_env` and `base_url_env` are validated as environment variable names,
  not secret values.
- `secret_ref` is constrained to a safe local reference pattern and rejects
  key-like, Authorization-like, token-like, and URL-secret-like values.
- `ProviderSecretResolver` resolves secrets at call time from environment or a
  local resolver; it does not persist resolved values into project files.
- `ProviderConnectionTestRequest.transient_api_key` is `repr=False` and is
  used only for the immediate fake/safe test call path.
- `ProviderRedactionService` redacts API-key-shaped strings, Authorization
  Bearer headers, relay tokens, secret assignments, tokenized URLs, path token
  segments, and raw provider response/error labels.
- Provider connection and model discovery responses return safe statuses such
  as `missing_secret`, `auth_failed`, `timeout`, `model_list_failed`, and
  `unsupported_model_list` without raw provider error bodies.
- Frontend Provider UI shows key configuration status and env/ref fields, not
  key values. No plaintext `api_key` input was found in the reviewed Provider
  UI paths.

## Cache Safety Review

- Backend connection status cache is a project-local JSON cache with an
  allowlisted schema. It does not store `safe_message`, Authorization headers,
  raw provider responses, raw error bodies, API keys, or transient keys.
- Frontend safe API cache is an in-memory `Map`; it does not use
  `localStorage`, `sessionStorage`, IndexedDB, service workers, or cloud cache.
- Frontend safe API cache rejects serialized payloads containing API keys,
  `transient_api_key`, provider secrets, raw env, raw provider response/error,
  raw prompt/output, hidden facts, NPC secrets, raw state deltas, raw GameState,
  debug memory, or mature/private markers.
- Provider model list cache stores safe summaries derived from
  `ProviderProfileV2.safe_summary`, `ModelProfile`, and capability matrix safe
  rows. It does not cache raw provider model-list responses.
- Cache stale state is visible and manual refresh is explicit. v3.6 does not add
  background provider polling or automatic networking.

## High-risk Provider Secret Issues

None found.

No high-risk Provider secret issue blocks v3.6 release.

## Medium-risk Provider Issues

1. Provider performance checks are mostly static or structural.
   Current checks verify windowing markers, safe cache code, cache schema, and
   provider UI source constraints. They do not run browser-level performance
   benchmarks with thousands of fake models.

2. Provider-supplied model ids/display names remain user-visible metadata.
   These are expected `ModelProfile` fields, but unusual provider model names
   could be noisy. They are not secrets by default; v3.7 can add stronger
   display-name normalization and truncation if needed.

3. Provider status cache field safety depends on continued allowlisting.
   The current schema is safe. Future cache fields should be rejected unless
   explicitly reviewed for secret, raw response, and routing-semantics impact.

4. Diagnostics/backup/export safety depends on continued redaction service use.
   Current tests cover provider logs and diagnostics. Future provider debug
   export additions should continue to use `ProviderRedactionService` and
   default exclusions.

5. Active route parity remains a separate v3.6 UI verification concern.
   This audit did not find a Provider secret leak, but any lazy route or
   Provider UI navigation changes should still be verified by the broader
   v3.6 route/accessibility audits before final release.

## Non-blocking Follow-ups

- Add a browser-level fake large model list rendering benchmark for Provider
  Connectivity Dashboard.
- Add a diagnostics fixture that includes provider status cache and model
  profile files to verify archive redaction/exclusion end to end.
- Add a route-level Provider UI smoke test that opens Connectivity, Model
  Assignment, Usage, and Prompt/Provider settings after lazy loading.
- Add stricter display-name normalization for provider-supplied model metadata
  if noisy local provider endpoints become common.
- Add an explicit routing regression proving cache reads never influence
  ProviderRouter selection, only UI status/stale display.

## Release Decision

v3.6 release is **not blocked** by Provider performance or Provider secret
safety issues.

Proceed with v3.6 release preparation if the broader performance,
accessibility, privacy/visibility, code review, frontend checks, final freeze
check, and release readiness checks remain passing.
