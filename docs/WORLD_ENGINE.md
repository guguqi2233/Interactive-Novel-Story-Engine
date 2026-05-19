# World Engine

This document describes the local world engine as of v1.1 Roleplay Immersion
Layer on top of v1.0 Stable Local Studio Edition. The engine is the
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

Old save JSON is loaded through Pydantic defaults, compatibility-friendly
model fields, and the v0.6+ save migration system. Missing v0.3-v0.6 fields
should default or migrate rather than crash.

## StateDelta Rules

`StateDelta` supports structured operations such as `set`, `inc`, `add`, and
`remove` over dot paths. Core paths used by the current engine include:

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

Known limitation: visible faction conflict summaries include
`conflict_tags` for player-known factions. Authors should avoid using those
tags for secret-only content until a stricter public-label field is added.

Known v0.7 hardening note: authoring/debug views may intentionally show full
local content, raw debug events, or raw deltas. They must stay visually and API
separated from player views and narrator payloads.

Known v0.8 authoring note: visual editors are authoring tools over content-pack
YAML. They do not change active session `GameState`, and saved edits must pass
preview/validation/explicit save flows.

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

The current engine does not implement a dynamic supply/demand economy, auctions, equipment
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
and conflict metadata. Reputation bands include hostile, suspicious,
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

The current engine does not simulate armies, diplomacy AI, territorial war, or complex
conflict escalation.

## Combat and Life State

Combat is lightweight and rules-first. Actions include:

- `attack`
- `defend`
- `flee`

Damage, hit/miss, hp, condition, stance, incapacitation, and death are decided
by deterministic rules. Public assault or killing can feed crime, witness,
rumor, reputation, quest, and reaction systems.

v0.6+ includes a small combat expansion:

- stances: `aggressive`, `defensive`, `cautious`, `fleeing`
- status effects: `guarded`, `stunned`, `bleeding`
- defend grants a guarded/defensive consequence through `StateDelta`
- guarded can reduce damage and be consumed
- stunned actors cannot act
- heavy damage can mark bleeding for future consequences
- flee has deterministic risk and failure consequences
- non-lethal attack can incapacitate without directly killing
- `visible_state.active_combat` exposes only player-visible combatants

This is not tactical combat. There is no grid movement, equipment system,
magic combat, or multi-round AI combat planner.

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

The current engine supports:

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

## Studio Home Dashboard

v0.7 adds a local Studio Home panel backed by `GET /studio/status`. It is a
safe summary surface for the local project. It can show:

- engine version and backend health
- available worlds count
- recent safe save summaries
- authoring/debug/performance API status
- current `LLM_PROVIDER` and local provider status labels
- recent validation and playtest summaries when available
- shortcuts to Play, Authoring, Save Browser, Migration, Mod Manager, Graphs,
  Narrative Evals, Performance, Playtesting, and Settings

Studio Home is not a debug dump. It must not return API keys, raw environment
variables, raw `GameState`, raw `state_deltas`, hidden facts, NPC secrets, or
debug memory.

## Settings and Local Privacy Panel

v0.7 adds `GET /studio/config-summary` and a Settings / Local Privacy panel.
The endpoint returns safe booleans and labels for:

- `LLM_PROVIDER`
- provider configured/status text
- whether the configured provider may receive prompts
- authoring/debug/performance/playtest/eval API status
- whether a database is configured
- a redacted database hint
- whether an API key is configured, without returning the key

The panel explains that saves, `GameState`, memory records, content packs, and
mods stay local; only configured LLM providers may receive prompts; API keys
are not exposed to the frontend; and local mods are validated as content-only
packages.

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

## Authoring Diff, Preview, and Dry Run

v0.6+ adds local authoring dry-run support:

- `preview-file-change` parses proposed YAML, validates a draft in a temporary
  copy, returns normalized YAML when possible, and reports a diff summary.
- `validate-draft` validates proposed file content without writing it.
- `impact-analysis` reports removed ids, renamed-id guesses, changed exits,
  and whether existing saves may require review.

These APIs do not modify active `GameState`, active sessions, or saves. They
are local authoring tools only and must stay behind `ENABLE_AUTHORING_API`.

## Visual Map Data Model and Editor

v0.8 adds a map visualization layer for `locations.yaml`. Location definitions
may include an optional `visual` field:

- `x`
- `y`
- `region_id`
- `icon`
- `color_tag`
- `display_group`
- `tags`
- `visibility`
- `notes` for authoring/debug use only

The backend exposes authoring map graph data as `MapVisualGraph` with
`MapVisualNode` and `MapVisualEdge`. Edges are derived from location exits.
When visual fields are missing, the graph builder supplies deterministic
authoring defaults without writing files.

