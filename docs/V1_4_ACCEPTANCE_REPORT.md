# v1.4 Acceptance Report: Content Production Pipeline

## Verdict

Accepted for v1.4.

v1.4 delivers the Content Production Pipeline as a local, deterministic,
validation-first production workflow. The implementation provides the content
production boundary contract, world/NPC/quest generators, location/mystery/
faction templates, batch validators, coverage planning, import/export profiles,
Local Content Library Pro, batch character and lorebook import, script package
and campaign starter builders, production dashboard, CLI, batch quality gate,
and v1.4 integration regression coverage.

The final blocker hardening prevents script package overwrite, redacts hidden
lorebook text from normal apply reports, and expands batch validation for raw
script-package sensitive files and secrets.

No high-risk acceptance blocker remains.

## Verification Date

2026-05-20 +08:00

## Verification Commands

- `python -m pytest`
- `cd frontend && npm.cmd run build`

## Verification Results

- Backend tests: passed, `1239 passed in 68.82s`.
- Frontend build: passed, `tsc -b && vite build` completed successfully.
- Non-blocking shell noise: Windows PowerShell reported an unsigned user
  profile warning while starting commands. The commands still completed with
  exit code 0 and the warning did not affect test/build results.

## Scope Accepted

Accepted v1.4 scope:

- Content Production Boundary Contract.
- World Pack Wizard.
- NPC Pack Generator.
- Quest Pack Generator.
- Location Cluster Templates.
- Mystery Template System.
- Faction Template System.
- Content Batch Validator.
- Content Coverage Planner.
- Export / Import Profiles.
- Local Content Library Pro.
- Batch Character Card Import.
- Batch Lorebook Classification.
- Script Package Builder.
- Campaign Starter Kit Builder.
- Production Pipeline Dashboard.
- Content Production CLI.
- Batch Quality Gate.
- v1.4 integration regression tests.

The accepted scope remains a local personal engine/studio workflow. It does
not add online marketplace features, cloud sync, remote content fetching,
arbitrary package execution, or default real-LLM generation.

## Boundary Review

### Content Production Boundary

Accepted.

- `docs/CONTENT_PRODUCTION_BOUNDARY.md` defines `production_draft`,
  `generated_content_candidate`, `batch_import_candidate`,
  `production_package`, `package_manifest`, `explicit_apply`,
  `validation_required`, `quality_required`, `active_world_pack`, and
  `active_game_state`.
- `ContentProductionPolicy` checks preview, validate, save, apply, import,
  export, and build decisions without writing disk, applying deltas, calling
  LLMs, or executing package content.
- Production drafts and generated candidates are not active runtime state.
- Preview and validate paths are tested as non-writing flows.
- Apply/build paths require explicit confirmation and validation or quality
  gates as appropriate.
- Production tooling does not directly mutate active `GameState`.

### Wizards / Generators

Accepted.

- `WorldPackWizardDraft` can create a minimal world-pack draft, preview files,
  validate, and apply to the worlds directory only after confirmation and the
  validation gate.
- `NPCPackGeneratorDraft` creates NPC candidates, RP/voice profiles,
  relationship candidates, goals, schedules, and hidden-secret candidates as
  draft/package data.
- `QuestPackGeneratorDraft` creates quest candidates, fact candidates,
  scenario regression candidates, and quest graph drafts while validating
  references and hidden-player text boundaries.
- Generator output remains draft/candidate/package data until explicit gated
  save/apply.
- Current generator paths are deterministic by default. Reserved
  `llm_assisted` metadata does not call a real provider in the accepted
  implementation.

### Templates

Accepted.

- `LocationClusterTemplate` loads, previews, validates, and applies map
  fragments to drafts without complex automatic layout or active state edits.
- Hidden edges are marked hidden and remain outside player maps unless normal
  visibility rules reveal them later.
- `MysteryTemplate` generates hidden truth facts, suspects, clues, red
  herrings, witness statements, quest/fact/rumor/evidence drafts, and scenario
  regression drafts. `truth_fact` is hidden and normal reports avoid hidden
  truth text.
- `FactionTemplate` generates faction drafts, relation drafts, NPC duty
  candidates, relationship candidates, and quest hook candidates. Hidden
  factions/relations remain authoring data and do not enter player-visible
  graphs.
- Template flows do not execute scripts and do not call LLMs.

### Batch Tools

Accepted.

- `ContentBatchValidator` validates batches of world, character, quest,
  template, mod, and script packages, aggregates blockers/warnings, rejects
  path traversal, and keeps normal reports redacted.
- Script package validation rejects executable files, sensitive files such as
  `.env`, database/log artifacts, and API-key-like secret tokens.
- `ContentCoveragePlanner` produces rule-based coverage suggestions for
  missing locations, NPC archetypes, quest types, clue paths, faction hooks,
  RP scenes, scenario regressions, and playtest paths. It does not write
  content.
- `BatchCharacterCardImport` converts multiple cards into candidates and a
  character pack draft while flagging invalid, unsafe, duplicate, and
  path-traversal cases.
- `BatchLorebookClassification` classifies entries into flavor,
  structured fact candidates, hidden fact candidates, and unsafe entries.
  Normal apply-draft reports redact hidden YAML text.
- `BatchQualityGate` evaluates multiple worlds/packages and returns pass/fail,
  blockers, warnings, per-item results, aggregate summaries, and recommended
  actions without modifying content or calling real LLMs.

### Packages / Library

Accepted.

- `ExportProfile` and `ImportProfile` provide explicit safe/default behavior
  for hidden authoring data, redaction, validation, quality gate, migration
  checks, executable rejection, unknown schema rejection, and overwrite policy.
