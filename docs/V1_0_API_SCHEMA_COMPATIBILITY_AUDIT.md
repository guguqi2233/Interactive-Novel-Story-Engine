# v1.0 API / Schema Compatibility Audit

Verification date: 2026-05-19

Scope:

- Core schemas: `GameState`, `StateDelta`, `Event`, `visible_state`, `SaveGame`
- Compatibility contracts: API, content pack schema, save migration, mod packaging
- Frontend API types in `frontend/src/api.ts`
- Legacy save fixtures and migration compatibility coverage
- v1.0 breaking-change risks for local stable edition

This audit is read-only except for this report. It does not change runtime behavior.

## Verdict

v1.0 API and schema compatibility is acceptable for release candidate status.

No high-risk compatibility blocker was found. The remaining risks are mostly contract clarity and long-term freeze risks: the GameState schema version is still `0.6`, quality API gating is split across existing local flags rather than a dedicated `ENABLE_QUALITY_API`, and player-visible map exit semantics should remain carefully documented.

## 已通过项目

1. Core `GameState` schema is versioned and stable.
   - `GameState` includes `schema_version`.
   - Current schema constant is `CURRENT_GAME_STATE_SCHEMA_VERSION = "0.6"`.
   - `load_game_state_payload` supports legacy payloads and version defaulting.

2. `StateDelta` schema is stable.
   - Operations are explicit: `SET`, `INC`, `ADD`, `REMOVE`.
   - Delta paths are validated.
   - State mutation still routes through `apply_delta`.

3. `Event` schema is stable.
   - Events include event id, turn, actor, action type, result, visibility, deltas, and timestamp.
   - Events require state deltas unless explicitly marked `allow_empty_delta`.
   - EventLog remains suitable for replay/debug/save recovery.

4. `visible_state` schema is represented consistently.
   - Frontend `VisibleState` type includes world, turn, location, inventory, visible objects, visible NPCs, known facts, quests, factions, rumors, crimes, relationships, combat summaries, and player condition.
   - Player API response envelopes in frontend types match backend player API contracts.

5. `SaveGame` schema contains version metadata.
   - Save metadata includes `engine_version`, `schema_version`, `world_id`, `world_version`, `content_pack_version`, timestamps, enabled mods, and `migration_history`.
   - Repository schema and Pydantic model are aligned.

6. Migration contract is clear.
   - `docs/V1_0_SAVE_MIGRATION_GUARANTEE.md` defines supported and unsupported migration ranges.
   - Legacy fixtures cover v0.3-like through v0.9-like saves, legacy saves, corrupted saves, hidden facts, debug memory, and old content pack versions.
   - Dry-run, idempotency, history, and hidden visibility preservation are tested.

7. Content pack schema is documented.
   - `docs/CONTENT_PACKS.md` and `docs/V1_0_CONTENT_SCHEMA_CONTRACT.md` cover manifest, locations, NPCs, items, quests, facts, factions, rumors, relationships, templates, scenario files, prompt profiles, visual fields, economy fields, and consequence fields.

8. Mod manifest schema is documented.
   - `docs/V1_0_MOD_CONTRACT.md` freezes the local content-only mod contract.
   - The contract explicitly forbids executable entrypoints, script execution, path traversal, online download, and active GameState mutation.

9. Player API compatibility is documented and tested.
   - `docs/V1_0_API_CONTRACT.md` documents player-facing routes and forbidden player fields.
   - Contract tests check player response shape and absence of debug/hidden fields.

10. Authoring API compatibility is documented.
    - Authoring routes are classified as local-only and gated by authoring configuration.
    - Preview / validate / save semantics are documented for visual editors, templates, import/export, and world files.

11. Debug API is clearly local-only.
    - Debug routes are documented as gated by `ENABLE_DEBUG_API`.
    - Raw state deltas and timeline replay remain debug-only by contract.

12. Quality API is local-only by policy.
    - Quality, eval, playtest, benchmark, and gate routes are documented as local tooling.
    - Quality reports use safe normal views and debug-only hidden details.

13. Frontend API types broadly match backend contracts.
    - Frontend types exist for visible state, saves, migrations, studio status, graphs, authoring, quality, playtests, and local configuration summaries.
    - The TypeScript API client does not model API keys or raw environment dumps.

14. Examples mostly align with actual schemas.
    - v1.0 content schema examples follow the loader/validator shape for the main world-pack files.
    - Migration and mod examples match the documented contracts.

