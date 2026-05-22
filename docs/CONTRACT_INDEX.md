# Contract Index

Generated from local schema constants. This document contains no raw env, API keys, hidden facts, or user data.

## v2.9+ Roadmap Contract Note

v2.9 is now planned as **Local UI / UX Foundation**. The v3.x near-term roadmap
continues with local desktop, Novel, Tavern, World, authoring/mod, QA/debug/
replay, performance, and accessibility UI polish. Online-Ready Architecture,
account systems, cloud sync, online marketplaces, remote package registries,
online narrative platforms, and online mature-content platforms are long-term
optional directions, not active contract targets.

v2.9 also introduces frontend-only UI safety contracts for the Local UI / UX
Foundation. These contracts are not new backend authority layers; they document
safe summary, navigation, redaction, diagnostics, and local-first UI behavior.

## Stable Contracts
- `GameState`: `1.8` (compatible)
- `StateDelta`: `1.8` (compatible)
- `EventLog`: `1.8` (compatible)
- `ContentPack`: `1.8` (compatible)
- `SaveMigration`: `1.8` (compatible)
- `ModuleManifest`: `1.8` (compatible)
- `ActionMod`: `1.8` (compatible)
- `PromptProfile`: `1.8` (compatible)
- `ProviderGateway`: `1.8` (compatible)
- `Package`: `1.8` (compatible)
- `DebugAPI`: `1.8` (compatible)
- `QualityGate`: `1.8` (compatible)

