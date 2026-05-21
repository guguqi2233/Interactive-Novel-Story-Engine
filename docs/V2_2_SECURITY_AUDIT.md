# v2.2 Security / Export Audit

Verification date: 2026-05-22

Scope: v2.2 Novel Studio MVP security, Novel API gating, Novel repository path safety, Novel export filtering, provider/prompt profile secrecy, frontend secret handling, player/debug/authoring API boundaries, tracked artifact scan, and real API key scan.

This audit reviews implementation and test evidence only. It does not modify business code.

## 已通过项目

1. Novel API is controlled by local authoring/studio configuration.
   - Novel manuscript, chapter, scene, outline, arc, plot-thread, foreshadowing, consistency, and export endpoints call the local authoring gate.
   - Novel quality endpoints use the quality API gate.
   - These routes are not designed as public/player APIs.

2. `NovelRepository` rejects path traversal.
   - Novel file paths are rooted under the project `novel/` section.
   - Storage helpers use safe identifiers and relative package path validation.
   - Tests cover traversal rejection and repository confinement.

3. Novel export does not include `.env`, API keys, or provider secrets.
   - `NovelExportService` renders manuscript/chapter/scene content only.
   - It does not render provider profiles, local env, settings, or project secrets.
   - Rendered output is checked with secret detection before writing.

4. Novel export does not include debug memory or raw `state_deltas`.
   - Export rendering does not consume debug memory or EventLog delta payloads.
   - Export rejects output containing `state_delta` markers.

5. Novel export does not include authoring private notes by default.
   - `authoring_notes` are not part of normal Markdown/TXT rendering.
   - Consistency checks flag authoring notes if they appear inside export candidate text.

6. Project export still filters sensitive project content.
   - Project package export retains v2.1 filtering for `.env`, secrets, logs, caches, databases, node modules, build outputs, and unsafe package paths.
   - Novel exports are regular project files, but project package validation still rejects secret-like text in included text files.

7. Provider profiles do not contain real API keys.
   - Project provider profile schema rejects raw `api_key`.
   - `api_key_env` references are allowed, but secret-like env values are rejected.
   - Safe export returns metadata/env-var references, not credential values.

8. Prompt profiles do not contain secrets or unsafe authority.
   - Project prompt profiles reject hidden-fact/state-modification permissions.
   - Prompt profile tests verify invalid permissions fail.

9. Draft generation tests do not call real APIs.
   - Novel draft generation uses injected fake/mock/local provider behavior in tests.
   - No v2.2 test path requires OpenAI or external network access.

10. Frontend does not store API keys.
    - The frontend API layer uses backend endpoints and does not read local `.env` files.
    - UI text displays safe configuration status, not raw key values.

11. Settings/config summaries do not return raw env.
    - Existing desktop/studio config summaries expose boolean/safe status only.
    - Tests assert `LLM_API_KEY` and raw secret values are not serialized in normal config responses.

12. Player API does not return raw `state_deltas`.
    - Existing player state responses use visible-state projections.
    - Raw deltas remain debug/authoring information and are covered by hidden leak tests.

13. Debug API remains controlled by `ENABLE_DEBUG_API`.
    - Debug endpoints use explicit debug gating.
    - Tests cover disabled debug API behavior and raw delta isolation.

14. Authoring API remains controlled by `ENABLE_AUTHORING_API`.
    - Authoring endpoints, including Novel routes, are gated and fail clearly when disabled.

15. `.env` is not tracked.
    - `git ls-files` scan found no tracked `.env` file.
    - `.env.example` is tracked and contains placeholders/empty values only.

16. Local artifacts are not tracked.
    - `git ls-files` scan found no tracked database files, logs, caches, `frontend/dist`, `node_modules`, desktop build outputs, backups, or crash reports.

17. No real `sk-...` API key was identified.
    - Secret scan found documentation variable names and obvious test/redaction fixtures.
    - No production credential value was identified in source, tracked config, frontend code, docs, or scripts.

18. Fake test keys are used as redaction fixtures, not real leaks.
    - Examples such as `sk-test-*`, `sk-real-looking-*`, and `sk-live-secret1234567890` appear in tests/docs as explicit fake values for redaction and safety checks.
    - Tests assert these values do not appear in generated reports, UI payloads, exports, or safe summaries.

19. Tests do not call real external APIs by default.
    - Provider tests use mock/fake/local_stub patterns.
    - Real provider behavior remains opt-in through local configuration and is not part of default pytest.

## 高风险问题

None found.

No reviewed v2.2 security/export path exposes real API keys, raw env, `.env`, provider secrets, debug memory, raw state deltas, authoring private notes, or local artifact files through Novel API, Novel export, project export, frontend UI, or player API.

## 中风险问题

1. Project package export can include generated Novel export files if the user includes the Novel export section.
   - Current mitigation: project package export rejects forbidden files and secret-like text in text files.
   - Residual risk: manually authored chapter text that contains non-pattern secret material may not be semantically detectable.
   - Status: Non-blocking.

2. Novel authoring API returns authoring-domain objects to Studio clients.
   - Current mitigation: API is local/studio-authoring gated and separate from player API.
   - Residual risk: future public/player routes must not reuse raw authoring models.
   - Status: Non-blocking.

3. Markdown/TXT export only covers v2.2 supported formats.
   - Current mitigation: supported export formats share the same renderer and safety checks.
   - Residual risk: future DOCX/EPUB/PDF exports must repeat the same filtering.
   - Status: Non-blocking.

## 小问题

1. The repository contains many fake secret strings in tests and historical audit docs. They are useful redaction fixtures but make raw secret scans noisy.

2. Some frontend debug/authoring panels still display raw state-delta details in explicitly debug/authoring contexts. This remains acceptable only while those views stay non-player and gated.

3. This audit did not run a fresh browser visual inspection. It relies on source/test review and prior frontend build evidence.

## 修复建议

1. Keep Novel APIs behind local authoring/studio gating and avoid exposing raw Novel models through player or public routes.

2. Add future export preflight checks that compare manuscript/chapter/scene text against known project secret labels, hidden fact ids, NPC secret ids, and provider profile fields before packaging.

3. When adding future export formats such as DOCX, EPUB, or PDF, route them through the same redaction and secret-detection layer used by Markdown/TXT.

4. Keep fake secret fixtures clearly named as test-only values to reduce confusion during release scans.

5. Continue scanning generated frontend bundles and project packages for `LLM_API_KEY`, `OPENAI_API_KEY`, `sk-`, `raw env`, and `state_delta` before release.

## 是否阻塞 v2.2 release

Not blocking.

Verdict: PASS_WITH_WARNINGS.

The warnings are non-blocking release-hardening items. No high-risk v2.2 security/export blocker was found.
