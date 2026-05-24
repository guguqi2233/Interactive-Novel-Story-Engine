# v3.6 Optimization Readiness Report

## Readiness Verdict

**Ready with Non-blocking Gaps**

The project is ready to move into v3.6 Local Performance & Accessibility Polish. The current v0.1-v3.5 capability stack appears integrated, tested, documented, and boundary-safe enough to begin optimization work rather than feature completion work.

The remaining gaps are not missing core product capabilities. They are routine optimization targets, fixture/tooling cleanup, and legacy checklist tuning.

## Required Conditions for v3.6

| Condition | Status | Notes |
| --- | --- | --- |
| v0.1-v3.5 features have no critical gap | Passed | Capabilities are present, integrated, or covered by successors. |
| Backend pytest passes | Passed | `1768 passed in 137.56s`. |
| Frontend build passes | Passed | Build succeeded with a non-blocking chunk-size warning. |
| Provider Connectivity is available and fake-provider tested | Passed | Provider connection/model discovery/sync paths are covered by pytest; no real provider tests were run. |
| Debug/Replay cannot modify GameState | Passed | Debug/replay surfaces are documented and implemented as observational. |
| Normal UI does not show hidden/debug/raw StateDelta data | Passed | v3.1-v3.5 frontend checks and audits cover normal-view boundaries. |
| No real API/provider tests | Passed | Tests use fake/mock/local provider paths. |
| No onlineization entry | Passed | No account, cloud sync, online marketplace, remote package download, API resale, online RP, online writing, or online play entry was found as an implemented near-term feature. |
| Provider secrets remain redacted | Passed | ProviderProfile uses `api_key_env` / `secret_ref`; transient key persistence/redaction is covered. |
| Mod execution boundary remains safe | Passed | Action Mods remain declarative; Rule Modules remain contract-only; arbitrary code plugins are not enabled. |

## Optimization Targets for v3.6

- Frontend bundle and chunk review, especially the large production chunk reported by Vite.
- Large EventLog and Timeline Replay virtualized rendering.
- Large Provider model list performance.
- Provider connection status cache and refresh behavior.
- Provider capability matrix performance.
- Quality dashboard large report rendering and filtering.
- Search/filter performance across Novel, Tavern, World, Authoring, QA, and Provider views.
- Keyboard shortcuts for common local studio workflows.
- Focus management for dialogs, wizards, debug gates, safe apply, backup/restore, and provider setup.
- Accessibility labels and descriptions for icon-heavy controls.
- Reduced-motion support for replay, dashboards, and panels.
- Large backup/restore/diagnostics progress UI.
- Large authoring package navigation and editor section indexing.
- Component splitting for high-density UI currently concentrated in `frontend/src/App.tsx`.

## Must-Fix Before v3.6

No release-blocking must-fix item was found.

Resolved v3.6 pre-cleanup items:

- Stable sample project and package fixture paths now exist for manual `project_quality_gate` and `mod_quality_gate` runs.
- The older v2 release checklist secret scanner now distinguishes test/redaction fake-key fixtures from production-path potential keys.
- A minimal local `mods/safe_content` fixture exists for mod quality gate checks.
- `docs/QUALITY_GATE_FIXTURES.md` documents stable fixture commands and direct `app.tools` invocations that require `PYTHONPATH=backend`.

## Recommended v3.6 Scope

v3.6 should remain an optimization and accessibility release, not a new platform expansion. Recommended scope:

- Performance polish for large local datasets: EventLog, StateDelta lists, timeline replay, model profiles, quality reports, module reports, backups, and diagnostics.
- Accessibility polish across all major studios: Novel, Tavern, World, Authoring/Mod, QA/Debug/Replay, Provider, and Desktop Studio.
- UI responsiveness and clarity: empty/error/disabled states, long-running operation progress, filter toolbars, keyboard navigation, and safe status summaries.
- Provider UI polish: model list caching, capability matrix scalability, status refresh ergonomics, and clearer safe diagnostics.
- Debug/QA scalability: virtualized viewers, safe redaction previews, large report summaries, and gated raw-detail affordances.
- Release tooling polish: stable fixtures, checklist false-positive reduction, and documented local commands.

v3.6 should not add accounts, cloud sync, online marketplace, remote package download, arbitrary code plugins, real provider CI calls, telemetry upload, or any feature that changes the World Engine / StateDelta / EventLog / Provider Gateway boundaries.

## Final Recommendation

Proceed to v3.6 planning and implementation as **Local Performance & Accessibility Polish**. No feature-completion blocker was found, and the current evidence supports treating v3.6 as an optimization stage.
