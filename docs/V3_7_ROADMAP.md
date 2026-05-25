# v3.7 Roadmap: Local Playable Complete Product CN

## Documentation Sync Status

v3.7 documentation now treats the release as **Local Playable Complete Product CN / 中文本地可游玩完整产品版**:

- 默认 UI 中文，并默认面向玩家 / 创作者。
- 首页突出打开/创建项目、写小说、Tavern RP、大世界游玩、配置模型服务和本地安全摘要。
- Debug / QA / Authoring / Mods / Diagnostics / Product Readiness 是高级工具，不默认占据首屏。
- 用户可以手动配置真实 LLM API、OpenAI-compatible、通用 relay-style/custom base URL、`local_http`、`mock` 或 `local_stub`。
- 用户可以手动 Test Connection、Fetch Models、同步安全 `ModelProfile`，并按 Novel / Tavern / World / Cross-Mode / Quality 等场景分配模型。
- 测试、CI、release checklist 仍使用 fake provider、`mock` 或 `local_stub`，不得真实联网。
- API Key 不进入 project、frontend storage、logs、diagnostics、backup、export、tests、fixtures、docs 或 package/profile 文件。
- 不支持账号、云同步、在线市场、远程包下载或在线平台。
- LLM 不是世界裁判，World Engine 仍是事实源。

## 版本主题

v3.7 的新主题是 **Local Playable Complete Product CN / 中文本地可游玩完整产品版**。

旧 v3.7 已经完成 Local Complete Product 的功能收束，但默认 UI 仍偏
开发者仪表盘：Product Readiness、QA、Debug、Replay、Diagnostics、
Disabled 状态和各种验收面板堆叠过多。修正版 v3.7 的重点不是继续增加
大系统，而是把现有能力整理成打开后能正常体验、创作和游玩的中文本地产品。

## 总目标

v3.7 修正版完成后，用户打开应用时应先看到玩家 / 创作者首页，而不是
开发者控制台。默认体验应清楚引导用户：

- 继续项目；
- 写小说；
- Tavern RP；
- 大世界游玩；
- 配置模型；
- 测试 Provider；
- 读取模型列表；
- 按 Novel、Tavern、World、Cross-Mode、Quality 分配模型；
- 使用真实 LLM 进行本地写作、RP 和世界游玩；
- 在需要时进入 Debug、QA、Authoring、Diagnostics 等高级工具。

v3.7 仍保持本地优先、安全、可审计。真实 LLM 只允许用户手动配置和手动
测试，CI 和自动测试必须继续使用 fake provider / local_stub / mock。

## 与旧 v3.7 的差异

旧 v3.7 的核心是“功能完整控制台”：证明每个能力存在、可检查、可验收。

新 v3.7 的核心是“中文本地可游玩产品”：默认首页面向玩家和创作者，首屏突出
主要体验路径，开发者工具进入高级工具区，Debug / QA / Readiness 不再默认
压过正常创作和游玩流程。

主要差异：

- UI 默认中文。
- 默认首屏从 Product Readiness Dashboard 改为玩家 / 创作者首页。
- Novel / Tavern / World 成为首屏主入口。
- Provider 配置成为用户可理解的模型设置流程。
- Debug / Replay / QA / Authoring / Diagnostics 默认收纳到高级工具。
- 未选择项目时只突出打开项目、创建项目、配置模型和产品导览，不堆叠大量 disabled 面板。
- 真实 Provider 连接和模型读取允许用户手动触发，但测试和 CI 不真实联网。

## 明确不做

v3.7 修正版明确不做：

1. 不做账号系统。
2. 不做云同步。
3. 不做在线市场。
4. 不做远程包自动下载。
5. 不做在线平台。
6. 不做多人协作。
7. 不做任意代码插件。
8. 不让真实 LLM 成为世界裁判。
9. 不让 UI 直接修改 `GameState`。
10. 不让 Debug / QA 默认占据首页。
11. 不把 API key 保存进 project。
12. 不让 CI 调用真实 provider。
13. 不把测试 fake provider 替换成真实 provider。
14. 不重写 World Engine。