Authoring map APIs are behind `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds/{world_id}/map`
- `POST /authoring/worlds/{world_id}/map/preview`
- `POST /authoring/worlds/{world_id}/map/validate`
- `PUT /authoring/worlds/{world_id}/map`

`PUT` converts graph edits back to `locations.yaml` and runs world validation
before saving. Validation errors reject the save. Player-visible map graphs
filter hidden nodes and hidden edges; authoring maps may show complete local
content in authoring-only panels.

The frontend Map Editor provides a simple SVG/form editor for node positions,
labels, regions, tags, and exit edges. It does not implement automatic layout,
does not call the LLM, and does not change player movement rules.

## Scenario Template System and Local Template Browser

v0.7 added local `ScenarioTemplate` support for reusable authoring drafts.
Templates live under `templates/` and are YAML data, not executable scripts.
v0.8 adds a Local Template Browser that can list, inspect, preview, validate,
and apply templates through authoring-gated APIs.

`ScenarioTemplate` fields:

- `id`
- `name`
- `description`
- `template_type`: `world`, `quest`, `location_cluster`, `npc_set`,
  `faction_set`, `mystery`, or `combat_encounter`
- `required_variables`
- `optional_variables`
- `output_files`
- `validation_rules`
- `tags`

The template renderer supports:

- `list_templates`
- `preview_template`
- `render_template`
- `validate_rendered_content`

Rendering performs simple `{{variable}}` substitution. Variable names and
values are checked for unsafe path traversal patterns, and output files must be
normal authoring YAML files. Preview and render do not write disk, do not
modify active `GameState`, and do not call the LLM.

Rendered world templates are validated in a temporary world root with
`validate_world_pack`. Non-world templates can be validated against a temporary
copy of a target world. Applying rendered content is intentionally separate:
creators must use the authoring API or another explicit save step, and the
validator remains the gate.

Template APIs:

- `GET /authoring/templates`
- `GET /authoring/templates/{template_id}`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/templates/{template_id}/apply`

Templates cannot execute scripts, cannot write active saves, and cannot bypass
validation.

## Import / Export Workflow and Advanced Packages

v0.7 added local authoring-gated archive import/export for worlds, mods, and
saves. v0.8 extends this into local packages with manifests, checksums,
compatibility checks, dry-run, and explicit apply. Archives are zip files
represented by the API as base64 payloads.

Import/export endpoints:

- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`
- `GET /authoring/export/templates`
- `GET /authoring/export/scenarios`
- `POST /authoring/import/packages/dry-run`
- `POST /authoring/import/packages/apply`

Legacy archive manifests are stored in `export_manifest.json` and include:

- `export_type`: `world`, `mod`, or `save`
- `id`
- `schema_version`
- optional content/mod version fields
- included file list

The importer rejects zip slip/path traversal, executable files, `.env`,
secret files, local database files, and logs. World imports run world
validation, mod imports run mod validation, and save imports check migration
status. Import/export does not call the LLM and does not modify active session
`GameState`.

v0.8 package archives also include `local_package_manifest.json` with:

- `package_id`
- `package_type`: `world`, `mod`, `save_bundle`, `template_pack`, or
  `scenario_suite`
- `version`
- `engine_version_min`
- `schema_version`
- `content_pack_version`
- `included_files`
- `checksums`
- `dependencies`
- `conflicts`
- `created_at`
- `notes`

Dry-run validates manifests, file paths, disallowed file types, checksums,
compatibility, overwrite conflicts, world/mod validation, and save migration
status. Apply requires explicit confirmation and a passing dry-run.

Save export can include full hidden save state by design. It is therefore a
local authoring/backup workflow only and must stay behind
`ENABLE_AUTHORING_API`.

## Visual Quest Graph Editor

v0.7 added an initial authoring-only quest graph layer for `quests.yaml`. v0.8
expands it into a fuller visual quest editor. It parses quests into:

- quest nodes
- stage nodes
- objective nodes
- trigger nodes
- reward nodes
- `next_stages` edges
- trigger-to-stage edges
- failure/alternate path edges where content provides them

The UI supports viewing and editing quest title/description, stage
title/description, objectives, triggers, `next_stages`, rewards, and visibility
fields. The frontend sends the edited graph to backend preview/validate/save
endpoints, which convert it back to `quests.yaml` and run draft validation.
Saving still uses the normal authoring validation path, so validation remains
the gate and active `GameState` is not modified.

Quest graph APIs are local authoring endpoints behind `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`
- `POST /authoring/worlds/{world_id}/quests/graph/validate`
- `PUT /authoring/worlds/{world_id}/quests/graph`

