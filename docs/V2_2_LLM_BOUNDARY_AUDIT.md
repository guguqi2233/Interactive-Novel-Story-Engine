# v2.2 LLM Boundary Audit

## Audit Scope

Reviewed v2.2 Novel Studio MVP code and tests, with emphasis on:

- `backend/app/platform/novel_studio.py`
- `backend/tests/test_v22_novel_studio_mvp.py`
- `backend/tests/test_v22_integration_regression.py`
- existing `ProjectPromptProfile`, Provider Gateway, and `LLMProvider` rules

## Passed Items

1. **Novel Mode does not let LLM directly modify `GameState`.**
   - Novel schemas, repository, outline/chapter/scene services, export,
     consistency checks, and quality evals are project-local draft systems.
   - Tests assert `GameState` is unchanged across Novel generation, import, and
     conversion paths.

2. **Novel Draft Generation only creates draft/proposal output.**
   - `NovelDraftGenerationService` returns schema-validated
     `GeneratedNovelDraft`.
   - Saving generated text requires explicit confirmation and writes only Novel
     scene draft text through `NovelRepository`.
   - It does not create `StateDelta`, `Event`, world facts, or content-pack
     files.

3. **Novel to World Draft Conversion does not write content pack or
   `GameState`.**
   - `NovelToWorldDraftService` returns `WorldContentDraft` candidates.
   - Tests confirm no world content-pack file is written.

4. **EventLog to Chapter Draft Import does not modify `EventLog`.**
   - `EventLogToNovelDraftService.preview_import()` reads event summaries only.
   - `apply_import()` writes Novel chapter draft text only after explicit
     confirmation.
   - Tests compare serialized EventLog before and after apply.

5. **Prompt Profile cannot enable hidden fact access or state modification.**
   - `ProjectPromptProfile` keeps `can_access_hidden_facts`,
     `can_modify_state`, `can_override_action_result`, and
     `can_bypass_visibility` as `Literal[False]`.
   - v2.2 tests assert unsafe profile construction is rejected.

6. **Provider Gateway / `LLMProvider` remains the model boundary.**
   - `NovelDraftGenerationService` accepts an injected `LLMProvider`.
   - It does not instantiate `OpenAIProvider`, `LocalHTTPProvider`, or any
     concrete provider directly.

7. **NovelPromptContext excludes forbidden prompt material.**
   - `NovelPromptContext` rejects secret-like content, `api_key`, and raw
     `state_delta` markers.
   - `NovelDraftGenerationService._generate()` re-checks for secret-like text,
     hidden fact markers, and raw state-delta markers before provider calls.

8. **WorldBible hidden entries do not enter Novel prompt context.**
   - `NovelWorldBibleContextBuilder` excludes hidden World Bible entries from
     normal context.
   - Debug exclusions list ids/reasons only, not hidden text.

9. **Character private notes do not enter LLM prompt.**
   - `CharacterProfile.safe_summary()` omits `private_notes_authoring_only`.
   - `NovelPromptContextBuilder` uses safe character summaries only.

10. **Raw state deltas do not enter draft generation prompt.**
    - `NovelPromptContext` and generation service reject raw state-delta
      markers.
    - EventLog import uses safe event summaries and filters text containing
      state-delta markers.

11. **Memory is not treated as authoritative fact.**
    - v2.2 Novel prompt context uses safe summaries and does not promote memory
      into world facts.
    - Existing v2.1 memory library keeps `authoritative: false`.

12. **Schema validation failures have clear errors.**
    - `GeneratedNovelDraft` is a Pydantic schema.
    - Fake provider schema failures propagate as provider/schema errors rather
      than applying partial state.

13. **Tests do not call real APIs.**
    - v2.2 tests use `FakeLLMProvider` and local `Settings(llm_provider="mock")`.

14. **Novel Quality Evals do not use external LLM judge.**
    - `NovelConsistencyChecker` and `NovelQualityEvaluator` are deterministic
      rule-based checks.

## Risk Items

- `NovelDraftGenerationService` is intentionally generic and accepts any
  injected `LLMProvider`. Production wiring must continue to obtain providers
  through Provider Gateway / factory code rather than constructing concrete
  provider classes in Novel modules.
- `NovelWorldBibleContextBuilder` supports authoring/debug notes when explicitly
  requested. UI and API callers must keep authoring/debug contexts separate
  from normal prompt/export contexts.

## High Risk Issues

None found.

## Medium Risk Issues

None blocking. The provider injection point should be reviewed again when a
full Novel generation UI/API is added.

## Minor Issues

- v2.2 tests cover the fake-provider path. Future provider-routing integration
  tests should verify the same boundaries through a full Gateway route when
  that UI/API is introduced.

## Recommendations

1. Keep `NovelDraftGenerationService` provider construction outside Novel code.
2. Add a future integration test for full Provider Gateway routing once Novel
   generation is exposed through API/UI.
3. Keep authoring/debug World Bible notes visually labeled and excluded from
   normal/export modes.

## Blocking Status

This audit does **not** block v2.2 acceptance.
