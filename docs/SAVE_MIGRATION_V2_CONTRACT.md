# Save Migration Contract v2

Save migration v2 upgrades v1.x saves into v2 metadata while preserving original
saves, EventLog, hidden visibility classification, module state, and save
metadata.

## SaveV2Metadata

Fields: `save_version`, `game_state_schema_version`, `engine_version`,
`content_pack_version`, `module_versions`, `migration_history`, and `checksum`.

## Rules

- Dry-run writes nothing.
- Apply creates a backup before migration.
- Failure preserves the original save.
- EventLog and hidden visibility classifications must be preserved.
- Unsupported versions fail safely and are not auto-repaired.

