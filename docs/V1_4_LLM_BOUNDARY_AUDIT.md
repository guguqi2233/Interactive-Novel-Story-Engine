# v1.4 LLM Boundary Audit

Verification Date: 2026-05-20

Scope:

- v1.4 Content Production Pipeline modules.
- Existing LLM provider factory and prompt-context boundaries.
- v1.4 tests, production CLI, batch validators, import/export profiles, package builders, and campaign starter builder.

Review Commands:

- `rg -n "OpenAI|create_llm_provider|LLMProvider|generate_json|generate_text|chat\\(|completion|llm|provider" backend/app/engine/content backend/app/quality backend/app/tools backend/tests`
- `rg -n "visible facts|visible_facts|narrator_safe|npc_known_facts|known_facts|hidden facts|hidden_fact|private_self_summary|prompt" backend/app/llm backend/app/roleplay backend/app/engine backend/app/api.py`
- `rg -n "GameState|StateDelta|validation_gate|AuthoringValidationGate|writes_to_disk|confirm_apply|active_game_state|apply" backend/app/engine/content backend/app/quality`
- Manual review of v1.4 production modules and tests.

## Verdict

v1.4 passes the LLM permission boundary audit.

No v1.4 production module was found to call a real LLM provider, instantiate a concrete provider, send generated production content to an LLM, or allow LLM output to modify active `GameState`. The v1.4 pipeline remains draft/package oriented: generators create structured drafts, candidates, previews, package manifests, and safe reports; explicit apply/build paths require confirmation and validation.

This audit does not block v1.4 acceptance.

## Passed Items

1. v1.4 modules do not call LLM by default.
   - Reviewed modules under `backend/app/engine/content` added for v1.4: World Pack Wizard, NPC Pack Generator, Quest Pack Generator, Location Cluster Templates, Mystery Templates, Faction Templates, Content Batch Validator, Coverage Planner, Import/Export Profiles, Local Content Library Pro, Batch Character Card Import, Batch Lorebook Classification, Script Package Builder, Campaign Starter Kit, Production Pipeline Dashboard, Production CLI, and Batch Quality Gate.
   - No direct `OpenAI`, `create_llm_provider`, `generate_json`, or concrete provider use was found in these production modules.

2. World Pack Wizard defaults to deterministic local generation.
   - `WorldPackWizardDraft.llm_assisted` exists as metadata/reserved future flag.
   - Current generation is deterministic Python/YAML generation and validation.
   - Preview and validate do not write disk; apply writes only content pack files after explicit confirmation and `AuthoringValidationGate`.

3. NPC Pack Generator defaults to deterministic local generation.
   - `NPCPackGeneratorDraft.llm_assisted` exists but is not used to call an LLM.
   - NPC candidates, RP profiles, voice profiles, schedules, goals, relationships, and hidden secrets are generated locally.
   - Safe export drops runtime knowledge/secrets and `private_self_summary`.

4. Quest Pack Generator defaults to deterministic local generation.
   - `QuestPackGeneratorDraft.llm_assisted` exists but is not used to call an LLM.
   - Quest candidates, clue facts, scenario regression drafts, and quest graph drafts are rule/template generated.
   - Apply writes only through `ContentAuthoringService.write_files`, which uses validation gate paths.

5. Mystery Template System does not call LLM to invent hidden truth.
   - Built-in mystery templates define hidden truth, suspects, clues, red herrings, and scenario drafts as structured data.
   - `truth_fact` is hidden and normal/player-facing generated text avoids raw truth text.

6. Batch Character Import treats external prompts as untrusted.
   - Batch import delegates each card to `CharacterCardImporter`.
   - External `system_prompt`, creator notes, and prompt-control text are reported as unsafe/unsupported.
   - Output is a draft character pack; it does not write active world or active `GameState`.

7. Batch Lorebook Classification does not put unsafe entries into prompts.
   - Batch lorebook import delegates to `LorebookClassifier`.
   - Prompt-control/injection entries are classified as unsafe and reported in `unsafe_entries`.
   - Hidden lore entries are redacted in normal reports unless explicit authoring debug mode is used.

8. Script Package Builder blocks prompt secrets and API keys.
   - Script package validation rejects `api_key`, `sk-`, private key markers, bearer tokens, `.env`, DB/log files, and executable suffixes.
   - It builds manifests/checksums and archives only; it does not execute package code or invoke LLM.

9. Campaign Starter Builder does not let LLM write active world.
   - Campaign starter preview composes deterministic drafts from existing builders/templates.
   - `llm_assisted` is reserved and reported as draft-only warning.
   - Build does not modify active `GameState`.

10. Generators only create drafts, candidates, or packages.
    - v1.4 generators return preview/report models with `writes_to_disk=False` by default.
    - Explicit apply/build paths require confirmation.
    - Active sessions are not modified.

