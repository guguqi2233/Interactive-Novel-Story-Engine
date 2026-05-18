# v0.8 LLM Boundary Audit

## Audit Date

2026-05-18

## Scope

This audit reviews the v0.8 "Visual World Authoring" work against the project rule that the LLM is a language layer, not the world judge. The reviewed scope includes:

- Visual Map data model, backend, and frontend editor.
- Visual Quest Graph Editor.
- NPC Goal Editor.
- Faction / Relationship Visual Editor.
- Item / Economy Editor.
- Rumor / Crime Consequence Editor.
- Validation Graph.
- Timeline Replay backend and frontend.
- World Branch / Diff System.
- Scenario Regression Suite.
- Local Template Browser.
- Prompt Profile Manager.
- Advanced Import / Export Packages.
- Desktop App Shell Polish.
- Authoring UX Integration Pass.
- Provider factory, narrator, memory context, scenario regression, playtesting, and relevant tests.

## Verification Commands

Commands used during this audit pass:

```powershell
rg -n "LLM|provider|generate_text|generate_json|Narrator|MemoryContext|hidden|state_deltas|prompt" backend/app/engine/content backend/app/tools backend/app/scenarios backend/app/core backend/app/llm backend/app/main.py backend/tests/test_v08_integration_regression.py docs/V0_8_ROADMAP.md
rg -n "LocalHTTPProvider|OpenAI|FakeLLMProvider|create_llm_provider|provider_factory|LLMProvider\(" backend/app backend/tests -g "*.py"
```

Latest verification already run in this v0.8 work session:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Result from the latest run in this session: `python -m pytest` passed with 596 tests, and the frontend build passed.

## 已通过项目

1. **v0.8 新增模块默认不调用 LLM**
   - Visual authoring modules are implemented as schema conversion, YAML editing, validation, preview, graph generation, diffing, import/export, and UI surfaces.
   - No v0.8 content authoring module was found directly using `generate_text`, `generate_json`, `Narrator`, or concrete provider classes for rule decisions.

2. **Visual Map Editor 不调用 LLM 自动生成地图**
   - Map graph generation is derived from `locations.yaml` and `exits`.
   - Visual defaults and validation are deterministic and do not call LLM.

3. **Quest Graph Editor 不调用 LLM 自动改任务**
   - Quest graph conversion is graph/schema/YAML based.
   - Validation checks references, unreachable stages, terminal stages, and visibility without LLM involvement.

4. **NPC Goal Editor 不调用 LLM 自动生成 NPC goal**
   - NPC goal authoring reads and writes structured goals from content data.
   - Goal validation checks ids, priorities, statuses, conditions, and planning action names through deterministic rules.

5. **Faction / Relationship Editor 不调用 LLM 决定关系**
   - Relationship and faction authoring paths operate on explicit graph fields.
   - Trust, fear, affinity, conflict, and visibility are edited as structured values and validated locally.

6. **Item / Economy Editor 不调用 LLM 定价**
   - Item prices and trade flags remain structured content fields.
   - Price authority remains in economy rules, not prompt output.

7. **Rumor / Crime Consequence Editor 不调用 LLM 判断后果**
   - Consequence graphs are deterministic authoring data.
   - Hidden fact leakage checks are validation rules, not LLM judgments.

8. **Validation Graph 不调用 LLM 解释错误**
   - Validation graph is built from structured validation reports.
   - It does not call an external or local model to interpret errors.

9. **Timeline Replay 不调用 LLM 总结 hidden events**
   - Timeline replay is debug data derived from EventLog and StateDelta records.
   - It is debug-gated and not sent to narrator.

10. **World Branch / Diff 不调用 LLM 判断 diff**
    - Branch and diff output are derived from structured content comparison, validation, and impact analysis.

11. **Scenario Regression 不调用真实 LLM**
    - Scenario regression uses a playtest/mock provider path.
    - Hidden text is redacted in safe summaries.

12. **Template Browser 不调用 LLM 渲染模板**
    - Template rendering uses local variable substitution and validation.
    - Templates are not script executors and do not use LLM generation.

13. **Prompt Profile Manager 不能扩大 LLM 权限**
    - Prompt profiles are configuration for style and prompt variants.
    - Profile validation rejects terms that would request hidden facts, raw state deltas, or GameState authority.
    - Profiles do not grant direct write access to GameState.

14. **Import / Export 不调用 LLM**
    - Package manifest, checksum, compatibility, dry-run, and validation flows are local deterministic checks.

15. **Desktop Shell 不打包 API key**
    - Desktop shell work remains a local prototype/script path.
    - API keys are not intended to be injected into frontend bundles or committed scripts.

16. **未发现 LLM 输出直接进入 GameState**
    - Rule results, state changes, and authoring saves do not use LLM output as authoritative state.
    - Runtime GameState changes remain behind rule/action code and StateDelta.

17. **Narrator 仍只接收 visible facts 与 narrator_safe memory**
    - Memory context filtering rejects hidden/debug memory for narrator/player contexts.
    - Narrator remains a rendering layer over already visible ActionResult and context.

