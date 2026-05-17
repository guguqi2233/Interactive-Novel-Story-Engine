# v0.5 Roadmap

## Theme

Authoring Tools, Advanced NPCs & Local Memory

## Goal

v0.5 upgrades the project from a local narrative RPG engine prototype into a more sustainable local world-making platform: easier to author, easier to validate, easier to debug, and ready for richer NPC behavior and safer memory context.

The release should preserve the core architecture:

- LLM does not directly modify `GameState`.
- All canonical state changes go through `StateDelta`.
- All player actions, system ticks, and NPC planning ticks are recorded as `Event`.
- Hidden facts do not enter `visible_state`.
- NPCs cannot know, repeat, react to, or plan from facts outside their knowledge.
- Business code depends on `LLMProvider`, not concrete provider classes.
- Content authoring tools cannot bypass `WorldLoader` or content validation.
- Memory is not an authoritative fact source and cannot overwrite `GameState` or `EventLog`.
- Procedural quest generation can produce drafts only; it cannot directly write to a running save's canonical state.
- Plugin / mod packs are local, explicit, and validated before loading.

## Current Baseline

v0.4 has:

- Multi-world content packs.
- Structured `GameState`.
- `StateDelta`.
- `EventLog`.
- SQLite save/load.
- Structured `visible_state`.
- `facts.yaml`.
- NPC schedule resolver.
- `search`, inventory, `lockpick`, and `sneak`.
- Quest state machine.
- World tick.
- Debug timeline viewer.
- Faction reputation.
- Rumor propagation.
- Crime / witness system.
- Social consequence tick.
- Combat core.
- Life state.
- NPC reaction rules.
- Advanced memory retrieval initial version.
- Content validation tools.
- Frontend social/debug panels.
- Centralized LLM provider factory.

## Recommended v0.5 Scope

v0.5 should focus on:

1. Content Authoring API.
2. Content Authoring Frontend.
3. World Pack Editor Validation UX.
4. Local Vector Memory Backend.
5. Memory Context Builder.
6. Advanced NPC Goal System.
7. NPC Planning Tick.
8. NPC Relationship Graph.
9. Automated Narrative Boundary Evals.
10. Multi-world Save Browser.

The following candidates are useful but should be treated as limited or deferred unless the core scope finishes early:

- Faction Conflict Layer: design and minimal schema only.
- Economy / Trade initial version: design and content schema only.
- Procedural Side Quest Generator: draft-only prototype, no direct runtime mutation.
- Plugin / Mod Packaging: validation and manifest design only, no dynamic code execution.

## Explicitly Not In v0.5

v0.5 should not include:

- Cloud sync, accounts, multiplayer, or hosted auth.
- Full visual world editor with drag-and-drop maps.
- Arbitrary plugin code execution.
- LLM-authored content auto-committed to running saves.
- LLM-driven NPC autonomous planning that changes state directly.
- Large-scale simulation of economics, wars, logistics, or population dynamics.
- Tactical combat expansion beyond v0.4 combat foundations.
- Complex vector database deployment as a hard dependency.
- Full quest graph editor.
- Production security for debug APIs beyond local-only controls.

## Recommended Development Order

1. Content Authoring API.
2. Content Authoring Frontend.
3. World Pack Editor Validation UX.
4. Multi-world Save Browser.
5. Local Vector Memory Backend.
6. Memory Context Builder.
7. Automated Narrative Boundary Evals.
8. Advanced NPC Goal System.
9. NPC Relationship Graph.
10. NPC Planning Tick.
11. Faction Conflict Layer design / minimal schema.
12. Economy / Trade design / minimal schema.
13. Procedural Side Quest Generator draft prototype.
14. Plugin / Mod Packaging manifest and validation.
15. v0.5 integration tests, audits, acceptance report, and release notes.

This order improves authoring and safety before adding more autonomous NPC behavior.

## Module 1: Content Authoring API

### Goal

Expose local-only backend endpoints for reading, validating, previewing, and safely writing content pack files under `worlds/{world_id}`.

### Data Structures

- `WorldPackSummary`
  - `world_id: str`
  - `name: str`
  - `description: str`
  - `schema_version: str`
  - `files: list[WorldPackFileSummary]`