Hidden quests can appear in the authoring UI because authoring is a local
creator tool, but they must not enter player `visible_state`.

Validation catches invalid `next_stage` references and missing trigger
references. Unreachable stages and missing terminal stages are warnings.

## NPC Goal Editor

v0.8 adds authoring support for NPC goals in `npcs.yaml`. The editor reads,
previews, validates, and saves structured goal data. The backend represents
the graph as NPC goal authoring DTOs and validates:

- unique goal ids per NPC
- valid priority values
- valid goal status
- condition references to facts/items/NPCs/locations/quests
- supported planning actions in `allowed_actions`
- legal `forbidden_actions`
- safe `desired_state` references

APIs:

- `GET /authoring/worlds/{world_id}/npcs/goals`
- `POST /authoring/worlds/{world_id}/npcs/goals/preview`
- `POST /authoring/worlds/{world_id}/npcs/goals/validate`
- `PUT /authoring/worlds/{world_id}/npcs/goals`

NPC goals remain deterministic planning inputs. The editor does not call the
LLM, does not grant NPCs unknown facts, and does not modify active runtime
state.

## Faction / Relationship Visual Editor

v0.8 adds authoring graph support for factions and NPC relationships. It reads
`factions.yaml`, `relationships.yaml`, and related NPC metadata, then exposes
authoring-only graph nodes and edges for:

- faction nodes
- NPC nodes
- relationship edges
- conflict/relation edges
- trust, fear, affinity, obligation, visibility, and conflict values

APIs:

- `GET /authoring/worlds/{world_id}/social/graph`
- `POST /authoring/worlds/{world_id}/social/graph/preview`
- `POST /authoring/worlds/{world_id}/social/graph/validate`
- `PUT /authoring/worlds/{world_id}/social/graph`

Player graph endpoints remain filtered separately. Hidden relationships and
hidden faction conflicts may appear in authoring views but must not enter
player graph or player visible state.

## Item / Economy Editor

v0.8 adds an Item / Economy authoring editor over `items.yaml` and merchant
fields in `npcs.yaml`. It supports item ids, names, descriptions, ownership,
visibility, tags, base prices, rarity, trade flags, portability, and merchant
shop inventory.

APIs:

- `GET /authoring/worlds/{world_id}/economy`
- `POST /authoring/worlds/{world_id}/economy/preview`
- `POST /authoring/worlds/{world_id}/economy/validate`
- `PUT /authoring/worlds/{world_id}/economy`

Validation checks item id uniqueness, ownership conflicts, non-negative
prices, valid trade flags, valid shop inventory item ids, and hidden shop item
warnings. Trade authority remains in backend economy rules; the frontend does
not calculate authoritative prices.

## Rumor / Crime Consequence Editor

v0.8 adds authoring support for social consequence graphs around rumors,
crimes, witnesses, reputation effects, and quest triggers. The editor reads
`rumors.yaml`, facts, factions, quests, and related consequence content where
available.

APIs:

- `GET /authoring/worlds/{world_id}/rumor-crime`
- `POST /authoring/worlds/{world_id}/rumor-crime/preview`
- `POST /authoring/worlds/{world_id}/rumor-crime/validate`
- `PUT /authoring/worlds/{world_id}/rumor-crime`

Validation checks rumor fact references, hidden fact text leakage in
player-facing rumor text, valid crime types, faction ids, quest trigger
references, duplicate consequence ids, and simple consequence-loop risks.
Runtime crime and social consequences remain rule-engine decisions.

## Visual Validation Graph

v0.8 can turn a structured validation report into a local authoring
`ValidationGraph`. It includes file, entity, reference, schema, and issue
nodes, with edges such as contains, references, missing_reference,
invalid_value, visibility_risk, and cycle.

APIs:

- `GET /authoring/worlds/{world_id}/validation-graph`
- `POST /authoring/worlds/{world_id}/validation-graph`

The graph is an authoring diagnostic. It does not auto-fix YAML, does not call
the LLM, and should avoid local absolute paths or sensitive configuration.

## Timeline Replay Visualizer

v0.8 adds debug-only timeline replay data for sessions and saves:

- `GET /debug/sessions/{session_id}/timeline`
- `GET /debug/saves/{save_id}/timeline`
- `POST /debug/saves/{save_id}/replay-dry-run`

Timeline replay groups events by turn and can include event kind, actor,
action type, result, visible-to-player flag, raw `state_deltas`, visible
changes, and replay dry-run summaries. Replay dry-run applies event deltas to
a fresh loaded initial state and reports checksums and invariant violations
without writing the database.

This is debug data only, gated by `ENABLE_DEBUG_API`. It must never enter
player APIs or narrator prompts.

