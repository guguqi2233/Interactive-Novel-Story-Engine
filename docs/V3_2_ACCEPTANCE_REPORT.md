# v3.2 Acceptance Report: Tavern Studio UI Pro

## Verdict

**Accepted with non-blocking documentation follow-up.**

v3.2 Tavern Studio UI Pro is accepted as a local-first RP workspace polish
release. The implemented scope adds Tavern workspace structure, character/profile
surfaces, chat and Multi-NPC UI, RP context panels, mature/boundary safety
surfaces, provider/prompt safe summaries, Cross-Mode review entries, export /
backup UX, local preferences, recovery drafts, reusable Tavern UI components,
and v3.2 regression coverage.

No high-risk release blocker was found after the v3.2 blocker fixes. Backend
tests and frontend production build pass.

## Verification Date

2026-05-23

## Verification Commands

```powershell
python -m pytest
```

Result:

```text
1725 passed
```

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
tsc -b passed
vite build passed
```

Additional v3.2 UI safety check:

```powershell
cd frontend
npm.cmd run check:v32-tavern-ui
```

Result:

```text
v3.2 Tavern UI regression check passed.
```

Note: Vite emitted the existing large chunk warning for the frontend bundle. This
is a non-blocking build warning, not a failed build.

## Scope Accepted

Accepted v3.2 scope:

- Tavern Studio UI Contract Review.
- Tavern Workspace Layout Polish through `TavernWorkspaceShell`.
- Character Card Library UI.
- Tavern Character / RP / Voice Profile Editor.
- Single Character Chat Pro.
- Multi-NPC Scene UI Pro.
- RP Memory Panel.
- Emotion Arc Panel.
- Relationship Tone Panel.
- Scene Mood Preset UI.
- Character Voice Lab UI.
- Boundary / Mature Settings UI Polish.
- Tavern Prompt / Provider UX Polish.
- Tavern Session Search / Tags / Filters as lightweight local UI/search support.
- Tavern -> World Proposal Review UX Pro.
- Tavern -> Novel Scene Draft UX Pro.
- World NPC -> Tavern Character UX Pro.
- RP Safety Dashboard.
- Tavern Session Export / Backup UX.
- Tavern Local Preferences.
- Tavern Recovery / Unsaved Session UX.
- Tavern UI Component Cleanup through `frontend/src/tavernUi.tsx`.
- Tavern UI Regression Tests.
- v3.2 Integration Regression Tests.

Key implementation evidence:

- `frontend/src/tavernUi.tsx` defines the reusable Tavern workspace and RP UI
  components.
- `frontend/src/App.tsx` wires v3.2 Tavern panels into the local Studio UI.
- `frontend/src/api.ts` exposes v3.2 Tavern safe API wrappers/types.
- `backend/app/platform/tavern_studio.py` provides Tavern preferences,
  recovery, export, RP safety, prompt context, provider generation, and World NPC
  adapter support.
- `backend/app/main.py` exposes safe local Tavern endpoints and keeps
  world-changing flows behind existing backend boundaries.
- `backend/tests/test_v32_tavern_ui_pro.py` and
  `backend/tests/test_v32_integration_regression.py` cover v3.2 privacy,
  provider, export, Cross-Mode, and frontend token regressions.
- `frontend/scripts/check-v32-tavern-ui.mjs` checks the Tavern UI entry points
  and safety copy without calling real backends or providers.

## Boundary Review

### Tavern Workspace

`TavernWorkspaceShell` is available and renders a left navigation, central RP
workspace, safe right context panel, and bottom status surface. It communicates
local-only status, provider safe summary, and Mature Module default-disabled
state.

Loading, empty, error, and disabled states are present through existing shared
state components and Tavern-specific empty/disabled copy. Some controls can
still benefit from more granular inline disabled reasons, but this is not a
release blocker.

### Characters / Profiles

Character Card Library and Tavern Character Editor are available. RPProfile and
VoiceProfile surfaces use safe editable/profile summaries. Private persona and
authoring-only notes are not part of normal safe summaries and are labeled as
authoring-only where surfaced.

Character cards are treated as local structured data. v3.2 does not add remote
character-card downloads, online character markets, or character-card script
execution.

### Chat / Multi-NPC

Single Character Chat Pro and Multi-NPC Scene UI Pro are available. Generated
Tavern replies are stored as `TavernMessage` records only. They do not write
World `GameState` or `EventLog`.

Tavern reply generation and Multi-NPC reply generation route through Provider
Gateway abstractions when a provider is available. Provider failure in Multi-NPC
generation safely degrades to a local safe fallback instead of exposing provider
errors.

Prompt context construction uses safe summaries. Tests cover hidden fact, NPC
secret, mature memory, private persona, and raw state delta exclusions.

### Memory / Emotion / Relationship / Mood / Voice

RP Memory, Emotion Arc, Relationship Tone, Scene Mood Preset, and Character
Voice Lab panels are accepted as safe-summary v3.2 UI Pro surfaces. They
communicate that RP metadata affects Tavern expression/session context only and
does not become World fact authority.

`mature_only` memory is hidden from normal memory context and normal export by
default.

### Boundary / Mature / Provider

Boundary / Mature Settings communicate:

- Mature Module disabled by default.
- Mature export default off.
- Consent required.
- Unknown/minor scenes blocked.
- Provider policy must allow selected rating.

Provider/Prompt panel displays provider and prompt safe summaries only. It does
not expose API keys, raw env, provider secrets, raw prompts, hidden facts, or
NPC secrets.

### Cross-Mode

Tavern -> World remains proposal / validation / dry-run / explicit apply.
Tavern UI does not directly mutate `GameState`. Apply paths remain backend
validated and confirmed, and World changes continue to use `StateDelta` and
`EventLog`.

Tavern -> Novel creates safe Novel draft material and does not modify the
original Tavern session or World state.

World NPC -> Tavern player-safe mode excludes NPC secrets and player-unknown
facts. Apply-to-Tavern creates a Tavern draft only and does not modify the
source World NPC.

### Safety / Export / Quality

RP Safety Dashboard is available and uses safe issue rows. Tavern export /
backup preview and confirmed export exclude API keys, hidden facts, NPC secrets,
mature/private memory, debug data, raw prompts, and raw `state_deltas` by
default.

Quality and safety reports do not print hidden/mature text bodies in normal
views. Tests verify exports and prompt contexts do not include secret-like or
hidden/mature markers.

### Global Boundary

Accepted boundary status:

- Tavern Mode remains RP session / memory / proposal mode.
- Tavern UI does not directly modify `GameState`.
- World Engine remains the fact source.
- LLM use remains behind Provider Gateway / injected provider abstractions.
- API keys do not enter frontend, Tavern export, logs, prompt context, or v3.2
  tests.
- Hidden facts, NPC secrets, private persona, mature memory, debug memory, raw
  prompts, and raw `state_deltas` do not enter normal Tavern UI.
- v3.2 does not introduce accounts, cloud sync, online RP, online marketplace,
  remote character downloads, or remote package auto-download.
- Tests use mock/local provider paths and do not call real APIs.

## Known Limitations

- v3.2 is a local UI Pro release, not a full online RP platform.
- Mature Module remains disabled by default and v3.2 does not implement an
  age-verification service or online mature-content platform.
- Several RP panels are safe-summary surfaces rather than deep full-featured
  editors.
- Multi-NPC turn order is readable but still lightweight; a richer turn lane can
  be added later.
- RP Safety Dashboard is summary-level and can use richer drill-down links in a
  later release.
- Frontend bundle size still emits the existing Vite chunk-size warning.
- README/SPEC/WORLD_ENGINE/LLM_PROTOCOL still need the dedicated v3.2
  documentation sync pass before final release notes/tagging.

## Acceptance Risks

- Future deeper Tavern editors must continue using safe summaries and keep
  private/mature/hidden data out of normal UI.
- Future Tavern generation endpoints must route through Provider Gateway and add
  equivalent no-real-provider regression tests.
- Future Cross-Mode apply UX must keep validation and explicit confirmation
  mandatory.
- Future debug/authoring prompt previews must remain gated and redacted.
- Documentation should be synchronized so public docs accurately describe v3.2
  without overstating it as online RP, cloud sync, or a complete commercial RP
  platform.

## Recommended v3.3 Priorities

- v3.3 World Studio UI Pro.
- World Workspace Layout.
- Map / Quest / Inventory / Combat panels.
- Economy and Faction War dashboards.
- Timeline replay and debug-gated World inspection.
- World Quality and validation UX polish.
- Continue local-first privacy and visibility regression checks across World
  Studio surfaces.

## Final Status

**v3.2 acceptance status: Accepted.**

Required verification passed:

- Backend full test suite: passed.
- Frontend production build: passed.
- v3.2 Tavern UI regression check: passed.

No high-risk v3.2 release blocker remains. The only noted release-readiness
follow-up is documentation synchronization for v3.2 public docs and release
notes.
