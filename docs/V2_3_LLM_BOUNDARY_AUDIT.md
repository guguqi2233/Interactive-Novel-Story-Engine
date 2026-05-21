# v2.3 LLM Boundary Audit

## Verdict

PASS.

v2.3 Tavern Studio MVP keeps the LLM as a language and roleplay reply layer. The
review found no high-risk path where Tavern Mode, Tavern response generation,
Tavern-to-World proposals, or World NPC adaptation directly modify `GameState`,
append `EventLog`, write content packs, or grant hidden-fact authority to prompt
profiles.

## Verification Date

2026-05-22

## Scope Reviewed

- `docs/V2_3_ROADMAP.md`
- `backend/app/platform/tavern_studio.py`
- `backend/app/main.py` Tavern routes
- `backend/app/evals/tavern_boundary.py`
- `backend/tests/test_v23_tavern_studio_mvp.py`
- `backend/tests/test_v23_integration_regression.py`

## Evidence Reviewed

- `TavernPromptContext` and `TavernPromptContextBuilder`
- `TavernResponseGenerationService`
- `SingleCharacterChatService`
- `TavernToWorldProposalService`
- `WorldNpcToTavernAdapterService`
- `TavernMemoryRecord` / `TavernMemoryService`
- `TavernLoreContextBuilder`
- `TavernRPProfile` / `TavernVoiceProfile`
- Tavern API chat/proposal/adapter endpoints
- Tavern boundary evals and v2.3 integration regression tests

## Passed Items

1. Tavern Mode does not give the LLM direct `GameState` authority.
   - Tavern schemas and services are project/Tavern data models.
   - `SingleCharacterChatService` saves user and character replies as
     `TavernMessage` records only.
   - No reviewed Tavern service applies `StateDelta` or mutates active World
     state.

2. Tavern Response Generation only produces RP replies or draft-like output.
   - `TavernResponseGenerationService` returns `GeneratedTavernReply`.
   - `GeneratedTavernReply` is schema-validated and rejects secret-like,
     hidden-fact, or `state_delta` material.
   - Generated replies are not World events and are not authoritative facts.

3. Tavern to World Proposal does not write `GameState`, `EventLog`, facts, or
   content packs.
   - `TavernToWorldProposalService` stores `TavernWorldProposal` objects.
   - Validation checks refs and forbidden material, but v2.3 has no apply-to-
     World workflow.

4. World NPC Adapter excludes player-unsafe NPC details.
   - `WorldNpcToTavernAdapterService` rejects hidden/non-visible NPCs in
     `player_safe` mode.
   - NPC secrets are not copied into the player-safe Tavern character.
   - NPC knowledge is filtered by `player_visible_fact_ids`.
   - Authoring-only private material is marked redacted rather than prompt-safe.

5. Prompt Profile cannot enable hidden-fact or state permissions.
   - Shared prompt profile validation rejects forbidden permission fields such
     as hidden fact access and state modification.
   - Tavern profile selection requires `mode_scopes` to include `tavern`.

6. Provider Gateway / `LLMProvider` remains the generation boundary.
   - Tavern generation service accepts an `LLMProvider`.
   - Tavern chat API obtains the provider through app state or
     `create_llm_provider`.
   - Tests use `FakeLLMProvider`; no v2.3 tests call a real external provider.

7. `TavernPromptContext` excludes forbidden data classes.
   - Context validation rejects secret-like text, `state_delta` material,
     `"hidden fact"` markers, and `private_persona`.
   - The builder uses safe summaries for Tavern characters, RP/voice profiles,
     scene mood, relationship tone, memory, and lore entries.

8. WorldBible and Lorebook hidden entries do not enter Tavern prompts.
   - `TavernLoreContextBuilder` excludes WorldBible hidden/authoring/debug
     entries.
   - Tavern lorebook entries must be public/tavern-safe and pass NPC-knowledge
     filtering before prompt inclusion.
   - LoreFact entries are taken through tavern-safe filtering and NPC known-fact
     checks.

9. Character private persona does not enter normal prompts.
   - `TavernRPProfile.safe_summary()` excludes
     `private_persona_authoring_only`.
   - Integration tests assert private persona does not appear in prompt context.

10. Raw `state_deltas` do not enter RP prompts.
    - Prompt context validation rejects `state_delta` / `state_deltas`.
    - Boundary evals include raw state delta leak detection.

11. Memory is not treated as authoritative fact.
    - `TavernMemoryRecord.authoritative` is fixed to `False`.
    - Hidden/debug/authoring-only memory is filtered out of normal Tavern memory
      context.

12. Schema failures are explicit.
    - Unsafe prompt context and unsafe generated replies raise validation
      errors.
    - Unsafe RP profile rules, scene mood permissions, invalid proposal refs,
      and secret-like character cards fail or produce clear warnings.

13. Tavern Safety Evals are deterministic and local.
    - `backend/app/evals/tavern_boundary.py` uses rule checks, not an external
      LLM judge.
    - Reports redact details and do not print raw hidden text in normal output.

## Risk Items

1. Keyword-based prompt validation is intentionally conservative but not a full
   semantic classifier.
   - Current validation rejects explicit secret-like text, `state_delta`,
     `"hidden fact"`, and private-persona markers.
   - This is acceptable for v2.3 because all normal inputs are constructed from
     safe summaries and deterministic filters, with regression tests for known
     leak classes.

2. Tavern chat API has a fallback that replaces `MockLLMProvider` with a local
   `FakeLLMProvider` response.
   - This keeps tests/local defaults deterministic and avoids accidental real
     API calls.
   - It should be documented in release notes as local stub behavior, not a
     production model response.

## High-Risk Issues

None found.

## Medium-Risk Issues

None blocking.

The only medium-watch area is that future expansion of Tavern prompt context
must keep using safe summaries and must not add raw lore, raw memory, raw
WorldBible entries, raw `GameState`, or raw EventLog deltas.

## Low-Risk Issues

1. The boundary evals catch deterministic known leak patterns. Future v2.4+
   richer multi-character contexts should add more fixtures for paraphrased
   hidden leaks and per-NPC knowledge boundaries.
2. Current World NPC adapter creates draft text from public NPC persona fields;
   future richer adapters should continue separating `player_safe` and
   `authoring` modes.

## Recommendations

1. Keep all future Tavern generation behind `TavernPromptContext` and
   `LLMProvider`.
2. Add regression fixtures whenever a new prompt context field is introduced.
3. Keep Tavern-to-World apply out of v2.3; if implemented later, require
   explicit validation, StateDelta/EventLog integration, and separate
   acceptance tests.
4. Expand boundary evals in v2.4 if multi-character generation becomes active.

## Acceptance Impact

This audit does not block v2.3 acceptance.

Final status: PASS, with non-blocking recommendations for future prompt-context
expansion.
