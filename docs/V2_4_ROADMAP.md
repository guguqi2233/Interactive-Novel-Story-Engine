# v2.4 Roadmap: Cross-Mode Bridge

## Version Theme

Cross-Mode Bridge on top of the v2.1 `NarrativeProject` layer, v2.2 Novel
Studio MVP, and v2.3 Tavern Studio MVP.

## Goal

v2.4 builds the safe bridge layer between Novel, Tavern, and World. It should
let users convert, reference, review, validate, audit, and explicitly apply
cross-mode drafts and proposals without bypassing World Engine authority.

Novel and Tavern remain authoring modes. They can produce drafts, suggestions,
scene material, memory, and proposal records. World Mode remains the runtime
fact engine. Any World-changing apply flow must pass validation, require
explicit confirmation, produce `StateDelta`, record `EventLog`, and append an
audit trail.

This roadmap is a development plan, not an acceptance report.

## Explicit Non-Goals

- No complete Novel Studio Pro.
- No complete Tavern Studio Pro.
- No large World simulation expansion.
- No online sync.
- No online script marketplace.
- No arbitrary-code plugins.
- No direct Novel or Tavern mutation of `GameState`.
- No automatic authoritative fact creation from `CrossModeLink`.
- No LLM authority to decide whether a proposal takes effect.
- No draft/proposal validation bypass.
- No apply flow bypassing `StateDelta` or `EventLog`.
- No RP memory as World fact.
- No Novel draft as World fact.
- No cross-mode export containing `.env`, API keys, raw env, debug memory, raw
  `state_deltas`, provider secrets, logs, caches, databases, or desktop build
  outputs.

## Recommended Development Order

1. Bridge Foundation:
   - Cross-Mode Bridge Core Schema.
   - Cross-Mode Draft / Proposal Repository.
   - Cross-Mode Audit Trail.
   - Cross-Mode Validation.
2. Novel / World Bridge:
   - Novel -> World Draft Pipeline.
   - Novel -> World Draft Review UI.
   - World -> Novel Chapter Pipeline.
   - World -> Novel Chapter UI.
3. Tavern / World / Novel Bridge:
   - Tavern -> World Proposal Apply Flow.
   - Tavern -> World Proposal Review UI.
   - World NPC -> Tavern Character Sync Review.
   - Tavern Session -> Novel Scene Draft.
   - Novel Character -> Tavern Character Draft.
4. Shared Review, Timeline, and Conflict Handling:
   - Shared Timeline Cross-Mode Backend.
   - Shared Timeline Cross-Mode UI.
   - CrossModeLink Review Dashboard.
   - Cross-Mode Conflict Detection.
   - Cross-Mode Conflict Resolution UI.
5. Portability and Release Hardening:
   - Cross-Mode Quality Gate.
   - Cross-Mode Import / Export.
   - v2.4 Integration Regression Tests.

## Module Plan

### 1. Cross-Mode Bridge Core Schema

- Goal: define the shared contracts for drafts, proposals, review state,
  validation state, apply state, and audit metadata.
- Data structures: `CrossModeBridgeItem`, `CrossModeBridgeStatus`,
  `CrossModeBridgeType`, `CrossModeSourceRef`, `CrossModeTargetRef`,
  `CrossModeReviewState`, `CrossModeApplyPolicy`.
- API changes: none beyond future consumers; schemas must be serializable and
  safe-summary friendly.
- Frontend changes: none required in this slice.
- Tests: schema defaults, JSON serialization, status transitions, hidden refs
  excluded from safe summaries.
- Acceptance: bridge records can represent Novel/Tavern/World conversions
  without modifying `GameState`, `EventLog`, or content packs.

### 2. Cross-Mode Draft / Proposal Repository

- Goal: persist cross-mode drafts, proposals, review decisions, validation
  reports, and audit refs under the project workspace.
- Data structures: `CrossModeBridgeRepository`, bridge item indexes, safe
  summaries, repository validation result.
- API changes: repository-backed services for create/load/save/list/update.
- Frontend changes: none required in this slice.
- Tests: save/load/list, stable ordering, path traversal rejection, repository
  does not read `.env`, databases, logs, cache, `node_modules`, `dist`, or
  desktop outputs.
