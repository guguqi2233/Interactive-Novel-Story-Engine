# v1.4 Roadmap: Content Production Pipeline

## Version Goal

v1.4 builds a local, safe, validation-first Content Production Pipeline for
batch-producing reusable world content.

The goal is to help a solo local creator produce and review world packs, NPC
packs, quest packs, location clusters, mystery cases, faction templates, script
packs, campaign starter kits, character card batches, lorebook batches, and
production-quality package exports without weakening the engine boundary.

The core rule is unchanged:

Content production creates drafts, templates, packages, and content-pack files.
It does not directly modify active `GameState`.

Any explicit save, apply, import, batch import, export, or package build must
pass validation and the Authoring Validation Gate. Runtime state changes, if
content is later used in a session, still happen only through `StateDelta` and
`Event`.

## Not In v1.4

- LLM world adjudication.
- LLM direct `GameState` mutation.
- Generators directly modifying active `GameState`.
- Batch import bypassing validation.
- Automatic overwrite of user world packs.
- Arbitrary-code plugin execution.
- Online marketplace.
- Cloud sync, accounts, or multi-user collaboration.
- Automatic remote URL content fetching.
- Applying untrusted character cards or lorebooks directly to active worlds.
- Default real-LLM generation in tests or normal pipeline flows.
- Generated content bypassing Quality Gate.
- Reading `.env`, API keys, databases, logs, caches, or system files as source
  content.
- Treating generated prose as authoritative hidden/player facts without schema
  validation and explicit visibility classification.

## Frozen Constraints

- LLM output cannot directly modify `GameState`.
- Runtime state changes must use `StateDelta`.
- Content production drafts are not active `GameState`.
- Generators create drafts or packages only.
- Save/apply/import/export/build operations require validation gate checks.
- Hidden facts do not enter player `visible_state`.
- Hidden content does not enter normal production reports.
- Authoring/debug APIs remain local-only.
- Import/export must not execute arbitrary code.
- Batch processing must not read `.env`, API keys, databases, system files, logs,
  caches, or build outputs.
- Provider factory remains the only LLM provider entry point.
- Default tests use mock/local-stub/fake providers and do not call real APIs.

## Recommended Development Order

1. Content Production Boundary Contract.
2. Content Batch Validator.
3. Batch Quality Gate.
4. Export / Import Profiles.
5. World Pack Wizard.
6. Location Cluster Templates.
7. NPC Pack Generator.
8. Quest Pack Generator.
9. Mystery Template System.
10. Faction Template System.
11. Batch Character Card Import.
12. Batch Lorebook Classification.
13. Content Coverage Planner.
14. Script Package Builder.
15. Campaign Starter Kit Builder.
16. Local Content Library Pro.
17. Production Pipeline Dashboard.
18. Content Production CLI.

The first phase should land the shared boundary, batch validation, and batch
quality gate before adding new generators. This keeps every later module on the
same draft/package/validation/reporting contract.

## Module Roadmap

### 1. Content Production Boundary Contract

Goal: Define the v1.4 production boundary for drafts, generated content,
imports, batch operations, packages, validation, reports, and active runtime
state.

Data structures:

- `ContentProductionPolicy`
- `ContentProductionDraft`
- `ContentProductionPreview`
- `ContentProductionValidationReport`
- `ContentProductionOperation`
- `ContentProductionRisk`
- `ProductionHiddenContentRef`
- `ProductionSafeSummary`

API changes:

- `GET /authoring/content-production/boundary`
- `POST /authoring/content-production/boundary/check`

Frontend changes:

- Add a local-only boundary/status panel in the production dashboard.
- Show whether an operation is draft-only, validation-gated, package-safe, and
  hidden-redacted.

Tests:

- Draft creation does not write active `GameState`.
- Preview does not write disk.
- Validate does not write disk.
- Save/apply/import/export/build require validation gate.
- Hidden content is excluded from normal reports.
- No real LLM provider is called.

Acceptance:

