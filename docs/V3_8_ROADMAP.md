# v3.8 Roadmap: Chinese Product UX Polish

## 版本主题

**v3.8 Chinese Product UX Polish / 中文产品体验打磨版**

v3.8 延续 v3.7 “中文本地可游玩完整产品版”的方向，但不再扩张大型功能。它的目标是把现有能力打磨成更顺手的中文本地软件：用户打开应用后，应能自然理解如何打开项目、写小说、角色 RP、玩大世界、配置模型服务、恢复后端连接、备份诊断，并在需要时进入高级工具。

v3.8 不是 v4.0 stable，也不是新系统开发阶段。它是 v3.7 到 v4.0 之间的产品体验整理阶段。

## 总目标

1. 首页更像玩家 / 创作者入口，而不是开发者仪表盘。
2. 首屏突出写小说、角色 RP、大世界游玩。
3. 后端不可用时有清晰中文恢复流程。
4. Provider / 模型服务配置更容易理解。
5. 首次使用向导更简洁，不像 checklist。
6. 高级工具默认折叠，不干扰普通使用。
7. 空状态、错误状态、禁用状态中文友好。
8. 本地安全和隐私提示保留，但不压过主流程。
9. 用户可以从首页顺畅进入本地游玩、写作、RP。
10. 保持本地优先、无账号、无云同步、无在线市场。

## 明确不做

1. 不做账号系统。
2. 不做云同步。
3. 不做在线市场。
4. 不做远程包自动下载。
5. 不做在线写作 / 在线 RP / 在线游玩平台。
6. 不做多人协作。
7. 不新增大型玩法系统。
8. 不做任意代码插件。
9. 不重写 World Engine。
10. 不改变 Provider Gateway。
11. 不改变 StateDelta / EventLog / Visibility 边界。
12. 不把 UI 打磨变成大功能扩张。

## 硬性要求

1. 默认 UI 中文。
2. 首页突出写小说、角色 RP、大世界游玩。
3. Debug / QA / Authoring 默认归入高级工具。
4. 后端不可用时有“重新连接 / 查看启动指南 / 打开诊断 / 打开设置”。
5. Provider 未配置时有清晰“配置模型服务”入口。
6. 不显示 API key。
7. 不显示 hidden facts。
8. 不显示 raw `state_deltas` normal view。
9. 测试不调用真实 provider。
10. `python -m pytest` 必须通过。
11. `cd frontend && npm.cmd run build` 必须通过。
12. frontend check scripts 必须通过。

## 推荐开发顺序

1. 中文产品体验总审查。
2. Product Home UX Polish。
3. Backend Unavailable Recovery UX。
4. First-Run Tour Simplification。
5. Three Main Modes Entry Polish。
6. Provider Setup UX Final Polish。
7. Provider / Model Explanation UX。
8. Advanced Tools Collapse UX。
9. Chinese Copy Consistency Pass。
10. Empty / Error / Disabled State Polish。
11. Local Play Flow Polish。
12. Project Lifecycle UX Polish。
13. Demo Project Experience Polish。
14. Settings / Privacy UX Polish。
15. Backup / Restore / Diagnostics UX Polish。
16. QA / Debug / Replay Access Polish。
17. Navigation / Sidebar Final Polish。
18. Product Status / Next Step UX。
19. Responsive / Window Size Polish。
20. Keyboard / Focus / Accessibility UX Polish。
21. Product Help / Inline Guide Polish。
22. UI Component Cleanup。
23. v3.8 Product UX Regression Tests。
24. v3.8 Integration Regression Tests。

优先处理用户第一眼会遇到的问题：首页、后端不可用、Provider 未配置、首次向导、三大入口。随后再处理高级工具、状态文案、响应式和测试。

## 模块计划

### 1. 中文产品体验总审查

目标：确认当前 UI 与“中文产品体验打磨版”的差距。

前端变化：无代码要求，先审查 Home、导航、Provider、Tour、World、Novel、Tavern、Backup、Diagnostics、Debug / QA 默认展示状态。

后端变化：无。

测试要求：记录当前 `pytest`、frontend build、frontend check scripts 结果。

验收标准：产出 v3.8 产品体验审查结论，明确高风险、中风险、非阻塞 UX 问题。

### 2. Product Home UX Polish

目标：首页更像玩家 / 创作者入口。

前端变化：

- 首屏优先显示继续项目、打开 / 创建项目、写小说、角色 RP、大世界游玩、配置模型服务。
- Product readiness、Quality、Debug、Diagnostics 只显示简短状态或进入高级工具。
- 本地隐私提示保持简短，不压过主入口。
- 未选择项目时不铺满 disabled 面板。

后端变化：优先复用现有 safe summary API。

测试要求：Home 显示写小说 / 角色 RP / 大世界游玩；Home 不默认显示 Debug / Replay panel；Home 不显示 raw `state_deltas`、API key、hidden facts。

