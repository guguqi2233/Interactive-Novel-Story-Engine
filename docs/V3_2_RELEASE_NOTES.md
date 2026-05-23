# v3.2 Release Notes: Tavern Studio UI Pro

## Version Name

**v3.2 Tavern Studio UI Pro**

## Version Goal

v3.2 improves Tavern Studio into a more usable local RP workspace. The release
focuses on local-first RP sessions, character/profile review, chat and
Multi-NPC workflows, RP safety visibility, safe Cross-Mode review, local export,
local preferences, and recovery UX.

Local-first remains the main direction. v3.2 does **not** add an online RP
platform, account system, cloud sync, online marketplace, remote character-card
download, remote package auto-download, or multi-user online chat.

Tavern Mode remains an RP session / memory / proposal mode. Tavern UI does not
directly modify World `GameState`, and the World Engine remains the source of
truth for facts. Provider Gateway remains the only model access boundary.
Mature Module remains disabled by default.

## New Tavern UI Capabilities

- Tavern Workspace Shell with left navigation, central RP workspace, safe right
  context panel, and bottom local/provider/mature status.
- Character Card Library for local Tavern character lists, safe summaries,
  creation/import entry points, and search/filter-oriented UI.
- Tavern Character / RP / Voice Profile Editor for public character fields,
  RP safe fields, voice safe fields, example dialogue, and boundary refs.
- Single Character Chat Pro with message list, timestamp/speaker badges,
  local input state, safety notes, provider status, and recovery entry.
- Multi-NPC Scene UI Pro with scene list, participant summaries, turn order,
  active speaker context, and safe next-reply generation.
- RP Memory, Emotion Arc, Relationship Tone, Scene Mood Preset, and Character
  Voice Lab safe-summary panels.
- Boundary / Mature Settings UI with mature disabled by default, consent
  required, unknown/minor block warnings, and mature export default off.
- Tavern Prompt / Provider panel showing prompt/provider safe summaries without
  API keys, raw prompts, provider secrets, hidden facts, or NPC secrets.
- Tavern -> World Proposal Review UX, Tavern -> Novel Scene Draft UX, and
  World NPC -> Tavern Character UX.
- RP Safety Dashboard, Tavern Session Export / Backup UX, Tavern Local
  Preferences, and Tavern Recovery / Unsaved Session UX.
- Tavern UI component cleanup in `frontend/src/tavernUi.tsx`.
- v3.2 Tavern UI and integration regression checks.

## Behavior Changes

- Tavern reply and Multi-NPC reply paths use Provider Gateway abstractions when
  provider context is available.
- Multi-NPC provider/schema failures safely degrade to a local safe fallback
  instead of surfacing provider internals.
- v3.2 Tavern errors return fixed safe messages for sensitive paths such as
  recovery, export, preferences, World NPC safe summary, and adaptation flows.
- Tavern export and backup UX defaults to filtering API keys, hidden facts, NPC
  secrets, mature/private memory, debug data, raw prompts, and raw
  `state_deltas`.
- Tavern recovery drafts are local-only and exclude prompt context, API keys,
  hidden facts, NPC secrets, mature/private content, and debug memory.

## Frontend Changes

- Added reusable Tavern UI components in `frontend/src/tavernUi.tsx`, including
  workspace, character/session cards, message bubbles, safety/status badges,
  safe summary panels, toolbar/status controls, and v3.2 panels.
- Updated `frontend/src/App.tsx` to render the Tavern Studio UI Pro workspace
  and panels.
- Updated `frontend/src/api.ts` with Tavern v3.2 types and safe API wrappers.
- Added `frontend/scripts/check-v32-tavern-ui.mjs`.
- Added `check:v32-tavern-ui` to `frontend/package.json`.

## Backend API Changes

v3.2 adds local safe-summary Tavern endpoints where existing APIs were not
enough for the UI:

- `GET /projects/{project_id}/world/npcs/safe-summary`
- `GET /projects/{project_id}/tavern/preferences`
- `PUT /projects/{project_id}/tavern/preferences`
- `GET /projects/{project_id}/tavern/recovery`
- `POST /projects/{project_id}/tavern/recovery`
- `POST /projects/{project_id}/tavern/recovery/{record_id}/restore`
- `DELETE /projects/{project_id}/tavern/recovery/{record_id}`
- `POST /projects/{project_id}/tavern/sessions/export-preview`
- `POST /projects/{project_id}/tavern/sessions/export`
- `GET /projects/{project_id}/tavern/rp-safety/latest`
- `POST /projects/{project_id}/tavern/rp-safety/run`

These APIs are local-only project APIs. They return safe summaries and do not
return API keys, raw env, provider secrets, hidden facts, NPC secrets,
mature/private memory, debug memory, raw prompts, or raw `state_deltas` in
normal responses.

## Tavern Workspace Changes

The Tavern workspace now presents a clearer local RP layout:

- left-side navigation for characters, sessions, Multi-NPC scenes, memory,
  voice, boundaries, safety, and export;
- central workspace for chat, scene, and management panels;
- right-side safe context panels;
- bottom status row for local-only, provider-safe, mature-disabled, and
  GameState boundary status.