- All v1.4 generators and batch tools reference the same production boundary.
- No module can claim active-runtime authority.

Content pack schema impact: introduces common production metadata and report
schema only; existing packs remain valid.

Save migration impact: none for active saves.

RP / NPC Knowledge / Visibility impact: generated RP/NPC fields are drafts until
validated; hidden/private fields remain non-player-facing.

LLM boundary impact: no new runtime LLM authority.

Leak risk: high if normal reports include hidden generated text. Normal reports
must use ids, counts, and safe summaries.

### 2. World Pack Wizard

Goal: Provide a step-by-step local wizard for creating a complete draft world
pack with metadata, locations, starter NPCs, factions, rumors, templates, and
quality checks.

Data structures:

- `WorldPackWizardDraft`
- `WorldPackWizardStep`
- `WorldPackSeedProfile`
- `WorldPackGenerationPreview`
- `WorldPackWizardValidationReport`

API changes:

- `POST /authoring/production/world-pack/preview`
- `POST /authoring/production/world-pack/validate`
- `POST /authoring/production/world-pack/save`

Frontend changes:

- Multi-step world-pack wizard.
- Preview generated files before save.
- Display validation, coverage, hidden-content, and migration impact.

Tests:

- Valid world pack draft can be generated and saved after validation.
- Invalid variables are rejected.
- Preview does not write disk.
- Save uses validation gate.
- Active `GameState` is unchanged.

Acceptance:

- A creator can create a minimal valid world pack draft and save it explicitly.

Content pack schema impact: may add optional production metadata and starter-kit
references.

Save migration impact: none; new worlds do not migrate active saves.

RP / NPC Knowledge / Visibility impact: initial facts and NPC knowledge must be
classified before save.

LLM boundary impact: deterministic by default; any future LLM draft assistant
must be opt-in, provider-factory based, schema-validated, and draft-only.

Leak risk: hidden seed facts must not appear in world descriptions or player
intro text.

### 3. NPC Pack Generator

Goal: Generate draft NPC packs containing NPC records, RP profile references,
voice profile references, relationship seeds, faction duties, simulation
presets, safe examples, and optional hidden/private notes.

Data structures:

- `NPCPackDraft`
- `NPCPackMemberDraft`
- `NPCPackRelationshipSeed`
- `NPCPackSimulationSeed`
- `NPCPackExportProfile`

API changes:

- `POST /authoring/production/npc-pack/preview`
- `POST /authoring/production/npc-pack/validate`
- `POST /authoring/production/npc-pack/save`

Frontend changes:

- NPC pack generator panel.
- Batch table for NPC ids, roles, factions, RP fields, voice fields, and hidden
  fields.
- Safe export preview.

Tests:

- Valid NPC pack roundtrip.
- Duplicate NPC ids rejected.
- Hidden/private notes excluded from safe export.
- Simulation preset refs validated.
- Save uses validation gate.

Acceptance:

- A creator can produce a reusable NPC pack without applying it to an active
  world.

Content pack schema impact: optional NPC pack manifest extensions.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: private RP fields and NPC secrets remain
hidden and not player-visible.

LLM boundary impact: no default real LLM calls.

Leak risk: high for `private_self_summary`, NPC secrets, hidden relationship
notes, and hidden faction ties.

### 4. Quest Pack Generator

Goal: Produce questline drafts with quest graphs, stage/objective structures,
triggers, rewards, consequences, scenario regression drafts, and quality checks.

Data structures:

- `QuestPackDraft`
- `QuestlineDraft`
- `QuestStageDraft`
- `QuestObjectiveDraft`
- `QuestPackScenarioDraft`

API changes:

- `POST /authoring/production/quest-pack/preview`
- `POST /authoring/production/quest-pack/validate`
- `POST /authoring/production/quest-pack/save`

Frontend changes:

- Quest pack generator with graph preview.
- Scenario regression draft preview.
- Hidden objective classification display.

Tests:

- Valid quest pack can be saved after validation.
- Missing refs and terminal stages are caught.
- Hidden objectives do not enter player-facing summaries.
- Generated scenario draft is deterministic.

