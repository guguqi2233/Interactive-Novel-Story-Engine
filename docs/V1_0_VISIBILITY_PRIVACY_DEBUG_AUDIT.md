# v1.0 Visibility / Privacy / Debug Data 专项审查

Verification Date: 2026-05-19

Verdict: Pass with one medium visibility hardening item.

本审查覆盖 v1.0 player API、visible state、graph/map/shop/quest 输出、debug API、authoring API、quality/playtest/scenario reports、settings/config summary、frontend 显示边界和 narrator debug data 输入边界。审查目标是确认 hidden facts、NPC secrets、debug state_deltas、hidden memory、hidden relationship、hidden map edge、API key、raw env 等不会进入普通玩家可见面。

## 审查依据

- `backend/app/session_store.py`
- `backend/app/main.py`
- `backend/app/engine/rules/graphs.py`
- `backend/app/engine/content/map_visual.py`
- `backend/app/engine/rules/relationships.py`
- `backend/app/engine/rules/rumors.py`
- `backend/app/engine/rules/quests.py`
- `backend/app/engine/rules/economy.py`
- `backend/app/quality/reports.py`
- `backend/tests/evals/hidden_info_leaks/test_hidden_info_leaks.py`
- `backend/tests/test_v10_api_contract.py`
- `backend/tests/test_v10_final_integration_regression.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`

## 已通过项目

1. hidden facts 不会进入 `visible_state`。
   - `build_visible_state` 只从 `state.player_visible_facts` 构造 `known_facts`。
   - `WorldLoader` 和 hidden leak tests 覆盖 hidden fact 不进入 player-visible facts。

2. hidden objects 未发现前不可见。
   - `_object_visible_to_player` 要求 object 在当前位置、`visible=True`，并且 `not hidden` 或 player 已在 `discovered_by`。
   - hidden item / hidden object 在 hidden leak suite 和 final integration 中有回归覆盖。

3. discoverable facts 只有发现后进入 known facts。
   - player API 使用 `state.player_visible_facts`，不直接按 `FactVisibility.DISCOVERABLE` 暴露。
   - search / world_tick 等规则通过 `StateDelta` 显式加入 `player_visible_facts`。

4. NPC secrets 默认不进入玩家上下文。
   - `VisibleNPCResponse` 只包含 id、mood、relationship、condition。
   - `NPCState.secrets` 不进入 `build_visible_state`。
   - hidden leak eval 覆盖 NPC secret 不进入 visible_state / player context。

5. hidden NPC 不会出现在 `visible_npcs`。
   - `_npc_visible_to_player` 要求 `not npc.hidden` 或 player 已发现。
   - combat visible summary 也通过同一可见性过滤隐藏 combatant / witness。

6. hidden witness 不会出现在 player API。
   - crime/witness debug detail 不进入 `GameInputResponse` / `GameStateResponse`。
   - hidden leak suite 覆盖 hidden witness 和 raw state_deltas 不进入 player API。

7. hidden relationship 不会进入 player graph。
   - `build_relationship_graph(debug=False)` 只返回 `known_by_player` 且两端 actor 玩家可见的关系。
   - visible_state relationships 也通过 `get_visible_relationships` 检查 known_by_player 和 actor visibility。

8. hidden faction conflict 不会进入 player graph。
   - `build_faction_graph(debug=False)` 只保留玩家已知 faction / reputation。
   - hidden faction 和 unknown faction relation 不进入 player graph。

9. hidden map edge 不会进入 player map。
   - `build_player_visible_map_visual_graph` 仅保留 known location 且 edge/node visibility 不是 hidden 的内容。
   - hidden map eval 覆盖 hidden node / edge 不进入 player map graph。

10. hidden quest 不会进入 player UI。
    - `get_visible_quests` 只返回 `known_to_player` 且非 inactive 的 quest。
    - hidden quest 在 hidden leak suite 中不进入 visible_state。

11. hidden item 不会进入 player shop UI。
    - `get_shop_inventory` 要求 item 存在、`visible=True`、`not hidden`、`tradeable=True`。
    - `can_buy` 对 hidden item 返回不可购买。

