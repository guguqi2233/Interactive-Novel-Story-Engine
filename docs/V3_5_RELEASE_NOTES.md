# v3.5 Release Notes: Local QA / Debug / Replay & Provider Connectivity UI Pro

## 1. Version Name

v3.5 **Local QA / Debug / Replay & Provider Connectivity UI Pro**

## 2. Version Goal

v3.5 turns local QA, Debug, Replay, Quality, Diagnostics, and Provider
Connectivity into a daily-use local inspection workspace. The release focuses
on helping users understand what happened in a world/session, inspect safe
quality reports, review debug data behind explicit gates, validate provider
configuration, discover/sync model metadata, and assign models by mode.

v3.5 remains local-first. It is not an account system, cloud sync feature,
online marketplace, online QA platform, remote package downloader, API resale
service, or specific relay-provider integration.

## 3. New QA / Debug / Replay Capabilities

- Added a v3.5 Local QA / Debug / Replay / Provider contract review.
- Added Timeline Replay UI Pro for session/save replay selection, turn/time
  timeline rows, event filters, replay controls, and safe replay summaries.
- Added EventLog Viewer Pro with event id, turn/time, event type, actor safe
  summary, source module, tags, visible summary, and linked StateDelta count.
- Added StateDelta Viewer Pro as a debug-sensitive, read-only viewer.
- Added Visible vs Debug State Compare with redacted hidden summaries and
  filtered-field counts.
- Added Hidden Leak Report UI Pro with severity, source, target, safe summary,
  and suggested action rows.
- Added Safe Debug Export Wizard with redaction policy, debug-gated scopes, and
  explicit confirm for raw debug export.
- Added shared QA/debug UI components and badges for debug gates, redacted
  values, status labels, safe report cards, and filters.

Debug and replay are observation tools only. They do not modify `GameState`,
apply `StateDelta`, delete/edit `EventLog`, or write replay state back.

## 4. New Provider Connectivity Capabilities

- Added Provider Connectivity Dashboard for local provider status, provider
  type, model count, last tested time, allowed modes, default model, warnings,
  and local-only boundary copy.
- Added safe Provider connection testing backend:
  `POST /projects/{project_id}/providers/test-connection`.
- Added Provider model discovery and sync:
  - `POST /projects/{project_id}/providers/fetch-models`
  - `POST /projects/{project_id}/providers/sync-models`
  - `GET /projects/{project_id}/providers/{provider_id}/models`
  - `PATCH /projects/{project_id}/providers/{provider_id}/models`
- Added `ModelProfile` metadata sync for provider/model ids, capability flags,
  context/token hints, recommended use cases, enabled state, and last seen time.
- Added Provider Model Assignment by Mode for Novel, Tavern, World,
  Cross-Mode, structured JSON, quality, memory summary, and cheap-summary use
  cases.
- Added capability warnings for structured JSON use cases and fallback-chain
  summaries.
- Added Provider Usage / Cost Dashboard Pro for local estimated usage by
  provider, model, mode, use case, success/error, estimated tokens, estimated
  cost, average latency, and error count.

Provider Connection & Model Discovery is a local Provider Gateway
configuration capability. It is not an API resale service, an online platform,
or an endorsement of any specific relay provider. CI and automated tests use
fake/mock/local provider paths and do not perform real provider network calls.

## 5. Behavior Changes

- Provider profiles reject raw secret-like values in `secret_ref`.
- Provider profile safe summaries redact `secret_ref` values and expose only
  configured status.
- Provider profile validation errors are sanitized so invalid secret-like input
  is not reflected in API responses.
- `transient_api_key` is request-only for local connection/model-fetch checks.
  It is not persisted and is not copied into ProviderProfile, ModelProfile,
  logs, diagnostics, backup, export, or frontend state.
- Diagnostics, logs, Provider errors, model discovery errors, and debug export
  summaries apply Provider redaction.
- Raw StateDelta/EventLog/debug payloads remain debug-gated.
- Normal QA/debug/provider views use safe summaries and must not render hidden
  facts, NPC secrets, debug memory, raw prompts, raw env, API keys, provider
  secrets, or raw `state_deltas`.

