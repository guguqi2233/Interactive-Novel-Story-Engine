# Project Specification

## Goal

Build a local-only LLM interactive fiction world engine. The LLM handles language-facing work: intent parsing, narrative rendering, memory summaries, and optional author-facing draft generation. The deterministic Python world engine owns canonical state, rules, causality, events, visibility, saves, social consequences, combat outcomes, authoring validation, and content-pack loading.

The project is local personal software, not a hosted multiplayer service.

## Core Responsibilities

### LLM Responsibilities

- Parse player natural language into schema-validated `PlayerIntent`.
- Render accepted world outcomes into player-facing prose.
- Summarize recent events into internal memory summaries.
- Optionally generate author-facing side quest drafts through `LLMProvider`.
- Operate only through `LLMProvider`.

### World Engine Responsibilities

- Store canonical `GameState`.
- Evaluate player intent with deterministic rules.
- Produce and apply `StateDelta` objects.
- Record player and system events.
- Persist and load saves through SQLite.
- Enforce visibility boundaries.
- Keep important facts, quests, items, NPC state, social state, combat state, time, memory records, and content-pack definitions in structured data.
- Validate content packs and local mods before loading or saving authoring edits.

## Architecture Boundary

The LLM is a narrator, parser, summarizer, and optional draft assistant. It is not the world judge.

The world engine is authoritative. It decides whether an action succeeds, what changes, what is visible, what is remembered, what gets saved, and what content is loadable.

No LLM output may directly mutate `GameState`.

All canonical changes must go through `StateDelta`.

All handled player actions, system ticks, NPC planning ticks, and system consequences must be recorded as `Event` entries.

Authoring APIs edit content-pack YAML, not active `GameState`. Procedural quest generation produces drafts only.

## Current v0.8 Gameplay Loop

1. Player submits text through API or frontend.
2. `IntentParser` returns schema-validated `PlayerIntent`.
3. `ActionDispatcher` selects an action handler.
4. The action handler resolves deterministic `ActionResult`.
5. Action deltas are applied with `apply_delta`.
6. Quest triggers caused by the action are resolved.
7. Turn advances for successful/partial actions.
8. World tick runs schedule, quest triggers, social consequences, NPC reactions, NPC planning, suspicion decay, delayed consequences, and post-delayed quest triggers.
9. Player event and system events are recorded.
10. Crime/witness consequences can be generated from the player event.
11. Narrator receives visible action facts and returns `NarrativeResult`.
12. API returns narration plus filtered `visible_state`.

## v0.8 Included Scope

Backend:

- FastAPI API with health, game start/input/state, save/load/delete/list, debug timeline, and local authoring endpoints.
- SQLite save/load for state snapshots, event history, and memory records.
- Multi-world content-pack loading from `worlds/{world_id}`.
- Content-pack validation CLI and structured validation report.
- Local authoring API for whitelisted YAML files.
- Content-only mod manifest discovery and validation.
- Save migration status, dry-run, apply, backup metadata, and CLI.
- Save migration UI in the frontend Save Browser.
- Authoring diff/preview/dry-run and content impact analysis.
- Relationship/faction graph APIs in player-safe and debug scopes.
- Debug performance APIs for local timing samples.
- Studio Home and Settings / Local Privacy safe summary endpoints.
- Narrative eval, playtest, import/export, scenario template, quest graph, and
  mod manager local studio endpoints.
- Visual map, quest graph, NPC goal, social graph, economy, rumor/crime,
  validation graph, timeline replay, world branch/diff, template browser,
  prompt profile, scenario regression, and advanced package endpoints.
- Multi-world save browser summaries.
- LLM provider factory using `LLM_PROVIDER`.

World engine:

- `GameState`, `StateDelta`, `EventLog`.
- Time system.
- NPC schedule resolver.
- Search action.
- Inventory rule functions.
- Lockpick action.
- Sneak action.
- Quest state machine.
- Faction reputation.
- Rumor propagation.
- Crime and witness system.
- Social consequence tick.
- Combat core: attack, defend, flee.
- Advanced combat slice: guarded/stunned/bleeding, cautious/fleeing stances,
  non-lethal attack, flee risk, and visible combat summary.
- Injury, death, and incapacitation rules.
- NPC reaction rules.
- NPC goals and deterministic NPC planning tick.
- NPC relationship graph.
- Faction conflict layer.
- Economy/trade rules and buy/sell actions.
- Advanced local memory retrieval with in-memory and SQLite stores plus a local-vector-ready fallback interface.
- `MemoryContextBuilder` for safe narrator/player/NPC memory context.
- Procedural side quest draft generation.

Frontend:

- React/Vite local prototype.
- World selection.
- Start/input flow.
- Save/load/delete browser.
- Visible state panels.
- Player-visible social/status panels.
- Local debug timeline and classified debug panels.
- Authoring panel for reading/editing/saving/validating content-pack YAML.
- Lightweight graph panels for player-visible and debug relationship/faction
  graph data.
