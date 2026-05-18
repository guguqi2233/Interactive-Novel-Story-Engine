# v0.8 Release Notes

## 1. Version Name

**v0.8 - Visual World Authoring**

This is a local, self-use interactive fiction world engine release. It is not a hosted service, not an online marketplace, and not a public desktop distribution.

## 2. Version Goal

v0.8 upgrades the local studio from a mostly YAML-centered authoring environment into a visual world-authoring workspace. The release focuses on structured visual editors, safer preview/validation/save flows, graph-based debugging, package import/export, local scenario regression, and authoring UX consistency.

The authority model is unchanged:

- The world engine remains the source of truth.
- The LLM is still a language layer, not the world judge.
- Visual editors edit content packs, not active runtime `GameState`.
- Runtime state changes still go through `StateDelta` and `Event`.

## 3. New Features

### Visual Map Authoring

- Added optional location visual metadata for map layout and editor display.
- Added map graph generation from `locations.yaml` and exits.
- Added authoring map APIs for read, preview, validate, and save.
- Added frontend Map Editor for locations, exits, coordinates, region/group metadata, edge labels, and edge types.
- Player-visible map output filters hidden locations and hidden edges.

### Visual Quest Graph Editor

- Expanded quest graph authoring for quests, stages, objectives, triggers, rewards, alternate/failure paths, and visibility.
- Added graph-to-YAML and YAML-to-graph conversion.
- Added validation for invalid `next_stage`, missing references, unreachable stages, and missing terminal paths.
- Save remains validation-backed and does not modify active saves.

### NPC Goal Editor

- Added structured authoring for NPC goals, priorities, conditions, desired state, allowed actions, and forbidden actions.
- Added validation for goal ids, statuses, priorities, references, and planning action names.
- Runtime NPC planning still remains rule-bound and knowledge-bound.

### Faction / Relationship Visual Editor

- Added authoring graph support for faction relations and NPC relationships.
- Supports structured trust, fear, affinity, obligation, conflict, and visibility fields.
- Hidden relationships remain excluded from player graph responses.

### Item / Economy Editor

- Added item/economy authoring model for items, prices, trade flags, ownership, containers, merchants, and shop inventory.
- Added validation for price, ownership conflicts, merchant references, and shop inventory references.
- Hidden shop items remain filtered from player shop/economy surfaces.
- The frontend can preview/display authoring data, but authoritative trade outcomes remain backend rule results.

### Rumor / Crime Consequence Editor

- Added authoring model for rumor, crime, witness, reputation, and quest consequence chains.
- Added validation for rumor fact references, hidden fact text leakage, duplicate consequence ids, and loop-like consequence risks.
- The editor configures future content rules and does not modify active crime records.

### Visual Validation Graph

- Added validation graph schema for files, entities, references, issues, schema nodes, and structured edges.
- Missing references and visibility risks can now be inspected as graph data.
- Validation graph remains an authoring tool, not player-facing content.

### Timeline Replay Visualizer

- Added debug timeline/replay backend data for turn groups, events, state delta summaries, and replay dry-run.
- Added frontend timeline replay view in debug tooling.
- Replay dry-run is deterministic and does not write the database.
- Timeline Replay is a debug tool and never enters player narration.

### World Branch / Diff

- Added local branch metadata and branch creation for world content packs.
- Added structured diff reports for added, removed, changed, renamed-candidate, broken-reference, migration-impact, and visibility-risk data.
- Branch creation copies only whitelisted content files and does not touch active `GameState`.

### Scenario Regression Suite

- Added scenario regression cases and run reports.
- Regression runs use mock/local deterministic providers.
- Forbidden visible facts fail regression.
- Runs use temporary sessions/saves and do not modify real user saves.

### Local Template Browser

- Added local template listing, detail, preview, render, and apply flows.
- Template preview does not write disk.
- Template apply requires validation and explicit save.
- Template Browser does not call LLM and does not execute scripts.

