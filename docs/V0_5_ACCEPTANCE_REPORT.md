# v0.5 Acceptance Report

## Verdict

Accepted for local v0.5 release.

v0.5 meets the release goal of upgrading the project into a more sustainable
local world-making platform with authoring tools, structured validation, local
memory retrieval, safer memory context, advanced deterministic NPC systems,
relationship/faction/economy extensions, procedural quest drafts, mod
validation, multi-world save browsing, and automated narrative boundary evals.

The project remains a local self-use engine. The LLM is still not the world
judge. Runtime world outcomes remain rule-engine decisions applied through
`StateDelta` and recorded in `EventLog`.

## Verification Date

2026-05-17

## Verification Commands

```powershell
python -m pytest
```

Result: `360 passed`

```powershell
cd frontend
npm.cmd run build
```

Result: passed. TypeScript build and Vite production build completed.

## Scope Accepted

### 1. Content Authoring API

Accepted.

- Authoring endpoints are gated by `ENABLE_AUTHORING_API`.
- The authoring service reads and writes only whitelisted YAML files.
- Path traversal is blocked by safe world id validation, file allowlist checks,
  and resolved-path containment checks.
- `POST /authoring/worlds/{world_id}/validate` runs structured validation.
- Writes parse YAML first, validate after save, and roll back invalid content.
- Authoring edits content-pack YAML only; they do not mutate active session
  `GameState`.

### 2. Content Authoring Frontend

Accepted.

- The React frontend includes an authoring mode separate from play mode.
- It can list world packs, select world files, edit YAML in a textarea, save,
  run validation, and display errors/warnings/suggestions.
- Disabled authoring API responses are handled without crashing.
- The frontend reads only `VITE_API_BASE_URL`; it does not store or display LLM
  API keys.

### 3. World Pack Editor Validation UX

Accepted.

- Validation reports are structured as errors, warnings, and suggestions.
- Issues include file, path, code, message, severity, optional ref id, and
  optional suggestion.
- CLI validation supports normal and JSON output.
- CLI returns non-zero when errors exist and zero for warning-only reports.
- API validation returns the same structured report shape.

### 4. Local Vector / SQLite Memory Backend

Accepted.

- Memory store implementations include in-memory, SQLite-backed, and
  local-vector-ready fallback stores.
- Memory records persist through `SQLiteSaveRepository`.
- Retrieval supports tags, entities, facts, turn range, substring, recency, and
  semantic query only when an optional backend is supplied.
- Deterministic fallback works without external vector services.
- Hidden/debug memory can be filtered by visibility.
- Memory remains non-authoritative and does not replace `GameState` or
  `EventLog`.

### 5. Memory Context Builder

Accepted.

- `MemoryContextBuilder` produces narrator-safe, player-visible, and NPC-known
  memory lists.
- Hidden and debug-only memory are excluded from narrator context.
- Memories tied to hidden/discoverable facts are excluded until the player
  knows those facts.
- NPC context checks `npc_knows`; NPCs do not receive memory tied to unknown
  facts.
- Builder tests verify that it does not mutate `GameState`.

### 6. Advanced NPC Goal System

Accepted.

- NPC goals load from content pack YAML.
- Goal selection is deterministic and priority based.
- Blocked/completed/dead/incapacitated NPC goal cases are covered by tests.
- Goal state changes are represented through `StateDelta`.
- Save/load preserves goal state.

### 7. NPC Planning Tick

Accepted.

- Planning tick supports limited deterministic actions such as move, talk,
  report crime, spread rumor, flee, guard, and rest.
- Planning considers goals, knowledge, rumors, crimes, relationships, and life
  state.
- NPCs cannot plan from unknown facts/rumors/crimes.
- Dead/incapacitated NPCs do not plan.
- Planning changes are emitted as `StateDelta` and appear in system tick event
  deltas.

Current implementation aggregates planning deltas into the `world_tick` system
event in the main loop. Standalone `npc_planning` events exist at the planning
rule layer but are not separately appended by `GameLoop`.