- Local studio launcher prototype documented for Windows PowerShell.
- Studio Home Dashboard.
- Save Migration UI.
- Mod Manager UI.
- Narrative Quality Dashboard.
- Performance Dashboard.
- Automated Playtesting Dashboard.
- Scenario Template preview UI.
- Visual Map Editor.
- Visual Quest Graph Editor full authoring slice.
- NPC Goal Editor.
- Faction / Relationship Visual Editor.
- Item / Economy Editor.
- Rumor / Crime Consequence Editor.
- Visual Validation Graph.
- Timeline Replay Visualizer.
- World Branch / Diff panels.
- Scenario Regression Suite UI.
- Local Template Browser.
- Prompt Profile Manager.
- Import/export controls for local world, mod, save, template, and scenario
  packages.
- Settings / Local Privacy panel.

Testing:

- Unit tests for core rules and actions.
- FastAPI tests.
- SQLite save/load tests with temporary databases.
- Boundary eval tests for narrative visibility leaks.
- v0.3, v0.4, v0.5, v0.6, v0.7, and v0.8 integration regression tests.
- Migration compatibility fixtures.
- Deterministic playtesting agents and narrative quality evals.
- Fake/mock LLM providers in automated tests.

## Persistence Model

SQLite stores:

- `SaveGame` with current `GameState` JSON snapshot.
- `StoredEvent` with full event JSON.
- `StoredMemory` with memory record JSON when explicitly saved.

Event history is suitable for debugging and scoped replay. `StateDelta` values are type-validated when reapplied.

## Visibility Model

Player-visible API responses must be derived from `visible_state`.

`visible_state` includes:

- world id
- turn
- formatted game time
- current location
- inventory
- visible objects
- visible NPC summaries
- known facts
- visible/known quests
- known factions
- known rumors
- known/reported/resolved crimes
- known relationships
- visible faction conflicts

It must not include:

- hidden facts not in `player_visible_facts`
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- hidden witnesses
- debug-only event details
- hidden inactive quests
- hidden factions
- hidden relationships
- hidden/debug memory records
- raw `state_deltas`

Known caveats:

- Current visible faction responses still include raw numeric reputation as well as a band. The frontend displays the band; moving raw reputation to debug-only remains a hardening recommendation.
- Current visible faction conflict responses include `conflict_tags`, which may hint at hidden social structure if authored incautiously.

## Debug Model

Debug timeline endpoints are local-development tools:

- `GET /debug/sessions/{session_id}/events`
- `GET /debug/saves/{save_id}/events`

They can show raw `state_deltas`, including hidden/system-only information. They are controlled by `ENABLE_DEBUG_API` and must not be treated as player-facing narrative output.

The frontend shows debug data only in the debug panel.

Performance debug endpoints are also controlled by `ENABLE_DEBUG_API`.
Performance recording is controlled by `ENABLE_PERF_LOGGING`, stores samples in
memory, and must not record prompt text, API keys, hidden fact text, raw
`GameState`, or raw `state_deltas`.

## Authoring Model

Authoring endpoints are local-development tools controlled by `ENABLE_AUTHORING_API`.

They can list, read, save, and validate whitelisted YAML files in content packs. They are not player APIs and may show hidden world content to the local author.

Authoring saves YAML files and runs validation. It does not write active session `GameState`.

v0.6 authoring preview/dry-run endpoints parse proposed YAML, validate it in a
temporary draft, calculate diff/impact summaries, and report possible save
migration risk without writing disk or active saves.

v0.7 extended authoring with scenario templates, quest graph preview, mod
manager views, and import/export. v0.8 extends authoring with visual map,
fuller quest graph, NPC goal, faction/relationship, item/economy,
rumor/crime, validation graph, branch/diff, template browser, and advanced
package workflows. These tools are still local-only, gated by
`ENABLE_AUTHORING_API`, and must not write active session `GameState`.
Authoring UI may show hidden world content to the local creator, but that data
must remain isolated from player UI and narrator inputs.

## Local Studio Model

The v0.8 local studio is a collection of trusted-local tools around the world
engine. It includes Studio Home, Save Migration UI, Mod Manager UI, narrative
eval and performance dashboards, playtesting dashboard, settings/privacy
panel, import/export, scenario templates, visual authoring editors, validation
graph, timeline replay, world branch/diff, prompt profiles, and desktop
launcher scripts.

These tools improve convenience but do not change authority:

- They do not make the frontend a source of truth.
- They do not let authoring tools edit active `GameState`.
- They do not let dashboards feed debug data into narration.
- They do not make local model output canonical.
- They do not execute mod or template scripts.

## Import / Export Model

World, mod, and save archives are local zip bundles with a manifest. Import
rejects path traversal, zip slip, executable files, `.env`, local database
files, logs, and secret files. World and mod imports run validation. Save
imports check migration status.

Save archives can contain full save state and event history, including hidden
state by design. They are authoring/backup data, not player-facing output.

v0.8 advanced packages add `local_package_manifest.json`, checksums,
compatibility checks, dry-run, and explicit apply. Supported package types are
world, mod, save bundle, template pack, and scenario suite. Package import
must not execute code, auto-overwrite content, or bypass validation/migration.

