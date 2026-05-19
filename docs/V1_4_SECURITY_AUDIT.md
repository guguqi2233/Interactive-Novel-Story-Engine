# v1.4 Security / Import / Batch Processing Audit

## Verification Date

2026-05-20

## Scope

This audit reviews the v1.4 Content Production Pipeline security boundary, with emphasis on authoring/production API gating, batch import safety, zip/package handling, generator isolation, batch validation, local library behavior, CLI redaction, frontend key handling, player API visibility, tracked sensitive files, provider factory failures, and test isolation.

v1.4 remains a local-only engine/studio workflow. Production tools generate drafts, candidates, reports, and packages; they do not directly modify active `GameState`, execute package code, or bypass validation gates.

## Review Commands

- `rg -n "ENABLE_AUTHORING_API|enable_authoring_api|production/|/production|library|Depends|authoring" backend/app/main.py backend/app/api.py frontend/src`
- `rg -n "ZipFile|zipfile|extract|extractall|path traversal|zip slip|\.\.|is_absolute|resolve|EXECUTABLE|\.exe|\.bat|\.cmd|\.ps1|\.sh" backend/app/engine/content backend/app/tools backend/tests`
- `rg -n "LLM_API_KEY|api_key|API key|\.env|DATABASE_URL|sqlite|\.db|\.log|secret|sk-" backend/app/engine/content backend/app/tools backend/tests frontend/src README.md docs`
- `rg -n "localStorage|sessionStorage|api_key|llm_api_key|LLM_API_KEY|sk-|password|token" frontend/src`
- `git ls-files | rg "(^|/)(\.env$|.*\.db$|.*\.sqlite$|.*\.sqlite3$|.*\.log$|node_modules/|frontend/dist/|dist/|build/|cache/|__pycache__/|\.pytest_cache/)"`
- `rg -n "sk-[A-Za-z0-9_-]{20,}|BEGIN PRIVATE KEY|api_key\s*[:=]|LLM_API_KEY\s*=" -S .`

## 已通过项目

1. Authoring / production API gating

   v1.4 production, library, wizard, generator, batch import, batch validation, script package, campaign starter, batch quality gate, and pipeline summary endpoints are guarded by `require_authoring_api()` and therefore controlled by `ENABLE_AUTHORING_API`. The inspected routes include `/production/*`, `/authoring/production/*`, and `/library/*`.

2. Batch import path traversal protection

   Batch character card import and batch lorebook classification validate local paths and zip members before parsing. Unsafe absolute paths, `..`, home-relative paths, and executable file suffixes are rejected.

3. Zip slip protection

   Zip package import paths are normalized and validated before extraction. Absolute paths, parent traversal, and backslash traversal are rejected. Batch character/lorebook zip imports use safe zip member checks.

4. Package import executable rejection

   Package import rejects executable suffixes such as `.exe`, `.bat`, `.cmd`, `.ps1`, `.sh`, `.js`, `.py`, `.dll`, `.so`, and similar script/binary entries. Import/export package validation also rejects `.env`, database, sqlite, SQL, log, and known secrets files.

5. Generators avoid `.env` / API key reads

   World Pack Wizard, NPC Pack Generator, Quest Pack Generator, faction/mystery/template generators, Script Package Builder, and Campaign Starter Kit use schema inputs, world/package roots, and deterministic service logic. They reject suspicious references such as `.env`, `api_key`, and `sk-` in user-controlled text where applicable. No generator path was found that intentionally reads `.env`, raw API keys, databases, or system files.

6. Batch validators reject root escape

   Content batch validation resolves package paths under the configured package root and rejects path traversal. It does not access arbitrary files outside the allowed root.

7. Script Package Builder excludes sensitive files

   Script package building rejects `.env`, API key/secrets markers, database files, SQL/sqlite files, logs, and executable/script files. It generates checksums and keeps normal manifests free of hidden fact text.

8. Campaign Starter Builder does not execute scripts

   Campaign starter generation composes deterministic drafts and package drafts through existing services. It does not execute templates, package scripts, shell commands, or external code.

9. Local Content Library path safety

   Local Content Library Pro uses safe ids and library-relative display labels instead of exposing absolute sensitive local paths in normal UI/API responses. Path traversal ids are rejected.

10. CLI output redaction

   The production CLI reuses service-layer logic, requires explicit apply/build flags for write operations, omits large archive payloads from output, and redacts suspicious keys and values including API-key-like strings, hidden fields, and private summaries.

