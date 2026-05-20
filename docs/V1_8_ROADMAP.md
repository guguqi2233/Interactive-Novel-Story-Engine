# v1.8 Roadmap - As Built

## Version Theme

Stable Contracts & Compatibility

## v1.8 Goal

v1.8 freezes the local compatibility layer before v2.0 platform work. It
stabilizes contract/version metadata, migration behavior, package validation,
compatibility shims, deprecated-field handling, compatibility tests, and
contract documentation.

This is an as-built roadmap. The items below describe the implemented v1.8
scope, not future work.

## Explicit Non-Goals

- No new major gameplay systems.
- No LLM world judge.
- No LLM-driven schema repair that is automatically applied.
- No arbitrary-code plugins.
- No online marketplace, cloud sync, account system, or hosted platform.
- No promise that every old save, package, module, or content pack is supported
  forever.
- No deletion of deprecated fields without metadata and migration strategy.
- No package import without validation and compatibility checks.
- No debug API data in player API.

## Completed Scope

- Compatibility Boundary Contract.
- Stable core contracts for GameState, StateDelta, and EventLog.
- Stable content, save, module, action, prompt, provider, package, API, and
  quality gate contracts.
- Schema/version compatibility matrix.
- Compatibility regression test suite.
- Migration failure recovery.
- Deprecated field policy.
- Backward compatibility shims.
- Contract docs generator.
- v2.0 compatibility checklist CLI.

## Implemented Modules

### Compatibility Boundary Contract

Goal: define version, compatibility, deprecation, shim, migration, and breaking
change rules.

Acceptance: `docs/COMPATIBILITY_BOUNDARY.md` exists; compatibility tools are
local-only and deterministic; breaking changes require migration or contract
bump.

### Stable GameState Contract

Goal: stabilize GameState metadata and serialization expectations.

Acceptance: GameState carries v1.8 contract metadata, legacy payloads can load
through compatibility paths, and hidden facts remain out of player-visible
state.

### Stable StateDelta Contract

Goal: keep state changes replayable, validated, and non-executable.

Acceptance: StateDelta carries contract metadata; contract validation rejects
invalid operations, forbidden paths, and hidden-to-visible mutations outside
rule-controlled paths.

### Stable EventLog Contract

Goal: preserve events for replay, debugging, migration, and quality analysis.

Acceptance: Event carries contract metadata, preserves state deltas, and keeps
secrets/debug payloads out of player-facing summaries.

### Stable Content Pack Schema Contract

Goal: document stable content pack schema expectations and legacy handling.

Acceptance: content pack contract docs exist; current content validation
continues to pass; deprecated schema fields warn through metadata.

### Stable Save Migration Contract

Goal: make migration explicit, validated, recoverable, and non-destructive on
failure.

Acceptance: migration preserves GameState, EventLog, hidden visibility
classification, module state, and metadata; dry-run does not write; apply
records backup/checksum data.

### Stable Module Manifest Contract

Goal: require versioned gameplay module manifests with safe permissions.

Acceptance: module manifests carry contract metadata; unsafe permissions remain
rejected; dependency/conflict compatibility remains validated.

### Stable Action Mod Contract

Goal: freeze declarative action shape and Action DSL safety expectations.

Acceptance: action definitions carry contract metadata; forbidden operations
and paths remain rejected; action results remain deterministic and rule-based.

### Stable Prompt Profile Contract

Goal: freeze prompt profile style configuration without expanding LLM authority.

Acceptance: prompt profiles carry contract metadata; hidden fact access and
state modification remain denied; exported profiles do not contain secrets.

### Stable Provider Gateway Contract

Goal: keep provider access behind the provider abstraction.

Acceptance: provider capability metadata carries contract metadata; safe
summaries do not expose API keys or raw environment values; business logic
continues to use provider factory/router paths.

### Stable Import / Export Package Contract

Goal: require local packages to be versioned, checksummed, validated, and safe
by default.

Acceptance: package manifests require contract metadata; imports reject zip
slip, executables, checksum mismatch, unsupported contract versions, and
sensitive files.

### Stable Authoring API Contract

Goal: document preview/validate/save semantics and validation-gate behavior.

Acceptance: authoring contract docs exist; preview/validate semantics remain
non-writing; save remains validation-gated.