## World Branch / Diff System

v0.8 adds lightweight local world branching and structured diff. Branches are
copies of whitelisted world YAML under `worlds/.branches/{world_id}/{branch}`.
They do not copy `.env`, databases, logs, caches, or arbitrary files.

APIs:

- `GET /authoring/worlds/{world_id}/branches`
- `POST /authoring/worlds/{world_id}/branches`
- `GET /authoring/worlds/{world_id}/diff?other=...`
- `POST /authoring/worlds/{world_id}/diff-draft`

`WorldDiff` reports added, removed, changed, and potential renamed entities,
broken references, migration impacts, and visibility risks. Diff is
authoring-only and deterministic; it does not modify active `GameState`, does
not migrate active saves, and does not call the LLM.

## Scenario Regression Suite

v0.8 adds scenario regression cases and run reports for local regression
testing. A case contains a world id, input sequence, expected visible facts,
forbidden visible facts, expected quest states, expected inventory, max turns,
and tags.

APIs:

- `GET /scenarios/regression`
- `POST /scenarios/regression/run`
- `GET /scenarios/regression/{run_id}`

The API is gated by playtest/eval/debug configuration. Runs use mock/local
providers through the normal game loop or test harness, do not modify real
user saves, and redact hidden fact text from reports.

## Prompt Profile Manager

v0.8 documents and exposes prompt profile management for local provider/model
preferences. `PromptProfile` can configure provider/model filters, narrator
style, prompt variants, temperature overrides, and optional output token
limits.

Prompt profiles cannot widen LLM authority. Validation rejects profiles that
try to request hidden facts, NPC secrets, raw `GameState`, raw `state_deltas`,
or direct `GameState` writes. Profiles may adjust style and variants only;
they do not change visible facts, narrator-safe memory filtering, provider
factory boundaries, or rule outcomes.

## Save Migration System

v0.6+ formalizes save migration. Save metadata includes engine/schema/content
version fields and migration history. `GameState` also carries a
`schema_version`.

Migration APIs and CLI support:

- list available migrations
- migration status
- dry-run migration
- apply migration with backup

Migration is deterministic, does not call the LLM, does not drop `EventLog`,
and must not change hidden/debug visibility classifications. Failed migration
rolls back rather than overwriting the original save.

## Save Migration UI

v0.7 exposes migration status, dry-run, apply, and history in the Save Browser.
The UI uses existing migration APIs and does not return or display raw hidden
save payloads. Applying migration requires confirmation. Dry-run is clearly
marked as non-writing.

## Visual Relationship and Faction Graphs

v0.6+ adds graph response schemas and APIs for relationship/faction inspection:

- player graph endpoints return player-visible nodes/edges only
- debug graph endpoints return fuller graph data only when debug API is enabled
- graph generation is deterministic and does not infer hidden relationships

The frontend renders these as lightweight lists/SVG summaries. Debug graphs
must remain in the debug panel.

## Mod Manager UI

v0.7 adds a local Mod Manager panel backed by authoring-gated mod endpoints.
It can list discovered content-only mods, show manifest fields, validate a
mod, display dependency/conflict/version status, show deterministic load order,
and display migration notes. It does not enable online downloads, does not
execute scripts, and does not hot-reload active saves.

## Automated Playtesting Agents

v0.6+ adds local playtesting agents:

- `random_valid_action_agent`
- `explore_agent`
- `quest_following_agent`
- `stress_agent`

Agents receive `VisibleStateResponse` and return player input text. The runner
sends that text through `GameLoop`, records events, checks invariants, and can
exercise save/load. Agents do not directly mutate `GameState` and do not call
real LLM APIs.

## Automated Playtesting Dashboard

v0.7 adds playtest APIs and a local dashboard:

- `GET /playtests/recent`
- `POST /playtests/run`
- `GET /playtests/{run_id}`

The API is controlled by `ENABLE_PLAYTEST_API` or debug mode. Reports include
turns run, actions taken, errors, invariant violations, visibility leak
summaries, save/load failures, and safe final state summaries. Reports are
studio/debug artifacts and must not enter player narration.

## Narrative Quality Evals

Narrative quality evals are deterministic test/eval utilities. They check
whether a `NarrativeResult` contradicts the `ActionResult`, invents key content,
leaks hidden facts/witnesses, becomes too long, omits visible consequences, or
suggests illegal actions. They do not use an external LLM judge.

## Narrative Quality Dashboard

v0.7 adds local eval report APIs and a dashboard:

- `GET /evals/narrative/recent`
- `POST /evals/narrative/run`
- `GET /evals/narrative/{run_id}`