18. **hidden facts 未发现进入 narrator prompt 的 v0.8 新路径**
    - v0.8 authoring/debug views can show authoring data locally, but they are separate from player/narrator flows.

19. **NPC secrets 未发现进入玩家可见响应的新路径**
    - Visibility boundaries remain enforced through visible state and graph/player endpoints.

20. **debug state_deltas 未发现进入 narrator 的新路径**
    - Raw deltas are used in debug timeline/replay surfaces and not in player/narrator APIs.

21. **hidden/debug memory 未发现进入 narrator 的新路径**
    - MemoryContextBuilder keeps filtering hidden and debug-only records.

22. **provider factory 仍是 provider 选择入口**
    - Runtime provider selection continues through `create_llm_provider`.
    - Direct concrete provider usage found in tests or test harnesses is not part of production business rule flow.

23. **测试不调用真实 API**
    - v0.8 integration tests use `local_stub`, mock, or fake transports.
    - Provider tests that instantiate concrete providers verify configuration/error behavior and do not require real API calls.

24. **schema 校验失败有明确错误或 fallback**
    - Authoring, import/export, prompt profile, graph, validation, template, and regression paths rely on structured schemas and validation reports.

## 风险项目

1. **Prompt Profile Manager 是新的 prompt 配置面**
   - Current validation blocks obvious attempts to request hidden facts, raw state deltas, or GameState authority.
   - Residual risk: future profile fields could accidentally become a prompt injection surface if validation is not kept strict.
   - Severity: low to medium, non-blocking.

2. **Scenario Regression / Playtesting 仍经过 Narrator-style components**
   - These flows use mock/playtest providers and safe summaries.
   - Residual risk: if a future option allows real providers in regression/playtesting, it must remain opt-in and never use hidden state as prompt input.
   - Severity: low, non-blocking.

3. **MemorySummarizer event payload still includes state delta-like event details**
   - This appears to be a pre-v0.8 behavior and does not grant GameState write authority.
   - It is not a narrator/player path, but if used with a real provider it may expose more structured event detail to the summarization layer than strictly necessary.
   - Severity: medium as a privacy hardening item, non-blocking for v0.8 because it is not a new v0.8 release blocker and hidden/debug memory filtering remains intact for narrator context.

4. **Authoring UI intentionally exposes full local authoring content**
   - This is expected for a local creator tool.
   - Risk is controlled by keeping authoring/debug surfaces isolated from player UI and narrator prompt construction.
   - Severity: low, non-blocking.

## 高风险问题

未发现高风险 LLM 权限边界问题。

No evidence was found that v0.8 lets LLM output directly modify GameState, decide game rules, bypass StateDelta, bypass EventLog, or receive hidden/debug memory through narrator context.

## 中风险问题

1. **MemorySummarizer structured event detail exposure**
   - The summarizer path can include event payload details such as state deltas.
   - This does not appear to affect narrator prompt or player API and does not modify GameState.
   - Recommendation: add a future redacted summarizer event view if real providers are used for summarization.
   - Blocking: no.

2. **Prompt Profile validation should remain allowlist-oriented**
   - Current checks reject dangerous phrases, but prompt profile surfaces naturally invite later expansion.
   - Recommendation: prefer structured enums and allowlists over free-form authority-related text fields.
   - Blocking: no.

## 小问题

1. Some checks are source and test-pattern based rather than a complete runtime prompt snapshot for every v0.8 UI path.
2. Direct concrete provider instantiation exists in tests; this is acceptable, but grep-based audits should continue distinguishing tests from business runtime code.
3. Desktop packaging remains a local prototype; packaging audits should continue checking scripts and build artifacts before each tag.
4. Validation and authoring APIs intentionally expose authoring data locally; documentation should continue labeling them as local-only and separate from player/narrator APIs.

## 修复建议

1. Add a small CI grep or unit test that fails if v0.8 authoring/content modules import concrete LLM providers or call `generate_text` / `generate_json`.
2. Keep prompt profile validation strict:
   - no hidden fact access,
   - no raw state delta access,
   - no GameState authority language,
   - no API key fields.
3. Consider adding a redacted MemorySummarizer input adapter before using real providers for summarization.
4. Keep scenario regression and playtesting on mock/local_stub providers by default.
5. Extend narrative boundary evals with prompt snapshots for any future prompt-builder changes.
6. Keep debug timeline, replay, validation graph, and authoring previews out of narrator context by construction.

## 是否阻塞 v0.8 acceptance

不阻塞。

v0.8 LLM boundary audit passed with non-blocking risks. The project still preserves the intended boundary:

- 世界引擎是事实源。
- LLM 只是语言层。
- v0.8 visual authoring tools edit local content only through preview, validation, and explicit save.
- No reviewed v0.8 path gives LLM authority to judge rules, mutate GameState, bypass StateDelta, or see hidden/debug memory through narrator context.
