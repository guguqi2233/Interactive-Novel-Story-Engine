# 中文产品手册 / 离线帮助

本文是 v3.8 **中文产品体验打磨版**的离线使用说明。它延续 v3.7 中文本地可游玩完整产品版，面向玩家、作者和本地创作者，帮助你在本机完成写小说、Tavern RP、大世界游玩、模型配置、备份、诊断和导出。

本手册不需要账号、不依赖云同步、不连接在线市场，也不包含真实 API Key。

## v3.7 产品形态

v3.8 默认是中文 UI，并且默认面向玩家 / 创作者，而不是开发者仪表盘。首页优先显示：

- 打开 / 创建项目；
- 继续项目；
- 写小说；
- 角色 RP；
- 大世界游玩；
- 配置模型服务；
- 本地隐私与安全摘要。

Debug / QA / Authoring / Mods / Diagnostics / Product Readiness 是高级工具。它们仍然保留完整能力，但默认收纳，不会在首屏压过写作、RP 和大世界游玩入口。

v3.8 额外打磨了后端不可用恢复流程、Provider / 模型服务说明、首次使用向导、空状态、错误状态、禁用状态、备份 / 诊断说明和内联帮助。它不新增账号、云同步、在线市场或远程下载，也不改变 World Engine、Provider Gateway、`StateDelta`、`EventLog` 或 visibility 边界。

## 1. 这是什么

本地 AI 叙事工作室是一个本地优先的三合一叙事产品：

- **写小说**：管理稿件、大纲、章节、场景、人物弧线、伏笔、导出和质量检查。
- **角色 RP**：管理角色卡、RP 会话、记忆、关系、情绪、Voice/Tone、边界和安全检查。
- **大世界游玩**：通过本地 World Engine 进行开放世界行动、地图、NPC、任务、背包、模块、存档和 Timeline 查看。

LLM 可以帮助解析输入、起草文本、生成 RP 回复或渲染叙事，但它不是世界裁判。世界事实、规则、状态变化、可见性和事件记录仍由本地 World Engine 管理。

## 2. 本地优先说明

项目默认在本机运行和保存：

- 无需账号。
- 不使用云同步。
- 不上传项目。
- 不连接在线市场。
- 不远程下载包。
- 不上传诊断包。
- API Key 不进入项目文件、前端存储、日志、诊断、备份或导出。

Provider / 模型服务可以连接用户自己配置的远程或本地模型，但连接只在用户手动测试、读取模型列表或触发生成时发生。自动测试和 CI 仍使用 `mock`、`local_stub` 或 fake provider。

API Key 不进入 project、frontend storage、logs、backup、diagnostics 或 export。真实 Provider 只能由用户手动配置和手动触发；测试不调用真实 provider。

## 3. 首次启动

推荐首次流程：

1. 启动本地后端和前端。
2. 打开应用首页。
3. 创建或打开本地项目。
4. 需要真实 LLM 时，进入“模型服务”配置 Provider。
5. 测试连接并读取模型列表。
6. 为 Novel / Tavern / World / Cross-Mode / Quality 分配模型。
7. 选择“写小说”“角色 RP”或“大世界游玩”开始体验。
8. 重要操作前先运行备份 dry-run。

首页默认面向玩家/创作者，不会把 Debug、QA、StateDelta 和开发者检查全部铺在首屏。

## 4. 打开 / 创建项目

在首页可以使用：

- **打开项目**：选择已有本地项目。
- **创建项目**：创建新的本地工作区。
- **最近项目**：显示脱敏路径摘要，不显示完整敏感路径。
- **体验 Demo 项目**：打开 `examples/demo_local_narrative_project`，使用 `fake/local_stub` provider，无需真实 API Key。

打开项目只改变本地工作区引用，不会自动覆盖用户项目，也不会直接修改 `GameState`。

## 5. 配置真实 LLM / 中转站 / 本地模型

进入“模型服务”或 Provider 设置向导后，可以选择：

- OpenAI。
- OpenAI-compatible。
- 中转站 / Relay。
- 本地模型服务 / `local_http`。
- 自定义 API。
- Mock / 测试。

Relay 表示通用 OpenAI-compatible 或自定义 Base URL 配置，不代表特定中转站，也不是 API 转售服务。

密钥来源必须使用安全引用：

- `api_key_env`：只保存环境变量名，例如 `OPENAI_API_KEY`。
- `secret_ref`：保存后端 secret resolver 的引用名。
- `local_secret_ref`：保存项目外本地 secret store 的引用名。
- `transient_api_key`：仅用于一次手动测试，不持久化。

