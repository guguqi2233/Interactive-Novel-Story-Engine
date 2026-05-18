# Upgrade Guide: v0.x to v1.0

This guide describes how to move local worlds, saves, mods, prompt profiles,
templates, and quality workflows from v0.1-v0.9 project states to v1.0 Stable
Local Studio Edition.

v1.0 is still a local self-use engine. The LLM remains a language layer, not a
world judge. `GameState`, `StateDelta`, and `EventLog` remain the authoritative
facts and replay surface.

## Scope And Guarantees

Supported upgrade guidance covers project states from v0.1 through v0.9.
Practical save migration coverage is strongest for the legacy fixture families
that the migration suite validates:

- v0.3-like saves
- v0.4-like saves
- v0.5-like saves
- v0.6-like saves
- v0.7-like saves
- v0.8-like saves
- v0.9-like saves

This guide does not promise recovery for corrupted saves, manually edited JSON
with missing core fields, saves without a usable `EventLog`, or unknown
third-party formats. Migration failures should return a clear error and must
not overwrite the original save.

## v1.0 Core Changes Summary

v1.0 stabilizes the local studio contracts around:

- Core `GameState`, `StateDelta`, `Event`, and `EventLog` semantics.
- Player, authoring, debug, migration, mod, studio, and quality API contracts.
- Content pack schema, including visual authoring fields.
- Save migration dry-run/apply behavior and `migration_history`.
- Content-only mod packaging and version compatibility checks.
- `LLMProvider` and provider factory boundaries.
- Prompt profile safety boundaries.
- Quality gate, hidden leak regression, scenario regression, stress tests, and
  benchmark workflows.
- Local desktop startup scripts and documentation.

v1.0 does not add cloud sync, accounts, multiplayer, arbitrary mod code
execution, a public desktop installer, or LLM authority over world rules.

## Before Upgrading

1. Back up the whole project directory or at least local worlds, mods,
   templates, packages, databases, and saves.
2. Confirm `.env`, database files, logs, caches, `node_modules`, frontend build
   outputs, and desktop build outputs are not tracked.
3. Confirm no real API key appears in content packs, saves, fixtures, docs,
   frontend source, logs, or exported packages.
4. Run validation and tests on the pre-upgrade state when possible:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

5. Read these v1.0 documents before freezing local content:

- `docs/V1_0_RELEASE_CRITERIA.md`
- `docs/V1_0_API_CONTRACT.md`
- `docs/V1_0_CONTENT_SCHEMA_CONTRACT.md`
- `docs/V1_0_SAVE_MIGRATION_GUARANTEE.md`
- `docs/V1_0_MOD_CONTRACT.md`
- `docs/CONTENT_PACKS.md`

## From v0.1-v0.3

Early v0.x worlds may predate the stable save migration, content schema, and
authoring APIs.

Upgrade notes:

- Treat v0.1-v0.2 saves as best-effort only unless they match a supported
  legacy fixture shape.
- Ensure saves have enough structured state and event history to migrate.
  Natural-language transcript alone is not a recoverable authoritative state.
- Move world content into explicit YAML content pack files instead of engine
  code or prompt text.
- Add a `manifest.yaml` with `schema_version`, `content_pack_version`,
  `world_id`, and version metadata.
- Recheck locations, NPCs, items, quests, and facts with `validate_world`.
- Recreate player progress manually in a new v1.0 save if the old save is
  missing core `GameState` or `EventLog` fields.

Expected work:

- Convert ad hoc facts into structured `facts.yaml`.
- Mark hidden facts and discoverable facts explicitly.
- Ensure player-facing text does not contain hidden truth by accident.
- Replace any prompt-only rule with engine-side validation or rule logic.

## From v0.4

v0.4 introduced more social consequence, combat, crime, witness, rumor,
faction, and debug timeline behavior.

Upgrade notes:

- Revalidate crime/witness data so hidden witnesses do not enter player API or
  narrator context.
- Revalidate rumor text so hidden fact truth is not copied into player-facing
  rumor fields.
