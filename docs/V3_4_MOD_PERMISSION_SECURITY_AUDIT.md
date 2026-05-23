# v3.4 Mod Permission / Security Boundary Audit

Verification date: 2026-05-24

Scope: v3.4 Authoring / Mod UI Pro security boundary for module permissions, Action Mod, Rule Module, Module Browser, import/export, provider profile packs, compatibility, certification, quality gate, and related regression tests.

This audit is documentation-only. It does not modify business code.

## Reviewed Areas

- `frontend/src/App.tsx`
- `frontend/scripts/check-v34-authoring-ui.mjs`
- `backend/app/engine/action_mod_validator.py`
- `backend/app/engine/actions/declarative.py`
- `backend/app/engine/action_registry.py`
- `backend/app/engine/rule_module_contract.py`
- `backend/app/platform/module_permissions.py`
- `backend/app/platform/package_manifest_v2.py`
- `backend/app/platform/module_browser.py`
- `backend/app/platform/mod_import_export.py`
- `backend/app/platform/provider_profile_pack.py`
- `backend/app/platform/mod_compatibility_matrix.py`
- `backend/app/platform/extension_certification.py`
- `backend/app/quality/mod_quality_gate.py`
- `backend/tests/test_action_mod_authoring_api.py`
- `backend/tests/test_v34_integration_regression.py`

## Passed Items

1. Mod UI does not expose an arbitrary-code plugin workflow.
   - Module Browser, Import/Export, Quality Gate, Certification, Compatibility, and Permission Dashboard all describe local metadata review rather than package execution.
   - The v3.4 frontend check includes required copy for local-only, no online marketplace, no remote download, and no arbitrary code execution.

2. Action Mod Editor does not provide an execution path for `exec`, `eval`, or scripts.
   - The UI labels Action Mods as declarative only and blocks code-like JSON textarea input containing `exec`, `eval`, `function`, `script`, `python`, `javascript`, `read_secrets`, `access_network`, or `access_filesystem`.
   - Backend validation uses `DeclarativeActionDefinition` and `DeclarativeStateDeltaTemplate`, validates state paths through the Action DSL whitelist, rejects executable permissions, and returns safe previews/test summaries.

3. Rule Module UI cannot enable `execute_code` as a runtime capability.
   - `RuleModuleManifest` rejects `can_execute_code`, `can_call_llm`, filesystem access, and network access.
   - The UI marks Rule Modules as contract-only and shows dangerous permissions as blocked.

4. Permission Dashboard does not provide a dangerous-permission enable button.
   - The dangerous permission list is fixed: `execute_code`, `access_filesystem`, `access_network`, `read_secrets`, `write_database`, `modify_game_state_directly`, `bypass_visibility`, and `call_llm`.
   - Requested dangerous permissions are displayed as blocked by the local default-deny policy.

5. Module Browser scans and validates local manifests without executing package code.
   - `ModuleBrowserService` reads manifests from local module directories, validates permissions and package manifests, scans for executable payloads and secret-like content, and returns safe summaries.

6. Import Wizard does not execute packages.
   - `ModImportExportService.import_dry_run` validates package manifests, relative paths, executable suffixes, secrets, mature policy markers, checksums, and duplicates.
   - `import_apply` requires explicit confirmation and writes only after a passing dry-run; imported modules are returned with `enabled=False`.

7. Remote package download and online marketplace entry are not present as implemented v3.4 capabilities.
   - UI copy explicitly says local-only, no online marketplace, and no remote download.
   - Static v3.4 frontend checks look for marketplace/remote/dangerous-permission enabling surfaces.

8. Provider Profile Pack cannot store raw provider secrets under the current validator.
   - `validate_provider_profile_pack` rejects forbidden fields such as `api_key`, `authorization`, `x-api-key`, auth/key headers, and non-test `sk-`-like values.
   - Shared provider profile patterns use `api_key_env` / `secret_ref`, not plaintext key storage.

9. Mod export checks for secret and executable leakage.
   - Export rejects executable suffixes and secret-like content.
   - Mature/private content is filtered unless the export policy explicitly allows it.

10. Mod import protects against zip slip/path traversal.
    - `validate_relative_package_path` is applied during dry-run and apply.
    - Apply resolves destination paths under the target directory and rejects zip slip escapes.

11. Mod import rejects executable files.
    - Package manifests and archive members are checked against executable suffixes including Python, JavaScript, shell, batch, PowerShell, binaries, and DLL-like payloads.

12. Action Mod remains routed through `ActionRegistry`.
    - Declarative action definitions are registered as mod actions through `ActionRegistry.register_mod_action`.
    - Existing regression tests exercise registration and confirm the registered handler is a declarative handler.

