# v1.4 Release Notes: Content Production Pipeline

## Version Name

v1.4: Content Production Pipeline

## Version Goal

v1.4 adds a local, safe, validation-first production workflow for creating and
reviewing reusable content at batch scale.

The release is for this local personal interactive fiction engine and studio.
It helps a solo creator build world-pack drafts, NPC packs, quest packs,
location clusters, mystery structures, faction templates, script packages,
campaign starter kits, character-card batches, lorebook batches, coverage
plans, package exports, and batch quality reports.

The core engine boundary is unchanged:

- The LLM is not the world judge.
- The world engine remains the only source of truth.
- v1.4 generators create drafts, candidates, and packages only.
- Production drafts do not modify active `GameState`.
- Apply/build flows must pass validation gates.
- Package import/export does not execute arbitrary code.

## New Features

### Content Production Boundary

- Added `docs/CONTENT_PRODUCTION_BOUNDARY.md`.
- Added `ContentProductionPolicy` and shared production concepts:
  `production_draft`, `generated_content_candidate`,
  `batch_import_candidate`, `production_package`, `package_manifest`,
  `explicit_apply`, `validation_required`, `quality_required`,
  `active_world_pack`, and `active_game_state`.
- Defined the required preview, validate, apply, validation gate, quality gate,
  dry-run, redaction, and package safety flow for v1.4 tools.

### World Pack Wizard

- Added `WorldPackWizardDraft`.
- Supports deterministic draft generation for starter world packs with
  manifest, locations, NPCs, items, quests, facts, and optional faction/rumor
  content.
- Preview is non-writing.
- Apply writes only after explicit confirmation and validation.

### NPC Pack Generator

- Added `NPCPackGeneratorDraft`.
- Produces NPC candidates, RP profile drafts, voice profile drafts,
  relationship candidates, goal candidates, schedule candidates, and hidden
  secret candidates.
- Hidden secrets are marked hidden and remain out of player-facing fields.
- Output remains draft/package data.

### Quest Pack Generator

- Added `QuestPackGeneratorDraft`.
- Produces quest candidates, fact candidates, optional rumor/consequence
  candidates, scenario regression candidates, and quest graph drafts.
- Validates referenced NPCs, locations, factions, facts, and hidden-player text
  boundaries.

### Location Cluster Templates

- Added `LocationClusterTemplate`.
- Supports reusable local map fragments with location nodes, exit edges,
  hidden edges, layout metadata, variables, and validation.
- Hidden paths remain hidden from player map output until normal visibility
  rules reveal them.

### Mystery Template System

- Added `MysteryTemplate`.
- Produces structured mystery drafts with hidden truth facts, suspects, clues,
  red herrings, witness statements, reveal/failure conditions, evidence items,
  questline drafts, rumor drafts, and scenario regression drafts.
- `truth_fact` is hidden by default.

### Faction Template System

- Added `FactionTemplate`.
- Produces faction drafts, relation drafts, NPC duty candidates, relationship
  candidates, and quest hook candidates.
- Hidden factions and hidden relations stay out of player-visible faction
  graphs.

### Content Batch Validator

- Added `ContentBatchValidationRequest` and `ContentBatchValidationReport`.
- Supports world packs, character packs, quest packs, template packs, mod
  packages, and script packages.
- Aggregates passed/warning/failed counts, blockers, per-package reports, and
  aggregate issues.
- Rejects path traversal, executable files, sensitive files, and secret-like
  content in package validation paths.

### Content Coverage Planner

- Added `ContentCoveragePlan`.
- Produces rule-based suggestions for missing location types, NPC archetypes,
  quest types, clue paths, faction hooks, RP scenes, scenario regressions, and
  playtest paths.
- Does not write content.

### Export / Import Profiles

- Added `ExportProfile` and `ImportProfile`.
- Safe defaults redact hidden text, reject executables, require validation,
  and forbid API keys.
- Profiles make import/export behavior explicit and reusable.

### Local Content Library Pro

- Extended Local Content Library with production-oriented content types,
  search/filter/tag flows, inspection, validation, batch validation,
  dependency summaries, quality summaries, and import/export profiles.
- Normal views avoid sensitive local paths and hidden details.

### Batch Character Card Import

- Added `BatchCharacterCardImportRequest` and
  `BatchCharacterCardImportReport`.
- Supports multiple local cards, safe zip inputs, and pasted JSON/YAML text.
- Each card goes through the existing character-card importer.
- Reports invalid, unsafe, duplicate, and candidate entries.

