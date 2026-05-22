# v2.9 UI Accessibility / Usability Audit

## Verdict

Pass with no release-blocking accessibility or usability issue found.

This audit reviewed the v2.9 Local UI / UX Foundation surfaces in the frontend, including the app shell, unified navigation, Project Home, mode landing pages, Provider setup, Module Browser, Quality Dashboard, Cross-Mode Dashboard, Settings / Privacy, Diagnostics Export, shared state components, and existing authoring/debug panels.

v2.9 materially improves wayfinding and local privacy clarity. The remaining issues are mostly polish debt from the older monolithic UI and should be handled in v3.0+ UI polish slices rather than blocking v2.9.

## Scope Reviewed

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/scripts/check-v29-ui-safety.mjs`
- `backend/tests/test_v29_ui_regression.py`
- `docs/V2_9_LOCAL_APP_SHELL_REVIEW.md`
- `docs/V2_9_UI_PRIVACY_VISIBILITY_AUDIT.md`

## Passed Items

1. **Major pages have titles**
   - The main app has a top-level product title.
   - Studio Home, Project Shell, Prompt Lab, World landing, authoring editors, Quality panels, Cross-Mode, Module Browser, Settings / Privacy, and diagnostics surfaces use `PageHeader`, `h2`, `h3`, or card headings.

2. **Major action buttons use clear labels**
   - Primary buttons use direct command labels such as Refresh, Start, Save Draft, Create Session, Validate, Certify, Quality Gate, Preview Chapter Draft, Build Apply Plan, Export local diagnostics JSON, and Run Coverage.
   - Provider setup buttons distinguish Validate, Status, Save Safe Profile, and Load Profiles.

3. **Disabled states have some explanation**
   - v2.9 adds `DisabledState`.
   - Debug export explains `ENABLE_DEBUG_API`.
   - Playtest and scenario regression panels include disabled API notices.
   - Several empty states explain what to load or run next.

4. **Error states are safe and visible**
   - `ErrorPanel` is used widely and sanitizes error content.
   - API client hardening redacts sensitive details before display.
   - Error states are visible in Studio Home, Provider, Settings, Authoring, Play, Quality, and Debug panels.

5. **Empty states usually include next-step hints**
   - Project, saves, validation, playtests, manuscripts, Tavern sessions, World health, content coverage, playtest, scenario regression, and authoring panels commonly use `EmptyState` with follow-up detail.

6. **Danger actions have confirmation in many established flows**
   - Save deletion, migration apply, graph save with warnings, authoring deletes, mod/archive flows, and other destructive authoring edits use `confirmDangerousAction` or explicit copy.

7. **Apply / import / export states are visible**
   - Migration apply confirms.
   - Package import/apply copy is explicit in the dangerous-action map.
   - Diagnostics debug export requires explicit confirmation.
   - Export surfaces explain filtering policies.

8. **Local-only / privacy state is clear**
   - Unified navigation, Project Home, Help / Onboarding, Settings / Privacy, SecretSafeNotice, and Diagnostics Export repeat local-only and secret-safe state without introducing online flows.

9. **Debug gated state is clear**
   - Unified navigation labels Debug / Replay as enabled or gated.
   - Diagnostics export requires `ENABLE_DEBUG_API`.
   - Debug panels show "debug disabled" when backend debug APIs are unavailable.

10. **Mature disabled state is clear**
    - Mature settings show disabled/default-off status.
    - Tavern landing states Mature Module is disabled by default.
    - Mature export is displayed as default off unless explicitly enabled.

11. **Provider setup explains `api_key_env`**
    - Provider setup copy explicitly says API keys are never entered in the frontend.
    - Provider cards explain `api_key_env` / `secret_ref`.
    - The form intentionally lacks a plaintext API key field.

12. **Module permission risk is understandable**
    - Module Browser shows local-only/no-marketplace/no-download/no-code-execution copy.
    - Risk badges, permission summaries, dangerous permissions, compatibility, certification, and quality status are exposed in safe summaries.

13. **Quality Gate blockers are easier to locate**
    - v2.9 adds a Quality Gate Dashboard with overall status, blocker count, warning count, category cards, and suggested safe issue routing.
    - Existing detailed quality panels still show blockers and recommended actions.

14. **Cross-Mode proposal state is easier to understand**
    - Cross-Mode Dashboard shows draft/proposal/pending/conflict/audit/timeline counts.
    - Direction lanes state that validation and confirmation are required before apply.

15. **No release-blocking information overload**
    - Project Home and new landing sections improve first-glance clarity.
    - Existing older panels remain dense, but the new shell provides safer top-level summaries before the dense views.

## High-Risk Usability Issues

None found.

No issue was found that would cause users to unknowingly expose secrets, bypass local/debug/mature boundaries, or mistake RP/UI actions for direct World Engine mutation.

## Medium-Risk Usability Issues

1. **The debug side panel remains visually prominent**
   - Debug / Replay is gated, but the older debug panel can still feel close to normal play UI.
   - This is not a privacy blocker because access depends on debug API gating, but it can confuse users about normal vs debug data.

2. **Some disabled buttons rely on surrounding context**
   - Many disabled actions are clear from nearby text, but not every button has a direct inline explanation.
   - Examples include some authoring/editor controls disabled by `isBusy`, missing selection, or missing project.

3. **Error states do not always include next-step guidance**
   - Errors are redacted and visible, but several panels still show "Request failed" without a panel-specific suggestion such as "check ENABLE_DEBUG_API" or "refresh provider profiles."

4. **Apply/import/export confirmation is not fully unified**
   - Confirmations exist in many dangerous flows, but v2.9 still uses browser confirm-style flows and distributed copy instead of a consistent `ConfirmDialog` UI.
   - This is acceptable for v2.9 foundation but should be polished later.

5. **Settings / Prompt Lab / Authoring remain dense**
   - v2.9 adds better entry surfaces, but older large sections still pack many tools into a single screen.
   - This may slow first-time users even though it does not block release safety.

## Low-Risk Issues

- Some quick-action buttons in landing cards are intentionally disabled placeholders. They communicate future or routed actions but are not yet full navigation controls.
- Some normal UI copy repeats safety exclusions like hidden facts and raw `state_deltas`. This is helpful for audits but may feel technical to non-developer users.
- Button labels are mostly clear, but iconography and keyboard-focused affordances are still minimal.
- There is no dedicated automated accessibility test suite yet; v2.9 relies on TypeScript build, static UI regression checks, and manual audit.

## Recommendations

1. In v3.0 Local Desktop Studio Polish, make Debug / Replay visually collapsible by default while preserving explicit access.
2. Replace distributed `confirmDangerousAction` calls with a unified accessible `ConfirmDialog` when the UI is ready for a broader component pass.
3. Add panel-specific next-step guidance to common `ErrorPanel` usages.
4. Extend `DisabledState` usage to more disabled buttons, especially missing-project, missing-selection, API-disabled, and busy states.
5. Continue breaking dense Studio / Authoring / Prompt Lab panels into smaller local-first task groups.
6. Add a lightweight accessibility smoke check later for heading order, button names, and focusable disabled/gated states if a test framework is introduced.

## Release Blocking Assessment

Not blocking v2.9 release.

The v2.9 UI foundation provides clear major titles, improved local navigation, safe empty/error states, understandable privacy/debug/mature status, and better Project/Mode/Quality/Cross-Mode summaries. Remaining issues are medium/low polish work and fit the planned v3.0+ local UI polish direction.
