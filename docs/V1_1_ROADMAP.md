# v1.1 Roadmap: Roleplay Immersion Layer

## Goal

v1.1 adds a **Roleplay Immersion Layer** on top of the stable v1.0 local studio.
The goal is to absorb useful tavern-style roleplay features such as character
cards, voice profiles, emotional tone, multi-character scenes, lorebook entries,
and example dialogue while preserving the existing world-engine fact boundary.

The world engine remains the source of truth. The LLM may help express,
summarize, and format roleplay output, but it does not judge world outcomes,
complete quests, decide combat, invent canonical facts, or directly mutate
`GameState`.

## Out Of Scope

- LLM world judging.
- LLM direct `GameState` mutation.
- LLM-decided combat outcomes.
- LLM-decided quest completion.
- LLM bypassing visibility rules.
- NPCs knowing facts outside their NPC knowledge.
- Executing scripts from character cards, lorebooks, imports, templates, or
  example dialogue.
- Online character marketplaces.
- Cloud sync, accounts, multiplayer, or online collaboration.
- Automatically importing untrusted external content into an active world.
- RP prompt profiles changing fact authority, visibility, or world rules.
- Replacing v1.0 `StateDelta`, `EventLog`, save migration, content validation,
  or quality gate boundaries.

## Hard Constraints

1. LLM output cannot directly modify `GameState`.
2. All canonical state changes go through `StateDelta`.
3. Player actions, system ticks, NPC planning ticks, and RP scene events must
   record `Event` entries.
4. NPC prompts and dialogue contexts can only include facts allowed by NPC
   knowledge.
5. Narrator prompts can only include visible facts and narrator-safe memory.
6. RP profiles may change expression style, tone, and formatting, not facts.
7. Character card import produces candidate profiles/content drafts only. It
   cannot modify active `GameState`.
8. Lorebook import must classify entries as `flavor_lore`, `structured_fact`,
   `hidden_fact`, or `unsafe_entry`.
9. RP prompts must not contain hidden facts unless current world state and
   visibility explicitly permit those facts for that actor/context.
10. RP output must pass a consistency check before being treated as safe
    player-facing narration/dialogue.

## Recommended Development Order

1. **Roleplay Boundary Contract**
2. **RP Profile / Voice Profile Schema**
3. **Character Card Importer**
4. **Lorebook Import / Classification**
5. **Example Dialogue Manager**
6. **RP Memory Context Builder**
7. **RP Prompt Profile Manager**
8. **RP Output Consistency Checker**
9. **NPC Emotional State System**
10. **Relationship Tone System**
11. **Dialogue Mode**
12. **Multi-NPC Scene / Group RP**
13. **Scene Mood Presets**
14. **Tavern Compatibility Import / Export**
15. **RP Frontend Panels**
16. **RP Scenario Templates**
17. **RP Boundary Evals**
18. **RP Regression Playtests**
19. **v1.1 Integration Tests And Acceptance**

The first phase should start with the boundary contract and schemas. That keeps
the charming roleplay layer from sneaking around the engine like it owns the
keys.

## Modules

### 1. Roleplay Boundary Contract

Goal:

- Document exactly what RP systems may read, write, prompt, import, export, and
  display.
- Define player-facing, narrator-safe, NPC-known, authoring-only, debug-only,
  and unsafe roleplay content categories.

Data structures:

- `RoleplayBoundaryContract`
- `RoleplayContextScope`
- `RoleplayVisibilityClass`
- `RoleplaySafetyDecision`

API changes:

- Optional local-only read endpoint:
  - `GET /studio/roleplay/boundary`
- No player API change required.

Frontend changes:

- Add local documentation/status panel inside Settings or Studio Home.
- Show local-only warning for RP imports and prompt profiles.

Tests:

- Boundary contract serializes to JSON.
- Player-facing scopes exclude hidden/debug classes.
- NPC scopes require knowledge checks.

Acceptance:

- All later RP modules reference this contract.
- Contract explicitly states that RP cannot modify world facts.

GameState / NPC Knowledge / Visibility impact:

- No direct schema change.
- Clarifies how RP contexts map to existing visibility and NPC knowledge rules.

LLM boundary impact:

- LLM authority remains unchanged.

Leak risk:

- Low if enforced by shared builders and tests.