Acceptance:

- Quest pack draft supports validation and quality review before save.

Content pack schema impact: optional quest pack manifest and scenario draft refs.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: quest triggers and hidden objectives
must respect visibility.

LLM boundary impact: no LLM quest authority.

Leak risk: hidden objective text and culprit/evidence truth can leak into normal
reports.

### 5. Location Cluster Templates

Goal: Batch-create coherent groups of locations, exits, regions, layers, hidden
paths, discovery rules, map metadata, and validation/diff previews.

Data structures:

- `LocationClusterTemplate`
- `LocationClusterDraft`
- `LocationNodeDraft`
- `LocationExitDraft`
- `LocationDiscoveryRuleDraft`

API changes:

- `GET /authoring/production/location-cluster/templates`
- `POST /authoring/production/location-cluster/preview`
- `POST /authoring/production/location-cluster/validate`
- `POST /authoring/production/location-cluster/save`

Frontend changes:

- Cluster template picker.
- Compact map preview and diff.
- Hidden-path and locked-path indicators.

Tests:

- Valid cluster roundtrip.
- Invalid location ids and missing edge targets caught.
- Hidden exits excluded from player map.
- Preview does not write disk.

Acceptance:

- Location clusters can be generated as draft map/content data.

Content pack schema impact: optional cluster template metadata.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: hidden paths and discovery rules remain
non-player-visible until discovered.

LLM boundary impact: no LLM map generation by default.

Leak risk: hidden routes and locked/unlock secrets in normal previews.

### 6. Mystery Template System

Goal: Create structured mystery/case drafts with suspects, evidence chains,
witnesses, hidden truths, rumors, crime consequences, red herrings, and
regression playtest expectations.

Data structures:

- `MysteryCaseTemplate`
- `MysteryCaseDraft`
- `EvidenceChainDraft`
- `SuspectDraft`
- `WitnessStatementDraft`
- `MysteryRegressionDraft`

API changes:

- `GET /authoring/production/mystery/templates`
- `POST /authoring/production/mystery/preview`
- `POST /authoring/production/mystery/validate`
- `POST /authoring/production/mystery/save`

Frontend changes:

- Mystery template wizard.
- Evidence graph preview.
- Hidden truth redaction in normal reports.

Tests:

- Valid case draft can be produced.
- Culprit/hidden truth does not enter player visible content.
- Evidence chain has discoverable path.
- Witness hidden facts remain scoped.

Acceptance:

- A mystery draft includes playable evidence structure and safe hidden fields.

Content pack schema impact: optional mystery/case template section and evidence
refs.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: suspects and witnesses know only their
own configured facts.

LLM boundary impact: no LLM culprit/evidence authority.

Leak risk: very high. Hidden truth, culprit, witness secrets, and red herrings
must stay out of normal/player reports.

### 7. Faction Template System

Goal: Batch-generate faction templates with metadata, reputation rules, conflict
edges, alert levels, duties, rumors, and starter NPC role patterns.

Data structures:

- `FactionTemplate`
- `FactionPackDraft`
- `FactionConflictSeed`
- `FactionDutySeed`
- `FactionRumorSeed`

API changes:

- `GET /authoring/production/faction/templates`
- `POST /authoring/production/faction/preview`
- `POST /authoring/production/faction/validate`
- `POST /authoring/production/faction/save`

Frontend changes:

- Faction template picker and graph preview.
- Conflict/duty/rumor batch editor.

Tests:

- Valid faction pack roundtrip.
- Invalid faction refs caught.
- Hidden faction conflict excluded from player graph.
- Duties validate against NPC simulation constraints.

Acceptance:

- Faction templates can seed conflict and duties without runtime simulation
  side effects.

Content pack schema impact: optional faction template metadata.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: hidden faction conflicts and private
alliances remain non-player-visible.

LLM boundary impact: no LLM faction adjudication.

Leak risk: hidden conflict and private allegiance leaks.

### 8. Content Batch Validator

