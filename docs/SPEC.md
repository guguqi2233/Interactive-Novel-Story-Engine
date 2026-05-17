# Project Specification

## Goal

Build a local-only LLM interactive fiction world engine. The LLM handles language-facing tasks: intent parsing, narrative rendering, and memory summaries. The deterministic Python world engine owns canonical state, rules, causality, events, visibility, saves, social consequences, and conflict outcomes.

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
- Keep important facts, quests, items, NPC state, social state, combat state, and time in structured state.

## Architecture Boundary

The LLM is a narrator and parser, not the world judge.

The world engine is authoritative. It decides whether an action succeeds, what changes, what is visible, what is remembered, and what gets saved.

No LLM output may directly mutate `GameState`.

All canonical changes must go through `StateDelta`.

All handled player actions and system consequences must be recorded as `Event` entries.

## Current v0.4 Gameplay Loop

1. Player submits text through API or frontend.
2. `IntentParser` returns schema-validated `PlayerIntent`.
3. `ActionDispatcher` selects an action handler.
4. The action handler resolves deterministic `ActionResult`.
5. Action deltas are applied with `apply_delta`.
6. Quest triggers caused by the action are resolved.
7. Turn advances for successful/partial actions.
8. World tick runs schedule, quest triggers, social consequences, NPC reactions, suspicion decay, delayed consequences, and post-delayed quest triggers.
9. Player event and system events are recorded.
10. Crime/witness consequences can be generated from the player event.
11. Narrator receives visible action facts and returns `NarrativeResult`.
12. API returns narration plus filtered `visible_state`.

## v0.4 Included Scope

Backend:

- FastAPI API with health, game start/input/state, save/load, and debug timeline endpoints.
- SQLite save/load for state snapshots, event history, and optional memory records.
- Content-pack loading from `worlds/{world_id}`.
- Content-pack validation CLI.
- Facts from `facts.yaml`.
- Factions from `factions.yaml`.
- Rumors from `rumors.yaml`.
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
- Faction reputation.
- Rumor propagation.
- Crime and witness system.
- Social consequence tick.
- Combat core: attack, defend, flee.
- Injury, death, and incapacitation rules.
- NPC reaction rules.
- Advanced local memory retrieval.
- Debug timeline event view.

Frontend:

- React/Vite local prototype.
- World selection.
- Start/input flow.
- Save/load buttons.
- Visible state panels.
- Player-visible social/status panels.
- Local debug timeline and classified debug panels.

Testing:

- Unit tests for core rules and actions.
- FastAPI tests.
- SQLite save/load tests with temporary databases.
- v0.3 and v0.4 integration regression tests.
- Fake/mock LLM providers in automated tests.

## Persistence Model

SQLite stores:

- `SaveGame` with current `GameState` JSON snapshot.
- `StoredEvent` with full event JSON.
- `StoredMemory` with memory record JSON when explicitly saved.

Event history is suitable for debugging and scoped replay. `StateDelta` values are type-validated when reapplied.

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
- known factions
- known rumors
- known/reported/resolved crimes

It must not include:

- hidden facts not in `player_visible_facts`
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- hidden witnesses
- debug-only event details
- hidden inactive quests
- hidden factions
- hidden/debug memory records

Known caveat: the current visible faction response includes raw numeric reputation as well as a band. The frontend displays only the band. Moving raw reputation to debug-only is a v0.4 hardening recommendation.

## Debug Model

Debug timeline endpoints are local-development tools:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They can show raw `state_deltas`, including hidden/system-only information. They are controlled by `ENABLE_DEBUG_API` and must not be treated as player-facing narrative output.

The frontend shows debug data only in the debug panel.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for handled player actions or system consequences.
- Do not store API keys in source, docs, fixtures, logs, database rows, or saves.
- Do not write provider-specific model calls inside world engine modules.
- Do not make canonical state changes without `StateDelta`.
- Do not expose hidden facts, NPC secrets, hidden witnesses, hidden NPCs, or hidden objects through player APIs.
- Do not put game rules only in prompts.
- Do not let combat, crime, rumor, faction, or NPC reaction outcomes be decided by LLM output.

## Not In v0.4

- Tactical grid combat.
- Multi-round NPC combat AI.
- Guard pursuit, arrest, trial, or full legal system.
- Economy/shop system.
- Crafting.
- Equipment progression, armor, weapon durability, or weight systems.
- Complex NPC autonomous planning.
- LLM-driven NPC agents.
- Pathfinding.
- Full world editor UI.
- Branching replay editor.
- Complex quest scripting language.
- Vector database memory.
- Accounts, cloud sync, or multiplayer.
- Production authentication for debug endpoints.

## v0.4 Known Hardening Items

- Split `ActionResult.reason` into player-safe and debug-only reason fields.
- Move raw faction reputation out of player API.
- Classify LLM-generated memory summaries from hidden/debug event sources as `debug_only` or `hidden` by default.
- Keep frontend debug panel closed by default if used for non-debug playtesting.
- Rewrite any mojibake prompt text into clean UTF-8.
