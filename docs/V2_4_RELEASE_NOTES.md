# v2.4 Release Notes: Cross-Mode Bridge

## 1. Version Name

v2.4 Cross-Mode Bridge

## 2. Version Goal

v2.4 introduces a local bridge layer between Novel Studio, Tavern Studio, and
World Mode. It lets project data move through explicit draft, proposal, review,
validation, apply-plan, and audit records without bypassing World Engine
authority.

v2.4 is not an automatic merge system. Novel and Tavern remain authoring modes,
and World Mode remains the runtime fact engine.

## 3. New Features

- Cross-mode artifact contracts for drafts, proposals, reviews, apply plans,
  audit records, status enums, and direction enums.
- `CrossModeRepository` for project-local bridge storage under
  `project/cross_mode/`.
- Novel -> World draft pipeline and review surface.
- World -> Novel chapter/scene draft preview and confirmed Novel draft apply.
- Tavern -> World proposal review, apply-plan generation, dry-run, rejection,
  and explicit audit confirmation.
- World NPC -> Tavern Character sync review as safe diff/proposal/draft data.
- Tavern Session -> Novel Scene draft flow.
- Novel Character -> Tavern Character draft flow.
- Cross-mode timeline view.
- CrossModeLink review dashboard.
- Cross-mode conflict detection and fix-draft workflow.
- Cross-mode validation service and CLI.
- Project Quality Gate integration with `include_cross_mode`.
- Cross-mode import/export support in project packages.
- Cross-mode audit trail.
- v2.4 integration regression tests.

## 4. Behavior Changes

- Project Quality Gate can include cross-mode checks.
- Project package export includes cross-mode sections by default when present.
- Cross-mode normal reports and frontend views use safe summaries and omit
  hidden/debug/secret material.
- Cross-mode dry-run does not write World state and does not persist dry-run
  repository metadata.
- Public Tavern -> World `apply-confirmed` reports
  `world_state_applied: false` unless a runtime service path supplies
  validated StateDeltas plus World `GameState` and `EventLog`.

## 5. API Changes

New local authoring/studio endpoints under `/projects/{project_id}/cross-mode`:

- `POST /novel-to-world/draft`
- `POST /novel-to-world/validate`
- `GET /novel-to-world/drafts`
- `POST /world-to-novel/preview`
- `POST /world-to-novel/apply`
- `GET /world-to-novel/drafts`
- `POST /tavern-to-world/proposals/{proposal_id}/apply-plan`
- `POST /tavern-to-world/proposals/{proposal_id}/dry-run`
- `POST /tavern-to-world/proposals/{proposal_id}/apply-confirmed`
- `POST /tavern-to-world/proposals/{proposal_id}/reject`
- `POST /world-tavern/compare`
- `POST /world-tavern/sync-proposal`
- `POST /world-tavern/apply-to-tavern`
- `POST /world-tavern/create-world-draft`
- `POST /tavern-to-novel/preview`
- `POST /tavern-to-novel/apply`
- `POST /novel-to-tavern/character-draft`
- `GET /timeline`
- `GET /links`
- `POST /links/review`
- `PATCH /links/{link_id}`
- `POST /conflicts/detect`
- `GET /conflicts/latest`
- `POST /conflicts/{conflict_id}/mark-reviewed`
- `POST /conflicts/{conflict_id}/ignore`
- `POST /conflicts/{conflict_id}/create-fix-draft`
- `POST /validate`
- `GET /audit`
- `GET /audit/{audit_id}`

Quality Gate API:

- `POST /projects/{project_id}/quality-gate/run?include_cross_mode=true`

CLI:

```bash
python -m backend.app.tools.validate_cross_mode <project_path>
python -m backend.app.tools.project_quality_gate <project_path> --include-cross-mode
```

## 6. Frontend Changes

- Project Shell adds a Cross-Mode Bridge panel.
- Novel -> World Review supports source refs, draft type selection, draft
  generation, draft list, and validation.
- World -> Novel preview shows safe event/chapter draft payloads and states
  that raw `state_deltas` and hidden/debug events are excluded.
- Tavern -> World Apply Review can build apply plans and communicates explicit
  confirmation requirements.
- Cross-mode timeline, link review, conflict list, audit list, and validation
  summary are visible as MVP review panels.
- Normal UI does not display API keys, raw env, hidden target bodies, debug
  memory, or raw `state_deltas`.

## 7. Cross-Mode Schema Changes

Added contracts:

- `CrossModeArtifactBase`
- `CrossModeDraft`
- `CrossModeProposal`
- `CrossModeReview`
- `CrossModeApplyPlan`
- `CrossModeAuditRecord`
- `CrossModeArtifactStatus`
- `CrossModeDirection`
- `CrossModeValidationReport`
- `CrossModeTimelineView`
- `CrossModeConflictReport`
- `CrossModeLinkReviewReport`

Important rules:

- Draft/proposal artifacts are not facts.
- `CrossModeApplyPlan.requires_confirmation` defaults to `true`.
- Proposed StateDeltas are proposal metadata until a validated apply path
  consumes them.
