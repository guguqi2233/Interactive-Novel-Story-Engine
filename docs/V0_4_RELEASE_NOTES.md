# v0.4 Release Notes

## Version Name

v0.4 - Social Consequences & Conflict Systems

## Release Target

v0.4 upgrades the local LLM interactive novel world engine from a trustworthy small-world prototype into an early narrative RPG engine prototype.

This remains a local self-use engine. It is not a hosted service, not a multiplayer product, and not a production-secured application.

The LLM is still not the world judge. It may parse intent, render prose, and summarize memory through `LLMProvider`, but all canonical world outcomes are decided by deterministic Python rules and recorded through `StateDelta` and `Event`.

## New Features

### Social System Base Schema

`GameState` now includes structured fields for:

- factions
- reputation
- rumors
- crimes
- witnesses
- social consequences
- social flags

Old v0.3-style state payloads with missing social fields can load with safe defaults.

### Faction Reputation

v0.4 adds faction state and reputation rules:

- `factions.yaml` content-pack support
- default reputation loading
- reputation changes through `StateDelta`
- deterministic reputation bands:
  - hostile
  - suspicious
  - neutral
  - friendly
  - trusted
- hidden faction filtering from `visible_state`

Crime and social consequence rules can affect faction reputation. The LLM does not decide reputation changes.

### Rumor Propagation

v0.4 adds structured rumors:

- optional `rumors.yaml`
- runtime rumor creation
- deterministic propagation between eligible NPCs
- player-known rumor filtering
- safe rumor text handling for hidden-linked facts

NPCs can only propagate rumors they know. Dead or incapacitated NPCs do not propagate rumors.

### Crime / Witness System

v0.4 introduces rule-owned crime and witness records:

- crime classification for actions such as theft, lockpicking, assault, and murder
- witness detection based on location, visibility, light, cover, alertness, suspicion, and sneak metadata
- witness knowledge via structured state
- crime consequences such as rumor creation and reputation loss

Hidden witnesses can influence rules, but their identities do not enter player API responses or Narrator prompts.

### Social Consequence Tick

World tick now includes social consequence processing.

Current tick sequence:

1. NPC schedule
2. quest triggers
3. social consequence tick
4. NPC reactions
5. suspicion decay
6. delayed consequences
7. post-delayed quest triggers

Tick results are deterministic, emitted as `StateDelta`, and recorded as system events when changes occur. Dedupe flags prevent repeated consequences such as repeated reputation loss from the same crime.

### Combat Core

v0.4 adds the first lightweight combat core:

- `attack`
- `defend`
- `flee`

Combat outcomes are decided by the rules engine, not by the LLM.

Implemented combat structures include:

- `CombatState`
- `CombatantState`
- `AttackResult`
- `DamageResult`

Damage changes HP/status/condition through `StateDelta`. Public assault or murder can feed into crime/witness rules.

This is not a tactical combat system. There is no grid, equipment progression, armor model, weapon durability, or autonomous multi-round combat AI.

### Injury / Death / Incapacitation

Actor life state is now structured with:

- `alive`
- `hp`
- `max_hp`
- `condition`
- `status_effects`

Conditions include:

- healthy
- wounded
- critical
- incapacitated
- dead

Rules prevent dead/incapacitated NPCs from schedule movement, talking, spreading rumors, witnessing new crimes, reacting normally, or influencing sneak observation.

### NPC Reaction Rules

NPCs can now react deterministically to structured knowledge:

- witnessed crime
- faction reputation band
- known rumor
- relationship to player
- combat/life state

Reactions can increase suspicion, reduce trust, refuse talk, flee, spread rumors, become hostile, or become friendly. NPCs cannot react to unknown rumors or unknown facts.

### Advanced Memory Retrieval

v0.4 adds structured `MemoryRecord` and local deterministic retrieval by:

- tags
- entity ids
- fact ids
- substring
- turn range
- recency

Memory is not an authoritative fact source. It does not replace `GameState` or `EventLog`.

Memory visibility supports:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

Hidden/debug memory must not enter Narrator context. Current Narrator does not directly consume memory records.

### Content Authoring Validation

v0.4 adds a local validation tool:

```powershell
python scripts\validate_world.py mist_valley
```

The validator reports errors, warnings, and suggestions, and returns a non-zero exit code when errors exist.

It checks:

- required YAML files
- schema validity
- duplicate ids
- cross-type id reuse warnings
- exits
- NPC locations
- NPC faction ids
- item placement conflicts
- quest trigger references
- fact `known_by`
- rumor references
- hidden fact leak warnings
- schedule locations
- basic combat/life field consistency

### Frontend Social / Debug Panels

The React/Vite frontend now displays player-visible v0.4 state:

- known factions
- reputation bands
- known rumors
- known crimes
- visible NPC condition
- save/load and world selection controls

The debug panel displays local-only debugging data:

- raw event timeline
- raw `state_deltas`
- social consequence events
- combat/injury events
- raw reputation deltas

Debug data remains visually separated from story output.

## Behavior Changes

- Unknown and clarification-required player inputs now record no-op `Event` entries with `allow_empty_delta=True`; they still do not mutate `GameState`.
- Step-based save persistence now stores system events as well as player events.
- Dead/incapacitated NPCs no longer affect sneak observation.
- Dead/incapacitated NPCs are prevented from schedule movement, conversation, rumor propagation, witnessing new crimes, and normal reaction processing.
- World tick now processes social consequence and NPC reaction rules in addition to schedule, quest, suspicion decay, and delayed consequences.
- Combat and social consequences can create additional system events after a player event.

## API Changes

