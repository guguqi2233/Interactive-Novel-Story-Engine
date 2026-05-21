# v1.9 Roadmap - Release Candidate Hardening

## Version Theme

Release Candidate Hardening.

## Goal

v1.9 stabilizes the local studio before a future v2.0 platform milestone. It
focuses on release gates, long-run confidence, migration safety, compatibility,
performance budgets, documentation, and final security review. It does not add a
large gameplay system or change the v1.8 stable contracts.

## Explicit Non-Goals

- New major gameplay systems.
- New large UI workspaces.
- LLM world judgment or direct `GameState` modification.
- Arbitrary-code plugins.
- Online marketplace, cloud sync, accounts, or collaboration.
- Breaking v1.8 contracts, old saves, old content packs, or module contracts.
- Treating local performance budgets as absolute across all machines.

## Implemented / Targeted Scope

1. Release Candidate Boundary Contract.
2. Full Quality Gate hardening through the existing standard quality gate.
3. Deterministic playtest and batch playtest coverage, with slow long-run runs
   executed explicitly.
4. Save/load/migration stress coverage.
5. Module compatibility stress coverage.
6. Prompt regression hardening with fake/mock providers by default.
7. Hidden leak regression hardening across normal reports.
8. Performance budget finalization through benchmark p50/p95/max reports.
9. Sample world and starter template polish.
10. Desktop startup and error recovery polish.
11. Documentation finalization.
12. Release checklist automation.
13. Final security audit.
14. v2.0 Release Candidate checklist.

## Recommended Order

1. Boundary and checklist docs.
2. Release checklist CLI.
3. Quality/stress/performance verification.
4. Documentation and README synchronization.
5. Audits, acceptance report, release notes.
6. Final freeze check and tag review.

## Acceptance Criteria

- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.
- `python -m backend.app.tools.v2_compatibility_checklist --json` passes.
- `python -m backend.app.tools.release_checklist --version v1.9 --json` passes.
- No tracked local artifacts or real API keys.
- v1.9 release docs and audits exist.
- High-risk blockers cannot be ignored by release checklist.

## LLM / Visibility / Security

v1.9 does not expand LLM authority. Prompt regression, benchmarks, playtests,
quality gates, and release checks use deterministic code and fake/mock/local
providers by default. Hidden facts, NPC secrets, raw prompts, raw env, API keys,
and debug data are redacted from normal reports.

## v2.0 Preparation

v1.9 prepares v2.0 by proving contract stability, release gate coverage,
security posture, documentation completeness, and local-only operational
readiness. v2.0 is not declared complete by this roadmap.

