# v2.4 LLM Boundary Audit

## Verdict

v2.4 Cross-Mode Bridge does not expand LLM authority. The implemented bridge
schemas, repository, validation, pipelines, quality-gate hook, import/export
filters, audit trail, and frontend review surfaces keep Novel/Tavern outputs as
drafts or proposals by default. World-changing apply paths require explicit
confirmation and, when runtime state is provided, use `StateDelta` plus
`EventLog`.

This audit does not identify a high-risk blocker for v2.4 acceptance.

## Verification Date

2026-05-22

## Reviewed Areas

- `backend/app/platform/cross_mode.py`
- `backend/app/main.py`
- `backend/app/platform/project_packages.py`
- `backend/app/quality/project_gate.py`
- `backend/tests/test_v24_cross_mode_bridge.py`
- `docs/V2_4_ROADMAP.md`
- `docs/LLM_PROTOCOL.md`

## Passed Items

1. **Novel -> World does not create authoritative World facts**
   - `NovelToWorldPipeline` creates `CrossModeDraft` records with validation
     warnings.
   - It does not write content packs, `facts.yaml`, active saves, or
     `GameState`.

2. **World -> Novel does not modify EventLog / GameState**
   - `WorldToNovelPipeline.preview()` stores draft metadata and returns safe
     summaries.
   - Tests verify hidden/debug events and raw `state_delta` text are excluded
     from chapter draft previews.

3. **Tavern -> World does not let LLM decide proposal apply**
   - Tavern-to-World apply is represented by `CrossModeApplyPlan`.
   - `apply_confirmed()` requires `explicit_confirm=True`.
   - No LLM call is made in the apply flow.

4. **Tavern -> Novel does not import hidden/debug memory by default**
   - `TavernToNovelPipeline.preview()` accepts caller-provided safe messages.
   - The bridge artifact redaction layer removes hidden/debug/state-delta-like
     fields from normal summaries.

5. **Novel -> Tavern does not expose private notes in safe draft**
   - `NovelCharacterToTavernPipeline` currently uses structured ids and mode
     metadata only.
   - It does not read or serialize `private_notes_authoring_only`.

6. **CrossModeLink does not apply facts**
   - Existing `CrossModeLink` remains reference metadata.
   - Link review and validation can report broken/hidden-risk links, but links
     do not mutate content or state.

7. **CrossModeApplyPlan requires confirmation**
   - `CrossModeApplyPlan.requires_confirmation` defaults to `true`.
   - Cross-mode validation reports a blocker if an apply plan disables
     confirmation.

8. **World apply uses StateDelta/EventLog when runtime state is supplied**
   - `TavernToWorldApplyService.apply_confirmed()` applies supplied deltas via
     `apply_delta()`.
   - It appends a `cross_mode_apply` `Event` containing the applied deltas.

9. **Prompt/Profile permission boundaries remain intact**
   - Existing `ProjectPromptProfile` rejects `can_access_hidden_facts` and
     `can_modify_state`.
   - v2.4 does not add prompt-profile authority fields.

10. **Provider Gateway remains the model boundary**
    - v2.4 cross-mode code does not instantiate concrete model providers.
    - Existing Novel/Tavern generation paths use injected `LLMProvider` or
      provider factory boundaries.

11. **No direct provider instantiation in v2.4 bridge code**
    - `cross_mode.py` contains no provider factory or vendor provider calls.

12. **Cross-mode draft/proposal summaries filter hidden/debug/state-delta-like data**
    - `_redact_obj()` removes keys and values containing hidden/debug/secret/API
      key/state-delta markers from normal summaries.
    - `CrossModeBaseModel` rejects secret-like text during schema validation.

13. **raw state_deltas are not normal prompt material**
    - v2.4 bridge currently has no LLM prompt builder.
    - `WorldToNovelPipeline` tests cover raw state-delta exclusion.

14. **Memory is not treated as authoritative fact**
    - v2.4 bridge does not promote Project/Tavern memory into World facts.
    - Tavern-to-World remains proposal/apply-plan based.

15. **Schema failures fail closed with clear errors**
    - Unsafe ids, provider secret strings, missing confirmation, and invalid
      repository paths raise `ValueError` or validation errors.

16. **Tests do not call real APIs**
    - v2.4 tests use local schemas, TestClient, temp project roots, and no real
      provider calls.

17. **Cross-mode quality/evals do not use external LLM judge**
    - Project Quality Gate cross-mode integration calls deterministic
      validation, conflict detection, and link review.

## Risk Items

### Medium Risk

1. **World apply API endpoint currently records audit unless runtime state is provided by service caller**
   - The HTTP `apply-confirmed` endpoint calls `apply_confirmed()` without an
     active `GameState`, `EventLog`, or `StateDelta` bundle.
   - Result: the endpoint does not mutate World state, which is safe, but it
     also means full runtime apply orchestration is not complete from the API.
   - This is not an LLM authority risk; it is an acceptance/feature-completeness
     risk for future apply workflows.

2. **CrossModeValidation is conservative but shallow for prompt/provider scans**
   - It catches secret-like artifacts and apply-plan blockers.
   - It does not yet deeply parse every possible future prompt/provider profile
     artifact under `cross_mode/`.
   - Existing shared-library schemas still provide the primary prompt/provider
     permission guard.

3. **Tavern -> Novel relies on caller-provided safe messages**
   - The pipeline itself does not fetch and filter Tavern messages.
   - Tests cover safe input and raw state-delta exclusion elsewhere, but future
     richer implementation should wire this to Tavern safe summaries directly.

### Low Risk

1. **CrossModeLink validation depends on known-ref discovery**
   - World refs with accepted prefixes are allowed without deep world-content
     existence checks.
   - This is acceptable for draft/proposal review but should be tightened before
     any broad apply workflow.

2. **Audit records are not a replacement for EventLog**
   - Confirmed World runtime apply still needs EventLog.
   - Current implementation records both only when runtime state/event log are
     passed to the service.

## High-Risk Issues

None found.

## Medium-Risk Issues

- API-level confirmed apply is currently a safe audit-only path unless supplied
  with runtime state/deltas by service-level callers.
- CrossModeValidation should become more semantic before large-scale apply
  workflows.

## Small Issues

- v2.4 LLM boundary is not yet documented in `docs/LLM_PROTOCOL.md`.
- Cross-mode pipelines are intentionally minimal; several conversions are
  structured-preview scaffolds rather than full semantic extraction.

## Fix Recommendations

1. Before enabling a user-facing World apply button, route the API through an
   active World session/save adapter that supplies validated `StateDelta`
   objects and `EventLog`.
2. Extend CrossModeValidation to load prompt/provider profile artifacts
   explicitly if cross-mode packages begin storing them.
3. Wire Tavern -> Novel preview to repository-backed safe Tavern message
   summaries rather than accepting only caller-provided safe text.
4. Add a v2.4 section to `docs/LLM_PROTOCOL.md` during v2.4 documentation sync.

## Acceptance Impact

Not blocking v2.4 acceptance.

The identified risks are scoped, non-LLM-authority issues. Current v2.4 code
does not let LLM output directly modify `GameState`, decide apply, bypass
visibility, create authoritative World facts, or access provider secrets.
