# v3.8 Playability UX Audit

Verification date: 2026-05-25

Scope: v3.8 Chinese Product UX Polish surfaces that determine whether a user can start from Home and naturally enter Novel writing, Tavern RP, World play, Provider setup, project creation/opening, backend recovery, Demo experience, and advanced tools without being blocked by developer-console noise.

## Passed Items

1. Home has the three main entries.
   - The Chinese Home includes three primary mode cards for writing novels, Tavern RP, and open-world play.
   - The cards are grouped in the v3.8 main mode area and are intended to be visible as the primary product entry points.

2. Novel entry is clear.
   - The Novel card uses Chinese copy for writing novels, recent manuscript context, chapter writing, and opening Novel Studio.
   - Empty-flow guidance points users toward creating a manuscript when no manuscript exists.
   - If Provider/model setup is missing, the flow points users to configure the model service rather than leaving the entry as a dead disabled control.

3. Tavern entry is clear.
   - The Tavern card uses Chinese copy for role RP, recent RP sessions, character selection, and starting RP.
   - Empty-flow guidance points users toward creating/importing a character when no character exists.
   - Provider missing flow uses the same model-service CTA.

4. World entry is clear.
   - The World card uses Chinese copy for open-world play, current world/save status, and world play entry.
   - The Home includes `继续大世界` and `开始大世界` actions.
   - Empty-flow guidance points users toward starting a new world when no save exists.

5. World has start/continue actions.
   - The v3.8 Product Home check verifies both continue-world and start-world copy/actions.
   - World play still routes through backend game APIs in integration checks, rather than direct UI GameState mutation.

6. Missing Provider guides users to configure the model service.
   - Home and mode cards surface `配置模型服务` as the next action when Provider/model readiness is missing.
   - `ProviderMissingState` provides a product-level CTA instead of a silent failure.

7. Missing Project guides users to open/create a project.
   - No-project Home state emphasizes opening or creating a local project.
   - Mode cards present "available after opening/creating a project" context rather than a wall of disabled buttons.

8. Backend unavailable state guides recovery.
   - `BackendUnavailableState` provides a Chinese recovery card with reconnect, startup guide, diagnostics, and settings actions.
   - It redacts raw env, stack traces, API keys, and sensitive path details.

9. Demo project is available for experience.
   - Home exposes `体验 Demo 项目`.
   - Demo copy says no API key is required and that users can try writing, RP, and world play.
   - The demo uses fake/local_stub provider metadata and does not include real credentials, mature/private content, or upload behavior.

10. Debug/QA does not interfere with the first screen.
    - Debug / Replay, Quality, diagnostics, StateDelta, EventLog, and other developer surfaces are grouped under Advanced Tools.
    - Debug is default-closed and remains DebugGate-protected.
    - Home checks reject default Debug/Replay/StateDelta/EventLog surfaces.

11. Empty states include next steps.
    - v3.8 empty/error/disabled state polish covers missing project, missing Provider, backend unavailable, missing manuscript, missing character, missing save, and debug-disabled states.
    - The relevant copy is Chinese and points to the next usable action.

12. Disabled states do not form a noisy wall.
    - Product Home checks reject `DisabledState` and `disabled=` usage in the Home slice.
    - No-project and missing-provider conditions are handled through contextual next steps and CTAs.

## Playability Blockers

None found.

No release-blocking playability blocker was found for v3.8. The checked Home, mode cards, provider/project recovery, Demo entry, and advanced-tool placement support the intended "open and start writing/RP/world play" flow.

## Medium-risk UX Issues

None blocking.

Residual medium-risk area: this audit is based on source inspection and existing regression scripts. It does not include a fresh browser-rendered pass across multiple window sizes or simulated backend-down runtime behavior. The automated checks cover the required structural regressions, but a final release freeze should still include one rendered smoke test.

## Non-blocking Follow-ups

1. Add a browser-rendered smoke test for Home at a narrow window size to verify all three main mode cards remain visible and readable.
2. Add a scripted backend-down UI smoke test that clicks reconnect/startup guide/diagnostics/settings actions.
3. Add fixture-driven checks for "no manuscript", "no Tavern character", and "no World save" rendered states, not only source tokens.
4. Continue reducing remaining English-only empty-state copy in deeper authoring/debug panels; this does not block the default playability flow.

## Verification Commands and Results

Commands run:

```powershell
cd frontend
npm.cmd run check:v38-product-home
npm.cmd run check:v38-local-play-flow
npm.cmd run check:v38-demo-project-experience
npm.cmd run check:v38-advanced-tools-collapse
npm.cmd run check:v38-state-polish
```

Results:

- `check:v38-product-home`: passed.
- `check:v38-local-play-flow`: passed.
- `check:v38-demo-project-experience`: passed.
- `check:v38-advanced-tools-collapse`: passed.
- `check:v38-state-polish`: passed.

## Release Decision

Ready for v3.8 release from the Playability UX perspective.

The v3.8 Chinese Home and local play flow provide clear entries for Novel, Tavern, and World; missing project/provider/backend states guide users to recovery actions; the Demo project is discoverable and safe; and Debug/QA developer tools no longer dominate the first screen.
