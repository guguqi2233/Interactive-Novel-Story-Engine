# v0.8 Security / Import-Export Audit

## Audit Date

2026-05-18

## Scope

This audit reviews v0.8 security, local-only API gates, authoring safety, import/export package safety, desktop launcher safety, provider configuration errors, and sensitive-data handling.

Reviewed areas:

- Authoring API and visual editor save paths.
- Debug, performance, eval, playtest, timeline, and replay endpoints.
- Import/export and advanced package dry-run/apply.
- Scenario templates and local template browser.
- Mod manager / mod loader boundaries.
- Desktop shell scripts and packaging documentation.
- Frontend API use and config summaries.
- Player API visibility boundaries.
- Provider factory configuration failures.
- Git tracking of local secrets, databases, logs, caches, dependency folders, and build outputs.

## Verification Commands

Commands used during this audit pass:

```powershell
rg -n "ENABLE_AUTHORING_API|enable_authoring|ENABLE_DEBUG_API|enable_debug|ENABLE_EVAL_API|ENABLE_PLAYTEST_API|ENABLE_PERF|performance|authoring_required|debug_required|playtest|eval" backend/app frontend/src .env.example README.md docs/DESKTOP_PACKAGING.md
rg -n "\.env|sk-|api_key|LLM_API_KEY|OPENAI_API_KEY|secret|DATABASE_URL|frontend/dist|node_modules|desktop|dist" . -g "!frontend/node_modules/**" -g "!data/**" -g "!frontend/dist/**" -g "!.git/**"
git status --short
git ls-files | rg "(^|/)(\.env$|.*\.db$|.*\.sqlite$|.*\.sqlite3$|.*\.log$|node_modules/|frontend/dist/|dist/|build/|desktop-build/|target/)"
```

Focused files read during this audit:

- `backend/app/main.py`
- `backend/app/engine/content/authoring_service.py`
- `backend/app/engine/content/import_export.py`
- `backend/app/engine/content/world_branching.py`
- `backend/app/core/instrumentation.py`
- `backend/app/llm/provider_factory.py`
- `backend/app/llm/local_provider.py`
- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`

Latest full verification already run in this v0.8 work session:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Latest result in this session: `python -m pytest` passed with 596 tests, and frontend build passed.

## 已通过项目

1. **authoring API 受 `ENABLE_AUTHORING_API` 控制**
   - `authoring_api_enabled()` reads runtime settings.
   - `require_authoring_api()` returns `403` when disabled.
   - Authoring routes use the local authoring service and are intended as local-only studio tools.

2. **debug API 受 `ENABLE_DEBUG_API` 控制**
   - `require_debug_api()` gates debug timeline, replay, performance, graph/debug-style surfaces, and narrative eval endpoints.
   - Debug disabled paths return `403`.

3. **eval / playtest / perf API 受对应配置或 debug 控制**
   - Performance debug endpoints are under `/debug/performance/*` and call `require_debug_api()`.
   - Narrative eval endpoints are currently debug-gated.
   - Playtest endpoints call `require_playtest_api()`, which allows `ENABLE_PLAYTEST_API` or debug mode.
   - Scenario regression is gated by playtest, eval, or debug configuration.

4. **authoring API 禁止路径穿越**
   - `ContentAuthoringService._safe_world_path` and `_safe_file_path` validate ids, resolve paths, and require files to stay inside the world pack.
   - Authoring file access is restricted to whitelisted YAML files.

5. **visual editor save 必须经过 validation**
   - Map graph save converts to `locations.yaml` and calls `write_file`.
   - Multi-file and editor saves use `validate_drafts` / `validate_world` and rollback on failed validation.
   - Quest, NPC goal, economy, social graph, and rumor/crime saves go through authoring validation flows.

6. **import/export 禁止 zip slip**
   - `_validate_zip_member` rejects absolute paths, `..`, and backslash-containing archive paths.
   - Safe package extraction validates every member before `extractall`.

7. **import/export 拒绝可执行文件**
   - `_validate_file_name` rejects executable/code suffixes through `FORBIDDEN_CODE_SUFFIXES`.
   - It also rejects `.env`, secret files, DB files, SQLite files, and logs.

8. **template browser 不执行模板脚本**
   - Scenario templates are YAML-based.
   - Template renderer rejects executable files in the template directory and unsafe variable names/values.
   - Preview does not write disk; apply requires explicit validation/save.

9. **mod manager 不执行任意代码**
   - Mod/package flow remains content/YAML-only.
   - Mod loader validation rejects executable entry points and unsafe paths.

10. **desktop shell 不包含 `.env` / API key**
    - Desktop packaging remains a launcher prototype.
    - Documentation states `.env` and API keys must not be bundled.
    - Scripts do not set or print `LLM_API_KEY`.

11. **startup scripts 不硬编码 API key**
    - `scripts/start_local_studio.ps1` and `scripts/start_local_studio.sh` set safe local defaults for non-secret config.
    - They explicitly state `LLM_API_KEY` is not read or written by the launcher.

12. **frontend 不存储 API key**
    - Frontend API code uses `VITE_API_BASE_URL`.
    - No frontend path was found reading or storing provider API keys.

13. **settings / config summary 不返回 raw env**
    - Studio config summary reports safe booleans and status labels.
    - Tests assert fake key values, `DATABASE_URL`, and `LLM_API_KEY` are not returned.

14. **player API 不返回 raw `state_deltas`**
    - v0.8 integration tests assert `/game/state/{session_id}` does not include `state_deltas`.
    - Raw deltas are debug timeline data only.

15. **player API 不返回 hidden facts / NPC secrets / hidden witness / debug memory / hidden relationship**
    - Existing visibility tests and v0.8 regression tests cover these boundaries.
    - Player graph excludes hidden relationships.

16. **performance logging 不记录 prompt 全文 / API key / hidden facts**
    - `PerformanceRecorder` sanitizes tags containing `api_key`, `llm_api_key`, `secret`, `sk-`, `prompt`, `game_state`, and `state_delta`.
    - Performance samples are local/in-memory and debug-gated for API access.

17. **`.env` 未被 git 跟踪**
    - `git ls-files` did not return tracked `.env`.
    - `.env.example` is intentionally tracked.

18. **数据库、日志、缓存、`frontend/dist`、desktop build outputs 未被 git 跟踪**
    - `git ls-files` sensitive/build-output scan returned no tracked matches for the reviewed patterns.
    - `.gitignore` has been updated for local and desktop build artifacts in v0.8 work.

19. **未发现真实 `sk-...` key**
    - Repository scan found fake test placeholders such as `sk-test-fake` and `sk-real-looking-but-local`.
    - These are test fixtures used to assert non-leak behavior and are not real provider credentials.

20. **测试假 key 不应误判为真实泄露**
    - Test fake keys are clearly named fake/test/local placeholders.
    - Tests assert these fake values do not appear in API responses.

21. **provider factory 在 openai / local_http 缺配置时清晰失败**
    - `OpenAIProvider` raises a clear `LLM_API_KEY is required` error.
    - `LocalHTTPProvider` raises a clear `LOCAL_LLM_BASE_URL is required when LLM_PROVIDER=local_http` error.
    - Provider factory supports only known provider names and errors on unsupported values.

22. **测试不调用真实 API**
    - Playtesting and scenario regression use deterministic fake/playtest providers.
    - Local HTTP provider tests use fake transports and do not require real network services.

23. **scenario templates 不能执行脚本**
    - Template directories are scanned for forbidden executable suffixes.
    - Template rendering is string/YAML substitution plus validation, not script execution.

24. **quest graph editor 不能绕过 validation**
    - Quest graph preview/validate/save routes validate graph-to-YAML output.
    - Save is rejected when validation errors are present.

25. **advanced package import 检查 checksum**
    - `LocalPackageManifest.checksums` is validated by `_validate_package_checksums`.
    - Missing files, missing checksums, and checksum mismatches are rejected.

26. **branch/diff 不能访问 world root 之外文件**
    - Branch ids are validated.
    - Branch paths are resolved under `worlds/.branches/{world_id}`.
    - Branch creation copies only `ALLOWED_AUTHORING_FILES`, not `.env`, databases, logs, caches, or arbitrary files.

## 高风险问题

未发现高风险安全问题。

No reviewed v0.8 path was found that allows path traversal, zip slip, executable package import, arbitrary mod/template code execution, API key exposure, raw env exposure, player raw `state_deltas`, or visual editor saves that bypass validation.

## 中风险问题

1. **Narrative eval API is debug-gated rather than independently eval-gated**
   - Current behavior satisfies the stated "corresponding config or debug control" requirement because debug mode gates the endpoints.
   - For stricter local studio separation, future work could let `ENABLE_EVAL_API` independently gate eval endpoints without requiring broad debug access.
   - Blocking: no.

2. **Desktop startup scripts pass non-secret local model endpoint config into backend process**
   - Scripts pass `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, timeout, and JSON-mode flags to the backend process.
   - They do not pass or print `LLM_API_KEY`, but local endpoint URLs may still be considered environment-sensitive in some setups.
   - Blocking: no.

3. **Import/export save bundles include full runtime save data**
   - This is expected for local save bundle export/import.
   - It remains a local package flow, but UI should continue to show summaries only and avoid raw save JSON.
   - Blocking: no.

4. **Debug API default remains enabled in `.env.example` / settings defaults**
   - This is acceptable for a local self-use engine, but it increases risk if someone binds the backend beyond localhost.
   - Documentation warns that debug/authoring/perf APIs are local-only.
   - Blocking: no.

## 小问题

1. PowerShell emitted local profile-loading warnings during commands. This is unrelated to project code but makes audit output noisy.
2. Secret scans find many documentation and test placeholders. They are not real credentials, but release checks should continue using both pattern scans and human review.
3. Performance tag sanitization is denylist-based. It currently covers key risky terms; an allowlist would be stricter if more tags are added.
4. Branch/diff visibility risk messages can mention hidden fact ids or risk descriptions in authoring-only output. This is intended for local authoring and should not be shown in player UI.

## 修复建议

1. Consider adding separate `require_eval_api()` gating so narrative eval endpoints can be enabled without broad debug API.
2. Keep import/export tests covering:
   - zip slip,
   - executable files,
   - `.env` and secret files,
   - checksum mismatch,
   - database/log rejection.
3. Add a lightweight release-check script that runs:
   - tracked-file sensitive artifact scan,
   - `sk-...` scan,
   - frontend `VITE_` env scan for secret-like names,
   - desktop output scan if a local shell build is produced.
4. Move performance sample tags toward a positive allowlist if future instrumentation starts adding more dynamic values.
5. Keep player API tests asserting absence of `state_deltas`, raw `GameState`, hidden facts, NPC secrets, hidden witnesses, debug memory, and hidden relationships.
6. Keep branch and import/export outputs as authoring/local-only summaries; never render raw package/save contents in player surfaces.

## 是否阻塞 v0.8 release

不阻塞。

v0.8 security / import-export audit passed with non-blocking risks. The current implementation preserves the intended local safety boundary:

- Authoring APIs are gated and path-safe.
- Visual editor saves go through validation.
- Debug/performance/timeline data is debug-gated.
- Import/export rejects zip slip, executable files, `.env`, secret files, DB files, logs, and checksum mismatches.
- Desktop shell scripts do not hardcode or print API keys.
- Player APIs do not expose raw `state_deltas` or hidden/debug state.