Goal: Validate multiple drafts/packages/worlds together and report structural,
visibility, schema, reference, migration, package safety, and quality issues.

Data structures:

- `ContentBatchValidationRequest`
- `ContentBatchValidationReport`
- `ContentBatchValidationItem`
- `ContentBatchIssue`
- `ContentBatchRiskSummary`

API changes:

- `POST /authoring/production/batch/validate`

Frontend changes:

- Batch validation report view.
- Filter by severity, file, entity, package, hidden risk, and validation gate
  status.

Tests:

- Multiple valid packages pass.
- Invalid refs caught across packages.
- Hidden leak risks are reported without raw hidden text.
- Path traversal and forbidden files rejected.

Acceptance:

- Batch validation becomes the shared gate before v1.4 package operations.

Content pack schema impact: none required.

Save migration impact: reports migration impact but does not mutate saves.

RP / NPC Knowledge / Visibility impact: validates hidden/player/RP/NPC knowledge
boundaries across batches.

LLM boundary impact: no LLM validation decisions.

Leak risk: normal reports must never include raw hidden facts or NPC secrets.

### 9. Content Coverage Planner

Goal: Plan missing content coverage for a world or package set, such as missing
roles, weak quest chains, sparse locations, missing rumors, missing NPC duties,
or absent playtest scenarios.

Data structures:

- `ContentCoveragePlan`
- `CoverageGap`
- `CoverageSuggestion`
- `CoveragePriority`
- `CoveragePlannerProfile`

API changes:

- `POST /authoring/production/coverage/plan`

Frontend changes:

- Coverage planner dashboard.
- Gap list linked to relevant generators and editors.

Tests:

- Detects missing NPC roles, quest coverage, location coverage, and playtests.
- Suggestions are safe summaries, not automatic edits.
- Hidden content is counted without leaking text.

Acceptance:

- A creator can see what content is missing before packaging.

Content pack schema impact: optional coverage report artifacts.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: coverage suggestions must not imply NPCs
know hidden facts.

LLM boundary impact: deterministic planner by default.

Leak risk: hidden content gap reports can reveal spoilers if not summarized.

### 10. Export / Import Profiles

Goal: Define reusable local profiles for safe export/import behavior, including
safe character packs, full debug exports, migration-aware exports, template-only
exports, and redacted review exports.

Data structures:

- `ExportImportProfile`
- `ExportProfilePolicy`
- `ImportProfilePolicy`
- `PackageSafetyProfile`
- `ProfileValidationReport`

API changes:

- `GET /authoring/production/profiles`
- `POST /authoring/production/profiles/validate`
- `POST /authoring/production/export`
- `POST /authoring/production/import-dry-run`
- `POST /authoring/production/import-apply`

Frontend changes:

- Profile selector for import/export flows.
- Explicit display of included/excluded hidden/private/debug fields.

Tests:

- Safe profile excludes hidden facts/API keys.
- Debug profile remains local/debug-only.
- Import dry-run writes nothing.
- Import apply requires validation gate.
- Path traversal and executable files rejected.

Acceptance:

- Import/export behavior is explicit, repeatable, and safe by profile.

Content pack schema impact: optional profile manifests.

Save migration impact: migration impact report only.

RP / NPC Knowledge / Visibility impact: profile controls safe/private RP fields
and NPC knowledge imports.

LLM boundary impact: no LLM import/export decisions.

Leak risk: high for full/debug exports; must be visibly marked local-only.

### 11. Local Content Library Pro

Goal: Extend the local content library for production use with richer metadata,
batch actions, archive/duplicate, validation status, quality status, dependency
status, and safe inspection.

Data structures:

- `LocalContentLibraryProIndex`
- `LocalContentLibraryProItem`
- `LibraryDependencyStatus`
- `LibraryQualityStatus`
- `LibraryBatchActionReport`

API changes:

- `GET /library/pro/items`
- `POST /library/pro/items/validate-batch`
- `POST /library/pro/items/archive-batch`
- `POST /library/pro/items/duplicate-batch`