13. Action Mod remains bounded by `StateDelta` / `EventLog`.
    - Declarative handlers generate `ActionResult.state_deltas` and an `Event` carrying those deltas; the UI/test harness shows safe delta summaries rather than raw deltas.
    - StateDelta template paths are restricted by the Action DSL validator.

14. Rule Module remains contract-only.
    - The Rule Module model is a manifest contract with provided systems, state schema extensions, actions/rules, permissions, and compatibility notes.
    - There is no sandbox/runtime loader for Rule Module code in v3.4.

15. Mod Quality Gate does not use an LLM judge for safety.
    - `run_mod_quality_gate` composes Module Browser, Compatibility Matrix, and Certification results.
    - No provider, narrator, prompt, OpenAI, or LLM call is used in the Mod Quality Gate safety decision path.

16. Tests do not execute unknown mod code.
    - v3.4 regression fixtures include an unsafe `run.py` payload as inert test content and assert it is detected/blocked.
    - Tests use local/mock settings and do not call real external APIs.

## High-Risk Issues

No high-risk Mod Permission / Security Boundary issue was found in this audit.

The reviewed implementation preserves the v3.4 boundary: local manifest/package scanning only, dangerous permissions default blocked, no arbitrary-code execution, no remote marketplace/download workflow, and no active `GameState` mutation from mod authoring surfaces.

## Medium-Risk Issues

1. Action Mod Editor still includes JSON textareas for `preconditions` and `checks`.
   - Current status: not an execution path. The UI blocks obvious code-like tokens before accepting JSON, and backend schemas only validate structured declarative conditions/checks.
   - Risk: users can still paste arbitrary-looking JSON, and Pydantic extra-field handling could make unsupported keys confusing even if they are not executed.
   - Release impact: not a security blocker because there is no execution path, no JS/Python runtime, and backend validation/test-harness output remains safe. It is a usability/security-hardening gap.

2. Some validation, browser, and quality messages include backend-generated error strings.
   - Current status: secret-like content is redacted in key manifest paths and imports; Module Browser uses `redact_text` for manifest v2 validation exceptions.
   - Risk: future validators that include raw file content in error messages could leak sensitive text into a report even without executing code.
   - Release impact: not a Mod Permission execution blocker, but it overlaps the separate Authoring UI privacy/visibility audit and should be hardened before final v3.4 release if that audit remains blocking.

## Low-Risk Issues

1. Certification wording should remain local advisory only.
   - Current UI and roadmap language avoid online certification claims.
   - Keep this wording stable so users do not confuse local checks with remote signing or marketplace trust.

2. Executable suffix blocking is extension-based.
   - The current denylist catches the expected v3.4 executable/script payloads.
   - Future hardening could add MIME/magic-byte detection, but v3.4 does not execute packages, so this is not a release blocker.

3. Static frontend checks are helpful but pattern-based.
   - `check:v34-authoring-ui` confirms required safety copy and catches obvious API-key/dangerous-primary-entry regressions.
   - It should be treated as a smoke check, not a complete proof of all UI security properties.

## Recommendations

1. Replace Action Mod `preconditions` / `checks` JSON textareas with fully field-level condition/check rows.
   - Keep the current token preflight until the structured rows fully cover all supported condition/check types.

2. Add a focused backend test that submits Action Mod precondition/check payloads with extra keys such as `code`, `script`, `eval`, and `exec`.
   - Expected result should be explicit rejection or deterministic stripping with no appearance in normalized YAML/test report.

3. Add a static v3.4 check for dangerous permission enabling controls.
   - Continue rejecting labels such as `enable dangerous permission`, `override dangerous permission`, and any button that implies runtime permission override.

4. Continue redacting all validation/report strings before they reach normal Authoring UI.
   - Prefer issue codes, affected IDs, safe summaries, and redacted path hints over raw exception text.

5. Keep Provider Profile Pack export/import restricted to `api_key_env` / `secret_ref`.
   - Add regression coverage for `headers.Authorization`, `x-api-key`, and nested secret fields if not already covered outside v3.4 tests.

6. Keep Rule Module contract-only until a future explicit sandbox design exists.
   - Do not add runtime loading, Python/JS execution, network access, filesystem access, or LLM calls through Rule Module paths in v3.4.

## v3.4 Release Blocker Status

This Mod Permission / Security Boundary audit does not find a high-risk blocker for v3.4 release.

However, v3.4 release readiness should still account for the separate Authoring UI privacy/visibility audit. If that audit remains blocked by raw hidden/authoring-only preview leakage, v3.4 as a whole remains blocked even though the Mod Permission / Security Boundary portion is acceptable.

Final status for this audit: **Pass with medium hardening recommendations; not independently blocking v3.4 release.**
