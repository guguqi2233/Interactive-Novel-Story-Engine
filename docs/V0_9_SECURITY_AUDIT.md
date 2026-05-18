# v0.9 Security / Test Data Audit

Verification date: 2026-05-19

Scope reviewed:

- API gating in `backend/app/main.py`
- v0.9 quality, playtesting, benchmark, scenario regression, and quality gate modules
- import/export and mod compatibility code paths
- frontend and local desktop scripts for API-key handling
- git-tracked files and repository-wide key pattern scan
- existing security, hidden-leak, benchmark, and integration tests

## Verdict

No evidence of real API keys, tracked local databases/logs/caches, arbitrary mod execution, zip slip acceptance, or player API raw `state_deltas` exposure was found.

One security acceptance issue was found: several read-only/run-style quality endpoints are not currently gated by `ENABLE_EVAL_API`, `ENABLE_PLAYTEST_API`, `ENABLE_PERF_LOGGING`, or `ENABLE_DEBUG_API`. They appear to return safe summaries rather than raw sensitive data, but this does not satisfy the requested v0.9 control boundary that eval/playtest/perf/quality APIs should be controlled by feature flags or debug mode.

## 已通过项目

- Authoring API has an explicit `authoring_api_enabled()` / `require_authoring_api()` path and existing tests for disabled authoring and path traversal.
- Debug API is controlled by `ENABLE_DEBUG_API`; debug event/timeline endpoints return 403 when disabled.
- Playtest API is controlled by `ENABLE_PLAYTEST_API` or debug mode via `require_playtest_api()`.
- Scenario regression / quality gate style API gating uses `scenario_regression_api_enabled()`, which allows playtest, eval, or debug mode.
- Benchmark API is controlled by `ENABLE_PERF_LOGGING` or debug mode via `require_benchmark_api()`.
- Quality gate API is gated and returns safe `QualityGateResult` fields: pass/fail, issue summaries, report ids, thresholds, and safe summary. It does not return raw `GameState`, raw env, prompt text, or API keys.
- Scenario regression authoring is under authoring APIs and tests cover path traversal and preview/save behavior.
- Playtesting agents act through `GameLoop` and deterministic harness providers; they do not directly mutate `GameState`.
- Stress tests use temporary SQLite repositories and generated/test states, not real user saves.
- Benchmark reports use `model_dump_safe()` and `_strip_sensitive()` to remove prompt/API-key/hidden-fact/state-json indicators.
- Hidden leak fixtures use fake keys such as `sk-test-fake-not-real` and safe assertion messages; normal report tests assert hidden text is not serialized.
- Import/export still validates archive members for zip slip/path traversal, rejects `.env`, database/log files, and executable suffixes, and checks package checksums.
- Mod compatibility stress uses `ModLoader` validation/resolution and does not execute mod code.
- Desktop startup scripts explicitly state that `LLM_API_KEY` is not read or written to logs; no hardcoded real key was found.
- Frontend uses only `VITE_API_BASE_URL` and displays `api_key_configured` boolean status rather than key contents.
- Settings/config summary returns safe status, not raw env or API-key values.
- Player API tests verify raw `state_deltas` do not enter player responses.
- Player visible-state filtering excludes hidden facts, NPC secrets, hidden witnesses, debug memory, hidden relationships, hidden quests, and hidden items.
- `.env`, frontend env files, SQLite/database/log/cache/build outputs, `node_modules`, and frontend `dist` are covered by ignore patterns or not tracked.
- `git ls-files` scan found only `.env.example` and `frontend/.env.example` among env-like tracked files.
- Repository-wide key scan found fake test placeholders only:
  - `sk-test-fake-not-real`
  - `sk-real-looking-but-local`
  - `test-secret-placeholder`
  - example `LLM_API_KEY=""`
- Provider factory tests cover clear failure for missing OpenAI/local HTTP configuration.
- Tests use mock/local stub/fake providers and fake transports; no real OpenAI API call path was found in v0.9 tests.

## 高风险问题

None found.

No evidence was found of:

- real `sk-...` API key leakage
- tracked `.env`, database, log, cache, `node_modules`, or frontend `dist`
- zip slip allowed in import/export
- executable package import accepted
- arbitrary mod code execution
- frontend storing API keys
- player API returning raw `state_deltas`
- tests calling a real external API

## 中风险问题