Frontend changes:

- Library Pro page with filters, dependency/quality badges, and safe metadata
  inspection.

Tests:

- Batch list/inspect/validate works.
- Sensitive local paths are redacted.
- Path traversal rejected.
- Archive/duplicate does not modify active `GameState`.

Acceptance:

- Creators can manage production artifacts locally without leaking secrets.

Content pack schema impact: optional indexed metadata cache.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: hidden fields remain marked/redacted in
normal library views.

LLM boundary impact: no LLM library decisions.

Leak risk: local paths, hidden text, and debug export metadata.

### 12. Batch Character Card Import

Goal: Import many character cards into draft NPC/character pack data with
classification, safety reports, conflict handling, and safe export defaults.

Data structures:

- `BatchCharacterCardImportRequest`
- `BatchCharacterCardImportReport`
- `CharacterCardImportItem`
- `CharacterCardConflict`
- `CharacterCardSafetyClassification`

API changes:

- `POST /authoring/production/character-cards/import-batch-preview`
- `POST /authoring/production/character-cards/import-batch-validate`
- `POST /authoring/production/character-cards/import-batch-save`

Frontend changes:

- Batch import panel.
- Per-card safety classification.
- Conflict review and safe export preview.

Tests:

- Batch dry-run writes nothing.
- Unsafe prompts rejected/quarantined.
- Hidden facts/private fields excluded from safe export.
- Duplicate NPC ids require explicit resolution.

Acceptance:

- Multiple cards can be reviewed and converted to safe drafts without active
  world changes.

Content pack schema impact: character pack manifest may include batch import
source metadata.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: imported secrets/private summaries are
authoring-only unless validated as safe public fields.

LLM boundary impact: no trusted external prompt authority.

Leak risk: very high for imported system prompts, creator notes, secrets, and
prompt injection.

### 13. Batch Lorebook Classification

Goal: Classify many lorebook entries into safe flavor, structured fact
candidates, hidden fact candidates, NPC knowledge candidates, unsafe entries,
and package notes.

Data structures:

- `BatchLorebookClassificationRequest`
- `BatchLorebookClassificationReport`
- `LorebookClassificationItem`
- `LorebookFactCandidate`
- `LorebookSafetyIssue`

API changes:

- `POST /authoring/production/lorebook/classify-batch`
- `POST /authoring/production/lorebook/validate-batch`
- `POST /authoring/production/lorebook/save-draft`

Frontend changes:

- Batch lorebook classification table.
- Filters for safe, hidden, structured, NPC-knowledge, and unsafe entries.

Tests:

- Hidden entries do not enter normal/player output.
- Unsafe/script-like entries rejected.
- NPC knowledge candidates do not grant unknown facts automatically.
- Save uses validation gate.

Acceptance:

- Large lorebooks can be safely triaged before inclusion.

Content pack schema impact: optional classification report artifacts.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: classified entries must respect fact
visibility and NPC knowledge boundaries.

LLM boundary impact: deterministic classification by default; optional future
LLM classifier must be draft-only and fake-provider tested.

Leak risk: hidden lore text and prompt injection.

### 14. Script Package Builder

Goal: Build local script/narrative package drafts from structured scenes,
dialogue scene templates, group RP templates, quest beats, and safe staging
metadata.

Data structures:

- `ScriptPackageManifest`
- `ScriptSceneDraft`
- `ScriptBeatDraft`
- `ScriptDialogueRef`
- `ScriptPackageValidationReport`

API changes:

- `POST /authoring/production/script-package/preview`
- `POST /authoring/production/script-package/validate`
- `POST /authoring/production/script-package/save`

Frontend changes:

- Script package builder.
- Scene/beat ordering view.
- Links to dialogue/group RP scene editors.

Tests:

- Valid script package saves after validation.
- Hidden scene beats are redacted from normal report.
- Package does not execute scripts despite name.
- Active session unchanged.

Acceptance:

- Script packages are structured story content, not executable code.