- Safe export profiles exclude API keys and hidden fact text.
- Local Content Library Pro supports search, filter, tags, inspection,
  validation, batch validation, export/import with profiles, dependency
  summaries, quality summaries, duplicate/archive helpers, and editor links.
- Normal library views avoid sensitive local paths and hidden details.
- `ScriptPackageBuilder` builds data packages with manifests, dependencies,
  conflicts, checksums, validation, dry-run/build/export, executable rejection,
  sensitive-file rejection, and hidden-text redaction in normal manifests.
- Script package build now rejects automatic overwrite of an existing package
  directory.
- `CampaignStarterKitBuilder` composes world, NPC, quest, faction, optional
  mystery, scenario, quality, and script package drafts. Preview is non-writing
  and build is validation/quality-gated.

### CLI / Dashboard

Accepted.

- `ProductionPipelineSummary` powers a local authoring-only dashboard for
  production drafts, generated packages, batch validation status, coverage
  plans, quality gate status, profile status, script package status, and
  campaign starter status.
- Dashboard responses are guarded by `ENABLE_AUTHORING_API` and redact API
  keys, raw environment values, hidden fact text, and sensitive paths.
- `python -m backend.app.tools.production` exposes local service-backed
  commands for world wizard, NPC pack, quest pack, batch validate, script
  package build, campaign starter, coverage plan, and batch quality gate.
- CLI preview is the safe default. Apply/build requires explicit flags.
- CLI output supports JSON or human-readable summaries and redacts API keys,
  raw env values, hidden/private fields, and archive payloads.
- Frontend build passes.

### LLM / Authority

Accepted.

- LLM remains a parser, narrator, summarizer, RP expression layer, or optional
  future draft assistant. It is not a world judge and not a production
  authority.
- v1.4 generators and production tools do not call real LLMs by default.
- Production modules do not instantiate concrete provider classes.
- Provider construction remains bounded by `create_llm_provider`.
- Generated content cannot directly enter `GameState`, apply `StateDelta`, or
  record runtime `Event`.
- Any future LLM-assisted generation must remain draft/candidate-only, use
  provider factory, pass schema validation, classify visibility, and go through
  validation and quality gates.
- Tests use deterministic local/mock/fake paths and do not call real APIs.

### Visibility / Package Safety

Accepted.

- Hidden facts, NPC secrets, private RP fields, hidden memories, hidden
  relationships, and production debug data are excluded from normal reports,
  player APIs, narrator prompts, and player UI.
- Safe package exports exclude API keys and hidden fact text.
- Batch character import treats external prompt text as untrusted data.
- Batch lorebook classification isolates hidden and unsafe entries and redacts
  hidden text in normal reports.
- Mystery templates keep truth facts hidden.
- Script package manifests do not include hidden fact text in normal mode.
- Package/import flows reject path traversal, zip slip, executable content,
  `.env`, database/log/cache/build artifacts, and secret-token-like content.
- Packages are data; import/export/package flows do not execute arbitrary code.

## Known Limitations

- v1.4 is a production pipeline for local drafts and packages, not an automatic
  publishing system or hosted collaboration service.
- Generators provide deterministic structural drafts; they do not guarantee
  literary quality or complete long-form campaign writing.
- `llm_assisted` fields are reserved metadata only in the accepted
  implementation.
- Batch quality and coverage reports are heuristic authoring aids, not absolute
  creative judgments.
- Local Content Library Pro remains a local library and does not download,
  sync, or publish content online.
- Script packages are structured data packages despite the name; they do not
  execute scripts.
- Campaign Starter Kit Builder creates starter-scale content only, not a full
  large campaign.
- Some older local quality/analyzer endpoints still rely on existing local
  feature flags rather than a dedicated `ENABLE_QUALITY_API`; keep the backend
  bound to localhost/local use.
- PowerShell profile signing warnings appear in command output on this machine
  but do not affect test/build results.

## Acceptance Risks

- Low risk: future generator work could accidentally turn reserved
  `llm_assisted` metadata into a real provider call. Keep provider-factory,
  fake-provider tests, draft-only output, and validation/quality gates mandatory.
- Low risk: future report UI changes could display debug/hidden fields in
  normal production views. Keep redaction tests near dashboard, library, batch
  reports, and package previews.
- Low risk: future package types could bypass script/sensitive-file checks.
  Reuse Content Batch Validator and ImportProfile policies for new package
  types.
- Low risk: CLI output can become a leakage surface if new commands print raw
  payloads. Keep JSON/human output filtered through safe summaries.
- Low risk: package build/apply flows must continue rejecting automatic
  overwrite unless a future explicit conflict-resolution design is added.

No known high-risk release blocker remains.

## Recommended v1.5 Priorities

- Deterministic campaign director tools for pacing, milestones, scene order,
  and chapter-scale production planning.
- Player-facing journal, clue board, rumor board, faction dossier, and
  discovered-content review improvements.
- Stronger semantic redaction for hidden text in reports, debug payloads, and
  package manifests.
- Content migration assistant for large generated worlds and package upgrades.
- Production bundle wizard for local release archives with clearer dependency
  and compatibility review.
- Optional draft-only LLM content assistants behind provider factory, schema
  validation, provenance tracking, redaction, validation gate, and quality gate.
- Broader component-level frontend tests for Production Dashboard, Library Pro,
  and generator panels.
- Richer analytics for unused content, hidden-content exposure, scenario
  coverage, NPC simulation coverage, and quest completion health.

## Final Status

v1.4 is accepted.

The project is ready to proceed to v1.4 release notes and final freeze checks,
subject to normal repository hygiene checks for tracked temporary files,
sensitive data, expected working-tree contents, and tag preparation.