不要把真实 Key 写进项目、README、文档、测试、fixtures、导出、备份、诊断或日志。

更详细的真实 LLM 手动 smoke test 请见 `docs/REAL_LLM_MANUAL_SMOKE_TEST.md`。

## 6. 读取模型列表

配置 Provider 后，用户可以手动点击 **Test Connection** 和 **Fetch Models**。

注意：

- 连接测试可能产生费用或被 provider 计入调用。
- 读取模型列表不是所有 provider 都支持。
- 如果 provider 不支持模型列表，可以手动添加 `model_id`。
- 模型列表只保存安全 `ModelProfile` 元数据，例如模型 ID、能力标记、推荐用途和启用状态。
- 不保存 API Key、Authorization header 或 raw provider response。

## 7. 分配模型

读取或手动添加模型后，为使用场景分配模型：

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

世界输入解析建议使用支持 JSON / 结构化输出的模型。如果模型能力不足，UI 会显示 warning。模型分配只是 Provider Gateway 的路由元数据，不会让模型决定世界事实。

## 8. 写小说

Novel Studio 可用于本地写作：

1. 创建或打开稿件。
2. 编辑大纲、章节和场景。
3. 管理人物弧线、伏笔、剧情线和时间线链接。
4. 使用已分配模型进行草稿、改写或摘要。
5. 从 World 安全摘要导入章节草稿。
6. 运行 Novel Quality。
7. 导出 Markdown / TXT。

边界：

- Novel 不直接修改 World `GameState`。
- Novel -> World 必须通过 draft / proposal / validation / apply。
- 导出默认过滤 secrets、hidden refs、debug、mature/private。

## 9. 角色 RP

Tavern Studio 可用于本地角色 RP：

1. 创建或导入角色卡。
2. 设置 RP Profile、Voice、Tone、Scene Mood。
3. 开始单角色聊天或多 NPC 场景。
4. 使用已分配模型生成回复。
5. 查看 RP memory、emotion、relationship。
6. 运行 RP Safety。
7. 需要影响世界时，生成 Tavern -> World proposal。
8. 需要写作素材时，生成 Tavern -> Novel draft。

边界：

- Mature Module 默认关闭。
- NPC secrets、private persona、mature memory 不进入 normal UI 或 normal prompt。
- Tavern 不直接修改 World `GameState`。

## 10. 大世界游玩

World Studio 可用于本地大世界体验：

1. 打开 World Studio。
2. 点击“开始大世界”或“继续大世界”。
3. 输入玩家行动。
4. 后端解析行动并应用本地规则。
5. LLM 只用于输入解析和叙事渲染。
6. 查看地图、NPC、任务、背包、交易和模块面板。
7. 保存 / 读取。
8. 查看 Timeline / EventLog 安全摘要。
9. 运行 World Quality。

边界：

- UI 不直接修改 `GameState`。
- 世界变化必须走 `StateDelta` / `EventLog`。
- normal UI 只显示 `visible_state` 和安全摘要。
- raw `state_deltas` 只在 DebugGate 下可见。

## 11. Cross-Mode

Cross-Mode 用于 Novel / Tavern / World 的本地互通：

- World -> Novel：从安全 EventLog / Timeline 摘要生成章节或场景草稿。
- Tavern -> Novel：把 RP 场景整理为小说素材。
- Tavern -> World：生成 proposal，经 validation 和 confirm 后才可 apply。
- Novel -> World：把小说设定转成世界 proposal。
- World NPC -> Tavern：把可公开 NPC 摘要转成 Tavern 角色草稿。

规则：

- draft 不自动 apply。
- apply 必须 validation + explicit confirm。
- hidden/mature/private 默认过滤。
- 不做云协作或自动同步。

## 12. 创作 / Mod

Authoring / Mod Studio 是高级工具，默认收纳在“高级工具”里。

可用方向：

- World Pack Editor。
- Script Pack Editor。
- Character Pack Editor。
- Quest / Location / NPC / Item / Rumor 编辑。
- Action Mod Editor。
- Rule Module Contract UI。
- Module Browser。
- Permission Dashboard。
- Compatibility Matrix。
- Certification。
- Import / Export Wizard。
- Mod Quality Gate。
- Validation / Diff / Preview / Dry-run / Safe Apply。

边界：

- 不支持任意代码插件。
- Mod 默认是声明式内容或声明式 Action Mod。
- Action Mod 必须通过 `ActionRegistry`、`StateDelta`、`EventLog`。
- Rule Module 是 contract-only。
- Safe Apply 必须 validation / dry-run / confirm。

## 13. 质量检查

Quality Gate 是本地确定性检查，不调用真实 provider 作为裁判。

可检查：

