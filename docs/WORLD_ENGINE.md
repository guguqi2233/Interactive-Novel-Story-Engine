# World Engine

## Purpose

The world engine is the deterministic authority for the fiction world. It owns canonical state, validates actions, applies rules, emits `StateDelta` objects, records `Event` entries, and supports SQLite saves.

The LLM may parse intent, render prose, and summarize memories, but it does not decide world truth.

## Core Concepts

### GameState

`GameState` is the canonical world snapshot. In v0.3 it includes:

- world id and turn
- game time
- player location and inventory ownership
- locations and exits
- objects/items, including hidden/discoverable/locked state
- NPCs, knowledge, schedule, alertness, suspicion, and activity
- structured facts and player-visible fact ids
- quest state and quest stages
- delayed consequences for system tick processing

### StateDelta

Every canonical state change must be represented as a `StateDelta`.

Supported operations:

- `set`
- `inc`
- `add`
- `remove`

Delta paths use dot notation such as:

- `player.location_id`
- `objects.sealed_letter.owner_id`
- `npcs.harlan.location_id`
- `quests.missing_tools.current_stage`

`apply_delta` validates Pydantic model field types when assigning values, so replayed JSON deltas from SQLite are converted back to model/enum types where possible.

### Event

Every handled player action is recorded as an `Event`. System changes such as world tick updates are recorded as system events.

Events contain:

- turn
- actor id
- action type
- result
- `state_deltas`
- visibility marker
- optional narrative text
- timestamp

Events are used for debugging, persistence, replay, and memory summarization.

## v0.3 Rule Systems

### NPC Schedule

NPCs can define schedule entries in content packs:

- `time_of_day`
- `location_id`
- `activity`

`resolve_npc_schedules(state)` compares current game time with NPC schedule entries and returns deltas for:

- NPC location changes
- NPC current activity changes

Invalid schedule target locations are rejected during content loading and rule resolution.

### Search

`SearchActionHandler` lets the player search:

- current location
- a visible/discovered object
- a visible/discovered NPC

Search can reveal:

- discoverable objects by adding the player to `objects.{id}.discovered_by`
- discoverable facts by adding fact ids to `player_visible_facts`

Search failure consumes time but does not reveal hidden facts.

### Inventory Rules

Inventory is derived from authoritative item ownership in `GameState.objects`.

Rules include:

- `can_pick_up`
- `pick_up_item`
- `drop_item`
- `has_item`
- `get_inventory`

Items support:

- `location_id`
- `owner_id`
- `container_id`
- `portable`
- `hidden`
- `discovered_by`
- `tags`

An item must not simultaneously belong to multiple placements. Pick up and drop operations return `StateDelta` lists.

### Lockpick

`LockpickActionHandler` supports locked object/container targets. It checks:

- target exists
- target is visible or discovered
- target is locked
- player has a lockpick tool tag, or attempts without a tool at higher difficulty

Outcomes:

- `success`: unlocks target and sets lock state opened
- `partial_success`: leaves scratches or a visible lock mark fact
- `failure`: damages or marks the lock
- `invalid`: target is missing, inaccessible, hidden-undiscovered, or not locked

The result is deterministic under the provided seeded RNG.

### Sneak

`SneakActionHandler` supports:

- sneaking to a connected location
- sneaking to an object in the current location
- sneaking near an NPC in the current location

The rule checks:

- valid target
- location connectivity
- possible observers
- destination cover/light
- NPC alertness/suspicion
- player stealth modifier

Hidden NPCs can influence rule difficulty, but their identity is not placed in player-visible facts.

### Quest State Machine

Quests are loaded from content-pack `quests.yaml` and stored in `GameState.quests`.

Quest data includes:

- id
- title
- description
- visibility
- status
- initial/current stage
- stages
- objectives
- triggers

Triggers can be based on:

- fact discovered
- item acquired
- NPC talked
- location visited

Quest changes are emitted as deltas, for example:

- `quests.{id}.status`
- `quests.{id}.known_to_player`
- `quests.{id}.current_stage`
- `quests.{id}.completed_objectives`

Only known/active quests enter `visible_state.quests`.

### World Tick

`run_world_tick(state, rng)` runs after a successful or partially successful player action, after time/turn changes.

The current tick handles:

- NPC schedule resolver
- NPC suspicion decay
- due delayed consequences
- quest triggers caused by tick deltas

Tick changes are returned as deltas and recorded in a system `Event` with `action_type="world_tick"` when changes occur.

### Debug Timeline

Local debug endpoints expose event history:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They are controlled by `ENABLE_DEBUG_API`.

Debug timeline may include raw `state_deltas`, including hidden/system details. It is for local development only and is not a player-facing narrative API.

## Visibility Boundary

`visible_state` is built from filtered state:

- hidden facts appear only if their id is in `player_visible_facts`
- hidden objects appear only after discovery
- hidden NPCs appear only after discovery
- NPC secrets are not included in player-visible context by default
- hidden inactive quests are not included

Narrator receives only action-visible facts, not raw `hidden_facts` or system tick deltas.

## Persistence

SQLite persistence stores:

- save metadata
- current `GameState` JSON snapshot
- full `Event` JSON payloads

Save/load can restore state and event history. Event replay applies each event's `state_deltas` against the initial state.

## Known v0.3 Limits

- No combat system.
- No economy/shop system.
- No equipment or weight system.
- No complex NPC planning or LLM-driven autonomous agents.
- No pathfinding.
- No full quest scripting language or quest editor.
- No complex memory/vector database integration.
- Debug timeline is minimal and local-only.

