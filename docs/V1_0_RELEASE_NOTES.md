# v1.0 Release Notes: Stable Local Studio Edition

## Version Name

**v1.0 Stable Local Studio Edition**

## Release Goal

v1.0 is the stability release for the local interactive novel world engine and
studio. The goal is not to add a large new gameplay layer, but to freeze the
core contracts, harden quality checks, polish the local workflow, and document
the system well enough for long-term local use.

This remains a **local self-use engine**. It is not a hosted service, not a
multi-user collaboration platform, and not a public desktop distribution.

## Frozen Core Contracts

v1.0 treats the following contracts as freeze candidates. Future breaking
changes should include migration notes, compatibility tests, and release-note
entries.

- `GameState` schema and `schema_version` semantics.
- `StateDelta` operation, path, validation, and apply semantics.
- `Event` / `EventLog` ordering, replay, and debug timeline semantics.
- Player visible state and player-facing API response shapes.
- Save metadata, migration dry-run/apply behavior, and `migration_history`.
- Content pack YAML layout and validation rules.
- Mod manifest, dependency, conflict, load-order, and content-only validation
  rules.
- `LLMProvider` interface and provider factory selection.
- Player, authoring, debug, migration, mod, studio, and quality API
  classifications.

The key runtime boundary remains unchanged: **StateDelta, EventLog, and
visibility filtering are core correctness boundaries.**

## New and Finalized Capabilities

- v1.0 release criteria and checklist documentation.
- Core API contract documentation.
- Content pack schema contract documentation.
- Save migration guarantee documentation.
- Mod packaging stable contract documentation.
- Performance budget documentation and benchmark budget support.
- Release checklist automation through
  `python -m backend.app.tools.release_check --version v1.0`.
- End-to-end local workflow guide.
- v0.x to v1.0 upgrade guide.
- Final integration regression coverage for the stable local workflow.

## Stability Improvements

- Full regression suite passes with 763 backend tests.
- Frontend TypeScript and production build pass.
- Standard quality gate passes for `mist_valley`.
- Migration compatibility now covers v0.3-like through v0.9-like fixtures.
- Memory store ordering and canonicalization were hardened in prior v1.0 work
  to reduce flaky retrieval comparisons.
- Benchmark reporting now supports budget thresholds and safe report dumps.
- Player visible map exits now filter visual-hidden locations from runtime
  player-visible exits.

## API Changes

v1.0 focuses on freezing and documenting APIs rather than introducing new
player-facing surface area.

Documented API categories:

- Player API: game start/input/state, health, save/load/list/delete.
- Authoring API: world pack read/write/validate, visual editors, templates,
  import/export.
- Debug API: timeline, debug graphs, performance.
- Quality API: quality gate, reports, playtests, scenario regression,
  benchmarks.
- Migration API: migration status, dry-run, apply, history.
- Mod API: mod listing, validation, dependency/conflict/load-order status.
- Studio status/config summary API.

Player API remains restricted to player-visible data. It must not return hidden
facts, NPC secrets, hidden witnesses, hidden relationships, hidden map exits,
hidden quests, hidden items, hidden/debug memory, raw `state_deltas`, raw env,
or API keys.

Authoring, debug, performance, eval, playtest, and quality APIs are
**local-only tooling APIs**. They are not intended as public hosted service
interfaces.

## Content Pack Schema Changes

The v1.0 content pack schema is documented in `docs/CONTENT_PACKS.md` and
`docs/V1_0_CONTENT_SCHEMA_CONTRACT.md`.

Frozen or documented areas include:

- `manifest.yaml`
- `locations.yaml`, including visual map fields.
- `npcs.yaml`, including goals, schedules, knowledge, and economy-related
  fields.
- `items.yaml`, including economy and visibility fields.
- `quests.yaml`, including quest graph fields.
- `facts.yaml`, including visibility and discoverability.
- `factions.yaml`
- `rumors.yaml`
- `relationships.yaml`
- Scenario regression files.
- Template files.
- Prompt profiles.
- Local package manifest fields.

Schema evolution after v1.0 should prefer optional fields first. Breaking
changes require validation warnings, migration notes, and compatibility tests.

## Save Migration Changes

v1.0 documents and tests the save migration guarantee.

Supported migration coverage includes:

- v0.3-like saves
- v0.4-like saves
- v0.5-like saves
- v0.6-like saves
- v0.7-like saves
- v0.8-like saves
- v0.9-like saves

Migration behavior:

- Check migration status before applying.
- Run dry-run before apply.
- Dry-run must not write database state.
- Apply records `migration_history`.
- Apply failure must not destroy or overwrite the original save.
- EventLog must be preserved.
- Hidden/debug visibility classification must remain stable.

Not guaranteed:

- Manually corrupted JSON.
- Saves missing core EventLog data.
- Unknown third-party formats.

## Mod Contract Changes

The v1.0 mod contract is documented in `docs/V1_0_MOD_CONTRACT.md`.

Stable mod manifest fields include:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `content_schema_version`
- `dependencies`
- `optional_dependencies`
- `conflicts`
- `compatible_worlds`
- `content_paths`
- `migration_notes`

