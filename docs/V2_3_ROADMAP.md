# v2.3 Roadmap: Tavern Studio MVP

## Version Theme

Tavern Studio MVP on top of the v2.1 Unified Narrative Project Layer and the
v2.2 Novel Studio MVP.

## Goal

v2.3 turns Tavern Mode from a safe project stub into a usable local RP workspace.
It should let users import or create character cards, configure RP Profiles and
Voice Profiles, create Tavern Sessions, run single-character chat, manage RP
memory, reference safe Lorebook / World Info context, use Scene Mood Presets and
Relationship Tone, generate RP replies, and turn important RP outcomes into
World proposals.

Tavern output remains RP material. It is not World Mode fact, does not modify
`GameState`, does not append or rewrite `EventLog`, and does not bypass content
validation. Tavern -> World always produces proposal/candidate data that must be
validated before it can affect world content or runtime state.

This roadmap is a development plan, not an acceptance report.

## Explicit Non-Goals

- No complete multi-character group chat system; v2.3 only adds a stub or
  minimal scene structure.
- No complete NSFW / mature module.
- No online RP platform.
- No cloud sync, online accounts, online marketplace, or online collaboration.
- No direct Tavern Session mutation of `GameState`.
- No LLM authority over world facts.
- No RP memory as an authoritative fact source.
- No character card direct overwrite of World NPC records.
- No Lorebook hidden entries in normal RP prompts.
- No Tavern export containing API keys, `.env`, debug memory, raw
  `state_deltas`, provider secrets, or raw env.

## Recommended Development Order

1. Tavern Foundation:
   - Tavern Core Schema.
   - Character Card Importer.
   - RP Profile / Voice Profile.
   - Tavern Session Repository.
   - Tavern API.
   - Tavern Frontend Shell.
2. Core RP Workflow:
   - Single Character Chat Backend.
   - Single Character Chat Frontend.
   - Multi-Character Scene Stub.
   - Tavern Memory System.
   - Lorebook / World Info Integration.
3. Style, Prompt, and Generation:
   - Scene Mood Presets.
   - Relationship Tone System.
   - Tavern Prompt Profile Integration.
   - Tavern Response Generation Service.
4. Cross-Mode and Release Hardening:
   - Tavern to World Proposal.
   - World NPC to Tavern Character Adapter.
   - Tavern Safety / Boundary Evals.
   - v2.3 Integration Regression Tests.

## Module Plan

### 1. Tavern Core Schema

- Goal: define the stable Tavern data model for the MVP.
- Data structures: `TavernProjectSection`, `TavernCharacter`,
  `TavernSession`, `TavernMessage`, `TavernSceneContext`,
  `TavernSessionStatus`.
- API changes: none beyond future consumers; schema must be serializable and
  safe-summary friendly.
- Frontend changes: none required in this slice.
- Tests: schema defaults, JSON serialization, hidden refs excluded from safe
  summaries, no dependency on `GameState`.
- Acceptance: Tavern objects can represent characters, sessions, messages, and
  scene context without modifying world state.

### 2. Character Card Importer

- Goal: import local character-card style data into Tavern character drafts.
- Data structures: `CharacterCardImportRequest`, `CharacterCardImportPreview`,
  `CharacterCardImportResult`, `TavernCharacterDraft`.
- API changes: add preview/apply endpoints under
  `/projects/{project_id}/tavern/import-character-card`.
- Frontend changes: file/text import panel with preview, warnings, and explicit
  apply.
- Tests: preview no write, apply creates Tavern draft, malformed card fails
  clearly, private notes excluded from safe summary.
- Acceptance: character card import never creates or overwrites World NPCs.

### 3. RP Profile / Voice Profile

- Goal: let Tavern characters reference local RP and voice style metadata.
- Data structures: `RPProfile`, `VoiceProfile`, `RPProfileRef`,
  `VoiceProfileRef`, safe summaries.
- API changes: profile list/read/create/update endpoints under Tavern or shared
  project profile routes.
- Frontend changes: profile editor/selector for character tone, speech style,
  examples, boundaries, and visibility warnings.
- Tests: profile serialization, no API keys, no hidden fact permissions,
  examples remain style-only.
- Acceptance: profiles can change expression and voice style but cannot change
  facts, knowledge, or visibility.

### 4. Tavern Session Repository

- Goal: persist Tavern sessions, messages, characters, profiles, lorebook refs,
  and presets under the project Tavern directory.
- Data structures: `TavernRepository`, session/message indexes, repository safe
  summary.
- API changes: repository-backed services for create/load/save/list.
- Frontend changes: none required in this slice.
- Tests: save/load/list, stable message ordering, path traversal rejected,
  repository does not read `.env`, databases, logs, cache, `node_modules`, or
  build outputs.
