# v1.0 Core API Contract

## Purpose

This document freezes the v1.0 local API contract for the Stable Local Studio
Edition. Its goal is to keep the frontend, save/migration tooling, content-pack
authoring, mod packaging, quality tools, and local automation stable after
v1.0.

The API remains a **local self-use API**. It is not a hosted service contract.
Any route that exposes authoring, debug, eval, playtest, performance, or quality
data must stay behind its local enable switch and must not be exposed as a
public internet API.

`docs/V1_0_ROADMAP.md` was not present at the time this contract was written.
This contract is based on the v1.0 release criteria, v0.9 acceptance report,
v0.9 release notes, current backend routes, and current frontend API client.

## Global Contract Rules

### Stability Policy

- Additive fields are allowed when they are optional or have safe defaults.
- Removing fields, renaming fields, changing method/path, changing response
  meaning, or changing local enable-gate behavior is a breaking change.
- Breaking changes after v1.0 require:
  - migration notes,
  - frontend client updates,
  - contract tests,
  - release notes,
  - and, if save/content/mod contracts are affected, migration or compatibility
    tests.

### Security And Visibility Rules

Player-facing APIs must not return:

- hidden facts,
- NPC secrets,
- hidden witnesses,
- hidden relationships,
- hidden map edges,
- hidden quests,
- hidden shop items,
- hidden/debug memory,
- raw `GameState`,
- raw `state_deltas`,
- API keys,
- raw environment variables,
- sensitive local paths.

Debug APIs may return debug data such as raw `state_deltas`, but only when
`ENABLE_DEBUG_API=true`. Debug payloads must not enter player APIs or narrator
prompts.

Authoring APIs may show hidden content to the local author, but only when
`ENABLE_AUTHORING_API=true` and only from whitelisted local content roots.

Quality/eval/playtest/benchmark APIs are local tooling APIs. Normal report
payloads must strip hidden/debug details.

### Error Policy

Stable errors:

- Missing player session: `404`.
- Missing save: `404` for load/status/delete and `400` where migration service
  returns a validation-style failure.
- Disabled authoring/debug/playtest/eval/benchmark/quality API: `403`.
- Invalid input schema: FastAPI/Pydantic `422`.
- Invalid authoring content or path: `400`.

Error messages must not include API keys, raw env values, or sensitive absolute
paths.

## API Categories

## 1. Player API

Classification: **player-facing**.

Enable switch: always available in local backend.

Visibility boundary: only `visible_state` and safe summaries. No raw
`state_deltas`, hidden facts, NPC secrets, hidden witnesses, debug memory, or
API keys.

### `GET /health`

Request schema: none.

Response schema:

```json
{
  "status": "ok"
}
```

Breaking change policy: path, method, and `status` field are frozen.

### `POST /game/start`

Request schema:

```json
{
  "world_id": "mist_valley"
}
```

`world_id` is optional. Omit it to use the default world.

Response schema: `StartGameResponse`.

```json
{
  "session_id": "string",
  "world_id": "string",
  "visible_state": "VisibleStateResponse",
  "turn": 0
}
```

Breaking change policy: route, method, `session_id`, `world_id`,
`visible_state`, and `turn` are frozen.

### `POST /game/input`

Request schema: `GameInputRequest`.

```json
{
  "session_id": "string",
  "player_input": "string"
}
```

Response schema: `GameInputResponse`.

```json
{
  "narrative_text": "string",
  "suggested_actions": ["string"],
  "visible_state": "VisibleStateResponse",
  "turn": 1
}
```

Breaking change policy: route, method, request fields, and response fields are
frozen. LLM narration cannot modify `GameState`; rules must resolve first.

### `GET /game/state/{session_id}`

Request schema: path parameter `session_id`.

Response schema: `GameStateResponse`.

```json
{
  "session_id": "string",
  "visible_state": "VisibleStateResponse",
  "turn": 1
}
```

Breaking change policy: route and response envelope are frozen. The response
must stay player-visible only.

### `GET /game/{session_id}/graphs/relationships`

Response schema: `RelationshipGraph`.

Visibility boundary: player-visible relationship graph only. Hidden NPCs and
hidden relationships are excluded.

