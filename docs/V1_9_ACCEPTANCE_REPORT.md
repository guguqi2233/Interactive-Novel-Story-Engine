# v1.9 Acceptance Report

## Verdict

Accepted for local v1.9 Release Candidate Hardening, subject to final command
verification on the target machine before tagging.

## Verification Date

2026-05-21

## Verification Commands

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- `python -m backend.app.tools.v2_compatibility_checklist --json`
- `python -m backend.app.tools.release_checklist --version v1.9 --json`

## Scope Accepted

- Release Candidate Boundary.
- Standard quality gate hardening using the existing aggregate gate.
- Deterministic playtest and batch playtest paths.
- Save/load/migration stress.
- Module compatibility stress.
- Prompt regression and hidden leak regression redaction.
- Performance budget reporting through benchmark p50/p95/max output.
- v1.9 release checklist automation.
- Final LLM, visibility, compatibility, performance, and security audits.

## Boundary Review

The LLM remains a language layer and does not modify `GameState`. The world
engine remains the source of truth. State changes still flow through
`StateDelta` and events. Release tools are local-only and do not upload reports
or call real providers by default.

## Known Limitations

- v1.9 is not v2.0.
- 1000+ turn long-run checks are explicit slow gates.
- Performance budgets are local estimates.
- Release checklist reports issues but does not auto-fix them.
- Sample world polish is not commercial content completeness.

## Acceptance Risks

- Final tag should not be created unless pytest, frontend build, v2
  compatibility checklist, and v1.9 release checklist pass in the final working
  tree.

## Recommended v2.0 Priorities

- Complete final RC soak runs.
- Expand third-party-like module/package fixtures.
- Keep documentation and release checklist aligned with actual commands.

## Final Status

Ready for final freeze checks after command verification.

