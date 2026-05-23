# v3.1 Acceptance Report: Novel Studio UI Pro

## Verdict

**Accepted with documented limitations.**

v3.1 is accepted as a local-first Novel Studio UI Pro foundation. The current
HEAD provides the Novel workspace shell, authoring panels, local draft/version
services, writing session support, search/filtering, export/import safety
surfaces, Novel quality UI, preferences, recovery UX, and regression coverage
without changing World Engine authority, Provider Gateway authority, or
local-first privacy boundaries.

One release-documentation gap remains: `docs/V3_1_ROADMAP.md` was not present
during acceptance. This does not block the verified runtime/test result, but it
should be filled before final v3.1 release freeze/tag.

## Verification Date

2026-05-23

## Verification Commands

```powershell
python -m pytest
```

Result: **passed**.

```text
1719 passed in 112.98s
```

```powershell
cd frontend
npm.cmd run build
```

Result: **passed**.

```text
tsc -b && vite build
✓ built in 1.12s
```

Vite emitted the existing non-blocking chunk-size warning for the main bundle.

Additional v3.1 UI safety/import check:

```powershell
cd frontend
npm.cmd run check:v31-novel-ui
```

Result: **passed**.

```text
v3.1 Novel UI regression check passed.
```

## Scope Accepted

### Novel Workspace

- `NovelWorkspaceShell` is present and integrated into the frontend Novel
  surface.
- Manuscript dashboard, Novel navigation, safe context/sidebar sections, and
  local status messaging are present.
- Loading, empty, error, and disabled-state patterns are available through the
  shared local UI foundation and v3.1 Novel panels.

### Outline / Chapter / Scene

- Outline Tree Pro exists as a lightweight Novel panel for outline navigation
  and validation-oriented copy.
- Chapter Editor Pro is integrated around the existing plain text/markdown
  chapter editing flow.
- Scene Cards Board is present and renders safe scene card summaries.
- Dirty/save/recovery UX is represented through local draft state, confirmation
  flows, draft recovery, and snapshot/restore services.
- Word count is represented in Novel UI summaries and editor status surfaces.

### Authoring Panels

- Character Arc Panel is present.
- Plot Thread / Foreshadowing Board is present.
- Timeline Link Panel is present.
- World Bible Sidebar is present.
- Normal UI surfaces use safe summaries and avoid hidden/private text.

### Draft / Search / Export

- `NovelDraftSnapshot` and `DraftVersionService` are implemented and tested.
- `WritingSessionState` and `WritingSessionService` are implemented and tested.
- `NovelSearchService` supports local search/filtering and excludes hidden
  normal-view content by default.
- Novel Export Wizard Pro is present in the frontend and export paths default
  to safe filtering.
- Backend export now filters non-normal chapters by default and excludes
  authoring notes, hidden refs, mature/private content, debug data, and secrets.

### Prompt / Provider / Quality

- Novel Prompt / Provider panel is present and displays provider/prompt safe
  summaries without API keys.
- Novel draft/rewrite/summary integration remains behind the provider boundary
  and is covered by v3.1 regression tests using mock/local provider behavior.
- Novel Quality Dashboard Pro is present and displays safe issue excerpts
  instead of hidden text or raw sensitive details.

### Cross-Mode

- World -> Novel import UX is present as a safe preview/import surface.
- World -> Novel preview does not modify `EventLog` or `GameState`.
- Novel -> World remains draft/proposal/validation/apply oriented through the
  Cross-Mode bridge and does not directly write World facts.
- Timeline/CrossMode links use safe summaries and avoid raw `state_deltas`.

### Regression Coverage

- Backend v3.1 coverage exists in:
  - `backend/tests/test_v31_novel_ui_pro.py`
  - `backend/tests/test_v31_integration_regression.py`
- Frontend v3.1 UI static regression check exists in:
  - `frontend/scripts/check-v31-novel-ui.mjs`
- Full backend suite and frontend build passed during acceptance.

## Boundary Review

