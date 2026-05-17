# World Engine

This document describes the local world engine as of v0.7. The engine is the
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

## Scenario Template System

v0.7 adds local `ScenarioTemplate` support for reusable authoring drafts.
Templates live under `templates/` and are YAML data, not executable scripts.

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

## Import / Export Workflow

v0.7 adds local authoring-gated archive import/export for worlds, mods, and
saves. Archives are zip files represented by the API as base64 payloads.

Import/export endpoints:

- `GET /authoring/export/worlds/{world_id}`
- `POST /authoring/import/worlds`
- `GET /authoring/export/mods/{mod_id}`
- `POST /authoring/import/mods`
- `GET /authoring/export/saves/{save_id}`
- `POST /authoring/import/saves`

Archive manifests are stored in `export_manifest.json` and include:

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

Save export can include full hidden save state by design. It is therefore a
local authoring/backup workflow only and must stay behind
`ENABLE_AUTHORING_API`.

## Visual Quest Graph Authoring

v0.7 adds an authoring-only quest graph layer for `quests.yaml`. It parses
quests into:

- quest nodes
- stage nodes
- objective nodes
- trigger nodes
- `next_stages` edges
- trigger-to-stage edges

The first UI slice supports viewing the graph and editing stage title, stage
description, objective text, and `next_stages`. The frontend sends the edited
graph to the backend preview endpoint, which converts it back to `quests.yaml`
and runs draft validation. Saving still uses the normal authoring file save
path, so validation remains the gate and active `GameState` is not modified.

Quest graph APIs are local authoring endpoints behind `ENABLE_AUTHORING_API`:

- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`

Hidden quests can appear in the authoring UI because authoring is a local
creator tool, but they must not enter player `visible_state`.

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

v0.7 keeps desktop packaging as a local launcher prototype and enhances the
launcher scripts. The Windows and shell scripts check basic dependencies,
start the FastAPI backend and Vite frontend or built preview, print safe local
status, and open the browser. This is not a formal installer, does not sign
code, does not auto-update, does not sync to cloud, and does not embed `.env`
or API keys into frontend assets.

## Local Model Provider Full Integration

v0.7 provides a more complete configurable local provider integration:

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

## Current Limits

- No account system, cloud sync, or remote publishing.
- No formal desktop installer.
- No graphical world editor beyond the current local authoring panels.
- No automatic YAML repair.
- No arbitrary mod code execution.
- No online mod download or complex mod version solver.
- No large-scale social simulation, diplomacy AI, or war simulation.
- No external vector database requirement.
- No external LLM judge in evals.
- No production APM/telemetry; performance samples remain local.
- NPC planning is limited to deterministic candidate actions.
- Procedural side quests are drafts only.
- Memory retrieval is context support, not canonical truth.
