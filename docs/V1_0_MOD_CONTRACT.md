# v1.0 Mod Packaging Stable Contract

## Goal

v1.0 freezes the local mod packaging contract for content-only mods. Mods can
be discovered, validated, ordered, checked for dependencies/conflicts, included
in local import/export workflows, and tested by compatibility stress tooling.

Mods must never execute arbitrary code. A v1.0 mod is a local content package,
not a plugin runtime, script extension, online marketplace item, or hot-reload
patch against an active session.

## Manifest File

Each mod root must contain a `mod.yaml` manifest. The manifest is parsed as
YAML with strict fields; unknown fields are rejected.

### Required Fields

```yaml
id: mist_mod
name: Mist Mod
version: 0.1.0
engine_version_min: 0.6.0
content_schema_version: "0.6"
entry_worlds:
  - mist_valley
content_paths:
  - content
```

### Stable v1.0 Fields

| Field | Required | Type | Semantics |
| --- | --- | --- | --- |
| `id` | yes | string | Stable mod identifier. Must be a safe local id. |
| `name` | yes | string | Human-readable local name. |
| `version` | yes | string | Mod package version. Parsed by the lightweight comparator. |
| `engine_version_min` | yes | string | Minimum engine version allowed to load/validate this mod. |
| `engine_version_max` | no | string/null | Optional maximum engine version. |
| `content_schema_version` | no | string | Content schema expected by the mod; defaults to current schema. |
| `dependencies` | no | list[string] | Required mod ids or simple version expressions. |
| `optional_dependencies` | no | list[string] | Optional mod ids or simple version expressions. |
| `conflicts` | no | list[string] | Mod ids or simple expressions that cannot be enabled together. |
| `load_order_hint` | no | integer | Deterministic ordering hint after dependencies are satisfied. |
| `compatible_worlds` | no | list[string] | World ids this mod declares compatibility with. |
| `migration_notes` | no | string | Human-authored notes for save/content migration risk. |
| `entry_worlds` | yes | list[string] | World ids inside the mod content roots to validate. |
| `content_paths` | yes | list[string] | Relative directories inside the mod root that contain world packs. |
| `author` | no | string/null | Optional local metadata. |
| `description` | no | string | Optional local description. |

The user-facing contract highlights `content_paths` because all content reads
must be rooted inside the mod directory. `entry_worlds` remains part of the
current implementation contract because the validator needs explicit world ids
inside those content paths.

## Version Rules

The v1.0 version comparator is intentionally small and deterministic:

- Numeric dot-separated versions compare by numeric parts.
- Hyphenated suffixes are treated as separators for numeric parsing.
- Missing numeric parts are padded with zero.
- Complex SAT solving is not supported.

Examples:

- `1.2.0 == 1.2`
- `1.3.0 > 1.2.9`
- `1.0.0 < 1.0.1`

## Prohibited Capabilities

v1.0 mods must not:

- Execute Python, JavaScript, shell, PowerShell, batch, native binaries, or any
  other script/code payload.
- Declare arbitrary code entrypoints such as `python_entrypoint`.
- Access files outside the mod directory.
- Use `..`, absolute paths, or path separators in dependency/conflict ids.
- Download content from the internet.
- Install dependencies.
- Modify active `GameState`.
- Hot-reload active sessions.
- Automatically overwrite user worlds, saves, templates, or profiles.
- Bypass `validate_world`.
- Expand the LLM boundary or grant LLMs state mutation authority.

The loader rejects executable file suffixes such as `.py`, `.js`, `.sh`,
`.bat`, `.cmd`, `.ps1`, `.exe`, `.dll`, and related script/code extensions.

## Validation Flow

The stable validation flow is:

1. **Manifest validation**
   - `mod.yaml` must be a YAML mapping.
   - Required fields must exist.
   - Unknown fields are rejected.
   - `entry_worlds` and `content_paths` must be non-empty.

2. **Version validation**
   - `engine_version_min` must be satisfied.
   - `engine_version_max`, if present, must not be exceeded.
   - `content_schema_version` mismatch is reported as a warning in the current
     implementation because v1.0 still supports compatibility checks before
     hard failures.

