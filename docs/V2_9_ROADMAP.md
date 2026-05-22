# v2.9 Roadmap: Local UI / UX Foundation

## Version Theme

Local UI / UX Foundation.

v2.9 changes the near-term direction from Online-Ready Architecture to a
local-first, UI-first, experience-first foundation release. The goal is to make
the existing Novel Studio, Tavern Studio, World Studio, Cross-Mode Bridge,
Provider Gateway, Script / Mod Platform, advanced modules, and RP/Mature safety
systems easier to understand and use without changing their authority
boundaries.

## Current Baseline

- v2.1 implemented Unified Narrative Project Layer.
- v2.2 implemented Novel Studio MVP.
- v2.3 implemented Tavern Studio MVP.
- v2.4 implemented Cross-Mode Bridge.
- v2.5 implemented Provider Gateway Pro.
- v2.6 implemented Script / Mod Platform Pro.
- v2.7 implemented Advanced World Simulation Modules.
- v2.8 implemented or planned Roleplay Immersion & Mature Module.

The project now has many local capabilities, but their UI surfaces are uneven.
v2.9 should improve the local shell, navigation, project entry points, provider
setup, quality dashboards, mode entry pages, local privacy messaging, and shared
frontend states before adding new major business systems.

## Goal

v2.9 should establish a coherent local UI / UX foundation for AI Narrative
Studio:

- clearer Project Home and mode entry points;
- unified local app shell and navigation;
- consistent module/provider/quality/status surfaces;
- shared loading, empty, error, disabled, dirty, confirm, and save patterns;
- local privacy and secrets messaging that is visible but not noisy;
- frontend component cleanup that reduces UI drift;
- regression checks that keep the frontend build stable.

v2.9 is primarily a UI architecture and experience release. It should not add
new large gameplay, online, account, marketplace, cloud, or collaboration
systems.

## Explicit Non-Goals

v2.9 does not implement:

- account system;
- cloud sync;
- online marketplace;
- remote package auto-download;
- online publishing platform;
- multi-user collaboration;
- new large gameplay modules;
- arbitrary-code plugins;
- World Engine rule changes;
- LLM permission boundary changes;
- frontend direct `GameState` mutation;
- frontend API key display;
- hidden/debug data in normal UI;
- Mature Module enabled by default.

Online-Ready Architecture, account systems, cloud sync, online marketplaces,
remote package registries, online narrative platforms, online mature-content
platforms, and remote package auto-download remain long-term optional
directions only.

## Hard Constraints

- Local-first remains the product model.
- UI optimization must not change business fact authority.
- Frontend world-state changes must go through backend APIs.
- World changes still require `StateDelta` and `EventLog`.
- Provider secrets must not enter frontend code or UI responses.
- Debug data must be gated by `ENABLE_DEBUG_API`.
- Mature/private content is not exported, displayed in normal views, or
  uploaded by default.
- `npm.cmd run build` must pass.
- Do not introduce large UI dependencies unless the roadmap or implementation
  notes explain why existing patterns are insufficient.
- Every new page must have loading, empty, error, and disabled states.

## Recommended Development Order

1. **Shell and Design Foundation**
   - Local App Shell Review
   - Design Token / Layout Foundation
   - Unified Navigation
   - Unified Loading / Empty / Error / Disabled States

2. **Project and Mode Entry**
   - Project Home Redesign
   - Mode Landing Pages
   - Novel / Tavern / World Entry Polish
   - Local Status Bar

3. **Trust, Setup, and Save UX**
   - Local Privacy & Secrets UX
   - Provider Setup UX Polish
   - Unified Confirm / Dirty State / Save UX
   - Settings / Preferences UX

4. **Operational Dashboards**
   - Module Browser UX Polish
   - Quality Gate Dashboard UX Polish
   - Cross-Mode Dashboard UX Polish

5. **Help, Cleanup, and Release Hardening**
   - Local Help / Onboarding Panels
   - Frontend Component Cleanup
   - UI Regression Tests / Build Checks
   - v2.9 UI Acceptance Report

## Module Plans

### 1. Local App Shell Review

