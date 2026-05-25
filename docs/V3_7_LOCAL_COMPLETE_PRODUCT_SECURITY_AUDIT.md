# v3.7 Local Complete Product Security Audit

Verification date: 2026-05-25

## Audit Basis

This is a read-only security audit for the v3.7 Local Complete Product phase.
It reviewed the current v3.7 integration status, Provider profile/cache/redaction
code, diagnostics and backup/restore services, package validation/import-export
hardening, DebugGate/UI boundaries, wrapper scripts, and local-first product
copy.

This audit did not modify business code or tests. It uses the current
`docs/V3_7_FULL_INTEGRATION_REVIEW.md` verification results as supporting
evidence:

- `python -m pytest`: passed, `1795 passed in 136.29s`.
- `cd frontend && npm.cmd run build`: passed.
- v2 release checklist: passed, no real API key pattern found.
- compatibility matrix and contract docs check: passed through the documented
  `PYTHONPATH=backend` invocation.
- all frontend `check:*` scripts are not yet passing; the known failures are
  product-readiness/static-copy blockers and are recorded below.

## Passed Items

1. **API key does not appear to enter frontend values, logs, backup,
   diagnostics, or export payloads as a raw secret.**
   - `ProviderProfileV2` accepts `api_key_env` and `secret_ref` references but
     rejects raw key fields such as `api_key`, `llm_api_key`, and
     `openai_api_key`.
   - frontend Provider setup copy and forms describe env var / local secret ref
     references and state that plaintext API key fields are not present.
   - diagnostics, backup, export, quality, and product readiness surfaces use
     safe summaries and exclusion copy for API keys, provider secrets, raw env,
     raw prompts, raw outputs, hidden facts, NPC secrets, debug memory, and raw
     `state_deltas`.

2. **`transient_api_key` is modeled as one-time input and not persisted by the
   reviewed Provider status cache.**
   - Provider connection testing accepts `transient_api_key` with `repr=False`.
   - connection-test safe messages are redacted with the transient key supplied
     as an extra secret.
   - `ProviderConnectionStatusCache` stores only allowlisted status metadata:
     provider profile id, status, tested time, latency, safe error type, model
     count, and redaction flag.
   - the cache explicitly documents that it does not store raw provider
     responses, raw error bodies, env values, Authorization headers, API keys,
     transient API keys, `transient_api_key` payload fields, ProviderProfile
     secret values, or `safe_message` text.

3. **`ProviderProfile` / `ProviderProfileV2` does not save raw API keys.**
   - `api_key_env` and `base_url_env` validators require uppercase environment
     variable names and reject secret-looking values.
   - `secret_ref` is limited to a safe local reference pattern and rejects
     secret-like text.
   - `safe_summary()` masks `secret_ref` as configured/not configured.

4. **Provider error redaction is present.**
   - `ProviderRedactionService` redacts OpenAI-style keys, Authorization bearer
     headers, API-key assignments, relay tokens, secret refs, token-like URL
     query/path segments, and raw provider response/error blocks.
   - provider connection and model discovery paths use redaction before
     returning safe messages.

5. **Debug UI remains gated.**
   - frontend code uses `DebugGate` and `ENABLE_DEBUG_API` messaging for raw
     EventLog, StateDelta, Visible vs Debug Compare, and Safe Debug Export
     surfaces.
   - debug export requires explicit confirmation and disables raw debug export
     when the debug API is disabled.

6. **Raw `state_deltas` are intended to stay out of normal UI.**
   - normal product readiness, Novel, Tavern, World, QA, diagnostics, backup,
     export, performance, and status surfaces repeatedly state that raw
     `state_deltas` are excluded.
   - EventLog raw JSON and StateDelta details are wrapped in debug-gated UI.
   - backend playtesting invariants check for raw `state_deltas` in player
     payloads.

7. **Mods and modules remain declarative and do not execute arbitrary code by
   default.**
   - gameplay module permission policy defaults arbitrary code execution,
     direct GameState mutation, database write, secret read, network access,
     LLM adjudication, and visibility bypass to false.
   - module/package validation rejects executable code and unsafe permissions.
   - Action Mod validation checks for executable/secret-like markers and keeps
     action outputs routed through declared validation paths.

8. **Import/export hardening is present.**
   - `validate_relative_package_path()` is used during package validation to
     guard package paths.
   - package v2 import performs validation before apply and requires
     `confirm_apply`.
   - package v2 export rejects secret-like text and hidden/debug payload markers
     in safe packages.
   - pack validation blocks executable payload suffixes and secret-like package
     content.

9. **Safe Apply / authoring flows require validation, dry-run, and confirm
   boundaries.**
   - v3.7 roadmap and current frontend/backend API surfaces preserve validation,
     dry-run, confirmation, and audit terminology for authoring, Cross-Mode,
     package import, backup/restore, migration, debug export, and export flows.
   - authoring and Cross-Mode UI copy states that draft/proposal/checklist
     surfaces do not directly mutate active `GameState`.

10. **Backup/restore safety is present.**
    - backup plan is dry-run by default.
    - backup creation requires `explicit_confirm`.
    - backup default exclusions include `.env`, API key, provider secrets, logs,
      cache, `node_modules`, `frontend/dist`, desktop build outputs, databases,
      debug-only data, and mature/private content unless explicitly requested.
    - backup target path must stay inside the local workspace and rejects
      disallowed path parts.
    - restore supports dry-run and apply requires `explicit_confirm`.