- Acceptance: bridge storage is local, deterministic, and separated from world
  saves and EventLog storage.

### 3. Novel -> World Draft Pipeline

- Goal: convert structured Novel material into World draft candidates without
  writing World content or runtime state.
- Data structures: `NovelWorldDraftRequest`, `NovelWorldDraftCandidate`,
  candidate validation summary, source Novel refs.
- API changes: preview/create endpoints for Novel-to-World draft candidates.
- Frontend changes: later review UI consumes candidates.
- Tests: character/plot/lore/timeline refs become candidates, invalid refs are
  rejected, no content-pack writes, no `GameState` mutation.
- Acceptance: Novel -> World creates validation-ready draft candidates only.

### 4. Novel -> World Draft Review UI

- Goal: provide a local review surface for Novel-derived World candidates.
- Data structures: frontend bridge item, candidate diff, validation warning,
  review decision.
- API changes: none beyond bridge repository and validation consumption.
- Frontend changes: candidate list, detail view, source refs, warnings,
  approve/reject/defer controls.
- Tests: build, empty state, invalid candidate warning display, no hidden text
  shown in normal view.
- Acceptance: users can review Novel-derived candidates without applying them.

### 5. World -> Novel Chapter Pipeline

- Goal: turn World EventLog/timeline material into Novel chapter draft
  proposals using player-visible or narrator-safe summaries only.
- Data structures: `WorldNovelChapterDraftRequest`,
  `WorldNovelChapterDraftProposal`, safe event summaries, excluded count.
- API changes: preview/create endpoints for World-to-Novel chapter drafts.
- Frontend changes: later UI consumes preview/apply-to-Novel-draft actions.
- Tests: preview no write, raw `state_deltas` excluded, hidden/debug events
  excluded, `EventLog` unchanged, `GameState` unchanged.
- Acceptance: World -> Novel reads World history safely and creates Novel draft
  material only.

### 6. World -> Novel Chapter UI

- Goal: provide a review UI for turning World timeline ranges into chapter
  draft proposals.
- Data structures: frontend event range selector, safe event summary,
  chapter draft preview, excluded event metadata.
- API changes: none beyond pipeline endpoints.
- Frontend changes: session/save selector, turn range controls, preview panel,
  apply-to-Novel draft confirmation.
- Tests: build, empty state, hidden/debug exclusion count, no raw deltas in UI.
- Acceptance: users can create Novel chapter drafts from World history without
  editing World state.

### 7. Tavern -> World Proposal Apply Flow

- Goal: add a safe explicit apply path for validated Tavern proposals.
- Data structures: `TavernWorldApplyRequest`, `TavernWorldApplyResult`,
  generated `StateDelta`, created `EventLog` refs, audit refs.
- API changes: apply endpoint for validated Tavern proposals with explicit
  confirmation.
- Frontend changes: consumed by proposal review UI.
- Tests: unvalidated proposals cannot apply, confirmation required, apply
  produces `StateDelta` and `EventLog`, hidden details excluded from normal
  result, rollback/failure preserves original state.
- Acceptance: Tavern -> World can affect World only through validated,
  explicit, auditable World Engine paths.

### 8. Tavern -> World Proposal Review UI

- Goal: provide a local review surface for Tavern proposals before validation
  and apply.
- Data structures: frontend proposal summary, validation report, apply preview,
  audit status.
- API changes: none beyond validation/apply endpoints.
- Frontend changes: proposal list, detail view, validation controls,
  approve/reject/defer/apply controls with explicit confirmation.
- Tests: build, disabled apply for invalid proposals, no hidden/private text in
  normal UI.
- Acceptance: users can review Tavern proposals and cannot apply invalid
  proposals by accident.

### 9. World NPC -> Tavern Character Sync Review

- Goal: review World NPC to Tavern Character adapter results and future sync
  candidates without overwriting NPCs.
- Data structures: `NpcTavernSyncCandidate`, safe NPC summary, authoring-only
  fields, sync warning.
- API changes: preview/list/review endpoints for adapter candidates.
- Frontend changes: side-by-side safe summary, hidden exclusion labels,
  create/update Tavern draft controls.