### 2. RP Profile / Voice Profile Schema

Goal:

- Define character expression profiles independent of canonical facts.
- Support style, tone, speech quirks, formality, pacing, allowed topics, and
  avoidance rules.

Data structures:

- `RPProfile`
- `VoiceProfile`
- `SpeechStyle`
- `RPProfileSource`
- `RPProfileValidationReport`

Fields:

- `id`
- `display_name`
- `applies_to_npc_id`
- `style_tags`
- `tone_defaults`
- `speech_patterns`
- `do_not_say`
- `allowed_registers`
- `example_dialogue_ids`
- `source`
- `visibility`
- `enabled`

API changes:

- `GET /authoring/worlds/{world_id}/rp/profiles`
- `POST /authoring/worlds/{world_id}/rp/profiles/preview`
- `POST /authoring/worlds/{world_id}/rp/profiles/validate`
- `PUT /authoring/worlds/{world_id}/rp/profiles`

All endpoints are gated by `ENABLE_AUTHORING_API`.

Frontend changes:

- Add RP Profiles panel under Authoring.
- Support profile list, NPC association, style fields, preview, validate, and
  save.

Tests:

- Valid profile passes validation.
- Profile cannot include hidden facts as style instructions.
- Profile cannot grant NPC knowledge.
- Disabled authoring API rejects access.

Acceptance:

- Profiles change generated wording only.
- Active `GameState` is unchanged by preview/validate/save until content pack
  edits are explicitly saved.

GameState / NPC Knowledge / Visibility impact:

- Optional content-pack additions only.
- No runtime fact authority change.

LLM boundary impact:

- Profiles may influence prompt style but not prompt facts.

Leak risk:

- Medium: profiles can accidentally include secret text. Validation must flag
  hidden fact text and unsafe instructions.

### 3. Character Card Importer

Goal:

- Import tavern-style character cards or JSON/YAML character definitions into
  safe candidate RP profiles and NPC content drafts.

Data structures:

- `CharacterCardImportRequest`
- `CharacterCardImportResult`
- `ImportedCharacterCandidate`
- `CharacterCardFieldClassification`

Classification:

- `profile_style`
- `public_bio`
- `candidate_structured_fact`
- `candidate_hidden_fact`
- `example_dialogue`
- `unsafe_instruction`
- `unsupported_field`

API changes:

- `POST /authoring/roleplay/character-cards/preview`
- `POST /authoring/roleplay/character-cards/validate`
- Optional explicit apply draft endpoint:
  - `POST /authoring/worlds/{world_id}/roleplay/character-cards/apply-draft`

Apply must be authoring-only, explicit, and validation-gated.

Frontend changes:

- Character Card Import panel.
- Show classified fields before apply.
- Require confirmation for candidate profile/content draft creation.

Tests:

- Safe card imports to candidate profile.
- Script-like fields become `unsafe_instruction`.
- Hidden fact-like fields are not player-facing.
- Import preview does not write files.
- Apply does not modify active `GameState`.

Acceptance:

- Import creates candidates only.
- No card field can execute code or bypass validation.

GameState / NPC Knowledge / Visibility impact:

- None at import preview.
- Draft content can later become content-pack YAML only after explicit save and
  validation.

LLM boundary impact:

- Import classification should be deterministic code for v1.1. If future LLM
  assistance is added, it must be separately gated and remain draft-only.

Leak risk:

- High unless every imported field is classified and unsafe/hidden fields are
  blocked from player-facing output.

### 4. Lorebook Import / Classification

Goal:

- Import lorebook entries while separating flavor text from structured facts,
  hidden facts, and unsafe entries.

Data structures:

- `LorebookEntryCandidate`
- `LorebookImportResult`
- `LorebookEntryClass`
- `LorebookActivationRule`

Required classes:

- `flavor_lore`
- `structured_fact`
- `hidden_fact`
- `unsafe_entry`

API changes:

- `POST /authoring/roleplay/lorebook/preview`
- `POST /authoring/roleplay/lorebook/validate`
- `POST /authoring/worlds/{world_id}/roleplay/lorebook/apply-draft`

Frontend changes:

- Lorebook import panel with classification table.
- Filters by safe/hidden/unsafe class.
- Explicit apply for safe drafts.

Tests:

- Flavor lore remains non-authoritative.
- Structured fact candidates require validation.
- Hidden fact entries do not enter narrator/player contexts.
- Unsafe entries cannot apply.
- Path traversal and scripts are rejected.

Acceptance:

- Lorebook entries never become active facts automatically.
- Hidden and unsafe entries are clearly marked.

GameState / NPC Knowledge / Visibility impact:

- Potential content-pack fact drafts only after explicit validation.
- NPC knowledge rules decide who can receive imported facts.

LLM boundary impact:

- Lorebook text cannot expand prompt authority.

Leak risk:

- High because lorebooks often contain spoilers. Classification and tests are
  mandatory.

### 5. Example Dialogue Manager

Goal:

- Store example dialogues as style and format references, not canonical events.

Data structures:

- `ExampleDialogue`
- `ExampleDialogueLine`
- `ExampleDialogueUsagePolicy`

Fields:

- `id`
- `npc_id`
- `speaker`
- `text`
- `tags`
- `visibility`
- `usage`: `style_only | format_only | forbidden_runtime_fact`

API changes:

- `GET /authoring/worlds/{world_id}/roleplay/example-dialogue`
- `POST /authoring/worlds/{world_id}/roleplay/example-dialogue/preview`
- `POST /authoring/worlds/{world_id}/roleplay/example-dialogue/validate`
- `PUT /authoring/worlds/{world_id}/roleplay/example-dialogue`

Frontend changes:

- Example Dialogue panel in Authoring.
- Highlight hidden/unsafe example lines.

Tests:

- Example dialogue does not enter `GameState`.
- Example dialogue cannot mark facts as known.
- Hidden example text is not included in player-facing prompts.

Acceptance:

- Examples influence style only through safe prompt builders.

GameState / NPC Knowledge / Visibility impact:

- None directly.

LLM boundary impact:

- Prompt builders must label examples as examples, not facts.

Leak risk:

- Medium: example text may include spoilers. Validate against hidden facts.

### 6. RP Memory Context Builder

Goal:

- Add roleplay-specific memory context construction while reusing v1.0 memory
  visibility rules.

Data structures:

- `RPMemoryContext`
- `RPMemorySelectionReason`
- `RPActorContext`

API changes:

- Optional debug/local endpoint:
  - `POST /debug/roleplay/memory-context/preview`

Frontend changes:

- Debug-only RP memory preview panel.

Tests:

- `hidden` and `debug_only` memory excluded from narrator/RP player context.
- NPC RP memory includes only NPC-known entries.
- Memory remains non-authoritative.

Acceptance:

- RP memory context cannot introduce new facts.

GameState / NPC Knowledge / Visibility impact:

- Uses existing memory records and knowledge checks.

LLM boundary impact:

- RP prompts get filtered memory only.

Leak risk:

- High if memory filters are bypassed; use shared `MemoryContextBuilder`.

### 7. RP Prompt Profile Manager

Goal:

- Extend prompt profiles for roleplay output style without expanding LLM
  authority.

Data structures:

- `RPPromptProfile`
- `RPPromptVariant`
- `RPTemperatureOverride`

API changes:

- `GET /studio/roleplay/prompt-profiles`
- `POST /studio/roleplay/prompt-profiles/select`
- Authoring endpoints for local profile files if stored in content.

Frontend changes:

- Settings / Privacy RP prompt section.
- Show selected RP profile and safety status.

Tests:

- Invalid profile requesting hidden facts is rejected.
- Selected profile changes tone metadata only.
- Provider factory remains the only provider selection entry.

Acceptance:

- Prompt profile cannot change facts, visibility, rules, or GameState.

GameState / NPC Knowledge / Visibility impact:

- None.

LLM boundary impact:

- Style-only.

Leak risk:

- Medium: unsafe prompt instructions must be validated.

### 8. RP Output Consistency Checker

Goal:

- Check roleplay output before display or storage for contradictions, invented
  facts, hidden leaks, NPC knowledge violations, and unsafe instructions.

Data structures:

- `RPOutputCheckRequest`
- `RPOutputCheckResult`
- `RPOutputIssue`

Rules:

- No invented item/location/NPC/fact.
- No hidden fact leak.
- No NPC speaking from unknown knowledge.
- No contradiction with `ActionResult` or visible state.
- No treating memory/example dialogue as canonical fact.
- No raw debug/state-delta text.

