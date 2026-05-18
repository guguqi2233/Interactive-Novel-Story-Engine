# v1.0 LLM 权限边界专项审查

Verification Date: 2026-05-19

Verdict: Pass with non-blocking hardening recommendations.

本审查面向 v1.0 Stable Local Studio Edition，重点确认 LLM 仍然只是语言层，世界引擎仍是事实源。审查范围覆盖 `IntentParser`、`Narrator`、`MemorySummarizer`、`MemoryContextBuilder`、`PromptProfile`、provider factory、local provider、NPC planning、quality gate、narrative evals、authoring tools、templates 和相关测试。

## 审查依据

- 文档：`docs/V1_0_ROADMAP.md`、`docs/LLM_PROTOCOL.md`、`docs/V1_0_RELEASE_CRITERIA.md`
- 核心代码：
  - `backend/app/core/game_loop.py`
  - `backend/app/llm/intent_parser.py`
  - `backend/app/llm/narrator.py`
  - `backend/app/llm/memory_summarizer.py`
  - `backend/app/llm/context_builder.py`
  - `backend/app/llm/prompt_profiles.py`
  - `backend/app/llm/provider_factory.py`
  - `backend/app/llm/local_provider.py`
  - `backend/app/quality/gate.py`
  - `backend/app/engine/content/side_quest_generator.py`
  - `backend/app/engine/content/scenario_templates.py`
  - `backend/app/evals/narrative_quality.py`
  - `backend/app/evals/narrative_consistency.py`
- 搜索检查：
  - concrete provider instantiation
  - `generate_json` / `generate_text` usage
  - narrator prompt inputs
  - hidden facts / state_deltas paths
  - quality gate / playtesting / eval provider usage

## 边界结论

v1.0 当前代码没有发现 LLM 输出直接写入 `GameState` 的路径。运行时状态变化由规则层产生 `StateDelta`，再由 `GameLoop` 应用；`Narrator` 在规则判定之后渲染文本，输出类型为 `NarrativeResult`，不参与规则判定、不产生 `StateDelta`、不写 `EventLog` 以外的事实状态。

LLM provider 仍通过 `LLMProvider` 抽象接入，`provider_factory.create_llm_provider` 是业务运行时选择 provider 的入口。测试中直接实例化 fake/local provider 属于测试隔离用途，不构成业务绕过。

## 已通过项目

1. 无 LLM 输出直接进入 `GameState`。
   - `GameLoop.step` 先通过 `ActionDispatcher` 和规则系统生成 `ActionResult.state_deltas`，再调用 `apply_delta`。
   - `Narrator.render` 发生在规则判定之后，只返回 `NarrativeResult`。

2. `IntentParser` 只输出 `PlayerIntent`。
   - `IntentParser.parse` 调用 `provider.generate_json(..., schema=PlayerIntent)`。
   - schema 校验失败或 provider 错误时 fallback 为 `UNKNOWN` / clarification intent，不写状态。

3. `Narrator` 只渲染已判定结果。
   - 输入 payload 只包含 `success_level`、`reason`、`visible_facts`、当前 location 和 tone。
   - 未传入 raw `GameState`、raw `state_deltas`、debug timeline 或 hidden facts 字段。

4. `MemorySummarizer` 只总结，不改变事实。
   - 输出 schema 为 `MemorySummary`。
   - 模块不调用 `apply_delta`，不写 `GameState`，不创建权威事实。

5. `MemoryContextBuilder` 只提供 narrator-safe / player-visible memory。
   - 使用 `filter_narrator_safe_memories`、`filter_player_visible_memories`。
   - 过滤 hidden/debug memory、未知 hidden/discoverable facts、`source_event_hidden`。
   - NPC 记忆上下文通过 `npc_knows` 约束。

6. `PromptProfile` 不能扩大 LLM 权限。
   - validator 禁止 profile 文本包含 hidden facts、NPC secrets、raw GameState、raw state_deltas、modify/write GameState 等边界破坏指令。
   - profile 只能影响风格、prompt variant、温度和 token 偏好。