- Tests: player-safe mode excludes NPC secrets, authoring mode marks private
  fields, no NPC writes, no `GameState` mutation.
- Acceptance: World NPC sync creates Tavern drafts/references only.

### 10. Tavern Session -> Novel Scene Draft

- Goal: convert selected Tavern session messages into Novel scene draft
  proposals without importing hidden/private/debug context.
- Data structures: `TavernNovelSceneDraftRequest`,
  `TavernNovelSceneDraftProposal`, safe message summaries, excluded refs.
- API changes: preview/create endpoints for Tavern-to-Novel scene drafts.
- Frontend changes: message range selector and scene draft preview.
- Tests: preview no write, private persona/debug memory excluded, RP memory not
  treated as fact, Novel draft write requires explicit confirmation.
- Acceptance: Tavern session material can become Novel draft material only.

### 11. Novel Character -> Tavern Character Draft

- Goal: create Tavern character drafts from Novel/shared character profiles
  without changing Novel characters or World NPCs.
- Data structures: `NovelTavernCharacterDraftRequest`,
  `NovelTavernCharacterDraft`, profile mapping warnings.
- API changes: preview/create endpoints for Novel-to-Tavern draft conversion.
- Frontend changes: character picker, safe profile preview, create draft
  action.
- Tests: private notes excluded, hidden refs excluded, no World NPC writes, no
  `GameState` mutation.
- Acceptance: Novel characters can seed Tavern drafts safely.

### 12. Shared Timeline Cross-Mode Backend

- Goal: provide backend services for cross-mode timeline refs and safe merged
  timeline summaries.
- Data structures: `CrossModeTimelineEntry`, `TimelineSourceMode`,
  `CrossModeTimelineSummary`, hidden/debug exclusion metadata.
- API changes: timeline list/filter/link endpoints scoped to project and mode.
- Frontend changes: later UI consumes merged timeline data.
- Tests: stable sorting, hidden/authoring-only filtering, EventLog unchanged,
  broken refs reported.
- Acceptance: cross-mode timeline summaries are safe references, not state
  changes.

### 13. Shared Timeline Cross-Mode UI

- Goal: show Novel/Tavern/World timeline links in one local project surface.
- Data structures: frontend timeline row, source badge, visibility label,
  conflict marker.
- API changes: none beyond timeline backend.
- Frontend changes: filtered timeline view, source-mode tabs, safe detail
  drawer, hidden exclusion counts.
- Tests: build, hidden entries not rendered, broken refs shown safely.
- Acceptance: users can inspect cross-mode chronology without exposing hidden
  details.

### 14. CrossModeLink Review Dashboard

- Goal: centralize CrossModeLink review, validation status, broken refs, and
  mode conversion provenance.
- Data structures: link review summary, link status, source/target safe labels,
  review decision.
- API changes: link review/list/update endpoints.
- Frontend changes: dashboard for links, broken refs, pending reviews, and
  provenance.
- Tests: broken link display, hidden target redaction, status update
  persistence.
- Acceptance: `CrossModeLink` remains transparent and reviewable without
  creating facts.

### 15. Cross-Mode Conflict Detection

- Goal: detect contradictions and unsafe overlaps across Novel, Tavern, World,
  timelines, characters, facts, and proposals.
- Data structures: `CrossModeConflict`, `CrossModeConflictType`,
  `CrossModeConflictSeverity`, safe conflict detail.
- API changes: conflict scan endpoint and repository-backed latest report.
- Frontend changes: later resolution UI consumes conflict reports.
- Tests: duplicate refs, stale links, incompatible target refs, hidden leak risk,
  proposal collisions, no hidden text in normal reports.
- Acceptance: conflicts are detected deterministically and safely reported.

### 16. Cross-Mode Conflict Resolution UI

- Goal: let users review conflicts and choose safe resolution actions.
- Data structures: frontend conflict row, resolution choice, confirmation
  payload, audit ref.
- API changes: resolution decision endpoint; no direct World apply unless routed
  through validated apply flow.
- Frontend changes: conflict list, diff panel, mark resolved/defer/reject,
  optional route-to-apply controls.
