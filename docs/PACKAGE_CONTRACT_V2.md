# Package Contract v2

Package v2 is the unified local package format for worlds, modules, plugins,
scripts, character transfer, prompt experiments, backups, and campaign exports.

## PackageV2Manifest

Fields: `package_id`, `package_type`, `version`, `contract_version`,
`engine_version_min`, `schema_versions`, `included_files`, `checksums`,
`dependencies`, `conflicts`, `redaction_policy`, `compatibility_policy`,
`created_at`, and optional signature placeholder.

## Import / Export Rules

- Import dry-run writes nothing.
- Import apply requires explicit confirmation.
- Every included file requires a checksum.
- Zip slip, absolute paths, executable files, `.env`, API keys, logs, caches,
  databases, frontend builds, backups, and crash reports are rejected by default.
- Safe packages cannot include hidden text, debug memory, raw prompts, or raw
  state deltas.
- Compatibility checks are required before apply.

Legacy v1 packages may enter a warning/migration path but are not silently
treated as v2.

