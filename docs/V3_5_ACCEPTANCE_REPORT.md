# v3.5 Acceptance Report: Local QA / Debug / Replay & Provider Connectivity UI Pro

## Verdict

Accepted with documented limitations.

v3.5 Local QA / Debug / Replay & Provider Connectivity UI Pro is accepted as a
local inspection, diagnostics, replay, quality, and provider-configuration
release. The implementation provides the planned QA/debug/replay contract
review, Timeline Replay, EventLog Viewer, StateDelta Viewer, Visible vs Debug
State Compare, Hidden Leak Report, Playtest Dashboard, Unified Quality Gate,
Performance Dashboard, Provider Connectivity Dashboard, safe Provider
connection testing, model discovery/sync, model assignment, Provider secret
redaction, Provider Usage/Cost dashboard, CrossMode Conflict Review, Module
Playtest/Stress UI, Save Migration Visualizer, Diagnostics Bundle Review, Local
Test Run Dashboard, Safe Debug Export Wizard, shared QA/debug components, UI
regression checks, and v3.5 integration regression tests.

No high-risk v3.5 release blocker remains in the accepted scope. The earlier
Provider secret blocker around unsafe `secret_ref` persistence and validation
error reflection has been fixed with stricter `secret_ref` validation,
redacted provider safe summaries, sanitized validation error responses, and
focused regression tests.

## Verification Date

2026-05-24

## Verification Commands

```powershell
python -m pytest
```

Result: passed, `1768 passed in 137.27s`.

```powershell
cd frontend
npm.cmd run build
```

Result: passed. Vite produced a successful production build and emitted the
existing chunk-size warning for the main bundle.

Additional v3.5 regression check run during release-blocker remediation:

```powershell
cd frontend
npm.cmd run check:v35-qa-debug-provider-ui
```

Result: passed.

## Scope Accepted

Accepted v3.5 scope:

1. Local QA / Debug / Replay Contract Review.
   - `docs/V3_5_QA_DEBUG_REPLAY_PROVIDER_CONTRACT_REVIEW.md` exists and maps
     current QA/debug/replay/provider contracts, debug gating, secret handling,
     and recommended v3.5 shape.

2. Timeline Replay UI Pro.
   - Timeline Replay exposes session/save selection, turn/time/event timeline
     rows, filters, replay controls, visible replay summaries, and debug-gated
     raw details. Replay is read-only.

3. EventLog Viewer Pro.
   - EventLog Viewer shows event id, turn/time, event type, actor safe summary,
     source module, tags, visible safe summary, and linked StateDelta counts.
     Raw event JSON and raw StateDelta details remain debug-gated.

4. StateDelta Viewer Pro.
   - StateDelta Viewer is marked debug-sensitive and read-only. It is available
     only through debug-gated UI and does not expose an apply-delta path.

5. Visible vs Debug State Compare.
   - Visible/debug compare summarizes visible sections, debug/raw state summary
     sections, filtered field counts, and visibility warnings with redacted
     hidden summaries.

6. Hidden Leak Report UI Pro.
   - Hidden leak reports show overall status, categories, severity, source,
     target, safe summary, and suggested action without printing hidden text
     bodies.

7. Playtest Dashboard Pro.
   - Playtest UI shows suite/run summaries, pass/fail, duration, failed step,
     action/event coverage, hidden leak warnings, and safe replay summaries.

8. Quality Gate Unified Dashboard Pro.
   - Unified Quality Gate aggregates Project, World, Novel, Tavern,
     Cross-Mode, Provider, Mods, Modules, RP/Mature, and Backup/Diagnostics
     statuses with blockers, errors, warnings, last run time, and safe next
     actions.

9. Performance Dashboard Pro.
   - Performance dashboard shows local API/save/EventLog/replay/provider/
     quality/playtest/build timing and size summaries without prompt/output
     text, API keys, or hidden facts.

10. Provider Connectivity Dashboard.
    - Provider connectivity surfaces local provider list, provider type,
      connection status, model count, last tested time, allowed modes, default
      model, warnings, and local-only/no-resale boundary copy.