### Prompt Profile Manager

- Added prompt profile schemas and local profile selection.
- Profiles can adjust safe style and prompt variants.
- Prompt Profiles cannot add hidden facts, raw `state_deltas`, API keys, or GameState authority.
- Provider selection remains through `LLMProvider` and provider factory.

### Advanced Import / Export Packages

- Added local package manifests and checksums.
- Added package dry-run and apply flows.
- Import rejects zip slip, executable files, `.env`, secret files, DB files, logs, checksum mismatches, and unsafe overwrite/conflict cases.
- Save import reports migration status.
- Import/Export does not execute arbitrary code.

### Desktop Shell Polish

- Updated local desktop shell documentation and startup scripts.
- Startup scripts check dependencies and local status more clearly.
- API keys and real `.env` files are not bundled or injected into frontend builds.
- Desktop shell remains a local prototype/enhancement, not a formal public release package.

### Authoring UX Integration

- Unified the Authoring workspace navigation across Map, Quests, NPC Goals, Factions/Relationships, Items/Economy, Rumors/Crime, Templates, and Validation.
- Shared preview/validate/save patterns, dirty-state UX, hidden-content warnings, local-only labels, and disabled API fallbacks.
- Authoring UI remains separate from player UI.

## 4. Behavior Changes

- Visual authoring is now the preferred local studio workflow for many content-pack areas, though raw YAML remains the underlying source.
- Content saves increasingly go through preview, validation, explicit save, and validation report display.
- Timeline replay and raw `state_deltas` are exposed only in debug tooling.
- Scenario regression and validation graph workflows provide safer feedback loops before content is treated as usable.
- Prompt profiles affect wording/style configuration only; they do not affect world authority or visibility rules.

## 5. API Changes

New or expanded local APIs include:

- Authoring map graph read/preview/validate/save.
- Quest graph preview/validate/save.
- NPC goal authoring preview/validate/save.
- Faction/relationship graph authoring.
- Item/economy authoring.
- Rumor/crime consequence authoring.
- Validation graph generation.
- Debug timeline and replay dry-run.
- World branch and diff APIs.
- Scenario regression run/report APIs.
- Template browser preview/apply APIs.
- Prompt profile list/select APIs.
- Advanced package import/export dry-run/apply APIs.

All authoring/debug/perf/eval/playtest APIs remain local tooling surfaces. They are not intended for production exposure beyond the local machine.

## 6. Frontend Changes

- Added/expanded visual authoring panels for map, quest graph, NPC goals, factions/relationships, items/economy, rumors/crime, templates, and validation.
- Added debug timeline replay UI.
- Added scenario regression UI.
- Added prompt profile controls in local settings/studio surfaces.
- Added package import/export workflows.
- Improved authoring UX consistency with shared status, warning, validation, preview, save, and hidden-content patterns.
- Player UI remains separate from authoring/debug UI and does not render authoring-only hidden content.

## 7. Content Pack Format Changes

v0.8 adds or formalizes optional content-authoring fields and schemas:

- Location `visual` fields for coordinates, region/grouping, icons, color tags, display groups, and authoring notes.
- Quest graph-compatible stage/objective/trigger/reward structures.
- NPC goal authoring fields for conditions, desired state, allowed actions, and forbidden actions.
- Faction and relationship graph authoring fields.
- Item/economy fields for prices, trade flags, rarity, ownership, merchant inventory, and hidden shop filtering.
- Rumor/crime consequence graph fields.
- Package manifest/checksum fields for local archives.
- Prompt profile fields for local provider/style configuration.

Existing `locations.yaml` files without visual fields remain compatible.

## 8. Authoring / Visual Editor Changes

- Visual editors are content-pack editors only.
- Visual editors do not directly modify active `GameState`.
- Visual editors cannot bypass validation by design.
- Quest Graph Editor does not bypass quest validation.
- Template Browser does not call LLM and does not execute scripts.
- Rumor/crime editor warns or errors on hidden fact text leakage.
- Authoring surfaces may show hidden content to the local creator, but this data is not player-visible and is not sent to narrator prompts.

