# v1.0 Content Pack Schema Contract

## Purpose

This document freezes the v1.0 content-pack contract for Stable Local Studio
Edition. It defines the local YAML formats that may be loaded, validated,
edited through authoring tools, packaged into mods, used by templates, and
referenced by quality/regression tooling.

Content packs are local data. They do not execute code, do not configure LLM
providers, and do not directly mutate active `GameState`. Runtime state is
created by loading validated content into `GameState`; later changes still go
through `StateDelta` and `EventLog`.

## Version Fields

### `schema_version`

`schema_version` identifies the runtime state/content schema generation. It is
stored on saves and `GameState`. Content tools compare mod/package
`content_schema_version` with the engine schema.

v1.0 policy:

- Existing v0.9 saves must load or migrate through the migration service.
- Breaking schema changes require a deterministic migration and compatibility
  tests.
- Content validation should warn before a planned breaking removal is enforced.

### `content_pack_version`

`content_pack_version` is derived from `manifest.yaml.version` where available
and is stored in save/package metadata.

v1.0 policy:

- Version increments are required for meaningful content-pack changes.
- Save migration and authoring impact analysis must flag removed/renamed ids
  that may affect existing saves.
- Player APIs never expose hidden content just because a content version
  changed.

## Post-v1.0 Compatibility Policy

- **Optional first:** new YAML fields must be optional at introduction.
- **Validation warning before breaking:** deprecations should first produce
  validation warnings or suggestions.
- **Migration required if breaking:** removing/renaming fields, changing ids,
  or changing required semantics requires migration notes and tests.
- **No silent visibility expansion:** no schema migration may turn hidden facts,
  hidden quests, hidden relationships, hidden map edges, hidden items, NPC
  secrets, debug memory, or debug-only data into player-visible content.
- **Authoring separation:** authoring-only fields may be shown in authoring UI
  but must not enter player `visible_state`.

## Common YAML Rules

- Files use UTF-8 YAML mappings.
- World list files use a top-level list key matching the file:
  `locations`, `npcs`, `items`, `quests`, `facts`, `factions`, `rumors`,
  `relationships`.
- Entity ids must be stable strings and unique within their file unless the
  file explicitly describes derived ids.
- References must point to existing ids where validation supports them.
- Free text must not contain API keys, `.env` content, database paths, or local
  secrets.
- Hidden fact text must not be copied into player-facing fields such as public
  descriptions, `text_for_player`, or visible quest text.

## `manifest.yaml`

Required fields:

- `world_id`
- `name`
- `start_location_id`

Optional fields:

- `version` defaulting to `0.1.0`
- `description` defaulting to empty string

Visibility semantics:

- Manifest fields are authoring/runtime metadata.
- `name` and `description` may be shown in local studio world lists.
- Manifest must not contain secrets.

Validation rules:

- `world_id` should match the directory id.
- `start_location_id` must reference an existing location.

Example:

```yaml
world_id: mist_valley
name: Mist Valley
version: 1.0.0
start_location_id: village_square
description: A local sample world.
```

## `locations.yaml`

Top-level key: `locations`.

Required fields per location:

- `id`
- `name`
- `description`

Optional fields:

- `exits`: mapping of direction/label to target location id
- `visible_objects`: list of object ids initially visible in that location
- `cover_level`: integer, default `0`
- `light_level`: integer, default `5`
- `visual`: map editor metadata

Visibility semantics:

- Location names and exits can enter player `visible_state` only when the
  location/exit is known through rules.
- `visual.notes` is authoring/debug-only.
- Hidden visual nodes/edges are filtered from player map graphs.

Validation rules:

- Exit targets must exist.
- `visual.x` and `visual.y` must be finite numbers.
- Extreme visual coordinates produce validation warnings.
- Blank `region_id` values are invalid/warned by validation.

Example:

```yaml
locations:
  - id: village_square
    name: Village Square
    description: A stone square under low mist.
    exits:
      north: blacksmith
    visible_objects:
      - notice_board
    cover_level: 1
    light_level: 4
    visual:
      x: 120
      y: 80
      region_id: village
      icon: square
      color_tag: safe
      display_group: village
      tags: [hub]
      visibility: public
      notes: Authoring note only.
```

## `npcs.yaml`

Top-level key: `npcs`.

Required fields per NPC:

- `id`
- `name`
- `location_id`
- `personality`

Optional fields:

- `faction_id`
- `knowledge`
- `goals`
- `priorities`
- `constraints`
- `current_goal_id`
- `plan_state`
- `visible`
- `hidden`
- `discovered_by`
- `schedule`
- `merchant`
- `shop_inventory`
- `buy_price_modifier`
- `sell_price_modifier`

Visibility semantics:

- Hidden NPCs do not enter player `visible_npcs` until discovered.
- NPC `knowledge`, `goals`, `plan_state`, and hidden status are authoring/rule
  data, not player-visible by default.
