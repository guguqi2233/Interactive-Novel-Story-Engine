# v1.0 Save Migration Guarantee

## Goal

v1.0 freezes the local save migration guarantee for the stable local studio
edition. The goal is not to promise recovery from arbitrary corruption. The
goal is to make supported historical saves verifiable, dry-runnable, safely
applicable, and non-destructive when migration fails.

Save migration remains a local deterministic operation. It does not call an
LLM, does not modify active game sessions, and does not change the player API
visibility boundary.

## Supported Migration Range

The v1.0 migration suite supports the following fixture families:

| Save family | Detected schema | Current behavior | v1.0 guarantee |
| --- | --- | --- | --- |
| v0.3-like saves | `0.3` | Apply `0.3->0.6` | Migrates to latest schema with EventLog preserved. |
| v0.4-like saves | `0.4` | Apply `0.4->0.6` | Migrates to latest schema with EventLog preserved. |
| v0.5-like saves | `0.5` | Apply `0.5->0.6` | Migrates to latest schema with EventLog preserved. |
| v0.6-like saves | `0.6` | Already latest | Migration is idempotent and does not rewrite save payloads. |
| v0.7-like saves | `0.6` | Already latest | Migration is idempotent and does not rewrite save payloads. |
| v0.8-like saves | `0.6` | Already latest | Migration is idempotent and does not rewrite save payloads. |
| v0.9-like saves | `0.6` | Already latest | Migration is idempotent and does not rewrite save payloads. |
| Legacy saves without schema metadata | `legacy` | Apply `legacy->0.6` | Metadata defaults are filled and the save migrates to latest schema. |

The current latest save schema is the engine `GameState` schema used by the
migration registry. v0.6 through v0.9 did not introduce a breaking save schema
change, so these saves are represented as current-schema saves with newer
engine/content metadata.

## Unsupported Inputs

The v1.0 guarantee does not cover:

- Manually corrupted JSON or malformed `state_json`.
- Saves missing a usable core `GameState` payload.
- Saves missing the core EventLog when a user expects replay guarantees.
- Unknown third-party save formats modified outside the migration contract.
- Databases edited directly outside the repository/migration services.
- Saves that intentionally place hidden content in player-visible fields before
  migration.

Unsupported inputs must fail clearly. They must not be silently rewritten into
apparently valid saves.

## Compatibility Matrix

| Source | Target | Registry path | Dry-run | Apply | Visibility guarantee |
| --- | --- | --- | --- | --- | --- |
| `legacy` | latest | `legacy->0.6` | Reports planned migration without DB write. | Writes migrated save and history. | Hidden/discoverable facts remain non-player-visible. |
| `0.3` | latest | `0.3->0.6` | Reports planned migration without DB write. | Writes migrated save and history. | Hidden/discoverable facts remain non-player-visible. |
| `0.4` | latest | `0.4->0.6` | Reports planned migration without DB write. | Writes migrated save and history. | Hidden/discoverable facts remain non-player-visible. |
| `0.5` | latest | `0.5->0.6` | Reports planned migration without DB write. | Writes migrated save and history. | Hidden/discoverable facts remain non-player-visible. |
| `0.6` | latest | none | Reports already latest. | No-op. | Existing visibility classifications are preserved. |
| v0.7-like current schema | latest | none | Reports already latest. | No-op. | Existing visibility classifications are preserved. |
| v0.8-like current schema | latest | none | Reports already latest. | No-op. | Existing visibility classifications are preserved. |
| v0.9-like current schema | latest | none | Reports already latest. | No-op. | Existing visibility classifications are preserved. |
| corrupted JSON | latest | none | Fails clearly. | Fails clearly. | Original save row remains unchanged. |

## Required Migration Semantics

### Deterministic

Migrations must be deterministic. Given the same source save and the same
registered migration path, the migrated `state_json`, metadata, EventLog, and
stored memory records must be stable apart from migration timestamps in newly
created history entries.

### Dry-run

Dry-run migration must:

- Build the same migration report as apply would build.
- Validate the source and migrated payload.
- Avoid writing database rows.
- Avoid changing `state_json`, `schema_version`, `migration_history`, EventLog,
  memory records, or save metadata.

### Apply

Apply migration must:

- Use `MigrationRegistry` to find the migration path.
- Validate before and after each migration step.
- Preserve EventLog rows.
- Preserve memory records and their visibility classifications.
- Record `migration_history` for every applied migration.
- Create backup metadata when a migration is actually applied.
- Leave already-current saves unchanged.

### Failure Safety

If migration fails:

- The original save row must remain unchanged.
- Existing `migration_history` must remain unchanged.
- Existing EventLog rows must remain unchanged.
- Existing memory records must remain unchanged.
- The caller must receive a clear migration error.

Migration code must not catch a failure and continue with a partially migrated
save.

### Migration History

`migration_history` is part of the v1.0 migration contract. Each applied entry
must include:

- `migration_id`
- `source_version`
- `target_version`
- `description`
- `applied_at`

Running migration again after a save reaches the current schema must be
idempotent: it must not append duplicate history entries.

## Visibility Guarantees

Migration must not change information classification:

- Hidden facts remain hidden.
- Discoverable facts remain undiscovered unless the source save already marked
  them visible.
- Debug memory remains debug-only.
- Hidden memory remains hidden.
- Player-visible facts remain the only fact IDs exposed through player-facing
  save/state surfaces.
- Raw debug data and state deltas remain outside player API responses.

Migration is allowed to normalize schema metadata, but it is not allowed to
promote hidden/debug information into player-visible fields.

## Test Coverage

v1.0 migration guarantee tests cover:

- Legacy/v0.3/v0.4/v0.5-like fixture migration to latest.
- v0.6/v0.7/v0.8/v0.9-like current-schema fixture idempotency.
- Corrupted save safe failure without overwrite.
- Migration history structure and duplicate-history prevention.
- EventLog preservation.
- Hidden/discoverable fact visibility preservation.
- Debug/hidden memory visibility preservation.
- Dry-run no-write behavior through repository migration semantics.
- Fixture secret scanning to avoid real API keys in compatibility data.

The migration compatibility suite is:

```powershell
python -m pytest backend/tests/test_migration_compatibility.py
```

The full v1.0 release gate must also run:

```powershell
python -m pytest
$env:PYTHONPATH='backend'; python -m app.tools.quality_gate --world mist_valley
```

## v1.0 Post-release Change Policy

After v1.0:

- New save fields should be optional first.
- Breaking schema changes require a new explicit migration class and fixture.
- Every new migration must support dry-run, apply, failure safety, and
  visibility preservation tests.
- Every new migration must preserve EventLog unless the release criteria
  explicitly state otherwise.
- Existing legacy fixtures must remain in the compatibility suite.
- Quality gate migration checks must remain part of release readiness.

The migration system is a compatibility boundary, not a content repair tool.
It should make valid historical saves load safely; it should not guess how to
repair arbitrary user edits or unknown third-party formats.