11. Provider Connection Test Backend.
    - `POST /projects/{project_id}/providers/test-connection` supports safe
      local connection testing through fake/mock/local provider paths in tests,
      returns `ProviderConnectionStatus`, and redacts errors.

12. Provider Model Discovery / Sync.
    - Model discovery and sync support fake OpenAI-compatible/custom responses,
      unsupported model-list status, manual model metadata, and safe
      `ModelProfile` persistence without saving secrets.

13. Provider Model Assignment by Mode.
    - Model assignment supports Novel, Tavern, World, Cross-Mode, structured
      JSON, quality, memory summary, and cheap-summary use cases with capability
      warnings and fallback-chain summaries.

14. Provider Connectivity Diagnostics / Secret Redaction.
    - Provider redaction covers API-key-like strings, Authorization Bearer,
      OpenAI-style keys, relay tokens, secret references, token-like URL
      query/path segments, raw provider errors, logs, and diagnostics.

15. Provider Usage / Cost Dashboard Pro.
    - Provider usage dashboard shows local usage estimates by provider, model,
      mode, use case, success/error, estimated tokens, estimated cost, average
      latency, and error counts without prompt/output bodies.

16. CrossMode Conflict Review Pro.
    - CrossMode conflict review categorizes character identity, timeline,
      relationship, fact visibility, stale link, broken link, and proposal
      validation conflicts. Fixes remain draft/proposal based.

17. Module Playtest / Stress UI Pro.
    - Module playtest/stress UI shows module suites, pass/fail, failed step,
      action coverage, namespace conflicts, migration conflicts, and hidden
      leak warnings without executing arbitrary code.

18. Save Migration Visualizer.
    - Save migration visualizer shows save schema version, migration-needed
      status, dry-run plan, affected fields, module state changes, warnings,
      and destructive-blocked status. Migration apply remains explicit-confirm
      and backend-controlled.

19. Diagnostics Bundle Review UI.
    - Diagnostics review shows included safe sections and excluded sections,
      including `.env`, API keys, provider secrets, raw env, raw prompt/output,
      hidden facts, NPC secrets, debug memory, raw `state_deltas`,
      mature/private content, and database files.

20. Local Test Run Dashboard.
    - Local test dashboard shows recommended local commands, latest safe test
      report/build status where available, local-only copy, and no arbitrary
      shell command execution UI.

21. Safe Debug Export Wizard.
    - Safe Debug Export Wizard shows risk copy, debug-gated scopes, redaction
      policy, explicit confirmation for raw export, and no upload behavior.

22. QA / Debug UI Component Cleanup.
    - Shared QA/debug/provider safety components and badges are present for
      debug gating, redacted values, safe report cards, status badges, and
      filter controls.

23. v3.5 UI Regression Tests.
    - `frontend/scripts/check-v35-qa-debug-provider-ui.mjs` and npm script
      `check:v35-qa-debug-provider-ui` are present and pass.

24. v3.5 Integration Regression Tests.
    - v3.5 regression coverage verifies QA/debug/replay safe summaries,
      debug-gated StateDelta access, redacted visible-vs-debug compare,
      safe hidden leak/quality/playtest/module/cross-mode/save-migration
      reports, fake-provider connection testing, model discovery/sync,
      model assignment validation, secret redaction, diagnostics/log
      exclusions, and no real provider calls.

## Boundary Review

Accepted v3.5 boundaries:

- World Engine remains the source of world facts and runtime authority.
- Debug and replay surfaces observe and analyze only. They do not modify
  `GameState`, apply `StateDelta`, delete/edit EventLog entries, or write back
  replay state.
- Runtime world changes still flow through backend game/action APIs,
  `StateDelta`, and `EventLog`.
- Normal UI continues to use safe summaries and `visible_state`-style data. It
  does not show hidden facts, NPC secrets, debug memory, raw prompts, raw env,
  provider secrets, API keys, or raw `state_deltas`.
- Raw StateDelta/EventLog/debug details are available only through DebugGate and
  backend `ENABLE_DEBUG_API`.
- StateDelta Viewer and Visible vs Debug Compare are debug-sensitive and
  redacted by default.
- Diagnostics, logs, backup/export, safe debug export, provider diagnostics,
  and quality reports default to redacted safe summaries.
