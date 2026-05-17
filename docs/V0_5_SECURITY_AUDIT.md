# v0.5 Security and Local Data Audit

## Audit Date

2026-05-17

## Scope

This audit reviews local security boundaries for v0.5:

- Authoring API gating, file whitelist, and path traversal protections.
- Debug API gating and sensitive configuration exposure.
- Player API filtering for raw deltas and hidden data.
- Frontend API-key handling.
- Git tracking of local secrets, databases, logs, caches, build output, and dependencies.
- API key scan for real `sk-...` style secrets.
- Provider factory failure behavior.
- Mod packaging safety.
- Content validation output and local configuration exposure.

## Verification Commands

- `git ls-files`
- `git ls-files .env *.db logs __pycache__ .pytest_cache node_modules frontend/dist frontend/.env`
- `rg "sk-[A-Za-z0-9_-]+|LLM_API_KEY|OPENAI_API_KEY|api_key|llm_api_key|DATABASE_URL|database_url" -n .`
- `Get-Content .gitignore`
- `Get-Content backend/app/main.py`
- `Get-Content backend/app/engine/content/authoring_service.py`
- `Get-Content backend/app/engine/content/mod_loader.py`
- `Get-Content backend/app/tools/validate_world.py`
- `Get-Content backend/app/llm/openai_provider.py`
- `Get-Content frontend/src/api.ts`
- Reviewed relevant tests:
  - `backend/tests/test_authoring_api.py`
  - `backend/tests/test_debug_api.py`
  - `backend/tests/test_mod_loader.py`
  - `backend/tests/test_llm_provider.py`

Full tests were not rerun during this audit document creation. The immediately preceding v0.5 integration task reported `python -m pytest` as `357 passed` and frontend build as passed.

## Passed Items

1. Authoring API is gated by `ENABLE_AUTHORING_API`.

   `require_authoring_api()` checks `authoring_api_enabled()` before authoring routes. Tests cover disabled behavior returning `403` with `Authoring API is disabled`.

2. Debug API is gated by `ENABLE_DEBUG_API`.

   `require_debug_api()` checks `debug_api_enabled()` before debug event routes. Tests cover disabled behavior returning `403` with `Debug API is disabled`.

3. Authoring API blocks path traversal.

   `ContentAuthoringService._safe_world_path` validates `world_id` with `_is_safe_id` and checks resolved paths stay under `worlds_root`.

   `_safe_file_path` requires `Path(file_name).name == file_name`, validates the filename against the allowlist, and checks the resolved parent remains the world pack directory.

4. Authoring API can only read/write whitelisted YAML files.

   `ALLOWED_AUTHORING_FILES` includes only:

   - `manifest.yaml`
   - `locations.yaml`
   - `npcs.yaml`
   - `items.yaml`
   - `quests.yaml`
   - `facts.yaml`
   - `factions.yaml`
   - `rumors.yaml`
   - `relationships.yaml`

   Non-whitelisted file reads such as `.env` are rejected by tests.

5. Authoring API does not read `.env`, databases, logs, source files, or system files.

   Access is limited by world id validation, filename whitelist, and resolved path checks. Source files and system paths are not on the allowlist.

6. Authoring writes parse YAML before save and validate after save.

   `write_file` parses YAML first. After writing, it runs world validation and rolls back invalid content. This protects active content packs from invalid writes and does not touch active sessions.

7. Debug API does not return API key or settings.

   Debug event responses include event fields only: turn, event id, actor, action type, result, state deltas, visibility flag, and created time. Tests assert a fake API key and `llm_api_key` are not present.

8. Player API does not return raw `state_deltas`.

   Player routes return `visible_state`, narrative text, suggested actions, turn, session id, save ids, and save summaries. Raw deltas are only in debug routes.

9. Player API does not return hidden facts, NPC secrets, hidden witnesses, or debug memory.

   `build_visible_state` filters facts by `player_visible_facts`, objects/NPCs by visibility/discovery, crimes by known/reported state, relationships by `known_by_player`, and does not serialize witnesses, secrets, debug memory, or raw state.

10. Frontend does not store API keys.

   `frontend/src/api.ts` only reads `VITE_API_BASE_URL`. It does not read, store, or send `LLM_API_KEY` or provider credentials.

11. Sensitive local files are not tracked.

   `git ls-files .env *.db logs __pycache__ .pytest_cache node_modules frontend/dist frontend/.env` returned no tracked files.

12. `.gitignore` covers expected local artifacts.

   `.gitignore` includes:

   - `.env`
   - `*.db`
   - `__pycache__/`
   - `.pytest_cache/`
   - `logs/`
   - `node_modules/`
   - `dist/`
   - `frontend/.env`
   - `*.tsbuildinfo`

13. No real `sk-...` API key was found.

   The secret scan found configuration names, docs placeholders, and fake test keys such as `super-secret-test-key` and `test-key-not-used`. No real `sk-...` key was found.