11. Frontend API key handling

   No frontend storage of API keys via `localStorage` or `sessionStorage` was found. The UI only displays configured/not-configured status and redacts suspicious values in diagnostic views.

12. Player API visibility boundary

   Player-facing API responses are built from `build_visible_state` and do not return raw `state_deltas`, hidden facts, NPC secrets, hidden witness details, debug memory, hidden relationships, intent queues, plan debug data, or production debug data.

13. Sensitive/generated files not tracked

   No tracked `.env`, database, sqlite, log, cache, `node_modules`, `frontend/dist`, desktop build output, or similar generated/sensitive artifact was found by `git ls-files`.

14. API key scan

   No real API key was identified. `sk-...` matches are test fixtures or explicit fake placeholders used to verify redaction and secret rejection behavior.

15. Fake test keys are intentional

   Test keys such as `sk-test-fake-not-real` and local fake secret strings are confined to tests/docs and are used to verify detection logic. They should not be treated as real credential leaks.

16. Provider factory failures are clear

   `create_llm_provider` remains the central provider selection path. Tests cover clear failures for missing `LLM_API_KEY` with `openai`, missing `LOCAL_LLM_BASE_URL` with `local_http`, and unknown provider names.

17. Tests avoid real API calls

   v1.4 tests use deterministic local behavior, temp roots, fake/mock provider settings, and fixture data. No path was found that requires calling real OpenAI or external APIs.

18. Batch fixtures avoid real user data

   v1.4 batch fixtures use temporary directories, sample worlds/packages, fake credentials, and synthetic content. No real user data fixture was found.

## 高风险问题

No high-risk security, import, or batch-processing release blocker was found.

## 中风险问题

1. Script package validation in the generic batch validator is less strict than the dedicated builder/import path.

   `ContentBatchValidator` rejects executable entries for raw script package directories, but its script-package branch does not fully duplicate all sensitive-file checks from `ScriptPackageBuilder` and the import/export package validator, such as `.env`, database, SQL/sqlite, log, or API-key marker checks inside arbitrary raw directories. The official build/export/import paths do reject these files, so this is not currently a release blocker, but the batch validator should be hardened to reuse the same sensitive-file policy for consistency.

## 小问题

1. CLI redaction is pattern-based.

   The CLI redacts common sensitive markers and hidden/private fields, but it is still a defensive string/pattern pass rather than a formally typed redaction schema for every possible service output. Current outputs are safe for inspected v1.4 commands.

2. Fake `sk-` fixtures can trigger simple scanners.

   Test fixtures intentionally include fake `sk-` strings to validate secret detection and redaction. Future release checks should continue distinguishing these from real credentials.

3. Production endpoints rely on local authoring mode.

   v1.4 production APIs are correctly gated by `ENABLE_AUTHORING_API`, but they should remain documented and deployed as local-only studio features.

4. PowerShell profile warning during commands is unrelated.

   Some command output may show a local PowerShell profile warning. This is environment noise and not a repository security issue.

## 修复建议

1. Before v1.4 final release, consider hardening `ContentBatchValidator` script package validation so it directly reuses or mirrors `ScriptPackageBuilder` / package import sensitive-file checks for `.env`, database, SQL/sqlite, log, API-key marker, and secret-bearing files.

2. Keep fake-key fixtures clearly named and scoped to tests so future scanners can distinguish them from credential leaks.

3. Maintain a single shared forbidden-file policy for import/export, batch validation, local library import, script package build, and CLI package validation.

4. Keep production and library APIs disabled by default outside local studio workflows, and retain `ENABLE_AUTHORING_API` as the required gate.

5. Continue running full secret scans and tracked-artifact checks before tagging v1.4.

## 是否阻塞 v1.4 release

Not blocking.

The audit found no high-risk release blocker. v1.4 security, import, and batch-processing boundaries are broadly consistent with the Content Production Boundary: production tools operate on drafts/packages, package import/export rejects unsafe files and traversal, production APIs are authoring-gated, player APIs remain visibility-filtered, tests use fake/local providers, and no tracked sensitive artifact or real API key was found.

The only medium-risk item is consistency hardening for script package validation inside the generic batch validator. Because the official script package builder and package import/export paths already reject sensitive files and executables, this is recommended hardening rather than a blocker.
