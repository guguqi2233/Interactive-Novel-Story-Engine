# v2.0 Release Candidate Checklist

This checklist records the readiness gates that must pass before entering a
future v2.0 platform release. It does not claim that v2.0 is complete.

## Contract Readiness

- [ ] GameState contract remains stable.
- [ ] StateDelta contract remains stable.
- [ ] EventLog contract remains stable.
- [ ] Content Pack schema contract remains stable.
- [ ] Save Migration contract preserves EventLog and visibility.
- [ ] Module Manifest and Action Mod contracts reject unsafe permissions.
- [ ] Prompt Profile contract cannot expand hidden/state permissions.
- [ ] Provider Gateway contract keeps secrets server-side.
- [ ] Package contract checks version, checksum, zip slip, executable files, and
  secrets.
- [ ] Authoring, Debug, and Quality Gate contracts remain isolated.

## Tooling Readiness

- [ ] `python -m backend.app.tools.v2_compatibility_checklist --json` passes.
- [ ] `python -m backend.app.tools.v2_release_candidate_checklist --json` passes.
- [ ] `python -m backend.app.tools.compatibility_matrix` runs.
- [ ] `python -m backend.app.tools.generate_contract_docs --check` passes.
- [ ] `python -m backend.app.tools.release_checklist --version v1.9 --json`
  passes.
- [ ] Compatibility tests pass.

## Migration Readiness

- [ ] Legacy saves migrate in dry-run and apply modes.
- [ ] Migration failure preserves the original save.
- [ ] Pre-migration backups can be restored with explicit confirmation.
- [ ] Hidden visibility classification remains unchanged.

## Package / Import / Export Readiness

- [ ] Safe export excludes `.env`, API keys, logs, caches, databases, and build
  artifacts.
- [ ] Import dry-run does not write user content.
- [ ] Import apply requires validation and explicit confirmation.
- [ ] Zip slip and executable files are rejected.

## Security / Privacy Readiness

- [ ] No real API keys in tracked files.
- [ ] No local artifacts are tracked.
- [ ] Logs and crash reports are local-only and redacted.
- [ ] Debug APIs remain gated.
- [ ] Tests use fake/mock/local providers by default.

## Content / Desktop Readiness

- [ ] Sample world passes validation and quality smoke.
- [ ] Starter templates validate and contain no secrets.
- [ ] Desktop startup diagnostics are documented.
- [ ] Error recovery plans avoid destructive automatic operations.

## Known v1.9 Warnings

- Slow 1000+ turn runs should be explicit, not default pytest behavior.
- Performance budgets are local estimates, not universal machine guarantees.
- Compatibility matrix is not a promise of indefinite support for every old
  package shape.

## Entry Criteria for v2.0

Enter v2.0 only when all release blockers are closed, tests and frontend build
pass, v1.9 release checklist passes, and the final audits report no high-risk
blockers.