The mod system is content-only. It does **not** execute arbitrary code, Python,
JavaScript, scripts, or declared entry points. Mod loading rejects path
traversal, executable content, missing dependencies, conflicts, and incompatible
schema/version combinations.

## Frontend / Studio Changes

v1.0 consolidates the local studio workflow introduced across v0.7-v0.9.

Frontend/studio areas include:

- Studio Home and status summaries.
- Save migration UI.
- Mod Manager.
- Authoring visual editors.
- Validation graph.
- Template browser.
- Import/export views.
- Quality, performance, narrative, playtesting, world health, and content
  coverage dashboards.
- Settings / Local Privacy panel.

The UI remains a local studio interface. It does not read local files directly;
it uses local backend APIs. It should not display API keys or mix debug-only
data into player-facing views.

## Desktop Startup Changes

Desktop packaging remains a local startup workflow, not a public installer.

v1.0 includes improved startup scripts and documentation for:

- Python dependency checks.
- Node/npm dependency checks.
- `.env` guidance.
- Backend startup.
- Frontend startup.
- Local URL opening.
- Debug/authoring/perf status display.
- Common troubleshooting for missing env, occupied ports, missing npm install,
  missing API key, and unavailable local model.

The desktop/startup workflow must not bundle real `.env` files or API keys into
frontend or desktop artifacts.

## Quality Gate / Testing Changes

v1.0 hardens quality validation as the release gate.

Quality gate standard profile includes checks around:

- `validate_world`
- hidden leak regression
- quest completion analysis
- dead-end detection
- NPC behavior coverage
- schedule conflict detection
- economy balance
- combat balance
- social consequence coverage
- save/load/migration stress
- performance benchmark smoke tests
- scenario regression smoke tests
- mod compatibility smoke tests

Verification at acceptance time:

- `python -m pytest`: 763 passed.
- `cd frontend && npm.cmd run build`: passed.
- `python -m backend.app.tools.quality_gate --world mist_valley --profile standard`: passed.
  - Health score: 98
  - Blockers: 0
  - Errors: 0
  - Warnings: 1

Quality score is a heuristic local signal. It is not an absolute judgment of
story quality, balance, or design merit.

## Sample World / Starter Templates

`mist_valley` is polished as the v1.0 sample world and is covered by validation,
scenario regression, quality gate, and integration tests.

Starter templates finalized for v1.0 include:

- `basic_village_world`
- `mystery_quest`
- `faction_conflict_seed`
- `small_dungeon`
- `merchant_and_trade`
- `rumor_chain`
- `NPC_goal_set`
- `combat_encounter_light`

Templates do not execute scripts and do not call LLMs. Rendered content must go
through validation before use.

## Security / Privacy Changes

Security and privacy remain local-first:

- No real-looking `sk-...` API keys were found by the release checklist secret
  scan.
- `.env` files must not be tracked.
- API keys must not enter frontend code, frontend builds, content packs, saves,
  reports, or logs.
- Settings/config summaries do not return raw env.
- Import/export rejects zip slip and executable content.
- Mod loading rejects arbitrary code execution.
- Benchmark and performance reports avoid prompt text, API keys, hidden facts,
  and raw `GameState`.
- Quality, playtest, scenario, and benchmark normal reports use safe summaries.

Memory remains advisory. It is **not** an authoritative fact source and must not
override structured world state.

## Known Limitations

- v1.0 is local self-use software, not a hosted product.
- There is no cloud sync, account system, or multi-user collaboration.
- Desktop startup is not a signed installer, auto-updater, or public release
  package.
- Quality scores are heuristic and can miss design issues.
- Visual editors are practical authoring tools, not a complete professional IDE.
- Large-scale warfare, large-scale economy simulation, and full tactical combat
  remain out of scope.
- LLM support remains bounded by `LLMProvider`; local model compatibility is not
  guaranteed for every local model server.
- Release checklist currently has a known false-positive risk: tracked
  `.env.example` files may be flagged as forbidden even though safe example env
  files are required by the release criteria.

## Upgrade Notes from v0.9

Recommended upgrade path:

1. Back up existing saves, worlds, mods, templates, and `.env`.
2. Review `docs/UPGRADE_GUIDE_V0_TO_V1.md`.
3. Update `.env.example` references and ensure local `.env` remains untracked.
4. Run:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

5. Validate the sample world and your content packs.
6. Check save migration status for existing saves.
7. Run migration dry-run before apply.
8. Run quality gate:

```powershell
python -m backend.app.tools.quality_gate --world mist_valley --profile standard
```

9. Validate mods through the mod manager or mod validation tests before use.
10. Run the release checklist before tagging or freezing a local build:

```powershell
python -m backend.app.tools.release_check --version v1.0
```

Do not rely on migration for corrupted saves or unknown third-party save
formats. Migration failure should not overwrite the original save.

## Recommended v1.1 Direction

- Fix the release checklist `.env.example` false positive while preserving real
  `.env` blocking.
- Add launcher process stop/status helpers.
- Add more sample worlds and starter templates.
- Improve visual editor ergonomics without breaking frozen API/schema
  contracts.
- Add quality report history and comparison views.
- Continue local provider compatibility adapters behind `LLMProvider`.
- Further split player-safe and debug-only rule failure reasons.
