# v3.4 Authoring / Mod UI Contract Review

## Current Authoring Routes

- Authoring Studio is exposed through the local frontend authoring workspace and existing FastAPI authoring endpoints.
- Current UI surfaces include project dashboard, map/location authoring, quest graph, NPC goals, social/faction relationships, item/economy, rumor/crime, RP character authoring, templates, world pack wizard, local content library, merge/diff review, Action Mod editor, and advanced module panels.
- Script / Mod Platform surfaces are available inside the project shell through local module scan, validation, permissions, compatibility, certification, quality gate, and audit summaries.

## Current Authoring Components

- The frontend remains mostly monolithic in `frontend/src/App.tsx`.
- Existing reusable authoring pieces include `AuthoringActionBar`, validation panels, preview panels, world pack wizard, template and package builders, map and graph editors, Action Mod editor, and local import/export profile panels.
- v3.4 adds a lightweight `AuthoringWorkspaceShell` for local package review surfaces. It does not replace existing editors or change their data model.

## Current Mod UI Components

- Module Browser uses `fetchProjectModules`, `scanProjectModules`, `fetchProjectModule`, and `validateProjectModule`.
- Permission review uses `fetchProjectModulePermissions` and `fetchProjectModulePermissionsSummary`.
- Compatibility review uses `fetchProjectModuleCompatibility` and `buildProjectModuleCompatibilityMatrix`.
- Certification and quality use `certifyProjectModule` and `runProjectModuleQualityGate`.
- Audit uses `fetchProjectModuleAudit`; Cross-Mode audit remains separate and safe-summary only.

## Current Data Flow

- Authoring editors operate on local drafts, YAML content, or package metadata.
- Apply/import/export paths must go through backend validation, dry-run or preview, and explicit confirmation when writes occur.
- Module browser reads local manifests and metadata only. It does not execute packages or enable modules.
- Provider profile package rules require `api_key_env` or `secret_ref`; raw provider keys are invalid.

## Current Validation / Quality UX

- World and project validation already exist through content validation and project validation APIs.
- Module validation, compatibility matrix, local advisory certification, and Mod Quality Gate are available as local safe summaries.
- v3.4 UI consolidates these signals so blockers are visible before import/apply/export.

## Current Import / Export UX

- Import/export APIs are local and dry-run-first where supported.
- Existing policies reject or exclude `.env`, API keys, provider secrets, databases, logs, caches, build outputs, executable payloads, path traversal, debug-only data, and mature/private content by default.
- Import/export UI must not present a remote marketplace, remote package download, upload, or cloud sync path.

## Current Apply / Dry-Run UX

- World pack wizard, templates, import flows, merge assistant, and cross-mode apply paths already use validation and confirmation concepts.
- v3.4 adds shared Authoring Diff / Preview / Dry-Run and Safe Apply UI surfaces to make the required sequence explicit.
- Safe Apply publishes only to local project/content pack files. It must not write active saves or active runtime `GameState`.

## Privacy / Visibility Risks

- Normal authoring UI must not show hidden facts, NPC secrets, debug memory, raw prompts, raw `state_deltas`, raw env, API keys, or provider secrets.
- Debug-only details must remain gated and must not be shown in normal authoring panels.
- Module import/export and provider/profile package views must never show plaintext secrets.

## Mod Permission Risks

- Dangerous permissions are default-deny: `execute_code`, `access_filesystem`, `access_network`, `read_secrets`, `write_database`, `modify_game_state_directly`, `bypass_visibility`, and `call_llm`.
- v3.4 does not implement runtime permission overrides or arbitrary-code plugins.
- Rule Modules are contract/manifests only in v3.4 and do not execute runtime code.

## Recommended v3.4 Authoring UI Shape

- Keep the existing local authoring editor surfaces, but wrap package/mod review in a consistent workspace shell.
- Make validation, permission, compatibility, certification, quality, audit, backup, diff, and safe apply surfaces visible before write operations.
- Treat missing data as `not run`, `not configured`, or disabled rather than inventing support.
- Keep all high-risk actions local, dry-run-first, validation-gated, and confirmation-gated.
