# v3.8 Provider UX / Secret Safety Audit

Verification date: 2026-05-25

Scope: v3.8 Chinese Provider setup UX, model discovery, manual model entry, model assignment, provider connection status cache, safe API cache, real-provider runtime boundaries, and fake-provider test policy.

## Passed Items

1. Provider setup is understandable in Chinese.
   - The v3.8 Provider setup wizard uses Chinese step labels for provider type, Base URL, API Key source, connection test, model fetch, model assignment, and completion.
   - Inline help explains model service, Base URL, API Key, environment variables, `secret_ref`, `local_secret_ref`, model lists, and why different modes can use different models.
   - Provider status labels are localized for missing key, auth failure, invalid Base URL, fetch failure, timeout, unsupported model list, and connected states.

2. API keys are not saved to project files.
   - Provider profile save logic stores `api_key_env`, `secret_ref`, or `local_secret_ref` references, not plaintext key values.
   - Backend tests reject raw `api_key` fields and secret-like values in profile metadata.
   - Test coverage confirms local secret values do not appear in provider profile files.

3. API keys do not enter `localStorage` or `sessionStorage`.
   - Provider setup/check scripts scan the Provider wizard and model-assignment UI for browser storage API usage.
   - The transient key input is a password input with `autoComplete="off"` and is kept in a ref rather than persisted UI state.

4. Transient keys are not persisted.
   - `transient_api_key` is only sent for explicit manual test/fetch requests.
   - Backend tests confirm transient keys do not enter saved ProviderProfile files, provider health responses, or connection status cache files.

5. Auth errors are redacted.
   - Provider connection tests return safe status such as `auth_failed` and safe error types.
   - Raw provider body text, Authorization headers, relay tokens, and transient key values are removed from rendered responses.

6. Raw model-list provider responses are not displayed.
   - Model list UI displays safe `ModelProfile` metadata and capability badges.
   - UI copy states raw provider response and Authorization headers are not rendered.
   - Backend fake/real-path tests verify fetched model reports do not include provider secrets.

7. Manual `model_id` add is safe.
   - Manual model entry adds model metadata only.
   - It does not require an API key, does not call a provider, and does not write secrets.
   - Duplicate model IDs are handled with a user-facing message.

8. Relay / middle-provider copy does not become API resale.
   - Chinese help describes Relay as compatible API Base URL configuration.
   - It explicitly says the project is not an API resale service, does not recommend a specific relay vendor, and requires users to provide their own lawful Base URL and key.

9. Tests do not call real providers.
   - Tests use fake/local_stub providers and injectable transports.
   - Real provider runtime paths are covered by injected clients/transports, while default test connection and model fetch paths are blocked from real HTTP clients.
   - CI-oriented copy states tests continue to use fake providers.

10. Provider UI includes a clear cost warning.
    - The Provider help section states API keys may incur provider charges.
    - Real connection/model fetch/generation is only user-triggered, not automatic.

11. Model assignment does not leak secrets.
    - Model assignment stores routing/use-case metadata and model IDs only.
    - Validation output is safe and does not include API keys or raw provider responses.
    - JSON/structured-output warnings are explanatory and do not expose secret data.

12. Provider caches do not save secrets.
    - `ProviderConnectionStatusCache` allows safe status fields only and redacts unsafe message/error values.
    - Frontend safe API cache rejects API keys, transient keys, Authorization headers, raw env, raw provider responses, raw prompts/outputs, hidden facts, debug data, and mature/private content.
    - Tests verify transient keys and Authorization headers do not enter cache files.

## High-risk Secret Issues

None found.

No release-blocking Provider secret leak was found in the checked v3.8 Provider UX and runtime boundaries.

## Medium-risk UX Issues

None blocking.

Residual medium-risk area: the current checks are static/source and pytest based. They verify the Provider wizard source, backend redaction, cache files, and fake-provider paths, but they do not replace a final browser-rendered smoke pass of every Provider error state.

## Non-blocking Follow-ups

1. Add a browser smoke test for Provider auth failure, missing key, timeout, and model-list fetch failure states to confirm rendered Chinese UI remains redacted.
2. Add a small source check that extracts rendered Provider status strings and rejects key-like values in labels/tooltips.
3. Keep relay wording under review so future copy does not imply a resale service or endorse a specific relay provider.
4. Add a release-freeze check that scans provider cache files created during manual testing before tagging.

## Verification Commands and Results

Commands run:

```powershell
cd frontend
npm.cmd run check:v38-provider-setup-ux
npm.cmd run check:v38-provider-model-explanation
```

Results:

- `check:v38-provider-setup-ux`: passed.
- `check:v38-provider-model-explanation`: passed.

Backend-focused provider safety checks:

```powershell
python -m pytest backend/tests/test_v37_real_provider_runtime_enablement.py backend/tests/test_v36_provider_connection_status_cache.py backend/tests/test_v38_integration_regression.py
```

Result:

- `22 passed`.

## Release Decision

Ready for v3.8 release from the Provider UX / secret safety perspective.

The checked Provider setup, model discovery, model assignment, runtime, and cache surfaces preserve the required boundary: users may manually configure and test real providers, but automatic tests remain fake/local_stub; plaintext API keys are not stored in project files or browser storage; transient keys are not persisted; provider errors and caches are redacted; raw model-list responses are not rendered; and relay/custom provider copy remains local configuration rather than API resale.
