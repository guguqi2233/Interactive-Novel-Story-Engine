# v2.8 LLM Boundary Audit

## Verification Date

2026-05-23

## Scope

This audit reviews v2.8 Roleplay Immersion & Mature Module boundaries across:

- Tavern / RP prompt context and message generation
- Multi-NPC Scene Pro
- Mature content policy, consent / boundary checks, and fade-to-black
- Mature memory partition and export filtering
- Provider Safety Routing
- Tavern -> World and Tavern -> Novel cross-mode flows
- RP / Mature quality gates and regression tests
- PromptProfile / SceneMoodPreset / NarrativeStyleMod permission boundaries

The review is code/document inspection only. No business code was changed.

## Passed Items

1. **RP / Tavern cannot directly modify `GameState`.**
   - Tavern chat writes `TavernMessage` records only.
   - Tavern -> World changes are represented as proposals and require validation / explicit apply outside Tavern.
   - Tests cover GameState non-mutation for v2.8 Multi-NPC flows.

2. **Multi-NPC Scene does not grant NPCs omniscience.**
   - Multi-NPC safe summaries and generated reply endpoint avoid hidden facts, NPC secrets, raw state deltas, and direct world writes.
   - Current MVP reply is deterministic safe text, not autonomous multi-agent world simulation.

3. **LLM does not judge age, consent, or boundary policy.**
   - `MatureContentPolicy`, `ConsentState`, `BoundaryCheckService`, and `RoleplayBoundaryProfile` use deterministic local checks.
   - Unknown age, minor age, unwilling consent, coercion, and incapacitation are blocked locally.

4. **LLM does not decide mature policy.**
   - Mature policy is project-local structured configuration.
   - Mature Module defaults to disabled.
   - `allow_explicit_adult` defaults to false and cannot be enabled implicitly.

5. **Fade-to-black is deterministic and not bypassed by LLM routing.**
   - `FadeToBlackRenderer` uses fixed safe templates.
   - Boundary failures produce safe fallback/refusal-style text.

6. **Mature memory does not enter normal context.**
   - `AdvancedRPMemoryRecord` and `MatureMemoryPartitionService` exclude `mature_only` memory from normal Tavern / Novel contexts.
   - `ProjectMemoryRecord.safe_content()` redacts `mature_only`.

7. **Hidden facts, NPC secrets, and raw `state_deltas` are filtered from normal RP prompt surfaces.**
   - `TavernPromptContext` rejects payloads containing secret-like text, raw state delta markers, hidden fact markers, and private persona markers.
   - RP safety evals cover hidden fact prompt leakage.

8. **Provider routing checks `ProviderSafetyPolicy`.**
   - Provider safety policy includes `allowed_content_ratings`, `allow_mature_content`, `allow_explicit_adult`, and optional local-only mature routing.
   - `ProviderRouter.resolve_provider_for_content_rating()` rejects or falls back based on project and provider policy.

9. **Mature provider route cannot silently bypass policy.**
   - Mature routing first checks project `MatureContentPolicy`.
   - Primary and fallback provider choices must satisfy the same safety policy.
   - Local-only mature policy rejects cloud primary routing and falls back only to an allowed local provider.

10. **Tavern -> World cannot be directly applied by LLM output.**
    - Tavern-to-world flow attaches `CrossModeRPSafetyMetadata`.
    - Missing RP safety metadata is a validation error for Tavern -> World proposals.
    - Mature content / mature memory metadata is blocked from normal Tavern -> World proposal validation.

11. **RP memory is not treated as a World fact.**
    - Advanced RP memory has `authoritative=false`.
    - Relationship tone changes are proposals / expression metadata, not direct world relationship mutations.

12. **Cross-Mode RP bridge remains proposal / validation / apply based.**
    - Tavern -> Novel preview filters mature-only material by default.
    - Tavern -> World requires proposal metadata and validation.
    - Cross-mode validation catches missing RP safety metadata.

13. **Tests do not call real APIs.**
    - v2.8 tests use mock / local_stub provider metadata and FastAPI `TestClient`.
    - No OpenAI or remote provider call is required for v2.8 regression coverage.

