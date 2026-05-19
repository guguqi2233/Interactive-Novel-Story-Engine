# v1.5 Visibility / Prompt / Context Audit

Verification date: 2026-05-20

Scope:

- v1.5 Prompt Lab context, prompt, benchmark, A/B, style, diagnostics,
  compatibility, usage, token budget, and experiment package flows.
- Frontend Prompt Lab normal UI surfaces.
- Existing narrator/context boundaries where they interact with v1.5.

This audit generated a documentation report only. No business code was changed.

## Audit Summary

Verdict: pass with non-blocking cautions.

Blocking status: no high-risk visibility/prompt/context leak was found for
v1.5.

The v1.5 implementation keeps Prompt Lab output in redacted, local-only reports.
Hidden facts, NPC secrets, debug memory, raw prompts, and raw state deltas are
not intended to appear in normal Prompt Lab UI or prompt reports. Debug raw
context inspection exists, but it is opt-in and redacted.

## Passed Items

1. Hidden facts do not enter normal context snapshots

   `Context Inspector` classifies non-visible facts as `hidden_redacted` and
   emits safe summaries such as ids plus redaction markers. Normal safe dumps
   redact known synthetic hidden text and secret patterns.

2. Hidden facts do not enter prompt reports by default

   Benchmark, structured output, A/B, style lab, voice lab, prompt regression,
   diagnostics, and experiment package reports use safe summaries or redacted
   payloads. v1.5 integration tests assert hidden sentinel text is absent from
   serialized reports.

3. NPC secrets do not enter Prompt Lab normal UI

   Prompt Lab frontend displays safe summaries, counts, flags, and findings. It
   does not display NPC secret fields or hidden authoring text in the normal
   Prompt Lab page.

4. Debug memory does not enter normal Context Inspector

   Memory summary inspection excludes hidden/debug-only memories and records
   exclusion reasons rather than content. Normal sections use redacted
   summaries.

5. Raw state deltas do not enter Prompt Lab normal view

   v1.5 context snapshots do not include raw `state_deltas` in normal sections.
   Prompt Diff, Token Budget, Benchmark, A/B, and Usage views do not surface raw
   delta payloads.

6. Prompt Diff does not display hidden text

   `PromptDiffReport.model_dump_safe()` strips API-key-like values, hidden fact
   text, NPC secret text, and secret keys. It flags relaxed hidden/state
   policies as blockers instead of rendering hidden content.

7. Benchmark reports do not display hidden text

   `ProviderBenchmarkCase.redacted_prompt_preview()` redacts configured hidden
   terms and secret patterns. Output summaries are short and secret-redacted.

8. A/B reports do not display hidden text

   Prompt A/B test cases support hidden terms, and reports are serialized via
   safe dump paths. Integration coverage verifies the hidden sentinel is absent.

9. Compatibility matrix does not display hidden prompts

   The compatibility matrix is derived from declared capabilities and local
   result summaries. It does not include raw prompt cases or hidden prompt text.

10. Usage dashboard does not display raw prompt

   `ModelUsageRecord` stores provider/model/use_case, duration, token estimates,
   cost estimates, success/failure, and error type. The frontend shows usage
   metadata only.

11. Token budget reports do not display hidden facts

   Token Budget drops `hidden_redacted` sections from trimmed context and flags
   a blocker if a hidden section would enter the final context. Safe report dumps
   strip sensitive text.

12. Prompt Experiment Package does not contain hidden facts全文

   Export validation rejects hidden facts, NPC secrets, raw `GameState`, raw
   state deltas, sensitive prompt snapshots, and API-key-like text. Test cases
   are redacted before packaging.

13. Local diagnostics do not send hidden prompt by default

   Local diagnostics use synthetic safe messages. Fake transport rejects hidden
   or secret terms if they appear in diagnostic payloads.

