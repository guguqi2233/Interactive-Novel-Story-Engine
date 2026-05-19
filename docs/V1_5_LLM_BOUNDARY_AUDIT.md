# v1.5 LLM Boundary Audit

Verification date: 2026-05-20

Scope:

- v1.5 Local Model & Prompt Lab modules.
- Provider factory / provider router usage.
- Prompt Profile permission boundary.
- Benchmark, diagnostics, regression, structured output, context inspection,
  token budget, usage tracking, compatibility, routing, and experiment package
  behavior.
- Existing v1.5 integration tests and relevant boundary tests.

This audit is read-only with respect to business code. It documents the current
boundary posture and release risks.

## Audit Summary

Verdict: conditionally pass.

Blocking status: no high-risk v1.5 LLM boundary blocker was found.

The v1.5 implementation follows the intended architecture: Prompt Lab can run
local diagnostics, comparisons, benchmarks, and redacted reports, but it does
not become a world judge and does not directly modify `GameState`. Real
provider calls are gated by explicit opt-in flags, and v1.5 tests cover fake
provider defaults, hidden redaction, prompt profile policy denial, usage
metadata safety, and GameState immutability for lab/eval runs.

## Passed Items

1. v1.5 modules and LLM calls

   `Provider Benchmark`, `Prompt A/B`, `Narrator Style Lab`, `NPC Voice Style
   Lab`, `Structured Output Reliability`, `Prompt Regression`, and `Local Model
   Diagnostics` are the v1.5 modules that may call an LLM-like provider. They
   default to fake/mock/local_stub behavior and route real provider creation
   through `create_llm_provider`.

   Metadata and report modules such as `Provider Capability Registry`,
   `Compatibility Matrix`, `Prompt Diff`, `Context Inspector`, `Token Budget`,
   `Usage Tracker`, `Provider Router`, and `Prompt Experiment Package` do not
   call providers directly.

2. Provider Benchmark default behavior

   `ProviderBenchmarkRun.allow_real_provider` defaults to `false`. OpenAI runs
   are blocked unless explicit opt-in is provided. Reports use redacted prompt
   previews and safe output summaries.

3. Prompt A/B fact authority

   Prompt A/B runs call `ModelPromptLabPolicy.validate_prompt_profile`.
   `PromptProfile` / `RPPromptProfile` validation requires
   `hidden_fact_policy=deny` and `state_modification_policy=deny`; profiles
   cannot widen fact access or state authority.

4. Narrator Style Lab ActionResult boundary

   Narrator style experiments evaluate style and safety findings against a
   visible action result. They do not mutate or replace `ActionResult`, and v1.5
   integration coverage asserts the original action reason remains unchanged.

5. NPC Voice Style Lab knowledge boundary

   NPC voice experiments check unknown fact mentions, hidden leaks, relationship
   invention, and quest completion invention. They accept state/context for
   checking but do not add NPC knowledge or mutate `GameState`.

6. Structured Output Test GameState boundary

   Structured output reliability tests call provider `generate_json` and
   validate schemas. Reports record success/failure metrics and schema failures;
   they do not write `GameState`.

7. Cost / Latency Tracker prompt privacy

   Usage tracking stores provider/model/use_case, duration, estimated tokens,
   estimated cost, success/failure, and error type. It estimates prompt/output
   tokens in memory but does not persist raw prompt text, hidden fact text, raw
   `GameState`, or API keys.

8. Context Inspector redaction

   Context snapshots classify sections as normal, narrator-safe, NPC-known,
   debug-only, or hidden-redacted. Hidden facts are represented as redacted
   sections with safe ids/summaries. Raw prompt output is off by default and,
   when explicitly requested, is redacted.

9. Prompt Diff safety policy detection

   Prompt diff flags relaxed `hidden_fact_policy` and
   `state_modification_policy` as blockers and strips sensitive keys/text from
   safe reports.

10. Compatibility Matrix authority

   The model compatibility matrix is derived from declared capabilities and
   local report summaries. It does not call real providers by itself and does
   not auto-switch production provider configuration.

11. Routing Rule Editor provider boundary

   Routing rules validate provider/model ids against capability metadata and
   produce safe summaries without API keys. Routing is policy/configuration
   only and is intended to delegate through `ProviderRouter` / `LLMProvider`,
   not grant models world-judge authority.

12. Prompt Regression pass/fail authority

   Prompt regression composes deterministic checks from structured output,
   prompt A/B, narrator style, NPC voice, and hidden leak findings. Pass/fail
   and blockers are code/eval derived, not judged by an LLM.

13. Local Model Diagnostics state boundary

   Local diagnostics use safe smoke messages and fake transports by default.
   Real local checks require `allow_real_local_check=true`. Diagnostics do not
   modify `GameState`.

14. Token Budget Manager safety boundary

   Token budget trimming protects safety/boundary/policy sections, drops hidden
   redacted sections, and reports blockers if hidden sections enter trimmed
   context or safety constraints exceed available budget.

15. Prompt Experiment Package secrecy

   Prompt experiment package export/import validation rejects API keys, raw env,
   hidden facts, raw `GameState`, raw `state_delta`, sensitive prompt snapshots,
   executable files, and path traversal. Import dry-run does not write active
   state, and imported profiles are not auto-enabled.

16. No LLM output directly enters GameState

   The v1.5 lab modules produce reports, matrices, diagnostics, summaries, and
   packages. No audited v1.5 code path writes provider output directly into
   active `GameState`. Integration coverage verifies benchmark/regression/
   structured-output runs leave a sample `GameState` unchanged.

