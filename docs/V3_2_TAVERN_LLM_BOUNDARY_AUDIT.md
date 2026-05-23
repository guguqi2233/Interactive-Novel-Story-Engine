# v3.2 Tavern LLM Boundary Audit

Verification date: 2026-05-23

Scope reviewed:

- `backend/app/platform/tavern_studio.py`
- `backend/app/main.py`
- `backend/tests/test_v23_tavern_studio_mvp.py`
- `backend/tests/test_v24_cross_mode_bridge.py`
- `backend/tests/test_v28_roleplay_mature_module.py`
- `backend/tests/test_v32_tavern_ui_pro.py`
- `backend/tests/test_v32_integration_regression.py`
- `frontend/src/tavernUi.tsx`
- `frontend/src/App.tsx`
- `docs/V3_2_ROADMAP.md`
- `docs/V3_2_TAVERN_UI_CONTRACT_REVIEW.md`

This is a documentation-only audit. No code was changed.

## Passed Items

1. **Tavern reply generation goes through Provider Gateway.**
   - `chat_tavern_session` routes the provider through `routed_provider_from_provider` or `routed_provider_from_settings`.
   - The routed use case is `ProviderRoutingUseCase.TAVERN_REPLY`.
   - `SingleCharacterChatService` then calls `TavernResponseGenerationService`, which uses the routed provider's `generate_json`.
   - v3.2 integration tests inject a `FakeLLMProvider` and verify the chat reply comes through that routed boundary.

2. **Multi-NPC reply generation goes through Provider Gateway.**
   - `generate_tavern_multi_scene_next_reply` now routes available providers through `routed_provider_from_provider` or `routed_provider_from_settings`.
   - When only the default mock is available, it wraps a deterministic `FakeLLMProvider` through the same routed provider helper.
   - Missing scene/session/character context falls back to a safe local message instead of calling a real provider or expanding authority.
   - v3.2 integration tests verify Multi-NPC reply generation uses the injected provider response.

3. **`TavernPromptContext` filters hidden facts.**
   - `TavernPromptContext.validate_safe_context` rejects payloads containing hidden fact markers, raw `state_delta` text, and secret-like material.
   - `TavernMessage.safe_summary()` omits non-`TAVERN_SAFE` messages.
   - `TavernMemoryRecord.safe_summary()` omits non-`TAVERN_SAFE` memory.
   - v3.2 tests verify hidden fact text does not enter normal message lists, memory context, or prompt context.

4. **NPC prompt context is limited to safe Tavern summaries.**
   - `TavernPromptContextBuilder` uses the current character's safe summary, safe profile summaries, safe recent messages, and safe lore/memory context.
   - World NPC adaptation in `player_safe` mode excludes NPC secrets and player-unknown facts before creating Tavern character/profile drafts.
   - No reviewed Tavern prompt builder path directly injects raw NPC knowledge or hidden World facts.

5. **NPC secrets do not enter Tavern prompt context.**
   - `WorldNpcToTavernAdapterService` excludes `NPCState.secrets` from `player_safe` output.
   - v3.2 tests verify adapter safe summaries do not contain NPC secret bodies.
   - `TavernPromptContext` tests assert NPC secret markers are absent.

6. **Private persona does not enter normal prompt context.**
   - `TavernRPProfile.safe_summary()` excludes `private_persona_authoring_only`.
   - v3.2 tests verify private persona text is absent from safe profile summary payloads.

7. **Mature memory does not enter normal prompt context.**
   - Mature/private memory has non-safe visibility and therefore returns no normal safe summary.
   - `TavernMemoryService.build_tavern_memory_context` includes only safe summaries.
   - v3.2 integration tests verify `mature_only` text is absent from memory context.

8. **Raw `state_deltas` do not enter Tavern prompt context.**
   - Prompt context validation rejects `state_delta`.
   - Generation input is rechecked before provider calls.
   - v3.2 export and prompt tests assert raw `state_delta` markers are absent from normal flows.

9. **PromptProfile cannot enable hidden fact access for Tavern.**
   - Existing `ProjectPromptProfile` validation rejects `can_access_hidden_facts=True`.
   - v2.3/v3.2 tests cover this boundary.
   - Tavern prompt profiles may affect style, not visibility authority.

