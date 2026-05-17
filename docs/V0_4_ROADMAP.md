# v0.4 Roadmap

## Theme

Social Consequences & Conflict Systems

## Goal

v0.4 upgrades the project from a trustworthy small-world interactive novel engine into an early narrative RPG engine with social consequences, faction reactions, rumor spread, crime witnesses, conflict resolution, and better memory retrieval.

The release must preserve the architecture established through v0.3:

- The LLM does not directly modify `GameState`.
- All canonical state changes go through `StateDelta`.
- All player actions, combat turns, crimes, rumor ticks, faction changes, and system ticks are recorded as `Event`.
- Hidden facts do not enter `visible_state`.
- NPCs cannot know, repeat, accuse, or react to facts outside their knowledge or observation context.
- Business code depends on `LLMProvider`, not concrete provider classes.
- Combat, crime, rumor, faction, and social consequence results are decided by deterministic rules, not by LLM output.
- Debug APIs remain local development surfaces and are never passed to Narrator.

## Current Baseline

v0.3 has:

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
- Centralized LLM provider factory.
- React frontend prototype.

## Explicitly Not In v0.4

v0.4 should stay focused. It should not include:

- Full tactical grid combat.
- Pathfinding or spatial simulation.
- Economy, shops, barter, or item pricing.
- Crafting or equipment progression.
- Complex social graph inference.
- Romance, persuasion mini-games, or relationship dialogue trees.
- Multi-agent LLM planning.
- LLM-generated crimes, rumors, factions, quests, or combat outcomes.
- Cloud sync, accounts, or multiplayer.
- Full world editor UI.
- Vector database deployment as a hard dependency.
- Production authentication for debug endpoints beyond clear local-only controls.
- Frontend visual redesign beyond necessary social/debug panels.

## Recommended Development Order

1. Content authoring validation tools.
2. Faction reputation.
3. Crime and witness system.
4. Rumor propagation.
5. NPC reaction rules.
6. Social consequence tick.
7. Combat system initial version.
8. Injury, death, and incapacitation rules.
9. Advanced memory retrieval.
10. Frontend social/debug panels.
11. v0.4 integration tests and acceptance report.

This order builds validation and deterministic social state before adding autonomous consequences and combat.

## Module 1: Content Authoring Validation Tools

### Goal

Add a validation layer for content packs so authors can safely define factions, crimes, rumors, combat-related objects, and NPC reaction metadata without silently creating invalid world state.

### Data Structures

Content pack schema additions:

- `factions.yaml`
  - `id: str`
  - `name: str`
  - `description: str`
  - `initial_reputation: int`
  - `known_to_player: bool`
  - `tags: list[str]`
- optional fields in `npcs.yaml`
  - `faction_id: str | None`
  - `witness_traits: list[str]`
  - `reaction_profile: str | None`
- optional fields in `locations.yaml`
  - `jurisdiction_faction_id: str | None`
  - `crime_visibility: public | private | guarded`
- optional fields in `items.yaml`
  - `weapon: bool`
  - `damage: int`
  - `illegal_tags: list[str]`

### Interfaces

- `backend/app/engine/content/validator.py`
  - `validate_world_pack(pack) -> list[ValidationIssue]`
  - `validate_references(pack) -> list[ValidationIssue]`
  - `validate_visibility_boundaries(pack) -> list[ValidationIssue]`
- `ValidationIssue`
  - `severity: error | warning`
  - `path: str`
  - `message: str`

### Impact Files

- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/content/validator.py`
- `backend/app/core/world_state.py`
- `worlds/mist_valley/*`
- `backend/tests/test_world_loader.py`
- `backend/tests/test_content_validation.py`

### StateDelta Paths

No runtime deltas are required for validation. Validation runs before `GameState` is created.

### Event Types

No runtime events are required. Optional debug-only validation reports should not enter `EventLog`.

### API

Optional local debug endpoint:

- `GET /debug/worlds/{world_id}/validation`

This endpoint is local-only and controlled by `ENABLE_DEBUG_API`.

### Frontend UI

Optional debug panel section:

- world validation summary
- error/warning count
- issue path and message

### Test Requirements

- Missing faction reference fails validation.
- NPC faction reference must exist.
- Location jurisdiction reference must exist.
- Weapon item with invalid damage fails validation.
- Hidden quest/fact text warnings can be emitted when authoring metadata suggests a leak.
- Existing `mist_valley` loads cleanly.

### Acceptance Standard

Invalid content pack references fail early with clear errors before a game session starts.

### Leakage Risk

Validation output may mention hidden ids or internal content paths. It must stay debug-only and must not appear in player API responses or narrator prompts.

### LLM Boundary

Validation is deterministic and does not call LLM.

## Module 2: Faction Reputation

### Goal

Add structured faction reputation so player actions can affect how groups react over time.

### Data Structures

Runtime state:

- `FactionState`
  - `id: str`
  - `name: str`
  - `reputation: int`
  - `known_to_player: bool`
  - `tags: list[str]`
  - `recent_changes: list[ReputationChange]`
- `ReputationChange`
  - `event_id: str`
  - `amount: int`
  - `reason: str`
  - `turn: int`

Content:

- `factions.yaml`
- NPC `faction_id`
- location `jurisdiction_faction_id`

### Interfaces

- `backend/app/engine/rules/factions.py`
  - `get_faction(state, faction_id) -> FactionState`
  - `change_reputation(state, faction_id, amount, reason, event_id) -> list[StateDelta]`
  - `get_visible_factions(state) -> list[VisibleFactionResponse]`
  - `get_faction_reaction_band(reputation) -> hostile | wary | neutral | friendly | allied`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/content/world_loader.py`
- `backend/app/engine/rules/factions.py`
- `backend/app/session_store.py`
- `backend/app/api.py`
- `worlds/mist_valley/factions.yaml`
- `backend/tests/test_factions.py`
- `backend/tests/test_game_api.py`

### StateDelta Paths

- `factions.{faction_id}.reputation`
- `factions.{faction_id}.known_to_player`
- `factions.{faction_id}.recent_changes`

### Event Types

- `faction_reputation_changed`
- `faction_discovered`
- `faction_reaction_updated`

### API

Extend `visible_state`:

- `factions: list[VisibleFactionResponse]`

Debug API may include raw reputation change history.

### Frontend UI

Left or right panel:

- known factions
- reputation band
- latest visible change reason

### Test Requirements

- Reputation changes only through `StateDelta`.
- Unknown factions do not enter `visible_state`.
- Known faction summaries are player-safe.
- Save/load preserves reputation and recent changes.
- EventLog records reputation changes.

### Acceptance Standard

At least one player action or system consequence can deterministically change faction reputation and show a filtered summary in `visible_state`.

### Leakage Risk

Internal reasons may reveal hidden witnesses, crimes, or faction motives. Player-visible change reasons must be sanitized or separately authored.

### LLM Boundary

LLM may render reputation changes after rules resolve them, but it cannot decide reputation deltas.

## Module 3: Crime and Witness System

### Goal

Track criminal acts, witnesses, accusations, and whether factions or NPCs become aware of a crime.

### Data Structures

- `CrimeState`
  - `id: str`
  - `crime_type: theft | assault | murder | trespass | lockpicking | illegal_item | custom`
  - `actor_id: str`
  - `target_id: str | None`
  - `location_id: str`
  - `turn: int`
  - `witness_ids: list[str]`
  - `reported_to_factions: list[str]`
  - `known_to_player: bool`
  - `status: hidden | witnessed | reported | resolved`
- `WitnessObservation`
  - `npc_id: str`
  - `confidence: int`
  - `reported: bool`
  - `fact_id: str`

### Interfaces

- `backend/app/engine/rules/crime.py`
  - `classify_crime(action_result, state) -> CrimeDraft | None`
  - `find_witnesses(state, location_id, actor_id) -> list[WitnessObservation]`
  - `record_crime(state, crime_draft) -> list[StateDelta]`
  - `report_crime(state, crime_id, faction_id) -> list[StateDelta]`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/core/game_loop.py`
- `backend/app/engine/rules/crime.py`
- `backend/app/engine/rules/visibility.py`
- `backend/app/engine/rules/world_tick.py`
- `backend/app/engine/actions/lockpick.py`
- `backend/app/engine/actions/sneak.py`
- `backend/tests/test_crime.py`
- `backend/tests/test_world_tick.py`

### StateDelta Paths

- `crimes.{crime_id}`
- `crimes.{crime_id}.status`
- `crimes.{crime_id}.witness_ids`
- `crimes.{crime_id}.reported_to_factions`
- `npcs.{npc_id}.knowledge`
- `facts.{fact_id}`
- `player_visible_facts`

### Event Types

- `crime_committed`
- `crime_witnessed`
- `crime_reported`
- `crime_resolved`

### API

Player API should not expose all crimes. Extend `visible_state` only with player-known consequences:

- `known_crimes: list[VisibleCrimeSummary]`

Debug API can expose full crime records.

### Frontend UI

Social/debug panel:

- known accusations or wanted status
- debug-only crime timeline with witnesses and reports

### Test Requirements

- Unwitnessed crime does not become public.
- Visible NPC in same location can witness a crime.
- Hidden NPC can influence rules without being named to player.
- Witness knowledge is added through `StateDelta`.
- Reporting crime can change faction reputation.
- Save/load preserves crimes and witness state.

### Acceptance Standard

A lockpicking/theft/assault-like act can create a structured crime, attach witnesses, and later produce a faction consequence without exposing hidden witnesses to player-facing outputs.

### Leakage Risk

Witness ids and hidden observer identity are sensitive. They may appear in debug events, but not in `visible_state`, narrator prompts, or player-facing reason strings unless discovered.

### LLM Boundary

LLM does not classify crimes, choose witnesses, or decide reports.

## Module 4: Rumor Propagation

### Goal

Let known facts, witnessed crimes, and social events spread between NPCs and factions through deterministic rules.

### Data Structures

- `RumorState`
  - `id: str`
  - `fact_id: str`
  - `source_event_id: str`
  - `known_by: list[str]`
  - `credibility: int`
  - `status: active | stale | disproven`
  - `tags: list[str]`
- NPC additions:
  - `gossip_tendency: int`
  - `trusted_factions: list[str]`

### Interfaces

- `backend/app/engine/rules/rumors.py`
  - `create_rumor_from_fact(state, fact_id, source_event_id) -> list[StateDelta]`
  - `spread_rumors(state, rng) -> list[StateDelta]`
  - `npc_can_share_rumor(state, npc_id, rumor_id) -> bool`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/rules/rumors.py`
- `backend/app/engine/rules/world_tick.py`
- `backend/app/engine/rules/knowledge.py`
- `backend/app/session_store.py`
- `backend/tests/test_rumors.py`
- `backend/tests/test_world_tick.py`

### StateDelta Paths

- `rumors.{rumor_id}`
- `rumors.{rumor_id}.known_by`
- `rumors.{rumor_id}.credibility`
- `rumors.{rumor_id}.status`
- `npcs.{npc_id}.knowledge`

### Event Types

- `rumor_created`
- `rumor_spread`
- `rumor_staled`
- `rumor_disproven`

### API

Extend `visible_state` only for rumors the player knows:

- `known_rumors: list[VisibleRumorSummary]`

Debug API may show full propagation graph.

### Frontend UI

Social panel:

- known rumors
- credibility band
- source if player-visible

Debug panel:

- propagation events and NPC knowledge changes

### Test Requirements

- Rumor spreads only between eligible NPCs.
- NPCs do not share rumors they do not know.
- Hidden facts do not become player-visible merely because rumor exists.
- Rumor can add NPC knowledge via `StateDelta`.
- Rumor spread is deterministic with fixed seed.
- Save/load preserves rumor state.

### Acceptance Standard

A witnessed or public fact can become a structured rumor and spread to at least one NPC without directly exposing hidden facts to the player.

### Leakage Risk

Rumor text may encode hidden fact content. Player-visible rumor summaries must only include rumors known to the player and safe text derived from public/discovered facts.

### LLM Boundary

LLM may render a known rumor after rules decide it exists. LLM does not create or spread rumors.

## Module 5: NPC Reaction Rules

### Goal

Let NPCs react to reputation, crimes, rumors, injuries, and known facts using deterministic profiles.

### Data Structures

- `ReactionProfile`
  - `id: str`
  - `hostility_threshold: int`
  - `fear_threshold: int`
  - `report_crime_threshold: int`
  - `help_player_threshold: int`
- NPC additions:
  - `reaction_profile: str`
  - `attitude_to_player: hostile | wary | neutral | friendly`

### Interfaces

- `backend/app/engine/rules/reactions.py`
  - `evaluate_npc_reaction(state, npc_id) -> list[StateDelta]`
  - `evaluate_all_reactions(state) -> list[StateDelta]`
  - `reaction_visible_to_player(state, npc_id, reaction) -> bool`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/rules/reactions.py`
- `backend/app/engine/rules/world_tick.py`
- `backend/app/engine/content/world_loader.py`
- `worlds/mist_valley/npcs.yaml`
- `backend/tests/test_reactions.py`

### StateDelta Paths

- `npcs.{npc_id}.mood`
- `npcs.{npc_id}.relationship_to_player`
- `npcs.{npc_id}.suspicion`
- `npcs.{npc_id}.alertness`
- `npcs.{npc_id}.goals`

### Event Types

- `npc_reaction_changed`
- `npc_became_hostile`
- `npc_reported_player`
- `npc_helped_player`

### API

Visible NPC summaries may include:

- `mood`
- `relationship_to_player`
- player-visible reaction band

Debug API may include raw reaction triggers.

### Frontend UI

Visible NPC panel:

- mood
- relationship
- alert/hostile band if visible

Debug timeline:

- reaction events

### Test Requirements

- NPC does not react to unknown crime/fact.
- NPC reacts after learning rumor/crime fact.
- Reaction changes through `StateDelta`.
- Hidden NPC reaction does not reveal identity.
- Reaction event is recorded.

### Acceptance Standard

At least one NPC can become wary/hostile/friendly from structured social state without LLM deciding the reaction.

### Leakage Risk

Reaction reasons can reveal hidden rumors or crimes. Store debug reasons separately from narrator-safe facts.

### LLM Boundary

LLM may render visible mood, but cannot decide reaction state.

## Module 6: Social Consequence Tick

### Goal

Extend world tick to process social systems after player actions: reputation updates, witness reports, rumor spread, and NPC reactions.

### Data Structures

- `SocialTickResult`
  - `state_deltas: list[StateDelta]`
  - `events: list[Event]`
  - `player_visible_fact_ids: list[str]`

### Interfaces

- `backend/app/engine/rules/social_tick.py`
  - `run_social_consequence_tick(state, rng) -> SocialTickResult`
- Called by existing world tick after schedule and quest triggers.

### Impact Files

- `backend/app/engine/rules/world_tick.py`
- `backend/app/engine/rules/social_tick.py`
- `backend/app/core/game_loop.py`
- `backend/tests/test_social_tick.py`
- `backend/tests/test_v04_integration_regression.py`

### StateDelta Paths

Can include:

- `crimes.*`
- `rumors.*`
- `factions.*`
- `npcs.*.knowledge`
- `npcs.*.mood`
- `npcs.*.relationship_to_player`
- `player_visible_facts`

### Event Types

- `social_tick`
- `crime_reported`
- `rumor_spread`
- `faction_reputation_changed`
- `npc_reaction_changed`

### API

No new player endpoint required. Results surface through `visible_state`.

Debug API should show social tick events.

### Frontend UI

Debug timeline:

- group social tick events
- expandable deltas

Social panel:

- updated factions, rumors, known accusations

### Test Requirements

- Tick is deterministic with fixed seed.
- Tick applies deltas through `StateDelta`.
- Tick events are appended in stable order.
- Hidden social events do not enter narrator.
- Save/load preserves tick-produced state.

### Acceptance Standard

After a qualifying player action, the social tick can deterministically propagate at least one consequence and record it as a system event.

### Leakage Risk

Social tick can produce hidden consequences. Only explicitly player-visible facts should enter `visible_state`; debug events remain local-only.

### LLM Boundary

No LLM calls.

## Module 7: Combat System Initial Version

### Goal

Add minimal deterministic conflict resolution for attacks between actors.

### Data Structures

- `CombatantState`
  - `actor_id: str`
  - `health: int`
  - `stamina: int`
  - `status_effects: list[str]`
  - `hostile_to: list[str]`
- Actor additions:
  - `health: int`
  - `max_health: int`
  - `combat_skill: int`
  - `defense: int`

### Interfaces

- `AttackActionHandler`
- `backend/app/engine/rules/combat.py`
  - `can_attack(state, attacker_id, target_id) -> RuleResult`
  - `resolve_attack(state, attacker_id, target_id, rng) -> ActionResult`
  - `calculate_damage(attacker, defender, weapon, rng) -> int`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/llm/schemas.py`
- `backend/app/engine/actions/attack.py`
- `backend/app/engine/action_dispatcher.py`
- `backend/app/engine/rules/combat.py`
- `backend/app/engine/rules/crime.py`
- `backend/tests/test_combat.py`

### StateDelta Paths

- `player.health`
- `player.status_effects`
- `npcs.{npc_id}.health`
- `npcs.{npc_id}.status_effects`
- `npcs.{npc_id}.hostile_to`
- `facts.{fact_id}`
- `crimes.{crime_id}`

### Event Types

- `attack`
- `combat_started`
- `combat_damage`
- `combat_missed`
- `combat_ended`

### API

Extend `visible_state`:

- player health/status
- visible NPC health band, not exact hidden internals unless intended

### Frontend UI

Left panel:

- player health and status

Visible NPC panel:

- health band
- hostile marker

Suggested actions can include attack/flee only when visible and valid.

### Test Requirements

- Cannot attack missing or invisible target.
- Attack consumes time and records Event.
- Damage applies through `StateDelta`.
- Assault can create crime if witnessed or in faction jurisdiction.
- Hidden target identity is not revealed.
- Deterministic fixed-seed outcomes.

### Acceptance Standard

Player can attack a visible NPC, produce deterministic damage, create appropriate events, and preserve state through save/load.

### Leakage Risk

Combat reasons must not reveal hidden observers, hidden faction consequences, or exact NPC stats unless visible.

### LLM Boundary

LLM may render combat outcome after rules resolve it. It does not decide hit/miss/damage.

## Module 8: Injury, Death, and Incapacitation

### Goal

Add clear actor life-state rules so combat and consequences can produce injuries without ambiguous prose.

### Data Structures

- `ActorLifeState`
  - `condition: healthy | injured | incapacitated | dead`
  - `injuries: list[InjuryState]`
- `InjuryState`
  - `id: str`
  - `type: wound | bruise | broken_bone | fatigue | custom`
  - `severity: minor | moderate | severe`
  - `created_turn: int`

### Interfaces

- `backend/app/engine/rules/injury.py`
  - `apply_damage(state, actor_id, amount, damage_type) -> list[StateDelta]`
  - `evaluate_life_state(state, actor_id) -> list[StateDelta]`
  - `actor_can_act(state, actor_id) -> bool`

### Impact Files

- `backend/app/core/world_state.py`
- `backend/app/engine/rules/injury.py`
- `backend/app/engine/rules/combat.py`
- `backend/app/engine/rules/world_tick.py`
- `backend/tests/test_injury.py`

### StateDelta Paths

- `player.health`
- `player.condition`
- `player.injuries`
- `npcs.{npc_id}.health`
- `npcs.{npc_id}.condition`
- `npcs.{npc_id}.injuries`

### Event Types

- `injury_applied`
- `actor_incapacitated`
- `actor_died`
- `injury_recovered`

### API

Player condition enters `visible_state`.

Visible NPC condition may be shown as a band:

- healthy
- hurt
- down
- dead

### Frontend UI

Status display:

- player condition
- visible injuries
- visible NPC condition band

### Test Requirements

- Damage can injure an actor.
- Severe damage can incapacitate.
- Death is explicit and irreversible unless later rules add resurrection.
- Incapacitated actor cannot perform normal actions.
- State persists through save/load.

### Acceptance Standard

Combat damage produces structured health and condition changes, not only narrative text.

### Leakage Risk

Exact NPC health may be hidden. Player API should show only visible bands unless full detail is intended.

### LLM Boundary

No LLM calls.

## Module 9: Advanced Memory Retrieval

### Goal

Improve memory retrieval so summaries and event memories can be searched by actor, fact, location, tags, and recency without replacing structured state.

### Data Structures

- `MemoryRecord`
  - `id: str`
  - `summary: str`
  - `event_ids: list[str]`
  - `actor_ids: list[str]`
  - `fact_ids: list[str]`
  - `location_ids: list[str]`
  - `tags: list[str]`
  - `created_turn: int`
  - `visibility: internal | player_visible`

### Interfaces

- `backend/app/llm/memory_store.py`
  - `add_memory(memory) -> None`
  - `search_memory(query: MemoryQuery) -> list[MemoryRecord]`
  - `list_recent_memories(limit) -> list[MemoryRecord]`
- `MemoryQuery`
  - `actor_ids`
  - `fact_ids`
  - `location_ids`
  - `tags`
  - `limit`

### Impact Files

- `backend/app/llm/memory_store.py`
- `backend/app/llm/memory_summarizer.py`
- `backend/app/db/models.py`
- `backend/app/db/repository.py`
- `backend/tests/test_memory_store.py`
- `backend/tests/test_memory_summarizer.py`

### StateDelta Paths

None. Memory does not modify canonical `GameState`.

### Event Types

- optional `memory_summary_created`

This event must not be treated as a canonical state change unless paired with explicit deltas.

### API

No player API in v0.4 by default.

Optional debug-only endpoint:

- `GET /debug/sessions/{session_id}/memories`

### Frontend UI

Debug panel:

- recent memories
- search/filter by actor/location/tag

### Test Requirements

- Memory search by tag.
- Memory search by actor.
- Memory search by location.
- Memory summaries do not mutate `GameState`.
- Hidden/internal memories do not enter player API.

### Acceptance Standard

The engine can retrieve relevant internal memories for future LLM context without promoting memory text into authoritative facts.

### Leakage Risk

Memory records may contain event deltas or hidden facts. They must be classified internal unless explicitly filtered.

### LLM Boundary

`MemorySummarizer` may use LLM through `LLMProvider` with schema validation. Retrieval and storage do not grant LLM write access to `GameState`.

## Module 10: Frontend Social and Debug Panels

### Goal

Expose v0.4 player-visible social state and local-only debug details in separate UI zones.

### Data Structures

Frontend types:

- `VisibleFaction`
- `VisibleRumor`
- `VisibleCrimeSummary`
- `VisibleActorCondition`
- `DebugSocialEvent`

### Interfaces

- Update `frontend/src/api.ts` to match additive `visible_state` fields.
- Add debug API client functions if needed:
  - validation issues
  - social tick events
  - memory records

### Impact Files

- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- backend API schemas

### StateDelta Paths

No frontend-owned deltas. Frontend displays backend state only.

### Event Types

Frontend displays existing events:

- faction
- crime
- rumor
- reaction
- combat
- injury

### API

Player-facing:

- existing `/game/start`
- existing `/game/input`
- existing `/game/state/{session_id}`

Debug-only:

- existing debug timeline
- optional validation/memory endpoints

### Frontend UI

Player-visible panels:

- factions
- known rumors
- known accusations/wanted state
- player condition
- visible NPC condition/reaction band

Debug-only panel:

- social tick timeline
- crime/witness details
- raw deltas
- validation issues
- memory records

### Test Requirements

- TypeScript build passes.
- Player panels render only `visible_state` data.
- Debug panel remains visually separate.
- No API key or environment values displayed.
- Hidden debug data is not copied into story text.

### Acceptance Standard

Frontend can show social state and debug details without mixing debug data into player narrative.

### Leakage Risk

Debug panel can expose raw deltas. It must stay local-only and should default closed if v0.4 introduces more sensitive social state.

### LLM Boundary

Frontend does not call LLM directly.

## Cross-Cutting API Additions

Prefer additive API changes to keep v0.3 clients functional.

Potential `visible_state` additions:

- `factions`
- `known_rumors`
- `known_crimes`
- `player_condition`
- `visible_npcs[].relationship`
- `visible_npcs[].condition_band`
- `visible_npcs[].reaction_band`

Potential debug additions:

- `GET /debug/worlds/{world_id}/validation`
- `GET /debug/sessions/{session_id}/social`
- `GET /debug/sessions/{session_id}/memories`

All debug APIs must:

- be controlled by `ENABLE_DEBUG_API`
- never return API keys or environment values
- never be used by Narrator
- be documented as local-only

## Cross-Cutting Event Types

v0.4 should standardize these `action_type` values:

- `faction_reputation_changed`
- `crime_committed`
- `crime_witnessed`
- `crime_reported`
- `rumor_created`
- `rumor_spread`
- `npc_reaction_changed`
- `social_tick`
- `attack`
- `combat_started`
- `combat_damage`
- `combat_ended`
- `injury_applied`
- `actor_incapacitated`
- `actor_died`
- `memory_summary_created`

Every event must include `state_deltas` unless explicitly marked `allow_empty_delta=True`.

## Hidden Facts, NPC Secrets, and Debug Leakage Review

High-risk paths to guard:

- `ActionResult.reason` entering Narrator.
- crime witness ids entering visible action facts.
- rumor text derived from hidden fact text.
- faction reputation reason strings exposing hidden crimes.
- combat/injury results exposing hidden observer identities.
- debug timeline raw `state_deltas` being shown outside the debug panel.
- memory summaries being shown to the player without visibility filtering.

Required protections:

- Keep player-safe reason strings separate from debug reasons.
- Use `visible_state` as the only normal player state output.
- Keep witness identities hidden unless discovered.
- Keep NPC secrets out of dialogue context unless rules make them player-visible.
- Keep debug endpoints disabled outside trusted local development.
- Add tests for hidden observer, hidden rumor, hidden crime, and hidden faction leakage.

## LLM Permission Boundary

v0.4 must not expand LLM authority.

Allowed:

- `IntentParser` parses player input into schema-validated intent.
- `Narrator` renders already-resolved rule outcomes into Chinese prose.
- `MemorySummarizer` summarizes events into internal memories through schema validation.

Not allowed:

- LLM choosing combat hit/miss/damage.
- LLM creating crimes or witnesses.
- LLM spreading rumors.
- LLM changing faction reputation.
- LLM deciding NPC reactions.
- LLM writing `GameState`.
- LLM writing `StateDelta`.
- LLM reading debug timeline as narrator context.

Business modules should continue to depend on `LLMProvider` only through constructor injection or the central provider factory at application composition boundaries.

## v0.4 Integration Tests

Add one or more deterministic integration tests covering:

1. Start `mist_valley`.
2. Search/discover a relevant object or fact.
3. Commit a witnessed suspicious act or crime.
4. Witness learns the fact through `StateDelta`.
5. Social tick reports or spreads the incident.
6. Faction reputation changes.
7. NPC reaction changes.
8. Combat action applies damage.
9. Injury/life state updates.
10. Save game.
11. Load game.
12. Continue one action.
13. Event order, turn, and replay remain stable.
14. `visible_state` excludes hidden witnesses, hidden facts, NPC secrets, and debug-only state.
15. Debug timeline contains the expected social/combat events.
16. Mock provider is used; no real LLM API call occurs.

## Final v0.4 Acceptance Standards

v0.4 is accepted only if all are true:

1. `python -m pytest` passes.
2. Frontend build passes.
3. New content-pack schemas are documented and validated.
4. Faction reputation is structured, persisted, and event-recorded.
5. Crime and witness state is structured, persisted, and event-recorded.
6. Rumor spread is deterministic and respects NPC knowledge.
7. NPC reactions are deterministic and respect known facts.
8. Social consequence tick records system events and applies deltas through `StateDelta`.
9. Combat has deterministic initial attack/damage resolution.
10. Injury/incapacitation/death rules are structured and persisted.
11. Memory retrieval remains internal and does not replace `GameState`.
12. Player APIs expose only filtered `visible_state`.
13. Debug APIs remain local-only and never enter Narrator.
14. Save/load preserves v0.4 state.
15. Replay remains stable for event `state_deltas`.
16. LLM remains language-layer only.
17. `docs/V0_4_ACCEPTANCE_REPORT.md` is generated.
18. `docs/V0_4_RELEASE_NOTES.md` is generated before tagging.

## v0.5 Candidate Direction

Potential v0.5 themes:

- Economy, shops, trade, and item valuation.
- Equipment, durability, and crafting.
- Travel/pathfinding and larger map simulation.
- Relationship arcs and social dialogue mechanics.
- Richer quest scripting and authoring tools.
- World editor prototype.
- Replay/diff UI for saves and timelines.
- Optional vector-backed memory store.
- NPC planning with strict rule-generated action candidates.
- Production hardening for debug/auth if the project ever moves beyond local-only use.