1. Some quality APIs are not gated.
   - Observed endpoints without explicit eval/playtest/perf/debug gating include:
     - `GET /quality/worlds/{world_id}/health`
     - `POST /quality/worlds/{world_id}/health/run`
     - `GET /quality/worlds/{world_id}/coverage`
     - `POST /quality/worlds/{world_id}/coverage/run`
     - `POST /quality/worlds/{world_id}/branch-regression/run`
     - `POST /quality/mods/compatibility-stress/run`
     - analyzer endpoints such as quest/dead-end/NPC/schedule/economy/combat/social quality analysis
   - Impact: these are local quality/studio endpoints and appear to return safe reports, but they can run analysis and expose local world structure summaries without the feature-flag boundary requested for quality APIs.
   - Recommended fix: introduce `quality_api_enabled()` or reuse `scenario_regression_api_enabled()` for all `/quality/...` run/read endpoints except perhaps an explicitly safe public health placeholder.

2. Quality report safety depends on analyzer field discipline.
   - Impact: `QualityIssue.message` and `safe_details` are normal-view fields. Future analyzer code could place hidden content there.
   - Current mitigation: `hidden_details_debug_only`, `normal_copy()`, and hidden leak tests.
   - Recommended fix: centralize normal-report sanitization and scan against world hidden fact text before API return.

3. Debug APIs intentionally expose raw `state_deltas`.
   - Impact: correct for local debug, but sensitive if debug mode is accidentally enabled in a shared environment.
   - Current mitigation: `ENABLE_DEBUG_API` gate and frontend debug panel isolation.
   - Recommended fix: keep default debug disabled for packaged/non-dev profiles and document local-only use.

4. Test fixtures contain fake key-looking strings.
   - Impact: secret scanners may flag false positives.
   - Current mitigation: strings are clearly fake and used in tests that assert redaction.
   - Recommended fix: maintain an allowlist note in security docs/CI secret scanning config.

## 小问题

- `ENABLE_DEBUG_API` currently defaults to true in `Settings` unless environment overrides it. For a local-only development engine this is understandable, but release profiles should prefer explicit opt-in.
- `docs/V0_9_ROADMAP.md` is missing in the current tree, reducing audit traceability.
- PowerShell profile signing warnings appear during command execution, but they are local shell noise and not a project security issue.
- Some redaction helpers are fixture-specific, for example replacing the sealed-letter hidden text. This is fine for tests but not a complete generic sanitizer.
- Quality health and coverage endpoints are useful for dashboards, but their security model should be documented once gated.

## 修复建议

Recommended before v0.9 release:

1. Gate all `/quality/...` endpoints consistently.
   - Add `quality_api_enabled()` returning `ENABLE_EVAL_API or ENABLE_PLAYTEST_API or ENABLE_PERF_LOGGING or ENABLE_DEBUG_API`.
   - Add `require_quality_api()` to every v0.9 quality endpoint, including health, coverage, branch regression, mod compatibility stress, quest analysis, dead-end analysis, NPC coverage, schedule conflict, economy balance, combat balance, and social consequence coverage.

2. Add regression tests for quality API disabled behavior.
   - Verify representative quality endpoints return 403 when all eval/playtest/perf/debug flags are false.
   - Verify quality gate remains gated.

3. Add normal-report safety tests for quality/gate/dashboard payloads.
   - Assert absence of `LLM_API_KEY`, `llm_api_key`, `sk-`, `state_deltas`, `state_json`, `prompt`, and representative hidden fixture text.

4. Restore/add `docs/V0_9_ROADMAP.md` for release traceability.

Recommended for v1.0 hardening:

- Make debug API default false for release/desktop profiles.
- Add a central normal-output sanitizer for quality reports, health scores, gate results, playtest batch reports, and scenario regression reports.
- Add CI secret scanning rules that distinguish known fake test keys from real credentials.
- Add a static test that rejects direct network-capable provider usage in test/eval/playtest paths.

## 是否阻塞 v0.9 release

Conditionally yes.

If the v0.9 acceptance criterion is interpreted strictly as "all eval/playtest/perf/quality APIs must be controlled by a corresponding flag or debug mode", then the ungated `/quality/...` endpoints are a release blocker.

If those endpoints are accepted as safe local read-only summaries, this becomes a medium-risk hardening item rather than a blocker. The safer recommendation is to gate them before v0.9 final acceptance.
