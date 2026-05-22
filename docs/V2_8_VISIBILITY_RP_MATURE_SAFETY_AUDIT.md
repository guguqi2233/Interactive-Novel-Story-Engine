# v2.8 Visibility / RP / Mature Safety Audit

## Verification Date

2026-05-23

## Scope

This audit reviews v2.8 visibility, roleplay, and mature safety boundaries for:

- Tavern normal prompt construction
- Multi-NPC Scene Pro safe summaries and reply generation
- RP memory, mature memory, emotion, tone, mood, and voice context
- Mature content policy and consent / boundary checks
- Fade-to-black behavior
- Provider mature routing
- Mature-aware mod and export policy
- RP-world consistency checks
- RP/Mature quality gate and normal report redaction

This is a read-only audit. No code was modified.

## Passed Items

1. **Hidden facts do not enter Tavern normal prompt by design.**
   - `TavernPromptContext` rejects payloads containing hidden fact markers.
   - Tavern prompt context is built from safe summaries only.
   - v2.8 regression tests cover hidden prompt leak detection.

2. **NPC secrets do not enter NPC prompt / safe summaries.**
   - Tavern character, RP profile, voice profile, scene mood, relationship tone, and lore context paths use safe summaries.
   - World NPC to Tavern adapter warnings state that Tavern drafts do not expose NPC secrets or mutate GameState.

3. **NPC unknown facts do not enter Multi-NPC prompt in current MVP.**
   - Multi-NPC Scene Pro currently emits deterministic safe Tavern text and does not build rich hidden fact prompt context.
   - Multi-NPC safe summary advertises hidden fact / NPC secret filtering.
   - Regression tests assert hidden fact text is absent from Multi-NPC API output.

4. **Character private notes do not enter prompt/export normal context.**
   - `CharacterVoiceLabProfile.private_notes_authoring_only` is excluded from `safe_summary()`.
   - `MatureExportFilter` removes private notes / private persona fields in normal export.
   - Tests assert private voice notes are absent from built voice context.

5. **`mature_only` memory does not enter normal prompt.**
   - `MatureMemoryPartitionService.filter_for_normal_context()` excludes mature-only records.
   - `EmotionState.safe_prompt_context()` excludes hidden/debug/mature-only visibility.
   - Project memory safe content also excludes `mature_only`.

6. **`mature_only` memory does not enter normal export.**
   - `MatureExportPolicy` defaults to `include_mature_content=false` and `include_mature_memory=false`.
   - `MatureExportFilter` removes mature-only visibility records and mature scene text by default.
   - Project export tests confirm mature memory files are excluded from normal export.

7. **Mature content is disabled by default.**
   - `MatureContentPolicy.enabled=false`.
   - `allow_explicit_adult=false`.
   - `ProjectSafetyPolicy` baseline is documented as mature-disabled by default.

8. **Unknown/minor age is blocked.**
   - `BoundaryCheckService.check_character_age()` blocks `unknown` and `minor` age categories.
   - Tests cover unknown age blocking.

9. **Unwilling consent is blocked.**
   - `BoundaryCheckService.check_consent()` blocks `unknown` and `unwilling` consent status.
   - Tests cover unwilling consent blocking.

10. **Coercion / unconscious / incapacitation risk is blocked.**
    - `ConsentState.coercion_risk` and `intoxication_or_unconscious_risk` become blockers.
    - These checks are deterministic local code, not LLM judgment.

11. **Fade-to-black is available by default.**
    - `MatureContentPolicy.default_fade_to_black=true`.
    - `FadeToBlackRenderer` uses safe fixed templates and rejects unsafe markers.

12. **Provider-disallowed mature routing is blocked or downgraded.**
    - `ProviderRouter.resolve_provider_for_content_rating()` checks mature project policy before provider selection.
    - Provider policies with `allow_mature_content=false` reject mature routing.
    - Local-only mature policies reject cloud primary routing and can fall back only to an allowed local provider.

13. **Mature mod defaults to disabled.**
    - `MatureModPolicy.default_enabled` is `Literal[False]`.
    - Mature package import dry-run warns about mature packages.
    - Normal module export excludes mature package content by default.

14. **RP-world consistency catches dead speakers and omniscient NPC patterns.**
    - `RPWorldConsistencyChecker` catches dead/incapacitated NPC speaking.
    - It also catches hidden fact references and NPC unknown fact mentions.

