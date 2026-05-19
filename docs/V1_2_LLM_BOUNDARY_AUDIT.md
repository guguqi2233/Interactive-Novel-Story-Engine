# v1.2 LLM Boundary Audit

Date: 2026-05-19

Scope: v1.2 Visual Authoring Pro modules, v1.1 RP layer interactions, runtime
narrator/dialogue context, provider construction, and regression tests.

## Executive Summary

v1.2 passes the LLM permission boundary audit for acceptance. The Visual
Authoring Pro modules are deterministic authoring tools: they parse content,
build drafts, preview, validate, diff, merge, import/export, and save content
packs through validation gates. They do not call an LLM to generate authoritative
world facts, maps, quests, relationships, faction conflicts, prices, crime
consequences, templates, merges, or diffs.

The runtime LLM boundary remains unchanged: the LLM is used only through provider
abstractions for intent parsing, narration, memory summarization, and existing
playtest/fake-provider flows. LLM output still does not directly mutate
`GameState`; rules produce `StateDelta` and events. Prompt profiles and RP
profiles affect style/context summaries only and do not expand world authority.

No high-risk blocker was found.

## Audit Method

- Searched v1.2 authoring modules under `backend/app/engine/content`.
- Searched provider construction and direct provider calls.
- Checked narrator prompt assembly and visible fact filtering.
- Checked RP dialogue context construction for `npc_known_facts`,
  `private_self_summary`, hidden memory, and hidden fact filtering.
- Checked v1.2 integration tests and authoring tests for mock/local providers.
- Checked import/export, merge, diff, template wizard, and validation gate paths
  for deterministic validation and disk-write boundaries.

## Passed Items

1. v1.2 modules do not call the LLM

   Passed. v1.2 authoring modules do not import concrete LLM providers and do
   not call `generate_text` or `generate_json`. The only content-module exception
   found is the older `side_quest_generator.py`, which accepts an `LLMProvider`
   parameter and is not part of the v1.2 Visual Authoring Pro save/preview API.

2. Visual Map Editor Pro does not use the LLM to generate maps

   Passed. Map authoring parses, previews, validates, saves, and builds
   player-visible graph projections deterministically.

3. Quest Graph Editor Pro does not use the LLM to generate quests

   Passed. Quest graph authoring performs graph/YAML conversion, validation,
   and deterministic scenario draft generation. No provider call is used.

4. NPC Relationship Editor does not use the LLM to decide relationships

   Passed. Relationship graph editing validates IDs, ranges, hidden flags, and
   tone presets deterministically. RP tone preview fields do not change numeric
   relationship values.

5. Faction Conflict Editor does not use the LLM to decide faction conflict

   Passed. Faction conflict data is edited and validated as content data. No LLM
   diplomacy or conflict decision path was found.

6. Rumor / Crime Consequence Editor does not use the LLM to decide consequences

   Passed. Consequence authoring checks fact, faction, NPC, quest references,
   hidden text leakage, loops, and dedupe warnings deterministically.

7. Item / Economy Editor does not use the LLM for pricing

   Passed. Item/economy authoring validates prices, inventory refs, hidden shop
   visibility, trade policy, and balance warnings without provider calls.

8. RP Character Authoring UI does not let imported prompts override boundaries

   Passed. Character card import and RP character authoring classify prompt
   control text as unsafe. Safe export excludes `private_self_summary`,
   knowledge, hidden facts, taboo topics, debug state, and unsafe examples.

9. Dialogue Scene Editor does not use the LLM to create authoritative scene facts

   Passed. Dialogue scene templates are saved as content templates only. They
   validate participants, locations, visible required facts, forbidden hidden
   topics, and allowed `StateDelta` templates without starting a live dialogue
   session or calling a provider.

10. Group RP Scene Authoring does not let the LLM create hidden facts

    Passed. Group RP scene templates validate participants, roles, hidden public
    context leakage, dead participant policy, and turn-order policy
    deterministically. They do not create facts and do not call an LLM.

11. Template Wizard does not use the LLM to generate content

    Passed. Template Wizard uses static deterministic templates and variable
    validation. Preview does not write disk; apply requires validation.

12. Merge Assistant / Diff Review does not use the LLM to resolve conflicts

    Passed. Merge conflicts are detected by structured comparisons and stable
    hashes. Resolution choices are explicit `base`, `ours`, `theirs`, or
    `custom`; no LLM conflict resolution is present. Diff Review produces
    deterministic added/removed/changed/visibility/migration summaries.

13. Prompt profiles and RP profiles cannot expand LLM authority

    Passed. Studio config states prompt profiles may adjust style and
    temperature, not hidden facts or `GameState` authority. RP context builders
    exclude `private_self_summary` and taboo topic text from prompt-safe
    dialogue profile context.