### `GET /game/{session_id}/graphs/factions`

Response schema: `FactionGraph`.

Visibility boundary: player-visible faction graph only. Hidden factions and
hidden faction conflict are excluded.

### Save / Load / List / Delete

#### `GET /game/saves`

Query: optional `world_id`.

Response schema: `SaveListResponse`.

```json
{
  "saves": ["SaveSummaryResponse"]
}
```

Save summaries include safe fields only: `save_id`, `world_id`, `world_name`,
`turn`, `current_location_name`, `formatted_time`, timestamps,
`player_summary`, and `enabled_mods`.

#### `POST /game/{session_id}/save`

Response schema: `SaveGameResponse`.

```json
{
  "save_id": "string",
  "session_id": "string",
  "world_id": "string",
  "turn": 0
}
```

#### `POST /game/load/{save_id}`

Response schema: `LoadGameResponse`.

```json
{
  "save_id": "string",
  "session_id": "string",
  "visible_state": "VisibleStateResponse",
  "turn": 0
}
```

#### `DELETE /game/saves/{save_id}`

Response schema: `DeleteSaveResponse`.

```json
{
  "save_id": "string",
  "deleted": true
}
```

Breaking change policy: save response envelopes and safe-summary behavior are
frozen. Adding optional metadata is allowed if it does not expose hidden state.

## 2. Migration API

Classification: **local save tooling**.

Enable switch: always available locally.

Visibility boundary: safe migration metadata only. No raw save JSON, raw
`GameState`, hidden facts, or raw `state_deltas`.

### `GET /migrations`

Response schema: `MigrationListResponse`.

Frozen fields: `migrations`, migration id/source/target/description fields.

### `GET /saves/{save_id}/migration-status`

Alias: `GET /game/saves/{save_id}/migration-status`.

Response schema: `SaveMigrationStatusResponse`.

Frozen fields: `save_id`, current/target version fields, `needs_migration`,
`migration_path`, warnings/errors, and safe mod mismatch metadata.

### `POST /saves/{save_id}/migrate-dry-run`

Alias: `POST /game/saves/{save_id}/migrate-dry-run`.

Response schema: `SaveMigrationResponse`.

Contract: dry-run must not write database state.

### `POST /saves/{save_id}/migrate`

Alias: `POST /game/saves/{save_id}/migrate`.

Response schema: `SaveMigrationResponse`.

Contract: apply records migration history and backup metadata. Failure must not
destroy the original save.

## 3. Authoring API

Classification: **local-only authoring**.

Enable switch: `ENABLE_AUTHORING_API`.

Visibility boundary: may expose hidden authoring content to the local creator,
but never to player APIs or narrator prompts. Must not modify active
`GameState`.

### World List / Read / Write / Validate

Routes:

- `GET /authoring/worlds`
- `POST /authoring/worlds`
- `GET /authoring/worlds/{world_id}`
- `GET /authoring/worlds/{world_id}/files`
- `GET /authoring/worlds/{world_id}/files/{file_name}`
- `PUT /authoring/worlds/{world_id}/files/{file_name}`
- `POST /authoring/worlds/{world_id}/preview-file-change`
- `POST /authoring/worlds/{world_id}/validate-draft`
- `POST /authoring/worlds/{world_id}/impact-analysis`
- `POST /authoring/worlds/{world_id}/validate`

Request schemas:

- file write: `AuthoringFileWriteRequest`
- draft preview/validate/impact: `AuthoringDraftFileRequest`
- create world: `AuthoringCreateWorldRequest`

Response schemas:

- `AuthoringWorldListResponse`
- `AuthoringCreateWorldResponse`
- `AuthoringWorldDetailResponse`
- `AuthoringFileListResponse`
- `AuthoringFileResponse`
- `AuthoringFileWriteResponse`
- `AuthoringFilePreviewResponse`
- `AuthoringValidationResponse`

Contract:

- Only whitelisted YAML files are readable/writable.
- Path traversal is rejected.
- Preview/validate/impact do not write disk.
- Save runs validation and returns structured errors/warnings.

### Visual Editors

Routes:

- Map: `GET/POST/PUT /authoring/worlds/{world_id}/map...`
- Quest graph: `GET/POST/PUT /authoring/worlds/{world_id}/quests/graph...`
- NPC goals: `GET/POST/PUT /authoring/worlds/{world_id}/npcs/goals...`
- Social graph: `GET/POST/PUT /authoring/worlds/{world_id}/social/graph...`
- Economy: `GET/POST/PUT /authoring/worlds/{world_id}/economy...`
- Rumor/crime: `GET/POST/PUT /authoring/worlds/{world_id}/rumor-crime...`
- Validation graph: `GET/POST /authoring/worlds/{world_id}/validation-graph`

Contract:

- `preview` does not write files.
- `validate` returns structured validation output.
- `PUT` converts graph/form data to YAML and runs validation before saving.
- Visual data does not affect active sessions until a future explicit reload.

### Templates

Routes:

- `GET /authoring/templates`
- `GET /authoring/templates/{template_id}`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/templates/{template_id}/apply`
- `POST /authoring/templates/{template_id}/render`

Contract:

- Templates are local data, not scripts.
- Preview/render do not write disk.
- Apply requires explicit local authoring flow and validation.

### Import / Export

Routes:

- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`
- `GET /authoring/export/templates/{pack_id}`
- `GET /authoring/export/scenarios/{suite_id}`
- `POST /authoring/import/packages/dry-run`
- `POST /authoring/import/packages/apply`

Contract:

- Archives are local package payloads.
- Import rejects zip slip, path traversal, executables, `.env`, DB files, logs,
  and secret files.
- Package apply requires a passing dry-run and explicit confirmation.
- Save bundles may contain hidden state by design and are private backup data,
  not player-facing output.

## 4. Mod API

Classification: **local-only authoring/mod tooling**.

Enable switch: `ENABLE_AUTHORING_API`.

Routes:

- `GET /authoring/mods`
- `GET /authoring/mods/load-order`
- `GET /authoring/mods/{mod_id}`
- `POST /authoring/mods/{mod_id}/validate`

Response schemas:

- `AuthoringModListResponse`
- `AuthoringModLoadOrderResponse`
- `AuthoringModDetailResponse`
- `AuthoringModValidationResponse`

Contract:

- Mods are content-only.
- No executable entry point is allowed.
- Loader must not read outside the mod root.
- Dependency/conflict/load-order semantics are frozen for v1.0.

## 5. Debug API

Classification: **debug-only local tooling**.

Enable switch: `ENABLE_DEBUG_API`.

Visibility boundary: may return raw debug timeline/delta summaries, but never
API keys, raw env, or sensitive config. Debug data must not enter player API or
narrator prompt surfaces.

Routes:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`
- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/timeline`
- `POST /debug/saves/{save_id}/replay-dry-run`
- `GET /debug/sessions/{session_id}/graphs/relationships`
- `GET /debug/sessions/{session_id}/graphs/factions`
- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

Response schemas:

- `DebugEventListResponse`
- `TimelineReplayResponse`
- `RelationshipGraph`
- `FactionGraph`
- `DebugPerformanceRecentResponse`
- `DebugPerformanceSummaryResponse`

Breaking change policy: debug routes are local-only but still frontend-visible;
path and envelope changes require frontend and test updates.

## 6. Quality API

Classification: **local quality/eval/playtest tooling**.

Enable switches:

- quality routes: current v0.9/v1.0 candidate behavior uses local
  `ENABLE_EVAL_API`, `ENABLE_PLAYTEST_API`, `ENABLE_PERF_LOGGING`, or
  `ENABLE_DEBUG_API`.
- playtest routes: `ENABLE_PLAYTEST_API` or debug.
- scenario regression routes: `ENABLE_PLAYTEST_API`, `ENABLE_EVAL_API`, or
  debug.
- benchmark routes: `ENABLE_PERF_LOGGING` or debug.
- narrative eval routes: debug in current implementation.

Visibility boundary: normal responses must strip hidden/debug details. Quality
reports are advisory and must not modify active `GameState` or active saves.

### Quality Gate And Reports

Routes:

- `POST /quality/worlds/{world_id}/gate/run`
- `GET /quality/worlds/{world_id}/health`
- `POST /quality/worlds/{world_id}/health/run`
- `GET /quality/worlds/{world_id}/coverage`
- `POST /quality/worlds/{world_id}/coverage/run`
- `GET /quality/worlds/{world_id}/quests`
- `POST /quality/worlds/{world_id}/quests/analyze`
- `POST /quality/worlds/{world_id}/dead-ends/analyze`
- `GET /quality/worlds/{world_id}/npc-coverage`
- `POST /quality/worlds/{world_id}/npc-coverage/analyze`
- `POST /quality/worlds/{world_id}/schedules/analyze`
- `POST /quality/worlds/{world_id}/economy/analyze`
- `POST /quality/worlds/{world_id}/combat/analyze`
- `POST /quality/worlds/{world_id}/social-consequences/analyze`
- `POST /quality/worlds/{world_id}/branch-regression/run`
- `POST /quality/mods/compatibility-stress/run`

Contract:

- LLM never decides pass/fail.
- Normal payloads must not include `hidden_details_debug_only`.
- Quality APIs do not auto-fix content.

### Playtests

Routes:

- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`
- `POST /playtests/batch/run`
- `GET /playtests/batch/{run_id}`

Contract:

- Agents use game loop/test harness actions.
- Agents do not directly mutate `GameState`.
- Reports do not expose hidden text in normal views.

### Scenario Regression

Routes:

- `GET /scenarios/regression`
- `POST /scenarios/regression/run`
- `GET /scenarios/regression/{run_id}`
- `GET /authoring/scenarios`
- `GET /authoring/scenarios/{scenario_id}`
- `POST /authoring/scenarios/preview`
- `POST /authoring/scenarios/{scenario_id}/validate`
- `PUT /authoring/scenarios/{scenario_id}`

Contract:

- Execution routes use local eval/playtest gates.
- Authoring routes use authoring gate.
- Runs use temporary/session-safe flows and do not modify real saves.

### Benchmarks

Routes:

- `POST /quality/benchmarks/run`
- `GET /quality/benchmarks/recent`

Contract:

- Benchmark reports do not record API keys, prompt text, hidden facts, raw env,
  raw `GameState`, or raw `state_deltas`.

### Narrative Evals

Routes:

- `GET /evals/narrative/recent`
- `POST /evals/narrative/run`
- `GET /evals/narrative/{run_id}`

Contract:

- No external LLM judge.
- Reports do not modify `GameState`.
- Hidden fixture text is redacted in normal payloads.

## 7. Studio Status / Config Summary API

Classification: **local studio safe summary**.

Enable switch: always available locally.

Routes:

- `GET /studio/status`
- `GET /studio/config-summary`
- `GET /studio/prompt-profiles`
- `POST /studio/prompt-profiles/select`

Response schemas:

- `StudioStatusResponse`
- `StudioConfigSummaryResponse`
- `PromptProfileListResponse`

Contract:

- May show provider type/status and whether an API key is configured.
- Must not show API key value.
- Must not show raw env.
- Must not show full sensitive DB paths unless explicitly redacted.
- Prompt profiles cannot enable hidden facts, raw `GameState`, raw
  `state_deltas`, or direct state-write authority.

## Contract Test Requirements

v1.0 contract tests must cover:

- OpenAPI route presence for frozen core paths.
- Player response envelope stability.
- Player API absence of debug/raw/hidden fields.
- Authoring/debug/quality/playtest/eval disabled routes returning `403`.
- Studio status/config summaries not leaking API keys.
- Migration dry-run not mutating saves.
- Save summaries not exposing raw state.

## Known v1.0 API Risks To Track

- There is no standalone `ENABLE_QUALITY_API` yet; quality endpoints are gated
  through existing local eval/playtest/perf/debug flags.
- Narrative eval endpoints are currently debug-gated rather than
  `ENABLE_EVAL_API` only.
- `ActionResult.reason` remains narrator-visible and must stay player-safe
  until split into player/debug reason fields.
- Some player-visible faction fields still expose raw numeric reputation and
  conflict tags; these are stable in current frontend but should be reviewed
  before long-term public schema freeze.

These risks do not require large API rewrites for this contract document, but
they should be resolved or explicitly accepted before v1.0 final freeze.
