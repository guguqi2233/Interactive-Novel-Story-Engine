# v2.3 Visibility / Tavern / Cross-Mode Audit

## Verdict

PASS.

v2.3 Tavern Studio MVP keeps normal Tavern context, prompts, UI, reports, and
cross-mode references separated from hidden World facts, NPC secrets, private
persona fields, debug memory, raw `state_deltas`, and active World state. No
high-risk visibility leak or cross-mode bypass was found.

## Verification Date

2026-05-22

## Scope Reviewed

- `docs/V2_3_ROADMAP.md`
- `backend/app/platform/tavern_studio.py`
- `backend/app/platform/shared_libraries.py`
- `backend/app/evals/tavern_boundary.py`
- `backend/app/main.py` Tavern routes
- `backend/tests/test_v23_tavern_studio_mvp.py`
- `backend/tests/test_v23_integration_regression.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`

## Passed Items

1. Hidden facts do not enter Tavern normal context.
   - `TavernPromptContext` validates against hidden-fact markers and unsafe
     prompt material.
   - v2.3 tests assert hidden fact text is absent from Tavern prompt context.

2. NPC secrets do not enter Tavern prompt.
   - `WorldNpcToTavernAdapterService` excludes `npc.secrets` and emits a
     warning that sensitive NPC fields were excluded.
   - Player-safe adapter mode rejects hidden/non-visible NPCs.

3. NPC unknown facts do not enter character prompt.
   - `TavernLoreContextBuilder` rejects lore entries whose linked fact ids are
     not in `npc_known_fact_ids`.
   - World NPC adapter filters NPC knowledge by `player_visible_fact_ids`.

4. WorldBible hidden entries are filtered.
   - `TavernLoreContextBuilder` excludes entries with hidden, authoring-only,
     or debug-only visibility and excludes `HIDDEN` / `AUTHORING_NOTE` entry
     types from normal Tavern context.

5. Lorebook hidden entries are filtered.
   - `TavernLorebookEntry.safe_entry()` returns `None` unless the entry is
     public or tavern-safe and `safe_for_tavern`.
   - Hidden lorebook entries are recorded only as excluded-debug metadata.

6. `private_persona_authoring_only` does not enter prompt/export paths.
   - `TavernRPProfile.safe_summary()` omits the private persona field.
   - `TavernPromptContextBuilder` only uses safe summaries.
   - Tests assert private persona text does not appear in prompt context.

7. Timeline hidden / authoring-only events are not included in Tavern normal
   context.
   - v2.3 does not wire Timeline or EventLog event bodies into Tavern prompt
     context.
   - Tavern context is built from session safe messages, safe memory, safe
     lore, safe profiles, scene mood, and relationship tone.

8. EventLog raw `state_deltas` do not enter Tavern context.
   - Tavern prompt validation rejects `state_delta` / `state_deltas`.
   - Tavern boundary evals include raw StateDelta leak detection.
   - v2.3 Tavern services do not read EventLog for normal RP prompts.

9. Tavern memory hidden/debug data is filtered.
   - `TavernMemoryRecord.safe_summary()` returns data only for
     `TAVERN_SAFE` visibility.
   - Hidden, debug-only, and authoring-only memory records do not enter normal
     Tavern memory context.

10. Hidden relationship state is not used for relationship tone context.
    - `RelationshipToneService.derive_tone_from_world_relationship_safe()`
      returns `None` for `hidden_relationship` or hidden visibility.
    - Tone changes are proposals and do not modify World relationship state.

11. Tavern to World Proposal does not bypass validation.
    - `TavernToWorldProposalService.validate_proposal()` rejects invalid target
      refs, path traversal-like refs, secrets, and StateDelta material.
    - v2.3 has no proposal apply-to-World path.

12. Tavern messages do not become World facts.
    - `SingleCharacterChatService` appends messages to Tavern repository only.
    - Generated replies are saved as `TavernMessage`, not as EventLog entries,
      facts, or content pack records.

13. CrossModeLink does not expose hidden targets in normal view.
    - `CrossModeLink.safe_summary()` returns `None` when the link is hidden.
    - Tavern-created links reference proposal/draft objects; they do not copy
      target hidden content into normal summaries.

14. Tavern Quality/Safety normal report does not print hidden text.
    - `TavernBoundaryEvalReport.model_dump_normal()` redacts serialized details.
    - Boundary eval results expose rule ids and issue codes, not raw hidden
      payloads.

15. Frontend Tavern UI does not display hidden/debug details.
    - Tavern UI consumes safe Tavern API responses for characters, sessions,
      messages, scene presets, and chat safety notes.
    - It displays explicit text that Tavern data does not include API keys,
      hidden facts, raw env, or raw `state_deltas`.
    - No Tavern frontend path directly reads local files or raw World state.

16. World Mode `visible_state` is not directly affected by Tavern Mode.
    - Tavern code paths do not call `apply_delta`, mutate `GameState`, or
      append EventLog.
    - Cross-mode world effects remain proposals.

## Possible Leak Paths Reviewed

- Character card import `creator_notes` and `system_prompt_like_text`.
- RP profile private persona fields.
- WorldBible hidden and authoring-only entries.
- Lorebook hidden entries and NPC-unknown fact refs.
- Tavern memory hidden/debug/authoring-only records.
- Relationship tone derived from hidden World relationship state.
- Tavern-to-World proposal normal summaries.
- World NPC to Tavern adapter player-safe output.
- CrossModeLink normal summaries.
- Tavern boundary eval normal reports.
- Tavern frontend rendering of characters, sessions, messages, chat safety
  notes, and scene presets.

## High-Risk Leaks

None found.

## Medium-Risk Leaks

None blocking.

The main medium-watch area is future expansion: if Timeline/EventLog context is
added to Tavern prompts later, it must go through the same safe-summary filter
used by Novel EventLog import and must never include raw `state_deltas`,
hidden/debug events, or authoring-only timeline notes.

## Low-Risk Issues

1. Tavern UI still contains wording that Tavern Studio MVP is "coming in v2.3"
   in one project mode card while the MVP implementation now exists. This is a
   documentation/UI wording sync issue, not a visibility leak.
2. The hidden-text filters are deterministic and fixture-backed. They should be
   expanded with more paraphrase and per-character knowledge cases if v2.4 adds
   full multi-character generation.

## Recommendations

1. Keep all future Tavern prompt fields derived from safe summary methods.
2. Add a dedicated Tavern Timeline/EventLog safe context builder before exposing
   timeline or EventLog-derived material to Tavern prompts.
3. Keep Tavern-to-World apply out of v2.3. Any future apply path must require
   explicit validation and World Engine `StateDelta` / `EventLog` handling.
4. Update frontend wording during v2.3 documentation/UI polish so implemented
   MVP panels are not described as future-only.

## Acceptance Impact

This audit does not block v2.3.

Final status: PASS, with only non-blocking wording and future-expansion
recommendations.
