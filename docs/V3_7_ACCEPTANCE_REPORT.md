# v3.7 Acceptance Report: Local Playable Complete Product CN

## Verdict

**Accepted: v3.7 Local Playable Complete Product CN。**

v3.7 通过系统验收，可作为“中文本地可游玩完整产品版”进入最终冻结。当前版本默认呈现面向玩家 / 创作者的中文首页，Debug / QA / Authoring / Diagnostics 已收纳到高级工具，真实 LLM Provider 支持用户手动配置与手动测试，自动测试仍使用 fake/local_stub provider，并保持 World Engine、StateDelta/EventLog、Visibility、Provider Gateway、secret 与本地优先边界。

本次验收未发现 release-blocking 问题。

## Verification Date

2026-05-25 (Asia/Shanghai)

## Verification Commands

| Command | Result |
| --- | --- |
| `python -m pytest` | Passed: `1820 passed in 204.86s`. |
| `cd frontend && npm.cmd run build` | Passed. Main App chunk: `App-sGtYzRJb.js` 476.63 kB, gzip 120.04 kB. No Vite >500 kB warning emitted. |
| All frontend `check:*` scripts from `frontend/package.json` | Passed: 62 / 62 scripts. 覆盖 v2.9-v3.6 回归检查，以及 v3.7 中文产品、Provider、工作流、端到端产品体验检查。 |
| `python -m backend.app.tools.project_quality_gate examples/demo_local_narrative_project` | Passed: `Project quality gate: PASS`; 0 blockers, 0 errors, 0 warnings. |

## Scope Accepted

- v3.7 默认产品形态是 **中文本地可游玩完整产品版**。
- 默认首页面向玩家 / 创作者，而不是开发者仪表盘。
- 首页突出打开 / 创建项目、体验 Demo、配置模型服务、写小说、角色 RP、大世界游玩。
- Debug / Replay、Quality Gate、Product Readiness、Authoring / Mods、Diagnostics、StateDelta Viewer、EventLog Viewer、Hidden Leak Report 保留，但作为高级工具进入，不占据首屏。
- Provider 设置支持真实 runtime 配置；测试与 CI 仍使用 fake/local_stub provider。
- Novel、Tavern、World、Cross-Mode、Backup / Restore / Diagnostics、Export、Demo 项目流程作为本地产品路径被验收通过。
- API key、transient key、hidden/debug/raw state、mature/private、本地优先等安全边界继续保持。

## Product UI Review

Passed.

- v3.7 首页使用中文产品文案，产品名与定位为“本地 AI 叙事工作室”。
- 首屏突出“写小说”、“角色 RP”、“大世界游玩”，不再默认呈现 Debug / Replay 或 readiness checklist 堆叠。
- 未选择项目时，主要引导为打开项目、创建项目、体验 Demo、配置模型服务；不会把所有模块铺成一屏 disabled 状态。
- 高级工具可找到但默认折叠，不干扰正常创作 / 游玩入口。
- v3.7 中文产品检查确认：Home 不显示 raw `state_deltas`，不显示 API key，不默认显示 Debug / Replay panel。

## Real LLM Runtime Review

Passed.

- Provider 设置支持 OpenAI、OpenAI-compatible、relay-style compatible endpoint、`local_http`、custom provider，以及 mock/test provider。
- 用户可手动 Test Connection、Fetch Models、同步安全 `ModelProfile` metadata、手动添加 model_id，并按 Novel、Tavern、World、Cross-Mode、memory/summary、Quality 等使用场景分配模型。
- 真实 provider 调用只在用户手动触发时发生；启动、测试、CI、frontend check 不调用真实 provider。
- `ProviderProfile` 不保存明文 API key。支持的 secret 来源保持为 `api_key_env`、`secret_ref`、已配置时的 `local_secret_ref`，以及 request/session-only 的 `transient_api_key`。
- Provider error/status summary 已脱敏；raw provider response、Authorization header、API key、transient key、raw env 不进入正常前端产品视图。
- Novel / Tavern / World 使用 LLM 时仍通过 Provider Gateway。Provider 只能影响措辞、延迟、成本、格式，不能裁判世界事实。

