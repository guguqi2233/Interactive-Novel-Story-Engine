# v1.1 LLM Boundary Audit

## Verdict

v1.1 currently preserves the v1.0 LLM authority boundary. The Roleplay
Immersion Layer adds expressive context, import classifiers, dialogue/session
managers, RP memory filtering, prompt style profiles, and output consistency
checks, but the reviewed implementation does not make the LLM a world judge and
does not allow LLM output to directly mutate `GameState`.

This audit does not identify any high-risk issue that blocks v1.1 acceptance.

Verification date: 2026-05-19

Reviewed areas:

- `docs/V1_1_ROADMAP.md`
- `docs/ROLEPLAY_BOUNDARY.md`
- `backend/app/roleplay/*`
- `backend/app/llm/narrator.py`
- `backend/app/llm/context_builder.py`
- `backend/app/llm/prompt_profiles.py`
- `backend/app/llm/provider_factory.py`
- `backend/app/llm/local_provider.py`
- `backend/app/core/game_loop.py`
- `backend/app/main.py`
- v1.1 RP tests and integration tests under `backend/tests`

## Passed Items

1. **v1.1 modules do not introduce new real LLM calls.**
   - Character card import, lorebook import, Tavern compatibility, RP scenario
     templates, example dialogue handling, RP memory context, Dialogue Mode,
     Group RP, scene mood presets, RP output consistency checks, RP boundary
     evals, and RP regression playtests are deterministic local code.
   - Existing LLM calls remain in established components such as
     `IntentParser`, `Narrator`, `MemorySummarizer`, and injected provider-based
     tooling.

2. **Character Card Importer does not execute external prompt text.**
   - `CharacterCardImporter` parses local JSON/YAML/text, normalizes fields,
     classifies unsafe/system-prompt content, and produces candidates.
   - `system_prompt`, `creator_notes`, jailbreak-like instructions, API-key
     requests, state mutation instructions, script-like content, and remote URL
     patterns are classified as unsafe or rejected.
   - Preview is draft-only. Apply requires authoring API, explicit confirmation,
     and validation.

3. **Lorebook Import does not put unsafe entries into prompts.**
   - `LorebookClassifier` classifies entries into `flavor_lore`,
     `structured_fact_candidate`, `hidden_fact_candidate`, and `unsafe_entry`.
   - `flavor_context_from_lorebook_report` returns only safe summaries from
     flavor entries.
   - Hidden and unsafe entries are not promoted into narrator or dialogue
     context by default.

4. **RP Profile cannot change fact permissions.**
   - `RPProfile` fields are expression metadata.
   - `private_self_summary` is excluded from player-visible state and safe
     dialogue profile context by default.
   - `taboo_topics` are counted or treated as authoring constraints; they do not
     grant NPC knowledge.

5. **Voice Profile only affects expression.**
   - `VoiceProfile` fields such as tone, catchphrases, sentence length, and
     speech habits feed safe dialogue profile summaries.
   - They do not alter `ActionResult`, `StateDelta`, relationship numbers, NPC
     knowledge, or quest state.

6. **Emotional State is not written by LLM output.**
   - `emotional_state` is structured NPC state.
   - Emotion changes come from deterministic rules in `app.engine.rules.emotions`
     and are represented as `StateDelta`.
   - Dialogue Mode can trigger emotion deltas from rule-side keyword checks, not
     from generated LLM text.

7. **Relationship Tone does not write relationship values.**
   - `RelationshipTone` is derived from relationship state, emotion, and safe
     rule-side signals.
   - Tone modifiers return expression-only tone objects and do not change
     `RelationshipState`.
   - Canonical relationship value changes still require `StateDelta`.

8. **Dialogue Mode does not let LLM directly modify `GameState`.**
   - `DialogueManager.continue_dialogue` parses local player input and emits
     deterministic relationship/emotion deltas.
   - Deltas are applied with `apply_delta` and recorded in an `Event`.
   - No generated LLM dialogue text is used as a source of state mutation.

9. **Group RP keeps NPC context isolated.**
   - `GroupDialogueManager.build_participant_context` builds context per NPC.
   - Each participant context is filtered through NPC knowledge and the
     roleplay boundary policy.
   - Dead/incapacitated NPCs are rejected from ordinary group scenes.

10. **Scene Mood cannot change `ActionResult`.**
    - `SceneMoodPreset` contributes compact style summaries only.
    - Existing tests verify mood summaries do not mutate `GameState` and do not
      override action failure/success semantics.

11. **Example Dialogue is not authoritative.**
    - `ExampleDialogue` uses explicit visibility and fact-policy fields.
    - Only `prompt_safe` entries can be selected for prompt context.
    - Entries mentioning unavailable facts are filtered. Example dialogue does
      not add facts or NPC knowledge.

12. **RP Memory Context filters hidden/debug memory.**
    - `RPMemoryContextBuilder` excludes `hidden` and `debug_only` memory.
    - Memory bound to hidden or player-unknown facts is excluded.
    - Memory remains advisory and does not update `GameState`.

13. **RP Prompt Profile cannot enable hidden facts.**
    - `RPPromptProfile.hidden_fact_policy` and
      `state_modification_policy` are constrained to `deny`.
    - `PromptProfile` validation rejects prompt-profile text that attempts to
      weaken visibility or GameState boundaries.