- `WorldPackFileSummary`
  - `filename: str`
  - `exists: bool`
  - `item_count: int`
  - `last_modified: str | None`
- `ContentFileReadResponse`
  - `world_id: str`
  - `filename: str`
  - `content: str`
  - `parsed_preview: dict | list | None`
- `ContentFileWriteRequest`
  - `content: str`
  - `validate_before_write: bool`
- `ContentValidationResponse`
  - `errors: list[ValidationIssue]`
  - `warnings: list[ValidationIssue]`
  - `suggestions: list[ValidationIssue]`

### Interfaces

- `backend/app/api_authoring.py`
  - `list_world_packs()`
  - `read_world_file(world_id, filename)`
  - `validate_world(world_id)`
  - `write_world_file(world_id, filename, request)`
- `backend/app/engine/content/authoring_service.py`
  - `safe_world_path(world_id) -> Path`
  - `safe_content_file_path(world_id, filename) -> Path`
  - `read_content_file(...)`
  - `write_content_file(...)`
  - `validate_content_before_commit(...)`

### Impact Files

- `backend/app/main.py`
- `backend/app/api.py` or new `backend/app/api_authoring.py`
- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/content/validator.py`
- `backend/app/engine/content/authoring_service.py`
- `backend/tests/test_authoring_api.py`
- `README.md`
- `.env.example`

### StateDelta Paths

None. Authoring edits content files, not active `GameState`.

If a future endpoint previews content as state, it must create a temporary `GameState` only and must not mutate active sessions.

### Event Types

No `EventLog` events are required because content authoring is outside a running game session.

Optional debug-only audit log:

- `content_file_saved`
- `content_pack_validated`

These must not enter player event timelines.

### API

Local-only authoring API, controlled by a new setting such as `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds`
- `GET /authoring/worlds/{world_id}/files/{filename}`
- `PUT /authoring/worlds/{world_id}/files/{filename}`
- `POST /authoring/worlds/{world_id}/validate`
- `POST /authoring/worlds/{world_id}/preview-start`

### Frontend UI

- Authoring mode tab.
- World pack selector.
- File list.
- Text/YAML editor area.
- Validate button.
- Validation result list.
- Preview start button.

### Test Requirements

- Authoring API disabled returns clear error.
- Enabled API can list worlds.
- Safe path handling rejects path traversal.
- Invalid YAML write is rejected when `validate_before_write=true`.
- Valid content write preserves file boundaries.
- Validation response matches CLI validator.

### Acceptance Standard

A local author can open `mist_valley`, edit a YAML file, validate it, and preview-load the world without bypassing `WorldLoader` or `validator`.

### Leakage Risk

Authoring API can expose hidden world content. It must be local-only and separate from player APIs and Narrator.

### LLM Boundary

No LLM calls. Any future AI-assisted authoring must produce drafts only and must still pass validation before save.

## Module 2: Content Authoring Frontend

### Goal

Provide a minimal frontend authoring surface for editing content pack YAML and viewing validation results.

### Data Structures

TypeScript mirrors:

- `WorldPackSummary`
- `WorldPackFileSummary`
- `ContentFileReadResponse`
- `ContentValidationResponse`
- `ValidationIssue`

### Interfaces

- `frontend/src/api.ts`
  - `fetchAuthoringWorlds`
  - `fetchWorldFile`
  - `saveWorldFile`
  - `validateWorld`
- `frontend/src/App.tsx`
  - authoring panel state
  - editor input state
  - validation output state

### Impact Files

- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- optional `frontend/src/types.ts`

### StateDelta Paths

None.

### Event Types

None in game `EventLog`.

### API

Consumes Module 1 authoring endpoints.

### Frontend UI

- Authoring sidebar or tab.
- World selector.
- YAML file selector.
- Editor textarea.
- Save and validate controls.
- Validation issue list grouped by error/warning/suggestion.

### Test Requirements

- `npm.cmd run build` passes.
- Authoring API disabled is handled without crashing.
- Validation results render clearly.
- No API keys are accepted, stored, or displayed.

### Acceptance Standard

The local UI can edit and validate content pack files while normal game UI remains usable.

### Leakage Risk

Authoring UI displays hidden content by design. It must be visually separated from player play mode and must not feed player narrative UI.

### LLM Boundary

No LLM calls.

## Module 3: World Pack Editor Validation UX

### Goal

Turn validation output into actionable authoring feedback with file paths, item ids, severity, and suggested fixes.

### Data Structures

- `ValidationIssue`
  - `severity: error | warning | suggestion`
  - `code: str`
  - `path: str`
  - `item_id: str | None`
  - `message: str`
  - `suggested_fix: str | None`
- `ValidationSummary`
  - `error_count: int`
  - `warning_count: int`
  - `suggestion_count: int`
  - `is_loadable: bool`

### Interfaces

- `validator.validate_world_pack(world_id) -> ValidationReport`
- `ValidationReport.to_api_response()`
- frontend grouping and filtering by severity / file / code

### Impact Files

- `backend/app/engine/content/validator.py`
- `backend/app/api_authoring.py`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `backend/tests/test_content_validation.py`

### StateDelta Paths

None.

### Event Types

None.

### API

- `POST /authoring/worlds/{world_id}/validate`

### Frontend UI

- Validation badge per file.
- Click issue to select file.
- Severity filters.
- Loadability indicator.

### Test Requirements

- Error blocks preview start.
- Warning does not block preview start.
- Issue codes are stable.
- Hidden fact leak warnings render in authoring UI only.

### Acceptance Standard

An author can identify and fix invalid references without reading backend logs.

### Leakage Risk

Validation may name hidden facts and NPC secrets. Keep validation output authoring/debug-only.

### LLM Boundary

No LLM calls.

## Module 4: Local Vector Memory Backend

### Goal

Add an optional local vector-like memory backend while preserving deterministic fallback search and avoiding external service requirements.

### Data Structures

- `MemoryBackendConfig`
  - `backend: in_memory | sqlite_fts | local_vector_stub`
  - `embedding_model: str | None`
  - `enabled: bool`
- `MemoryEmbeddingRecord`
  - `memory_id: str`
  - `embedding: list[float] | None`
  - `embedding_backend: str`
  - `created_at: str`

### Interfaces

- `backend/app/llm/memory_store.py`
  - existing deterministic methods remain
- `backend/app/llm/memory_backend.py`
  - `MemoryBackend` protocol
  - `InMemoryMemoryBackend`
  - `SQLiteFTSMemoryBackend`
  - optional `LocalVectorMemoryBackend` interface stub
- `MemoryStore.search_memory(...)` delegates to backend and visibility filters.

### Impact Files

- `backend/app/llm/memory_store.py`
- `backend/app/llm/memory_backend.py`
- `backend/app/db/models.py`
- `backend/app/db/repository.py`
- `backend/tests/test_memory_store.py`
- `backend/tests/test_memory_backend.py`
- `.env.example`
- `docs/LLM_PROTOCOL.md`

### StateDelta Paths

None. Memory is not canonical `GameState`.

### Event Types

Optional system event when memory is created from event summarization:

- `memory_record_created`

It must reference source events and must not alter `GameState`.

### API

Optional debug/local endpoints:

- `GET /debug/sessions/{session_id}/memories`
- `GET /debug/saves/{save_id}/memories`

Player APIs should not expose hidden/debug memory.

### Frontend UI

Debug panel:

- memory search input
- filter by visibility/tag/entity/fact
- memory record details

### Test Requirements

- Deterministic search still works without embeddings.
- Hidden/debug memory is filtered from narrator/player context.
- Save/load preserves memory records.
- SQLite-backed search returns stable results.
- Tests do not call external embedding APIs.

### Acceptance Standard

Memory retrieval can use local persistence and search without replacing `GameState` or leaking hidden/debug memory.

### Leakage Risk

High if hidden memories are misclassified. All retrieval paths must accept an explicit audience: `player`, `narrator`, or `debug`.

### LLM Boundary

No direct LLM authority. If embeddings are added later, they must not decide facts or mutate state.

## Module 5: Memory Context Builder

### Goal

Create a safe layer that selects relevant memory, visible facts, recent events, and NPC context for Narrator without exposing hidden/debug data.

### Data Structures

- `NarrativeContext`
  - `visible_facts: list[str]`
  - `visible_entities: list[str]`
  - `recent_player_events: list[SafeEventSummary]`
  - `memories: list[MemoryRecord]`
  - `current_location_id: str`
  - `tone: str`
- `SafeEventSummary`
  - `turn: int`
  - `action_type: str`
  - `player_safe_result: str`

### Interfaces

- `backend/app/llm/context_builder.py`
  - `build_narrator_context(state, event_log, memory_store, action_result) -> NarrativeContext`
  - `filter_memory_for_audience(memories, audience)`
  - `summarize_event_for_narrator(event) -> SafeEventSummary`

### Impact Files

- `backend/app/core/game_loop.py`
- `backend/app/llm/narrator.py`
- `backend/app/llm/prompts.py`
- `backend/app/llm/memory_store.py`
- `backend/tests/test_context_builder.py`
- `backend/tests/test_narrator.py`

### StateDelta Paths

None.

### Event Types

None.

### API

No public API required.

Debug-only endpoint may expose the built context for inspection:

- `GET /debug/sessions/{session_id}/narrator-context-preview`

This must be disabled unless debug API is enabled.

### Frontend UI

Debug panel:

- narrator context preview
- memory ids included
- redaction indicators

### Test Requirements

- Hidden facts excluded.
- NPC secrets excluded.
- Hidden/debug memories excluded.
- Raw `state_deltas` excluded.
- Hidden witness ids excluded.
- Narrator receives only `NarrativeContext`, not raw event objects.

### Acceptance Standard

Narrator prompt assembly has a single auditable context builder and no scattered ad hoc context construction.

### Leakage Risk

This is the highest-risk v0.5 module. It must be covered by regression tests and audits before enabling memory-to-narrator integration.

### LLM Boundary

The LLM receives only prefiltered context and still cannot modify `GameState`.

## Module 6: Advanced NPC Goal System

### Goal

Make NPCs goal-oriented in a structured way without free-form LLM planning.

### Data Structures

- `NPCGoalState`
  - `id: str`
  - `npc_id: str`
  - `goal_type: protect | acquire | report | travel | talk | avoid | rest | trade`
  - `target_id: str | None`
  - `priority: int`
  - `status: active | blocked | completed | abandoned`
  - `known_required_facts: list[str]`
  - `created_turn: int`
  - `source_event_id: str | None`
- NPC extension:
  - `goals: list[str]` remains content-friendly
  - runtime `goal_ids: list[str]`

### Interfaces

- `backend/app/engine/rules/npc_goals.py`
  - `create_npc_goal(...) -> list[StateDelta]`
  - `complete_npc_goal(...) -> list[StateDelta]`
  - `get_active_goals_for_npc(state, npc_id)`
  - `npc_can_pursue_goal(state, npc_id, goal)`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/rules/npc_goals.py`