## Playability Review

Passed.

- Novel workflow 可从中文首页进入，支持本地写作、稿件 / 章节、Provider 状态提示、安全导出、Novel Quality。
- Tavern workflow 可从中文首页进入，支持本地角色 RP、多 NPC 场景入口、RP memory / emotion / relationship 状态、mature 默认关闭、RP Safety。
- World workflow 可从中文首页进入，提供“开始大世界 / 继续大世界”类入口、行动输入、visible map/NPC/quest/inventory/module panels、save/load、Timeline、World Quality。
- Cross-Mode workflow 保持 draft/proposal/review/apply 模式；apply 需要明确确认，不自动同步。
- Backup / Restore / Diagnostics 与 Export 提供中文过滤说明、本地不上传语义、必要 dry-run / confirm、默认排除 secrets/debug/mature/private。
- `examples/demo_local_narrative_project` 通过 project quality gate，可作为安全本地 Demo 路径，并使用 fake/local_stub Provider 配置。

## Boundary Review

Passed.

- UI 不直接修改 `GameState`。
- World-changing actions 继续通过后端 game/action API、`StateDelta`、`EventLog`。
- LLM 是语言 / 解析 / 叙事层，不是世界裁判。
- `visible_state` 与 safe summary 仍是 normal UI 数据来源。Hidden facts、NPC secrets、debug memory、raw prompts、raw provider responses、raw `state_deltas` 不进入 normal UI。
- StateDelta Viewer 与 raw debug surfaces 继续 debug-gated。
- Debug / Replay 只观察，不 apply delta，不写入 `GameState`。
- Mature/private 默认关闭，默认不进入 normal export / backup / diagnostics。
- v3.7 未引入账号系统、云同步、在线市场、远程包自动下载、在线 RP / writing / play 平台或 API 转售服务。

## Known Limitations

- 真实 LLM smoke test 仍是手动流程，不进入 CI。用户手动连接真实 provider 时可能产生费用，并会向所配置 provider 发送 prompt。
- 部分高级 / 调试 / 管理界面保留 Provider、Debug、StateDelta、EventLog、Quality Gate 等中英混合技术术语，以避免边界概念被弱化。
- v3.7 是本地可游玩完整产品候选版，不是 v4.0 stable packaging/release line。
- Demo 内容刻意保持小型、安全、确定性；它验证产品路径，不代表完整长篇内容展示。
- 本次验收按要求运行自动化命令；未额外执行浏览器级人工视觉验收。

## Acceptance Risks

- 真实 Provider 行为取决于用户配置、endpoint compatibility、认证、超时、模型列表支持情况。这是手动 runtime 风险，不是 CI 要求。
- 模型能力 metadata 来自安全 discovery 或手动标注；World intent parser 使用模型前仍应关注 JSON / structured-output warning。
- 后续 UI 文案修改必须保持中文可游玩产品定位，避免首屏重新退化为开发者仪表盘。
- 后续 cache / performance 改动必须继续保持 no-secret、no-hidden、no-raw prompt/output、no-raw-delta 边界。

## Recommended v4.0 Priorities

- 收束为 Local AI Narrative Studio Stable，并打磨 launcher / packaging / release 流程。
- 将真实 LLM 手动 smoke test checklist 做成更清晰的 opt-in UI 与文档流程。
- 执行浏览器级视觉验收，覆盖中文 Home、Provider Wizard、Novel、Tavern、World、Backup、Diagnostics、Settings。
- 继续打磨中文文案，同时保留必要的技术边界术语。
- 冻结 v4.0 文档、release checklist、acceptance checklist。
- 继续强化 backup/restore、diagnostics、import/export、Demo 项目与非开发者使用体验。

## Final Status

**Accepted for v3.7 final freeze.**

当前项目满足 v3.7 Local Playable Complete Product CN 验收范围。后端测试、前端生产 build、全部 frontend check、Demo project quality gate 均通过。未发现 high-risk release blocker。
