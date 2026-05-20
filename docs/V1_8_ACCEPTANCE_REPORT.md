# v1.8 Acceptance Report

## Verdict

Accepted with documentation caveats resolved in this freeze pass.

v1.8 is accepted as the Stable Contracts & Compatibility release for the local engine. It freezes the v1.8 compatibility boundary around GameState, StateDelta, EventLog, content packs, save migration, module/action manifests, prompt/provider profiles, import/export packages, authoring/debug APIs, and quality gate results.

## Verification Date

2026-05-21

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
python -m backend.app.tools.v2_compatibility_checklist --json
```

Observed verification:

- `python -m pytest`: `1558 passed`
- `npm.cmd run build`: passed
- v2 compatibility checklist CLI: passed for the main contract documents

## Scope Accepted

- Compatibility Boundary Contract
- Stable GameState Contract
- Stable StateDelta Contract
- Stable EventLog Contract
- Stable Content Pack Schema Contract
- Stable Save Migration Contract
- Stable Module Manifest Contract
- Stable Action Mod Contract
- Stable Prompt Profile Contract
- Stable Provider Gateway Contract
- Stable Import / Export Package Contract
- Stable Authoring API Contract
- Stable Debug API Contract
- Stable Quality Gate Contract
- Schema Version Compatibility Matrix
- Compatibility Test Suite
- Migration Failure Recovery
- Deprecated Field Policy
- Backward Compatibility Shims
- Contract Docs Generator
- v2.0 Compatibility Checklist CLI

## Boundary Review

- The world engine remains the only source of truth.
- LLMs remain language components. They do not decide compatibility, migration, gameplay results, schema repair, or direct GameState changes.
- GameState, StateDelta, and EventLog now carry stable v1.8 contract metadata while keeping legacy compatibility paths.
- StateDelta validation rejects unsupported operations and forbidden paths in the contract validation path.
- EventLog remains replay-oriented and preserves state deltas. Player-visible summaries must not contain secrets or hidden debug data.
- Save migration preserves EventLog, hidden visibility classification, module state, and save metadata.
- Migration failure recovery preserves the original save, records checksum/backup information, and requires explicit restore.
- Package import/export requires validation, compatibility checks, checksum validation, zip-slip protection, executable rejection, and secret exclusion.
- Prompt profiles cannot expand hidden fact access or state modification authority.
- Provider safe summaries do not include API keys or raw environment values.
- Debug API data remains separated from player API data.

## Known Limitations

- v1.8 does not complete v2.0. It prepares stable pre-v2.0 contracts and compatibility tooling.
- v1.8 does not primarily add new gameplay systems or large UI modules.
- Compatibility shims are intentionally narrow and best effort. Unsupported breaking changes still fail.
- Compatibility matrix entries are guidance for known contract combinations, not a promise that every old package or save is permanently supported.
- Deprecated fields are not removed immediately. They require metadata, warnings, and a migration path before removal.
- Migration failure recovery is not an automatic repair system for every corrupted save.
- Contract docs generator documents local schema constants and registry metadata; it does not replace manual release review.
- A Vite chunk-size warning remains non-blocking.
- Local PowerShell profile signing warnings may appear in command output and are not project failures.

## Acceptance Risks

- Future schema additions must include contract metadata and compatibility tests. Skipping either would weaken v1.8 guarantees.
- New compatibility shims could accidentally change visibility classification if they bypass central policy and tests.
- Package import/export safety depends on keeping the validation gate mandatory.
- Release tagging should only happen after confirming no local database, logs, cache, build outputs, backups, crash reports, or secrets are staged.

## Recommended v1.9 Priorities

- RC hardening for v2.0 readiness.
- Expand compatibility fixtures for more legacy save, content pack, module, action, prompt, and package shapes.
- Strengthen static checks for provider factory/router usage.
- Add release automation that verifies contract docs, acceptance docs, audits, tests, build, secret scan, and tracked-artifact scan.
- Improve migration diagnostics with more precise user-facing recovery messages.
- Continue tightening debug/player API isolation tests.

## Final Status

v1.8 is acceptable as a local Stable Contracts & Compatibility release once this acceptance report, release notes, and audits are committed with the v1.8 contract implementation. Tagging is recommended only after a final freeze check confirms all release documents are present and no unintended local artifacts are tracked.
