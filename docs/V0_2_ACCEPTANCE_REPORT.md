# v0.2 Acceptance Report

## Verdict

v0.2 is accepted with minor follow-up risks.

The project now satisfies the v0.2 milestone goals: `state_deltas` is the unified mutation/event payload, content packs support `facts.yaml`, `/game/start` supports world selection, SQLite save/load is wired into FastAPI, `visible_state` is structured for frontend use, and the frontend exposes minimal world and save/load controls.

## Verification Date

2026-05-17

## Verification Commands

Backend:

```bash
python -m pytest
```

Result:

```text
88 passed
```

Frontend:

```bash
cd frontend
npm.cmd run build
```

Result:

```text
vite build completed successfully
```

## Scope Accepted

### StateDelta and Event Consistency

Accepted.

- `ActionResult` uses `state_deltas: list[StateDelta]`.
- `Event` uses `state_deltas: list[StateDelta]`.
- `GameLoop` applies each delta through `apply_delta`.
- Event persistence serializes full event JSON including `state_deltas`.
- Tests cover multiple deltas, empty-delta allowance, action outputs, game-loop event recording, memory summaries, and SQLite event round trips.

The deprecated single-delta compatibility fields noted in v0.1 have been removed from active schemas.

### facts.yaml Content Pack Support

Accepted.

- `WorldLoader` loads optional `worlds/{world_id}/facts.yaml`.
- `FactDef` validates `id`, `text`, `visibility`, `known_by`, and `tags`.
- Imported facts are written into `GameState.facts`.
- `public` facts enter `player_visible_facts`.
- `hidden` and `discoverable` facts do not enter player-visible state by default.
- `known_by` references are validated against NPC ids, with `player` allowed.
- `worlds/mist_valley/facts.yaml` is present.

Tests cover normal loading, missing `facts.yaml`, invalid `known_by`, hidden facts, public facts, and discoverable facts.

### Multi-World Start

Accepted.

- `POST /game/start` accepts optional `world_id`.
- Missing `world_id` defaults to `mist_valley`.
- Missing world packs return a clear `404`.
- Session initialization uses `WorldLoader`.
- Responses include top-level `world_id` and `visible_state.world_id`.
- Frontend has a world selector with `mist_valley`.

### SQLite Save/Load API

Accepted.

Implemented API:

- `GET /game/saves`
- `POST /game/{session_id}/save`
- `POST /game/load/{save_id}`

Accepted behavior:

- Saves include `world_id`, current turn, full `GameState` JSON, and full `Event` JSON.
- Save snapshots write state and events in one SQLite transaction.
- Loading a save creates a restored active session with restored event log.
- Continued play after load increments turn correctly.
- Missing saves return clear `404` errors.
- Save/list/load responses do not return hidden facts or full hidden state JSON.

### visible_state API Contract

Accepted.

`visible_state` now exposes structured, player-visible data:

- `world_id`
- `turn`
- `time`
- `location`
- `inventory`
- `visible_objects`
- `visible_npcs`
- `known_facts`
- `quests`

Backend generates formatted game time via the time rule module. Hidden facts, hidden objects, and NPC secrets are not included in `visible_state`. Quest output is intentionally a placeholder list and does not implement a quest state machine.

### Provider Factory

Accepted.

- `InMemorySessionStore` uses the centralized provider factory by default and still accepts an injectable `ProviderFactory` for tests.
- Tests and local sessions can run with mock/fake providers without touching business logic.
- `OpenAIProvider` remains behind the `LLMProvider` abstraction and reads key/model from configuration.
- No API keys are hardcoded.
- `create_llm_provider(settings)` selects `mock` or `openai` from `LLM_PROVIDER`.
- Missing OpenAI credentials and unknown provider values fail clearly.

### Frontend World and Save/Load Controls

Accepted.

- Frontend can select `mist_valley` before starting.
- Frontend can save the current active session.
- Frontend can list saves and load a selected save.
- Frontend displays structured visible state fields: time, location, inventory, quests, visible objects, visible NPCs, and known facts.
- API base URL remains environment-configured through `VITE_API_BASE_URL`.
- No API keys are present in frontend code.

## Boundary Review

### LLM Authority Boundary

Accepted.

- Intent parsing remains read/parse only.
- Action handlers produce rule-based `ActionResult` and `state_deltas`.
- `GameLoop` applies deltas through world-state logic.
- Narrator renders accepted results and does not mutate state.
- Save/load does not involve LLM calls.

### Hidden Information Boundary