API changes:

- `POST /roleplay/output/check`
- Optional local debug endpoint for detailed explanation:
  - `POST /debug/roleplay/output/check`

Frontend changes:

- Show RP output safety status in dialogue/debug panels.

Tests:

- Invented item fails.
- Hidden fact leak fails.
- NPC unknown fact fails.
- Correct roleplay output passes.
- Normal result redacts hidden text.

Acceptance:

- Dialogue and group RP outputs pass checker before player display.

GameState / NPC Knowledge / Visibility impact:

- Read-only.

LLM boundary impact:

- Checker is deterministic code, not an LLM judge.

Leak risk:

- Medium: failure reports must not print hidden text in normal view.

### 9. NPC Emotional State System

Goal:

- Add lightweight emotional state to NPCs for roleplay tone while keeping
  deterministic rules and `StateDelta`.

Data structures:

- `NPCEmotionState`
- `EmotionBand`
- `EmotionCause`

Potential fields:

- `current_emotion`
- `intensity`
- `valence`
- `arousal`
- `causes`
- `expires_turn`

API changes:

- Player visible state may include safe emotion bands for visible NPCs.
- Debug API may include detailed causes.

Frontend changes:

- Show NPC mood/emotion badge in player UI for visible NPCs.
- Authoring/debug details stay separate.

Tests:

- Emotional changes are applied through `StateDelta`.
- Hidden causes do not enter player UI.
- Dead/incapacitated NPCs do not update emotion inappropriately.

Acceptance:

- Emotions influence dialogue tone only.
- Emotions do not create facts or override relationships.

GameState / NPC Knowledge / Visibility impact:

- Possible additive `NPCState` fields; migration may be required if persisted.
- Player sees only safe summaries.

LLM boundary impact:

- LLM may receive safe emotion band, not hidden cause text.

Leak risk:

- Medium: emotion causes may reveal secrets. Split visible band from debug cause.

### 10. Relationship Tone System

Goal:

- Convert relationship values into player/NPC-safe dialogue tone bands.

Data structures:

- `RelationshipTone`
- `ToneBand`
- `ToneReason`

API changes:

- Player graph/visible state may include safe tone band for known
  relationships.
- Debug graph may include full reasons under debug gate.

Frontend changes:

- Relationship panel displays tone band.
- Authoring social graph can preview tone.

Tests:

- Hidden relationships do not produce player tone.
- Tone reasons are safe summaries.
- Relationship changes still use `StateDelta`.

Acceptance:

- Tone is derived from known relationship data and cannot reveal hidden edges.

GameState / NPC Knowledge / Visibility impact:

- Derived field preferred; persisted only if needed with migration.

LLM boundary impact:

- Dialogue prompts may receive safe tone band for that actor.

Leak risk:

- Medium if reasons include hidden relationship details.

### 11. Dialogue Mode

Goal:

- Add a focused roleplay dialogue loop for one visible NPC while using existing
  action/event/state boundaries.

Data structures:

- `DialogueSession`
- `DialogueTurn`
- `DialogueContext`
- `DialogueModeResult`

API changes:

- `POST /game/{session_id}/dialogue/start`
- `POST /game/{session_id}/dialogue/input`
- `POST /game/{session_id}/dialogue/end`

Player-facing responses include safe dialogue text and filtered visible state.

Frontend changes:

- Dialogue panel with active NPC, recent lines, safe emotion/tone, and exit.

Tests:

- Starting dialogue with hidden/unseen NPC fails.
- Dialogue input records Event.
- Any state changes go through `StateDelta`.
- NPC context excludes unknown facts.
- Output consistency checker runs.

Acceptance:

- Dialogue is immersive but not fact-authoritative.

GameState / NPC Knowledge / Visibility impact:

- May add active dialogue session state.
- NPC knowledge gate is mandatory.

LLM boundary impact:

- LLM renders dialogue after rule context is built.
- LLM cannot decide quest completion or relationship changes.

Leak risk:

- High: dialogue prompts are rich. They must use roleplay context builders.

### 12. Multi-NPC Scene / Group RP

Goal:

- Support scenes involving multiple visible NPCs with per-actor knowledge and
  voice context.

Data structures:

- `RPScene`
- `RPSceneParticipant`
- `RPSceneTurn`
- `ParticipantContext`