### Stable Debug API Contract

Goal: keep debug data stable, gated, redacted, and isolated from player API.

Acceptance: debug contract docs exist; debug API remains controlled by local
debug settings and redacts secrets/hidden content by default.

### Stable Quality Gate Contract

Goal: stabilize local quality report format.

Acceptance: quality results include contract metadata, target type, checks,
thresholds, pass/fail, blockers, warnings, report refs, and redaction policy.

### Schema Version Compatibility Matrix

Goal: expose known compatibility status for current stable contracts.

Acceptance: `python -m backend.app.tools.compatibility_matrix` runs locally and
reports contract compatibility without modifying files or calling providers.

### Compatibility Test Suite

Goal: provide deterministic regression tests for legacy compatibility and
contract behavior.

Acceptance: `backend/tests/compatibility/` exists and is included in the full
pytest suite.

### Migration Failure Recovery

Goal: preserve original saves and provide recovery information when migration
apply fails.

Acceptance: apply records pre-migration checksum and backup metadata; failure
preserves original save and provides recovery plan/restore path.

### Deprecated Field Policy

Goal: prevent silent deletion of fields that old saves or content may depend
on.

Acceptance: deprecated fields require metadata, replacement hints, migration
strategy, and warning level; generated docs list known deprecated fields.

### Backward Compatibility Shims

Goal: support minimal safe compatibility for known legacy shapes.

Acceptance: shims can rename fields, fill safe defaults, detect legacy
versions, and emit warnings; they cannot change hidden/visible classification
or hide unsupported breaking changes.

### Contract Docs Generator

Goal: generate deterministic contract index, schema version matrix, and
deprecated-field docs.

Acceptance: `python -m backend.app.tools.generate_contract_docs` runs locally
and writes docs without secrets, raw env, hidden text, or user data.

### v2.0 Compatibility Checklist CLI

Goal: provide a local readiness check for core v2.0 compatibility documents.

Acceptance: `python -m backend.app.tools.v2_compatibility_checklist --json`
passes when the main contract docs exist and reports blockers when required
docs are missing.

## Test Requirements

- Full backend suite must pass with deterministic local providers:

```powershell
python -m pytest
```

- Frontend build must pass:

```powershell
cd frontend
npm.cmd run build
```

- Compatibility suite must pass:

```powershell
python -m pytest backend/tests/compatibility
```

- v2 checklist CLI must pass:

```powershell
python -m backend.app.tools.v2_compatibility_checklist --json
```

## LLM / Visibility / Security Boundaries

- LLMs remain language components, not world judges.
- Compatibility tools, migration recovery, shims, docs generator, and checklist
  do not call an LLM.
- LLM output cannot directly modify GameState.
- Compatibility shims cannot make hidden data visible.
- Prompt profiles cannot enable hidden facts or state modification.
- Provider safe summaries cannot expose API keys or raw env.
- Package import/export must reject zip slip, executables, sensitive files,
  checksum mismatch, and unsupported contract versions.
- Debug API data must remain isolated from player API.

## Final v1.8 Acceptance Standard

v1.8 is acceptable when:

- all main contract docs exist;
- release notes, acceptance report, and release audits exist;
- compatibility tests and full pytest pass;
- frontend build passes;
- v2 compatibility checklist CLI passes;
- no tracked `.env`, database, logs, caches, build outputs, backups, crash
  reports, or secrets are present;
- no high-risk LLM, visibility, package, or migration blocker remains.

## Recommended v1.9 Direction

Release Candidate Hardening:

- expand legacy fixture coverage;
- add release automation for docs/checklist/tests/build/secret scans;
- strengthen static checks for provider factory/router usage;
- improve migration diagnostics and recovery UX;
- continue hardening debug/player API isolation;
- run repeated freeze checks before v2.0.

## v2.0 Platform Preparation

- Keep contract versions explicit for core state, content, modules, packages,
  prompts, providers, and APIs.
- Maintain migration paths and deprecated-field metadata.
- Keep compatibility matrix and generated contract docs current.
- Require validation and compatibility checks before import/export/apply.
- Treat v2.0 as a platform milestone only after v1.9 hardening closes remaining
  compatibility and release-process risks.
