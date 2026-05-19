# v1.5 Security / Provider / API Key Audit

Verification date: 2026-05-20

Scope:

- v1.5 provider configuration, Provider Capability Registry, Provider
  Benchmark, Prompt Lab CLI, Local Model Diagnostics, Usage Tracker, Context
  Inspector, Provider Routing, Prompt Experiment Packages, and frontend Prompt
  Lab surfaces.
- Repository tracking status for common sensitive/runtime artifacts.

This audit generated a documentation report only. No business code was changed.

## Audit Summary

Verdict: pass with non-blocking cautions.

Blocking status: no high-risk v1.5 security / provider / API key blocker was
found.

API keys are read from backend settings/environment and represented in normal
frontend/API summaries only as booleans. v1.5 Prompt Lab reports, usage logs,
experiment packages, provider summaries, CLI output, and diagnostics are
designed to avoid raw secrets and raw prompts. Real provider calls remain
explicit opt-in.

## Passed Items

1. API key source

   `LLM_API_KEY` is read by backend configuration (`Settings.llm_api_key`) from
   environment. The field is marked `repr=False` and is not a frontend input.

2. API key does not enter frontend as a value

   Frontend API types and Prompt Lab UI display `api_key_configured` as a
   boolean/status only. No raw key value is returned or rendered.

3. API key does not enter usage logs

   `ModelUsageRecord` stores provider/model/use_case, timing, estimated token
   counts, estimated cost, success/failure, and error type. It does not store
   raw prompt text or API key values.

4. API key does not enter Prompt Experiment Packages

   `prompt_experiment_packages.py` rejects API-key-like tokens, raw env,
   private key markers, hidden facts, raw `GameState`, raw state deltas, and
   sensitive prompt snapshots during validation.

5. API key does not enter exported prompt profiles

   Prompt Profiles contain style, variant, temperature, and RP boundary fields.
   They do not carry provider credentials. Profile validation rejects weakened
   visibility or GameState boundaries.

6. Provider safe summaries do not return secrets

   Provider capability summaries expose provider/model metadata and booleans
   such as `requires_api_key` or `api_key_configured`. They do not return key
   values, raw env, or full credential material.

7. local_http base URL handling

   `local_http` diagnostics expose `base_url_configured` rather than the full
   URL in reports. Studio config summaries redact database paths and do not
   expose local provider secrets. Base URL itself is not treated as an API key,
   but report paths avoid returning the raw configured URL.

8. Real provider benchmark opt-in

   `allow_real_provider` defaults to `false`. OpenAI benchmark attempts without
   explicit opt-in are blocked with `real_provider_blocked=true`.

9. Tests do not call real APIs by default

   v1.5 tests use fake/local_stub providers and include a CLI test proving
   OpenAI benchmark without opt-in is blocked.

10. Fake/test keys are redaction sentinels

   Test fixtures include fake `sk-...` strings to verify redaction. Current
   tests assert those strings do not appear in safe payloads.

11. `.env` is not tracked

   No tracked `.env` file was found. `.env.example` is tracked and contains
   empty placeholder values and safety comments.

12. Runtime artifacts are not tracked

   `git ls-files` did not show tracked database, log, cache, `node_modules`,
   `frontend/dist`, or desktop build output paths. A local `world_engine.db`
   exists in the workspace but is not shown as tracked/staged.

13. Real `sk-...` key scan

   Search hits are fake/test sentinel strings or documentation placeholders.
   No real credential value was identified in the audited v1.5 files.

14. Provider routing config does not store API keys

   `ProviderRoutingRule` stores use_case, provider/model ids, constraints, and
   fallback ids. It does not contain credential fields.

15. Cost tracker does not record raw prompt

   Usage tracking estimates token counts from message/output content but stores
   only numeric metadata and error type.

16. Context Inspector defaults to redacted

   Raw prompt output is disabled by default. When explicitly enabled, the field
   is `raw_prompt_redacted` and safe dump methods strip hidden/API-key-like
   content.

17. CLI output avoids secrets

   Prompt Lab CLI commands use service-layer safe report outputs and default to
   fake/non-real provider modes unless an explicit real-provider flag is passed.

18. Frontend does not store provider secrets

   Prompt Lab frontend has controls/status for provider capability, benchmark,
   diagnostics, usage, and routing. It displays booleans/status labels, not raw
   API keys.

## High-Risk Issues

No high-risk security/provider/API key issue was found in v1.5.

The audit did not find:

- raw API key returned to frontend,
- API key stored in usage records,
- API key exported into Prompt Experiment Packages,
- default real provider benchmark execution,
- provider routing config containing secrets,
- tracked `.env` or tracked runtime database/log/cache/build artifacts.

## Medium-Risk Issues

1. Explicit real provider benchmark mode can send prompts off-machine

   Impact: medium.

   This is intended functionality, but it must remain behind
   `allow_real_provider=true` and visible UI/CLI warnings. Prompt cases must
   stay redacted and safe.

   Status: not blocking.

2. Explicit real local diagnostics can call a local endpoint

   Impact: medium.

   `allow_real_local_check=true` allows local HTTP checks. It sends safe smoke
   messages, not world facts. The raw base URL is not returned in reports.

   Status: not blocking.

3. Boolean `api_key_configured` reveals credential presence

   Impact: medium-low.

   The value does not expose the key. It is acceptable for local Studio/Prompt
   Lab diagnostics, but it must not be exposed to player APIs or exported
   packages.

   Status: not blocking.

4. Local runtime database exists in workspace

   Impact: medium-low.

   `world_engine.db` exists locally, which is expected for this project. It is
   not tracked/staged in the current scan. Continue to keep database files
   ignored.

   Status: not blocking.

## Small Issues

1. Fake `sk-...` strings in tests/docs can trigger broad secret scanners.

   These are deliberate redaction fixtures. Secret scanning should allow known
   fake test values while still rejecting real keys.

2. `.env.example` includes `LLM_API_KEY=""`.

   This is an empty placeholder and safe. It also explicitly warns not to expose
   provider credentials as `VITE_*` variables.

3. Provider capability metadata includes cost hints and `requires_api_key`.

   This is non-secret metadata. It should remain declarative and not be treated
   as a live provider health check.

## Fix Recommendations

1. Keep all real provider execution behind explicit `allow_real_provider` or
   `allow_real_local_check` flags.

2. Keep frontend controls from accepting or storing API key values. Keys should
   remain backend environment/secret-store inputs only.

3. Preserve regression tests that serialize usage summaries, provider summaries,
   benchmark reports, context snapshots, Prompt Experiment Packages, and CLI
   output, then assert no API key or raw prompt appears.

4. Keep `world_engine.db`, logs, caches, `node_modules`, `frontend/dist`, and
   desktop build outputs ignored and out of commits.

5. If usage tracking gains persistent storage, add a migration/test proving no
   raw prompts, raw outputs, hidden facts, or credentials are persisted.

6. Continue to distinguish fake `sk-...` sentinel strings in tests from real
   credentials in release audits.

7. Do not export provider routing config with secrets; if routing export is
   added later, validate it through the same package-secret rejection path.

## v1.5 Release Blocking Status

Does this block v1.5 release: no.

Rationale:

- API keys are not exposed as values through v1.5 API/UI/report/package paths.
- Real provider calls are not default behavior.
- Prompt Lab CLI and frontend use fake/local defaults and safe summaries.
- Usage and context inspection avoid raw prompt persistence by default.
- No tracked `.env` or tracked runtime artifact was found.

Recommended release condition: proceed after full v1.5 regression tests and
frontend build pass, and after confirming no new sensitive files are staged.
