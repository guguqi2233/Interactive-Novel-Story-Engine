# v3.5 Provider Connectivity Secret Audit

## Audit Scope

This audit reviews v3.5 Provider Connectivity, connection testing, model
discovery/sync, model assignment, provider diagnostics, frontend Provider UI,
logs, diagnostics, backup/export boundaries, and related regression tests.

Reviewed files include:

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v35-qa-debug-provider-ui.mjs`
- `backend/app/llm/provider_connection_test.py`
- `backend/app/llm/provider_model_discovery.py`
- `backend/app/llm/provider_model_assignment.py`
- `backend/app/llm/provider_profiles.py`
- `backend/app/llm/provider_redaction.py`
- `backend/app/desktop/local_logs.py`
- `backend/app/desktop/diagnostics_bundle.py`
- v3.5 Provider and integration regression tests

The audit is read-only for business code. It verifies that Provider
Connectivity is a local configuration workflow, not an API resale service or
online platform capability.

## Passed Checks

1. Provider UI does not display API key values.
   - Provider UI displays `api_key_env`, `secret_ref`, configuration status,
     and safe provider/model metadata.
   - The UI copy states that API keys are never entered or rendered.
   - No plaintext `name="api_key"` input was found.

2. Provider UI does not store API key values in `localStorage` or
   `sessionStorage`.
   - `localStorage` usage found in `frontend/src/App.tsx` is limited to the
     first-run onboarding completion flag.
   - No Provider key, `transient_api_key`, Authorization header, or provider
     secret storage path was found in frontend browser storage.

3. `transient_api_key` is not persisted.
   - `ProviderConnectionTestRequest.transient_api_key` is request-only and
     marked `repr=False`.
   - Connection and model discovery builders do not copy
     `transient_api_key` into `ProviderProfileV2`.
   - Regression tests assert transient keys do not appear in saved provider
     profile YAML.

4. `transient_api_key` does not enter `ProviderProfile`.
   - `ProviderProfileV2` fields allow `api_key_env` and `secret_ref`, not raw
     keys.
   - Tests verify `transient_api_key` and sentinel key values are absent from
     profile files after connection testing and model sync.

5. `transient_api_key` does not enter logs.
   - `LocalLogService` redacts provider secret shapes through desktop policy
     plus `ProviderRedactionService`.
   - Tests assert transient key sentinels are absent from log payloads and
     captured logs.

6. `transient_api_key` does not enter diagnostics.
   - Diagnostics bundle preview/create use safe payloads and redacted logs.
   - Tests assert provider raw responses, Authorization headers, and
     transient-like fake keys do not appear in diagnostics bundles.

7. `transient_api_key` does not enter backup/export by design.
   - v3.5 roadmap and diagnostics/export UI copy state secrets, raw env,
     provider secrets, raw provider responses, and debug/private data are
     excluded.
   - No backup/export path was found that serializes Provider connection test
     payloads or transient request keys.

8. `test-connection` responses do not contain secrets.
   - `test_provider_connection_safe()` redacts safe messages with
     `redact_provider_connection_text()`.
   - Tests cover connected, missing secret, auth failure, timeout, invalid URL,
     raw provider error, and transient-key redaction cases.

9. `fetch-models` responses do not contain Authorization headers.
   - Model discovery uses fake client paths in tests and redacts provider
     errors.
   - Tests assert Authorization headers and secret-like model discovery errors
     are absent from responses.

10. Provider raw errors are redacted.
    - `ProviderRedactionService` covers Authorization Bearer, OpenAI-style
      `sk-*` keys, relay tokens, secret assignments, query secrets, token-like
      URL path segments, and raw provider response/error blocks.
    - Provider connection and model discovery tests cover raw provider error
      redaction.

11. Model sync reports do not contain secrets.
    - `sync_provider_models_safe()` stores normalized `ModelProfile` metadata:
      model id, display name, provider profile id, capability booleans,
      context/token metadata, use cases, enabled state, and last-seen time.
    - Tests assert transient keys do not appear in sync responses, model list
      responses, or provider profile YAML.

12. ProviderProfile stores only safe secret references.
    - `ProviderProfileV2` accepts `api_key_env` and `secret_ref`.
    - It rejects raw fields such as `api_key`, `llm_api_key`, and
      `openai_api_key`.
    - Provider profile validation rejects direct secret-like content in normal
      fields.

13. Relay/custom providers are not described as API resale.
    - UI copy says relay is "profile metadata only" and that no API resale or
      specific relay support is implied.
    - v3.5 roadmap explicitly states Provider Connectivity is local
      configuration, not API resale.

14. Tests do not call real providers.
    - v3.5 Provider tests use fake provider, mock, or local_stub paths.
    - `FakeProviderConnectionTestClient` and `FakeProviderModelDiscoveryClient`
      are deterministic and do not perform network I/O.

15. CI is not configured to connect to real providers by default.
    - v3.5 roadmap requires fake providers/fake clients in CI.
    - Existing tests assert fake/local paths and do not require real secrets or
      network calls.

16. `base_url` token-like segments are covered by redaction.
    - `ProviderRedactionService` redacts token-like URL query keys and path
      segments such as `/token/...`, `/secret/...`, `/auth/...`, and API key
      query values.
    - Tests cover query/path secret redaction.

## High-Risk Secret Issues

No high-risk Provider Connectivity secret issue was found.

No blocker was found for:

- API key display in Provider UI;
- browser storage persistence of Provider secrets;
- `transient_api_key` persistence;
- secret leakage in connection/model discovery responses;
- Authorization header leakage;
- raw provider error leakage;
- real provider calls in automated tests;
- relay/custom being presented as API resale.

## Medium-Risk Secret Issues

No medium-risk release-blocking secret issue was found.

Medium-risk areas to keep guarded:

- Provider UI includes fields named `api_key_env` and `secret_ref`. These are
  safe reference fields, but future UI changes must not turn them into plaintext
  key fields.
- `base_url` is user-configurable for compatible/relay/custom providers. The
  current redaction covers token-like query/path segments, but future
  diagnostics should continue applying `ProviderRedactionService` before
  rendering or bundling URLs.
- `transient_api_key` exists as a request field for local connection/model
  checks. It must remain one-shot and must not be copied into frontend state
  beyond the form submission lifecycle or backend persisted profiles.

## Low-Risk Issues

- Provider setup currently lives inside the large Prompt Lab / Provider UI area.
  This is acceptable for v3.5, but future v3.6 UI cleanup could separate
  Provider Connectivity into smaller components with more direct static checks.
- Some docs mention relay-style providers. They correctly state that relay is a
  generic OpenAI-compatible/custom base URL profile, not a specific service or
  resale offering.
- Diagnostics and logs are covered by tests, but any new diagnostics sections
  must explicitly include provider redaction in their serialization path.

## Fix Recommendations

No release-blocking fix is required for v3.5.

Recommended non-blocking follow-ups:

- Keep Provider redaction tests in the full release suite.
- Add future frontend component tests if a dedicated Provider Connectivity form
  is split out of `App.tsx`.
- Continue using `api_key_env` / `secret_ref` labels and avoid any plaintext
  `api_key` field in UI types, forms, docs, or examples.
- Keep `ProviderRedactionService` as the single redaction path for provider
  logs, diagnostics, connection errors, model discovery errors, and safe export
  summaries.
- If real provider connection testing is ever allowed outside CI, require an
  explicit local opt-in and keep test/CI defaults fake-only.

## Release Decision

Not blocked.

v3.5 can proceed toward release readiness from the Provider Connectivity secret
perspective, assuming `python -m pytest`, frontend build, and v3.5 provider/UI
regression checks remain passing.
