# Content Pack Authoring Guide

This document describes the v0.4 content pack format for the local interactive novel world engine.

Content packs define world data. They do not own rules. Rules live in the Python world engine, and all runtime changes still flow through `StateDelta` and `Event`.

## Directory Layout

Each world lives under `worlds/{world_id}/`.

Example:

```text
worlds/mist_valley/
  manifest.yaml
  locations.yaml
  npcs.yaml
  items.yaml
  facts.yaml
  quests.yaml
  factions.yaml
  rumors.yaml
```

`factions.yaml` and `rumors.yaml` are v0.4 additions. `rumors.yaml` is optional; missing rumor files are treated as an empty seed rumor list.

## Validation

Run:

```powershell
python scripts\validate_world.py mist_valley
```

The validator reports `errors`, `warnings`, and `suggestions`.

Exit code rules:

- non-zero when errors exist
- zero when only warnings or suggestions exist

The tool checks schema shape, id references, invalid exits, NPC locations, NPC faction ids, item placement conflicts, quest trigger references, fact `known_by` references, rumor fact references, hidden fact player-text risks, schedule locations, and basic combat/life field consistency.

## manifest.yaml

Defines world identity and metadata.

Expected fields:

- `id`
- `name`
- `description`
- optional author/version metadata, if supported by the loader

The manifest `id` should match the directory name.

## locations.yaml

Each location must include:

- `id`
- `name`
- `description`
- `exits`

Useful optional fields include:

- `visible`
- `hidden`
- `discovered_by`
- `cover_level`
- `light_level`
- `tags`

`exits` must point to existing location ids.

## npcs.yaml

Each NPC must include:

- `id`
- `name`
- `location_id`
- `personality`
- `knowledge`

Common optional fields:

- `faction_id`
- `visible`
- `hidden`
- `discovered_by`
- `schedule`
- `goals`
- `secrets`
- `mood`
- `relationship_to_player`

`schedule` entries support:

- `time_of_day`
- `location_id`
- `activity`

Schedule `location_id` values must exist.

Runtime v0.4 life/combat state supports HP, stamina, alive/dead state, condition, status effects, hostility, suspicion, and alertness. The current content pack loader initializes the runtime defaults and loads only the authorable fields supported by `NPCDef`; do not assume arbitrary combat stat fields in YAML are accepted unless the schema is extended.

NPC secrets are never player-visible by default. NPCs must not act on facts or rumors they do not know.

## items.yaml

Items support structured ownership and placement.

Core fields:

- `id`
- `name`
- `description`
- optional `location_id`
- optional `owner_id`
- optional `container_id`
- `portable`
- `hidden`
- `discovered_by`
- `tags`

Lock-related optional fields:

- `locked`
- `lock_difficulty`
- `lock_state`

Only one of `location_id`, `owner_id`, and `container_id` should be active for a normal item placement. The validator warns or errors on conflicting ownership.

v0.4 combat does not yet implement authored weapons, armor, damage types, or equipment progression.

## facts.yaml

Facts make important world information structured instead of leaving it only in prose.

Each fact includes:

- `id`
- `text`
- `visibility`: `public`, `hidden`, or `discoverable`
- `known_by`
- `tags`

Rules:

- `known_by` NPC ids must exist.
- `public` facts may enter initial player-visible facts.
- `hidden` facts do not enter `visible_state` by default.
- `discoverable` facts enter player-visible known facts only after discovery through rules such as `search`, quest triggers, or other explicit deltas.

Rumor text must not expose hidden fact text unless that text is intentionally safe for the player.

## quests.yaml

Quest definitions support structured state and triggers.

Fields:

- `id`
- `title`
- `description`
- `initial_stage`
- `stages`
- `visibility`
- `triggers`

Each stage includes:

- `id`
- `title`
- `description`
- `objectives`
- `next_stages`

Trigger sources can reference:

- discovered facts
- acquired items
- NPC talked
- visited locations
- reputation conditions, when rule support exists

Triggers must reference existing ids. Quest state changes are applied through `StateDelta`; the LLM does not decide quest progress.

## factions.yaml

v0.4 faction definitions support reputation and player-known faction filtering.

Each faction includes:

- `id`
- `name`
- `description`
- `default_reputation`
- `known_by_player`
- `tags`

Example:

```yaml
factions:
  - id: valley_watch
    name: Valley Watch
    description: Local guards and patrols.
    default_reputation: 0
    known_by_player: true
    tags: ["law", "settlement"]
```

Rules:

- `default_reputation` initializes `GameState.factions`.
- `known_by_player=false` factions should not appear in player-facing `visible_state`.
- Reputation changes are rule-generated `StateDelta` values, never LLM decisions.

The frontend currently displays reputation bands. Raw reputation values should be treated as debug/internal unless the player API intentionally exposes them.

## rumors.yaml

v0.4 seed rumors are optional. Runtime rumors can also be created by crime, combat, quest, or social tick rules.

Each rumor supports:

- `id`
- optional `source_event_id`
- optional `fact_id`
- optional `text_for_player`
- `truth_status`: `true`, `false`, `distorted`, or `unknown`
- `known_by_npcs`
- `known_by_factions`
- `known_by_player`
- `spread_level`
- `tags`
- `created_turn`

Example:

```yaml
rumors:
  - id: rumor_old_road
    fact_id: old_road_smugglers
    text_for_player: People whisper about strange traffic near the old road.
    truth_status: unknown
    known_by_npcs: ["harlan"]
    known_by_factions: []
    known_by_player: false
    spread_level: 1
    tags: ["road", "whisper"]
    created_turn: 0
```

Rules:

- `fact_id`, when present, must reference an existing fact.
- NPC ids in `known_by_npcs` must exist.
- Faction ids in `known_by_factions` must exist.
- Rumors about hidden facts must use safe `text_for_player` or another vague text.
- Rumor propagation is deterministic in v0.4 and must not reveal hidden fact truth directly.

## Crime And Witness Data

Crime and witness records are runtime state in v0.4. They are generated by rules from player actions, combat, lockpicking, theft, social tick, and related consequences.

Do not author canonical crime records in a content pack for v0.4. Future versions may add seed criminal history or law-zone content files.

Player-facing APIs expose only known or public crime consequences. Hidden witnesses remain hidden from player output and Narrator prompts.

## Debug Data

Debug timeline data is not player-facing content. It can include raw `state_deltas`, hidden witnesses, hidden consequences, and internal ids.

Debug APIs are local-only and controlled by `ENABLE_DEBUG_API`.

Never write content assuming debug data will be available to the Narrator or player UI.

## Current Limits

v0.4 content packs do not yet support:

- authored combat equipment stats
- weapon damage tables
- armor systems
- shops or economy
- legal zones or law codes as separate files
- visual map authoring
- automatic content repair
- graphical world editor
- vector memory configuration