- Novel Mode remains a draft/authoring mode.
- Novel UI does not directly modify `GameState`.
- World Engine remains the source of authoritative facts.
- World-changing flows remain bound to backend validation, `StateDelta`, and
  `EventLog`.
- Novel -> World still uses draft/proposal/validation/apply boundaries.
- World -> Novel reads safe EventLog/timeline summaries and does not rewrite
  World state.
- Novel LLM use remains behind Provider Gateway / provider abstractions.
- API keys are not displayed in Novel UI, export output, logs, diagnostics, or
  test fixtures.
- Hidden facts, NPC secrets, debug memory, raw prompts, and raw `state_deltas`
  are excluded from normal Novel UI surfaces.
- Draft snapshots reject non-normal hidden/authoring targets and store only
  user draft text plus safe metadata.
- Search skips hidden/private normal-view content by default.
- Export defaults exclude authoring notes, hidden refs, mature/private content,
  debug data, and secrets.
- No account, cloud sync, online writing, online publishing, marketplace, or
  remote package download entry was added as a v3.1 current feature.
- Tests use mock/local provider paths and do not call real external APIs.

## Known Limitations

- `docs/V3_1_ROADMAP.md` is missing in the current HEAD and should be added
  before final v3.1 release freeze/tag.
- v3.1 is not a rich-text editor, collaborative editor, cloud writing product,
  online publishing platform, DOCX/EPUB export suite, or full publishing system.
- Outline Tree Pro is a lightweight local UI foundation, not a full drag/drop
  IDE-grade outliner.
- Scene Cards Board does not implement complex kanban drag/drop.
- World Bible Sidebar and Timeline Link Panel expose safe summaries and links,
  not full world-editing tools.
- Export Wizard Pro supports local Markdown/TXT oriented workflows; online
  publishing and cloud sync are out of scope.
- Novel Quality Dashboard does not auto-fix issues and does not use an external
  LLM judge.
- Some deeper authoring/debug API surfaces remain intended for local trusted
  authoring workflows and must stay gated and documented separately from normal
  Novel UI.

## Acceptance Risks

- Missing `docs/V3_1_ROADMAP.md` is the primary release checklist gap.
- The frontend build still emits a non-blocking bundle-size warning; this is not
  a v3.1 blocker but should be revisited during future frontend polish.
- Several v3.1 "Pro" UI surfaces are intentionally lightweight foundation
  panels. Future work should deepen interactions without weakening visibility,
  LLM, export, or World Engine boundaries.
- Continued care is required to keep future authoring/debug views from
  reintroducing hidden fact, raw prompt, raw `state_delta`, or provider-secret
  exposure.

## Recommended v3.2 Priorities

v3.2 should proceed as **Tavern Studio UI Pro** while preserving the same
local-first and visibility boundaries:

- Tavern workspace shell and session navigation.
- Character card/session/multi-NPC scene entry polish.
- RP memory, emotion, relationship tone, scene mood, and voice profile panels.
- Boundary profile and mature-module settings clarity, with mature disabled by
  default.
- Tavern quality/safety dashboard and RP leak checks.
- Tavern export/privacy polish.
- Cross-mode Tavern -> World and World -> Tavern review UX.
- Tavern UI regression checks for no secrets, no hidden facts, and no direct
  `GameState` mutation.

Carry-forward Novel follow-ups:

- Add `docs/V3_1_ROADMAP.md`.
- Deepen outline tree editing and export preview.
- Add richer Novel quality issue navigation.
- Consider code-splitting to reduce frontend bundle size.

## Final Status

**PASS for v3.1 system acceptance, with the roadmap documentation gap noted.**

The current project passes full backend tests and frontend production build.
The v3.1 Novel Studio UI Pro scope is integrated as a local-first authoring UI
foundation, and no high-risk blocker remains in the verified implementation.
Before final v3.1 release tagging, add the missing `docs/V3_1_ROADMAP.md` and
rerun the release freeze checks.
