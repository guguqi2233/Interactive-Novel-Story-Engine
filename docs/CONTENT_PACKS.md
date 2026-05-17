# Content Pack Format

World content lives under `worlds/{world_id}`. Content packs are local YAML
data. They are loaded and validated by the world loader before they become
runtime `GameState`.

The engine must not hardcode a specific world. `mist_valley` is only the sample
world.

## Directory Layout

```text
worlds/
  mist_valley/
    manifest.yaml
    locations.yaml
    npcs.yaml
    items.yaml
    quests.yaml
    facts.yaml
    factions.yaml
    rumors.yaml
    relationships.yaml
```

Optional local mods may live under `mods/{mod_id}` and contain a `mod.yaml`
manifest plus content paths. Mods are content-only and must not execute code.

## manifest.yaml

Required fields:

```yaml
world_id: mist_valley
name: Mist Valley
version: 0.6.0
start_location_id: village_square
description: A small valley world used for local testing.
```

`world_id` must match the directory id used by `/game/start`.

The manifest `version` is treated as the content pack version for save
metadata where available. Runtime saves also carry `schema_version`,
`world_version`, `content_pack_version`, and `migration_history`; those are
save metadata, not player-visible facts.

## locations.yaml

Each location must define:

```yaml
- id: village_square
  name: Village Square
  description: A wind-worn square at the center of the valley.
  exits:
    north: blacksmith
  visible: true
  hidden: false
  discovered_by:
    - player
  cover_level: 1
  light_level: 2
```

Validation checks that exits point to existing locations.

## npcs.yaml

NPCs may define schedule, knowledge, social state, life state, goals, merchant
fields, and planning metadata.

```yaml
- id: harlan
  name: Harlan
  location_id: blacksmith
  personality: terse but fair
  knowledge:
    - fact_old_road_closed
  goals:
    - id: keep_shop_safe
      description: Keep the forge and tools safe.
      priority: 10
      status: active
      conditions: []
      desired_state: {}
      allowed_actions:
        - guard_location
        - report_crime
      forbidden_actions: []
  priorities:
    safety: 10
  constraints:
    avoid_locations: []
  current_goal_id: keep_shop_safe
  plan_state:
    last_action: guard_location
  secrets:
    - fact_hidden_debt
  mood: neutral
  relationship_to_player: neutral
  faction_id: village_council
  alertness: 1
  suspicion: 0
  alive: true
  hp: 10
  max_hp: 10
  condition: healthy
  status_effects: []
  merchant: true
  shop_inventory:
    - simple_lockpick
  buy_price_modifier: 1.1
  sell_price_modifier: 0.6
  schedule:
    - time_of_day: morning
      location_id: blacksmith
      activity: opening the forge
```

Validation checks:

- `location_id` exists.
- `faction_id` exists when provided.
- schedule locations exist.
- life fields are valid.
- goal ids and statuses are valid.

NPC secrets are not player-visible by default.

## items.yaml

Items define ownership, visibility, portability, lock state, and economy data.

```yaml
- id: simple_lockpick
  name: Simple Lockpick
  description: A small bent tool used for cheap locks.
  location_id: village_square
  owner_id:
  container_id:
  portable: true
  hidden: false
  discovered_by:
    - player
  tags:
    - tool
    - lockpick
  locked: false
  lock_difficulty: 0
  lock_state: intact
  base_price: 12
  tradeable: true
  rarity: common
```

Ownership fields must not conflict. An item should not simultaneously belong
to a location, owner, and container unless a future container rule explicitly
supports it.

Economy fields:

- `base_price`: non-negative integer.
- `tradeable`: whether merchants can trade the item.
- `rarity`: author-defined rarity label.

Hidden items do not appear in `visible_state` until discovered.

## facts.yaml

Facts are structured knowledge records:

```yaml
- id: fact_old_road_closed
  text: The old road is blocked by a recent rockslide.
  visibility: public
  known_by:
    - harlan
  tags:
    - road
```

Visibility values:

- `public`: can enter initial player-known facts.
- `hidden`: not player-visible by default.
- `discoverable`: visible only after discovery.

Validation checks that `known_by` NPC ids exist.

Hidden fact text must not be copied into player-visible descriptions, rumors,
or quest draft fields.

## quests.yaml

