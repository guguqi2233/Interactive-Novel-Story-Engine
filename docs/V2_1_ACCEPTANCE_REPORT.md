# v2.1 Acceptance Report: Unified Narrative Project Layer

## Verdict

PASS.

v2.1 is accepted as the Unified Narrative Project Layer release. The implementation adds a local `NarrativeProject` layer above the v2.0 modular platform, with project metadata, workspace layout, repository/storage, local Project API, Project Shell, shared libraries, CrossModeLink references, Novel/Tavern stubs, a World Mode adapter, project import/export, v2.0 workspace migration, project validation, and project-level quality gate integration.

v2.1 does not claim complete Novel Studio or complete Tavern Studio functionality. Novel and Tavern modes are accepted as safe project stubs only. World Mode remains governed by the existing World Engine.

## Verification Date

2026-05-22

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Results:

- `python -m pytest`: passed, `1586 passed in 119.29s`.
- `cd frontend && npm.cmd run build`: passed.
- Frontend build warning: Vite reported an existing chunk-size warning for `assets/index-CCBBxZPF.js` at `561.64 kB`. This is a non-blocking warning and does not affect v2.1 acceptance.

## Scope Accepted

### NarrativeProject

Accepted:

- `NarrativeProject` core schema exists and includes project id, name, version, timestamps, engine/schema version, optional world/campaign refs, project root, modes, libraries, settings, safety policy, and migration history.
- `project.yaml` can be created, read, saved, and validated through `ProjectRepository`.
- Project workspace layout is defined with Novel, Tavern, World, scripts, providers, quality, and export sections.
- Repository operations reject unsafe project roots and path traversal through the safe root resolver.
- Project safety policy keeps `export_secrets=False`.

### Project API / Frontend

Accepted:

- Local Project API supports list, create, get, patch metadata, validate, sections, status, mode status, World start/state, and project quality gate.
- Project API is gated through local authoring/quality controls and does not expose raw env, provider secrets, hidden facts, raw `GameState`, or raw `state_deltas`.
- Project Shell is present in the frontend.
- Novel, Tavern, World, Script, Quality, Providers, and Settings mode entry points are visible through the shell/status flow.
- Disabled or missing mode requirements return safe status instead of crashing the UI.
- Frontend build passes.

### Shared Libraries

Accepted:

- `CharacterLibrary` and `CharacterProfile` support safe summaries that omit private authoring-only notes.
- `WorldBible` and `WorldBibleEntry` distinguish flavor, structured fact, hidden, authoring note, and style note entries; hidden entries do not enter safe summaries.
- `TimelineLibrary` supports project timeline events and filters hidden/authoring-only events from safe summaries.
- `LoreFactLibrary` supports draft, flavor, structured, hidden, and authoring-note entries with mode-safe filtering.
- `ProjectPromptProfile` rejects hidden-fact access, state modification, action-result override, and visibility bypass.
- `ProjectProviderProfile` rejects raw key fields and now also rejects secret-like values in `api_key_env`; valid `api_key_env` values are environment variable names only.
- `ProjectMemoryRecord.authoritative` is fixed to `False`; memory remains context material, not world fact authority.

### CrossModeLink

Accepted:

- `CrossModeLink` and `CrossModeLinkRegistry` support create, validate, list, mark broken, and delete operations.
- Links store references only; they do not mutate source or target objects.
- Hidden links return no normal safe summary.
- Project validation now checks CrossModeLink files for broken status, missing refs, and unresolved project refs.

### Mode Router / Stubs

Accepted:

- Mode Router reports enabled/configured/missing-requirement status for project modes.
- Novel Mode Project Stub stores outlines/chapters as drafts only and does not modify `GameState`.
- Tavern Mode Project Stub stores sessions/messages/proposals only; RP proposals do not create `StateDelta` or world facts.
- World Mode adapter can start existing worlds from a project context while using the existing `InMemorySessionStore`, `GameLoop`, visible-state projection, `StateDelta`, and `EventLog` paths.
- Existing `/game/start` behavior remains compatible.

### Project Import / Export

Accepted:

- Project export creates a `ProjectPackageManifest` with checksums.
- Export excludes `.env`, API keys, databases, logs, caches, node_modules, frontend dist, backups, crash reports, executables, and secret-like text by default.
- Import dry-run validates without writing.
- Import apply requires explicit confirmation.
- Zip slip, executable files, checksum mismatch, and duplicate project ids are rejected or reported clearly.

### Migration From v2.0

Accepted:

- v2.0-style workspace detection and migration planning are implemented.
- Dry-run produces a plan and does not write target files.
- Apply creates a v2.1 `NarrativeProject` workspace under the requested target.
- Source v2.0 workspace is copied from, not modified or deleted.
- `.env`, API keys, database secrets, logs, caches, node_modules, build outputs, executables, and secret-like files are skipped.
- `migration_history` is recorded.