- Project Quality。
- World Quality。
- Novel / Tavern / World 工作流。
- Cross-Mode validation。
- Hidden Leak。
- Playtest。
- Module Stress。
- Mod Quality Gate。
- Backup / Diagnostics safety。

报告应显示 safe summary，不显示 hidden text 全文、API Key、raw prompts 或 raw state deltas。

## 14. 调试 / 回放

Debug / Replay 是高级工具，不默认占据首页。

包括：

- Timeline Replay。
- EventLog Viewer。
- StateDelta Viewer。
- Visible vs Debug Compare。
- Hidden Leak Report。
- Save Migration Visualizer。
- Safe Debug Export。

边界：

- Debug UI 受 `ENABLE_DEBUG_API` 控制。
- Replay 只观察，不回写。
- StateDelta raw view 只在 DebugGate 下可用。
- Debug export 需要显式确认。

## 15. 备份 / 恢复

备份和恢复是本地数据保护流程。

备份规则：

- 先 dry-run。
- 显示包含 / 排除摘要。
- 默认排除 `.env`、API Key、provider secrets、raw env、logs、cache、database、build outputs、debug raw data、mature/private。
- 创建备份需要用户确认。

恢复规则：

- 先 dry-run。
- 检查冲突和安全状态。
- apply 必须显式确认。
- 不静默覆盖项目。

## 16. 诊断 / 导出

诊断和导出默认本地执行，不上传。

导出可覆盖：

- Novel Markdown / TXT。
- Tavern 会话摘要。
- World / package 内容。
- Mod / package。
- Diagnostics bundle。

默认过滤：

- API Key。
- `.env`。
- provider secrets。
- raw env。
- hidden refs。
- debug raw data。
- mature/private。
- raw prompts / raw outputs。

Diagnostics 需要先预览，debug bundle 需要显式确认和 Debug API。

## 17. API Key 安全

API Key 安全原则：

- 不进入前端代码。
- 不进入 project。
- 不进入 logs。
- 不进入 diagnostics。
- 不进入 backup。
- 不进入 export。
- 不进入 docs、tests、fixtures、mods、templates、prompt profiles。
- Provider UI 不显示已保存 secret。
- local secret store 如存在，必须在项目外，并被备份/导出/诊断排除。

推荐使用 `api_key_env`、`secret_ref` 或 `local_secret_ref`。一次性 `transient_api_key` 只用于当前手动测试请求。

## 18. Mature 默认关闭

Mature Module 默认关闭。

默认规则：

- mature/private 不进入 normal prompt。
- mature/private 不进入 normal export。
- mature/private 不进入 diagnostics。
- mature/private 不进入 backup。
- unknown/minor-age 或非同意场景按策略阻止。
- 本手册不提供露骨示例。

## 19. 不支持内容

v3.7 不支持：

- 账号系统。
- 云同步。
- 在线市场。
- 远程包下载。
- 在线写作平台。
- 在线 RP 平台。
- 在线游玩平台。
- 多人协作。
- 任意代码插件。
- API 转售服务。

这些不是 v3.7 近期能力。除非未来版本明确实现、测试、文档化并审计，否则不要把它们当作已支持功能。

## 20. 常见问题

**没有项目怎么办？**
在首页点击“打开项目”“创建项目”或“体验 Demo 项目”。

**没有 Provider 怎么办？**
可以先使用 Demo / `mock` / `local_stub`。需要真实 LLM 时，进入“模型服务”配置 Provider。

**模型列表读取失败怎么办？**
确认 Base URL、密钥引用和网络状态。如果 provider 不支持模型列表，可以手动添加 `model_id`。

**真实 LLM 会不会自动联网？**
不会。真实连接测试、模型读取和生成都需要用户手动触发。

**CI 会不会调用真实 provider？**
不会。CI 和自动测试必须使用 fake provider、`mock` 或 `local_stub`。

**LLM 会不会决定世界事实？**
不会。LLM 只做语言层辅助；世界事实仍由本地 World Engine、规则、`StateDelta` 和 `EventLog` 管理。

**如何回到 mock/local_stub？**
把 Provider profile 和模型分配切回 `mock` 或 `local_stub`。如果本地 shell 设置了真实 Provider 环境变量，可在本地 shell 中清空或重启后端。

**导出会包含密钥或隐藏内容吗？**
默认不会。导出、备份和诊断都有过滤摘要；debug/mature/private 需要显式 opt-in 和确认。

## 建议验证命令

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Demo 项目质量检查：

```powershell
python -m backend.app.tools.project_quality_gate examples/demo_local_narrative_project --profile fast --include-cross-mode --json
```
