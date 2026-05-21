# Release Candidate Boundary

v1.9 is a Release Candidate hardening milestone for the local AI Narrative
Studio. It is not a feature expansion release. Its job is to prove that the
v1.8 contracts, local quality gates, migration recovery, package safety,
desktop startup path, documentation, and release checks are ready to support a
future v2.0 platform milestone.

## Definitions

- `release_candidate`: a locally verified build candidate with tests, build,
  compatibility, security, documentation, and quality gates passing.
- `release_blocker`: any issue that prevents a release candidate from being
  tagged.
- `high_risk_blocker`: failing tests, failing frontend build, hidden fact leak,
  LLM authority violation, migration corruption, package import security risk,
  real API key leak, tracked local artifacts, missing release docs, or failing
  v2 compatibility checklist.
- `medium_risk_warning`: a documented limitation that does not break safety,
  compatibility, or release verification.
- `release_checklist`: the local checklist that aggregates docs, security,
  compatibility, quality gate, and optional runtime checks.
- `long_run_validation`: deterministic playtest or batch playtest coverage
  using fake/mock/local providers and temporary data.
- `final_security_audit`: local-only review for secrets, package safety,
  tracked artifacts, redaction, and controlled debug surfaces.
- `final_quality_gate`: deterministic quality gate output; it never auto-fixes
  content or calls a real LLM.

## Release Blockers

The following must fail v1.9 release:

- `python -m pytest` failure.
- frontend build failure.
- Any hidden fact, NPC secret, raw prompt, raw env, or API key entering normal
  player-facing or release reports.
- LLM output directly modifying `GameState` or deciding world facts.
- Migration failure corrupting the original save or losing EventLog data.
- Package import/export zip slip, executable-file acceptance, or secret leak.
- Real API key or secret committed to the repository.
- `.env`, database, logs, cache, frontend build output, backups, crash reports,
  or desktop build outputs tracked by git.
- Missing v1.9 acceptance, release notes, audit, roadmap, boundary, or v2.0 RC
  checklist docs.
- Failing v2 compatibility checklist.

## Allowed Warnings

Warnings may be documented without blocking release when they do not weaken
safety or compatibility. Examples include machine-dependent benchmark variance,
Vite chunk-size warnings with a successful build, or optional slow playtests not
run during a quick local checklist.

## Boundaries

- The LLM remains a language layer and never becomes the world judge.
- Release and quality checks do not mutate active saves.
- Long-run and stress tests use temporary data and mock/local providers.
- Release checklists do not commit, tag, upload, or auto-fix anything.
- Debug data and hidden content stay out of player APIs and normal reports.