3. **Safe path validation**
   - Every `content_paths` entry must be relative.
   - No `content_paths` entry may escape the mod root.
   - Dependency, optional dependency, and conflict references must be safe ids
     or simple local version expressions, not filesystem paths.

4. **No executable content validation**
   - The mod directory is scanned for forbidden code/executable suffixes.
   - Any executable payload makes validation fail.

5. **World validation**
   - For every `content_paths` and `entry_worlds` pair, `validate_world` runs
     against the mod content root.
   - Broken content references, visibility issues, schema errors, and other
     world validation errors are included in the mod validation report.

6. **Dependency resolution**
   - Required dependencies must be present in the enabled mod set.
   - Missing dependencies fail dependency resolution.

7. **Conflict detection**
   - Enabled mods that declare conflicts with each other fail conflict checks.

8. **Load order**
   - Dependencies are loaded before dependents.
   - Ties are sorted by `load_order_hint`, then mod id.
   - Cyclic dependencies fail load-order resolution.

9. **Migration status**
   - `migration_notes` and import/export save metadata are advisory signals for
     save migration risk.
   - Mods do not run migrations directly and do not modify saves.

## Import / Export Contract

Local package import/export may include mod packages, but must preserve the mod
security contract:

- Zip slip/path traversal is rejected.
- Executable content is rejected.
- `.env`, API keys, database connection data, logs, caches, and build outputs
  are not imported.
- Valid imported mods must still pass manifest and content validation.
- Imports must not auto-overwrite existing local content unless an explicit
  workflow asks for it.

## API Boundary

Mod APIs are authoring/local tooling surfaces. They are not player-facing
runtime APIs.

Current local API surfaces include:

- `GET /authoring/mods`
- `GET /authoring/mods/{mod_id}`
- `POST /authoring/mods/{mod_id}/validate`
- `GET /authoring/mods/load-order`
- `POST /quality/mods/compatibility-stress/run`

Authoring mod APIs are gated by `ENABLE_AUTHORING_API`. Quality/stress APIs are
local quality tooling and must remain gated by local quality/eval/playtest/debug
settings.

API responses must not expose API keys, raw environment variables, or sensitive
local absolute paths in normal payloads.

## Stable Test Expectations

The v1.0 mod contract is covered by tests that assert:

- A valid content-only mod is discovered and validates.
- Missing dependencies fail dependency resolution.
- Conflicting mod pairs fail conflict detection.
- Deterministic dependency-aware load order is produced.
- Path traversal in `content_paths` is rejected.
- Executable content is rejected.
- Arbitrary executable entrypoint fields are rejected by strict manifest
  validation.
- Content schema mismatch is reported.
- Mod validation reuses `validate_world`.
- Authoring mod APIs obey `ENABLE_AUTHORING_API`.
- Mod compatibility stress catches dependency, conflict, broken reference,
  traversal, executable content, and sensitive path redaction cases.

Run the focused suites with:

```powershell
python -m pytest backend/tests/test_mod_loader.py backend/tests/test_mod_compat_stress.py
```

Run the full release suite with:

```powershell
python -m pytest
```

## Known Limits

- v1.0 does not implement online mod distribution.
- v1.0 does not execute mod code.
- v1.0 does not solve complex semantic version constraints.
- v1.0 does not hot-reload mods into active sessions.
- v1.0 does not automatically migrate saves when mods change.
- v1.0 mod compatibility stress is a local safety/regression tool, not a proof
  that all mod combinations produce ideal narrative design.

## Post-v1.0 Change Policy

After v1.0:

- New manifest fields should be optional first.
- Breaking manifest changes require a migration/compatibility note and tests.
- Any new content file type must remain data-only and pass path/executable
  safety checks.
- Any new dependency/version behavior must remain deterministic.
- Any new mod API must be local-only and gated.
- The no-arbitrary-code-execution rule is not negotiable without a separate
  security design and a new contract.