## 硬性边界

- UI 默认中文。
- Provider 真实连接只允许用户手动触发。
- 自动测试全部使用 fake provider / mock / local_stub。
- `ProviderProfile` 不保存明文 key。
- 如实现 local secret store，必须位于 project 外，并被 backup、export、diagnostics 排除。
- `transient_api_key` 只用于当前请求或当前会话，不进入持久化。
- normal UI 不显示 hidden facts、NPC secrets、debug memory、raw `state_deltas`。
- Debug UI 仍受 `ENABLE_DEBUG_API` 控制。
- Mature/private 默认关闭、默认不导出。
- `python -m pytest` 必须通过。
- `cd frontend && npm.cmd run build` 必须通过。
- v3.7 中文 UI、Provider 边界和端到端产品体验检查必须通过。

## 推荐开发顺序

1. 中文产品 UI 目标审查。
2. 中文 UI 文案与本地化基础。
3. 玩家 / 创作者首页重构。
4. 左侧导航降噪与高级工具折叠。
5. 中文首次使用向导。
6. 项目打开 / 创建 / 最近项目体验。
7. 真实 LLM Provider 启用后端。
8. 真实 LLM Provider 设置向导 UI。
9. 模型读取 / 模型分配最终收口。
10. 真实 LLM 运行状态与手动连通测试。
11. Novel 中文可用工作流。
12. Tavern 中文可用工作流。
13. World 中文可游玩工作流。
14. Cross-Mode 中文工作流收口。
15. Debug / QA / Authoring 高级工具隐藏策略。
16. Backup / Restore / Diagnostics 中文体验收口。
17. 中文 Settings / Privacy / Provider 收口。
18. 中文错误 / 空状态 / 禁用状态收口。
19. Demo 项目一键体验入口。
20. 真实 LLM 手动 Smoke Test 文档与安全开关。
21. 中文产品手册 / 离线帮助。
22. v3.7 中文 UI 回归测试。
23. v3.7 真实 LLM 边界回归测试。
24. v3.7 端到端产品体验测试。

第一阶段应先改变默认体验层级：中文首页、导航降噪、Debug/QA 收纳和 Provider
入口清晰化。Provider 真实连接后端和手动 smoke test 应在安全边界明确后再进入。

## 模块计划

### 1. 中文产品 UI 目标审查

目标：确认当前 UI 与“中文本地可游玩完整产品版”的差距。

前端变化：
- 盘点首屏、侧栏、导航、Tour、Provider、World、Novel、Tavern、Debug/QA 的默认展示。
- 标记需要中文化、降噪、折叠或迁移到高级工具的组件。

后端变化：无。

测试要求：
- 不改代码时只记录当前 build/check 结果。
- 如发现安全泄露，另开阻塞修复。

验收标准：
- 产出审查报告或 roadmap 更新。
- 明确哪些 UI 属于默认产品体验，哪些属于高级工具。

### 2. 中文 UI 文案与本地化基础

目标：让默认 UI 中文化，避免核心工作流仍以英文控制台文案呈现。

前端变化：
- 将首页、导航、Provider 设置、Novel/Tavern/World 入口、空状态、错误状态、禁用状态改为中文。
- 建立轻量文案常量或局部文案分组，避免散落硬编码。
- 保留必要英文专有名词，如 Novel、Tavern、Provider、Debug、StateDelta、EventLog。

后端变化：无。

测试要求：
- 新增中文 UI 静态检查，确认首屏核心文案包含中文入口。
- 确认中文 aria-label 不包含 secrets、hidden facts 或 raw debug data。

验收标准：
- 默认首屏中文可理解。
- 核心按钮和状态不再主要依赖英文。

### 3. 玩家 / 创作者首页重构

目标：默认首页从开发者仪表盘改为玩家 / 创作者首页。

