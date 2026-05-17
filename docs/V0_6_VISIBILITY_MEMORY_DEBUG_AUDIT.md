# v0.6 Visibility, Memory, and Debug Data Audit

## Audit Date

2026-05-18

## Scope

本审计聚焦 v0.6 的可见性、记忆、debug 数据隔离边界，检查 player API、Narrator 输入、debug API、authoring preview、migration、playtesting、local provider、desktop prototype、mod versioning 和 combat visible summary 是否可能泄露隐藏信息。

审查覆盖：

- `build_visible_state`
- visibility rules
- relationship/faction graph APIs
- debug timeline/performance APIs
- MemoryContextBuilder / MemoryStore visibility filters
- save migration
- authoring preview / impact-analysis
- playtesting reports
- narrative boundary / quality evals
- local model provider slice
- desktop packaging prototype
- mod versioning
- combat visible summary
- frontend player/debug/authoring separation

## Verification Commands

```powershell
rg -n "visible_state|visible_npcs|known_facts|known_rumors|known_crimes|active_combat|build_visible_state|hidden|secrets|debug|state_deltas|performance|graph|MemoryContext|filter_narrator|migration|preview-file-change|impact-analysis" backend/app backend/tests frontend/src
Get-Content backend/app/session_store.py
Get-Content backend/app/engine/rules/visibility.py
Get-Content backend/tests/evals/test_narrative_boundaries.py
Get-Content backend/app/engine/rules/relationships.py
Get-Content backend/app/engine/rules/faction_conflict.py
Get-Content backend/app/llm/memory_store.py
Get-Content backend/app/main.py
```

最近一次完整验证结果来自当前 v0.6 工作会话：

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

结果：`451 passed`；前端 build 通过。

## 已通过项目

1. hidden facts 默认不会进入 `visible_state.known_facts`。
   - `build_visible_state` 只从 `state.player_visible_facts` 生成 `known_facts`。
   - world loader / migration / eval tests 覆盖 hidden fact 不自动进入玩家可见事实。

2. hidden objects 未发现前不可见。
   - `_object_visible_to_player` 要求对象在当前位置、`visible=true`，且 `hidden=false` 或 player 在 `discovered_by`。
   - search 成功后通过 `StateDelta` 写入发现状态。

3. discoverable facts 只有发现后进入 `known_facts`。
   - `known_facts` 由 `player_visible_facts` 驱动。
   - search / quest / content tests 覆盖发现后才可见。

4. NPC secrets 默认不进入玩家上下文。
   - `Narrator.render` 只传 `success_level`、`reason`、`visible_facts`。
   - boundary eval 覆盖 NPC secret 不进入 narrator prompt。

5. hidden NPC 不进入 `visible_npcs`。
   - `_npc_visible_to_player` 要求 `visible=true` 且 `hidden=false` 或 player 已发现。
   - schedule/world tick/crime/combat tests 覆盖 hidden NPC 不进入 visible state。

6. hidden witness 不进入 player API 的主要可见区。
   - crime/social/combat tests 覆盖 hidden witness 不进入 `visible_npcs`、combat summary 和 narrative prompt。
   - known crimes 只显示玩家已知/公开的犯罪摘要，不返回 witness ids。

7. hidden relationship 不进入 player graph。
   - `build_relationship_graph(debug=False)` 过滤 `known_by_player=false` 的关系。
   - 还额外检查关系两端 actor 是否玩家可见。
   - graph tests 覆盖 hidden relationship 不进入 player graph。

8. hidden faction conflict 不进入 player graph / visible conflict summary。
   - faction graph 只显示玩家已知 faction。
   - `get_visible_faction_conflicts` 只返回玩家已知 faction，并过滤未公开 target faction。

9. debug graph 只在 `ENABLE_DEBUG_API` 开启时可用。
   - debug graph endpoints 调用 `require_debug_api()`。
   - tests 覆盖 debug disabled 返回 403。

10. debug `state_deltas` 不进入 narrator。
    - debug events 可以在 debug API 返回 `state_deltas`，但 `Narrator.render` 不接收 raw event 或 raw `state_deltas`。
    - boundary eval 覆盖 raw `state_deltas` 不进入 narrator prompt。

11. debug performance data 不包含 prompt 全文/API key。
    - instrumentation 只记录 sample name、duration、stage durations、sanitized tags。
    - sanitizer 过滤 `api_key`、`llm_api_key`、`secret`、`sk-`、`prompt`、`game_state`、`state_delta`。
    - tests 覆盖 debug performance API 不返回 API key 和 `state_deltas`。

12. memory context 过滤 hidden/debug memory。
    - `filter_narrator_safe_memories` 只允许 `player_visible` 和 `narrator_safe`。
    - `MemoryContextBuilder` 会排除 hidden/debug memory，并检查 hidden/discoverable fact 是否玩家已知。
    - boundary/v05 tests 覆盖 hidden/debug memory 不进入 narrator context。

13. migration 不改变 visibility classification。
    - migration 主要补 schema/version/default metadata。
    - migration tests 覆盖 hidden facts 迁移后仍 hidden，debug memory fixture 仍 debug-only。

14. authoring preview 不把 hidden content 推入 player UI。
    - authoring API 受 `ENABLE_AUTHORING_API` 控制。
    - preview/draft/impact 在 content pack 草稿层运行，不写 active `GameState`。
    - tests 覆盖 validate-draft 不修改 active session visible state。

15. playtesting report 不进入 player narrative。
    - playtesting 是 CLI/test harness，本身不接入 player narrative。
    - agents 通过 visible state 选择动作，不直接读取 hidden state 做普通决策。

