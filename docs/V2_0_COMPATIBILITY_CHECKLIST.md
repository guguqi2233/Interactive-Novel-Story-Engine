# v2.0 Compatibility Checklist

## Checklist Purpose

This checklist records the compatibility readiness conditions that must remain
true before the project can move from v1.8 Stable Contracts & Compatibility
toward v1.9 Release Candidate Hardening and a future v2.0 platform milestone.

It is a local readiness document. It does not claim that v2.0 is complete.

## Contract Readiness Checklist

- [x] GameState Contract: `docs/GAMESTATE_CONTRACT.md`
- [x] StateDelta Contract: `docs/STATEDELTA_CONTRACT.md`
- [x] EventLog Contract: `docs/EVENTLOG_CONTRACT.md`
- [x] Content Pack Schema Contract: `docs/CONTENT_PACK_SCHEMA_CONTRACT.md`
- [x] Save Migration Contract: `docs/SAVE_MIGRATION_CONTRACT.md`
- [x] Module Manifest Contract: `docs/MODULE_MANIFEST_CONTRACT.md`
- [x] Action Mod Contract: `docs/ACTION_MOD_CONTRACT.md`
- [x] Prompt Profile Contract: `docs/PROMPT_PROFILE_CONTRACT.md`
- [x] Provider Gateway Contract: `docs/PROVIDER_GATEWAY_CONTRACT.md`
- [x] Package Contract: `docs/PACKAGE_CONTRACT.md`
- [x] Authoring API Contract: `docs/AUTHORING_API_CONTRACT.md`
- [x] Debug API Contract: `docs/DEBUG_API_CONTRACT.md`
- [x] Quality Gate Contract: `docs/QUALITY_GATE_CONTRACT.md`

## Tooling Checklist

- [x] Compatibility matrix CLI:

```powershell
python -m backend.app.tools.compatibility_matrix
```

- [x] Contract docs generator CLI:

```powershell
python -m backend.app.tools.generate_contract_docs
```

- [x] v2 compatibility checklist CLI:

```powershell
python -m backend.app.tools.v2_compatibility_checklist
```

- [x] Compatibility tests:

```powershell
python -m pytest backend/tests/compatibility
```

## Migration Readiness Checklist

- [x] Migration dry-run does not write user save data.
- [x] Migration apply records pre-migration checksum.
- [x] Migration apply creates a recoverable backup before changing save data.
- [x] Migration failure preserves the original save.
- [x] Migration recovery plan is available.
- [x] EventLog is preserved.
- [x] Hidden visibility classification is preserved.
- [ ] v1.9 should expand legacy fixture coverage beyond the current v1.8 suite.

## Package / Import / Export Readiness Checklist

- [x] Package manifests require contract version.
- [x] Package imports validate checksums.
- [x] Package imports reject zip slip.
- [x] Package imports reject executable files by default.
- [x] Safe exports exclude `.env`, API keys, logs, caches, databases, raw env,
  and hidden text by default.
- [x] Import dry-run does not write files.
- [x] Import apply requires explicit confirmation.
- [ ] v1.9 should add broader fixture coverage for old package shapes.

## Module / Action Mod Readiness Checklist

- [x] Gameplay module manifests declare contract version.
- [x] Declarative actions declare contract version.
- [x] Unsafe module permissions are rejected.
- [x] Action DSL remains declarative and non-executable.
- [x] Module/action compatibility does not change hidden/visible
  classification.
- [ ] v1.9 should add more compatibility fixtures for third-party-like module
  and action layouts.

## Prompt / Provider Readiness Checklist

- [x] Prompt profiles declare contract version.
- [x] Prompt profiles cannot enable hidden fact access.
- [x] Prompt profiles cannot enable state modification.
- [x] Provider capability metadata declares contract version.
- [x] Provider safe summaries exclude API keys and raw env.
- [x] Provider routing/factory remains the intended model-call entry point.
- [ ] v1.9 should strengthen static checks for direct provider construction.

## Security / Privacy Checklist

- [x] `.env` must remain untracked.
- [x] Databases, logs, caches, frontend build outputs, desktop build outputs,
  backups, and crash reports must remain untracked.
- [x] Contract docs and generated docs must not include API keys, raw env,
  hidden text, raw GameState, or user data.
- [x] Debug API data must not enter player API.
- [x] Compatibility tools must not call real external APIs.
- [x] Package import/export must not execute package contents.
- [ ] Final v2.0 release automation should repeat tests, build, secret scan,
  tracked-artifact scan, and checklist validation.

## Known Gaps for v1.9 RC Hardening

- Broader legacy fixtures are needed before a v2.0 platform claim.
- Release automation should verify all required docs, tests, build, secret
  scans, and tracked-artifact scans.
- Provider factory/router usage would benefit from stronger static checks.
- Migration recovery UX can provide clearer user-facing diagnostics.
- Compatibility matrix coverage should grow as more legacy formats are
  encountered.

## Criteria for Entering v2.0

The project may enter v2.0 only when:

- all required contracts are present and reviewed;
- compatibility tests, full pytest, and frontend build pass;
- v2 checklist CLI passes with no blockers;
- release audits show no high-risk LLM, visibility, security, package, or
  migration blocker;
- package/import/export paths enforce validation and compatibility checks;
- deprecated-field metadata is complete for fields still accepted from legacy
  inputs;
- no secrets or local build/runtime artifacts are tracked;
- v1.9 release-candidate hardening has closed known compatibility gaps.