15. **Quality Gate catches boundary bypass at least at the v2.8 MVP layer.**
    - `run_rp_mature_quality_gate()` detects mature default-on blockers.
    - Project quality gate integrates RP/Mature gate results.
    - RP safety evals and style/world consistency checkers provide deterministic blockers.

16. **Normal reports avoid printing sensitive text.**
    - RP style findings use `[redacted]` safe detail for private/hidden leaks.
    - RP safety eval results report issue codes rather than full sensitive payloads.
    - Quality gate normal dump redacts blockers, errors, and warnings.

## Possible Leak Paths

1. **Future richer Multi-NPC prompt construction.**
   - Current Multi-NPC implementation is safe because it does not build rich per-NPC provider prompts.
   - If future work adds real per-speaker ProviderGateway context, the highest-risk path will be per-NPC knowledge filtering.

2. **User-provided safe summaries.**
   - Many v2.8 systems rely on safe-summary inputs from existing Tavern/World/Prompt libraries.
   - Existing validators catch key markers, but future custom fields should continue using structured safe summary methods instead of raw payloads.

3. **Mature mod/package textual payloads.**
   - Mature package policy blocks default-enabled mature content, hidden fact access, provider bypass, executable payloads, and secrets.
   - However, normal content text still needs ongoing hidden-leak tests as mod formats expand.

4. **Quality Gate breadth.**
   - The v2.8 quality gate is wired in, but the current project-level RP/Mature scan is intentionally MVP.
   - Focused tests cover core boundaries; full artifact scanning should be expanded before release finalization.

## High-Risk Leak / Boundary Issues

No high-risk visibility, RP, or mature safety blocker was found in this audit.

No inspected path currently allows:

- hidden facts in Tavern normal prompt;
- mature-only memory in normal prompt/export;
- character private notes in normal prompt/export;
- unknown/minor/unwilling/coerced/incapacitated mature scenes to pass boundary checks;
- mature provider routing to bypass provider policy;
- Tavern/RP to directly mutate `GameState`;
- mature mod packages to default-enable mature content.

## Medium-Risk Issues

1. **RP/Mature Quality Gate should be broadened.**
   - Current gate covers default-safe and blocker plumbing, while focused checks cover individual safety cases.
   - Recommended expansion: scan stored Tavern messages, memory records, cross-mode proposals, provider policies, and export previews.

2. **Multi-NPC Scene Pro should remain conservative until per-NPC prompt capture tests exist.**
   - The current MVP is safe.
   - If ProviderGateway-driven multi-speaker generation is added, tests must capture outgoing prompt messages and assert per-NPC knowledge scope.

3. **Normal report redaction depends on safe dump methods being used.**
   - Current v2.8 reports have normal/safe dump methods and redacted issue details.
   - New report APIs should continue returning normal summaries by default, not raw debug payloads.

## Low-Risk Issues

1. **Fade-to-black templates are conservative.**
   - Safe and acceptable, but not yet deeply style-aware.

2. **Mature settings UI is policy-only.**
   - This is safer for v2.8, but users cannot inspect mature memory details from normal UI.

3. **Provider safety is declaration-based.**
   - The app enforces local `ProviderSafetyPolicy`; it does not independently verify external provider policies.

## Fix Recommendations

Before v2.8 final acceptance:

1. Expand RP/Mature Quality Gate artifact scanning for:
   - Tavern messages;
   - Tavern memory and mature memory;
   - cross-mode proposals;
   - normal project/novel/tavern/module export previews;
   - provider safety policy mismatch.
2. Add prompt-capture tests before adding richer Multi-NPC ProviderGateway calls.
3. Keep normal report APIs on safe summaries and gate raw/debug views behind explicit debug configuration.
4. Continue to run hidden leak and mature memory export tests as part of full regression.

## v2.8 Blocker Assessment

**Does this block v2.8?**

No. The audited implementation satisfies the v2.8 visibility, RP, and mature safety boundary for a default-off Mature Module and RP immersion MVP.

The medium-risk items are hardening priorities, not current release blockers, provided the final v2.8 acceptance run confirms:

- full backend tests pass;
- frontend build passes;
- no real provider/API calls occur in tests;
- normal exports and normal prompts remain free of hidden facts, NPC secrets, mature-only memory, private notes, raw `state_deltas`, and secrets.
