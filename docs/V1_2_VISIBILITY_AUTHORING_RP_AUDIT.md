# v1.2 Visibility, Authoring, and RP Audit

Date: 2026-05-19

Scope: v1.2 Visual Authoring Pro visibility boundaries, authoring/player UI
separation, RP prompt safety, hidden content redaction, draft history, diff,
merge, reference picker, character pack export, template wizard, validation
gate, and narrator prompt boundaries.

## Executive Summary

v1.2 is mostly aligned with the visibility and RP boundary contract. Player
runtime surfaces are well protected: hidden facts, hidden relationships, hidden
faction conflicts, hidden quests, hidden map edges, hidden shop items, raw
`state_deltas`, and RP private fields are filtered from player-facing state or
prompt contexts by dedicated runtime builders and tests.

No player-facing high-risk leak was found.

Two authoring-normal-view risks should be tracked before final polish:

- Merge Assistant conflict payloads currently include full `base`, `ours`, and
  `theirs` entity dictionaries. On authoring routes this is useful for conflict
  resolution, but a normal authoring view can accidentally display hidden fact
  text or private RP fields unless the frontend/backend uses a redacted conflict
  projection.
- ReferenceIndex marks hidden references, and hidden facts use redacted labels,
  but some hidden reference kinds, especially hidden rumors/factions/items, can
  still expose labels that may be sensitive if content authors put hidden text in
  those fields.

These are medium risks because they are gated authoring surfaces, not player
APIs or prompts. They do not block v1.2 if documented as authoring/debug-only
and followed by redaction hardening, but they should be fixed before treating
normal authoring views as safe for spoiler-free browsing.

## Audit Method

- Reviewed `build_visible_state` player API construction.
- Reviewed runtime visibility rules for quests, relationships, faction
  conflicts, map graphs, and shop inventory.
- Reviewed RP context builders, roleplay boundary checks, and RP consistency
  checks.
- Reviewed v1.2 authoring modules for normal/debug view handling.
- Reviewed Draft History, Content Diff Review, Merge Assistant, Character Pack
  Builder, Template Wizard, ReferenceIndex, and Authoring Validation Gate.
- Reviewed regression and eval coverage for hidden information leaks.

## Passed Items

1. Hidden facts do not enter player `visible_state`

   Passed. `build_visible_state` only includes facts from
   `state.player_visible_facts`. World loading keeps hidden facts out of that
   set by default. Existing hidden-info evals and v1.2 integration tests cover
   hidden fact text not appearing in player state.

2. Hidden facts do not enter ordinary RP prompt context

   Passed. RP memory and dialogue context builders filter hidden/debug memory
   and unknown facts. `RoleplayContextPolicy`, `RPOutputConsistencyChecker`, and
   RP boundary evals catch hidden fact leakage and NPC unknown fact mentions.

3. `private_self_summary` does not enter player context by default

   Passed. `build_npc_dialogue_profile_context` intentionally excludes
   `private_self_summary` and taboo topic text. RP Character Authoring validates
   that `private_self_summary` remains hidden and safe export excludes it.

4. Hidden relationship does not enter player graph

   Passed. Player visible state uses `get_visible_relationships`, and content
   validation catches `hidden_relationship` combined with `known_by_player`.
   Social graph authoring also tracks hidden relationship fields separately.

5. Hidden faction conflict does not enter player graph

   Passed. Player visible state uses `get_visible_faction_conflicts`, which
   filters by player-known faction conflict visibility. Faction authoring
   exposes visibility fields as content data and validates hidden faction
   boundaries.

6. Hidden quest/objective does not enter player UI

   Passed. Player visible state uses `get_visible_quests`; hidden quests remain
   out of player UI. Quest validation detects public quest text that reveals
   hidden facts. Hidden objective fields are authoring data, not player
   visible objectives.

7. Hidden map edge does not enter player map

   Passed. Player map graph projection uses
   `build_player_visible_map_visual_graph`, and tests cover hidden edges being
   filtered. Validation emits warnings for edges touching hidden visual
   locations.

8. Hidden shop item does not enter player shop UI

   Passed. Economy rules filter shop inventory through item visibility.
   Item/Economy authoring rejects hidden or non-player-visible items in player
   shop inventory with `hidden_item_in_player_shop`.

9. Authoring editors are isolated from player UI

   Passed. Authoring endpoints are gated by `ENABLE_AUTHORING_API`; player
   routes do not expose ReferenceIndex, authoring draft history, editor graphs,
   or debug authoring payloads. v1.2 integration tests verify disabled
   authoring API behavior and player API non-exposure.

10. Draft History does not save API keys

    Passed. Draft History stores authoring draft snapshots only and rejects
    content containing API-key/config markers such as `api_key`,
    `llm_api_key`, `openai_api_key`, `database_url`, and test secret
    placeholders.

11. Content Diff normal view redacts hidden details in entity summaries

    Passed with watch item. `ContentDiffReview` uses safe summaries for hidden
    or discoverable entities and produces structural visibility risk messages.
    Normal summaries do not intentionally include full hidden details.

