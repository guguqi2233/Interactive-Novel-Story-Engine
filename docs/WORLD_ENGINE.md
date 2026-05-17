# World Engine

This document describes the local world engine as of v0.5. The engine is the
only source of truth for world state, rules, consequences, persistence, and
visibility. The LLM layer may parse intent, render narration, and summarize
memory, but it does not decide rule outcomes or mutate `GameState`.

## Core Boundary

- `GameState` is authoritative.
- All state changes are represented as `StateDelta` entries.
- Player actions and system ticks are recorded as `Event` records.
- Rule systems never call the LLM.
- Narration receives only player-visible facts and narrator-safe memory.
- Hidden facts, NPC secrets, hidden witnesses, debug data, and hidden memory do
  not enter player API responses or narrator prompts.

## Main Flow

1. The API or CLI receives player input.
2. `IntentParser` turns text into a structured intent through `LLMProvider`.
3. `ActionDispatcher` routes the intent to a deterministic action handler.
4. The handler returns `ActionResult` with `state_deltas`.
5. `apply_delta` updates `GameState`.
6. `EventLog` records the player event.
7. `WorldTick` runs deterministic system rules and records system events.
8. `Narrator` renders the visible result as text.
9. APIs return `narrative_text`, suggested actions, and structured
   `visible_state`.

## GameState Areas

The current state model includes:

- Player: location, inventory ownership through item state, currency, health,
  and stealth-related fields.
- Locations: exits, visible objects, cover/light fields, and metadata.
- NPCs: location, mood, relationship to player, knowledge, secrets, life state,
  schedule, goals, plan state, merchant data, faction id, alertness, and
  suspicion.
- Items: location/owner/container ownership, portability, hidden/discovered
  state, tags, price, rarity, and trade flags.
- Facts: public, hidden, or discoverable structured facts with known-by data.
- Quests: stages, objectives, visibility, triggers, and runtime state.
- Social systems: factions, reputation, rumors, crimes, witnesses,
  relationships, faction conflict, social flags, and consequence dedupe data.
- Combat and life state: combatants, hp, condition, stance, and status effects.
- Memory: memory records are persisted separately and are not authoritative
  facts.

Old save JSON is loaded through Pydantic defaults and compatibility-friendly
model fields. Missing v0.4/v0.5 social or memory fields should default rather
than crash.

## StateDelta Rules

`StateDelta` supports structured operations such as `set`, `inc`, `add`, and
`remove` over dot paths. Core paths used by v0.5 include:

- `player.location_id`
- `player.currency`
- `items.{item_id}.owner_id`
- `items.{item_id}.location_id`
- `npcs.{npc_id}.location_id`
- `npcs.{npc_id}.goals`
- `npcs.{npc_id}.plan_state`
- `relationships.{relationship_id}.trust`
- `factions.{faction_id}.reputation`
- `factions.{faction_id}.alert_level`
- `rumors.{rumor_id}.known_by_npcs`
- `crimes.{crime_id}.status`
- `witnesses.{witness_id}`
- `combats.{combat_id}.combatants.{actor_id}.hp`
- `quests.{quest_id}.current_stage`

Rules may prepare deltas, but they must not directly mutate `GameState`.

## Event Log

Every player action and system consequence is represented as an `Event`.
Events include:

- `event_id`
- `turn`
- `actor_id`
- `action_type`
- `target_id`
- `input_text`
- `result`
- `state_deltas`
- `visible_to_player`
- `narrative_text`
- `created_at`

Debug timeline APIs expose events only when debug mode is enabled. Player APIs
do not expose raw `state_deltas`.

## Content Packs

