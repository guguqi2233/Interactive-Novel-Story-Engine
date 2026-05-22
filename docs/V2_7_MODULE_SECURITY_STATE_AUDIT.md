# v2.7 Module Security / State Audit

## Verdict

v2.7 Advanced World Simulation Modules are **not blocked** for release on module
security or state-boundary grounds in the current implementation. The audited
module layer does not execute package code, does not access the network, does
not read secrets, does not write databases directly, and uses local
`StateDelta` / `Event` objects for runtime effects.

Verification date: 2026-05-22.

## Audited Files

- `backend/app/engine/advanced_modules.py`
- `backend/app/engine/module_state.py`
- `backend/app/playtesting/module_playtest.py`
- `backend/app/quality/module_quality_gate.py`
- `backend/app/quality/module_compatibility_stress.py`
- `backend/app/platform/mod_import_export.py`
- `backend/tests/test_v27_advanced_modules.py`
- `backend/tests/test_v27_advanced_module_integration_regression.py`

## Passed Items

1. **No arbitrary code execution**
   - The v2.7 advanced module implementation contains rule/helper functions,
     Pydantic schemas, and deterministic or seeded-random resolution logic.
   - The v2.7 integration tests statically check that `advanced_modules.py`
     does not contain obvious `eval(` or `exec(` usage.
   - Import dry-run rejects executable payloads through existing package
     security rules.

2. **No filesystem access from modules**
   - `advanced_modules.py`, `module_state.py`, module playtests, compatibility
     stress, and module quality gate do not expose module-authored filesystem
     access.
   - Filesystem handling remains in import/export and browser services, which
     use package path validation and forbidden file checks.

3. **No network access from modules**
   - The audited v2.7 module runtime code has no `requests`, `httpx`, `socket`,
     provider, or external API path.
   - Hacking is modeled as in-world digital state only and does not touch real
     network systems.

4. **No secret access**
   - Module runtime code does not read `.env`, provider secrets, raw env, API
     keys, or local private files.
   - `module_state_path` rejects sensitive path segments such as `secrets`,
     `api_key`, `debug_memory`, and `raw_env`.
   - Import/export hardening rejects secret-like package content.

5. **No direct database writes**
   - v2.7 module rule helpers do not import database repositories or write DB
     state directly.
   - Module playtests use in-memory/temporary state and TestClient setup when
     API coverage is needed.

6. **GameState mutation is copy/apply based**
   - Module helpers return `ActionResult` and `StateDelta` lists plus `Event`
     records.
   - Tests explicitly verify that selected module calls do not mutate the input
     `GameState` before deltas are applied.
   - Runtime changes are applied through `apply_delta` in tests/playtests.

7. **Namespaced module state**
   - New module state is held in `GameState.modules`.
   - `ModuleStateExtension.namespace` must equal
     `state.modules.{module_id}`.
   - `module_state_path` constructs `modules.{module_id}...` delta paths.
   - Invalid module namespace declarations are rejected.

8. **Core GameState schema protection**
   - `ModuleStateField` rejects core field names including
     `schema_version`, `engine_version`, `contract_version`, `player`,
     `facts`, `npcs`, and `quests`.
   - Module extension validation rejects attempts to declare non-module
     namespaces.

9. **StateDelta path validation**
   - `validate_module_state_delta` enforces the module prefix
     `modules.{module_id}` for module-owned deltas.
   - It rejects sensitive path segments.
   - Tests cover rejection of a module delta targeting `player.hp`.

10. **EventLog coverage**
    - Module action/tick helpers create `Event` records with the same
      `state_deltas` returned in the `ActionResult`.
    - Module playtest reports track `event_count`.
    - Module quality gate can block missing EventLog coverage when configured
      with `require_event_log=true`.

11. **Save/load stability**
    - Module playtests validate JSON save/load stability.
    - v2.7 integration regression tests validate save/load stability for module
      state and tactical state.

12. **Migration dry-run and apply semantics**
    - `ModuleMigrationService.dry_run_module_migration` works on a deep copy
      and does not mutate the original state.
    - `apply_module_migration` requires confirmation when the plan requires it.
    - Successful apply appends `module_migration_history`.
    - Apply failures return the original state and a report with errors.

13. **Destructive remove default rejection**
    - `ModuleMigrationStep` requires `destructive=True` for
      `remove_module_state`.
    - `ModuleMigrationService` still rejects removal unless
      `confirm_destructive=true`.
    - `ModImportExportService.remove_module_state` also rejects destructive
      removal by default.