15. Old fixtures can migrate.
    - Compatibility tests cover legacy save fixtures up to v0.9-like saves.
    - Corrupted saves are expected to fail safely instead of being silently overwritten.

16. Breaking-change policy is documented.
    - API and content schema documents define additive optional fields, migration requirements for breaking changes, and warning-before-breaking policy.

## 兼容性风险

1. GameState schema version remains `0.6` in a v1.0 release.
   - This is not automatically a breaking issue: engine release version and GameState schema version can differ.
   - Risk is user/operator confusion unless release notes and migration docs keep saying that v1.0 still uses the current save schema version.

2. Quality API does not appear to have a single dedicated `ENABLE_QUALITY_API` freeze point.
   - Current documentation allows quality routes to be gated through existing eval/playtest/perf/debug configuration.
   - This is compatible with current code, but less clean as a stable v1.0 API contract.

3. Player-visible location exits need a precise compatibility rule.
   - Player map graph filtering protects hidden edges, but `visible_state.location.exits` is a core player schema field.
   - If content authors rely on hidden or conditional exits, the compatibility contract should state exactly whether such exits may appear in `visible_state`.

4. Some frontend visible-state fields are optional while backend often returns arrays.
   - Optional frontend fields are backward-compatible, but they make the frozen frontend contract slightly looser than the backend response shape.

5. API and content examples are manually maintained.
   - The project has contract tests, but not a generated OpenAPI/schema snapshot checked into docs.
   - Future drift is possible if examples change independently from Pydantic/TypeScript types.

6. Player-visible faction and reputation fields are already part of the API surface.
   - If v1.1 wants to simplify or hide raw numeric bands, that may become a breaking frontend/API change.

## 高风险问题

None found.

No evidence was found that a core schema is undocumented, that old save fixtures are unmigratable, or that player API contract tests knowingly permit raw hidden/debug state.

## 中风险问题

1. `schema_version = "0.6"` may be mistaken for an incomplete v1.0 schema freeze.
   - Impact: migration support and operator expectations.
   - Suggested handling: explicitly state in v1.0 release notes and migration guarantee that schema version is independent from product version.

2. Quality API gating is split across local flags.
   - Impact: long-term API compatibility and operator configuration.
   - Suggested handling: either keep the documented split as the v1.0 contract, or add a future non-breaking `ENABLE_QUALITY_API` umbrella in v1.1.

3. Hidden/conditional exit semantics need contract-level clarity.
   - Impact: compatibility between world content, player visible state, and map graph APIs.
   - Suggested handling: freeze the rule that player visible map/exits may only contain discovered/player-known exits, or document any intentional exception.

## 小问题

1. `docs/V1_0_API_CONTRACT.md` contains a stale note that it was written when `docs/V1_0_ROADMAP.md` was not present.
   - This does not affect runtime compatibility but should be cleaned up before final documentation freeze.

2. Some frontend response types are intentionally permissive.
   - Optional arrays and nullable fields are safe for compatibility, but they reduce strict schema drift detection.

3. Content schema examples are not all proven by doc-driven tests.
   - Current validation tests cover the sample world, starter templates, invalid fixtures, and hidden leakage fixtures, but not every snippet embedded in docs.

4. API contract tests focus on critical envelopes and disabled gates, not every route in a golden snapshot.
   - This is acceptable for v1.0 if the documented breaking-change policy is followed.

## 修复建议

Before v1.0 final tag:

1. Add a short note to release notes or migration docs:
   - Product release: v1.0.
   - Current GameState schema version: `0.6`.
   - This is intentional unless a breaking save schema migration is introduced.

2. Decide whether the v1.0 compatibility contract accepts split quality API gating.
   - If accepted, keep the current docs explicit.
   - If not, add a future additive umbrella flag rather than breaking existing flags.

3. Clarify player-visible exit semantics in `CONTENT_PACKS` / API contract.
   - Hidden exits and hidden map edges should not become player-visible through `visible_state`.

4. Consider adding a lightweight API schema snapshot test after v1.0.
   - This can compare route response envelopes and frontend types without forcing a large OpenAPI workflow.

5. Remove stale wording in API contract docs during final documentation cleanup.

## 是否阻塞 v1.0

Not blocking.

The current API/schema state is compatible enough for v1.0 provided the medium risks above are accepted as documented limitations or addressed during the final documentation pass. No high-risk API/schema compatibility blocker was identified.
