# v0.4 Acceptance Report

## Verdict

Accepted with non-blocking hardening risks.

v0.4 meets the release goal of upgrading the engine into a local narrative RPG prototype with structured social consequences, factions, rumors, crime/witness records, deterministic combat, life-state rules, NPC reactions, advanced memory retrieval, content validation, and frontend social/debug panels.

The core architecture remains intact:

- LLM is still a parser, narrator, and summarizer, not the world judge.
- The world engine remains the authoritative source of truth.
- Canonical state changes continue to use `StateDelta`.
- Player actions and system consequences are represented as `Event` entries.
- Player APIs use filtered `visible_state`.
- Debug timeline data remains isolated from Narrator.

## Verification Date

2026-05-17

## Verification Commands

Executed from repository root unless otherwise noted.

```powershell
python -m pytest
```

Result:

```text
257 passed
```

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
tsc -b && vite build succeeded
```

Additional content-pack validation:

```powershell
python scripts\validate_world.py mist_valley
```

Result:

```text
errors: 0
warnings: 1
suggestions: 0
```

The single warning is non-blocking: `sealed_letter` is reused across content types as both an item id and a quest id.

## Scope Accepted

### 1. Social Schema

Accepted.

`GameState` contains stable social-system fields for factions, reputation, rumors, crimes, witnesses, social consequences, and social flags.

Backward compatibility is covered by tests that load old-style state JSON with missing v0.4 social fields and fill defaults safely. SQLite save/load preserves v0.4 social fields.

`visible_state` does not expose hidden social records by default. Player-facing crime output is limited to known/reported/resolved summaries and excludes witness internals.

### 2. Faction Reputation

Accepted.

`factions.yaml` is supported by the content loader. Reputation is represented in structured state and changed through `StateDelta` using faction rule helpers.

Reputation bands are computed by deterministic rules. Hidden factions are filtered from `visible_state`.

Crime/social consequences and NPC reaction rules can consume faction reputation state.

Known caveat: visible faction responses currently include raw numeric reputation as well as the band. The frontend displays the band only. Moving raw numeric reputation to debug-only is recommended for v0.5 hardening.

### 3. Rumor Propagation

Accepted.

Rumors are structured as runtime state and can be loaded from optional `rumors.yaml` or created by rule consequences. Rumor propagation emits `StateDelta` values and is deterministic.

NPCs propagate only rumors they know, and dead/incapacitated NPCs are filtered from rumor propagation.

Player-visible rumor text uses `text_for_player`, already-visible fact text, or a vague fallback. Hidden fact text is not automatically revealed.

Rumor propagation is recorded through world/system events when tick deltas occur.

### 4. Crime / Witness

Accepted.

Crime classification is rule-owned. Witness detection is based on structured state such as location, visibility, light, cover, alertness, suspicion, and sneak metadata.

Hidden witnesses can affect deterministic consequences but are not exposed through player API or Narrator prompts. Crime state can trigger rumors, reputation changes, and NPC reactions.

Crime and witness state is covered by save/load tests.

### 5. Social Consequence Tick

Accepted.

World tick sequence is documented and implemented as:

1. NPC schedule
2. quest triggers
3. social consequence tick
4. NPC reactions
5. suspicion decay
6. delayed consequences
7. post-delayed quest triggers

Tick output is deterministic, produces `StateDelta` values, and records system events when there are changes. Crime consequence dedupe uses social flags to avoid repeated reputation loss and repeated consequences from the same crime.

Hidden consequences remain outside Narrator context.

### 6. Combat

Accepted.

`attack`, `defend`, and `flee` actions are available. Hit/miss/damage outcomes are determined by rules with deterministic RNG in tests, not by LLM.

Damage modifies HP/condition/status through `StateDelta`. Public assault or murder can create crime records. Combat state persists through SQLite save/load.

Combat does not call LLM for adjudication.

### 7. Life State

Accepted.

Player and NPC life state is structured with `alive`, `hp`, `max_hp`, `condition`, and `status_effects`.

Rules prevent dead/incapacitated NPCs from schedule movement, talking, rumor propagation, witnessing new crimes, and NPC reaction processing. The v0.4 release-blocking sneak observer issue was fixed: dead/incapacitated NPCs no longer affect sneak observation or receive sneak suspicion deltas.

Visible death/injury information remains filtered through `visible_state`.

### 8. NPC Reaction

Accepted.

NPC reactions are deterministic and based on known structured inputs such as witnessed crimes, known rumors, faction reputation band, relationship, and combat/life state.

NPCs do not react to unknown rumors/facts. Reactions emit `StateDelta` values and are captured in system tick events. Social flags prevent repeated reactions for the same source.

### 9. Advanced Memory Retrieval

Accepted.

`MemoryRecord` is structured with content, source events, tags, entity ids, fact ids, visibility, importance, and created turn.

Retrieval supports tags, entity ids, fact ids, substring, recency, and turn range. Memory store save/load is supported through SQLite repository memory methods.

Memory remains non-authoritative and does not replace `GameState` or `EventLog`. Hidden/debug memories are excluded from narrator/player contexts through explicit filters.

Known caveat: callers must use the safe filters when preparing narrator context. Current Narrator does not consume memory records directly.

### 10. Content Validation

Accepted.

The local validator runs with:

```powershell
python scripts\validate_world.py mist_valley
```

It checks schema and references across manifest, locations, NPCs, items, quests, facts, factions, and rumors. It covers exits, NPC locations, NPC faction ids, item placement conflicts, quest trigger references, fact `known_by`, rumor references, hidden fact leak warnings, schedule locations, and basic combat/life consistency.

Valid `mist_valley` has no errors. Invalid-world behavior and non-zero error exits are covered by automated tests.

### 11. Frontend

Accepted.

The React/Vite frontend includes:

- player-visible social panel for known factions, reputation bands, known rumors, and known crimes
- player-visible status/combat placeholders driven by backend `visible_state`
- debug panel with raw event timeline, state deltas, social/debug grouping, combat/injury grouping, and raw reputation delta display
- save/load and world selection controls

Debug-disabled behavior is handled gracefully. Debug data is shown only inside the debug panel and is not copied into story/narrative output.

Frontend build passes.

### 12. v0.4 Integration Tests

Accepted.

Integration coverage includes:

- social consequence flow from `mist_valley`
- hidden witness filtering
- public illegal actions producing crime/social consequences
- combat damage and crime integration
- dead/incapacitated NPC behavior
- memory retrieval safety
- save/load/replay preservation for v0.4 social state

## Boundary Review

### LLM Boundary

Passed.

v0.4 rule modules do not call LLM:

- faction reputation
- rumor propagation
- crime/witness
- social consequence tick
- combat
- life state
- NPC reactions
- content validation
- memory retrieval

LLM outputs remain schema-validated:

- `PlayerIntent`
- `NarrativeResult`
- `MemorySummary`

No LLM output directly modifies `GameState`.

Provider selection remains centralized through `create_llm_provider(settings)` and `LLM_PROVIDER`.

### StateDelta Boundary

Passed.

Player actions and system ticks produce `StateDelta` values for canonical mutations. `apply_delta` type-validates assignments and dictionary entries for structured runtime models such as crimes, rumors, witnesses, and combat records.

Clarification and unknown player inputs now record `Event` entries with `allow_empty_delta=True` while leaving state unchanged.

### Event Boundary

Passed.

Handled player actions are recorded as player events. World tick and crime consequence changes are recorded as system events. `SaveService.persist_step` now persists system events from `GameLoopResult`, preventing event loss in step-based persistence.

### Visibility Boundary

Passed with non-blocking caveats.

`visible_state` filters:

- hidden facts
- hidden objects before discovery
- hidden NPCs before discovery
- NPC secrets
- hidden witnesses
- hidden inactive quests
- hidden factions
- hidden/debug memory records

Debug API can expose raw `state_deltas`, but it is local-only and controlled by `ENABLE_DEBUG_API`. Debug information is not passed to Narrator.

### Save / Load / Replay

Passed within current scope.

SQLite save/load preserves v0.4 social, combat, life, event, and memory data. Replay tests apply stored event `state_deltas` and verify final v0.4 social state consistency for covered flows.

## Known Limitations

- No tactical grid combat.
- No multi-round autonomous NPC combat AI.
- No guard pursuit, arrest, trial, or full legal system.
- No economy, shops, crafting, equipment progression, armor, or weapon durability.
- No pathfinding or large-scale world simulation.
- No LLM-driven autonomous NPC planning.
- No vector database or embedding pipeline.
- Content validation reports issues but does not auto-fix YAML.
- Debug API has no production authentication and must remain local-only.
- Raw numeric faction reputation is still present in player API, though the frontend displays only the band.
- `ActionResult.reason` is still passed to Narrator and relies on rule authors to keep it player-safe.
- Memory summaries generated from hidden/debug event sources require careful visibility classification before becoming narrator context.
- Some legacy text/prompt files still contain mojibake; boundaries are enforced by code and tests, but prompt clarity should be cleaned up.

## Acceptance Risks

### Medium Risk: Raw Reputation In Player API

Player-visible faction response includes raw reputation value. This does not leak hidden faction ids, and the frontend displays only reputation band, but raw mechanical state should move to debug-only in v0.5.

### Medium Risk: ActionResult Reason Safety

Narrator receives `ActionResult.reason`. Current reasons are player-safe enough for v0.4, but the schema should split player-safe reason from debug/internal reason before richer rule systems are added.

### Medium Risk: Memory Summary Classification

Memory retrieval filters are safe, but `MemorySummary` content derived from raw event deltas can contain hidden details if callers store it as narrator-safe. v0.5 should make summary visibility classification explicit.

### Low Risk: Debug Panel Default Open

Frontend debug panel defaults open in the local prototype. Debug data remains isolated to debug UI, but default-closed behavior would be safer for playtesting.

### Low Risk: Content Id Reuse Warning

`mist_valley` currently reuses `sealed_letter` across item and quest ids. The validator reports this as a warning, not an error. It is acceptable for v0.4 but should be cleaned up if id namespaces are later unified.

## Recommended v0.5 Priorities

1. Split `ActionResult.reason` into `player_reason` and `debug_reason`.
2. Remove raw numeric reputation from player API or gate it behind debug API.
3. Add explicit memory visibility classification for summaries derived from hidden/debug events.
4. Clean prompt and legacy text mojibake into readable UTF-8.
5. Default frontend debug panel to closed for safer local playtesting.
6. Tighten `WorldLoader` reference validation to match the validator for containers and rumor NPC references.
7. Expand combat toward equipment, armor, healing, surrender, and multi-round NPC reactions only after keeping deterministic boundaries.
8. Add law/guard response systems if crime consequences become more prominent.
9. Consider optional vector memory backend while preserving local deterministic fallback.
10. Generate v0.4 release notes and final tag after freeze checks.

## Final Status

v0.4 is accepted for local release.

Required verification passed:

- Backend tests: `257 passed`
- Frontend build: passed
- Content validator on `mist_valley`: `0 errors`

No high-risk blocker remains after the release-blocking sneak/life-state fix and event persistence fix. Remaining items are hardening tasks suitable for v0.5 planning or a v0.4.x patch.
