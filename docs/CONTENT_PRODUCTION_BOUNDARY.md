# Content Production Boundary Contract

## Purpose

v1.4 introduces the Content Production Pipeline: local tools for producing
world packs, NPC packs, quest packs, location clusters, mystery cases, faction
templates, script packages, campaign starter kits, batch imports, and production
reports.

The pipeline is a content-authoring system. It is not a runtime authority and
not a second world engine.

The core rule is:

Content production may create drafts, candidates, packages, previews,
validation reports, and safe summaries. It must not directly mutate active
`GameState`.

## Boundary Concepts

### production_draft

A local draft of future content. A draft can contain proposed YAML, structured
entities, imported card data, template output, package metadata, or generated
content candidates.

A production draft is not active runtime state. It is not visible to the player
unless explicitly saved into a content pack, loaded into a runtime session, and
then exposed by normal visibility rules.

### generated_content_candidate

A structured candidate produced by a deterministic generator or a future
draft-only assistant. It may be invalid, incomplete, hidden, unsafe, or
duplicated. It becomes content only after preview, validation, explicit save or
apply, and gate approval.

### batch_import_candidate

An imported local item queued for review, such as a character card, lorebook
entry, package, template, or starter kit component.

Batch import candidates default to dry-run review and do not write active world
packs.

### production_package

A local package artifact assembled from content drafts. A package is data. It
must not execute scripts, run plugins, fetch remote URLs, or read local secrets.

### package_manifest

Structured package metadata describing package type, ids, files, dependencies,
schema version, safety profile, validation status, and quality status.

The manifest is not a permission grant. It cannot bypass validation gates,
quality gates, path checks, or visibility rules.

### explicit_apply

A user-confirmed operation that applies a validated draft/package to a content
pack. Explicit apply is separate from preview and validation.

By default, explicit apply writes content-pack files only. It does not modify
active sessions or active `GameState`.

### validation_required

All save, apply, import-apply, export/build, and batch apply paths must pass
`AuthoringValidationGate` or a stricter v1.4 batch gate that includes it.

Validation errors block the operation.

### quality_required

Package builds and release-oriented batch operations must pass the relevant
Quality Gate or Batch Quality Gate. Quality warnings may require explicit
confirmation. High hidden-leak risk blocks normal operations by default.

### active_world_pack

The content pack on disk that can be loaded by the world engine. Production
tools may write this only through explicit save/apply flows after validation.

### active_game_state

The runtime `GameState` of an active session. Content production tools must not
directly modify it.

Runtime changes still happen only through gameplay, system ticks, rules,
`StateDelta`, and `EventLog`.

## Policy Implementation

The shared policy module is:

`backend/app/engine/content/content_production_boundary.py`

It defines:

- `ContentProductionPolicy`
- `ContentProductionConcept`
- `ContentProductionOperation`
- `ContentProductionDecision`
- `ContentProductionDraft`
- `ContentProductionCheckRequest`
- `ContentProductionCheckResponse`
- `ProductionHiddenContentRef`
- `ProductionSafeSummary`

The policy is read-only. It does not write disk, does not apply deltas, does not
call LLM providers, and does not execute package content.

## Required Flow

All v1.4 content production modules must follow this flow:

1. Generate or import draft/candidate/package data.
2. Preview without writing disk.
3. Validate without writing disk.
4. Run validation gate for save/apply/import/export/package build.
5. Run quality gate for package/release-oriented operations.
6. Require explicit user confirmation for apply/batch apply.
7. Require dry-run before batch apply.
8. Write only content-pack/package files after gates pass.
9. Never directly write active `GameState`.

## Allowed

- Generate deterministic draft content.
- Import local files into dry-run candidates.
- Build safe package manifests.
- Produce previews and validation reports.
- Produce normal reports using safe summaries, ids, counts, and redacted hidden
  references.
- Write content-pack/package files after explicit gated save/apply.
- Use debug/local reports for deeper diagnostics when explicitly gated.

## Forbidden

- Directly modifying active `GameState`.
- Applying generated content to active sessions.
- Writing disk during preview.
- Writing disk during validate.
- Batch import writing active world packs by default.
- Batch apply without a dry-run.
- Apply without explicit confirmation.
- Save/apply/import/export/build without validation gate.
- Package build without quality gate where required.
- Executing scripts or arbitrary code from any package.
- Reading `.env`, API keys, databases, logs, caches, build outputs, or system
  files as source content.
- Fetching remote URLs automatically.
- Letting hidden content enter normal production reports.
- Letting generated prose become authoritative facts without schema validation
  and visibility classification.

## Hidden Content And Reports

Normal production reports must not include raw hidden content.

They may include:

- hidden item counts
- hidden ids when safe
- redacted references
- issue codes
- file/entity paths
- safe summaries

They must not include:

- hidden fact text
- NPC secrets
- private RP profile text
- hidden memory text
- debug-only memory text
- hidden relationship notes
- raw `GameState`
- raw `state_deltas`
- API keys or local secret paths

Debug reports may include more structural detail only behind local debug gates.
Debug payloads must not be reused in player UI, narrator prompts, RP prompts,
or normal production dashboards.

## LLM Boundary

v1.4 content production does not grant new LLM authority.

Generators are deterministic by default. If a future draft helper uses an LLM,
it must:

- use the provider factory
- use schema-validated output
- produce drafts only
- require preview, validation, explicit save/apply, and gates
- never write active `GameState`
- never bypass hidden-content redaction
- use mock/local-stub/fake providers in default tests

The LLM remains a language/draft assistant, not a world judge and not a package
executor.

## Import / Export Safety

Production import/export must keep the v1.2 package rules:

- no path traversal
- no executable package code
- no `.env`
- no API keys
- no database files
- no log/cache/build output files
- no remote URL fetching
- no automatic overwrite of user worlds
- no active `GameState` mutation

## Relationship To Authoring Boundary

The v1.2 Authoring Boundary still applies.

Content Production extends authoring with batch and package-oriented flows, but
does not override:

- `AuthoringValidationGate`
- explicit save/apply
- hidden field redaction
- local-only authoring/debug APIs
- active `GameState` separation

## Acceptance Requirements

- Preview does not write disk.
- Validate does not write disk.
- Generated drafts do not modify active `GameState`.
- Apply requires explicit confirmation and validation gate.
- Batch apply requires dry-run.
- Hidden content does not enter normal production reports.
- Packages do not execute scripts.
- No real LLM provider is called by boundary policy or tests.