- Check combat and life state fields against the v1.0 content schema.
- Ensure debug timeline/state delta data stays behind debug API boundaries.
- Run hidden leak regression after migration or content conversion.

Recommended checks:

```powershell
python -m backend.app.tools.validate_world worlds/mist_valley
python -m backend.app.tools.quality_gate --world mist_valley --profile standard
```

## From v0.5

v0.5 added local authoring, memory, MemoryContextBuilder, advanced NPC
goals/planning, relationship graph, faction conflict, economy/trade,
procedural quest drafts, automated evals, plugin/mod packaging, and multi-world
save browsing.

Upgrade notes:

- Memory is still not an authoritative fact source. Do not use memory records
  as a replacement for structured `facts.yaml`, `GameState`, or `EventLog`.
- Hidden/debug memory must not enter narrator prompts or player responses.
- NPC planning remains rule-based lightweight planning, not LLM multi-agent
  autonomy.
- Procedural quest output should be treated as drafts that must pass validation.
- Add or update relationship, faction, economy, shop, and NPC goal fields to
  the v1.0 schema.
- Convert early mod manifests to the v1.0 content-only mod contract.

What to inspect:

- `npcs.yaml` goals, schedules, knowledge, merchant inventory, and visibility.
- `relationships.yaml` and `factions.yaml` visibility and ID references.
- `items.yaml` ownership, price, tradeability, hidden flags, and shop refs.
- Mod manifests for missing version/dependency/conflict fields.

## From v0.6

v0.6 formalized save migration, migration CLI/API, compatibility fixtures,
richer authoring UI, authoring preview/dry-run, visual graph backend/frontend,
playtesting agents, narrative quality evals, performance instrumentation,
advanced mod versioning, desktop prototype, local model provider stubs, and
combat expansion.

Upgrade notes:

- Confirm every save has or can receive:
  - `engine_version`
  - `schema_version`
  - `world_id`
  - `world_version`
  - `content_pack_version`
  - `created_at`
  - `updated_at`
  - `migration_history`
- Run migration status and dry-run before applying.
- Keep `EventLog` and hidden/debug visibility classifications intact during
  migration.
- Review mod manifests for engine/content schema compatibility ranges.
- Review combat stance/status fields if your world uses combat content.

Do not skip dry-run. A failed apply should not overwrite the original save, but
you should still keep an external backup before migration.

## From v0.7

v0.7 polished the local studio with Studio Home, Save Migration UI, Mod Manager
UI, Narrative Quality Dashboard, Performance Dashboard, local HTTP provider
integration, desktop startup improvements, scenario templates, quest graph
editor, playtesting dashboard, import/export, and settings/privacy UI.

Upgrade notes:

- `local_http` must be selected through `LLM_PROVIDER=local_http` and the
  provider factory. Business modules should not instantiate concrete providers.
- Scenario templates must remain YAML/template renderers, not script executors.
- Import/export packages must reject zip slip, executable files, `.env`, API
  keys, and invalid manifests.
- Settings/config summary endpoints should expose safe booleans and provider
  status, not raw env or full secrets.
- Save Migration UI must display summaries and history, not raw `GameState`.

Recommended review:

- Check `docs/DESKTOP_PACKAGING.md` and startup scripts for local-only behavior.
- Check import/export archives for manifests and checksums.
- Rebuild the frontend after pulling v1.0 UI contracts.

## From v0.8

v0.8 expanded visual world authoring: map editor, full quest graph editor, NPC
goal editor, faction/relationship editor, item/economy editor, rumor/crime
editor, validation graph, timeline replay, branch/diff, scenario regression UI,
template browser, prompt profile manager, advanced import/export, desktop shell
polish, and integrated authoring UX.

Upgrade notes:

- Location `visual` fields are optional authoring metadata. They should not
  affect movement rules or player-visible state unless explicitly exposed by a
  player-safe map API.
- Visual editor saves must go through preview, validation, and explicit save.
  They must not directly modify active session `GameState`.
- Quest graph edits must roundtrip through `quests.yaml` and validation.
- Timeline replay is debug-only and must not enter player narration.
- Prompt profiles must not add hidden facts, raw `GameState`, raw
  `state_deltas`, or API keys to prompts.