14. **Hidden module info filtering**
    - Tactical visible summary omits hidden combatants.
    - Faction war visible summary omits unknown/hidden regions.
    - Hacking log extraction filters hidden logs.
    - Deduction rejects hidden evidence and only uses known facts for
      hypothesis testing.
    - Survival event summaries do not include hidden route danger.
    - Cultivation rejects hidden techniques.
    - Module playtests check visible summaries for hidden leak sentinels.

15. **Module Quality Gate coverage**
    - `ModuleQualityGateConfig` includes playtest, EventLog, save/load,
      hidden leak, action conflict, migration failure, and dangerous permission
      checks.
    - Compatibility stress reports can surface namespace conflicts, action/alias
      conflicts, migration conflicts, permission conflicts, hidden leak risks,
      and load order.

## High-Risk Issues

None found in the current v2.7 implementation.

## Medium-Risk Issues

1. **Some advanced module helpers intentionally emit non-module StateDelta paths**
   - Examples include player inventory changes for crafting/forage, `turn`
     changes for travel, and public consequence flags for public illegal magic.
   - These are engine-owned consequences rather than module-state extensions,
     and tests verify they are explicit `StateDelta` outputs.
   - Risk: future modules could expand this pattern and accidentally write
     broader core fields without a clear allowlist.
   - Recommendation: add a formal v2.7 module consequence allowlist for
     permitted non-module paths such as `turn`, `player.inventory`, and vetted
     public consequence flags.

2. **EventLog is produced by helpers but not yet enforced by a runtime wrapper**
   - Current helpers return events and tests/playtests check EventLog coverage.
   - Risk: future callers could apply deltas without appending the returned
     `Event`.
   - Recommendation: introduce a shared module action runner that atomically
     resolves action, applies deltas, and appends EventLog, or route all
     player-facing module actions through the existing game loop.

3. **Module state schema is MVP-level**
   - `ModuleStateExtension` validates namespace/default fields but does not yet
     perform deep JSON Schema validation for every module field.
   - Recommendation: add typed per-module extension specs or JSON Schema
     validation before accepting external module packages as fully enabled.

## Minor Issues

1. **ActionRegistry integration is not complete for every advanced helper**
   - v2.7 includes deterministic helpers and dashboard/API scaffolding.
   - Some actions are not yet registered as runtime `ActionRegistry` handlers.
   - This is not a current state/security blocker, but it should be completed
     before wider player-facing module enablement.

2. **Import/export v2.7 action conflict detection is shallow**
   - Current import dry-run detects duplicate action ids inside selected action
     payloads.
   - Cross-package and core-action conflict checks are covered by compatibility
     stress/quality paths, but import dry-run could be made stricter.

3. **Hidden filtering is module-specific**
   - Each module currently handles hidden data with local rules.
   - A shared safe-summary helper would reduce the chance of future omissions.

## Recommendations

1. Add a `ModuleConsequencePolicy` or equivalent allowlist for non-module
   `StateDelta` paths emitted by advanced modules.
2. Add a shared module runtime runner that guarantees:
   - resolve action;
   - validate all deltas;
   - apply through `apply_delta`;
   - append EventLog;
   - return safe visible summary only.
3. Extend `ModuleQualityGate` to scan all advanced module files for filesystem,
   network, database, `eval`, `exec`, provider, and secret-access imports as the
   v2.7 module surface grows.
4. Add deep schema validation for package-provided module state definitions
   before any import can enable a module by default.
5. Keep destructive state removal blocked by default and require explicit
   user-facing confirmation plus backup/migration report for any future remove
   flow.
6. Continue running hidden-leak playtests for tactical, economy, faction,
   magic, hacking, crafting, deduction, survival/travel, and cultivation paths.

## Release Impact

This audit does **not block v2.7 release**.

The current code preserves the main state/security boundaries:

- no arbitrary code execution;
- no module network or filesystem access;
- no secret reads;
- no direct database writes;
- no direct mutation of active `GameState`;
- module state is namespaced under `state.modules.{module_id}`;
- module deltas and migration are validated;
- destructive removal is blocked by default;
- hidden module data is filtered from normal visible summaries;
- quality gate covers the important module safety categories.

The medium-risk items should be treated as v2.7 hardening follow-ups, especially
the formal allowlist for non-module consequence deltas and a shared runtime
runner that enforces EventLog append semantics.