The current routes are debug-gated. Reports include run ids, timestamps, pass
counts, failure reasons, categories, and safe case summaries. They do not
modify `GameState`, do not call real model APIs, and must not display hidden
fixture text in ordinary UI.

## Performance Instrumentation

v0.6+ adds local performance samples for game loop stages, save/load,
memory search, and authoring validation. Samples are in-memory, controlled by
`ENABLE_PERF_LOGGING`, and exposed only through debug performance APIs gated by
`ENABLE_DEBUG_API`.

Performance data must not include prompt text, API keys, hidden fact text, raw
`GameState`, or raw `state_deltas`. Performance work must never bypass
`StateDelta`, `EventLog`, visibility, schema validation, or rule correctness.

## Performance Dashboard

v0.7 exposes the local performance samples in a dashboard. It shows recent
samples and summaries for game loop, intent parsing, action resolution, world
tick, narrator, save/load, memory search, and authoring validation when data is
available. The dashboard is debug-gated, local-only, and must not display
prompt text, hidden content, API keys, raw `GameState`, or raw
`state_deltas`.

## Plugin / Mod Packaging

The engine includes a content-only mod packaging layer. A v0.6+ mod manifest can
describe:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `content_schema_version`
- `dependencies`
- `optional_dependencies`
- `conflicts`
- `load_order_hint`
- `compatible_worlds`
- `migration_notes`
- `entry_worlds`
- `content_paths`
- `author`
- `description`

Mods may contain YAML content packs only. The loader does not execute Python,
JavaScript, shell scripts, or arbitrary code. It rejects paths outside the mod
directory and validates entry worlds through the same content validation path.

Dependency, conflict, engine-version, content-schema, and load-order checks are
simple and deterministic in v0.7. There is no online download, SAT solver, hot
reload of active saves, or arbitrary script execution.

Known limitation: some invalid mod manifest errors may include local file
paths in diagnostics. Keep mod validation local until path sanitization is
tightened further.

## Desktop Packaging Prototype

v1.0 keeps desktop packaging as a local launcher prototype and hardens the
launcher scripts. The Windows and shell scripts check dependencies, ports,
`DATABASE_URL`, `.env` guidance,
start the FastAPI backend and Vite frontend or built preview, print safe local
status, run `/health` and `/studio/status` checks, and open the browser. This
is not a formal installer, does not sign code, does not auto-update, does not
sync to cloud, and does not embed `.env` or API keys into frontend assets.

## Local Model Provider Full Integration

v1.0 keeps the configurable local provider integration:

- `local_stub`: deterministic test/offline provider
- `local_http`: OpenAI-compatible local HTTP chat endpoint integration

`local_http` uses `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`,
`LOCAL_LLM_TIMEOUT_SECONDS`, and `LOCAL_LLM_JSON_MODE`. It still goes through
`LLMProvider`; outputs are schema-validated for JSON calls and have no new
authority. Local model output cannot directly modify `GameState`.

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

## v1.0 Quality And Automated Playtesting Layer

v1.0 stabilizes the local quality-analysis layer on top of the visual authoring
studio. These tools inspect content packs, event timelines, playtest reports,
scenario regression output, save/migration behavior, and performance samples.
They produce safe reports for authors; they do not modify active `GameState`,
active saves, or world-pack YAML unless a separate authoring save flow is used.

The common report format is `WorldQualityReport`:

- `run_id`, `world_id`, `created_at`
- engine, schema, and content-pack version metadata
- `categories`
- `metrics` as structured `QualityMetric` records
- `issues` as structured `QualityIssue` records
- `summary`
- `recommended_actions`

`QualityIssue` supports `info`, `warning`, `error`, and `blocker` severities.
Normal reports use `safe_details`; hidden or sensitive diagnostic material must
stay in `hidden_details_debug_only` and must only be exposed through explicitly
debug/local-only surfaces. Normal quality reports must not include hidden fact
text, NPC secrets, hidden witnesses, raw `GameState`, raw `state_deltas`, API
keys, raw environment variables, or local sensitive paths.

Current v1.0 quality modules include:

- Automated Playtesting Scenario Expansion: deterministic scenarios for
  exploration, quest paths, combat, stealth, economy, crime/social behavior,
  save/load, migration, and hidden-leak probes.
- Scenario Regression Authoring UI: local authoring of regression cases stored
  in controlled scenario files, with preview/validate/save flows.
- Hidden Information Leak Regression Suite: pytest evals for player API,
  narrator context, memory context, graphs, maps, shops, quest state, reports,
  and quality output.
- Quest Completion Analysis: static and scenario/playtest-assisted analysis of
  missing stage refs, missing trigger refs, unreachable stages, completion
  paths, circular paths, and hidden quest visibility risks.