Accepted.

- `visible_state` is built from filtered player-visible fields.
- Hidden facts and hidden objects do not appear in API-visible state.
- NPC secrets are not exposed in visible NPC summaries.
- Save list and load responses do not expose raw `GameState` JSON.

### Content/Engine Separation

Accepted.

- World content is loaded from `worlds/{world_id}`.
- `facts.yaml` joins manifest, locations, NPCs, items, and quests as content-pack data.
- Engine code does not hardcode specific world facts.

## Known Limitations

1. Save files are stored locally in one SQLite database; there is no save naming UI, overwrite UI, or delete endpoint.
2. `quests` in `visible_state` is an empty placeholder; no quest state machine exists yet.
3. Inventory is exposed but item pickup/use inventory rules are still minimal.
4. Active sessions are still in memory; SQLite restores sessions only when explicitly loaded.
5. Frontend save/load controls are minimal and not yet polished for large save lists.
6. `visible_state` object/NPC summaries currently expose ids and basic NPC mood/relationship only.
7. The FastAPI app version still reports `0.1.0`; update app metadata when preparing a formal v0.2 tag.

## Acceptance Risks

### Low Risk

- Structured `visible_state` is intentionally minimal and may need additive fields.
- Save/load API creates a new session on load rather than replacing an existing session.
- Frontend labels and layouts are functional but sparse.

### Medium Risk

- SQLite repository has transaction support for snapshots, but the active session and save repository are still composed manually in app state.

No high-risk blocker remains for v0.2 acceptance.

## Recommended v0.3 Priorities

1. Add save metadata such as user-facing name, created world, last location, and optional overwrite/delete APIs.
2. Add quest state to `GameState` and expose only player-visible quest summaries.
3. Add inventory actions and object acquisition rules through `StateDelta`.
4. Add provider integration smoke tests that do not call real APIs.
5. Add API version metadata update to `0.2.0` or next release tag.
6. Expand frontend save/load UX for multiple saves.

## Final Status

Accepted for v0.2.

The system is still a local-first prototype, but the v0.2 changes materially strengthen the project architecture: content facts are data-driven, state mutation is delta-list based, saves are restorable through API, the frontend receives a stable visible-state contract, and the LLM remains outside the authority path for world state.

## v0.2.1 Patch Notes

### Provider Factory专项验收

验收日期：2026-05-17

验收结论：通过。

检查结果：

1. `LLM_PROVIDER` 已成为生产路径 provider 选择的唯一配置入口。
   - `Settings.llm_provider` 从环境变量 `LLM_PROVIDER` 读取，默认值为 `mock`。
   - `create_llm_provider(settings)` 根据 `LLM_PROVIDER` 选择 `mock` 或 `openai`。
   - `InMemorySessionStore` 默认使用 `create_llm_provider`，不再直接绑定具体 provider 类。

2. 业务模块只依赖 `LLMProvider` 抽象。
   - `IntentParser`、`Narrator`、`MemorySummarizer` 继续通过构造参数接收 `LLMProvider`。
   - `backend/app` 中具体 provider 的实例化仅存在于 `backend/app/llm/provider_factory.py`。
   - 测试代码仍可使用 `FakeLLMProvider` 作为受控测试替身。

3. 测试不会调用真实 API。
   - provider factory 测试只构造 `OpenAIProvider`，不调用 `generate_text` 或 `generate_json`。
   - OpenAI SDK client 仍为懒加载，构造 provider 不会发起网络请求。

4. `LLM_PROVIDER=openai` 且缺少 API key 时会清晰失败。
   - 缺少 `LLM_API_KEY` 时抛出 `LLMProviderError`。
   - 错误信息包含 `LLM_API_KEY is required`。

5. `.env.example` 和文档已同步。
   - `.env.example` 标注 `LLM_PROVIDER` 支持 `mock`、`openai`，默认保留 `mock`。
   - `docs/LLM_PROTOCOL.md` 记录集中式 factory、支持的 provider、缺失凭据和未知 provider 的错误边界。

6. 测试通过。

```bash
python -m pytest
```

结果：

```text
92 passed
```

残留说明：

- `backend/app` 中没有业务模块直接实例化 `OpenAIProvider`、`MockLLMProvider` 或 `FakeLLMProvider`。
- `backend/app/llm/provider_factory.py` 是唯一允许创建生产 provider 的位置。
- 测试中直接使用 `FakeLLMProvider` 和构造 `OpenAIProvider` 属于测试替身和构造验证，不进入业务运行路径。