API changes:

- `POST /game/{session_id}/roleplay/scenes/start`
- `POST /game/{session_id}/roleplay/scenes/input`
- `POST /game/{session_id}/roleplay/scenes/end`

Frontend changes:

- Group RP panel with participant list, speaker labels, and visible safety
  badges.

Tests:

- Hidden NPC cannot join player-facing scene.
- Each participant receives only their own knowledge.
- Scene event records Event.
- Output checker catches cross-NPC hidden leak.

Acceptance:

- Group RP supports tone and voice without shared omniscience.

GameState / NPC Knowledge / Visibility impact:

- Scene state may be runtime/session-only or persisted through save schema with
  migration.

LLM boundary impact:

- Prompt builder must isolate participant knowledge.

Leak risk:

- High: multi-actor prompts can accidentally blend knowledge. Requires strong
  tests.

### 13. Scene Mood Presets

Goal:

- Provide safe mood presets for scene presentation and narrator/dialogue style.

Data structures:

- `SceneMoodPreset`
- `MoodPresetScope`

API changes:

- `GET /roleplay/mood-presets`
- Authoring endpoints if presets are world-defined.

Frontend changes:

- Mood preset selector for dialogue/group RP.

Tests:

- Mood presets cannot include hidden facts.
- Mood preset changes style only.

Acceptance:

- Mood affects expression, not facts or rule outcomes.

GameState / NPC Knowledge / Visibility impact:

- None unless active mood is saved as session metadata.

LLM boundary impact:

- Safe style input only.

Leak risk:

- Low to medium depending on custom preset text.

### 14. Tavern Compatibility Import / Export

Goal:

- Support import/export of common tavern-style character/lore/profile data as
  local, safe drafts.

Data structures:

- `TavernImportManifest`
- `TavernExportManifest`
- `TavernCompatibilityReport`

API changes:

- `POST /authoring/roleplay/tavern/import/preview`
- `POST /authoring/roleplay/tavern/import/apply-draft`
- `GET /authoring/roleplay/tavern/export/{profile_id}`

Frontend changes:

- Tavern compatibility panel under Authoring.

Tests:

- Import rejects executable/script fields.
- Import preview does not write files.
- Apply requires explicit confirmation and validation.
- Export omits API keys and hidden state unless explicitly debug/local export
  and documented.

Acceptance:

- Compatibility is best-effort and local-only.

GameState / NPC Knowledge / Visibility impact:

- No active world changes without explicit authoring save.

LLM boundary impact:

- Import/export does not call LLM by default.

Leak risk:

- High because imported cards may contain secrets and prompt injections.

### 15. RP Frontend Panels

Goal:

- Add local studio panels for RP profile editing, character card import,
  lorebook review, dialogue mode, scene mood, example dialogue, and RP safety.

Data structures:

- TypeScript mirrors for schemas above.

API changes:

- No extra backend changes beyond module endpoints.

Frontend changes:

- `Roleplay` workspace section.
- Authoring panels for profiles/imports/lorebooks/examples.
- Player-facing dialogue panel for safe dialogue mode.
- Debug-only RP context inspection panel.

Tests:

- `npm.cmd run build` passes.
- Disabled authoring/debug APIs degrade safely.
- Player UI does not show debug-only RP data.
- Import panels do not display API keys or raw hidden state.

Acceptance:

- RP UI is clearly separated between player, authoring, and debug scopes.

GameState / NPC Knowledge / Visibility impact:

- UI must not infer hidden state client-side.

LLM boundary impact:

- UI cannot send unfiltered raw state to LLM.

Leak risk:

- Medium: front-end panels can blur authoring/player zones. Visual separation
  required.

### 16. RP Scenario Templates

Goal:

- Add safe local templates for roleplay-heavy scenes and character setup.

Data structures:

- Extend `ScenarioTemplate` with RP template types:
  - `character_voice`
  - `dialogue_scene`
  - `group_scene`
  - `lorebook_seed`
  - `relationship_tone_seed`

API changes:

- Reuse template browser endpoints.

Frontend changes:

- Template Browser filter for RP templates.

Tests:

- RP templates preview and render without writing disk.
- Rendered content validates.
- Templates do not execute scripts or call LLM.

Acceptance:

- Templates are safe authoring drafts only.