10. **Tavern Mode does not let the LLM directly create World facts.**
    - The system message for Tavern generation explicitly says not to create world facts, StateDeltas, or GameState changes.
    - `GeneratedTavernReply` may include `proposed_world_effects`, but these are redacted summaries and do not apply World changes.
    - World-changing consequences must become proposals and pass validation/apply.

11. **Tavern -> World still uses proposal, validation, and apply.**
    - `TavernToWorldProposalService` creates proposal records with RP safety metadata.
    - `validate_proposal` blocks invalid target refs, secrets, `state_delta` material, direct quest completion, missing RP safety metadata, and mature content/memory entering World facts.
    - Cross-Mode apply uses `TavernToWorldApplyService`, explicit confirmation, `StateDelta`, and `EventLog`.
    - v3.2 integration tests verify no direct `GameState` change occurs before confirmed apply.

12. **LLM output does not directly modify `GameState`.**
    - `TavernResponseGenerationService` returns `GeneratedTavernReply`.
    - Chat services append Tavern messages only.
    - GameState mutation remains in Cross-Mode confirmed apply flows with supplied `StateDelta` and `EventLog`.

13. **Tests do not call real APIs.**
    - v3.2 tests use `FakeLLMProvider`, `mock`, and project-local temporary directories.
    - No reviewed v3.2 test requires OpenAI or a real provider.

14. **RP Safety / Quality does not use an external LLM judge.**
    - `TavernRPSafetyDashboardService` uses `run_rp_mature_quality_gate`, which is a local deterministic scan/quality gate path.
    - Existing RP/mature quality tests validate safe summaries and redaction without external LLM calls.

## Risk Items

1. **Safe fallback in Multi-NPC generation.**
   - If session or character context is unavailable, Multi-NPC generation returns a safe local fallback message.
   - This is a safe degradation path, not a Provider Gateway bypass for normal configured generation.
   - Risk level: low.

2. **Prompt context relies on safe summary methods.**
   - The LLM boundary depends on `safe_summary()` implementations for characters, messages, memory, RP profiles, voice profiles, lore, scene mood, and relationship tone.
   - Current tests cover the most sensitive cases, but future fields must continue to implement safe summaries before entering prompt context.
   - Risk level: low to medium for future expansion, not a current blocker.

3. **Policy wording contains sensitive category labels.**
   - UI and reports may say "hidden facts excluded" or "NPC secrets excluded".
   - These labels are not leaked sensitive content.
   - Risk level: low.

## High-Risk Issues

None found.

## Medium-Risk Issues

None found that block v3.2 acceptance.

## Minor Issues

1. **Provider Gateway routing should remain covered for every future Tavern generation use case.**
   - Current chat and Multi-NPC flows are covered.
   - Future RP summary, voice sample, or mood sample generation should add equivalent tests.

2. **Multi-NPC fallback should stay visibly local-stub/safe if surfaced in UI.**
   - The backend fallback avoids real provider calls and does not expand LLM authority.
   - Future UI could display this as a provider-disabled/degraded state.

3. **More granular NPC knowledge tests would be useful in v3.3+.**
   - Current tests verify no NPC secret or hidden fact body reaches prompts.
   - Future deep multi-character scenes should test per-participant knowledge segmentation.

## Recommended Fixes

1. Add focused regression tests for any future Tavern generation endpoint to verify:
   - routed Provider Gateway use;
   - no hidden facts;
   - no NPC secrets;
   - no private persona;
   - no mature memory by default;
   - no raw prompts or raw `state_deltas`.

2. Keep `TavernPromptContext` validation strict and expand forbidden markers if new sensitive context categories are added.

3. Keep RP Safety and Quality Gate deterministic by default; do not introduce external LLM judge behavior without a separate boundary review.

4. If authoring/debug prompt previews are introduced later, gate them explicitly and redact secrets/hidden/mature/private content.

## Acceptance Blocking Assessment

This audit does **not** identify a v3.2 acceptance blocker.

Final Tavern LLM boundary verdict: **Pass with minor non-blocking follow-up recommendations**.