- Goal: audit the current frontend shell, top-level layout, panels, navigation,
  settings surfaces, and local status indicators.
- Frontend changes: document current shell gaps and decide which containers,
  navigation areas, and panels should become shared patterns.
- Backend changes: none expected.
- Tests: static frontend build and route smoke checks where available.
- Acceptance: a review summary identifies shell gaps, duplicated UI patterns,
  and the minimum shared shell needed for v2.9.

### 2. Design Token / Layout Foundation

- Goal: define local design tokens for spacing, typography, color roles, panel
  density, borders, status colors, and responsive layout.
- Frontend changes: centralize reusable styles without introducing a large UI
  framework; keep operational UI compact and scannable.
- Backend changes: none.
- Tests: frontend build; visual smoke checks for representative desktop and
  narrow widths if local tooling exists.
- Acceptance: new and existing v2.9 surfaces use consistent layout and status
  styling without breaking current screens.

### 3. Unified Navigation

- Goal: make Project Home, Novel, Tavern, World, Cross-Mode, Modules, Provider,
  Quality, Settings, and Help discoverable from one local navigation model.
- Frontend changes: shared navigation component, active state, mode grouping,
  disabled state, and local-only labels where appropriate.
- Backend changes: none expected.
- Tests: frontend build; navigation state tests or route smoke checks.
- Acceptance: users can reliably move between the main local studio areas
  without hidden one-off entry points.

### 4. Project Home Redesign

- Goal: make the first project screen a useful local dashboard rather than a
  passive landing area.
- Frontend changes: project summary, recent local activity, mode cards,
  local privacy status, provider status, quality status, and next-step actions.
- Backend changes: optional read-only summary endpoint if current APIs cannot
  supply safe project metadata efficiently.
- Tests: empty project, missing provider, quality-warning, and disabled-feature
  states.
- Acceptance: Project Home helps users choose Novel, Tavern, World, Modules,
  Provider, Quality, or Settings without exposing secrets or hidden data.

### 5. Mode Landing Pages

- Goal: give Novel, Tavern, and World modes consistent local landing pages.
- Frontend changes: shared mode header, recent drafts/sessions/saves, local
  status, safe action shortcuts, and relevant warnings.
- Backend changes: optional read-only mode summary APIs.
- Tests: empty state, loading state, API error state, disabled feature state.
- Acceptance: each mode has a predictable entry page before deeper editors.

### 6. Local Status Bar

- Goal: expose local runtime status without turning it into cloud telemetry.
- Frontend changes: status bar for local project, save state, provider mode,
  debug flag, mature flag, quality state, and offline/local-only indicators.
- Backend changes: optional safe status endpoint that excludes secrets, hidden
  facts, raw prompts, raw `state_deltas`, and local sensitive paths.
- Tests: status rendering for provider missing, mock provider, debug disabled,
  mature disabled, and quality warning states.
- Acceptance: users can see local readiness without leaking private data.

### 7. Unified Loading / Empty / Error / Disabled States

- Goal: replace inconsistent ad hoc states with shared UI patterns.
- Frontend changes: reusable state components and per-page state copy.
- Backend changes: none.
- Tests: representative screens render loading, empty, error, and disabled
  states without crashing.
- Acceptance: every new v2.9 page and touched high-level page has all four
  states.

### 8. Unified Confirm / Dirty State / Save UX

- Goal: make local draft edits, unsaved changes, destructive actions, import,
  export, and apply flows feel predictable.
- Frontend changes: shared confirm dialogs, dirty-state indicators, save/apply
  buttons, disabled states, and clear error handling.
- Backend changes: no authority changes; APIs remain responsible for validation
  and apply.
- Tests: unsaved-change warnings, confirm-required actions, failed save, and
  successful save.
- Acceptance: UI cannot silently apply world-changing edits without explicit
  user action and backend validation.

### 9. Local Privacy & Secrets UX

- Goal: make local privacy guarantees visible and understandable.
- Frontend changes: privacy badges, local-only explanations, provider secret
  redaction labels, export filtering notes, mature/private default-off labels.
- Backend changes: optional safe privacy summary endpoint.
- Tests: provider secret is never rendered; export notes appear; mature/private
  default-off state appears.
