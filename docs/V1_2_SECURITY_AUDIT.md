# v1.2 Security, Import, and Package Audit

Date: 2026-05-19

Scope: v1.2 Visual Authoring Pro security posture, authoring/debug gates,
validation gate usage, import/export archive safety, package import, character
packs, template wizard, local content library, branch merge, draft history,
frontend key handling, player API redaction, provider factory failures, and
test provider behavior.

## Executive Summary

v1.2 is suitable for local release from a security/import/package perspective.
Authoring APIs are gated, debug APIs are gated, package import rejects traversal
and executable content, character packs reject secrets and scripts, local
library operations validate IDs and root boundaries, frontend code does not
persist API keys, player APIs omit raw state/debug/private data, and tests use
mock/local/fake providers.

No high-risk release blocker was found.

The main medium-risk item is that `ENABLE_DEBUG_API` defaults to true in local
settings. The endpoints are still controlled by the flag and are intended for a
local self-hosted engine, but release docs and startup profiles should continue
to make the local-only posture explicit.

## Audit Method

- Searched backend and frontend for authoring/debug gate usage, API-key
  handling, zip/package extraction, script execution markers, path traversal,
  raw `state_deltas`, and hidden/private data exposure.
- Checked git-tracked files for `.env`, databases, logs, caches, frontend
  `dist`, build outputs, and node modules.
- Searched for real-looking `sk-...` keys and reviewed matches.
- Reviewed `ImportExportService`, `CharacterPackBuilder`,
  `LocalContentLibraryService`, `TemplateWizard`, `WorldMergeService`, provider
  factory, OpenAI provider, and LocalHTTP provider.
- Reviewed existing tests covering zip slip, executable rejection, API-key
  redaction, provider failures, hidden data redaction, and fake/local providers.

## Passed Items

1. Authoring API is controlled by `ENABLE_AUTHORING_API`

   Passed. `/authoring/...` and `/library/...` routes call
   `require_authoring_api()`. `ENABLE_AUTHORING_API` defaults to false in
   settings, and tests cover disabled authoring returning 403.

2. Debug API is controlled by `ENABLE_DEBUG_API`

   Passed. Debug routes call `require_debug_api()`. Tests verify disabled debug
   API behavior and that debug responses do not include API keys.

3. Visual editor save goes through the validation gate

   Passed. `ContentAuthoringService.write_file`, `write_files`, and visual
   graph save paths use `AuthoringValidationGate`. v1.2 integration tests
   monkeypatch the gate and verify save/import apply paths call it.

4. Import/export forbids zip slip

   Passed. Archive extraction validates every member with `_validate_zip_member`
   before `extractall`, rejecting absolute paths, `..`, and backslashes. Tests
   cover zip slip rejection.

5. Character pack import/export does not include API keys

   Passed. Character pack validation scans for secret markers including
   `api_key`, `secret_key`, `private_key`, bearer tokens, `sk-`, and private key
   headers. Safe export excludes hidden facts by default and tests assert no API
   key or hidden fact text.

6. Template Wizard does not execute scripts

   Passed. Template Wizard uses deterministic in-process template generation,
   safe IDs, root path checks, validation, and explicit apply. No script
   execution path was found.

7. Local Content Library forbids path traversal

   Passed. Library IDs are restricted by `_safe_id`; duplicate/export/inspect
   paths use safe IDs and `_safe_child` root-resolution checks. Tests cover path
   traversal rejection.

8. Branch merge cannot access files outside world roots

   Passed. Merge preview resolves branches through `WorldBranchService` and
   authoring-safe world paths. It iterates allowed authoring files rather than
   arbitrary paths.

9. Draft History does not save raw env

   Passed. Draft history accepts only authoring-allowed file names and rejects
   API/env/config markers such as `api_key`, `llm_api_key`,
   `openai_api_key`, `database_url`, and test secret placeholders.

10. Frontend does not store API keys

    Passed. Frontend search found no `localStorage`, `sessionStorage`,
    `indexedDB`, or cookie usage for keys. The UI displays only
    `api_key_configured` boolean status and has a redaction helper for
    `sk-...` patterns.

11. Settings/config summary does not return raw env

    Passed. Studio config summary returns provider labels and
    `api_key_configured` boolean status, not raw `LLM_API_KEY` or raw env
    content. Tests assert fake keys and `llm_api_key` are not returned.

12. Player API does not return raw `state_deltas`

    Passed. Player state uses `VisibleStateResponse`, not raw `GameState` or
    event debug payloads. Multiple tests/evals assert `state_deltas` are absent
    from player APIs.