### Batch Lorebook Classification

- Added `BatchLorebookClassificationRequest` and
  `BatchLorebookClassificationReport`.
- Classifies lorebook entries into flavor lore, structured fact candidates,
  hidden fact candidates, and unsafe entries.
- Normal reports redact hidden lorebook text.

### Script Package Builder

- Added `ScriptPackageManifest`.
- Builds structured data packages with included worlds, quests, characters,
  templates, scenarios, quality profile, dependencies, conflicts, checksums,
  validation, dry-run/build, and zip export.
- Script packages do not execute scripts despite the name.
- Build now rejects automatic overwrite of an existing package directory.

### Campaign Starter Kit Builder

- Added `CampaignStarterKitDraft`.
- Composes starter-scale world, NPC, quest, faction, optional mystery,
  scenario regression, quality config, and script package drafts.
- Preview is non-writing.
- Build requires validation and quality dry-run.

### Production Pipeline Dashboard

- Added `ProductionPipelineSummary`.
- Summarizes active production drafts, recent generated packages, batch
  validation status, content coverage plan, quality gate status, import/export
  profile status, script package status, and campaign starter status.
- Gated by `ENABLE_AUTHORING_API`.

### Content Production CLI

- Added `python -m backend.app.tools.production`.
- Commands cover world wizard, NPC pack, quest pack, batch validate, script
  package build, campaign starter, coverage plan, and batch quality gate.
- Preview is the safe default.
- Apply/build requires explicit flags.

### Batch Quality Gate

- Added `BatchQualityGateRequest` and `BatchQualityGateReport`.
- Evaluates multiple worlds or packages for release/export readiness.
- Reports pass/fail, blockers, warnings, per-item results, aggregate summary,
  and recommended actions.
- Does not automatically fix content.

## Behavior Changes

- Content production is now a first-class local studio workflow.
- Production tools operate on drafts, candidates, packages, previews, and
  reports, not active runtime state.
- Preview and validate operations are expected to be non-writing.
- Apply/build flows require explicit user intent and validation/quality checks.
- Hidden content is redacted from normal production reports.
- Safe exports exclude API keys and hidden fact text.
- Script package build rejects automatic overwrite rather than silently
  replacing an existing package directory.
- Batch lorebook apply-draft normal reports redact hidden YAML draft text.
- Batch validation checks raw script-package directories for sensitive files
  and secret-like content.

## API Changes

v1.4 adds production-facing local API surfaces for:

- Content production boundary checks.
- World Pack Wizard preview/validate/apply.
- NPC Pack Generator preview/validate/apply/export.
- Quest Pack Generator preview/validate/apply.
- Location Cluster Template list/preview/apply.
- Mystery Template preview/apply.
- Faction Template preview/apply.
- Content Batch Validator.
- Content Coverage Planner.
- Export / Import Profiles.
- Local Content Library Pro.
- Batch Character Card Import.
- Batch Lorebook Classification.
- Script Package Builder dry-run/build/validate/export.
- Campaign Starter Kit preview/build/export.
- Production Pipeline Dashboard summary.
- Batch Quality Gate.

These APIs are local authoring/production tools. They are not player APIs and
do not grant runtime state authority.

## Frontend Changes

- Added production-oriented studio surfaces for the v1.4 pipeline.
- Added or extended panels for:
  - World Pack Wizard.
  - NPC Pack Generator.
  - Quest Pack Generator.
  - Location Cluster Templates.
  - Mystery and faction template flows.
  - Batch validation and batch quality status.
  - Local Content Library Pro.
  - Batch character card import.
  - Batch lorebook classification.
  - Script Package Builder.
  - Campaign Starter Kit Builder.
  - Production Pipeline Dashboard.
- Frontend build passes with the v1.4 surfaces.
- Player UI remains separated from authoring/production/debug data.

## Content Production Changes

- Production drafts are distinct from active `GameState`.
- Generated content must remain structured draft/candidate/package data until
  reviewed and validated.
- Generators default to deterministic local logic and do not call a real LLM.
- Reserved `llm_assisted` fields are metadata only in this release.
- Hidden facts, NPC secrets, RP private fields, unsafe import prompts, and
  production debug data stay out of normal reports and player-facing surfaces.
- Coverage and quality outputs are advisory authoring reports, not canonical
  world facts.

## Package / Import / Export Changes

