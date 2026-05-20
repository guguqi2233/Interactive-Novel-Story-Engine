# v1.8 Security, Package, and Migration Audit

Verification date: 2026-05-21

## Passed Items

- `.env` is not tracked by git.
- Git tracked-file checks did not show databases, logs, caches, `frontend/dist`, desktop build outputs, backups, or crash reports.
- Package import performs zip-slip protection and rejects executable files by default.
- Package export/import contracts exclude `.env`, API keys, logs, caches, and database files by default.
- Package manifests require `contract_version`, checksum validation, redaction policy, and compatibility checks.
- Migration failure recovery creates a pre-migration backup, records checksum information, preserves the original save on failure, and exposes an explicit restore path.
- Provider safe summaries do not include API keys or raw environment values.
- Compatibility tools operate on repository-local schema constants, docs, and fixtures. They do not read arbitrary root-external files.
- Tests use fake/local/mock providers and fake key strings for redaction coverage. They do not require real external API calls.
- The `sk-...` scan only found fake/test keys in tests and historical audit notes.
- Debug and authoring APIs remain controlled by their existing local feature flags.

## High-Risk Issues

No high-risk package, migration, or secret handling issue was identified for v1.8.

## Medium-Risk Issues

- A local `world_engine.db` exists in the workspace root. It is not tracked or staged, but it must remain ignored and must not be included in release commits or packages.
- v1.8 release-freeze docs were missing before this documentation pass. Final tagging should re-run the freeze check.

## Small Issues

- PowerShell profile signing warnings appear in local command output. They are machine configuration noise, not project security failures.
- Vite emits a chunk-size warning during frontend build. It is not a security blocker.

## Fix Recommendations

- Keep `.env`, database files, logs, caches, build outputs, backups, and crash reports ignored.
- Keep package import validation order strict: path safety, executable rejection, manifest contract version, checksum, compatibility, then dry-run/apply.
- Continue using fake key fixtures only for redaction tests.
- Re-run `git ls-files` and secret scans before tagging.

## Release Impact

This audit does not block v1.8 release, provided the final freeze check confirms release notes, acceptance report, and audit documents are present.