13. Player API does not return hidden facts, NPC secrets, hidden witnesses,
    debug memory, or hidden relationships

    Passed. Visible state is assembled through visibility-filtered rules and
    tested by hidden info leak evals, narrative boundary evals, and v1.2
    integration regression.

14. `.env` is not git-tracked

    Passed. `git ls-files` only showed `.env.example` and
    `frontend/.env.example`, which are safe templates.

15. Databases, logs, caches, frontend dist, and build outputs are not
    git-tracked

    Passed. The git-tracked artifact scan did not find tracked `.db`,
    `.sqlite`, `.log`, cache directories, `frontend/dist`, build outputs, or
    node modules.

16. No real `sk-...` key was found

    Passed. Matches were documentation warnings and test placeholders such as
    `sk-test-fake...` or `sk-real-looking-but-local` inside tests. No production
    real secret was identified.

17. Test fake keys are not treated as real leaks

    Passed. Fake keys are explicitly used in regression tests to assert
    redaction and rejection behavior. Existing release/security tests recognize
    these as fixtures.

18. Provider factory fails clearly when `openai` or `local_http` lacks config

    Passed. `OpenAIProvider` raises `LLMProviderError("LLM_API_KEY is required
    for OpenAIProvider")`. `LocalHTTPProvider` raises `LLMProviderError` when
    `LOCAL_LLM_BASE_URL` is missing. Tests cover both paths.

19. Tests do not call real APIs

    Passed. Tests use `mock`, `local_stub`, `FakeLLMProvider`, or fake
    LocalHTTP transports. The v1.2 integration test explicitly sets
    `llm_provider="local_stub"`.

20. Package import does not execute arbitrary code

    Passed. Package import extracts data archives only after path/file/checksum
    validation. Executable suffixes are rejected, mods are data-only, and
    template/scenario imports parse/validate content instead of executing code.

## High-Risk Issues

No high-risk issue was found.

## Medium-Risk Issues

1. `ENABLE_DEBUG_API` defaults to true

   Debug API is correctly controlled by `ENABLE_DEBUG_API`, but the default is
   true in local settings. This matches the local/self-hosted development
   posture, yet it increases risk if the backend is exposed beyond localhost.

   Impact: local debug exposure risk if deployed improperly.

   Recommendation: keep release/startup docs explicit that production-like or
   shared environments must set `ENABLE_DEBUG_API=false`; consider a separate
   release profile that defaults it to false.

2. Save archive export can contain full runtime state by design

   Save exports are local backup artifacts and may contain hidden runtime state
   and EventLog data. This is documented, but users should treat save archives
   as sensitive files.

   Impact: local package confidentiality risk if shared externally.

   Recommendation: label save exports as sensitive in UI/docs and avoid
   importing/exporting them through any future online channel.

## Low-Risk Issues

1. Local Content Library character pack export format is separate from package
   import apply

   The library can export a `character_pack.json` zip for character packs, while
   general package apply expects local package manifests. This is not a security
   leak, but it can be confusing operationally.

   Recommendation: document that Character Pack Builder import/apply uses its
   own dry-run/apply flow, or wrap character-pack library exports with a local
   package manifest later.

2. Some older audit docs contain mojibake text

   This does not affect runtime security, but makes historical review harder.

   Recommendation: normalize encoding opportunistically when touching old docs.

## Fix Recommendations

1. Add a CI-style static test that asserts all `/authoring` and `/library`
   routes call `require_authoring_api()` and all `/debug` routes call
   `require_debug_api()`.

2. Add a static test that scans tracked files for forbidden local artifacts:
   `.env`, `.db`, `.sqlite`, `.log`, `frontend/dist`, caches, build outputs, and
   node modules, allowing only `.env.example`.

3. Add a static test that rejects real-looking `sk-...` values except allowlisted
   test placeholders.

4. Add a release profile or documented startup preset with
   `ENABLE_DEBUG_API=false` for safer packaged use.

5. Keep package imports data-only: no script hooks, no remote URLs, no automatic
   overwrite, no active `GameState` mutation.

## v1.2 Release Blocking Assessment

Not blocking v1.2 release.

The audit found no high-risk issue and no evidence of real API keys, tracked
secret files, executable package import, zip slip, frontend key storage, raw
player API state leakage, or real API usage in tests. The medium-risk items are
local-operational hardening tasks and should be tracked, but they do not block
v1.2 release for a local self-hosted engine.