## 6. Frontend Changes

- Expanded `frontend/src/App.tsx` with v3.5 QA, Debug, Replay, Provider,
  Diagnostics, Quality, Performance, CrossMode, Module Stress, Save Migration,
  and Safe Debug Export surfaces.
- Expanded `frontend/src/api.ts` with v3.5 provider connectivity, model
  discovery/sync, model assignment, and QA/debug helper calls.
- Added `frontend/scripts/check-v35-qa-debug-provider-ui.mjs`.
- Added `check:v35-qa-debug-provider-ui` npm script.
- Added UI regression checks for:
  - Timeline Replay;
  - EventLog Viewer;
  - StateDelta Viewer;
  - Visible vs Debug Compare;
  - Hidden Leak Report;
  - Playtest Dashboard;
  - Unified Quality Dashboard;
  - Performance Dashboard;
  - Provider Connectivity;
  - Provider Model List / Assignment;
  - Provider Usage;
  - CrossMode Conflict Review;
  - Module Playtest / Stress;
  - Save Migration Visualizer;
  - Diagnostics Bundle Review;
  - Safe Debug Export;
  - DebugGate copy;
  - no normal raw StateDelta UI;
  - no Provider API key UI;
  - no account/cloud/marketplace UI.

## 7. Backend API Changes

New or expanded backend/provider surfaces include:

- `POST /projects/{project_id}/providers/test-connection`
  - returns safe `ProviderConnectionStatus`;
  - supports fake/mock/local provider testing in automated tests;
  - redacts provider errors and secrets.

- `POST /projects/{project_id}/providers/fetch-models`
  - returns safe model discovery reports;
  - supports unsupported model-list status;
  - does not persist transient secrets.

- `POST /projects/{project_id}/providers/sync-models`
  - persists safe `ModelProfile` metadata;
  - returns added/updated/disabled/unchanged sync status.

- `GET /projects/{project_id}/providers/{provider_id}/models`
  - returns safe model summaries.

- `PATCH /projects/{project_id}/providers/{provider_id}/models`
  - updates safe model metadata.

- Provider model assignment endpoints for loading, validating, and saving mode
  routing configuration.

Backend Provider support now includes:

- `provider_connection_test`;
- `provider_model_discovery`;
- `provider_model_assignment`;
- `provider_redaction`;
- stricter `ProviderProfileV2` secret reference validation;
- redacted Provider profile safe summaries.

## 8. Timeline / EventLog / StateDelta Changes

- Timeline Replay normal view shows visible/system-safe event summaries and
  replay controls.
- EventLog Viewer normal view shows safe event cards, not raw event JSON.
- StateDelta Viewer is explicitly debug-sensitive, read-only, and gated.
- Raw `state_deltas` are visible only through debug-gated UI.
- Replay controls observe and navigate; they do not write back to EventLog,
  `GameState`, saves, or content packs.
- Visible vs Debug Compare shows redacted summaries and counts instead of full
  hidden text.

## 9. Quality / Playtest / Diagnostics Changes

- Unified Quality Gate Dashboard aggregates Project, World, Novel, Tavern,
  Cross-Mode, Provider, Mods, Modules, RP/Mature, and Backup/Diagnostics.
- Playtest Dashboard Pro shows pass/fail, duration, failed step, action/event
  coverage, hidden leak warnings, and safe replay summaries.
- Performance Dashboard Pro shows local timing/size metrics without prompts,
  outputs, hidden facts, or secrets.
- CrossMode Conflict Review Pro surfaces safe conflict rows and draft-only fix
  affordances.
- Module Playtest / Stress UI shows module coverage, conflicts, migration
  warnings, and hidden leak warnings without arbitrary code execution.
- Save Migration Visualizer shows dry-run migration plans and warnings without
  raw save JSON.
- Diagnostics Bundle Review UI previews included/excluded sections and defaults
  to excluding secrets, raw env, raw prompt/output, hidden facts, NPC secrets,
  debug memory, raw `state_deltas`, mature/private content, and database files.