- `backend/app/engine/rules/npc_reactions.py`
- `backend/tests/test_npc_goals.py`
- `worlds/mist_valley/npcs.yaml`

### StateDelta Paths

- `npc_goals.{goal_id}`
- `npcs.{npc_id}.goal_ids`
- `npc_goals.{goal_id}.status`
- `npc_goals.{goal_id}.priority`

### Event Types

- `npc_goal_created`
- `npc_goal_completed`
- `npc_goal_blocked`
- `npc_goal_abandoned`

### API

Player API should not expose hidden NPC goals.

Debug API:

- `GET /debug/sessions/{session_id}/npc-goals`

### Frontend UI

Debug panel:

- NPC goal list
- goal status
- source event
- blocked reason

### Test Requirements

- NPC cannot get a goal from unknown facts.
- Dead/incapacitated NPC cannot pursue active goals.
- Goal creation and completion go through `StateDelta`.
- Hidden goals do not enter player API.
- Save/load preserves goals.

### Acceptance Standard

NPCs can carry structured goals that later planning ticks can evaluate deterministically.

### Leakage Risk

NPC goals can reveal hidden motives. Keep player API filtered.

### LLM Boundary

No LLM planning. Goals are created by rules, reactions, content, or validated authoring drafts.

## Module 7: NPC Planning Tick

