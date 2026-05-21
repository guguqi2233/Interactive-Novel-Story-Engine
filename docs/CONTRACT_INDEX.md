# Contract Index

Generated from local schema constants. This document contains no raw env, API keys, hidden facts, or user data.

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
- `WorldProjectSection`: `2.1` (project-aware World Mode adapter config)
- `ProjectPackageManifest`: `2.1` (NarrativeProject import/export package manifest)
- `ProjectValidationReport`: `2.1` (normal/debug-safe project validation report)
- `ProjectQualityGateConfig` / `ProjectQualityGateResult`: `2.1` (project-level quality aggregation)

## Notes
- v1.8 compatibility contracts are local-only and deterministic.
- v2.1 project contracts are local-only and do not replace GameState,
  StateDelta, EventLog, content-pack, provider, package, or compatibility
  contracts.
