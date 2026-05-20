# v1.7 LLM Boundary Audit

## Scope

This audit reviews the v1.7 Polished Desktop Studio surface:

- desktop policy, local config, workspace/recent-project services, health checks, crash reports, update notes, startup diagnostics;
- launcher scripts;
- desktop packaging safety documentation and tests;
- v1.7 integration regression tests.

The review focuses on whether desktop management flows call LLM providers,
grant the LLM new authority, leak provider secrets, or bypass the world engine
boundary.

## 已通过项目

1. **v1.7 新增 desktop modules do not call LLM providers.**  
   `backend/app/desktop/*` contains no `LLMProvider`, provider factory,
   provider router, `generate_text`, `generate_json`, OpenAI client, or model
   invocation path. Provider-related fields are limited to safe summaries and
   config validation.

2. **Desktop Launcher does not call LLM.**  
   `scripts/start_local_studio.ps1` and `scripts/start_local_studio.sh` set
   safe local defaults such as `LLM_PROVIDER=mock`, start backend/frontend
   processes, check local HTTP readiness, and print safe warnings. They do not
   invoke any provider API or call model endpoints.

3. **Project Selector does not call LLM.**  
   Workspace selection/listing/counting only inspects local workspace structure
   and safe metadata. It does not parse content through an LLM and does not
   mutate active `GameState`.

4. **Local Config Manager does not call LLM.**  
   It reads `Settings`, returns safe summaries, checks missing provider config,
   and can generate an `.env.example`-style template. It does not validate a
   provider by calling it.

5. **Log Viewer / log policy does not call LLM.**  
   The implemented desktop policy redacts logs locally with regex-based
   handling. No LLM log analysis path was found.

6. **Error Recovery Wizard does not call LLM.**  
   No implemented v1.7 recovery service was found that invokes LLM. Roadmap
   language requires recovery steps to be deterministic and local.

7. **Backup / Restore boundary does not call LLM.**  
   Implemented policy checks backup/export candidates by local path and secret
   scanning rules. No LLM involvement was found.

8. **One-click Quality Gate does not call a real LLM in v1.7 desktop code.**  
   No v1.7 desktop-specific one-click quality endpoint with provider calls was
   found. Existing quality gate/eval infrastructure remains separate and uses
   mock/local deterministic test paths by default in tests.

9. **Offline Help / Update Notes do not call LLM or network.**  
   `LocalUpdateNotesService` reads local `docs/V*_RELEASE_NOTES.md` files and
   redacts key-like text locally. No network or provider call was found.

10. **Health Check does not call LLM.**  
    `DesktopHealthCheckService` checks backend/config/database/workspace state
    and provider config summaries. It explicitly does not call providers.

11. **Crash Report Viewer does not call LLM.**  
    `CrashReportService` records, lists, redacts, and deletes local reports.
    It does not send crash text to an LLM for analysis.

12. **No LLM output directly enters `GameState` through v1.7 desktop flows.**  
    Desktop services do not produce LLM output. Workspace selection, config,
    health, update notes, crash reports, startup diagnostics, and packaging
    safety checks do not call `apply_delta`, write `StateDelta`, or mutate game
    sessions.

13. **Provider factory remains the provider boundary for model calls.**  
    v1.7 desktop code does not instantiate concrete providers or bypass
    provider factory/router. It only inspects provider config strings from
    settings.

14. **Tests do not call real APIs.**  
    v1.7 tests use `Settings(llm_provider="mock")` or fake test keys. The one
    `openai` setting in integration tests is only used to exercise safe config
    redaction; no provider call is made.

15. **Desktop Studio cannot bypass core world-engine boundary in implemented paths.**  
    Implemented desktop services are local management/safe-summary flows. They
    do not write active saves, apply content, dispatch actions, or modify
    `GameState` directly.

## 风险项目

1. **Several v1.7 roadmap features are only partially implemented or represented by boundary/policy tests.**  
   Log Viewer, Error Recovery Wizard, Backup / Restore, One-click Quality Gate,
   One-click Export World Pack, and Offline Help Docs do not all have full
   production-grade service/API implementations in the current code. Their LLM
   boundary is safe because no LLM path exists, but acceptance should not
   overstate runtime completeness.

2. **Launcher can start backend configured with a real provider.**  
   The launcher itself does not call LLM, but it passes through local provider
   config and can start a backend whose normal gameplay/authoring flows may use
   `LLM_PROVIDER=openai` if the user configured it. This is expected behavior,
   but documentation should continue to distinguish “launcher startup” from
   “later user-initiated LLM gameplay flows.”

3. **Startup diagnostics reports provider config presence but does not validate provider reachability.**  
   This is correct for the no-real-LLM boundary, but users may mistake it for a
   provider health test. Documentation already frames diagnostics as local
   safety/readiness checks.

## 高风险问题

None found.

No v1.7 desktop module was found that calls a real LLM provider, lets LLM output
enter `GameState`, or bypasses provider factory/router.

## 中风险问题

None found that blocks v1.7 acceptance.

The main medium-risk area is scope clarity: some roadmap items remain boundary
or documentation-level in the current implementation. This is an acceptance
scope/documentation risk, not an LLM permission boundary failure.

## 小问题

1. **Launcher readiness checks use local HTTP calls.**  
   PowerShell `Invoke-WebRequest` and shell `urllib.request` are used for local
   `/health`, `/studio/status`, and frontend readiness. These are not LLM calls
   and are limited to configured local URLs, but audit notes should keep them
   separate from “no network” statements about LLM/provider access.

2. **Config summary includes provider type/model id.**  
   This is safe metadata, not a secret. It should remain a safe summary only and
   never include API keys or raw provider config.

3. **Fake test keys appear in tests.**  
   These are explicitly fake (`sk-test-...`) and are used to verify redaction.
   They should continue to be excluded from real-key leak findings.

## 修复建议

1. Keep v1.7 desktop management flows provider-free. If future recovery/log
   explanation features need “AI help,” make them opt-in, mock by default, and
   ensure they receive redacted summaries only.

2. Do not add provider health checks to startup diagnostics unless they are
   explicitly user-enabled and routed through the existing provider factory.

3. Keep launcher documentation precise: launcher startup does not call LLM, but
   normal backend gameplay may later call the configured provider when the user
   runs LLM-backed flows.

4. For any future One-click Quality Gate UI, ensure the default profile uses
   deterministic local checks and does not run real-provider evals.

5. Continue adding tests that assert desktop service responses do not include
   `LLM_API_KEY`, raw env, raw prompt, hidden facts, or provider secret values.

## 是否阻塞 v1.7 acceptance

**No.**

The v1.7 LLM boundary is acceptable for release: implemented desktop studio
flows do not call LLM providers, do not grant LLM world authority, do not write
LLM output to `GameState`, and do not bypass the existing provider boundary.
