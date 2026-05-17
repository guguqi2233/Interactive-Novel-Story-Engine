# v0.7 Security / Packaging Audit

## Audit Date

2026-05-18

## Scope

This audit covers the v0.7 local studio security and packaging surface:

- Authoring, debug, eval, playtest, performance, import/export, mod, template, quest graph, settings, and player APIs.
- Local archive import/export and zip handling.
- Mod packaging/versioning safety.
- Desktop packaging prototype scripts and documentation.
- Frontend API-key handling and debug/player UI separation.
- Git tracking of local-only artifacts.
- Provider factory failure behavior and test isolation from real APIs.

This is a code and repository audit only. It does not modify business code.

## Verification Commands

Commands run during this audit:

```powershell
rg -n "require_authoring_api|require_debug_api|require_playtest_api|ENABLE_|debug/performance|evals/narrative|playtests|authoring" backend/app/main.py backend/app/config.py
rg -n "\.\.|resolve\(|extractall|ZipFile|FORBIDDEN_CODE_SUFFIXES|python_entrypoint|entrypoint|content_paths|validate_mod|path traversal|unsafe|executable" backend/app/engine/content backend/app/tools
git status --short
git ls-files | rg "(^|/)(\.env|.*\.db|.*\.sqlite|.*\.sqlite3|.*\.log|node_modules|frontend/dist|desktop-dist|desktop_build|release|\.pytest_cache|__pycache__)"
rg -n "sk-[A-Za-z0-9_-]{20,}" . --glob "!frontend/node_modules/**" --glob "!frontend/dist/**" --glob "!.git/**" --glob "!*.db" --glob "!*.sqlite" --glob "!*.sqlite3"
rg -n "API_KEY|LLM_API_KEY|OPENAI_API_KEY|LOCAL_LLM|localStorage|sessionStorage|document\.cookie|VITE_" frontend/src scripts docs/DESKTOP_PACKAGING.md .env.example README.md
rg -n "api_key|API_KEY|prompt|hidden|state_delta|GameState|raw env|database" backend/app/core/instrumentation.py backend/app/main.py backend/app/api.py backend/app/session_store.py backend/app/engine/rules/visibility.py
rg -n "OpenAIProvider\(|LocalHTTPProvider\(|LocalStubProvider\(|MockLLMProvider\(|FakeLLMProvider\(" backend/app --glob "!backend/app/llm/provider_factory.py" --glob "!backend/app/llm/openai_provider.py" --glob "!backend/app/llm/local_provider.py" --glob "!backend/app/llm/mock_provider.py" --glob "!backend/app/llm/fake_provider.py"
rg -n "OpenAI\(|openai|LLM_PROVIDER|local_http|requests|httpx|urllib|socket" backend/tests tests --glob "!**/__pycache__/**"
git check-ignore -v .env world_engine.db logs\desktop-backend.out.log frontend\dist\index.html desktop-dist\app.txt release\app.zip frontend\node_modules\pkg
```

Full test and frontend build were not rerun in this audit. The most recent v0.7 integration pass before this audit was `python -m pytest` with 500 passing tests and a successful frontend build.

## 已通过项目

1. **Authoring API gate**
   - All `/authoring/...` routes inspected in `backend/app/main.py` call `require_authoring_api()`.
   - `require_authoring_api()` is controlled by `ENABLE_AUTHORING_API`, defaulting to disabled in `backend/app/config.py`.

2. **Debug API gate**
   - Debug event, graph, and performance endpoints call `require_debug_api()`.
   - `require_debug_api()` is controlled by `ENABLE_DEBUG_API`.

3. **Eval / playtest / perf API gate**
   - Narrative eval endpoints are debug-gated.
   - Playtest endpoints call `require_playtest_api()`, which accepts either `ENABLE_PLAYTEST_API=true` or debug enabled.
   - Performance endpoints are debug-gated and only expose sanitized performance samples.

4. **Authoring path traversal protection**
   - `ContentAuthoringService` resolves world paths under the configured worlds root and requires file names to be in the authoring whitelist.
   - Direct `../` traversal and non-whitelisted file reads/writes are rejected.

5. **Import/export zip-slip protection**
   - `ImportExportService._validate_zip_member()` rejects absolute paths, `..` components, and backslash-containing archive member names before extraction.
   - `_extract_safe_archive()` validates every member before `extractall()`.

6. **Import/export executable rejection**
   - Import/export rejects `.py`, `.js`, shell/batch/PowerShell scripts, `.exe`, `.dll`, and related executable suffixes through `FORBIDDEN_CODE_SUFFIXES`.
   - `.env`, secret YAML/JSON files, local DB files, and logs are rejected in archives.

7. **Mod manager / mod loader code execution boundary**
   - `ModLoader` validates mods as local content/YAML packages only.
   - It rejects executable suffixes and validates `content_paths` stay inside the mod directory.
   - No Python/JS entrypoint execution path was found.

8. **Mod loader directory boundary**
   - Mod IDs are constrained to safe characters.
   - `content_paths` reject absolute paths and `..`, and resolved paths must remain under the mod root.

9. **Desktop packaging prototype does not embed secrets**
   - `scripts/start_local_studio.ps1` and `scripts/start_local_studio.sh` do not read, print, or inject `LLM_API_KEY` into the frontend.
   - The scripts only pass local operational config such as `LLM_PROVIDER`, feature flags, `DATABASE_URL`, and `VITE_API_BASE_URL`.
   - `docs/DESKTOP_PACKAGING.md` explicitly says not to package `.env` or API keys.

10. **Startup scripts do not hardcode API keys**
    - No hardcoded OpenAI/API key value was found in startup scripts.
    - The scripts print a notice that `LLM_API_KEY` is not read or written to logs by the launcher.

