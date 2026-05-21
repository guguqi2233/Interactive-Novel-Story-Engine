# v2.4 Acceptance Report: Cross-Mode Bridge

## Verdict

Accepted for v2.4 release as a local Cross-Mode Bridge MVP.

v2.4 establishes the shared draft/proposal/review/apply-plan/audit layer for
Novel, Tavern, and World. It preserves the core boundary: Novel and Tavern do
not directly modify `GameState`; World Mode remains the fact source; actual
World-changing apply paths must use validation, explicit confirmation,
`StateDelta`, and `EventLog`.

## Verification Date

2026-05-22

## Verification Commands

```bash
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: 1614 passed.
- `npm.cmd run build`: passed. Vite reported the existing chunk-size warning
  for the frontend bundle.

## Scope Accepted

Accepted v2.4 scope:

1. Cross-Mode Bridge Core Schema:
   `CrossModeDraft`, `CrossModeProposal`, `CrossModeReview`,
   `CrossModeApplyPlan`, `CrossModeAuditRecord`, status/direction enums.
2. Cross-Mode Draft / Proposal Repository:
   `CrossModeRepository` stores artifacts under `project/cross_mode/`, rejects
   unsafe ids/paths, rejects provider-secret-like artifact content, and supports
   save/load/list/audit operations.
3. Novel -> World Draft Pipeline:
   creates `CrossModeDraft`/proposal-ready draft artifacts without writing
   content packs or `GameState`.
4. Novel -> World Draft Review UI:
   Project Shell exposes a Cross-Mode panel for generating/reviewing draft
   summaries and validation status.
5. World -> Novel Chapter Pipeline:
   safe preview from event/timeline summaries, raw `state_delta` filtering, and
   confirmed Novel draft writes only.
6. World -> Novel Chapter UI:
   frontend preview surface is present in the Cross-Mode panel and states that
   raw deltas/hidden events are excluded.
7. Tavern -> World Proposal Apply Flow:
   apply plans require confirmation, dry-run performs no World writes and no
   repository write, service-level confirmed apply uses `StateDelta` and records
   `EventLog` when runtime state/EventLog/deltas are provided.
8. Tavern -> World Proposal Review UI:
   frontend review surface can build apply plans and communicates confirmation
   requirements.
9. World NPC -> Tavern Character Sync Review:
   compare/proposal endpoints produce safe diff/proposal metadata and do not
   overwrite World NPCs.
10. Tavern Session -> Novel Scene Draft:
    creates cross-mode draft artifacts from tavern-safe message summaries and
    requires confirmation to write Novel draft material.
11. Novel Character -> Tavern Character Draft:
    creates safe Tavern draft artifacts from Novel/character refs without
    modifying character profiles or World state.
12. Shared Timeline Cross-Mode Backend:
    `CrossModeTimelineService` builds normal-safe merged timeline views and
    filters hidden/debug/authoring-only entries by default.
13. Shared Timeline Cross-Mode UI:
    frontend Cross-Mode panel displays timeline entries from safe backend data.
14. CrossModeLink Review Dashboard:
    backend review reports broken/duplicate/stale/hidden-risk links, and the
    frontend displays safe counts/status.
15. Cross-Mode Conflict Detection:
    detector reports duplicate/stale/hidden-risk link conflicts with normal
    safe summaries.
16. Cross-Mode Conflict Resolution UI:
    frontend/backend support reviewed/ignored/fix-draft semantics without
    editing source data directly.
17. Cross-Mode Validation:
    validates links, drafts, proposals, apply plans, provider/profile safety
    patterns, hidden-target risks, and conflict blockers.
18. Cross-Mode Quality Gate:
    Project Quality Gate supports `include_cross_mode` and fails on blockers
    such as missing confirmation, hidden leak risk, broken critical links, and
    provider-secret artifacts.
19. Cross-Mode Import / Export:
    Project package manifest includes cross-mode sections and export mode;
    normal export excludes secret-like content and raw debug markers; import
    dry-run checks schema, checksums, zip slip, forbidden material, and refs.
20. Cross-Mode Audit Trail:
    audit records are appended for key bridge operations and normal summaries
    redact hidden/secret-like content.
21. v2.4 Integration Regression Tests:
    `backend/tests/test_v24_cross_mode_bridge.py` covers schemas, repository,
    pipelines, apply semantics, import/export, validation, quality gate, audit,
    and boundary behavior.

## Boundary Review

World authority:

- World Engine remains the fact source.
- `GameState` is not modified by Novel/Tavern draft/proposal creation.
- Service-level Tavern -> World confirmed apply uses `apply_delta()` and
  appends an `Event` when runtime state/EventLog/StateDeltas are supplied.
- The public HTTP apply-confirmed route currently records explicit audit
  confirmation and returns `world_state_applied: false`; it does not pretend to
  perform a full runtime World apply.

Novel/Tavern boundaries:

- Novel -> World creates drafts/proposals only.
- Tavern -> World creates proposal/apply-plan/audit records unless a validated
  runtime service path is invoked.
- Tavern -> Novel and World -> Novel write only Novel draft material after
  explicit confirmation.
- World NPC -> Tavern sync creates safe diff/proposal/draft data and does not
  overwrite NPCs.

Visibility and secrets:

- Normal reports, timeline views, validation output, quality-gate output,
  audit summaries, and frontend Cross-Mode panels exclude hidden facts, NPC
  secrets, debug memory, raw `state_deltas`, API keys, raw env, and provider
  secrets.
- CrossMode artifacts reject provider-secret-like content at schema/storage
  boundaries.
- Project export normal mode excludes `.env`, API keys, provider secrets,
  debug memory, raw `state_deltas`, databases, logs, caches, and build output.

LLM boundary:

- Cross-mode validation, conflict detection, import/export, audit, and quality
  gate are deterministic and do not use an external LLM judge.
- Cross-mode draft generation is draft/proposal-only.
- Provider Gateway / `LLMProvider` remains the only model boundary.
- Tests use fake/mock/local providers and do not call real APIs.

Frontend boundary:

- Cross-Mode UI shows safe summaries/counts/statuses.
- It does not directly mutate `GameState`.
- It does not display API keys, raw env, hidden target contents, debug memory,
  or raw `state_deltas` in normal Cross-Mode panels.

## Known Limitations

1. The public Tavern -> World `apply-confirmed` route is audit-confirmation
   oriented. Full runtime World apply requires a backend service caller to
   provide validated StateDeltas plus runtime `GameState` and `EventLog`.
2. CrossMode conflict and validation normal reports rely on `safe_summary`
   conventions. Current detectors produce safe text, but future rules must
   preserve that discipline.
3. World -> Novel preview can accept caller-provided safe event summaries. It
   filters forbidden markers, but a stronger future version should bind preview
   directly to server-side EventLog/session lookup.
4. CrossMode import/export filtering is strong for secrets and raw debug
   markers, but it is not a full semantic hidden-lore classifier.
5. Frontend Cross-Mode review surfaces are MVP panels, not full multi-pane
   professional merge tools.
6. Conflict resolution can mark/ignore/create fix draft, but it does not
   automatically repair source data.

## Acceptance Risks

No high-risk blocker remains.

Residual risks:

- Misunderstanding the HTTP `apply-confirmed` route as a complete runtime World
  apply path.
- Future code placing hidden prose into fields named `safe_summary`.
- Future debug export or debug timeline exposure accidentally bypassing local
  debug gating.
- Overloading CrossMode export with semantically sensitive normal fields that
  do not match secret/debug markers.

These risks are documented and non-blocking for v2.4 MVP acceptance.

## Recommended v2.5 Priorities

1. Runtime World Apply Hardening:
   add a fully session/save-bound apply API that loads World state, validates
   proposal eligibility, applies StateDeltas transactionally, appends EventLog,
   and writes rollback/audit metadata.
2. Safe Payload Types:
   introduce stricter `SafeText` / `NormalViewPayload` helpers for reports,
   timeline entries, audit summaries, and UI previews.
3. Server-Side World -> Novel Source Binding:
   derive safe event summaries from EventLog/session ids rather than accepting
   caller-provided summaries as the primary source.
4. CrossMode Review UX:
   expand the frontend review dashboard with typed detail renderers, stronger
   redaction, diff views, and clearer apply state.
5. Conflict Resolution Backend:
   add structured fix-draft types and validation for source/target conflict
   repairs.
6. Export Policy Hardening:
   add semantic visibility checks for normal/authoring/debug export modes.
7. Audit Trail Completeness:
   ensure all review, validation, import/export, quality-gate, and future apply
   operations append normalized audit records.

## Final Status

v2.4 is accepted as implemented.

Final status: PASS.

The project is ready for v2.4 release-note generation and final freeze checks,
with the documented limitations carried forward as v2.5 hardening priorities.
