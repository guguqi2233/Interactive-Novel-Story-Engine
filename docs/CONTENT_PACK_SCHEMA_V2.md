# Content Pack Schema v2

Content Pack Schema v2 defines the stable v2 world manifest while preserving
safe v1 loading through compatibility shims and warnings.

## ContentPackV2Manifest

Fields: `world_id`, `name`, `version`, `schema_version`, `engine_version_min`,
`contract_version`, `modules_required`, `content_files`, `migration_policy`,
`visibility_policy`, and `package_metadata`.

## Compatibility

v1 content packs without `schema_version` load only through legacy compatibility
warnings or explicit migration. Unsupported versions fail safely. Hidden fields
must remain hidden and never enter player `visible_state`.

