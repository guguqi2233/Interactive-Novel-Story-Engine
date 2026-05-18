# v0.9 Visibility, Leak Regression, and Debug Data Audit

Verification date: 2026-05-19

Scope reviewed:

- player visible-state construction in `backend/app/session_store.py`
- visibility/filtering rule entry points for quests, rumors, crimes, relationships, faction conflicts, graphs, maps, and shop/economy flows
- v0.9 quality report schemas and normal/debug report separation
- v0.9 playtesting, scenario regression, benchmark, health score, and quality gate outputs
- hidden information leak evals under `backend/tests/evals/hidden_info_leaks/`
- debug/timeline/performance frontend placement in `frontend/src/App.tsx`
- narrator and memory context boundaries as referenced by existing tests/docs

## Verdict

v0.9 maintains the intended visibility boundary: player APIs and normal quality/playtest/scenario reports avoid raw debug data and hidden details, while debug-only views are kept behind debug or local-studio API controls.

No high-risk visibility leak was found.

The main residual risk is authoring/report discipline: new analyzers must continue putting raw hidden content only in `hidden_details_debug_only`, not in `message` or `safe_details`.

## 已通过项目

- Hidden facts do not enter `visible_state` unless their id is in `state.player_visible_facts`.
- Hidden objects remain invisible until discovered by the player.
- Discoverable facts enter player-known facts only through explicit visibility/discovery state, not through memory or quality reports.
- NPC secrets are not included in `VisibleNPCResponse`; visible NPC data is limited to id, mood, relationship, and condition.
- Hidden NPCs are filtered by `_npc_visible_to_player()` and do not enter `visible_npcs` unless discovered.
- Hidden witnesses are excluded from player API payloads; hidden witness identities are tested in hidden leak evals and combat visibility tests.
- Hidden relationships are filtered from player graph / visible relationship outputs by `get_visible_relationships()` and `build_relationship_graph(debug=False)`.
- Hidden faction conflicts and unknown factions are filtered from player graph / visible faction conflict outputs.
- Hidden map edges are filtered by the player-visible map graph builder; hidden edge tests assert empty player edge output for hidden destinations.
- Hidden quests are filtered through `get_visible_quests()`, requiring `known_to_player` and non-inactive status.
- Hidden items are filtered from player inventory/location/shop-adjacent visible surfaces by visibility rules and validation checks.
- Normal quality reports use `WorldQualityReport.normal_copy()` / `model_dump_normal()` to remove `hidden_details_debug_only`.
- Playtest scenario reports and playtest batch reports expose normal dump helpers that redact debug-only/known hidden fixture text.
- Scenario regression reports redact known hidden fixture text in failure and leak summaries.
- Benchmark reports use `model_dump_safe()` and `_strip_sensitive()` to exclude prompt, API key, hidden fact text, fact text, and state JSON keys/values.
- Narrative consistency eval failures hash/redact forbidden terms in rule failure markers, avoiding raw hidden witness/fact text in normal quality reports.
- Debug API remains separated from player API. Tests verify debug events are unavailable when `ENABLE_DEBUG_API` is false.
- Raw `state_deltas` appear in debug event/timeline models and debug panel only; player `/game/state` and `/game/input` responses are tested to omit them.
- Quality gate aggregates normal copies of quality reports and returns safe report links, issue summaries, and thresholds rather than raw hidden payloads.
- Frontend debug timeline/state-delta rendering is contained in the debug panel, not in the main player narrative area.
- Narrator prompt construction still avoids raw `GameState`, raw EventLog, and raw `state_deltas`; memory context filtering excludes hidden/debug memory from narrator-safe context.

## 可能泄露路径

