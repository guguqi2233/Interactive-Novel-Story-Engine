# v2.6 Mod Security / Permission Audit

Verification date: 2026-05-22

Scope: v2.6 Script / Mod Platform Pro implementation, including `PackageManifestV2`, `ModulePermissionSet`, pack validators, Action Mod schema/registry/evaluator, Rule Module contract, Module Browser, Import/Export hardening, Mod Quality Gate, and Mod Audit Trail.

## Passed Items

1. `PackageManifestV2` rejects executable entry points.
   - `PackageEntryPoint.path` rejects executable suffixes.
   - `PackageEntryPoint.kind` rejects `python`, `javascript`, `executable`, `shell`, and `binary`.
   - Manifest security validation also rejects executable payloads in `included_files`.

2. `ModulePermissionSet` defaults to deny dangerous permissions.
   - All permission categories default to empty dictionaries.
   - No dangerous permission is enabled by default.

3. Dangerous permissions are treated as blockers.
   - `execute_code`, `access_filesystem`, `access_network`, `read_secrets`, `write_database`, `modify_game_state_directly`, `bypass_visibility`, and `call_llm` are listed in `DANGEROUS_PERMISSION_KEYS`.
   - `validate_module_permissions()` returns errors for any requested dangerous permission.
   - `PackageManifestV2` rejects manifests whose permission report is not OK.

4. Action Mods cannot directly modify `GameState`.
   - `ModActionEvaluator` delegates to the declarative action handler and returns `ActionResult` / `StateDelta` proposals.
   - Regression tests verify the source `GameState` remains unchanged during mod action evaluation.

5. Action Mods cannot execute arbitrary code.
   - `ActionMod` rejects arbitrary-code and `call_llm` markers.
   - `ModActionEvaluator` contains no `exec`, `eval`, filesystem, network, database, or provider calls.
   - Tests scan v2.6 action mod evaluator/test harness for `exec(` and `eval(`.

6. Rule Modules do not execute runtime code.
   - `RuleModuleManifest` is contract-only in v2.6.
   - `can_execute_code`, `can_call_llm`, filesystem access, and network access are rejected when enabled.

7. Module Browser does not execute packages.
   - Module Browser scans manifests and safe summaries only.
   - No package code execution path, dynamic import, plugin execution, or provider call was found in `module_browser.py`.

8. Import dry-run does not write package files.
   - `ModImportExportService.import_dry_run()` inspects zip entries in memory and returns a report with `writes_to_disk=False`.

9. Import apply requires explicit confirmation.
   - `import_apply(..., confirm=False)` raises an error before writing.
   - Confirmed apply writes into `project/modules/imported/<package_id>` and does not enable the module.

10. Provider Profile Pack rejects raw API keys.
    - Validator rejects `api_key`, `authorization`, `x-api-key`, auth/key headers, and non-test `sk-` literals.
    - `api_key_env` and `secret_ref` remain allowed as references.

11. Mod audit normal summaries are redacted.
    - `ModAuditRecord.normal_summary()` passes `safe_summary` through `redact_text()`.
    - Audit repository constrains audit IDs with `safe_identifier()`.

12. Tests do not execute unknown mod code.
    - v2.6 tests instantiate schemas, run deterministic declarative handlers, and run known local CLI modules.
    - Tests do not execute package payloads, arbitrary scripts, real providers, or unknown module code.

## High-Risk Issues

1. Module Browser secret scan may read forbidden local files inside module directories.
   - `ModuleBrowserService._contains_secret()` recursively reads text from files under allowed module roots, skipping only `node_modules`, `dist`, and `.git`.
   - It does not currently skip `.env`, database files, log files, or cache directories before reading.
   - The scan does not return file contents, and it flags secret-like content, but the requirement is stricter: package scan should not read `.env/db/logs/cache`.
   - This should block v2.6 release until the scanner refuses these paths before opening them.

## Medium-Risk Issues

1. Mod audit redaction is API-key focused.
   - `redact_text()` redacts `sk-...` keys and private-key blocks.
   - It does not fully redact all possible `authorization: Bearer ...` or custom secret literals if a caller passes such content into `safe_summary`.
   - Current code paths pass controlled summaries, but the audit API would be safer if `ModAuditRepository.append_action()` rejected or generalized redaction for secret-like input.

2. Action Mod direct security marker scan is narrow.
   - `ActionMod` directly rejects `arbitrary_code` and `call_llm`.
   - Filesystem/network/database/state/visibility permissions are blocked through `ModulePermissionSet`, manifest validation, and import/export scanning.
   - This layered design is acceptable, but future entry points must not bypass manifest/permission validation.

## Low-Risk Issues

1. Import apply writes package files after confirmation.
   - This is expected behavior, but it should remain disabled for high-risk modules until quality gate and explicit user enable flows exist.

2. `RuleModuleManifest` allows state schema extension declarations with warnings.
   - This is contract-only and does not mutate state, but future runtime migration support will need a separate security review.

3. Provider Profile Pack export can include `api_key_env` / `secret_ref`.
   - This is intended, but exported provider packs must continue to exclude resolved secret values.

## Fix Recommendations

1. Fix release blocker in Module Browser scanning:
   - Before opening any scanned file, reject or skip forbidden names/suffixes/directories using the same policy as package import/export.
   - Explicitly avoid reading `.env`, `*.db`, `*.sqlite`, `*.sqlite3`, `*.log`, `logs/`, `cache/`, `caches/`, `node_modules/`, `dist/`, desktop outputs, backups, and crash reports.
   - Add tests proving these paths are reported as unsafe without reading their contents.

2. Strengthen audit safe-summary handling:
   - Make `append_action()` reject `contains_secret_text(safe_summary)` or apply broader redaction for authorization/header-like secrets.
   - Add a regression test that a deliberately secret-like audit summary is not persisted verbatim.

3. Keep all future module install/enable paths gated by:
   - `PackageManifestV2`,
   - `ModulePermissionSet`,
   - package-type validator,
   - Compatibility Matrix,
   - Mod Quality Gate,
   - explicit confirmation,
   - Mod Audit Trail.

4. Preserve the v2.6 non-goal:
   - Do not add arbitrary-code plugin execution or sandbox runtime without a separate design, permission model, and security audit.

## Release Blocker Status

Blocks v2.6 release until the Module Browser scan is hardened to avoid reading `.env`, database, log, and cache files.

The rest of the reviewed permission and execution boundaries are consistent with v2.6 goals: dangerous permissions are blocked, Action Mods remain declarative, Rule Modules are contract-only, import apply requires confirmation, and Provider Profile Packs do not store real API keys.