前端变化：
- 首页首屏显示当前项目卡片。
- 未选择项目时显示打开项目、创建项目、配置模型、产品导览。
- 选择项目后突出继续项目、写小说、Tavern RP、大世界游玩、配置模型。
- 右侧显示下一步、项目状态、Provider 状态、本地安全摘要。
- Product Readiness Dashboard 移入高级工具或验收页。

后端变化：优先复用现有 safe summary API。

测试要求：
- 首页显示 Novel/Tavern/World 三大入口。
- 未选择项目时主 CTA 是打开/创建项目和配置模型。
- normal Home 不显示 raw `state_deltas`、API key、hidden facts。

验收标准：
- 用户打开应用即可理解下一步。
- Debug/QA/Readiness 不再压过主入口。

### 4. 左侧导航降噪与高级工具折叠

目标：导航按日常使用优先级组织。

前端变化：
- 主入口：Home、Novel、Tavern、World。
- 次级入口：Provider、Settings、Backup。
- 高级工具折叠：Authoring / Mods、QA / Quality、Debug / Replay、Diagnostics。
- 未选择项目时 Novel/Tavern/World 显示“需要项目”，但视觉弱化，不铺满 disabled 状态。

后端变化：无。

测试要求：
- Debug / Replay 不默认高亮。
- Advanced Tools 默认折叠或在下方。
- 不出现账号、云同步、在线市场主入口。

验收标准：
- 玩家和创作者路径清晰。
- 开发者工具仍可进入，但不默认抢占视线。

### 5. 中文首次使用向导

目标：将 13 步 onboarding 简化为中文单步卡片体验。

前端变化：
- 显示当前步骤大卡片。
- 显示进度，如 `1/13`。
- 支持 Back、Next、Skip、Finish。
- `View all steps` 折叠显示全部步骤。
- 默认不显示 Debug 面板。

后端变化：无。

测试要求：
- Tour 可打开、跳过、重新打开。
- Tour 文案明确本地优先、无账号、无云同步、无在线市场。
- Provider 步骤不要求明文 API key。

验收标准：
- 新用户能理解从项目到 Provider 到三大模式的流程。

### 6. 项目打开 / 创建 / 最近项目体验

目标：让用户在没有项目时不迷路。

前端变化：
- 首页未选择项目状态只突出打开项目、创建项目、最近项目、配置模型。
- 最近项目显示 safe path summary，不显示敏感路径。
- 创建项目后引导进入 Novel/Tavern/World 或 Provider 设置。

后端变化：复用 Project API 和 Recent Projects safe summary。

测试要求：
- no project 状态友好。
- 不显示一屏 disabled 工具。
- 不显示 raw path、secrets、debug data。

验收标准：
- 从冷启动到项目选择的路径清楚。

### 7. 真实 LLM Provider 启用后端

目标：允许用户手动启用真实 Provider 连接测试和模型读取，同时保持 CI fake provider。

前端变化：无或仅展示安全状态。

后端变化：
- 明确区分测试/CI fake client 与用户手动 real client。
- 增加安全开关或请求标记，只有用户显式触发时才允许真实 provider client。
- 真实请求不得在自动启动、后台刷新、测试、quality gate 或 CI 中发生。
- 响应必须继续脱敏。

测试要求：
- fake provider 测试继续覆盖 success/auth_failed/missing_secret/timeout/model_list_failed。
- 自动测试断言不调用真实网络。
- 真实 client 路径只做可注入/手动 smoke test 文档，不在 CI 执行。

验收标准：
- 用户可以手动测试真实 Provider。
- CI 永不真实联网。

### 8. 真实 LLM Provider 设置向导 UI

目标：让普通用户能理解并配置真实 LLM。

前端变化：
- 中文设置向导支持 provider type、base URL、api_key_env、secret_ref、local_secret_ref。
- 可选一次性 transient key 测试，但明确不保存。
- 明确“不保存到项目、不进日志/备份/导出/诊断”。
- 提供 Test Connection、Fetch Models、Sync Models CTA。