7. `LocalHTTPProvider` 仍通过 `LLMProvider` 抽象。
   - 实现 `generate_text` / `generate_json`。
   - `generate_json` 经过 Pydantic schema 校验。
   - 缺少 `LOCAL_LLM_BASE_URL` 时返回清晰 `LLMProviderError`。

8. provider factory 仍是运行时唯一 provider 选择入口。
   - `session_store` 默认通过 `create_llm_provider` 注入 provider。
   - concrete provider direct instantiation 主要出现在 `provider_factory` 和测试文件。

9. NPC planning 不调用 LLM。
   - playtesting、NPC planning、coverage、schedule、quality analysis 使用 deterministic rules 或 `PlaytestLLMProvider` mock path。

10. quality gate 不由 LLM 判定。
    - `run_quality_gate` 聚合 validator、quality analyzers、stress、benchmark、scenario regression、playtest batch、mod compatibility 等 deterministic 报告。
    - pass/fail 由 blocker/error/warning/profile/threshold 规则决定。

11. narrative evals 不使用外部 LLM judge。
    - `narrative_quality` 和 `narrative_consistency` 基于 mock/fake narrator outputs 和规则化字符串/结构检查。

12. authoring tools 不调用 LLM 自动改写内容。
    - visual editors、validation graph、branch/diff、import/export、templates、schema validation 均是 deterministic authoring paths。
    - 保存路径仍要求 validation / explicit save。

13. templates 不调用 LLM。
    - `ScenarioTemplateRenderer` 做变量替换、YAML 解析、安全路径检查和 validation。
    - 不执行脚本，不调用 provider。

14. hidden facts 未发现直接进入 narrator prompt 的稳定路径。
    - `Narrator` 不传 `ActionResult.hidden_facts`。
    - narrative boundary tests 覆盖 hidden facts、NPC secrets、hidden witness、raw state_deltas 不进入 narrator prompt。

15. NPC secrets 未发现进入玩家可见响应的稳定路径。
    - 玩家上下文通过 visible state / visible facts 约束。
    - memory 和 eval tests 覆盖 NPC secret 不进入 narrator/player context。

16. debug `state_deltas` 未发现进入 narrator 的稳定路径。
    - `Narrator.render` 不传 raw state deltas。
    - debug timeline/state_delta 仅属于 debug API 范围。

17. 测试不调用真实 API。
    - 大量 tests 使用 `FakeLLMProvider`、`MockLLMProvider`、`LocalStubProvider`、`PlaytestLLMProvider`。
    - local_http tests 使用 fake transport，不启动真实本地模型服务。

18. schema 校验失败有明确错误或 fallback。
    - `IntentParser` fallback 为 clarification intent。
    - `OpenAIProvider`、`LocalHTTPProvider`、`LocalStubProvider`、`FakeLLMProvider` 在 schema 失败时抛出清晰 `LLMProviderError`。

## 风险项目

1. `ActionResult.reason` 进入 narrator prompt。
   - 当前 `Narrator` 构造 safe payload 时包含 `action_result.reason`。
   - 现有规则代码大多写入玩家安全原因，但该字段本身没有类型级别区分 `player_reason` 与 `debug_reason`。
   - 若未来规则作者把 hidden/debug 细节写入 `reason`，可能进入 narrator prompt。

2. `MemorySummarizer` 输入包含 event `state_deltas`。
   - 该模块只总结，不写事实源；但传给 summarizer 的 `events_payload` 包含 state delta JSON。
   - 当前 runtime 未把 memory summary 直接接入 narrator，且 `MemoryContextBuilder` 会过滤 memory visibility。
   - 风险在于未来调用方若把 debug/raw event 生成的 summary 标为 narrator_safe，可能扩大可见性。

3. 可选 `llm_assisted_generate_side_quest` 仍存在。
   - 该函数通过注入的 `LLMProvider` 生成 `QuestDraft`，随后 validate 和 redact hidden text。
   - 当前没有发现它接入自动保存、active GameState 或 runtime adjudication。
   - 如果未来暴露到 authoring UI，应继续要求 authoring-only、explicit review、validation、no active GameState mutation。

4. `PromptProfile` 的安全验证基于 forbidden terms。
   - 已能阻止明显越权指令，但不是完整自然语言安全证明。
   - 当前 profile 只控制 style/variant/temperature，因此不阻塞。

