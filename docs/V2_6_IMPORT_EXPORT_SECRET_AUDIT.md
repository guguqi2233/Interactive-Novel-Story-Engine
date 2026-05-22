# v2.6 Import / Export / Secret Audit

## Scope

This audit reviews the v2.6 Script / Mod Platform Pro import/export and secret
boundaries for local extension packages. It focuses on `ModImportExportService`,
package path validation, package-type validators, provider profile pack handling,
checksums, duplicate package detection, import confirmation, and mod audit
summaries.

This is a read-only security audit. It does not modify business code.

## 已通过项目

1. Mod import rejects zip slip and path traversal.
   - `validate_relative_package_path()` rejects absolute paths, empty paths, and
     `..` path segments.
   - `import_apply()` revalidates members before writing and checks resolved
     destination paths stay under the import target.

2. Mod import rejects executable payloads.
   - v2.6 blocks executable suffixes including `.py`, `.js`, `.sh`, `.ps1`,
     `.bat`, `.cmd`, `.exe`, `.dll`, and `.com`.
   - `PackageManifestV2` also rejects executable entry points and executable
     included files.

3. Mod import rejects secret-like content.
   - `contains_secret_text()` catches `sk-...` style keys, private-key blocks,
     and generic API-key/authorization markers.
   - Provider Profile Pack import uses stricter JSON inspection for raw
     `api_key`, `authorization`, `x-api-key`, and secret-like headers.

4. Mod export filters `.env`, database, log, cache, `node_modules`, and
   frontend `dist` paths.
   - Export validates every relative package path before reading file bytes.
   - Forbidden names, suffixes, and directories are rejected by the common
     package path policy.

5. Mod export filters API keys and provider secrets.
   - Export refuses files containing secret-like text.
   - Provider Profile Pack export only permits safe references such as
     `api_key_env` and `secret_ref`; raw keys and authorization headers are
     blocked.

6. Prompt/Profile packs reject secrets and forbidden authority flags.
   - Prompt Profile Pack validation blocks secret-like text and flags such as
     `can_access_hidden_facts`, `can_modify_state`,
     `can_override_action_result`, and `can_bypass_visibility`.

7. Character packs avoid private material in public summaries.
   - `CharacterPack.safe_summary()` excludes keys containing `private` or
     `secret` from the public preview.
   - Character pack validation checks for secret-like content.

8. World extension packs check hidden leak markers.
   - World extension validation rejects hidden/debug/raw delta markers such as
     `hidden_fact`, `npc_secret`, `debug_memory`, and `raw_state_delta`.

9. Script packs reject executable and hidden-leak payloads.
   - Script Pack v2 validation blocks executable entries, secrets, and hidden
     leak markers in player-facing script/template sections.

10. Package checksums are supported and validated.
    - Manifest checksum entries require `sha256:<hex>` format.
    - Import dry-run computes archive member SHA-256 values and reports
      mismatches.

11. Duplicate `package_id` is detected.
    - Import dry-run checks the existing local module browser index and reports
      duplicate package IDs.

12. Import apply requires explicit confirmation and does not auto-enable modules.
    - `import_apply()` raises if `confirm=False`.
    - Successful import returns `enabled=False`, so imported packages are not
      automatically activated.

13. Existing regression coverage includes import/export security cases.
    - v2.6 tests cover zip slip rejection, executable rejection, secret
      rejection, duplicate package ID handling, explicit import confirmation,
      provider pack safe export, and secret export rejection.

## 高风险问题

1. Import dry-run records forbidden path errors but still reads forbidden entry
   bytes.
   - In `ModImportExportService.import_dry_run()`, each zip member is validated,
     but the loop continues to `archive.read(name)` even after
     `validate_relative_package_path(name)` fails.
   - This means a package containing `.env`, database files, logs, cache files,
     forbidden build outputs, or zip-slip paths is rejected, but its bytes may
     still be loaded into memory for secret scanning.
   - No content is returned to the caller in the normal report, but v2.6's
     boundary requires forbidden sensitive package paths to be rejected without
     reading their payloads.
   - Release impact: high. This should be fixed before v2.6 acceptance.