### Goal

Add a deterministic tick that lets NPCs take limited actions based on schedule, goals, relationships, knowledge, and life state.

### Data Structures

- `NPCPlanStep`
  - `npc_id: str`
  - `goal_id: str | None`
  - `plan_type: move | report | talk_to_npc | spread_rumor | rest | flee | idle`
  - `target_id: str | None`
  - `reason_code: str`
  - `visible_to_player: bool`
- `NPCPlanningResult`
  - `state_deltas: list[StateDelta]`
  - `events: list[Event]`

### Interfaces

- `backend/app/engine/rules/npc_planning.py`
  - `resolve_npc_planning_tick(state, rng) -> NPCPlanningResult`
  - `choose_plan_for_npc(state, npc_id, rng) -> NPCPlanStep`
  - `resolve_plan_step(state, step) -> list[StateDelta]`

### Impact Files

- `backend/app/engine/rules/world_tick.py`
- `backend/app/engine/rules/npc_planning.py`
- `backend/app/engine/rules/npc_goals.py`
- `backend/app/core/game_loop.py`
- `backend/tests/test_npc_planning.py`
- `backend/tests/test_world_tick.py`

### StateDelta Paths

- `npcs.{npc_id}.location_id`
- `npcs.{npc_id}.activity`
- `npcs.{npc_id}.relationship_to_player`
- `npcs.{npc_id}.knowledge`
- `npc_goals.{goal_id}.status`
- `rumors.{rumor_id}.known_by_npcs`

