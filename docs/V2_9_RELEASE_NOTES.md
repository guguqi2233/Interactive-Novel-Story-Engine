# v2.9 Release Notes: Local UI / UX Foundation

## 1. Version Name

v2.9 is **Local UI / UX Foundation**.

This release moves the near-term project direction toward local-first,
UI-first, experience-first product work. It is not an online platform release.

## 2. Version Goal

v2.9 unifies the local Studio experience across Project Home, Novel, Tavern,
World, Cross-Mode, Script / Mods, Providers, Quality, Debug / Replay, Settings,
Privacy, and Diagnostics surfaces.

The release goal is better discoverability, safer local privacy messaging,
clearer setup flows, and more consistent loading / empty / error / disabled
states. It does not change World Engine authority, LLM authority, Provider
Gateway authority, save authority, import authority, or module execution
boundaries.

## 3. New UI / UX Capabilities

- Unified local navigation for Project Home, Novel, Tavern, World, Cross-Mode,
  Script / Mods, Providers, Quality, Debug / Replay, and Settings.
- Redesigned Project Home with local-only status, mode cards, Provider and
  Quality summaries, privacy summary, recent safe activity, and quick actions.
- Mode landing surfaces for Novel, Tavern, World, Cross-Mode, Script / Mods,
  Providers, Quality, Debug / Replay, and Settings.
- Local Status Bar with safe project, backend, provider, quality, debug, and
  local-only summaries.
- Shared UI building blocks for cards, badges, local-only notices, feature
  summaries, risk markers, validation status, and disabled states.
- Local Help / Onboarding panels that explain the three-mode workflow,
  Provider setup, Mods and permissions, Quality Gate, Cross-Mode proposals, and
  privacy/secrets handling.
- Local Diagnostics Export UI with safe preview and explicit debug-export
  confirmation.
- Lightweight v2.9 UI safety regression checks.

## 4. Behavior Changes

- v2.9 makes local-first behavior explicit in the UI: no account system, no
  cloud sync, no online marketplace, and no remote package auto-download are
  presented as near-term product flows.
- Debug / Replay and Diagnostics surfaces now communicate debug gating more
  clearly.
- Provider setup no longer presents plaintext API-key entry as a normal UI
  path; users are guided toward `api_key_env` or `secret_ref`.
- Normal diagnostics and export surfaces default to safe summaries and filtering
  rather than raw debug payloads.
- Error text is routed through safer formatting and redaction helpers.

## 5. Frontend Changes

- `frontend/src/App.tsx` now contains v2.9 local shell, navigation, status,
  mode landing, Project Home, diagnostics, settings/privacy, provider, module,
  quality, cross-mode, and help/onboarding UI surfaces.
- `frontend/src/styles.css` adds lightweight design tokens and v2.9 layout /
  navigation / status styles. No large UI framework was introduced.
- `frontend/src/api.ts` adds frontend API-client hardening helpers:
  `ApiError`, `safeFetch`, `parseJsonSafe`, `getErrorMessageSafe`,
  `isApiDisabledError`, and `isDebugDisabledError`.
- `frontend/package.json` adds the v2.9 UI safety check script.
- `frontend/scripts/check-v29-ui-safety.mjs` provides lightweight static checks
  for local-first UI, no plaintext API-key field, no online marketplace entry,
  and key v2.9 surfaces.

## 6. API Usage Changes

No backend API route changes are required for v2.9.

Frontend API usage is safer:

- errors are normalized through safe helpers;
- debug-disabled and API-disabled states can be recognized by the UI;
- secret-like values, authorization headers, raw environment text, hidden fact
  markers, raw prompts, raw `state_deltas`, stack traces, and sensitive local
  paths are redacted from user-facing error messages.

Diagnostics export in v2.9 is a local UI safe-preview/export surface built from
safe frontend state. If future backend diagnostics export endpoints are added,
they must repeat server-side filtering and must not rely on frontend filtering
alone.

## 7. Project Home Changes

Project Home now acts as a local dashboard:

- project name and local-only status;
- Novel, Tavern, World, Script / Mods, Provider, Quality, Debug / Replay, and
  Settings cards;
- Provider configured / missing summary;
- Quality Gate status summary;
- privacy summary stating that API keys are not stored in projects, exports
  filter secrets, and cloud sync is not implemented;
- quick actions for core local workflows.

Project Home does not display API keys, raw local sensitive paths, hidden facts,
NPC secrets, debug memory, or raw `state_deltas`.

## 8. Navigation Changes

Unified Navigation exposes:

- Project Home;
- Novel;
- Tavern;
- World;
- Cross-Mode;
- Script / Mods;
- Providers;
- Quality;
- Debug / Replay;
- Settings.

Navigation uses the existing local state-router model rather than adding a new
router or backend authority. Debug / Replay is shown with debug-gated state.
Mature Module is not promoted as a main navigation destination and remains
inside Settings / Tavern boundary-related surfaces.