- Dead-End / Unreachable Objective Detector: pragmatic checks for unreachable
  required items/NPCs/facts, locked paths without access, undiscoverable clues,
  and quest blockers.
- NPC Behavior Coverage Report and NPC Schedule Conflict Detector: coverage and
  conflict analysis for NPC goals, schedules, planning actions, reactions,
  rumor/crime participation, and quest-required availability.
- Economy Balance Sanity Checks: non-authoritative checks for negative prices,
  arbitrage risk, shop references, hidden shop inventory, reward outliers, and
  extreme price modifiers.
- Combat Balance Sanity Checks: non-authoritative checks for lethal dead ends,
  missing non-lethal paths, critical NPC death without fallback, public combat
  consequence gaps, and unresolved status effects.
- Faction / Rumor / Crime Consequence Coverage: checks for missing references,
  untriggerable consequences, dedupe risks, faction effects, and hidden fact
  leakage in social systems.
- Save / Load / Migration Stress Tests: deterministic temporary-DB scenarios
  for many turns, save/load cycles, migration dry-run/apply, save-bundle
  import/export, replay dry-run, and hidden-safe reporting.
- Performance Benchmark Suite: local benchmarks for game loop, world tick,
  save/load, migration dry-run, validation, map/quest graph conversion, memory
  search, and scenario regression.
- Narrative Consistency Evals: deterministic evals for contradictions with
  `ActionResult`, `visible_state`, timeline, NPC knowledge, quest state, and
  memory authority.
- World Health Score Dashboard: a heuristic dashboard that aggregates quality
  reports into structure, reachability, secrecy, continuity, balance, coverage,
  performance, and migration-safety dimensions. It is not an absolute quality
  judgment.
- Content Coverage Dashboard: safe coverage summaries for locations, NPCs,
  items, quests, facts, factions, rumors, crimes, combat, and trade.
- Branch Diff Regression Testing: selects relevant regression cases from a
  `WorldDiff` and runs them in temporary sessions.
- Mod Compatibility Stress Testing: checks mod combinations without executing
  code or modifying original world/mod files.
- Automated Playtest Batch Runner: deterministic batch execution across
  scenarios, agents, and seeds, with aggregate safe reports.
- Quality Gate CLI / API: runs a configured local gate over validation,
  hidden-leak checks, quest/dead-end/NPC/economy/combat/social analyses,
  stress tests, benchmarks, scenario regression, and mod compatibility smoke
  checks.

Quality tools are local development tools. They must not call real LLM APIs by
default, must use mock/local-stub providers in tests, and must not make the LLM
the pass/fail judge. The quality gate uses deterministic code, thresholds, and
report severities.

## v1.1 Roleplay Immersion Layer

v1.1 adds a Roleplay Immersion Layer for character voice, dialogue continuity,
group scenes, local Tavern-like imports, and RP-specific regression checks. It
does not change the core authority model: `GameState`, `StateDelta`, `EventLog`,
visibility, NPC knowledge, and deterministic rules remain the fact layer. RP
features may change expression style, tone, scene mood, and safe dialogue
context; they must not create facts, complete quests, decide combat, reveal
hidden information, or let model output directly mutate state.

### Roleplay Boundary

`docs/ROLEPLAY_BOUNDARY.md` defines the v1.1 RP boundary terms:

- `authoritative_fact`
- `visible_fact`
- `npc_known_fact`
- `narrator_safe_memory`
- `rp_flavor`
- `emotional_expression`
- `prohibited_fact_creation`
- `debug_only_context`

`RoleplayContextPolicy` is the shared policy object used by RP context builders
and consistency checks. It permits voice, sentence style, emotional expression,
relationship atmosphere, and scene mood. It prohibits critical item/NPC/location
creation, task completion, knowledge changes, relationship-value changes,
dead-character contradiction, hidden fact leakage, and `ActionResult` override.

### Character Card Importer

Character card import is local authoring only. APIs:

- `POST /authoring/characters/import/preview`
- `POST /authoring/characters/import/validate`
- `POST /authoring/characters/import/apply`

The importer accepts JSON, YAML, simple text cards, and Tavern-like fields such
as `name`, `description`, `personality`, `scenario`, `first_message`,
`example_dialogue`, `creator_notes`, and `system_prompt`. It returns candidates:

- `rp_profile_candidate`
- `voice_profile_candidate`
- `example_dialogue_candidate`
- `flavor_lore_candidate`
- `structured_fact_candidate`
- `hidden_fact_candidate`
- `unsafe_or_unsupported_entries`

