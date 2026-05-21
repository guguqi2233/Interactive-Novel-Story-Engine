# v2.1 Visibility / Cross-Mode / Debug Data Audit

Verification date: 2026-05-22

Scope: v2.1 Unified Narrative Project Layer, including Project API, Project Shell, shared libraries, CrossModeLink, Mode Router, World Mode adapter, project import/export, project validation, project quality gate, and v2.1 integration tests.

Verification evidence:
- `python -m pytest`: 1585 passed
- `cd frontend && npm.cmd run build`: passed, with existing Vite chunk-size warning
- Reviewed `backend/app/platform/*`, `backend/app/quality/project_gate.py`, project endpoints in `backend/app/main.py`, and `backend/tests/test_v21_*.py`

## Passed Items

1. Hidden facts do not enter World Mode `visible_state`.
   - Project World endpoints return `build_visible_state(game_loop.state)`.
   - They do not return raw `GameState`.
   - v2.1 integration tests assert project world start payload contains `visible_state` and does not include `hidden_facts` or API key markers.

2. Hidden facts do not enter Novel normal context by default.
   - `LoreFactLibrary.get_novel_safe_lore()` excludes `fact_type="hidden"`.
   - `TimelineEvent.safe_summary()` returns `None` for hidden and authoring-only events.
   - `ChapterDraft.safe_summary()` hides authoring-only draft body behind `[authoring draft]`.
   - Novel stub remains project draft metadata and does not become world-visible context.

3. Hidden facts do not enter Tavern normal context by default.
   - `LoreFactLibrary.get_tavern_safe_lore()` excludes hidden entries.
   - `ProjectMemoryLibrary.get_memory_context_for_mode("tavern")` only includes `tavern_safe` and `player_visible` records.
   - `TavernMessageDraft.safe_summary()` only returns messages with `visibility="tavern_safe"`.

4. NPC secrets are not automatically inserted into Tavern sessions.
   - v2.1 Tavern Mode is a stub and has no prompt assembly that injects NPC secrets.
   - Tavern proposals remain `RPProposalDraft` with `creates_state_delta=False` and `creates_world_fact=False`.
   - Full NPC-knowledge-aware Tavern prompt validation is still future work and is listed under risk items.

5. WorldBible hidden entries are filtered.
   - `WorldBibleEntry.is_safe_context` only allows `flavor` or `style_note` entries with `public` or `narrator_safe` visibility.
   - `WorldBible.safe_summary()` omits hidden entries.
   - Tests assert hidden WorldBible text is absent from safe summary.

6. LoreFactLibrary hidden entries are filtered.
   - Novel and Tavern safe getters exclude hidden entries.
   - World import candidates only include `structured` or `draft` entries explicitly flagged for world import; they do not auto-import into GameState.

7. MemoryLibrary hidden/debug memory is filtered.
   - `ProjectMemoryRecord.safe_content()` redacts `debug_only` and `hidden` records.
   - Mode-based memory filtering excludes hidden/debug memory from Novel/Tavern/World normal contexts.
   - `authoritative` is fixed to `False`, so memory cannot become world fact by itself.

8. CrossModeLink does not expose hidden targets to normal view.
   - `CrossModeLink.safe_summary()` returns `None` when `hidden=True`.
   - Link registry validation marks missing refs as `broken`; it does not dereference or copy hidden targets.
   - Project validation reports broken/invalid cross-mode link files without printing target hidden content.

9. Timeline hidden / authoring-only events do not enter player context.
   - `TimelineEvent.safe_summary()` suppresses `visibility="hidden"` and `authoring_only=True`.
   - `TimelineLibrary.safe_timeline_summary()` only includes entries with non-null safe summaries.

10. Character private notes do not enter player/narrator summaries.
    - `CharacterProfile.safe_summary()` excludes `private_notes_authoring_only`.
    - Tests assert private note text is absent from character safe summaries.

11. Provider profiles do not leak API keys.
    - `ProjectProviderProfile` rejects raw `api_key`, `llm_api_key`, and `openai_api_key` fields.
    - `api_key_env` is allowed as an environment variable reference and is not a secret value.
    - Project validation treats `api_key_env` as an allowed reference while still rejecting raw secret-like content.

12. Project export normal flow does not contain secrets.
    - `export_project()` excludes forbidden paths through `validate_relative_package_path()`.
    - It skips text files containing secret-like values.
    - Import validation rejects secret-like text, checksum mismatches, forbidden paths, executable files, and zip slip.
    - v2.1 tests assert exported archives do not include `.env`, raw API key markers, or test secret values.