## 9. Provider UX Changes

Provider setup now emphasizes safe local configuration:

- supported setup paths include OpenAI, OpenAI-compatible, local HTTP, relay,
  mock, and local stub profile styles;
- setup copy explains provider types and routing hints;
- UI accepts `api_key_env` / `secret_ref` metadata rather than plaintext API-key
  entry;
- Provider pages avoid rendering secrets, raw environment values, or provider
  secret bodies.

Provider Gateway remains the only model entry point. UI changes do not expand
LLM authority.

## 10. Module Browser UX Changes

Script / Mod and Module Browser surfaces now provide clearer local package
context:

- package type categories for Script Pack, World Extension, Character Pack,
  Prompt Pack, Provider Pack, Narrative Style Mod, RP Profile Mod, Action Mod,
  and Rule Module;
- risk badges;
- permission summaries;
- compatibility summaries;
- certification and Quality Gate summaries;
- local-only messaging;
- explicit no-online-marketplace, no-remote-auto-download, and no-arbitrary-code
  execution guidance.

v2.9 does not introduce an online module marketplace or remote package download.

## 11. Quality / Cross-Mode Dashboard UX Changes

Quality Dashboard now presents safer, more actionable local summaries:

- overall status;
- blocker, error, and warning counts;
- category summaries for Project, World, Novel, Tavern, Cross-Mode, Provider,
  Mods, Modules, and RP / Mature;
- safe issue summaries and suggested actions.

Cross-Mode Dashboard now summarizes:

- draft count;
- proposal count;
- pending review count;
- conflict count;
- recent audit items;
- direction lanes between Novel, Tavern, and World;
- validation / confirmation state for proposal review.

These dashboards do not display hidden target details, raw `state_deltas`, API
keys, provider secrets, or debug-only payloads in normal views.

## 12. Privacy / Diagnostics UX Changes

v2.9 adds clearer local privacy and diagnostics messaging:

- API keys are read through environment variables or local secret references;
- API keys are not stored in project files;
- exports filter secrets by default;
- mature/private content remains hidden and excluded from normal exports by
  default;
- debug data is gated by `ENABLE_DEBUG_API`;
- Diagnostics Export defaults to safe summaries and excludes `.env`, API keys,
  provider secrets, hidden facts, mature/private content, debug memory, raw
  prompts, and raw `state_deltas`;
- debug export requires explicit confirmation and debug API enablement.

No report upload, cloud sync, telemetry, account flow, or online diagnostics
service is introduced.

## 13. Known Limitations

- v2.9 is not a complete frontend rewrite; `frontend/src/App.tsx` remains large.
- Some older panels still rely on surrounding context for disabled/error
  explanations.
- Confirm UX remains distributed through existing confirmation helpers and
  warnings rather than a full accessible modal system.
- Some quick actions are lightweight entry points or disabled placeholders,
  not new business workflows.
- Debug / Replay remains present in the local shell and should become more
  clearly collapsible/debug-only in later polish.
- Vite reports a non-blocking large chunk-size warning after build.
- v2.9 uses TypeScript build, static UI safety checks, and pytest static
  integration checks; no browser/E2E framework was added.
- v2.9 does not add account systems, cloud sync, online marketplace, remote
  package auto-download, multiplayer collaboration, or new large gameplay
  systems.

## 14. Upgrade Notes From v2.8

- No save migration is required for v2.9 UI-only changes.
- Existing v2.8 World Engine, Provider Gateway, Script / Mod Platform, advanced
  module, RP, and Mature boundaries remain in force.
- Provider profiles should continue to use `api_key_env` or `secret_ref`.
- Do not expect account, cloud sync, online marketplace, remote package
  registry, or online platform workflows in v2.9; those are deferred to
  long-term optional directions.
- Run the standard checks after upgrading:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v29-ui
```

Observed v2.9 acceptance verification:

- `python -m pytest`: `1687 passed`
- `cd frontend && npm.cmd run build`: passed

## 15. Recommended v3.0 Direction

The recommended v3.0 direction is **Local Desktop Studio Polish**.

Suggested priorities:

- make Debug / Replay more clearly collapsible and debug-only by default;
- introduce a reusable accessible confirm dialog for dangerous actions;
- improve older disabled/error states with next-step guidance;
- split the largest frontend panels into smaller local components;
- add lightweight accessibility smoke checks;
- convert more generic JSON previews into purpose-built safe summary cards;
- keep local-first privacy, Provider Gateway, World Engine, StateDelta,
  EventLog, visibility, and LLM boundaries unchanged.

## Boundary Statement

v2.9 UI changes do not change the World Engine fact boundary. The World Engine
remains the source of truth. UI changes do not allow direct `GameState`
mutation, do not bypass validation/apply flows, do not expand LLM authority, do
not display API keys, and do not show hidden/debug data in normal UI.