后端变化：
- 如实现 `local_secret_ref`，必须 project 外存储并默认被 backup/export/diagnostics 排除。
- 保存 ProviderProfile 时仍不得保存明文 key。

测试要求：
- ProviderProfile 不含明文 API key。
- transient key 不持久化。
- UI 不把 key 放入 localStorage/sessionStorage。

验收标准：
- 用户可配置真实 Provider，但安全边界清晰。

### 9. 模型读取 / 模型分配最终收口

目标：模型列表和分配流程成为清晰产品路径。

前端变化：
- 中文模型列表，支持搜索、能力筛选、启用状态。
- 模型分配按 Novel、Tavern、World、Cross-Mode、Quality 展示。
- JSON 能力和 streaming/tool 支持以中文 warning 展示。
- 首页 Provider 摘要只显示配置状态和下一步，不展示过多模型调试细节。

后端变化：复用 ModelProfile sync 和 routing validation。

测试要求：
- fake model discovery 成功。
- unsupported_model_list 安全提示。
- 模型分配 capability warning 正确。

验收标准：
- 用户能从 Provider 设置走到模型分配完成。

### 10. 真实 LLM 运行状态与手动连通测试

目标：显示真实 LLM 是否可用，但不后台自动探测。

前端变化：
- Provider 状态展示为未配置、已配置未测试、已连接、失败、缺少密钥等中文状态。
- 慢 Provider、超时、高错误率显示安全建议。
- 所有测试和刷新按钮必须是用户手动触发。

后端变化：
- 真实请求只在明确手动动作中执行。
- 连接状态 cache 不保存 secrets 或 raw response。

测试要求：
- fake provider 覆盖状态。
- cache 不含 API key/transient key/raw response。

验收标准：
- 用户知道模型服务是否可用，并知道下一步。

### 11. Novel 中文可用工作流

目标：Novel Studio 作为中文写作工作区可用。

前端变化：
- Novel 入口中文化：继续写作、打开大纲、章节、场景、导出、质量检查。
- Provider 未配置时给中文下一步，而不是开发者 warning 堆叠。
- LLM 写作动作必须通过 Provider Gateway。

后端变化：无语义改变。

测试要求：
- Novel 入口可编译。
- no project / missing provider 状态中文友好。
- Novel 不直接修改 World GameState。

验收标准：
- 用户能从首页进入写小说流程。

### 12. Tavern 中文可用工作流

目标：Tavern RP 作为中文角色 RP 工作区可用。

前端变化：
- Tavern 入口中文化：角色卡、会话、单人聊天、多 NPC 场景、记忆、边界、导出。
- Mature/private 默认关闭说明简洁可见。
- Provider 未配置时提示配置模型。

后端变化：无语义改变。

测试要求：
- Tavern 入口可编译。
- NPC secrets / mature memory 不进 normal UI。
- Tavern 不直接修改 World GameState。

验收标准：
- 用户能从首页进入本地 RP。

### 13. World 中文可游玩工作流

目标：World Studio 是“可游玩”而不是“可检查”。

前端变化：
- 首页明确显示 Continue World、Start World、Open World Studio。
- 无项目或无存档时提示“创建/打开项目后即可开始大世界游玩”。
- World 主界面突出叙事、行动输入、地图/NPC/任务/背包、保存/读取。
- Debug/Timeline/EventLog 默认不在普通游玩首屏。

后端变化：无 World Engine 语义改变。

测试要求：
- World 入口中文 CTA 存在。
- normal World UI 使用 `visible_state`。
- hidden facts、NPC secrets、raw `state_deltas` 不显示。

验收标准：
- 用户能明显看见并开始大世界游玩。

### 14. Cross-Mode 中文工作流收口

目标：让 Novel / Tavern / World 互通流程可理解。

前端变化：
- 中文展示 draft、proposal、review、validation、apply、audit。
- Apply 仍需 confirm。
- hidden/mature/private 默认过滤。

后端变化：无语义改变。