16. narrative quality / boundary evals 覆盖主要泄露路径。
    - 覆盖 hidden fact、NPC secret、hidden witness、debug `state_deltas`、hidden/debug memory、rumor hidden fact text、procedural quest draft hidden text。

17. local model provider 不扩大可见性边界。
    - `local_stub`/`local_http` 均在 `LLMProvider` 抽象后面。
    - local provider 输出仍只能进入 intent/narrator schema，不直接写 `GameState`。

18. desktop packaging prototype 不把 `.env` 打包进前端。
    - 当前 v0.6.12 只是 PowerShell launcher 和文档，不是正式 bundle。
    - launcher 不设置 `LLM_API_KEY`，也不将其作为 `VITE_` 变量传给前端。

19. combat visible summary 不泄露 hidden NPC/witness。
    - `_visible_combat_summary` 只返回 player 或 `_npc_visible_to_player` 通过的 combatant。
    - combat tests 和 v0.6 integration test 覆盖 hidden witness 不进入 active combat summary。

## 可能泄露路径

1. `visible_state.relationships` 可能泄露隐藏 actor id。
   - `get_visible_relationships` 当前只检查 `relationship.known_by_player`。
   - 它没有像 player graph 那样检查 `source_id` / `target_id` 是否是玩家可见 NPC。
   - 如果某个 relationship 被标记为 `known_by_player=true`，但 source/target 是 hidden NPC，则 player API 的 `visible_state.relationships` 可能暴露 hidden NPC id。
   - 这是本审计发现的主要 player API 泄露路径。

2. Authoring UI / API 会显示 hidden content。
   - 这是本地创作工具的预期行为，但必须保持和 player UI 技术/视觉隔离。
   - 若前端未来复用 authoring data 到 player panel，存在泄露风险。

3. Debug timeline 返回 raw `state_deltas`。
   - 这是 debug API 的预期能力，并受 `ENABLE_DEBUG_API` 控制。
   - 风险在于前端 debug panel 或未来功能把 debug event 数据混入 player narrative。

4. Mod validation errors may include local paths in some error messages.
   - `ModLoaderError` for invalid manifest includes the manifest path in raised error text.
   - Current mod validation reports mostly use relative paths for content issues, but API/CLI error handling should avoid exposing absolute local paths outside local authoring/debug contexts.

5. Performance tags rely on blacklist sanitization.
   - Current implementation filters common sensitive terms.
   - Future tags with unusual secret names could bypass blacklist if developers add raw content as tags.

## 高风险泄露

1. `visible_state.relationships` actor visibility gap.
   - Severity: high.
   - Impact: a known relationship involving a hidden NPC can reveal that hidden NPC id through player API, even though `visible_npcs` and player graph filter it.
   - Evidence: `get_visible_relationships` filters only `relationship.known_by_player`; `build_visible_state` serializes returned source/target ids.
   - Blocking assessment: this should be treated as a v0.6 acceptance blocker unless existing content/tests prove impossible states cannot set `known_by_player=true` for hidden actors. The safer fix is small and local: filter visible relationships by player-visible actor endpoints.

## 中风险泄露

1. Debug API raw `state_deltas` can be displayed in frontend debug panel.
   - Currently isolated to debug panel and debug endpoints.
   - Continue treating debug API as local-only.
   - Add regression checks if frontend panel layout changes.

2. Authoring UI hidden content exposure is intentional but powerful.
   - Authoring pages can show hidden facts/secrets/content.
   - Must remain behind `ENABLE_AUTHORING_API` and never hydrate player panels from authoring API data.

3. Mod validation / manifest errors may expose local filesystem paths.
   - Local-only authoring/debug context makes this less severe.
   - Still preferable to normalize public API errors to relative mod paths.

4. Performance instrumentation uses blacklist redaction.
   - The current data model is safe if callers only pass ids and stage names.
   - Future instrumentation should avoid content text/prompt tags entirely rather than relying on sanitizer.

## 小问题

1. `graphs.py` player graph is more conservative than `visible_state.visible_npcs`.
   - It hides hidden NPCs even if discovered, because its `_npc_visible_to_player` ignores `discovered_by`.
   - This reduces leak risk but may under-display legitimate known relationships.

2. Some test/stub strings are mojibake.
   - Not a visibility issue, but makes audit snapshots and prompt review harder.

3. `ENABLE_DEBUG_API` defaults to true in local settings.
   - Acceptable for this local-only project, but docs and freeze checks must keep saying debug is not for public deployment.

## 修复建议

Blocking / before v0.6 acceptance:

1. Filter `visible_state.relationships` by actor visibility.
   - Recommended behavior:
     - Always allow `player`.
     - For NPC endpoints, require the NPC to be visible to the player using the same logic as `_npc_visible_to_player`.
     - If either source or target is not visible, omit the relationship from player API.
   - Add tests:
     - known relationship involving hidden NPC does not enter `visible_state.relationships`;
     - player graph and visible_state relationship filtering stay aligned.

Strongly recommended non-blocking hardening:

2. Normalize mod validation API errors to relative paths.
3. Add a frontend regression test or lightweight assertion that debug timeline state_deltas render only in debug panel.
4. Add a developer guideline: performance tags must never contain prompt text, content text, hidden fact text, raw GameState, or API keys.
5. Consider making graph visibility helper use the same discovered-by-aware NPC visibility function as visible_state, if player graph should show discovered hidden NPCs.

## 是否阻塞 v0.6

Yes, conditionally.

The audit found one high-risk player API leak path: `visible_state.relationships`
can expose a hidden NPC id if a relationship is marked `known_by_player=true`.
Because player graph already handles this correctly, the likely fix is small and
should be completed before v0.6 acceptance.

No LLM, migration, performance, combat summary, or debug graph issue by itself
blocks v0.6 from a visibility/memory/debug perspective.
