# World Engine

## Purpose

The world engine is the deterministic authority for the fiction world. It owns canonical state, validates actions, applies rules, emits `StateDelta` objects, records `Event` entries, and supports SQLite saves.

The LLM may parse intent, render prose, and summarize memories. It does not decide world truth.

## Core Concepts

### GameState

`GameState` is the canonical world snapshot. In v0.4 it includes:

- world id and turn
- game time
- player location, inventory ownership, HP, condition, combat stance, and status effects
- locations and exits
- objects/items, including hidden/discoverable/locked state
- NPCs, knowledge, secrets, schedule, alertness, suspicion, faction, life state, and combat state
- structured facts and player-visible fact ids
- quest state and quest stages
- delayed consequences
- factions and reputation
- rumors
- crimes and witness records
- social consequences and social flags
- active or ended combat records

### StateDelta

Every canonical state change must be represented as a `StateDelta`.

Supported operations:

- `set`
- `inc`
- `add`
- `remove`

Delta paths use dot notation, for example:

- `player.location_id`
- `objects.sealed_letter.owner_id`
- `npcs.harlan.location_id`
- `quests.missing_tools.current_stage`
- `factions.village_council.reputation.value`
- `rumors.rumor_id.known_by_npcs`
- `crimes.crime_id.status`
- `combats.combat_id.status`

`apply_delta` type-validates Pydantic model field assignments and validates top-level dictionary entries such as `crimes.*`, `rumors.*`, and `witnesses.*` so replayed JSON deltas are restored as structured models where possible.

### Event

Every handled player action is recorded as an `Event`. System changes such as world tick, crime consequences, social consequences, and NPC reactions are recorded as system events when they produce changes.

Events contain:

- turn
- actor id
- action type
- result
- `state_deltas`
- visibility marker
- optional narrative text
- timestamp

Events support debugging, persistence, replay, and memory summarization.

## v0.4 Rule Systems

### NPC Schedule

NPCs can define schedule entries in content packs:

- `time_of_day`
- `location_id`
- `activity`

`resolve_npc_schedules(state)` returns deltas for NPC location and activity changes. Dead or incapacitated NPCs do not move.

### Search

`SearchActionHandler` lets the player search the current location, a visible/discovered object, or a visible/discovered NPC.

Search can reveal discoverable objects and facts through `StateDelta`. Failure consumes time but does not reveal hidden facts.

### Inventory Rules

Inventory is derived from authoritative item placement in `GameState.objects`.

Rules include:

- `can_pick_up`
- `pick_up_item`
- `drop_item`
- `has_item`
- `get_inventory`

Items support `location_id`, `owner_id`, `container_id`, `portable`, `hidden`, `discovered_by`, and `tags`. Pick up and drop operations return deltas.

### Lockpick

`LockpickActionHandler` supports locked object/container targets. It checks target existence, visibility/discovery, locked state, and tool availability. Outcomes can open, scratch, damage, or reject a target. Failed/partial attempts can generate visible lock-mark facts and crime consequences if witnessed.

### Sneak

`SneakActionHandler` supports sneaking to a connected location, to an object, or past/near an NPC. It considers cover, light, possible observers, NPC alertness/suspicion, and player stealth modifier.

Hidden NPCs may influence rule difficulty, but their identity is not placed in player-facing facts.

### Quest State Machine

Quests are loaded from `quests.yaml` and stored in `GameState.quests`.

Quest triggers can be based on:

- fact discovered
- item acquired
- NPC talked
- location visited

Quest changes are emitted as deltas. Only known/active quests enter `visible_state.quests`.

### Faction Reputation

Factions are loaded from `factions.yaml`.

Runtime state stores:

- faction id/name/description/tags
- reputation value
- whether the faction is known to the player
- recent reputation reasons

Rules in `engine/rules/factions.py` provide:

- `get_reputation`
- `change_reputation`
- `set_reputation`
- `get_visible_factions`
- `reputation_band`

Reputation changes are `StateDelta` based and can be produced by crime/social consequences. Player API currently exposes visible factions and their reputation band; raw reputation is also present in the current response model and is listed as a known hardening target.

### Rumor Propagation

Rumors are loaded from optional `rumors.yaml` or created by rules.

`RumorState` tracks:

- id
- optional source event and fact id
- player-safe text
- truth status
- NPC/faction/player knowledge
- spread level
- tags

Rules support creating rumors, adding rumors to NPCs/factions, marking rumors known by the player, filtering visible rumors, and deterministic propagation between NPCs in the same location.

Rumors do not automatically reveal hidden fact text. If a rumor links to a hidden fact, player-facing text must be safe authored text or the vague fallback.

### Crime And Witness

Crime rules classify player events such as theft, lockpicking, assault, murder, vandalism, trespass, and reserved forbidden magic.

