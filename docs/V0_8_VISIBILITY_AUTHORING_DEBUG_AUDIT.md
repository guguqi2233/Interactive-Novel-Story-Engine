# v0.8 Visibility / Authoring / Debug Data Audit

## Audit Date

2026-05-18

## Scope

This audit reviews v0.8 visibility, authoring isolation, and debug-data boundaries. The reviewed areas include:

- Player `visible_state`, visible facts, visible NPCs, visible objects, player map, player graph, player shop UI, and narrator context.
- v0.8 authoring tools: Map Editor, Quest Graph Editor, NPC Goal Editor, Faction / Relationship Editor, Item / Economy Editor, Rumor / Crime Consequence Editor, Validation Graph, Template Browser, Branch / Diff, Import / Export, Prompt Profiles, and Authoring UX shared components.
- Debug-only surfaces: Timeline Replay and raw `state_deltas`.
- Scenario Regression reports and prompt/memory filtering.

## Verification Commands

Commands used during this audit pass:

```powershell
rg -n "visible_state|visible_npcs|known_facts|hidden|secret|witness|state_deltas|narrator|authoring|debug|player graph|visible map|shop|PromptProfile|template|import|export" backend/app frontend/src backend/tests/test_v08_integration_regression.py docs/V0_8_ROADMAP.md
rg -n "MapVisual|QuestGraph|NPCGoal|RelationshipAuthoring|ItemEconomy|RumorCrime|ValidationGraph|TimelineReplay|WorldBranch|ScenarioRegression|PromptProfile|LocalPackage|hidden" backend/app/engine/content backend/app/core backend/app/scenarios backend/app/llm backend/app/main.py frontend/src backend/tests -g "*.py" -g "*.tsx" -g "*.ts"
```

Focused files read during this audit:

- `backend/app/engine/rules/visibility.py`
- `backend/app/engine/content/map_visual.py`
- `backend/app/core/timeline_replay.py`
- `backend/app/llm/context_builder.py`
- `backend/app/engine/content/import_export.py`
- `backend/app/llm/prompt_profiles.py`

Latest full verification already run in this v0.8 work session:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Latest result in this session: `python -m pytest` passed with 596 tests, and frontend build passed.

## 已通过项目

1. **hidden facts 不进入 `visible_state`**
   - Visibility is still based on explicit player-visible facts and discovery state.
   - Existing tests cover hidden facts remaining hidden across world load, migrations, regressions, and integration flows.

2. **hidden objects 未发现前不可见**
   - `get_visible_facts` checks hidden object discovery before adding object ids to visible facts.
   - Search and visibility tests cover hidden object filtering.

3. **discoverable facts 只有发现后进入 `known_facts`**
   - Memory and visibility paths distinguish hidden/discoverable facts from player-visible facts.
   - `MemoryContextBuilder` excludes undiscovered discoverable facts from narrator/player memory context.

4. **NPC secrets 默认不进入玩家上下文**
   - NPC knowledge remains rule-bound.
   - Authoring can show local creator data, but player visible state and narrator context do not receive NPC secrets by default.

5. **hidden NPC 不出现在 `visible_npcs`**
   - NPC visibility requires `visible` and either not hidden or discovered by the actor.
   - Tests cover hidden NPC schedule, sneak, reaction, planning, combat summary, and integration boundaries.

6. **hidden witness 不出现在 player API**
   - Crime/witness and social tick tests cover hidden witness exclusion from player-visible payloads.
   - v0.8 does not add a new player witness exposure path.

7. **hidden relationship 不进入 player graph**
   - Relationship graph tests and v0.8 integration checks assert hidden relationship ids such as `hidden_edge` do not appear in player graph responses.

8. **hidden faction conflict 不进入 player graph**
   - Faction graph/player graph paths use known/visible faction state, while authoring/debug graph surfaces remain separate.

9. **authoring UI 与 player UI 隔离**
   - v0.8 Authoring UX uses explicit authoring panels and authoring-only labels.
   - Player UI is not the consumer of authoring graph payloads.

10. **Map Editor 不把 hidden exits 显示到 player map**
    - `build_player_visible_map_visual_graph` filters hidden nodes and hidden edges.
    - Edges are only included when both endpoints are player-known and non-hidden.

11. **Quest Graph Editor 不把 hidden quest 显示到 player UI**
    - Quest graph editor operates under authoring APIs.
    - Existing quest visible-state tests cover hidden quest exclusion from player visible state.

12. **NPC Goal Editor 不把 hidden goal 显示到 player UI**
    - NPC goal authoring is an authoring API surface.
    - Tests cover hidden NPC goal data not appearing in player visible state.

13. **Relationship Editor 不把 hidden relationships 显示到 player UI**
    - Authoring graph may show local creator relationship details.
    - Player graph tests verify hidden relationships remain filtered.

14. **Item / Economy Editor 不把 hidden shop inventory 显示到 player shop UI**
    - Validation warns that hidden shop inventory is authoring/debug-only until discovered.
    - Economy/player shop tests cover hidden item filtering.

15. **Rumor / Crime Editor 不泄露 hidden fact text**
    - Validation detects rumor text that repeats hidden fact text with `rumor_reveals_hidden_fact`.
    - v0.8 integration tests exercise this warning path.

16. **Validation Graph 不泄露敏感本地路径**
    - Validation graph is derived from structured validation issues, file names, paths, ids, and issue codes.
    - v0.8 tests assert placeholder secret strings are not included in validation graph output.