2. Module Browser secret scanning can read forbidden local files inside module
   directories.
   - `ModuleBrowserService._contains_secret()` recursively reads small files
     under package roots and skips only `node_modules`, `dist`, and `.git`.
   - It does not currently reuse `validate_relative_package_path()` before
     reading each file, so `.env`, database, log, cache, backup, or crash-report
     files placed under a module directory may be read during scan.
   - This affects local scan/review, not export output, but it is part of the
     same import/export/secret boundary for module packages.
   - Release impact: high. This should be fixed before v2.6 acceptance.

## 中风险问题

1. Mod audit redaction is narrower than secret detection.
   - `ModAuditRepository.append_action()` and `normal_summary()` apply
     `redact_text()`.
   - `redact_text()` redacts `sk-...` and private-key blocks, but does not
     redact all generic `authorization`, `bearer`, or `api_key=value` forms
     that `contains_secret_text()` would flag.
   - Controlled v2.6 module APIs generally write safe summaries, but a future
     caller could pass a generic authorization string into an audit summary and
     persist it.
   - Recommended severity: medium, because no current reviewed path intentionally
     writes such data, but the audit boundary should be made as strict as the
     secret detector.

2. Import/export service is not fully wired into Mod Audit Trail.
   - Module API operations record scan/validate/certify audit entries.
   - The direct import/export service path does not currently append
     `import_dry_run`, `import_apply`, or `export` audit records by itself.
   - This is more of an audit-completeness issue than a secret leak, but it
     matters for v2.6 traceability.

3. Checksums validate declared files, but undeclared extra files are still
   scanned and may be accepted if safe.
   - The implementation validates checksums listed in the manifest.
   - It also scans every archive member for forbidden paths, executables, and
     secrets.
   - However, it does not require every non-manifest file to appear in
     `included_files` or `checksums`.
   - Recommended severity: medium/low depending on the desired strictness of the
     package contract. For a release quality gate, requiring declared files would
     improve supply-chain clarity.

## 小问题

1. Forbidden path reporting is coarse.
   - Reports identify the path problem, but do not categorize whether the issue
     is zip slip, forbidden name, forbidden suffix, or forbidden directory.
   - This is acceptable for blocking import, but less helpful for authoring UX.

2. Provider Profile Pack safe export is metadata-only at the service result
   level.
   - `ModExportResult` returns checksums and file counts, not an archive.
   - Current checks confirm no secret appears in export metadata, but future
     package archive export should retain the same provider-secret filtering.

3. Character private-field filtering is key-name based.
   - Public summaries drop keys containing `private` or `secret`, which is safe
     for current fixtures.
   - Future schemas should prefer explicit visibility fields to avoid relying
     only on key names.

## 修复建议

1. Fix import dry-run to skip reading any zip member after path validation fails.
   - If `validate_relative_package_path(name)` raises, record the error and
     continue to the next archive member without `archive.read(name)`.
   - Also skip checksum reads for paths that fail validation.

2. Reuse package path validation before Module Browser reads package files.
   - `_contains_secret()` and `_contains_executable()` should compute a relative
     path from the package root and call `validate_relative_package_path()`.
   - Forbidden files should be reported as unsafe without reading their content.

3. Expand audit redaction to match secret detection.
   - Redact generic `authorization`, `bearer`, `api_key`, `x-api-key`, and
     private key variants in `redact_text()`.
   - Add a focused test that audit summaries cannot persist these strings.

4. Wire Mod Import / Export into Mod Audit Trail.
   - Record safe `import_dry_run`, `import_apply`, `export`, and `reject`
     audit entries.
   - Ensure audit summaries use structured reasons and never include file
     contents.

5. Consider enforcing manifest-declared files for import.
   - Treat undeclared extra files as warnings or blockers depending on package
     type.
   - This would tighten checksum and supply-chain review without enabling code
     execution.

## 是否阻塞 v2.6

Yes. The current v2.6 import/export/secret boundary has high-risk blockers:

- Import dry-run rejects forbidden paths but still reads forbidden archive member
  bytes.
- Module Browser scan can read forbidden local files under module directories
  while looking for secrets.

The export side is substantially stronger because it validates paths before
reading file bytes. Provider Profile Pack, Prompt Profile Pack, Character Pack,
World Extension Pack, and Script Pack validators cover the main secret and
hidden-leak cases. However, v2.6 release acceptance should wait until the two
high-risk read-before-skip paths are fixed and covered by focused regression
tests.
