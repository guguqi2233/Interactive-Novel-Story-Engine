# Content Pack Format

World content lives under `worlds/{world_id}`. Content packs are local YAML
data. They are loaded and validated by the world loader before they become
runtime `GameState`.

The engine must not hardcode a specific world. `mist_valley` is only the sample
world.

## v1.0 Schema Freeze

v1.0 freezes the current local content-pack schema for Stable Local Studio
Edition. The detailed freeze contract lives in
`docs/V1_0_CONTENT_SCHEMA_CONTRACT.md`.

Frozen v1.0 formats:

- `manifest.yaml`
- `locations.yaml`, including optional `visual` map fields
- `npcs.yaml`, including schedules, goals, merchant fields, and visibility
- `items.yaml`, including economy, lock, ownership, and visibility fields
- `quests.yaml`, including graph editor stages, triggers, rewards, and
  alternate/failure paths
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`
- scenario templates in `templates/`
- content-only `mod.yaml`
- scenario regression files
- prompt profiles
- import/export package manifests

Post-v1.0 compatibility policy:

- New fields must be optional first.
- Breaking field removals, renames, or required semantic changes require a
  migration and release notes.
- Validation should warn before a planned breaking change becomes an error.
- Content migrations must not make hidden/debug data player-visible.
- Visual editors, template application, import/export, and authoring saves must
  continue to run validation before writing.

Content packs still do not configure LLM providers, execute scripts, or modify
active runtime `GameState` directly.

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
version: 1.0.0
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
  visual:
    x: 120
    y: 80
    region_id: village
    icon: square
    color_tag: safe
    display_group: village
    tags:
      - hub
    visibility: public
    notes: Authoring-only note; not player-visible.
```

Validation checks that exits point to existing locations.

v0.8 visual map fields are optional. If omitted, authoring map graph builders
provide deterministic default positions without writing the file. `visual`
fields are for authoring and map display only; they do not change movement,
visibility, or rule outcomes.

`visual.visibility` can mark nodes or edges as public, discoverable, or hidden.
Player-visible map graphs must show only known non-hidden locations and exits.
Authoring maps can show full local content in authoring-only panels.

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
engine_version_min: 0.7.0
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
  v0.7.
- There is no online registry, automatic download, arbitrary script execution,
  hot reload of active saves, or complex SAT-style version solver.

## Save Migration Notes

v0.6+ saves include migration metadata:

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

Known v0.7 hardening note: authoring and debug graph views can expose full
local content for the creator/developer. Player graph APIs must remain filtered
to player-known relationships and factions.

## ScenarioTemplate Schema

v1.0 starter scenario templates live under `templates/` and are YAML data, not
executable scripts. They can generate world, quest, location cluster, NPC set,
faction set, mystery, or combat encounter drafts.

The stable v1.0 starter set is:

- `basic_village_world`: complete minimal world pack.
- `mystery_quest`: hidden clue and hidden quest seed.
- `faction_conflict_seed`: visible and hidden faction tension seed.
- `small_dungeon`: two-room location cluster with map visual fields.
- `merchant_and_trade`: safe merchant inventory and trade item.
- `rumor_chain`: rumor chain that avoids hidden fact text leakage.
- `NPC_goal_set`: supported NPC goal/planning examples.
- `combat_encounter_light`: light non-lethal combat encounter seed.

```yaml
id: mist_valley_mystery_seed
name: Mist Valley Mystery Seed
description: Adds a small mystery-oriented starter draft.
template_type: mystery
required_variables:
  - world_id
  - mystery_name
optional_variables:
  tone: quiet
output_files:
  - file_name: facts.yaml
    content: |
      facts:
        - id: fact_{{mystery_name}}
          text: A safe author-facing draft fact.
          visibility: discoverable
          known_by: []
          tags: [mystery]
validation_rules:
  - validate_world_pack
tags:
  - starter
```

Template variable names must be safe ids, variable values cannot contain path
traversal patterns, and output files must be whitelisted content YAML files.
Template directories reject executable/script files. Preview/render does not
write active saves or active `GameState`; applying rendered output must go
through authoring save and validation.

## Quest Graph Format

The v0.8 quest graph editor converts `quests.yaml` into a graph-shaped
authoring DTO:

- quest nodes with `id`, `title`, `description`, `initial_stage`, and
  `visibility`
- stage nodes with `id`, `title`, `description`, objectives, and
  `next_stages`
- trigger nodes with `type`, `id`, `action`, optional `objective_id`, and
  optional `next_stage`
- reward nodes where rewards are present
- edges for stage transitions and trigger-to-stage transitions
- failure/alternate-path edges where authored

The graph preview endpoint converts the graph back to `quests.yaml` and runs
draft validation. The full editor can preview, validate, and explicitly save
through authoring APIs. It does not modify active `GameState`.

Validation checks invalid `next_stage`, missing trigger references,
unreachable stage warnings, missing terminal stage warnings, and hidden quest
visibility boundaries.

## NPC Goal Authoring Fields

NPC goal authoring reads and writes the same `goals` objects embedded in
`npcs.yaml`:

- `id`
- `description`
- `priority`
- `status`
- `conditions`
- `desired_state`
- `allowed_actions`
- `forbidden_actions`

The v0.8 editor validates goal id uniqueness, known condition references,
supported planning actions, and legal desired-state references. It does not
grant NPCs unknown facts and does not call the LLM.

## Relationship / Faction Visual Fields

Faction and relationship visual authoring works over `factions.yaml`,
`relationships.yaml`, and NPC metadata. It can edit:

- faction relations and conflict values
- relationship source/target ids
- `relation_type`
- `trust`
- `fear`
- `affinity`
- `obligation`
- `known_by_player` / visibility

Hidden relationships and hidden faction conflicts may appear in authoring
graphs but must not enter player graph APIs.

## Item / Economy Editor Fields

The v0.8 Item / Economy editor covers item fields and merchant inventory:

- item `id`, `name`, `description`
- `base_price`
- `rarity`
- `tradeable`
- `portable`
- `hidden`
- `tags`
- `location_id`, `owner_id`, `container_id`
- NPC `merchant`, `shop_inventory`, `buy_price_modifier`,
  `sell_price_modifier`

Validation catches ownership conflicts, negative prices, invalid shop item ids,
and hidden shop inventory warnings. The frontend does not calculate
authoritative trade prices.

## Rumor / Crime Consequence Graph Fields

The v0.8 Rumor / Crime editor can represent consequence nodes for:

- triggers
- crimes
- witnesses
- rumors
- reputation effects
- quest triggers

Validation checks rumor `fact_id`, hidden fact text leakage in
`text_for_player`, crime type values, faction ids, quest trigger references,
duplicate consequence ids, and simple loop risks. Runtime consequences remain
rule-engine decisions.

## Import / Export Package Format

v0.7 local archives are zip files with `export_manifest.json`:

```json
{
  "export_type": "world",
  "id": "mist_valley",
  "schema_version": "0.7",
  "content_pack_version": "0.7.0",
  "mod_version": null,
  "files": ["worlds/mist_valley/manifest.yaml"]
}
```

Supported export types are `world`, `mod`, and `save`. Import rejects zip
slip/path traversal, executable files, `.env`, secret files, database files,
and logs. World imports run world validation, mod imports run mod validation,
and save imports check migration status. Save archives can contain full hidden
runtime state and must be treated as private local backup data.

v0.8 advanced packages also include `local_package_manifest.json`:

```json
{
  "package_id": "mist_valley",
  "package_type": "world",
  "version": "0.8.16",
  "engine_version_min": "0.8.0",
  "schema_version": "7",
  "content_pack_version": "0.8.0",
  "included_files": ["worlds/mist_valley/manifest.yaml"],
  "checksums": {
    "worlds/mist_valley/manifest.yaml": "sha256..."
  },
  "dependencies": [],
  "conflicts": [],
  "created_at": "2026-05-18T00:00:00Z",
  "notes": "Local package."
}
```

Supported package types are `world`, `mod`, `save_bundle`, `template_pack`,
and `scenario_suite`. Dry-run validates manifest, checksums, compatibility,
path traversal, disallowed file types, overwrite conflicts, validation, and
save migration status. Apply requires explicit confirmation and a passing
dry-run.

## Prompt Profile Fields

Prompt profiles are local LLM prompt configuration, not content-pack facts:

- `id`
- `name`
- `description`
- `provider_filter`
- `model_filter`
- `narrator_style`
- `intent_parser_prompt_variant`
- `narrator_prompt_variant`
- `memory_prompt_variant`
- `temperature_overrides`
- `max_output_tokens`
- `enabled`

Profiles cannot include API keys, hidden fact text, raw `GameState`, raw
`state_deltas`, NPC secrets, or instructions that let the LLM write state.
Provider selection remains controlled by runtime configuration and
`LLMProvider`.

## Mod Manager Fields

The Mod Manager UI displays content-only mod metadata from `mod.yaml`:

- id, name, version, author, description
- engine version min/max
- content schema version
- dependencies and optional dependencies
- conflicts
- load order hint and resolved load order
- compatible worlds
- migration notes
- validation status

The manager does not execute code, download online mods, hot-reload active
saves, or bypass validation.

## Local Provider Notes

Content packs do not configure model providers. Provider selection remains a
runtime environment concern through `LLM_PROVIDER`. `local_stub` and
`local_http` are language-layer providers only. Their output cannot directly
write content pack files, active saves, or `GameState`.

## Combat and Life Fields

Combat/life state fields used by v0.6+ include:

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

## v1.0 Quality Authoring Notes

v1.0 quality tools analyze content packs without changing them. They can report
quest reachability problems, dead ends, NPC schedule conflicts, hidden
information leak risks, economy/combat/social sanity issues, scenario
regression failures, benchmark regressions, and content coverage gaps.

Quality reports are advisory. They do not auto-repair YAML, do not write active
saves, do not call LLMs, and do not make `GameState` changes. Hidden fact text,
NPC secrets, hidden witnesses, and hidden relationship details must stay out of
normal report fields. Debug-only diagnostics must be explicitly marked.

Scenario regression files and template packs are local authoring/test data.
They must not contain API keys, `.env` contents, database paths, or executable
scripts. Imports and advanced packages must pass manifest, checksum, path, file
type, and validation checks before apply.

See `docs/QUALITY_SYSTEM.md` for the report schemas, quality gate config,
playtest scenario schema, benchmark report schema, health score categories, and
coverage report categories.

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

- The v1.0 authoring UI has multiple visual editors and quality dashboards, but
  it is still not a
  full IDE, multiplayer editor, or complex drag/drop graph system.
- No automatic YAML repair.
- No online mod registry or download support.
- No hot reload of running saves after authoring edits.
- No complex version solver for mods.
- No dynamic economy simulation.
- No LLM-powered automatic content rewriting.
- No formal desktop installer or auto-update path.
- No online import/export or cloud sync.
- No template script execution.
- No LLM automatic world/map/quest/social/economy rewriting.
- No automatic quality-report repair of content packs.
- No claim that quality scores are absolute judgments.
