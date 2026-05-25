# v3.7 Playable Product Boundary Audit

Verification Date: 2026-05-25

Scope: v3.7 Local Playable Complete Product CN boundary review. This audit is based on local source inspection of the backend world loop, provider gateway, Cross-Mode services, debug/replay routes, authoring/mod import paths, mature policy defaults, frontend UI usage, and v3.7 check scripts. No real provider was called, no data was uploaded, and no business code was changed.

## Passed Items

1. UI does not directly modify backend `GameState`.
   - The playable World UI submits player text through the backend game input path and stores returned `visible_state` as frontend display state.
   - v3.7 frontend checks continue to guard against direct UI calls such as `setGameState`, `applyStateDelta`, or other direct world-state mutation helpers.

2. World play still goes through `/game/input` or backend action APIs.
   - `/game/input` calls `GameLoop.step(...)`, returns `visible_state`, narrative text, suggested actions, and turn information.
   - The frontend World action panel presents player input as a backend action flow, not as local state mutation.

3. `StateDelta` and `EventLog` boundaries are preserved.
   - `GameLoop.step(...)` resolves actions, applies state changes through `apply_delta`, and records resulting player/system events in `EventLog`.
   - EventLog and Timeline UI paths are read/inspect flows; they do not delete or rewrite authoritative events.

4. The LLM remains a parser/narrator, not a world judge.
   - `IntentParser` returns structured `PlayerIntent` only.
   - `Narrator` renders confirmed rule results and visible facts.
   - `ProviderGateway` routes safe payloads and does not apply world state, inspect hidden data, or grant provider authority over rules.

5. Novel -> World remains draft/proposal/validation/apply.
   - Novel-to-World paths create drafts/proposals and run validation. They do not directly mutate active World state.
   - Cross-Mode validation rejects unsafe hidden or raw state-delta style material in normal proposal flows.

6. Tavern -> World remains proposal/validation/apply.
   - Tavern-to-World proposals are validated before they can become ready.
   - Direct quest completion, state-delta text, mature/private leakage, and unsafe references are rejected or warned before apply planning.

7. Cross-Mode does not auto-apply.
   - Tavern-to-World apply plans require confirmation.
   - The public apply-confirmed route requires `explicit_confirm` and returns `world_state_applied: false` with `runtime_apply_required: true`, keeping active runtime apply separate from review.
   - v3.7 fixtures/checks use `auto_apply: false` and confirm-required metadata.

8. Debug and Replay are observation-only in the product UI.
   - Debug routes call the debug API gate and are disabled when debug is not enabled.
   - Timeline replay and replay dry-run use read models or copied state for inspection; they do not write back to the active game loop.
   - `StateDelta` raw inspection remains behind `DebugGate` in the QA/Debug UI.

9. Authoring does not directly modify active `GameState`.
   - Authoring and package flows use validation, preview, dry-run, and explicit confirmation.
   - Safe apply/package apply paths operate on authoring/package artifacts and do not directly mutate active runtime world state.

10. Mods do not execute arbitrary code by default.
    - Package manifests and import/export validation reject executable entry points and executable file suffixes.
    - Action Mods remain declarative and must go through `ActionRegistry` / `StateDelta` / `EventLog` boundaries.
    - Rule Modules remain contract-only.

11. Mature content is disabled by default.
    - Mature policy defaults to disabled.
    - Mature/private/debug export flags default to excluded.
    - Mature/private memory is not part of normal prompt, export, backup, or diagnostics flows by default.

12. Provider is not the world judge.
    - Provider choice can affect wording, latency, cost, and formatting only.
    - World facts, action success, module outcomes, `StateDelta` application, and `EventLog` authority remain local engine responsibilities.

## Boundary Regressions

None found.

No release-blocking regression was found in the playable product boundary review. The current v3.7 implementation preserves the core World Engine, `StateDelta`, `EventLog`, visibility, Provider Gateway, Cross-Mode, Debug/Replay, Authoring/Mod, and mature/private boundaries.

## Medium-risk Issues

1. Some debug rendering components rely on parent `DebugGate` placement.
   - Current usages of raw event/state-delta debug summaries are behind debug-gated sections.
   - Future hardening should consider component-level `debugEnabled` guards for raw debug renderers so accidental reuse in a normal route cannot expose raw data.

2. `TavernToWorldApplyService.apply_confirmed(...)` has an internal stateful path for runtime apply when a caller supplies `state`, `event_log`, and `state_deltas` together.
   - The current public project route does not pass those runtime objects and returns `world_state_applied: false`.
   - This is acceptable for v3.7, but future runtime apply wiring should keep validation, explicit confirmation, `StateDelta`, and `EventLog` checks at the backend boundary.

3. Product readiness/checklist UI repeats boundary status in several places.
   - This is not a boundary regression, but future v4.0 polish could centralize boundary summaries to reduce inconsistency risk.

## Release Decision

Pass.

v3.7 remains eligible as a Local Playable Complete Product from a boundary perspective. No high-risk playable product boundary blocker was found. The medium-risk notes are hardening follow-ups and do not block v3.7 release/tagging.