- Tests: build, hidden details redacted, invalid resolution disabled,
  confirmation required for state-affecting routes.
- Acceptance: conflict UI never bypasses validation or apply semantics.

### 17. Cross-Mode Validation

- Goal: validate bridge items, links, proposals, drafts, refs, visibility, and
  apply eligibility.
- Data structures: `CrossModeValidationReport`, issue severity, normal/debug
  view split, validation policy.
- API changes: validation endpoint for bridge item/project scope.
- Frontend changes: validation report panels in review surfaces.
- Tests: valid items pass, invalid refs fail, hidden leak risks flagged,
  normal report redacts hidden text, no project mutation.
- Acceptance: no draft/proposal can apply to World without passing validation.

### 18. Cross-Mode Quality Gate

- Goal: integrate cross-mode validation, conflict detection, proposal safety,
  export safety, and boundary evals into the project quality gate.
- Data structures: `CrossModeQualityGateConfig`,
  `CrossModeQualityGateResult`, blocker/warning summaries.
- API changes: project quality gate includes cross-mode checks.
- Frontend changes: quality dashboard summary for bridge readiness.
- Tests: blockers fail gate, warnings remain non-blocking, no hidden text in
  normal result, no real provider calls.
- Acceptance: high-risk cross-mode boundary violations block release/readiness.

### 19. Cross-Mode Import / Export

- Goal: package cross-mode bridge records safely for local backup or transfer.
- Data structures: `CrossModePackageManifest`, included sections, checksums,
  excluded sections, import dry-run result.
- API changes: export, import dry-run, import apply endpoints or CLI hooks.
- Frontend changes: safe export/import controls with warnings.
- Tests: excludes `.env`, API keys, databases, logs, cache, `node_modules`,
  `dist`, debug memory, raw `state_deltas`, provider secrets; rejects zip slip,
  executables, checksum mismatch.
- Acceptance: cross-mode packages are local, non-executable, and secret-safe.

### 20. Cross-Mode Audit Trail

- Goal: record cross-mode preview, validation, review, conflict decision, and
  apply events for traceability.
- Data structures: `CrossModeAuditEvent`, audit event type, actor label,
  source/target refs, redacted details.
- API changes: audit append/list endpoints; audit append is internal to bridge
  services.
- Frontend changes: audit timeline in bridge dashboard and review pages.
- Tests: append-only behavior, stable ordering, no hidden text in normal audit,
  apply events include generated EventLog refs when applicable.
- Acceptance: every cross-mode apply and review decision is auditable.

### 21. v2.4 Integration Regression Tests

- Goal: prove the bridge works with v2.1 NarrativeProject, v2.2 Novel Studio,
  v2.3 Tavern Studio, and World Mode boundaries.
- Data structures: project fixtures for Novel drafts, Tavern proposals, World
  saves/EventLog, timeline refs, hidden facts, NPC secrets, and fake providers.
- API changes: none.
- Frontend changes: build coverage for bridge/review surfaces.
- Tests: full deterministic backend suite and frontend build.
- Acceptance: no state, visibility, provider, import/export, apply, audit, or
  conflict-resolution regression remains.

## Impact on NarrativeProject

- Cross-mode bridge records become first-class project-local data.
- Project workspace should reserve storage for bridge items, validation reports,
  conflicts, audit events, import/export packages, and review metadata.
- Project validation must include bridge refs, proposal state, apply eligibility,
  audit completeness, export safety, and hidden visibility boundaries.
- Project import/export must continue excluding `.env`, API keys, raw env,
  databases, logs, caches, debug memory, raw `state_deltas`, provider secrets,
  and executable files.

## Impact on Novel Studio

- Novel Studio keeps draft semantics.
- Novel -> World creates World draft candidates only.
- Novel Character -> Tavern Character creates Tavern draft/adapters only.
- World -> Novel and Tavern -> Novel create Novel drafts only and do not make
  Novel output authoritative World state.
- Novel exports must not include hidden World facts, Tavern private persona,
  debug memory, or raw `state_deltas`.

## Impact on Tavern Studio

