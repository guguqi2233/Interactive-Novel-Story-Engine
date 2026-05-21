# Plugin API Contract v2

Plugins are local platform bundles. A plugin may include modules, content packs,
prompt profiles, authoring extensions, templates, and script packages. Plugin
loading is manifest-only and never executes package code.

## PluginManifest

Required fields: `plugin_id`, `name`, `version`, `contract_version`,
`plugin_type`, `engine_version_min`, `dependencies`, `conflicts`,
`included_modules`, `included_content_packs`, `included_prompt_profiles`,
`included_authoring_extensions`, `included_templates`,
`included_script_packages`, `permissions`, `checksums`, and
`redaction_policy`.

Default permissions are all false: `execute_code`, `access_network`,
`access_filesystem`, `call_llm`, and `modify_game_state_directly`.

## Rules

- Missing or unsupported `contract_version` is rejected.
- Unsafe permissions are rejected.
- Plugin import/export must pass package validation and compatibility checks.
- Plugins cannot read `.env`, API keys, databases, logs, or arbitrary files.