- Acceptance: Tavern data is local, deterministic, and separated from world
  saves and EventLog storage.

### 5. Tavern API

- Goal: expose local project APIs for Tavern characters, sessions, messages,
  profiles, lorebook refs, and scene context.
- Data structures: request/response schemas for character/session/message CRUD,
  archive, import, safe summary, and validation errors.
- API changes: add local authoring/studio routes under
  `/projects/{project_id}/tavern/...`.
- Frontend changes: later Tavern Shell consumes these APIs.
- Tests: list/create/get/patch characters, create/archive sessions, append/list
  messages, missing project error, disabled authoring API behavior, no secrets.
- Acceptance: API never returns API keys, raw env, raw `GameState`, hidden fact
  text, NPC secrets, debug memory, or raw `state_deltas`.

### 6. Tavern Frontend Shell

- Goal: replace the Tavern stub with a minimal Tavern Studio workspace shell.
- Data structures: frontend types for Tavern safe summaries, sessions,
  characters, messages, scene context, profiles, and warnings.
- API changes: none beyond Tavern API consumption.
- Frontend changes: character list/import entry, session list/create/open,
  single-character chat entry, memory/lorebook panels, mood/tone controls,
  proposal panel, multi-character scene stub.
- Tests: `npm.cmd run build`, empty state, disabled API state, no API key or
  hidden/debug data rendered.
- Acceptance: a user can enter Tavern Mode and manage local MVP entities without
  full group RP orchestration.

### 7. Single Character Chat Backend

- Goal: support deterministic session/message flow for one user and one Tavern
  character.
- Data structures: `SingleCharacterChatRequest`,
  `SingleCharacterChatPreview`, `SingleCharacterChatApplyResult`,
  message append records.
- API changes: preview/apply endpoints for appending user messages and applying
  generated or manually supplied character replies.
- Frontend changes: later chat panel consumes preview/apply.
- Tests: preview no write, apply explicit, message order stable, no `GameState`
  mutation, no EventLog mutation.
- Acceptance: chat changes only Tavern session data.

### 8. Single Character Chat Frontend

- Goal: provide the MVP chat panel for one Tavern character.
- Data structures: frontend chat message, pending preview, safety warnings,
  provider disabled state.
- API changes: none beyond backend chat endpoints.
- Frontend changes: session transcript, message composer, preview/apply flow,
  generated reply placeholder, visible safety warnings.
- Tests: build, empty transcript, disabled API/provider state, no hidden/debug
  details in transcript.
- Acceptance: chat UI supports basic local RP workflow without exposing
  secrets or writing world state.

### 9. Multi-Character Scene Stub

- Goal: define a minimal structure for future group scenes without implementing
  complete multi-character orchestration.
- Data structures: `TavernScene`, `TavernSceneParticipant`,
  `TavernSceneTurnStub`, scene safe summary.
- API changes: minimal list/create/read scene endpoints or session scene
  metadata fields.
- Frontend changes: "multi-character scene coming later" panel with participant
  metadata and disabled turn controls.
- Tests: scene serialization, participant refs validation, no provider calls.
- Acceptance: group scene metadata exists, but no full group chat claims are
  made.

### 10. Tavern Memory System

- Goal: store RP memories as non-authoritative project memory references.
- Data structures: `TavernMemoryRecord`, `TavernMemoryVisibility`,
  `TavernMemoryContext`, memory safe summary.
- API changes: list/create/update memory endpoints and session memory linking.
- Frontend changes: memory panel with visibility labels and authoring/debug
  separation.
- Tests: memory defaults non-authoritative, hidden/debug memory filtered from
  normal RP prompt, memory cannot override facts or NPC knowledge.
- Acceptance: RP memory helps Tavern continuity but never becomes world truth.

### 11. Lorebook / World Info Integration

- Goal: provide safe lorebook/world-info context to RP without hidden leaks.
- Data structures: `TavernLorebookEntry`, `TavernWorldInfoContext`,
  filtered context result, excluded-debug metadata.
- API changes: safe context builder endpoints for session/character prompts.
- Frontend changes: lorebook/world-info panel with safe entries and hidden
  exclusion counts.
- Tests: flavor lore included, hidden entries excluded, NPC secrets excluded
  unless explicit character knowledge allows a safe summary, debug data filtered.
- Acceptance: normal RP context never includes hidden World Bible entries or
  raw hidden fact text.

### 12. Scene Mood Presets

- Goal: let sessions apply mood/style metadata without changing facts.
- Data structures: `SceneMoodPreset`, mood tags, intensity, safety flags.
- API changes: mood preset CRUD/list and session mood selection.
- Frontend changes: mood selector with safe preset summaries.
- Tests: mood serialization, mood affects style context only, no state changes,
  no hidden facts.