- Tavern Studio keeps RP session / memory / proposal semantics.
- Tavern -> World apply becomes possible only through the validated,
  explicitly-confirmed bridge apply flow.
- Tavern Session -> Novel Scene Draft creates Novel draft material only.
- RP memory remains non-authoritative.
- Tavern prompt/context boundaries from v2.3 continue to apply.

## Impact on World Mode / GameState

- World Mode remains the only runtime fact engine.
- `GameState` can only change through `StateDelta`.
- Every World-changing apply must record `EventLog`.
- Apply failures must preserve original `GameState`, saves, and EventLog.
- Novel/Tavern draft/proposal records cannot mutate World runtime state by
  themselves.

## Impact on CrossModeLink

- `CrossModeLink` becomes reviewable through bridge dashboard surfaces.
- Links may store provenance, validation status, conflict markers, and audit
  refs.
- Links must not expose hidden targets in normal views.
- Links must not create authoritative facts or apply state changes.

## LLM Boundary

- LLMs remain language generators only.
- LLMs may generate summaries, text drafts, suggestions, and proposal
  candidates.
- LLMs cannot decide whether a proposal applies.
- LLMs cannot directly modify `GameState`, `EventLog`, content packs, or
  bridge audit records.
- Any LLM-assisted bridge operation must use Provider Gateway / `LLMProvider`.
- Tests must use fake/mock/local-stub providers and never call real APIs.
- Prompt profiles cannot enable hidden fact access, state modification,
  action-result override, or visibility bypass.

## Visibility, Privacy, and Memory Risks

- Hidden facts, NPC secrets, hidden witnesses, debug memory, raw
  `state_deltas`, raw prompts, provider secrets, and API keys are the main
  cross-mode leak risks.
- Normal context, normal UI, exports, validation reports, conflict reports, and
  audit trails should show safe labels, refs, counts, or redacted summaries
  rather than hidden text.
- NPC secrets must not enter Tavern or Novel normal view.
- RP memory and Novel prose are not World facts unless promoted through
  validation and explicit apply.
- Debug views must remain explicitly gated and separate from normal authoring
  and player-facing views.

## v2.4 Integration Test Requirements

- Cross-mode schema serialization and defaults.
- Repository save/load/list with path traversal rejection.
- Novel -> World draft generation without content-pack or `GameState`
  mutation.
- World -> Novel import reading safe EventLog/timeline summaries only.
- Tavern -> World apply requiring validation and explicit confirmation.
- Apply flow producing `StateDelta` and `EventLog`.
- CrossModeLink review without hidden target exposure.
- Conflict detection and resolution backend behavior.
- Conflict resolution UI build and hidden redaction behavior.
- Audit trail append-only behavior.
- Cross-mode import/export excluding `.env`, API keys, raw env, databases,
  logs, caches, `node_modules`, `dist`, debug memory, raw `state_deltas`, and
  provider secrets.
- LLM/prompt paths using fake/mock/local providers only.
- Full backend suite:
  - `python -m pytest`
- Frontend build:
  - `cd frontend && npm.cmd run build`

## Final Acceptance Criteria

- Cross-mode bridge core schemas, repository, validation, audit trail, and
  quality gate are implemented.
- Novel -> World, World -> Novel, Tavern -> World, Tavern -> Novel, and Novel
  -> Tavern flows produce drafts/proposals/review records safely.
- Any World-changing apply path requires validation, explicit confirmation,
  `StateDelta`, `EventLog`, and audit trail.
- `CrossModeLink` remains reference/review metadata and never creates
  authoritative facts.
- Hidden facts, NPC secrets, private notes, debug memory, raw `state_deltas`,
  API keys, raw env, and provider secrets do not enter normal prompts, UI,
  exports, validation reports, quality reports, or audit trails.
- Full backend tests and frontend build pass.

## v2.5 Candidate Direction

v2.5 should focus on **World Studio Review & Apply**: richer World authoring
review, safe content-pack diff/apply, proposal batching, rollback-aware save
integration, deeper conflict resolution, and project-level release dashboards.
It should continue local-first constraints and should not move into online sync,
marketplace, or arbitrary-code plugin execution until cross-mode apply,
visibility, export, and audit boundaries remain stable.