## Character Card / Profile UI Changes

- Character Card Library shows local Tavern characters with safe status,
  tags/profile hints, and selection actions.
- Tavern Character Editor distinguishes public character fields from
  authoring-only/private fields.
- RPProfile and VoiceProfile surfaces use safe summaries.
- Character cards are local structured data. v3.2 does not execute scripts in
  character cards and does not add an online character marketplace or remote
  character download flow.

## Chat / Multi-NPC UI Changes

- Single Character Chat Pro shows safe Tavern messages with speaker/timestamp
  context and local input state.
- Multi-NPC Scene UI Pro shows participants, scene summaries, turn order, and
  active-speaker context.
- Generated replies are stored as Tavern messages only. They do not modify
  World `GameState` or write `EventLog`.
- Provider errors in Multi-NPC generation fall back safely without exposing
  provider internals.

## RP Memory / Emotion / Relationship / Mood / Voice UI Changes

- RP Memory Panel displays safe summaries and keeps mature-only memory hidden
  by default.
- Emotion Arc Panel and Relationship Tone Panel communicate that these metadata
  affect Tavern expression/session context only.
- Scene Mood Preset UI communicates that mood presets affect expression, not
  facts.
- Character Voice Lab is text-only in v3.2. It does not implement TTS and does
  not call a real provider by default.

## Boundary / Mature / Provider UX Changes

- Boundary / Mature Settings UI makes default-off mature policy explicit.
- Unknown/minor age block, consent requirement, mature export default-off, and
  provider policy requirements are shown as safety guidance.
- Provider/Prompt panel shows safe provider/prompt summaries only.
- API keys, provider secrets, raw env, raw prompts, hidden facts, NPC secrets,
  and mature/private memory are not shown in normal Tavern UI.

## Cross-Mode RP UX Changes

- Tavern -> World Proposal Review explains that RP content is not a World fact
  until validated and explicitly applied.
- Tavern -> World remains proposal / validation / dry-run / explicit apply.
- Tavern -> Novel Scene Draft uses safe message summaries and filters
  mature/private/hidden/debug content by default.
- World NPC -> Tavern Character UX supports player-safe review, excluding NPC
  secrets and player-unknown facts. Applying creates Tavern draft data only and
  does not modify the source World NPC.

## RP Safety / Export / Backup Changes

- RP Safety Dashboard shows safe issue rows for hidden leak risk, NPC knowledge,
  private persona, mature memory, provider safety routing, world consistency,
  proposal validation, and export safety.
- Tavern Session Export / Backup supports safe preview and confirmed local
  export.
- Normal export excludes API keys, hidden facts, NPC secrets, mature/private
  memory, debug data, raw prompts, and raw `state_deltas`.
- Export/backup does not upload data and does not implement cloud backup.

## Privacy / Boundary Changes

Accepted boundaries for v3.2:

- Tavern Mode is RP session / memory / proposal mode.
- Tavern UI does not directly modify World `GameState`.
- World Engine remains the fact source.
- World changes still require backend validation and existing
  `StateDelta` / `EventLog` flows.
- Provider Gateway remains the only model entry point.
- API keys do not enter frontend, Tavern export, logs, prompt context, tests, or
  release documentation.
- Hidden facts, NPC secrets, private persona, mature memory, debug memory, raw
  prompts, and raw `state_deltas` do not enter normal Tavern UI.
- Mature Module remains disabled by default.
- v3.2 does not add accounts, cloud sync, online RP, online marketplace, remote
  character downloads, or multi-user online chat.

## Known Limitations

- v3.2 is a Tavern UI Pro polish release, not a full online RP product.
- Several RP panels are safe-summary surfaces rather than deep full-featured
  editors.
- Multi-NPC turn order is lightweight; richer turn lanes can be added later.
- RP Safety Dashboard is summary-level and can use deeper drill-down links later.
- Character Voice Lab is text-only and does not implement TTS.
- v3.2 does not implement cloud backup, online RP, accounts, marketplace,
  multiplayer chat, remote character-card downloads, or a commercial RP service.
- Frontend build currently emits the existing Vite chunk-size warning.
- README/SPEC/WORLD_ENGINE/LLM_PROTOCOL still need the dedicated v3.2
  documentation sync pass before final release tagging.

## Upgrade Notes from v3.1

- Existing v3.1 Novel Studio UI Pro behavior is preserved.
- v3.2 adds Tavern UI surfaces and safe local APIs; it does not require account
  setup, cloud setup, or online RP services.
- Provider setup remains env/local-secret based. Do not paste API keys into the
  frontend.
- Existing Tavern data remains local project data. Tavern messages and memory do
  not become World facts unless a separate Tavern -> World proposal is validated
  and explicitly applied.
- Mature workflows remain opt-in and disabled by default.
- Recommended verification after upgrade:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v32-tavern-ui
```

## Recommended v3.3 Direction

v3.3 should focus on **World Studio UI Pro**:

- World workspace layout.
- Map / Quest / Inventory / Combat panels.
- Economy and Faction War dashboards.
- Timeline replay and debug-gated World inspection.
- World Quality and validation UX polish.
- Continued local-first privacy and visibility regression checks for World
  Studio.