14. No LLM output directly enters GameState

    Passed. Runtime LLM output goes through intent/narrator schemas and rule
    systems. Dialogue effects are produced by deterministic rule deltas. v1.2
    authoring drafts are content pack drafts, not active session mutation.

15. Narrator still receives only visible facts and narrator-safe memory

    Passed. `Narrator.render` receives a safe action result containing
    `success_level`, `reason`, and `visible_facts`, plus the explicit
    `visible_facts` list. Memory context filtering keeps hidden/debug memory out
    of narrator-safe context.

16. NPC dialogue receives only npc-known facts

    Passed. Dialogue and group dialogue context use NPC knowledge filtering and
    roleplay context policy. Existing tests verify hidden facts known by one NPC
    do not appear in another NPC's safe context.

17. Hidden facts are blocked from ordinary prompts

    Passed with watch items. Hidden facts are blocked from player-visible state,
    narrator-safe memory, ordinary dialogue context, player map, safe character
    exports, normal diff summaries, and v1.2 integration tests. Authoring debug
    views can inspect hidden content by design; those routes are gated by
    `ENABLE_AUTHORING_API`.

18. Provider factory remains the only provider selection entry

    Passed. Runtime session construction uses `create_llm_provider`. The factory
    is the selection point for `mock`, `local_stub`, `local_http`, and `openai`.
    v1.2 modules do not instantiate `OpenAIProvider` or `LocalHTTPProvider`
    directly.

19. Tests do not call real APIs

    Passed. v1.2 tests use `mock`, `local_stub`, or fake providers. The v1.2
    integration regression explicitly sets `llm_provider="local_stub"`. Existing
    LocalHTTP tests use fake transports rather than real network calls.

## Risk Items

### High Risk

No high-risk issue was found.

### Medium Risk

1. Existing side quest generator has an LLM-assisted path

   `backend/app/engine/content/side_quest_generator.py` accepts an
   `LLMProvider` and calls `generate_json`. This appears to be an older or
   separate assisted generation path, not a v1.2 Visual Authoring Pro editor
   save path. It is not currently evidence of a v1.2 boundary violation, but it
   is close enough to authoring that future wiring could accidentally treat LLM
   output as content.

   Recommendation: keep this module explicitly labeled as assisted draft-only.
   Any future API using it should require preview, validation gate, explicit
   save, and must never apply directly to active `GameState`.

2. Authoring debug surfaces can inspect hidden content

   This is allowed by the v1.2 boundary contract for local authoring/debug use,
   but it remains sensitive. Normal player UI and ordinary narrator/RP prompts
   must never consume these authoring payloads.

   Recommendation: continue testing normal-view redaction for Diff Review,
   Project Dashboard, ReferenceIndex, Character Pack safe export, and player
   APIs.

3. Prompt profiles are style-affecting and provider-affecting

   Prompt profiles can adjust style, prompt variants, and temperature. Current
   code and docs state they cannot add hidden facts or change world authority.
   The risk is future profile fields drifting into permission semantics.

   Recommendation: keep profile schema limited to style/provider filtering and
   temperature. Add regression tests if new profile fields are added.

### Low Risk

1. Narrator system prompt text appears encoding-corrupted in source.

   This does not appear to expand LLM authority, but it may reduce prompt clarity
   and make future boundary reviews harder.

   Recommendation: normalize prompt file encoding and add a small snapshot test
   for required boundary phrases in the narrator system prompt.

2. Diff Review validation issue summaries may include validation messages.

   Current normal summaries redact hidden entity details and visibility risks are
   structural. Continue avoiding hidden fact full text in validation messages
   that can surface in normal views.

   Recommendation: keep hidden leak reports structural in normal mode and reserve
   hidden text for explicit debug-only reports.

## Fix Recommendations

1. Add a dedicated test that scans v1.2 authoring modules and fails if they
   import concrete providers or call `generate_text` / `generate_json`.

2. Add a guardrail comment and test around `side_quest_generator.py` clarifying
   that LLM-generated side quests are draft-only and must pass validation before
   save.

3. Add narrator prompt boundary snapshot coverage after fixing prompt encoding.

4. Keep the Authoring Validation Gate as the only save/import/merge/apply gate
   and add regression coverage whenever a new v1.2 editor endpoint is added.

5. Keep all tests configured with `mock`, `local_stub`, fake providers, or fake
   LocalHTTP transports. Do not set `llm_provider="openai"` in tests except for
   pure config/status tests that do not instantiate a network provider.

## Acceptance Impact

Not blocking v1.2 acceptance.

The audit finds no direct LLM calls in v1.2 Visual Authoring Pro editor paths,
no LLM authority expansion through RP/prompt profiles, no LLM direct
`GameState` mutation, and no real API usage in v1.2 tests. The medium and low
items should be tracked as hardening tasks, but they do not block v1.2
acceptance.
