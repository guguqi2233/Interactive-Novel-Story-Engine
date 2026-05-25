# v3.7 Release Notes: Local Playable Complete Product CN

## 1. 版本名称

**v3.7 Local Playable Complete Product CN / 中文本地可游玩完整产品版**

v3.7 是面向中文玩家和创作者的本地完整产品版本。它不是新的大型系统扩张，也不是 v4.0 stable；它的重点是把 v0.1-v3.6 已完成的 Novel、Tavern、World、Provider、Cross-Mode、Backup、Diagnostics、Debug、QA、Authoring / Mod 等能力收束成打开后能正常体验、创作和游玩的本地产品。

## 2. 版本目标

v3.7 的目标是让用户在本地完成完整叙事体验：

- 打开或创建本地项目。
- 使用默认中文 UI。
- 配置真实 LLM API、OpenAI-compatible、relay-style compatible endpoint、`local_http`、custom、mock 或 local_stub Provider。
- 手动测试连接、读取模型列表，并保存安全的 `ModelProfile` metadata。
- 按 Novel、Tavern、World、Cross-Mode、Quality 等场景分配模型。
- 本地写小说。
- 本地进行 Tavern RP。
- 本地玩大世界。
- 使用 Cross-Mode draft / proposal / validation / confirm-gated apply。
- 在高级工具中使用 Quality、Debug、Replay、Authoring / Mod、Backup、Diagnostics、Export。

v3.7 继续保持本地优先。LLM 不是世界裁判，World Engine 仍是事实源，Provider Gateway 仍是唯一模型入口。

## 3. 中文 UI 默认

- 默认 UI 以中文产品体验为主。
- 首页、首次使用向导、左侧导航、Provider 设置、Novel / Tavern / World 入口、Settings、Backup / Diagnostics、Debug / Replay 标签、Error / Empty / Disabled 状态已收口到中文表达。
- 必要技术术语保留中英混合，例如 Provider / 模型服务、Tavern RP、Debug / 调试、StateDelta、EventLog、Quality Gate。

## 4. 玩家 / 创作者首页

v3.7 的默认首页从开发者仪表盘调整为玩家 / 创作者首页。

首页重点展示：

- 当前项目状态。
- 打开项目 / 创建项目。
- 体验 Demo 项目。
- 配置模型服务。
- 写小说。
- 角色 RP。
- 大世界游玩。
- 下一步建议。
- Provider 状态摘要。
- 本地安全简短提示。

未选择项目时，首页只突出打开 / 创建项目、Demo、配置模型服务和产品引导，不再铺满 disabled 模块。

## 5. 三大入口：写小说 / 角色 RP / 大世界

v3.7 首屏突出三个普通用户最关心的入口：

- **写小说**：进入 Novel Studio，本地写作、章节、场景、导出与 Novel Quality。
- **角色 RP**：进入 Tavern Studio，本地角色 RP、多 NPC 场景、记忆 / 情绪 / 关系面板与 RP Safety。
- **大世界游玩**：进入 World Studio，开始 / 继续大世界、输入行动、查看地图 / NPC / 任务 / 背包 / 模块、保存 / 读取与 Timeline。

这三个入口是默认产品体验，不需要用户先理解 Debug、StateDelta 或 readiness checklist。

## 6. 高级工具折叠

以下能力保留完整，但默认收纳到高级工具：

- Product Readiness Dashboard。
- Product Acceptance Checklist。
- Authoring / Mods。
- Quality Gate。
- Debug / Replay。
- StateDelta Viewer。
- EventLog Viewer。
- Hidden Leak Report。
- Diagnostics。
- Export。

Debug / QA 是高级工具，不默认占据首页。Debug UI 仍受 `ENABLE_DEBUG_API` 控制，Replay 仍只观察不回写。

## 7. 真实 LLM Provider 配置

v3.7 可以接入真实 LLM API，但真实连接只允许用户手动触发。

支持的 Provider 类型包括：