11. **Frontend does not store API keys**
    - Frontend API configuration uses only `VITE_API_BASE_URL`.
    - No `localStorage`, `sessionStorage`, cookie, or API-key persistence path was found in `frontend/src`.

12. **Settings/config summary is redacted**
    - `/studio/config-summary` returns safe booleans and labels, including `api_key_configured`, but not the key.
    - It returns a redacted database hint rather than raw env or full sensitive paths.

13. **Player API avoids raw state_deltas and hidden data**
    - Player-facing game routes return `visible_state`.
    - `build_visible_state()` uses visibility filters for hidden objects, hidden NPCs, known facts, visible relationships, and visible combat summaries.
    - Raw `state_deltas` appear in debug timeline responses, not player game responses.

14. **Performance logging sanitizes sensitive tags**
    - `backend/app/core/instrumentation.py` removes tags containing `api_key`, `llm_api_key`, `secret`, `sk-`, `prompt`, `game_state`, or `state_delta`.
    - Performance API does not expose prompt text, raw GameState, or raw hidden facts by design.

15. **Git ignore coverage for local artifacts**
    - `.gitignore` covers `.env`, `*.db`, `logs/`, `node_modules/`, `frontend/dist/`, `desktop-dist/`, `release/`, Tauri target output, and common desktop installers.
    - `git check-ignore` confirmed representative paths are ignored.

16. **Tracked artifact scan**
    - `git ls-files` matched only `.env.example` and `frontend/.env.example` for env-like files.
    - No tracked real `.env`, DB, log, cache, `node_modules`, `frontend/dist`, desktop output, or release archive was found by the checked pattern.

17. **Real key scan**
    - No `sk-...` style key matching the checked pattern was found.
    - Placeholder/test configuration strings remain distinguishable from real provider keys.

18. **Provider factory clear failure behavior**
    - Provider selection remains centralized in `provider_factory.py`.
    - `openai` and `local_http` configuration failures are covered by provider tests and raise clear `LLMProviderError` paths.

19. **Tests avoid real API calls**
    - Local HTTP provider tests use fake transports.
    - OpenAI provider tests instantiate provider/config behavior but do not perform real API calls.

20. **Scenario templates are data renderers, not script runners**
    - Templates are YAML-defined, variable-substitution based, and output only whitelisted authoring YAML files.
    - Variable names and path-like values are checked to prevent traversal.
    - Rendered content is parsed as YAML and validated before use.

21. **Quest graph editor validation boundary**
    - Quest graph preview converts graph data back to YAML and calls authoring draft validation.
    - The preview path writes no disk content and does not modify active GameState.

## 高风险问题

No high-risk security or packaging blocker was found in this audit.

## 中风险问题

1. **Save export returns complete save archive as base64 through an authoring endpoint**
   - `/authoring/export/saves/{save_id}` returns a base64 zip containing save JSON and events.
   - This is appropriate for local authoring/import-export, but it is a sensitive local-data transfer surface because save bundles can contain full hidden state and event history.
   - Current mitigation: endpoint is gated by `ENABLE_AUTHORING_API`, disabled by default, and documented as local-only.
   - Recommendation: keep this endpoint local-only, add prominent UI warnings when exporting save bundles, and avoid rendering `archive_base64` directly in user-facing UI beyond a download workflow.

2. **Debug API defaults to enabled for local development**
   - `ENABLE_DEBUG_API` defaults to true in `backend/app/config.py`.
   - This is acceptable for a local self-use engine, but it is risky if the backend is bound to a non-local interface.
   - Current mitigation: launcher defaults bind to `127.0.0.1`, docs frame debug as local-only.
   - Recommendation: before any packaged or shared LAN workflow, default debug to false or make the launcher explicitly confirm non-loopback debug use.

3. **Narrative eval API uses debug gate rather than a separate eval gate**
   - Config exposes `ENABLE_EVAL_API`, and `/studio/config-summary` reports eval availability as eval-or-debug, but narrative eval routes currently call `require_debug_api()`.
   - This satisfies the requirement that eval APIs be controlled by a corresponding config or debug control, but the separate `ENABLE_EVAL_API` is not currently an independent route gate.
   - Recommendation: future cleanup can add `require_eval_api()` for clearer operator expectations.

## 小问题

1. **PowerShell profile warning during shell commands**
   - PowerShell emitted a local profile execution-policy warning during audit commands.
   - The warning did not affect command results, but it adds noise to local security reports.
   - Recommendation: run audit/check commands with `-NoProfile` in scripts or CI-like local recipes.

2. **Authoring UI intentionally can display hidden content**
   - Authoring is a creator tool and may show full YAML, including hidden facts or secret text.
   - Current mitigation: authoring is gated, local-only, and visually separate from player UI.
   - Recommendation: preserve this separation and avoid reusing authoring components inside player-facing views.

3. **Debug timeline displays raw state_deltas**
   - This is expected for a debug tool and is currently gated by `ENABLE_DEBUG_API`.
   - Recommendation: keep all raw `state_deltas` rendering inside debug panels only.

## 修复建议

Before v0.7 tag, no mandatory security fix is required.

Recommended non-blocking hardening:

1. Add a dedicated `require_eval_api()` so `ENABLE_EVAL_API=true` can enable evals without enabling all debug endpoints.
2. Add explicit export warnings in the frontend for save bundles, since exported saves can include hidden state by design.
3. Consider making `ENABLE_DEBUG_API=false` the default in packaged desktop profiles while keeping it easy to enable for local development.
4. Add a no-profile note or wrapper for local audit commands to avoid PowerShell profile warning noise.

## 是否阻塞 v0.7 release

Not blocking.

Final security verdict: **v0.7 security / packaging audit passed for local self-use release**, with the medium-risk items above treated as local-only operational cautions rather than release blockers.