17. **Timeline Replay 只在 debug API enabled 时可用**
    - Timeline replay endpoints are under `/debug/...`.
    - Raw state deltas are exposed only through debug timeline responses, not player APIs.

18. **debug `state_deltas` 不进入 narrator**
    - Timeline replay uses raw `state_deltas` for local debugging.
    - Narrator/memory context paths remain separate and filtered.

19. **Branch / Diff 不把 authoring-only hidden details 混入 player UI**
    - Branch/diff APIs are authoring-only and produce structured authoring reports.
    - They are not consumed by player state or narrator.

20. **Scenario Regression report 不显示 hidden fact 全文**
    - Scenario regression redacts known hidden text before returning failure reasons and hidden leak summaries.
    - Tests assert hidden fixture text is not present in API responses.

21. **Template Browser 不执行脚本**
    - Template renderer rejects unsafe paths and executable file suffixes.
    - Preview does not write disk, and apply uses explicit validation/save flow.

22. **Import / Export 不导入 `.env` / API key**
    - Import/export validation rejects `.env`, secrets files, DB files, logs, and executable code.
    - Zip slip/path traversal is rejected.

23. **Prompt Profile 不能启用 hidden facts**
    - Prompt profile validation rejects hidden facts, NPC secrets, raw GameState, raw state deltas, and GameState write-authority language.
    - Integration tests assert prompt profile config output does not contain unsafe hidden-fact language.

24. **narrator 无法看到 raw `state_deltas`**
    - Player state integration tests assert `state_deltas` is absent from `/game/state`.
    - Raw deltas remain debug timeline data, not narrator input.

## 可能泄露路径

1. **Authoring data is intentionally complete**
   - Authoring APIs can show hidden locations, quests, NPC goals, relationships, and content text to the local creator.
   - This is expected, but it must remain isolated from player UI and narrator prompts.

2. **Debug timeline contains raw `state_deltas`**
   - This is intended for local debugging.
   - It is sensitive debug data and must remain behind `ENABLE_DEBUG_API`.

3. **Branch / Diff and Validation Graph can mention hidden-risk references**
   - These are authoring-only diagnostics.
   - They should not be rendered in player-facing panels or narrative responses.

4. **Import / Export save bundles contain runtime state**
   - Save bundles can contain hidden state by design.
   - They must remain local package artifacts and should not be displayed as player summaries.

5. **Prompt profiles can influence prompt wording**
   - Current validation blocks attempts to request hidden facts or raw state deltas.
   - Future profile fields must stay structured and bounded.

## 高风险泄露

未发现高风险泄露。

No reviewed v0.8 path was found that sends hidden facts, hidden objects, hidden NPCs, hidden witnesses, hidden relationships, hidden faction conflicts, raw `state_deltas`, or debug memory into player visible state or narrator context.

## 中风险泄露

1. **Debug timeline raw deltas require strict gate discipline**
   - `TimelineReplay` intentionally includes raw `state_deltas`.
   - Current implementation keeps this under debug endpoints.
   - Risk becomes medium only if frontend routing or future API reuse places timeline data in non-debug/player areas.
   - Blocking: no.

2. **Authoring UI hidden content isolation depends on frontend composition**
   - v0.8 has many authoring panels, all designed as local creator tools.
   - The main risk is accidental reuse of authoring payloads inside player UI components.
   - Current tests include player-boundary assertions, but this should remain a recurring regression focus.
   - Blocking: no.

3. **Save package import/export can carry hidden runtime state**
   - Save bundle exports are expected to include full local save state and EventLog.
   - Import/export API rejects secrets and unsafe files, but UI summaries must continue avoiding raw save display.
   - Blocking: no.

## 小问题

1. Validation graph issues can include file/path-like YAML paths. Current output is content-relative, not local absolute paths, but future messages should avoid adding absolute filesystem paths.
2. Scenario regression redaction currently targets known hidden fixture strings and leak summaries. Future custom scenario packs should continue returning safe summaries rather than hidden text.
3. Prompt profile validation uses forbidden-term checks for authority/hidden access. A stricter allowlist would be more robust if profiles grow.
4. Source review found recurring PowerShell profile loading warnings during local commands; this is unrelated to project visibility behavior.

## 修复建议

1. Add a recurring integration assertion that player UI/API responses never include:
   - `state_deltas`,
   - `debug_only`,
   - hidden relationship ids,
   - hidden quest ids,
   - hidden fact text.
2. Keep timeline replay and validation graph APIs debug/authoring-only and never reuse their response types in player endpoints.
3. Add a small frontend test or static check that authoring-only components are not rendered inside the player narrative/state panel.
4. Extend scenario regression redaction to use content-pack hidden fact texts dynamically if custom scenario fixtures are added.
5. Prefer allowlisted prompt profile fields and enum variants over free-form security-sensitive instructions.
6. Keep import/export package previews summarized; never render raw save JSON, raw GameState, raw EventLog, or raw `state_deltas` in normal player UI.

## 是否阻塞 v0.8

不阻塞。

v0.8 visibility / authoring / debug data audit passed with non-blocking risks. The current implementation keeps these boundaries intact:

- Player APIs expose only player-visible state.
- Authoring APIs can show complete local content but remain separated from player/narrator surfaces.
- Debug timeline and raw `state_deltas` remain debug-only.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden faction conflicts, hidden shop inventory, hidden quest data, and hidden/debug memory do not enter narrator/player-visible contexts through reviewed v0.8 paths.