- OpenAI。
- OpenAI-compatible。
- 中转站 / relay-style compatible endpoint。
- 本地模型服务 / `local_http`。
- 自定义 API / custom。
- Mock / 测试。
- local_stub。

Secret 来源支持：

- `api_key_env`。
- `secret_ref`。
- `local_secret_ref`，如本地安全配置已启用。
- `transient_api_key`，仅用于当前请求或当前会话。

`ProviderProfile` 不保存明文 API key。API key 不进入 project、frontend storage、logs、diagnostics、backup、export、tests、fixtures、mods、package manifests、prompt profiles 或文档示例。

测试、CI、release checks 不调用真实 provider，仍使用 fake/mock/local_stub provider。

## 8. 模型读取 / 模型分配

v3.7 收口了 Provider 模型读取与模型分配流程：

- 手动 Test Connection。
- 手动 Fetch Models。
- 同步安全的 `ModelProfile` metadata。
- 支持手动添加 model_id。
- 支持按 capability 过滤或提示：文本、JSON / 结构化输出、流式、工具调用。
- 支持按使用场景分配模型：
  - 小说草稿。
  - 小说改写。
  - Tavern 回复。
  - 多 NPC 场景。
  - 世界输入解析。
  - 世界叙事渲染。
  - Cross-Mode 草稿。
  - 记忆摘要。
  - 质量检查。
  - 低成本摘要。

World 输入解析会提示 JSON / 结构化输出能力要求。模型分配不改变 Provider Gateway 语义，也不让模型决定世界事实。

## 9. Novel 可用流程

Novel Studio 作为中文本地写作工作区被验收：

- 打开 Novel Studio。
- 创建 / 打开稿件。
- 写章节。
- 查看大纲、场景、人物、伏笔。
- 使用已分配模型进行生成、改写或摘要。
- 从 World 导入章节草稿。
- 导出 Markdown / TXT。
- 运行 Novel Quality。

Novel 不直接修改 World `GameState`。任何进入 World 的内容仍必须走 draft / validation / apply 边界。

## 10. Tavern 可用流程

Tavern Studio 作为中文本地 RP 工作区被验收：

- 打开 Tavern Studio。
- 选择 / 创建角色。
- 开始单角色 RP。
- 开始多 NPC 场景。
- 使用已分配模型生成回复。
- 查看 RP memory、emotion、relationship。
- Tavern -> Novel 草稿。
- Tavern -> World proposal。
- 运行 RP Safety。

Mature module 默认关闭。NPC secrets、mature/private memory 不进入 normal prompt / UI。Tavern 不直接修改 World `GameState`。

## 11. World 可游玩流程

World Studio 作为中文本地大世界游玩工作区被验收：

- 打开 World Studio。
- 开始 / 继续大世界。
- 输入行动。
- 使用已分配模型进行输入解析和叙事渲染。
- 查看地图、NPC、任务、背包、模块面板。
- 保存 / 读取。
- 查看 Timeline。
- 运行 World Quality。

玩家输入仍走 `/game/input` 或后端 action API。LLM 只解析输入和渲染叙事，不裁判战斗、经济、战争、魔法、推理、生存或其他世界规则结果。World changes 仍走 `StateDelta` / `EventLog`。

## 12. Cross-Mode 流程

v3.7 保留并收口 Cross-Mode 工作流：

- World -> Novel。
- Tavern -> Novel。
- Tavern -> World。
- Novel -> World。
- World NPC -> Tavern。

Cross-Mode 使用 draft / proposal / validation / review / confirm-gated apply / audit 流程。Apply 必须明确确认，不自动同步，不绕过 validation，不直接修改 `GameState`。Hidden、mature、private 内容默认过滤。

## 13. Backup / Diagnostics / Export

Backup / Restore / Diagnostics / Export 已中文化并作为本地安全流程收口：

