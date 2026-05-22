# v2.5 Cost / Logging / Privacy Audit

Verification Date: 2026-05-22

Scope: v2.5 Provider Gateway Pro cost tracking, usage records, provider call traces, routing explanations, fallback traces, benchmark reports, structured-output reliability reports, frontend usage dashboard, and related privacy boundaries.

Review Command:

```powershell
rg -n "prompt|output|hidden|api_key|secret|telemetry|upload|cloud|sync|ProviderCallTrace|usage|benchmark|structured|performance" backend/app/llm backend/app/core backend/app/main.py frontend/src/App.tsx frontend/src/api.ts docs/V2_5_ROADMAP.md
```

## 已通过项目

1. Usage records do not define fields for full prompt text or full model output text.
   - `ModelUsageRecord` / provider usage APIs expose usage metadata such as provider id, model id, mode, use case, estimated tokens, estimated cost, duration, success, and error type.
   - No persisted usage field was found for raw prompt payload, raw response body, hidden fact text, raw env, or API key.

2. Usage tracking estimates tokens and cost without persisting sensitive text.
   - `UsageTrackingProvider` estimates input/output tokens from call inputs and outputs, then records only counts, cost estimate, and safe metadata.
   - Success and failure paths record safe observability metadata; failures store an error category/type, not prompt or output bodies.

3. Usage APIs return safe summaries.
   - Provider usage endpoints return recent safe records and aggregate summaries by mode, use case, provider, and model.
   - Responses do not include prompt text, output text, API key values, raw environment values, or provider secret values.

4. Provider usage dashboard does not display sensitive content.
   - The frontend usage panel renders recent calls, token estimates, cost estimates, errors, and grouped summaries.
   - UI copy explicitly states that prompts, outputs, API keys, hidden facts, and raw state deltas are not displayed.

5. ProviderCallTrace and fallback trace are metadata-only.
   - `ProviderCallTrace` contains provider/profile ids, model id, use case, behavior/reason, success state, error type, and duration.
   - No prompt, output, API key, provider secret, raw env, or hidden fact field is present.
   - Fallback tracing uses the same safe trace structure.

6. Routing explanations do not contain secrets.
   - Routing decisions expose provider id, model id, use case, reason, warnings, and fallback ids.
   - Provider safe summaries redact sensitive keys and secret-like values.

7. Benchmark reports avoid full prompt and secret storage.
   - Provider benchmark reports store safe case metadata, timing, schema validity, error type, and safety notes.
   - Prompt preview fields are redacted and capped rather than storing full prompt text.

8. Structured-output reliability reports avoid full output and hidden text.
   - Reliability reports store schema name, provider id, success state, validation errors, retry count, fallback usage, and safe summaries.
   - Hidden leak checks use sentinel terms and report policy violations without needing to print hidden text in normal report fields.

9. Performance instrumentation includes sensitive-field guards.
   - Existing instrumentation patterns include forbidden markers for API keys, secrets, prompts, game state, and state deltas.
   - No evidence was found that performance logs intentionally persist prompt bodies, API keys, hidden facts, or raw state deltas for v2.5 provider usage.

10. Cost estimates are positioned as estimates, not billing.
    - v2.5 docs and frontend copy describe provider usage cost as an estimate.
    - There is no online billing, provider resale, telemetry upload, or cloud sync path for provider usage.

11. No telemetry upload or cloud sync of provider data was found.
    - The reviewed provider usage, benchmark, reliability, and dashboard paths are local project features.
    - No remote telemetry endpoint or cloud sync behavior was identified in the v2.5 provider observability code paths.

## 高风险问题

No confirmed high-risk issue was found in the reviewed v2.5 cost, logging, and privacy paths.

Specifically, no code path was found that deliberately persists or returns:

- Full provider prompts.
- Full provider outputs.
- API keys or authorization headers.
- Raw environment values.
- Hidden fact text.
- Raw `state_deltas`.
- Provider secrets in usage records, benchmark reports, reliability reports, routing explanations, or frontend usage summaries.

## 中风险问题

1. Token estimation still receives raw prompt/output in memory before discarding it.
   - The current usage tracker correctly persists only estimates, but the estimator is called with message/output text during the provider call lifecycle.
   - This is expected for local token estimation, but it means future debug logging, exception serialization, or overly broad tracing around that code could accidentally capture sensitive locals.
   - Current status: not a confirmed leak, but this area should remain covered by regression tests and log-sanitization checks.

2. Benchmark and structured reliability reports include redacted prompt previews.
   - Reports avoid full prompt storage, but preview safety depends on redaction helpers and supplied hidden-term sentinels.
   - If a caller supplies arbitrary sensitive text that does not match known secret/hidden patterns, a short redacted preview could still contain contextual sensitive wording.
   - Current status: acceptable for local mock/default tests, but should be tightened before any broader benchmark sharing or debug export.

3. Debug mode needs continued explicit separation.
   - v2.5 normal views are safe, but debug tooling generally has higher disclosure risk.
   - Any future debug prompt capture should require explicit enablement, strong labels, and redaction by default.
   - Current status: not blocking because no default raw prompt/output logging path was found.

## 小问题

1. Unknown cost can be visually ambiguous.
   - Some paths use `None` for unknown estimates, while dashboards may render zero-like summaries when totals are absent.
   - Recommendation: keep UI language explicit: "estimate unavailable" versus "estimated zero cost".

2. Error categories are safe but should remain coarse.
   - `error_type` currently appears metadata-only.
   - Recommendation: keep it to provider/category names and avoid embedding raw exception messages from remote SDKs unless sanitized.

3. Prompt preview fields deserve a documented retention policy.
   - Even redacted previews are still derived from prompts.
   - Recommendation: document whether benchmark/reliability prompt previews are kept only in local reports and excluded from normal exports.

## 修复建议

1. Add regression tests that assert provider usage API responses do not contain sentinel strings such as `sk-live`, `HIDDEN_FACT_SENTINEL`, `raw_state_deltas`, `Authorization`, `prompt_text`, or `output_text`.

2. Add a benchmark/reliability privacy test with a hidden sentinel not covered by ordinary API-key patterns and require it to be redacted from prompt previews.

3. Consider disabling prompt previews by default for benchmark and reliability reports, or make preview generation opt-in under an explicitly labeled debug mode.

4. Ensure any future debug export or diagnostic bundle excludes provider usage records with prompt-derived previews unless a separate debug export policy is explicitly implemented.

5. Display unknown cost as "estimate unavailable" rather than `0` where model pricing is absent.

6. Keep `ProviderCallTrace`, routing explanations, fallback traces, and usage records as allowlisted metadata schemas. Avoid adding free-form `details` fields unless they are redacted and tested.

## 是否阻塞 v2.5

Current verdict: Not blocking v2.5 acceptance.

Reasoning:

- No confirmed path was found that persists or returns full prompts, full outputs, API keys, hidden facts, raw state deltas, provider secrets, telemetry uploads, or cloud-synced provider data.
- Usage records, call traces, routing explanations, fallback traces, and frontend dashboard data are metadata-only in normal operation.
- The main remaining privacy risks are preventive hardening items around redacted prompt previews and future debug/logging expansion, not confirmed release blockers.

Conditional blocker:

- If v2.5 release policy requires zero prompt-derived text in every benchmark or reliability artifact, then redacted prompt preview fields should be disabled or made explicit-debug-only before final release.