- Acceptance: normal UI communicates privacy without exposing sensitive values.

### 10. Provider Setup UX Polish

- Goal: make provider setup clearer while preserving Provider Gateway authority.
- Frontend changes: provider profile list, mock/local/remote labels, missing
  env guidance, safety policy summary, cost/token estimate caveat, no key
  display.
- Backend changes: read-only safe provider summary if current API is too raw.
- Tests: missing env, mock provider, local provider, remote provider, policy
  warning, and no-secret rendering.
- Acceptance: users can configure or inspect providers without API keys entering
  frontend responses or logs.

### 11. Module Browser UX Polish

- Goal: improve local module/package browsing without adding an online market.
- Frontend changes: clearer module list, filters, permission risk display,
  compatibility status, quality status, import/export warnings, local-only
  messaging.
- Backend changes: optional summary fields only; no remote registry.
- Tests: empty module list, unsafe module, permission warning, compatibility
  warning, API disabled state.
- Acceptance: module browsing remains local and does not imply remote download
  or online marketplace support.

### 12. Quality Gate Dashboard UX Polish

- Goal: make quality results actionable without hiding blockers.
- Frontend changes: quality summary, blocker/warning grouping, release readiness
  checklist, RP/Mature/module/provider sections, safe report details.
- Backend changes: optional report summary normalization.
- Tests: pass, warning, blocker, loading, error, and report-redaction states.
- Acceptance: users can understand why a project passes or fails without seeing
  hidden facts, secrets, or mature/private content in normal reports.

### 13. Cross-Mode Dashboard UX Polish

- Goal: make Novel/Tavern/World bridge state easier to inspect.
- Frontend changes: draft/proposal queues, validation status, apply-required
  labels, mature/private filtering notes, safe source summaries.
- Backend changes: optional read-only cross-mode summary endpoint.
- Tests: no drafts, invalid draft, mature-filtered draft, proposal pending,
  apply disabled state.
- Acceptance: Cross-Mode UI reinforces proposal/validation/apply boundaries.

### 14. Novel / Tavern / World Entry Polish

- Goal: improve the first-click experience for the three primary modes.
- Frontend changes: Novel recent drafts/outlines, Tavern sessions/characters,
  World saves/active world, and consistent quick actions.
- Backend changes: optional safe summaries only.
- Tests: each mode handles no data, partial data, API error, and disabled
  provider/module states.
- Acceptance: users can enter each mode through a consistent local workflow.

### 15. Settings / Preferences UX

- Goal: make local preferences, privacy, provider, debug, mature, module, and
  UI settings easier to scan.
- Frontend changes: grouped settings sections, clear local-only text, safe
  toggles, disabled states, and reset/confirm patterns.
- Backend changes: optional preferences summary endpoint; no cloud account.
- Tests: defaults, disabled debug, mature disabled, provider missing, save
  failure, and no-secret rendering.
- Acceptance: settings are understandable without implying accounts, cloud
  sync, or online services.

### 16. Local Help / Onboarding Panels

- Goal: explain local workflows in context without making a marketing landing
  page.
- Frontend changes: concise onboarding panels for Project Home, Novel, Tavern,
  World, Provider, Modules, Quality, and privacy.
- Backend changes: none expected.
- Tests: panels render in empty/disabled states and can be dismissed locally.
- Acceptance: new users can find the next local action without online setup.

### 17. Frontend Component Cleanup

- Goal: reduce duplicated UI code and make future UI Pro work easier.
- Frontend changes: extract shared components for panels, toolbars, status
  chips, tabs, forms, confirmation, and state placeholders.
- Backend changes: none.
- Tests: frontend build; smoke checks for screens touched by refactor.
- Acceptance: cleanup reduces drift without changing business behavior.

### 18. UI Regression Tests / Build Checks

- Goal: add focused checks that protect the new UI foundation.
- Frontend changes: lightweight regression tests or build-time checks according
  to the existing frontend toolchain.
- Backend changes: none unless test fixtures need read-only safe endpoints.
- Tests: `cd frontend && npm.cmd run build`; page state smoke tests where
  feasible; backend tests if any API summaries are added.