## v2.1 Narrative Project Contracts
- `NarrativeProject`: `2.1` (local project metadata container)
- `ProjectWorkspaceLayout`: `2.1` (local directory structure and safety rules)
- `ProjectRepository`: `2.1` (project.yaml create/load/save/list/update)
- `ProjectModeConfig`: `2.1` (Novel/Tavern/World/Script/Quality mode flags)
- `ProjectLibraryRefs`: `2.1` (shared library references)
- `ProjectSafetyPolicy`: `2.1` (`local_only`, debug export flag, mature content flag, external provider flag, `export_secrets=false`)
- `CharacterProfile` / `CharacterLibrary`: `2.1` (shared character metadata; private notes authoring-only)
- `WorldBible` / `WorldBibleEntry`: `2.1` (flavor/structured/hidden/authoring entries with visibility filtering)
- `TimelineEvent` / `TimelineLibrary`: `2.1` (project timeline refs; hidden/authoring-only events filtered)
- `LoreFactEntry` / `LoreFactLibrary`: `2.1` (draft/flavor/structured/hidden lore and mode-safe filtering)
- `ProjectPromptProfile` / `PromptProfileLibrary`: `2.1` (mode-scoped style profiles; hidden/state authority fields fixed false)
- `ProjectProviderProfile` / `ProviderProfileLibrary`: `2.1` (provider metadata and env-var references only; no raw API keys)
- `ProjectMemoryRecord` / `ProjectMemoryLibrary`: `2.1` (non-authoritative project memory with mode filtering)
- `CrossModeLink`: `2.1` (reference links only; no automatic conversion or visibility change)
- `NovelProjectSection`, `NovelOutlineDraft`, `ChapterDraft`: `2.1` (Novel stub draft contracts)
- `NovelManuscript`, `NovelOutline`, `NovelChapter`, `NovelScene`, `CharacterArc`, `PlotThread`, `ForeshadowingItem`: `2.2` (Novel Studio MVP draft contracts)
- `NovelPromptContext`, `NovelWorldBibleContext`, `GeneratedNovelDraft`, `WorldContentDraft`, `NovelQualityReport`: `2.2` (Novel context, draft generation, conversion, and quality contracts)
- `TavernProjectSection`, `TavernSessionDraft`, `TavernMessageDraft`, `RPProposalDraft`: `2.1` (Tavern stub/proposal contracts)
- `TavernCharacter`, `TavernSession`, `TavernMessage`, `TavernSceneContext`: `2.3` (Tavern Studio MVP session/message contracts)
- `TavernRPProfile` / `TavernVoiceProfile`: `2.3` (RP and voice style contracts; expression only, no world authority)
- `TavernMemoryRecord`, `TavernLorebookEntry`, `TavernPromptContext`, `GeneratedTavernReply`: `2.3` (Tavern memory/lore/prompt/generation contracts with safe filtering)
- `SceneMoodPreset`, `RelationshipTone`: `2.3` (Tavern style/tone contracts; no GameState mutation)
- `TavernWorldProposal`: `2.3` (Tavern-to-World proposal contract; validation required, no apply-to-World path)
- `CrossModeDraft`: `2.4` (cross-mode draft artifact; safe summaries only, no direct World mutation)
- `CrossModeProposal`: `2.4` (reviewable cross-mode proposal; proposed StateDeltas are metadata until validated apply)
- `CrossModeReview`: `2.4` (review status and redacted notes for cross-mode artifacts)
- `CrossModeApplyPlan`: `2.4` (explicit apply plan; requires confirmation by default)
- `CrossModeAuditRecord`: `2.4` (append-only local bridge audit metadata; not a replacement for World EventLog)
- `CrossModeConflictReport`: `2.4` (normal/debug-safe conflict report across Novel/Tavern/World refs)
- `CrossModeValidationReport`: `2.4` (validation report for links, drafts, proposals, apply plans, provider/profile safety, and hidden-target risks)
- `CrossModeTimelineView`: `2.4` (normal-safe merged timeline view; hidden/debug/authoring entries filtered by default)
- `ProviderProfileV2`: `2.5` (provider profile metadata with provider type, env/secret refs, model profiles, fallback ids, cost hints, and safety policy; no raw API keys)
- `ModelProfile`: `2.5` (per-model capability, use-case, context-window, structured-output, and cost-hint metadata)
- `ProviderSafetyPolicy`: `2.5` (allowed/disallowed modes, sensitive/debug prompt controls, logging defaults, redaction, and local-only policy)
- `ProviderRoutingRule`: `2.5` (mode/use-case provider selection metadata with JSON capability and fallback constraints)
- `ProviderCallTrace`: `2.5` (safe fallback/call metadata contract; no prompt/output/API key/hidden text)
- `ProviderUsageRecord`: `2.5` (local token/cost estimate metadata; no prompt/output/API key/hidden text)
- `ProviderCapabilityReport` / `ModelCapabilityMatrix`: `2.5` (provider/model capability summaries for routing and UI; no provider calls required)
- `PackageManifestV2`: `2.6` (common local extension package manifest; declarative entry points only, checksums, compatibility, permissions, no executable payloads)
- `ModulePermissionSet`: `2.6` (structured package/module permissions; dangerous permissions denied by default)
- `ScriptPackV2`: `2.6` (script/scenario/template draft package; no automatic apply)
- `WorldExtensionPack`: `2.6` (additive/patch world content candidate package; no active GameState mutation)
- `CharacterPack`: `2.6` (character/RP/voice/world-NPC-draft package; private fields excluded from public summaries)
- `PromptProfilePack`: `2.6` (prompt/style profile package; cannot grant hidden fact access or state authority)
- `ProviderProfilePack`: `2.6` (provider profile template package; api_key_env/secret_ref only, no raw API keys)
- `NarrativeStyleMod`: `2.6` (expression-only narrative style package; no fact authority)
- `RPProfileMod`: `2.6` (RP/voice presentation patch package; cannot patch NPC knowledge)
- `ActionMod`: `2.6` (declarative action mod package registered through ActionRegistry; no arbitrary code or LLM calls)
- `RuleModuleManifest`: `2.6` (rule module contract/permission manifest; no v2.6 runtime code execution)
- `ModCompatibilityMatrix`: `2.6` (local dependency/conflict/version/permission compatibility report)
- `ExtensionCertificationReport`: `2.6` (deterministic local package certification report; not an online certification)
- `ModQualityGateResult`: `2.6` (mod/package quality gate result for manifest, permission, compatibility, secret, executable, and action-test checks)
- `ModAuditRecord`: `2.6` (safe local audit record for module scan/validate/certify/quality/import/export operations; not EventLog)
- `ModuleStateExtension` / `ModuleStateField`: `2.7` (namespaced advanced module state extension contract under `state.modules.{module_id}`)
- `ModuleMigrationPlan` / `ModuleMigrationStep`: `2.7` (advanced module save migration dry-run/apply contract with destructive removal blocked by default)
- `TacticalCombatState`: `2.7` (module-scoped tactical encounters, combatants, AP, range, cover, stance, status, and visible summaries)
- `EconomySimState`: `2.7` (module-scoped markets, commodities, supply/demand, scarcity, price-index modifiers, and economy ticks)
- `FactionWarState`: `2.7` (module-scoped regional conflict, control score, front pressure, morale, supply, war phase, and visibility)
- `MagicState`: `2.7` (module-scoped casters, mana/focus, known spells, spell definitions, and local spell effects)
- `HackingState`: `2.7` (module-scoped hackable objects, access state, trace, visible logs, and in-world hacking actions)
- `CraftingState`: `2.7` (module-scoped recipes, jobs, material consumption, workstation checks, and output proposals)
- `DeductionState`: `2.7` (module-scoped evidence, claims, hypotheses, and known-fact-only deduction checks)
- `SurvivalTravelState`: `2.7` (module-scoped fatigue/hunger/thirst status, routes, travel costs, risk, camp/rest, and forage)
- `CultivationState`: `2.7` (module-scoped cultivators, realm/stage/progress/qi, techniques, breakthrough rules, and cultivation actions)
- `ModulePlaytestScenario` / `ModulePlaytestReport`: `2.7` (deterministic advanced module playtest contract with EventLog/save-load/hidden-leak checks)
- `ModuleCompatibilityStressReport`: `2.7` (advanced module combination stress report for namespace/action/migration/permission/hidden-leak conflicts)
- `ModuleQualityGateResult`: `2.7` (advanced module quality gate result for playtest, compatibility, migration, EventLog, save/load, hidden leak, and permission checks)
- `AdvancedRPMemoryRecord`: `2.8` (non-authoritative RP continuity memory with tavern/novel/mature/hidden/debug visibility filtering)
- `EmotionState` / `EmotionArc`: `2.8` (session-local emotional presentation metadata; no World fact authority)
- `RelationshipToneProfile`: `2.8` (bounded RP relationship-tone metadata derived from safe memory/emotion/world summaries)
- `RoleplayBoundaryProfile`: `2.8` (project/character/session RP boundary contract; mature disabled by default)
- `MatureContentPolicy`: `2.8` (default-off mature content policy for rating, adult eligibility, consent, fade-to-black, and export controls)
- `ConsentState` / `BoundaryCheckResult`: `2.8` (deterministic age/consent/boundary check contracts; no LLM judgment)
- `FadeToBlackPolicy`: `2.8` (safe deterministic fade/refusal/transition rendering policy)
- `MatureExportPolicy`: `2.8` (normal/authoring/debug export filtering contract with mature export disabled by default)
- `MatureModPolicy`: `2.8` (mature-related package policy for import/export warnings, default-disabled behavior, and boundary/provider restrictions)
- `RPSafetyEvalCase`: `2.8` (deterministic RP/Mature safety eval case contract for hidden, private, mature, provider, and export leaks)
- `RPStyleQualityReport`: `2.8` (local RP/style quality report for voice, mood, private/hidden leaks, and rating mismatch)
- `RPWorldConsistencyReport`: `2.8` (local RP-to-world consistency report for dead speakers, unknown facts, nonexistent refs, and quest contradictions)
- `CrossModeRPSafetyMetadata`: `2.8` (RP/Mature safety metadata attached to cross-mode proposals/drafts)
- `RPMatureQualityGateResult`: `2.8` (project quality gate sub-result for RP/Mature boundary, routing, export, consistency, and cross-mode blockers)
- `UnifiedNavigation`: `2.9` (frontend local navigation contract over existing Project/Novel/Tavern/World/Cross-Mode/Script-Mod/Provider/Quality/Debug/Settings surfaces; no new router authority)
- `LocalStatusBar`: `2.9` (frontend safe summary contract for project/backend/provider/quality/debug/local-only/privacy status)
- `ProjectHomeSummary`: `2.9` (frontend safe Project Home overview contract; no direct GameState mutation)
- `ModeLandingPage`: `2.9` (frontend safe mode entry contract for Novel/Tavern/World/Cross-Mode/Script-Mod/Provider/Quality/Debug surfaces)
- `DiagnosticsExportSafePreview`: `2.9` (frontend local diagnostics preview contract; filters API keys, `.env`, provider secrets, hidden facts, mature/private content, debug memory, and raw state deltas by default)
- `FrontendApiSafeError`: `2.9` (frontend API error formatting contract with secret/path/authorization/raw-debug redaction and disabled/debug API detection)
- `V29UISafetyCheck`: `2.9` (`npm.cmd run check:v29-ui` static UI safety check for local-first entries and no plaintext API key field)
- `WorldProjectSection`: `2.1` (project-aware World Mode adapter config)
- `ProjectPackageManifest`: `2.1` (NarrativeProject import/export package manifest)
- `ProjectValidationReport`: `2.1` (normal/debug-safe project validation report)
- `ProjectQualityGateConfig` / `ProjectQualityGateResult`: `2.1` (project-level quality aggregation)

## Notes
- v1.8 compatibility contracts are local-only and deterministic.
- v2.1 project contracts are local-only and do not replace GameState,
  StateDelta, EventLog, content-pack, provider, package, or compatibility
  contracts.