5. local provider 发送 prompt 到配置的本地 HTTP endpoint。
   - 这是预期行为，但 Settings / Privacy 和 LLM protocol 必须继续清楚说明 local_http 会接收 prompt 内容。
   - 不影响世界裁判边界。

## 高风险问题

未发现高风险 LLM 权限边界问题。

未发现以下 blocker：

- LLM output 直接写入 `GameState`
- LLM output 直接产生 `StateDelta`
- LLM 决定 combat / quest / economy / social consequence / quality gate pass-fail
- provider factory 被业务路径绕过
- narrative evals 使用外部 LLM judge
- authoring/template 自动调用 LLM 改写并保存内容

## 中风险问题

1. `ActionResult.reason` 缺少 player-safe 类型隔离。
   - 风险：未来规则新增时将 hidden witness、hidden fact、debug cause 写入 `reason`，被 narrator prompt 使用。
   - 当前状态：测试覆盖主要泄露路径，未发现现有 blocker。

2. `MemorySummarizer` 可接收 raw event/state_delta payload。
   - 风险：未来把 debug/raw event 生成的 summary 错误标记为 narrator_safe。
   - 当前状态：summary 不是权威事实源，MemoryContextBuilder 有过滤，runtime narrator 未直接接入 memory summary。

3. LLM-assisted quest draft helper 需要继续保持隔离。
   - 风险：未来若接入 UI 并允许自动保存，可能让 LLM 间接改 content pack。
   - 当前状态：只生成 draft，validate 后返回，不修改 active GameState。

## 小问题

1. 部分 local stub / prompt 文本存在编码异常显示。
   - 影响可读性和测试文本质量，不构成权限边界问题。

2. `PromptProfile` 安全边界依赖关键词拦截。
   - 当前足以保护已实现字段，但建议长期改为结构化 allowlist。

3. quality/local-only API 的启用开关属于安全审查关注点。
   - 这不是 LLM 权限问题；仍建议在 security audit 中持续确认 quality/eval/playtest/debug API 都受本地配置控制。

## 修复建议

1. 在 v1.1 或后续小版本中拆分 `ActionResult.reason`：
   - `player_reason`：允许进入 narrator prompt 和 player API。
   - `debug_reason`：只允许进入 debug timeline / debug API。

2. 为 narrator prompt 增加中心化 payload sanitizer：
   - 明确 denylist：`hidden_facts`、`state_deltas`、`debug_*`、`npc_secret`、`hidden_witness`、raw `GameState`。
   - 在 tests 中 snapshot 检查 prompt payload。

3. 为 `MemorySummarizer` 输出落库增加 visibility 分类强制策略：
   - 从 raw/debug events 生成的 summary 默认 `debug_only` 或 hidden。
   - 只有来源全为 player-visible / narrator-safe 时才能标为 `narrator_safe`。

4. 保持 `llm_assisted_generate_side_quest` 仅为 draft helper：
   - 不接 active session。
   - 不自动写 YAML。
   - 不绕过 validation。
   - UI 暴露时必须明确 authoring-only 和 explicit save。

5. 将 PromptProfile 安全策略从 forbidden terms 逐步迁移到结构化 allowlist：
   - style 字段只允许描述语气。
   - prompt variant 只允许枚举值。
   - 不允许用户 profile 注入自定义系统提示。

6. 在 release checklist 中保留 provider 搜索检查：
   - 业务代码不得直接实例化 `OpenAIProvider` / `LocalHTTPProvider`。
   - 测试 direct instantiation 需限定 fake transport 或 schema failure 场景。

## 是否阻塞 v1.0 acceptance

不阻塞。

本次审查未发现 v1.0 acceptance blocker。当前 LLM 边界满足 Stable Local Studio Edition 的核心要求：世界引擎是事实源，LLM 是语言层；LLM 输出不直接修改 `GameState`；规则、迁移、quality gate、authoring、templates、playtesting 和 evals 不把 LLM 当作世界裁判。

v1.0 可以继续进入后续 acceptance / release 审查，但建议将 `ActionResult.reason` player/debug 拆分列为 v1.1 优先硬化项。
