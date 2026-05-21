# v2.1 Security / Project Data Audit

Verification date: 2026-05-22

Scope: v2.1 Unified Narrative Project Layer, including Project API, ProjectRepository, workspace layout, import/export, migration, validation, quality gate, Project Shell frontend, and repo hygiene.

Verification evidence:
- `python -m pytest`: 1585 passed
- `cd frontend && npm.cmd run build`: passed, with existing Vite chunk-size warning
- Read-only review of `backend/app/platform/*`, `backend/app/quality/project_gate.py`, project endpoints in `backend/app/main.py`, desktop/config redaction paths, frontend project shell, and v2.1 tests
- `git ls-files` tracked artifact scan
- Secret-pattern scan for `sk-...`, private key markers, and `api_key` assignments

## Passed Items

1. Project API is controlled by local authoring/studio configuration.
   - Project endpoints under `/projects` call `require_authoring_api()`.
   - Project quality gate endpoint calls `require_quality_api()`.
   - Project API returns safe summaries, status, validation reports, or visible-state projections; it does not return raw env or raw GameState.

2. ProjectRepository rejects path traversal.
   - Project roots are resolved through `resolve_safe_project_root(..., base_root=repository.root)`.
   - Workspace path validation rejects absolute paths, `..`, `.env`, and forbidden local artifact directories.
   - Repository list responses use redacted paths (`.../<project-dir>`).

3. Project import/export rejects zip slip and unsafe paths.
   - Archive validation calls `validate_relative_package_path()` for every zip entry.
   - Import apply resolves targets under the output directory and rejects path escapes.
   - Tests cover zip slip rejection.

4. Project export excludes `.env`, API keys, databases, logs, cache, node_modules, and dist-like artifacts.
   - Export path validation rejects forbidden filenames, executable suffixes, database/log/cache-like suffixes, `node_modules`, `frontend/dist`, backups, and crash reports.
   - Export skips text files containing secret-like text.
   - v2.1 tests verify `.env` and fake API key content are absent from exported archives.

5. Provider profiles do not contain raw API keys.
   - `ProjectProviderProfile` rejects raw `api_key`, `llm_api_key`, and `openai_api_key`.
   - `api_key_env` is allowed as a reference to a local environment variable name only.
   - Validation allows `api_key_env` while still rejecting raw secret-like text.

6. Project migration does not migrate secrets.
   - Migration skips `.env`, node_modules, dist, logs, cache, backups, crash reports, executable/scripts, databases, and files containing secret-like text.
   - v2.1 tests verify `.env` is not migrated and source directories are not modified.

7. Project validation does not print secrets.
   - Normal validation reports use `normal_copy()` and `redact_text()`.
   - Secret-like text produces a generic `secret_like_text` error.
   - Hidden/debug markers produce generic warning messages rather than payload text.

8. Project Quality Gate does not leak hidden text in normal output.
   - It consumes normal project validation output.
   - `ProjectQualityGateResult.model_dump_normal()` redacts blockers, errors, and warnings.
   - Current v2.1 blockers use generic codes/messages.

9. Frontend does not store API keys.
   - Frontend API types expose `api_key_configured` / `contains_api_key` booleans where needed, not raw keys.
   - Project Shell includes a visible note that it shows no API keys, hidden facts, or raw env.
   - No v2.1 frontend project shell code writes or stores provider secrets.

10. Settings/config summaries avoid raw env.
    - Existing config/desktop summaries report provider type and `api_key_configured` booleans.
    - Raw env handling is restricted to redacted diagnostics/security code.

11. Player API does not return raw `state_deltas`.
    - Project World endpoints return `visible_state` only.
    - Debug/timeline views can expose state delta details in gated debug/authoring contexts, but Project World player state responses do not.

12. Debug API remains controlled by `ENABLE_DEBUG_API`.
    - Existing debug endpoints call `require_debug_api()`.
    - Desktop health/config surfaces report whether debug API is enabled, not raw debug data.

13. Authoring API remains controlled by `ENABLE_AUTHORING_API`.
    - Existing authoring endpoints call `require_authoring_api()`.
    - v2.1 Project API follows the same authoring gate.

14. `.env` is not tracked by git.
    - `git ls-files` did not list a root `.env`.
    - Tracked env examples are `.env.example` / `frontend/.env.example`, which are acceptable placeholder files.

15. Databases, logs, cache, frontend dist, and desktop build outputs are not tracked.
    - `git ls-files` did not show `.db`, `.sqlite`, `.sqlite3`, logs, cache directories, `node_modules`, `frontend/dist`, backups, crash reports, or desktop build outputs.

16. No clear real `sk-...` key was found.
    - Secret scan found fake/test placeholders such as `sk-test-*`, `sk-real-looking-*`, `sk-live-secret1234567890`, and placeholder API key field names in tests/docs.
    - These are used by redaction/security tests and docs; no production raw API key was identified.

17. Fake test keys are intentionally not real leaks.
    - Existing redaction tests use obvious fake markers such as `sk-test`, `test-secret-placeholder`, and `sk-real-looking-*`.
    - Security scanners and release checks should continue treating these as test fixtures, not production credentials.

18. Tests do not call real APIs.
    - v2.1 tests configure `llm_provider="mock"` or instantiate local schemas/services only.
    - No v2.1 test invokes OpenAI or external network providers.

## High-Risk Issues

None found.

No evidence was found that v2.1 exposes raw API keys, tracks local secrets/artifacts, permits path traversal, accepts zip slip, migrates secrets, prints hidden text in normal reports, or calls real APIs in tests.

## Medium-Risk Issues

None blocking.

The main design consideration is that Project export is a local portability/export mechanism. It filters secrets and forbidden files, but it is not a public sanitized publishing profile for every hidden world-design datum. Public sharing should use a future explicit redacted export profile.

## Minor Issues

1. Secret scans report many fake key strings in tests and historic audit docs. These are expected, but release reviewers should continue distinguishing them from real keys.
2. Frontend contains debug/authoring UI code that can render state delta details in debug-oriented panels. This is outside Project World player-state responses and should remain gated by backend debug/authoring APIs.
3. `api_key_env` is intentionally exported as a variable name reference. It must never be replaced with a raw key in project files.

## Recommendations

1. Add a future `project_public_export` profile with explicit hidden-fact redaction before treating NarrativeProject packages as public share artifacts.
2. Keep release checklist scans for `.env`, database/log/cache/build outputs, `node_modules`, backups, crash reports, raw `sk-...` keys, and private key blocks.
3. Keep v2.1 and later tests pinned to `mock` / `local_stub` providers.
4. Add focused future tests for Project API disabled behavior once project settings become user-configurable in the frontend.
5. Continue treating `api_key_env` as the only allowed provider secret reference in project files.

## v2.1 Release Impact

Blocking status: not blocked.

The v2.1 security and project-data boundary is acceptable for release. Project APIs are local-authoring gated, repository/import/export/migration paths reject unsafe files and traversal, provider profiles do not store raw keys, normal validation/quality reports are redacted, git does not track local secrets/artifacts, and tests use mock/local behavior rather than real external APIs.