## 9. Import / Export Changes

- Local package export supports manifest and checksum metadata.
- Import dry-run checks manifest, checksum, compatibility, path traversal, disallowed file types, overwrite/conflict status, and migration status.
- Import apply requires explicit confirmation.
- Import/export rejects zip slip and executable files.
- Import/export does not import `.env`, API keys, DB connection config, logs, or arbitrary code.
- Imported save bundles report migration status after import.

## 10. Desktop Shell Changes

- Desktop shell scripts and documentation were polished for local use.
- Startup flow better communicates backend/frontend status and local-only safety expectations.
- Scripts do not hardcode real API keys.
- `.env` is not bundled or committed.
- This is still a local launcher/shell prototype, not a signed installer or public desktop release.

## 11. Testing / Scenario Regression Changes

- Backend suite verified: **596 tests passed**.
- Frontend build verified after standalone rerun.
- v0.8 adds integration coverage for:
  - visual map authoring,
  - quest graph authoring,
  - NPC goal authoring,
  - faction/relationship authoring,
  - item/economy authoring,
  - rumor/crime authoring,
  - validation graph,
  - timeline replay,
  - branch/diff,
  - scenario regression,
  - templates,
  - prompt profiles,
  - import/export,
  - v0.8 end-to-end boundaries.

Scenario regression is a local test harness, not a formal player AI or live gameplay mode.

## 12. Known Limitations

- Frontend build had one transient failure during a parallel verification run, then passed immediately when rerun standalone. Watch this during final freeze.
- Authoring single-file saves validate and roll back on validation failure, but a process crash between write and rollback could leave invalid YAML. Atomic authoring writes are recommended for v0.9.
- Some mod validation errors may include local path-like data in authoring-only reports. Further path sanitization is recommended.
- Narrative eval endpoints are debug-gated rather than independently gated by `ENABLE_EVAL_API`.
- Debug timeline intentionally exposes raw `state_deltas` when debug API is enabled. It must remain local-only.
- Authoring tools intentionally expose hidden content to the local creator; they must remain separate from player/narrator surfaces.
- Save/package exports can contain full local state and must remain local artifacts.
- Desktop shell remains a local prototype, not a formal packaged desktop product.
- Visual graph layout and editor ergonomics are functional but intentionally lightweight.

## 13. Upgrade Notes From v0.7

- Re-run the full backend test suite and frontend build after pulling v0.8 changes:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

- Existing worlds should still load when `locations.yaml` lacks visual fields.
- If using authoring features, enable `ENABLE_AUTHORING_API` only for local development.
- If using timeline replay, enable `ENABLE_DEBUG_API` only locally.
- Review `.env.example` for any new local-only roots/configuration such as template or package import roots.
- Do not expose authoring/debug/perf/eval/playtest APIs on a public network.
- Treat package imports as local files: use dry-run first and verify validation results before apply.
- Prompt profiles are local configuration only and must not include API keys.

## 14. Recommended v0.9 Directions

1. Atomic authoring writes and stronger rollback durability.
2. Better path redaction for authoring/mod/validation reports.
3. Independent `ENABLE_EVAL_API` gating for narrative eval endpoints.
4. More frontend/component tests for visual editors and authoring-player separation.
5. Richer graph layout and reference picker UX.
6. Stronger branch/diff merge previews and id rename workflows.
7. More deterministic timeline replay checkpoints.
8. Safe local asset manager for images/audio references.
9. Accessibility and keyboard workflow pass for the authoring studio.
10. Continued desktop shell polish without treating it as public distribution.

## Final Note

v0.8 is accepted as a local visual authoring release. It expands creator tooling substantially while preserving the core safety boundary: the world engine is the fact source, and the LLM is only a bounded language layer.
