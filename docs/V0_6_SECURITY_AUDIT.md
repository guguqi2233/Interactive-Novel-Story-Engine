# v0.6 Security and Local Packaging Audit

## Audit Date

2026-05-18

## Scope

本审计检查 v0.6 的本地安全、API gate、路径安全、敏感信息、debug/authoring 隔离、migration 安全、mod packaging、desktop prototype 和 playtesting 边界。

本项目仍定位为本地自用引擎，不是公网服务。审计结论按本地开发/本地工作室场景判断。

## Verification Commands

```powershell
git ls-files
git status --short
rg -n "sk-[A-Za-z0-9_-]+|LLM_API_KEY|OPENAI_API_KEY|api_key|llm_api_key|DATABASE_URL|\.env|node_modules|frontend/dist|dist/|Start-Process|authoring|debug|migration|state_deltas" . --glob "!frontend/node_modules/**" --glob "!node_modules/**" --glob "!frontend/dist/**"
Get-Content .gitignore
Get-Content backend/app/playtesting/agents.py
Get-Content backend/app/playtesting/runner.py
Get-Content backend/app/db/repository.py
Get-Content backend/app/engine/content/mod_loader.py
```

Latest full verification from the current v0.6 work session:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Result: `451 passed`; frontend build passed.

## 已通过项目

1. Authoring API 受 `ENABLE_AUTHORING_API` 控制。
   - All `/authoring/...` routes call `require_authoring_api()`.
   - Tests cover disabled authoring returning 403.

2. Debug API 受 `ENABLE_DEBUG_API` 控制。
   - Debug event, graph, and performance routes call `require_debug_api()`.
   - Tests cover debug disabled returning 403.

3. Performance debug API 受 debug 控制。
   - `/debug/performance/recent` and `/debug/performance/summary` call `require_debug_api()`.

4. Authoring API 禁止路径穿越。
   - `ContentAuthoringService._safe_world_path` restricts world ids to safe characters and resolves under `worlds_root`.
   - `_safe_file_path` rejects non-whitelisted names and requires `Path(file_name).name == file_name`.
   - Tests cover `../` traversal rejection.

5. Authoring API 只能读写白名单 YAML。
   - Allowed files are fixed in `ALLOWED_AUTHORING_FILES`.
   - Non-whitelisted files such as `.env` are rejected.

6. Authoring preview/dry-run 不写磁盘。
   - `preview_file_change`, `validate_draft`, and `analyze_file_impact` use draft validation/temp dirs or read-only comparison.
   - Tests verify preview leaves source YAML unchanged.

7. Migration API 不返回 raw hidden `GameState`.
   - Migration status/dry-run/apply responses return version/path/history/warnings only.
   - They do not include `state_json`, raw facts, raw memory, or raw events.

8. Migration apply has backup/failure safety.
   - `SQLiteSaveRepository.migrate_save` runs in a transaction.
   - Dry-run rolls back.
   - Apply creates a backup save when migrations are applied.
   - Failure rolls back and tests cover original save preservation.

9. Debug API does not return API key, env vars, or DB path by design.
   - Debug event API returns event fields and state deltas, not settings.
   - Debug performance API returns timing samples and sanitized tags.
   - Tests cover no API key in debug responses.

10. Player API does not return raw `state_deltas`.
    - Player game APIs return `visible_state`, narrative text, suggested actions, and turn/session metadata.
    - Boundary tests cover raw `state_deltas` not entering player payload/narrator.

11. Frontend does not store API keys.
    - Frontend uses `VITE_API_BASE_URL`.
    - No `VITE_LLM_API_KEY` pattern or frontend key storage was found.
    - Desktop script explicitly does not set `LLM_API_KEY`.

12. `.env`, DB, logs, caches, frontend build outputs, and dependencies are ignored.
    - `.gitignore` contains `.env`, `*.db`, `__pycache__/`, `.pytest_cache/`, `logs/`, `node_modules/`, `dist/`, `frontend/.env`, and `*.tsbuildinfo`.
    - `git ls-files` does not show `.env`, DB files, logs, caches, `node_modules`, `frontend/dist`, or desktop build outputs.

13. No real `sk-...` key found.
    - Secret scan did not identify a real OpenAI-style key.
    - Hits were config names, docs examples, and fake test keys such as `super-secret-test-key` / `test-key-not-used`.

14. Provider factory fails clearly on missing config.
    - `openai` without `LLM_API_KEY` raises `LLMProviderError`.
    - `local_http` without `LOCAL_LLM_BASE_URL` raises `LLMProviderError`.
    - Tests cover both failure paths without real API calls.

15. Tests do not call real APIs.
    - Tests use mock/fake/local_stub/playtest providers.
    - `LocalHTTPProvider` is a config-checked stub and does not call a local service.