GameState / NPC Knowledge / Visibility impact:

- None until explicit content save and reload.

LLM boundary impact:

- No LLM calls.

Leak risk:

- Medium if templates contain hidden text in player-facing fields.

### 17. RP Boundary Evals

Goal:

- Add evals for roleplay prompt/output boundaries.

Data structures:

- `RPBoundaryEvalCase`
- `RPBoundaryEvalReport`

Coverage:

- Character card prompt injection.
- Lorebook hidden fact leak.
- NPC unknown fact in dialogue.
- Example dialogue mistaken as fact.
- Debug memory in RP prompt.
- Multi-NPC knowledge bleed.
- RP output invented item/location/quest stage.

API changes:

- Optional local eval endpoint:
  - `POST /evals/roleplay/run`

Frontend changes:

- Optional dashboard integration with narrative/quality eval panels.

Tests:

- All evals use fake/mock outputs.
- No external LLM judge.
- Failure summaries do not print hidden text.

Acceptance:

- RP boundary suite runs in CI/local tests.

GameState / NPC Knowledge / Visibility impact:

- Read-only.

LLM boundary impact:

- Verifies boundary.

Leak risk:

- Low if fixtures redact hidden text in failure output.

### 18. RP Regression Playtests

Goal:

- Add deterministic regression scenarios for dialogue and group RP paths.

Data structures:

- Extend `PlaytestScenario` with:
  - `dialogue_path`
  - `group_rp_path`
  - `character_voice_probe`
  - `lorebook_leak_probe`

API changes:

- Reuse playtest batch and scenario regression APIs.

Frontend changes:

- Playtesting Dashboard can filter RP scenarios.

Tests:

- Dialogue scenario deterministic.
- Hidden lore leak probe fails safely.
- Group RP does not share hidden knowledge across NPCs.
- Events are recorded for RP scene turns.

Acceptance:

- RP regression suite is part of v1.1 quality gate smoke path.

GameState / NPC Knowledge / Visibility impact:

- Tests enforce no direct mutation and no NPC omniscience.

LLM boundary impact:

- Uses mock/local_stub provider.

Leak risk:

- Medium; normal reports must redact hidden text.

## v1.1 Integration Test Requirements

The v1.1 integration suite must cover:

1. Character card import preview, validation, unsafe-field rejection, and
   explicit draft apply.
2. Lorebook classification into flavor, structured fact, hidden fact, and
   unsafe entry.
3. RP profile and prompt profile validation.
4. Example dialogue style-only behavior.
5. RP memory context filtering for narrator/player/NPC contexts.
6. Dialogue mode with visible NPC only.
7. Group RP with per-NPC knowledge isolation.
8. Emotional state and relationship tone changes through `StateDelta`.
9. RP output consistency checker.
10. RP frontend build and disabled API fallback.
11. Hidden fact, NPC secret, debug memory, raw state_delta, and example-dialogue
    leak regression.
12. Save/load/migration compatibility if RP session/emotion fields are
    persisted.
13. Quality gate smoke integration for RP evals/playtests.

Required commands:

```powershell
python -m pytest
cd frontend
npm.cmd run build
python -m backend.app.tools.quality_gate --world mist_valley --profile standard
```

## Final Acceptance Criteria

v1.1 can be accepted when:

- All v1.0 release boundaries still pass.
- RP imports are draft-only and cannot execute scripts.
- RP profile, voice profile, lorebook, and example dialogue schemas are
  documented and validated.
- Dialogue and group RP produce Events.
- Any canonical state change uses `StateDelta`.
- NPC dialogue contexts are limited by NPC knowledge.
- Narrator/RP prompts receive only visible facts and narrator-safe memory.
- RP output consistency checks block or flag hidden leaks and invented
  canonical facts.
- Player UI does not show authoring/debug RP data.
- `python -m pytest` and frontend build pass.
- No real API key or hidden text appears in normal reports.

## v1.2 Candidates

- More expressive scene director tools that remain non-authoritative.
- Better local voice/style preview with side-by-side safe context inspection.
- Optional relationship arc authoring, still rule-validated.
- More tavern/card format adapters.
- Richer RP quality dashboards and history comparisons.
- Expanded sample worlds focused on dialogue-heavy play.
- Optional local model adapter refinements behind `LLMProvider`.