17. Provider factory remains the concrete provider entry

   Direct concrete provider instantiation was found in provider implementation
   files and `provider_factory.py`. v1.5 business/lab modules use
   `create_llm_provider` or fake test providers for local deterministic checks.

18. Tests avoid real APIs by default

   v1.5 integration tests use fake/local_stub providers. CLI coverage verifies
   an OpenAI benchmark attempt without explicit opt-in is blocked and does not
   expose secrets.

19. Schema failure clarity

   Structured output reliability and benchmark paths record schema failures,
   provider errors, retries, and safe error classes. Local diagnostics reports
   missing base URL and timeout/error parsing states explicitly.

## Risk Items

1. Synthetic hidden leak prompts in benchmark/evals

   Some default or test cases contain synthetic hidden-like sentinel text such
   as a fake hidden fact phrase. This is acceptable for local hidden leak
   testing because reports redact configured hidden terms and tests verify the
   payload does not expose them. The operational risk is that future cases
   copied from real worlds could accidentally embed real hidden text.

2. Explicit real provider and real local diagnostic modes

   Real provider benchmark and local model checks are intentionally available
   behind explicit flags. The current boundary blocks default real calls, but
   these paths still require careful operator discipline and redaction because
   they can send evaluation prompts to a configured provider.

3. Debug raw context inspection

   `Context Inspector` supports explicit raw prompt inclusion for local debug.
   The implementation redacts the raw prompt and defaults it off. This remains
   a sensitive surface and should stay out of normal/player UI.

4. Usage tracking wraps provider calls

   Usage tracking receives messages to estimate token counts, then stores only
   metadata. This is safe as implemented, but future persistence backends must
   preserve the same no-raw-prompt invariant.

5. Existing non-v1.5 summarizer prompts include state delta summaries

   `MemorySummarizer` can receive event state delta payloads through older
   memory summarization flows. This is outside the v1.5 Prompt Lab additions,
   but it remains a boundary area to keep covered by existing hidden/debug
   memory and narrator prompt tests.

## High-Risk Issues

No high-risk LLM boundary issue was found in the audited v1.5 code.

Specifically, the audit did not find:

- v1.5 LLM output directly writing `GameState`.
- Prompt Profiles enabling hidden facts or state modification.
- Default benchmark/test paths calling real external APIs.
- Provider construction bypassing `LLMProvider` / `create_llm_provider` in
  v1.5 business modules.
- Prompt Lab reports exporting API keys or unredacted hidden fact text by
  default.

## Medium-Risk Issues

1. Real provider opt-in requires continued UI/CLI friction

   Impact: medium.

   Real provider benchmarks and local diagnostics are explicit, but all UI/CLI
   entry points must continue showing a confirmation/warning before sending any
   prompt outside fake/local_stub paths.

   Current status: not blocking; covered by flags and CLI test behavior.

2. Context Inspector debug raw mode must remain debug-only

   Impact: medium.

   Raw prompt inspection is redacted and off by default, but accidental reuse in
   normal UI would be a leak risk.

   Current status: not blocking; normal safe dumps redact hidden/API key text.

3. Synthetic hidden eval cases could be confused with real hidden facts

   Impact: medium.

   Hidden leak tests need sentinel strings, but future maintainers should avoid
   copying real world hidden facts into reusable benchmark cases.

   Current status: not blocking; current tests assert redaction.

## Small Issues

1. Prompt experiment package default benchmark config contains an extra
   prompt-like field that is not part of the benchmark schema.

   This appears to be ignored by Pydantic rather than creating a boundary leak.
   It is a cleanliness issue, not a release blocker.

2. Safe provider summaries expose `api_key_configured` as a boolean.

   This does not leak the key value. It is acceptable for local diagnostics, but
   should remain out of player APIs and package exports.

3. Some older test fixtures intentionally contain fake `sk-...` strings.

   Tests treat them as fake leak sentinels and assert redaction. They should not
   be treated as real credentials, but future secret scans should continue to
   distinguish fake fixtures from actual keys.

## Fix Recommendations

1. Keep real provider and real local diagnostic execution behind explicit
   `allow_real_provider` / `allow_real_local_check` flags, plus visible UI/CLI
   warnings.

2. Add or preserve regression tests that assert Prompt Lab normal reports do not
   include hidden text, API keys, raw prompts, raw env, raw `GameState`, or raw
   `state_deltas`.

3. Keep `Context Inspector` raw prompt inclusion debug-only and redacted. Do
   not wire raw prompt payloads into player UI, narrator prompts, exports, or
   normal dashboards.

4. If usage tracking moves from memory to SQLite/file storage, add tests proving
   only `ModelUsageRecord` metadata is persisted and raw prompt/output text is
   not stored.

5. Normalize or remove ignored prompt-like fields in default experiment package
   benchmark configs during a non-blocking cleanup pass.

6. Continue scanning v1.5 modules for concrete provider instantiation outside
   `provider_factory.py` and provider implementation classes.

7. Preserve schema validation fallback behavior: structured output failures
   should produce safe error reports, not partial authority-bearing data.

## Acceptance Impact

Does this block v1.5 acceptance: no.

Rationale:

- v1.5 Prompt Lab remains diagnostic/evaluative and does not gain world-state
  authority.
- Real provider calls are opt-in, not default.
- Prompt Profiles remain style-only and cannot widen hidden fact or state
  modification policies.
- Provider construction remains centralized through the provider factory/router
  boundary.
- Normal reports and packages are designed to redact hidden content and secrets.

Recommended acceptance condition: proceed to v1.5 acceptance after the broader
visibility/security audits and full regression/build verification pass.