14. **Quality Gate is not LLM-judged.**
    - RP / Mature quality gate uses deterministic local checks and safe summaries.
    - Reports redact sensitive text rather than asking an LLM to classify pass/fail.

15. **PromptProfile / StyleMod cannot enable hidden fact access.**
    - Scene mood and RP/mature profile schemas use `Literal[False]` permission fields for hidden access and state mutation.
    - Narrative Style Mod validation rejects explicitly forbidden behaviors rather than treating default false permission fields as unsafe.

## Risk Items

1. **Multi-NPC Scene Pro is still MVP-level.**
   - The current endpoint writes deterministic safe Tavern text and does not yet build rich per-NPC provider prompts.
   - This is safe for LLM boundaries, but future richer speaker context must keep per-NPC knowledge filtering strict.

2. **RP / Mature Quality Gate is intentionally minimal.**
   - Current gate proves default-safe behavior and blocker plumbing, but does not yet exhaustively scan every project artifact.
   - Existing focused evals cover key leak and policy cases; broader project-level scanning should be expanded before final v2.8 release.

3. **Provider safety relies on declared provider policy metadata.**
   - The router enforces local declarations, but it does not verify external provider real-world policy.
   - This is consistent with local-first architecture, but docs/UI must keep stating that provider policy is local configuration, not a legal/safety guarantee.

4. **Mature content generation is not implemented.**
   - This is an intentional non-goal. Current code supports policy, routing, filtering, and safe fade-to-black behavior.
   - Release notes should avoid claiming adult content generation support.

## High-Risk Issues

No high-risk LLM boundary blocker was found in the inspected v2.8 implementation.

Specifically, no inspected path allows:

- LLM output to directly mutate `GameState`;
- LLM judgment of age, consent, or mature policy pass/fail;
- mature memory in ordinary Tavern / Novel context;
- provider mature routing bypassing `ProviderSafetyPolicy`;
- Tavern -> World direct apply without proposal / validation;
- hidden facts or raw `state_deltas` in normal Tavern prompt context.

## Medium-Risk Issues

1. **Quality Gate breadth should be expanded before final acceptance.**
   - The deterministic RP/Mature Quality Gate exists, but its current implementation is a starting aggregation layer.
   - Recommended: add project artifact scanning for Tavern prompts, mature memory exports, provider routing mismatches, and cross-mode proposal metadata.

2. **Future Multi-NPC provider prompting needs stricter context tests.**
   - The current implementation is safe because it does not send rich hidden context.
   - If v2.8 later adds actual per-NPC ProviderGateway calls, tests must assert each prompt only includes that NPC's known facts and safe RP metadata.

## Low-Risk Issues

1. **Provider policy names are local declarations.**
   - The code enforces declared policy fields, but users must still configure provider profiles accurately.

2. **Fade-to-black templates are fixed and conservative.**
   - This is safe, but not yet stylistically rich.

3. **Mature settings UI is policy-focused.**
   - It intentionally does not display mature memory content or sensitive details.

## Fix Recommendations

Before v2.8 acceptance:

1. Expand RP/Mature Quality Gate project scanning so it checks stored Tavern messages, mature memory, exports, provider profile policy, and cross-mode proposals.
2. If Multi-NPC ProviderGateway generation becomes richer, add tests that capture outbound provider messages and assert:
   - no hidden facts;
   - no NPC secrets;
   - no raw `state_deltas`;
   - no mature memory in normal context;
   - no unknown facts for the active NPC.
3. Keep Mature Module release notes explicit that v2.8 provides default-off policy/routing/export/safety infrastructure, not an online mature content platform.
4. Preserve mock/local provider tests as the default and keep real provider calls out of CI.

## Acceptance Blocker Assessment

**Does this block v2.8 acceptance?**

No. The current LLM boundary implementation is acceptable for v2.8 acceptance as a default-off RP/Mature safety framework.

The medium-risk items above are recommended hardening tasks, not release blockers, provided final v2.8 acceptance continues to confirm:

- `python -m pytest` passes;
- `cd frontend && npm.cmd run build` passes;
- no real provider calls are made by tests;
- no high-risk hidden fact, mature memory, provider routing, or direct GameState mutation regression appears.