11. **Diagnostics are redacted and local-only.**
    - diagnostics preview records included/excluded sections and writes no file.
    - diagnostics exclude `.env`, API keys, provider secrets, raw env, raw
      prompt/output, hidden facts, NPC secrets, debug memory, raw
      `state_deltas`, mature/private content, database files, and full save
      files by default.
    - diagnostics bundle validation rejects sensitive text after desktop and
      provider redaction checks.
    - debug diagnostics require explicit debug confirmation and enabled debug
      API.

12. **ErrorBoundary is redacted.**
    - frontend error boundary copy states that it does not show stack trace,
      API key, raw env, hidden facts, or sensitive local path in normal UI.
    - product error/empty/disabled state polish includes safe error wording and
      next actions without uploading errors.

13. **Wrapper tools are allowlisted.**
    - `scripts/run_tool.ps1` and `scripts/run_tool.sh` map a fixed set of tool
      names to backend modules and reject unsupported tool names.
    - wrappers set `PYTHONPATH=backend` / backend path for local tool
      execution and do not accept arbitrary shell commands.

14. **No account, cloud sync, online marketplace, remote package download, or
    online platform entry was found as a supported v3.7 capability.**
    - README, docs, `.env.example`, and frontend copy consistently describe
      local-first behavior and explicitly exclude accounts, cloud sync, online
      marketplace, online RP/writing/play, remote package auto-download, and API
      resale service claims.

15. **No real Provider CI test is indicated by the reviewed code and reports.**
    - Provider connection/model tests use fake/mock/local_stub paths.
    - `.env.example` and docs instruct tests/CI to use fake providers/fake
      clients and not call real provider networks by default.

## High-risk Issues

None found in the reviewed security boundaries.

No evidence was found of raw API key persistence, ProviderProfile raw key
storage, transient key cache persistence, Debug UI mutation of `GameState`, raw
`state_deltas` intentionally rendered in normal UI, arbitrary-code mod
execution enablement, unsafe wrapper command execution, or online account/cloud
marketplace entry as an implemented v3.7 feature.

## Medium-risk Issues

1. **v3.7 frontend product checks currently fail on secret-boundary wording.**
   - `check:v37-novel-workflow`
   - `check:v37-tavern-workflow`
   - `check:v37-world-workflow`
   - `check:v37-cross-mode-workflow`
   - `check:v37-qa-debug-workflow`
   - `check:v37-backup-diagnostics-workflow`

   These failures appear to be static-copy safety failures around API-key or
   transient-key terminology outside the scripts' allowed safe exclusion
   wording. They are not evidence of actual raw secret persistence, but they are
   release-blocking for v3.7 because the frontend safety checks must pass before
   Local Complete Product acceptance.

2. **v3.7 privacy/safety review check is missing explicit hidden-fact exclusion
   wording.**
   - `check:v37-privacy-safety-review` expects the normal product UI to include
     explicit hidden fact display exclusion copy: `no hidden fact text`.
   - Backend and older frontend boundaries still pass, but the v3.7 product UI
     should make this exclusion unambiguous before release.

3. **v3.0 Desktop Packaging token regression remains a product-check blocker.**
   - `check:v30-ux` fails because the current frontend no longer exposes the
     expected "Desktop Packaging" completion token.
   - This is primarily a product-readiness/static check issue, but preserving
     visible desktop packaging/exclusion boundaries matters for release hygiene.

4. **Tool invocation remains sensitive to the documented wrapper/PYTHONPATH
   path.**
   - Direct `python -m backend.app.tools.compatibility_matrix` and direct
     `python -m backend.app.tools.generate_contract_docs` imports fail.
   - The documented `PYTHONPATH=backend` / `app.tools...` invocation and
     allowlisted wrappers work. This is not a security flaw, but operators
     should keep using wrappers to avoid confusing tool failures.

## Non-blocking Follow-ups

- Keep frontend static checks aligned with v3.7 product copy so safe exclusion
  language is explicit without resembling plaintext key input.
- Add a browser-level smoke test for DebugGate disabled/enabled states and
  product privacy review pages.
- Add a small fixture that asserts `ProviderConnectionStatusCache` file content
  cannot contain `safe_message`, raw provider response, Authorization header,
  raw env, API key, or transient key text.
- Continue expanding import/export tests for nested archive names, executable
  suffixes, hidden/debug markers, and package metadata edge cases.
- Keep wrappers allowlisted if new backend tools are added; do not add a generic
  shell-command wrapper.
- Consider documenting the v3.7 workflow copy rules next to the check scripts so
  future UI text changes do not accidentally trip secret-safety scanners.

## Release Decision

Security-specific verdict: **No high-risk security issue found.**

v3.7 release verdict: **Not ready for final v3.7 release acceptance yet.**

Reason: current v3.7 frontend product checks still fail on secret-boundary copy,
hidden-fact exclusion copy, and the inherited v3.0 Desktop Packaging token. The
failures do not currently show a raw secret leak or boundary bypass, but they
must be fixed and rechecked before v3.7 can be declared a Local Complete
Product.

Recommended next step:

1. Fix the v3.7 frontend safety-copy check failures without adding any new
   secret input fields.
2. Restore or safely replace the v3.0 Desktop Packaging completion token.
3. Re-run frontend `check:*`, `python -m pytest`, and frontend build.
4. Re-run this security audit or update it after all checks pass.