- Acceptance: mood influences expression only.

### 13. Relationship Tone System

- Goal: model relationship tone for RP presentation and continuity.
- Data structures: `RelationshipTone`, `RelationshipToneState`,
  tone transition proposal.
- API changes: tone list/update endpoints scoped to Tavern sessions or
  character pairs.
- Frontend changes: relationship tone controls and safety labels.
- Tests: tone changes do not alter World relationship state, tone proposals are
  separated from World facts, private notes redacted.
- Acceptance: relationship tone is Tavern presentation metadata unless promoted
  through a validated proposal.

### 14. Tavern Prompt Profile Integration

- Goal: use Tavern-scoped prompt profiles while preserving LLM authority
  boundaries.
- Data structures: `TavernPromptContext`, `TavernPromptProfileSelection`,
  safety-filtered context refs.
- API changes: profile selection for Tavern character/session generation.
- Frontend changes: prompt profile selector with compatibility warnings.
- Tests: only Tavern-scoped profiles accepted, forbidden permissions rejected,
  hidden facts/API keys/raw state deltas excluded.
- Acceptance: prompt profiles can influence style and format, not facts,
  permissions, visibility, or world state.

### 15. Tavern Response Generation Service

- Goal: optionally generate RP replies for Tavern sessions.
- Data structures: `GeneratedTavernReply`, `TavernGenerationRequest`,
  `TavernGenerationSafetyReport`.
- API changes: generation preview endpoint and explicit apply endpoint for
  saving generated replies as messages.
- Frontend changes: generate/review/apply controls in chat panel.
- Tests: fake/mock/local provider only, all calls through Provider Gateway /
  `LLMProvider`, hidden facts excluded from provider input, schema validation
  errors handled clearly.
- Acceptance: generated text is an RP draft/reply only and cannot modify
  `GameState`, EventLog, world facts, or NPC knowledge.

### 16. Tavern to World Proposal

- Goal: convert important RP outcomes into explicit World proposal candidates.
- Data structures: `TavernWorldProposal`, `TavernWorldProposalType`,
  `TavernWorldProposalValidationReport`.
- API changes: create/list/validate proposal endpoints under Tavern or project
  proposal routes.
- Frontend changes: proposal panel for candidate facts, relationship changes,
  quest hooks, NPC notes, and warnings.
- Tests: proposal does not write content packs or active saves, validation
  catches unsafe/missing refs, hidden notes excluded from public fields.
- Acceptance: Tavern -> World is always proposal / validation, never direct
  world mutation.

### 17. World NPC to Tavern Character Adapter

- Goal: create Tavern character drafts from safe World NPC summaries.
- Data structures: `WorldNpcTavernAdapter`, `NpcToTavernCharacterDraft`,
  adapter warnings.
- API changes: preview/apply endpoints for NPC-to-Tavern character draft
  creation.
- Frontend changes: "create Tavern character from World NPC" action with
  preview and visibility warnings.
- Tests: preview excludes hidden NPC secrets, apply does not modify NPC, missing
  NPC fails clearly, CrossModeLink optional.
- Acceptance: adapter creates a Tavern draft/reference only.

### 18. Tavern Safety / Boundary Evals

- Goal: add deterministic safety checks for RP prompts, exports, memories,
  proposals, and reports.
- Data structures: `TavernSafetyEvalCase`, `TavernSafetyReport`,
  issue severity enum.
- API changes: safety eval endpoint and Project Quality Gate integration.
- Frontend changes: safety report panel or warning summary in Tavern Shell.
- Tests: hidden fact leak detection, NPC secret exclusion, raw `state_deltas`
  exclusion, provider secret exclusion, no real API calls.
- Acceptance: high-risk boundary violations are blockers.

### 19. v2.3 Integration Regression Tests

- Goal: prove Tavern MVP works with v2.1 NarrativeProject and v2.2 Novel/World
  boundaries.
- Data structures: focused fixtures for projects, characters, lorebooks,
  sessions, memory, world NPC refs, and fake provider outputs.
- API changes: none.
- Frontend changes: build coverage for Tavern shell.
- Tests: full deterministic backend suite and frontend build.
- Acceptance: v2.3 can be released only if integration tests show no state,
  visibility, provider, import/export, or proposal boundary regressions.

## Impact on NarrativeProject

- Tavern becomes a first-class mode section in `NarrativeProject`.
- Project workspace should reserve Tavern storage for characters, sessions,
  lorebooks, scene presets, memory refs, profiles, proposals, and exports.
