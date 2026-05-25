# v3.7 Local Complete Product Usability Audit

Verification Date: 2026-05-25

Scope: v3.7 Local Complete Product usability review for first-run onboarding,
Project Home, Provider setup, model assignment, Novel/Tavern/World workflows,
Cross-Mode proposal review, Authoring/Mod, QA/Debug/Replay, Backup/Restore,
Diagnostics/Export, Settings, and product error/empty/disabled states.

This audit is documentation-only and read-only with respect to business code and
tests. No real provider, LLM, upload, account, cloud sync, marketplace, or
remote package workflow was used.

Evidence reviewed:

- `docs/V3_7_ROADMAP.md`
- `docs/V3_7_FULL_INTEGRATION_REVIEW.md`
- `frontend/src/App.tsx`
- `frontend/src/desktopUi.tsx`
- `frontend/src/providerUi.tsx`
- `docs/PRODUCT_GUIDE.md`

Latest integration context from `docs/V3_7_FULL_INTEGRATION_REVIEW.md`:

- `python -m pytest`: `1795 passed`
- `cd frontend && npm.cmd run build`: passed
- Frontend `check:*`: 44 passed and 9 failed
- The current release blockers are product/static frontend check failures, not a
  confirmed runtime usability crash or missing local product entry point.

## Passed Items

| Area | Status | Usability Evidence |
| --- | --- | --- |
| First-run flow clarity | Passed | `FirstRunOnboardingFlow` provides a 13-step local complete product tour, skip/finish controls, direct jump actions, progress indicator, and local-first/privacy summaries. |
| Project Home next-step guidance | Passed | Product Home/status panels expose project readiness, local health, Provider, Quality, Backup, Diagnostics, and navigation actions with safe summaries. |
| Provider setup readability | Passed | Provider surfaces show local setup, profile validation, supported provider types, missing-secret guidance, safe cache/stale status, and no plaintext key workflow. |
| Model assignment readability | Passed | Provider Model Assignment groups use cases by mode, shows capability warnings, supports save feedback, and states that no secret is stored. |
| Novel workflow understandability | Passed | Novel complete workflow checklist names manuscript, outline, chapter, scene, World import, export, provider, and quality readiness with next actions. |
| Tavern workflow understandability | Passed | Tavern checklist covers character library, RP/session/memory, mature default-off, Provider, Cross-Mode proposals, safety, export, and backup. |
| World workflow understandability | Passed | World checklist names start/play, suggested actions, visible-state panels, modules, save/load, Timeline/EventLog, Quality, Provider, and DebugGate. |
| Cross-Mode proposal clarity | Passed | Cross-Mode checklist and tour copy explain draft/proposal/review/apply, validation, audit, conflict review, and no direct GameState mutation. |
| Authoring / Mod workflow clarity | Passed | Authoring checklist covers editors, Module Browser, permissions, compatibility, certification, validation, import/export, dry-run, and Safe Apply. |
| Quality / Debug / Replay issue location | Passed with caveat | QA checklist covers Quality, Timeline Replay, EventLog, StateDelta, Visible vs Debug, Hidden Leak, Playtest, Module Stress, migration, diagnostics, and Safe Debug Export. Debug disabled text explicitly points to `ENABLE_DEBUG_API`. |
| Backup / Restore confidence | Passed | Backup/restore panels use dry-run-first wording, explicit confirmation, progress states, safe errors, and default exclusion summaries. |
| Diagnostics / Export filtering clarity | Passed | Diagnostics and export panels emphasize preview-first, local-only, redacted bundles and default exclusion of secrets, hidden/debug, mature/private, databases, logs, caches, and build outputs. |
| Settings completeness | Passed | Settings sections include General, Local Privacy, Providers, Export, Debug, Backup/Restore, Diagnostics, Mature Module, UI Preferences, Keyboard Shortcuts, and Quality Gate. |
| Error / Empty / Disabled state friendliness | Passed | Product state polish defines empty, error, and disabled guidance for Project Home, Novel, Tavern, World, Authoring, Provider, QA/Debug, Backup/Restore, Diagnostics, and Settings. |
| Information overload management | Partially passed | v3.6/v3.7 provide grouping, status badges, checklists, cards, next actions, and jump links; some product dashboards remain dense and should continue to be collapsed/progressive where possible. |

## High-risk Usability Issues

None confirmed in the inspected UI surfaces.

No direct high-risk usability issue was found that would make the local product
unusable by itself. The first-run tour, Product Home, readiness dashboards,
workflow checklists, Provider setup, Settings, QA/Debug, Backup/Restore, and
Diagnostics all expose next actions and safe explanatory text.

However, v3.7 should not be released yet because the full frontend check suite
is not green. Those failures are tracked below as release-relevant medium-risk
issues and must be fixed before final acceptance.

## Medium-risk Issues

1. **Frontend product/static checks still fail.**
   `docs/V3_7_FULL_INTEGRATION_REVIEW.md` records 9 failing frontend checks,
   including v3.7 workflow checks and the privacy/safety review check. These are
   release-blocking for v3.7 acceptance because the product requires all
   frontend checks to pass, even though they do not currently prove a broken
   runtime workflow.

2. **Security/privacy terminology can feel noisy in workflow checklists.**
   Several v3.7 workflow checks flag API-key/transient-key terminology outside
   the expected safe-exclusion wording. The UI intent is protective, but the
   repeated terminology can distract from task completion and should be tightened
   so users see clear action language instead of scanner-sensitive phrasing.

3. **Product readiness surfaces are information-dense.**
   Product Readiness, Acceptance Checklist, Lifecycle Checklist, workflow
   checklists, privacy review, and status/health panels are useful but dense.
   Users may need clearer default collapse, prioritization by blocker/warning,
   and "next best action" emphasis before v3.7 final polish.

4. **Provider setup remains concept-heavy.**
   Provider profiles, secret refs, model discovery, ModelProfile sync,
   capability matrix warnings, assignment by mode, stale cache, and slow
   provider warnings are all present. The flow is understandable for technical
   users, but non-technical users may benefit from a single guided sequence:
   configure profile -> test -> fetch/sync -> assign -> validate.

5. **QA / Debug / Replay has many expert surfaces.**
   Quality, EventLog, Timeline, StateDelta, Hidden Leak, Playtest, migration,
   diagnostics, and debug export are all available, but the number of panels can
   be intimidating. The current checklist helps, but blocker-first grouping
   should remain a v3.7 final polish target.

## Non-blocking Follow-ups

- Add more collapse-by-default behavior for large product readiness and
  acceptance sections, especially when most items are `ready`.
- Keep one prominent "next recommended action" near the top of Product Home.
- Make Provider setup read as a wizard sequence even when users enter through
  the dashboard.
- Add clearer "why disabled" text for any action that depends on project,
  Provider, model assignment, debug enabled, dry-run, or confirmation state.
- Keep Backup/Restore and Diagnostics copy calm and explicit about what will be
  included, excluded, and written before any confirm step.
- Continue refining wording so security/privacy exclusions remain clear without
  overwhelming users with repeated scanner-sensitive terms.
- After fixing the known check failures, rerun all frontend `check:*` scripts
  and update v3.7 acceptance documentation.

## Release Decision

Usability-specific decision: **No high-risk usability issue confirmed.**

v3.7 release decision: **Not ready for final release/tag yet.** The product is
usable in shape and most complete-product surfaces have clear next actions, but
v3.7 acceptance still requires the failing frontend product/static checks to be
fixed and rerun. Once those checks pass, this usability audit does not identify
an additional release-blocking usability issue.