14. Frontend Prompt Lab does not show debug context in ordinary areas

   The Prompt Lab normal page shows redacted summaries, counts, and status
   labels. Raw context is gated behind an explicit "Debug raw redacted" checkbox
   and rendered as redacted debug raw prompt.

15. Narrator remains isolated from raw state deltas

   v1.5 Prompt Lab does not route raw state deltas into narrator prompts.
   Existing narrator boundary tests continue to assert hidden facts and raw
   deltas do not enter player-facing narrative prompt snapshots.

## Possible Leak Paths

1. Context Inspector debug raw mode

   `include_debug_raw=true` can include a redacted raw prompt view. The current
   output is redacted, but this remains the most sensitive Prompt Lab context
   surface and must stay debug-only.

2. Synthetic hidden terms in eval fixtures

   Some tests and default hidden-refusal cases use synthetic hidden sentinel
   strings. Current reports redact them. Future test authors must avoid copying
   real world hidden facts into reusable prompt cases.

3. Frontend debug/event panels outside Prompt Lab

   The broader Studio frontend contains debug/timeline panels that can display
   `state_deltas`. This is outside the normal Prompt Lab UI, but it should
   remain gated as debug/local tooling and must not feed narrator/player UI.

4. Safe summaries containing ids

   Context snapshots may show hidden fact ids or exclusion ids as redacted
   references. This is acceptable for local authoring/debug context, but should
   not be copied into player UI or normal exports.

## High-Risk Leaks

No high-risk v1.5 visibility/prompt/context leak was found.

The audit did not find:

- hidden fact text in normal context snapshots,
- hidden fact text in Prompt Lab normal reports,
- raw prompt text in usage records,
- raw state deltas in Prompt Lab normal view,
- Prompt Experiment Package export of hidden fact text by default.

## Medium-Risk Leaks

1. Debug raw context inspection remains sensitive

   Impact: medium.

   The explicit raw context toggle is redacted and off by default. If reused in
   normal UI without debug labeling, it could become a leak path.

   Status: not blocking.

2. Broader frontend debug state delta panels require local/debug gating

   Impact: medium.

   Raw `state_deltas` are visible in debug/timeline surfaces outside Prompt Lab.
   This is acceptable for local debug, but must never be reused by narrator,
   player UI, prompt reports, or exports.

   Status: not blocking for v1.5 Prompt Lab.

3. Hidden ids in safe summaries may reveal entity existence

   Impact: medium-low.

   Context Inspector may show hidden ids in redacted summaries. This is useful
   for local diagnosis, but normal player-facing UI must not consume it.

   Status: not blocking.

## Small Issues

1. The Prompt Lab frontend labels the raw prompt details as "Redacted debug raw
   prompt"; this is clear, but future UI should keep it visually separated from
   normal report cards.

2. Some redaction checks use string matching for sentinel hidden phrases. This
   works for current fixtures but should be supplemented by structured hidden
   ids wherever possible.

3. Existing non-v1.5 memory summarization paths can summarize event delta
   payloads. Existing narrator/prompt tests cover player-facing leakage, but
   this should remain in the broader prompt-boundary watchlist.

## Fix Recommendations

1. Keep `include_debug_raw` disabled by default and render it only with debug
   labeling and redacted output.

2. Preserve v1.5 integration tests that assert hidden sentinel text is absent
   from benchmark, A/B, style, voice, context, usage, package, and regression
   reports.

3. Add future regression coverage to prove Prompt Lab frontend never renders
   `raw_prompt_redacted` unless the user explicitly enables the debug raw
   checkbox.

4. Keep debug/timeline `state_deltas` outside normal Prompt Lab and player UI.

5. Prefer hidden ids and structured leak flags over hidden text in all future
   prompt lab reports.

## v1.5 Blocking Status

Does this block v1.5: no.

The current visibility/prompt/context boundary is acceptable for v1.5
acceptance, assuming the broader security audit and full regression/build runs
also pass.
