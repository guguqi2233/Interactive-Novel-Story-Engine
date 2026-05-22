# v2.6 LLM Boundary Audit

Verification date: 2026-05-22

Scope: v2.6 Script / Mod Platform Pro contracts, pack validators, Action Mod registration/evaluation, Rule Module contract, Module Browser, Compatibility Matrix, Certification Tool, Mod Quality Gate, Import/Export hardening, Mod Audit Trail, and regression tests.

## Passed Items

1. Prompt Profile Pack cannot enable hidden fact access.
   - `PromptProfilePack` validation rejects `can_access_hidden_facts`, `can_modify_state`, `can_override_action_result`, and `can_bypass_visibility`.
   - Coverage exists in `test_v26_mod_platform.py` and `test_v26_script_mod_platform_integration.py`.

2. Narrative Style Mod is expression-only.
   - `NarrativeStyleMod.safe_summary()` reports `fact_authority=expression_only`.
   - Conversion to prompt preset explicitly sets hidden/state/action override permissions to `False`.
   - Validation rejects hidden access, state modification, action result override, key-item creation, and quest completion behavior markers.

3. RP Profile Mod cannot modify NPC knowledge.
   - RP patches are limited to soft presentation paths.
   - Patch paths containing `knowledge`, `hidden`, or `game_state` are rejected.

4. Action Mod cannot call LLM.
   - `ActionMod` rejects `call_llm` markers.
   - `ModulePermissionSet` treats `call_llm` as a dangerous blocked permission.
   - `ModActionEvaluator` delegates only to the deterministic declarative handler and does not import provider/gateway code.

5. Rule Module cannot call LLM by default.
   - `RuleModulePermissions.can_call_llm` defaults to `False`.
   - `validate_rule_module_manifest()` rejects `can_call_llm=True`.

6. Mods do not bypass Provider Gateway.
   - v2.6 mod modules do not instantiate providers or call `generate_text` / `generate_json`.
   - Provider Profile Pack is metadata/template-only and does not execute provider connection tests.

7. Mods cannot let LLM directly modify GameState.
   - v2.6 mod paths are declarative package/profile/style/action/rule contracts.
   - Action Mods return `ActionResult` with `StateDelta` proposals through the declarative handler; tests verify the source `GameState` remains unchanged.

8. Mods cannot let LLM decide action success.
   - Action success is determined by declarative preconditions/checks/outcomes and deterministic handler logic.
   - `ModActionEvaluator` has no LLM dependency.

9. Provider Profile Pack does not allow secrets.
   - Validation rejects `api_key`, `authorization`, `x-api-key`, auth/key headers, and non-test `sk-`-like literals.
   - Import/export special-cases provider packs so `api_key_env` is allowed while raw key fields remain rejected.

10. Hidden facts and raw state deltas are blocked in relevant v2.6 package paths.
    - Script and World Extension validators scan for hidden/debug leak markers, including hidden facts, NPC secrets, debug memory, and raw state delta markers.
    - Action Mod hidden visible-text leak is covered by the test harness.

11. Existing Novel/Tavern/World/CrossMode LLM boundaries remain intact.
    - v2.6 adds mod/package infrastructure without changing provider routing, World Engine authority, CrossMode apply flow, or Novel/Tavern prompt generation behavior.
    - Existing v2.4/v2.5 regression suites still pass.

12. Tests do not call real APIs.
    - New v2.6 tests use local schemas, temp directories, `mock` settings, and CLI subprocesses only.
    - Full test suite passes without real OpenAI, relay, or local model calls.

13. Quality Gate is deterministic.
    - `ModQualityGate` composes Module Browser, Compatibility Matrix, and Certification results.
    - It does not use an LLM judge for pass/fail.

## Risk Items

1. Validator invocation is still a contract requirement.
   - Some pack schemas are permissive containers by design; safety conclusions require running the relevant validator or import/quality gate path.
   - This is acceptable for v2.6 because package import, Module Browser, Certification, Quality Gate, and regression tests all use validation paths.

2. Hidden leak detection is marker-based in v2.6.
   - Current checks catch explicit hidden/debug/raw-state markers and forbidden permission fields.
   - They are deterministic and safe, but they are not semantic classifiers.

3. `ActionMod` security marker scanning is intentionally narrow.
   - `call_llm` and arbitrary-code markers are blocked, while filesystem/network/database access is primarily blocked by `ModulePermissionSet`, manifest validation, executable rejection, and import/export scanning.
   - This avoids false positives in benign text, but means full safety relies on the combined package validation stack.

## High-Risk Issues

None found.

## Medium-Risk Issues

None blocking.

Non-blocking medium watch item: ensure every future import/install/enable path always calls the appropriate pack validator and Mod Quality Gate before making a package available. Direct schema construction alone should not be treated as certification.

## Low-Risk Issues

1. Hidden/debug leak checks are conservative string/marker checks, not semantic redaction.
2. Rule Modules are contract-only and experimental; future runtime support will require a fresh LLM/security review.
3. Action Mod DSL support is intentionally minimal and delegated to the existing declarative handler; richer DSL behavior will need additional tests before acceptance.

## Fix Recommendations

1. Keep all future module enable/install flows gated by:
   - manifest validation,
   - `ModulePermissionSet`,
   - package-type validator,
   - compatibility matrix,
   - Mod Quality Gate,
   - audit record.

2. If v2.7+ adds richer prompt/style imports, add structured fields for prompt permissions instead of relying on marker scanning alone.

3. If Rule Module runtime execution is ever introduced, require a new sandbox design and a separate acceptance boundary. Do not reuse the v2.6 contract-only approval as runtime approval.

4. Add future tests that exercise Module Browser API responses for prompt/style/RP/provider packs once example fixture packages exist.

## Acceptance Blocker Status

Not blocking v2.6 acceptance.

The reviewed v2.6 implementation preserves the LLM boundary: mods cannot call providers, cannot decide world facts, cannot directly mutate `GameState`, cannot bypass `StateDelta` / `EventLog`, and cannot turn LLM output into authoritative World state.
