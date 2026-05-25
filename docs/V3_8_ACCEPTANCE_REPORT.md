# v3.8 Acceptance Report - Chinese Product UX Polish

## Verdict

Accepted: v3.8 Chinese Product UX Polish is ready for release.

v3.8 successfully moves the current product experience closer to a Chinese local desktop application for players and creators. The default Home experience now emphasizes writing novels, Tavern RP, and open-world play instead of presenting a developer dashboard. Debug, QA, Authoring, Diagnostics, Product Readiness, EventLog, and StateDelta tools remain available as advanced tools without occupying the first screen.

## Verification Date

2026-05-25

## Verification Commands

| Command | Result |
| --- | --- |
| `python -m pytest` | Passed: 1825 tests |
| `cd frontend && npm.cmd run build` | Passed |
| `cd frontend && npm.cmd run check:*` | Passed: 83 frontend check scripts |
| `python -m backend.app.tools.project_quality_gate examples/demo_local_narrative_project` | Passed |

Frontend build summary:

- Main App chunk: `App-roxgXq70.js`, 484.96 kB, gzip 122.79 kB.
- No Vite `>500 kB` main App chunk warning was reported.

## Scope Accepted

Accepted v3.8 scope:

- Chinese Product UX Polish.
- Product Home UX polish for Chinese players and creators.
- Three main mode entry polish: writing novels, Tavern RP, and open-world play.
- Backend unavailable recovery UX.
- First-run tour simplification.
- Provider setup UX and Provider/model explanation polish.
- Advanced Tools collapse UX.
- Chinese copy consistency pass.
- Empty, error, and disabled state polish.
- Local play flow polish.
- Project lifecycle and Demo project experience polish.
- Settings, privacy, backup, restore, diagnostics, QA, Debug, Replay, navigation, responsive, keyboard/focus/accessibility, inline help, and UI component cleanup polish.
- v3.8 product UX and integration regression checks.

Explicitly unchanged:

- World Engine authority.
- Provider Gateway semantics.
- StateDelta and EventLog contracts.
- Visibility boundaries.
- DebugGate requirements.
- Local-first product scope.

## Product UX Review

Passed:

- Home defaults to Chinese product copy.
- Home highlights `写小说`, `角色 RP`, and `大世界游玩`.
- Home does not default to Debug / Replay panels.
- Home does not render raw `state_deltas`.
- No-project state emphasizes open/create project, demo project, and Provider setup instead of a wall of disabled controls.
- Backend unavailable state provides a Chinese recovery flow with reconnect, startup guide, diagnostics, and settings entry points.
- Backend unavailable state uses a safe API base URL summary and redacted error text.
- Provider setup is presented as a Chinese step-by-step wizard.
- Provider/model explanation covers Base URL, API Key, env vars, `secret_ref`, `local_secret_ref`, model list, model assignment, JSON capability warnings, and relay-style compatible endpoints.
- Advanced tools are collapsible and do not dominate the default Home screen.
- Settings, backup, diagnostics, empty/error/disabled states, inline help, and local safety notices are Chinese-first.

Non-blocking polish left:

- Some advanced Debug and legacy Authoring panels still contain English technical labels.
- Some Provider terminology remains intentionally bilingual, such as Provider, Base URL, ModelProfile, and raw provider response.
- The `g+q` shortcut can still open the Debug drawer directly; this does not bypass DebugGate or mutate state, but could be softened in a later UX pass.

## Playability Review

Passed:

- Novel entry is visible and framed as writing workflow.
- Tavern entry is visible and framed as roleplay workflow.
- World entry is visible and includes start/continue guidance.
- Demo project entry is available for local tryout without real API keys.
- Missing project, missing Provider, missing model list, missing model assignment, no manuscript, no Tavern character, and no World save states provide clear next steps.
- Provider missing state points users to `配置模型服务`.
- Local play flow remains local and does not introduce accounts, cloud sync, online marketplaces, or remote package downloads.

Demo project validation:

- `examples/demo_local_narrative_project` passed project quality gate.
- Demo project is intended for fake/local_stub provider use and does not require a real API key.

## Boundary Review

Passed:

- API keys are not displayed in frontend UI.
- API keys are not intended to enter project files, frontend storage, logs, backups, diagnostics, or exports.
- Transient provider keys remain request/session scoped and are not persisted by the UI.
- Provider UI does not render Authorization headers or raw provider responses.
- Tests and frontend checks use fake/local_stub paths and do not call real providers.
- `DebugGate` remains the boundary for debug-sensitive StateDelta and raw debug details.
- Raw `state_deltas` do not appear in normal Home or normal player UI.
- Hidden facts, NPC secrets, debug memory, raw prompts, and raw outputs remain excluded from normal UI safe summaries.
- World actions continue to go through backend game/action APIs and the existing StateDelta/EventLog flow.
- LLMs remain language/rendering providers, not world judges.
- No account, cloud sync, online marketplace, online platform, API resale, or remote package auto-download entry point was accepted for v3.8.

## Known Limitations

- v3.8 is a UX polish release, not a new product architecture release.
- Some deep advanced-tool surfaces remain developer-oriented by design.
- v3.8 does not implement a full i18n framework; it uses Chinese-first product copy and local maintainable strings.
- Real LLM usage remains user-configured and user-triggered. Automated tests and CI remain fake/local only.
- Backend unavailable UX explains recovery but does not automatically start arbitrary backend processes.

## Acceptance Risks

No release-blocking acceptance risks remain.

Residual risks are non-blocking:

- Long-term maintainability of Chinese copy would benefit from a future lightweight string catalog.
- Some advanced panels may continue to feel technical until v3.9 or v4.0 polish.
- Provider UX is safer and clearer, but real provider configuration still depends on user-supplied valid Base URL and secrets outside project files.

## Recommended v3.9 Priorities

- Further Chinese copy unification in advanced Debug, QA, Authoring, and legacy panels.
- Make Novel, Tavern, and World main cards route more directly to their active workspace sections.
- Soften Debug keyboard shortcut behavior so it opens Advanced Tools guidance before expanding Debug.
- Add optional in-app guided recovery for backend startup that remains allowlisted and local-only.
- Continue reducing App shell size and extracting product UI components.
- Improve visual hierarchy and onboarding for first-time real Provider setup.

## Final Status

Final status: Accepted for v3.8 release.

The verified state satisfies the v3.8 goal: Chinese Product UX Polish that makes the local product feel more usable for everyday writing, roleplay, and world play, while preserving local-first privacy, Provider secret safety, DebugGate, visibility, StateDelta, EventLog, and World Engine boundaries.
