# v1.1 Visibility / RP Context / Memory Audit

## Verdict

v1.1 currently preserves the v1.0 visibility boundary for player state,
roleplay context, group RP, and RP memory. Reviewed player-facing and RP prompt
builders do not expose raw `state_deltas`, hidden facts, debug memory, NPC
private profile fields, or unsafe imported lore by default.

No high-risk leak blocks v1.1 acceptance.

Verification date: 2026-05-19

Reviewed areas:

- `backend/app/session_store.py`
- `backend/app/llm/context_builder.py`
- `backend/app/llm/narrator.py`
- `backend/app/roleplay/dialogue.py`
- `backend/app/roleplay/example_dialogues.py`
- `backend/app/roleplay/lorebooks.py`
- `backend/app/roleplay/tavern_compat.py`
- `backend/app/playtesting/rp_regression.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- v1.1 RP unit/eval/integration tests

## Passed Items

1. **Hidden facts do not enter `visible_state`.**
   - `build_visible_state` includes only `state.player_visible_facts` in
     `known_facts`.
   - Visible NPCs, objects, quests, rumors, crimes, relationships, faction
     conflicts, and combatants are filtered through their respective visibility
     rules.
   - `visible_state` does not include raw `GameState`, raw events, or
     `state_deltas`.

2. **Hidden facts do not enter RP prompt context by default.**
   - Dialogue context uses `get_npc_context_for_dialogue` and
     `RoleplayContextPolicy`.
   - The returned `DialogueContext.safe_context_summary` reports counts and
     safe tone/emotion summaries rather than raw hidden fact text.
   - Group RP uses per-participant context and safe summaries.

3. **NPC secrets do not enter player context.**
   - `private_self_summary` is excluded from visible state and
     `NPCDialogueProfileContext`.
   - `taboo_topics` are counted as authoring constraints and are not copied into
     player-facing prompt summaries.

4. **NPC unknown facts do not enter that NPC's dialogue context.**
   - Dialogue context fact ids come from NPC knowledge plus roleplay policy
     filtering.
   - Tests cover NPC hidden/unknown fact exclusion in focused dialogue and
     group RP.

5. **Hidden memory does not enter RP memory context.**
   - `RPMemoryContextBuilder` rejects `MemoryVisibility.HIDDEN`.
   - Memory attached to hidden or player-unknown facts is excluded even if the
     memory visibility itself is narrator-safe.

6. **Debug memory does not enter RP memory context.**
   - `RPMemoryContextBuilder` rejects `MemoryVisibility.DEBUG_ONLY`.
   - Exclusion reasons are returned only when the builder is explicitly created
     with debug reasons enabled.

7. **`private_self_summary` is not player-facing by default.**
   - Safe profile context uses public persona and voice fields.
   - Visible state does not include `rp_profile` or `voice_profile` raw payloads.
   - Tavern safe export omits `private_self_summary`.

8. **Example dialogue hidden facts are filtered.**
   - `build_example_dialogue_context` selects only `prompt_safe` entries.
   - If an example references a fact, both player visibility and NPC knowledge
     are required.
   - `authoring_only`, `debug_only`, and `unsafe` examples do not enter prompt
     context.

9. **Lorebook hidden entries are classified and isolated.**
   - `LorebookClassifier` splits entries into flavor, structured fact
     candidates, hidden fact candidates, and unsafe entries.
   - `flavor_context_from_lorebook_report` returns only flavor safe summaries.
   - Hidden and unsafe entries require authoring review and are not added to RP
     prompts by default.

10. **Group RP context does not cross-contaminate NPC knowledge.**
    - `GroupDialogueManager.build_participant_context` builds one context per
      NPC.
    - Tests verify an NPC that knows a hidden fact may have that fact id in its
      own known facts while another NPC does not, and safe summaries do not
      print hidden ids/text.

11. **Emotional state does not leak hidden reason text.**
    - `EmotionalState` stores structured emotion/tone fields rather than raw
      hidden cause text.
    - Dialogue context uses safe emotion summaries.
    - Emotion rule metadata is on `StateDelta`, not player-facing RP context.

12. **Relationship tone does not leak hidden relationship details.**
    - Relationship tone summaries are derived expression bands and do not
      include hidden relationship ids or hidden fact tags.
    - Hidden relationships remain out of the player graph.

13. **RP panel uses safe API fields.**
    - Frontend `DialogueModeResponse` and `GroupDialogueSceneResponse` consume
      `DialogueContext`, `GroupParticipantContext`, and `VisibleState`.
    - The RP panel displays safe emotional/tone/mood/topic summaries and does
      not fetch debug event payloads or raw `state_deltas`.

14. **Tavern safe export does not default-export hidden facts.**
    - Safe character export excludes `private_self_summary`.
    - Safe lorebook export includes only public facts.
    - Authoring-debug mode still redacts hidden/private details in the current
      implementation.

15. **RP regression reports do not print hidden text in normal fields.**
    - `RPRegressionReport` redacts hidden fact text in failure and leak
      summaries.
    - `model_dump_normal` strips debug-only hidden detail fields from nested
      quality reports.

16. **Narrator cannot see raw `state_deltas`.**
    - `Narrator.render` sends a reduced action result payload with
      `success_level`, `reason`, and `visible_facts`.
    - `ActionResult.hidden_facts` and raw state delta payloads are not included
      in narrator messages.

## Possible Leak Paths

1. **Misclassified narrator-safe/RP memory content.**
   - `RPMemoryContextBuilder` correctly filters by `visibility`, fact bindings,
     NPC knowledge, and hidden-source tags.
   - However, if a memory record is incorrectly marked `NARRATOR_SAFE` and has
     no `fact_ids` linking it to a hidden fact, the builder cannot reliably
     infer that its free text is secret.
   - This is a content hygiene risk rather than a code bypass.

2. **Player-visible relationship tags.**
   - `build_visible_state` returns tags for relationships that are already
     visible to the player.
   - Hidden relationships are filtered, but a visible relationship could still
     carry an author-provided tag that contains spoiler-like text.
   - Relationship tone summaries are safer than raw tags and strip hidden-tag
     details, but visible-state relationship tags should remain subject to
     content validation.

3. **Authoring UI intentionally displays authoring content.**
   - Authoring pages may show raw YAML and hidden authoring fields by design.
   - This is acceptable for local authoring but must remain visually and
     functionally separate from player RP panels.

4. **Lorebook and character card classifiers are rule-based.**
   - They catch explicit secret/spoiler/prompt-injection markers, but ambiguous
     hidden content may require author review.

## High-Risk Leaks

None found.

No reviewed path exposes hidden facts, NPC secrets, hidden/debug memory, raw
`state_deltas`, or hidden relationships to player-visible state or ordinary RP
prompt context by default.

## Medium-Risk Leaks

None blocking.

The main medium-risk category is content misclassification: free-text memory,
relationship tags, imported lore, or public persona fields can contain spoilers
if an author places secret text into fields that are explicitly treated as safe.
Existing tests and validators reduce this risk, but they cannot perfectly infer
all semantic secrets.

## Small Issues

1. **`RPRegressionStepRecord.input_text` stores player inputs.**
   - Current RP regression tests avoid hidden text and reports redact known
     hidden fact text in failure/leak summaries.
   - If a future regression scenario deliberately places hidden text in
     `input_sequence`, normal report output could include the player's probing
     input. Prefer safe paraphrases for secret-probing scenario input text.

2. **Safe RP memory summaries include safe memory content.**
   - This is intended behavior for narrator-safe memory.
   - It depends on correct memory visibility/fact tagging.

3. **Authoring-debug Tavern export mode name can sound permissive.**
   - Current implementation still redacts private/hidden details. Documentation
     should keep that clear.

## Recommended Fixes

No release-blocking fixes are required.

Recommended non-blocking follow-ups:

1. Add validation or linting for player-visible relationship tags that include
   `hidden_fact:`, `secret`, `spoiler`, or known hidden fact ids.
2. Add a memory-ingest helper that requires `fact_ids` for memories containing
   known hidden fact text, so RP memory filtering can make stronger decisions.
3. Redact or omit `RPRegressionStepRecord.input_text` from future normal report
   API responses if secret-probing scenarios start using literal hidden text.
4. Keep authoring/debug RP panels visually separate from player RP panels and
   avoid reusing raw authoring payload components in player UI.
5. Continue adding classifier fixtures for subtle prompt injection and spoiler
   phrasing in character cards and lorebooks.

## v1.1 Acceptance Impact

This audit does not block v1.1.

v1.1 acceptance should still require:

- `python -m pytest`
- frontend build
- RP boundary evals
- RP regression playtests
- no hidden text in normal reports
- no raw state deltas or debug memory in player/RP prompt surfaces