### Event Types

- `npc_planning_tick`
- `npc_plan_step_resolved`
- `npc_goal_progressed`

### API

Player API only reflects visible consequences in `visible_state`.

Debug API:

- timeline already shows planning events
- optional `GET /debug/sessions/{session_id}/npc-plans`

### Frontend UI

Debug timeline:

- filter by NPC planning events
- expand plan step deltas

### Test Requirements

- Tick is deterministic with fixed seed.
- Dead/incapacitated NPCs do not plan.
- NPC cannot plan from unknown facts or rumors.
- Hidden NPC planning does not enter narrator.
- Planning deltas are recorded as system events.
- Save/load preserves planning-relevant state.

### Acceptance Standard

After player actions, eligible NPCs can make limited deterministic progress toward goals without LLM authority.

### Leakage Risk

Planning reasons can reveal hidden knowledge. Player-safe narrative must not receive raw plan reasons.

### LLM Boundary

No LLM planning in v0.5. Future LLM suggestions, if any, must be drafts converted into validated rule proposals.

## Module 8: NPC Relationship Graph

### Goal

Represent relationships between NPCs, factions, and player in a structured way for reactions, rumors, planning, and social consequences.

### Data Structures

- `RelationshipEdge`
  - `id: str`
  - `source_id: str`
  - `target_id: str`
  - `relationship_type: trust | fear | loyalty | rivalry | family | debt | authority`
  - `strength: int`
  - `known_by_player: bool`
  - `known_by_npcs: list[str]`
  - `tags: list[str]`

### Interfaces

- `backend/app/engine/rules/relationships.py`
  - `get_relationship(source_id, target_id)`
  - `change_relationship(...) -> list[StateDelta]`
  - `get_visible_relationships(state)`
  - `npc_knows_relationship(state, npc_id, edge_id)`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/content/world_loader.py`
- optional `worlds/{world_id}/relationships.yaml`
- `backend/app/engine/rules/npc_reactions.py`
- `backend/app/engine/rules/npc_planning.py`
- `backend/tests/test_relationships.py`

### StateDelta Paths

- `relationships.{edge_id}`
- `relationships.{edge_id}.strength`
- `relationships.{edge_id}.known_by_player`
- `relationships.{edge_id}.known_by_npcs`

### Event Types

- `relationship_changed`
- `relationship_discovered`

### API

Extend `visible_state` only with player-known relationship summaries.

Debug API can expose raw graph.

### Frontend UI

Player UI:

- known relationships summary

Debug UI:

- relationship graph list, not a large visualization library

### Test Requirements

- Hidden relationship not visible.
- NPC cannot react to unknown relationship.
- Relationship change goes through `StateDelta`.
- Save/load preserves graph.

### Acceptance Standard

At least NPC reaction and planning rules can query structured relationships safely.

### Leakage Risk

Relationships may reveal secrets. Keep default hidden unless explicitly known.

### LLM Boundary

No LLM inference of relationships into canonical state.

## Module 9: Faction Conflict Layer

### Goal

Introduce minimal structured conflict between factions for future social simulation, without large war simulation.

### Data Structures

- `FactionConflictState`
  - `id: str`
  - `faction_a_id: str`
  - `faction_b_id: str`
  - `status: cold | tense | hostile | truce`
  - `intensity: int`
  - `known_by_player: bool`
  - `source_event_ids: list[str]`

### Interfaces

- `backend/app/engine/rules/faction_conflicts.py`
  - `get_conflict(...)`
  - `change_conflict_intensity(...) -> list[StateDelta]`
  - `get_visible_conflicts(state)`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/rules/faction_conflicts.py`