Content pack schema impact: new script package manifest.

Save migration impact: none.

RP / NPC Knowledge / Visibility impact: script beats must not reveal hidden
facts to player/NPC/RP contexts unless visible.

LLM boundary impact: no LLM scene authority by default.

Leak risk: name confusion with executable scripts; hidden beat spoilers.

### 15. Campaign Starter Kit Builder

Goal: Assemble a starter campaign package from world pack, NPC pack, quest pack,
location cluster, faction template, mystery case, script package, and playtest
fixtures.

Data structures:

- `CampaignStarterKitManifest`
- `CampaignStarterKitDraft`
- `CampaignStarterDependency`
- `CampaignStarterQualityReport`
- `CampaignStarterImportPlan`

API changes:

- `POST /authoring/production/campaign-starter/preview`
- `POST /authoring/production/campaign-starter/validate`
- `POST /authoring/production/campaign-starter/export`

Frontend changes:

- Campaign assembly dashboard.
- Dependency and quality gate checklist.
- Safe package export flow.

Tests:

- Valid starter kit includes manifest and dependencies.
- Missing dependencies caught.
- Hidden/debug data excluded from safe export.
- Quality gate required before export.

Acceptance:

- A creator can assemble a local starter campaign package for reuse.

Content pack schema impact: new starter kit manifest.

Save migration impact: none for active saves; migration impact report for
target content schema.

RP / NPC Knowledge / Visibility impact: cross-package NPC/fact/quest visibility
must validate before export.

LLM boundary impact: no LLM campaign authority.

Leak risk: high due to aggregation of many package types.

### 16. Production Pipeline Dashboard

Goal: Provide a local dashboard for production status, drafts, batch validation,
quality gate, coverage plan, package safety, recent operations, and next steps.

Data structures:

- `ProductionPipelineSummary`
- `ProductionPipelineTask`
- `ProductionPipelineStatus`
- `ProductionRiskSummary`
- `ProductionRecentOperation`

API changes:

- `GET /authoring/production/summary`
- `GET /authoring/production/recent`

Frontend changes:

- Production dashboard page.
- Quick links to generators, validators, quality gate, coverage planner, and
  library pro.

Tests:

- Dashboard returns safe summaries.
- Hidden details and local sensitive paths redacted.
- Authoring disabled state handled safely.

Acceptance:

- Creator can see production readiness without opening raw files.

Content pack schema impact: none.

Save migration impact: shows migration impact summaries only.

RP / NPC Knowledge / Visibility impact: dashboard shows counts/status, not raw
hidden text.

LLM boundary impact: no LLM status decisions.

Leak risk: hidden summary/details and local paths.

### 17. Content Production CLI

Goal: Provide local CLI entry points for batch validate, batch quality gate,
batch export, coverage plan, and package inspection.

Data structures:

- `ContentProductionCLIReport`
- `ContentProductionCLIExitCode`
- `ContentProductionCLIProfile`

API changes:

- No HTTP API required; CLI calls existing services.

Frontend changes:

- Optional dashboard copy with CLI command examples.

Tests:

- CLI validates temp world/package dirs.
- CLI rejects forbidden files and path traversal.
- CLI does not call real LLM by default.
- CLI exit codes are deterministic.

Acceptance:

- Local users can run production checks in scripts without weakening safety.

Content pack schema impact: none.

Save migration impact: can report migration impact; must not mutate saves unless
future explicit migration command is added.

RP / NPC Knowledge / Visibility impact: reports are redacted like API reports.

LLM boundary impact: provider factory only; default mock/local-stub.

Leak risk: CLI stdout can leak hidden text if reports are not sanitized.

### 18. Batch Quality Gate

Goal: Extend the existing Quality Gate to evaluate batches of generated content,
packages, starter kits, imports, and production plans before save/export/apply.

Data structures:

- `BatchQualityGateRequest`
- `BatchQualityGateReport`
- `BatchQualityGateDecision`
- `BatchQualityIssue`
- `BatchQualityThreshold`

API changes:

- `POST /authoring/production/quality-gate/run`

Frontend changes:

- Batch quality gate panel.
- Pass/fail, warnings, hidden-risk, migration-impact, and coverage summaries.

Tests:

- Valid batch passes.
- Validation errors block.
- Hidden leak risks block or require debug-only override.
- Quality warnings require confirmation.
- Reports redact hidden text.

Acceptance:

- No v1.4 package/export/apply flow bypasses the batch quality gate.

Content pack schema impact: optional quality report artifacts.

Save migration impact: reports migration impact only.

RP / NPC Knowledge / Visibility impact: evaluates player/RP/NPC knowledge leak
risks across batch artifacts.

LLM boundary impact: no LLM quality judgment.

Leak risk: high if evidence snippets include hidden content; use structural
safe summaries.

## v1.4 Integration Test Requirements

1. Boundary:
   - Production draft does not modify active `GameState`.
   - Preview and validate do not write disk.
   - Save/apply/import/export/build go through validation gate.

2. Generators:
   - World pack, NPC pack, quest pack, location cluster, mystery, faction,
     script package, and campaign starter drafts are deterministic.
   - Generated drafts are schema-valid or produce validation errors.
   - No generator directly writes active sessions or active saves.

3. Batch import / package safety:
   - Batch character card import dry-run writes nothing.
   - Batch lorebook classification does not grant NPC knowledge automatically.
   - Package import rejects path traversal, `.env`, database/log/cache files,
     executable code, and remote URLs.
   - No package operation executes arbitrary code.

4. Visibility / RP / NPC knowledge:
   - Hidden facts do not enter player `visible_state`.
   - Hidden content does not enter normal production reports.
   - Private RP fields and NPC secrets remain out of player/RP prompt contexts.
   - NPC knowledge candidates remain candidates until validated/applied through
     content rules.

5. Quality:
   - Content Batch Validator catches invalid refs and schema errors.
   - Batch Quality Gate blocks validation errors and high hidden-leak risk.
   - Coverage Planner reports gaps without modifying content.

6. LLM / provider:
   - No v1.4 default test calls real OpenAI APIs.
   - Production modules do not instantiate concrete providers directly.
   - Optional future LLM draft helpers use provider factory, schema validation,
     fake-provider tests, and draft-only output.

7. Frontend / CLI:
   - Frontend build passes.
   - Authoring disabled state does not crash.
   - CLI reports deterministic safe summaries and redacts hidden/sensitive data.

## v1.4 Final Acceptance Standards

- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.
- `docs/CONTENT_PRODUCTION_BOUNDARY.md` exists.
- `docs/V1_4_ACCEPTANCE_REPORT.md` exists.
- `docs/V1_4_RELEASE_NOTES.md` exists.
- v1.4 LLM boundary audit confirms no generated content has runtime state
  authority and no real API calls occur in tests.
- v1.4 visibility/package audit confirms hidden facts, NPC secrets, private RP
  fields, hidden memory, hidden relationships, and debug details are excluded
  from player UI, narrator prompts, and normal production reports.
- v1.4 security audit confirms no arbitrary code execution, path traversal,
  `.env` / API key / DB / system file reads, remote URL fetches, or unsafe
  imports.
- Batch validation and Batch Quality Gate are used by all save/import/export
  production paths.
- No high-risk release blocker remains.

## v1.5 Candidate Directions

- Deterministic campaign director tools for pacing, scene sequencing, and
  milestone planning.
- Player-facing journal, clue board, rumor board, and faction dossier
  improvements.
- Advanced mystery/case runtime support with evidence chains and suspect
  behaviors.
- Better semantic hidden-text redaction for debug, reports, and timelines.
- Save/content migration assistant for large generated worlds.
- Local-only visual packaging wizard for release bundles.
- Optional draft-only LLM content assistants behind strict validation,
  provenance, and redaction gates.
- Content analytics for long-running worlds: play coverage, dead content,
  hidden-content exposure, NPC simulation coverage, and quest completion health.
