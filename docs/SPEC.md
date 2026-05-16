# Project Specification

## Goal

Build a local-only LLM interactive fiction world engine. The LLM handles language-facing tasks: intent parsing, narrative rendering, NPC dialogue context rendering, and memory summaries. The deterministic world engine owns canonical state, rules, causality, events, visibility, and saves.

The project is local personal software, not a hosted multiplayer service.

## Core Responsibilities

### LLM Responsibilities

- Parse player natural language into schema-validated `PlayerIntent`.
- Render accepted world outcomes into player-facing prose.
- Summarize recent events into internal memory summaries.
- Operate only through `LLMProvider`.

### World Engine Responsibilities

- Store canonical `GameState`.
- Evaluate player intent with deterministic rules.
- Produce and apply `StateDelta` objects.
- Record player and system events.
- Persist and load saves through SQLite.
- Enforce visibility boundaries.
- Keep important facts, quests, items, NPC state, and time in structured state.

## Architecture Boundary

The LLM is a narrator and parser, not the world judge.

The world engine is authoritative. It decides whether an action succeeds, what changes, what is visible, and what gets saved.

No LLM output may directly mutate `GameState`.

## Current v0.3 Gameplay Loop

1. Player submits text through API or frontend.
2. `IntentParser` returns schema-validated `PlayerIntent`.
3. `ActionDispatcher` selects an action handler.
4. The action handler resolves deterministic `ActionResult`.
5. Action deltas are applied with `apply_delta`.
6. Quest triggers caused by the action are resolved.
7. Turn advances for successful/partial actions.
8. World tick runs schedule, suspicion decay, delayed consequences, and tick quest triggers.
9. Player event and system tick events are recorded.
10. Narrator receives visible action facts and returns `NarrativeResult`.
11. API returns narration plus filtered `visible_state`.

## v0.3 Included Scope

Backend:

- FastAPI API with health, game start/input/state, save/load, and debug timeline endpoints.
- SQLite save/load for state snapshots and event history.
- Content-pack loading from `worlds/{world_id}`.
- Facts from `facts.yaml`.
- Multi-world start through optional `world_id`.
- Structured `visible_state`.
- LLM provider factory using `LLM_PROVIDER`.

World engine:

- `GameState`, `StateDelta`, `EventLog`.
- Time system.
- NPC schedule resolver.
- Search action.
- Inventory rule functions.
- Lockpick action.
- Sneak action.
- Quest state machine.
- NPC/world system tick.
- Debug timeline event view.

Frontend:

- React/Vite local prototype.
- World selection.
- Start/input flow.
- Save/load buttons.
- Visible state panels.
- Debug timeline panel.

Testing:

- Unit tests for core rules and actions.
- FastAPI tests.
- SQLite save/load tests with temporary databases.
- v0.3 integration regression tests.
- Fake/mock LLM providers in automated tests.

## Persistence Model

SQLite stores:

- `SaveGame` with current `GameState` JSON snapshot.
- `StoredEvent` with full event JSON.

Event history is suitable for debugging and replay. `StateDelta` values are type-validated when reapplied.

## Visibility Model

Player-visible API responses must be derived from `visible_state`.

`visible_state` includes:

- world id
- turn
- formatted game time
- current location
- inventory
- visible objects
- visible NPC summaries
- known facts
- visible/known quests

It must not include:

- hidden facts not in `player_visible_facts`
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- debug-only event details

## Debug Model

Debug timeline endpoints are local-development tools:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They can show raw `state_deltas`. They are controlled by `ENABLE_DEBUG_API` and must not be treated as player-facing narrative output.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for handled player actions.
- Do not store API keys in source, docs, fixtures, logs, or database rows.
- Do not write provider-specific model calls inside world engine modules.
- Do not make canonical state changes without `StateDelta`.
- Do not expose hidden facts, NPC secrets, hidden NPCs, or hidden objects through player APIs.
- Do not put game rules only in prompts.

## Not in v0.3

- Combat.
- Economy/shop system.
- Crafting.
- Equipment and weight systems.
- Complex NPC autonomous planning.
- LLM-driven NPC agents.
- Pathfinding.
- World editor UI.
- Branching replay editor.
- Complex quest scripting language.
- Vector database memory.
- Accounts, cloud sync, or multiplayer.
- Production authentication for debug endpoints.