- Package imports must require dry-run/confirmation for overwrite-risk changes.

Content to revalidate:

- map visual coordinates and hidden exits
- quest graph next stages, triggers, rewards, failure paths, and visibility
- NPC goals and allowed/forbidden planning actions
- item ownership/shop visibility
- rumor/crime consequence hidden text risks
- prompt profile fields and provider filters

## From v0.9

v0.9 added the Quality & Automated Playtesting toolchain: world quality
reports, scenario expansion, scenario authoring, hidden leak regression, quest
completion analysis, dead-end detection, NPC behavior coverage, schedule
conflict detection, economy/combat/social sanity checks, save/load/migration
stress tests, performance benchmarks, narrative consistency evals, world health
dashboard, content coverage dashboard, branch diff regression, mod
compatibility stress, playtest batch runner, and quality gate.

Upgrade notes:

- Quality reports and health scores are local authoring aids, not absolute
  quality judgments.
- Quality reports must not automatically modify content packs or active saves.
- Hidden details must stay out of normal report views.
- Playtesting agents are test agents, not formal player AI.
- Quality gate pass/fail is rule/config based; the LLM does not decide it.
- Benchmark reports must not record prompt text, API keys, or hidden fact text.

Before v1.0 freeze, run:

```powershell
python -m backend.app.tools.quality_gate --world mist_valley --profile standard
```

Use `strict` for release candidates and `fast` for quick local checks.

## Save Migration Steps

Use the migration CLI/API for save upgrades. Do not hand-edit saves unless you
are recovering a backup copy and understand the schema.

### 1. Backup

Back up:

- database files
- exported save bundles
- world packs used by the save
- enabled mods
- `.env` separately if needed, but never commit it

### 2. Check Migration Status

```powershell
python -m backend.app.tools.migrate_save --list
python -m backend.app.tools.migrate_save --save-id <save_id> --status
```

Confirm the reported current version, target version, migration path, warnings,
and mod/content pack compatibility notes.

### 3. Dry-Run

```powershell
python -m backend.app.tools.migrate_save --save-id <save_id> --dry-run
```

Dry-run must not write the database. Treat dry-run errors as blockers until you
understand whether the save is unsupported, corrupted, missing core fields, or
blocked by incompatible content/mod versions.

### 4. Apply

```powershell
python -m backend.app.tools.migrate_save --save-id <save_id> --apply
```

Apply should record `migration_history`. If apply fails, the original save
should remain unchanged. Restore from backup if you suspect a local filesystem,
database, or manual-edit problem.

### 5. Verify

After migration:

- Load the save.
- Confirm `schema_version` and `migration_history`.
- Confirm `EventLog` remains present.
- Confirm hidden/debug visibility classifications did not change.
- Run a small playthrough or scenario regression.
- Run quality gate if this save/content is part of a release candidate.

## Content Pack Schema Changes

Review `docs/V1_0_CONTENT_SCHEMA_CONTRACT.md` and `docs/CONTENT_PACKS.md`.

v1.0 content packs should use explicit structured YAML:

- `manifest.yaml`: world id/name/version, `schema_version`,
  `content_pack_version`, compatible engine range, enabled mods if relevant.
- `locations.yaml`: location ids, names, descriptions, exits, locks,
  visibility, tags, optional visual map fields.
- `npcs.yaml`: NPC identity, visibility, knowledge, goals, schedules,
  relationships, merchant/shop fields, life/combat hints.
- `items.yaml`: item identity, ownership/location/container, portability,
  tradeability, price, rarity, hidden flags, tags.
- `quests.yaml`: quest/stage/objective/trigger/reward/failure path data and
  visibility.
- `facts.yaml`: fact ids, visibility, discoverability, known_by, tags, and
  player-safe summaries.
- `factions.yaml`: faction ids, reputation bands, conflicts, visibility.
- `relationships.yaml`: NPC/faction relationships, trust/fear/affinity,
  obligation, conflict, and visibility.
- `rumors.yaml`: rumor ids, linked fact ids, player-safe rumor text,
  spread/reputation effects.