### 8. NPC Relationship Graph

Accepted.

- `relationships.yaml` is supported.
- Relationship state includes trust, fear, affinity, obligation, tags, and
  player-known visibility.
- Relationship changes go through `StateDelta`.
- Hidden relationships do not enter `visible_state`.
- Relationship score affects rumor propagation and NPC planning.
- Save/load preserves relationship state.

### 9. Faction Conflict Layer

Accepted.

- Faction relations and conflict metadata load from `factions.yaml`.
- Alert/conflict changes are represented through `StateDelta`.
- Incidents are deduped through social flags.
- Hidden target factions are filtered from visible faction-conflict relations.
- Faction conflict can be triggered by crimes, reputation bands, and rumors.

### 10. Economy / Trade

Accepted.

- Items support base price, tradeable flag, rarity, and tags.
- NPC merchants support shop inventory and price modifiers.
- Player currency is authoritative backend state.
- Buy/sell actions use backend rule checks and produce `StateDelta` values for
  currency, ownership, and shop inventory.
- Non-tradeable and stolen item cases are covered.
- The frontend does not calculate authoritative prices.

### 11. Procedural Side Quest Generator

Accepted.

- Generator returns `QuestDraft`, not runtime quest state.
- Rule-based generation does not call the LLM.
- LLM-assisted generation uses an injected `LLMProvider` and schema-validates
  `QuestDraft`.
- Generated drafts do not mutate `GameState`.
- Drafts do not write `quests.yaml`; saving content remains an explicit
  authoring action.
- Hidden fact text is rejected or redacted from player-facing draft fields.

### 12. Automated Narrative Boundary Evals

Accepted.

- Boundary evals cover hidden facts, NPC secrets, hidden witnesses, raw
  `state_deltas`, hidden/debug memory, rumor hidden fact text, and procedural
  quest draft hidden text.
- Evals use fake/mock providers and do not call real APIs.
- The release-blocking rumor and memory summary regressions are now covered.

### 13. Plugin / Mod Packaging

Accepted.

- Mod discovery and validation are implemented for local content-only mods.
- Manifest validation covers required fields, dependencies, conflicts, entry
  worlds, content paths, and engine version metadata.
- Mod loader rejects path traversal and absolute paths.
- Mod loader rejects executable-code-like files and does not import or execute
  mod code.
- Entry worlds are validated through the normal world validation path.

### 14. Multi-world Save Browser

Accepted.

- Save list supports `world_id` filtering and updated-time ordering.
- Save summaries include safe fields: save id, world id/name, turn, current
  location name, formatted time, timestamps, and optional summary.
- Save summaries do not include raw `GameState`, hidden facts, raw
  `state_deltas`, witnesses, or memory records.
- Delete save is implemented.
- Load creates/restores an active session and can continue play.

### 15. v0.5 Integration Tests

Accepted.

The suite includes v0.5 integration regression coverage for:

- authoring gating, reading, validation, path safety, and no active-state
  mutation;
- memory persistence and safe context building;
- NPC goals, planning, knowledge boundaries, relationships, and life-state
  restrictions;
- faction conflict, economy/trade, and save/load preservation;
- procedural quest draft and mod validation;
- multi-world save browser behavior.

## Boundary Review

### LLM Boundary

Passed.

- Runtime provider construction remains centralized through
  `create_llm_provider`.
- Business modules depend on `LLMProvider`, not concrete vendor SDKs.
- v0.5 rule modules do not call LLM providers.
- LLM-assisted side quest generation is draft-only and schema-validated.
- No LLM output directly writes `GameState`, emits authoritative `StateDelta`,
  or decides combat, trade, rumor, crime, planning, faction, relationship, or
  quest outcomes.

### StateDelta Boundary

Passed.

- Runtime canonical changes in v0.5 systems use `StateDelta`.
- Save/replay tests cover state preservation for the release-critical flows.
- Authoring and mod validation do not mutate active game state.

