# v3.8 Chinese Product Usability Audit

Verification date: 2026-05-25

Scope: v3.8 Chinese Product UX Polish across Home, first-run tour, navigation/sidebar, Advanced Tools, Provider setup, three main mode entries, backend unavailable recovery, empty/error/disabled states, Settings, Backup/Diagnostics, and Product Guide / Offline Help.

## Passed Items

1. First screen looks like a Chinese product.
   - The Home surface uses Chinese product copy and prioritizes local creative/play actions.
   - The first screen is oriented around project continuation, writing novels, Tavern RP, world play, model service setup, and local safety summaries.

2. Mixed Chinese/English does not block understanding.
   - Core UI copy is Chinese.
   - Technical English terms such as Provider, Base URL, API Key, Debug, Quality Gate, and ModelProfile are accompanied by Chinese explanations.
   - Remaining English is mostly technical labels or deeper advanced-tool copy, not the default product path.

3. First-run tour is simplified.
   - The first-run tour is a 7-step product guide instead of a full developer checklist wall.
   - It shows the current step card, progress, Chinese Back/Next/Skip/Finish actions, and a collapsed "view all steps" area.
   - It does not default to Debug / Replay / StateDelta panels.

4. Navigation is clear.
   - Sidebar structure separates primary entries, common settings, and Advanced Tools.
   - Main entries are Home, Novel, Tavern, and World; common settings include Provider/model service, Settings, and Backup.
   - No-project state is a weak prompt, not a disabled navigation wall.

5. Advanced Tools are reasonably collected.
   - Cross-Mode, Authoring / Mods, Quality, Debug / Replay, Diagnostics, Export, Product Readiness, EventLog, StateDelta, and Hidden Leak surfaces are findable through Advanced Tools.
   - Advanced Tools are default-collapsed and Debug / Replay is not highlighted by default.

6. Provider setup is understandable for ordinary users.
   - Provider setup is presented as a Chinese wizard: choose service type, Base URL, key source, test connection, fetch models, assign models, finish.
   - Inline help explains model service, relay, Base URL, API Key location, model list, model assignment, JSON capability warnings, and possible costs.
   - Relay copy says it is compatible API configuration, not API resale or a specific vendor recommendation.

7. Three main play modes are prominent.
   - Home has large cards for writing novels, Tavern RP, and open-world play.
   - Each card includes status, next step, recent content, Provider model state, and a primary action.
   - World includes start/continue actions.

8. Backend unavailable recovery is clear.
   - The UI has a Chinese backend-unavailable recovery card with current API safe summary and actions for reconnect, startup guide, diagnostics, and settings.
   - Error details are redacted and do not show raw env, stack traces, API keys, or sensitive paths.

9. Error / empty / disabled states are friendlier.
   - Missing project, missing Provider, backend unavailable, missing manuscript, missing Tavern character, missing World save, and Debug disabled states point to next actions.
   - Home does not use a wall of disabled controls.

10. Settings is clear.
    - Settings sections are grouped as general, model service, model assignment, local privacy, export, debug, backup/restore, diagnostics, Mature Module, and UI preferences.
    - It does not present account/cloud/marketplace settings as near-term product features.
    - Privacy, Debug, export filtering, Mature default-off, and Provider safety copy are visible.

11. Backup/Diagnostics feels safer for users.
    - Backup/restore/diagnostics copy is Chinese.
    - Filtering summaries explain that API Key, `.env`, Provider secrets, debug raw data, raw `state_deltas`, mature/private content, logs, caches, databases, and build outputs are excluded by default.
    - The UI states local-only/no upload behavior and dry-run/confirm expectations.

12. Product Guide is Chinese-readable.
    - `docs/PRODUCT_GUIDE.md` is a Chinese offline manual.
    - It covers local-first behavior, first run, project lifecycle, real LLM/provider setup, model list/model assignment, Novel, Tavern, World, Cross-Mode, Authoring/Mod, Quality, Debug/Replay, Backup/Restore, Diagnostics/Export, API key safety, Mature default-off, unsupported online features, and FAQ.

13. Default UI no longer feels like an obvious developer console.
    - Product Home does not default to Product Readiness, Debug / Replay, EventLog, StateDelta, or full QA panels.
    - QA/Debug/Authoring remain available as advanced tools instead of dominating the first screen.

14. Information overload is reduced on the primary path.
    - Home uses mode cards, next-step suggestions, Provider status, Demo entry, and local safety summaries rather than exposing all subsystems at once.
    - First-run and advanced-tool sections are collapsed where appropriate.

## High-risk Usability Issues

None found.

No release-blocking usability issue was found for the v3.8 Chinese product experience.

## Medium-risk Issues

None blocking.

Residual medium-risk areas:

1. Some deeper advanced/editor/debug panels still contain English copy. This does not block the default Chinese Home / Novel / Tavern / World / Provider / Backup / Settings paths, but it remains polish debt.
2. The audit is based on static source checks and script evidence. It does not replace a browser-rendered visual pass across small windows, backend-down state, and no-project state.
3. Provider and advanced-tool pages still carry some technical terms by design. They are explained in Chinese, but new users may still benefit from more inline examples.

## Non-blocking Follow-ups

1. Continue translating deeper Authoring, Debug, and old validation empty states after v3.8.
2. Add a browser snapshot smoke test for Home, Provider setup, first-run tour, Settings, Backup, and backend unavailable states.
3. Add a short "术语表" section to the product guide for Provider, Base URL, API Key, ModelProfile, DebugGate, and Quality Gate.
4. Add a rendered no-project/no-provider/no-save fixture pass to confirm the UI does not visually feel disabled-heavy.
5. Review narrow-window Home screenshots before final freeze to catch visual overload that static checks cannot see.

## Verification Commands and Results

Commands run:

```powershell
cd frontend
npm.cmd run check:v38-product-ux
npm.cmd run check:v38-first-run-tour
npm.cmd run check:v38-navigation-sidebar
npm.cmd run check:v38-provider-setup-ux
npm.cmd run check:v38-settings-privacy-ux
npm.cmd run check:v38-state-polish
npm.cmd run check:v38-backup-diagnostics-ux
npm.cmd run check:v38-inline-guide
npm.cmd run check:v38-advanced-tools-collapse
```

Results:

- `check:v38-product-ux`: passed.
- `check:v38-first-run-tour`: passed.
- `check:v38-navigation-sidebar`: passed.
- `check:v38-provider-setup-ux`: passed.
- `check:v38-settings-privacy-ux`: passed.
- `check:v38-state-polish`: passed.
- `check:v38-backup-diagnostics-ux`: passed.
- `check:v38-inline-guide`: passed.
- `check:v38-advanced-tools-collapse`: passed.

## Release Decision

Ready for v3.8 release from the Chinese product usability perspective.

The default product path now reads as a Chinese local product rather than a developer dashboard: Home highlights writing, RP, and world play; the first-run tour is simplified; navigation is grouped; Provider setup is explained; backend recovery is actionable; Settings and Backup/Diagnostics are understandable; and Advanced Tools remain findable without overwhelming ordinary use.
