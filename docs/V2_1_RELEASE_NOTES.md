# v2.1 Release Notes: Unified Narrative Project Layer

## Version Name

v2.1 Unified Narrative Project Layer

## Version Goal

v2.1 turns the v2.0 local modular narrative RPG platform into a three-mode project foundation. The main addition is `NarrativeProject`: a local project container that can organize Novel drafts, Tavern/RP sessions, World play, scripts, mods, provider profile references, shared libraries, quality reports, exports, and migration metadata.

This is the data foundation for the future Novel / Tavern / World three-in-one platform. It is not an online platform, not a marketplace release, and not a complete Novel or Tavern product.

LLM remains the language layer. World Engine remains the fact source for World Mode.

## New Features

- Added `NarrativeProject` schema with project metadata, engine/schema version, optional world/campaign references, mode config, library references, settings, safety policy, and migration history.
- Added local project workspace layout:
  - `project.yaml`
  - `novel/`
  - `tavern/`
  - `world/`
  - `scripts/`
  - `providers/`
  - `quality/`
  - `exports/`
- Added `ProjectRepository` for create, load, save, list, update, and validate flows.
- Added local Project API and Project Shell.
- Added shared libraries:
  - Character Library
  - World Bible
  - Timeline Library
  - Lore / Fact Library
  - Prompt Profile Library
  - Provider Profile Library
  - Memory Library
- Added `CrossModeLink` for references between Novel, Tavern, World, Script, Quality, and Settings assets.
- Added Mode Router with safe Novel, Tavern, World, Script, Quality, and Settings status.
- Added Novel Mode project stub.
- Added Tavern Mode project stub.
- Added World Mode project adapter.
- Added Project import/export package flow.
- Added v2.0 workspace to v2.1 project migration flow.
- Added Project Validation.
- Added Project Quality Gate integration.
- Added v2.1 integration regression tests and audits.

## Behavior Changes

- Project workflows can now be organized around `NarrativeProject` rather than only world/campaign directories.
- World Mode can be launched through a project-aware endpoint while still using the existing World Engine runtime.
- Novel and Tavern mode data are explicitly project drafts/proposals and are not World facts.
- CrossModeLink stores relationships between assets but does not apply conversions or state changes.
- Provider profiles in project files are metadata and environment-variable references only.
- Project export/import now applies project-specific manifest, checksum, zip slip, executable, duplicate id, and secret filtering checks.

## API Changes

Added local Project API endpoints:

- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `GET /projects/{project_id}/sections`
- `GET /projects/{project_id}/status`
- `POST /projects/{project_id}/validate`
- `GET /projects/{project_id}/modes`
- `GET /projects/{project_id}/modes/{mode}`
- `POST /projects/{project_id}/world/start`
- `GET /projects/{project_id}/world/state/{session_id}`
- `POST /projects/{project_id}/quality-gate/run`

Project API endpoints are local authoring/studio endpoints. They are not public cloud APIs and should not be exposed as a public service.

Existing `/game/start` and related World APIs remain compatible.

## Frontend Changes

- Added Project Shell in the frontend.
- Added project list/create/open/validate controls.
- Added mode cards for Novel, Tavern, World, Script, Quality, Providers, and Settings.
- Novel Mode displays a safe stub message for future Novel Studio work.
- Tavern Mode displays a safe stub message for future Tavern Studio work.
- Project Shell normal UI does not display API keys, raw env, hidden facts, raw GameState, or raw state deltas.

## Project Workspace Changes

The recommended v2.1 project layout is:

```text
project/
  project.yaml
  novel/
    outlines/
    chapters/
    drafts/
    exports/
  tavern/
    characters/
    sessions/
    lorebooks/
  world/
    content_pack/
    saves/
    campaigns/
  scripts/
    quests/
    templates/
    mods/
  providers/
    profiles/
  quality/
    reports/
    playtests/
    evals/
  exports/
```

Project workspace creation does not create `.env`, real key files, databases, logs, caches, `node_modules`, frontend dist, desktop build outputs, backups, or crash reports.

## Shared Library Changes

- Character profiles have public summaries and authoring-only private notes.
- World Bible entries distinguish flavor, structured facts, hidden entries, authoring notes, and style notes.
- Timeline events can reference novel, tavern, world, authoring, imported, or draft events.
- Lore/fact entries distinguish flavor, structured, hidden, draft, and authoring-note material.
- Prompt profiles can select style and prompt variants but cannot access hidden facts, modify state, override action results, or bypass visibility.
- Provider profiles can store provider type, display name, capabilities, allowed modes, fallback ids, and `api_key_env` references. They cannot contain raw API keys.
- Project memory records are non-authoritative by default and cannot become World facts by being linked.

