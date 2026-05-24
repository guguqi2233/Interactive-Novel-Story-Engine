# v3.6 Privacy / Visibility Regression Audit

Verification date: 2026-05-24

## Scope

This audit verifies that v3.6 performance and accessibility work did not
regress privacy, visibility, debug, Provider secret, cache, search, label,
loading, diagnostics, backup, mature/private, or local-first boundaries.

The review covers:

- route-level code splitting and lazy-loaded debug surfaces;
- EventLog, Timeline Replay, and StateDelta rendering;
- Quality and Hidden Leak reports;
- Provider model/status caches and frontend safe API cache;
- search/filter indexes;
- ErrorBoundary redaction;
- accessibility labels and loading skeletons;
- diagnostics / backup progress UI;
- localStorage / sessionStorage usage;
- mature/private default behavior;
- account, cloud, online marketplace, and remote download entrypoints.

The audit is read-only for business code. The only repository change made for
this task is this report.

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v36-performance-a11y
```

Results:

- `python -m pytest`: passed, `1783 passed in 113.65s`.
- `npm.cmd run build`: passed.
- `npm.cmd run check:v36-performance-a11y`: passed.
- Current build emits no Vite `>500 kB` chunk warning.
- Current main App chunk: `assets/App-BBc0cBc4.js` 445.81 kB, gzip
  107.20 kB.

Additional source evidence reviewed:

- `docs/V3_6_ROADMAP.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/errorBoundary.tsx`
- `frontend/src/filterUtils.ts`
- `frontend/src/safeApiCache.ts`
- `frontend/src/providerUi.tsx`
- `frontend/src/desktopUi.tsx`
- `backend/app/llm/provider_connection_cache.py`
- v3.6 frontend check scripts.

## Passed Items

1. Code splitting does not expose debug routes as normal routes.
   Route-level lazy loading uses safe `Suspense` fallbacks and
   `AppErrorBoundary`. No normal route was found that directly exposes
   StateDelta Viewer or raw debug export without DebugGate.

2. Lazy-loaded debug pages remain DebugGate controlled.
   `StateDeltaViewerPanel` is rendered inside an active `<DebugGate>`, and
   EventLog / Timeline raw detail sections are wrapped in DebugGate.

3. EventLog normal UI does not display raw `state_deltas`.
   EventLog normal rows show event id, turn/time, type, actor/source safe
   summaries, visible summary, tags, and linked StateDelta count. Raw event
   JSON and StateDelta details are nested under DebugGate.

4. Timeline normal UI does not display hidden/debug events or raw deltas.
   Timeline safe summaries redact debug-only events, display visible changes
   only as redacted path summaries, and keep raw `event.state_deltas` under
   DebugGate.

5. StateDelta Viewer remains debug-gated.
   The viewer is not presented as normal UI and includes debug-sensitive copy,
   redacted value summaries, path/op/event filters, and no apply-delta action.

6. Quality reports do not display hidden text full content.
   Quality rows use safe issue summaries and redacted report text. Hidden text
   is summarized or counted rather than printed in normal report rows.

7. Hidden Leak reports do not display hidden text full content.
   Hidden Leak issue browsing uses target grouping, severity/source-target
   filters, and safe metadata search. It explicitly states that hidden text and
   secrets are never printed.

8. Provider model cache does not contain API keys.
   Frontend Provider model list caching writes safe model metadata summaries
   through `safeApiCache`, and the cache rejects API key-like payloads before
   storage.

9. Provider status cache does not contain `transient_api_key`.
   Backend `ProviderConnectionStatusCache` stores only provider profile id,
   status, tested time, latency, safe error type, model count, and redaction
   status. It explicitly excludes API keys, transient API keys, Authorization
   headers, raw provider responses, raw error bodies, and `safe_message`.

10. Frontend API cache rejects hidden/debug/secrets.
    `safeApiCache` is in-memory only and rejects payloads containing API keys,
    transient keys, Authorization headers, raw provider responses, raw prompts,
    raw outputs, hidden facts, NPC secrets, NPC knowledge, raw StateDelta,
    raw GameState, debug memory, or mature/private markers.

11. Search/filter indexes do not cache hidden text in normal UI.
    Shared search helpers redact secret-like patterns, and normal list filters
    build indexes from safe metadata such as ids, labels, statuses, visible
    summaries, safe warnings, and redacted paths. Hidden Leak search is limited
    to safe metadata.

12. ErrorBoundary does not display stack/secrets/raw env/sensitive paths.
    `AppErrorBoundary` uses safe error formatting, redacts stack traces, API
    keys, Authorization headers, raw env, hidden facts, NPC secrets, raw
    prompts, raw StateDelta markers, debug memory, private notes, and local
    sensitive paths.

13. Accessibility labels do not include hidden facts or secrets.
    Shared accessible-name generation uses `safeAriaText`, and the v3.6 a11y
    checks reject secret-like, hidden, NPC secret, and raw-debug tokens in
    `aria-label` text.

14. Loading skeletons do not briefly display hidden/debug data.
    Loading skeletons use static safe text and explicitly state that skeleton
    rows never contain project data, hidden facts, raw debug payloads, or
    secrets.

15. Diagnostics / backup progress UI does not display secrets.
    Progress surfaces show staged safe summaries and exclusion policies for
    `.env`, API keys, provider secrets, debug data, mature/private data,
    databases, logs/cache, and build outputs.

16. localStorage / sessionStorage usage remains narrow.
    `safeApiCache` forbids localStorage, sessionStorage, IndexedDB, and service
    worker storage. Current frontend localStorage use is limited to local UI
    preferences: first-run onboarding, keyboard shortcuts, and reduced motion.

17. Mature/private remains default hidden / excluded.
    Tavern, Provider, Settings, export, backup, and diagnostics copy continues
    to mark mature/private content default-off, opt-in, and excluded from
    normal exports, backups, diagnostics, and recovery by default.

18. No account, cloud sync, online marketplace, or remote download entrypoint
    was found.
    v3.6 checks reject enabling UI patterns for those features, and reviewed
    copy continues to frame them as out of near-term scope.

## High-risk Privacy Regressions

None confirmed.

No high-risk privacy, visibility, debug-gating, Provider secret, cache, label,
or loading-state regression was found in the current source review and test
run.

Important note:

- The v3.6 Performance and Accessibility audits record a high-risk active-route
  parity issue for `studio`, `prompt_lab`, and settings-related lazy routes.
  That issue is a release blocker for functional/usability confidence, but this
  privacy-focused audit did not find evidence that the route split itself
  exposes hidden/debug/secrets.

## Medium-risk Visibility Issues

1. Privacy validation is still mostly source/static plus backend tests.
   The current checks are strong for known patterns, but they do not render all
   possible runtime payloads in a browser with malicious fake hidden facts,
   NPC secrets, API keys, raw prompts, and raw StateDelta data.

2. `DebugEventSummary` can render raw `state_deltas` by design.
   Current usage appears inside debug-oriented surfaces, but the helper itself
   has no DebugGate parameter. Future reuse must remain debug-only or be
   refactored to require an explicit debug gate.

3. EventLog safe metadata still derives tags and source module from
   `state_deltas`.
   The code redacts values and debug-gates non-visible events, but metadata
   extraction from deltas should remain under regression tests so hidden paths
   do not drift into normal UI.

4. Search safety depends on developer discipline.
   `buildSafeSearchIndex` redacts secret-like strings, but it cannot know
   semantic hidden/private fields unless callers pass only safe metadata.
   Normal search expansions should require review.

5. localStorage is currently safe but should stay constrained.
   Only UI preference keys were found. Future localStorage/sessionStorage use
   should be blocked unless it is explicit safe preference metadata.

6. ErrorBoundary redaction relies on pattern coverage.
   Current redaction covers known sensitive strings. New sensitive field names
   should be added to redaction tests when introduced.

7. Debug-gated raw data remains present by design.
   Raw EventLog and StateDelta details exist for debug workflows. Release
   checks must continue verifying that code splitting, windowing, and cache
   work do not move those details into normal UI.

## Cache Safety Review

Frontend safe API cache:

- Uses an in-memory `Map`, not persistent browser storage.
- Rejects unsafe payloads before writing.
- Sanitizes summaries and safe errors.
- Rejects or redacts:
  - API key-like strings;
  - Authorization headers;
  - `transient_api_key`;
  - provider secrets and secret refs;
  - raw env;
  - raw provider responses/errors;
  - raw prompts and outputs;
  - hidden facts;
  - NPC secrets and NPC knowledge;
  - raw StateDelta and raw GameState markers;
  - debug memory;
  - mature/private markers.

Backend Provider connection status cache:

- Stores only safe status metadata:
  - `provider_profile_id`;
  - `status`;
  - `tested_at`;
  - `latency_ms`;
  - `safe_error_type`;
  - `model_count`;
  - `redaction_applied`.
- Provides TTL / stale state through safe summaries.
- Does not store `safe_message`, API keys, transient keys, Authorization
  headers, raw provider response, raw error body, raw env, or ProviderProfile
  secret values.

Provider model cache:

- Frontend caching stores safe count/metadata summaries and model list safe
  rows through `safeApiCache`.
- Raw Provider responses and API keys are excluded from UI and cache.

## UI Label Safety Review

Accessible labels:

- `safeAriaText` redacts API key-like tokens, hidden fact markers, NPC secret
  markers, raw debug markers, private/mature markers, and local sensitive paths
  before dynamic strings enter labels.
- Status, risk, severity, leak, event type, StateDelta op, model capability,
  dashboard card, section card, and navigation labels use readable safe text.
- v3.6 a11y checks reject secret-like or hidden/debug terms in `aria-label`
  patterns.

Loading labels and skeletons:

- Route loading fallback uses static safe copy.
- Skeleton rows are `aria-hidden` and contain no dynamic project content.
- Progressive load notes state that summaries load before large lists and do
  not expose hidden/debug/secrets.

Error labels:

- Route error states use safe, redacted titles and live regions.
- ErrorBoundary does not render stack traces, raw env, local sensitive paths,
  hidden facts, API keys, or provider secrets in normal UI.

## Non-blocking Follow-ups

- Add browser-level privacy smoke tests that inject fake hidden facts, NPC
  secrets, API keys, raw prompts, raw outputs, raw StateDelta payloads, and
  mature/private markers into representative safe summaries and assert they do
  not render in normal UI.
- Add a lightweight lint/check for new localStorage/sessionStorage keys.
- Add a search-index audit that flags hidden/private/debug field names passed
  to normal-mode `buildSafeSearchIndex`.
- Make `DebugEventSummary` require an explicit `debugEnabled` or DebugGate prop
  to prevent accidental normal reuse.
- Add provider cache serialization fixtures for very large model lists and
  error responses.
- Expand ErrorBoundary redaction tests when new sensitive field names are added.
- Add active-route runtime smoke checks for lazy-loaded routes so source-token
  checks cannot be satisfied by unused legacy code.

## Release Decision

The v3.6 privacy / visibility regression audit is **not blocked on privacy
grounds**.

Current evidence shows:

- full backend test suite passes;
- frontend build passes;
- v3.6 performance/a11y check passes;
- DebugGate boundaries are still present;
- normal UI avoids hidden/debug/raw StateDelta data;
- safe caches reject secrets and hidden/debug payloads;
- ErrorBoundary, labels, skeletons, diagnostics, backup progress, and search
  helpers preserve safe-summary behavior.

This does not override the separately recorded v3.6 route-level parity blocker
from the Performance and Accessibility audits. Final v3.6 release should still
verify or restore lazy route feature parity before acceptance, but no additional
privacy-specific blocker was found here.