- Backup 支持 dry-run 和过滤摘要。
- Restore apply 需要 confirm。
- Diagnostics preview / export 保持本地，不上传。
- Export 需要 preview / filtering summary / confirm。
- 默认排除：
  - API key。
  - `.env`。
  - provider secrets。
  - debug raw data。
  - mature/private。
  - hidden refs。
  - databases、logs、cache、build outputs。

Diagnostics、backup、export 不显示 secrets，不上传项目数据。

## 14. Demo 项目

新增安全 Demo 项目：

`examples/demo_local_narrative_project`

Demo 项目用于本地体验：

- 试写小说。
- 试角色 RP。
- 试大世界游玩。
- 查看 Cross-Mode 示例。
- 使用 fake/local_stub Provider。

Demo 不包含真实 API key、`.env`、数据库、日志、缓存、build outputs、mature/private 内容、raw state_deltas 或任意代码插件。Demo project quality gate 已通过。

## 15. 安全边界

v3.7 不放宽任何核心边界：

- UI 不直接修改 `GameState`。
- LLM 不是世界裁判。
- World Engine 仍是事实源。
- World changes 仍走 `StateDelta` / `EventLog`。
- Provider Gateway 仍是唯一模型入口。
- normal UI 只显示 `visible_state` 和 safe summaries。
- Hidden facts、NPC secrets、debug memory、raw prompts、raw outputs、raw provider responses、raw `state_deltas` 不进入 normal UI。
- Debug UI 仍受 `ENABLE_DEBUG_API` 控制。
- Debug / Replay 只观察，不 apply delta，不写 `GameState`。
- Mature/private 默认关闭，默认不导出。
- Mod 不执行任意代码。
- Action Mod 仍通过 ActionRegistry / StateDelta / EventLog。
- Rule Module 仍 contract-only。
- 不做账号、云同步、在线市场、远程包自动下载、在线写作/RP/游玩平台、API 转售服务。

## 16. 已知限制

- 真实 LLM smoke test 是手动流程，不进入 CI。用户手动连接真实 provider 时可能产生费用，并会向所配置 provider 发送 prompt。
- 不保证所有 OpenAI-compatible / relay-style endpoint 都支持模型列表读取；不支持时可手动添加 model_id。
- 部分高级工具仍保留技术术语，例如 StateDelta、EventLog、Debug、Quality Gate。
- Demo 项目是小型安全样例，不是完整长篇内容展示。
- v3.7 是中文本地可游玩完整产品版，不是 v4.0 stable。

## 17. 从旧 v3.7 或 v3.6 升级注意事项

从旧 v3.7：

- 默认首页从 Local Complete Product Dashboard 调整为中文玩家 / 创作者首页。
- Debug / QA / Product Readiness / Diagnostics / Authoring 默认进入高级工具。
- 首屏不再展示一屏 disabled 状态。
- Novel / Tavern / World 三大入口变为默认主路径。
- Provider 设置流程更接近普通用户真实配置模型服务的路径。

从 v3.6：

- v3.6 的性能 / 可访问性优化继续保留。
- v3.7 增加中文产品收束、真实 LLM 手动配置路径、Demo 项目、产品手册和端到端体验检查。
- API key 安全边界不变：不进入 project / frontend / logs / diagnostics / backup / export。
- 测试仍不调用真实 provider。
- World Engine / StateDelta / EventLog / Visibility / Provider Gateway 语义不变。

## 18. 推荐 v4.0 方向

v4.0 推荐方向是 **Local AI Narrative Studio Stable**。

建议重点：

- 稳定本地 launcher / packaging / release 流程。
- 完成浏览器级视觉验收和非开发者使用体验打磨。
- 继续完善中文文案与离线帮助。
- 将真实 LLM 手动 smoke test 做成更清晰的 opt-in 流程。
- 冻结 stable 级 release checklist、acceptance checklist、privacy/security audits。
- 继续强化 backup/restore、diagnostics、import/export、demo project 和 Provider setup 的稳定性。