- Export/import profiles make package safety behavior explicit.
- Safe export mode excludes API keys and hidden fact text.
- Import profiles reject executables and require validation by default.
- Batch character import treats external prompt text as untrusted data.
- Batch lorebook classification isolates hidden and unsafe entries.
- Script packages include manifests and checksums and are data-only.
- Package/import/export flows must not execute arbitrary code.
- Package flows reject path traversal, zip slip, executable files, `.env`,
  databases, logs, caches, build outputs, and secret-like content where
  applicable.
- Automatic overwrite is not part of the accepted package build behavior.

## CLI Changes

Added:

- `python -m backend.app.tools.production world-wizard`
- `python -m backend.app.tools.production npc-pack`
- `python -m backend.app.tools.production quest-pack`
- `python -m backend.app.tools.production batch-validate`
- `python -m backend.app.tools.production build-script-package`
- `python -m backend.app.tools.production campaign-starter`
- `python -m backend.app.tools.production coverage-plan`
- `python -m backend.app.tools.production batch-quality-gate`

CLI behavior:

- Preview is safe by default.
- Apply/build requires explicit flags.
- JSON and human-readable output modes are supported.
- Output redacts API keys, raw env values, hidden/private fields, and archive
  payloads.
- Commands reuse service-layer code.

## Testing / Quality Changes

- Added v1.4 module tests for production boundary, generators, templates,
  batch tools, package builders, dashboard, CLI, and batch quality gate.
- Added v1.4 integration regression tests.
- Added release-blocker regression coverage for:
  - script package overwrite rejection
  - hidden lorebook YAML redaction in normal apply-draft reports
  - sensitive file and secret rejection in script-package batch validation
- Latest acceptance verification:
  - `python -m pytest`: `1239 passed in 68.82s`
  - `cd frontend && npm.cmd run build`: passed
- Batch Quality Gate is deterministic and does not call real LLMs.
- Quality reports do not automatically repair content.

## Known Limitations

- v1.4 is not an online marketplace.
- v1.4 does not provide cloud sync, accounts, multiplayer collaboration, or
  remote publishing.
- Generators do not automatically create complete high-quality worlds or
  long-form campaigns.
- Generated drafts are structurally useful starting points, not guaranteed
  finished creative content.
- `llm_assisted` fields are reserved metadata only in this release.
- Content Coverage Planner and Batch Quality Gate are heuristic authoring aids,
  not absolute creative judgments.
- Local Content Library Pro does not download remote content.
- Script packages are data packages and do not run code.
- Campaign Starter Kit Builder creates starter-scale packages, not complete
  large campaigns.
- Some older local analyzer/quality endpoints still rely on existing local
  feature flags rather than a dedicated `ENABLE_QUALITY_API`.
- The PowerShell profile warning seen in local command output is an environment
  issue and does not affect v1.4 test/build status.

## Upgrade Notes From v1.3

- Existing v1.3 saves and runtime NPC simulation behavior remain compatible.
- v1.4 adds production tools; it does not require existing worlds to opt into
  generation.
- New package, production, and profile schemas may appear in local content
  library and production artifacts.
- Keep `ENABLE_AUTHORING_API` enabled only for local trusted studio use.
- Do not treat production drafts as active world state.
- Review generated drafts before applying them to world-pack files.
- Run validation and, for release/export workflows, Batch Quality Gate before
  publishing or archiving content locally.
- Safe export should be used when sharing files outside a trusted local debug
  context.
- If future LLM-assisted draft generation is implemented, it must remain
  draft-only and validation-gated.

## Recommended v1.5 Directions

- Deterministic campaign director tools for pacing, milestones, scene order,
  and chapter-scale production planning.
- Player-facing journal, clue board, rumor board, faction dossier, and
  discovered-content review improvements.
- Stronger semantic redaction for hidden text in reports, debug payloads, and
  package manifests.
- Content migration assistant for large generated worlds and package upgrades.
- Local production bundle wizard for release archives with clearer dependency
  and compatibility review.
- Optional draft-only LLM content assistants behind provider factory, schema
  validation, provenance tracking, redaction, validation gate, and quality gate.
- Broader component-level frontend tests for Production Dashboard, Library Pro,
  and generator panels.
- Richer analytics for unused content, hidden-content exposure, scenario
  coverage, NPC simulation coverage, and quest completion health.

## Final Notes

v1.4 keeps the project firmly local-first. The Content Production Pipeline
improves how content is produced, reviewed, validated, and packaged, but it
does not change runtime authority.

The engine remains rules-first. The LLM remains language-facing. Production
tools remain draft/package-facing.
