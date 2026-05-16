# v0.1 Acceptance Report

## Verdict

v0.1 is accepted as a local-only minimal playable prototype.

The project now has a working backend loop, deterministic world-state boundary, schema-validated LLM abstraction, event logging, SQLite save repository, content-pack loading, visibility and NPC knowledge rules, memory summarization, and a minimal React frontend prototype.

## Verification Date

2026-05-17

## Verification Commands

Backend:

```bash
python -m pytest
```

Result:

```text
73 passed
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

### Backend API

- `GET /health`
- `POST /game/start`
- `POST /game/input`
- `GET /game/state/{session_id}`

The API uses an in-memory session store for active sessions and exposes only visible state summaries to clients.

### Core World Engine

- `GameState` is structured with player, locations, objects, NPCs, facts, time, flags, and knowledge fields.
- `StateDelta` supports `set`, `inc`, `add`, and `remove`.
- State mutation in the main loop flows through `apply_delta`.
- `Event` records full `state_deltas` for replay/debugging.
- `EventLog` supports append, list, recent, and turn-based reads.

### Game Loop

The v0.1 loop performs:

1. Receive player input.
2. Parse `PlayerIntent`.
3. Dispatch to action handler.
4. Resolve `ActionResult`.
5. Apply `StateDelta` list.
6. Render narrative.
7. Commit state and append event.
8. Return narrative and visible state.

Narration failure does not commit partial state.

### Actions

Implemented basic handlers:

- `observe`
- `move`
- `talk`
- `use_item`
- `wait`

Each action has deterministic rule checks and structured results. Actions consume game time.

### LLM Boundary

- Business modules depend on `LLMProvider`.
- `OpenAIProvider` reads API key and model from configuration/environment.
- `FakeLLMProvider` and `MockLLMProvider` support tests/local loop.
- LLM JSON outputs are validated by Pydantic schemas.
- No real API calls are used in tests.

### Visibility and Knowledge

- Hidden objects are not visible unless discovered.
- Player-visible facts and NPC knowledge are separate.
- NPC dialogue context is filtered through structured fact visibility.
- Secrets do not enter player-facing context by default.
- Narrator receives visible facts only, not hidden facts.

### Persistence

- SQLite repository exists for saves and events.
- `GameState` is stored as JSON.
- `Event` is stored as full JSON including `state_deltas`.
- Tests use temporary SQLite databases.

### Content Packs

- `WorldLoader` imports `worlds/{world_id}` YAML content.
- `mist_valley` example world is present.
- Loader validates missing fields and invalid references.
- Default game session loads from content pack rather than hardcoded engine content.

### Memory

- `MemorySummarizer` summarizes recent events through `LLMProvider.generate_json`.
- `MemorySummary` is schema-validated.
- `MemoryStore` interface and in-memory implementation exist.
- Memory is explicitly non-authoritative and does not replace `EventLog`.

### Frontend Prototype

- React + Vite + TypeScript app exists under `frontend`.
- API base URL is configured via `VITE_API_BASE_URL`.
- UI includes story body, input box, suggested actions, left info rail, and collapsible debug panel.
- Frontend does not contain API keys.

## Boundary Review

### StateDelta Boundary

Accepted with one compatibility note:

- The main loop applies state through `apply_delta`.
- Events record full `state_deltas`.
- `state_delta` remains as a deprecated compatibility field.

### LLM Authority Boundary

Accepted:

- Intent parser produces structured intent only.
- Action handlers and world rules determine outcomes.
- Narrator renders accepted outcomes only.
- Memory summarizer summarizes event history only.

### Secret/Hidden Data Boundary

Accepted for v0.1:

- API visible state excludes hidden objects.
- Narrator prompt receives safe action result data and visible facts only.
- NPC secrets are filtered by structured fact visibility.

## Known Limitations

1. `state_delta` compatibility fields still exist in `Event` and `ActionResult`; v0.2 should remove them after all callers use `state_deltas`.
2. `FactState` is not yet loaded from content pack YAML.
3. `/game/start` does not yet let clients choose `world_id`.
4. Active sessions are in memory; SQLite save/load is implemented but not wired into API session restoration.
5. Frontend displays turn but not formatted game time, inventory, or quests from backend state.
6. No live LLM integration is exercised in automated tests.
7. No NPC schedule system yet.
8. No combat, lockpick, sneak, inventory rules, quest state machine, or multi-world save browser.

## Acceptance Risks

### Low Risk

- Deprecated single-delta fields may confuse future contributors.
- API-visible state is intentionally minimal.
- Memory search is simple substring matching.

### Medium Risk

- Fact visibility is present in engine state but not yet first-class in content packs.
- SQLite persistence is not yet transaction-wrapped with the API loop.

No high-risk blocker remains for v0.1 local prototype acceptance.

## Recommended v0.2 Priorities

1. Remove deprecated single-delta fields and standardize on `state_deltas`.
2. Add `facts.yaml` to content packs and wire it to `GameState.facts`.
3. Add `world_id` selection to `/game/start`.
4. Add save/load API endpoints backed by SQLite.
5. Add typed visible-state fields for time, inventory, quests, and known facts.
6. Add NPC schedule resolver that emits `StateDelta`.
7. Add a provider selection factory for `mock` vs `openai`.
8. Add frontend save/load and world selection controls.

## Final Status

Accepted for v0.1.

The system satisfies the intended first milestone: a local, schema-validated, deterministic interactive fiction loop where the LLM is a language layer and the world engine remains the authority over state, rules, events, and persistence.
