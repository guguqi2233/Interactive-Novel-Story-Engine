# v0.5 Release Notes

## Version Name

v0.5 - Authoring Tools, Advanced NPCs & Local Memory

## Version Goal

v0.5 moves the project from a playable local RPG world engine toward a local world-making platform. The release focuses on safer content authoring, richer validation, local memory retrieval, lightweight NPC planning, relationship/social extensions, draft-only procedural quest support, content-only mod packaging, and better multi-world save management.

This remains a local self-use engine. It is not a hosted product, and the authoring/debug surfaces are intended only for trusted local development.

The core boundary is unchanged: the LLM is still not the world judge. It may parse intent, render narration from filtered context, summarize memory, or assist with draft content, but canonical world outcomes are decided by the rules engine and applied through `StateDelta`.

## New Features

- Content Authoring API for listing world packs, reading/writing whitelisted YAML files, creating local world folders, and running validation.
- Content Authoring Frontend with a YAML editor, file picker, validation report display, and disabled-state handling when authoring is not enabled.
- Structured validation reports with file/path/code/message/severity, plus clearer errors, warnings, and suggestions for content authors.
- SQLite-backed memory store and deterministic local search by tag, entity, fact, turn range, substring, and recency.
- `MemoryContextBuilder` for constructing narrator-safe and NPC-scoped memory context while filtering hidden/debug memory.
- NPC goal schemas and rule helpers for structured goals, priorities, constraints, current goal selection, and plan state.
- NPC planning tick for limited deterministic actions such as moving, reporting known crimes, spreading known rumors, fleeing, guarding, and resting.
- NPC relationship graph with trust, fear, affinity, obligation, visibility, and relationship-aware rumor/planning hooks.
- Faction conflict layer with structured faction relations, alert/conflict state, incident handling, and player-visible filtering.
- Economy/trade initial rules for item prices, merchant inventory, player currency, buy/sell checks, and trade state deltas.
- Procedural side quest generator initial version. It creates `QuestDraft` candidates only and does not directly mutate `GameState` or write active saves.
- Automated narrative boundary evals for hidden facts, NPC secrets, hidden witnesses, hidden/debug memory, debug deltas, rumor text, and quest draft leaks.
- Content-only plugin/mod packaging with manifest validation, dependency/conflict checks, path safety, and no arbitrary code execution.
- Multi-world save browser support with save summaries, world filtering, safe load, and delete flow.

## Behavior Changes

- Memory summaries coerced from legacy `MemorySummary` records are treated as `debug_only` by default, not narrator-safe context.
- Rumor player-facing text is sanitized when it would reveal the text of an undiscovered hidden/discoverable fact.
- World validation now warns when rumor text appears to expose hidden fact text, even before the rumor is known by the player.
- NPC planning is now part of the world tick flow, but remains deterministic, rule-limited, and not LLM-driven.
- Player-facing state is broader than v0.4, but must still be filtered: hidden facts, hidden NPCs, hidden witnesses, NPC secrets, hidden relationships, and hidden/debug memory must not enter player narrative.
- Authoring and debug outputs are explicitly separate from player APIs and narrator inputs.

## API Changes

### Authoring API

Authoring APIs are controlled by `ENABLE_AUTHORING_API` and are for local development only:

- `GET /authoring/worlds`
- `POST /authoring/worlds`
- `GET /authoring/worlds/{world_id}`
- `GET /authoring/worlds/{world_id}/files`
- `GET /authoring/worlds/{world_id}/files/{file_name}`
- `PUT /authoring/worlds/{world_id}/files/{file_name}`
- `POST /authoring/worlds/{world_id}/validate`
- `GET /authoring/mods`
- `POST /authoring/mods/{mod_id}/validate`

Authoring file access is restricted to whitelisted YAML files and rejects path traversal. It must not read `.env`, database files, logs, source files, or system paths.

### Game / Save API

- Save listing supports safer summaries and world filtering.
- Save deletion is available through the game API.
- Save summaries are intended to expose only player-safe information, not raw `GameState`, raw `state_deltas`, hidden facts, hidden witnesses, or debug memory.

### Debug API

Debug APIs remain gated by `ENABLE_DEBUG_API` and are local-development tools. Debug timeline data is not player narrative and must not be passed to Narrator.

## Content Pack Format Changes

v0.5 expands the content model while keeping existing packs loadable through defaults where possible:

- `relationships.yaml` for NPC/NPC or NPC/player relationship edges.
- `npcs.yaml` supports goal/planning-related fields and merchant-related fields.
- `items.yaml` supports economy fields such as `base_price`, `tradeable`, and `rarity`.
- `factions.yaml` supports relation/conflict/alert extensions.
- Mod manifests describe local content-only packages, dependencies, conflicts, entry worlds, and content paths.
- Procedural quest output uses `QuestDraft`, which is separate from runtime `QuestState` and requires validation/review before being saved as content.
- Validation covers more cross-file references, including schedules, factions, rumors, quest triggers, ownership conflicts, hidden fact text, economy values, and mod manifests.

## Frontend Changes

- Added an authoring surface for selecting worlds, editing whitelisted YAML files, saving local changes, and running validation.
- Added structured validation display grouped by severity and file/path information.
- Expanded social/debug panels for v0.5 state such as known factions, rumors, relationships, faction conflict, combat/social summaries, timeline details, and debug-only data where enabled.
- Added multi-world save browsing with summaries, world filtering, load, and delete controls.
- The frontend still does not store or display API keys and does not compute authoritative hidden state.

## Testing / Evals Changes

Verification for v0.5 acceptance:

- `python -m pytest` passed with 360 tests.
- `cd frontend && npm.cmd run build` passed.

New or expanded test coverage includes:

- Authoring API enable/disable, whitelist, YAML parsing, path traversal, and validation behavior.
- Structured validation report behavior.
- SQLite/deterministic memory store search and safety filtering.
- Memory context filtering for narrator and NPC context.
- NPC goals, planning tick, relationships, faction conflict, economy/trade, side quest drafts, and mod loading.
- Multi-world save browser behavior and safe summaries.
- Narrative boundary evals for hidden facts, NPC secrets, hidden witnesses, debug deltas, hidden/debug memory, rumor text, and procedural quest drafts.

Tests use mock/fake providers and do not call real OpenAI APIs.

## Known Limitations

- Authoring/debug APIs are local-development tools, not production security boundaries.
- The authoring frontend is a minimal textarea-based editor, not a full content studio or graph editor.
- Memory is not an authoritative fact source. It must not overwrite `GameState`, `EventLog`, quests, facts, crimes, or relationships.
- `MemoryContextBuilder` is implemented and tested, but full runtime narrator integration remains conservative and should be expanded carefully.
- NPC planning is lightweight, deterministic, and rule-constrained. It is not LLM multi-agent autonomous reasoning.
- Procedural side quest generation produces drafts only. Drafts must be reviewed and validated before becoming content.
- Plugin/mod packaging is content-only and does not execute arbitrary Python, JavaScript, or other scripts.
- Economy/trade, faction conflict, relationships, and NPC goals are first-pass systems, not full simulations.
- Some player-visible social summaries still expose simple structured values for local debugging and should be refined if stricter diegetic presentation is needed.
- Mod validation/reporting may still expose local development paths in authoring/debug contexts; do not treat these surfaces as player-facing.
- Existing Narrator prompt text has known encoding/wording cleanup needs, but the LLM authority boundary is unchanged.

## Upgrade Notes From v0.4

- Review `.env.example` and add new local settings such as `ENABLE_AUTHORING_API`, `ENABLE_DEBUG_API`, `MEMORY_BACKEND`, `AUTHORING_ROOT`, and any project-local database URL setting used by your environment.
- Keep `LLM_PROVIDER=mock` for local tests unless deliberately testing a real provider.
- Run `python -m backend.app.tools.validate_world mist_valley` after updating content packs.
- Existing v0.4 saves should load through default-filled state fields, but v0.5 social/memory/relationship/economy fields may be empty until new actions or content initialize them.
- Update world packs if you want to use new schemas such as `relationships.yaml`, NPC goals, merchant fields, faction conflict fields, or mod manifests.
- Treat generated side quests as drafts. Save them to content only through the authoring workflow after validation.
- Do not enable authoring/debug APIs outside a trusted local environment.

## Recommended v0.6 Direction

- Replace raw YAML editing with structured forms for common content types.
- Add a quest graph editor and stronger quest trigger visualization.
- Improve memory-to-narrator integration through a single audited context builder path.
- Expand narrative boundary evals into golden transcript regression suites.
- Add richer relationship and faction visualization in debug/authoring UI.
- Harden save/replay verification for large scenario playthroughs.
- Improve mod load-order UI and composed-world validation.
- Expand economy/trade only after the authority and visibility boundaries remain stable.
- Explore LLM-assisted authoring as draft/review/export only, never direct runtime mutation.

## Final Status

v0.5 is accepted as a local development release candidate with no known high-risk release blockers after the blocker fixes. The release expands authoring, memory, NPC planning, social structure, validation, and save management while preserving the rule-engine authority model.
