# World Engine

## Purpose

The world engine is the deterministic authority for the fiction world. It owns canonical state, validates proposed actions, applies rules, emits deltas, records events, and supports persistence.

The LLM may describe, interpret, and summarize, but the world engine decides what is true.

## Core Concepts

### GameState

`GameState` is the canonical snapshot of the world at a point in time. It may later include locations, characters, inventories, clocks, flags, relationships, memories, and active quests.

Only the world engine may apply changes to `GameState`.

### Event

An `Event` is an append-only record of something that happened. Every player action must become an event even if the action fails.

Events should be suitable for audit, replay, debugging, and memory summarization.

### StateDelta

A `StateDelta` is a typed, validated state transition. It describes a specific change, why it is allowed, and which event caused it.

State updates must flow through `StateDelta`; direct mutation is forbidden.

## Initial Modules

- `app.world.state`: canonical state models and public views.
- `app.world.events`: event models and event types.
- `app.world.deltas`: state delta models and application contract.
- `app.world.engine`: orchestration for evaluating actions and applying accepted deltas.
- `app.persistence`: future SQLite repositories and save handling.

## Rule Evaluation

Rules should be deterministic Python code. The engine should treat LLM intent as input, then check:

- Is the actor present and capable?
- Does the target exist in the known state?
- Is the action allowed by location, inventory, relationships, time, or flags?
- What state deltas result?
- What outcome event should be recorded?

## Delta Application

Delta application should be small, explicit, and testable. Each delta type should have a narrow meaning, such as moving an actor, setting a flag, changing an inventory item, advancing time, or adding memory.

Invalid deltas must fail before mutating state.

## Persistence

The first durable design should favor:

- Append-only event log.
- Latest state snapshot.
- Save metadata.
- Optional memory summaries generated from older events.

SQLite is sufficient for local personal use.

## Extension Points

Future systems can be added behind the same boundary:

- Inventory and item rules.
- NPC schedules.
- Relationship simulation.
- Combat or conflict resolution.
- Time and weather.
- Long-term memory compression.
- Scenario import/export.