测试要求：
- Cross-Mode 不绕过 validation/apply。
- Draft 不修改 GameState。

验收标准：
- 用户理解“草稿/提案不是世界事实”。

### 15. Debug / QA / Authoring 高级工具隐藏策略

目标：保留能力，但不默认占据首页。

前端变化：
- Debug / Replay、QA / Quality、Authoring / Mods、Diagnostics 进入 Advanced Tools。
- Debug 默认关闭。
- Debug route 或 drawer 打开后仍显示 DebugGate。
- Product Readiness Dashboard 移到高级工具或验收页面。

后端变化：无。

测试要求：
- 首屏不默认显示 Timeline Replay、EventLog、StateDelta、Hidden Leak。
- Debug disabled 状态清晰。
- raw debug details 仍 gated。

验收标准：
- 日常使用不被开发者面板干扰。

### 16. Backup / Restore / Diagnostics 中文体验收口

目标：让本地数据保护流程可理解。

前端变化：
- Backup、Restore、Diagnostics 中文化。
- 显示 dry-run、确认、过滤摘要、排除项。
- 不上传、不云同步的说明简洁可见。

后端变化：无语义改变。

测试要求：
- diagnostics/backup/export 不含 secrets。
- restore apply 仍需 confirm。

验收标准：
- 用户理解如何安全备份和诊断。

### 17. 中文 Settings / Privacy / Provider 收口

目标：设置页成为普通用户能理解的本地配置中心。

前端变化：
- 中文分区：通用、本地隐私、Provider、模型、导出、Debug、备份恢复、诊断、Mature、UI 偏好。
- 不出现账号、云同步、在线市场设置。
- Provider 区不显示 API key 值。

后端变化：无语义改变，除非实现 local secret store。

测试要求：
- Settings 关键分区存在。
- Mature 默认 disabled。
- no secrets rendered。

验收标准：
- 用户能找到关键配置。

### 18. 中文错误 / 空状态 / 禁用状态收口

目标：减少 disabled 堆叠，改为上下文提示。

前端变化：
- Empty state 给下一步。
- Error state 脱敏并给修复建议。
- Disabled state 说明原因，但不占据一屏。
- 未选项目时不渲染大量 disabled 工具卡。

后端变化：无。

测试要求：
- 错误状态不显示 stack/secrets/sensitive path。
- no project 首页只显示关键 CTA。

验收标准：
- 用户不会被禁用面板淹没。

### 19. Demo 项目一键体验入口

目标：让用户能快速体验本地产品。

前端变化：
- 首页提供“打开 Demo 项目”或“导入 Demo 项目”入口。
- 说明 demo 使用 fake/local_stub，不真实联网。
- Demo 入口不覆盖用户项目。

后端变化：
- 如需要，提供安全 demo project copy/import 流程。
- 必须防路径穿越，不包含 secrets。

测试要求：
- demo project quality gate 通过。
- demo 不含 `.env`、db、logs、cache、build outputs、secrets。

验收标准：
- 新用户可以快速体验 Novel/Tavern/World/Cross-Mode。

### 20. 真实 LLM 手动 Smoke Test 文档与安全开关

目标：提供用户手动验证真实 LLM 的安全说明。

前端变化：
- Provider 设置页链接到手动 smoke test 说明。
- 真实测试按钮说明“只在点击时联网”。

后端变化：
- 提供明确开关或注入点，避免 CI 误用真实 client。

测试要求：
- CI 扫描确认真实 provider 测试默认不运行。
- 文档不写真实 key。

验收标准：
- 用户可手动测试真实 Provider，自动测试不真实联网。

### 21. 中文产品手册 / 离线帮助

目标：文档同步到中文本地可游玩产品。

文档变化：
- README、SPEC、PRODUCT_GUIDE、V3_7_RELEASE_NOTES、离线帮助更新。
- 说明 v3.7 默认面向玩家/创作者。
- 说明 Debug/QA/Authoring 是高级工具。
- 说明 Provider 可手动配置真实 API，但 CI 不真实联网。

