# v2.5 Provider Security / Secret Audit

## Verification Date

2026-05-22

## Scope

This audit reviews v2.5 Provider Gateway Pro secret handling across provider
profiles, secret resolution, Provider APIs, frontend UI, project export, usage
tracking, benchmark/reliability reports, debug/config summaries, tests, docs,
and repository hygiene.

This is a report-only audit. No business code was modified.

## Review Commands

```powershell
git ls-files | Select-String -Pattern '(^|/)(\.env$|.*\.db$|.*\.sqlite$|.*\.sqlite3$|logs/|.*\.log$|node_modules/|frontend/dist/|desktop-dist/|desktop_build/|release/)'
rg -n "sk-[A-Za-z0-9_-]{20,}|BEGIN .*PRIVATE KEY|Authorization|Bearer|api_key|secret_ref|base_url|headers" backend/app backend/tests frontend/src docs .env.example
git status --short
Get-Content .env.example
```

## Passed Items

1. `ProviderProfileV2` rejects raw `api_key`, `llm_api_key`, and `openai_api_key` fields.
2. Provider profiles use `api_key_env` and `secret_ref` references instead of storing raw key values.
3. `ProviderSecretResolver` resolves secrets in backend code only and does not expose a frontend-safe serialization path for secret values.
4. Provider API create/list/get/update/validate/status responses return safe summaries rather than raw provider configs.
5. Provider UI uses `api_key_env` and `secret_ref` fields and does not contain a plaintext `api_key` input field.
6. Project export skips secret-like provider profile files through the shared project package secret filter.
7. Provider usage tracking records safe metadata only: provider/model ids, mode, use case, token estimates, cost estimate, latency, success/error metadata.
8. Provider usage records do not store prompt text, output text, API key, raw env, hidden fact text, or debug memory.
9. Provider benchmark and structured-output reliability reports use safe report dumps and redact hidden/API-key-like text in prompt previews.
10. Default benchmark/reliability tests use fake/mock/local providers and do not call real OpenAI, relay, or local model services.
11. Debug/config summaries expose booleans such as `api_key_configured`, not raw key values.
12. `OpenAICompatibleProvider.safe_summary()` reports `api_key_configured` but does not include the API key.
13. `.env.example` contains placeholders and empty values only; `LLM_API_KEY=""` is blank.
14. `.env.example` documents that provider profiles may reference env var names only and must not store real keys.
15. `git ls-files` scan did not report tracked `.env`, database, log, cache, `node_modules`, `frontend/dist`, or desktop build output files.
16. Relay profile support is generic OpenAI-compatible configuration only; no third-party relay key is embedded.
17. Local provider status and diagnostics expose safe configuration booleans and redacted hints, not local secrets.
18. The known `sk-*` strings in tests/docs are fake fixtures such as `sk-test-*`, `sk-real-looking-*`, or deliberate redaction test values.

## High-Risk Issues

No confirmed high-risk provider secret leak was found in the current scan.

There is no evidence of:

- a real API key committed to source,
- `.env` being tracked,
- provider API returning raw secrets,
- frontend storing a provider key,
- default tests calling a real provider,
- project export including raw provider secret values.

## Medium-Risk Issues

### M1. `base_url` Values Are Stored In Provider Profiles And May Need Stronger Token-Like URL Policy

Current behavior:

- `ProviderProfileV2.safe_summary()` does not return the actual `base_url`; it returns `base_url_configured` and `base_url_source`.
- Repository validation scans string values with `contains_secret_text`.
- `contains_secret_text` catches `sk-*`, private key markers, `api_key`, `authorization`, and `bearer`, but not every possible token-like URL path or query parameter.

Risk:

- A user could accidentally enter a relay URL containing a token in a query string or path that does not match current secret patterns.
- The safe API/UI would not display the URL, but the project profile file itself could contain that sensitive URL.

Recommendation:

- Prefer `base_url_env` for relay or sensitive endpoints.
- Add provider-profile validation that rejects `base_url` containing query strings, userinfo, `token`, `key`, `auth`, `signature`, or long high-entropy path segments.
- Consider making relay profiles require `base_url_env` unless explicitly marked local/safe.

Release impact:

- Medium risk. It does not currently leak through API/UI/export safe summaries, but it could store a sensitive relay URL in a project file if a user enters one.

### M2. Test Fixtures Include Fake Authorization/Header Assertions

Current behavior:

- `backend/tests/test_v25_provider_gateway_pro.py` asserts a fake `Authorization` header contains `sk-test-fake` inside a fake transport.
- The fixture is local to tests and uses fake key material.

Risk:

- Low operational risk, but broad secret scans will continue to flag these test strings unless the release scanner recognizes fake key markers.

Recommendation:

- Keep fake key prefixes clearly fake (`sk-test-*`, `sk-fake-*`, `sk-placeholder-*`).
- Ensure release scans distinguish fake fixtures from real secrets and continue to fail on real-looking keys outside explicit test fixtures.

Release impact:

- Not blocking.

