# v1.9 Visibility / Privacy / Leak Audit

## Passed Items

- Normal quality and benchmark reports use safe summaries and redaction helpers.
- Hidden leak regression tests cover player visible state, narrator/dialogue
  prompts, reports, logs, crash reports, exports, and debug separation.
- Backup/export and package profiles reject secrets and hidden text in safe
  outputs.
- Debug APIs remain separate from player APIs.

## Possible Leak Paths

- Future report types must reuse existing normal-report redaction helpers.
- Slow long-run reports should store ids/counts/safe summaries rather than raw
  hidden text.

## High-Risk Leaks

None found.

## Medium-Risk Leaks

- Test fixtures intentionally contain fake secrets and hidden text to validate
  redaction. They should remain clearly marked as fixtures.

## Low-Risk Issues

- Some older docs mention hidden leak examples; they are not normal runtime
  reports.

## Recommendations

- Keep hidden text out of release checklist output.
- Keep crash/log viewers local-only and redacted.

## Blocks v1.9

No visibility/privacy blocker identified.