- NPCs cannot act on facts outside their knowledge.

Validation rules:

- `location_id` must exist.
- `faction_id` must exist when provided.
- Schedule `location_id` values must exist.
- Merchant `shop_inventory` item ids must exist.
- Goal ids/statuses/actions/references must be valid.

Example:

```yaml
npcs:
  - id: harlan
    name: Harlan
    location_id: blacksmith
    personality: Terse but fair.
    faction_id: village_council
    knowledge:
      - village_square_is_misty
    goals:
      - id: keep_shop_safe
        description: Keep the forge safe.
        priority: 10
        status: active
        conditions: []
        desired_state:
          location_id: blacksmith
        allowed_actions: [guard_location, report_crime]
        forbidden_actions: []
    visible: true
    hidden: false
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

## `items.yaml`

Top-level key: `items`.

Required fields per item:

- `id`
- `name`
- exactly one placement: `location_id`, `owner_id`, or `container_id`

Optional fields:

- `description`
- `portable`
- `visible`
- `hidden`
- `discoverable`
- `discovered_by`
- `tags`
- `base_price`
- `tradeable`
- `rarity`
- `locked`
- `lock_difficulty`
- `lock_state`

Visibility semantics:

- Hidden/discoverable items do not enter player visible objects/shop data until
  rules reveal them.
- Economy fields are authoring/rule data; authoritative price calculation
  remains backend-only.

Validation rules:

- Placement is required and mutually exclusive.
- `base_price` and `lock_difficulty` are non-negative.
- Owner ids must be existing NPC ids or `player`.
- Location ids must exist.

Example:

```yaml
items:
  - id: simple_lockpick
    name: Simple Lockpick
    description: A small bent tool.
    location_id: village_square
    portable: true
    hidden: false
    tags: [tool, lockpick]
    base_price: 12
    tradeable: true
    rarity: common
```

## `quests.yaml`

Top-level key: `quests`.

Required fields per quest:

- `id`
- `title`
- `initial_stage`
- `stages`

Required fields per stage:

- `id`
- `title`

Optional quest fields:

- `description`
- `visibility`: `public` or `hidden`, default hidden
- `triggers`
- `rewards`

Optional stage fields:

- `description`
- `objectives`
- `next_stages`
- `failure_stages`
- `alternate_stages`

Visibility semantics:

- Public quests may enter player visible quest state.
- Hidden quests do not enter player UI until activated/revealed.
- Authoring graph fields are editor DTOs; `quests.yaml` remains the canonical
  content file.

Validation rules:

- `initial_stage` must exist.
- `next_stages`, `failure_stages`, and `alternate_stages` must reference
  existing stages.
- Trigger ids must reference existing facts/items/NPCs/locations/factions where
  the trigger type requires it.
- Objective references must exist in the quest.
- Unreachable stage and missing terminal-stage checks may be warnings.

Example:

```yaml
quests:
  - id: missing_tools
    title: Missing Tools
    description: Help Harlan account for missing tools.
    visibility: public
    initial_stage: ask_harlan
    stages:
      - id: ask_harlan
        title: Ask Harlan
        description: Speak with Harlan.
        objectives: [talk_to_harlan]
        next_stages: [find_tool]
      - id: find_tool
        title: Find The Tool
        objectives: [recover_tool]
        next_stages: []
    triggers:
      - type: npc_talked
        id: harlan
        action: complete_objective
        objective_id: talk_to_harlan
        next_stage: find_tool
```

## `facts.yaml`

Top-level key: `facts`.

Required fields per fact:

- `id`
- `text`
- `visibility`: `public`, `hidden`, or `discoverable`

Optional fields:

- `known_by`
- `tags`

Visibility semantics:

- `public` facts can become initial player-known facts.
- `hidden` facts are not player-visible by default.
- `discoverable` facts become visible only through rule-driven discovery.
- `known_by` can include NPC ids or `player`; hidden facts known by player
  produce validation warnings because that combination is risky.

Validation rules:

- `known_by` NPC ids must exist unless the id is `player`.
- Hidden fact text must not appear in player-facing rumor text.

Example:

```yaml
facts:
  - id: village_square_is_misty
    text: The village square is misty in the morning.
    visibility: public
    known_by: [player]
    tags: [weather]
```

## `factions.yaml`

Top-level key: `factions`.

Required fields per faction:

- `id`
- `name`

Optional fields:

- `description`
- `default_reputation`
- `known_by_player`
- `relations`
- `conflict_tags`
- `default_conflict_level`
- `default_alert_level`
- `resources`
- `tags`

Visibility semantics:

- `known_by_player=false` factions do not enter player faction UI/graphs.
- Relations and conflict tags can be authoring/debug data and should not reveal
  hidden social structure through player text.

Validation rules:

- Relation target faction ids must exist.
- Conflict/alert levels must be non-negative.

Example:

```yaml
factions:
  - id: village_council
    name: Village Council
    description: Local civic authority.
    default_reputation: 0
    known_by_player: true
    relations:
      old_road_smugglers: -30
    conflict_tags: [road_dispute]
    default_alert_level: 0
    resources:
      coin: 100
    tags: [local]