Quests define stages, objectives, visibility, and triggers.

```yaml
- id: find_the_old_road
  title: Find the Old Road
  description: Learn what happened beyond the village.
  visibility: public
  initial_stage: start
  stages:
    - id: start
      title: Ask Around
      description: Find someone who knows about the old road.
      objectives:
        - id: ask_harlan
          description: Talk to Harlan.
          completed: false
      next_stages:
        - road_known
    - id: road_known
      title: The Road Is Blocked
      description: The old road is blocked.
      objectives: []
      next_stages: []
  triggers:
    - type: fact_discovered
      fact_id: fact_old_road_closed
      next_stage: road_known
```

Trigger references may include facts, items, NPCs, locations, reputation,
conversation, or quest state depending on the rule path. Validation checks
known references where supported.

Hidden quests do not enter `visible_state` until activated or revealed.

## factions.yaml

Factions define reputation and conflict metadata:

```yaml
- id: village_council
  name: Village Council
  description: The informal authority in Mist Valley.
  default_reputation: 0
  known_by_player: true
  tags:
    - local
  relations:
    bandits: -30
  conflict_tags:
    - road_dispute
  default_alert_level: 0
  resources:
    coin: 100
```

Runtime state tracks:

- reputation toward the player
- reputation band
- known/hidden status
- relations to other factions
- conflict level
- alert level
- resources

Validation checks relation targets when possible. Hidden factions should not be
referenced by player-facing text.

## rumors.yaml

Rumors are structured social knowledge:

```yaml
- id: rumor_locked_shed
  source_event_id:
  fact_id:
  text_for_player: Someone has been asking about the locked shed.
  truth_status: unknown
  known_by_npcs:
    - harlan
  known_by_factions:
    - village_council
  known_by_player: false
  spread_level: 1
  tags:
    - shed
  created_turn: 0
```

Rumors linked to hidden facts must use safe player-facing text. They must not
expose the hidden fact's real text unless the fact is legitimately known.

## relationships.yaml

Relationships are directional records between NPCs or actors:

```yaml
- id: harlan_to_mira
  source_id: harlan
  target_id: mira
  relation_type: coworker
  trust: 40
  fear: 0
  affinity: 25
  obligation: 10
  tags:
    - village
  known_by_player: false
```

Validation checks that source and target actor ids exist. Hidden relationships
do not enter player APIs.

Relationship values can influence rumor propagation, NPC planning, and
reactions. Changes must go through `StateDelta`.

## NPC Goals

NPC goals can be embedded in `npcs.yaml`. A goal contains:

```yaml
id: keep_shop_safe
description: Keep the shop safe.
priority: 10
status: active
conditions:
  - type: knows_fact
    fact_id: fact_old_road_closed
desired_state:
  location_id: blacksmith
allowed_actions:
  - guard_location
  - report_crime
forbidden_actions:
  - flee_location
```

NPC goals are deterministic rule inputs. They do not call the LLM and do not
allow NPCs to know unknown facts.

## Economy and Trade Fields

Items:

- `base_price`
- `tradeable`
- `rarity`
- `tags`

NPC merchants:

- `merchant`
- `shop_inventory`
- `buy_price_modifier`
- `sell_price_modifier`

Player currency is stored in `GameState`. Buy/sell actions are authoritative
backend actions and must not be calculated only in the frontend.

## Procedural Quest Drafts

Procedural side quest generation produces `QuestDraft`, not runtime quest
state:

```yaml
title: Missing Tools
premise: A local craftsperson needs help recovering a lost tool.
involved_npcs:
  - harlan
involved_locations:
  - blacksmith
involved_items:
  - simple_lockpick
required_facts:
  - fact_old_road_closed
stages:
  - id: start
    title: Ask Harlan
    description: Speak with Harlan.
triggers: []
rewards:
  coin: 5
risk_flags:
  - needs_author_review
validation_notes:
  - Generated as a draft; validate before saving.
```

Drafts must be reviewed by the local creator and saved explicitly through
authoring tools if desired. The generator must not directly modify active
saves, `GameState`, or `quests.yaml`.

LLM-assisted draft generation is optional, goes through `LLMProvider`, and must
be schema-validated. It may not silently create nonexistent references.

## Mod Manifest

Content-only mods use `mod.yaml`:

```yaml
id: sample_mod
name: Sample Mod
version: 0.1.0
engine_version_min: 0.6.0
engine_version_max:
content_schema_version: "6"
dependencies: []
optional_dependencies: []
conflicts: []
load_order_hint: 0
compatible_worlds:
  - mist_valley
entry_worlds:
  - mist_valley
content_paths:
  - worlds/mist_valley
migration_notes: "No migration required."
author: Local Author
description: Adds local content for testing.
```

Rules:

- Mods are local content packages only.
- Mods must not execute Python, JavaScript, shell, or arbitrary code.
- Paths must stay inside the mod directory.
- Entry worlds are validated through the normal world validation pipeline.
- Dependency, optional dependency, conflict, engine-version,
  content-schema-version, and load-order checks are simple and deterministic in
  v0.6.
- There is no online registry, automatic download, arbitrary script execution,
  hot reload of active saves, or complex SAT-style version solver.

## Save Migration Notes

v0.6 saves include migration metadata:

- `engine_version`
- `schema_version`
- `world_id`
- `world_version`
- `content_pack_version`
- `created_at`
- `updated_at`
- `migration_history`
- enabled mod ids and versions where available

Migrations are deterministic local code. They do not call the LLM, do not drop
event history, and must not change hidden/debug classifications into
player-visible data. Authoring preview and impact analysis can warn about
removed or renamed ids that may require migration work, but they do not apply a
migration or write active saves.

## Graph Visibility Fields

Relationship and faction graphs derive visibility from existing structured
fields:

- `known_by_player` on factions and relationships.
- actor/object visibility fields such as `hidden`, `visible`, and
  `discovered_by`.
- player-known facts, rumors, crimes, and quest state where graph labels refer
  to world knowledge.

Player graph APIs must return only player-known nodes and edges. Debug graph
APIs may include more complete graph information, but only when
`ENABLE_DEBUG_API=true`, and must not return API keys, environment variables,
raw `GameState`, or raw `state_deltas`.

Known v0.6 hardening note: player graph filtering is currently stricter than
the `visible_state.relationships` summary. Before v0.6 acceptance, the player
visible-state relationship summary should also filter relationship endpoints by
actor visibility.

## Combat and Life Fields

Combat/life state fields used by v0.6 include:

- `alive`
- `hp`
- `max_hp`
- `condition`: `healthy`, `wounded`, `critical`, `incapacitated`, `dead`
- `status_effects`: currently includes support for `guarded`, `stunned`, and
  `bleeding`
- `stance`: currently includes `aggressive`, `defensive`, `cautious`, and
  `fleeing`

`defend` can set guarded/defensive state, attacks can consume guarded state,
stunned actors cannot take normal combat actions, bleeding is a lightweight
tracked status, and non-lethal attacks prefer incapacitation over death.
Combat outcomes remain deterministic rule-engine decisions and do not call the
LLM. Player-visible combat summaries must not reveal hidden NPCs or hidden
witnesses.

## Validation Commands

Validate the sample world:

```powershell
python scripts\validate_world.py mist_valley
```

Produce JSON:

```powershell
python scripts\validate_world.py mist_valley --json
```

Authoring API validation:

```text
POST /authoring/worlds/{world_id}/validate
POST /authoring/mods/{mod_id}/validate
```

Validation reports contain:

- `errors`
- `warnings`
- `suggestions`
- issue `file`
- YAML `path`
- `code`
- `message`
- `severity`
- optional reference id and fix suggestion

The CLI returns a non-zero exit code when errors are present.

## Security and Visibility Rules

- Content packs cannot access local secrets.
- Authoring API may read/write only whitelisted YAML files.
- Debug data is not player-facing content.
- Hidden facts must not be copied into public text.
- Hidden NPCs, witnesses, relationships, and factions remain hidden unless
  revealed by rules.
- Memory records are context aids, not content pack facts.
- Mods are data only and cannot execute code.

## Current Limits

- The v0.6 authoring UI is richer than a textarea editor, but it is still not a
  full IDE or graphical quest graph editor.
- No automatic YAML repair.
- No online mod registry or download support.
- No hot reload of running saves after authoring edits.
- No complex version solver for mods.
- No dynamic economy simulation.
- No LLM-powered automatic content rewriting.
- No formal desktop installer or auto-update path.