- Provider Gateway remains the only model entry point.
- Provider connectivity, test connection, model discovery, model sync, and
  model assignment are local Provider configuration capabilities. They do not
  add an online platform, API resale service, or second LLM authority path.
- Provider choice may affect wording, latency, cost, formatting, or capability
  routing; it does not decide world facts.
- `ProviderProfile` stores provider metadata plus `api_key_env` / safe
  `secret_ref` references. It does not store raw API keys.
- `transient_api_key` is request-only for local test/fetch flows. It is not
  persisted, not copied to ProviderProfile/ModelProfile, and not included in
  logs, diagnostics, backup/export, frontend state, or API responses.
- Provider connection/model discovery tests use fake/mock/local_stub clients
  and do not perform real provider network calls.
- Provider raw errors, Authorization headers, token-like URLs, and secret-like
  strings are redacted before display or diagnostics.
- No account, cloud sync, online marketplace, remote package auto-download,
  online QA platform, API resale service, or specific relay service support is
  accepted in v3.5.

## Known Limitations

- v3.5 is not a World Engine, save-system, or gameplay rule release.
- v3.5 does not implement account, cloud sync, online marketplace, online QA,
  remote package auto-download, API resale, or provider CI connectivity to real
  services.
- Provider model discovery is implemented and tested through safe/fake client
  paths. Real provider connectivity remains a local user-configured runtime
  capability outside CI and must keep explicit secret handling.
- Provider usage/cost remains an estimate, not billing-grade accounting.
- Safe Debug Export is local-only and redacted by default; raw debug exports
  remain a high-care debug workflow requiring explicit confirm and debug API.
- Several v3.5 QA/Debug/Provider panels still live in a large frontend module.
  This is acceptable for release readiness but should be split in future
  maintainability/accessibility work.
- The frontend production build emits the existing Vite chunk-size warning. The
  build succeeds; code splitting remains a v3.6 polish item.

## Acceptance Risks

- Medium risk: Debug raw data is intentionally inspectable when
  `ENABLE_DEBUG_API` is enabled. Regression checks and audits must keep raw
  EventLog/StateDelta/debug payloads inside DebugGate.
- Medium risk: Provider connectivity includes one-request
  `transient_api_key` input for local testing/fetching. Current tests verify it
  is not persisted or leaked, but any future provider flow must keep the same
  redaction and non-persistence policy.
- Medium risk: Real provider model-list behavior varies by provider. v3.5
  correctly treats unsupported model listing as a safe status, but user
  guidance should avoid promising universal model discovery.
- Low risk: Static frontend checks are smoke/regression checks, not a formal
  proof of every UI path.
- Low risk: Performance and quality dashboards may become dense on very large
  projects; v3.6 should improve progressive disclosure and large-report
  performance.

## Recommended v3.6 Priorities

1. Local Performance & Accessibility Polish.
   - Address bundle size/code splitting, route-level loading, and large report
     rendering performance.

2. Provider UI performance and accessibility.
   - Improve model-list performance, capability matrix performance, keyboard
     navigation, focus management, and friendlier capability warnings.

3. QA/Debug component modularization.
   - Split Timeline Replay, EventLog, StateDelta, Provider Connectivity,
     Quality, Diagnostics, and Debug Export panels into smaller files with
     stronger component-level checks.

4. Large report UX.
   - Add progressive disclosure or virtualization for EventLog, Timeline,
     Quality, Playtest, Performance, and Provider usage reports.

5. Continued redaction hardening.
   - Keep Provider redaction, diagnostics redaction, debug export filtering,
     and hidden leak report policies in the release checklist.

6. Safer local provider guidance.
   - Keep relay/custom provider language generic and local-configuration based,
     avoiding any implication of API resale or endorsed third-party services.

## Final Status

Final status: **Accepted for v3.5 release readiness, with documented
limitations and v3.6 follow-up recommendations.**

Required verification passed:

- `python -m pytest`: passed, `1768 passed`.
- `cd frontend && npm.cmd run build`: passed.
- `cd frontend && npm.cmd run check:v35-qa-debug-provider-ui`: passed during
  v3.5 release-blocker remediation.

No high-risk v3.5 acceptance blocker remains in the accepted scope.
