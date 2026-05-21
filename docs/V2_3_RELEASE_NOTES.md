# v2.3 Release Notes

## 1. Version Name

v2.3 Tavern Studio MVP

## 2. Version Goal

v2.3 turns the Tavern Mode stub into a usable local Tavern Studio MVP inside `NarrativeProject`. It adds project-local roleplay characters, sessions, messages, memory, lore/world-info context, scene mood, relationship tone, single-character chat, provider-gated reply generation, and Tavern-to-World proposal workflows.

Tavern Mode remains separate from World Mode authority:

- Tavern Mode outputs are RP sessions, messages, memories, drafts, or proposals by default.
- Tavern Mode does not directly modify World `GameState`.
- Tavern-to-World creates proposals only.
- World NPC to Tavern Character creates draft/adapter records only.
- LLM remains a language layer, not the world referee.
- Provider Gateway / `LLMProvider` remains the only model entry point.

## 3. New Features

- Tavern core schemas for project sections, characters, sessions, messages, scene context, visibility, speaker type, and session status.
- Local `TavernRepository` storage under `project/tavern/`.
- Local authoring APIs under `/projects/{project_id}/tavern/...`.
- Tavern frontend shell in the Project Shell.
- Character card import from JSON/YAML-style local card data.
- RP Profile and Voice Profile schemas with safe summaries.
- Single-character chat backend and frontend.
- Multi-character scene stub for future group RP work.
- Tavern memory records and safe memory context.
- Lorebook / World Info integration through Tavern-safe context filtering.
- Scene Mood Presets for style-only atmosphere control.
- Relationship Tone System for safe relationship presentation/proposals.
- Tavern-scoped Prompt Profile integration.
- Tavern response generation using injected `LLMProvider`.
- Tavern-to-World `TavernWorldProposal` candidates.
- World NPC to Tavern Character adapter.
- Tavern safety / boundary evals.
- v2.3 focused and integration regression tests.

## 4. Behavior Changes

- Tavern Mode is no longer only a placeholder. It now stores and manages project-local RP data.
- Tavern chat stores messages as `TavernMessage` records, not World events.
- Tavern memory is non-authoritative and does not override World facts, NPC knowledge, `GameState`, or `EventLog`.
- Tavern-to-World outcomes are proposal records and are not applied to World Mode in v2.3.
- World NPC adaptation creates Tavern drafts/references without changing the original NPC.
- Project Quality Gate can include Tavern boundary checks.

## 5. API Changes

New local authoring APIs include:

```text
GET  /projects/{project_id}/tavern/characters
POST /projects/{project_id}/tavern/characters
GET  /projects/{project_id}/tavern/characters/{character_id}
PATCH /projects/{project_id}/tavern/characters/{character_id}
POST /projects/{project_id}/tavern/import-character-card
GET  /projects/{project_id}/tavern/sessions
POST /projects/{project_id}/tavern/sessions
GET  /projects/{project_id}/tavern/sessions/{session_id}
PATCH /projects/{project_id}/tavern/sessions/{session_id}
GET  /projects/{project_id}/tavern/sessions/{session_id}/messages
POST /projects/{project_id}/tavern/sessions/{session_id}/messages
POST /projects/{project_id}/tavern/sessions/{session_id}/archive
POST /projects/{project_id}/tavern/sessions/{session_id}/chat
GET  /projects/{project_id}/tavern/scene-presets
POST /projects/{project_id}/tavern/scene-presets
PATCH /projects/{project_id}/tavern/scene-presets/{preset_id}
GET  /projects/{project_id}/tavern/proposals
POST /projects/{project_id}/tavern/proposals
POST /projects/{project_id}/tavern/proposals/{proposal_id}/validate
POST /projects/{project_id}/tavern/proposals/{proposal_id}/reject
POST /projects/{project_id}/tavern/adapt-world-npc
```

These APIs are local authoring/studio APIs. They are not player APIs and must remain gated by local authoring configuration.

## 6. Frontend Changes

- Project Shell Tavern mode now shows a Tavern Studio MVP surface.
- Users can create Tavern characters.
- Users can import character cards.
- Users can create/open Tavern sessions.
- Users can append messages and use the single-character chat panel.
- UI includes MVP panels for lore/context, memory, scene mood, relationship tone, proposals, and multi-character scene stub.
- API-disabled states degrade safely.
- The UI does not display API keys, raw env, hidden facts, NPC secrets, debug memory, raw `state_deltas`, or provider secrets in the Tavern normal surface.

## 7. Tavern Schema Changes

New v2.3 Tavern contracts include:

- `TavernProjectSection`
- `TavernCharacter`
- `TavernSession`
- `TavernMessage`
- `TavernSceneContext`
- `TavernSessionStatus`
- `ImportedCharacterCard`
- `TavernRPProfile`
- `TavernVoiceProfile`
- `MultiCharacterScene`
- `TavernMemoryRecord`
- `TavernLorebookEntry`
- `SceneMoodPreset`
- `RelationshipTone`
- `TavernPromptContext`
- `GeneratedTavernReply`
- `TavernChatResponse`
- `TavernWorldProposal`

These schemas do not depend on `GameState` and do not create authoritative World facts.

## 8. Tavern Repository / Storage Changes

Tavern files live under the project-local Tavern section:

```text
project/
  tavern/
    characters/
    sessions/
    messages/
    lorebooks/
    scene_presets/
    memory/
    proposals/
    exports/
```

`TavernRepository` supports local create/load/save/list operations for Tavern characters, sessions, messages, scene presets, memory, multi-character scene stubs, and proposals. It rejects path traversal and does not read `.env`, databases, logs, caches, node modules, or frontend build outputs.

## 9. Character Card Import Changes

- Character card import accepts JSON/YAML-style local card content.
- Imported cards can produce Tavern character drafts and related profile draft data.
- Import does not create or overwrite World NPCs.
- Import does not execute embedded script-like content.
- Creator/private notes remain authoring-only.
- System-prompt-like text is scanned for unsafe authority expansion, including hidden fact access or state modification claims.
- Secret-like content such as API-key-shaped strings is rejected or warned on and is not accepted as profile/runtime authority.

## 10. RP Profile / Voice Profile Changes

- `TavernRPProfile` models public persona, roleplay rules, emotional baseline, relationship defaults, boundaries, and safety flags.
- `TavernVoiceProfile` models tone, speech habits, vocabulary style, sentence length, catchphrases, and emotional markers.
- Private persona fields are excluded from normal RP prompt context.
- Voice and RP profiles can affect expression and style only.
- Profiles cannot modify World NPCs, World facts, `GameState`, or `EventLog`.

## 11. Cross-Mode Changes

- Tavern sessions, messages, memory, and proposals can reference project/world records through safe refs.
- Tavern-to-World creates `TavernWorldProposal` candidates only.
- World NPC to Tavern Character creates a Tavern draft/adapter result and optional cross-mode reference.
- `CrossModeLink` remains reference-only and does not apply state changes.
- Tavern messages do not become World facts or World events.
- Novel Mode and World Mode remain compatible with the v2.3 Tavern additions.

## 12. LLM / Prompt Profile Changes

- Tavern reply generation is optional and provider-backed.
- `TavernResponseGenerationService` accepts an injected `LLMProvider` and produces `GeneratedTavernReply`.
- Tests use fake/mock/local provider paths and do not call real APIs.
- `TavernPromptContext` contains only safe character/profile summaries, safe voice style, safe mood/tone, recent safe messages, Tavern-safe memory, and safe lorebook entries.
- Prompt Profiles may adjust Tavern style and formatting only.
- Prompt Profiles cannot enable hidden fact access, state modification, action-result override, or visibility bypass.
- Provider Gateway / `LLMProvider` remains the model access boundary.

## 13. Safety / Eval Changes

- Tavern boundary evals cover prompt hidden-leak risks, NPC unknown facts, private persona exclusion, debug memory exclusion, raw `state_deltas`, direct `GameState` mutation, World event creation, proposal apply attempts, and World NPC adapter secrecy.
- Tavern Safety Eval does not use an external LLM judge.
- Eval reports avoid printing hidden text in full.
- Project Quality Gate can include Tavern boundary checks.

## 14. Known Limitations

- Tavern Studio is an MVP, not a complete Tavern replacement or full RP platform.
- Multi-character scene support is a stub/minimal structure.
- No full group-chat orchestration, turn scheduler, streaming, voice, image, online RP, cloud sync, accounts, or marketplace behavior.
- No complete Mature/NSFW module in v2.3.
- Tavern-to-World does not implement apply-to-World.
- Tavern session export is not part of the v2.3 MVP; any future Tavern export must exclude secrets, `.env`, raw env, provider secrets, debug memory, raw `state_deltas`, hidden facts, and private persona unless explicitly authoring-only.
- Hidden-content detection is deterministic and rule-based; arbitrary user-authored hidden truth in free text cannot be semantically guaranteed.
- Frontend build still has a non-blocking Vite chunk-size warning.

## 15. Upgrade Notes from v2.2

- Existing v2.2 `NarrativeProject` workspaces remain valid.
- Tavern Mode now creates additional files under `project/tavern/`.
- Enable `ENABLE_AUTHORING_API=true` only on a trusted local machine to use Tavern authoring APIs.
- No new real API key is required for v2.3.
- Keep `LLM_PROVIDER=mock` or `local_stub` for tests.
- If using optional real provider-backed RP locally, credentials must remain in environment/local secret config and must not be stored in project files, exports, prompt profiles, provider profiles, frontend env, character cards, or Tavern sessions.
- Tavern-to-World proposals are review candidates. They do not modify world state in v2.3.
- Existing Novel Studio workflows from v2.2 should continue to work unchanged.

## 16. Recommended v2.4 Direction

Recommended v2.4 theme: Cross-Mode Bridge.

Suggested priorities:

1. Safe review and explicit-apply workflow for Novel/Tavern-to-World proposals.
2. Cross-mode bridge dashboard for Novel, Tavern, World, timelines, characters, and proposals.
3. Proposal validation that routes any World-changing action through World Engine rules, `StateDelta`, and `EventLog`.
4. Richer World NPC adapter review and diff tooling.
5. Stronger multi-character Tavern scene safety after the v2.3 stub proves stable.
6. Project Quality Gate aggregation across Novel, Tavern, World, import/export, and provider/profile boundaries.

v2.4 should continue the same boundaries: LLM is not the world judge, Provider Gateway remains the model entry point, Tavern and Novel outputs are draft/proposal material, and World Mode facts remain under the World Engine.
