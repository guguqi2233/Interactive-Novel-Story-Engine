# v2.1 LLM Boundary Audit

Verification date: 2026-05-22

Scope: v2.1 Unified Narrative Project Layer, including `NarrativeProject`, project workspace/repository/API, shared libraries, `CrossModeLink`, Mode Router, Novel/Tavern stubs, World Mode adapter, project import/export, project migration, project validation, project quality gate, and v2.1 integration regression tests.

Verification evidence:
- `python -m pytest`: 1585 passed
- `cd frontend && npm.cmd run build`: passed, with the existing Vite chunk-size warning
- Reviewed implementation under `backend/app/platform/`, `backend/app/quality/project_gate.py`, project endpoints in `backend/app/main.py`, and v2.1 tests in `backend/tests/test_v21_*.py`

## Passed Items

1. NarrativeProject does not expand LLM authority.
   - `NarrativeProject` is a local project metadata container, not a fact engine.
   - `ProjectSafetyPolicy.export_secrets` is fixed to `False`.
   - `ProjectSafetyPolicy.allow_external_providers` defaults to `False`.
   - `NarrativeProject.safe_summary()` returns project metadata and safety policy only; it does not expose raw env, provider secrets, hidden facts, or raw GameState.

2. Novel Mode stub does not write drafts into GameState.
   - `NovelOutlineDraft`, `ChapterDraft`, and `NovelModeProjectState` are Pydantic models only.
   - `ChapterDraft.safe_summary()` returns `[authoring draft]` for authoring-only content.
   - v2.1 regression tests assert Novel draft structures do not mutate `GameState`.

3. Tavern Mode stub does not write RP sessions into GameState.
   - `TavernSessionDraft` and `TavernMessageDraft` are draft/session records only.
   - `RPProposalDraft.creates_state_delta` and `creates_world_fact` are fixed to `False`.
   - v2.1 regression tests assert Tavern proposals remain proposals and do not become world facts.

4. World Mode remains governed by the World Engine.
   - Project World start uses `InMemorySessionStore`, existing world loading, `GameLoop`, `GameState`, visible-state projection, and the existing action pipeline.
   - Project endpoints return `visible_state`; they do not return raw GameState.
   - The integration test steps a project-launched world session and verifies an Event is recorded in `EventLog`.

5. CrossModeLink does not auto-convert hidden facts.
   - `CrossModeLink` stores references only.
   - `CrossModeLink.safe_summary()` returns `None` when `hidden=True`.
   - `CrossModeLinkRegistry.validate_link()` marks missing refs as `broken`; it does not transform or apply linked data.
   - Project validation now reports broken or invalid `cross_mode_links.json` entries.

6. PromptProfileLibrary blocks fact-authority expansion.
   - `ProjectPromptProfile` uses `Literal[False]` for `can_access_hidden_facts`, `can_modify_state`, `can_override_action_result`, and `can_bypass_visibility`.
   - Tests cover unsafe hidden-fact permission rejection.

7. ProviderProfileLibrary stays within Provider Gateway assumptions.
   - `ProjectProviderProfile` stores provider metadata and mode routing only.
   - It accepts `api_key_env` references but rejects raw `api_key`, `llm_api_key`, and `openai_api_key` fields.
   - v2.1 does not add a code path that instantiates concrete providers from project files.
   - Search found no concrete provider instantiation in `backend/app` outside provider-owned code.

8. Provider Profile does not contain real API keys.
   - Raw key fields are rejected by model validation.
   - Secret-like strings in provider profile values are rejected except for `api_key_env`, which is an environment variable reference.
   - Project validation treats `api_key_env` as an allowed reference while still rejecting raw secret-like text.

9. MemoryLibrary is not an authoritative fact source.
   - `ProjectMemoryRecord.authoritative` is fixed to `False`.
   - `ProjectMemoryLibrary.get_memory_context_for_mode()` filters by mode visibility.
   - Hidden/debug memory is excluded from narrator/world-safe context.