### Validation / Quality Gate

Accepted:

- Project validation checks `project.yaml`, workspace directories, default world references, world content validation where present, forbidden export candidates, secret-like text, hidden/debug marker risks, and CrossModeLink validity.
- Validation normal view redacts issue messages and avoids hidden text payloads.
- Project Quality Gate aggregates project validation and optional world quality gate.
- Invalid provider profile data and invalid CrossModeLink files fail validation/quality gate.
- Blockers cause project quality gate failure.

### v2.1 Integration Regression Tests

Accepted:

- v2.1 regression tests cover project create/load/list/update, Project API, shared library safe summaries, prompt/provider profile safety, memory authority, CrossModeLink validation, Novel/Tavern no-GameState-mutation behavior, World Mode adapter, import/export safety, migration safety, validation, quality gate, and frontend static Project Shell contract.

## Boundary Review

### LLM Boundary

Accepted:

- v2.1 project code does not add real LLM calls.
- `NarrativeProject`, shared libraries, CrossModeLink, Project API, import/export, migration, validation, and quality gate do not let LLM output directly enter `GameState`.
- Prompt profiles cannot enable hidden fact access, state modification, action-result override, or visibility bypass.
- Provider profiles store provider metadata and env-var references only; real API keys remain outside project files.
- Provider Gateway remains the intended model entry point.

### World Engine Boundary

Accepted:

- World Engine remains the World Mode fact source.
- World Mode state changes still flow through the existing World Engine action pipeline, `StateDelta`, and `EventLog`.
- Novel and Tavern data are draft/proposal/context records only.
- CrossModeLink only records references and does not apply state changes.

### Visibility / Cross-Mode Boundary

Accepted:

- Project World endpoints return `visible_state`, not raw `GameState`.
- Hidden facts, NPC secrets, hidden links, hidden timeline events, hidden WorldBible entries, hidden/debug memory, private character notes, and raw state deltas do not enter normal Project API or Project Shell responses.
- Project validation and quality gate normal reports avoid hidden text payloads.

### Security / Project Data Boundary

Accepted:

- Project APIs are local authoring/studio style endpoints, not public cloud APIs.
- Project repository and workspace helpers reject unsafe roots and traversal.
- Import/export rejects zip slip, executables, forbidden files, checksum mismatch, duplicate ids, and secret-like content.
- Migration does not modify the source workspace and skips secrets/artifacts.
- No v2.1 test calls a real external API.

## Known Limitations

- Novel Mode is a project stub only. It supports safe project draft metadata, not a full Novel Studio editor.
- Tavern Mode is a project stub only. It supports safe session/proposal metadata, not a full Tavern/RP chat product.
- Tavern safe context is mode-safe, but not yet a full per-NPC `npc_knowledge` prompt validator.
- Project export is a trusted local portability/export flow, not a public redacted publishing profile for all hidden world design material.
- Project validation performs pragmatic file/ref checks and does not semantically parse every future Novel/Tavern library file format.
- Frontend Project Shell is a lightweight project entry point and does not yet provide full editors for all shared libraries.
- The existing Vite chunk-size warning remains non-blocking.

## Acceptance Risks

- Future Novel/Tavern implementations must preserve the v2.1 boundary that drafts/proposals do not become world facts without explicit validation.
- Future merged context builders must continue excluding hidden facts, NPC secrets, private notes, debug memory, raw state deltas, raw prompts, and provider secrets.
- Future public project export must introduce an explicit redacted export profile before project packages are treated as shareable public artifacts.
- Project provider profile tooling must keep treating `api_key_env` as an env-var name only and must never replace it with a raw key.

No high-risk blocker remains for v2.1 acceptance.

## Recommended v2.2 Priorities

1. Build Novel Studio MVP on top of the accepted NarrativeProject layer:
   - outline editor,
   - chapter drafts,
   - revision history,
   - continuity checks,
   - safe export profiles.
2. Add multi-library Novel context builder tests proving hidden facts are excluded when CharacterLibrary, WorldBible, TimelineLibrary, LoreFactLibrary, PromptProfileLibrary, and MemoryLibrary are combined.
3. Add a public/redacted project export profile if project packages are intended for sharing beyond trusted local use.
4. Expand CrossModeLink visualization and conflict review in the frontend.
5. Prepare Tavern Studio MVP requirements, especially per-character/NPC knowledge validation before prompt assembly.

## Final Status

Accepted.

v2.1 successfully establishes the Unified Narrative Project Layer without weakening v2.0 platform boundaries. The release is suitable to proceed to v2.1 release notes and final freeze checks.