12. raw `state_deltas` 只在 debug API。
    - Player API (`/game/start`、`/game/input`、`/game/state`) 返回 `visible_state` 和 narrative，不返回 EventLog 或 raw delta。
    - `/debug/sessions/.../events`、timeline 和 replay endpoint 才返回 state delta 详情，并受 debug gate 控制。

13. debug API 受 `ENABLE_DEBUG_API` 控制。
    - `require_debug_api` 检查 `enable_debug_api`。
    - debug events、timeline、debug graphs、debug performance 都调用 `require_debug_api`。
    - contract / integration tests 覆盖 disabled 时返回 403。

14. authoring API 与 player API 隔离。
    - authoring endpoint 使用 `/authoring/...` 命名空间和 `require_authoring_api`。
    - 前端将 authoring surfaces 放在 authoring zone，并标注 local / authoring-only。
    - authoring preview/validate 不修改 active GameState 的回归测试已存在。

15. quality reports normal view 不包含 hidden text。
    - `WorldQualityReport.normal_copy` 移除 `hidden_details_debug_only`。
    - `_quality_api_payload` 递归移除 `hidden_details_debug_only` 和 `*_debug_only`。
    - tests 覆盖 hidden details 不进入 normal summary / health score / quality gate payload。

16. playtest reports normal view 不包含 hidden text。
    - playtest and batch reports 使用 safe summaries / `model_dump_normal` 路径。
    - hidden leak probe 输出 normal report 时不打印 hidden fact 全文。

17. scenario regression reports normal view 不包含 hidden text。
    - scenario regression failure reasons 使用 safe summary。
    - v0.9/v1.0 integration 覆盖 forbidden visible facts 泄露时安全报告。

18. settings/config summary 不返回 raw env。
    - `/studio/config-summary` 返回 provider、布尔配置、`api_key_configured` 和 redacted database hint。
    - 不返回 `llm_api_key`、raw `.env`、完整敏感 database URL。

19. frontend 不显示 API key。
    - frontend 只读取 `VITE_API_BASE_URL`。
    - Settings 面板显示 API key 是否 configured，不显示 key 值。
    - API client 类型中没有 key value 字段。

20. narrator 无法看到 raw debug data。
    - `Narrator.render` 不接收 raw `GameState`、raw `state_deltas`、debug timeline。
    - `MemoryContextBuilder` 过滤 hidden/debug memory。
    - narrative boundary tests 覆盖 raw state_deltas 不进入 narrator prompt。

## 可能泄露路径

1. `visible_state.location.exits` 直接返回 `LocationState.exits`。
   - 当前 player map graph 会过滤 hidden map edge。
   - 但 `build_visible_state` 中 `VisibleLocationResponse.exits=location.exits` 未按 visual visibility、known locations 或 hidden/conditional edge 规则过滤。
   - 如果内容作者把隐藏出口直接写入 runtime `exits`，玩家 API 可能看到目标 location id。

2. Rumor player text 依赖 validator 和 runtime sanitizer 双重保护。
   - `_safe_rumor_text` 会在 rumor 指向未知 protected fact 且 text 包含 fact text 时返回 vague rumor。
   - 若 hidden fact 被 paraphrase 到 `text_for_player`，字符串包含检测不一定能识别语义泄露。
   - 这是内容质量 / authoring validation 限制，不是 runtime raw field 泄露。

3. debug timeline 前端可展示 raw state_deltas。
   - 当前该 UI 在 timeline/debug 区域，且数据来自 debug endpoint。
   - 若未来把同一组件复用到普通 player 区，需要保持 debug-only 标识和 endpoint gating。

4. authoring UI 可以显示完整 world pack 内容。
   - 这是本地 authoring 设计目标，不是 player API。
   - 风险在于视觉隔离或路由复用错误；当前前端使用 authoring zone 和 hidden content badges。

5. quality issue `message` 本身仍需由 analyzer 作者保持 safe。
   - `normal_copy` 会移除 `hidden_details_debug_only`，但不会自动语义审查 `message`。
   - 大部分 analyzer 使用 safe message，hidden text 放入 debug-only 或 redacted paths。

## 高风险泄露