```

## `rumors.yaml`

Top-level key: `rumors`.

Required fields per rumor:

- `id`

Optional fields:

- `source_event_id`
- `fact_id`
- `text_for_player`
- `truth_status`
- `known_by_npcs`
- `known_by_factions`
- `known_by_player`
- `spread_level`
- `created_turn`
- `tags`

Visibility semantics:

- `text_for_player` is the only player-facing rumor text.
- Rumors linked to hidden facts must use safe wording and not quote the hidden
  fact text.
- Truth status should not reveal hidden truth before rules reveal it.

Validation rules:

- `fact_id` must exist when provided.
- `known_by_npcs` ids must exist.
- `known_by_factions` ids must exist.
- Hidden fact text in `text_for_player` produces warning/error depending on the
  validator path.

Example:

```yaml
rumors:
  - id: bridge_warning
    fact_id: bridge_is_unsafe
    text_for_player: People are uneasy about the bridge.
    truth_status: unknown
    known_by_npcs: [harlan]
    known_by_factions: [village_council]
    known_by_player: false
    spread_level: 1
    tags: [bridge]
```

## `relationships.yaml`

Top-level key: `relationships`.

Required fields per relationship:

- `source_id`
- `target_id`
- `relation_type`

Optional fields:

- `id`; if omitted, runtime derives `source_id:relation_type:target_id`
- `trust`
- `fear`
- `affinity`
- `obligation`
- `tags`
- `known_by_player`

Visibility semantics:

- `known_by_player=false` relationships do not enter player relationship UI or
  player graph.
- Authoring/debug graphs may show full relationship data locally.

Validation rules:

- Source and target ids must be existing NPC ids or `player`.
- Derived/explicit relationship ids must be unique.
- Numeric relationship values must stay in accepted ranges.

Example:

```yaml
relationships:
  - id: harlan_to_mira
    source_id: harlan
    target_id: mira
    relation_type: coworker
    trust: 40
    fear: 0
    affinity: 25
    obligation: 10
    tags: [village]
    known_by_player: false
```

## Scenario Templates

Template files live under `templates/` and are YAML data, not scripts.

Required fields:

- `id`
- `name`
- `description`
- `template_type`
- `required_variables`
- `optional_variables`
- `output_files`
- `validation_rules`
- `tags`

Output file fields:

- `file_name`
- `content`

Validation rules:

- Template ids and variable names must be safe ids.
- Variable values must not contain path traversal.
- Output files must be whitelisted authoring YAML files.
- Executable files in template directories are rejected.
- Preview/render does not write disk.
- Apply requires explicit confirmation and validation.

Example:

```yaml
id: basic_village_world
name: Basic Village World
description: Small local starter world.
template_type: world
required_variables:
  - world_id
  - world_name
optional_variables: {}
output_files:
  - file_name: manifest.yaml
    content: |
      world_id: "{{world_id}}"
      name: "{{world_name}}"
      start_location_id: square
validation_rules:
  - validate_world_pack
tags: [starter]
```

## Mod Manifest

File name: `mod.yaml`.

Required fields:

- `id`
- `name`
- `version`
- `engine_version_min`
- `entry_worlds`
- `content_paths`

Optional fields:

- `engine_version_max`
- `content_schema_version`
- `dependencies`
- `optional_dependencies`
- `conflicts`
- `load_order_hint`
- `compatible_worlds`
- `migration_notes`
- `author`
- `description`

Validation rules:

- Extra fields are forbidden.
- `entry_worlds` and `content_paths` must not be empty.
- Paths must stay inside the mod directory.
- Executable content is rejected.
- Entry worlds are validated with normal world validation.
- Version/dependency/conflict/load-order checks are deterministic.

Example:

```yaml
id: sample_mod
name: Sample Mod
version: 1.0.0
engine_version_min: 1.0.0
engine_version_max:
content_schema_version: "0.6"
dependencies: []
optional_dependencies: []
conflicts: []
load_order_hint: 0
compatible_worlds: [mist_valley]
entry_worlds: [mist_valley]
content_paths:
  - worlds/mist_valley
