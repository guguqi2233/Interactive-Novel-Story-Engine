# v1.8 Release Notes

## Version Name

v1.8 - Stable Contracts & Compatibility

## Release Goal

v1.8 is the pre-v2.0 stable contract release. It focuses on freezing compatibility rules, schema/version metadata, migration behavior, package validation, and contract documentation so v1.9 can harden the project toward a v2.0 platform milestone.

This release does not primarily add new gameplay systems. The LLM is still not the world judge, and the local world engine remains the source of truth.

## New Features

- Compatibility Boundary Contract for versioning, migrations, deprecated fields, shims, and breaking-change rules.
- Stable contracts for GameState, StateDelta, EventLog, content packs, save migration, module manifests, Action Mods, Prompt Profiles, Provider Gateway, packages, authoring/debug APIs, and Quality Gate.
- Schema Version Compatibility Matrix API/CLI.
- Compatibility Test Suite under `backend/tests/compatibility/`.
- Migration Failure Recovery with pre-migration checksum, backup creation, failed-attempt records, recovery plan, and explicit restore.
- Deprecated Field Policy and generated deprecated-field documentation.
- Backward Compatibility Shims for safe field rename/default/legacy detection cases.
- Contract Docs Generator for `CONTRACT_INDEX`, schema matrix, and deprecated fields.
- v2.0 Compatibility Checklist CLI.

## Behavior Changes

- New v1.8 contract paths require explicit `contract_version` for packages, module manifests, Action Mods, prompt profiles, provider metadata, and related manifests.
- Legacy inputs may go through compatibility shims and warnings where safe, but unsupported breaking versions still fail.
- StateDelta contract validation rejects invalid operations, forbidden paths, and hidden-to-visible mutations outside rule-controlled paths.
- Package import performs compatibility checks as part of the safety gate.
- Migration apply records recovery metadata before changing save data.

## Contract Changes

- `GameState`, `StateDelta`, and `Event` include stable contract metadata.
- EventLog contract keeps events replayable and prevents player-facing event summaries from carrying secrets or hidden debug payloads.
- Prompt Profile contract keeps hidden fact access and state modification denied.
- Provider Gateway contract keeps safe summaries secret-free and preserves the factory/router entry point.
- Quality Gate results include contract metadata, stable target type, redaction policy, blockers, warnings, and report references.

## Schema / Migration Changes

- Save migration contract now requires before/after validation, migration history, EventLog preservation, hidden visibility preservation, and backup/rollback policy.
- Migration failure recovery does not overwrite the original save on failure.
- Deprecated fields require metadata with replacement and migration strategy.
- Missing schema/contract metadata in old content can be handled through legacy compatibility where explicitly allowed.

## Compatibility Changes

- Compatibility matrix statuses include compatible, migration-required, deprecated, unsupported, and unknown.
- Compatibility shims are intentionally minimal. They can warn and fill safe defaults, but they cannot make hidden data visible or hide unsupported breaking changes.
- Compatibility matrix does not mean all old content is permanently supported.

## Import / Export Changes

- Local package manifests now require contract version, schema version, checksums, dependencies/conflicts, and redaction policy.
- Package import rejects zip slip, executable files, checksum mismatch, unsupported contract versions, and sensitive files.
- Safe exports continue to exclude `.env`, API keys, logs, caches, databases, raw environment values, and hidden text by default.
- Import dry-run must not write disk; import apply requires explicit confirmation.

## Testing Changes

- Added compatibility regression tests for legacy saves, legacy content/package/module/action/profile paths, hidden visibility preservation, contract-version enforcement, checksum mismatch, migration failure recovery, deprecated fields, generated contract docs, and v2 checklist.
- Full backend suite passed: `1558 passed`.
- Frontend build passed with a non-blocking Vite chunk-size warning.

## Known Limitations

- v2.0 is not complete.
- v1.8 does not promise indefinite support for every old save, world pack, module, prompt profile, or package.
- Migration failure recovery is not an automatic repair system for all corrupted saves.
- Deprecated fields are not removed immediately, but future removal still requires migration and compatibility review.
- Compatibility matrix is a local compatibility guide, not a formal platform marketplace guarantee.
- Contract docs generator does not replace manual audit and acceptance review.

## Upgrade Notes From v1.7

- Existing v1.7 saves and content should continue through compatibility and migration paths where supported.
- New package/module/action/prompt/provider artifacts should include v1.8 contract metadata.
- Run compatibility tests and matrix checks before packaging or tagging:

```powershell
python -m backend.app.tools.compatibility_matrix
python -m backend.app.tools.generate_contract_docs
python -m backend.app.tools.v2_compatibility_checklist
python -m pytest backend/tests/compatibility
```

- Do not bypass package validation, save migration validation, or Quality Gate checks.

## Recommended v1.9 Direction

- RC hardening for v2.0 platform readiness.
- Broader legacy fixture coverage.
- Release automation for contract docs, checklist, secret scan, tests, build, and tracked-artifact scan.
- Stronger provider factory/router static checks.
- More detailed migration diagnostics and recovery UX.