- Acceptance: UI foundation has repeatable build/regression coverage.

### 19. v2.9 UI Acceptance Report

- Goal: produce final release evidence for the UI foundation.
- Frontend changes: none.
- Backend changes: none.
- Tests: full backend suite if backend endpoints changed; frontend build always.
- Acceptance: `docs/V2_9_ACCEPTANCE_REPORT.md` exists and records commands,
  scope, limitations, privacy/security review, and final status.

## Cross-Cutting Impact

### Novel Studio

Novel Studio should gain a clearer local entry page, recent draft/outlines
summary, provider readiness cues, export privacy hints, and consistent empty/
error/disabled states. v2.9 must not change Novel-to-World validation rules or
let prose drafts become facts without structured validation.

### Tavern Studio

Tavern Studio should gain clearer session entry, character/voice/RP/mature
status cues, Multi-NPC entry polish, and privacy indicators. RP still cannot
directly mutate `GameState`, and mature/private content remains default-filtered
from normal views and exports.

### World Studio

World Studio should gain clearer save/world entry, module status cues, local
runtime status, and quality warnings. UI changes must not alter World Engine
rules, `StateDelta`, `EventLog`, visibility, NPC knowledge, or save migration
authority.

### Script / Mod Platform

Module and package UI should become easier to scan and safer to use locally.
v2.9 does not add online marketplace, remote registry, automatic download, or
remote package execution.

### Provider Gateway

Provider setup should become clearer and safer. Provider Gateway remains the
only model entry point. Provider UI must never show raw API keys, raw env, or
provider secrets.

### Quality Gate

Quality dashboards should become more actionable and readable while preserving
blockers. Normal reports must not expose hidden facts, NPC secrets, raw prompts,
raw `state_deltas`, API keys, or mature/private content.

### Privacy / Security

v2.9 should make privacy boundaries more visible. It must not weaken local-only
defaults, secret handling, export filtering, debug gating, mature/private
filtering, or package validation for UI convenience.

## v2.9 Integration Test Requirements

- Frontend build passes with `cd frontend && npm.cmd run build`.
- New/changed pages render loading, empty, error, and disabled states.
- Project Home, mode landing pages, navigation, settings, provider setup,
  module browser, quality dashboard, and cross-mode dashboard have smoke
  coverage where local test tooling supports it.
- Provider UI tests confirm API keys and env values are not displayed.
- Quality/report UI tests confirm hidden/debug/private/mature sensitive content
  is not rendered in normal views.
- Export UI tests confirm secrets and mature/private content are filtered by
  default.
- Any new read-only backend summary endpoint has focused pytest coverage.
- No test calls real provider APIs.

## v2.9 Final Acceptance Criteria

- Local App Shell Review is complete.
- Shared layout and UI state patterns are documented and applied to v2.9
  surfaces.
- Unified navigation exposes Project Home, Novel, Tavern, World, Modules,
  Provider, Quality, Settings, and Help.
- Project Home has local status, mode entry, provider, quality, and privacy
  cues.
- Novel, Tavern, and World have consistent mode landing pages.
- Provider UI never displays API keys.
- Normal UI never displays hidden facts, NPC secrets, debug memory, raw prompts,
  raw `state_deltas`, or mature/private content.
- Debug views remain gated by `ENABLE_DEBUG_API`.
- Export UI defaults to secret and mature/private filtering.
- No account, cloud sync, online marketplace, remote registry, remote package
  auto-download, online publishing, or multi-user collaboration feature is
  introduced.
- Frontend build passes.
- If backend APIs changed, `python -m pytest` passes.
- `docs/V2_9_ACCEPTANCE_REPORT.md` exists before release.

## v3.0 Candidate Direction

Recommended v3.0 direction: **Local Desktop Studio Polish**.

v3.0 should build on v2.9's local UI foundation and improve desktop startup,
project selection, recent projects, local health checks, backup/restore,
diagnostics, crash report review, offline help, and packaging polish. It should
remain local-first and should not introduce account systems, cloud sync, online
marketplaces, online publishing, or remote package execution.