测试要求：
- 文档不含真实 API key。
- 不声称支持账号、云同步、在线市场。

验收标准：
- 用户能离线理解如何开始。

### 22. v3.7 中文 UI 回归测试

目标：防止 UI 回到开发者仪表盘堆叠。

检查内容：
- 首页中文主入口存在。
- Novel/Tavern/World 三大入口存在。
- 未选择项目时主 CTA 是打开/创建项目和配置模型。
- Debug / Replay 不默认显示。
- no account/no cloud/no marketplace 文案存在但不压过主入口。

验收标准：
- `npm.cmd run check:v37-product-cn` 或等价脚本通过。

### 23. v3.7 真实 LLM 边界回归测试

目标：确保真实 LLM 能力不破坏安全边界。

测试内容：
- ProviderProfile 不保存明文 key。
- transient key 不持久化。
- cache/logs/diagnostics/backup/export 不含 key。
- fake provider 覆盖所有 CI 测试。
- 真实 provider 测试默认跳过，必须手动开关。

验收标准：
- `python -m pytest` 通过。
- 静态扫描确认无真实 provider CI 调用。

### 24. v3.7 端到端产品体验测试

目标：验证本地产品体验闭环。

测试内容：
- 冷启动首页。
- 打开/创建项目。
- 配置 Provider。
- 读取模型。
- 分配模型。
- 进入 Novel / Tavern / World。
- World start/continue 入口存在。
- Cross-Mode、Backup、Diagnostics 可从合适入口进入。
- Debug/QA 在高级工具中。

验收标准：
- frontend build 通过。
- v37 中文产品检查通过。
- pytest 通过。
- 不出现 release blocker。

## 对各工作区的影响

### Novel Studio

Novel 变成首页主入口之一，默认中文展示“继续写作 / 打开小说 / 导出 / 质量检查”。
Provider 未配置时给清晰下一步，但 Novel 不直接修改 World。

### Tavern Studio

Tavern 变成首页主入口之一，默认中文展示“角色 RP / 会话 / 多 NPC 场景 / 边界设置”。
Mature/private 默认关闭，Tavern 仍不能直接修改 World。

### World Studio

World 变成首页主入口之一，必须明确显示 Continue World、Start World、Open World Studio。
normal World UI 仍只使用 `visible_state` 和 safe summaries。

### Authoring / Mod Studio

Authoring / Mods 保留为高级工具。它不再默认占据首页，但仍可用于本地包编辑、
验证、dry-run、权限、兼容和 safe apply。

### Provider Gateway / Provider Connectivity

Provider 配置升级为产品主流程。用户可手动配置真实 Provider、测试连接、读取模型、
分配模型。Provider Gateway 仍是唯一模型入口，Provider 不能改变世界事实。

### QA / Debug / Replay

QA / Debug / Replay 保留完整能力，但默认收纳进高级工具。Debug 仍必须受
`ENABLE_DEBUG_API` 控制，Replay 只观察，不修改 GameState 或 EventLog。

### Backup / Restore / Diagnostics

中文化并保留本地安全流程。默认排除 secrets、hidden/debug、mature/private、
数据库、日志、缓存和构建产物。Diagnostics 不上传。

### Privacy / Security / Visibility

修正版 v3.7 不放宽任何边界。中文化和产品化不能让 normal UI 显示 hidden facts、
NPC secrets、debug memory、raw `state_deltas`、API key、raw prompt/output 或
provider raw response。

## v4.0 候选方向

v4.0 推荐方向仍是 **Local AI Narrative Studio Stable**。

候选重点：
- 冻结核心产品 UI。
- 稳定真实 Provider 手动配置体验。
- 完成中文/英文双语文案体系，如需要。
- 做最终安全、隐私、可用性和安装/启动体验审计。
- 收敛 demo、手册、备份、导出和本地启动流程。
- 只在 v3.7 修正版达到“可正常体验和游玩”后进入稳定版准备。