验收标准：用户打开应用即可理解下一步，而不是先看到开发者检查台。

### 3. Backend Unavailable Recovery UX

目标：后端不可用时给用户清晰中文恢复流程。

前端变化：将 `Backend API unavailable` 映射为中文产品错误，提供“重新连接 / 查看启动指南 / 打开诊断 / 打开设置”，错误文案不显示 stack trace、raw env、敏感路径或 API key。

后端变化：如有必要，补充安全 health / startup summary，不暴露 raw env。

测试要求：后端不可用状态显示中文恢复步骤；错误提示不泄露 secrets / stack / sensitive path。

验收标准：用户看到错误后知道先启动后端、重试连接或打开诊断。

### 4. First-Run Tour Simplification

目标：首次使用向导更像产品引导，而不是验收 checklist。

前端变化：当前步骤大卡片、进度、上一步 / 下一步 / 跳过 / 完成中文按钮、“查看全部步骤”默认折叠，默认不显示 Debug / Replay / QA 面板。

后端变化：无。

测试要求：首次向导中文显示；默认只显示当前步骤；Skip / Finish 可用；不显示 API key、debug panel、raw `state_deltas`。

验收标准：新用户能理解本地优先、打开项目、配置模型、进入三大模式的流程。

### 5. Three Main Modes Entry Polish

目标：三大入口成为产品主路径。

前端变化：写小说、角色 RP、大世界游玩分别显示状态、下一步、最近内容、Provider 模型状态和主操作；缺项目或缺 Provider 时给上下文提示，不堆 disabled。

后端变化：无 World Engine 语义变化。

测试要求：三大入口存在并中文友好；World 入口仍通过后端 action API；Novel / Tavern 不直接修改 World GameState。

验收标准：用户能从首页直接进入写作、RP 或大世界游玩。

### 6. Provider Setup UX Final Polish

目标：让普通用户能理解“模型服务”配置。

前端变化：Provider 设置中文化为“模型服务配置”，解释 OpenAI、OpenAI-compatible、中转站 / Relay、本地模型服务、自定义 API、Mock / 测试；明确 API key 不保存到项目；Test Connection / Fetch Models / Save / Assign Models 按产品流程排序；中转站说明为兼容 API base URL，不描述为 API 转售服务。

后端变化：无 Provider Gateway 语义变化。

测试要求：Provider Wizard 中文显示；transient key 不持久化；fake provider 测试连接和模型列表可用；UI 不显示 Authorization header 或 raw provider response。

验收标准：用户知道应该选择哪类模型服务，以及为什么密钥不会被保存到项目中。

### 7. Provider / Model Explanation UX

目标：解释模型、能力、分配和 fallback，降低技术门槛。

前端变化：模型能力标记用中文解释；世界输入解析提示需要 JSON / 结构化输出；模型分配按小说草稿、Tavern 回复、世界输入解析、世界叙事渲染、Cross-Mode、质量检查等使用场景展示；fallback 解释为备用模型。

后端变化：复用 ModelProfile 与 assignment validation。

测试要求：fake model list sync 成功；model assignment 保存成功；JSON capability warning 显示；no secrets rendered。

验收标准：用户能理解“读取模型列表”和“按模式分配模型”的关系。

### 8. Advanced Tools Collapse UX

目标：高级工具可找到，但不干扰普通使用。

前端变化：Advanced Tools 默认折叠，包含 Cross-Mode、Authoring / Mods、Quality、Debug / Replay、Diagnostics、Export、Product Readiness；首页只显示简短入口，不渲染完整面板；Debug / Replay 仍受 DebugGate / ENABLE_DEBUG_API 控制。

后端变化：无。

测试要求：Home 不默认显示 Debug panel；Debug / Replay 在高级工具中；raw `state_deltas` 不在 Home。

验收标准：日常写作 / RP / 游玩不被开发者功能打断。

### 9. Chinese Copy Consistency Pass

目标：统一核心中文文案，减少核心流程中英文混杂。

前端变化：统一“模型服务”“大世界”“角色 RP”“高级工具”“本地安全”“诊断”“备份 / 恢复”等表达；保留必要英文技术术语：Provider、Tavern RP、Debug、StateDelta、EventLog、Quality Gate。

后端变化：无。

测试要求：中文 UI 静态检查覆盖 Home、Provider、Settings、Backup、Diagnostics。

验收标准：普通用户主要路径以中文理解为主。

### 10. Empty / Error / Disabled State Polish

目标：状态提示更像产品，不像报错堆叠。

前端变化：Empty state 给下一步；Error state 脱敏并给恢复建议；Disabled state 说明原因并弱化展示；Provider missing、project missing、debug disabled、backend unavailable 分别有专门文案。