## Cross-Mode Changes

- CrossModeLink can link Novel, Tavern, World, Script, Quality, and Settings refs.
- Links can be draft, validated, broken, or deprecated.
- Link validation checks missing or unresolved references.
- Hidden links do not appear in normal safe summaries.
- CrossModeLink never modifies GameState, never writes StateDelta, and never changes visibility by itself.

## Import / Export Changes

- Added `ProjectPackageManifest` for `narrative_project` packages.
- Export includes project-safe sections and checksums.
- Export skips or rejects:
  - `.env`
  - API keys
  - database files
  - logs
  - caches
  - node_modules
  - frontend dist
  - desktop build outputs
  - backups
  - crash reports
  - executable/script files
  - secret-like text
- Import dry-run does not write.
- Import apply requires explicit confirmation.
- Zip slip, executable files, checksum mismatch, and duplicate project id are rejected.

Project export is a local portability/export mechanism. It is not yet a public redacted sharing profile for all hidden world-design content.

## Migration From v2.0 Changes

- Added detection for v2.0-style workspace roots.
- Added project migration planning.
- Added migration dry-run.
- Added migration apply with explicit target project root.
- Migration copies supported sections into the v2.1 workspace layout:
  - worlds
  - saves
  - mods/modules/action mods
  - templates
  - provider profiles
  - quality reports
- Migration skips `.env`, API keys, database secrets, logs, caches, node_modules, build outputs, backups, crash reports, executables/scripts, and secret-like files.
- Migration records `migration_history`.
- Source v2.0 workspace is not deleted or modified.

## Testing / Validation Changes

- Added v2.1 integration tests for:
  - NarrativeProject schema, workspace, repository
  - Project API
  - Project Shell static contract
  - Shared library safe summaries
  - Prompt/Profile safety
  - ProviderProfile secret rejection
  - Memory non-authority
  - CrossModeLink validation
  - Novel/Tavern no-GameState-mutation behavior
  - World Mode project adapter
  - Project import/export safety
  - v2.0 migration safety
  - Project validation
  - Project quality gate
- Acceptance verification:
  - `python -m pytest`: `1586 passed`
  - `cd frontend && npm.cmd run build`: passed, with the existing non-blocking Vite chunk-size warning.

## Known Limitations

- Novel Mode is a stub, not a complete novel editor.
- Tavern Mode is a stub, not a complete Tavern/RP chat system.
- World Mode still uses the existing World Engine and does not gain a new fact model.
- CrossModeLink only stores references and validation state; it does not automatically convert Novel/Tavern assets into World facts.
- Novel and Tavern outputs are drafts/proposals by default, not authoritative World facts.
- Tavern safe context is mode-safe, but full per-NPC `npc_knowledge` validation belongs to a future Tavern Studio phase.
- Project export is safe for local portability, but not yet a public redacted package profile.
- Frontend Project Shell is a lightweight entry point and does not yet include full shared-library editors.
- The existing Vite chunk-size warning remains non-blocking.

## Upgrade Notes From v2.0

- Existing v2.0 worlds, saves, modules, templates, providers, and quality reports can be migrated into a v2.1 `NarrativeProject` workspace through the migration tool.
- Always run migration dry-run first.
- Migration apply creates a new v2.1 project target and should not overwrite or delete the source v2.0 workspace.
- Real API keys must remain in local env or local secret config, not in project files.
- Provider profiles should use env-var references such as `LLM_API_KEY`, not raw key values.
- World gameplay behavior remains compatible; existing `/game/start` still works.
- Project-aware World start is additive and does not replace the existing World API.

## Recommended v2.2 Direction

- Build Novel Studio MVP on top of the accepted project layer.
- Add outline/chapter drafting, revision history, continuity checks, and safe novel exports.
- Add multi-library Novel context builder tests that prove hidden facts stay excluded.
- Add public/redacted project export profile before public sharing.
- Expand CrossModeLink visualization and conflict review.
- Prepare Tavern Studio MVP, especially NPC-knowledge-aware prompt/context validation.

## Boundary Reminder

- v2.1 is the data base for the three-in-one platform.
- LLM is still not the world judge.
- World Mode still uses the existing World Engine.
- `GameState` is still modified only through World Engine rules and `StateDelta`.
- `EventLog` remains the record of World actions.
- ProviderProfile does not contain real API keys.
- Project export does not include secrets by default.
