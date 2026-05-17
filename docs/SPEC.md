# Project Specification

## Goal

Build a local-only LLM interactive fiction world engine. The LLM handles language-facing work: intent parsing, narrative rendering, memory summaries, and optional author-facing draft generation. The deterministic Python world engine owns canonical state, rules, causality, events, visibility, saves, social consequences, combat outcomes, authoring validation, and content-pack loading.

The project is local personal software, not a hosted multiplayer service.

## Core Responsibilities

### LLM Responsibilities

- Parse player natural language into schema-validated `PlayerIntent`.
- Render accepted world outcomes into player-facing prose.
- Summarize recent events into internal memory summaries.
- Optionally generate author-facing side quest drafts through `LLMProvider`.
- Operate only through `LLMProvider`.

### World Engine Responsibilities

- Store canonical `GameState`.
- Evaluate player intent with deterministic rules.
- Produce and apply `StateDelta` objects.
- Record player and system events.
- Persist and load saves through SQLite.
- Enforce visibility boundaries.
- Keep important facts, quests, items, NPC state, social state, combat state, time, memory records, and content-pack definitions in structured data.
- Validate content packs and local mods before loading or saving authoring edits.

## Architecture Boundary

The LLM is a narrator, parser, summarizer, and optional draft assistant. It is not the world judge.

The world engine is authoritative. It decides whether an action succeeds, what changes, what is visible, what is remembered, what gets saved, and what content is loadable.

No LLM output may directly mutate `GameState`.

All canonical changes must go through `StateDelta`.

All handled player actions, system ticks, NPC planning ticks, and system consequences must be recorded as `Event` entries.

Authoring APIs edit content-pack YAML, not active `GameState`. Procedural quest generation produces drafts only.

## Current v0.5 Gameplay Loop

1. Player submits text through API or frontend.
2. `IntentParser` returns schema-validated `PlayerIntent`.
3. `ActionDispatcher` selects an action handler.
4. The action handler resolves deterministic `ActionResult`.
5. Action deltas are applied with `apply_delta`.
6. Quest triggers caused by the action are resolved.
7. Turn advances for successful/partial actions.
8. World tick runs schedule, quest triggers, social consequences, NPC reactions, NPC planning, suspicion decay, delayed consequences, and post-delayed quest triggers.
9. Player event and system events are recorded.
10. Crime/witness consequences can be generated from the player event.
11. Narrator receives visible action facts and returns `NarrativeResult`.
12. API returns narration plus filtered `visible_state`.

## v0.5 Included Scope

Backend:

- FastAPI API with health, game start/input/state, save/load/delete/list, debug timeline, and local authoring endpoints.
- SQLite save/load for state snapshots, event history, and memory records.
- Multi-world content-pack loading from `worlds/{world_id}`.
- Content-pack validation CLI and structured validation report.
- Local authoring API for whitelisted YAML files.
- Content-only mod manifest discovery and validation.
- Multi-world save browser summaries.
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
- NPC goals and deterministic NPC planning tick.
- NPC relationship graph.
- Faction conflict layer.
- Economy/trade rules and buy/sell actions.
- Advanced local memory retrieval with in-memory and SQLite stores plus a local-vector-ready fallback interface.
- `MemoryContextBuilder` for safe narrator/player/NPC memory context.
- Procedural side quest draft generation.

Frontend:

- React/Vite local prototype.
- World selection.
- Start/input flow.
- Save/load/delete browser.
- Visible state panels.
- Player-visible social/status panels.
- Local debug timeline and classified debug panels.
- Authoring panel for reading/editing/saving/validating content-pack YAML.

Testing:

- Unit tests for core rules and actions.
- FastAPI tests.
- SQLite save/load tests with temporary databases.
- Boundary eval tests for narrative visibility leaks.
- v0.3, v0.4, and v0.5 integration regression tests.
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
- known relationships
- visible faction conflicts

It must not include:

- hidden facts not in `player_visible_facts`
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- hidden witnesses
- debug-only event details
- hidden inactive quests
- hidden factions
- hidden relationships
- hidden/debug memory records
- raw `state_deltas`

Known caveats:

- Current visible faction responses still include raw numeric reputation as well as a band. The frontend displays the band; moving raw reputation to debug-only remains a hardening recommendation.
- Current visible faction conflict responses include `conflict_tags`, which may hint at hidden social structure if authored incautiously.

## Debug Model

Debug timeline endpoints are local-development tools:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They can show raw `state_deltas`, including hidden/system-only information. They are controlled by `ENABLE_DEBUG_API` and must not be treated as player-facing narrative output.

The frontend shows debug data only in the debug panel.

## Authoring Model

Authoring endpoints are local-development tools controlled by `ENABLE_AUTHORING_API`.

They can list, read, save, and validate whitelisted YAML files in content packs. They are not player APIs and may show hidden world content to the local author.

Authoring saves YAML files and runs validation. It does not write active session `GameState`.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for handled player actions, system ticks, NPC planning ticks, or system consequences.
- Do not store API keys in source, docs, fixtures, logs, database rows, or saves.
- Do not write provider-specific model calls inside world engine modules.
- Do not make canonical state changes without `StateDelta`.
- Do not expose hidden facts, NPC secrets, hidden witnesses, hidden NPCs, hidden objects, hidden relationships, or hidden/debug memory through player APIs.
- Do not put game rules only in prompts.
- Do not let combat, crime, rumor, faction, trade, NPC planning, relationship, or quest outcomes be decided by LLM output.
- Do not let authoring or mod packaging execute arbitrary code.
- Do not let procedural side quest generation write active saves or content files without explicit authoring review/export.

## Not In v0.5

- Hosted service security, auth, accounts, cloud sync, or multiplayer.
- Tactical grid combat or multi-round combat AI.
- Guard pursuit, arrest, trial, or full legal system.
- Dynamic supply/demand economy, crafting, equipment progression, durability, or weight systems.
- Full graphical world editor or quest graph editor.
- LLM-driven autonomous NPC agents.
- Pathfinding and large-scale world simulation.
- Arbitrary plugin code execution or online mod download.
- Full vector database or embedding pipeline as a hard dependency.
- Automatic content repair.

## v0.5 Known Hardening Items

- Split `ActionResult.reason` into player-safe and debug-only reason fields.
- Move raw faction reputation out of player API.
- Sanitize or remap player-visible faction conflict tags.
- Sanitize invalid mod manifest errors so authoring APIs do not return local absolute paths.
- Classify LLM-generated memory summaries from hidden/debug event sources as `debug_only` or `hidden` by default.
- Keep frontend debug panel closed by default if used for non-debug playtesting.
- Rewrite any mojibake prompt text into clean UTF-8.