未发现已证实的高风险泄露。

本次未发现以下 blocker：

- hidden facts 进入 `known_facts`
- hidden NPC / witness 进入 player API
- raw `state_deltas` 进入 player API
- API key 或 raw env 进入 frontend / config summary
- debug API 在 disabled 时仍可访问
- quality/playtest/scenario normal reports 输出 `hidden_details_debug_only`

## 中风险泄露

1. Player visible_state 可能通过 `location.exits` 暴露隐藏出口 id。
   - 严重性：中。
   - 当前已有 player map graph 过滤 hidden edge，但 visible_state 仍返回 runtime exits。
   - 如果 content pack 使用 exits 表示“实际可移动出口”，这可以视作设计允许；如果 exits 同时承载“隐藏出口”，则会泄露。
   - 建议 v1.0 acceptance 前明确 content contract：隐藏出口不得放入 runtime exits，或增加 visible exit filtering。

2. Rumor hidden text paraphrase 风险。
   - 严重性：中。
   - 现有 runtime 过滤完整 hidden fact text；validation 能检测直接复制 hidden fact text。
   - 无法检测所有语义等价改写。

3. Quality analyzer safe message 依赖实现纪律。
   - 严重性：中。
   - `hidden_details_debug_only` 已被剥离，但 `message` / `safe_details` 仍需 analyzer 保持无 hidden full text。
   - 现有 tests 覆盖主要质量报告 normal view。

## 小问题

1. `ENABLE_DEBUG_API` 默认值在 `Settings` 中为 true。
   - 本地工作室可接受，但文档和 `.env.example` 应继续强调 debug/local-only。
   - 发布前建议用户显式确认本地绑定地址和 debug 状态。

2. 前端 Settings 显示 “API Key configured”。
   - 不泄露 key 值，但仍暴露本地配置状态。
   - 对本地单用户工作室可接受。

3. 前端 debug/timeline 代码中有多处 state_deltas 渲染。
   - 当前位于 debug timeline / replay 区域。
   - 建议保持 CSS/标题/notice 明确区分 debug-only。

4. player graph 对 hidden-but-discovered NPC 的关系可能偏保守。
   - `build_relationship_graph` 的 `_npc_visible_to_player` 只接受 `not hidden`，未考虑 `discovered_by`。
   - 这会导致少显示，而不是泄露；非阻塞。

## 修复建议

1. 明确或实现 visible exits 过滤。
   - 最保守方案：`VisibleLocationResponse.exits` 只返回目标 location 非 hidden 或已发现的 exits。
   - 若隐藏出口不应在 runtime exits 中出现，则在 `CONTENT_PACKS` / validator 中明确禁止 hidden target 出现在 player start-known exits。
   - 为 hidden target exit 增加 player API regression test。

2. 将 rumor leakage 检测从 exact hidden text 扩展到 authoring-time warnings。
   - 保持 runtime vague fallback。
   - 在 validator 中对 hidden fact 的 keywords/tags 做更保守 warning，而不是依赖全文匹配。

3. 为 quality analyzers 增加 safe message helper。
   - 建议统一使用 `safe_issue_message(...)` 或 lint-style test，禁止 hidden fixture text 出现在 `message` 和 `safe_details`。

4. 在 frontend 继续保持 debug/authoring/player 三类区域视觉隔离。
   - Debug timeline / state_delta components 不复用到普通 player narration。
   - Authoring full content 只在 authoring route / panel 中显示。

5. 将 `ENABLE_DEBUG_API` 默认值在 v1.0 release docs 中写成“本地开发默认，可手动关闭”。
   - 若未来面向更广泛用户，建议默认关闭 debug API。

## 是否阻塞 v1.0

不阻塞 v1.0，但建议在 v1.0 acceptance 中记录一个中风险已知限制：`visible_state.location.exits` 与 visual map hidden edge 是两套机制，当前 player map graph 会过滤 hidden edge，但 runtime visible exits 需要内容规范或后续过滤来避免隐藏出口 id 泄露。

除该中风险外，当前 visibility、privacy、debug data 边界满足 v1.0 Stable Local Studio Edition 的本地稳定版要求。
