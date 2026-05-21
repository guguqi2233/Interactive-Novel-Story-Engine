# v1.9 Release Notes

## Version Name

v1.9 - Release Candidate Hardening.

## Version Goal

v1.9 prepares the local AI Narrative Studio for a future v2.0 platform milestone
by hardening release checks, quality gates, stress coverage, performance budget
reporting, compatibility verification, documentation, and security review.

## New Functionality

- v1.9 release checklist CLI.
- Release Candidate boundary documentation.
- v2.0 Release Candidate checklist documentation.
- Final v1.9 audit and acceptance document set.

## Behavior Changes

- v1.9 does not change the world authority model.
- LLM output still cannot directly modify `GameState`.
- Release checklist does not auto-fix, commit, tag, upload, or run real
  providers.

## Hardening Changes

- Standard quality gate is treated as the local aggregate gate.
- Playtest, batch playtest, save/load stress, module compatibility stress, and
  benchmark budget output are documented as v1.9 hardening inputs.

## Quality Gate Changes

The quality gate aggregates validation, hidden leak regression, scenario smoke,
save/load/migration stress, benchmark smoke, and module compatibility smoke.

## Long-run / Stress Test Changes

Long-run and stress checks default to deterministic fake/mock/local paths.
1000+ turn runs are explicit slow gates rather than default pytest behavior.

## Prompt / Hidden Leak Regression Changes

Prompt and hidden leak reports remain redacted. They do not allow an LLM to judge
pass/fail or write state.

## Performance Budget Changes

Benchmark reports include p50, p95, max, and budget metadata. These budgets are
local estimates, not absolute guarantees across all machines.

## Sample World / Starter Templates

Sample world and starter templates remain local examples. They are not complete
commercial content.

## Desktop / Recovery

Desktop startup, diagnostics, logs, crash reports, and recovery surfaces remain
local-only and redacted.

## Release Checklist

Use:

```bash
python -m backend.app.tools.release_checklist --version v1.9 --json
```

The checklist validates release docs, README guidance, tracked artifacts,
secret scans, v2 compatibility docs, quality gate status, and optional runtime
checks.

## Known Limitations

- v2.0 is not complete.
- Compatibility matrix does not promise indefinite support for every old shape.
- Release checklist reports blockers but does not repair them.
- Performance budgets vary by local machine.

## Upgrade Notes from v1.8

v1.8 stable contracts remain in force. Package import/export still requires
validation and compatibility checks. Deprecated fields are not removed without a
documented migration path.

## Recommended v2.0 Direction

Proceed to final v2.0 RC only after tests, frontend build, release checklist,
v2 compatibility checklist, and final audits pass without high-risk blockers.
