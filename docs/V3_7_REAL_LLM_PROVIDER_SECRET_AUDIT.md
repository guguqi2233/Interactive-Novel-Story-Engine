# v3.7 Real LLM Provider Secret Audit

Verification Date: 2026-05-25

Scope: v3.7 real LLM runtime enablement, Provider Gateway, ProviderProfile storage, secret resolution, transient key handling, provider connection/model discovery, provider status cache, frontend Provider UI, logs, diagnostics, backup/export surfaces, manual smoke-test documentation, tests, and CI/network posture.

This audit is source-review based. No real provider was called, no data was uploaded, and no business code was modified.

## Passed Items

1. **API key does not enter project files.**
   `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and `openai_api_key` fields. `ProviderProfileRepository.validate_provider_profile()` rejects secret-like values except safe metadata references (`api_key_env`, `base_url_env`, `secret_ref`, `local_secret_ref`). Project provider profile YAML may store reference metadata such as `OPENAI_API_KEY` or `providers/main`, but not the key value.

2. **API key does not enter frontend storage.**
   Frontend `localStorage` usage is limited to onboarding, keyboard-shortcut, and reduced-motion preferences. Provider setup uses `api_key_env`, `secret_ref`, `local_secret_ref`, or a one-time password input read through a ref for manual requests. No `localStorage` or `sessionStorage` write path for API keys or `transient_api_key` was found.

3. **API key does not enter logs.**
   `LocalLogService` redacts desktop secrets and provider-specific secret patterns. Existing v3.7 tests write fake Authorization/API-key material into logs and assert the safe log response does not include those values.

4. **API key does not enter diagnostics.**
   `DiagnosticsBundleService` includes only safe payload sections, excludes `.env`, API keys, provider secrets, local provider secret stores, raw env, raw prompt/output, hidden/debug data, and mature/private content, then validates bundles with desktop and provider redaction.

5. **API key does not enter backup/export.**
   `BackupService` writes only safe summaries and excludes `.env`, API keys, provider secrets, the local provider secret store, logs, caches, databases, debug-only data, and mature/private content by default. v3.7 provider runtime tests assert fake provider keys do not appear in backup/export-like payloads.

6. **ProviderProfile does not save plaintext keys.**
   `ProviderProfileV2` allows `api_key_env`, `secret_ref`, and `local_secret_ref`, and forbids raw key fields. `safe_summary()` masks `secret_ref` and `local_secret_ref` as configured booleans/markers.

7. **local_secret_ref is resolved outside the project.**
   `ProviderSecretResolver` resolves `local_secret_ref` from `AI_NARRATIVE_STUDIO_LOCAL_SECRET_DIR` or an OS user config directory. It rejects local secret stores at or under the workspace, and path resolution prevents escaping the local secret store.

8. **transient_api_key is not persisted.**
   `ProviderConnectionTestRequest` accepts `transient_api_key` only for a one-time connection/model-list request. Provider profile persistence, health responses, and cache files are tested to exclude the transient key and even the `transient_api_key` field name from saved profile text.

9. **transient_api_key does not enter cache.**
   `ProviderConnectionStatusCacheEntry` is an `extra="forbid"` schema limited to `provider_profile_id`, `status`, `tested_at`, `latency_ms`, `safe_error_type`, `model_count`, and `redaction_applied`. It intentionally stores no raw provider response, raw error body, env value, Authorization header, API key, transient API key, or secret reference value.

10. **Raw provider errors are redacted.**
    Provider connection and model discovery use `provider_redactor` and pass the transient key as an extra secret. Tests cover raw provider errors containing fake Authorization headers, token-like query values, relay tokens, and fake `sk-*` values, and assert the rendered status/report is redacted.

11. **Manual smoke-test documentation contains no real key.**
    `docs/REAL_LLM_MANUAL_SMOKE_TEST.md`, `README.md`, `docs/LLM_PROTOCOL.md`, and `.env.example` describe `api_key_env`, `secret_ref`, `local_secret_ref`, and one-time `transient_api_key` with placeholders only. The docs state that real provider smoke tests are manual, may incur cost, may send prompts to the configured provider, and must not place keys in project/frontend/logs/diagnostics/backups/exports.

12. **Tests do not call a real provider by default.**
    Provider connection and model discovery default to fake clients unless `allow_real_connection` / `allow_real_provider` is explicitly true. v3.7 tests use fake/local_stub providers or injected transports. The only real-client test path with `allow_real_provider=True` uses an injected local transport and does not perform external network I/O.

13. **CI real-provider calls were not found.**
    The repository currently has no `.github` workflow directory. Source scans found no CI workflow that enables real provider calls. Existing tests and documentation require fake providers/fake clients for automated runs.

14. **Relay/custom wording is not API resale.**
    `README.md`, `docs/LLM_PROTOCOL.md`, `docs/REAL_LLM_MANUAL_SMOKE_TEST.md`, and Provider UI text describe relay as generic OpenAI-compatible/custom base URL configuration. They explicitly state that the project is not an API resale service and does not integrate with a specific relay vendor.

15. **Secret-like scan hits are fixture-only.**
    A repository scan for production-looking `sk-*` strings found them in tests and historical audit docs as deliberate redaction/rejection fixtures, not as production provider configuration.

## High-risk Secret Issues

None found.

No evidence was found that real API keys are saved to project files, frontend storage, logs, diagnostics, backups, exports, provider profiles, or provider caches. No automated test path was found that calls a real provider by default.

## Medium-risk Issues

1. **No active CI workflow is present to enforce no-network policy.**
   This is not a secret leak in the current repository, because no CI workflow was found. It does mean the audit cannot verify an active CI job configuration. If CI workflows are added later, they should include an explicit no-real-provider/no-network guard for provider tests.

2. **Manual real-provider flow depends on user intent.**
   Real provider calls are correctly gated behind manual UI/API flags, but users can still intentionally run Test Connection, Fetch Models, or generation against their configured provider. Documentation correctly warns that this may send prompts and incur cost.

## Non-blocking Follow-ups

1. Add a small CI/static check when CI workflow files are introduced, verifying that provider tests use fake clients and do not set `allow_real_provider` for external network calls.
2. Keep the release secret scanner allowlist strict: allow fake/redaction fixtures only in tests/docs, never production code, `.env`, project profiles, or packages.
3. Continue testing diagnostics, logs, backups, exports, and frontend responses with fake production-looking secret strings so redaction regressions are caught early.
4. Consider documenting the exact default OS local secret store locations in the product guide for users who choose `local_secret_ref`.

## Release Decision

Pass for v3.7.

The real LLM runtime support keeps Provider Gateway as the only model entry, preserves local-first secret boundaries, and does not introduce a release-blocking Provider secret issue. Real provider use remains manual/user-triggered; tests and automated checks remain fake-provider based.
