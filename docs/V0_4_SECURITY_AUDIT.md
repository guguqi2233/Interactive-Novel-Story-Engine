# v0.4 Security / Debug API Audit

## Audit Date

2026-05-17

## Scope

This audit focuses on v0.4 security, local debug API exposure, secret handling, player API boundaries, frontend debug separation, LLM provider safety, memory visibility, and content validation output.

Reviewed areas:

- Backend API schemas and route handlers.
- Debug timeline endpoints.
- Player-facing game endpoints and `visible_state`.
- LLM provider factory and OpenAI provider key handling.
- Memory retrieval visibility filters.
- Frontend API client and debug panel rendering.
- `.env.example`, README, and v0.4 audit / acceptance documentation.
- Git-tracked file categories relevant to secrets, databases, logs, caches, build artifacts, and dependencies.

Business code was not changed as part of this audit.

## Verification Commands

Commands run in this audit:

```powershell
rg -n "ENABLE_DEBUG_API|require_debug_api|debug_api_enabled|/debug|state_deltas|llm_api_key|database_url|LLM_API_KEY" backend\app backend\tests frontend\src docs\V0_4_ACCEPTANCE_REPORT.md docs\V0_4_LLM_BOUNDARY_AUDIT.md docs\V0_4_VISIBILITY_AUDIT.md README.md .env.example
```

```powershell
rg -n "sk-[A-Za-z0-9_-]{20,}" . --glob '!frontend/package-lock.json'
```

```powershell
rg -n "LLM_API_KEY|OPENAI_API_KEY|api_key|apikey|api-key" . --glob '!frontend/package-lock.json'
```

Previously reviewed in the v0.4 freeze checks:

```powershell
git ls-files | rg -n "(^|/)(\.env$|\.env\.|node_modules/|frontend/dist/|dist/|logs?/|__pycache__/|\.pytest_cache/)|\.db$|\.sqlite$|\.log$|\.pyc$"
```

```powershell
git ls-files frontend/dist node_modules .pytest_cache logs data world_engine.db *.db *.log
```

```powershell
git ls-files --others --exclude-standard | rg -n "(\.env$|\.db$|\.sqlite$|\.log$|\.pyc$|node_modules|frontend/dist|__pycache__|\.pytest_cache|logs)"
```

Full regression commands were not run again in this audit:

```powershell
python -m pytest
cd frontend && npm.cmd run build
```

Latest v0.4 freeze verification reported `257 passed` for backend tests and a successful frontend build.

## Checked Areas

1. Debug API gating by `ENABLE_DEBUG_API`.
2. Debug API response contents.
3. Local-only debug API documentation.
4. Player API exclusion of raw `state_deltas`.
5. Player API exclusion of hidden facts, NPC secrets, hidden witnesses, and debug memory.
6. Frontend API key handling.
7. Git tracking of `.env`, databases, logs, caches, `node_modules`, and `frontend/dist`.
8. Repository scan for real `sk-...` API keys.
9. Distinction between fake test keys and real secret leaks.
10. Provider factory behavior when `LLM_PROVIDER=openai` is missing an API key.
11. Test isolation from real OpenAI calls.
12. Frontend debug panel separation from player narrative UI.
13. Advanced memory retrieval filtering for hidden and debug-only records.
14. Content validation output and local configuration exposure.

## Passed Items

- Debug timeline endpoints are gated by `ENABLE_DEBUG_API` through `require_debug_api`.
- Debug endpoints return event timeline fields, including `state_deltas`, but do not return API keys, environment variables, database URLs, database paths, provider settings, or raw process configuration.
- README documents the debug API as a local development feature and warns that raw `state_deltas` may contain hidden or system-level information.
- Player-facing response schemas do not expose raw `state_deltas`.
- Player-facing `visible_state` is intended to include only filtered player-visible data. The v0.4 visibility audit found no blocking leakage path for hidden facts, NPC secrets, hidden witnesses, or debug memory after the blocker fixes.
- Frontend code does not store or display API keys. It uses `VITE_API_BASE_URL` for backend API routing.
- Debug timeline data is rendered inside the debug panel, not in the main player narrative area.
- `.env` is not tracked by git in the reviewed state.
- Databases, logs, cache files, `node_modules`, and `frontend/dist` were not found as tracked files in the reviewed freeze checks.
- No real `sk-...` key pattern was found in the repository scan.
- Test-only values such as `super-secret-test-key` and `test-key-not-used` are fake keys used to assert non-leak behavior and are not real provider credentials.
- Provider factory / OpenAI provider behavior is covered by tests: `LLM_PROVIDER=openai` without an API key fails clearly instead of silently falling back or attempting an unauthenticated call.
- LLM boundary documentation and tests indicate that rule modules do not call real APIs, and test providers remain mock/fake.
- Advanced memory retrieval includes narrator-safe filtering; hidden and debug-only memory records are excluded from narrator-safe context.
- Current Narrator flow does not consume raw debug timeline data.
- Content validation tooling reports content-pack validation errors and warnings; it does not output API keys, environment variables, or database configuration.