16. Mod packaging does not execute arbitrary code.
    - Mod loader reads YAML manifests/content only.
    - Executable suffixes such as `.py`, `.js`, `.sh`, `.bat`, `.exe`, `.dll`, etc. are rejected in validation.

17. Mod loader prevents access outside mod directory.
    - `_safe_mod_relative_path` rejects absolute paths and `..`, resolves under mod root, and requires existing directories.
    - Tests cover path traversal rejection.

18. Desktop prototype does not package `.env` or API key into frontend.
    - v0.6 desktop slice is a launcher script, not a compiled installer.
    - `scripts/start_local_studio.ps1` sets local defaults but does not read/write `LLM_API_KEY`.
    - Docs warn not to pass API keys into `VITE_` variables or frontend bundles.

19. Playtesting agents cannot directly modify `GameState`.
    - Agents receive `VisibleStateResponse` and return input text.
    - Runner sends inputs through `GameLoop.step`.
    - Invariants inspect state after the fact but ordinary agents do not mutate state directly.

20. Content validation tools do not intentionally output sensitive local config.
    - Validation reports focus on world/mod YAML references and issues.
    - No env vars, API keys, or database path outputs were found in validation code paths.

## 高风险问题

1. Player API may leak hidden relationship actor ids.
   - Source: `get_visible_relationships` currently filters only `relationship.known_by_player`.
   - Impact: if a relationship involving a hidden NPC is marked `known_by_player=true`, `visible_state.relationships` can expose hidden NPC ids even when `visible_npcs` and player graph filter them.
   - Security relevance: this is a player API hidden-information leak, not only a UI issue.
   - Status: also identified in `docs/V0_6_VISIBILITY_MEMORY_DEBUG_AUDIT.md`.
   - Blocking: yes, this should block v0.6 release until fixed or proven impossible by schema/rules/tests.

## 中风险问题

1. Debug API exposes raw `state_deltas` by design.
   - This is expected for local debug timeline.
   - Risk is accidental mixing into player UI or narrative.
   - Current mitigations: route gated by `ENABLE_DEBUG_API`, frontend debug panel separation, boundary tests for player API/narrator.

2. Authoring API can read hidden world content by design.
   - This is expected for local authoring.
   - It must stay disabled by default and isolated from player UI.
   - Current default: `ENABLE_AUTHORING_API=false`.

3. Mod manifest invalid errors can include local manifest paths.
   - `_read_manifest` raises errors including the `Path` object.
   - Local-only authoring reduces impact, but API/CLI output should prefer relative paths to avoid leaking absolute local paths.

4. Desktop launcher writes logs under `logs/`.
   - Logs are ignored by git.
   - Current launcher avoids API key logging, but future backend logs should remain redacted.

5. `ENABLE_DEBUG_API` default is true in `Settings`.
   - This is acceptable for local development but unsafe for any public deployment.
   - Documentation states debug APIs are local-only.

## 小问题

1. Secret scan has noisy test/doc hits.
   - Examples: `super-secret-test-key`, `test-key-not-used`, `LLM_API_KEY` config names.
   - These are not real secrets.

2. `.gitignore` ignores `dist/`, which covers `frontend/dist`, but does not explicitly list desktop-specific build directories.
   - No desktop build outputs are currently present/tracked.
   - Future Tauri/Electron outputs should be added explicitly when introduced.

3. Performance tag sanitizer is blacklist-based.
   - Current tags are safe, but future instrumentation should avoid passing content/prompt text at call sites.

4. Desktop script defaults `DATABASE_URL=sqlite:///./world_engine.db`.
   - `*.db` is ignored, so this is not a git leak.
   - Future desktop packaging should move DB/logs into an OS app data directory.

## 修复建议

Blocking before v0.6 release:

1. Fix `visible_state.relationships` to filter hidden actors.
   - Filter relationship endpoints with the same player visibility rules used for NPCs.
   - Add tests for a `known_by_player=true` relationship pointing to a hidden NPC.

Recommended non-blocking hardening:

2. Normalize mod loader / authoring API errors to relative local paths.
3. Add explicit `.gitignore` entries for future desktop build output directories once selected, e.g. `src-tauri/target/`, `electron/dist/`, or `desktop/dist/`.
4. Keep debug/authoring APIs documented as local-only, and consider defaulting `ENABLE_DEBUG_API=false` if the project ever moves beyond personal local use.
5. Add a small check that frontend player components never render `DebugEvent.state_deltas`; keep that data in debug panel only.

## 是否阻塞 v0.6 release

Yes.

The security audit finds one release-blocking hidden-information issue:
`visible_state.relationships` can leak hidden NPC ids if a relationship is
marked player-known while an endpoint actor is hidden. This is a player API
leak and should be fixed before v0.6 release.

All other reviewed security/local-packaging areas are acceptable for a local-only
v0.6 release after that blocker is resolved.