13. Project validation normal report does not print hidden text.
    - `validate_project(..., profile="normal")` returns `normal_copy()`.
    - Hidden/debug markers produce generic `hidden_leak_risk` warnings without including the hidden text itself.
    - Error/warning messages are passed through `redact_text()`.

14. Project Quality Gate normal result does not print hidden text.
    - `ProjectQualityGateResult.model_dump_normal()` redacts blockers/errors/warnings.
    - Project Quality Gate consumes the normal Project Validation report.
    - Current messages are generic and do not include hidden text payloads.

15. World Mode player API does not return raw `state_deltas`.
    - Project World endpoints return `visible_state` only.
    - Existing player-facing state APIs also use visible-state projection.
    - Debug/timeline code may expose deltas through debug-oriented paths, but not through Project World player state endpoints.

16. Debug data remains isolated from normal project APIs.
    - v2.1 project endpoints are authoring/studio endpoints and return safe summaries, status, validation reports, and visible-state projections.
    - They do not expose debug memory, raw env, raw GameState, raw prompts, or raw state delta objects.

17. Narrator does not receive raw state deltas from v2.1.
    - v2.1 does not add narrator prompt assembly.
    - Existing GameLoop narrator calls pass confirmed `ActionResult`, visible facts, current location, and optional scene mood; raw state deltas are not part of the v2.1 project context.

## Possible Leak Paths

1. Project export includes project content sections such as `world/content_pack`.
   - This is suitable for local project portability and trusted backup/import flows.
   - It filters secrets, executables, forbidden files, and unsafe paths, but it is not a public-player redaction profile for hidden world design content.
   - If v2.1 later adds public sharing/export profiles, they should add explicit hidden fact redaction.

2. Tavern Mode does not yet perform full NPC-knowledge validation.
   - Shared libraries prevent hidden entries from default Tavern-safe context.
   - A future full Tavern prompt builder must additionally verify each fact against the specific character/NPC knowledge scope.

3. Novel Mode safe context depends on explicit flags and safe summary methods.
   - Current stubs are safe, but a future Novel Studio context builder must preserve hidden/authoring-only filters when combining libraries.

4. Debug views are not implemented by v2.1 project endpoints.
   - This is safe for now, but future debug views should be explicitly gated and should not be confused with normal project status/quality reports.

## High-Risk Leaks

None found.

No evidence was found that hidden facts, NPC secrets, debug memory, raw state deltas, raw GameState, raw env, or provider secrets enter Project API normal responses, Project Shell normal UI, Novel/Tavern stubs, World Mode visible state, project validation normal reports, or project quality gate normal results.

## Medium-Risk Leaks

None blocking.

The main medium-risk design consideration is that project export is a local portability export, not a public redacted export. This should be documented and separated from any future public/player-facing export profile.

## Minor Issues

1. `api_key_env` appears in provider profile safe exports by design. It is an environment variable name, not a secret value.
2. Project validation warns on hidden/debug markers outside explicit world/quality context, but does not yet semantically classify every file format in Novel/Tavern libraries.
3. v2.1 has safe stubs for Novel/Tavern. Full context builders in future versions will need additional tests for multi-library merged contexts.

## Recommendations

1. Add a future `public_project_export` or `redacted_project_export` profile before exposing project packages as shareable public artifacts.
2. Add Tavern prompt/context tests that verify facts against per-character/NPC knowledge before full Tavern Studio work.
3. Add Novel context-builder tests that combine WorldBible, LoreFactLibrary, TimelineLibrary, and CharacterLibrary while proving hidden text is excluded.
4. Keep project validation/quality gate normal views generic and redacted; reserve raw object inspection for explicitly gated debug APIs.
5. Continue requiring project import/export validation for forbidden paths, executable files, secrets, zip slip, duplicate project ids, and checksum mismatches.

## v2.1 Acceptance Impact

Blocking status: not blocked.

The v2.1 visibility and cross-mode boundaries are acceptable for release acceptance. The current implementation keeps hidden facts, NPC secrets, private character notes, hidden/debug memory, authoring-only timeline events, raw state deltas, and provider secrets out of normal Project API, Project Shell, Novel/Tavern stubs, World Mode visible state, validation reports, and quality gate results.