11. No LLM output directly enters `GameState`.
    - No v1.4 production path sends content to an LLM or consumes LLM output.
    - Existing runtime LLM use remains behind intent/narration/dialogue boundaries and provider factory.

12. No LLM output bypasses validation gate.
    - v1.4 production paths are not LLM-backed.
    - Apply/build/import/export paths use validation or package safety checks; primary world content apply paths go through `AuthoringValidationGate` via `ContentAuthoringService`, `WorldPackWizard`, or import/export services.

13. Narrator prompt boundary remains intact.
    - `backend/app/llm/context_builder.py` continues to build narrator context from player-visible facts and narrator-safe memory.
    - Hidden facts are excluded unless already visible to the player.

14. NPC dialogue context remains knowledge-scoped.
    - `backend/app/roleplay/dialogue.py` and `backend/app/llm/context_builder.py` continue to pass `npc_known_facts` / NPC-known context rather than raw world facts.
    - RP prompt style summaries exclude private fields.

15. Hidden facts are guarded before prompt use.
    - Roleplay boundary, output consistency checker, example dialogue filtering, dialogue scene authoring, group scene authoring, lorebook classification, character card import, and world validation all include hidden leak checks.
    - v1.4 normal production reports redact hidden lore/fact text.

16. Provider factory remains the provider selection entry point.
    - Provider selection is centralized in `backend/app/llm/provider_factory.py`.
    - v1.4 production modules do not instantiate `OpenAIProvider`, `LocalHTTPProvider`, or `MockLLMProvider`.
    - Tests that exercise provider behavior use explicit mock/local-stub configuration.

17. Tests do not call real APIs.
    - v1.4 API tests set `llm_provider="mock"` or do not instantiate providers.
    - v1.4 generator tests include source-level checks that production modules do not call `OpenAI` or `create_llm_provider`.
    - Full regression currently passes with local deterministic providers.

## Risk Items

1. Reserved `llm_assisted` fields exist in several v1.4 schemas.
   - Impact: Low today, because they do not trigger provider calls.
   - Risk: Future implementation could accidentally connect these flags to real LLM generation without enforcing draft-only, schema validation, provenance, and validation gate boundaries.

2. Existing `side_quest_generator.llm_assisted_generate_side_quest` remains in the codebase.
   - Impact: Low for v1.4, because it is not part of the v1.4 production pipeline and accepts an injected `LLMProvider`.
   - Risk: If future production modules reuse it, generated quest text must remain draft-only and pass hidden leak validation.

3. Normal report redaction is implemented per module.
   - Impact: Low to medium.
   - Risk: As more v1.4/v1.5 package/report formats are added, inconsistent report redaction could accidentally expose hidden generated text to normal views.

4. CLI output redaction is string-token based.
   - Impact: Low.
   - Risk: Semantic hidden text not containing tokens such as `hidden`, `secret`, or known fact ids may not be fully redacted unless the upstream report already redacts it structurally.

## High-Risk Issues

None found.

No v1.4 production module was found to:

- Call a real LLM.
- Instantiate a concrete LLM provider directly.
- Treat LLM output as authoritative content.
- Write LLM output to active `GameState`.
- Bypass validation gate with generated content.

## Medium-Risk Issues

None blocking.

Medium attention item:

- Reserved `llm_assisted` flags should remain inert until a future explicit design adds provider-factory-only, fake-provider-tested, schema-validated, draft-only behavior. This is not a release blocker because the current code does not call LLM.

## Minor Issues

1. Some source-level tests search for specific strings such as `OpenAI` / `create_llm_provider`.
   - This is useful as a guardrail but not a complete semantic proof. Keep integration tests that verify behavior, not only source text.

2. CLI redaction is intentionally conservative and token based.
   - Continue preferring structured report redaction upstream over relying on CLI text filters.

3. `llm_assisted` reserved fields may confuse future contributors.
   - Documentation should continue to state that these flags are reserved and default-off, not active content generation.

## Fix Recommendations

No release-blocking fixes are required.

Recommended non-blocking follow-ups:

1. Add a shared `LLM_ASSISTED_RESERVED` policy helper if v1.5 adds more reserved LLM-assisted fields.
2. Keep all future LLM-assisted content generation behind:
   - provider factory only,
   - fake-provider tests,
   - schema validation,
   - draft-only output,
   - provenance metadata,
   - hidden leak checks,
   - `AuthoringValidationGate`,
   - no active `GameState` writes.
3. Centralize normal-report redaction for production reports before adding more package types.
4. Keep CLI output tests for hidden/API key redaction.

## Acceptance Impact

Not blocking v1.4 acceptance.

Final assessment:

- LLM remains a language/narration layer, not a world judge.
- v1.4 production tools are deterministic local draft/package tools by default.
- Generated content cannot directly modify active `GameState`.
- Hidden facts and prompt-unsafe external content are classified, redacted, quarantined, or validation-gated before use.
- Provider factory remains the only provider selection entry point.
