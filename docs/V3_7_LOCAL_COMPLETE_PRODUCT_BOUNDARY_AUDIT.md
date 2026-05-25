# v3.7 Local Complete Product Boundary Audit

Verification Date: 2026-05-25

Scope: v3.7 Local Complete Product boundary review for World Engine authority,
StateDelta/EventLog, Cross-Mode apply, Authoring/Mod safety, Debug/Replay,
Provider authority, and normal UI visibility. This audit is read-only with
respect to business code and tests; no real provider, LLM, upload, account,
cloud sync, marketplace, or remote package workflow was used.

Evidence reviewed:

- `AGENTS.md`
- `docs/V3_7_ROADMAP.md`
- `docs/V3_7_FULL_INTEGRATION_REVIEW.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `backend/app/core/state_delta.py`
- `backend/app/core/event_log.py`
- `backend/app/core/game_loop.py`
- `backend/app/platform/cross_mode.py`
- `backend/app/platform/tavern_studio.py`
- `backend/app/platform/novel_studio.py`
- `backend/app/engine/action_registry.py`
- `backend/app/engine/action_mod_validator.py`
- `backend/app/engine/gameplay_modules.py`
- `backend/app/llm/provider_gateway.py`
- `frontend/src/App.tsx`
- `frontend/src/desktopUi.tsx`
- `frontend/src/errorBoundary.tsx`

Latest integration context from `docs/V3_7_FULL_INTEGRATION_REVIEW.md`:

- `python -m pytest`: `1795 passed`
- `cd frontend && npm.cmd run build`: passed
- Frontend `check:*`: 44 passed and 9 failed
- Current v3.7 blockers are product/static check failures, not confirmed
  World Engine, StateDelta/EventLog, Provider, Debug, or Mod boundary bypasses.

## Passed Items

| Check | Status | Evidence |
| --- | --- | --- |
| World Engine remains the fact source | Passed | `docs/WORLD_ENGINE.md` keeps `GameState` as authoritative state; `backend/app/core/game_loop.py` applies rule results through `StateDelta`. |
| UI does not directly modify `GameState` | Passed at current evidence level | Normal UI actions call backend APIs and product/readiness/checklist surfaces are safe-summary/observation oriented. No v3.7 product dashboard/checklist path was found that directly mutates active `GameState`. |
| LLM does not directly modify `GameState` | Passed | `ProviderGateway` explicitly does not build prompts, apply world state, or inspect hidden data; providers only produce text/JSON through routed calls. |
| World changes go through `StateDelta` / `EventLog` | Passed | `GameLoop` applies deltas through `apply_delta`; Cross-Mode confirmed apply requires `state`, `event_log`, and `state_deltas` together and appends an EventLog entry. |
| Novel -> World remains draft/proposal/validation/apply | Passed | Cross-Mode service validates drafts and builds apply plans requiring confirmation; validation rejects GameState/apply-delta-like payloads in draft content. |
| Tavern -> World remains proposal/validation/apply | Passed | Tavern proposals validate target refs, reject secret/StateDelta material, block direct quest completion through RP promises, and remain proposal-only. |
| World -> Novel does not modify `EventLog` / `GameState` | Passed | `EventLogToNovelDraftService.preview_import` reads visible event summaries and filters hidden/non-player-visible events; it creates Novel draft content, not world events or state. |
| Authoring Safe Apply does not modify active `GameState` directly | Passed at current evidence level | World Engine docs and Authoring/Mod workflow docs keep authoring draft/candidate/proposal flows separate from active runtime state; safe apply remains validation/dry-run/confirm bounded. |
| Mods do not execute arbitrary code | Passed | Action mod validation rejects `execute_code`; package manifests forbid executable entry point kinds; module permissions treat code execution as forbidden. |
| Action Mods route through `ActionRegistry` / `StateDelta` / `EventLog` | Passed | `ActionRegistry` registers declarative mod actions; gameplay module boundary checks require StateDelta and Event for runtime module actions. |
| Rule Modules remain contract-only | Passed | Gameplay module policy blocks direct GameState mutation, direct database writes, secret reads, network access, LLM adjudication, visibility bypass, and missing StateDelta/Event paths. |
| Debug/Replay are observation-only | Passed | v3.5/v3.6 debug/replay UI is gated; docs and UI copy state Replay does not write EventLog or state, and StateDelta views are DebugGate controlled. |
| Provider is not a world judge | Passed | `ProviderGateway` routing can affect provider/model selection, wording, latency, and formatting only; LLM/provider output is not authoritative world state. |
| `visible_state` remains normal UI safe source | Passed | World UI/readiness copy keeps normal player-facing panels bound to `visible_state` and safe summaries; backend exposes typed `visible_state` responses. |
| Hidden facts / NPC secrets do not enter normal UI | Passed at current evidence level | Normal UI copy and audit surfaces consistently state hidden facts, NPC secrets, debug memory, raw prompts, and raw StateDelta are excluded from normal views. |

## Boundary Regressions

None confirmed.

No release-blocking boundary regression was found in the reviewed World Engine,
StateDelta/EventLog, Cross-Mode, Provider Gateway, Debug/Replay, or Mod/Action
paths. The current v3.7 release blockers recorded in the full integration
review are frontend product/static check failures and wording/checklist hygiene,
not demonstrated runtime boundary bypasses.

## Medium-risk Issues

1. **Frontend v3.7 product checks are not clean.**
   `docs/V3_7_FULL_INTEGRATION_REVIEW.md` records 9 failing frontend checks.
   The most boundary-adjacent failures are v3.7 workflow checks that flag
   API-key/transient-key terminology outside the expected safe exclusion
   wording, plus the privacy/safety review check missing the exact `no hidden
   fact text` exclusion copy. This is a release readiness issue because users
   should see unambiguous product-level boundary language.

2. **v3.0 UX token failure still affects the all-checks release gate.**
   `check:v30-ux` reports a missing `Desktop Packaging` completion token. This
   is not a direct boundary bypass, but it keeps the full frontend check suite
   from being green and should be resolved before v3.7 final acceptance.

3. **Cross-Mode confirmed apply remains a sensitive backend path.**
   The reviewed implementation requires explicit confirmation and applies
   supplied deltas through `apply_delta` before appending an EventLog record.
   This satisfies the boundary, but it should stay covered by focused tests so
   future UI/product polish cannot call it without validation, dry-run, and
   confirmation.

## Non-blocking Follow-ups

- Tighten v3.7 product UI wording so all workflow and privacy/safety check
  scripts recognize the intended exclusions for API keys, transient keys, hidden
  facts, NPC secrets, debug memory, raw prompts, raw outputs, and raw
  `state_deltas`.
- Keep Cross-Mode apply tests focused on `explicit_confirm`, validation status,
  StateDelta application, and EventLog audit records.
- Continue to keep authoring/import/package previews non-executing and
  separated from active runtime sessions.
- Consider documenting release-profile expectations for `ENABLE_DEBUG_API`
  defaults so local development and packaged local use remain clear to users.
- During v3.7 acceptance, rerun the full frontend `check:*` suite after fixing
  the product/static check failures.

## Release Decision

Boundary-specific decision: **No high-risk boundary regression found.**

v3.7 release decision: **Not ready for final release/tag yet.** The boundary
audit itself does not identify a World Engine, StateDelta/EventLog, Provider,
Debug, or Mod release blocker, but `docs/V3_7_FULL_INTEGRATION_REVIEW.md`
records failing frontend product/static checks. v3.7 should proceed to final
acceptance only after those check failures are fixed and the full verification
suite is rerun.