World content lives under `worlds/{world_id}`. The loader validates YAML
schemas and reference integrity before creating runtime state. Current content
files include:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`

The engine must not hardcode content from `mist_valley` or any other world.

## Visibility

Player-visible state is produced by explicit visibility rules. It may include:

- current location
- formatted game time
- inventory
- visible objects
- visible NPCs
- known facts
- visible quests
- known factions and reputation bands
- known rumors
- known crimes or public consequences
- known relationships
- visible faction conflicts

It must not include:

- hidden facts not discovered by the player
- hidden objects or NPCs not discovered by the player
- NPC secrets
- hidden witnesses
- hidden faction details
- hidden/debug memory
- raw event `state_deltas`
- API keys, environment variables, or local paths

Known v0.5 limitation: visible faction conflict summaries include
`conflict_tags` for player-known factions. Authors should avoid using those
tags for secret-only content until a stricter public-label field is added.

## Time, Schedule, and World Tick

Game time is a simple day plus minutes-of-day structure. Actions advance time
through deltas. After player action resolution, `WorldTick` runs deterministic
system rules. The intended order is:

1. Time advancement from the action result.
2. NPC schedule resolution.
3. Quest triggers.
4. Crime witness/report handling.
5. Rumor propagation.
6. Reputation and faction consequences.
7. NPC reactions.
8. NPC planning.
9. Delayed consequences.

System changes are recorded as system events. Hidden system events may affect
the world, but they do not become narration unless later visible through normal
rules.

## NPC Schedule

NPC schedules are loaded from `npcs.yaml`. A schedule entry contains:

- `time_of_day`
- `location_id`
- `activity`

The resolver moves or updates NPCs using `StateDelta`. Dead or incapacitated
NPCs do not follow schedules.

## Search

`search` is a deterministic action for discovering objects or facts near the
current location, a visible object, or a visible NPC. Success can reveal
discoverable objects/facts by updating discovered state through `StateDelta`.
Failure consumes time but does not leak hidden content.

## Inventory and Economy

Inventory is derived from item ownership in `GameState`, not from frontend
state. Items may have:

- `location_id`
- `owner_id`
- `container_id`
- `portable`
- `hidden`
- `discovered_by`
- `base_price`
- `tradeable`
- `rarity`
- `tags`

Only one ownership location should be active at a time. Pickup, drop, use,
buy, and sell actions produce `StateDelta` entries and events. Trade prices are
rule-based and may consider merchant modifiers and reputation bands. The LLM
does not price items.

v0.5 does not implement a dynamic supply/demand economy, auctions, equipment
slots, or full stolen-goods simulation.

## Lockpick and Sneak

`lockpick` supports locked doors and containers with structured lock state.
Success, partial success, failure, and invalid results are rule outcomes.
Failure can leave traces or create social consequences.

`sneak` supports movement or approach attempts influenced by cover, light,
NPC alertness, and player stealth fields. Hidden observers may affect the rule
result, but their identity is not exposed to the narrator or player API.

## Quest State Machine

Quests are loaded from `quests.yaml` with stages, objectives, visibility, and
triggers. Triggers may reference facts, items, NPC conversations, locations,
reputation, crimes, or other structured state. Quest state changes go through
`StateDelta` and are visible only when the quest is known or active.

## Social Systems

### Factions and Reputation

`factions.yaml` defines factions, default player reputation, visibility, tags,
and v0.5 conflict metadata. Reputation bands include hostile, suspicious,
neutral, friendly, and trusted. Reputation changes are rule-driven and are not
decided by the LLM.

### Rumors

Rumors are structured records with known-by NPCs/factions, player visibility,
truth status, spread level, and safe player-facing text. A rumor linked to a
hidden fact must not reveal the hidden fact text unless the fact is legitimately
known to the player.

### Crime and Witnesses

Crime records and witness records represent theft, assault, murder,
lockpicking, trespass, vandalism, and reserved crime types. Witness detection
uses location, visibility, life state, light/cover, and sneak/combat context.
Hidden witnesses may affect rules without being exposed to player APIs.

### NPC Reactions

NPC reactions include suspicion changes, refusing talk, fleeing, spreading
rumors, calling for help, friendliness, and hostility. Reactions require
structured inputs such as known crimes, known rumors, relationship state,
faction reputation, combat status, or quest state. Dead or incapacitated NPCs
do not react.

### Faction Conflict

Faction conflict tracks faction-to-faction relations, alert level, conflict
level, resources, and conflict tags. Incidents can come from crimes, public
combat, rumors, quest stages, or reputation bands. Conflict changes are
deduped by source/consequence ids where supported and are visible only for
player-known factions/conflicts.

v0.5 does not simulate armies, diplomacy AI, territorial war, or complex
conflict escalation.

## Combat and Life State

Combat is lightweight and rules-first. Actions include:

- `attack`
- `defend`
- `flee`

Damage, hit/miss, hp, condition, stance, incapacitation, and death are decided
by deterministic rules. Public assault or killing can feed crime, witness,
rumor, reputation, quest, and reaction systems.

Life state prevents contradictions:

- Dead NPCs do not move by schedule.
- Dead NPCs do not talk.
- Dead NPCs do not spread rumors.
- Dead NPCs do not become new witnesses.
- Incapacitated NPCs have restricted action.

## Memory

Memory is not authoritative state. It summarizes or indexes events for
retrieval, but it does not replace `GameState`, facts, quests, or event logs.

### MemoryStore Backends

v0.5 supports:

- `InMemoryMemoryStore`
- `SQLiteMemoryStore`
- `LocalVectorMemoryStore` / optional vector-style interface with deterministic
  substring and metadata fallback

Search supports tags, entities, facts, turn ranges, substring, recency, and
semantic query only when a backend supports it. No external vector database is
required.

### MemoryContextBuilder

`MemoryContextBuilder` builds safe memory context for narrator and NPC dialogue.
It filters by:

- memory visibility
- player-known facts
- NPC knowledge
- location/entity/fact relevance
- recent turns
- importance

`hidden` and `debug_only` memories do not enter narrator context. NPC dialogue
does not receive memories tied to facts or rumors the NPC does not know.

## Procedural Side Quest Drafts

The side quest generator creates `QuestDraft` candidates. It has:

- a rule-based mode that does not call the LLM
- an optional LLM-assisted mode through `LLMProvider`

Generated quests are drafts, not runtime quest state. They do not modify
`GameState`, active saves, or `quests.yaml`. A creator must explicitly review
and save content through authoring tools, and validation must pass before the
pack is treated as valid.

LLM-assisted drafts must be schema-validated and may only reference existing
content unless new content is marked as proposed.

## Authoring API and Validation UX

The local authoring API is controlled by `ENABLE_AUTHORING_API`. It is intended
for local development only. It can list worlds, read whitelisted YAML files,
write whitelisted YAML after YAML parsing, create world pack skeletons, and run
structured validation.

Allowed world files are:

- `manifest.yaml`
- `locations.yaml`
- `npcs.yaml`
- `items.yaml`
- `quests.yaml`
- `facts.yaml`
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`