后端变化：如需要可提供安全错误分类，不暴露 raw details。

测试要求：missing project 中文友好；missing provider 显示配置模型服务；debug disabled 提示 ENABLE_DEBUG_API；no stack trace / secrets rendered。

验收标准：用户遇到缺配置时知道做什么。

### 11. Local Play Flow Polish

目标：写小说、角色 RP、大世界游玩更顺畅。

前端变化：首页每个入口都有清晰下一步；Provider 未配置时引导配置模型服务；项目未打开时引导打开 / 创建项目；World 没有存档时引导开始新世界；Tavern 没有角色时引导创建 / 导入角色；Novel 没有稿件时引导创建稿件。

后端变化：不改变 game loop、StateDelta 或 EventLog。

测试要求：Novel/Tavern/World empty flow 可理解；Provider missing flow 可理解；frontend build 通过。

验收标准：用户能从首页进入本地写作、RP 或大世界。

### 12. Project Lifecycle UX Polish

目标：打开、创建、最近项目、Demo 项目更顺。

前端变化：最近项目显示 safe path summary；创建项目后给下一步；打开项目失败显示中文恢复建议；不显示敏感完整路径，除非用户明确展开。

后端变化：复用 project/recent safe summary。

测试要求：no project 状态友好；recent project safe summary；demo project entry；no raw sensitive path。

验收标准：冷启动到项目选择不迷路。

### 13. Demo Project Experience Polish

目标：Demo 成为快速体验入口。

前端变化：首页显示“体验 Demo 项目”；Demo 下显示试写小说、试角色 RP、试大世界游玩；明确 Demo 使用 fake/local_stub，不需要真实 API key。

后端变化：如需导入 / 打开 Demo，必须只返回 safe summary。

测试要求：demo project quality gate 通过；demo 不含 secrets、mature/private、raw `state_deltas`；demo 不调用真实 provider。

验收标准：用户可以不用真实密钥先体验产品。

### 14. Settings / Privacy UX Polish

目标：设置页面更像中文本地软件设置。

前端变化：设置分区清晰；不出现账号、云同步、在线市场设置；Privacy 解释本地优先与 API key 安全；Mature 默认关闭。

后端变化：无。

测试要求：Settings 中文显示；no account/cloud/marketplace sections；no secrets rendered。

验收标准：用户能找到关键设置且不会误以为有在线账号能力。

### 15. Backup / Restore / Diagnostics UX Polish

目标：数据保护流程更安心。

前端变化：备份、恢复、诊断文案中文化和简化；显示过滤摘要：API key、`.env`、provider secrets、debug raw data、mature/private、db/log/cache/build outputs；Restore dry-run / confirm 明确；不上传说明清楚。

后端变化：无安全语义变化。

测试要求：backup / diagnostics UI 中文；diagnostics filtering 中文；restore confirm 存在；no secrets rendered。

验收标准：用户理解备份和诊断是本地、安全、预览优先。

### 16. QA / Debug / Replay Access Polish

目标：高级诊断能力可达但不压主流程。

前端变化：Quality / Debug / Replay 入口在高级工具中清晰命名；Debug disabled 状态中文解释；Safe Debug Export 风险提示清楚；普通页面只显示简短质量状态。

后端变化：无；Debug API 仍由 ENABLE_DEBUG_API 控制。

测试要求：Debug route / panel gated；Replay 只观察；raw StateDelta 仅 debug-gated。

验收标准：普通用户不被 Debug 干扰，高级用户可找到工具。

### 17. Navigation / Sidebar Final Polish

目标：导航结构稳定。

前端变化：主入口：首页、写小说、角色 RP、大世界；常用设置：模型服务、设置、备份；高级工具：Cross-Mode、创作 / Mod、质量检查、调试 / 回放、诊断、导出；当前模式高亮；未选择项目时减少 disabled 噪音。

后端变化：无。

测试要求：高级工具默认折叠；Debug / Replay 在高级工具中；主入口包含写小说 / 角色 RP / 大世界。

验收标准：导航像产品，而不是模块清单。

### 18. Product Status / Next Step UX

目标：让用户知道现在该做什么。

前端变化：首页和状态栏显示安全摘要；next step 按优先级显示：打开项目、配置模型、分配模型、开始写作 / RP / 大世界；状态详情进入对应页面，不在首页展开所有报告。

后端变化：复用 health / product readiness / provider status safe summary。

测试要求：missing provider warning；backend unavailable state；health summary safe。

验收标准：下一步建议清楚，不泄露敏感信息。

### 19. Responsive / Window Size Polish

目标：窗口缩放和小屏体验更稳。

前端变化：首页卡片在窄窗口下不重叠；侧栏和高级工具在小宽度下折叠合理；Provider Wizard、Tour、World 行动输入、Backup/Diagnostics 状态在小屏可读。