- Local Test Run Dashboard shows recommended local validation commands and safe
  latest report/build summaries without arbitrary shell execution.

## 10. Provider Connection / Model Discovery / Model Assignment Changes

- Provider connection testing returns local safe status values such as
  connected, missing secret, auth failed, timeout, invalid base URL, model-list
  failed, and unsupported model list.
- Model discovery supports fake OpenAI-compatible/custom responses in tests and
  handles unsupported model-list providers safely.
- Model sync stores normalized `ModelProfile` metadata and does not delete
  disabled user-managed models unless explicitly configured.
- Manual model metadata can be patched without secrets.
- Model assignment by mode validates capability requirements such as JSON /
  structured-output support for structured use cases.
- Provider Gateway remains the only model entry point. Provider routing changes
  do not allow providers to decide world facts.

## 11. Secret Redaction / Privacy Changes

- Added Provider redaction for:
  - API-key-like strings;
  - Authorization Bearer values;
  - OpenAI-style keys;
  - relay-style tokens;
  - secret assignment strings;
  - secret references;
  - token-like URL query/path segments;
  - raw provider response/error blocks.
- Diagnostics and logs apply redaction before user-facing output.
- Provider connection and model discovery errors are safe summaries, not raw
  provider error dumps.
- `ProviderProfile` stores only provider metadata plus `api_key_env` or a safe
  `secret_ref`.
- `ProviderProfileV2.secret_ref` rejects direct key-like values.
- `transient_api_key` is one-request-only and must not enter logs,
  diagnostics, backup, export, provider profiles, model profiles, usage
  records, call traces, crash reports, frontend state, or docs examples.
- Frontend Provider UI does not display API keys or Authorization headers.

## 12. Known Limitations

- v3.5 is not a World Engine, save-system, or gameplay rule release.
- v3.5 does not implement account, cloud sync, online marketplace, online QA,
  remote package auto-download, API resale, or provider CI connectivity to real
  services.
- Provider model discovery is implemented and tested through safe/fake client
  paths. Real provider connectivity remains a local user-configured runtime
  capability outside CI and must keep explicit secret handling.
- Provider usage/cost is an estimate, not billing-grade accounting.
- Safe Debug Export is local-only and redacted by default. Raw debug export
  remains a high-care workflow requiring `ENABLE_DEBUG_API` and explicit
  confirmation.
- Several v3.5 panels still live in a large frontend module. This is acceptable
  for v3.5 release readiness but should be split in v3.6.
- Frontend production build still emits the existing Vite chunk-size warning.

## 13. Upgrade Notes from v3.4

- Existing v3.4 Authoring / Mod UI Pro workflows remain local-first and
  draft/candidate/proposal based.
- v3.5 adds QA/debug/provider inspection surfaces around existing Studio modes;
  it does not change World Engine authority or Authoring safe-apply rules.
- Provider profiles should use `api_key_env` or safe `secret_ref` references.
  Raw keys in provider profile fields are rejected.
- Provider connectivity tests and model discovery in automated tests use fake
  provider clients. CI should not be configured with real provider keys.
- Debug raw details require `ENABLE_DEBUG_API`; normal users should rely on
  safe summaries unless explicitly debugging.
- Release validation should include:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v35-qa-debug-provider-ui
```

## 14. Recommended v3.6 Direction

Recommended v3.6 theme: **Local Performance & Accessibility Polish**.

Recommended v3.6 priorities:

- frontend code splitting and bundle-size reduction;
- Provider model list performance and caching UX;
- Provider capability matrix performance and accessibility;
- keyboard navigation and focus management across QA/debug/provider surfaces;
- large report virtualization or progressive disclosure for Timeline,
  EventLog, Quality, Playtest, Performance, and Provider Usage;
- clearer user-facing explanations for Provider capability warnings;
- component-level accessibility checks if the frontend testing stack expands;
- continued secret redaction and debug-gating regression coverage.

v3.6 should keep the same local-first route and must not add accounts, cloud
sync, online marketplaces, remote package download, API resale, or real
provider CI calls.