- `backend/app/engine/content/world_loader.py`
- optional `worlds/{world_id}/faction_conflicts.yaml`
- `backend/tests/test_faction_conflicts.py`

### StateDelta Paths

- `faction_conflicts.{conflict_id}`
- `faction_conflicts.{conflict_id}.status`
- `faction_conflicts.{conflict_id}.intensity`

### Event Types

- `faction_conflict_changed`

### API

Player-visible known conflicts only.

### Frontend UI

Social panel:

- known faction tensions

### Test Requirements

- Hidden conflict not visible.
- Invalid faction references fail validation.
- Conflict changes through `StateDelta`.

### Acceptance Standard

Minimal schema and query layer exist; no full war simulation.

### Leakage Risk

Faction conflicts can reveal hidden factions or motives.

### LLM Boundary

No LLM decides conflict status.

## Module 10: Economy / Trade Initial Design

### Goal

Define the first trade/economy structures without implementing a full economy.

### Data Structures

- `CurrencyState`
  - `id: str`
  - `name: str`
- `MerchantState`
  - `npc_id: str`
  - `inventory_item_ids: list[str]`
  - `price_rules: dict[str, int]`
  - `faction_id: str | None`
- `TradeOffer`
  - `seller_id: str`
  - `buyer_id: str`
  - `item_id: str`
  - `price: int`
  - `currency_id: str`

### Interfaces