12. Character Pack safe export does not include hidden facts

    Passed. Character Pack Builder safe export excludes hidden fact candidates
    by default, excludes credentials, rejects executable content and traversal,
    and does not import hidden facts into player-visible content by default.

13. Template Wizard does not write hidden fields into player-facing content

    Passed. Template Wizard uses deterministic templates, preview is read-only,
    apply requires validation, and generated content is checked by world
    validation before save/apply. No LLM or hidden fact injection path was
    found in the wizard itself.

14. Reference Picker marks hidden refs

    Passed. `ReferenceIndexItem` has explicit `hidden` and `player_visible`
    fields. Hidden facts use fact IDs rather than hidden text as labels and
    mark `text_redacted=true` in authoring-safe metadata.

15. Authoring Validation Gate blocks high-risk hidden leaks

    Passed. `AuthoringValidationGate` scans validation errors/warnings for leak
    and hidden fact risks, blocks by default, and appends
    `authoring_gate_hidden_leak_blocked` unless an explicit debug override is
    supplied.

16. Narrator cannot see raw `state_deltas`

    Passed. `Narrator.render` sends a safe action result with success level,
    reason, and visible facts only. Narrative boundary evals assert raw
    `state_deltas` do not enter narrator prompts or player API.

## Possible Leak Paths

1. Merge Assistant conflict payloads expose full conflicting entities

   `MergeConflict` includes `base`, `ours`, and `theirs` dictionaries. If a
   hidden fact, hidden quest, hidden relationship note, or private RP profile
   changes in both branches, those full values can be returned to the authoring
   API. This is acceptable for explicit debug conflict resolution, but it is not
   safe as a normal authoring view without a redacted projection.

2. ReferenceIndex hidden labels are partly redacted by kind, not universally

   Hidden facts are redacted by label, but hidden rumors can use
   `text_for_player`, hidden factions can expose faction names, and hidden items
   can expose item names. These labels may be harmless in many packs, but the
   schema cannot guarantee they are spoiler-free.

3. Content Diff validation issue summaries include validation messages

   Current validators generally avoid full hidden text in normal messages, but
   the normal diff path includes `issue.message`. Any future validator that puts
   hidden text directly in a message could leak it through normal diff review.

4. Authoring preview YAML intentionally contains hidden/private fields

   Visual editors and RP authoring previews are local authoring surfaces. They
   can contain full draft YAML, including hidden fields. This is expected for
   debug/authoring workflows but must not be reused by player UI or ordinary RP
   prompt builders.

## High-Risk Leaks

No high-risk player-facing or prompt-facing leak was found.

## Medium-Risk Leaks

1. Merge Assistant normal-view redaction gap

   Risk: authoring normal view can display full hidden/private entity data if it
   renders `MergeConflict.base/ours/theirs` directly.

   Impact: authoring-only spoiler/private leak, not player API leak.

2. ReferenceIndex hidden label redaction gap for some hidden entity kinds

   Risk: hidden rumor/faction/item labels may reveal author-sensitive details.

   Impact: authoring-only spoiler leak in normal picker views.

3. Content Diff depends on validator message hygiene

   Risk: future validation messages containing hidden text could surface through
   `validation_issues`.

   Impact: authoring normal-view hidden detail leak.

## Low-Risk Issues

1. Validation warning wording differs by subsystem

   Some warnings say hidden items/edges are filtered, while v1.2 stricter
   authoring editors block certain hidden-player combinations. This is not a
   leak, but consistent severity language would make authoring decisions clearer.

2. Authoring debug and normal payloads are not always structurally distinct

   Several APIs return rich authoring data and rely on the frontend to decide
   what is normal vs debug. This is acceptable locally but should be hardened
   with explicit redacted response models for normal views.

## Fix Recommendations

1. Add a redacted merge conflict projection for normal view.

   Keep full `base/ours/theirs` only behind explicit debug mode or an
   `include_hidden_details=true` style flag. Normal responses should include
   entity IDs, conflict type, file name, visibility state, and safe summaries.

2. Redact ReferenceIndex labels for all hidden kinds by default.

   Suggested rule: if `hidden=true`, label should be the ID or a neutral
   placeholder unless the kind is known to be safe. Put original labels only in
   debug authoring mode.

3. Make Content Diff normal view strip validation messages for hidden/leak
   issues.

   Keep code/path/ref ID and structural risk labels. Avoid carrying arbitrary
   `issue.message` text into normal diff views when the issue is hidden/leak
   related.

4. Add regression tests for merge normal-view redaction and hidden ReferenceIndex
   labels.

   These should be deterministic and use temporary world packs with hidden fact
   text in branch conflicts and hidden rumor labels.

5. Continue enforcing Authoring Validation Gate for all save/import/merge/apply
   operations.

   The gate is currently the strongest cross-editor hidden leak barrier and
   should remain mandatory.

## v1.2 Blocking Assessment

Not blocking v1.2 for player/RP runtime acceptance.

Blocking status for spoiler-safe normal authoring browsing: partial. Player UI
and RP prompt surfaces are protected, but Merge Assistant and ReferenceIndex
should receive normal-view redaction hardening before claiming that every
authoring normal view is fully hidden-detail safe.
