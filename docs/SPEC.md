# Project Specification

## Goal

Build a local-only LLM interactive fiction world engine. The LLM provides language intelligence: intent parsing, narrative rendering, NPC dialogue, and memory summaries. The deterministic world engine owns the real world state: rules, causality, event logs, and saves.

The first version should deliver only the smallest playable loop, while preserving boundaries that support later expansion.

## Core Responsibilities

### LLM Responsibilities

- Parse player natural-language input into structured intent candidates.
- Render validated world outcomes into prose.
- Generate NPC dialogue within provided state and memory context.
- Summarize old events into compact memory records.

### World Engine Responsibilities

- Store the canonical `GameState`.
- Evaluate player intent against deterministic rules.
- Produce and apply validated `StateDelta` objects.
- Record every player action and system outcome as `Event` entries.
- Persist and load saves.
- Maintain causality: state changes must be explainable by prior events.

## Architecture Boundary

The LLM is advisory and expressive. It can propose structured intent and text, but it cannot directly mutate canonical state.

The world engine is authoritative. It decides whether an action is possible, creates state deltas, applies them, and records events.

## Minimal Playable Flow

1. Player submits an action as text.
2. API records a player `Event`.
3. LLM intent parser receives limited current context and returns a schema-validated intent.
4. World engine evaluates the intent against `GameState`.
5. World engine emits one or more `StateDelta` objects.
6. State deltas are validated and applied to `GameState`.
7. System records resulting outcome events.
8. LLM narrative renderer receives the accepted outcome and returns schema-validated narration.
9. API returns updated public state view and narration.

## Persistence Model

Initial persistence should use SQLite. The event log is the most important durable record. A save can store both the latest snapshot and the event history needed for auditing or replay.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for player actions.
- Do not store API keys in source files, docs examples with real values, tests, fixtures, logs, or database rows.
- Do not write provider-specific model calls inside world engine modules.
- Do not make irreversible state changes without an event and a delta.
- Do not implement broad game systems before the minimal loop exists.

## First-Version Scope

Included:

- Project documentation.
- Backend package skeleton.
- Typed domain schema placeholders.
- LLM provider interface placeholder.
- API package placeholder.
- Test package placeholder.

Deferred:

- Full database schema.
- Complete gameplay rules.
- Frontend.
- Live provider integrations.
- Save browser, editor tooling, multi-world support, combat, economy, and advanced memory.