后端变化：无。

测试要求：build 通过；关键页面无明显文本溢出；主要 CTA 在小窗口仍可访问。

验收标准：日常桌面窗口大小下可用，不需要全屏才能操作。

### 20. Keyboard / Focus / Accessibility UX Polish

目标：延续 v3.6 可访问性，打磨中文产品路径。

前端变化：Tour、Provider Wizard、Dialog、Advanced Tools 折叠区焦点合理；后端不可用错误出现后，焦点落到恢复操作；icon-only 按钮有中文 aria-label；快捷键不触发危险操作。

后端变化：无。

测试要求：accessibility / focus checks 通过；dangerous confirm 不默认 focus destructive button；no secrets in aria-label。

验收标准：键盘和辅助技术用户可以完成核心路径。

### 21. Product Help / Inline Guide Polish

目标：减少用户跳文档的频率。

前端变化：Home、Provider、World、Backup、Diagnostics 提供短 inline guide；帮助链接到离线帮助或本地文档；文案保持简短，不压主流程。

后端变化：无，除非已有 offline help API 可复用。

测试要求：help links 不指向远程在线服务；文档不含真实 API key。

验收标准：用户能在 UI 内理解常见步骤。

### 22. UI Component Cleanup

目标：清理重复产品文案和旧 dashboard 残留。

前端变化：合并重复的 Error / Empty / Disabled 文案；移除或隐藏默认首页上的旧开发者描述；保留高级工具完整功能；不做大重写。

后端变化：无。

测试要求：frontend build 通过；v3.7/v3.8 check scripts 通过；不删除安全边界文案。

验收标准：UI 更整洁，功能边界不变。

## 回归测试

### v3.8 Product UX Regression Tests

检查 Home 中文标题、三大入口、Debug 默认隐藏、raw `state_deltas` 不进 Home、高级工具折叠、Provider missing CTA、Backend unavailable recovery、First-run tour 简化、Settings/Backup/Diagnostics 中文、no account/cloud/marketplace copy、API key 不显示。

### v3.8 Integration Regression Tests

覆盖 Home、Provider、Novel、Tavern、World、Advanced Tools、Backend unavailable、Provider missing、fake provider、model assignment、World action backend API、DebugGate、no secrets、no hidden facts、no account/cloud/marketplace entries。

## 对主要工作区的影响

Novel 继续作为首页主入口之一。v3.8 重点打磨入口文案、缺 Provider 提示、写作下一步、导出 / Quality 的上下文入口，不改变 Novel 数据语义，也不允许 Novel 直接修改 World GameState。

Tavern 继续作为首页主入口之一。v3.8 重点让“角色 RP”更直观，简化角色 / 会话 / 多 NPC 场景入口提示，保持 mature/private 默认关闭，NPC secrets 不进 normal UI。

World 是“可游玩”的核心。v3.8 重点让继续 / 开始大世界更明显，减少 Debug / EventLog 对普通游玩的干扰。World changes 仍走后端 API、StateDelta 和 EventLog。

Provider 设置是普通用户的主流程之一。v3.8 重点降低术语门槛，解释 Provider、Base URL、API key 来源、模型读取、模型分配和 fallback。Provider Gateway 语义不变，真实 provider 只允许用户手动触发。

QA / Debug / Replay 保留完整能力，但默认作为高级工具。v3.8 只打磨入口、说明和 disabled 状态，不放宽 DebugGate，不让 Replay 修改状态。

Backup / Restore / Diagnostics 继续强化中文解释：dry-run、confirm、过滤摘要、不上传、本地安全。默认排除 secrets、hidden/debug、mature/private、数据库、日志、缓存和构建产物。

## Privacy / Security / Visibility

v3.8 不放宽任何边界。中文化、折叠、缓存、恢复提示、帮助文案都不得显示 API key、hidden facts、NPC secrets、debug memory、raw prompts、raw outputs、raw provider response 或 raw `state_deltas`。

## 与 v3.7 / v4.0 的关系

v3.8 不重新定义产品范围，而是把 v3.7 打磨得更日常可用。它关注的是“第一眼”“下一步”“恢复路径”“中文解释”“少打扰”“少工程感”。

v4.0 推荐方向仍是 **Local AI Narrative Studio Stable**。v3.8 为 v4.0 准备更稳定的中文产品体验、启动恢复流程、Provider 配置路径、帮助文案和 UX 回归测试。

## 路线一致性

当前 v3.8 规划与既有路线没有冲突：

- 不引入账号、云同步、在线市场、远程下载或在线平台。
- 不改变 World Engine、Provider Gateway、StateDelta / EventLog / Visibility。
- 不调用真实 provider in tests。
- 不保存 API key 到 project、frontend、logs、backup、diagnostics 或 export。
- 不把 Debug / QA / Authoring 变成普通首页默认内容。