- `QualityIssue.message` and `QualityIssue.safe_details` are treated as normal-view safe. If a future analyzer writes hidden fact text into either field, `normal_copy()` will not remove it.
- `WorldHealthScore.blockers` and `warnings` are derived from normal report issue messages. Unsafe issue messages would propagate into health dashboards.
- `QualityGateResult.blockers`, `errors`, and `warnings` are derived from normalized issue messages. Unsafe analyzer messages would propagate into gate output.
- Scenario regression `expected_visible_facts` / `forbidden_visible_facts` are user-authored ids. They are normally safe identifiers, but authors could put hidden prose in these fields unless validation or UI guidance prevents it.
- Debug APIs intentionally expose raw `state_deltas` and fuller graph/timeline data when enabled. This is acceptable for local debug, but any frontend placement outside debug panels would become a leak path.
- Authoring UI can display complete world content by design. It must remain visually and navigationally isolated from player UI.
- `ActionResult.reason` still reaches narrator prompt input. If rule code puts debug-only hidden detail into `reason`, narrator could see it.

## 高风险泄露

None found.

No evidence was found that:

- hidden facts enter player `visible_state`
- hidden witnesses enter player API
- hidden relationships or hidden faction conflicts enter player graph
- hidden map edges enter player map
- raw `state_deltas` enter player API
- benchmark/performance reports include prompt text/API keys/hidden facts
- debug timeline data is sent to narrator

## 中风险泄露

1. Normal report fields rely on analyzer discipline.
   - Risk: `message` or `safe_details` could contain hidden text if future analyzers are careless.
   - Current mitigation: `hidden_details_debug_only`, `normal_copy()`, v0.9 integration tests, and hidden leak evals.
   - Suggested fix: central hidden-content scanner for all normal quality/gate/dashboard outputs.

2. `ActionResult.reason` remains narrator-visible.
   - Risk: unsafe debug rationale from rules could reach the narrator prompt.
   - Current mitigation: docs and tests treat `reason` as player-safe.
   - Suggested fix: split into `player_reason` and `debug_reason`.

3. Debug panel renders `state_deltas`.
   - Risk: frontend refactor could accidentally move debug timeline details into normal dashboard/player sections.
   - Current mitigation: debug panel placement and API gating.
   - Suggested fix: add frontend snapshot/contract tests that forbid `state_deltas` outside debug components.

## 小问题

- Some redaction helpers are local and fixture-specific, for example replacement of the known sealed-letter phrase. This is fine for tests but not a universal sanitizer.
- `WorldHealthScore` does not itself have a `model_dump_normal()` method; it relies on inputs already being normal copies. Current builder normalizes reports internally.
- `docs/V0_9_ROADMAP.md` is absent in the current tree, so audit traceability to the intended v0.9 roadmap is incomplete.
- Frontend TypeScript includes `state_deltas` types for debug timeline responses. This is expected, but it makes component placement discipline important.

## 修复建议

Before v0.9 acceptance:

- Restore/add `docs/V0_9_ROADMAP.md` for audit traceability.
- Add one regression test that serializes representative normal outputs from:
  - `WorldQualityReport`
  - `WorldHealthScore`
  - `PlaytestBatchRun`
  - `ScenarioRegressionRun`
  - `QualityGateResult`
  and asserts absence of `hidden_details_debug_only`, `state_deltas`, `prompt`, `api_key`, and representative hidden fixture text.

Recommended for v1.0 hardening:

- Introduce a central `sanitize_normal_report_payload(world, payload)` helper that can remove known hidden fact text, debug keys, raw deltas, and prompt/API-key indicators from normal surfaces.
- Split `ActionResult.reason` into player-safe and debug-only fields.
- Add frontend contract tests or lint-like checks for debug-only components so raw `state_deltas` remain confined to debug panels.
- Validate scenario authoring fields so hidden prose is not placed in `forbidden_visible_facts` or expected/actual summary fields intended for normal dashboards.

## 是否阻塞 v0.9

Not blocked.

No high-risk leak blocker was found. The residual issues are medium/low-risk hardening items centered on future analyzer discipline and debug UI placement.