14. **RP Output Consistency Checker covers key overreach patterns.**
    - `RPOutputConsistencyChecker` checks hidden fact leakage, NPC unknown fact
      mentions, invented item/NPC/location ids, dead/incapacitated NPC speech,
      contradiction with `ActionResult`, unauthorized relationship changes,
      unauthorized quest completion, and raw debug/state-delta leakage markers.
    - It is deterministic code, not an external LLM judge.

15. **Tavern import does not trust external system prompts.**
    - Tavern compatibility reuses character card and lorebook classification.
    - Import preview is local-only and draft-only.
    - Apply requires explicit confirmation and validation.

16. **No LLM output directly enters `GameState`.**
    - Reviewed RP managers do not consume provider output for authoritative
      state transitions.
    - Existing `Narrator` returns `NarrativeResult` only.
    - Existing `IntentParser` returns structured intent, which is then resolved
      by rules.

17. **Narrator remains limited to visible facts and safe action result fields.**
    - `Narrator.render` passes a reduced `ActionResult` payload containing
      `success_level`, `reason`, and `visible_facts`.
    - `hidden_facts` from `ActionResult` are not included in narrator messages.

18. **NPC dialogue context is scoped to known facts.**
    - Dialogue and group context builders use `get_npc_context_for_dialogue`,
      `RoleplayContextPolicy`, and `npc_known_facts`.
    - Integration tests cover NPC unknown fact filtering and group context
      isolation.

19. **Provider factory remains the production provider selection path.**
    - Production settings still go through `create_llm_provider`.
    - Tests may instantiate fake/local provider harnesses directly, including
      `LocalHTTPProvider` with fake transport, but this does not represent
      business routing.

20. **Tests do not call real APIs.**
    - v1.1 tests use deterministic local code, `FakeLLMProvider`,
      `LocalStubProvider`, or fake transports.
    - RP boundary evals and regression playtests use fake outputs rather than
      external LLM judges.

21. **Schema failures are explicit.**
    - Prompt profiles, RP profiles, voice profiles, local providers, character
      cards, lorebooks, example dialogue, and Tavern resources raise clear
      validation errors or return structured validation reports.

## Risk Items

1. **Dialogue Mode has a checker hook, but no full LLM dialogue generation path
   yet.**
   - Current `/game/dialogue/continue` returns a local generic narrative string
     and validates the player input as a `RoleplayOutputCandidate`.
   - This is safe for v1.1 because there is no LLM-generated dialogue output to
     mutate state or leak hidden facts.
   - If future work adds real LLM dialogue text, that output must be routed
     through `RPOutputConsistencyChecker` before display and must remain
     non-authoritative.

2. **Safe summaries can contain style/free-text fields.**
   - Public persona, voice tone, scene mood labels, and flavor lore summaries
     are allowed to affect expression.
   - They are non-authoritative, but content authors could accidentally put
     spoilers into fields meant to be public style.
   - Existing validators and tests cover many unsafe/hidden cases; continued
     schema validation is important.

3. **Character card and lorebook classification is rule-based.**
   - This is correct for no-LLM boundary control, but it is conservative rather
     than semantically perfect.
   - Ambiguous hidden content may require manual review. This is a known local
     authoring limitation, not an LLM authority issue.

4. **Tavern export supports safe summaries, not full private authoring export.**
   - Safe export avoids credentials, save data, raw state, and hidden facts.
   - A future authoring-debug export mode would need explicit warnings and
     separate tests if it ever includes hidden material.

## High-Risk Issues

None found.

No reviewed v1.1 module gives an LLM direct write access to `GameState`, direct
relationship/emotion mutation authority, hidden fact access outside visibility
rules, or provider selection outside the established abstraction.

## Medium-Risk Issues

None blocking.

The main medium-risk area is future integration: if a later Dialogue Mode
implementation starts calling an LLM for NPC lines, the output checker must be
made mandatory before display, and generated text must never be used as the
source of `StateDelta`.

## Small Issues

1. **The current dialogue API uses generic local response text.**
   - This is safe but not yet a complete RP generation pipeline.
   - Documentation and acceptance should keep describing it as a bounded local
     RP layer, not as autonomous LLM character simulation.

2. **Rule-based import classification is intentionally approximate.**
   - Unsafe/system-prompt patterns are caught, but subtle spoilers may still
     require author review.
   - This should remain documented as a local authoring limitation.

3. **Tests directly instantiate local/fake providers in harnesses.**
   - This is acceptable for deterministic tests, but production/business code
     should continue using the provider factory.

## Recommended Fixes

No release-blocking fixes are required.

Recommended non-blocking follow-ups:

1. Add a guardrail test for any future endpoint that returns generated RP text:
   assert it calls `RPOutputConsistencyChecker` before player display.
2. Keep expanding validation for RP profile, scene mood, lorebook, and example
   dialogue fields that may contain accidental spoiler text.
3. Document the current Dialogue Mode response as local bounded RP scaffolding
   until real provider-backed dialogue generation is implemented.
4. Consider adding a static audit test that flags production imports of concrete
   LLM providers outside `provider_factory.py`, while allowing test harnesses.

## v1.1 Acceptance Impact

This audit does not block v1.1 acceptance.

Acceptance remains conditional on the normal release checks:

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- v1.1 visibility/privacy/security audits
- no real API keys or hidden content in normal reports
- no later code changes that route LLM output into authoritative state
