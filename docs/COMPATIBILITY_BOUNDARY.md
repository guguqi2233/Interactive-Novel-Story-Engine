# Compatibility Boundary

v1.8 freezes the local compatibility rules used before v2.0 platform work.
Compatibility checks are deterministic, local-only, and never call an LLM.

## Stable Version Fields

- `engine_version`: engine/runtime version that produced a save or package.
- `schema_version`: data schema version for GameState, saves, or content packs.
- `content_pack_version`: world/content package version.
- `save_version`: save schema version.
- `module_contract_version`: gameplay module manifest contract.
- `package_contract_version`: local package contract.
- `provider_contract_version`: provider gateway metadata contract.

## Rules

- Breaking changes require migration or a major contract bump.
- Deprecated fields require metadata with replacement and migration strategy.
- Save migration must preserve EventLog and hidden visibility classification.
- Package import must perform compatibility, checksum, zip-slip, executable, and secret checks.
- Module/action/prompt/provider profiles must declare contract version.
- Compatibility shims may warn and fill safe defaults, but must not make hidden data visible.

LLM output cannot repair schema failures and apply them automatically.