The API rejects path traversal and non-whitelisted file names. It must not read
`.env`, database files, logs, source files, or arbitrary local paths. It must
not mutate active session `GameState`.

Validation reports contain structured `errors`, `warnings`, and `suggestions`
with file, path, code, message, severity, and optional reference ids. CLI
validation still returns a non-zero exit code when errors are present.

## Plugin / Mod Packaging

v0.5 includes a content-only mod packaging layer. A mod manifest can describe:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `dependencies`
- `conflicts`
- `entry_worlds`
- `content_paths`
- `author`
- `description`

Mods may contain YAML content packs only. The loader does not execute Python,
JavaScript, shell scripts, or arbitrary code. It rejects paths outside the mod
directory and validates entry worlds through the same content validation path.

Known v0.5 limitation: some invalid mod manifest errors may include local file
paths in diagnostics. Keep mod validation local until path sanitization is
tightened further.

## Multi-world Save Browser

Save listing supports world filtering, updated-time ordering, deletion, and
safe summaries. A save summary may include:

- save id
- world id
- world name
- turn
- current location name
- formatted time
- created and updated timestamps
- optional player summary

Save summaries must not include raw `GameState`, hidden facts, raw
`state_deltas`, debug memory, or API keys.

## Debug Timeline

Debug timeline APIs are controlled by `ENABLE_DEBUG_API` and are for local
development only. They expose event timelines and `state_deltas` for debugging.
This data must remain separated from player APIs and narrator prompts.

## Current Limits

- No account system, cloud sync, or remote publishing.
- No graphical world editor beyond a textarea authoring UI.
- No automatic YAML repair.
- No arbitrary mod code execution.
- No large-scale social simulation, diplomacy AI, or war simulation.
- No external vector database requirement.
- NPC planning is limited to deterministic candidate actions.
- Procedural side quests are drafts only.
- Memory retrieval is context support, not canonical truth.
