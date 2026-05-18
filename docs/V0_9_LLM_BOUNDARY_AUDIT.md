# v0.9 LLM Boundary Audit

Verification date: 2026-05-19

Scope reviewed:

- v0.9 quality modules under `backend/app/quality/`
- v0.9 playtesting expansion under `backend/app/playtesting/`
- narrative consistency evals under `backend/app/evals/`
- v0.9 CLI tools under `backend/app/tools/`
- related API wiring in `backend/app/main.py`
- existing LLM boundary docs and runtime language layer modules

Note: `docs/V0_9_ROADMAP.md` was requested as an input but was not present in the current working tree during this audit. This report therefore uses the implemented v0.9 modules, tests, and `docs/LLM_PROTOCOL.md` as the source of truth.

## Verdict

v0.9 remains within the intended LLM boundary: the new quality, analysis, regression, stress, benchmark, and quality gate systems are deterministic local code paths and do not grant LLM output authority over `GameState`.

No high-risk LLM authority violation was found.

The only notable residual risk is inherited from the existing narrator contract: `Narrator` includes `ActionResult.reason` in its prompt payload. That field must remain player-safe in rule code. This is documented in `docs/LLM_PROTOCOL.md` and covered by boundary/eval tests, but it remains a correctness discipline to preserve.

## 已通过项目

- v0.9 quality analyzers do not call real LLM providers:
  - `quest_analysis`
  - `dead_end_detector`
  - `npc_behavior_coverage`
  - `schedule_conflict_detector`
  - `economy_balance`
  - `combat_balance`
  - `social_consequence_coverage`
  - `content_coverage`
  - `health_score`
  - `branch_diff_regression`
  - `mod_compat_stress`
  - `save_load_stress`
  - `benchmarks`
  - `gate`
- Playtesting scenarios use `PlaytestLLMProvider`, a deterministic in-process provider used to exercise the normal `IntentParser` / `Narrator` / `GameLoop` path without external network calls.
- Hidden leak regression and narrative consistency evals use rule-based string/schema checks. They do not use an external LLM judge.
- Quest completion analysis is static/dynamic local analysis and does not call LLM.
- Dead-end detection is local content graph analysis and does not call LLM.
- NPC coverage and schedule conflict detection do not infer unknown facts through LLM; they inspect content packs, events, timeline/playtest reports, and safe summaries.
- Economy, combat, and social consequence checks are deterministic sanity checks. They do not ask LLM to judge balance or consequence results.
- Save/load/migration stress tests use temporary SQLite repositories and migration services. They do not call LLM.
- Performance benchmark outputs use safe environment summaries and explicit stripping for `api_key`, `prompt`, `hidden fact`, `fact_text`, `state_json`, and similar sensitive fields.
- Quality gate pass/fail is determined by configured thresholds and `QualityIssue` severity, not by LLM output.
- v0.9 normal report paths use `WorldQualityReport.normal_copy()` / `model_dump_normal()` patterns to remove `hidden_details_debug_only`.
- Existing narrator implementation still sends only `success_level`, `reason`, `visible_facts`, current location, tone, and explicit visible facts to the provider. It does not send raw `GameState` or raw `state_deltas`.
- Memory filtering remains in `MemoryContextBuilder` / memory store helpers; hidden and debug memories are excluded from narrator-safe context.
- Provider selection for configurable runtime providers remains centralized in `backend/app/llm/provider_factory.py`.
- Tests use mock, fake, local stub, fake transport, or `PlaytestLLMProvider`; no evidence of real OpenAI API calls in v0.9 tests was found.
- Pydantic schemas are used for v0.9 report/config/request/result models, and LLM JSON outputs elsewhere continue to be schema-validated by provider callers.

## 风险项目

