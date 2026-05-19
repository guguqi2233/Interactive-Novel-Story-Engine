# Authoring Pro Boundary Contract

## Purpose

v1.2 Visual Authoring Pro adds richer local editors for maps, quests,
relationships, factions, rumors, crimes, economy data, RP characters, dialogue
scenes, templates, packages, branches, and draft history. These tools improve
creation workflow, but they do not become the world engine.

`GameState` remains the active runtime truth. Authoring data is content-pack
data, draft data, preview data, or validation data until a runtime system
explicitly loads it in a future session or a separately designed apply flow.

## Boundary Concepts

### authoring_draft

A proposed content change held in request payloads, temporary files, local draft
history, or editor state. A draft can be previewed and validated. It does not
modify active `GameState`, active saves, active sessions, or event history.

### preview_result

A read-only report generated from draft content. It may include normalized YAML,
diff summaries, migration impact, affected references, and validation output.
Preview never writes disk and never updates runtime sessions.

### validation_report

A deterministic schema/reference/visibility/safety report for content-pack data
or draft data. Validation never writes disk. Validation errors block save.
Validation warnings require explicit confirmation before save.

### explicit_save

An intentional local authoring action that writes validated content-pack files.
It is separate from preview and validate. It does not update active
`GameState`, active saves, or active game sessions.

### active_world_pack

The currently stored content-pack files under `worlds/{world_id}`. Save writes
may update this content after validation. Already-running sessions keep their
existing `GameState` until restarted, reloaded, or handled by a future explicit
apply design.

### active_game_state

The runtime state inside an active session or save. It changes only through the
world engine, `StateDelta`, and `Event` rules. Authoring drafts, previews,
validations, visual editor saves, imports, templates, and branch operations do
not directly modify it.

### migration_impact

A safe report that an authoring change may affect old saves or references, such
as deleted ids, renamed ids, changed exits, or changed schema expectations. It
is advisory in v1.2. It does not migrate saves by itself.

### hidden_authoring_field

Local creator-facing content that may contain secrets, spoilers, private RP
notes, debug-only data, hidden relationships, hidden facts, hidden witnesses, or
other non-player-facing material. Hidden authoring fields may be visible in
local authoring/debug surfaces, but not in player UI, ordinary narrator prompts,
or ordinary RP prompts.

### player_visible_content

Content that has passed visibility rules and can be shown to the player through
`visible_state`, player graph APIs, dialogue context, or narration. Hidden facts,
NPC secrets, hidden witnesses, hidden/debug memory, raw `state_deltas`, and RP
private fields are excluded unless deterministic rules explicitly make safe
content visible.

## Unified Save Flow

All v1.2 visual editors must follow this flow:

1. Build an `authoring_draft` from editor state.
2. Run preview to produce a `preview_result`; preview does not write disk.
3. Run validation to produce a `validation_report`; validation does not write
   disk.
4. If validation has errors, block save.
5. If validation has warnings, require explicit warning confirmation.
6. On explicit save, write only content-pack files.
7. Re-run validation after writing. If persisted validation fails, roll back the
   write.
8. Report `migration_impact` when ids, exits, schema, or references may affect
   existing saves.

## Apply To Active Session

Applying authoring output directly to an active session is not part of v1.2. It
must be separately designed before use and must still obey:

- deterministic rule decision
- `StateDelta`
- `Event`
- visibility filtering
- no LLM direct state mutation

The default policy blocks `apply_to_active_session`.

## Visibility And RP Rules

- Hidden authoring fields do not enter player UI.
- Hidden facts do not enter player `visible_state`.
- NPCs do not receive facts outside NPC knowledge rules.
- RP `private_self_summary`, taboo topics, hidden examples, debug examples, and
  unsafe import text do not enter ordinary player-facing context.
- Authoring/debug APIs remain local-only and must stay separated from player
  APIs.

## LLM Boundary

Visual Authoring Pro does not grant the LLM new authority. Any future
LLM-assisted authoring may produce drafts only. It must go through
`LLMProvider`, schema validation, preview, validation, explicit save, and the
same boundary checks as hand-authored content.

`provider_factory` remains the only runtime LLM provider entry.

## Import / Export Boundary

Import/export and package flows are authoring operations. They must not execute
arbitrary code, read `.env`, API keys, database files, logs, or arbitrary system
files, or auto-overwrite worlds without explicit confirmation. Imported
character cards, lorebooks, templates, and packages remain drafts until
validated and explicitly saved.