Crime/witness rules support:

- `classify_crime`
- `detect_witnesses`
- `create_crime_record`
- `add_witness_record`
- `apply_crime_consequences`
- `get_player_known_crimes`

Witness detection uses NPC location, visibility, life state, light/cover, alertness, suspicion, and sneak metadata. Hidden NPCs can witness events as rule observers, but their identity does not enter player API or narrator prompts.

Visible crime summaries only include player-known or public/reported crime information and omit witness internals.

### Social Consequence Tick

`run_world_tick` includes social consequence processing after schedule and quest trigger resolution.

The v0.4 tick sequence is:

1. NPC schedule
2. quest triggers
3. social consequence tick
4. NPC reaction rules
5. suspicion decay
6. delayed consequences
7. post-delayed quest triggers

Social tick handles deterministic consequences such as crime reporting, rumor generation/propagation, reputation changes, and dedupe flags so the same consequence does not repeat indefinitely.

### Combat Core

Combat is lightweight and narrative-RPG oriented. It is not a tactical grid system.

Implemented actions:

- `attack`
- `defend`
- `flee`

Combat rules check target existence, reachability, visibility, and life state. Attack resolves deterministic hit/miss/glancing/critical style outcomes with seeded RNG. Damage and combat state changes are emitted as `StateDelta`.

Public attacks can generate assault or murder crime records through the crime system.

### Injury, Death, And Incapacitation

Player and NPC life state includes:

- `alive`
- `hp`
- `max_hp`
- `condition`
- `status_effects`

Conditions:

- `healthy`
- `wounded`
- `critical`
- `incapacitated`
- `dead`

Rules in `life_state.py` include:

- `apply_damage`
- `heal_damage`
- `update_condition`
- `mark_incapacitated`
- `mark_dead`
- `can_act`
- `can_move`
- `can_talk`

Dead or incapacitated NPCs do not talk, move on schedules, propagate rumors, or react normally.

### NPC Reaction Rules

NPC reactions are deterministic and based on structured state:

- witnessed crime
- faction reputation band
- known rumor
- relationship to player
- combat/life state

Reaction outcomes include suspicion changes, refusing talk, fleeing, spreading rumors, becoming hostile, and becoming friendly.

Reaction changes use `StateDelta` and are recorded through world tick system events. NPCs cannot react to unknown facts or unknown rumors.

### Advanced Memory Retrieval

Memory remains non-authoritative. It does not replace `GameState` or `EventLog`.

`MemoryRecord` supports:

- id
- content
- source event ids
- tags
- entity ids
- fact ids
- visibility
- importance
- created turn

Memory visibility values:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

Retrieval supports deterministic local search by tags, entity ids, fact ids, substring, and turn range. Hidden/debug-only memories are filtered out of narrator/player contexts by explicit helper functions.

SQLite can preserve memory records through repository methods, but no vector database is required in v0.4.

### Content Validation Tools

Local content validation is available through:

```powershell
python scripts\validate_world.py mist_valley
```

The validator checks schema and references across:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`

It reports errors, warnings, and suggestions. Errors return a non-zero exit code. Warnings do not.

## Visibility Boundary

`visible_state` is built from filtered state:

- hidden facts appear only if their id is in `player_visible_facts`
- hidden objects appear only after discovery
- hidden NPCs appear only after discovery
- NPC secrets are not included in player-visible context by default
- hidden inactive quests are not included
- hidden factions are not included unless known to player
- rumors are included only when known by player
- crime records are included only when player-known, reported, or resolved

Narrator receives only action-visible facts and safe action result fields. It does not receive raw `hidden_facts`, system tick deltas, debug timeline events, witness records, or raw `GameState`.

## Debug Timeline

Local debug endpoints expose event history:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They are controlled by `ENABLE_DEBUG_API`.

Debug timeline may include raw `state_deltas`, including hidden/system details. It is for local development only and is not a player-facing narrative API.

## Persistence

SQLite persistence stores:

- save metadata
- current `GameState` JSON snapshot
- full `Event` JSON payloads
- optional `MemoryRecord` JSON payloads

Save/load can restore state and event history. Event replay applies each event's `state_deltas` against the initial state within the currently supported replay scope.

## Known v0.4 Limits

- No tactical combat grid or multi-round NPC combat AI.
- No guard pursuit, arrest, trial, or full legal system.
- No economy/shop/crafting/equipment progression.
- No pathfinding or large-scale world simulation.
- No LLM-driven autonomous NPC planning.
- No vector database or embedding pipeline.
- Content validation is CLI/report only; it does not auto-fix YAML.
- Debug API has no production authentication and must remain local-only.
- Raw faction reputation is still present in player API and should be moved to debug-only in a future hardening pass.