## Low-Risk Issues

### L1. Provider Secret Resolver Error Messages Include Env Var Names

`ProviderSecretResolver` errors include missing env var names such as `RELAY_API_KEY`.

This is acceptable because env var names are references, not secret values. Still, these errors should remain backend-only or safe API messages.

### L2. Safe Summaries Include `api_key_env` / `secret_ref` Identifiers

Provider safe summaries expose the env var name or local secret reference id. This is useful for authoring and not a raw secret, but it should be treated as configuration metadata rather than player-facing information.

### L3. Debug/Prompt-Lab Real Provider Opt-In Exists

Prompt Lab benchmark/reliability/diagnostic flows include explicit real-provider opt-in flags. Defaults remain fake/mock-safe, and tests do not enable real providers.

## Specific Checks

### 1. ProviderProfileV2 Rejects Real `api_key` Field

Status: **Pass**

`ProviderProfileV2` rejects raw key fields. Tests cover raw `api_key` rejection.

### 2. API Key Only Through `api_key_env` / `secret_ref`

Status: **Pass**

Provider profile schema and resolver use env refs or local secret refs. Raw values are not part of the profile contract.

### 3. ProviderSecretResolver Does Not Return Secret To Frontend

Status: **Pass**

Resolver is backend-only. Provider API uses safe summaries.

### 4. Provider API Does Not Return Secret

Status: **Pass**

Responses return `safe_summary()` output and capability metadata. No raw key value was found in API response construction.

### 5. Provider UI Does Not Display Secret

Status: **Pass**

The UI has `api_key_env` and `secret_ref` fields. It does not include a plaintext `api_key` input.

### 6. Project Export Filters Provider Secret

Status: **Pass with medium caveat**

Project package export skips secret-like text. The caveat is token-like `base_url` values that evade current patterns.

### 7. Provider Usage Logs Do Not Contain Secret

Status: **Pass**

Usage logs store metadata only and omit prompts/outputs/secrets.

### 8. Provider Benchmark Reports Do Not Contain Secret

Status: **Pass**

Reports use safe dumps and redacted prompt previews. Default tests use fake providers.

### 9. Debug API Does Not Return Secret

Status: **Pass**

Debug/config surfaces use `api_key_configured` booleans and redacted hints. No raw secret return path was found.

### 10. `.env` Not Tracked

Status: **Pass**

Tracked-file scan reported no `.env`.

### 11. `.env.example` Placeholder Only

Status: **Pass**

`LLM_API_KEY=""`; Provider Gateway notes explicitly require env refs and no real keys.

### 12. Docs/Tests Only Fake Keys

Status: **Pass**

`sk-*` matches are fake/redaction fixtures or documented examples. Continue enforcing fake prefixes.

### 13. Real `sk-...` Key Presence

Status: **No real key found**

The scan found fake fixtures and redaction examples, not confirmed real credentials.

### 14. `base_url` Token-Like Path

Status: **Medium risk**

Safe summaries hide actual base URLs, but profile files may store `base_url`. Validation should be hardened for token-like URL content.

### 15. Relay Profile Third-Party Key

Status: **Pass**

Relay profiles use OpenAI-compatible config with `api_key_env` / `secret_ref`; no vendor key is embedded.

### 16. Local Provider Sensitive Path Leakage

Status: **Pass**

Local provider config exposes configured/missing status and safe hints. No raw local sensitive path leak was identified in Provider Profile UI/API.

### 17. Logs Printing Headers / Authorization

Status: **No production leak found**

`OpenAICompatibleProvider` builds an Authorization header for transport, but safe summary omits it. Test fake transport records headers inside a test assertion only. No production logging of headers was found.

### 18. Tests Calling Real Provider

Status: **Pass**

Default tests use mock/fake/local_stub/fake transports. Real provider flags exist but are not enabled by tests.

## Fix Recommendations

1. Harden `ProviderProfileV2.base_url` validation:
   - reject query strings for stored `base_url`,
   - reject userinfo,
   - reject `token`, `key`, `auth`, `signature`, `credential`, and similar markers,
   - reject long high-entropy path segments,
   - prefer `base_url_env` for relay/middleman profiles.
2. Add a focused test for token-like `base_url` rejection.
3. Add a release scanner allowlist for fake key markers and fail on non-fake `sk-*`.
4. Keep Provider API responses wrapped in safe summaries only.
5. Continue ensuring usage/benchmark/reliability reports never store prompt or output text by default.

## Release Blocker Assessment

**Blocks v2.5 release: No, with one medium-risk follow-up.**

The current implementation does not show a confirmed secret leak and satisfies
the core provider secret boundary: no raw key storage in ProviderProfileV2, no
key returned to frontend/API, no prompt/output/key in usage logs, no default
real provider tests, and no tracked `.env`.

The main follow-up is stronger `base_url` validation for relay/openai-compatible
profiles. It is recommended before final hardening, but it is not a confirmed
release blocker unless project files are expected to store user-entered relay
URLs that may embed tokens.

