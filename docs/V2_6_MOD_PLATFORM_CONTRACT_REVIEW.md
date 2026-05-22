# v2.6 Mod Platform Contract Review

## Existing Contracts

- `PackageV2Manifest` and `PackageV2Validator` provide an existing local package contract with file checksums, import dry-run, and security scanning.
- `GameplayModuleManifest` provides a declarative gameplay module contract for actions, rules, permissions, and compatibility notes.
- `ActionRegistry` registers core actions and declarative module actions. v2.6 extends this with explicit mod-action registration while preserving the existing handler boundary.
- `ProviderProfileV2` and provider profile repository already enforce the v2.5 rule that provider profiles store `api_key_env` or `secret_ref`, not raw keys.

## Existing Package Types

- Content package archives through `package_v2.py`.
- Gameplay modules through `gameplay_module_loader.py`.
- Project import/export packages through `project_packages.py`.
- Provider profile templates through Provider Gateway Pro.
- Cross-mode artifacts through `cross_mode.py`.

## Existing Validation

- `validate_world.py` and content validation cover world packs.
- `PackageV2Validator` rejects path traversal, executable suffixes, secrets, hidden/debug payloads, checksum mismatches, and unsafe files.
- `GameplayModuleLoader` rejects dangerous permissions, executable files, unsafe state schema prefixes, and incompatible module metadata.
- Project import/export filters `.env`, databases, logs, caches, `node_modules`, `dist`, provider secrets, raw prompts, raw `state_deltas`, and debug memory.

## Existing Permission Model

- Gameplay modules have boolean permission fields for code execution, filesystem/network access, LLM calls, and direct GameState mutation.
- v2.5 provider profiles have provider safety policies and secret boundaries.
- v2.6 needs one shared `ModulePermissionSet` so package manifests, rule modules, action mods, provider packs, and UI dashboards can report risk consistently.

## Existing Compatibility Checks

- Existing compatibility tools check contract versions, gameplay module dependencies/conflicts, package metadata, and project quality gates.
- Existing checks are local and deterministic; they do not call LLMs.

## Gaps Before v2.6

- Package manifests are split across content packages, gameplay modules, project packages, and provider profiles.
- There is no single package type taxonomy for script packs, world extensions, character packs, prompt/profile packs, action mods, and rule modules.
- Module browser APIs are fragmented between old local module tooling and project-scoped provider/cross-mode APIs.
- Action mod tests exist at the validator level, but not as a reusable package-level harness with safe reports.
- Audit records exist for cross-mode but not for module scan/validate/certify/import/export.

## Security Risks

- The main risk is accidental expansion from declarative content into arbitrary code execution. v2.6 must keep Python, JavaScript, shell, binary, filesystem, network, database, and secret access blocked.
- Provider Profile Packs can become a secret leak vector if raw keys or authorization headers are allowed.
- World extension patches can become destructive if target/path/operation/migration impact are not explicit.
- Action Mods can bypass the engine if they mutate `GameState` directly instead of returning `ActionResult` / `StateDelta` proposals.

## Recommended v2.6 Contract Shape

- Use `PackageManifestV2` as the common manifest for all extension packages.
- Use `ModulePermissionSet` as the shared permission and risk summary.
- Treat every extension as local-only, declarative, and validation-gated.
- Keep Action Mods inside `ActionRegistry`; handlers interpret declarations only and produce `ActionResult` / `StateDelta` proposals.
- Keep Rule Modules contract-only in v2.6: permissions and schema declarations are reviewable, but there is no runtime execution.
- Make Module Browser, Compatibility Matrix, Certification, Quality Gate, Import/Export, and Audit Trail consume the same manifest and permission contracts.