- scenario regression files: deterministic input sequences and expected safe
  outcomes.
- templates: manifest plus renderable YAML drafts, never scripts.
- prompt profiles: style/config metadata only, never API keys or hidden facts.

Compatibility policy:

- New fields should be optional first.
- Breaking changes require migration and release notes.
- Validation should warn before future breaking changes become required.
- Authoring-only fields must not appear in player-visible responses.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, and hidden
  memory must remain outside player-visible content.

Run:

```powershell
python -m backend.app.tools.validate_world worlds/mist_valley
```

## Mod Manifest Changes

v1.0 mods are content-only. Update manifests to the stable contract documented
in `docs/V1_0_MOD_CONTRACT.md`.

Expected fields include:

- `id`
- `name`
- `version`
- `engine_version_min`
- `engine_version_max`
- `content_schema_version`
- `dependencies`
- `optional_dependencies`
- `conflicts`
- `load_order_hint`
- `compatible_worlds`
- `content_paths`
- `migration_notes`

Forbidden behavior:

- Python, JavaScript, shell, or other script execution.
- Executable entry points.
- Reading files outside the mod directory.
- Online downloads or marketplace behavior.
- Automatic overwrite of user worlds or saves.
- Bypassing `validate_world`, visibility rules, or migration checks.

Before enabling a v0.x mod in v1.0:

1. Validate the manifest.
2. Check dependency/conflict resolution.
3. Check load order.
4. Validate the composed content.
5. Check save migration status for saves that used older mod versions.

## Prompt Profile Changes

Prompt profiles are local configuration for style and prompt variants. They do
not change LLM permissions.

Expected fields include:

- `id`
- `name`
- `description`
- `provider_filter`
- `model_filter`
- `narrator_style`
- `intent_parser_prompt_variant`
- `narrator_prompt_variant`
- `memory_prompt_variant`
- `temperature_overrides`
- `max_output_tokens`
- `enabled`

Rules:

- Profiles must not contain API keys.
- Profiles must not add hidden facts, raw `GameState`, raw `state_deltas`, or
  debug memory to prompts.
- Profiles must not allow LLM output to directly mutate `GameState`.
- Provider selection remains through `LLM_PROVIDER` and provider factory.
- Schema validation failure should produce a clear error or safe fallback.

## Quality Gate Changes

v1.0 uses quality gate profiles:

- `fast`: quick local smoke check.
- `standard`: default pre-release local gate.
- `strict`: release candidate gate with stricter thresholds.

Run:

```powershell
python -m backend.app.tools.quality_gate --world mist_valley --profile standard
```

Depending on local module path configuration, some setups may use:

```powershell
python -m app.tools.quality_gate --world mist_valley --profile standard
```

The gate may include:

- `validate_world`
- hidden leak regression
- quest completion analysis
- dead-end detector
- NPC behavior coverage
- schedule conflict detector
- economy balance checks
- combat balance checks
- social consequence coverage
- save/load/migration stress
- performance benchmark smoke test
- scenario regression smoke test
- mod compatibility smoke test

Quality gate results are local diagnostics. They do not call a real LLM, do not
upload telemetry, do not modify active saves, and do not automatically rewrite
world packs.

## Common Errors And Fixes

### Missing `.env`

Create one from `.env.example`. Do not commit it.

### Missing `DATABASE_URL`

Set a local SQLite URL or the repository-supported default. Do not point tests
at a real user database unless you intend to operate on it.

### OpenAI Provider Missing API Key

If `LLM_PROVIDER=openai`, set `LLM_API_KEY` locally. Do not put the key in
frontend files, docs, saves, or content packs. For tests, use `mock` or
`local_stub`.

### `local_http` Missing Base URL

If `LLM_PROVIDER=local_http`, set `LOCAL_LLM_BASE_URL` and
`LOCAL_LLM_MODEL`. The provider must fail clearly when required config is
missing.

### Authoring, Debug, Eval, Playtest, Or Quality API Disabled

Enable the matching local-only environment flag only when needed:

- `ENABLE_AUTHORING_API`
- `ENABLE_DEBUG_API`
- `ENABLE_EVAL_API`
- `ENABLE_PLAYTEST_API`
- `ENABLE_QUALITY_API`
- `ENABLE_PERF_LOGGING`

These APIs are local tools, not public production endpoints.

### Content Validation Fails With Missing References

Check YAML ids for locations, NPCs, items, facts, quests, factions, rumors, and
relationships. Use the validation graph or quality reports to locate missing
references.

### Migration Reports No Path

The save may be older than supported fixtures, manually modified, missing core
metadata, or using incompatible content/mod versions. Keep the backup and
consider recreating progress in a new v1.0 save.

### Corrupted Save Fails

This is expected. Corrupted saves are not guaranteed migratable. A safe failure
should not overwrite the original save.

### Mod Validation Fails

Check dependency/conflict fields, engine/content schema compatibility, path
traversal attempts, executable files, and content validation results.

### Hidden Leak Regression Fails

Remove hidden fact text, NPC secrets, hidden witnesses, hidden relationships,
hidden map edges, hidden quest details, or debug data from player-visible
fields, normal reports, and narrator contexts.

### Frontend Build Fails

Run dependency installation in `frontend/`, then rebuild:

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

## Rollback Suggestions

- Keep immutable backups of saves before migration.
- Export save bundles before applying migration.
- Restore a world pack by replacing it with the backed-up directory.
- Restore a save by replacing the database or importing a known-good bundle.
- If migration apply fails, do not keep retrying on the only copy. Restore the
  backup and inspect the dry-run output.
- Roll back code by checking out the previous tag or branch.
- Disable authoring/debug/eval/playtest/quality APIs when troubleshooting
  normal player behavior.
- Keep old mod packages until migrated saves have been verified.

Rollback cannot reconstruct data that was never stored structurally. If an old
project kept important facts only in natural language prose, recreate them as
structured content.

## Security Tips

- Never commit `.env`, API keys, database files, logs, caches, frontend build
  output, or desktop build output.
- Keep API keys on the backend/local environment side only.
- Do not export packages containing `.env`, database connection strings, or
  local secrets.
- Do not enable debug/authoring/eval/playtest/quality APIs on untrusted
  networks.
- Do not execute mod or template code. v1.0 packages are content archives.
- Reject zip slip, path traversal, executable files, and unknown manifests when
  importing packages.
- Keep hidden facts out of player-visible text, normal quality reports,
  narrator prompts, and memory context.
- Treat memory as a recall aid, not an authoritative fact source.
- Review `git status --short` before committing v1.0 upgrades.

## v1.0 Upgrade Checklist

- [ ] Project directory backed up.
- [ ] Local saves backed up or exported.
- [ ] Content packs validated.
- [ ] Save migration status checked.
- [ ] Save migration dry-run passed.
- [ ] Save migration apply completed only after backup.
- [ ] Migrated saves load successfully.
- [ ] `migration_history` recorded.
- [ ] Hidden/debug visibility classifications preserved.
- [ ] Mods updated to v1.0 manifest contract.
- [ ] Prompt profiles validated and contain no secrets.
- [ ] Templates preview/render without scripts.
- [ ] Import/export dry-runs pass before apply.
- [ ] Hidden leak regression passes.
- [ ] Scenario regression passes or only has accepted non-blocking warnings.
- [ ] Quality gate `standard` profile passes or reports only accepted
      non-blocking limitations.
- [ ] `python -m pytest` passes.
- [ ] `cd frontend && npm.cmd run build` passes.
- [ ] No real API keys or sensitive local paths are tracked.

## Known Limitations

- v1.0 does not guarantee migration of corrupted saves or arbitrary unknown
  third-party formats.
- v1.0 does not prove every possible quest path is mathematically complete.
- Quality score is not an absolute design judgment.
- Playtesting agents are deterministic test tools, not real player AI.
- Narrative consistency evals do not use an external LLM judge.
- Desktop startup scripts are local convenience tooling, not a signed public
  installer.
- Mods and templates are content-only and cannot execute arbitrary code.