- `backend/app/engine/rules/trade.py`
  - `get_trade_inventory(state, npc_id)`
  - `can_buy_item(...)`
  - `buy_item(...) -> list[StateDelta]`
  - `sell_item(...) -> list[StateDelta]`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/rules/inventory.py`
- optional `worlds/{world_id}/trade.yaml`
- `backend/tests/test_trade.py`

### StateDelta Paths

- `player.currency.{currency_id}`
- `objects.{item_id}.owner_id`
- `objects.{item_id}.location_id`
- `npcs.{npc_id}.inventory`

### Event Types

- `trade_offer_viewed`
- `item_bought`
- `item_sold`

### API

No required v0.5 player API unless implementing trade action.

### Frontend UI

Defer full shop UI. Debug or placeholder panel only if implemented.

### Test Requirements

- Buying item changes ownership through `StateDelta`.
- Hidden merchant inventory not visible.
- Reputation can affect price only through deterministic rules.

### Acceptance Standard

Design and schema are ready; implementation may be deferred.

### Leakage Risk

Merchant inventory can reveal hidden quest items.

### LLM Boundary

No LLM price decisions.

## Module 11: Procedural Side Quest Generator

### Goal

Create a draft-only workflow for generating side quest candidates for authors to review.

### Data Structures

- `QuestDraft`
  - `id: str`
  - `title: str`
  - `description: str`
  - `stages: list[QuestStageDraft]`
  - `trigger_candidates: list[QuestTrigger]`
  - `validation_status: draft | valid | invalid`
  - `source_context_ids: list[str]`
- `QuestDraftReview`
  - `approved: bool`
  - `notes: str`

### Interfaces

- `backend/app/authoring/quest_drafts.py`
  - `create_quest_draft_from_context(...)`
  - `validate_quest_draft(...)`
  - `export_draft_to_content_yaml(...)`

### Impact Files

- `backend/app/llm/provider_base.py` only if LLM-assisted drafts are enabled through existing abstraction
- `backend/app/engine/content/validator.py`
- `backend/app/authoring/quest_drafts.py`
- `backend/tests/test_quest_drafts.py`

### StateDelta Paths

None. Drafts cannot mutate active `GameState`.

### Event Types

No game events. Optional authoring audit entry only.

### API

Authoring-only:

- `POST /authoring/worlds/{world_id}/quest-drafts`
- `POST /authoring/worlds/{world_id}/quest-drafts/{draft_id}/validate`
- `POST /authoring/worlds/{world_id}/quest-drafts/{draft_id}/export`

### Frontend UI

Authoring tab:

- draft list
- validation result
- export button disabled until valid

### Test Requirements

- Draft cannot write to active save.
- Exported draft must pass validator.
- If LLM is used, output must be schema-validated and treated as draft only.
- Tests use mock provider.

### Acceptance Standard

Authors can create and validate draft quests without compromising runtime authority.

### Leakage Risk

Generator may use hidden content. Draft UI is authoring-only.

### LLM Boundary

LLM can suggest drafts only. It cannot activate quests, complete objectives, or write to `GameState`.

## Module 12: Automated Narrative Boundary Evals

### Goal

Add automated tests/evals that verify Narrator and memory context never expose hidden information.

### Data Structures

- `BoundaryEvalCase`
  - `id: str`
  - `input_context: dict`
  - `forbidden_strings: list[str]`
  - `required_strings: list[str]`
  - `audience: player | narrator | debug`
- `BoundaryEvalResult`
  - `case_id: str`
  - `passed: bool`
  - `violations: list[str]`

### Interfaces

- `backend/tests/evals/test_narrative_boundaries.py`
- optional CLI:
  - `python scripts/run_boundary_evals.py`

### Impact Files

- `backend/tests/evals/*`
- `backend/app/llm/context_builder.py`
- `backend/app/llm/narrator.py`
- `scripts/run_boundary_evals.py`

### StateDelta Paths

None.

### Event Types

None.

### API

No runtime API.

### Frontend UI

No UI required.

### Test Requirements

- Hidden fact id/text absent from narrator prompt.
- NPC secrets absent.
- Hidden witness ids absent.
- Debug `state_deltas` absent.
- Hidden/debug memory absent.
- Mock provider only.

### Acceptance Standard

Boundary evals run in CI/local pytest and fail clearly on leaks.

### Leakage Risk

Eval fixtures may contain hidden strings. They must remain test/debug-only.

### LLM Boundary

No real LLM calls in eval tests.

## Module 13: Plugin / Mod Packaging

### Goal

Define a local plugin/mod pack format for content-only extensions.

### Data Structures

- `ModManifest`
  - `id: str`
  - `name: str`
  - `version: str`
  - `target_engine_version: str`
  - `dependencies: list[str]`
  - `content_paths: list[str]`
  - `load_order: int`
- `ModValidationReport`
  - `errors`
  - `warnings`
  - `suggestions`

### Interfaces

- `backend/app/engine/content/mod_loader.py`
  - `discover_mods()`
  - `validate_mod(mod_id)`
  - `compose_world_with_mods(world_id, mod_ids)`

### Impact Files

- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/content/validator.py`
- `backend/app/engine/content/mod_loader.py`
- optional `mods/`
- `backend/tests/test_mod_loader.py`

### StateDelta Paths

None at load time. Mods define content; runtime effects still go through normal rules and deltas.

### Event Types

None.

### API

Authoring/debug-only:

- `GET /authoring/mods`
- `POST /authoring/worlds/{world_id}/validate-with-mods`

### Frontend UI

Authoring UI:

- mod list
- validation status
- load order preview

### Test Requirements

- Invalid dependency fails validation.
- Content id conflicts are reported.
- Mods cannot load arbitrary Python code.
- Composed world passes validator before start.

### Acceptance Standard

Local content-only mod packaging is designed and minimally validated.

### Leakage Risk

Mods may contain hidden content. Authoring-only surfaces may display it; player APIs must not.

### LLM Boundary

No LLM involved.

## Module 14: Multi-world Save Browser

### Goal

Improve save browsing by grouping saves by world, showing player-visible summaries, and allowing safe load/continue flows.

### Data Structures

- `SaveSummary`
  - `save_id: str`
  - `world_id: str`
  - `turn: int`
  - `location_name: str | None`
  - `formatted_time: str`
  - `created_at: str`
  - `updated_at: str`
  - `player_visible_summary: str | None`
- `SaveBrowserResponse`
  - `worlds: list[WorldSaveGroup]`

### Interfaces

- `backend/app/db/repository.py`
  - `list_saves_grouped_by_world()`
- `backend/app/main.py`
  - enrich `GET /game/saves`
- frontend save browser components

### Impact Files

- `backend/app/db/repository.py`
- `backend/app/api.py`
- `backend/app/main.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `backend/tests/test_game_api.py`

### StateDelta Paths

None.

### Event Types

None.

### API

- `GET /game/saves?group_by_world=true`
- existing `POST /game/load/{save_id}`

### Frontend UI

- Save browser grouped by world.
- Search/filter by world.
- Continue latest save button.
- Display only player-visible summaries.

### Test Requirements

- Multi-world saves list correctly.
- Hidden state not included in summaries.
- Loading save creates active session and preserves world id.
- Missing save returns clear error.

### Acceptance Standard

Local users can manage multiple worlds and saves without inspecting raw database rows.

### Leakage Risk

Save summaries must not include hidden facts, hidden witnesses, NPC secrets, or debug memory.

### LLM Boundary

No LLM calls.

## Cross-cutting Requirements

### StateDelta Discipline

Runtime modules that alter canonical state must return `StateDelta`:

- NPC goals.
- NPC planning tick.
- Relationship graph.
- Faction conflict changes.
- Economy/trade if implemented.

Authoring modules must not mutate active sessions.

### Event Discipline

Every player action, system tick, NPC planning tick, and runtime state-changing system consequence must record `Event`.

Authoring edits should not enter game `EventLog`; if needed, use a separate local authoring audit log.

### Visibility Discipline

All player-facing APIs must filter:

- hidden facts
- hidden objects
- hidden NPCs
- NPC secrets
- hidden witnesses
- hidden relationships
- hidden goals
- hidden/debug memory
- raw `state_deltas`

Debug and authoring APIs may show hidden data only when explicitly enabled and must be clearly separated.

### LLM Boundary

Allowed LLM roles:

- intent parsing
- narration from filtered context
- memory summarization with schema validation
- optional draft-only authoring suggestions

Forbidden LLM roles:

- direct `GameState` mutation
- direct `StateDelta` execution without rule validation
- deciding NPC planning outcomes
- deciding quest activation/completion in runtime
- deciding canonical relationships, faction conflict, or trade outcomes
- writing content directly into active saves

## v0.5 Integration Tests

Required integration coverage:

1. Authoring edit -> validate -> preview start.
2. Invalid content cannot start a session.
3. Multi-world save browser lists only safe summaries.
4. Memory context builder excludes hidden/debug memory.
5. NPC goal created from known event -> planning tick records event -> state changes through deltas.
6. NPC cannot plan from unknown fact/rumor.
7. Relationship graph affects reaction/planning only when known.
8. Debug authoring output never appears in player API or narrator prompt.
9. Procedural quest draft cannot mutate active save.
10. Plugin/mod validation rejects executable-code-like or path-traversal inputs.

## v0.5 Audits

Before release:

- v0.5 system acceptance report.
- v0.5 LLM boundary audit.
- v0.5 visibility / secrecy / authoring audit.
- v0.5 security / local authoring API audit.
- v0.5 release notes.
- final freeze check.

## v0.5 Final Acceptance Standard

v0.5 is accepted when:

- Backend tests pass with no real API calls.
- Frontend build passes.
- Authoring API is local-only, gated, path-safe, and validator-backed.
- Frontend authoring UI can edit and validate content without exposing hidden data to player UI.
- Memory context builder is the single audited path into Narrator context.
- Hidden/debug memory cannot enter Narrator.
- NPC goal and planning systems are deterministic and event-recorded.
- NPC planning uses only known facts, known rumors, relationships, goals, and visible/structured state.
- Multi-world save browser works with player-safe summaries.
- No runtime module bypasses `StateDelta`.
- No new concrete provider instantiation appears in business modules.
- No API key or sensitive local config is exposed.
- v0.5 audits find no release-blocking issue.

## v0.6 Candidate Direction

Possible v0.6 themes:

- Richer content studio with structured forms instead of raw YAML.
- Full quest graph editor and validation.
- Relationship/faction visualization.
- Expanded economy and trade actions.
- LLM-assisted authoring assistant with strict draft/review/export boundaries.
- More robust local memory backend with optional embeddings.
- Narrative regression suite with golden transcripts.
- Mod packaging and load-order UI.
- Scenario simulation runner for large regression playthroughs.
- Export/import tools for world packs and saves.