10. WorldBible hidden entries are not narrator-safe.
    - `WorldBibleEntry.is_safe_context` only allows `flavor` or `style_note` entries with `public` or `narrator_safe` visibility.
    - Hidden entries are excluded from `WorldBible.safe_summary()`.

11. Tavern safe context is filtered.
    - `LoreFactLibrary.get_tavern_safe_lore()` excludes hidden facts.
    - `ProjectMemoryLibrary` only returns `tavern_safe` and `player_visible` memory for Tavern mode.
    - This does not by itself prove NPC knowledge membership, but it prevents hidden library entries from being included by default.

12. Novel safe context is filtered.
    - `LoreFactLibrary.get_novel_safe_lore()` excludes hidden facts.
    - `TimelineEvent.safe_summary()` excludes hidden and authoring-only events.
    - Novel output remains draft data, not world fact data.

13. No v2.1 path lets LLM output directly enter GameState.
    - v2.1 additions are schema, repository, API, import/export, migration, validation, and quality gate code.
    - No new LLM call is introduced by `backend/app/platform/*`.
    - World gameplay still uses the existing GameLoop boundary.

14. Tests do not call real APIs.
    - v2.1 API tests configure `llm_provider="mock"`.
    - v2.1 tests instantiate schemas and local services only.
    - No v2.1 regression test invokes a real provider.

15. Schema validation failures produce clear errors or safe reports.
    - Pydantic rejects unsafe prompt/provider schemas.
    - Project API converts unsafe project create/update errors to HTTP 400 where applicable.
    - Project validation reports `project_manifest_invalid`, `secret_like_text`, `cross_mode_link_broken`, and `cross_mode_link_invalid_ref`.

## Risk Items

1. World Mode adapter inherits existing provider configuration.
   - The adapter itself does not call a real API, but it creates normal `InMemorySessionStore` sessions. If the runtime is configured with a real provider, the existing GameLoop may use that provider as designed.
   - This is acceptable for production configurability, but tests and release checks must keep `llm_provider=mock` or `local_stub`.

2. Tavern safe context is mode-safe, not full NPC-knowledge validation.
   - v2.1 shared libraries filter hidden content, but they do not yet cross-check every Tavern-safe fact against a specific NPC's `npc_knowledge`.
   - This is acceptable for a v2.1 stub, but should become a stricter v2.2/v2.3 check before full Tavern Studio.

3. Novel safe context relies on explicit library flags.
   - `safe_for_novel` and visibility filtering prevent hidden entries by default.
   - A future Novel Studio implementation must preserve this and avoid raw WorldBible/Fact dumps.

## High-Risk Issues

None found.

No evidence was found that v2.1 grants LLM authority to modify `GameState`, bypasses `StateDelta`/`EventLog`, exposes hidden facts by default, or adds real-provider calls to tests.

## Medium-Risk Issues

None blocking.

The World Mode adapter's dependency on the existing runtime provider config is a normal integration behavior, but release/testing profiles must keep mock/local providers by default.

## Minor Issues

1. The v2.1 shared library layer is intentionally schema-first. Some deeper semantic checks, such as Tavern NPC-specific knowledge validation for every safe context item, are still future work.
2. `api_key_env` appears in safe exports by design. It is an environment variable name, not a secret value. Reviewers should not treat this as key leakage unless a raw value appears.

## Recommendations

1. Add a v2.2/v2.3 Tavern-specific validator that checks Tavern-safe facts against character/NPC knowledge scopes before prompt assembly.
2. Add a future Novel context builder test that proves Novel safe context cannot include hidden world facts even when multiple libraries are merged.
3. Keep release checklists enforcing mock/local_stub provider defaults for automated tests.
4. Continue scanning project packages and exports for raw `api_key`, `sk-...`, raw env, hidden facts, raw prompts, and raw GameState payloads.

## v2.1 Acceptance Impact

Blocking status: not blocked.

The v2.1 LLM boundary is acceptable for release acceptance. The new NarrativeProject layer, shared libraries, stubs, router, and project tooling do not expand LLM authority. World Mode remains the only runtime fact engine, and project-level Novel/Tavern data remains draft/proposal metadata unless later validated through existing World Engine boundaries.
