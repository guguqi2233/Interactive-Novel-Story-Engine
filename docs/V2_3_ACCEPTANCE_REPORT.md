# v2.3 Acceptance Report

## Verdict

PASS_WITH_WARNINGS

v2.3 Tavern Studio MVP is accepted as a local roleplay and authoring milestone on top of the v2.1 `NarrativeProject` layer and the v2.2 Novel Studio MVP. The implementation provides Tavern schemas, local repository/API/frontend shell, character card import, RP and voice profiles, single-character chat, Tavern memory, safe lore/world-info context, scene mood and relationship tone controls, provider-gated response generation, Tavern-to-World proposals, World NPC to Tavern draft adaptation, and Tavern boundary regression coverage.

No high-risk acceptance blocker was found. Remaining warnings are documented MVP limitations rather than release blockers.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: PASS, `1604 passed in 113.27s`
- `cd frontend && npm.cmd run build`: PASS
- Frontend build warning: Vite reported an existing chunk-size warning for a bundled asset larger than 500 kB. This is non-blocking for v2.3.

## Scope Accepted

Accepted v2.3 scope:

1. Tavern Core Schema
   - `TavernProjectSection`, `TavernCharacter`, `TavernSession`, `TavernMessage`, `TavernSceneContext`, `TavernSessionStatus`, and supporting enums are present.
   - Tavern schemas are Pydantic models and do not depend on `GameState`.

2. Character Card Importer
   - `CharacterCardImportService` imports JSON/YAML-style card data into Tavern and character-profile draft artifacts.
   - Import does not execute embedded code, does not import API keys, and does not create World NPCs or mutate `GameState`.
   - Prompt-like permissions such as state modification or hidden fact access are rejected or surfaced as warnings.

3. RP Profile / Voice Profile
   - `TavernRPProfile` and `TavernVoiceProfile` are available.
   - Private persona and authoring-only notes are excluded from normal prompt/safe summaries.
   - RP and voice profile data can shape expression but cannot change world facts.

4. Tavern Session Repository
   - `TavernRepository` stores Tavern data under `project/tavern/`.
   - Repository flows support characters, sessions, messages, scene presets, memories, multi-character scene stubs, and proposals.
   - Path traversal is rejected and storage does not read `.env`, databases, logs, caches, `node_modules`, or `dist`.

5. Tavern API
   - Local authoring APIs exist under `/projects/{project_id}/tavern/...`.
   - APIs support character/session/message operations, card import, chat, scene presets, relationship tones, memory, lore context, proposals, World NPC adaptation, and safety evaluation.
   - APIs are local authoring/studio endpoints and do not expose API keys, raw env, raw `GameState`, raw `state_deltas`, hidden facts, or provider secrets.

6. Tavern Frontend Shell
   - Project Shell includes a Tavern mode surface.
   - Tavern UI can show/create Tavern characters, import character cards, list/create/open sessions, display chat, and show MVP controls for scene mood, memory, lore, proposals, and multi-character scene stubs.
   - Disabled/error/empty states are handled without exposing sensitive details.
   - Frontend build passes.

7. Single Character Chat Backend / Frontend
   - `SingleCharacterChatService` appends user messages, builds safe Tavern context, generates a character reply through provider abstraction, and stores the reply as `TavernMessage`.
   - Frontend provides a textarea-based single-character chat panel with loading/error states and collapsible safety notes.
   - Chat does not write World events, `StateDelta`, or `GameState`.

8. Multi-Character Scene Stub
   - `MultiCharacterScene` and service/repository support minimal scene drafts.
   - v2.3 does not implement full multi-character speaker orchestration or generation.

9. Tavern Memory System
   - `TavernMemoryRecord` and `TavernMemoryService` support local RP memory records and safe context construction.
   - Memory is non-authoritative by default and cannot override `GameState`, `EventLog`, facts, NPC knowledge, or visibility.

