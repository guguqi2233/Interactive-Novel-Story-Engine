# v0.7 Visibility, Debug Data, and Local Privacy Audit

## Audit Date

2026-05-18

## Scope

This audit reviews v0.7 visibility and privacy boundaries across:

- Player `visible_state`
- Player graph APIs
- Debug graph and timeline APIs
- Performance debug APIs
- Narrative Quality Dashboard
- Playtesting Dashboard
- Save Migration UI / API
- Mod Manager UI / API
- Import / Export Workflow
- Settings / Local Privacy Panel
- Local model provider status
- Desktop packaging prototype
- Authoring UI and quest/template editors
- Narrator input construction

The audit is read-only. No code changes were made.

## Review Method

Reviewed relevant code paths and tests:

- `backend/app/session_store.py`
- `backend/app/engine/rules/visibility.py`
- `backend/app/engine/rules/graphs.py`
- `backend/app/engine/rules/relationships.py`
- `backend/app/engine/rules/faction_conflict.py`
- `backend/app/main.py`
- `backend/app/core/instrumentation.py`
- `backend/app/engine/content/import_export.py`
- `backend/app/llm/narrator.py`
- `backend/app/llm/context_builder.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- v0.7 regression tests and targeted privacy tests

## 已通过项目

1. **hidden facts 不进入 `visible_state`**
   - `visible_state.known_facts` is built from `state.player_visible_facts`.
   - Hidden/discoverable facts do not appear unless explicitly discovered and added to player-visible facts.
   - Playtesting invariants check hidden fact text and hidden fact visibility leaks.

2. **hidden objects 未发现前不可见**
   - `build_visible_state` uses `_object_visible_to_player`.
   - Objects must be in the current location, visible, and either not hidden or discovered by the player.

3. **discoverable facts 只有发现后进入 `known_facts`**
   - Discoverable facts are filtered by the same `player_visible_facts` authority path.
   - Search/discovery rules reveal facts through `StateDelta`; prompt text is not trusted as discovery.

4. **NPC secrets 默认不进入玩家上下文**
   - NPC state includes `secrets`, but `visible_state.visible_npcs` only exposes id, mood, relationship, and condition.
   - Dialogue context rules use NPC knowledge boundaries rather than raw secrets.

5. **hidden NPC 不进入 `visible_npcs`**
   - `build_visible_state` uses `_npc_visible_to_player`.
   - Hidden NPCs require player discovery before entering player-visible NPC lists.

6. **hidden witness 不进入 player API**
   - Crime/witness state is not exposed raw through player APIs.
   - `known_crimes` exposes only player-known/public crime summaries, not hidden witness identity.

7. **hidden relationship 不进入 player graph**
   - Player relationship graph filters to `known_by_player` relationships and requires visible actors.
   - Hidden NPCs are filtered from player graph nodes and edges.

8. **hidden faction conflict 不进入 player graph / visible state**
   - Player faction graph filters factions by known-to-player status.
   - `get_visible_faction_conflicts` only emits known factions and known target-faction relationships.

9. **debug graph 受 `ENABLE_DEBUG_API` 控制**
   - Debug graph endpoints call `require_debug_api`.
   - Player graph endpoints call non-debug graph builders and remain filtered.

10. **debug `state_deltas` 不进入 narrator**
    - Narrator receives reduced `ActionResult` payload: success level, reason, and visible facts.
    - Debug event APIs and frontend debug panels may show raw deltas, but those are separate from narrator calls.

11. **debug performance data 不包含 prompt 全文/API key**
    - `PerformanceRecorder` sanitizes tags containing sensitive terms such as `api_key`, `secret`, `sk-`, `prompt`, `game_state`, and `state_delta`.
    - Performance APIs expose timing samples and summaries, not prompts or raw state.

12. **Narrative Quality Dashboard 不显示 hidden fixture text in ordinary report path**
    - Report response contains categories, case ids, and failure reasons.
    - Known fixture text is sanitized in route response helper for the hard-coded hidden test string.

13. **Playtesting Dashboard 不显示 hidden fact 全文**
    - Playtest report response applies `_safe_report_text`.
    - Frontend additionally redacts `hidden_fact_text_visible:*` indicators before display.

14. **Migration UI 不显示 raw `GameState`**
    - Migration status/dry-run/apply responses expose versions, migration path, warnings, and history only.
    - Tests assert `state_json` and raw `state_deltas` do not appear in migration status payloads.

15. **Mod Manager 不显示本地敏感路径**
    - Mod manager responses expose manifest summaries, dependencies, conflicts, compatible worlds, and validation status.
    - It does not return local absolute paths or environment values.

16. **Import / Export 拒绝敏感 files and path traversal**
    - Archive import rejects zip slip, absolute/path traversal entries, executable code, `.env`, secrets files, DB files, and logs.
    - Tests cover path traversal, executable files, invalid manifest, and `.env`/API-key placeholder rejection.

17. **Settings / Privacy Panel 不显示 API key/raw env**
    - `/studio/config-summary` returns `api_key_configured: bool` and redacted database path hint.
    - It does not return raw env, `LLM_API_KEY`, or full sensitive path.

18. **Local provider 配置不泄露敏感信息**
    - Studio config summary returns provider name and high-level provider status.
    - It does not return API keys. `LOCAL_LLM_BASE_URL` is not returned raw.

19. **Desktop packaging 不把 `.env` 打包进前端**
    - v0.7 packaging remains launcher-script based, not a formal bundled app.
    - Documentation states `.env`, API keys, database files, and build outputs are excluded and must not be embedded.

20. **Authoring UI 与 player UI 隔离**
    - Authoring mode is separate from play mode.
    - Authoring can display full content-pack YAML for the local creator, but it does not mutate active `GameState` or feed player/narrator outputs.

21. **Narrator 无法看到 raw `state_deltas` through normal path**
    - `Narrator.render` intentionally constructs `safe_action_result` without `state_deltas` or `hidden_facts`.
    - `MemoryContextBuilder` filters hidden/debug memory before narrator-safe use.

## 可能泄露路径

1. **Authoring and import/export archives contain full content by design**
   - World/mod/save archives may include hidden authoring content or saved internal state.
   - This is expected for local archive workflows, but these archives must remain local authoring data and must not be rendered in player UI or narrator prompts.

2. **Debug timeline and debug graph expose internal data by design**
   - Debug APIs expose raw `state_deltas` and debug-only graph nodes when enabled.
   - This is acceptable for local development but must remain behind `ENABLE_DEBUG_API` and out of player/narrator surfaces.

3. **Narrative eval failure reasons can mention fixture-derived strings**
   - Current helper sanitizes a known hidden fixture string.
   - Future eval cases should avoid embedding raw hidden content in report-visible failure reasons.

4. **Playtest reports can include invariant identifiers**
   - Current reports avoid raw hidden fact text, but they may include fact ids or leak markers.
   - This is acceptable for local/debug tooling, but not player narrative.

5. **Settings provider status reveals whether a key is configured**
   - `api_key_configured` is a boolean status, not a secret.
   - For local-only use this is acceptable; it should not become a remote/public status endpoint.

6. **Debug panel in frontend renders raw `state_deltas`**
   - This is intentionally local-debug only.
   - It should remain visually and structurally separate from player story UI.

## 高风险泄露

None found.

No player API path was found that returns raw `GameState`, hidden facts, NPC secrets, hidden witness identities, hidden relationships, hidden faction conflicts, debug memory, API keys, or raw environment variables.

## 中风险泄露

1. **Import/export save archives can contain complete save internals**
   - Export save returns a base64 zip containing `state_json` and event data.
   - This is expected for local save bundle export and is gated by `ENABLE_AUTHORING_API`, but it is more sensitive than player API responses.
   - Recommendation: label save bundle responses clearly as local archive data and avoid showing archive payloads directly in UI. Consider streaming downloads instead of exposing base64 in future.

2. **Authoring UI intentionally exposes hidden content**
   - Full YAML editing means hidden facts, hidden quest text, NPC secrets, and hidden mod metadata may be visible to the local author.
   - This is correct for an authoring tool, but it is a visibility boundary risk if authoring panels are ever mixed into player mode.
   - Recommendation: keep authoring mode visually isolated and continue frontend contract tests that player UI lacks authoring/debug-only data.

3. **Debug event timeline exposes raw `state_deltas`**
   - This is necessary for local debugging but sensitive.
   - It is gated by debug API and displayed in debug panel only.
   - Recommendation: keep `ENABLE_DEBUG_API` local-only; add an obvious warning if the backend is ever bound beyond localhost.

## 小问题

1. **Player graph hidden NPC discovery behavior is conservative**
   - `visible_state` allows discovered hidden NPCs to become visible.
   - `build_relationship_graph` currently treats hidden NPCs as non-player-visible regardless of `discovered_by`.
   - This does not leak hidden data; it may under-display discovered relationships. Not a release blocker.

2. **Narrative eval sanitization is specific**
   - `_safe_report_text` redacts a known fixture string and `sk-` patterns.
   - Broader hidden fixture redaction would be safer for future eval expansion.

3. **Base64 archive responses are large and sensitive**
   - Current implementation is functional for local API tests.
   - A future download/upload file endpoint would reduce accidental UI display of archive payloads.

4. **Settings panel exposes `api_key_configured`**
   - This is intentionally a boolean and not sensitive in local context.
   - It should remain absent from any public/remote deployment mode.

## 修复建议

Recommended non-blocking follow-ups:

1. Add a generic redaction helper for narrative eval and playtest reports that can redact all configured hidden fixture strings.
2. Add frontend tests or static contracts ensuring authoring/debug panels are not rendered inside player story content.
3. Consider streaming import/export downloads/uploads instead of base64 JSON payloads.
4. Add a local-only warning banner when `ENABLE_DEBUG_API=true`, `ENABLE_AUTHORING_API=true`, or archive export APIs are available.
5. Align player graph NPC visibility with `visible_state` if discovered hidden NPC relationships should appear.
6. Add a future “safe archive summary” endpoint that reports archive metadata without exposing archive payload.

## 是否阻塞 v0.7

No.

Final visibility/debug/privacy verdict: **v0.7 visibility, debug data, and local privacy audit passed with non-blocking medium-risk notes**.