Player-facing APIs remain centered on existing game endpoints:

- `POST /game/start`
- `POST /game/input`
- `GET /game/state/{session_id}`
- `GET /game/saves`
- `POST /game/{session_id}/save`
- `POST /game/load/{save_id}`

`visible_state` now includes v0.4 social fields:

- `factions`
- `known_rumors`
- `known_crimes`
- visible NPC `condition`

Debug APIs remain local-development only and controlled by `ENABLE_DEBUG_API`:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

Debug API can return raw `state_deltas` and hidden/system-only information. It must not be exposed as a player-facing or production API.

Known API caveat:

- `VisibleFactionResponse` still includes raw numeric `reputation` as well as `band`. The frontend displays only `band`; raw reputation should move to debug-only in a future hardening pass.

## Content Pack Format Changes

v0.4 content packs may include:

```text
worlds/{world_id}/
  manifest.yaml
  locations.yaml
  npcs.yaml
  items.yaml
  facts.yaml
  quests.yaml
  factions.yaml
  rumors.yaml
```

### factions.yaml

Adds faction definitions:

- `id`
- `name`
- `description`
- `default_reputation`
- `known_by_player`
- `tags`

### rumors.yaml

Adds optional seed rumors:

- `id`
- optional `source_event_id`
- optional `fact_id`
- optional `text_for_player`
- `truth_status`
- `known_by_npcs`
- `known_by_factions`
- `known_by_player`
- `spread_level`
- `created_turn`
- `tags`

### NPC Content

NPCs can reference:

- `faction_id`
- `schedule`
- visibility fields

Runtime v0.4 actor life/combat state has defaults. Arbitrary authored combat stat fields are not yet accepted unless the schema explicitly supports them.

### Items

Item placement remains structured through:

- `location_id`
- `owner_id`
- `container_id`

Lock-related item fields are supported:

- `locked`
- `lock_difficulty`
- `lock_state`

v0.4 does not add authored weapons, armor, or equipment progression.

## Frontend Changes

The frontend prototype now includes:

- social panel for known factions, bands, known rumors, and known crimes
- status panel for player/visible NPC status information when available
- debug timeline grouping for social and combat events
- raw reputation delta display in debug panel
- graceful handling of disabled debug API

The frontend does not call LLM directly and does not infer hidden state. Player-facing UI reads backend `visible_state`; debug details stay inside the debug panel.

## Test Results

Verification date: 2026-05-17

Backend:

```powershell
python -m pytest
```

Result:

```text
257 passed
```

Frontend:

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
tsc -b && vite build succeeded
```

Content validation:

```powershell
python scripts\validate_world.py mist_valley
```

Result:

```text
errors: 0
warnings: 1
suggestions: 0
```

The warning is non-blocking: `sealed_letter` is reused across item and quest ids.

## Known Limitations

- Local self-use prototype only; not production-secured.
- No tactical grid combat.
- No multi-round autonomous NPC combat AI.
- No guard pursuit, arrest, trial, or full legal system.
- No economy, shops, crafting, equipment progression, armor, weapon durability, or weight system.
- No pathfinding or large-scale world simulation.
- No LLM-driven autonomous NPC planning.
- No vector database or embedding pipeline.
- No graphical world editor.
- Content validator reports issues but does not auto-fix YAML.
- Debug API has no production authentication and must remain local-only.
- Raw numeric faction reputation remains in player API.
- `ActionResult.reason` is still passed to Narrator and relies on rule authors to keep it player-safe.
- Memory summaries derived from hidden/debug events require careful visibility classification before future narrator use.
- Some legacy prompt/text content contains mojibake and should be cleaned for readability.

## Upgrade Notes From v0.3

### Save Data

v0.4 extends `GameState` with social, combat, life, rumor, crime, witness, and memory-related fields.

Old v0.3 save payloads missing these fields should load with default values through compatibility logic. Existing local SQLite databases may need schema migration for memory/event additions, which the repository initializes lazily.

For clean local testing, deleting old ignored local `.db` files is acceptable.

### Content Packs

Add or review:

- `factions.yaml`
- `rumors.yaml`

Then run:

```powershell
python scripts\validate_world.py {world_id}
```

Content packs should avoid player-facing rumor text that directly reveals hidden facts.

### Frontend

Rebuild the frontend after pulling v0.4 changes:

```powershell
cd frontend
npm install
npm.cmd run build
```

Use `VITE_API_BASE_URL` to point the frontend at the local backend.

### Environment

Recommended local defaults:

```text
LLM_PROVIDER=mock
ENABLE_DEBUG_API=true
DATABASE_URL=sqlite:///./world_engine.db
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use `LLM_PROVIDER=openai` only with `LLM_API_KEY` set in the local environment. Do not commit API keys.

## Recommended v0.5 Direction

1. Split `ActionResult.reason` into `player_reason` and `debug_reason`.
2. Remove raw numeric faction reputation from player API or expose it only through debug API.
3. Add explicit memory visibility classification for LLM-generated summaries.
4. Clean prompt/text mojibake into readable UTF-8.
5. Default frontend debug panel to closed for safer playtesting.
6. Tighten `WorldLoader` reference validation to match the validator.
7. Expand combat carefully with equipment, armor, healing, surrender, and multi-round NPC reactions.
8. Add law/guard response systems if crime consequences become central.
9. Add optional vector memory backend while preserving deterministic local fallback.
10. Consider a simple world authoring UI after validator coverage is stronger.

## Final Note

v0.4 is accepted for local release.

The world engine remains the only source of truth. The LLM remains language-layer only. Debug data remains local-only. Memory remains context, not canon.