## Save Migration Model

Saves carry engine/schema/world/content metadata and migration history. The
v0.6 migration system can report status, dry-run, and apply migration with a
backup. Migrations are deterministic code, do not call LLMs, must preserve
EventLog, and must not reclassify hidden/debug data as player-visible.

## Correctness Over Convenience And Performance

Performance instrumentation and future optimizations must not bypass
`StateDelta`, `EventLog`, Pydantic/schema validation, content validation,
visibility filtering, provider abstraction, or migration validation. A faster
path that weakens rule correctness or privacy is invalid.

The same principle applies to local studio convenience. A nicer visual editor,
faster import path, easier template flow, branch/diff workflow, prompt profile,
or desktop launcher must not bypass validation, visibility, migration dry-run,
event logging, provider abstraction, or content-only mod restrictions.

## Forbidden Practices

- Do not let LLM output directly overwrite `GameState`.
- Do not apply unvalidated LLM JSON.
- Do not skip event creation for handled player actions, system ticks, NPC planning ticks, or system consequences.
- Do not store API keys in source, docs, fixtures, logs, database rows, or saves.
- Do not write provider-specific model calls inside world engine modules.
- Do not make canonical state changes without `StateDelta`.
- Do not expose hidden facts, NPC secrets, hidden witnesses, hidden NPCs, hidden objects, hidden relationships, or hidden/debug memory through player APIs.
- Do not put game rules only in prompts.
- Do not let combat, crime, rumor, faction, trade, NPC planning, relationship, or quest outcomes be decided by LLM output.
- Do not let authoring or mod packaging execute arbitrary code.
- Do not let procedural side quest generation write active saves or content files without explicit authoring review/export.
- Do not let scenario templates execute scripts or write active saves.
- Do not let quest graph editing bypass `quests.yaml` validation.
- Do not let visual map, NPC goal, social graph, item/economy, rumor/crime, or
  validation graph tools bypass content validation.
- Do not let import/export install archives without path, type, manifest, and
  validation checks.
- Do not let advanced packages skip checksum validation before apply.
- Do not expose provider secrets, raw env, raw `GameState`, or raw
  `state_deltas` through Studio Home, Settings, dashboards, or player APIs.

## Not In v0.8

- Hosted service security, auth, accounts, cloud sync, or multiplayer.
- Tactical grid combat or multi-round combat AI.
- Guard pursuit, arrest, trial, or full legal system.
- Dynamic supply/demand economy, crafting, equipment progression, durability, or weight systems.
- Complex drag/drop IDE, multiplayer authoring, or automatic content repair.
- LLM-driven autonomous NPC agents.
- Pathfinding and large-scale world simulation.
- Arbitrary plugin code execution or online mod download.
- Full vector database or embedding pipeline as a hard dependency.
- Automatic content repair.
- Formal desktop installer, code signing, or auto-update.
- External LLM judge for narrative quality.
- Required local model server or mandatory local LLM integration.
- Production APM, telemetry upload, or hosted monitoring.
- Complex mod version SAT solving or online mod download.
- Any performance optimization that bypasses correctness boundaries.
- Online marketplace, upload/download sync, or account-based collaboration.
- Frontend direct filesystem access.
- Authoring UI direct edits to active runtime sessions.
- Arbitrary template or mod script execution.
- A local model provider that can directly write `GameState`.
- Automatic publishing or automatic overwrite of user world packs.
- LLM-generated map/quest/NPC/social/economy/consequence content that bypasses
  explicit preview, validation, and save.

## v0.8 Known Hardening Items

- Split `ActionResult.reason` into player-safe and debug-only reason fields.
- Move raw faction reputation out of player API.
- Sanitize or remap player-visible faction conflict tags.
- Sanitize invalid mod manifest errors so authoring APIs do not return local absolute paths.
- Classify LLM-generated memory summaries from hidden/debug event sources as `debug_only` or `hidden` by default.
- Keep frontend debug panel closed by default if used for non-debug playtesting.
- Rewrite any mojibake prompt text into clean UTF-8.
- Fix `visible_state.relationships` so player API filters relationship
  endpoints by actor visibility, matching player graph behavior.
- Normalize invalid mod manifest errors so authoring/debug APIs do not expose
  absolute local paths.
- Keep desktop DB/log defaults out of source control and move them to OS app
  data directories before any formal packaging milestone.
- Consider a dedicated `require_eval_api()` so `ENABLE_EVAL_API` can enable
  narrative eval endpoints without enabling all debug endpoints.
- Add stronger frontend warnings around save bundle export, because save
  archives can include hidden state and full event history by design.
- Keep desktop packaging as a prototype until bundle scanning, app data
  directory policy, process lifecycle, and secret handling are formalized.
- Continue adding component-level frontend tests for visual authoring panels.
- Keep debug timeline/replay data out of player/narrator routes.
- Consider stricter allowlists for prompt profile free-text fields if profiles
  expand beyond the current local style controls.