- Normal summaries redact hidden/debug/secret-like material.

## 8. Cross-Mode Repository / Storage Changes

- Cross-mode files are stored under:

```text
project/
  cross_mode/
    drafts/
    proposals/
    reviews/
    apply_plans/
    audit/
    timeline_cache/
    conflicts/
```

- Repository ids are validated.
- Repository paths are constrained to the project root.
- Provider-secret-like content is rejected when storing cross-mode artifacts.
- Safe list/load operations support deterministic tests and review surfaces.

## 9. Novel / Tavern / World Interop Changes

- Novel -> World creates world-content draft/proposal records only.
- World -> Novel reads safe event/timeline summaries and writes only Novel
  draft material after explicit confirmation.
- Tavern -> World creates proposals and apply plans. A World-changing apply
  must use validated StateDeltas and EventLog.
- World NPC -> Tavern Character creates diff/proposal/draft data and does not
  overwrite NPCs.
- Tavern -> Novel creates Novel scene draft artifacts from tavern-safe message
  summaries.
- Novel -> Tavern creates Tavern character/RP/voice draft material from safe
  character refs.
- `CrossModeLink` remains a reference/review structure, not a fact conversion
  mechanism.

## 10. Validation / Quality Gate Changes

- Cross-mode validation checks links, drafts, proposals, apply plans,
  hidden-target risks, provider-secret artifacts, unvalidated proposals, and
  conflict blockers.
- Apply plans without confirmation are blockers.
- Provider secrets in artifacts are blockers.
- Project Quality Gate can include cross-mode validation, conflict detection,
  link review, export safety, and provider/profile safety.
- Normal validation and quality-gate output do not include hidden fact text.

## 11. Import / Export Changes

- `ProjectPackageManifest` includes `export_mode` and cross-mode sections.
- Normal export can include cross-mode drafts/proposals/reviews/apply plans and
  audit records.
- Cross-mode export excludes `.env`, API keys, provider secrets, raw debug
  memory, raw `state_deltas`, databases, logs, caches, build outputs, and
  secret-like text.
- Debug export requires an explicit debug flag.
- Import dry-run validates schema, checksums, unsafe paths, zip slip,
  forbidden debug material, and duplicate/missing entries.
- Import does not apply proposals and does not modify active `GameState`.

## 12. Audit Trail Changes

- Cross-mode operations append local audit records for draft creation,
  proposal creation, apply-plan creation, confirmed apply requests, rejection,
  validation, import/export, conflict detection, and quality-gate work where
  wired.
- AuditTrail complements World EventLog. It does not replace EventLog for
  runtime World changes.
- Normal audit summaries redact hidden/secret-like material.

## 13. Known Limitations

- v2.4 is a Cross-Mode Bridge MVP, not an automatic intelligent merge system.
- Public Tavern -> World `apply-confirmed` is audit-confirmation oriented and
  returns `world_state_applied: false`; full runtime World apply requires a
  service caller with validated StateDeltas, runtime `GameState`, and
  `EventLog`.
- Conflict resolution can mark reviewed/ignored or create fix drafts, but it
  does not automatically modify source data.
- Frontend Cross-Mode views are MVP panels, not full professional diff/merge
  tooling.
- World -> Novel preview can accept caller-provided safe summaries; future work
  should bind it more tightly to server-side EventLog/session lookup.
- Export filtering is strong for secrets and raw debug markers, but not a full
  semantic hidden-lore classifier.

## 14. Upgrade Notes from v2.3

- Existing v2.3 Tavern Studio and v2.2 Novel Studio data remain compatible.
- New CrossMode artifacts are stored under `project/cross_mode/`.
- Existing `CrossModeLink` data continues to be reference metadata only.
- Project Quality Gate may now be run with `--include-cross-mode`.
- Projects should keep provider profiles secret-free and continue storing only
  `api_key_env` references.
- No real API key is required for v2.4.
- Tests and local development should keep `LLM_PROVIDER=mock` or
  `local_stub`.

## 15. Recommended v2.5 Direction

Recommended v2.5 direction: **World Studio Review & Apply**.

Suggested priorities:

1. Harden a full runtime World apply API that loads target World session/save
   state, validates proposal eligibility, applies StateDeltas transactionally,
   appends EventLog, and records rollback/audit metadata.
2. Add stricter safe payload types for normal reports, timeline entries, audit
   summaries, and frontend preview payloads.
3. Bind World -> Novel import to server-side EventLog/session lookup.
4. Improve CrossMode review UI with typed diff panels and stronger redaction.
5. Expand conflict resolution into structured fix-draft workflows.
6. Add semantic visibility checks for normal/authoring/debug exports.
7. Continue local-first constraints. Do not move to online sync, online
   collaboration, marketplace, or arbitrary-code plugins until apply,
   visibility, export, and audit boundaries are more mature.

## Final Boundary Statement

LLM remains a language layer, not the world judge. Provider Gateway remains the
only model entry point. Novel/Tavern cannot directly modify World `GameState`.
Drafts/proposals require validation, apply requires explicit confirmation, and
World apply must go through `StateDelta` and `EventLog`.