14. Test fake keys are identifiable as non-real.

   Test strings are human-readable fake values and do not match real OpenAI key patterns.

15. OpenAI provider fails clearly without API key.

   `OpenAIProvider.__init__` raises `LLMProviderError("LLM_API_KEY is required for OpenAIProvider")` when configured without a key. Provider factory tests cover this path.

16. Tests do not call the real API.

   Tests use `FakeLLMProvider`, `MockLLMProvider`, or instantiate OpenAI provider configuration paths without network calls. No test invokes `OpenAIProvider.generate_text` or `generate_json` against a live service.

17. Mod packaging does not execute arbitrary code.

   `ModLoader` only reads YAML manifests and validates content directories. It has no dynamic import, subprocess execution, or script execution path.

18. Mod loader rejects executable-code-like content.

   It flags suffixes including `.py`, `.js`, `.ts`, `.sh`, `.bat`, `.cmd`, `.ps1`, `.exe`, and `.dll`.

19. Mod loader prevents access outside the mod directory for content paths.

   `_safe_mod_relative_path` rejects absolute paths and `..`, resolves the path, and checks it remains under the mod root.

20. Content validation CLI does not output environment or database configuration.

   `backend/app/tools/validate_world.py` accepts a world id and `--worlds-root`, then prints structured validation reports. It does not read or print app settings, API keys, environment variables, or database paths.

## High Risk Issues

None found.

No reviewed player-facing endpoint returns API keys, raw environment values, raw local database paths, hidden/debug memory, hidden witness records, or raw state deltas.

## Medium Risk Issues

1. Invalid mod manifest errors can expose local filesystem paths.

   `ModLoader._read_manifest` raises:

   ```text
   Invalid mod manifest {path}: {exc}
   ```

   If this exception is surfaced by `/authoring/mods`, the response can include a local absolute path under the configured mods root. This is authoring-only and locally gated, but it is still local data disclosure.

   Blocking status: not automatically blocking for a local-only tool, but recommended to fix before v0.5 freeze if the security bar treats local paths as sensitive.

2. `ModValidationReport` can include relative file paths for forbidden code.

   The current implementation uses `path.relative_to(root)` for executable-code findings, which is good because it avoids absolute paths. The risk is low-to-medium only if future changes switch to absolute paths.

   Blocking status: not blocking.

## Low Risk Issues

1. Debug API intentionally returns raw `state_deltas`.

   This is expected for local debug timeline use and is gated by `ENABLE_DEBUG_API`. It must remain separate from player APIs and narrator prompts.

2. Authoring API intentionally exposes hidden content pack YAML.

   This is expected for local authoring. It is gated by `ENABLE_AUTHORING_API` and separate from player APIs. It should not be enabled for any shared or hosted environment.

3. Authoring API uses the configured `worlds_root`.

   If a user deliberately points `worlds_root` at a sensitive directory containing matching safe ids and whitelisted YAML names, the service will operate there. This is a local configuration responsibility, not a path traversal bug.

4. `README.md` contains placeholder API key instructions.

   The scan found `LLM_API_KEY="your-local-key"` in docs, which is safe placeholder content.

5. `DATABASE_URL` appears in docs and settings.

   These are configuration names and default local paths, not secret values.

## Fix Recommendations

1. Sanitize mod manifest exception messages.

   Change API-facing errors from absolute/local path strings to safe labels such as:

   ```text
   Invalid mod manifest mod.yaml: ...
   ```

   Keep full paths only in local logs if needed, and avoid returning them from authoring endpoints.

2. Add a regression test for mod API path sanitization.

   Create an invalid manifest under a temp mods root and assert the response does not include the temp directory path.

3. Keep authoring and debug disabled by default in non-local environments.

   Current defaults are local-friendly. Any future hosted mode should default both APIs off and require explicit local-only enablement.

4. Keep fake keys obviously fake.

   Continue using values like `test-key-not-used` and avoid realistic `sk-...` fixtures.

5. Preserve frontend credential boundary.

   The frontend should continue to read only `VITE_API_BASE_URL` and never accept/store provider API keys.

6. Keep debug data out of player responses and narrator input.

   Debug timeline data should remain confined to `/debug/*` routes and the debug panel.

## Blocking Assessment

No high-risk blocker was found.

v0.5 release is not blocked by this audit if local path disclosure in mod manifest errors is accepted as a non-hosted, authoring-only risk. Recommended pre-freeze hardening: sanitize invalid mod manifest error messages and add a regression test.

## Final Security Verdict

v0.5 security / local data audit passed with one medium non-blocking local data disclosure risk.

The project maintains the expected local-only boundaries: authoring and debug APIs are gated, player APIs remain filtered, raw state deltas are debug-only, frontend code does not handle API keys, sensitive runtime artifacts are not tracked, no real API keys were found, and mod packages are content-only with no arbitrary code execution.