10. Lorebook / World Info Integration
    - `TavernLorebookEntry` and `TavernLoreContextBuilder` provide safe Tavern context.
    - Hidden lore, authoring notes, NPC unknown facts, NPC secrets, and debug-only entries are excluded from normal RP prompt context.

11. Scene Mood Presets
    - `SceneMoodPreset` supports style-only mood, pacing, sensory, and emotional-tone fields.
    - Scene mood cannot enable hidden fact access, override action results, or modify world state.

12. Relationship Tone System
    - `RelationshipTone` and `RelationshipToneService` provide safe relationship-tone context and proposal-oriented tone changes.
    - Hidden relationship state and authoring-only tone notes are excluded from normal prompts.
    - Tone changes do not modify World relationship state.

13. Tavern Prompt Profile Integration
    - `TavernPromptContext` and its builder support tavern-scoped prompt profile selection.
    - Prompt context excludes hidden facts, NPC unknown facts, private persona, raw debug memory, raw `state_deltas`, API keys, provider secrets, and raw env.
    - Prompt profiles cannot enable hidden fact access or state modification.

14. Tavern Response Generation Service
    - `TavernResponseGenerationService` accepts an injected `LLMProvider`.
    - Generated output is validated as `GeneratedTavernReply`.
    - Generated replies are RP replies/proposals only and do not modify `GameState`, append `EventLog`, create World facts, or overwrite messages without explicit confirmation semantics.
    - Tests use fake/mock/local provider paths and do not call real APIs.

15. Tavern to World Proposal
    - `TavernWorldProposal` and `TavernToWorldProposalService` create candidate proposals such as relationship changes, fact discovery, quest hints, promises/deals, mood changes, and timeline event candidates.
    - Proposals are validation-gated candidate records only.
    - v2.3 does not implement apply-to-World.

16. World NPC to Tavern Character Adapter
    - `WorldNpcToTavernAdapterService` creates Tavern draft/reference artifacts from World NPC data.
    - `player_safe` mode excludes NPC secrets and unknown facts.
    - Authoring mode can mark additional metadata as authoring-only.
    - Adapter does not modify the NPC, `GameState`, or World content.

17. Tavern Safety / Boundary Evals
    - Tavern boundary evals cover prompt leak risks, private persona exclusion, debug memory exclusion, raw `state_deltas`, no direct `GameState` mutation, no World event creation, no proposal apply, and World NPC adapter secrecy.
    - Failure reports use labels/safe details and do not print hidden text in full.

18. v2.3 Integration Regression Tests
    - v2.3 focused and integration regression tests are present in `backend/tests/test_v23_tavern_studio_mvp.py` and `backend/tests/test_v23_integration_regression.py`.
    - Tavern boundary eval coverage is present in `backend/app/evals/tavern_boundary.py`.
    - Full pytest suite passes.

## Boundary Review

LLM boundary:

- LLM remains a language layer.
- Tavern response generation uses an injected `LLMProvider` abstraction and test paths use fake/mock providers.
- `TavernPromptContext` excludes hidden facts, NPC unknown facts, NPC secrets, private persona, raw debug memory, raw `state_deltas`, API keys, provider secrets, and raw env.
- Prompt profiles cannot enable hidden fact access or state modification.
- Generated Tavern replies are not world facts and cannot mutate `GameState`.

World Engine boundary:

- World Engine remains the World Mode fact source.
- `GameState` changes continue to require `StateDelta`.
- World events remain recorded through `EventLog`.
- Tavern Mode produces RP session, message, memory, draft, and proposal artifacts only.
- Tavern-to-World conversion creates `TavernWorldProposal` candidates and does not write content packs, `facts.yaml`, saves, active `GameState`, or `EventLog`.
- World NPC adaptation creates Tavern drafts/references and does not modify NPC data.

Visibility and privacy boundary:

- Hidden World Bible entries do not enter normal Tavern context.
- Lorebook hidden entries and authoring notes are filtered from normal RP prompt context.
- NPC secrets and NPC unknown facts are excluded from player-safe Tavern prompt/context.
- Character private persona and authoring-only notes are excluded from normal prompts and safe summaries.
- Hidden/debug Tavern memory is filtered from normal chat context.
- Raw `state_deltas` do not enter Tavern prompts, messages, or normal reports.
- Tavern safety reports use safe labels rather than hidden text in full.

Cross-mode boundary:

- `CrossModeLink` remains a reference system and does not apply state changes.
- Tavern-to-World proposals require validation and remain unapplied in v2.3.
- RP memory is not an authoritative fact source.
- World NPC to Tavern Character adaptation is one-way draft/reference creation, not bidirectional sync.
- Novel Mode remains unaffected by Tavern additions.

Security/API boundary:

- Tavern APIs are local authoring/studio APIs and are gated by the existing authoring configuration.
- TavernRepository rejects traversal and confines storage to `project/tavern/`.
- Character card import does not execute script-like content and rejects or warns on secret-like content.
- Provider profiles store env-var references only, not real API keys.
- Frontend does not store API keys, raw env, hidden facts, debug memory, or raw `state_deltas`.

## Known Limitations

1. Tavern Studio is an MVP, not a complete roleplay platform.
   - Multi-character scene support is a stub/minimal structure.
   - No full group-chat orchestration, turn scheduler, streaming, image, voice, online RP, account system, cloud sync, or marketplace behavior.

2. Tavern-to-World remains proposal-only.
   - v2.3 does not implement apply-to-World.
   - Future apply must require schema validation, explicit confirmation, visibility checks, and normal World Engine `StateDelta` / `EventLog` handling.

3. Mature/NSFW support is out of scope.
   - v2.3 does not implement a complete mature content module.
   - Existing safety flags remain metadata boundaries rather than a mature-content runtime.

4. Safety detection is deterministic and rule-based.
   - Known hidden refs, NPC secret refs, private-persona markers, raw `state_deltas`, and secret-like strings are blocked or flagged.
   - Arbitrary author-written leakage in free text cannot be semantically guaranteed without future richer validation.

5. Tavern session export is not part of v2.3.
   - If added later, it must reuse current secret, private-persona, debug-memory, hidden-fact, and raw-delta filtering.

6. Frontend MVP is functional but compact.
   - It favors simple panels, textareas, and disabled/coming-soon states over a full Tavern desktop experience.
   - Vite still emits a non-blocking chunk-size warning.

## Acceptance Risks

Low to medium, non-blocking:

- Future multi-character generation will need stronger turn-level prompt isolation and NPC-knowledge fixtures.
- Future Tavern export must reuse the current secret/hidden/private/debug filtering.
- Future proposal apply must go through World validation, explicit confirmation, `StateDelta`, and `EventLog`.
- Future provider-backed RP features must keep fake/mock provider coverage and avoid real API calls in tests.
- Rule-based leak checks should be expanded as Tavern contexts become richer.

No high-risk release blocker remains for v2.3 acceptance.

## Recommended v2.4 Priorities

1. World Studio / Proposal Review
   - Add a safe review and explicit-apply workflow for Novel/Tavern-to-World proposals.
   - Keep World writes behind validation, `StateDelta`, and `EventLog`.

2. Stronger Multi-Character Tavern Flow
   - Add turn scheduling, per-speaker prompt isolation, and group-scene safety evals.

3. Project Quality Gate Deepening
   - Aggregate Tavern boundary evals, Novel quality evals, project validation, and World quality checks into a clearer release dashboard.

4. Tavern Export / Session Archive
   - Add safe RP session export only after secret/private/debug/hidden filters are reused.

5. Richer World NPC Adapter Review
   - Add draft diff/review before adapting World NPCs to Tavern characters and before creating cross-mode links.

## Final Status

v2.3 is accepted as Tavern Studio MVP with warnings.

Release recommendation: proceed to v2.3 release notes and final freeze checks if no new blockers appear.
