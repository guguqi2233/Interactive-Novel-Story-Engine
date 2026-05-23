# v3.1 Novel LLM Boundary Audit

Verification Date: 2026-05-23

Scope: v3.1 Novel Studio UI Pro LLM authority, Provider Gateway usage, prompt
context visibility, draft/version storage, Cross-Mode boundaries, tests, and
quality checks.

This audit is documentation-only. It does not modify business code.

## 已通过项目

1. Novel draft generation has an explicit Provider Gateway integration path.

   Existing integration tests route `novel_draft` through `ProviderGateway`
   before constructing `NovelDraftGenerationService`. The routed provider is a
   mock/local stub provider, and tests assert that hidden sentinels, API-key-like
   values, and raw `state_delta` strings do not enter provider messages.

2. Novel rewrite and summary share the same generation service boundary.

   `NovelDraftGenerationService` exposes rewrite and summary methods through the
   same internal `_generate` flow used for draft generation. That flow validates
   prompt context and generated output for secret-like strings and raw
   `state_delta` markers before returning structured data.

3. `NovelPromptContext` filters hidden and secret-bearing payloads.

   `NovelPromptContext.validate_no_hidden_or_secrets` rejects API-key-like
   strings, raw `state_delta` markers, and secret-like text before provider use.
   Prompt context construction uses safe project prompt profiles and safe
   character summaries.

4. World Bible hidden entries are excluded from normal prompt context.

   `NovelWorldBibleContextBuilder` skips hidden World Bible entries in normal
   context. Debug metadata may record excluded IDs/counts, but hidden text is not
   included in normal prompt context.

5. Character private notes are excluded from normal Novel prompt context.

   Character context uses safe summaries rather than private notes. Existing
   Novel tests check that private/hidden character text does not appear in
   normal context.

6. Raw `state_deltas` are blocked from Novel prompt context.

   Prompt validation and World-to-Novel preview filtering reject raw
   `state_delta` markers. Normal Novel UI and prompt context are expected to
   show safe summaries, IDs, counts, or redacted labels instead.

7. Draft version snapshots do not store provider prompts.

   `NovelDraftSnapshot` / `DraftVersionService` store user draft text and safe
   metadata only. Snapshot validation rejects secret-like text, hidden fact
   markers, raw `state_delta`, and raw prompt markers.

8. Unsafe Novel prompt profiles are rejected by contract.

   Prompt profile safety validation covers dangerous authority flags such as
   hidden-fact access and state modification. Prompt profiles may affect writing
   style and task selection, but they do not expand LLM authority.

9. Novel Mode does not directly create World facts.

   Novel-to-World flow remains draft/proposal oriented. Novel drafts and
   manuscript data are not authoritative World facts until they pass the
   established Cross-Mode validation/apply path.

10. Novel -> World remains draft/proposal/validation bounded.

    Existing Cross-Mode services and tests keep Novel -> World as draft or
    proposal output. The flow does not write content packs or mutate active
    `GameState` directly.

11. World -> Novel does not modify `EventLog` or `GameState`.

    World-to-Novel import preview filters hidden/debug/raw-delta content.
    Confirmed apply writes Novel-side chapter draft data only; it does not edit
    the source `EventLog` or active World `GameState`.

12. LLM output is not allowed to directly modify `GameState`.

    No reviewed Novel LLM path writes `GameState` directly. World changes remain
    behind backend validation, `StateDelta`, and `EventLog` boundaries.

13. Tests use mock/local providers rather than real APIs.

    Reviewed Novel, Provider Gateway, and v3.1 integration tests use fake,
    mock, recording, or local stub providers. No real OpenAI API call is required
    by the test paths checked for this audit.

14. Novel quality checks are deterministic and do not use an external LLM judge.

    Novel quality checks are implemented through deterministic consistency and
    quality services. They do not delegate pass/fail decisions to an external
    model.

## 风险项目

1. Provider Gateway use is proven by integration tests, but not type-enforced by
   `NovelDraftGenerationService`.

   The generation service accepts an `LLMProvider` instance. This keeps service
   tests simple, but it means the hard Provider Gateway requirement is enforced
   by caller conventions, API wiring, and tests rather than by the service type
   itself.

2. Rewrite and summary use the same safe service path, but direct gateway tests
   focus more heavily on draft generation.

   The service-level boundary is shared, yet release regression should include
   explicit routed-provider tests for rewrite and summary to prevent a future
   caller from bypassing routing.

3. Debug/authoring context must remain separate from normal generation.

   Some builders can expose richer authoring/debug summaries when explicitly
   requested. These views must never be passed into normal Novel generation,
   export, or quality reports without safe filtering.

4. v3.1 roadmap documentation was not confirmed during this audit.

   The code and tests provide the main evidence for the boundary review, but
   release acceptance should ensure `docs/V3_1_ROADMAP.md` exists and describes
   the same Provider Gateway and visibility constraints.

## 高风险问题

No high-risk Novel LLM boundary issue was found in the reviewed code and tests.

There is no evidence that Novel LLM output can directly mutate `GameState`, write
`EventLog`, bypass Provider Gateway in production-facing integration paths,
receive hidden World facts in normal prompt context, or decide World fact
authority.

## 中风险问题

1. `NovelDraftGenerationService` can be constructed with any `LLMProvider`.

   Current tests demonstrate correct Provider Gateway usage, but a future API or
   UI caller could accidentally pass a raw provider. This is a medium hardening
   risk, not a current release blocker, because no reviewed production-facing
   path shows a direct raw-provider bypass.

2. Routed-provider coverage should be broadened for rewrite and summary.

   Rewrite and summary share the same `_generate` safety path, but explicit
   integration regression for all Novel LLM use cases would make the boundary
   easier to preserve during later UI work.

## 小问题

1. v3.1 roadmap file appears to be a documentation gap if still absent at
   release freeze.

2. Prompt context preview, if exposed as a future API, needs a strict normal-view
   contract that returns safe summaries only, not raw prompts.

3. Service-level tests sometimes instantiate fake providers directly. This is
   acceptable for unit tests, but release-level integration tests should continue
   to prove Provider Gateway routing.

## 修复建议

1. Add a Novel generation factory or API helper that resolves providers only
   through `ProviderGateway` for `novel_draft`, `novel_rewrite`, and
   `chapter_summary`.

2. Add routed-provider regression tests for rewrite and summary, matching the
   existing `novel_draft` hidden-leak test style.

3. Keep `NovelPromptContext.validate_no_hidden_or_secrets` on every provider
   call path, including preview and future generation endpoints.

4. Keep draft snapshots limited to user-authored draft text and safe metadata;
   do not store raw provider prompts, hidden context, or full provider outputs as
   snapshot metadata.

5. Ensure `docs/V3_1_ROADMAP.md` and release notes explicitly state that Novel
   mode cannot create World facts directly and that Provider Gateway remains the
   only model entry.

## 是否阻塞 v3.1 acceptance

Not blocked.

The reviewed implementation preserves the core v3.1 Novel LLM boundaries:
Provider Gateway is used in integration paths, normal prompt context filters
hidden facts and raw deltas, Novel drafts are not World facts, World -> Novel
does not mutate World state, tests use mock/local providers, and quality checks
remain deterministic.

The medium-risk items are hardening recommendations for future maintainability,
not observed release blockers.