## High Risk Issues

None found.

No high-risk security blocker was identified in this audit.

## Medium Risk Issues

1. `ENABLE_DEBUG_API=true` appears in local example configuration.

   This is acceptable for a local-only engine, but it would be risky if the backend were exposed outside a trusted local machine. Debug endpoints can reveal hidden world state through event `state_deltas`.

   Blocking: no, because the project is explicitly local-only and README documents the boundary.

2. The frontend debug panel can display raw event deltas when debug API is enabled.

   This is expected for local development, but playtesters should not treat the debug panel as player-facing narrative UI.

   Blocking: no.

3. Player-visible faction data currently includes a raw numeric reputation value where the UI mainly needs a reputation band.

   This is not a credential or API-key issue, but it is a visibility-hardening concern. If the design goal is to avoid exposing exact social scores, the player API should eventually return only the band unless explicit visibility allows the raw value.

   Blocking: no for v0.4 security, but recommended for v0.5 hardening.

4. `ActionResult.reason` can be passed toward narration.

   Existing rule implementations should keep this player-safe. Future rule authors could accidentally include hidden rule details if this convention is not enforced.

   Blocking: no, but future hardening should split internal debug reason from player-safe reason.

5. Memory records rely on correct visibility classification.

   Hidden and debug-only memory is filtered from narrator-safe retrieval, but future callers must not store hidden summaries as `narrator_safe` by mistake.

   Blocking: no, because current retrieval filters are present and Narrator does not consume hidden/debug memory.

## Low Risk Issues

- README and `.env.example` include placeholder key text such as `your-local-key`; these are examples, not real credentials.
- Test files intentionally contain fake key strings to verify that debug APIs do not leak settings.
- PowerShell profile warnings seen during command execution are unrelated to project security.
- `.env.example` and `frontend/.env.example` are intentionally tracked and should remain tracked.
- The content validator may emit world content warnings, but no sensitive local configuration was observed in its expected output.

## Non-blocking Notes

- This audit did not rerun full backend tests or frontend build. The latest v0.4 freeze verification reported backend tests passing and frontend build succeeding.
- Before this audit, `docs/V0_4_SECURITY_AUDIT.md` was the missing document in the v0.4 freeze checklist. This file closes that documentation gap.
- Debug API should remain bound to local development workflows. Do not expose it on an untrusted network.
- If the project is ever distributed beyond local self-use, the default debug stance should be revisited and likely changed to disabled-by-default.

## Required Fixes Before v0.4 Tag

No blocking security fixes are required before the v0.4 tag based on this audit.

Recommended non-blocking hardening after v0.4:

1. Return only reputation bands in player APIs unless raw values are explicitly player-known.
2. Split `ActionResult.reason` into player-safe and debug/internal fields.
3. Add tests asserting debug timeline content never appears in narrator prompts.
4. Add tests for memory visibility classification at the point where memories are converted into narrator context.
5. Consider setting `ENABLE_DEBUG_API=false` in non-local example profiles if such profiles are added later.

## Final Security Verdict

v0.4 security audit passed.

No high-risk blocker was found. The debug API is appropriate for local development as currently documented, and sensitive provider configuration was not observed in debug responses, player responses, tracked files, or frontend code.

Recommendation: continue the v0.4 freeze process after rerunning the final freeze check, because this audit document was the previously missing security artifact.