- Project validation must include Tavern refs, profile permissions, prompt
  safety, export safety, and proposal validity.
- Project import/export must exclude `.env`, API keys, raw env, databases, logs,
  cache, debug memory, raw `state_deltas`, provider secrets, and unsafe
  executable files.

## Impact on Novel Studio

- Novel Studio remains independent and keeps draft/proposal semantics.
- Tavern sessions may link to Novel characters or scene refs through
  `CrossModeLink`, but no Tavern memory or RP output becomes Novel canon unless
  explicitly imported as a Novel draft.
- Novel exports must not include Tavern hidden memory, private character notes,
  NPC secrets, or raw RP debug context.

## Impact on World Mode / GameState

- World Mode remains the only runtime fact engine.
- Tavern Mode must not directly modify `GameState`, `StateDelta`, `EventLog`,
  world content packs, or active saves.
- Tavern proposals can reference World NPCs, facts, locations, quests, or
  relationships, but application to World content/state requires existing World
  validation paths.
- RP memory and relationship tone cannot override NPC knowledge or world facts.

## Impact on CrossModeLink

- `CrossModeLink` should record optional references such as:
  - Tavern character -> shared CharacterProfile.
  - Tavern character -> World NPC.
  - Tavern session -> project memory record.
  - RP outcome -> World proposal.
  - World NPC -> Tavern character draft.
- Cross-mode links must not expose hidden targets in normal views.
- Broken or missing refs should be validation warnings/errors, not silent
  conversions.

## LLM Boundary

- LLMs remain language generators only.
- Tavern generation must use Provider Gateway / `LLMProvider`.
- Prompt profiles cannot enable `can_access_hidden_facts`, `can_modify_state`,
  `can_override_action_result`, or `can_bypass_visibility`.
- RP prompts may include safe character summaries, safe lorebook/world-info,
  safe memory, scene mood, relationship tone, and style instructions.
- RP prompts must not include API keys, raw env, hidden facts, NPC secrets,
  debug memory, raw `state_deltas`, provider secrets, or private authoring
  notes.
- Generated RP output must be schema-validated before it can be saved as a
  Tavern message.

## Visibility, Privacy, and Memory Risks

- Hidden World Bible entries, hidden lore/facts, NPC secrets, hidden witnesses,
  debug memory, and raw `state_deltas` are the main leak risks.
- Character private notes are authoring-only and must not enter normal RP
  prompt/export.
- Tavern memory has visibility labels and defaults to non-authoritative.
- Normal reports and exports should show safe labels, counts, refs, or redacted
  summaries rather than hidden text.
- Debug views must remain explicitly gated and separate from player/RP normal
  views.

## v2.3 Integration Test Requirements

- Tavern schema serialization and defaults.
- Character card import preview/apply without direct `GameState` mutation.
- RP Profile / Voice Profile safe summaries excluding secrets/private notes.
- Tavern session repository save/load/list with path traversal rejection.
- Tavern API disabled behavior and secret-safe responses.
- Single-character chat with fake/mock/local provider only.
- RP prompt context excluding hidden facts, NPC secrets, debug memory, raw
  `state_deltas`, API keys, provider secrets, and character private notes.
- Tavern memory not becoming authoritative facts.
- Lorebook / World Info safe filtering.
- Scene Mood and Relationship Tone affecting style only.
- Tavern-to-World proposal creating candidate objects only.
- World NPC adapter creating Tavern draft/reference only.
- Project Quality Gate integration for Tavern safety checks.
- Frontend build:
  - `cd frontend && npm.cmd run build`
- Backend suite:
  - `python -m pytest`

## Final Acceptance Criteria

- Tavern Core, repository, API, and frontend shell are usable locally.
- Single-character chat works with explicit save/apply behavior.
- Character card import creates Tavern drafts, not World NPC overwrites.
- RP Profile, Voice Profile, Scene Mood, Relationship Tone, and prompt profile
  integration affect expression only.
- Tavern response generation uses Provider Gateway and fake/mock/local providers
  in tests.
- Tavern -> World creates proposals only and requires validation.
- World NPC -> Tavern character creates drafts/references only.
- Hidden facts, NPC secrets, private notes, debug memory, raw `state_deltas`,
  API keys, and raw env do not enter normal prompts, UI, exports, reports, or
  packages.
- Full backend tests and frontend build pass.

## v2.4 Candidate Direction

v2.4 should focus on a deeper World Studio / cross-mode production workflow:
validated proposal review, richer World authoring from Novel/Tavern drafts,
Tavern multi-character scene expansion if the v2.3 stub proves stable, and
stronger project-level quality dashboards. It should not move to online
platform features until local boundaries, exports, and compatibility remain
stable across Novel, Tavern, and World modes.