Preview and validation do not write disk. Apply requires `confirm_save=true`,
uses authoring validation, and writes content only through the authoring
service. The importer rejects remote URLs and script-like payloads. External
`system_prompt` and `creator_notes` are treated as untrusted and unsafe when
they attempt to override world or prompt authority.

### RP Profile And Voice Profile

NPCs may now include `rp_profile`, `voice_profile`, `dialogue_style`,
`speech_habits`, `taboo_topics`, `emotional_mask`, and
`example_dialogue_refs`. Safe voice fields can enter dialogue context. Hidden or
authoring-only profile fields, especially `private_self_summary`, do not enter
player-facing prompts by default.

`RPProfile` controls persona and expression preferences. `VoiceProfile` controls
tone, sentence length, vocabulary style, catchphrases, speech habits, silence
style, and emotional tells. These profiles are expression data only. They do
not change NPC knowledge, relationship values, `ActionResult`, quest state, or
visibility.

### NPC Emotional State

`EmotionalState` tracks a small structured emotional layer on NPC state:

- `primary_emotion`
- `intensity`
- `stability`
- `stress`
- `trust_tone`
- `fear_tone`
- `affection_tone`
- `last_emotional_event_id`
- optional `expires_turn`

Emotion rule helpers can derive shifts from events, apply shifts, decay emotion,
and summarize emotion for dialogue. Emotional changes are rule outcomes and
must go through `StateDelta` and events. The LLM may express emotion in text but
cannot write `emotional_state`.

### Relationship Tone

`RelationshipTone` derives an expression layer from existing relationship
values, faction reputation, emotional state, and recent event tags. It includes
address style, formality, warmth, tension, intimacy, respect, resentment, fear,
avoidance, and trust expression.

Relationship tone only affects prompt style summaries. It does not directly
modify `RelationshipState`; relationship value changes still require normal
rules and `StateDelta`. Hidden relationships must not enter player-visible
graphs or dialogue prompts.

### Dialogue Mode

Dialogue Mode adds structured `DialogueSession` records and a `DialogueManager`.
APIs:

- `POST /game/dialogue/start`
- `POST /game/dialogue/continue`
- `POST /game/dialogue/end`

A dialogue session stores participants, focus NPC, turn range, dialogue mode,
active topics, safe context summary, and status. Dialogue context is built from
player-visible facts, NPC-known facts, safe voice/profile fields, relationship
tone, emotional state, prompt-safe example dialogue, scene mood, and safe RP
memory. NPCs cannot receive facts they do not know.

Dialogue may produce rule-authorized consequences such as relationship deltas,
emotional shifts, quest triggers, fact reveals, or rumor hearing. Those changes
are decided by code, emitted as `StateDelta`, and recorded as events. LLM text
cannot directly decide them.

### Multi-NPC Scene / Group RP

Group RP uses `GroupDialogueScene` and `GroupDialogueManager`. APIs:

- `POST /game/group-dialogue/start`
- `POST /game/group-dialogue/next-speaker`
- `POST /game/group-dialogue/end`

Each participant gets an independent context based on that NPC's knowledge,
emotion, relationship tone, and visibility. Group scenes record events and use a
deterministic next-speaker rule. Dead or incapacitated NPCs do not participate
in ordinary group chat. Group RP is not an autonomous multi-agent simulator and
does not let NPC contexts share hidden facts.

### Scene Mood Presets

Content packs may define `scene_moods.yaml` with `SceneMoodPreset` entries.
Mood presets can influence tone, pacing, sensory focus, metaphor style,
dialogue pressure, and intensity range. They are style controls only: they do
not modify `GameState`, `ActionResult`, hidden fact filtering, or prompt safety.

Dialogue Mode and Group RP can select a mood preset, and prompt profiles may
reference safe mood settings. Invalid presets are caught by validation.

### Lorebook Import / Classification

Lorebook import is local authoring only. APIs:

- `POST /authoring/lorebook/import/preview`
- `POST /authoring/lorebook/import/validate`
- `POST /authoring/lorebook/import/apply`

`LorebookClassifier` parses JSON, YAML, or text entries and classifies them as:

- `flavor_lore`
- `structured_fact_candidate`
- `hidden_fact_candidate`
- `unsafe_entry`

Flavor lore can become safe style/context. Structured facts must be written to
content packs before becoming authoritative. Hidden fact candidates remain under
visibility control. Unsafe prompt/control entries are quarantined and cannot
enter prompts. The importer does not execute instructions, read remote URLs, or
modify active `GameState`.

### Example Dialogue Manager

Example dialogue entries are authoring content used to guide voice. They do not
become `GameState` facts and do not add NPC knowledge. APIs:

- `GET /authoring/worlds/{world_id}/example-dialogue`
- `POST /authoring/worlds/{world_id}/example-dialogue/preview`
- `POST /authoring/worlds/{world_id}/example-dialogue/validate`
- `PUT /authoring/worlds/{world_id}/example-dialogue`

Only `prompt_safe` entries with safe fact policy can enter dialogue context.
Entries marked `authoring_only`, `debug_only`, or `unsafe` stay out of runtime
prompts. Hidden fact references are filtered unless the relevant facts are
visible and known according to normal rules.

### RP Memory Context Builder

`RPMemoryContextBuilder` builds RP-safe memory lists for a speaker and player:

- `speaker_safe_memories`
- `player_visible_shared_memories`
- `relationship_memories`
- `recent_dialogue_memories`
- debug-only `excluded_memory_reasons`

It filters hidden memory, debug-only memory, memory tied to unknown facts, and
memory tied to currently invisible hidden facts. Memory remains non-authoritative
and cannot override `GameState`.

### RP Prompt Profile Manager

v1.1 extends `PromptProfile` with `RPPromptProfile` fields for RP style:
dialogue depth, emotional intensity, prose density, response length,
perspective, inner thought policy, and optional sensuality style policy. The
boundary fields are fixed:

- `hidden_fact_policy=deny`
- `state_modification_policy=deny`

Validation rejects profiles that try to widen authority. RP prompt profiles may
change style only; they cannot change visible facts, NPC knowledge,
`ActionResult`, `StateDelta`, or quest state.

### RP Output Consistency Checker

`RPOutputConsistencyChecker` checks generated RP text against the safe dialogue
context. It can flag hidden fact leakage, NPC unknown-fact mentions, invented
key items/NPCs/locations, dead NPCs speaking, contradictions with
`ActionResult`, unauthorized relationship change, unauthorized quest completion,
and raw debug/state-delta leakage.

The checker does not use an external LLM judge and does not modify state. On
serious violations it can reject output, request retry, or fall back to a safe
summary.

### Tavern Compatibility Import / Export

Tavern-like compatibility APIs:

- `POST /authoring/tavern/import/preview`
- `POST /authoring/tavern/import/apply`
- `POST /authoring/tavern/export`

Supported import resources are character cards, lorebook/world info, example
dialogue, and prompt presets. Import always goes through parse, classification,
unsafe detection, preview, explicit apply, and validation. It rejects path
traversal in source names, remote URL references, and script-like payloads.

Safe export supports character-like cards, safe lorebook export, and prompt
profile export. Safe mode excludes API keys, raw `GameState`, save data, and
hidden facts. Authoring/debug export modes must remain local and warned.
Compatibility is practical and best-effort; it is not a promise that every
external Tavern format is fully supported.

### RP Scenario Templates

RP scenario templates live under `templates/rp/` and create dialogue or group
scene drafts. APIs:

- `GET /authoring/rp-scenario-templates`
- `GET /authoring/rp-scenario-templates/{template_id}`
- `POST /authoring/rp-scenario-templates/{template_id}/preview`
- `POST /authoring/rp-scenario-templates/{template_id}/apply`

Templates can specify scene type, required/optional participants, suggested
mood, suggested dialogue mode, opening context, allowed/forbidden topics,
required visible facts, and safety notes. They do not call the LLM, do not
modify active saves, and cannot expand NPC knowledge or hidden fact access.

Known v1.0 implementation note: `ENABLE_PLAYTEST_API`, `ENABLE_EVAL_API`,
`ENABLE_DEBUG_API`, and `ENABLE_PERF_LOGGING` gate the main playtest, eval,
debug, benchmark, and quality-gate flows. There is currently no separate
`ENABLE_QUALITY_API` setting. Some analyzer endpoints are local-only but not
all have an independent feature flag yet; keep the backend bound to localhost
and do not expose quality APIs as a hosted service.

## Current Limits

- No account system, cloud sync, or remote publishing.
- No formal desktop installer.
- No complex drag/drop IDE or multiplayer authoring workflow.
- No automatic YAML repair.
- No arbitrary mod code execution.
- No online mod download or complex mod version solver.
- No large-scale social simulation, diplomacy AI, or war simulation.
- No external vector database requirement.
- No external LLM judge in evals.
- No production APM/telemetry; performance samples remain local.
- Quality reports and health scores are heuristic authoring aids, not absolute
  design judgments and not canonical world facts.
- Quality, eval, benchmark, and playtest APIs are local-only tools, not
  production or hosted-service endpoints.
- NPC planning is limited to deterministic candidate actions.
- Procedural side quests are drafts only.
- Memory retrieval is context support, not canonical truth.