### Event Boundary

Passed with a non-blocking caveat.

- Player actions and world tick consequences are recorded in `EventLog`.
- NPC planning deltas are included in the `world_tick` system event in runtime.
- Planning rule helpers also build individual planning events, but these are
  not appended separately by `GameLoop`.

### Visibility / Memory Boundary

Passed.

- Player APIs expose structured `visible_state`, not raw state.
- Hidden facts, hidden objects, hidden NPCs, NPC secrets, hidden witnesses,
  hidden relationships, and hidden/debug memory are filtered.
- Rumors linked to unknown hidden/discoverable facts no longer expose hidden
  fact text even when `text_for_player` is populated.
- `MemorySummary` values added directly to `MemoryStore` default to
  `debug_only`, preventing raw event summaries from entering narrator context.
- Debug timeline data remains on debug endpoints/panels only.

### Authoring / Debug Boundary

Passed.

- Authoring and debug APIs are gated by explicit environment settings.
- Authoring APIs are local-only and file-whitelisted.
- Debug APIs expose raw deltas only when enabled and are separate from player
  APIs and narrator input.

## Known Limitations

1. Player-visible faction and relationship responses still include some raw
   numeric values. The frontend primarily displays bands/labels, but v0.6
   should move raw social metrics to debug-only surfaces.
2. `visible_state.faction_conflicts.conflict_tags` may hint at hidden social
   structure if authored incautiously. A player-safe label field is preferred.
3. Invalid mod manifest errors may still include local path text in some
   authoring error paths. This is local-only but should be sanitized.
4. `Narrator` receives `ActionResult.reason`; rule authors must keep reasons
   player-safe until `player_reason` and `debug_reason` are split.
5. Narrator prompt system text contains mojibake and should be rewritten in
   clean UTF-8. Code-level prompt inputs remain filtered.
6. Memory context is implemented and tested, but runtime `GameLoop` still calls
   `Narrator` with action-visible facts only. Future memory-to-narrator
   integration must route through `MemoryContextBuilder`.
7. NPC planning is intentionally lightweight and deterministic. It is not
   multi-agent LLM planning.
8. Economy/trade is minimal. There is no dynamic supply/demand economy,
   crafting, equipment, durability, or weight system.
9. Mod packaging is content-only. There is no online registry, hot reload, or
   arbitrary code execution.
10. Authoring UI is a textarea-based local tool, not a full schema-aware IDE.

## Acceptance Risks

No high-risk release blocker remains after the v0.5 blocker fix pass.

Residual accepted risks:

- Local authoring/debug tools can reveal hidden content by design and must
  remain disabled outside trusted local use.
- Some player-visible social payloads are more raw than ideal.
- Mod error path sanitization should be tightened before broader sharing.
- Prompt text readability should be fixed to reduce future maintenance risk.

These risks do not block a local-only v0.5 release.

## Recommended v0.6 Priorities

1. Build a richer content studio with structured forms instead of raw YAML.
2. Add a quest graph editor and stronger quest trigger validation.
3. Move raw reputation/relationship/conflict numbers to debug-only APIs.
4. Add player-safe labels for faction conflict and social summaries.
5. Sanitize mod validation errors and local path reporting.
6. Integrate runtime memory context through `MemoryContextBuilder` only.
7. Rewrite LLM prompts in clean UTF-8 and split player/debug action reasons.
8. Add optional embedding backend support behind provider abstractions.
9. Improve mod load-order UI and conflict previews.
10. Add scenario simulation runners and golden narrative regression tests.

## Final Status

v0.5 is accepted for local release.

Required verification passed:

- Backend: `360 passed`
- Frontend: production build passed

The release preserves the core project contract:

- LLM is language layer, not world judge.
- World engine remains the source of truth.
- Canonical changes go through `StateDelta`.
- Player actions and system consequences are recorded as events.
- Hidden/debug data is kept out of player APIs and narrator prompts.
- Authoring/debug/mod tooling remains local and gated.
