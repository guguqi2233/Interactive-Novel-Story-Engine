# v3.2 Tavern UI Privacy / Visibility Audit

Verification date: 2026-05-23

Scope reviewed:

- `frontend/src/App.tsx`
- `frontend/src/tavernUi.tsx`
- `frontend/src/api.ts`
- `backend/app/main.py`
- `backend/app/platform/tavern_studio.py`
- `backend/tests/test_v32_tavern_ui_pro.py`
- `backend/tests/test_v32_integration_regression.py`
- `docs/V3_2_ROADMAP.md`
- `docs/V3_2_TAVERN_UI_CONTRACT_REVIEW.md`

This is a documentation-only audit. No code was changed.

## Passed Items

1. **Tavern UI does not show API keys.**
   - Provider and settings surfaces use safe status wording such as configured / not shown.
   - `TavernPromptProviderPanel` explicitly says API keys are not shown.
   - v3.2 regression tests assert Tavern preferences, prompt context, multi-NPC responses, safety reports, and exports do not contain `api_key`.

2. **Tavern UI does not show raw env.**
   - v3.2 Tavern surfaces use local-safe summaries and do not expose raw environment values.
   - Settings and config text continues to state raw env is not shown.

3. **Tavern Prompt / Provider panel does not show provider secrets.**
   - The panel shows a Provider Gateway safe summary only.
   - It does not expose plaintext provider credentials, raw prompt text, or provider secret values.

4. **Tavern normal UI filters hidden facts.**
   - `TavernMessage.safe_summary()` returns `None` for non-`TAVERN_SAFE` messages.
   - Tavern prompt context validation rejects hidden fact text.
   - v3.2 integration tests verify hidden messages and hidden RP memory do not enter normal message lists or Tavern prompt context.

5. **Tavern normal UI filters NPC secrets.**
   - `WorldNpcToTavernAdapterService` in `player_safe` mode excludes NPC secrets and unknown facts.
   - UI copy for World NPC -> Tavern states player-safe mode excludes NPC secrets and unknown facts.
   - v3.2 tests verify World NPC adapter safe summaries do not contain NPC secret text.

6. **Character editor does not show private persona expanded by default.**
   - `TavernCharacterEditor` copy treats private persona as authoring-only.
   - `TavernRPProfile.safe_summary()` does not include `private_persona_authoring_only`.
   - v3.2 integration tests verify private persona text is absent from safe profile summaries.

7. **RP Memory Panel does not show `mature_only` memory by default.**
   - `TavernMemoryRecord.safe_summary()` returns `None` for non-`TAVERN_SAFE` memory.
   - `RPMemoryPanel` states mature-only memory is hidden by default.
   - v3.2 tests verify mature memory is not present in normal memory context.

8. **Emotion / Relationship panels do not display hidden triggers or hidden relationships.**
   - Current v3.2 panels are safe-summary UI surfaces.
   - Relationship tone changes are proposal-only for World changes.
   - No normal UI path was found that renders hidden trigger or hidden relationship bodies.

9. **Multi-NPC Scene UI does not show NPC unknown facts.**
   - Multi-NPC UI displays scene summaries, participants, turn order, and generated Tavern messages.
   - It does not expose NPC knowledge internals or unknown World facts.
   - Multi-NPC generation now routes through Tavern Provider Gateway when context is available and falls back safely.

10. **Scene Mood / Voice Lab do not show private notes.**
    - Current panels are safe local authoring summaries.
    - Voice Lab states it is text voice only, uses safe samples, and does not call a real provider by default.

11. **Tavern -> World Proposal UI does not show mature/private details in normal view.**
    - Proposals use `normal_summary()` and redaction helpers.
    - Mature memory proposals are summarized as filtered metadata rather than raw body text.
    - UI copy states RP content is not a World fact until validated and applied.

12. **Tavern -> Novel UI does not show mature/private details by default.**
    - Tavern -> Novel preview uses safe message summaries.
    - v3.2 integration tests verify `mature_only` source text is filtered from preview output.

13. **World NPC -> Tavern `player_safe` mode does not leak NPC secrets.**
    - Adapter tests verify NPC secrets, private NPC fear text, and hidden fact text are absent from safe summaries.
    - The UI states `player_safe` excludes NPC secrets and unknown facts.

14. **Export UI does not include mature/private content by default.**
    - `TavernSessionExportService` exports safe messages only by default.
    - Export filtering policy lists API keys, hidden facts, NPC secrets, mature/private memory, debug data, raw prompts, and raw `state_deltas` as excluded.
    - v3.2 tests verify normal export excludes hidden fact text, NPC secret body text, `mature_only`, and API key markers.

15. **Quality / RP Safety Dashboard does not print hidden or mature text bodies.**
    - `TavernRPSafetyDashboardService` produces safe issue rows.
    - RP Safety Dashboard copy says hidden leaks, NPC knowledge, private persona, mature memory, provider routing, world consistency, proposal validation, and export safety use safe issue rows.

16. **Error surfaces are intended to be safe.**
    - Tavern v3.2 endpoint errors are based on validation messages and redacted helpers.
    - No new Tavern UI path was found that intentionally prints full local paths or stack traces.

17. **No online RP / cloud sync / account entry was introduced as a Tavern feature.**
    - Roadmap and UI text explicitly describe no online RP platform, no account, no cloud sync, no online marketplace, and no remote character-card download.
    - v3.2 frontend regression checks verify no online RP primary entry is introduced.

## High-Risk UI Leaks

None found in the reviewed v3.2 Tavern UI surfaces.

## Medium-Risk UI Leaks

None found that block v3.2 release.

## Minor Issues

1. **Some safety copy contains sensitive-category words by design.**
   - Examples include "NPC secrets excluded", "hidden facts excluded", and "mature memory hidden".
   - This is policy wording, not leaked content. Tests should continue distinguishing policy labels from raw sensitive bodies.

2. **Some older non-Tavern debug/editor surfaces still mention raw `state_deltas`.**
   - The reviewed Tavern normal UI does not expose raw `state_deltas`.
   - Existing debug/editor views should remain governed by their existing debug/authoring gating and are outside the Tavern normal UI scope.

3. **Current Pro panels are safe-summary oriented rather than deep editors for every RP artifact.**
   - This is acceptable for v3.2 UI Pro foundation, but later versions should continue adding richer controls without weakening visibility rules.

## Recommended Fixes

1. Keep v3.2 regression checks strict about raw body text:
   - API key-like strings;
   - hidden fact bodies;
   - NPC secret bodies;
   - mature/private memory bodies;
   - raw prompts;
   - raw `state_deltas`.

2. When future Tavern panels become deeper editors, require explicit authoring labels for any authoring-only data and keep normal view filtered.

3. If debug Tavern views are expanded later, gate them behind `ENABLE_DEBUG_API` and keep mature/private content separate from debug visibility.

4. Maintain the distinction between safe policy wording and leaked content in tests and audits.

## Release Blocking Assessment

This audit does **not** identify a v3.2 release blocker.

Final privacy / visibility verdict: **Pass with minor non-blocking notes**.