- `PlaytestLLMProvider` is instantiated directly inside playtesting and benchmark harness code. This is acceptable for the local deterministic test harness, but it is technically a provider object outside `provider_factory`. It should remain limited to playtesting/eval/benchmark code and must not become a general runtime provider selection path.
- `Narrator` includes `ActionResult.reason` in prompt input. If a future rule puts hidden fact text or debug-only rationale in `reason`, the narrator could receive unsafe content. Current tests and docs treat `reason` as player-safe, but this remains a discipline-dependent boundary.
- `QualityGateResult` aggregates issue messages from many analyzers. The current gate normalizes reports through `normal_copy()` and redacts the known hidden fixture phrase, but future analyzers must keep `message` and `safe_details` safe and put raw hidden details only in `hidden_details_debug_only`.
- Benchmark code runs a real `GameLoop` turn with `PlaytestLLMProvider`; this is safe today, but any future replacement with configurable providers must be blocked unless explicitly requested and isolated from CI.
- `docs/V0_9_ROADMAP.md` is missing, which weakens traceability between intended v0.9 boundaries and implemented modules.

## 高风险问题

None found.

No evidence was found that:

- v0.9 LLM output directly enters `GameState`
- quality gate pass/fail is delegated to an LLM
- v0.9 analyzers call OpenAI/local HTTP providers
- hidden facts are intentionally added to narrator prompts
- raw `state_deltas` are sent to narrator
- hidden/debug memory is used as narrator-safe memory

## 中风险问题

1. `ActionResult.reason` remains part of narrator prompt input.
   - Impact: hidden text could leak if a future rule author writes unsafe details into `reason`.
   - Current mitigation: existing docs call this out; tests cover hidden data boundaries; rule outputs are expected to keep `reason` player-safe.
   - Suggested hardening: split `player_reason` and `debug_reason` in a future release.

2. v0.9 report aggregation depends on analyzer authors keeping normal fields safe.
   - Impact: a future analyzer could place hidden fact text in `message` or `safe_details`.
   - Current mitigation: `QualityIssue.hidden_details_debug_only`, `normal_copy()`, and regression tests verify safe report forms.
   - Suggested hardening: add a reusable hidden-text scanner/sanitizer at quality report construction boundaries.

3. `PlaytestLLMProvider` direct use is safe but should remain harness-only.
   - Impact: if copied into runtime code, it could bypass the intended provider selection convention.
   - Current mitigation: usage is limited to playtesting/benchmark modules and deterministic local tests.
   - Suggested hardening: document this exception in `LLM_PROTOCOL.md` and/or add a code search test that permits direct provider construction only in test/playtesting harness paths.

## 小问题

- `docs/V0_9_ROADMAP.md` was not present during audit, despite being listed as an input. This is a documentation traceability gap, not an LLM authority issue.
- `PlaytestLLMProvider.generate_text()` returns fixed mojibake-like narration text. This does not affect authority boundaries, but it makes audit/readability poorer.
- Benchmark threshold key handling is deterministic and safe, but future benchmark additions should keep using `model_dump_safe()` and `_strip_sensitive()`.

## 修复建议

Recommended before or during v0.9 acceptance:

- Add or restore `docs/V0_9_ROADMAP.md` so acceptance, audits, and release notes have a canonical plan reference.
- Keep `PlaytestLLMProvider` explicitly documented as a local deterministic harness provider, not a selectable runtime provider.
- Add a regression test that scans v0.9 normal quality/gate outputs for `hidden_details_debug_only`, `state_deltas`, `prompt`, `api_key`, and representative hidden fixture text.

Recommended for v1.0 hardening:

- Split `ActionResult.reason` into `player_reason` and `debug_reason`.
- Make `QualityIssue.message` and `safe_details` pass through a central safety sanitizer that can be given the current world's hidden fact texts.
- Add a static boundary test that fails if rule/quality modules import `OpenAIProvider`, `LocalHTTPProvider`, or call `create_llm_provider` outside approved language-layer entry points.

## 是否阻塞 v0.9 acceptance

Not blocked.

The missing `docs/V0_9_ROADMAP.md` should be fixed for release traceability, but it is not an LLM permission boundary blocker. No high-risk LLM authority issue was found in the implemented v0.9 code paths.