migration_notes: No migration required.
author: Local Author
description: Local content-only mod.
```

## Scenario Regression Files

Scenario regression files are local test/quality data. They must not be treated
as canonical story events.

Required fields per scenario:

- `id`
- `world_id`
- `name`
- `input_sequence`

Optional fields:

- `description`
- `initial_save`
- `expected_visible_facts`
- `forbidden_visible_facts`
- `expected_quest_states`
- `expected_inventory`
- `max_turns`
- `tags`

Validation rules:

- Scenario ids must be safe local ids.
- `world_id` must refer to a known world when run.
- Scenario authoring preview does not write disk.
- Runs must use temporary sessions/saves and mock/local providers.
- Reports must not print hidden fact text in normal output.

Example:

```yaml
scenarios:
  - id: ask_harlan_path
    world_id: mist_valley
    name: Ask Harlan Path
    input_sequence:
      - "go north"
      - "talk to harlan"
    expected_visible_facts: []
    forbidden_visible_facts:
      - sealed_letter_under_stone
    expected_quest_states:
      missing_tools: active
    max_turns: 10
    tags: [quest]
```

## Prompt Profiles

Prompt profiles are local settings data, not world facts.

Required fields:

- `id`
- `name`
- `narrator_style`
- `intent_parser_prompt_variant`
- `narrator_prompt_variant`
- `memory_prompt_variant`
- `enabled`

Optional fields:

- `description`
- `provider_filter`
- `model_filter`
- `temperature_overrides`
- `max_output_tokens`

Validation rules:

- Profiles must not contain API keys.
- Profiles must not enable hidden facts, NPC secrets, raw `GameState`, raw
  `state_deltas`, or direct state-write authority.
- Provider selection still goes through runtime settings and `LLMProvider`.

Example:

```yaml
id: calm_local_narrator
name: Calm Local Narrator
description: Restrained local prose profile.
provider_filter: [mock, local_stub, local_http]
model_filter: []
narrator_style: concise and grounded
intent_parser_prompt_variant: default
narrator_prompt_variant: default
memory_prompt_variant: default
temperature_overrides:
  narrator: 0.4
enabled: true
```

## Map Visual Fields

`locations.yaml.visual` is frozen as optional authoring/display metadata:

- `x`
- `y`
- `region_id`
- `icon`
- `color_tag`
- `display_group`
- `notes`
- `visibility`: `public`, `hidden`, `discoverable`
- `tags`

The visual map graph DTO contains:

- nodes: `id`, `name`, `location_id`, coordinates, region/tags/visibility
- edges: `source_location_id`, `target_location_id`, `edge_type`, `label`,
  `visibility`

Visual fields do not affect movement rules.

## Quest Graph Fields

The graph editor DTO is an authoring view over `quests.yaml`. The YAML file
remains canonical.

Frozen graph concepts:

- quest nodes,
- stage nodes,
- objective nodes,
- trigger nodes,
- reward nodes,
- next/failure/alternate edges,
- visibility.

Graph preview/validate does not write disk. Save converts back to YAML and
runs world validation.

## Economy Fields

Frozen item fields:

- `base_price`
- `tradeable`
- `rarity`

Frozen merchant fields on NPCs:

- `merchant`
- `shop_inventory`
- `buy_price_modifier`
- `sell_price_modifier`

Authoritative prices are calculated by backend economy rules, not frontend
display code.

## Crime / Rumor Consequence Fields

v1.0 freezes rumor/consequence authoring as local structured content:

- rumor `fact_id`
- rumor `text_for_player`
- `truth_status`
- `known_by_npcs`
- `known_by_factions`
- `known_by_player`
- `spread_level`
- consequence graph nodes for trigger, crime, witness, rumor, reputation
  effect, and quest trigger where represented by authoring DTOs

Runtime crime/witness/social consequences remain deterministic rule-engine
behavior and are not decided by the LLM.

## Player / Authoring / Debug Visibility Matrix

| Data Type | Player API | Authoring UI/API | Debug API |
| --- | --- | --- | --- |
| Public fact text | yes when known | yes | yes |
| Hidden fact text | no | yes | yes when debug enabled |
| NPC secrets | no | yes | yes when debug enabled |
| Hidden witness | no | authoring/debug only | yes when debug enabled |
| Hidden relationship | no | yes | yes when debug enabled |
| Hidden map edge | no | yes | yes when debug enabled |
| Hidden quest | no until revealed | yes | yes when debug enabled |
| Hidden shop item | no until revealed | yes | yes when debug enabled |
| `visual.notes` | no | yes | yes when debug enabled |
| Raw `state_deltas` | no | no | yes when debug enabled |

## v1.0 Freeze Acceptance

The content schema is accepted for v1.0 only when:

- `validate_world` passes for `mist_valley`.
- Starter templates render and validate.
- Invalid schema fixtures are rejected.
- Hidden fact leakage fixtures produce warnings/errors.
- Authoring preview/dry-run does not write disk.
- Visual editor save flows run validation.
- Mods remain content-only and cannot execute code.
- Import/export packages reject zip slip, executables, `.env`, secrets, and
  checksum mismatches.
- Full `python -m pytest` passes.
